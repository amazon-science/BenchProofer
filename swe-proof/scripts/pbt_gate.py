#!/usr/bin/env python
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Run G-PBT on ONE bundle and record the stamped verdict into meta.json.

The authoritative check for a ported battery: the manifest is judged by the
real verifier, never by an agent's self-report. Prints one line:

    [<iid>/<backend>] G-PBT=<status> :: <detail>

Exit 0 iff status is pass or a genuine skip; 1 on fail/error. A
`pbt_missing_manifest` skip exits 1 too — "no battery yet" is not a success
for a port task (it matches green_check, which does not count that skip as
green).

Spec lane only, so no Docker. Each case re-runs the backend checker, which for
the Lean-family backends means a `lake` build: budget with
SBU_PBT_VERIFY_TIMEOUT and SBU_PBT_WORKERS (per-bundle case concurrency). The
300s gate default is for a quiet host; under a wave the fleets pass 1800, having
measured a 300s cap truncating the tail of a distribution whose p99 was 126s.
A build that hits the cap is inconclusive, which makes the whole battery
TIMED-OUT (an error) — so an under-budgeted run costs the cell, not just time.

Usage:
  SBU_BENCHMARK=swe_bench_verified SBU_BENCHMARK_DIR=benchmark-verified \
    python scripts/pbt_gate.py --backend lean <instance_id> [--validate-only]

--validate-only skips the verifier entirely and reports just the mechanical
checks (same_spec + obligation preserved + no new assumptions, plus witness
SHAPE on the backends that require one) for every case. Cheap (no lake build),
so it is the right inner loop while authoring. It cannot tell you whether a
witness actually discriminates — that needs the two builds the gate runs.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

# The Lean toolchain lives in ~/.elan; a bare shell (cron, sg docker) may not
# have it on PATH, and lean_verify.sh would then fail as an infra error that
# looks like a spec defect.
os.environ["PATH"] = f"{Path.home() / '.elan' / 'bin'}:{os.environ.get('PATH', '')}"


def validate_only(iid: str, backend_name: str) -> int:
    """Mechanical scope check for every case; no verifier."""
    from swebench_unified.backends import get_backend
    from swebench_unified.gates.base import Bundle
    from swebench_unified.gates.pbt import load_manifest
    from swebench_unified.pbt_witness import (WITNESS_REQUIRED,
                                              witness_anchor_problems,
                                              witness_problems)
    from swebench_unified.variant_scope import frozen_self_check, variant_problems

    backend = get_backend(backend_name)
    bundle = Bundle(iid, backend)
    frozen = bundle.solution_src()
    if not frozen:
        print(f"[{iid}/{backend_name}] VALIDATE=error :: no solution file")
        return 1
    self_problems = frozen_self_check(frozen, backend.language)
    if self_problems:
        print(f"[{iid}/{backend_name}] VALIDATE=error :: frozen solution fails "
              f"its own scope check: {self_problems}")
        return 1
    try:
        tests = load_manifest(bundle)
    except Exception as e:
        print(f"[{iid}/{backend_name}] VALIDATE=error :: manifest load: "
              f"{type(e).__name__}: {e}")
        return 1
    if tests is None:
        print(f"[{iid}/{backend_name}] VALIDATE=error :: no properties.py")
        return 1
    if not tests:
        print(f"[{iid}/{backend_name}] VALIDATE=error :: SPEC_TESTS is empty")
        return 1

    bad = 0
    kinds: dict[str, int] = {}
    for case in tests:
        cid = case.get("id", "?") if isinstance(case, dict) else "?"
        if not isinstance(case, dict):
            print(f"  {cid}: MALFORMED (not a dict)")
            bad += 1
            continue
        kinds[str(case.get("kind"))] = kinds.get(str(case.get("kind")), 0) + 1
        module = case.get("module")
        if not isinstance(module, str) or not module.strip():
            print(f"  {cid}: MALFORMED (no 'module' source)")
            bad += 1
            continue
        if case.get("expect") not in ("verify", "reject"):
            print(f"  {cid}: MALFORMED (expect={case.get('expect')!r})")
            bad += 1
            continue
        if case.get("kind") not in ("uniqueness", "soundness", "admissibility"):
            print(f"  {cid}: MALFORMED (kind={case.get('kind')!r})")
            bad += 1
            continue
        problems = variant_problems(frozen, module, backend.language)
        # A reject case on a tactic-proof backend needs a witness, else its
        # rejection attributes nothing to the spec (see pbt_witness). Checked
        # here for shape only; the two builds that decide it are the gate's.
        if (case.get("expect") == "reject"
                and backend_name in WITNESS_REQUIRED):
            problems = problems + [
                f"witness: {p}" for p in
                (witness_problems(case.get("witness"))
                 + witness_anchor_problems(frozen, case.get("witness")))]
        if problems:
            print(f"  {cid}: OUT-OF-SCOPE :: {'; '.join(problems)}")
            bad += 1
        else:
            print(f"  {cid}: scope-ok ({case.get('kind')}/{case.get('expect')})")
    status = "ok" if not bad else "fail"
    print(f"[{iid}/{backend_name}] VALIDATE={status} :: {len(tests)} case(s) "
          f"{kinds}, {bad} out-of-scope")
    return 0 if not bad else 1


def main() -> int:
    # The gate's own `applies_to` is the choice list, so a backend added to G-PBT
    # is runnable from here without an edit -- and one the gate skips cannot be
    # asked for at all, rather than reported as a skip that looks like a verdict.
    from swebench_unified.gates.pbt import applies_to as pbt_backends
    ap = argparse.ArgumentParser(description="Run G-PBT on one bundle.")
    ap.add_argument("instance")
    ap.add_argument("--backend", required=True,
                    choices=list(pbt_backends))
    ap.add_argument("--validate-only", action="store_true",
                    help="mechanical scope check only; no verifier, no record")
    ap.add_argument("--no-record", action="store_true",
                    help="run the gate but do not write meta.json")
    ap.add_argument("--json", action="store_true",
                    help="also dump the full per-case data as JSON")
    args = ap.parse_args()

    iid, bk = args.instance, args.backend
    if args.validate_only:
        return validate_only(iid, bk)

    from swebench_unified.gates import run_gates

    results = run_gates(iid, bk, ["G-PBT"], mode="strict",
                        record=not args.no_record)
    r = results[0]
    print(f"[{iid}/{bk}] G-PBT={r.status} :: {r.detail}")
    if args.json:
        print(json.dumps(r.data, indent=2, sort_keys=True))
    else:
        for c in (r.data or {}).get("cases", []):
            mark = "ok " if c.get("ok") else "BAD"
            print(f"  {mark} {c.get('id')}: {c.get('kind')}/{c.get('expect')} "
                  f"-> {c.get('outcome')} [{c.get('wall_s')}s]")

    if r.status == "pass":
        return 0
    # A missing-manifest skip is not success for a port task (green_check
    # agrees: it does not count that skip as green).
    if r.status == "skip" and not (r.data or {}).get("pbt_missing_manifest"):
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
