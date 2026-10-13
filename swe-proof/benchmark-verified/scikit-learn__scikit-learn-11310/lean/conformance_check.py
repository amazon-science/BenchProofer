#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for scikit-learn__scikit-learn-11310.

The bundle models ONE behavior: the refit block of `BaseSearchCV.fit`. Its Lean
implementation (`implementation_refitTiming`) produces the recorded refit-duration
observable:

    refit_duration = some(end_clock - start_clock) if refit_enabled else none

mirroring the patched repo code
(`sklearn/model_selection/_search.py`):

    if self.refit:
        ...
        refit_start_time = time.time()
        self.best_estimator_.fit(...)
        refit_end_time = time.time()
        self.refit_time_ = refit_end_time - refit_start_time

i.e. `self.refit_time_` is set to `refit_end_time - refit_start_time` exactly when
`self.refit` is truthy, and is otherwise absent (the attribute is never assigned).

This script transliterates that R/I impl into Python (`shadow`) and differential-
tests it against the ORACLE: a faithful in-process replica of the POST-PATCH
behavior. We do NOT stand up a search estimator / fit loop (heavy, and the modeled
value is the pure timing-record step). Instead we reproduce the patched behavior
with the SAME observables the real code exposes (mapping.md): `self.refit` ->
`refit_enabled`, `time.time()` before the refit -> `start_clock`, `time.time()`
after the refit -> `end_clock`. The attribute is represented as `("set", value)`
when present and `None` when absent. They must agree for every input — in
particular when `refit_enabled` is False (attribute absent) and when the two
readings are equal (zero-duration refit).

stdlib-only; deterministic built-in fuzzer. Pinned seed: 11310 (also in mapping.md).
"""
import sys
from fractions import Fraction

SEED = 11310
N = 120_000


# --- ORACLE: the post-patch behavior, faithful in-process replica -------------
# Returns the recorded refit-duration observable:
#   ("set", duration) when the refit branch runs (attribute present),
#   None              when refit is disabled (attribute absent).
def oracle(refit_enabled, start_clock, end_clock):
    refit_time = None                                   # attribute unset
    if refit_enabled:                                   # if self.refit:
        refit_start_time = start_clock                  # time.time()
        # self.best_estimator_.fit(...)  (time elapses here)
        refit_end_time = end_clock                      # time.time()
        refit_time = ("set", refit_end_time - refit_start_time)
    return refit_time


# --- shadow of implementation_refitTiming (the R/I leg) -----------------------
# Mirrors Solution.lean exactly.
def shadow(refit_enabled, start_clock, end_clock):
    refit_duration = None
    if refit_enabled:
        s = start_clock
        e = end_clock
        refit_duration = ("set", e - s)
    return refit_duration


def disagree(args):
    got = oracle(*args)
    want = shadow(*args)
    if got != want:
        return (args, got, want)
    return None


# --- input corpus -------------------------------------------------------------
# Clock readings are modeled as rationals (mapping.md). We fuzz over integer/
# fractional second offsets; the spec is unconditional in the two readings, so
# the corpus includes start_clock > end_clock pairs as well as the monotonic
# (start_clock <= end_clock) ones a real wall clock produces.
def _lcg(seed):
    x = seed & 0xFFFFFFFF
    while True:
        x = (1103515245 * x + 12345) & 0x7FFFFFFF
        yield x


def _enumerate_edge():
    cases = []
    # (start, end) pairs with start <= end, including equal (zero duration).
    clock_pairs = [
        (0, 0),                 # zero-duration refit
        (0, 1),                 # 1 second
        (100, 100),             # equal, large
        (1234567, 1234567 + 5),
        (Fraction(3, 2), Fraction(7, 2)),   # fractional: 1.5 -> 3.5 (rationals)
        (1, 0),                 # end < start (spec is unconditional)
        (Fraction(7, 2), Fraction(3, 2)),   # fractional, end < start
    ]
    for refit in (True, False):
        for s, e in clock_pairs:
            cases.append((refit, s, e))
    return cases


def main() -> int:
    checked = 0

    for args in _enumerate_edge():
        d = disagree(args)
        if d:
            print(f"DISAGREE edge {d[0]!r}: oracle={d[1]} shadow={d[2]}")
            print("status=fail")
            return 1
        checked += 1

    rnd = _lcg(SEED)
    for _ in range(N):
        refit = (next(rnd) & 1) == 1
        start = next(rnd) % 10_000_000           # a wall-clock instant (ms-ish ticks)
        delta = next(rnd) % 1_000_000            # elapsed duration magnitude
        # spec is unconditional in the readings: cover end >= start AND end < start
        end = start + (delta if (next(rnd) & 3) != 0 else -delta)
        d = disagree((refit, start, end))
        if d:
            print(f"DISAGREE fuzz {d[0]!r}: oracle={d[1]} shadow={d[2]}")
            print("status=fail")
            return 1
        checked += 1

    print(f"checked={checked} disagreements=0")
    print("status=pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
