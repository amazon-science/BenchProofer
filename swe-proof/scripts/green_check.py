#!/usr/bin/env python
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Read-only fully-green sweep over a corpus: the batch picker and the release gate.

The PREDICATE lives in `swebench_unified.greenness` -- what "fully green" means, and
which gate is failing, has exactly one definition and every consumer imports it.
This script is the corpus walk around it: one bundle directory per row, reading
meta.json and nothing else (never a log line, never an agent's self-report).

Usage: SBU_BENCHMARK=<b> green_check.py --benchmark-dir <root> --backend <bk>
       [--only-ok]     # only consider bundles whose result.json final_status==ok
Prints TSV: <verdict>\t<instance_id> where verdict in {GREEN, NOTGREEN, NORESULT}.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))


def classify(bundle_dir: Path, backend: str, instance_id: str) -> tuple[str, str]:
    from swebench_unified.atomic_io import read_json_or_none
    from swebench_unified.greenness import failing_reasons
    meta_p = bundle_dir / "meta.json"
    if not meta_p.exists():
        return "NORESULT", "no meta.json"
    # An unreadable record is a cell whose state is UNKNOWN, so it is reported
    # not-green and the sweep continues. Raising here instead loses the verdicts
    # of every other cell in the corpus, which is the more expensive failure: the
    # callers are whole-corpus passes (triage worklist, the visualizer, the fleet
    # supervisor) and writers do not hold a reader out. It is reported loudly
    # rather than skipped, because "cannot tell" must never read as "fine".
    meta = read_json_or_none(meta_p)
    if meta is None:
        return "NOTGREEN", "meta.json unreadable (truncated or not valid JSON)"
    gates = meta.get("gates", {})
    if not gates:
        return "NOTGREEN", "no gates recorded"

    bad = failing_reasons(gates)
    return ("NOTGREEN", ";".join(bad)) if bad else ("GREEN", "ok")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--benchmark-dir", required=True)
    ap.add_argument("--backend", required=True)
    ap.add_argument("--only-ok", action="store_true")
    args = ap.parse_args()

    root = ROOT / args.benchmark_dir
    counts = {"GREEN": 0, "NOTGREEN": 0, "NORESULT": 0}
    for d in sorted(root.glob(f"*/{args.backend}")):
        iid = d.parent.name
        rp = d / "result.json"
        fs = None
        if rp.exists():
            try:
                fs = json.loads(rp.read_text()).get("final_status")
            except json.JSONDecodeError:
                pass
        if args.only_ok and fs != "ok":
            continue
        verdict, why = classify(d, args.backend, iid)
        counts[verdict] += 1
        print(f"{verdict}\t{iid}\t{why}")
    print(f"# counts: {counts}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
