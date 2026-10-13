#!/usr/bin/env python3
"""G-AX executable soundness check for matplotlib__matplotlib-25479.

This bundle consumes NO `@ContractOnly` axiom: both behaviours under
specification are modelled deeply. What G-AX validates here are the two
A-REFERENCES — the model's deep characterisations of the two real operations —
against the REAL matplotlib callees, executed in-container:

  (A-reference 1) `colormaps_equal` / the model's `__eq__` characterisation:
      two mappings are equal  iff  same extension flag AND same lookup-table
      contents — the LABEL is NOT part of the comparison. We assert that the
      real `matplotlib.colors.Colormap.__eq__` agrees with this predicate over
      boundary cases (equal copies; relabelled copies; every pair of distinct
      extension-flag values; truncated/mutated lookup tables; tables carrying
      an indeterminate entry) and randomized fuzz.

      Two facts about that predicate are load-bearing and are asserted here
      directly against the real callee rather than assumed:
        * the extension flag ranges over SIX mutually distinguishable values
          (False, True, 'neither', 'min', 'max', 'both'), and with equal tables
          the real comparison separates all 15 distinct pairs. So the flag leg
          is not a two-valued test, and the fuzz draws over the whole domain.
        * the table comparison is `np.array_equal` at its default settings,
          i.e. an elementwise `==` fold, under which an entry holding an
          indeterminate float value compares unequal to EVERY entry — itself
          included. A table carrying such an entry is therefore equal to no
          table at all, not even to itself; the model's entry relation states
          this and the boundary cases below exercise it.

  (A-reference 2) `register_named` / the model's registration characterisation:
      after registering a mapping under a chosen label, the registry holds an
      independent snapshot reachable under that label whose OWN label equals the
      chosen label (regardless of the supplied mapping's label), the supplied
      mapping is left untouched, and the snapshot is equal (by the label-free
      equality above) to the supplied mapping. We assert this against the real
      `matplotlib.colormaps.register` + `get_cmap`.

Imports only the standard library plus matplotlib — the very package the gold
patch edits; nothing test-only. Exit 0 iff every observation is sound.
"""
import random
import sys

import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.colors import Colormap, ListedColormap


# --- model.py reference encodings (kept in lock-step with the spec) ----------

def model_equal(a, b):
    """Reference of model.py `colormaps_equal`: equal iff same extension flag
    and same lookup-table contents; the label is irrelevant."""
    if not isinstance(b, Colormap):
        return False
    if a.colorbar_extend != b.colorbar_extend:
        return False
    if not a._isinit:
        a._init()
    if not b._isinit:
        b._init()
    return np.array_equal(a._lut, b._lut)


# The extension flag's full documented value domain. Publicly reachable: the
# string members are what `Colormap.with_extremes` / the colorbar machinery set
# (colors.py) and what `from_levels_and_colors` propagates.
EXTEND_DOMAIN = (False, True, "neither", "min", "max", "both")

# An entry value that no comparison accepts, reached through public API only.
INDETERMINATE = float("nan")


def make_cmap(name, colors=None):
    """A small initialised colormap with a chosen label."""
    if colors is None:
        colors = [(0.0, 0.0, 0.0, 1.0), (1.0, 1.0, 1.0, 1.0)]
    cm = ListedColormap(colors, name=name)
    cm._init()
    return cm


# --- A-reference 1: Colormap.__eq__ is label-free ----------------------------

def check_equality_reference():
    base = matplotlib.colormaps["viridis"]

    # equal copy
    c = base.copy()
    assert (c == base) == model_equal(c, base) == True

    # relabelled copy: DIFFERENT label, same lut/extend -> EQUAL (the fix)
    c = base.copy()
    c.name = "totally-different-label"
    assert (c == base) is True, "relabelled copy must be equal (label-free)"
    assert model_equal(c, base) is True

    # flipped extension flag -> unequal
    c = base.copy()
    c.colorbar_extend = not base.colorbar_extend
    assert (c == base) == model_equal(c, base) == False

    # EVERY pair of distinct extension-flag values, over IDENTICAL tables and
    # identical labels: the real comparison must separate all 15 of them, which
    # is what pins the flag leg to a six-valued rather than a two-valued test.
    for i in range(len(EXTEND_DOMAIN)):
        for j in range(len(EXTEND_DOMAIN)):
            a = base.copy(); a.colorbar_extend = EXTEND_DOMAIN[i]
            b = base.copy(); b.colorbar_extend = EXTEND_DOMAIN[j]
            real = (a == b)
            assert real == model_equal(a, b), (
                "equality reference unsound on extension flags %r vs %r: "
                "real=%r model=%r"
                % (EXTEND_DOMAIN[i], EXTEND_DOMAIN[j], real, model_equal(a, b)))
            if i != j:
                assert real is False, (
                    "extension-flag values %r and %r are not separated by the "
                    "real comparison; the flag leg would then admit a carrier "
                    "that merges them"
                    % (EXTEND_DOMAIN[i], EXTEND_DOMAIN[j]))
            else:
                assert real is True, (
                    "equal tables, equal labels and equal extension flag %r "
                    "must compare equal" % (EXTEND_DOMAIN[i],))

    # An INDETERMINATE table entry: the elementwise fold reports unequal against
    # every entry, so such a table is equal to NO table -- itself included. Both
    # routes below are public API.
    ind = base.with_extremes(bad=(INDETERMINATE, 0.0, 0.0, 1.0))
    ind._init()
    assert np.isnan(ind._lut).any(), (
        "with_extremes(bad=...) did not place the indeterminate entry")
    assert (ind == ind) is False, (
        "a table carrying an indeterminate entry compares equal to itself; the "
        "entry relation would then be reflexive, which the fold is not")
    assert model_equal(ind, ind) is False
    ind2 = base.with_extremes(bad=(INDETERMINATE, 0.0, 0.0, 1.0))
    ind2._init()
    assert (ind == ind2) == model_equal(ind, ind2) == False
    assert (ind == base) == model_equal(ind, base) == False
    assert (base == ind) == model_equal(base, ind) == False

    ind3 = make_cmap("ind3", [(INDETERMINATE, 0.2, 0.3, 1.0),
                             (0.4, 0.5, 0.6, 1.0)])
    assert (ind3 == ind3) == model_equal(ind3, ind3) == False
    ind4 = make_cmap("ind4-relabelled", [(INDETERMINATE, 0.2, 0.3, 1.0),
                                         (0.4, 0.5, 0.6, 1.0)])
    assert (ind3 == ind4) == model_equal(ind3, ind4) == False
    # a determinate table still compares equal to its relabelled twin, so the
    # indeterminate case above is not a blanket "everything is unequal"
    det3 = make_cmap("det3", [(0.1, 0.2, 0.3, 1.0), (0.4, 0.5, 0.6, 1.0)])
    det4 = make_cmap("det4-relabelled", [(0.1, 0.2, 0.3, 1.0),
                                         (0.4, 0.5, 0.6, 1.0)])
    assert (det3 == det4) == model_equal(det3, det4) == True

    # mutated lookup table (set_bad changes the lut) -> unequal
    c = base.copy()
    c.set_bad('y')
    assert (c == base) == model_equal(c, base) == False

    # truncated lookup table (different size) -> unequal
    c = base.copy()
    c._lut = c._lut[:10, :]
    assert (c == base) == model_equal(c, base) == False

    # non-Colormap comparand -> unequal
    assert (base == 42) is False

    # fuzz: random labels / extension flags / small luts
    rng = random.Random(25479)
    names = ["a", "b", "viridis", "some_cmap_name", "my_cmap_name",
             "Test", "wrong-cmap", "test-cmap", "", "x" * 8]
    def fuzz_channel():
        # an indeterminate channel value some of the time, so the fold's
        # non-reflexive side is reached by the fuzz and not only by the
        # boundary cases above
        return INDETERMINATE if rng.random() < 0.08 else rng.random()

    def fuzz_row():
        return (fuzz_channel(), rng.random(), rng.random(), 1.0)

    for _ in range(4000):
        n = rng.randint(2, 6)
        colors1 = [fuzz_row() for _ in range(n)]
        same_colors = rng.random() < 0.5
        if same_colors:
            colors2 = list(colors1)
        else:
            m = rng.randint(2, 6)
            colors2 = [fuzz_row() for _ in range(m)]
        a = make_cmap(rng.choice(names), colors1)
        b = make_cmap(rng.choice(names), colors2)
        # the extension flag is drawn over its WHOLE value domain on both
        # operands: restricting it to the two-valued part would leave the
        # majority of the domain unobserved
        if rng.random() < 0.5:
            a.colorbar_extend = rng.choice(EXTEND_DOMAIN)
        if rng.random() < 0.5:
            b.colorbar_extend = rng.choice(EXTEND_DOMAIN)
        real = (a == b)
        mod = model_equal(a, b)
        assert real == mod, (
            "equality reference unsound: labels=(%r,%r) extend=(%r,%r) "
            "real=%r model=%r" % (a.name, b.name, a.colorbar_extend,
                                  b.colorbar_extend, real, mod))


# --- A-reference 2: register relabels the stored snapshot --------------------

def check_register_reference():
    # the exact scenario from the issue / F2P test: a builtin colormap whose
    # label was changed, registered under a DIFFERENT label.
    cmap = matplotlib.colormaps["viridis"].with_extremes(over='r')
    cmap.name = "test-cmap"
    supplied_label = cmap.name
    supplied_extend = cmap.colorbar_extend

    matplotlib.colormaps.register(name='wrong-cmap', cmap=cmap)

    # supplied mapping left untouched
    assert cmap.name == supplied_label, "supplied cmap.name must be untouched"
    assert cmap.colorbar_extend == supplied_extend
    assert plt.get_cmap("wrong-cmap").colorbar_extend == supplied_extend, (
        "snapshot must carry the supplied extension flag value exactly")

    # lookup by the chosen label returns a snapshot whose OWN label is that label
    returned = plt.get_cmap("wrong-cmap")
    assert returned is not cmap, "registry must store an independent snapshot"
    assert returned.name == "wrong-cmap", (
        "snapshot label must equal the registration label, got %r"
        % returned.name)
    # the snapshot equals the supplied mapping under the label-free equality
    assert returned == cmap, "snapshot must equal the supplied mapping"
    assert model_equal(returned, cmap) is True

    matplotlib.colormaps.unregister("wrong-cmap")

    # fuzz: many (supplied-label, registration-label) pairs
    rng = random.Random(254790)
    for k in range(300):
        reg_label = "reg-%d" % k
        supplied = "src-%d" % rng.randint(0, 9999)
        n = rng.randint(2, 6)
        colors = [(rng.random(), rng.random(), rng.random(), 1.0)
                  for _ in range(n)]
        if rng.random() < 0.25:
            colors[rng.randrange(len(colors))] = (INDETERMINATE, 0.2, 0.3, 1.0)
        cm = ListedColormap(colors, name=supplied)
        # the whole flag domain, not just one string member: the snapshot must
        # carry the flag through EXACTLY
        cm.colorbar_extend = rng.choice(EXTEND_DOMAIN)
        snap_extend = cm.colorbar_extend
        snap_label_src = cm.name
        matplotlib.colormaps.register(name=reg_label, cmap=cm)
        # supplied untouched
        assert cm.name == snap_label_src
        out = plt.get_cmap(reg_label)
        assert out is not cm
        assert out.name == reg_label, (
            "snapshot label %r != registration label %r" % (out.name, reg_label))
        # compared WITHOUT a bool() coercion: coercing would accept a snapshot
        # that had merged two distinct flag values into one
        assert out.colorbar_extend == snap_extend and \
            type(out.colorbar_extend) is type(snap_extend), (
                "snapshot extension flag %r is not the supplied %r"
                % (out.colorbar_extend, snap_extend))
        # copy fidelity is BITWISE, so the snapshot's table matches the supplied
        # one entry for entry even where an entry is indeterminate. That is a
        # different question from the ==-relation, which is why equal_nan is set
        # here and left at its default in the equality reference above.
        cm._init(); out._init()
        assert np.array_equal(out._lut, cm._lut, equal_nan=True), (
            "snapshot lookup table is not a faithful copy of the supplied one")
        # ... and the ==-relation then agrees with the model on the same pair,
        # in whichever direction the fold lands: equal for a determinate table,
        # unequal when the table carries an indeterminate entry.
        determinate = not np.isnan(cm._lut).any()
        assert (out == cm) == model_equal(out, cm) == determinate, (
            "registration snapshot equality disagrees: real=%r model=%r "
            "determinate=%r" % (out == cm, model_equal(out, cm), determinate))
        matplotlib.colormaps.unregister(reg_label)


def main():
    check_equality_reference()
    check_register_reference()
    print("G-AX OK: Colormap.__eq__ label-free equality (A-reference 1) and "
          "register snapshot relabelling (A-reference 2) sound on boundary + "
          "fuzz inputs against real matplotlib; the extension flag was "
          "observed over all %d of its values (all %d distinct pairs separated) "
          "and the table comparison over indeterminate as well as determinate "
          "entries." % (len(EXTEND_DOMAIN),
                        len(EXTEND_DOMAIN) * (len(EXTEND_DOMAIN) - 1) // 2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
