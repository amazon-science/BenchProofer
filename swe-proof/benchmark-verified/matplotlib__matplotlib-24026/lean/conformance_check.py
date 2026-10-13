#!/usr/bin/env python
"""G-CONF: differential conformance for matplotlib__matplotlib-24026.

Runs INSIDE the instance image with the gold patch applied (apply_gold=True,
PYTHONPATH=/testbed). Builds the Python shadow of the Lean
`implementation_stackplotColors` / `nthColor` skeleton and diffs it against the
REAL patched `matplotlib.stackplot.stackplot` over a discrete catalogue plus
>=1e5 randomized draws.

  observable: when a non-empty palette `colors` is supplied, the facecolor of
  each of the `n` stacked regions returned by `stackplot`.
    region i facecolor  ==  to_rgba(colors[i % len(colors)])

The shadow returns the list of palette tokens [nthColor(colors, i) for i in
range(n)]; both legs are normalized through matplotlib.colors.to_rgba (the I/O
bridge from mapping.md) before comparison, since the real artifact stores
resolved RGBA. Exit 0 iff zero disagreements. stdlib-only fuzzing (pinned seed).
"""
import random
import sys

SEED = 20240629
N_RANDOM = 120_000  # >= 1e5


# ---- Python shadow of implementation_stackplotColors -----------------------

def nth_color(colors, i):
    # transliteration of nthColor: palette entry at index i mod len(colors)
    return colors[i % len(colors)]


def shadow_colors(colors, n):
    # transliteration of implementation_stackplotColors (success leg):
    # exactly one color per region, cycling through the palette.
    return [nth_color(colors, i) for i in range(n)]


# ---- real callee observation ------------------------------------------------

def real_colors(palette, n):
    """Run the REAL patched stackplot with `n` stacked unit series and the given
    `palette`. Return the list of resolved per-region facecolors (RGBA)."""
    import numpy as np
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    x = np.arange(3)
    # n series, each a length-3 row of small positive values
    ys = [np.array([1.0, 2.0, 3.0]) + k for k in range(n)]
    fig, ax = plt.subplots()
    try:
        r = ax.stackplot(x, *ys, colors=palette)
        out = [tuple(coll.get_facecolor()[0]) for coll in r]
    finally:
        plt.close(fig)
    return out


def main():
    import matplotlib.colors as mcolors

    def rgba(tok):
        return tuple(round(c, 6) for c in mcolors.to_rgba(tok))

    # discrete palettes: named, hex, CN cycle-refs (the discriminating case),
    # rgb tuples-as-strings handled via named tokens here.
    palettes = [
        ["C0", "C1", "C2"],
        ["C2", "C3", "C4"],
        ["red", "green", "blue"],
        ["#ff0000", "#00ff00", "#0000ff"],
        ["C0"],
        ["red"],
        ["C5", "magenta"],
        ["C0", "C1", "C2", "C3", "C4", "C5"],
        ["#123456", "C7"],
    ]
    layer_counts = [1, 2, 3, 4, 5, 7]

    disagreements = 0
    checked = 0
    cache = {}

    def check(pal, n):
        nonlocal disagreements, checked
        key = (tuple(pal), n)
        if key not in cache:
            got = [rgba(c) for c in real_colors(pal, n)]
            exp = [rgba(c) for c in shadow_colors(pal, n)]
            cache[key] = (got, exp)
        got, exp = cache[key]
        checked += 1
        if got != exp:
            disagreements += 1
            if disagreements <= 5:
                print(f"MISMATCH palette={pal} n={n}: real={got!r} shadow={exp!r}")

    # full discrete matrix
    for pal in palettes:
        for n in layer_counts:
            check(pal, n)

    # randomized fuzz
    token_pool = (
        [f"C{i}" for i in range(10)]
        + ["red", "green", "blue", "magenta", "cyan", "yellow", "black", "white"]
        + ["#ff0000", "#00ff00", "#0000ff", "#123456", "#abcdef"]
    )
    rng = random.Random(SEED)
    for _ in range(N_RANDOM):
        plen = rng.randint(1, 8)
        pal = [rng.choice(token_pool) for _ in range(plen)]
        n = rng.randint(1, 9)
        check(pal, n)

    print(f"checked={checked} disagreements={disagreements}")
    if disagreements == 0:
        print(f"status=pass conformance OK ({checked} checks, 0 disagreements)")
        return 0
    print(f"status=fail {disagreements} disagreement(s)")
    return 1


if __name__ == "__main__":
    sys.exit(main())
