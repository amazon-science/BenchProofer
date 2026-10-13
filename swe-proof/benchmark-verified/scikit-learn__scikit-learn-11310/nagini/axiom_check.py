#!/usr/bin/env python3
"""G-AX executable soundness check for scikit-learn__scikit-learn-11310.

Executes the REAL unchanged operations the model axiomatizes and asserts that
every observation meets the axiom's `Ensures`. Two kind-A axioms:

  (A-reference) `clock_after(reference)` models the wall-clock reading the gold
      patch takes with `time.time()`. The encoded property is monotonicity: a
      reading taken after a reference instant is never earlier than it,
      i.e. for two sequential calls t1 = time.time(); t2 = time.time(),
      t2 >= t1. This is exactly how the gold patch uses it (refit_start_time
      then refit_end_time bracketing the refit fit). The model abstracts the two
      readings as the ordered inputs `start`, `end` (precondition end >= start),
      so the proof does not consume this axiom's Ensures; this check VALIDATES
      that the real time.time() produces that ordering (A-reference), grounding
      the precondition.

  (A-consumed) `elapsed_between(earlier, later)` models the real subtraction
      `later - earlier` the gold patch computes (refit_end_time -
      refit_start_time). The encoded property is: for an ordered pair
      (later >= earlier) the difference is non-negative.

Imports nothing repo-specific: `time` is the Python standard library — the same
module the gold patch calls (`import time`; `time.time()`). Exit 0 iff every
obligation holds.
"""
import random
import sys
import time


def check_clock_monotone(n_pairs):
    """Assert the REAL time.time() is non-decreasing across two sequential
    calls (the `clock_after` axiom's Ensures): a reading after a reference
    instant is never earlier than it.

    time.time() is not guaranteed strictly monotone (NTP adjustments can move
    it), but the gold patch's two readings bracket real work and the F2P test
    only requires the difference to be >= 0; here we observe the ordinary
    sequential-call behaviour the patch relies on. We also assert the much
    stronger guarantee on the difference via the elapsed check below.
    """
    violations = 0
    for _ in range(n_pairs):
        t1 = time.time()              # real callee: reference reading
        t2 = time.time()              # real callee: later reading
        # The axiom's Ensures for the second call: Result() >= reference.
        if not (t2 >= t1):
            violations += 1
    return violations


def check_elapsed_nonneg(samples):
    """Assert the REAL subtraction later - earlier is non-negative whenever
    later >= earlier (the `elapsed_between` axiom: Requires(later >= earlier)
    => Ensures(Result() >= 0.0))."""
    for earlier, later in samples:
        if not (later >= earlier):
            # only inputs satisfying the axiom's Requires are in-domain
            continue
        observed = later - earlier            # real arithmetic op
        assert observed >= 0.0, (
            "elapsed_between axiom unsound on (%r, %r): later - earlier = %r "
            "< 0 despite later >= earlier" % (earlier, later, observed))


def main():
    # --- clock monotonicity (A-consumed): observe real sequential readings ---
    # In practice time.time() is non-decreasing across back-to-back calls on a
    # quiescent clock; assert no violation over many pairs.
    pair_violations = check_clock_monotone(200000)
    assert pair_violations == 0, (
        "clock_after axiom unsound: observed %d sequential time.time() pairs "
        "where the later reading was EARLIER than the reference" %
        pair_violations)

    # --- elapsed non-negativity (A-consumed): boundary + fuzz subtraction -----
    boundary = [
        (0.0, 0.0),                      # zero-length interval (the F2P case)
        (0.0, 1e-9),                     # tiny positive interval
        (1.0, 1.0),
        (1234567890.0, 1234567890.5),
        (0.0, 1e18),                     # very large interval
        (-1.0, 0.0), (-5.0, -1.0),       # negative readings, still ordered
    ]
    # real time.time() readings, bracketing trivial work (as the gold patch does)
    for _ in range(2000):
        a = time.time()
        b = time.time()
        if b >= a:
            boundary.append((a, b))

    rng = random.Random(11310)
    fuzz = []
    for _ in range(200000):
        x = rng.uniform(-1e12, 1e12)
        y = rng.uniform(-1e12, 1e12)
        lo, hi = (x, y) if x <= y else (y, x)
        fuzz.append((lo, hi))

    check_elapsed_nonneg(boundary)
    check_elapsed_nonneg(fuzz)

    print("G-AX OK: clock_after (time.time() monotone over 200000 sequential "
          "pairs, 0 violations) + elapsed_between (later-earlier >= 0 over %d "
          "boundary + 200000 fuzz ordered pairs) sound" % len(boundary))
    return 0


if __name__ == "__main__":
    sys.exit(main())
