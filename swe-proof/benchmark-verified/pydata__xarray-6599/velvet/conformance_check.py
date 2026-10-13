#!/usr/bin/env python3
"""G-CONF differential conformance check for pydata__xarray-6599 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region transliterated
              to Python over the *real* repo types. The R/I content here is the
              KIND DISPATCH (`match t.kind`): a datetime array routes to the
              epoch-relative conversion, a duration array to the direct float
              cast, a numeric array passes through. The two A-reference callees
              (`datetime_to_numeric`, `astype(float)`) are left as the REAL repo
              callees (G-CONF isolates the R/I legs; the A legs stay with G-AX).
  * ORACLE  — `patch.diff`'s behaviour: the patched `_ensure_numeric` /
              `to_floatable` applied at base_commit (the real correctness
              oracle, G-RESOLVE). `to_floatable` is nested inside
              `_ensure_numeric`, so the oracle calls `_ensure_numeric` on a
              constructed DataArray and reads back its (float) values.

They must agree on every input across the three kinds. Exit 0 iff zero
disagreements; any disagreement is a mechanical R/I-fidelity counterexample
(e.g. a wrong dispatch routing a duration through the epoch path). Runs
in-container (the prebuilt SWE-Bench instance image); numpy + xarray + stdlib
only. The fuzz seed is pinned (mapping.md §4) for a deterministic verdict.
"""
import random
import sys

import numpy as np
import xarray as xr
from xarray.core.computation import _ensure_numeric
from xarray.core.duck_array_ops import datetime_to_numeric

SEED = 6599
N_FUZZ = 100_000
OFFSET = np.datetime64("1970-01-01")
MISSING = -(2 ** 63)  # the reserved NaT count (Solution.lean `missingCount`)


def _make_dataarray(raw_ns, kind):
    """Build the real repo type (DataArray) for a given kind from int ns counts."""
    arr = np.asarray(raw_ns, dtype="int64")
    if kind == "datetime":
        data = arr.view("datetime64[ns]")
    elif kind == "duration":
        data = arr.view("timedelta64[ns]")
    else:  # numeric
        data = arr.astype("float64")
    return xr.DataArray(data, dims="x")


# --- the R/I shadow: Solution.lean `toNumeric`'s kind dispatch ---------------

def shadow_convert(raw_ns, kind):
    """`toNumeric` transliterated: dispatch on kind, A-reference callees left
    as the REAL repo callees. Returns the float values (or None for the
    .error .illTypedForDuration leaf — never reached post-patch)."""
    da = _make_dataarray(raw_ns, kind)
    if kind == "datetime":
        # epochCount: the real epoch-relative callee
        return np.asarray(
            datetime_to_numeric(da.data, offset=OFFSET, datetime_unit="ns"),
            dtype=float,
        )
    elif kind == "duration":
        # durationCast: the real direct float cast
        return np.asarray(da.astype(float).data, dtype=float)
    else:  # numeric: pass through unchanged
        return np.asarray(da.data, dtype=float)


# --- the oracle: patch.diff behaviour (patched _ensure_numeric/to_floatable) -

def oracle_convert(raw_ns, kind):
    da = _make_dataarray(raw_ns, kind)
    return np.asarray(_ensure_numeric(da).data, dtype=float)


def fuzz_inputs(n, rng):
    kinds = ["datetime", "duration", "numeric"]
    # boundary cases first (plan §4.1 step 4)
    boundary_raw = [
        [],
        [0],
        [1000, 2000, 3000],          # the F2P timedelta case
        [0, 1000, 10_000_000_000],
        [-5, -1, 0, 1, 5],
        [2 ** 31, 2 ** 40, -(2 ** 40)],
        [MISSING],                   # the reserved NaT count
        [MISSING, 1000, 2000],       # the faithfulness counterexample input
        [MISSING, MISSING, 0, MISSING],
        [MISSING + 1, MISSING],
    ]
    for raw in boundary_raw:
        for k in kinds:
            yield raw, k
    for _ in range(n):
        m = rng.randint(1, 16)
        raw = [MISSING if rng.random() < 0.1
               else rng.randint(-(2 ** 45), 2 ** 45) for _ in range(m)]
        yield raw, rng.choice(kinds)


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0
    for raw, kind in fuzz_inputs(N_FUZZ, rng):
        count += 1
        shadow = shadow_convert(raw, kind)
        oracle = oracle_convert(raw, kind)
        # equal_nan: a missing datetime (NaT) converts to nan on BOTH sides
        # (spec's NumVal.nan leaf <-> real datetime_to_numeric's nan); nan
        # positions must coincide and every other value must be exactly equal.
        if not np.array_equal(shadow, oracle, equal_nan=True):
            disagreements.append((raw, kind, list(shadow), list(oracle)))
            if len(disagreements) >= 5:
                break
    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for raw, kind, sh, orc in disagreements:
            print("  raw=%r kind=%s shadow=%r oracle=%r" % (raw, kind, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of toNumeric's kind dispatch agrees with "
          "patch.diff behaviour on %d inputs (seed=%d), 0 disagreements."
          % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
