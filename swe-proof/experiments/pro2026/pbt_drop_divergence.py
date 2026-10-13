#!/usr/bin/env python
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Remove out-of-scope divergence rivals from velvet/lean PBT batteries.

## Why

Velvet cells that declare `set_option loom.semantics.termination "partial"` are
making a deliberate, G-HYGIENE-checked statement that their proof obligation is
PARTIAL correctness. A rival that loops forever therefore verifies *by the declared
semantics*, so `expect="reject"` fails and the cell records SPEC-TOO-WEAK. That is
not a defect in the cell's postcondition — it restates the `set_option` line, and
it would flag all 135 `partial` pro velvet cells identically. The 500-bundle
verified round passed G-PBT 500/500 without ever counting divergence as a finding.

Measured 2026-08-17: 9 of the first 12 velvet SPEC-TOO-WEAK verdicts were
divergence-only, all 9 on `partial` cells. `prompts/shared/pbt_port.md` now rules
the class out, but batteries authored before that fix still carry the cases. This
script removes them from the already-written manifests.

## How, and why not a regex

Each case is a dict literal inside the `SPEC_TESTS` list of a hand-authored Python
module with per-case comments and shared `_swap` variables. The removal is done by
parsing the module with `ast`, locating the `SPEC_TESTS` assignment, and deleting
the exact line span of each matching element — never by pattern-matching source
text, which would mangle the surrounding prose or clip a neighbouring case.

The `_RIVAL_*` module variable that built the dropped case is left in place on
purpose: it still runs its `_swap` exact-once assertion at import, which is the
manifest's drift detector against an edited solution file.

Nagini is refused outright: Viper's `MustTerminate` is a real per-function
obligation a spec can carry or omit (50 of 238 pro nagini specs carry it), so
there a divergence rival IS a live class.

Usage:
  python3 experiments/pro2026/pbt_drop_divergence.py --backends velvet lean [--apply]
  python3 experiments/pro2026/pbt_drop_divergence.py --cells cells.json --apply

TRACKED ON PURPOSE, at this path: 13 shipped `properties.py` batteries cite it as
what removed their divergence cases, so relocating it dangles a citation in a
frozen artifact. See the same note in `pbt_verify.py`; the rest of this lane's
drivers were wave scaffolding and are not in a clone.
"""
from __future__ import annotations

import argparse
import ast
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

os.environ.setdefault("SBU_BENCHMARK", "swe_bench_pro_python")
os.environ.setdefault("SBU_BENCHMARK_DIR", "benchmark-pro")

PRO = ROOT / "benchmark-pro"

# Case-id markers for the divergence/non-termination class.
#
# Matched on HYPHEN-DELIMITED SEGMENTS, not as substrings. A substring regex is
# wrong here and was caught in dry-run: `hang` matches "c-hang-es", so
# `rival-no-changes` and `rival-invert-change-flag` — both legitimate value-level
# rivals about a `changed` flag — were flagged as divergence. Segment matching
# keeps `rival-hang-on-deferred` and rejects `rival-no-changes`.
#
# Deliberately narrow: "loop" alone is NOT a marker, since a loop-bound
# off-by-one rival is a value-level attack, not a divergence one.
_SEGMENT_PREFIXES = ("diverg", "nonterm", "nonprogress", "infinit", "forever",
                     "hang", "spin")
_PHRASES = ("never-advances", "non-term", "non-progress", "vacuous-exit")


def is_divergence(case_id: str) -> bool:
    cid = case_id.lower()
    if any(p in cid for p in _PHRASES):
        return True
    return any(seg.startswith(_SEGMENT_PREFIXES)
               for seg in cid.split("-"))

NOTE = """
# ---------------------------------------------------------------------------
# LANE DISPOSITION (2026-08-17): divergence / non-termination rivals removed.
#
# This backend's file declares its termination semantics with a `set_option`
# (velvet) / is total by construction (lean), so a rival that loops forever
# verifies BY THE DECLARED SEMANTICS. Recording that as SPEC-TOO-WEAK restates
# the declaration instead of exposing a defect in this postcondition, and would
# flag every `termination "partial"` cell identically. Measured: 9 of the first
# 12 velvet SPEC-TOO-WEAK verdicts were divergence-only, all 9 on `partial`
# cells. The class is ruled out for velvet/lean in prompts/shared/pbt_port.md;
# nagini keeps it, because Viper's `MustTerminate` is a real per-function
# obligation a spec can carry or omit.
#
# Cases removed from SPEC_TESTS by experiments/pro2026/pbt_drop_divergence.py:
{ids}
#
# Their `_swap`-built module variables are intentionally retained: the exact-once
# assertion is this manifest's drift detector against an edited solution file.
# ---------------------------------------------------------------------------
"""


def case_spans(src: str) -> list[tuple[str, int, int]]:
    """(case_id, start_line, end_line) for every element of SPEC_TESTS."""
    tree = ast.parse(src)
    out: list[tuple[str, int, int]] = []
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        if not any(isinstance(t, ast.Name) and t.id == "SPEC_TESTS"
                   for t in node.targets):
            continue
        if not isinstance(node.value, ast.List):
            raise ValueError("SPEC_TESTS is not a list literal")
        for el in node.value.elts:
            cid = None
            if isinstance(el, ast.Dict):
                for k, v in zip(el.keys, el.values):
                    if (isinstance(k, ast.Constant) and k.value == "id"
                            and isinstance(v, ast.Constant)):
                        cid = v.value
            if cid is None:
                raise ValueError(f"SPEC_TESTS element at line {el.lineno} has no "
                                 f"literal 'id' — refusing to edit by guesswork")
            out.append((cid, el.lineno, el.end_lineno))
    return out


def failing_case_ids(bundle: Path) -> set[str] | None:
    """Case ids that did NOT meet their `expect` in the last recorded G-PBT run,
    or None if this cell has no recorded verdict yet."""
    mp = bundle / "meta.json"
    try:
        data = (json.loads(mp.read_text()).get("gates", {})
                .get("G-PBT", {}).get("data") or {})
    except (OSError, json.JSONDecodeError):
        return None
    cases = data.get("cases")
    if not cases:
        return None
    return {c["id"] for c in cases if not c.get("ok")}


def repair(path: Path, apply: bool, only_failing: bool = True,
           extra_cases: frozenset[str] = frozenset()) -> tuple[list[str], str | None]:
    src = path.read_text()
    spans = case_spans(src)
    # `extra_cases` names cases whose MECHANISM is divergence but whose id carries
    # no divergence keyword — e.g. `rival-nondelivery-loop`, whose own refinement
    # reads "a loop that cannot exit (`while true`) precedes an otherwise CORRECT
    # gold assembly ... only DELIVERY is missing". These must be named explicitly by
    # the operator after reading the refinement, never inferred: "loop" alone is not
    # a divergence marker (a loop-bound off-by-one is a value-level attack).
    drop = [(cid, lo, hi) for cid, lo, hi in spans
            if is_divergence(cid) or cid in extra_cases]
    if only_failing and drop:
        # A divergence rival that was correctly REJECTED is a legitimate passing
        # case — on a `termination "total"` cell it is even a good one. Only the
        # ones that actually verified against expect="reject" are the out-of-scope
        # artifacts, so strip nothing else. Without a recorded verdict we cannot
        # tell, so we leave the cell alone rather than guess.
        failing = failing_case_ids(path.parent)
        if failing is None:
            return [cid for cid, _, _ in drop], "SKIPPED: no recorded G-PBT verdict yet"
        drop = [t for t in drop if t[0] in failing]
    if not drop:
        return [], None
    if len(drop) == len(spans):
        # Removing every case would leave an empty battery, which G-PBT records as
        # `pbt_empty_manifest` (a skip) -> green_check treats it as not-green.
        # Refuse rather than silently produce a hollow cell.
        return [cid for cid, _, _ in drop], "REFUSED: would empty SPEC_TESTS"
    lines = src.splitlines(keepends=True)
    kill = set()
    for _, lo, hi in drop:
        # ast line numbers are 1-based and inclusive
        for n in range(lo, hi + 1):
            kill.add(n)
        # also absorb a trailing comment-only run immediately above the case,
        # which is that case's explanatory prose
        n = lo - 1
        while n >= 1 and lines[n - 1].lstrip().startswith("#"):
            kill.add(n)
            n -= 1
    kept = [l for i, l in enumerate(lines, start=1) if i not in kill]
    ids = "\n".join(f"#   - {cid}" for cid, _, _ in drop)
    new = "".join(kept).rstrip("\n") + "\n" + NOTE.format(ids=ids)
    if apply:
        path.write_text(new)
    return [cid for cid, _, _ in drop], None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--backends", nargs="*", default=["velvet", "lean"])
    ap.add_argument("--cells", type=Path, default=None)
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--extra-cases", nargs="*", default=[],
                    help="case ids whose MECHANISM is divergence but whose id "
                         "carries no keyword (name them after reading the "
                         "refinement; never inferred)")
    ap.add_argument("--all-divergence", action="store_true",
                    help="strip divergence cases even where they were correctly "
                         "REJECTED (default: only those that actually verified)")
    args = ap.parse_args()

    if "nagini" in args.backends:
        print("REFUSING nagini: MustTerminate is a real per-function obligation "
              "there, so a divergence rival is a live uniqueness class.",
              file=sys.stderr)
        return 2

    targets: list[Path] = []
    if args.cells:
        for item in json.loads(args.cells.read_text()):
            iid, bk = (item["iid"], item["backend"]) if isinstance(item, dict) \
                else (item[1], item[0])
            if bk in args.backends:
                targets.append(PRO / iid / bk / "properties.py")
    else:
        for bk in args.backends:
            targets += sorted(PRO.glob(f"*/{bk}/properties.py"))

    n_cells = n_cases = 0
    problems: list[str] = []
    for p in targets:
        if not p.is_file():
            continue
        try:
            dropped, err = repair(p, args.apply,
                                  only_failing=not args.all_divergence,
                                  extra_cases=frozenset(args.extra_cases))
        except Exception as e:
            problems.append(f"{p.parents[1].name}/{p.parents[0].name}: "
                            f"{type(e).__name__}: {e}")
            continue
        if err:
            problems.append(f"{p.parents[1].name}/{p.parents[0].name}: {err} "
                            f"({dropped})")
            continue
        if dropped:
            n_cells += 1
            n_cases += len(dropped)
            print(f"  {p.parents[0].name:7} {p.parents[1].name[:52]:52} "
                  f"-{len(dropped)} {dropped}")
    verb = "removed" if args.apply else "would remove"
    print(f"\n{verb} {n_cases} divergence case(s) from {n_cells} cell(s)")
    if problems:
        print(f"\n{len(problems)} problem(s):")
        for x in problems:
            print(f"  {x}")
    if not args.apply:
        print("\n(dry run — pass --apply to write)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
