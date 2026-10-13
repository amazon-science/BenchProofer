#!/usr/bin/env python3
r"""G-CONF differential conformance check for matplotlib__matplotlib-24026 (plan §4.1).

Runs IN-CONTAINER with the gold patch applied (the orchestrator passes
apply_gold=True), so the ORACLE is the patched repo's real behaviour: the real
`matplotlib.stackplot.stackplot` colour selection, exercised end-to-end by
actually drawing a stack and reading back each area's rendered fill colour.

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs, on BOTH
legs of the fix:

  * VALUE leg (A1-A3) — SHADOW: Solution.lean's `cyclicColors` transliterated to
      Python over the real repo types via the mapping.md §2 bijection
      (area i -> colors[i % len(colors)]), each colour token resolved to an RGBA
      tuple with matplotlib.colors.to_rgba (the observable the F2P image test
      renders). ORACLE: the per-area facecolors read off the PolyCollections the
      real patched stackplot returns. There are NO A-tagged ops in the computed
      `out` (no consumed axiom), so the value shadow is pure R/I.

  * FRAME leg (A4, directive 5) — SHADOW: `sharedCycle = sharedCycleOld`, i.e.
      the axes' shared colour cycle is unchanged. ORACLE: a CONTROL axes drawn
      with the SAME plot calls but no stackplot; after stackplot runs on the test
      axes, the colour the test axes hands its NEXT ordinary artist must equal the
      colour the control axes hands ITS next artist. Any divergence is the bug
      (the pre-patch `set_prop_cycle`/`get_next_color` perturbed the shared cycle).

They must agree on every input. Exit 0 iff zero disagreements; any disagreement
is a mechanical R/I-fidelity counterexample. matplotlib + stdlib only; the
fuzz seed is pinned (mapping.md §4).
"""
import random
import sys

import matplotlib
matplotlib.use("Agg")
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import to_rgba

SEED = 24026
N_FUZZ = 100_000

# A palette of colour specs the stackplot path accepts. CN cycle references are
# included precisely because they are what the pre-patch set_prop_cycle rejected
# (the issue's ValueError) — the fix must accept them.
PALETTE = ["C0", "C1", "C2", "C3", "C4", "red", "#00ff00", "tab:blue", "0.25"]


# --- the R/I shadow: Solution.lean cyclicColors, transliterated --------------
def shadow_facecolors(colors, layer_count):
    """cyclicColors(colors, layer_count) = [colors[i % len(colors)] ...],
    each token resolved to RGBA (mapping.md §2: colour-spec token comparison is
    done at the rendered-RGBA level)."""
    n = len(colors)
    return [to_rgba(colors[i % n]) for i in range(layer_count)]


# --- the ORACLE: the REAL patched stackplot, end-to-end ----------------------
def oracle_facecolors(colors, layer_count):
    """patch.diff behaviour: draw a stack of `layer_count` areas with the supplied
    `colors` and read back each PolyCollection's rendered facecolor (RGBA)."""
    x = np.arange(4)
    # layer_count strictly-positive rows so np.row_stack yields shape
    # (layer_count, N); values are irrelevant to colour selection.
    y = np.ones((layer_count, len(x)), dtype=float)
    fig, ax = plt.subplots()
    try:
        colls = ax.stackplot(x, y, colors=colors)
        out = [tuple(c.get_facecolor()[0]) for c in colls]
    finally:
        plt.close(fig)
    return out


def oracle_frame_ok(colors, layer_count):
    """Directive-5 frame: the shared colour cycle must be untouched. Compare the
    NEXT cycle colour the test axes hands an ordinary artist after a stackplot,
    against a control axes that did the same minus the stackplot. Equal => the
    shared cycle was not perturbed (sharedCycle = sharedCycleOld)."""
    x = np.arange(4)
    y = np.ones((layer_count, len(x)), dtype=float)

    fig, (ax_test, ax_ctrl) = plt.subplots(1, 2)
    try:
        # Both axes get one identical prior line so they start cycle-aligned.
        ax_test.plot(x, x, color="C0")
        ax_ctrl.plot(x, x, color="C0")
        # Only the test axes runs stackplot with explicit colours.
        ax_test.stackplot(x, y, colors=colors)
        # The colour each axes now hands its NEXT ordinary artist.
        next_test = to_rgba(ax_test._get_lines.get_next_color())
        next_ctrl = to_rgba(ax_ctrl._get_lines.get_next_color())
    finally:
        plt.close(fig)
    return next_test == next_ctrl, next_test, next_ctrl


def fuzz_inputs(n, rng):
    # boundary cases first (plan §4.1 step 4)
    yield (["C2", "C3", "C4"], 3)        # the issue's reproduction
    yield (["C0", "C1", "C2"], 3)        # the F2P test's case
    yield (["C2"], 1)
    yield (["C2"], 4)                    # single colour, wrap
    yield (["C0", "C1"], 5)              # fewer colours than areas (wrap)
    yield (["C0", "C1", "C2"], 2)        # more colours than areas (surplus)
    yield (["red", "#00ff00", "tab:blue"], 3)
    for _ in range(n):
        k = rng.randint(1, len(PALETTE))
        colors = [rng.choice(PALETTE) for _ in range(k)]
        layer_count = rng.randint(1, 8)   # >=1: stackplot needs >=1 area
        yield (colors, layer_count)


# Each oracle draw renders a figure, so an honest ">=10^5 distinct draws" sweep
# is the binding cost. We run the full value-leg sweep to N_FUZZ and run the
# (2x-figure) frame leg on a bounded sample of the SAME inputs; both legs cover
# every boundary case. FRAME_SAMPLE is logged so the cap is not silent.
FRAME_SAMPLE = 3000


def main():
    rng = random.Random(SEED)
    value_disagreements = []
    frame_violations = []
    count = 0
    frame_checked = 0
    for colors, lc in fuzz_inputs(N_FUZZ, rng):
        count += 1
        shadow = shadow_facecolors(colors, lc)
        oracle = oracle_facecolors(colors, lc)
        if shadow != oracle:
            value_disagreements.append((colors, lc, shadow, oracle))
        if frame_checked < FRAME_SAMPLE:
            frame_checked += 1
            ok, nt, nc = oracle_frame_ok(colors, lc)
            if not ok:
                frame_violations.append((colors, lc, nt, nc))
        if len(value_disagreements) >= 5 and len(frame_violations) >= 5:
            break

    if value_disagreements or frame_violations:
        if value_disagreements:
            print("G-CONF FAIL: %d colour-value R/I disagreement(s) over %d inputs "
                  "(seed=%d):" % (len(value_disagreements), count, SEED))
            for colors, lc, sh, orc in value_disagreements[:5]:
                print("  colors=%r layers=%d shadow=%r oracle=%r"
                      % (colors, lc, sh, orc))
        if frame_violations:
            print("G-CONF FAIL: %d shared-cycle frame violation(s) "
                  "(directive-5 frame broken):" % len(frame_violations))
            for colors, lc, nt, nc in frame_violations[:5]:
                print("  colors=%r layers=%d next_test=%r next_ctrl=%r"
                      % (colors, lc, nt, nc))
        return 1

    print("G-CONF OK: R/I shadow of selectLayerColors agrees with patch.diff "
          "behaviour on %d inputs (seed=%d): per-area facecolors match the cyclic "
          "model on all %d, AND the axes' shared colour cycle stayed equal to a "
          "control axes on the %d frame-checked inputs (directive-5 frame held), "
          "0 disagreements." % (count, SEED, count, frame_checked))
    return 0


if __name__ == "__main__":
    sys.exit(main())
