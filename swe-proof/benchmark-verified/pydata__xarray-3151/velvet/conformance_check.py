#!/usr/bin/env python3
"""G-CONF differential conformance check for pydata__xarray-3151 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region transliterated to
              Python: `dimOK` / `allDimsOK` over a `List Dimension`, with the
              deep order test `isMonoInc`/`isMonoDec` inlined (the A-reference
              callee, validated separately by axiom_check.py/G-AX). Result is the
              boolean `ok` (True ⇔ validation succeeds ⇔ no ValueError).
  * ORACLE  — `patch.diff`'s behaviour: the patched `combine_by_coords` applied
              at base_commit (the real correctness oracle, G-RESOLVE). We observe
              whether it raises the "monotonic global indexes" ValueError.

Bridge (mapping.md §2): a scenario specifies, for two datasets ds1/ds2, a
concat axis `x` (values differ between datasets ⇒ `Dimension.varies = True`) and
a bystander axis `y` (identical coords on both ⇒ `varies = False`). The SHADOW
builds the corresponding `List Dimension` (x: varies, global concatenated ranks;
y: non-varying, its ranks); the ORACLE builds the real Datasets and runs the
patched combine. They must agree: `ok_shadow == (not raised)`.

The expensive real-combine oracle is memoized per distinct scenario shape, so we
compare on >=10^5 fuzzed inputs while invoking xarray only once per shape. Exit 0
iff zero disagreements; any disagreement is a mechanical R/I counterexample.

Runs in-container (the prebuilt SWE-Bench instance image); the gold patch is
applied before this runs. Imports xarray/numpy (repo deps) + stdlib only. The
fuzz seed is pinned (mapping.md §4) for a deterministic verdict.
"""
import random
import sys

SEED = 3151
N_FUZZ = 100_000

MONOTONIC_ERR = "monotonic global indexes"


# --- the R/I shadow: Solution.lean dimOK/allDimsOK, transliterated -----------

def _iso_mono_inc(xs):
    return all(xs[k] <= xs[k + 1] for k in range(len(xs) - 1))


def _iso_mono_dec(xs):
    return all(xs[k] >= xs[k + 1] for k in range(len(xs) - 1))


def _is_monotonic(xs):
    return _iso_mono_inc(xs) or _iso_mono_dec(xs)


def _dim_ok(varies, index):
    # dimOK d = !d.varies || isMonotonic d.index
    return (not varies) or _is_monotonic(index)


def shadow_ok(dims):
    """allDimsOK: True iff every axis meets its obligation. `dims` is a list of
    (varies, index) pairs — the R/I image of `List Dimension`."""
    return all(_dim_ok(varies, index) for (varies, index) in dims)


# --- the oracle: patch.diff behaviour (real patched combine_by_coords) --------

def _scenario_to_datasets(scn):
    """Build (ds1, ds2) realizing a scenario. `scn` = (x1, x2, ycoord) where x1,
    x2 are the per-dataset concat-axis integer coords (each individually sorted
    ascending, x1[0] < x2[0]) and ycoord is the identical bystander axis coord
    shared by both datasets."""
    import numpy as np
    import xarray as xr
    x1, x2, ycoord = scn
    ny = len(ycoord)
    d1 = np.zeros((len(x1), ny))
    d2 = np.zeros((len(x2), ny))
    ds1 = xr.Dataset(data_vars=dict(data=(['x', 'y'], d1)),
                     coords=dict(x=list(x1), y=list(ycoord)))
    ds2 = xr.Dataset(data_vars=dict(data=(['x', 'y'], d2)),
                     coords=dict(x=list(x2), y=list(ycoord)))
    return ds1, ds2


def oracle_ok(scn):
    """Run the patched combine_by_coords; return True iff it does NOT raise the
    monotonic-global-indexes ValueError. Any other failure is a malformed
    scenario and re-raises (loud, not silently masked)."""
    import xarray as xr
    ds1, ds2 = _scenario_to_datasets(scn)
    try:
        xr.combine_by_coords([ds1, ds2])
        return True
    except ValueError as e:
        if MONOTONIC_ERR in str(e):
            return False
        raise


# --- scenario generation -----------------------------------------------------

def _ranks(values):
    """Order-rank carrier (mapping.md §2): map values to dense ranks preserving
    order. For the bystander y this matches the resulting index's order type."""
    order = {v: i for i, v in enumerate(sorted(set(values), key=lambda z: (str(type(z)), z)))}
    return [order[v] for v in values]


def gen_scenario(rng):
    """Yield (scn, dims) where scn drives the oracle and dims drives the shadow.

    x axis (concat / varies=True): two per-dataset blocks `base1`, `base2`, each
    sorted ascending and individually distinct (so each dataset's x index is
    monotonic increasing — required by `_infer_concat_order_from_coords`), with
    base1[0] < base2[0] so the datasets order as [ds1, ds2] and the global concat
    coord is base1 ++ base2. Whether that global coord is monotonic — and hence
    whether the post-patch check raises — is left to the random draw; the shadow
    predicts it from the ranks. base1[0] != base2[0] keeps the inferred tile
    positions distinct.
    y axis (bystander / varies=False): identical coords on both datasets;
    monotonic or not, independently — must never affect the outcome post-patch."""
    n1 = rng.randint(1, 4)
    n2 = rng.randint(1, 4)
    base1 = sorted(rng.sample(range(0, 30), n1))
    base2 = sorted(rng.sample(range(0, 30), n2))
    # guarantee base1[0] < base2[0] (dataset order [ds1, ds2], distinct positions)
    if base1[0] >= base2[0]:
        base1, base2 = (base1, base2) if base1[0] < base2[0] else (
            ([base1[0] - 1] + base1) if base1[0] > 0 else base1,
            base2)
        # simplest robust fix: shift base2 up so its first strictly exceeds base1[0]
        shift = base1[0] + 1 - base2[0]
        if shift > 0:
            base2 = [v + shift for v in base2]
    # bystander y: identical coords on both datasets
    ny = rng.randint(1, 4)
    if rng.random() < 0.5:
        ycoord = sorted(rng.sample(range(0, 10), ny))            # monotonic
    else:
        ycoord = rng.sample(range(0, 10), ny)                    # possibly not
    scn = (tuple(base1), tuple(base2), tuple(ycoord))

    global_x = list(base1) + list(base2)
    dims = [
        (True, _ranks(global_x)),     # concat axis x: varies
        (False, _ranks(ycoord)),      # bystander axis y: non-varying
    ]
    return scn, dims


def boundary_scenarios():
    """Curated cases incl. the issue's exact MCVE shape and all four
    (varies x monotonic) dimOK combinations."""
    out = []
    # MCVE: x=[1,2,3]/[4,5,6,7] (monotonic concat), y=['a','c','b'] non-mono bystander
    out.append(((1, 2, 3), (4, 5, 6, 7), (0, 2, 1)))   # y ranks of a,c,b
    # bystander y monotonic
    out.append(((1, 2, 3), (4, 5, 6, 7), (0, 1, 2)))
    # non-monotonic GLOBAL concat axis (must raise even post-patch)
    out.append(((0, 1, 5), (2, 3, 4), (0, 1, 2)))
    out.append(((0, 1, 5), (2, 3, 4), (0, 2, 1)))      # + non-mono bystander
    # singletons
    out.append(((0,), (1,), (0,)))
    out.append(((0,), (1,), (0, 2, 1)))
    return out


def main():
    rng = random.Random(SEED)
    cache = {}            # scn -> oracle_ok (memoize the expensive real combine)
    disagreements = []
    count = 0

    def compare(scn, dims):
        nonlocal count
        count += 1
        sh = shadow_ok(dims)
        if scn in cache:
            orc = cache[scn]
        else:
            orc = oracle_ok(scn)
            cache[scn] = orc
        if sh != orc:
            disagreements.append((scn, sh, orc))

    # boundary cases first
    for scn in boundary_scenarios():
        global_x = list(scn[0]) + list(scn[1])
        dims = [(True, _ranks(global_x)), (False, _ranks(list(scn[2])))]
        compare(scn, dims)
        if len(disagreements) >= 5:
            break

    # fuzz
    while count < N_FUZZ and len(disagreements) < 5:
        scn, dims = gen_scenario(rng)
        compare(scn, dims)

    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for scn, sh, orc in disagreements:
            print("  scenario=%r shadow_ok=%r oracle_ok=%r" % (scn, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of validateOrdering agrees with patch.diff "
          "behaviour on %d inputs (seed=%d, %d distinct scenarios), "
          "0 disagreements." % (count, SEED, len(cache)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
