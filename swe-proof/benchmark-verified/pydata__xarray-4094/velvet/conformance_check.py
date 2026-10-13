#!/usr/bin/env python3
"""G-CONF differential conformance check for pydata__xarray-4094 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region transliterated
              to Python over the real repo types, via the mapping.md bijection.
              `toComponents` builds, for each component label, the coordinate-
              NAME set its extracted component carries; the gold extraction
              (`sliceCoords ... keep:=false`) discards the transient selector
              label, so each component's coordinate names == the shared sample
              coordinates. There is no A-consumed op in the impl region
              (sliceCoords is the A-reference deep model, an I-op for G-CONF).
  * ORACLE  — `patch.diff`'s behaviour: the patched
              `DataArray.to_unstacked_dataset` applied at base_commit (the real
              correctness oracle, G-RESOLVE). We observe each rebuilt component's
              coordinate-name set, plus the labels (dict keys) and the success of
              reassembly.

They must agree on every input. Exit 0 iff zero disagreements; any disagreement
is a mechanical R/I-fidelity counterexample.

Runs in-container (the prebuilt SWE-Bench instance image with patch.diff
applied), numpy + xarray only. The fuzz seed is pinned (mapping.md §4).
"""
import random
import sys

import numpy as np
import xarray as xr

SEED = 4094
N_FUZZ = 400


# --- the R/I shadow: Solution.lean toComponents/sliceCoords, transliterated ---
def shadow_components(sel_dim, sample_coords, variables):
    """expectedComponents sampleCoords vars, with sliceCoords keep:=false (gold).
    Returns an ordered list of (label, sorted-coord-names)."""
    out = []
    for k in variables:
        # sliceCoords selDim sampleCoords false  ==  sampleCoords
        out.append((k, sorted(sample_coords)))
    return out


# --- the oracle: the patched to_unstacked_dataset's observable behaviour ------
def oracle_components(data, new_dim, sample_dims):
    """Run the patched DataArray.to_unstacked_dataset and read back, per
    component label, the coordinate-name set it carries (plus label order)."""
    stacked = data.to_stacked_array(new_dim, sample_dims=sample_dims)
    unstacked = stacked.to_unstacked_dataset(new_dim)   # patched: drop=True
    out = []
    for k in list(unstacked.data_vars):
        coords = sorted(str(c) for c in unstacked[k].coords)
        out.append((str(k), coords))
    return out, unstacked, stacked


def make_dataset(n_vars, sample_len, dtype):
    arr = xr.DataArray(
        np.arange(sample_len).astype(dtype),
        coords=[("x", list(range(sample_len)))],
    )
    return xr.Dataset({"v%d" % j: arr.copy() for j in range(n_vars)})


def fuzz_specs(n, rng):
    # boundary cases first
    yield (2, 3, np.int64)      # the reported MCVE
    yield (2, 2, np.int64)
    yield (3, 4, np.float64)
    yield (4, 2, np.int64)
    yield (5, 3, np.float64)
    for _ in range(n):
        yield (rng.randint(2, 6), rng.randint(2, 8),
               rng.choice([np.int64, np.float64]))


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0
    new_dim = "y"
    sample_dims = ["x"]
    sample_coords = list(sample_dims)

    for n_vars, sample_len, dtype in fuzz_specs(N_FUZZ, rng):
        count += 1
        data = make_dataset(n_vars, sample_len, dtype)
        oracle, unstacked, stacked = oracle_components(data, new_dim, sample_dims)
        labels = [lbl for lbl, _ in oracle]
        shadow = shadow_components(new_dim, sample_coords, labels)

        # (1) coordinate-name sets agree component-by-component (R/I leg A4/A6)
        if shadow != oracle:
            disagreements.append(("coords", (n_vars, sample_len, str(dtype)),
                                  shadow, oracle))
        # (2) the transient selector label is absent from every component (A6)
        for lbl, coords in oracle:
            if new_dim in coords:
                disagreements.append(("selDim-present", (n_vars, sample_len),
                                      lbl, coords))
        # (3) roundtrip identical to the original (the F2P assertion)
        if not unstacked.identical(data):
            disagreements.append(("roundtrip", (n_vars, sample_len, str(dtype)),
                                  "not-identical", None))

        if len(disagreements) >= 5:
            break

    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for kind, spec, a, b in disagreements:
            print("  [%s] spec=%r left=%r right=%r" % (kind, spec, a, b))
        return 1
    print("G-CONF OK: R/I shadow of toComponents agrees with patch.diff "
          "behaviour on %d stacked-array shapes (seed=%d), 0 disagreements."
          % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
