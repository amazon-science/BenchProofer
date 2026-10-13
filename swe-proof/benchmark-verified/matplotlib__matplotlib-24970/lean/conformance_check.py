#!/usr/bin/env python
"""G-CONF: differential conformance for matplotlib__matplotlib-24970.

Runs INSIDE the instance image with the gold patch applied (apply_gold=True,
PYTHONPATH=/testbed). Builds the Python R/I shadow of the Lean
`implementation_index` / `problem_spec_index` skeleton and diffs it against the
REAL patched callee `matplotlib.colors.Colormap.__call__` over a discrete
catalogue of palette sizes + integer values plus >=1e5 randomized integer
inputs.

Modeled behavior: the integer-indexing branch of `Colormap.__call__`. An integer
data value `v` is converted to the index of a lookup-table (LUT) row:
  * `0 <= v < N`  -> its own palette color, row `v`;
  * `v < 0`       -> the `under` row, index `N`;
  * `v >= N`      -> the `over` row, index `N + 1`.
The LUT has `N + 3` rows (palette `0..N-1`, then under=N, over=N+1, bad=N+2).

Bridge (mapping.md): the Lean result is the list of LUT row indices. The real
callee returns RGBA colors, not indices, so we bridge index -> color through the
real LUT: a shadow index `j` is mapped to `cm._lut[j]` and compared cell-for-cell
against the RGBA the real `cm(value)` returns. Because every LUT row is distinct
for the colormaps used (`viridis` resampled to N), an index match is necessary
and sufficient for a color match.

Exit 0 iff zero disagreements. numpy + matplotlib only; pinned seed.
"""
import random
import sys

SEED = 20240630
N_RANDOM = 120_000  # >= 1e5


# ---- Python shadow of implementation_index (post-patch R/I leg) -------------

def shadow_index(N, v):
    """Transliteration of desiredIndex / implementation_index: the exact LUT row
    index for a single integer data value `v` under a palette of `N` colors."""
    idx = int(v)
    if idx > N - 1:
        idx = N + 1
    if idx < 0:
        idx = N
    return idx


# ---- real callee observation ------------------------------------------------

def real_color(cm, v):
    """RGBA the REAL patched Colormap.__call__ returns for one integer value."""
    import numpy as np
    out = cm(np.array([v], dtype=int))
    return tuple(float(c) for c in np.asarray(out)[0])


def main():
    import numpy as np
    import matplotlib as mpl

    rng = random.Random(SEED)

    # palette sizes to exercise (resample viridis to size N); each has N+3 rows.
    palette_sizes = [1, 2, 3, 4, 8, 16, 64, 128, 255, 256, 300]
    cms = {N: mpl.colormaps["viridis"].resampled(N) for N in palette_sizes}
    luts = {}
    for N, cm in cms.items():
        cm._init() if not cm._isinit else None
        luts[N] = np.array(cm._lut)

    def shadow_color(N, v):
        return tuple(float(c) for c in luts[N][shadow_index(N, v)])

    cases = []  # (N, value)
    # discrete catalogue: boundaries -1, 0, 1, N-1, N, N+1 and a few interior pts
    for N in palette_sizes:
        for v in {-3, -1, 0, 1, N // 2, N - 1, N, N + 1, N + 5, 2 * N, -N}:
            cases.append((N, int(v)))

    for _ in range(N_RANDOM):
        N = rng.choice(palette_sizes)
        # bias toward boundaries + out-of-range so the over/under slots are hit
        v = rng.randint(-2 * N - 5, 2 * N + 5)
        cases.append((N, v))

    disagreements = 0
    checked = 0
    for N, v in cases:
        got = real_color(cms[N], v)
        exp = shadow_color(N, v)
        checked += 1
        if got != exp:
            disagreements += 1
            if disagreements <= 5:
                print(f"MISMATCH N={N} v={v}: real={got!r} shadow={exp!r} "
                      f"(shadow_idx={shadow_index(N, v)})")

    print(f"checked={checked} disagreements={disagreements}")
    if disagreements == 0:
        print(f"status=pass conformance OK ({checked} checks, 0 disagreements)")
        return 0
    print(f"status=fail {disagreements} disagreement(s)")
    return 1


if __name__ == "__main__":
    sys.exit(main())
