#!/usr/bin/env python
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Throttled single-variant checker for the G-PBT authoring fleet.

WHY THIS EXISTS. `prompts/shared/pbt_author.md` originally told the authoring
agent "do NOT run the heavy verifier; the parent does that". Phase A of the pro
PBT lane (2026-08-17) measured why that is the wrong instruction: of the first
hand-authored batteries, EVERY positive control initially failed, and every
failure was a tactic/proof-shape problem, not a spec defect —

  * velvet `pos-control-echo`   : gold tactic body errored "No goals to be
                                  solved" (loom_solve alone already closes it)
  * velvet `pos-control-cascade`: gold body never unfolds menuLookup/encoderMenu
  * velvet `pos-control-find`   : needed the key equalities case-split BEFORE
                                  `split` fires on the match
  * lean   `pos-control-pure-if`: gold `simp only [Id.run, ...]` makes no
                                  progress once the monad is gone

Shipped unchecked, each reads as "verification failed" and is mislabeled
SPEC-TOO-STRONG. That is exactly the 95%-false-positive first sweep recorded in
docs/pro-pbt-plan.md §4. An author that can CHECK a variant fixes its own test
instead of handing an artifact to the adjudicator.

But letting 64-100 concurrent authoring agents each spawn verifiers freely is a
load hazard, and gate verdicts are measurements: on a saturated host the repair
queue shrank 73 -> 11 purely by lowering fleet width. So verifier access is
GLOBALLY throttled here by a cross-process file-lock semaphore: fleet width and
verifier width are decoupled. Authors may be 100-wide while at most
SBU_PBT_SLOTS_<BACKEND> verifiers run at any instant.

Usage (from an authoring agent):
    python3 experiments/pro2026/pbt_verify.py <instance_id> <backend> <variant.lean|.py>

Prints one of:
    SAME_SPEC=yes|no
    RESULT=VERIFIES | REJECTED | TIMEOUT
    plus the verifier summary (first lines of its diagnostics) on rejection.

Exit code is 0 whenever the check RAN (including REJECTED — a rejection is a
datum, not an error); 2 on a usage/IO problem, 3 if same_spec fails (the region
surgery touched the spec, which the author must fix before anything else).

TRACKED ON PURPOSE, at this path. `experiments/` is gitignored, but 346 shipped
`properties.py` batteries cite this file as the tool that produced their evidence
and 328 spell the full path, so moving or dropping it turns a live citation in a
frozen artifact into a dangling one. Do not relocate it; the same holds for
`pbt_drop_divergence.py`. Everything else this lane used was wave scaffolding and
is not in a clone.
"""
from __future__ import annotations

import fcntl
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

os.environ.setdefault("SBU_BENCHMARK", "swe_bench_pro_python")
os.environ.setdefault("SBU_BENCHMARK_DIR", "benchmark-pro")
# 3x the stock cap: a slow verification recorded as a failure is indistinguishable
# from a real spec defect, and this runs under fleet load.
os.environ.setdefault("SBN_VERIFY_TIMEOUT", "900")

SLOT_ROOT = Path(os.environ.get("SBU_PBT_SLOT_DIR", "/tmp/sbu_pbt_slots"))

# Concurrent verifier budget per backend on a 192-core host.
#   nagini: each verify is a JVM whose Viper runs SBN_PARALLEL_VERIFIERS=4 Z3
#           threads (scripts/nagini_verify.sh:33) -> ~4-5 cores each.
#   lean/velvet: one `lake env lean` process, ~1-2 cores, 2-5s median.
DEFAULT_SLOTS = {"nagini": 24, "lean": 40, "velvet": 40}


def _slots(backend: str) -> int:
    env = os.environ.get(f"SBU_PBT_SLOTS_{backend.upper()}")
    if env and env.isdigit() and int(env) > 0:
        return int(env)
    return DEFAULT_SLOTS.get(backend, 8)


class Semaphore:
    """Cross-process counting semaphore over N flock'd files.

    A directory of N lock files; acquiring means winning LOCK_EX|LOCK_NB on any
    one of them. Robust to killed holders (the kernel drops the flock when the
    fd closes on process death) — which a pidfile or a counter file would not
    be, and this fleet kills agents on timeout by design (agent.py
    _kill_descendants).
    """

    def __init__(self, name: str, n: int, poll_s: float = 0.4):
        self.dir = SLOT_ROOT / name
        self.dir.mkdir(parents=True, exist_ok=True)
        self.n, self.poll_s = n, poll_s
        self._fh = None

    def __enter__(self):
        waited = 0.0
        while True:
            for i in range(self.n):
                fh = (self.dir / f"{i}.lock").open("a+")
                try:
                    fcntl.flock(fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
                except OSError:
                    fh.close()
                    continue
                self._fh = fh
                if waited:
                    print(f"# waited {waited:.0f}s for a {self.dir.name} "
                          f"verifier slot ({self.n} total)", file=sys.stderr)
                return self
            time.sleep(self.poll_s)
            waited += self.poll_s

    def __exit__(self, *exc):
        if self._fh is not None:
            fcntl.flock(self._fh, fcntl.LOCK_UN)
            self._fh.close()
            self._fh = None
        return False


def main() -> int:
    if len(sys.argv) < 4:
        print(__doc__)
        return 2
    iid, backend, variant = sys.argv[1], sys.argv[2], Path(sys.argv[3])
    if not variant.is_file():
        print(f"no such variant file: {variant}", file=sys.stderr)
        return 2

    from swebench_unified.backends import get_backend
    from swebench_unified.gates._common import check_bundle_source
    from swebench_unified.gates.base import Bundle
    from swebench_unified.markers import same_spec

    bundle = Bundle(iid, get_backend(backend))
    frozen = bundle.solution_src()
    if not frozen:
        print(f"no frozen solution for {iid}/{backend}", file=sys.stderr)
        return 2
    src = variant.read_text()

    ok_spec = same_spec(frozen, src, bundle.backend.language)
    print(f"SAME_SPEC={'yes' if ok_spec else 'no'}")
    if not ok_spec:
        print("The variant CHANGED THE SPEC. A PBT case must edit only the "
              "implementation region (lean/velvet may also edit the proof / "
              "prove_correct body). Fix the region surgery before checking "
              "verify/reject — as written this case would be recorded as "
              "'spec-changed' (malformed test), never as a finding.",
              file=sys.stderr)
        return 3

    timeout = int(os.environ.get("SBN_VERIFY_TIMEOUT", "900"))
    with Semaphore(backend, _slots(backend)):
        t0 = time.monotonic()
        r = check_bundle_source(bundle, src, timeout)
    dt = time.monotonic() - t0

    if getattr(r, "timed_out", False):
        print(f"RESULT=TIMEOUT  ({dt:.1f}s, cap {timeout}s)")
        print("A timeout is INCONCLUSIVE, not a rejection: gates/pbt.py records "
              "it as such and forces MALFORMED-TESTS. Simplify the variant.")
        return 0
    print(f"RESULT={'VERIFIES' if r.success else 'REJECTED'}  ({dt:.1f}s)")
    if not r.success:
        print("--- verifier diagnostics (first 40 lines) ---")
        blob = (r.summary or "") + "\n" + (getattr(r, "stdout", "") or "")
        for ln in blob.splitlines()[:40]:
            print(ln)
    return 0


if __name__ == "__main__":
    sys.exit(main())
