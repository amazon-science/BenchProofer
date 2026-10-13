#!/usr/bin/env python
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Corpus-wide static attacks on ported G-PBT batteries. No builds.

The audit agents attack one cell each with real `lake` builds, which is the only
way to answer "is this rival actually wrong". But some defect classes are
STRUCTURAL: they can be decided by reading every manifest at once, and a class
that is absent corpus-wide is worth establishing cheaply rather than hoping that
every independent auditor happens to look. This runs in seconds and needs no
verifier, so it can run while the build semaphore is saturated.

Each check below is a forgery that would pass the real gate:

  gold-verbatim     an expect="verify" case whose module IS the frozen solution
                    byte-for-byte. It verifies honestly and tests nothing about
                    the impl. NOT automatically a defect: an admissibility case
                    whose PASS SOURCE is "the frozen impl discharges the
                    postcondition, so the spec is satisfiable" is a real
                    obligation, and the frozen impl is the honest witness for
                    it (`admiss-gold-*`), so this is reported, not failed.

  duplicate-module  two cases sharing one module. Also not automatically a
                    defect -- one rival with two witnesses at different input
                    points is MORE evidence -- but a duplicate whose witnesses
                    also match is a padded battery.

  proof-only-reject an expect="reject" case whose IMPL REGION equals gold's, so
                    the only difference is the proof script. This one is a real
                    defect: the case rejects because the tactic script was
                    changed, and attributes that to the spec.

  unanchored        a reject witness that never names the spec predicate
                    (lean: `problem_spec_*`; velvet: a declared `method`). Such a
                    witness can only be about the IMPL, so it proves the rival
                    differs from gold rather than that it violates the spec --
                    and it passes both halves of the gate's discrimination check.

A healthy corpus reports zero proof-only-reject and zero unanchored witnesses.
The other two checks are expected to fire a little: the gold-verbatim hits should
all be `admiss-*` cases (matching the nagini convention), and any duplicate
module should carry two distinct witnesses.

Usage:
  SBU_BENCHMARK=swe_bench_verified SBU_BENCHMARK_DIR=benchmark-verified \
    python scripts/pbt_static_audit.py [--backend velvet|lean|all] [--json OUT]
"""
from __future__ import annotations

import argparse
import collections
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from swebench_unified.backends import get_backend  # noqa: E402
from swebench_unified.corpus_root import default_benchmark_dir  # noqa: E402
from swebench_unified.gates.base import Bundle  # noqa: E402
from swebench_unified.gates.pbt import load_manifest  # noqa: E402
from swebench_unified.pbt_witness import _strip_lean_comments  # noqa: E402
from swebench_unified.variant_scope import parse_regions  # noqa: E402

# `parse_regions` gives (start, end) LINE spans, end exclusive of the marker.
_SPEC_PRED = re.compile(r"\b(problem_spec_[A-Za-z0-9_']+)")
_METHOD = re.compile(r"^\s*method\s+([A-Za-z0-9_']+)", re.M)


def impl_text(src: str, tables) -> str:
    """Every impl region's body, concatenated. "" when there are no regions."""
    spans = parse_regions(src, tables).get("impl") or []
    lines = src.splitlines()
    return "\n".join("\n".join(lines[lo:hi - 1]) for lo, hi in spans)


def anchors(src: str, backend: str) -> set[str]:
    """The names a witness must reach for to be about the SPEC at all."""
    if backend == "lean":
        return set(_SPEC_PRED.findall(src))
    return set(_METHOD.findall(src))


def audit_cell(iid: str, backend: str) -> list[dict]:
    bk = get_backend(backend)
    bundle = Bundle(instance_id=iid, backend=bk)
    src = bundle.solution_src()
    tests = load_manifest(bundle)
    if not tests or not src:
        return []
    out: list[dict] = []
    gold_impl = impl_text(src, bk.language).strip()
    names = anchors(src, backend)
    seen: dict[str, str] = {}
    for case in tests:
        if not isinstance(case, dict):
            continue
        cid = str(case.get("id", "?"))
        module = case.get("module")
        if not isinstance(module, str):
            continue
        row = {"iid": iid, "backend": backend, "case": cid,
               "expect": case.get("expect")}
        if module.strip() == src.strip():
            out.append({**row, "check": "gold-verbatim",
                        "detail": "module is the frozen solution byte-for-byte"})
        prior = seen.setdefault(module.strip(), cid)
        if prior != cid:
            same_w = (case.get("witness") ==
                      next((c.get("witness") for c in tests
                            if isinstance(c, dict) and c.get("id") == prior), None))
            out.append({**row, "check": "duplicate-module",
                        "detail": f"shares its module with {prior!r}"
                                  + ("; witnesses identical too" if same_w else
                                     "; witnesses differ (more evidence, not less)")})
        if case.get("expect") != "reject":
            continue
        if gold_impl and impl_text(module, bk.language).strip() == gold_impl:
            out.append({**row, "check": "proof-only-reject",
                        "detail": "impl region equals gold's, so only the proof "
                                  "differs: the rejection is a tactic gap"})
        witness = case.get("witness")
        if isinstance(witness, str) and names:
            w = _strip_lean_comments(witness)
            if not any(re.search(rf"\b{re.escape(n)}", w) for n in names):
                out.append({**row, "check": "unanchored-witness",
                            "detail": "names no spec predicate/method, so it is "
                                      "about the impl rather than the spec"})
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--backend", default="all",
                    choices=["velvet", "lean", "nagini", "all"])
    ap.add_argument("--benchmark-dir", default=default_benchmark_dir())
    ap.add_argument("--json", default="")
    args = ap.parse_args()

    backends = (["velvet", "lean"] if args.backend == "all"
                else [args.backend])
    root = ROOT / args.benchmark_dir
    findings, stats = [], collections.Counter()
    for backend in backends:
        for p in sorted(root.glob(f"*/{backend}/properties.py")):
            iid = p.parents[1].name
            stats[f"{backend}-batteries"] += 1
            try:
                rows = audit_cell(iid, backend)
            except Exception as e:
                rows = [{"iid": iid, "backend": backend, "check": "load-error",
                         "detail": f"{type(e).__name__}: {e}"}]
            for r in rows:
                stats[r["check"]] += 1
            findings.extend(rows)

    by_check: dict[str, list[dict]] = collections.defaultdict(list)
    for f in findings:
        by_check[f["check"]].append(f)
    for check in sorted(by_check):
        rows = by_check[check]
        print(f"\n# {check}: {len(rows)}")
        for r in rows[:40]:
            print(f"    {r['backend']:<7} {r['iid']:<38} {r.get('case','-'):<28} "
                  f"{r['detail']}")
        if len(rows) > 40:
            print(f"    ... and {len(rows) - 40} more")
    print(f"\n# {dict(stats)}")
    if args.json:
        Path(args.json).write_text(json.dumps(
            {"stats": dict(stats), "findings": findings}, indent=2))
        print(f"# -> {args.json}")
    # proof-only-reject and unanchored-witness are real defects; the other two
    # are reports a human decides on, so only these two set the exit code.
    hard = stats["proof-only-reject"] + stats["unanchored-witness"]
    return 1 if hard else 0


if __name__ == "__main__":
    sys.exit(main())
