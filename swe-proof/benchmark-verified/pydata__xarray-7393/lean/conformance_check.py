#!/usr/bin/env python
"""G-CONF: differential conformance for pydata__xarray-7393.

Runs INSIDE the instance image with the gold patch applied (apply_gold=True,
PYTHONPATH=/testbed). Builds the Python R shadow of the Lean
`implementation_arrayConvert` skeleton and diffs it against the REAL patched
`PandasMultiIndexingAdapter.__array__` over a discrete matrix plus >=1e5
randomized draws on real pandas.MultiIndex / numpy objects.

  shadow of implementation_arrayConvert   vs   PandasMultiIndexingAdapter.__array__
  observable: (str(result.dtype), [int(v) for v in result])

The differential test targets the CHANGED branch — a SELECTED level. There the
result dtype must be the EFFECTIVE dtype (the requested dtype, else the adapter's
stored original dtype), NOT the pandas-widened dtype of the raw level values.
The non-level branch (`level = none`) is the UNCHANGED parent-class conversion
and is not a realistic configuration for a multi-index level adapter (its
`.array.values` are level tuples), so it is excluded here; it is taken as the
modeled input `superArray` and is unaffected by the patch (see refinement.md /
mapping.md).

Exit 0 iff zero disagreements. stdlib-only fuzzing (pinned seed).
"""
import random
import sys

SEED = 7393
N_RANDOM = 120_000  # >= 1e5

# dtypes whose values we keep small + in range so widening/narrowing is lossless.
DTYPES = ["int32", "int64", "float32", "float64"]


def effective_dtype(self_dtype, dtype_arg):
    """effectiveDtype: requested dtype if given, else the stored original."""
    return self_dtype if dtype_arg is None else dtype_arg


def shadow_level(self_dtype, dtype_arg, raw_values):
    """Python R shadow of implementation_arrayConvert on the level branch:
    castArray (effectiveDtype selfDtype dtypeArg) rawArray.data.
    Returns the observable (dtype_str, values)."""
    d = effective_dtype(self_dtype, dtype_arg)
    return (d, [int(v) for v in raw_values])


def main():
    import numpy as np
    from xarray.core.indexing import PandasMultiIndexingAdapter
    import pandas as pd

    rng = random.Random(SEED)

    def make_multiindex(level_values, level_dtype, n_levels):
        """A pandas.MultiIndex with `n_levels` levels; the FIRST level carries
        `level_values` at `level_dtype`. Returns (midx, level_name)."""
        arrays = [np.array(level_values, dtype=level_dtype)]
        names = ["lev0"]
        for j in range(1, n_levels):
            arrays.append(np.array(list(range(len(level_values))), dtype="int64"))
            names.append(f"lev{j}")
        midx = pd.MultiIndex.from_arrays(arrays, names=names)
        return midx, "lev0"

    def real_observe_level(self_dtype, dtype_arg, level_values, level_dtype,
                           n_levels):
        midx, level_name = make_multiindex(level_values, level_dtype, n_levels)
        adapter = PandasMultiIndexingAdapter(
            midx, dtype=np.dtype(self_dtype), level=level_name,
        )
        if dtype_arg is None:
            arr = np.asarray(adapter)
        else:
            arr = np.asarray(adapter, dtype=np.dtype(dtype_arg))
        return (str(arr.dtype), [int(v) for v in np.asarray(arr).ravel().tolist()])

    def run_case(self_dtype, dtype_arg, level_values, level_dtype, n_levels):
        exp = shadow_level(self_dtype, dtype_arg, level_values)
        got = real_observe_level(self_dtype, dtype_arg, level_values,
                                 level_dtype, n_levels)
        return exp, got

    disagreements = 0
    checked = 0

    def check(case):
        nonlocal disagreements, checked
        exp, got = run_case(*case)
        checked += 1
        if exp != got:
            disagreements += 1
            if disagreements <= 5:
                print(f"MISMATCH case={case}: real={got!r} shadow={exp!r}")

    # ---- discrete edge matrix (incl. the F2P scenario: int32/float32, no arg) --
    for sd in DTYPES:
        for da in [None] + DTYPES:
            for nlev in (1, 2):
                check((sd, da, [0, 1, 2], sd, nlev))
    # F2P-faithful: raw level dtype widened relative to the stored original.
    check(("int32", None, [0, 1], "int64", 1))
    check(("float32", None, [0, 1], "float64", 1))

    # ---- randomized fuzz ----
    for _ in range(N_RANDOM):
        sd = rng.choice(DTYPES)
        da = rng.choice([None] + DTYPES)
        n = rng.randint(1, 3)
        vals = [rng.randint(-1000, 1000) for _ in range(rng.randint(1, 5))]
        # raw level dtype: sometimes the original, sometimes widened.
        ld = rng.choice([sd, "int64", "float64"])
        check((sd, da, vals, ld, n))

    print(f"checked={checked} disagreements={disagreements}")
    if disagreements == 0:
        print(f"status=pass conformance OK ({checked} checks, 0 disagreements)")
        return 0
    print(f"status=fail {disagreements} disagreement(s)")
    return 1


if __name__ == "__main__":
    sys.exit(main())
