#!/usr/bin/env python3
"""G-AX executable soundness check for matplotlib__matplotlib-20859.

Validates the ONE deep-model reference of this bundle (there are no consumed
axioms) against the REAL unchanged callee it models: the runtime type-membership
tests (`isinstance`) the parent-dispatch keys on, and the structural class
hierarchy fact the fix relies on.

  (A-reference) the `pure`-region predicates `isRegion` / `isCanvas` /
      `isTopCanvas` and the lemma `isTopCanvas → isCanvas` model:

        isRegion p     ⇔  isinstance(parent, Axes)
        isCanvas p     ⇔  isinstance(parent, FigureBase)     (BROAD test)
        isTopCanvas p  ⇔  isinstance(parent, Figure)         (NARROW test)

      and the load-bearing structural fact

        isTopCanvas p → isCanvas p
            ⇔  issubclass(Figure, FigureBase)  AND  for every real parent,
               isinstance(p, Figure) implies isinstance(p, FigureBase),

      together with the discriminating real object the fix is about:

        a nested sub-canvas (SubFigure) satisfies isCanvas but NOT isTopCanvas
            ⇔  isinstance(subfig, FigureBase) and not isinstance(subfig, Figure)

      and the branch disjointness the dispatch assumes:

        a plotting region is not a figure-like canvas and vice versa
            ⇔  not isinstance(axes, FigureBase) and not isinstance(fig, Axes).

Imports `matplotlib` — the same package the gold patch lives in (the repo under
test); plus stdlib. Exit 0 iff every obligation holds.
"""
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.axes import Axes
from matplotlib.figure import Figure, FigureBase, SubFigure


def check_hierarchy():
    """The static structural fact behind `isTopCanvas → isCanvas`: the narrow
    canvas class is a subclass of the broad one, and the region class is
    unrelated to both."""
    assert issubclass(Figure, FigureBase), (
        "isTopCanvas->isCanvas unsound: Figure is not a subclass of FigureBase")
    assert issubclass(SubFigure, FigureBase), (
        "isCanvas model unsound: SubFigure is not a subclass of FigureBase")
    assert not issubclass(SubFigure, Figure), (
        "discriminator unsound: SubFigure is a subclass of Figure (then the "
        "narrow test would already accept it and there would be no bug)")
    assert not issubclass(Axes, FigureBase), (
        "branch-disjointness unsound: Axes is a FigureBase")
    assert not issubclass(Figure, Axes), (
        "branch-disjointness unsound: Figure is an Axes")


def model_kind(parent):
    """The Container shape the model would assign, computed from the REAL
    membership tests in the impl's branch order."""
    if isinstance(parent, Axes):
        return "region"
    elif isinstance(parent, FigureBase):
        return "canvas"
    else:
        return "other"


def check_object(parent, want_region, want_canvas, want_top):
    """Per-object: the three predicates evaluated via the REAL isinstance match
    the model's intent, and the implication isTopCanvas->isCanvas holds."""
    is_region = isinstance(parent, Axes)        # isRegion
    is_canvas = isinstance(parent, FigureBase)  # isCanvas  (broad)
    is_top = isinstance(parent, Figure)         # isTopCanvas (narrow)
    assert is_region == want_region, (parent, "isRegion", is_region, want_region)
    assert is_canvas == want_canvas, (parent, "isCanvas", is_canvas, want_canvas)
    assert is_top == want_top, (parent, "isTopCanvas", is_top, want_top)
    # the load-bearing lemma, checked on the real object
    if is_top:
        assert is_canvas, (parent, "isTopCanvas without isCanvas")
    # branch disjointness: never both region and canvas
    assert not (is_region and is_canvas), (parent, "both region and canvas")


def main():
    check_hierarchy()

    n = 0
    # top-level canvas: isCanvas + isTopCanvas, not region
    for _ in range(6):
        check_object(plt.figure(), False, True, True); n += 1
    # nested sub-canvas (the reported case): isCanvas but NOT isTopCanvas
    for _ in range(6):
        check_object(plt.figure().subfigures(), False, True, False); n += 1
    # deeper nesting: still a canvas, still not top-level
    check_object(plt.figure().subfigures().subfigures(), False, True, False); n += 1
    # plotting region (Axes): isRegion only
    for _ in range(6):
        check_object(plt.figure().add_subplot(), True, False, False); n += 1
    # unsupported parents: none of the three
    for o in ["s", 42, 3.5, None, [1], {"k": 1}, object(), (1,)]:
        check_object(o, False, False, False); n += 1

    # The discriminator the whole fix turns on, stated explicitly:
    sf = plt.figure().subfigures()
    assert model_kind(sf) == "canvas", (
        "the reported bug's input (a nested sub-canvas) must be modeled as a "
        "canvas (accepted), but model_kind=%r" % model_kind(sf))
    assert isinstance(sf, FigureBase) and not isinstance(sf, Figure), (
        "discriminator unsound: a sub-canvas must be a broad FigureBase but not "
        "a narrow Figure")

    print("G-AX OK: isRegion/isCanvas/isTopCanvas deep model (== isinstance "
          "against Axes / FigureBase / Figure) and the isTopCanvas->isCanvas "
          "lemma sound on %d real objects; sub-canvas is FigureBase & not "
          "Figure (the discriminator)." % n)
    return 0


if __name__ == "__main__":
    sys.exit(main())
