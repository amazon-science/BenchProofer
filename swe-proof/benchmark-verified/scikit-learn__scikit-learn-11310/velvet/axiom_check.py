#!/usr/bin/env python3
"""G-AX — executable soundness check for scikit-learn__scikit-learn-11310.

Validates the ONE load-bearing axiom of Solution.lean against the REAL callee.

AXIOM (Solution.lean, mapping.md §3 / refinement.md steps 2-3):
    The process wall clock, read twice across one synchronous unit of work, is
    NON-DECREASING — the later reading is never earlier than the earlier one.
    The readings enter the model as the read-only inputs `startT` / `endT`,
    with the contract stated as the precondition `require startT ≤ endT`.

REAL CALLEE: `time.time()` (Python stdlib `time`), the exact callee the gold
patch adds and calls (`refit_start_time = time.time()` … `refit_end_time =
time.time()`). It is UNCHANGED by the patch — the patch only `import time`s and
brackets the pre-existing refit `fit(...)` with two calls.

WHAT WE ASSERT: for many consecutive pairs of `time.time()` readings — both
back-to-back AND separated by a unit of intervening work (mimicking the real
`best_estimator_.fit(...)` between the two patch readings) — the pair is
non-decreasing: `start <= end`. This is exactly the precondition's claim, at
the level the axiom claims it (no double-masking: we assert on the raw readings,
not on a derived quantity). If every observed pair satisfies it, the axiom is a
sound lower bound on the real callee's behavior and `endT - startT >= 0` (the
recorded `refit_time_`) holds. Exit 0 iff sound. stdlib only.

NOTE on the documented caveat (mapping.md §3): `time.time()` reads
CLOCK_REALTIME, which can in principle step backwards under an NTP adjustment.
The patch and its FAIL_TO_PASS test (`test_search_cv_timing`, which asserts
`search.refit_time_ >= 0`) rely on consecutive in-process readings being
non-decreasing across a short refit; this check measures that exact property
empirically and is the operative contract. We do NOT claim more (e.g. strict
increase or any minimum/maximum elapsed bound) — the precondition assumes only
`<=`, so only `<=` need hold here.
"""
import sys
import time

N_BACK_TO_BACK = 2_000_000   # immediate consecutive readings (tightest case)
N_WITH_WORK = 200_000        # readings separated by a unit of intervening work


def _busy_unit(k):
    """A small, variable unit of intervening work standing in for the refit
    `best_estimator_.fit(...)` between the two clock readings."""
    s = 0
    for i in range(k % 64):
        s += i * i
    return s


def main():
    violations = []
    count = 0

    # Case A: back-to-back readings (start == end is fine; start > end is a
    # violation of the monotone-clock axiom).
    for _ in range(N_BACK_TO_BACK):
        start = time.time()
        end = time.time()
        count += 1
        if not (start <= end):
            violations.append(("back_to_back", start, end, end - start))
            if len(violations) >= 5:
                break

    # Case B: readings bracketing a unit of work (the real patch shape).
    if len(violations) < 5:
        for k in range(N_WITH_WORK):
            start = time.time()
            _busy_unit(k)
            end = time.time()
            count += 1
            if not (start <= end):
                violations.append(("with_work", start, end, end - start))
                if len(violations) >= 5:
                    break

    if violations:
        print("G-AX FAIL: monotone-clock axiom violated by real time.time() on "
              "%d/%d observed pairs (start > end): %r"
              % (len(violations), count, violations))
        return 1
    print("G-AX OK: real time.time() is non-decreasing across %d consecutive "
          "reading pairs (back-to-back + bracketing a work unit); every pair "
          "satisfies start <= end, so the recorded span end - start >= 0. The "
          "monotone-clock precondition is a sound lower bound on the real callee."
          % count)
    return 0


if __name__ == "__main__":
    sys.exit(main())
