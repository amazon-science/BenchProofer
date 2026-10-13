#!/usr/bin/env python3
r"""G-CONF differential conformance check for matplotlib__matplotlib-25479 (plan §4.1).

Runs IN-CONTAINER with the gold patch applied (the orchestrator passes
apply_gold=True), so the ORACLE is the patched repo's real behaviour: the real
`matplotlib.cm.ColormapRegistry.register` (site A) and the real
`matplotlib.colors.Colormap.__eq__` (site B).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs. There are
NO A-tagged ops (no consumed axioms, no deep-model reference), so both shadows
are pure R/I.

  Site A — registration name stamping (`registeredColormap`):
    * SHADOW  — Solution.lean's rule transliterated via mapping.md §2:
                the stored colormap advertises the chosen registration `name`
                (content otherwise preserved).
    * ORACLE  — register the colormap under `name` with the REAL patched
                `register`, then read back the stored copy's `.name`.

  Site B — name-independent value equality (`colormapsEqual`):
    * SHADOW  — colormap_eq_spec(a, b) =
                  (a.colorbar_extend == b.colorbar_extend) and
                  np.array_equal(a._lut, b._lut)
                i.e. the field conjunction WITHOUT the name (mapping.md §2:
                colorbar_extend ↔ extendStyle, _lut ↔ lookupTable).
    * ORACLE  — the REAL patched `Colormap.__eq__` (`a == b`).

They must agree on every input. Exit 0 iff zero disagreements; any disagreement
is a mechanical R/I-fidelity counterexample. stdlib + matplotlib + numpy only.
Fuzz seed pinned (mapping.md §4).
"""
import random
import sys

SEED = 25479
N_FUZZ = 100_000


def _build():
    import matplotlib
    matplotlib.use("Agg")
    import numpy as np
    from matplotlib.colors import ListedColormap, Colormap
    return matplotlib, np, ListedColormap, Colormap


def _make_cmap(ListedColormap, name, colors, extend, n=None):
    """Construct a concrete Colormap with a chosen advertised name, colour data
    (which determines the lookup table), and colorbar_extend flag."""
    cmap = ListedColormap(colors, name=name, N=n)
    cmap.colorbar_extend = extend
    cmap._init()  # materialize ._lut so __eq__ compares initialized tables
    return cmap


# --- Site A: registration name stamping --------------------------------------

def check_register(matplotlib, ListedColormap, idx, advertised, reg_name,
                   colors, extend):
    """SHADOW: stored colormap advertises reg_name. ORACLE: real register, read
    back the stored copy's .name and content."""
    registry = matplotlib.colormaps
    cmap = _make_cmap(ListedColormap, advertised, colors, extend)
    # unique registry name so we never collide with builtins or prior iterations
    unique = "gconf_%d_%s" % (idx, reg_name)
    try:
        registry.register(name=unique, cmap=cmap)
        stored = registry[unique]
        shadow_name = unique                      # Solution.lean: out.name = name
        oracle_name = stored.name                 # real patched register
        # content preservation (mapping.md §2: copy preserves extend + lut)
        content_ok = (stored.colorbar_extend == cmap.colorbar_extend)
        return (shadow_name == oracle_name) and content_ok, shadow_name, oracle_name
    finally:
        try:
            registry.unregister(unique)
        except Exception:
            pass


# --- Site B: name-independent value equality ---------------------------------

def shadow_eq(np, a, b):
    """colormap_eq_spec transliterated: name is NOT consulted."""
    if a.colorbar_extend != b.colorbar_extend:
        return False
    return bool(np.array_equal(a._lut, b._lut))


def check_equality(np, a, b):
    shadow = shadow_eq(np, a, b)
    oracle = bool(a == b)                          # real patched Colormap.__eq__
    return shadow == oracle, shadow, oracle


def main():
    matplotlib, np, ListedColormap, Colormap = _build()
    rng = random.Random(SEED)
    disagreements = []
    count = 0

    palette = ["red", "green", "blue", "black", "white", "yellow",
               "cyan", "magenta", "orange", "purple"]
    names = ["viridis", "test-cmap", "wrong-cmap", "some_cmap_name",
             "my_cmap_name", "Test", "", "a", "plasma_x"]

    def rand_colors():
        k = rng.randint(1, 5)
        return [rng.choice(palette) for _ in range(k)]

    # --- boundary cases for site A (the issue's own scenario) ----------------
    boundaryA = [
        ("some_cmap_name", "my_cmap_name", ["red", "green", "blue"], False),
        ("test-cmap", "wrong-cmap", ["red"], True),
        ("same", "same", ["blue", "yellow"], False),   # advertised == reg name
        ("", "edge", ["black"], True),
    ]
    for advertised, reg, colors, extend in boundaryA:
        count += 1
        ok, sh, orc = check_register(matplotlib, ListedColormap, count,
                                     advertised, reg, colors, extend)
        if not ok:
            disagreements.append(("register", advertised, reg, sh, orc))

    # --- fuzz site A ---------------------------------------------------------
    for _ in range(N_FUZZ // 2):
        count += 1
        advertised = rng.choice(names)
        reg = rng.choice(names) or "n"
        ok, sh, orc = check_register(matplotlib, ListedColormap, count,
                                     advertised, reg, rand_colors(),
                                     rng.choice([True, False]))
        if not ok:
            disagreements.append(("register", advertised, reg, sh, orc))
            if len(disagreements) >= 5:
                break

    # --- boundary cases for site B (test_colormap_equals scenarios) ----------
    base = _make_cmap(ListedColormap, "base", ["red", "green", "blue"], False)
    same_content_diff_name = _make_cmap(ListedColormap, "Test",
                                        ["red", "green", "blue"], False)
    diff_extend = _make_cmap(ListedColormap, "base", ["red", "green", "blue"], True)
    diff_lut = _make_cmap(ListedColormap, "base", ["red", "green", "yellow"], False)
    diff_size = _make_cmap(ListedColormap, "base", ["red", "green"], False)
    boundaryB = [
        (base, same_content_diff_name),   # only name differs -> equal (the fix)
        (base, diff_extend),              # extend differs    -> not equal
        (base, diff_lut),                 # lut differs       -> not equal
        (base, diff_size),                # lut size differs  -> not equal
        (base, base),                     # identical         -> equal
    ]
    for a, b in boundaryB:
        count += 1
        ok, sh, orc = check_equality(np, a, b)
        if not ok:
            disagreements.append(("equality", a.name, b.name, sh, orc))

    # --- fuzz site B ---------------------------------------------------------
    for _ in range(N_FUZZ // 2):
        count += 1
        a = _make_cmap(ListedColormap, rng.choice(names), rand_colors(),
                       rng.choice([True, False]))
        # 50%: same content, different name (the discriminating fixed case)
        if rng.random() < 0.5:
            b = _make_cmap(ListedColormap, rng.choice(names),
                           list(a.colors), a.colorbar_extend, n=a.N)
        else:
            b = _make_cmap(ListedColormap, rng.choice(names), rand_colors(),
                           rng.choice([True, False]))
        ok, sh, orc = check_equality(np, a, b)
        if not ok:
            disagreements.append(("equality", a.name, b.name, sh, orc))
            if len(disagreements) >= 5:
                break

    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for row in disagreements:
            print("  ", row)
        return 1
    print("G-CONF OK: R/I shadows of registeredColormap + colormapsEqual agree "
          "with patch.diff behaviour on %d inputs (seed=%d), 0 disagreements."
          % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
