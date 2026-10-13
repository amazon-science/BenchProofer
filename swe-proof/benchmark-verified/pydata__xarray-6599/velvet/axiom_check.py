#!/usr/bin/env python3
"""G-AX executable soundness check for pydata__xarray-6599.

Executes the REAL unchanged callees that `to_floatable` dispatches to and
asserts that the deep models in Solution.lean's `pure` region match them on
boundary cases + randomized fuzzing. Both callees are modeled DEEPLY, so each is
an A-REFERENCE (no consumed module-level axiom):

  (A-reference 3.1) `epochCount` == `datetime_to_numeric(v,
      offset=np.datetime64("1970-01-01"), datetime_unit="ns")` on a
      datetime64[ns] array: the result equals the int64 ns-since-epoch count
      cast to float, EXCEPT the reserved NaT count (int64 min), which the real
      callee maps to nan (`epochCount`'s `NumVal.nan` leaf). AND `epochCount`
      is .error on a duration array — validated by confirming the real epoch
      path RAISES when fed a timedelta64 array (the pre-patch bug from the
      issue's traceback).

  (A-reference 3.2) `durationCast` == `x.astype(float)` on a timedelta64[ns]
      array: the result equals the int64 ns count cast to float — including
      the reserved NaT count, which astype(float) does NOT special-case (it
      comes through as float(int64 min), matching `durationCast`'s plain
      `NumVal.num` map).

Imports only `numpy` and the repo's own `datetime_to_numeric` — the same callees
the gold patch calls. Exit 0 iff every obligation holds.
"""
import random
import sys

import numpy as np

# the unchanged callee the datetime branch uses (gold: computation.py:1938)
from xarray.core.duck_array_ops import datetime_to_numeric

OFFSET = np.datetime64("1970-01-01")  # the pinned offset the gold patch passes
MISSING = -(2 ** 63)                  # Solution.lean `missingCount` (NaT carrier)


# --- deep-model reference encodings (lock-step with Solution.lean `pure`) -----

def epoch_count_model(raw_ns):
    """Solution.lean `epochCount` on the datetime kind: the ns count as float,
    except the reserved missing count (NaT), which maps to NumVal.nan."""
    arr = np.asarray(raw_ns, dtype="int64").astype(float)
    arr[np.asarray(raw_ns, dtype="int64") == MISSING] = np.nan
    return arr


def duration_cast_model(raw_ns):
    """Solution.lean `durationCast`: the ns count, as float (NO NaT
    special-case — the missing count comes through as its numeric value)."""
    return np.asarray(raw_ns, dtype="int64").astype(float)


# --- the checks ---------------------------------------------------------------

def check_epoch_reference(raw_ns):
    """A-reference 3.1: epochCount == real datetime_to_numeric on a datetime
    (nan positions must coincide; non-nan values must be equal)."""
    v = np.asarray(raw_ns, dtype="int64").view("datetime64[ns]")
    observed = datetime_to_numeric(v, offset=OFFSET, datetime_unit="ns")  # real
    expected = epoch_count_model(raw_ns)                                  # model
    observed = np.asarray(observed, dtype=float)
    assert np.array_equal(observed, expected, equal_nan=True), (
        "epochCount deep model unsound on %r: datetime_to_numeric gave %r, "
        "model gives %r" % (list(raw_ns), list(observed), list(expected)))


def check_epoch_undefined_on_duration(raw_ns):
    """A-reference 3.1 (.error leaf): the real epoch path RAISES on a duration,
    so epochCount = .error .illTypedForDuration is faithful."""
    td = np.asarray(raw_ns, dtype="int64").view("timedelta64[ns]")
    try:
        datetime_to_numeric(td, offset=OFFSET, datetime_unit="ns")  # real callee
    except Exception:
        return  # expected: the pre-patch bug (the issue's traceback)
    raise AssertionError(
        "epochCount .error leaf unsound: real datetime_to_numeric did NOT raise "
        "on a timedelta64 array %r — the epoch path is not ill-typed there"
        % (list(raw_ns),))


def check_duration_reference(raw_ns):
    """A-reference 3.2: durationCast == real x.astype(float) on a duration."""
    td = np.asarray(raw_ns, dtype="int64").view("timedelta64[ns]")
    observed = td.astype(float)               # real callee
    expected = duration_cast_model(raw_ns)    # model
    assert np.array_equal(observed, expected), (
        "durationCast deep model unsound on %r: astype(float) gave %r, "
        "model gives %r" % (list(raw_ns), list(observed), list(expected)))


def main():
    # boundary integer ns counts (incl. the F2P test's [1000,2000,3000] and the
    # reserved NaT count = int64 min)
    boundary = [
        [],
        [0],
        [1000, 2000, 3000],          # the F2P timedelta case
        [0, 1000, 10_000_000_000],
        [-5, -1, 0, 1, 5],
        [2 ** 31, 2 ** 40, -(2 ** 40)],
        [1] * 7,
        [MISSING],                   # NaT alone
        [MISSING, 1000, 2000],       # the G-PANEL-2 counterexample input
        [MISSING, MISSING, 0, MISSING],
        [MISSING + 1, MISSING],      # neighbor of the reserved count vs NaT
    ]
    for raw in boundary:
        check_epoch_reference(raw)
        check_duration_reference(raw)
        if raw:  # the .error leaf check needs a non-empty array to subtract
            check_epoch_undefined_on_duration(raw)

    # randomized fuzz over int64 ns counts, with NaT sprinkled in
    rng = random.Random(6599)
    for _ in range(20000):
        n = rng.randint(1, 16)
        raw = [MISSING if rng.random() < 0.1
               else rng.randint(-(2 ** 45), 2 ** 45) for _ in range(n)]
        check_epoch_reference(raw)
        check_duration_reference(raw)
        check_epoch_undefined_on_duration(raw)

    print("G-AX OK: epochCount (== datetime_to_numeric, offset=1970-01-01, "
          "unit=ns; NaT count -> nan) + durationCast (== astype(float); NaT "
          "count NOT special-cased) deep models sound on %d boundary + 20000 "
          "fuzz arrays (NaT-bearing); epoch path confirmed ill-typed on "
          "timedelta arrays (the .error leaf)." % len(boundary))
    return 0


if __name__ == "__main__":
    sys.exit(main())
