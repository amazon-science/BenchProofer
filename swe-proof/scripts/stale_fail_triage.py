#!/usr/bin/env python3
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Split the not-green cells into "repair the spec" and "re-run the gate".

A red cell is not by itself a spec defect. It is a recorded FAIL LABEL about the
bytes the gate read when it ran, and those bytes move, so a cell can stay red on a
role that judged a specification no longer on disk. Routing that to a repair agent
asks for a defence against an attack the current spec may already reject, and the
honest answer -- "no repair needed" -- is not a repair, so the cell stays red and
the next wave asks again.

`audit_freshness.py` asks this for a GREEN cell and answers with the EARLIEST stamp
across the audit roles, because a green claim is only as fresh as its stalest role.
For a red cell the question is the mirror image and the stamp has to be the FAILING
role's own: a sibling re-run later says nothing about the verdict the cell is red on.

WHY A STRENGTHENED SPEC INVALIDATES A FAIL -- what `decide`'s verdicts mean here:

  * SPEC-IDENTICAL -- the recorded attack was admissible against exactly these
    bytes and still is. The label describes the spec on disk. REPAIR.
  * STRENGTHENED -- every line of difference only narrows what verifies. A recorded
    break claims "this wrong implementation verifies", and adding a constraint can
    only take implementations away, so the claim does not transfer to the stronger
    spec and has to be re-measured. RE-GATE. (The monotonicity runs the opposite way
    from the green case, where strengthening PRESERVES the verdict.)
  * RE-AUDIT -- a conjunct was removed or a postcondition rewritten. Neither
    direction transfers. RE-GATE.

RE-GATE IS NOT AMNESTY: it re-runs the role on the current bytes, and if the attack
still verifies the cell comes back red with a fresh stamp and lands in the repair
lane on the next pass. The routing only decides which of the two expensive things
is spent on the cell first, and a gate run is the cheaper.

THE COMMIT CLOCK TRAILS THE EDIT, so one committed blob cannot decide this: a spec
edit can sit uncommitted while a gate reads it, and then the newest commit at or
before the stamp reports an edit the gate already saw as a change made since,
misrouting a live label to a re-gate that can only reconfirm it. Both brackets are
compared instead -- newest at or before, oldest strictly after -- because whatever
the gate read is one of those two or lies between them, differing from the current
spec in the same direction. So a label is stale only when the spec on disk differs
from BOTH, and the ambiguous case resolves to REPAIR, the reading that does not
discard a live finding.

BOTH BRACKETS COME FROM THE REPOSITORY THAT CONTAINS THE CORPUS, which
`audit_freshness.History` resolves from the corpus path rather than assuming this
checkout: `--benchmark-dir` accepts a corpus anywhere on disk. A corpus no repository
holds has no brackets to offer, so nothing can be shown stale there and every label a
`sources` hash does not decide stands. That is the fail-closed direction for THIS
tool, and it is the mirror of `audit_freshness`'s: calling a label stale is what
discards evidence here, so an unprovable label goes to repair.

    stale_fail_triage.py --benchmark-dir benchmark-verified
    stale_fail_triage.py --out-stale lanes/regate.tsv --out-true lanes/repair.tsv
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from audit_freshness import (  # noqa: E402
    AUDIT_GATES, GATED, History, _sources_verdict, decide,
)
from swebench_unified.corpus_root import default_benchmark_dir  # noqa: E402

# The verdicts under which a recorded FAIL still describes the spec on disk.
# Only one, and it is the exact one: a byte-identical spec signature means every
# attack the gate ran is still admissible and still lands where it landed.
FAIL_TRANSFERS = frozenset({"SPEC-IDENTICAL"})


def failing_audit_gates(meta: dict) -> list[str]:
    """The audit roles this cell is red on, in gate order.

    The agent roles only: a static gate's fail re-runs cheaply on the current bytes
    and is never stale, so including one would route a mechanical defect into a
    re-gate lane that cannot fix it.
    """
    gates = meta.get("gates") or {}
    out = []
    for gate in AUDIT_GATES:
        entry = gates.get(gate)
        if isinstance(entry, dict) and str(entry.get("status")) == "fail":
            out.append(gate)
    return out


def _stamp(entry: dict) -> dt.datetime | None:
    raw = entry.get("checked_at")
    if not raw:
        return None
    try:
        return dt.datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
    except ValueError:
        return None


def commit_after(hist: History, rel: str, when: dt.datetime) -> str | None:
    """The OLDEST commit touching `rel` strictly after `when` -- the other bracket.

    Reaches into `History`'s newest-first index rather than running another `git
    log`, which over a whole corpus is one process instead of one per cell.
    """
    best: str | None = None
    for stamp, sha in hist._by_path.get(rel, ()):        # newest-first
        if stamp > when.timestamp():
            best = sha                                   # keep walking to older
        else:
            break
    return best


def _diverged(cell: Path, gates: dict, failing: list[str]) -> str:
    """Which recorded source no longer matches disk, as the row's own evidence.

    `_sources_verdict` answers yes/no, which is all the routing needs, but a row that
    just says "moved" is a claim the reader has to re-derive. Naming the file and both
    short digests makes the row checkable on sight, and a stale label and a live one
    go to different lanes.
    """
    for gate in failing:
        entry = gates.get(gate)
        src = entry.get("sources") if isinstance(entry, dict) else None
        if not isinstance(src, dict):
            continue
        for name, digest in sorted(src.items()):
            path = cell / name
            if not path.is_file():
                return f"{name} recorded by the gate is now missing"
            now = hashlib.sha256(path.read_bytes()).hexdigest()
            if now != digest:
                return f"{name} {digest[:12]} -> {now[:12]}"
    return "a recorded source no longer matches disk"


def plan_fail(cell: Path, backend: str, meta: dict,
              hist: History) -> tuple[str, str, str, str]:
    """`(verdict, detail, "", "")`, or `("_blob", "<before>", "<after>", gate)`.

    The blob form defers to the caller so every historical spec this run needs is
    fetched in one `git cat-file --batch`, as `audit_freshness.main` does. An empty
    `<after>` means the spec has not been committed since the gate ran: there is no
    later state for the gate to have read.
    """
    def final(kind: str, detail: str) -> tuple[str, str, str, str]:
        return kind, detail, "", ""
    gates = meta.get("gates") or {}
    failing = failing_audit_gates(meta)
    if not failing:
        return final("NO-AUDIT-FAIL", "red on static gates only")

    # `sources` is exact where it exists, and is asked of the failing roles alone: a
    # sibling that recorded no hashes cannot make this one unmeasurable. BOTH answers
    # are final, the MOVED one especially -- a recorded digest that no longer matches
    # the file IS the changed bytes, so falling through to the commit bracket below
    # would re-decide a proof by inference against a clock that trails the edit.
    sv = _sources_verdict(cell, {g: gates[g] for g in failing})
    if sv == "PROVEN-FRESH":
        return final("SPEC-IDENTICAL", f"{failing[0]} sources hashes match")
    if sv == "PROVEN-MOVED":
        return final("SPEC-MOVED", f"{_diverged(cell, gates, failing)} "
                                   f"(recorded by {failing[0]})")

    stamps = [(g, _stamp(gates[g])) for g in failing]
    dated = [(g, s) for g, s in stamps if s is not None]
    if not dated:
        return final("UNSTAMPED", f"{failing[0]} carries no checked_at")

    # The NEWEST failing role, not the oldest. The cell is red while ANY role is
    # red, so it can only be routed to a re-gate if EVERY failing role predates
    # the spec change -- one role that failed against the current bytes is a
    # live finding and the cell has to go to repair.
    gate, when = max(dated, key=lambda p: p[1])

    from swebench_unified.backends.registry import get_backend
    spec = cell / get_backend(backend).language.solution_filename
    if not spec.is_file():
        return final("NO-SPEC", f"{spec.name} missing")
    rel = hist.name(spec)
    if rel is None:
        # No repository holds this spec, so there is no dated copy to compare the
        # current bytes against. The fail-closed direction here is the mirror of
        # `audit_freshness`'s: this tool DISCARDS a finding when it calls a label
        # stale, so an unprovable label stands and the cell goes to repair.
        return final("SPEC-IDENTICAL",
                     f"no git repository contains {spec.name}; the label stands")
    sha = hist.commit_at(rel, when)
    if sha is None:
        # No commit at or before the stamp: the spec has never been committed in
        # the state the gate read. Cannot prove the label stale, so it stands.
        return final("SPEC-IDENTICAL", f"no committed blob at or before {gate}")
    later = commit_after(hist, rel, when)
    return "_blob", f"{sha}:{rel}", (f"{later}:{rel}" if later else ""), gate


def main() -> int:
    ap = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    ap.add_argument("--benchmark-dir", default=default_benchmark_dir())
    # Opt-in, not defaulted: `release_gate.py` runs this tool to READ a verdict, and
    # a check that rewrites two lane files as a side effect of being read can
    # retarget a live wave. The routing use passes them explicitly.
    ap.add_argument("--out-stale", default=None,
                    help="write the re-gate lane here (default: write nothing)")
    ap.add_argument("--out-true", default=None,
                    help="write the repair lane here (default: write nothing)")
    ap.add_argument("--json")
    args = ap.parse_args()

    from green_check import classify as green_classify

    bench = ROOT / args.benchmark_dir if not Path(args.benchmark_dir).is_absolute() \
        else Path(args.benchmark_dir)
    print("indexing history...", flush=True)
    hist = History(bench)
    if hist.top is None:
        # A corpus in no repository: `sources` hashes still decide the labels that
        # carry them, and every other label stands, because the only thing this tool
        # can do with a missing history is decline to discard a finding.
        print(f"# no git repository contains {bench}; a label no `sources` hash"
              f" decides stands, and the cell goes to repair", flush=True)

    rows: list[dict] = []
    pending: list[tuple[dict, str, str]] = []
    walked = 0
    for inst in sorted(p for p in bench.iterdir() if p.is_dir()):
        for backend in GATED:
            cell = inst / backend
            mp = cell / "meta.json"
            if not mp.is_file():
                continue
            walked += 1
            state, why = green_classify(cell, backend, inst.name)
            if str(state).upper() == "GREEN":
                continue
            try:
                meta = json.loads(mp.read_text())
            except (OSError, ValueError):
                rows.append({"instance_id": inst.name, "backend": backend,
                             "verdict": "UNREADABLE", "detail": "meta.json",
                             "why": why})
                continue
            row = {"instance_id": inst.name, "backend": backend, "why": why,
                   "failing": failing_audit_gates(meta)}
            out = plan_fail(cell, backend, meta, hist)
            if out[0] == "_blob":
                row["gate"] = out[3]
                pending.append((row, out[1], out[2]))
            else:
                row["verdict"], row["detail"] = out[0], out[1]
            rows.append(row)

    want = [s for _, before, after in pending for s in (before, after) if s]
    print(f"fetching {len(want)} historical spec blob(s)...", flush=True)
    blobs = hist.blobs(want)
    for row, before, after in pending:
        cell = bench / row["instance_id"] / row["backend"]
        # Both brackets have to say the spec moved: a disagreement means the current
        # bytes might be exactly what the gate judged, and then the label is live.
        seen = [(tag, blobs[spec]) for tag, spec in (("before", before),
                                                    ("after", after))
                if spec and spec in blobs]
        if not seen:
            row["verdict"] = "SPEC-IDENTICAL"
            row["detail"] = "the recorded blob is unreachable; the label stands"
            continue
        verdicts = [(tag, *decide(cell, row["backend"], src)) for tag, src in seen]
        transfers = [v for v in verdicts if v[1] in FAIL_TRANSFERS]
        if transfers:
            tag, kind, detail = transfers[0]
            row["verdict"] = kind
            row["detail"] = f"{row['gate']}: unchanged vs the {tag} blob ({detail})"
        else:
            tag, kind, detail = verdicts[0]
            row["verdict"] = kind
            row["detail"] = (f"{row['gate']}: {detail}"
                             + ("" if len(verdicts) > 1 else
                                "; not committed since the gate ran"))

    tally = Counter(r["verdict"] for r in rows)
    # Coverage, printed separately from the finding count, because `release_gate.py`
    # overturns a clean verdict from a check that "ran but looked at nothing" and can
    # only tell the two apart if the cells EXAMINED are reported independently.
    print(f"\n{walked} cell(s) examined")
    print(f"{len(rows)} not-green cell(s)")
    for kind, n in tally.most_common():
        mark = "  -> repair" if kind in FAIL_TRANSFERS else "  -> re-gate"
        if kind == "NO-AUDIT-FAIL":
            mark = "  -> mechanical"
        print(f"  {kind:16s} {n:4d}{mark}")

    stale = [r for r in rows if r["verdict"] not in FAIL_TRANSFERS
             and r["verdict"] != "NO-AUDIT-FAIL"]
    true = [r for r in rows if r["verdict"] in FAIL_TRANSFERS]
    for path, sel in ((args.out_stale, stale), (args.out_true, true)):
        if not path:
            continue
        p = ROOT / path if not Path(path).is_absolute() else Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("".join(f"{r['instance_id']}\t{r['backend']}\n"
                             for r in sorted(sel, key=lambda r: (r["instance_id"],
                                                                 r["backend"]))))
        print(f"wrote {len(sel)} -> {path}")
    # The finding count, with a digit, because a reader that greps for it needs
    # one: the heading below says the word "stale" and nothing else does, so a
    # gate keyed on that heading alone can never see a non-zero result.
    print(f"\n{len(stale)} stale fail label(s)")
    print("stale fail labels (a re-gate, not a repair):")
    for r in sorted(stale, key=lambda r: (r["instance_id"], r["backend"])):
        print(f"  {r['instance_id']}/{r['backend']:7s} {r['verdict']:15s}"
              f" {r['detail'][:95]}")
    if args.json:
        Path(args.json).write_text(json.dumps(rows, indent=1))
        print(f"wrote {args.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
