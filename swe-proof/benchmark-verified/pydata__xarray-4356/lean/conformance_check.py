#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for pydata__xarray-4356.

The bundle models the missing-value invalidation pass of
`xarray/core/nanops._maybe_null_out` (mapping.md): after a min_count-aware
sum/prod reduction, each output cell is kept iff at least `min_count` of the
entries reduced into it were present, else it is replaced by the fill sentinel.

The soundness-critical clause is the per-cell *total* count of reduced entries:
the POST-PATCH code uses `np.take(mask.shape, axis).prod()` — the PRODUCT of the
sizes of all reduced axes — and never rejects a multi-axis reduction. The
modeled value is a pure function of the observables the routine reads (the
reduced-axis sizes, each cell's reduced value, each cell's missing-element
count, `min_count`, and the promoted fill value), so the ORACLE below is a
faithful in-process replica of the POST-PATCH decision and the SHADOW is the
op-for-op transliteration of `implementation_enforceMinCount`
(Solution.lean impl region), per refinement.md.

We compare structurally: the result is ('ok', tuple_of_cell_values). A cell that
is fill-substituted is encoded as the sentinel marker 'FILL' (we do NOT compare
the numeric fill value itself — the patch leaves `dtypes.maybe_promote` untouched;
what the patch changes is *which* cells get filled). This makes the comparison
exact and float-safe.

stdlib-only. Pinned seed: 4356 (also in mapping.md).
"""
import random
import sys

SEED = 4356
N = 120_000

FILL = "FILL"  # marker: this cell is replaced by the fill sentinel


def _prod(xs):
    p = 1
    for x in xs:
        p *= x
    return p


# --- ORACLE: faithful in-process replica of the POST-PATCH decision -----------
# Post-patch nd-branch: null_mask = (np.take(mask.shape, axis).prod()
#                                    - mask.sum(axis) - min_count) < 0
# i.e. a cell is invalidated iff total - missing - min_count < 0.
# The guard `raise ValueError` for multi-axis reductions is GONE post-patch, so
# multi-axis requests are thresholded, never rejected.
def oracle(inp):
    axis_sizes = inp["axisSizes"]
    cells = inp["cells"]              # list of (value, missing)
    min_count = inp["minCount"]
    total = _prod(axis_sizes)         # np.take(shape, axis).prod()
    out = []
    for (value, missing) in cells:
        if (total - missing - min_count) < 0:
            out.append(FILL)
        else:
            out.append(value)
    return ("ok", tuple(out))


# --- SHADOW of implementation_enforceMinCount (the R/I legs) -------------------
# Mirrors Solution.lean impl region exactly: total = axisSizes.prod (Int);
# reducedCellValue = if total - missing < minCount then FILL else value.
def reduced_cell_value(total, min_count, cell):
    value, missing = cell
    if total - missing < min_count:
        return FILL
    return value


def shadow(inp):
    axis_sizes = inp["axisSizes"]
    cells = inp["cells"]
    min_count = inp["minCount"]
    total = _prod(axis_sizes)
    out = []
    for cell in cells:
        out.append(reduced_cell_value(total, min_count, cell))
    return ("ok", tuple(out))


def disagree(inp):
    got = oracle(inp)
    want = shadow(inp)
    if got != want:
        return (inp, got, want)
    return None


def _enumerate_edge():
    cases = []
    # F2P scenario: multi-axis reduction (length>=2) reduced to a single cell.
    # Single-axis (buggy) count would be mask.shape[axis] of just one axis; the
    # product count is 3*4*5 = 60. With min_count=3 and 58 missing -> 2 valid < 3
    # => FILL; the single-axis count (e.g. 5) - 58 would be hugely negative too,
    # but the point is multi-axis is ACCEPTED (no raise) and counts the product.
    cases.append(dict(axisSizes=[3, 4, 5], cells=[(7.0, 58)], minCount=3))
    # multi-axis, plenty valid -> keep
    cases.append(dict(axisSizes=[3, 4, 5], cells=[(7.0, 10)], minCount=3))
    # single-axis, boundary: total=4, missing=2, valid=2, min_count=2 -> keep
    cases.append(dict(axisSizes=[4], cells=[(1.0, 2)], minCount=2))
    # single-axis, boundary: valid just below -> FILL
    cases.append(dict(axisSizes=[4], cells=[(1.0, 3)], minCount=2))
    # multi-cell nd result, mixed keep/fill
    cases.append(dict(axisSizes=[2, 3], cells=[(1.0, 0), (2.0, 5), (3.0, 4)], minCount=2))
    # min_count = 1 (the issue's example), one missing-heavy cell
    cases.append(dict(axisSizes=[2, 2], cells=[(9.0, 4)], minCount=1))
    # min_count = 0: total-missing-0 < 0 never (missing<=total) -> all kept
    cases.append(dict(axisSizes=[3, 3], cells=[(1.0, 9), (2.0, 0)], minCount=0))
    # empty cell list
    cases.append(dict(axisSizes=[2, 2], cells=[], minCount=1))
    # large product
    cases.append(dict(axisSizes=[10, 10, 10], cells=[(5.0, 998)], minCount=3))
    return cases


def main() -> int:
    checked = 0
    for inp in _enumerate_edge():
        d = disagree(inp)
        if d:
            print(f"DISAGREE edge: oracle={d[1]} shadow={d[2]} inp={d[0]}")
            print("status=fail")
            return 1
        checked += 1

    rng = random.Random(SEED)
    for _ in range(N):
        ndim = rng.randint(1, 4)
        axis_sizes = [rng.randint(1, 8) for _ in range(ndim)]
        total = _prod(axis_sizes)
        min_count = rng.randint(0, total + 2)
        ncells = rng.randint(0, 6)
        cells = []
        for _ in range(ncells):
            value = float(rng.randint(-1000, 1000))
            missing = rng.randint(0, total)   # 0..total entries missing
            cells.append((value, missing))
        inp = dict(axisSizes=axis_sizes, cells=cells, minCount=min_count)
        d = disagree(inp)
        if d:
            print(f"DISAGREE fuzz: oracle={d[1]} shadow={d[2]} inp={d[0]}")
            print("status=fail")
            return 1
        checked += 1

    print(f"checked={checked} disagreements=0")
    print("status=pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
