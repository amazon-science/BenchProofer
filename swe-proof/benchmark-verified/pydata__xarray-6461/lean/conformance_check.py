#!/usr/bin/env python3
"""G-CONF for pydata__xarray-6461.

Differential test: the R Python shadow of `implementation_whereAttrs`
(Solution.lean) vs. the REAL patched `xr.where(cond, x, y, keep_attrs=True)`
attribute-resolution path in `xarray/core/computation.py`. The orchestrator
applies the gold patch before running this, so the imported `xr.where` is the
fixed version.

Modeled behavior (mapping.md): under `keep_attrs=True`, the resulting `.attrs`
of `xr.where(cond, x, y)` are
  * `{}`/None-with-no-arrays handling: if none of cond/x/y is a DataArray there
    is nothing to merge and the merge routine returns None (xarray then leaves
    the scalar result without an attrs mapping — not observable as a labelled
    object), and
  * otherwise the attributes of the second positional argument `x`
    (`getattr(x, "attrs", {})`).

Type bridge (mapping.md): an `Arg.darray d` ↔ a 1-D `DataArray` carrying attr
dict `d`; an `Arg.scalar` ↔ a Python int. We compare the resolved attribute
dict (key/value set), which is all the F2P test (`actual.attrs == {}`) and the
issue consume.

We only exercise the case where at least one argument is a DataArray (so
`xr.where` returns a labelled object whose `.attrs` we can read). The
no-DataArray case (`Except.ok none`) corresponds to xarray returning a bare
array with no attrs mapping; it is verified separately by asserting the shadow
yields the `none` branch there (no observable labelled `.attrs`), and is not
fed to the numpy oracle.

Exit 0 iff zero disagreements over >=1e5 fuzzed cases. stdlib + numpy + xarray.
"""
import random
import sys

SEED = 6461
N_CASES = 100_000

# ---- the R shadow of implementation_whereAttrs (Solution.lean) -------------
# An Arg is either ("darray", attrs_dict) or ("scalar", None).

def attrs_of(arg):
    kind, payload = arg
    return dict(payload) if kind == "darray" else {}

def is_darray(arg):
    return arg[0] == "darray"

def shadow(cond, x, y):
    """Returns ('ok_none',) | ('ok_some', attrs_dict)."""
    objs = [a for a in (cond, x, y) if is_darray(a)]
    if not objs:
        return ("ok_none",)
    return ("ok_some", attrs_of(x))

# ---- fuzzing ---------------------------------------------------------------

def rand_attrs(rng):
    n = rng.randint(0, 3)
    keys = ["attr", "units", "name", "src", "k"]
    rng.shuffle(keys)
    return {keys[i]: rng.choice(["a", "b", "x", "y", "1", "0"]) for i in range(n)}

def rand_arg(rng):
    if rng.random() < 0.5:
        return ("darray", rand_attrs(rng))
    return ("scalar", None)


def main():
    import numpy as np
    import xarray as xr

    rng = random.Random(SEED)
    mismatches = 0
    checked = 0
    none_branch_checked = 0

    # A fixed boolean condition pattern of length 2 (matches the F2P test shape).
    cond_values = [True, False]

    for _ in range(N_CASES):
        cond = rand_arg(rng)
        x = rand_arg(rng)
        y = rand_arg(rng)

        spec = shadow(cond, x, y)

        # Build the real xarray arguments. A darray cond must be boolean; x/y
        # darrays are numeric. Scalars are plain ints.
        def build(arg, *, is_cond=False, numeric_fill=1):
            kind, payload = arg
            if kind == "scalar":
                return numeric_fill
            data = cond_values if is_cond else [numeric_fill, numeric_fill]
            return xr.DataArray(data, dims="x", attrs=dict(payload))

        cond_obj = build(cond, is_cond=True)
        x_obj = build(x, numeric_fill=1)
        y_obj = build(y, numeric_fill=0)

        # xr.where needs `cond` to be array-like to broadcast; if cond is a
        # bare scalar bool we still pass an int (xarray accepts it). At least
        # one of the three must be a DataArray for a labelled result.
        if not any(is_darray(a) for a in (cond, x, y)):
            # 'ok_none' branch: no labelled object => xarray returns a bare
            # numpy result with no .attrs mapping. Just assert the shadow agrees
            # on the branch and skip the numpy oracle.
            assert spec == ("ok_none",), spec
            none_branch_checked += 1
            continue

        actual = xr.where(cond_obj, x_obj, y_obj, keep_attrs=True)
        real_attrs = dict(actual.attrs)

        assert spec[0] == "ok_some", spec
        expected_attrs = spec[1]

        if real_attrs != expected_attrs:
            mismatches += 1
            if mismatches <= 5:
                print(f"MISMATCH cond={cond} x={x} y={y}: "
                      f"real={real_attrs} shadow={expected_attrs}", file=sys.stderr)
        checked += 1

    print(f"checked={checked} none_branch={none_branch_checked} "
          f"mismatches={mismatches}")
    if mismatches:
        print("G-CONF FAIL")
        sys.exit(1)
    print("G-CONF PASS")
    sys.exit(0)


if __name__ == "__main__":
    main()
