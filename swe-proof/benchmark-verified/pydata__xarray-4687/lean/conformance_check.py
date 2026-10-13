#!/usr/bin/env python
"""G-CONF: differential conformance for pydata__xarray-4687.

Runs INSIDE the instance image with the gold patch applied (apply_gold=True,
PYTHONPATH=/testbed). Builds the Python R/A-reference shadow of the Lean
`implementation_condSelect` skeleton and diffs it against the REAL patched
`xarray.where` over a discrete catalogue plus >=1e5 randomized cases.

  observable: for a boolean condition array `cond`, two int operands `x`, `y`
  (each with an attrs dict), and a `keep_attrs` flag in {None, True, False}:
    - result.values = elementwise np.where(cond, x, y)
    - result.attrs  = x.attrs  when the resolved flag is True, else {}

The shadow is grounded ONLY in the inputs (SPEC_GUIDE §0.8): it computes the
selection and the retained-attrs directly from `cond`, `x`, `y`, and the flag,
never echoing xarray's output.

Exit 0 iff zero disagreements. stdlib-only fuzzing (pinned seed).
"""
import random
import sys

SEED = 20240626
N_RANDOM = 120_000  # >= 1e5

ATTR_KEYS = ["attr", "units", "long_name", "src"]
ATTR_VALS = ["x", "y", "cond", "m", "K", "test1", "test2", "foo", "bar"]


# ---- Python shadow of implementation_condSelect ----------------------------

def sel_vals(cond, xs, ys):
    # transliteration of selVals (zip truncates to the shortest, matching the
    # List.zip semantics; conformance inputs are equal-length / broadcastable)
    return [xv if c else yv for (c, (xv, yv)) in zip(cond, zip(xs, ys))]


def shadow(cond, x_vals, x_attrs, y_vals, y_attrs, keep_attrs, default_keep):
    # resolve the flag against the ambient default (getKeepAttrsDefault)
    ka = default_keep if keep_attrs is None else keep_attrs
    kept = ka is True
    values = sel_vals(cond, x_vals, y_vals)
    attrs = dict(x_attrs) if kept else {}
    return values, attrs


def rand_attrs(rng):
    n = rng.randint(0, 3)
    keys = rng.sample(ATTR_KEYS, min(n, len(ATTR_KEYS)))
    return {k: rng.choice(ATTR_VALS) for k in keys}


def main():
    try:
        import numpy as np
        import xarray as xr
        from xarray.core.options import _get_keep_attrs
    except Exception as e:  # pragma: no cover
        print(f"status=error import failed: {e}")
        return 2

    rng = random.Random(SEED)
    # ambient default retention, as the real config resolves it (normally False)
    default_keep = bool(_get_keep_attrs(default=False))

    mismatches = 0
    checked = 0

    # ---- discrete catalogue (incl. the F2P scenario) ----
    catalogue = [
        ([True, False], [1, 1], {"attr": "x"}, [0, 0], {"attr": "y"}, True),
        ([True, False], [1, 1], {"attr": "x"}, [0, 0], {"attr": "y"}, False),
        ([True, False], [1, 1], {"attr": "x"}, [0, 0], {"attr": "y"}, None),
        ([True], [5], {}, [0], {"a": "b"}, True),
        ([False, False, True], [7, 8, 9], {"u": "K"}, [-1, -2, -3], {}, True),
    ]

    def run_case(cond, xv, xa, yv, ya, ka):
        nonlocal mismatches, checked
        checked += 1
        x = xr.DataArray(np.array(xv), dims="d", attrs=dict(xa))
        y = xr.DataArray(np.array(yv), dims="d", attrs=dict(ya))
        c = xr.DataArray(np.array(cond, dtype=bool), dims="d")
        if ka is None:
            actual = xr.where(c, x, y)
        else:
            actual = xr.where(c, x, y, keep_attrs=ka)
        exp_vals, exp_attrs = shadow(cond, xv, xa, yv, ya, ka, default_keep)
        a_vals = [int(v) for v in np.asarray(actual.values).tolist()]
        a_attrs = dict(actual.attrs)
        if a_vals != [int(v) for v in exp_vals] or a_attrs != exp_attrs:
            if mismatches < 10:
                print(f"MISMATCH cond={cond} x={xv}/{xa} y={yv}/{ya} "
                      f"keep={ka}: actual=({a_vals},{a_attrs}) "
                      f"expected=({exp_vals},{exp_attrs})")
            mismatches += 1

    for case in catalogue:
        run_case(*case)

    # ---- randomized fuzz ----
    for _ in range(N_RANDOM):
        n = rng.randint(1, 6)
        cond = [rng.random() < 0.5 for _ in range(n)]
        xv = [rng.randint(-50, 50) for _ in range(n)]
        yv = [rng.randint(-50, 50) for _ in range(n)]
        xa = rand_attrs(rng)
        ya = rand_attrs(rng)
        ka = rng.choice([None, True, False])
        run_case(cond, xv, xa, yv, ya, ka)

    print(f"status=ok checked={checked} mismatches={mismatches} "
          f"default_keep={default_keep}")
    return 0 if mismatches == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
