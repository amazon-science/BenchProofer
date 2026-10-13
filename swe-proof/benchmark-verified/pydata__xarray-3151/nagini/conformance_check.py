#!/usr/bin/env python3
"""G-CONF differential conformance check for pydata__xarray-3151 (nagini).

SHADOW: the impl region of model.py, copied VERBATIM below with the contract
calls stripped (`Invariant`/`Assert` lines removed; nothing else changed).
The model IS Python, so no transliteration is needed. The `@Pure` spec helper
`any_joined_nonmonotonic` is NOT called by the impl region (it appears only in
the contracts), so it is not carried over; there are no `@ContractOnly`
callees in this bundle (empty axioms region). The carrier is plain
`List[int]`, so no PSeq shim is needed.

ORACLE: the REAL patched repo behaviour the model models per mapping.md —
whether the post-concatenation monotonicity guard inside
`xarray.core.combine.combine_by_coords` rejects (raises its
"monotonic global indexes" ValueError) the combined result. The gate applies
patch.diff to /testbed before this script runs and sets PYTHONPATH=/testbed,
so `import xarray` resolves the PATCHED library.

Bridge (mapping.md section 2): a Requires-satisfying input is a pair of
parallel 0/1 flag lists (`is_joined`, `is_monotonic`), one entry per
coordinate dimension of the combined result. Each flag vector is realized as
a REAL combine scenario, deterministically:

  * dimension d with is_joined[d]==1: the coordinate VARIES between the input
    datasets — the grid has two tiles along d. is_monotonic[d]==1 uses tile
    coords [0,1] / [2,3] (combined index [0,1,2,3], monotonic increasing);
    is_monotonic[d]==0 uses [0,2] / [1,3] (each tile individually increasing,
    so the upstream per-dataset ordering inference succeeds and orders the
    tiles by first element, but the COMBINED index [0,2,1,3] is
    non-monotonic).
  * dimension d with is_joined[d]==0: a bystander — the coordinate is
    IDENTICAL on every input dataset (so it is not concatenated along).
    is_monotonic[d]==1 uses [0,1]; is_monotonic[d]==0 uses [0,2,1].

The input datasets form the full grid over the joined dimensions' tiles
(2**k datasets for k joined dimensions), each carrying one float data
variable spanning all dimensions. The oracle result (raised or not) is a
deterministic function of the flag vector, so it is memoized per vector; the
shadow is compared against it on every one of the >=1e5 inputs.

Extra direction probes: is_monotonic==1 abstracts "monotonic EITHER
direction"; besides the increasing realization above, two explicit scenarios
check a monotonically DECREASING joined coordinate against shadow([1],[1])
and shadow([1,0],[1,0]).

Input domain (the model's Requires): equal-length parallel lists with every
entry in {0,1}. Boundary: exhaustive over all vectors of dimension count
0..3 (85 pairs). Fuzz: 100000 vectors of dimension count 0..5 with at most
3 joined dimensions (keeps the realization grid <= 8 datasets); every fuzz
vector satisfies the Requires. Pinned fuzz seed: 3151.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib + numpy (a repo dependency) only.
"""
import itertools
import random
import sys

SEED = 3151
N_FUZZ = 100_000

# The modeled guard's ValueError message fragment. The upstream ordering
# inference uses a DIFFERENT message ("neither monotonically increasing nor
# ..."); the realizations below keep every dataset's varying coordinate
# individually increasing (or, in the direction probes, decreasing) precisely
# so that upstream guard never fires — reaching it is a scenario bug and is
# surfaced loudly, never conflated with the modeled verdict.
_GUARD_MSG = "monotonic global indexes"


# --- the impl region of model.py, verbatim (contract calls stripped) ---------

def guard_rejects(is_joined, is_monotonic):
    # Inspect only the dimensions that were joined along; a non-monotonic
    # joined dimension triggers rejection. Carried-through dimensions are
    # never inspected. Walk right-to-left so the front-recursive existential
    # unfolds one dimension per step.
    rejected = False  # type: bool
    i = len(is_joined)
    while i > 0:
        if is_joined[i - 1] == 1:
            if is_monotonic[i - 1] == 0:
                rejected = True
        i = i - 1
    return rejected


# --- oracle: the real patched combine_by_coords -------------------------------

# Per-dimension coordinate realizations (see module docstring).
_JOINED_TILES = {
    1: ([0, 1], [2, 3]),   # combined [0,1,2,3]: monotonic increasing
    0: ([0, 2], [1, 3]),   # combined [0,2,1,3]: non-monotonic
}
_BYSTANDER_COORD = {
    1: [0, 1],             # monotonic
    0: [0, 2, 1],          # non-monotonic, identical on every dataset
}


def _build_datasets(np, xr, is_joined, is_monotonic):
    """Realize a flag vector as the full grid of real Datasets."""
    n = len(is_joined)
    dims = ["d%d" % k for k in range(n)]
    joined_positions = [k for k in range(n) if is_joined[k] == 1]
    datasets = []
    fill = 0.0
    for tile_choice in itertools.product((0, 1), repeat=len(joined_positions)):
        tile_of = dict(zip(joined_positions, tile_choice))
        coords = {}
        shape = []
        for k in range(n):
            if is_joined[k] == 1:
                coord = _JOINED_TILES[is_monotonic[k]][tile_of[k]]
            else:
                coord = _BYSTANDER_COORD[is_monotonic[k]]
            coords[dims[k]] = list(coord)
            shape.append(len(coord))
        data = np.full(shape, fill, dtype=float)
        fill += 1.0
        datasets.append(xr.Dataset(data_vars={"data": (dims, data)},
                                   coords=coords))
    return datasets


def _combine_rejects(xr, datasets):
    """Run the real combine_by_coords; True iff the modeled guard raises.
    Any other exception means the scenario construction is broken and is
    re-raised loudly (never folded into the verdict)."""
    try:
        xr.combine_by_coords(datasets)
        return False
    except ValueError as e:
        if _GUARD_MSG in str(e):
            return True
        raise AssertionError(
            "scenario tripped a NON-modeled guard (expected only the %r "
            "ValueError): %s" % (_GUARD_MSG, e))


def make_oracle(np, xr):
    cache = {}

    def oracle(is_joined, is_monotonic):
        key = (tuple(is_joined), tuple(is_monotonic))
        if key not in cache:
            datasets = _build_datasets(np, xr, is_joined, is_monotonic)
            cache[key] = _combine_rejects(xr, datasets)
        return cache[key]

    return oracle, cache


# --- input generation ---------------------------------------------------------

def boundary_vectors():
    """Exhaustive over all Requires-satisfying vectors of dimension 0..3."""
    for n in range(0, 4):
        for is_joined in itertools.product((0, 1), repeat=n):
            for is_monotonic in itertools.product((0, 1), repeat=n):
                yield list(is_joined), list(is_monotonic)


def fuzz_vector(rng):
    n = rng.randint(0, 5)
    is_joined = [rng.randint(0, 1) for _ in range(n)]
    # cap joined dimensions at 3 so the realization grid stays <= 8 datasets
    joined_positions = [k for k in range(n) if is_joined[k] == 1]
    while len(joined_positions) > 3:
        is_joined[joined_positions.pop(rng.randrange(len(joined_positions)))] = 0
    is_monotonic = [rng.randint(0, 1) for _ in range(n)]
    return is_joined, is_monotonic


# --- direction probes: decreasing global coordinate is still monotonic --------

def check_decreasing_probes(np, xr):
    """A joined coordinate whose COMBINED index runs monotonically decreasing
    (tiles [3,2] and [1,0], each individually decreasing) must map to
    is_monotonic==1 and hence not be rejected; with and without a
    non-monotonic bystander alongside."""
    failures = []
    # probe 1: single decreasing joined dimension
    ds_hi = xr.Dataset(data_vars={"data": (["d0"], np.zeros(2))},
                       coords={"d0": [3, 2]})
    ds_lo = xr.Dataset(data_vars={"data": (["d0"], np.ones(2))},
                       coords={"d0": [1, 0]})
    real = _combine_rejects(xr, [ds_hi, ds_lo])
    shadow = guard_rejects([1], [1])
    if real != shadow:
        failures.append(("decreasing-joined", [1], [1], shadow, real))
    # probe 2: decreasing joined dimension + non-monotonic bystander
    yb = _BYSTANDER_COORD[0]
    ds_hi2 = xr.Dataset(data_vars={"data": (["d0", "d1"], np.zeros((2, 3)))},
                        coords={"d0": [3, 2], "d1": yb})
    ds_lo2 = xr.Dataset(data_vars={"data": (["d0", "d1"], np.ones((2, 3)))},
                        coords={"d0": [1, 0], "d1": yb})
    real2 = _combine_rejects(xr, [ds_hi2, ds_lo2])
    shadow2 = guard_rejects([1, 0], [1, 0])
    if real2 != shadow2:
        failures.append(("decreasing-joined+bystander", [1, 0], [1, 0],
                         shadow2, real2))
    return failures


def main():
    import numpy as np
    import xarray as xr

    oracle, cache = make_oracle(np, xr)
    checked = 0

    def compare(is_joined, is_monotonic):
        shadow_out = guard_rejects(is_joined, is_monotonic)
        real_out = oracle(is_joined, is_monotonic)
        if shadow_out != real_out:
            print("DISAGREEMENT")
            print("  is_joined=%r is_monotonic=%r" % (is_joined, is_monotonic))
            print("  shadow=%r" % (shadow_out,))
            print("  real=%r" % (real_out,))
            return False
        return True

    n_boundary = 0
    for is_joined, is_monotonic in boundary_vectors():
        if not compare(is_joined, is_monotonic):
            return 1
        n_boundary += 1
        checked += 1

    rng = random.Random(SEED)
    for _ in range(N_FUZZ):
        is_joined, is_monotonic = fuzz_vector(rng)
        if not compare(is_joined, is_monotonic):
            return 1
        checked += 1

    probe_failures = check_decreasing_probes(np, xr)
    if probe_failures:
        for tag, is_joined, is_monotonic, shadow_out, real_out in probe_failures:
            print("DISAGREEMENT (%s)" % tag)
            print("  is_joined=%r is_monotonic=%r" % (is_joined, is_monotonic))
            print("  shadow=%r" % (shadow_out,))
            print("  real=%r" % (real_out,))
        return 1

    print("G-CONF OK: shadow impl (guard_rejects) == real patched "
          "combine_by_coords guard on %d inputs (%d exhaustive boundary + "
          "%d fuzz, seed %d; %d distinct realized scenarios) + 2 decreasing-"
          "direction probes, 0 disagreements."
          % (checked, n_boundary, N_FUZZ, SEED, len(cache)))
    import json
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "distinct_scenarios": len(cache),
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
