#!/usr/bin/env python3
"""G-CONF differential conformance check for pydata__xarray-4356 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region transliterated
              to Python via the mapping.md bijection. The decision for one output
              cell of a reduction is `cellMissing`, branching on whether the
              output keeps a dimension:
                if remainingDimCount >= 1 (array branch):
                    missing := prodList(reducedSizes) < missingCount + requiredCount
                else (scalar branch, the whole input collapses to one value):
                    missing := fillAdmissible and (totalSize - missingCount < requiredCount)
              where prodList is the backward product fold (R/I ops) and
              fillAdmissible is the dtype-guard (R bridge, see below). There is no
              A-tagged callee in the computed `out` (the only modeled callee, the
              `.prod()`, is the deep model `prodList` itself, an A-reference
              handled by G-AX; here it is transliterated as the R/I product).
  * ORACLE  — the REAL gold-patched `xarray.core.nanops._maybe_null_out`
              IMPORTED FROM THE PATCHED REPO (not inlined), driven on real numpy
              arrays. We read off, per output cell, whether the patched code
              replaced it with the fill value (NaN).

They must agree on every input. Both BRANCHES of `_maybe_null_out` are exercised:

  * array branch  (result.ndim >= 1): reduction over a STRICT subset of axes;
    the gold patch changed the element count `mask.shape[axis]` ->
    `np.take(mask.shape, axis).prod()`. Modeled by the product decision.
  * scalar branch (result.ndim == 0): reduction over ALL axes (the F2P scenario,
    `da.sum(dim=["x","y","z"])`); the real post-gold guard is
    `getattr(result, "dtype", None) not in dtypes.NAT_TYPES`. Because of numpy's
    NaT-comparison quirk `np.dtype('float64') in dtypes.NAT_TYPES` is True, so a
    float64 result NEVER nulls out while a float32 result DOES; the spec models
    this exactly via `fillAdmissible = (result.dtype not in dtypes.NAT_TYPES)`.

`fillAdmissible` is read off the SAME real `result` the oracle feeds to
`_maybe_null_out`, so the shadow and oracle agree by construction iff the spec's
scalar formula matches the real guarded null-out. The raise-removal (the deleted
multi-dim ValueError) is modeled by `out` always being `Except.ok`; here the
oracle never raises (post-patch), confirming completion on every multi-dim input.

Runs in-container (the prebuilt SWE-Bench instance image) against the patched
repo. The fuzz seed is pinned (mapping.md §4) for a deterministic verdict.
Exit 0 iff zero disagreements; any disagreement is a mechanical R/I-fidelity
counterexample.
"""
import random
import sys

import numpy as np

# the REAL gold-patched function + the real NAT_TYPES, imported from the repo.
from xarray.core import dtypes
from xarray.core.nanops import _maybe_null_out

SEED = 4356
N_FUZZ = 100_000


# --- the R/I shadow: Solution.lean prodList + cellMissing ---------------------
def prod_list(sizes):
    """prodList transliterated: prodList [] = 1; (x::xs) = x * prodList xs."""
    total = 1
    for s in sizes:
        total = s * total
    return total


def cell_missing(remaining_dim_count, reduced_sizes, total_size,
                 missing_count, required_count, fill_admissible):
    """cellMissing transliterated: the per-cell missing decision, branching on
    whether the output keeps a dimension."""
    if remaining_dim_count >= 1:
        return prod_list(reduced_sizes) < missing_count + required_count
    else:
        return fill_admissible and (total_size - missing_count < required_count)


# --- the oracle: the REAL patched _maybe_null_out on real numpy arrays --------
def oracle_missing_cells(result, axis, mask, min_count):
    """Drive the patched code and read off, per output cell, whether it was
    replaced by the fill value (NaN). `result` is the actual reduction value;
    a NaN in the post-call output marks a cell the patched code nulled out."""
    out = _maybe_null_out(result, axis, mask, min_count)
    out_arr = np.asarray(out, dtype=float)
    flat = np.atleast_1d(out_arr).ravel()
    return [bool(np.isnan(v)) for v in flat]


def shadow_missing_cells(result, shape, axis, mask, min_count):
    """Per-output-cell shadow decision, aligned with oracle_missing_cells, over
    BOTH branches. For the scalar branch (result.ndim == 0) fillAdmissible is the
    real dtype guard read off `result`; reducedSizes/totalSize per the mapping."""
    remaining = int(getattr(result, "ndim", 0))
    fill_admissible = getattr(result, "dtype", None) not in dtypes.NAT_TYPES
    total_size = int(mask.size)
    if remaining >= 1:
        axes = tuple(np.atleast_1d(axis))
        reduced_sizes = [int(shape[a]) for a in axes]
        missing = np.atleast_1d(mask.sum(axis=axis)).ravel()
        return [cell_missing(remaining, reduced_sizes, total_size, int(m),
                             min_count, fill_admissible) for m in missing]
    else:
        # all-dims reduction: a single output cell collapsing every element.
        missing = int(mask.sum())
        return [cell_missing(remaining, [], total_size, missing, min_count,
                             fill_admissible)]


def make_result(shape, axis, dtype):
    """The reduction value `_maybe_null_out` is called with — built by an actual
    reduction so its ndim/shape/dtype match the real call site."""
    base = np.zeros(shape, dtype=dtype)
    if axis is None:
        return base.astype(float).sum()  # scalar, float (the ndim==0 / dim=... path)
    return base.astype(float).sum(axis=tuple(np.atleast_1d(axis)))


def gen_array_case(rng):
    """ARRAY branch: reduction over a STRICT subset of axes -> result ndim >= 1
    (the branch the gold patch's `np.take(...).prod()` count changed)."""
    ndim = rng.randint(2, 4)
    shape = tuple(rng.randint(1, 5) for _ in range(ndim))
    k = rng.randint(1, ndim - 1)
    axes = sorted(rng.sample(range(ndim), k))
    axis = tuple(axes) if len(axes) > 1 else axes[0]
    mask = np.zeros(shape, dtype=bool)
    flat = mask.ravel()
    p = rng.choice([0.0, 0.2, 0.5, 0.9, 1.0])
    for i in range(flat.size):
        if rng.random() < p:
            flat[i] = True
    mask = flat.reshape(shape)
    # min_count from 0 (the spec has NO precondition: requiredCount = 0 is a
    # modeled input — the real code then never nulls out, and so must the shadow)
    min_count = rng.randint(0, max(2, int(np.prod([shape[a] for a in np.atleast_1d(axis)])) + 1))
    dtype = rng.choice([np.float64, np.float32, np.int64])
    result = make_result(shape, axis, dtype)
    return result, shape, axis, mask, min_count


def gen_scalar_case(rng):
    """SCALAR branch: reduction over ALL axes (the F2P scenario) -> result ndim 0.
    Vary the result dtype (float64 vs float32) to exercise BOTH sides of the
    NAT_TYPES guard. axis is a tuple of all axes (multi-dim, sequence-named) OR
    None (the ellipsis path) -- the gold removed the raise on the tuple form."""
    ndim = rng.randint(1, 4)
    shape = tuple(rng.randint(1, 5) for _ in range(ndim))
    mask = np.zeros(shape, dtype=bool)
    flat = mask.ravel()
    p = rng.choice([0.0, 0.2, 0.5, 0.9, 1.0])
    for i in range(flat.size):
        if rng.random() < p:
            flat[i] = True
    mask = flat.reshape(shape)
    # min_count from 0: the requiredCount = 0 slice is spec-pinned (no require)
    min_count = rng.randint(0, max(2, int(np.prod(shape)) + 1))
    dtype = rng.choice([np.float64, np.float32])
    # all-axes reduction -> ndim 0 scalar; result dtype follows the input dtype.
    base = np.zeros(shape, dtype=dtype)
    result = base.sum()  # 0-d, dtype preserved (float32 stays float32)
    axis = tuple(range(ndim))  # multi-dim sequence axis (the raise-removed path)
    return result, shape, axis, mask, min_count


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0

    # boundary cases spanning both branches, incl. the exact original-audit
    # counterexamples (scalar float64 never nulls; float32 does).
    def scalar_result(shape, dtype):
        return np.zeros(shape, dtype=dtype).sum()
    boundary = [
        # array branch: 2 of 3 axes (product != single size = the fix content)
        (scalar_result((2, 3, 4), float).sum() if False else np.zeros((2, 3, 4)).sum(axis=(0, 1)),
         (2, 3, 4), (0, 1), np.zeros((2, 3, 4), dtype=bool), 3),
        (np.zeros((2, 3, 4)).sum(axis=(0, 1)), (2, 3, 4), (0, 1), np.ones((2, 3, 4), dtype=bool), 3),
        (np.zeros((2, 3, 4)).sum(axis=(1, 2)), (2, 3, 4), (1, 2), np.zeros((2, 3, 4), dtype=bool), 5),
        # scalar branch float64 (dead null-out): (2,3) 1-present min_count=5 -> NOT missing
        (scalar_result((2, 3), np.float64), (2, 3), (0, 1),
         np.array([[False, True, True], [True, True, True]]), 5),
        # scalar branch float32 (live null-out): same shape -> IS missing (present<min_count)
        (scalar_result((2, 3), np.float32), (2, 3), (0, 1),
         np.array([[False, True, True], [True, True, True]]), 5),
        # scalar branch float64 smallest witnesses from the audit
        (scalar_result((1,), np.float64), (1,), (0,), np.array([True]), 2),
        (scalar_result((1, 1), np.float64), (1, 1), (0, 1), np.array([[True]]), 1),
        # scalar branch float32 fully-present (never missing)
        (scalar_result((1,), np.float32), (1,), (0,), np.array([False]), 1),
        # min_count = 0 (the previously-unpinned slice; the round-4 audit's
        # atk_3 differed from gold exactly here): never missing, both branches,
        # even with EVERYTHING missing.
        (np.zeros((2, 3, 4)).sum(axis=(0, 1)), (2, 3, 4), (0, 1),
         np.ones((2, 3, 4), dtype=bool), 0),
        (scalar_result((2, 3), np.float32), (2, 3), (0, 1),
         np.ones((2, 3), dtype=bool), 0),
        (scalar_result((2, 3), np.float64), (2, 3), (0, 1),
         np.ones((2, 3), dtype=bool), 0),
    ]
    cases = list(boundary)
    for _ in range(N_FUZZ // 2):
        cases.append(gen_array_case(rng))
    for _ in range(N_FUZZ // 2):
        cases.append(gen_scalar_case(rng))

    for result, shape, axis, mask, min_count in cases:
        count += 1
        try:
            shadow = shadow_missing_cells(result, shape, axis, mask, min_count)
            oracle = oracle_missing_cells(result, axis, mask, min_count)
        except Exception as e:  # noqa: BLE001
            disagreements.append((shape, axis, min_count, "EXC", repr(e)))
            if len(disagreements) >= 5:
                break
            continue
        if shadow != oracle:
            disagreements.append((shape, axis, min_count, shadow, oracle))
            if len(disagreements) >= 5:
                break

    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for d in disagreements:
            print("  shape=%r axis=%r min_count=%r shadow=%r oracle=%r" % d)
        return 1
    print("G-CONF OK: R/I shadow of reductionMissingDecision agrees with the REAL "
          "gold-patched _maybe_null_out (imported, real NAT_TYPES guard) on %d "
          "inputs spanning BOTH the array branch (ndim>=1) and the scalar/all-dims "
          "branch (ndim==0, float64 dead vs float32 live), seed=%d, 0 disagreements."
          % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
