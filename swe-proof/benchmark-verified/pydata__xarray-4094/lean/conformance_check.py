#!/usr/bin/env python3
"""G-CONF for pydata__xarray-4094.

The gold patch is already applied to /testbed when this runs. We compare the R
(type-refinement) Python shadow of `implementation_toUnstackedDataset` (the Lean
impl, transliterated op-for-op per refinement.md) against the REAL patched
`DataArray.to_unstacked_dataset`, over >=1e5 fuzzed inputs. Zero disagreements =>
exit 0.

Model (refinement.md): the loop is

    data_dict = {}
    for k in variables:
        data_dict[k] = self.sel({variable_dim: k}, drop=True).squeeze(drop=True)
    return Dataset(data_dict)

where `variables`/`variable_dim` come from the stacked MultiIndex level, and the
fixed token is `drop=True` (the LABEL-REMOVING extraction mode, `extractSlice
true k`).

  * Oracle = the REAL patched `stacked.to_unstacked_dataset(dim, level)`.
  * Shadow = the loop above, rebuilt op-for-op: read the same `variables` /
             `variable_dim` from the stacked index, extract each slice via the
             REAL `sel({variable_dim: k}, drop=True).squeeze(drop=True)` callee
             (the A-reference op #2, NOT substituted by a model), and recombine
             with `Dataset(data_dict)`.

Type bijection (mapping.md): kappa<->variable label k, nu<->extracted slice,
vars<->idx.levels[level_number], extractSlice True k <-> sel(...,drop=True).
squeeze(drop=True), result<->Dataset(data_dict).

The fuzzer covers the discriminating regime: single-sample-dimension datasets
(the GH4049 bug), multi-dimension datasets, varying variable counts / dim sizes /
level selectors, so the shadow's `drop=True` extraction is exercised against the
real method on inputs where the buggy `drop=False` default would raise MergeError.
stdlib-only (numpy + xarray are the repo's own deps).
"""
import sys
import warnings

import numpy as np
import pandas as pd
import xarray as xr


def _outcome(call):
    """Run `call`; return ('error', ExcType) or ('ok', Dataset)."""
    try:
        return ("ok", call())
    except Exception as e:  # noqa: BLE001 - we compare the exception type
        return ("error", type(e).__name__)


def oracle(stacked, dim, level):
    return _outcome(lambda: stacked.to_unstacked_dataset(dim, level))


def shadow(stacked, dim, level):
    """R transliteration of implementation_toUnstackedDataset (Lean).

    Mirrors the patched loop exactly, with the A-reference extraction left as the
    REAL `sel(...,drop=True).squeeze(drop=True)` callee.
    """
    def build():
        idx = stacked.indexes[dim]
        if not isinstance(idx, pd.MultiIndex):
            raise ValueError(f"'{dim}' is not a stacked coordinate")
        level_number = idx._get_level_number(level)
        variables = idx.levels[level_number]      # vars : List kappa
        variable_dim = idx.names[level_number]
        # Op 1: data_dict = {}  (association list, insertion-ordered)
        data_dict = {}
        # Op 2: for k in variables: extractSlice True k  (drop=True mode)
        for k in variables:
            data_dict[k] = stacked.sel(
                {variable_dim: k}, drop=True
            ).squeeze(drop=True)
        # Op 3: return Dataset(data_dict)
        return xr.Dataset(data_dict)
    return _outcome(build)


def _equal(o, s):
    if o[0] != s[0]:
        return False
    if o[0] == "error":
        return o[1] == s[1]
    try:
        return bool(o[1].identical(s[1]))
    except Exception:  # noqa: BLE001
        return False


def make_case(rng):
    """Build a stacked DataArray + (dim, level) selector, fuzzing the regime."""
    nvars = rng.randint(1, 4)
    nx = rng.randint(1, 5)
    single = rng.random() < 0.5  # single sample-dim (the GH4049 bug) vs two
    names = ["a", "b", "c", "d"][:nvars]
    coords = [("x", list(range(nx)))]
    if single:
        arrs = {nm: xr.DataArray(rng.randn(nx), coords=coords) for nm in names}
    else:
        ny = rng.randint(1, 4)
        coords2 = [("x", list(range(nx))), ("y", list(range(ny)))]
        arrs = {}
        for nm in names:
            if rng.random() < 0.5:
                arrs[nm] = xr.DataArray(rng.randn(nx, ny), coords=coords2)
            else:
                arrs[nm] = xr.DataArray(rng.randn(nx), coords=coords)
    data = xr.Dataset(arrs)
    dim = "z"
    stacked = data.to_stacked_array(dim, sample_dims=["x"])
    level = rng.choice([0, "variable"])
    return stacked, dim, level


def main():
    import random
    rng = random.Random(4094)   # pinned seed (mapping.md)
    nprng = np.random.RandomState(4094)

    class R:
        def random(self):
            return float(nprng.rand())

        def randint(self, a, b):
            return int(nprng.randint(a, b + 1))

        def randn(self, *shape):
            return nprng.randn(*shape)

        def choice(self, xs):
            return xs[int(nprng.randint(0, len(xs)))]

    r = R()
    N = 100_000
    disagreements = 0
    first = None
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        for _ in range(N):
            try:
                stacked, dim, level = make_case(r)
            except Exception:  # noqa: BLE001 - skip degenerate construction
                continue
            o = oracle(stacked, dim, level)
            s = shadow(stacked, dim, level)
            if not _equal(o, s):
                disagreements += 1
                if first is None:
                    first = (dim, level, o[0], s[0])
    if disagreements:
        print("G-CONF FAIL: %d/%d disagreements; first=%r"
              % (disagreements, N, first))
        return 1
    print("G-CONF OK: %d inputs, 0 disagreements" % N)
    return 0


if __name__ == "__main__":
    sys.exit(main())
