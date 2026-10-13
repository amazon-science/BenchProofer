#!/usr/bin/env python3
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Decide, per cell, whether its audit verdict still describes the spec on disk.

An audit role's conclusion is about the SPECIFICATION, not about the file that
carries it: the solution file also holds the implementation, and every attack an
audit runs rewrites that implementation on purpose. So the predicate is
`markers.spec_signature` -- the same identity `variant_scope.same_spec` uses to
enforce "same spec, different impl" -- and never the file's mtime or whole-file
hash, both of which move for edits the audit was already about.

Three outcomes. SPEC-IDENTICAL: the signature is unchanged, so every attack the
audit ran is still admissible and lands the same way. STRENGTHENED: every line of
difference is an ADDED obligation, and an obligation only narrows what verifies, so
"no wrong implementation verified" survives a fortiori; the opposite risk -- a spec
the patched repo no longer satisfies -- is measured on the current bytes by
G-VERIFY and the G-EQ/G-PBT positive controls rather than guessed at here. Anything
else is RE-AUDIT: no monotonicity argument covers a removed conjunct or a rewritten
postcondition.

The bytes the audit saw come from the gate's recorded `sources` hashes where they
exist, and otherwise from the git blob as of the last commit at or before the
audit's `checked_at` -- a commit clock that trails the edit it records, so the git
path errs toward reporting drift that was in fact already audited. The audit's own
time is the EARLIEST stamp across the audit roles, because a cell is only as fresh
as its stalest role.

WHICH REPOSITORY THAT BLOB COMES FROM: the one that CONTAINS the corpus, resolved
from the corpus path by `check_stamp_freshness.work_tree`, never this checkout. A
corpus reached through `--benchmark-dir` or `SBU_BENCHMARK_DIR` can sit anywhere on
disk and a published corpus is its own repository. When no repository holds it there
is no history to offer, and that is fail-closed: `sources` hashes still decide the
cells that carry them, and every other cell reads UNKNOWN, which is in NEEDS_AUDIT.
The `sources` path needs no repository at all, so a corpus whose records carry
digests is decidable from a tarball.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from check_stamp_freshness import work_tree  # noqa: E402
from swebench_unified.backends.registry import GATED_BACKENDS  # noqa: E402
from swebench_unified.corpus_root import default_benchmark_dir  # noqa: E402

# The release-gated backends under the short name this module exports;
# `stale_fail_triage.py` imports it from here. One binding, not a second list --
# the names live in the backend registry.
GATED = GATED_BACKENDS

# The roles whose conclusions this script is about. The static gates re-run cheaply
# on the current bytes, so their freshness is not in question and their stamps are
# deliberately excluded: including them would let a re-run static gate make a stale
# agent audit look fresh.
AUDIT_GATES = ("G-EQ", "G-PANEL-1", "G-PANEL-2", "G-PANEL-3")

# Verdicts that mean "nobody has audited these bytes". UNKNOWN and UNPARSEABLE
# are in here on purpose: they are failures to MEASURE freshness, and a release
# gate that treats "I could not tell" as "fine" is not a gate.
NEEDS_AUDIT = frozenset(
    {"RE-AUDIT", "NEVER-AUDITED", "UNKNOWN", "UNPARSEABLE", "NO-SPEC"})

# A line that can only make a spec harder to satisfy. Deliberately a closed
# list: anything not recognised here is treated as a substantive change, so a
# new kind of edit fails toward RE-AUDIT rather than being waved through.
OBLIGATION = re.compile(
    r"MustTerminate"                     # nagini's termination obligation
    r"|nagini_contracts\.obligations"    # and its import
    r"|^\s*(?:decreasing|termination_by)\b",   # lean/velvet equivalents
)

# Strengthenings that show up as a SUBSTITUTION rather than an addition, so the
# "nothing was removed" test cannot see them. Each pair is old -> new and must be a
# move to strictly stronger semantics; they are applied to the old text before the
# diff, which asks "is the new spec just the old one strengthened?". Partial
# correctness excuses a run that never returns and total correctness does not, so it
# carries the same monotonicity as an added obligation.
STRENGTHENING_REWRITES = (
    ("open PartialCorrectness", "open TotalCorrectness"),
    ('loom.semantics.termination "partial"',
     'loom.semantics.termination "total"'),
)

# A line that is NOTHING BUT a termination obligation. Anchored end to end on
# purpose: `Requires(And(MustTerminate(2), n > 0))` mentions the obligation but
# carries a real precondition alongside it, so matching loosely would wave
# through the deletion of a genuine conjunct as "just an obligation".
OBLIGATION_ONLY = re.compile(
    r"^\s*(?:Requires|Invariant)\(MustTerminate\(\d+\)\)\s*$"
    r"|^\s*from nagini_contracts\.obligations import MustTerminate\s*$"
)

# Verifier resource knobs. They bound the search the prover may do, not what is
# being proved, so adding or raising one cannot change which implementations satisfy
# the spec -- and a bound set too low makes the proof fail outright, which G-VERIFY
# reports on the current bytes.
INERT_PRAGMA = re.compile(r"^\s*set_option\s+max(?:Heartbeats|RecDepth)\b")


def _semantic_lines(sig: str, comment: str) -> list[str]:
    """The signature's lines with comment-only lines dropped.

    `spec_signature` keeps comments, because for `same_spec` any textual change is
    worth flagging. Here the question is what the spec MEANS, and no verifier reads a
    comment: keeping them reports the prose justifying an added obligation as a
    rewritten spec.
    """
    out = []
    for line in sig.splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith(comment):
            out.append(line)
    return out


def _spec_signature(src: str, backend: str) -> str | None:
    """`markers.spec_signature` for a backend name, or None if it will not parse.

    A file whose region markers are malformed has no spec view, and guessing one is
    worse than declining: those cells surface as UNPARSEABLE and are counted, not
    silently dropped.
    """
    from swebench_unified.backends.registry import get_backend
    from swebench_unified.markers import spec_signature
    try:
        return spec_signature(src, get_backend(backend).language)
    except Exception:
        return None


class History:
    """Commits that touched each path, newest first, from ONE pass over the log.

    `git rev-list -1 --before=T HEAD -- <path>` per cell walks the whole history once
    per cell and does not finish on a corpus this size. One `git log --name-only`
    pass builds the same information for every path at once, and "the commit as of
    time T" then costs a scan of one path's short list.

    Constructed from the DIRECTORY it is about -- the corpus root for a sweep, one
    cell for `verdict_for` -- and it resolves the repository that contains that
    directory itself. It is the only anchor in this module: the pathspec it logs,
    the keys `commit_at` is asked for and the process `blobs` reads objects out of
    all come from `self.top`, so a corpus outside this checkout is dated by its own
    repository instead of raising `ValueError` against this one, and the three
    questions cannot end up asked of two different trees.

    `top is None` means no repository holds the directory. Then nothing is dated and
    `name` answers None for every path, which `plan` turns into UNKNOWN -- a verdict
    in NEEDS_AUDIT, so an undatable cell needs an audit rather than passing.
    """

    def __init__(self, target: Path) -> None:
        target = Path(target)
        self.top = work_tree(target)
        self._by_path: dict[str, list[tuple[int, str]]] = {}
        if self.top is None:
            return
        try:
            pathspec = str(target.resolve().relative_to(self.top))
        except ValueError:              # `--show-toplevel` disowned its own argument
            self.top = None
            return
        out = subprocess.run(
            ["git", "log", "--pretty=format:@%ct %H", "--name-only", "--",
             pathspec],
            cwd=self.top, capture_output=True, text=True, timeout=900).stdout
        stamp, sha = 0, ""
        for line in out.splitlines():
            if line.startswith("@"):
                head, _, sha = line[1:].partition(" ")
                stamp = int(head)
            elif line and sha:
                self._by_path.setdefault(line, []).append((stamp, sha))

    def name(self, p: Path) -> str | None:
        """`p` as the repository holding the corpus names it, or None when none can.

        The spelling of the keys `commit_at` and `commit_after` are asked for, so it
        comes off the same object that built them: a caller naming a path against one
        repository and looking it up in another's index gets a MISS, and a miss reads
        as "never committed", which is a verdict rather than an error.
        """
        if self.top is None:
            return None
        try:
            return str(Path(p).resolve().relative_to(self.top))
        except ValueError:
            return None

    def commit_at(self, rel: str, when: dt.datetime) -> str | None:
        """The newest commit touching `rel` at or before `when`."""
        for stamp, sha in self._by_path.get(rel, ()):     # already newest-first
            if stamp <= when.timestamp():
                return sha
        return None

    def blobs(self, specs: list[str]) -> dict[str, str]:
        """`{"<sha>:<path>": content}` for many blobs in one `git cat-file` process.

        One process for the corpus, rather than a `git show` per cell. Missing objects
        come back as a `... missing` line and are absent from the result, which the
        caller reads as "no old bytes" -- the same reading a corpus in no repository
        gets, since there is then no process to read an object out of.
        """
        if not specs or self.top is None:
            return {}
        proc = subprocess.run(["git", "cat-file", "--batch"], cwd=self.top,
                              timeout=900, input="\n".join(specs).encode(),
                              capture_output=True)
        out, pos, found = proc.stdout, 0, {}
        for spec in specs:
            nl = out.find(b"\n", pos)
            if nl < 0:
                break
            header = out[pos:nl].decode(errors="replace").split()
            if len(header) < 3:                    # "<spec> missing"
                pos = nl + 1
                continue
            size = int(header[2])
            found[spec] = out[nl + 1:nl + 1 + size].decode(errors="replace")
            pos = nl + 1 + size + 1                # payload is followed by a newline
        return found


def _sources_verdict(cell: Path, gates: dict) -> str | None:
    """"PROVEN-FRESH" / "PROVEN-MOVED" from recorded hashes, or None if unusable.

    Every audit gate has to carry `sources` for this to answer: one gate's
    matching hashes say nothing about a sibling role that recorded none.
    """
    seen = 0
    for gate in AUDIT_GATES:
        entry = gates.get(gate)
        if not isinstance(entry, dict):
            continue
        src = entry.get("sources")
        if not isinstance(src, dict) or not src:
            return None
        seen += 1
        for name, digest in src.items():
            path = cell / name
            if (not path.is_file()
                    or hashlib.sha256(path.read_bytes()).hexdigest() != digest):
                return "PROVEN-MOVED"
    return "PROVEN-FRESH" if seen else None


def plan(cell: Path, backend: str, meta: dict,
         hist: History) -> tuple[str, str] | str:
    """Either a final verdict, or the `<sha>:<path>` of the old bytes it needs.

    Split out from `decide` only so every blob the run wants is fetched in one `git
    cat-file` batch instead of one process per cell.
    """
    gates = meta.get("gates") or {}
    if _sources_verdict(cell, gates) == "PROVEN-FRESH":
        return "SPEC-IDENTICAL", "sources hashes match"

    stamps = []
    for gate in AUDIT_GATES:
        entry = gates.get(gate)
        if isinstance(entry, dict) and entry.get("checked_at"):
            try:
                stamps.append(dt.datetime.fromisoformat(
                    str(entry["checked_at"]).replace("Z", "+00:00")))
            except ValueError:
                pass
    if not stamps:
        return "NEVER-AUDITED", "no audit gate carries a timestamp"

    from swebench_unified.backends.registry import get_backend
    spec_file = cell / get_backend(backend).language.solution_filename
    if not spec_file.is_file():
        return "NO-SPEC", f"{spec_file.name} missing"

    rel = hist.name(spec_file)
    if rel is None:
        # No repository holds this spec file, so there is no dated copy of the bytes
        # the audit read. UNKNOWN is in NEEDS_AUDIT, which is the fail-closed answer:
        # a cell git cannot date is re-audited, not passed.
        return "UNKNOWN", "no git repository contains the spec file"
    sha = hist.commit_at(rel, min(stamps))
    if sha is None:
        return "UNKNOWN", "no committed blob at or before the audit"
    return f"{sha}:{rel}"


def decide(cell: Path, backend: str, then_src: str) -> tuple[str, str]:
    """(verdict, detail) given the spec file as the audit saw it."""
    from swebench_unified.backends.registry import get_backend
    spec_file = cell / get_backend(backend).language.solution_filename
    now_src = spec_file.read_text(errors="replace")
    now_sig = _spec_signature(now_src, backend)
    then_sig = _spec_signature(then_src, backend)
    if now_sig is None or then_sig is None:
        return "UNPARSEABLE", "spec regions do not parse"
    if now_sig == then_sig:
        return "SPEC-IDENTICAL", "spec signature byte-identical"

    comment = get_backend(backend).language.comment_line
    new = set(_semantic_lines(now_sig, comment))
    old = set(_semantic_lines(then_sig, comment))
    if old == new:
        return "SPEC-IDENTICAL", "only comments changed; the spec is unchanged"

    # Ask the question as "is the new spec the old one strengthened?", so a
    # strengthening spelled as a substitution is not read as a rewrite.
    for before, after in STRENGTHENING_REWRITES:
        old = {ln.replace(before, after) for ln in old}
    if old == new:
        return "STRENGTHENED", "partial correctness replaced by total"

    def inert(line: str) -> bool:
        """Changing this line cannot change which implementations satisfy the spec.

        A re-tuned obligation LEVEL counts: `MustTerminate(3)` -> `MustTerminate(6)`
        reads as a deletion, but the obligation is present either way and the level
        only orders which obligated method may call which. An inconsistent ordering
        makes the proof fail, which G-VERIFY measures on the current bytes.
        """
        return bool(OBLIGATION_ONLY.match(line) or INERT_PRAGMA.match(line))

    removed = sorted(ln for ln in old - new if not inert(ln))
    added = sorted(new - old)
    if removed:
        return "RE-AUDIT", (f"{len(removed)} spec line(s) removed or rewritten,"
                            f" e.g. {removed[0].strip()[:70]!r}")
    unexplained = [ln for ln in added
                   if not OBLIGATION.search(ln) and not inert(ln)]
    if unexplained:
        return "RE-AUDIT", (f"{len(unexplained)} added spec line(s) are not"
                            f" obligations, e.g. {unexplained[0].strip()[:70]!r}")
    return "STRENGTHENED", f"{len(added)} obligation line(s) added, none weakened"


def verdict_for(cell: Path, backend: str) -> tuple[str, str]:
    """(verdict, detail) for ONE cell, for callers outside the corpus sweep.

    `main` batches history and blobs across the corpus because it has to; a caller
    holding a single cell open gets the same answer from the same code, since one
    `git log` scoped to that cell plus one `cat-file` is cheap. It exists so that
    caller does not re-derive audit freshness itself: `check_stamp_freshness` reports
    an audit gate's digest mismatch as `deferred` -- deferred TO THIS FUNCTION, since
    a changed spec file does not by itself mean a stale audit.
    """
    try:
        meta = json.loads((cell / "meta.json").read_text())
    except (OSError, ValueError):
        return "UNKNOWN", "meta.json unreadable"
    # Resolved first: `History` resolves the repository holding this cell from the
    # path it is given, so a caller holding a path relative to the cwd would have it
    # looked up in whatever repository the cwd happens to sit in.
    cell = Path(cell).resolve()
    hist = History(cell)
    got = plan(cell, backend, meta, hist)
    if isinstance(got, tuple):
        return got
    then_src = hist.blobs([got]).get(got)
    if then_src is None:
        return "UNKNOWN", "the recorded blob is no longer reachable"
    return decide(cell, backend, then_src)


def _argparser() -> argparse.ArgumentParser:
    """Its own function so a test can assert the defaults without a corpus walk.

    Two defaults matter. `--out`: a release check must not write anywhere the caller
    did not name. `--benchmark-dir`: the corpus the environment names, never a fixed
    one, or the check reports about a tree the caller did not ask about.
    """
    ap = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    ap.add_argument("--benchmark-dir", default=default_benchmark_dir())
    # No default path. The report is the stdout table plus the per-cell lines the
    # release gate reads (`release_gate._reaudit_verdict` parses the count and the
    # names, never a file); a lane file is what a fleet driver wants, and a driver can
    # name where it goes.
    ap.add_argument("--out", default="",
                    help="also write a lane file of the cells whose audit no"
                         " longer applies, '<instance_id>\\t<backend>' per line")
    ap.add_argument("--green-only", action="store_true",
                    help="skip cells that are already not green (they have"
                         " their own lane)")
    ap.add_argument("--show", type=int, default=25)
    return ap


def main() -> int:
    args = _argparser().parse_args()

    from green_check import classify as green_classify

    bench = ROOT / args.benchmark_dir
    print("indexing history...", flush=True)
    hist = History(bench)
    if hist.top is None:
        # Named rather than left implicit in a column of UNKNOWNs: the corpus is
        # readable and every cell will be judged, but the only evidence left is the
        # `sources` hashes the records carry themselves.
        print(f"# no git repository contains {bench}; only records carrying `sources`"
              f" hashes can be decided, the rest read UNKNOWN", flush=True)

    tally: Counter = Counter()
    reaudit: list[tuple[str, str, str]] = []
    pending: list[tuple[Path, str, str, bool]] = []      # cell, backend, spec, green
    for inst in sorted(p for p in bench.iterdir() if p.is_dir()):
        for backend in GATED:
            cell = inst / backend
            meta_path = cell / "meta.json"
            if not meta_path.is_file():
                continue
            # `green_check.classify` is the only authority for greenness; it returns
            # `(verdict, why)` with verdict one of GREEN / NOTGREEN / NORESULT.
            state, _why = green_classify(cell, backend, inst.name)
            green = state == "GREEN"
            if args.green_only and not green:
                continue
            try:
                meta = json.loads(meta_path.read_text())
            except (OSError, ValueError):
                tally[("unreadable", green)] += 1
                continue
            outcome = plan(cell, backend, meta, hist)
            if isinstance(outcome, tuple):
                kind, detail = outcome
                tally[(kind, green)] += 1
                if kind in NEEDS_AUDIT:
                    reaudit.append((inst.name, backend, detail))
            else:
                pending.append((cell, backend, outcome, green))

    print(f"fetching {len(pending)} historical blobs...", flush=True)
    blobs = hist.blobs([spec for _, _, spec, _ in pending])
    for cell, backend, spec, green in pending:
        then_src = blobs.get(spec)
        if then_src is None:
            kind, detail = "UNKNOWN", "the recorded blob is no longer reachable"
        else:
            kind, detail = decide(cell, backend, then_src)
        tally[(kind, green)] += 1
        if kind in NEEDS_AUDIT:
            reaudit.append((cell.parent.name, backend, detail))

    print(f"{'verdict':16s} {'green':>6s} {'not-green':>10s}")
    kinds = sorted({k for k, _ in tally})
    for kind in kinds:
        print(f"{kind:16s} {tally[(kind, True)]:6d} {tally[(kind, False)]:10d}")
    print(f"{'TOTAL':16s} {sum(v for (_, g), v in tally.items() if g):6d} "
          f"{sum(v for (_, g), v in tally.items() if not g):10d}")

    where = "stdout"
    if args.out:
        out = ROOT / args.out          # an absolute --out is used as given
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text("".join(f"{i}\t{b}\n" for i, b, _ in sorted(reaudit)))
        try:
            where = str(out.relative_to(ROOT))
        except ValueError:
            where = str(out)     # an --out outside the repo; report it as given
    # One phrasing whether or not a file was written: this line is the verdict
    # release_gate reads, and the lines under it are the names it quotes.
    print(f"\n{len(reaudit)} cell(s) need a fresh audit -> {where}")
    for i, b, detail in sorted(reaudit)[:args.show]:
        print(f"  {i}/{b}: {detail}")
    if len(reaudit) > args.show:
        print(f"  ... and {len(reaudit) - args.show} more"
              f" (raise --show, or --out FILE for the whole lane)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
