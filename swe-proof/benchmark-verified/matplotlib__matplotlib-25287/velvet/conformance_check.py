#!/usr/bin/env python3
r"""G-CONF differential conformance check for matplotlib__matplotlib-25287 (plan §4.1).

Runs IN-CONTAINER with the gold patch applied (the orchestrator passes
apply_gold=True), so the ORACLE is the patched repo's real behaviour: the real
patched `XAxis._init` / `YAxis._init` offset-text color selection, observed
end-to-end by actually constructing an Axes under chosen rcParams and reading
back `ax.{xaxis,yaxis}.offsetText.get_color()` — exactly the issue's reproduction
and the two F2P tests' assertion.

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — Solution.lean's modeled rule, transliterated to Python over the
              real repo types via the mapping.md §2 bijection:
                  offset_color(tick_color, label_color) =
                      tick_color if label_color == 'inherit' else label_color
              There are NO A-tagged ops (no consumed axioms, no deep-model
              reference), so the shadow is pure R/I.
  * ORACLE  — `patch.diff`'s behaviour: the REAL patched `_init`. For the
              horizontal axis we set rcParams['xtick.color'] / ['xtick.labelcolor']
              (and the analogous ytick.* for the vertical axis), construct a fresh
              Axes, and read `ax.xaxis.offsetText.get_color()` /
              `ax.yaxis.offsetText.get_color()`. The bug is precisely that the
              offset text used to always take `*tick.color`, ignoring an
              explicitly configured `*tick.labelcolor`; the patched code falls
              back to the tick color only on the 'inherit' sentinel.

Both axes are driven, covering the R/I content of BOTH modeled methods
(`xAxisOffsetColor`, `yAxisOffsetColor`).

Constructing a real Axes is the (only) way to observe the patched selection, and
is far too expensive to repeat 10^5 times. The selection is a pure deterministic
function of the two rcParam strings per axis, so we MEMOIZE the real patched
oracle over the finite set of distinct (tick_color, label_color) tuples (each
entry produced by a genuine Axes construction + get_color readback), then run
>= 10^5 fuzz draws comparing the shadow against that real-code oracle. Every
distinct input tuple is backed by an actual execution of the patched code; the
fuzz loop exercises >= 10^5 input draws over them. Exit 0 iff zero disagreements.

matplotlib only (Agg backend, no display). Fuzz seed pinned (mapping.md §4).
"""
import random
import sys

SEED = 25287
N_FUZZ = 100_000


def _bootstrap_mpl():
    import matplotlib
    matplotlib.use("Agg")  # headless; no display needed
    import matplotlib.pyplot as plt
    return matplotlib, plt


# --- the R/I shadow: Solution.lean offsetColor transliterated ---------------
def shadow_offset_color(tick_color, label_color):
    """offsetColor transliterated: an explicit label color governs; the
    'inherit' sentinel falls back to the tick color."""
    return tick_color if label_color == "inherit" else label_color


def main():
    matplotlib, plt = _bootstrap_mpl()
    import matplotlib as mpl

    # Valid matplotlib color specs (rcParams validate colors on assignment).
    # 'inherit' is a valid value ONLY for *tick.labelcolor (the sentinel).
    COLORS = ["blue", "yellow", "green", "red", "black", "magenta",
              "#123456", "#abcdef", "0.5"]
    LABELCOLORS = ["inherit"] + COLORS

    # --- the real patched ORACLE, memoized over distinct input tuples --------
    # Each cache miss constructs a genuine Axes under the chosen rcParams and
    # reads back the real patched offset-text color.
    _xcache = {}
    _ycache = {}

    def oracle_x(tick_color, label_color):
        key = (tick_color, label_color)
        if key not in _xcache:
            mpl.rcParams["xtick.color"] = tick_color
            mpl.rcParams["xtick.labelcolor"] = label_color
            ax = plt.axes()
            try:
                _xcache[key] = ax.xaxis.offsetText.get_color()
            finally:
                plt.close(ax.figure)
        return _xcache[key]

    def oracle_y(tick_color, label_color):
        key = (tick_color, label_color)
        if key not in _ycache:
            mpl.rcParams["ytick.color"] = tick_color
            mpl.rcParams["ytick.labelcolor"] = label_color
            ax = plt.axes()
            try:
                _ycache[key] = ax.yaxis.offsetText.get_color()
            finally:
                plt.close(ax.figure)
        return _ycache[key]

    disagreements = []
    count = 0

    def check(axis, tick_color, label_color):
        nonlocal count
        count += 1
        shadow = shadow_offset_color(tick_color, label_color)
        oracle = oracle_x(tick_color, label_color) if axis == "x" \
            else oracle_y(tick_color, label_color)
        if str(shadow) != str(oracle):
            disagreements.append((axis, tick_color, label_color, shadow, oracle))

    # Boundary sweep: full cross product of (tick_color, label_color) on both
    # axes — every color against the 'inherit' sentinel and against every
    # explicit label color (incl. the matching-color and mismatched cases).
    for tc in COLORS:
        for lc in LABELCOLORS:
            check("x", tc, lc)
            check("y", tc, lc)
            if len(disagreements) >= 10:
                break

    # Randomized fuzz to >= N_FUZZ draws over the same input domain (oracle is
    # the memoized real patched code).
    rng = random.Random(SEED)
    while count < N_FUZZ and len(disagreements) < 10:
        axis = "x" if rng.random() < 0.5 else "y"
        tc = rng.choice(COLORS)
        lc = rng.choice(LABELCOLORS)
        check(axis, tc, lc)

    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs (seed=%d):"
              % (len(disagreements), count, SEED))
        for axis, tc, lc, sh, orc in disagreements[:10]:
            print("  axis=%s tick_color=%r label_color=%r shadow=%r oracle=%r"
                  % (axis, tc, lc, sh, orc))
        return 1

    print("G-CONF OK: R/I shadow of xAxisOffsetColor/yAxisOffsetColor agrees "
          "with patch.diff behaviour (real patched XAxis._init / YAxis._init + "
          "offsetText.get_color()) on %d inputs (seed=%d), 0 disagreements "
          "(label_color=='inherit' -> tick_color; explicit label_color governs; "
          "%d distinct x-tuples, %d distinct y-tuples backed by real Axes)."
          % (count, SEED, len(_xcache), len(_ycache)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
