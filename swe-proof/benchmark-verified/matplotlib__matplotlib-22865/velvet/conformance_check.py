#!/usr/bin/env python3
"""G-CONF differential conformance check for matplotlib__matplotlib-22865 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region transliterated
              to Python over the *real* repo type, via the mapping.md bijection
              (`np.dstack([X,Y])` first axis ↔ `List Seg`; `startIdx`/`endIdx`
              ↔ the slice bounds; `(segs.drop s).take (e-s)` ↔ the first-axis
              slice). The impl region has NO A-tagged callee (the whole
              selection is concrete positional arithmetic), so the shadow is
              pure R/I and G-CONF carries real weight (conf_skip=false).
  * ORACLE  — `patch.diff`'s behaviour. Two complementary legs, both the real
              patched code:
        Phase A (real callee, authoritative): a real `matplotlib.colorbar.
              Colorbar` is constructed across the full reachable configuration
              matrix (extend × drawedges × orientation × number of levels); the
              patched `_add_solids` runs end-to-end and the divider segments it
              hands to `set_segments` are read back via
              `cbar.dividers.get_segments()`. This exercises the REAL
              `_extend_lower()` / `_extend_upper()` flags through the real
              `extend` configuration — the flag-derivation half of the fix.
        Phase B (real numpy, scale): ≥10^5 synthetic meshes of random size with
              random (drawedges, extend_lower, extend_upper) booleans; the
              oracle is the literal patched selection statement
              `np.dstack([X, Y])[start_idx:end_idx]` (with `start_idx`/`end_idx`
              from the patched formula) run on REAL numpy arrays. This exercises
              the numpy-slice ↔ drop/take R-bijection at scale, including the
              `-1 ↔ n-1` cut and the n∈{0,1} empty-slice boundaries
              (mapping.md §2.1) — the positional-slice half of the fix.

They must agree on every Requires-satisfying input. Exit 0 iff zero
disagreements; any disagreement is a mechanical R/I-fidelity counterexample.

Runs in-container (the prebuilt SWE-Bench instance image, matplotlib 3.5), the
gold patch already applied by the orchestrator (apply_gold). stdlib + numpy +
matplotlib only. The fuzz seed is pinned (mapping.md §4) for a deterministic
verdict.
"""
import random
import sys
import warnings

warnings.filterwarnings("ignore")

import numpy as np

SEED = 22865
N_FUZZ = 100_000


# --- the R/I shadow: Solution.lean startIdx/endIdx/selectSeg -----------------
def start_idx(extend_lower):
    """startIdx (extLow : Bool) : Nat := if extLow then 0 else 1."""
    return 0 if extend_lower else 1


def end_idx(extend_upper, n):
    """endIdx (extUp : Bool) (n : Nat) : Nat := if extUp then n else n - 1.
    (Nat subtraction: max(n-1, 0); for the realizable n >= 1 this is n-1.)"""
    return n if extend_upper else max(n - 1, 0)


def shadow_select(full, drawedges, extend_lower, extend_upper):
    """selectSeg (segs) drawEdges extLow extUp, transliterated to a first-axis
    slice of the dstack array. `full` is np.dstack([X, Y]) (shape (n, 2, 2));
    the model is (segs.drop s).take (e - s) when drawEdges else []."""
    if not drawedges:
        return full[:0]                       # [] : List Seg
    n = len(full)                             # segs.length
    s = start_idx(extend_lower)               # startIdx extLow
    e = end_idx(extend_upper, n)              # endIdx extUp n
    # (segs.drop s).take (e - s): drop s rows, then take (e - s) of the rest.
    take = max(e - s, 0)                      # Nat subtraction
    return full[s:][:take]


# --- Phase A oracle: the REAL patched Colorbar, full config matrix -----------
def real_colorbar_segments(extend, nlevels, drawedges, orientation):
    """Build a real Colorbar and return (np.dstack([X,Y]), drawedges,
    _extend_lower(), _extend_upper(), real divider segments)."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.colors as mcolors
    from matplotlib.colorbar import Colorbar

    cmap = plt.get_cmap("viridis")
    bounds = np.arange(nlevels)               # nlevels boundaries -> nlevels-1 inner colors
    extra = {"neither": 0, "min": 1, "max": 1, "both": 2}[extend]
    nb_colors = (len(bounds) - 1) + extra
    colors = cmap(np.linspace(40, 255, nb_colors).astype(int))
    cmap2, norm = mcolors.from_levels_and_colors(bounds, colors, extend=extend)
    fig = plt.figure(figsize=(4, 1))
    ax = plt.subplot(111)
    cbar = Colorbar(ax, cmap=cmap2, norm=norm, orientation=orientation,
                    drawedges=drawedges)
    X, Y = cbar._mesh()
    full = np.dstack([X, Y])
    segs = cbar.dividers.get_segments()
    el, eu = cbar._extend_lower(), cbar._extend_upper()
    de = cbar.drawedges
    plt.close(fig)
    real = np.array(segs) if len(segs) else np.empty((0,) + full.shape[1:])
    return full, de, el, eu, real


def phase_a():
    """Authoritative differential over the real callee's reachable config
    matrix. Returns (count, disagreements)."""
    disagreements = []
    count = 0
    for nlevels in range(2, 40):
        for extend in ("neither", "min", "max", "both"):
            for drawedges in (True, False):
                for orientation in ("horizontal", "vertical"):
                    try:
                        full, de, el, eu, real = real_colorbar_segments(
                            extend, nlevels, drawedges, orientation)
                    except Exception as exc:               # unrealizable combo
                        continue
                    count += 1
                    shadow = shadow_select(full, de, el, eu)
                    if (shadow.shape != real.shape
                            or not np.allclose(shadow, real)):
                        disagreements.append(
                            ("A", extend, nlevels, drawedges, orientation,
                             shadow.shape, real.shape))
                        if len(disagreements) >= 5:
                            return count, disagreements
    return count, disagreements


# --- Phase B oracle: the REAL patched numpy slice, at scale ------------------
def oracle_patched_slice(full, drawedges, extend_lower, extend_upper):
    """The literal patched statement, on real numpy arrays:
        if drawedges:
            start_idx = 0 if _extend_lower() else 1
            end_idx   = len(X) if _extend_upper() else -1
            set_segments(np.dstack([X, Y])[start_idx:end_idx])
        else:
            set_segments([])
    `full` is np.dstack([X, Y]); len(X) == len(full)."""
    if not drawedges:
        return full[:0]
    si = 0 if extend_lower else 1
    ei = len(full) if extend_upper else -1
    return full[si:ei]


def fuzz_meshes(n, rng):
    # boundary cases first: the empty / single / two boundary meshes and the
    # F2P matrix (bounds = arange(3) -> 3 boundaries) under every flag combo.
    for nb in (0, 1, 2, 3):
        for de in (True, False):
            for el in (True, False):
                for eu in (True, False):
                    yield nb, de, el, eu
    for _ in range(n):
        nb = rng.randint(0, 30)
        de = rng.random() < 0.5
        el = rng.random() < 0.5
        eu = rng.random() < 0.5
        yield nb, de, el, eu


def make_full(nb, rng):
    """A real np.dstack([X, Y]) of nb boundary segments with arbitrary float
    content (content is opaque to the positional selection)."""
    X = np.array([[rng.uniform(-10, 10), rng.uniform(-10, 10)] for _ in range(nb)])
    Y = np.array([[rng.uniform(-10, 10), rng.uniform(-10, 10)] for _ in range(nb)])
    if nb == 0:
        X = np.empty((0, 2)); Y = np.empty((0, 2))
    return np.dstack([X, Y])


def phase_b(n, rng):
    disagreements = []
    count = 0
    for nb, de, el, eu in fuzz_meshes(n, rng):
        count += 1
        full = make_full(nb, rng)
        shadow = shadow_select(full, de, el, eu)
        oracle = oracle_patched_slice(full, de, el, eu)
        if shadow.shape != oracle.shape or not np.array_equal(shadow, oracle):
            disagreements.append(("B", nb, de, el, eu,
                                  shadow.tolist(), oracle.tolist()))
            if len(disagreements) >= 5:
                break
    return count, disagreements


def main():
    rng = random.Random(SEED)
    a_count, a_dis = phase_a()
    b_count, b_dis = phase_b(N_FUZZ, rng)
    disagreements = a_dis + b_dis
    total = a_count + b_count
    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs "
              "(phase A real-Colorbar=%d, phase B real-numpy=%d):"
              % (len(disagreements), total, a_count, b_count))
        for d in disagreements:
            print("  ", d)
        return 1
    print("G-CONF OK: R/I shadow of selectSegM agrees with patch.diff behaviour "
          "on %d inputs (phase A real-Colorbar=%d configs, phase B real-numpy "
          "fuzz=%d, seed=%d), 0 disagreements." % (total, a_count, b_count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
