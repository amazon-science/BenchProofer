#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for pydata__xarray-6992.

The bundle models ONE routine: the coordinate/variable/index NAME bookkeeping of
`Dataset.reset_index` (mapping.md), restricted to the domain where every reset
target is a PLAIN single dimension index whose only associated coordinate is the
target name itself (`get_all_coords(name) == {name}`, non-`PandasMultiIndex`).

ORACLE = the REAL, gold-patched `xarray.Dataset.reset_index` (this script runs
in-container with the gold patch applied). We build genuine `xr.Dataset`s whose
indexed coordinates are all plain dimension coordinates, call the real
`reset_index`, and read the resulting NAME collections:

    varNames   = set(result._variables)
    coordNames = set(result._coord_names)
    indexNames = set(result._indexes)

SHADOW = the op-for-op transliteration of `implementation_resetIndexCoords`
(Solution.lean impl region), per refinement.md, computed over the OBSERVED input
name collections:

    dropVars    = resetNames if drop else set()
    indexNames' = indexNames - resetNames
    varNames'   = varNames   - dropVars
    coordNames' = coordNames - dropVars

This genuinely tests the soundness-critical clause (the gold fix): a dropped
dimension coordinate must leave the coordinate set together with its variable
(`coord_names = self._coord_names - drop_variables`), so the invariant
`coord_names ⊆ variables` is preserved — the pre-patch `set(new_variables) |
self._coord_names` left the dropped name lingering as a coordinate.

stdlib + numpy/xarray (present in the testbed). Pinned seed: 6992 (also in
mapping.md). Falls back with status=error if xarray is unavailable.
"""
import random
import sys

SEED = 6992
N = 120_000

try:
    import numpy as np
    import xarray as xr
except Exception as e:  # pragma: no cover
    print(f"import failure: {e}")
    print("status=error")
    sys.exit(2)


DIMS = ["x", "y", "z", "w"]


def build_dataset(rng):
    """Construct an xr.Dataset whose indexed coordinates are all plain dimension
    coordinates. Returns (ds, indexed_dims) where indexed_dims is the set of
    dimension names carrying an index (candidates for reset)."""
    ndims = rng.randint(1, 4)
    dims = rng.sample(DIMS, ndims)
    sizes = {d: rng.randint(1, 4) for d in dims}

    coords = {}
    indexed_dims = []
    for d in dims:
        if rng.random() < 0.8:
            # a plain dimension coordinate -> gets a PandasIndex
            coords[d] = (d, np.arange(sizes[d]))
            indexed_dims.append(d)

    data_vars = {}
    n_data = rng.randint(0, 3)
    for i in range(n_data):
        d = rng.choice(dims)
        nm = f"v{i}"
        data_vars[nm] = (d, np.arange(sizes[d], dtype=float))

    # optional non-index coordinate(s): a coordinate over a dim whose name is not
    # the dim itself -> no index, must be left untouched by reset_index
    n_nic = rng.randint(0, 2)
    for i in range(n_nic):
        d = rng.choice(dims)
        nm = f"c{i}"
        if nm not in coords and nm not in data_vars:
            coords[nm] = (d, np.arange(sizes[d]))

    ds = xr.Dataset(data_vars=data_vars, coords=coords)
    # keep only indexed dims that really carry an index in the built dataset
    real_indexed = [d for d in indexed_dims if d in set(ds._indexes)]
    return ds, real_indexed


def observe(ds):
    return (set(ds._variables), set(ds._coord_names), set(ds._indexes))


def shadow(varNames, coordNames, indexNames, resetNames, drop):
    dropVars = set(resetNames) if drop else set()
    return (
        set(varNames) - dropVars,
        set(coordNames) - dropVars,
        set(indexNames) - set(resetNames),
    )


def domain_ok(ds, resetNames):
    """Confirm every reset target is a plain single dimension index whose only
    associated coordinate is the target name (the modeled domain)."""
    for name in resetNames:
        if name not in ds._indexes:
            return False
        idx = ds._indexes[name]
        # get_all_coords(name) == {name}: no shared/multi-index coordinates
        try:
            allc = set(ds.xindexes.get_all_coords(name))
        except Exception:
            return False
        if allc != {name}:
            return False
        # reject pandas MultiIndex level machinery (out of modeled domain)
        if type(idx).__name__ == "PandasMultiIndex":
            return False
    return True


def one_trial(rng):
    ds, indexed = build_dataset(rng)
    if not indexed:
        return None  # nothing resettable; not in modeled scope
    k = rng.randint(1, len(indexed))
    resetNames = rng.sample(indexed, k)
    drop = rng.random() < 0.5
    if not domain_ok(ds, resetNames):
        return None
    vin, cin, iin = observe(ds)
    try:
        res = ds.reset_index(resetNames, drop=drop)
    except Exception as e:
        return ("EXC", resetNames, drop, repr(e))
    got = observe(res)
    want = shadow(vin, cin, iin, resetNames, drop)
    if got != want:
        return ("DISAGREE", resetNames, drop,
                {"input": (sorted(vin), sorted(cin), sorted(iin)),
                 "oracle": tuple(sorted(s) for s in got),
                 "shadow": tuple(sorted(s) for s in want)})
    return None


def _edge_cases(rng):
    """Hand-built MVCE-flavoured scenarios."""
    checks = 0
    # single indexed dim coord, drop=True -> name must leave BOTH variables and
    # coord_names (the invariant fix)
    for drop in (True, False):
        ds = xr.Dataset(coords={"z": ("z", np.arange(3))},
                        data_vars={"v": ("z", np.arange(3, dtype=float))})
        if "z" in set(ds._indexes) and domain_ok(ds, ["z"]):
            vin, cin, iin = observe(ds)
            res = ds.reset_index("z", drop=drop)
            assert observe(res) == shadow(vin, cin, iin, ["z"], drop), \
                f"edge single drop={drop}"
            # invariant: coord_names subset of variables
            assert set(res._coord_names) <= set(res._variables), \
                f"invariant broken drop={drop}"
            checks += 1
    # two indexed dim coords, reset one
    for drop in (True, False):
        ds = xr.Dataset(coords={"x": ("x", np.arange(2)), "y": ("y", np.arange(3))},
                        data_vars={"v": (("x", "y"), np.zeros((2, 3)))})
        if domain_ok(ds, ["x"]):
            vin, cin, iin = observe(ds)
            res = ds.reset_index("x", drop=drop)
            assert observe(res) == shadow(vin, cin, iin, ["x"], drop), \
                f"edge two-reset-one drop={drop}"
            checks += 1
    return checks


def main() -> int:
    rng = random.Random(SEED)
    checked = _edge_cases(rng)
    trials = 0
    while trials < N:
        r = one_trial(rng)
        trials += 1
        if r is not None:
            print(f"DISAGREE: {r}")
            print("status=fail")
            return 1
        checked += 1
    print(f"checked={checked} (edge+fuzz) disagreements=0")
    print("status=pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
