#!/usr/bin/env python3
"""G-AX — validate the single A-reference for pydata__xarray-6992.

The impl models the UNCHANGED callee `self.xindexes.get_all_coords(name)` DEEPLY
as the literal singleton `{name}` in the modeled domain (a plain single dimension
index). This is an A-reference (refinement.md op 2): it must equal what the REAL
callee returns. G-AX runs the real `Indexes.get_all_coords` on genuine
`xr.Dataset`s over boundary + fuzzed inputs and asserts:

    for a plain dimension coordinate `name` (its own PandasIndex, non-multi):
        set(ds.xindexes.get_all_coords(name)) == {name}

If the real callee ever returned MORE than `{name}` for such a coordinate, the
deep model would be unsound; G-AX would fail. (The convert-branch callee
`to_base_variable()` is identity on the name abstraction — no observable name
property to check — so it is not a consumed axiom.)

stdlib + numpy/xarray (present in the testbed). Pinned seed: 6992.
"""
import random
import sys

SEED = 6992
N = 40_000

try:
    import numpy as np
    import xarray as xr
except Exception as e:  # pragma: no cover
    print(f"import failure: {e}")
    print("status=error")
    sys.exit(2)


DIMS = ["x", "y", "z", "w", "t"]


def build(rng):
    ndims = rng.randint(1, 5)
    dims = rng.sample(DIMS, ndims)
    sizes = {d: rng.randint(1, 4) for d in dims}
    coords = {}
    indexed = []
    for d in dims:
        if rng.random() < 0.85:
            coords[d] = (d, np.arange(sizes[d]))
            indexed.append(d)
    data_vars = {}
    for i in range(rng.randint(0, 3)):
        d = rng.choice(dims)
        data_vars[f"v{i}"] = (d, np.arange(sizes[d], dtype=float))
    # optional non-index coordinate
    for i in range(rng.randint(0, 2)):
        d = rng.choice(dims)
        nm = f"c{i}"
        if nm not in coords and nm not in data_vars:
            coords[nm] = (d, np.arange(sizes[d]))
    ds = xr.Dataset(data_vars=data_vars, coords=coords)
    real_indexed = [d for d in indexed if d in set(ds._indexes)]
    return ds, real_indexed


def check_ds(ds, indexed):
    for name in indexed:
        idx = ds._indexes[name]
        if type(idx).__name__ == "PandasMultiIndex":
            continue  # out of modeled domain
        allc = set(ds.xindexes.get_all_coords(name))
        if allc != {name}:
            return (name, sorted(allc))
    return None


def main() -> int:
    checked = 0
    # boundary: minimal single-dim dataset
    ds = xr.Dataset(coords={"z": ("z", np.arange(1))})
    v = check_ds(ds, [d for d in ["z"] if d in set(ds._indexes)])
    if v:
        print(f"AXIOM VIOLATED (boundary): get_all_coords({v[0]}) = {v[1]} != {{{v[0]}}}")
        print("status=fail")
        return 1
    checked += 1

    rng = random.Random(SEED)
    trials = 0
    while trials < N:
        ds, indexed = build(rng)
        trials += 1
        if not indexed:
            continue
        v = check_ds(ds, indexed)
        if v:
            print(f"AXIOM VIOLATED: get_all_coords({v[0]}) = {v[1]} != {{{v[0]}}}")
            print("status=fail")
            return 1
        checked += 1

    print(f"checked={checked} plain-index coordinates; get_all_coords(name)=={{name}} holds")
    print("status=pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
