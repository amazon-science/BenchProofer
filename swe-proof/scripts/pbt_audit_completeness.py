#!/usr/bin/env python
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Which cells still need a PBT audit under the CURRENT audit prompt?

`pbt_certify.py` asks whether a recorded G-PBT pass was judged by a harness at
least as strict as HEAD; that is the gate's side. This asks the other side: the
audit prompt also gained attacks while the corpus was being built, and a
`pbt_audit` payload attests to the prompt that produced it, so a cell audited
before an attack existed carries a verdict nobody would grant today.

The reasons a cell is listed, with the non-obvious reading of each:

  never-audited, audit-has-no-clock, audited-before-forgery-prompt -- no
      `agent_verdict`, or its clock predates --since. That clock is
      `gates["G-PBT"]["checked_at"]`, not `pbt_audit["audited_at"]` (a wave tag,
      not a time); the gate's stamp bounds the audit from above because the audit
      fleet re-gates each cell right after auditing it.
  bprime-required-but-absent -- the prompt requires the forgery test only for a
      case whose `gold_signature` is not a plain evaluation, so a battery whose
      every passing reject is `decided` tier legitimately records none, and
      demanding one anyway queues a re-audit with nothing to find.
  lanes-unrecorded, no-admissibility-lane -- `data.lanes` carries no
      admissibility case, or predates the field. The gate is only advisory there
      (a vacuous precondition is an omission an author must ARGUE, not something
      a gate adjudicates), which is why the question belongs to an auditor.
  weak-gold-evidence -- a passing reject rests on a weak signature tier (see
      pbt_signature_tiers.py) that no audit has settled with builds. Read per
      CASE, so a payload covering nine of ten weak cases leaves the tenth open,
      and clearable, because an auditor who ran the builds records them against
      the case id.

Exit 0 iff no cell in scope needs an audit.

Usage:
  SBU_BENCHMARK_DIR=<corpus> python scripts/pbt_audit_completeness.py \
      [--backend velvet] [--since <iso8601>] [--worklist-dir DIR] [--json OUT]
"""
from __future__ import annotations

import argparse
import collections
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from swebench_unified.backends.registry import GATED_BACKENDS  # noqa: E402

# Tiers that a human still has to look at; see pbt_signature_tiers.py for what
# each one means and why `reduced` is NOT among them.
WEAK_TIERS = frozenset({"shape", "stuck", "other", "unrecorded"})

# When the forgery test became mandatory in prompts/shared/pbt_audit.md. A payload
# written before this cannot contain the evidence whatever it says, so the cutoff
# is what makes "attested under the CURRENT prompt" decidable. Move it with the
# prompt, or override per run with --since.
FORGERY_PROMPT_LANDED = "2026-08-13T00:47:00+00:00"


def audit_clock(gate: dict) -> datetime | None:
    """When this cell's audit ran, as an upper bound: the gate's `checked_at`, for
    the reason the module docstring gives."""
    try:
        t = datetime.fromisoformat(gate.get("checked_at") or "")
    except ValueError:
        return None
    return t if t.tzinfo else t.replace(tzinfo=timezone.utc)


def records_forgery(e: dict) -> bool:
    """Whether one `witness_evidence` entry records the flipped-claim experiment.

    Two spellings, because the payloads carry two. The canonical one is a single
    `forgery_exit` (or `forgery_error` when the build did not get that far); the
    other splits it into `clean_forgery_ref_exit` beside `clean_forgery_rival_exit`,
    which a cell needs when the naive flipped claim verifies vacuously and only the
    truncated CLEAN forgery separates the two sides -- richer than the canonical
    shape, not poorer.

    One function, because both the coverage set below and the forgery requirement in
    `needs_audit` ask this question: two call sites disagreeing over a key name would
    report the cell that ran the sharper experiment as one that ran none, and go on
    asking it for the experiment forever.
    """
    return any(k in e for k in ("forgery_exit", "forgery_error",
                                "clean_forgery_ref_exit",
                                "clean_forgery_rival_exit"))


def decided_by_builds(audit: dict) -> set[str]:
    """Case ids whose gold-side evidence an auditor settled with real builds.

    The shape the audit prompt asks for: one `witness_evidence` entry per case id,
    holding the witness's own exits against gold and the rival plus the FORGERY
    result -- the flipped claim, which `pbt_signature_tiers` names as the only thing
    that separates a hollow rejection from a real one. `records_forgery` decides
    which keys count as that result.

    Presence, not content. The recorded exits are an agent's prose, and parsing them
    would be a regex adjudicating exactly what the tier docstring says a regex cannot.
    What this decides is whether the experiment was RUN AND RECORDED for the case;
    whether its outcome was read correctly is the audit's own judgement. `gold_exit` is
    required alongside, so an entry naming a forgery result without the witness's own
    gold-side result attests nothing: one number is not a comparison.

    `case` is read as a synonym for `id` because the payloads use both spellings and no
    single entry carries both, so there is nothing to disambiguate; refusing the second
    would report an audit that did record its builds as one that recorded none, and ask
    it again on every pass.
    """
    out: set[str] = set()
    for e in audit.get("witness_evidence") or []:
        if not isinstance(e, dict) or "gold_exit" not in e:
            continue
        if not records_forgery(e):
            continue
        cid = e.get("id") or e.get("case")
        if isinstance(cid, str) and cid:
            out.add(cid)
    return out


def needs_audit(blob: dict, since: datetime | None) -> list[str]:
    """Every reason this cell is not attested under the current prompt."""
    from pbt_signature_tiers import classify  # noqa: PLC0415  (sibling script)

    gate = (blob.get("gates") or {}).get("G-PBT") or {}
    data = gate.get("data") or {}
    audit = blob.get("pbt_audit") or {}
    cases = data.get("cases") or []
    reasons: list[str] = []

    # Whether this record reports gold-side signatures AT ALL. The forgery test and
    # the weak-tier screen are both questions about the SHAPE of the gold-side
    # evidence -- did the kernel evaluate the claim, or did it get stuck -- and a
    # backend whose verifier discharges the postcondition itself never emits such a
    # signature. `classify("")` is `unrecorded`, a WEAK tier, so applying those two
    # reasons where no signature exists would put every cell of that backend on the
    # worklist for evidence its verifier cannot produce.
    #
    # Read off the DATA rather than the backend name, so a backend that starts
    # recording signatures is covered by that fact alone and one that lost them is
    # not quietly excused: no signature anywhere in the lane is itself reported, as
    # `lanes-unrecorded` or by pbt_certify's harness-age check.
    rejects = [c for c in cases if c.get("expect") == "reject" and c.get("ok")]
    signature_bearing = any(c.get("gold_signature") for c in rejects)

    # Whether an audit under the CURRENT prompt exists at all. The weak-tier reason
    # below is discharged by that audit's recorded builds, so it has to know: a
    # payload from before the forgery test existed cannot contain the experiment
    # however complete it looks -- which is what the clock is for.
    audited_under_prompt = False
    if not audit.get("agent_verdict"):
        reasons.append("never-audited")
    else:
        clock = audit_clock(gate)
        if clock is None:
            reasons.append("audit-has-no-clock")
        elif since and clock < since:
            reasons.append("audited-before-forgery-prompt")
        else:
            audited_under_prompt = True
            if signature_bearing:
                # Required only where the gold-side evidence is not a plain
                # evaluation: anything outside `decided` triggers the forgery test.
                tiers = {classify(c.get("gold_signature") or "") for c in rejects}
                evidence = audit.get("witness_evidence") or []
                has_forgery = any(isinstance(e, dict) and records_forgery(e)
                                  for e in evidence)
                if tiers - {"decided"} and not has_forgery:
                    reasons.append("bprime-required-but-absent")

    lanes = data.get("lanes")
    if lanes is None:
        reasons.append("lanes-unrecorded")
    elif not lanes.get("admissibility"):
        reasons.append("no-admissibility-lane")

    if signature_bearing:
        weak = [c for c in rejects
                if classify(c.get("gold_signature") or "") in WEAK_TIERS]
        # An id-less case can never be attested, and that is the safe direction:
        # nothing in the payload can be tied to it.
        settled = decided_by_builds(audit) if audited_under_prompt else set()
        if any(c.get("id") not in settled for c in weak):
            reasons.append("weak-gold-evidence")
    return reasons


def main() -> int:
    ap = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    ap.add_argument("--backend", choices=GATED_BACKENDS, action="append",
                    help="repeatable; default every release-gated backend")
    ap.add_argument("--since", default=FORGERY_PROMPT_LANDED,
                    help="ISO time the current prompt landed; '' to disable")
    ap.add_argument("--worklist-dir",
                    help="write <dir>/wl_audit_<backend>.txt, one iid per line")
    ap.add_argument("--json", help="write the per-cell reasons as JSON")
    args = ap.parse_args()

    from swebench_unified import paths

    corpus = paths.TASKS_ROOT
    if not corpus.is_dir():
        print(f"no corpus at {corpus} -- set SBU_BENCHMARK_DIR", file=sys.stderr)
        return 2
    since = (datetime.fromisoformat(args.since) if args.since else None)
    backends = args.backend or list(GATED_BACKENDS)

    per_cell: dict[str, list[str]] = {}
    need: dict[str, list[str]] = {b: [] for b in backends}
    counts: dict[str, collections.Counter] = {
        b: collections.Counter() for b in backends}
    total = collections.Counter()
    payloads = collections.Counter()

    for d in sorted(p for p in corpus.iterdir() if p.is_dir()):
        for b in backends:
            m = d / b / "meta.json"
            if not m.exists():
                continue
            total[b] += 1
            try:
                blob = json.loads(m.read_text())
            except (OSError, json.JSONDecodeError):
                reasons = ["unreadable-meta"]
            else:
                if isinstance(blob.get("pbt_audit"), dict):
                    payloads[b] += 1
                reasons = needs_audit(blob, since)
            per_cell[f"{b}/{d.name}"] = reasons
            if reasons:
                need[b].append(d.name)
                for r in reasons:
                    counts[b][r] += 1

    # A backend where NOT ONE cell carries a `pbt_audit` payload is not a corpus of
    # un-audited cells; it is a backend this prompt does not apply to. The payload is
    # witness-shaped throughout -- `witness_evidence`, `witnesses_rebuilt`, and the
    # forgery test itself, which forges a witness -- and a verifier that discharges
    # the postcondition itself produces no witness to forge.
    #
    # Reported rather than silently omitted, so a reader of a clean run need not know a
    # third backend exists to notice it was missing. It does not fail the run, because
    # "this question does not apply" is not a defect, and the cells are not left
    # unexamined: their audit attestation is decided by `audit_freshness.py` and the
    # G-PANEL-* role records, both backend-agnostic and both run by the release gate.
    not_applicable = [b for b in backends if total[b] and not payloads[b]]
    for b in backends:
        if b in not_applicable:
            print(f"{b}: not applicable over {total[b]} cell(s) -- no cell "
                  f"carries a pbt_audit payload, because this backend's "
                  f"rejections have no witness to forge; its audit attestation "
                  f"is covered by audit_freshness.py and the G-PANEL-* records")
            print()
            continue
        print(f"{b}: {len(need[b])} of {total[b]} need an audit "
              f"under the current prompt")
        for r, n in counts[b].most_common():
            print(f"    {n:5}  {r}")
        if args.worklist_dir:
            dest = Path(args.worklist_dir) / f"wl_audit_{b}.txt"
            # The caller names a directory, so create it: failing to write here
            # would throw away a whole corpus walk along with the worklist.
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text("\n".join(sorted(need[b]))
                            + ("\n" if need[b] else ""))
            print(f"    -> {dest}")
        print()
    for b in not_applicable:
        need[b] = []
        per_cell = {k: v for k, v in per_cell.items() if not k.startswith(f"{b}/")}

    if args.json:
        Path(args.json).write_text(json.dumps(per_cell, indent=1, sort_keys=True))
        print(f"-> {args.json}")
    return 0 if not any(need[b] for b in backends) else 1


if __name__ == "__main__":
    sys.exit(main())
