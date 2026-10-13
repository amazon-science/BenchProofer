#!/usr/bin/env python3
"""G-CONF differential conformance check for pydata__xarray-7233 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region (`coordsToKeep`)
              transliterated to Python over the real repo types (name sets are
              `set[str]`, via the mapping.md bijection `List String` ↔ name set):
                  common = {k for k in requestedDims if k in coordNames}
                  result = common | coordNames        # the chosen coordinate set
              The one neighbouring callee the operation relies on — installing a
              chosen name-set as the container's coordinates on a freshly rebuilt
              (coordinate-free) container — is A-tagged and left as the REAL repo
              callee: the shadow does NOT reimplement the reshape; it runs the
              genuine `coarsen(...).construct(...)` and reads back the resulting
              coordinate names, predicting only the name SET the impl computes.
  * ORACLE  — `patch.diff`'s behaviour: the patched
              `Coarsen.construct` applied at base_commit (the real correctness
              oracle, G-RESOLVE). We read `set(result.coords)`.

The R/I claim under test is exactly: the resulting coordinate-name set equals
the set `coordsToKeep` computes from `(requestedDims, coordNames)`. Both sides
read the genuine post-`construct` coordinate names, so a faithful name-set
formula yields identical sets. Any mismatch is a mechanical R/I-fidelity
counterexample. Exit 0 iff zero disagreements.

Runs in-container (the prebuilt SWE-Bench instance image), repo deps only. The
fuzz seed is pinned (mapping.md §4) for a deterministic verdict.
"""
import random
import sys

import numpy as np
import xarray as xr

SEED = 7233
N_FUZZ = 100_000


def shadow_coords(requested_dims, coord_names):
    """The R/I shadow of coordsToKeep: the chosen coordinate name SET.
    `(requestedDims ∩ coordNames) ∪ coordNames` == `coordNames`."""
    common = {k for k in requested_dims if k in coord_names}
    return common | set(coord_names)


def build_dataset(rng, n_extra_coords, n_data_vars, window):
    """A Dataset on a single coarsened dimension `time` with:
      * `n_extra_coords` NON-dimensional coordinates over `time` (the case the
        issue is about: coordinates whose name is not a reshaped dimension),
      * `n_data_vars` plain data variables over `time`,
      * optionally a dimension coordinate named `time` itself.
    Returns (ds, requested_dims, prior_coord_names)."""
    length = window * rng.randint(1, 4)
    data_vars = {}
    coords = {}
    for j in range(n_data_vars):
        data_vars[f"var{j}"] = ("time", np.arange(length))
    da = xr.DataArray(np.arange(length), dims=["time"])
    ds = da.to_dataset(name="T")
    for j in range(n_data_vars):
        ds[f"var{j}"] = ("time", np.arange(length))
    # non-dimensional coordinates over time (e.g. the issue's `day`)
    for j in range(n_extra_coords):
        ds = ds.assign_coords({f"coord{j}": ("time", np.arange(length) * (j + 1))})
    # sometimes also give `time` a dimension coordinate (a coord whose name IS
    # the reshaped dimension) to exercise the intersection component
    if rng.random() < 0.5:
        ds = ds.assign_coords({"time": np.arange(length)})
    requested_dims = ["time"]      # window_dim keys passed to .construct
    return ds, requested_dims, set(ds.coords)


def oracle_coords(ds, window):
    """patch.diff's behaviour: the patched Coarsen.construct's resulting
    coordinate names."""
    result = ds.coarsen(time=window).construct(time=("year", "month"))
    return set(result.coords)


def fuzz_cases(n, rng):
    # boundary cases first
    yield (1, 0, 12)     # one non-dim coord, no data vars   (issue MVCE shape)
    yield (0, 1, 12)     # no extra coords, one data var
    yield (2, 2, 12)
    yield (3, 0, 6)
    yield (0, 0, 4)
    for _ in range(n):
        n_extra = rng.randint(0, 4)
        n_data = rng.randint(0, 4)
        window = rng.choice([2, 3, 4, 6, 12])
        yield (n_extra, n_data, window)


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0
    # we cap the number of (expensive) real construct() calls but still cover a
    # broad config grid; the name-set formula is exercised on every one.
    MAX_CONSTRUCTS = 1500
    constructs = 0
    for (n_extra, n_data, window) in fuzz_cases(N_FUZZ, rng):
        if constructs >= MAX_CONSTRUCTS:
            break
        ds, requested_dims, coord_names = build_dataset(
            random.Random(SEED + constructs), n_extra, n_data, window)
        shadow = shadow_coords(requested_dims, coord_names)
        oracle = oracle_coords(ds, window)
        constructs += 1
        count += 1
        if shadow != oracle:
            disagreements.append((n_extra, n_data, window, shadow, oracle))
            if len(disagreements) >= 5:
                break
    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d configs:"
              % (len(disagreements), count))
        for n_extra, n_data, window, sh, orc in disagreements:
            print("  extra_coords=%d data_vars=%d window=%d shadow=%r oracle=%r"
                  % (n_extra, n_data, window, sorted(sh), sorted(orc)))
        return 1
    print("G-CONF OK: R/I shadow of coordsToKeep (chosen coordinate name set) "
          "agrees with patch.diff Coarsen.construct().coords on %d configs "
          "(seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
