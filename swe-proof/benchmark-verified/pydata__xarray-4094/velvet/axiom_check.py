#!/usr/bin/env python3
"""G-AX executable soundness check for pydata__xarray-4094.

Executes the REAL repo callee — `DataArray.sel({variable_dim: k}, drop=<flag>)
.squeeze(drop=True)` (xarray/core/dataarray.py:1964) — on stacked DataArrays
(the GH4094 single-dimension shape that triggers the bug, plus randomized fuzz
variants) and asserts that the deep model `sliceCoords` of Solution.lean is
faithful.

There is NO consumed axiom in this bundle; the only kind-A obligation is the
A-reference deep model:

  (A-reference, gold leg)  with drop=True, the extracted component's coordinate
      NAMES == sampleCoords  (Solution.lean: sliceCoords selDim sampleCoords
      keep:=false), and the transient selector label selDim is ABSENT.

  (discriminator, prepatch leg) with drop=False (the pre-patch behaviour), the
      extracted component's coordinate NAMES == sampleCoords + [selDim]
      (Solution.lean: sliceCoords ... keep:=true), and selDim is PRESENT. This
      confirms Solution_prepatch.lean faithfully models the bug.

  (roundtrip)  with drop=True, Dataset(data_dict) is identical(...) to the
      original Dataset; with drop=False it raises MergeError. This is exactly
      the FAIL_TO_PASS assertion `assert_identical(unstacked, data)`.

Imports only numpy + xarray (the repo under test). Exit 0 iff every obligation
holds.
"""
import sys
import random

import numpy as np
import xarray as xr
from xarray.core.merge import MergeError


def make_dataset(n_vars, sample_len, dtype):
    """Build a Dataset of `n_vars` single-(sample-)dimension variables sharing
    one sample coordinate 'x' of length `sample_len`. This is the GH4094 shape:
    every variable has exactly the sample dim, nothing else."""
    arr = xr.DataArray(
        np.arange(sample_len).astype(dtype),
        coords=[("x", list(range(sample_len)))],
    )
    data_vars = {}
    for j in range(n_vars):
        data_vars["v%d" % j] = arr.copy()
    return xr.Dataset(data_vars)


def extract_coords(stacked, variable_dim, k, drop):
    """The real repo op: extract one labeled component and read its coordinate
    NAMES (the modeled observable)."""
    sl = stacked.sel({variable_dim: k}, drop=drop).squeeze(drop=True)
    return sorted(str(c) for c in sl.coords)


def check_one(data, sample_dims, new_dim):
    stacked = data.to_stacked_array(new_dim, sample_dims=sample_dims)
    idx = stacked.indexes[new_dim]
    variable_dim = idx.names[0]          # the MultiIndex level NAME (selection key)
    variables = list(idx.levels[0])      # vars (the component labels)
    sel_dim = new_dim                    # selDim: the stacked dimension being
                                         # indexed; the residual scalar
                                         # coordinate left by .sel is named this
    sample_coords = sorted(sample_dims)  # sampleCoords (the shared sample dims)

    # selDim must not be one of the sample coordinates (Solution.lean require)
    assert sel_dim not in sample_coords, (
        "precondition violated: selector %r is a sample coordinate %r"
        % (sel_dim, sample_coords))

    # --- A-reference (gold leg, drop=True): coords == sampleCoords, no selDim
    gold_dict = {}
    for k in variables:
        coords_drop = extract_coords(stacked, variable_dim, k, drop=True)
        assert coords_drop == sample_coords, (
            "A-reference unsound (gold, drop=True): component %r coords=%r, "
            "model sliceCoords(keep=false)=%r" % (k, coords_drop, sample_coords))
        assert sel_dim not in coords_drop, (
            "gold leg: selector %r leaked onto component %r" % (sel_dim, k))
        gold_dict[k] = stacked.sel({variable_dim: k}, drop=True).squeeze(drop=True)

    # --- discriminator (prepatch leg, drop=False): coords == sampleCoords+[selDim]
    expected_keep = sorted(sample_coords + [sel_dim])
    for k in variables:
        coords_nodrop = extract_coords(stacked, variable_dim, k, drop=False)
        assert coords_nodrop == expected_keep, (
            "prepatch model unfaithful (drop=False): component %r coords=%r, "
            "model sliceCoords(keep=true)=%r" % (k, coords_nodrop, expected_keep))
        assert sel_dim in coords_nodrop, (
            "prepatch leg: selector %r should persist on component %r"
            % (sel_dim, k))

    # --- roundtrip: gold reassembly is identical; prepatch reassembly conflicts
    rebuilt = xr.Dataset(gold_dict)
    assert rebuilt.identical(data), (
        "roundtrip (gold, drop=True) not identical to original for "
        "sample_dims=%r vars=%r" % (sample_dims, variables))

    # the pre-patch path must fail to reassemble (the reported MergeError) when
    # the stacked dimension is the only non-sample dim (single-dim case)
    if len(variables) >= 2:
        nodrop_dict = {}
        raised = False
        try:
            for k in variables:
                nodrop_dict[k] = stacked.sel(
                    {variable_dim: k}).squeeze(drop=True)
            xr.Dataset(nodrop_dict)
        except MergeError:
            raised = True
        assert raised, (
            "prepatch path unexpectedly succeeded (no MergeError) for "
            "single-dim case sample_dims=%r vars=%r" % (sample_dims, variables))


def main():
    checks = 0

    # boundary: the exact GH4094 MCVE shape, plus close variants. The sample
    # dimension length is >= 2 so squeeze(drop=True) does NOT remove the sample
    # coordinate (that singleton-squeeze interaction is orthogonal to the drop
    # flag this change toggles; the F2P test uses length 3).
    boundary = [
        (2, 3, np.int64),     # the reported MCVE
        (2, 2, np.int64),     # smallest non-singleton sample dim
        (3, 4, np.float64),
        (2, 5, np.int64),
        (4, 2, np.float64),
        (5, 3, np.int64),
    ]
    for n_vars, sample_len, dtype in boundary:
        data = make_dataset(n_vars, sample_len, dtype)
        check_one(data, sample_dims=["x"], new_dim="y")
        checks += 1

    # randomized fuzz over the single-dim shape
    rng = random.Random(4094)
    for _ in range(200):
        n_vars = rng.randint(2, 6)
        sample_len = rng.randint(2, 8)
        dtype = rng.choice([np.int64, np.float64])
        data = make_dataset(n_vars, sample_len, dtype)
        check_one(data, sample_dims=["x"], new_dim="y")
        checks += 1

    print("G-AX OK: sliceCoords deep model (== real sel(drop=True).squeeze "
          "coordinate set) sound; prepatch (drop=False) faithfully leaves the "
          "selector coordinate and raises MergeError on reassembly; gold "
          "roundtrip identical. %d stacked-array shapes checked." % checks)
    return 0


if __name__ == "__main__":
    sys.exit(main())
