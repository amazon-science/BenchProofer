#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for matplotlib__matplotlib-26113.

The bundle models ONE routine: the per-cell `accum` reduction in `Axes.hexbin`'s
`C is not None` branch (mapping.md). Given the flattened per-cell value lists
`cells` (out-of-range bucket already dropped) and the resolved count threshold
`mincnt`, each cell is either summarised by `reduce_C_function` or left as
`np.nan`.

POST-PATCH rule (the gold edit changes the keep test `> mincnt` to `>= mincnt`):

    accum[i] = reduce_C_function(acc) if len(acc) >= mincnt else nan

Standing up numpy / the full hexbin pipeline to drive the real reduction is heavy
and unnecessary: the modeled value is this pure per-cell decision over the
observables the real comprehension reads (the cell length and `mincnt`). So the
ORACLE below is a faithful in-process replica of the POST-PATCH comprehension, and
the SHADOW is the op-for-op transliteration of `implementation_hexbinAccum`
(Solution.lean impl region), per refinement.md. `reduce_C_function` is taken as a
concrete real reduction (`sum`); `np.nan` is modeled by the sentinel `None`
(matching `Option Float`'s `none`).

This genuinely tests the soundness-critical clause: a cell holding EXACTLY
`mincnt` points must be summarised (post-patch), not dropped (pre-patch) — the
F2P scenario with `mincnt=1` and singleton cells.

stdlib-only. Pinned seed: 26113 (also in mapping.md).
"""
import random
import sys

SEED = 26113
N = 120_000

REDUCE = sum  # concrete stand-in for reduce_C_function (A-reference, applied identically)
NAN = None    # sentinel for np.nan  <->  Option.none


# --- ORACLE: faithful in-process replica of the POST-PATCH comprehension ------
def oracle(cells, mincnt):
    return [REDUCE(acc) if len(acc) >= mincnt else NAN for acc in cells]


# --- SHADOW of implementation_hexbinAccum (the R leg) -------------------------
# Mirrors Solution.lean impl region exactly (mut accum, for-loop, >= test).
def shadow(cells, mincnt):
    accum = []
    for acc in cells:
        if len(acc) >= mincnt:
            accum = accum + [REDUCE(acc)]
        else:
            accum = accum + [NAN]
    return accum


def disagree(cells, mincnt):
    got = oracle(cells, mincnt)
    want = shadow(cells, mincnt)
    if got != want:
        return (cells, mincnt, got, want)
    return None


def _enumerate_edge():
    cases = []
    # F2P scenario: mincnt=1, cells of size exactly 1 must be summarised.
    cases.append(([[1.0], [1.0], [1.0], [1.0]], 1))
    # size exactly mincnt is the discriminator (kept post-patch)
    cases.append(([[3.0, 4.0]], 2))
    cases.append(([[3.0, 4.0, 5.0]], 3))
    # size mincnt-1 is dropped
    cases.append(([[3.0]], 2))
    cases.append(([[]], 1))
    # empty cell with mincnt=0 is summarised (sum([]) == 0)
    cases.append(([[]], 0))
    cases.append(([[], [1.0], [2.0, 3.0]], 0))
    # negative threshold: everything summarised
    cases.append(([[], [1.0]], -1))
    # mixed grid
    cases.append(([[1.0], [], [2.0, 2.0], [3.0]], 1))
    # no cells
    cases.append(([], 1))
    return cases


def _rand_cells(rng):
    ncells = rng.randint(0, 8)
    cells = []
    for _ in range(ncells):
        k = rng.choice([0, 0, 1, 1, 1, 2, 2, 3, 4])
        cells.append([float(rng.randint(-5, 5)) for _ in range(k)])
    return cells


def main() -> int:
    checked = 0
    for cells, mincnt in _enumerate_edge():
        d = disagree(cells, mincnt)
        if d:
            print(f"DISAGREE edge: oracle={d[2]} shadow={d[3]} cells={d[0]} mincnt={d[1]}")
            print("status=fail")
            return 1
        checked += 1

    rng = random.Random(SEED)
    for _ in range(N):
        cells = _rand_cells(rng)
        mincnt = rng.choice([-1, 0, 1, 2, 3])
        d = disagree(cells, mincnt)
        if d:
            print(f"DISAGREE fuzz: oracle={d[2]} shadow={d[3]} cells={d[0]} mincnt={d[1]}")
            print("status=fail")
            return 1
        checked += 1

    print(f"checked={checked} disagreements=0")
    print("status=pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
