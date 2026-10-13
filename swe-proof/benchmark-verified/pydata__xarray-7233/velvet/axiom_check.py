#!/usr/bin/env python3
"""G-AX executable soundness check for pydata__xarray-7233.

This bundle consumes NO axioms: the coordinate re-selection is concrete set
bookkeeping over name lists, spelled out in Solution.lean's pure/impl regions.
The only neighbouring callee the modeled operation relies on is the routine that
installs a chosen name-set as a container's coordinate names on an otherwise
coordinate-free rebuild — an UNCHANGED operation. G-AX validates the A-reference
property the deep model assumes about that real callee:

  (A-reference) the real `xarray.Dataset.set_coords(S)` is an IDENTITY on the
      coordinate-name set: after installing `S` on a rebuilt container whose
      variables include exactly the names in `S` (and possibly more), the
      resulting `set(ds.coords)` equals `S`. The model treats "the chosen
      coordinate name-set becomes the result's coordinate names" as exact; this
      check refutes that on the real callee over boundary + randomized inputs.

We also confirm the pure set-algebra identity the deep model encodes —
`(requestedDims ∩ coordNames) ∪ coordNames == coordNames` — holds for every
fuzzed pair, since that identity is the substance of `keptCoordNames`.

Imports only `xarray`/`numpy` (the repo's own deps, present in the instance
image). Exit 0 iff every obligation holds.
"""
import random
import sys

import numpy as np
import xarray as xr


def kept_coord_names(requested_dims, coord_names):
    """Reference of Solution.lean's keptCoordNames as a SET."""
    common = {k for k in requested_dims if k in coord_names}
    return common | set(coord_names)


def check_setcoords_identity(var_names, chosen):
    """Assert the real Dataset.set_coords(chosen) yields exactly `chosen` as the
    coordinate-name set, on a coordinate-free Dataset carrying `var_names`."""
    n = 6
    ds = xr.Dataset({name: ("d", np.arange(n)) for name in var_names})
    # set_coords requires the names to exist as variables; `chosen ⊆ var_names`.
    result = ds.set_coords(list(chosen))
    observed = set(result.coords)
    assert observed == set(chosen), (
        "set_coords name identity violated: chose %r, got coords %r"
        % (sorted(chosen), sorted(observed)))


def check_set_identity(requested_dims, coord_names):
    """Assert (requestedDims ∩ coordNames) ∪ coordNames == coordNames."""
    got = kept_coord_names(requested_dims, coord_names)
    assert got == set(coord_names), (
        "set-algebra identity violated: requested=%r coords=%r got=%r"
        % (requested_dims, sorted(coord_names), sorted(got)))


def main():
    pool = [f"n{i}" for i in range(8)]

    # --- A-reference: set_coords name identity, boundary cases --------------
    boundary_vars = [
        ["n0"],
        ["n0", "n1"],
        ["n0", "n1", "n2", "n3"],
        pool,
    ]
    for var_names in boundary_vars:
        # every subset-as-chosen up to a few sizes
        for ksize in range(0, len(var_names) + 1):
            chosen = var_names[:ksize]
            check_setcoords_identity(var_names, chosen)

    # --- A-reference: randomized fuzz ---------------------------------------
    rng = random.Random(7233)
    for _ in range(2000):
        m = rng.randint(1, len(pool))
        var_names = rng.sample(pool, m)
        ksize = rng.randint(0, m)
        chosen = rng.sample(var_names, ksize)
        check_setcoords_identity(var_names, chosen)

    # --- pure set-algebra identity the deep model encodes -------------------
    boundary_pairs = [
        ([], []),
        (["time"], []),
        ([], ["day"]),
        (["time"], ["day"]),
        (["time"], ["time", "day"]),
        (["time", "x"], ["time", "day", "lat"]),
    ]
    for req, coords in boundary_pairs:
        check_set_identity(req, coords)
    for _ in range(20000):
        req = rng.sample(pool, rng.randint(0, len(pool)))
        coords = rng.sample(pool, rng.randint(0, len(pool)))
        check_set_identity(req, coords)

    print("G-AX OK: set_coords name identity (A-reference) sound on %d boundary "
          "+ 2000 fuzz inputs; (W∩C)∪C==C identity sound on %d + 20000 fuzz pairs."
          % (sum(len(v) + 1 for v in boundary_vars), len(boundary_pairs)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
