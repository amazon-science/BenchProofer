#!/usr/bin/env python3
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Run the REAL weakness auditor against a bundle, and record nothing.

A repair agent's problem is not finding a clause that defeats the attack it was
shown. It is surviving the audit that runs afterwards, whose attacks are authored
from scratch against the new spec text: a repair can land with every static and
docker gate passing and the shown attack dead, and still be refuted by a fresh
attack the same hole admits. The agent cannot see that coming, because its own
adversarial round is a few hand-written attacks and the judge's is an adversary
agent with the audit prompt and its own budget.

This gives the agent the judge. It runs the `eq` audit role -- the same prompt,
the same attack floor, the same re-derivation that scores G-EQ and G-PANEL-1 --
and prints what those two gates WOULD say. Nothing is written to the bundle:
`run_audit` returns its payload for the caller to record, and here the caller
does not record it, so a cell's meta.json is untouched no matter what this finds.
That is what makes it safe to run while a driver holds the cell lock and while
the cell's real audit history stands.

The scratch dir is deliberately KEPT (`run_audit_stage` deletes it after
deriving). Its attack files are the finding: a CANDIDATE names a file, and the
next repair step is to read that file and work out which observable let it
through.

Usage:
    SBU_BENCHMARK=swe_bench_verified SBU_BENCHMARK_DIR=benchmark-verified \
      python scripts/self_audit.py <instance_id> <backend> [--timeout S]

Exit status is about the MEASUREMENT, not about the spec: 0 when the roles
reached a verdict (pass or fail -- read the output), 2 when they reached none.
An INCONCLUSIVE result is not evidence that the spec is sound; it means nothing
looked, and the check has to be re-run.
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("instance_id")
    ap.add_argument("backend")
    ap.add_argument("--timeout", type=int, default=None,
                    help="per-role wall clock (default: SBU_AUDIT_TIMEOUT, else "
                         "the harness default)")
    ap.add_argument("--min-attacks", type=int, default=None,
                    help="attack floor for a clean pass (default: the harness "
                         "value the real audit uses -- lowering it makes this "
                         "check weaker than the judge, which defeats the point)")
    args = ap.parse_args()

    from swebench_unified.adversary import check_attack
    from swebench_unified.backends import get_backend
    from swebench_unified.construct.build_one import (
        AUDIT_ROLE_TIMEOUT_DEFAULT, MIN_ATTACKS_DEFAULT, _derive_audit_verdict)
    from swebench_unified.gates.base import Bundle
    from swebench_unified.gates._audit import run_audit
    from swebench_unified.harness import run_resolve

    timeout = args.timeout
    if timeout is None:
        v = os.environ.get("SBU_AUDIT_TIMEOUT")
        timeout = int(v) if v and v.isdigit() else AUDIT_ROLE_TIMEOUT_DEFAULT
    floor = MIN_ATTACKS_DEFAULT if args.min_attacks is None else args.min_attacks

    bundle = Bundle(args.instance_id, get_backend(args.backend))
    print(f"# self-audit {args.instance_id}/{args.backend}: running the `eq` "
          f"audit role (timeout {timeout}s, attack floor {floor})", flush=True)
    print("# nothing is recorded; meta.json is not touched", flush=True)

    payload = run_audit(bundle, "eq", timeout_s=timeout)
    scratch = payload.get("_scratch")

    # One resolve per distinct (instance, patch), shared across both derivations
    # -- the same memo the real stage uses, for the same two reasons: the oracle
    # is the expensive step, and two derivations that disagree about whether a
    # patch resolves would be a difference between this check and the judge.
    cache: dict[tuple[str, str], object] = {}

    def resolve_once(iid: str, patch_text: str):
        key = (iid, patch_text)
        if key not in cache:
            cache[key] = run_resolve(iid, patch_text)
        return cache[key]

    verdicts = {}
    for gate, role in (("G-EQ", "eq"), ("G-PANEL-1", "panel_1")):
        results: dict = {}
        status, note = _derive_audit_verdict(
            role, bundle, payload, min_attacks=floor,
            check_attack=check_attack, run_resolve=resolve_once,
            attack_results=results)
        verdicts[gate] = (status, note, results, role)

    print()
    for gate, (status, note, _, _role) in verdicts.items():
        print(f"{gate} = {status.upper()}")
        print(f"  {note}")
        print()

    # The per-attack labels are the same ones verdict.md renders, and they are
    # what tells a repair which of its own assumptions was wrong: `rejected` is
    # the spec doing its job, `correct echo` is an attack that resolves (not a
    # weakness), and a candidate is the hole.
    labels = verdicts["G-EQ"][2]
    if labels:
        print("# per-attack outcome (the label the judge would record):")
        for path in sorted(labels):
            print(f"  {Path(path).name:44} {labels[path]}")
        print()

    if scratch:
        print(f"# attack sources KEPT for you to read: {scratch}")
        print("# (delete it yourself when done; nothing else will)")

    # The same test the retry loop in `run_audit_stage` uses: the derivation
    # marks a role that reached no verdict by opening its note with
    # "<role>: INCONCLUSIVE". Both roles come from ONE agent run, so either both
    # are inconclusive or the run produced a verdict.
    if all(note.lstrip().startswith(f"{role}: INCONCLUSIVE")
           for _status, note, _labels, role in verdicts.values()):
        print("\n# INCONCLUSIVE: the role reached no verdict, so this says "
              "NOTHING about the spec. Re-run before drawing a conclusion.")
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
