#!/usr/bin/env python3
"""G-AX executable soundness check for matplotlib__matplotlib-20859.

This bundle consumes NO `@ContractOnly` axiom. The only non-trivial semantic
fact the model relies on is the SUBTYPE RELATION that the parent-classification
dispatch tests: which parent classes are members of the canvas-surface family
(the `FigureBase` family), which are coordinate-system artists (`Axes`), and
which are foreign. The model encodes that relation DEEPLY as the pure
predicates `in_canvas_family` / `is_coords_artist` over class-family tags
(model.py pure region). This script validates that deep model against the REAL
matplotlib class hierarchy (an A-reference check):

  TAG_COORDS    -> matplotlib.axes.Axes
  TAG_TOPLEVEL  -> matplotlib.figure.Figure       (subclass of FigureBase)
  TAG_NESTED    -> matplotlib.figure.SubFigure     (subclass of FigureBase)
  TAG_FOREIGN   -> a plain artist in neither family (matplotlib.lines.Line2D)

The model's two predicates must agree, for every modelled tag, with the REAL
isinstance/issubclass relations the gold dispatch uses:

  is_coords_artist(tag)  ==  issubclass(real_class, Axes)
  in_canvas_family(tag)  ==  (issubclass(real_class, FigureBase)
                              and not issubclass(real_class, Axes))

and the discriminating fact must hold:

  SubFigure IS a FigureBase  (so the nested region is accepted), and
  SubFigure is NOT a Figure  (so the pre-patch narrow `Figure` check rejected it).

Imports only matplotlib (the very package the patch lives in) and the standard
library. Exit 0 iff every obligation holds.
"""
import sys

import matplotlib
matplotlib.use("Agg")  # headless; no display needed for class-hierarchy checks

from matplotlib.axes import Axes
from matplotlib.figure import Figure, FigureBase, SubFigure
from matplotlib.lines import Line2D


# --- model.py reference encodings (kept in lock-step with model.py) ----------

TAG_COORDS = 0
TAG_TOPLEVEL = 1
TAG_NESTED = 2
TAG_FOREIGN = 3

# tag -> the real matplotlib class it stands for (mapping.md §3)
_REAL_CLASS = {
    TAG_COORDS: Axes,
    TAG_TOPLEVEL: Figure,
    TAG_NESTED: SubFigure,
    TAG_FOREIGN: Line2D,
}


def model_is_coords_artist(tag):
    """model.py pure: is_coords_artist."""
    return tag == TAG_COORDS


def model_in_canvas_family(tag):
    """model.py pure: in_canvas_family."""
    return tag == TAG_TOPLEVEL or tag == TAG_NESTED


# --- the real dispatch predicates, as the gold patch expresses them ----------

def real_is_coords_artist(cls):
    """The gold first branch: `isinstance(parent, Axes)`."""
    return issubclass(cls, Axes)


def real_in_canvas_family(cls):
    """The gold second branch (post-patch): `isinstance(parent, FigureBase)`,
    reached only when the first branch did not fire."""
    return issubclass(cls, FigureBase) and not issubclass(cls, Axes)


def main():
    # 1. The two model predicates agree with the real subtype relation for
    #    every modelled tag.
    for tag, cls in _REAL_CLASS.items():
        assert model_is_coords_artist(tag) == real_is_coords_artist(cls), (
            "is_coords_artist deep model unsound for %s (tag %d): model=%r real=%r"
            % (cls.__name__, tag, model_is_coords_artist(tag),
               real_is_coords_artist(cls)))
        assert model_in_canvas_family(tag) == real_in_canvas_family(cls), (
            "in_canvas_family deep model unsound for %s (tag %d): model=%r real=%r"
            % (cls.__name__, tag, model_in_canvas_family(tag),
               real_in_canvas_family(cls)))

    # 2. The three branches are mutually exclusive and exhaustive over the
    #    modelled tags (no class falls into two families).
    for tag, cls in _REAL_CLASS.items():
        coords = real_is_coords_artist(cls)
        family = real_in_canvas_family(cls)
        assert not (coords and family), (
            "%s is BOTH coords and canvas-family" % cls.__name__)

    # 3. The discriminating subtype facts the whole fix turns on.
    assert issubclass(SubFigure, FigureBase), (
        "SubFigure must be a FigureBase (the nested region must be accepted)")
    assert not issubclass(SubFigure, Figure), (
        "SubFigure must NOT be a Figure (the pre-patch narrow check rejected it)")
    assert issubclass(Figure, FigureBase), (
        "Figure must be a FigureBase")
    assert not issubclass(Axes, FigureBase), (
        "Axes must not be in the canvas-surface family")
    assert not issubclass(Line2D, FigureBase) and not issubclass(Line2D, Axes), (
        "a foreign artist must be in neither family")

    # 4. SubFigure is genuinely accepted under the post-patch family check but
    #    rejected under the pre-patch narrow Figure check (the bug -> fix delta,
    #    expressed purely over the real classes, no repo edit referenced).
    assert real_in_canvas_family(SubFigure), (
        "post-patch dispatch must accept SubFigure as a canvas-family parent")
    assert not issubclass(SubFigure, Figure), (
        "pre-patch dispatch (isinstance(parent, Figure)) would reject SubFigure")

    print("G-AX OK: in_canvas_family / is_coords_artist deep model == real "
          "matplotlib subtype relation over %d classes; SubFigure is a "
          "FigureBase but not a Figure (the discriminating fact)."
          % len(_REAL_CLASS))
    return 0


if __name__ == "__main__":
    sys.exit(main())
