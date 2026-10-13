#!/usr/bin/env python3
"""G-AX executable soundness check for matplotlib__matplotlib-24026.

Executes the REAL stdlib callee (`itertools.cycle`, the same module the gold
patch imports) and asserts that the deep model `cyclicColors` (Solution.lean's
`pure` region) reproduces it exactly.

The one kind-A check:

  (A-reference) the deep model `cyclic_colors(colors, layer_count)` ==
      the colours the REAL `itertools.cycle(colors)` hands out over
      `layer_count` successive `next(...)` calls. The changed colour-source
      operation is modeled DEEPLY (not behind a consumed axiom); G-AX validates
      that deep model against the real callee:

        area i  ->  colors[i % len(colors)]

      i.e. the supplied colours repeated cyclically, one per area, in order.

There are NO consumed axioms in this bundle (the directive-5 shared-cycle frame
borrows no callee contract; its real soundness is checked end-to-end by
conformance_check.py / G-CONF). Imports only stdlib `itertools`. Exit 0 iff every
obligation holds.
"""
import itertools
import random
import sys


# --- model.py reference encoding (kept in lock-step with cyclicColors) -------

def cyclic_colors(colors, layer_count):
    """Reference implementation of Solution.lean's deep model `cyclicColors`:
    area i takes colors[i % len(colors)]."""
    n = len(colors)
    return [colors[i % n] for i in range(layer_count)]


# --- the real callee --------------------------------------------------------

def real_cycle_draw(colors, layer_count):
    """The colours the REAL itertools.cycle hands out, exactly as the patched
    stackplot consumes them: `colors = itertools.cycle(colors)` then one
    `next(colors)` per area."""
    it = itertools.cycle(colors)
    return [next(it) for _ in range(layer_count)]


def check(colors, layer_count):
    assert len(colors) > 0, "require colors non-empty (precondition)"
    observed = real_cycle_draw(colors, layer_count)        # real callee
    expected = cyclic_colors(colors, layer_count)          # deep model
    assert observed == expected, (
        "cyclic_colors deep model unsound on colors=%r layer_count=%r: "
        "itertools.cycle gave %r, deep model gives %r"
        % (colors, layer_count, observed, expected))


def main():
    palette = ["C0", "C1", "C2", "C3", "C4", "red", "#00ff00",
               "tab:blue", "0.5", "xkcd:teal"]

    # --- boundary cases ----------------------------------------------------
    boundary = [
        (["C2"], 0),                       # zero areas
        (["C2"], 1),                       # single colour, single area
        (["C2"], 5),                       # single colour, many areas (wrap)
        (["C2", "C3", "C4"], 3),           # equal length (the issue's case)
        (["C0", "C1", "C2"], 3),           # the F2P test's case
        (["C0", "C1", "C2"], 2),           # more colours than areas (surplus)
        (["C0", "C1"], 5),                 # fewer colours than areas (wrap)
        (["red", "#00ff00", "tab:blue"], 7),
        (palette, 0),
        (palette, 1),
        (palette, len(palette)),
        (palette, 2 * len(palette) + 1),   # multiple full wraps
    ]
    for colors, lc in boundary:
        check(colors, lc)

    # --- randomized fuzz ---------------------------------------------------
    rng = random.Random(24026)
    for _ in range(20000):
        k = rng.randint(1, len(palette))            # non-empty colour list
        colors = [rng.choice(palette) for _ in range(k)]
        layer_count = rng.randint(0, 30)
        check(colors, layer_count)

    print("G-AX OK: cyclic_colors deep model (== itertools.cycle consumption) "
          "sound on %d boundary + 20000 fuzz (colors, layer_count) cases; "
          "no consumed axioms (directive-5 frame checked by G-CONF)."
          % len(boundary))
    return 0


if __name__ == "__main__":
    sys.exit(main())
