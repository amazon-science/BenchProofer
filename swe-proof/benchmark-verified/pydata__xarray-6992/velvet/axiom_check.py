#!/usr/bin/env python3
"""G-AX executable soundness check for pydata__xarray-6992.

The bundle consumes NO library callee's `ensures` as an axiom: the changed
operation (`Dataset.reset_index`'s name-set bookkeeping) is modeled DEEPLY in
Solution.lean (`computeNameSets`). The only kind-A obligation is a single
**A-reference** about an UNCHANGED neighbouring callee:

  (A-reference) `Indexes.get_all_coords(name)` reports the FULL coordinate
      footprint of the (multi-)index keyed by `name`, namely
      `{index.dim} ∪ set(level coordinate names)`. The deep model takes this
      footprint as its `dim` + `levels` inputs; this check validates that the
      footprint the model assumes equals what the real callee returns.

This runs the REAL `xarray` callee (no patch needed — `get_all_coords` is
unchanged by the gold patch; run unpatched so the reference reflects the
neighbour's own behaviour) on a battery of index shapes (plain `PandasIndex`,
1/2/3-level `PandasMultiIndex`, multiple disjoint indexes, an index with extra
non-index coordinates present) plus randomized fuzz. Imports only the in-tree
`xarray` / `pandas` / `numpy`. Exit 0 iff every observation matches.
"""
import sys
import random

import numpy as np
import pandas as pd
import xarray as xr


def index_footprint_model(ds, name):
    """The footprint the deep model assumes for the index keyed by `name`:
    {index.dim} ∪ {level coordinate names}.  (Multi-index: dim + level names;
    single PandasIndex: just {dim}, no levels.)"""
    idx = ds._indexes[name]
    dim = idx.dim
    pidx = getattr(idx, "index", None)
    level_names = list(getattr(pidx, "names", []) or [])
    # a plain pandas.Index reports its sole name (== dim); a MultiIndex reports
    # its level names. The model's `levels` are the level coords distinct names.
    footprint = {dim}
    for nm in level_names:
        if nm is not None:
            footprint.add(nm)
    return footprint


def check_footprint(ds, name):
    real = set(ds.xindexes.get_all_coords(name, errors="ignore").keys())  # real callee
    model = index_footprint_model(ds, name)
    assert real == model, (
        "get_all_coords A-reference unsound for key %r: real footprint %r, "
        "model footprint %r" % (name, sorted(real), sorted(model)))
    return real


def datasets_boundary():
    out = []

    # single PandasIndex on a 1-D dim
    out.append(xr.Dataset(coords={"x": [1, 2, 3]}))

    # 2-level multi-index on dim x
    midx2 = pd.MultiIndex.from_product([["a", "b"], [1, 2]], names=("foo", "bar"))
    out.append(xr.Dataset(coords={"x": midx2}))

    # 3-level multi-index on dim x
    midx3 = pd.MultiIndex.from_arrays(
        [["p", "p", "q", "q"], [1, 2, 1, 2], ["u", "v", "u", "v"]],
        names=("a", "b", "c"))
    out.append(xr.Dataset(coords={"x": midx3}))

    # multi-index plus an extra independent single index on another dim,
    # plus a non-index data variable
    out.append(xr.Dataset(
        data_vars={"d": ("x", [10, 20, 30, 40])},
        coords={"x": midx2, "y": [0, 1, 2]}))

    # two disjoint single indexes
    out.append(xr.Dataset(coords={"x": [1, 2], "z": [9, 8, 7]}))

    return out


def datasets_fuzz(rng, n):
    for _ in range(n):
        kind = rng.choice(["single", "multi2", "multi3"])
        size = rng.randint(1, 5)
        dim = rng.choice(["x", "dim0", "t"])
        if kind == "single":
            yield xr.Dataset(coords={dim: list(range(size))})
        elif kind == "multi2":
            a = [rng.choice("ab") for _ in range(size + 2)]
            b = [rng.randint(0, 2) for _ in range(size + 2)]
            n1, n2 = rng.choice(["foo", "lvl0", "g"]), rng.choice(["bar", "lvl1", "h"])
            if n1 == n2:
                n2 = n2 + "_2"
            midx = pd.MultiIndex.from_arrays([a, b], names=(n1, n2))
            yield xr.Dataset(coords={dim: midx})
        else:
            a = [rng.choice("pq") for _ in range(size + 3)]
            b = [rng.randint(0, 2) for _ in range(size + 3)]
            c = [rng.choice("uv") for _ in range(size + 3)]
            names = ("a", "b", "c")
            midx = pd.MultiIndex.from_arrays([a, b, c], names=names)
            yield xr.Dataset(coords={dim: midx})


def main():
    checked = 0
    for ds in datasets_boundary():
        for name in list(ds._indexes):
            check_footprint(ds, name)
            checked += 1

    rng = random.Random(6992)
    for ds in datasets_fuzz(rng, 4000):
        for name in list(ds._indexes):
            check_footprint(ds, name)
            checked += 1

    print("G-AX OK: get_all_coords A-reference (index footprint == "
          "{dim} ∪ levels) sound on %d index-key observations "
          "(boundary + 4000 fuzz datasets)." % checked)
    return 0


if __name__ == "__main__":
    sys.exit(main())
