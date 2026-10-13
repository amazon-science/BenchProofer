"""Twin-artifact model for matplotlib__matplotlib-20859.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A plotting-container artist is attached to a *parent*. The parent may be one
  of two unrelated families:

    * a coordinate-system artist (the kind that itself already belongs to an
      enclosing canvas), or
    * any member of the canvas-surface family. That family has a common base
      type, and the family includes BOTH the whole top-level canvas AND a
      nested canvas region carved out of a larger canvas. A nested region is a
      genuine member of the canvas-surface family (it shares the family's base
      type) even though it is not the top-level canvas type.

  The behaviour pinned here is how the attachment classifies the parent and
  what canvas the new artist comes to belong to:

    * if the parent is a coordinate-system artist, the artist is flagged as
      belonging to coordinates, and the canvas it belongs to is the canvas that
      coordinate-system artist already sits on;
    * otherwise, if the parent is ANY member of the canvas-surface family
      (the top-level canvas OR a nested region alike), the artist is flagged as
      not-coordinates and the canvas it belongs to is the parent itself;
    * otherwise the attachment is rejected.

  The discriminating case: a nested canvas region is a member of the
  canvas-surface family, so attaching the artist to it must SUCCEED — flag
  not-coordinates and make the artist belong to that nested region — and must
  NOT be rejected merely because the nested region is not the top-level canvas
  type.

The parent is modelled by a small object carrying a family tag and the identity
of the canvas it already sits on. Membership in the canvas-surface family is a
pure predicate over the tag that mirrors the real subtype relation (the nested
region and the top-level canvas both carry the family base type). Rejection is
a user-defined exception (a builtin exception in an `Exsures` crashes the Nagini
translator; mapping.md).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import Optional
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


class ParentRejected(Exception):
    """Signals a parent that belongs to neither family (the `TypeError` the
    desired behaviour raises). A builtin exception in an `Exsures` crashes the
    Nagini translator (mapping.md §2)."""


class Parent:
    """A candidate parent. `tag` identifies its class family; `host_canvas`
    is the identity of the canvas the parent itself already sits on (only used
    when the parent is a coordinate-system artist)."""

    def __init__(self, tag: int, host_canvas: int) -> None:
        Requires(MustTerminate(2))
        Ensures(Acc(self.tag) and self.tag == tag)
        Ensures(Acc(self.host_canvas) and self.host_canvas == host_canvas)
        self.tag = tag                # type: int
        self.host_canvas = host_canvas  # type: int


class Attached:
    """The outcome of a successful attachment: the coordinates flag and the
    identity of the canvas the new artist belongs to."""

    def __init__(self, is_coords: bool, canvas: int) -> None:
        Requires(MustTerminate(2))
        Ensures(Acc(self.is_coords) and self.is_coords == is_coords)
        Ensures(Acc(self.canvas) and self.canvas == canvas)
        self.is_coords = is_coords  # type: bool
        self.canvas = canvas        # type: int


# Class-family tags (distinct identities; the exact integers are immaterial,
# only the subtype relation below matters).
TAG_COORDS = 0      # a coordinate-system artist
TAG_TOPLEVEL = 1    # the top-level canvas type
TAG_NESTED = 2      # a nested canvas region (shares the family base type)
TAG_FOREIGN = 3     # something in neither family


# pure-start
@Pure
def is_coords_artist(tag: int) -> bool:
    """Whether the parent is a coordinate-system artist."""
    return tag == TAG_COORDS


@Pure
def in_canvas_family(tag: int) -> bool:
    """Whether the parent is a member of the canvas-surface family, i.e. its
    class carries the family base type. BOTH the top-level canvas and a nested
    canvas region are members (they share the base type); a coordinate-system
    artist and a foreign object are not. Mirrors the real subtype relation
    (mapping.md §3)."""
    return tag == TAG_TOPLEVEL or tag == TAG_NESTED
# pure-end


def attach(parent: Parent) -> Attached:
    # pre-conditions-start
    # The parent is read-only (the attachment inspects it but does not mutate
    # it); fractional permission, required and ensured, so no caller can satisfy
    # a postcondition vacuously by overwriting the input.
    Requires(Acc(parent.tag, 1 / 2))
    Requires(Acc(parent.host_canvas, 1 / 2))
    Requires(MustTerminate(6))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(parent.tag, 1 / 2))
    Ensures(Acc(parent.host_canvas, 1 / 2))
    # Returns normally (a successful attachment) exactly when the parent is a
    # coordinate-system artist OR any member of the canvas-surface family.
    Ensures(is_coords_artist(parent.tag) or in_canvas_family(parent.tag))
    # On success the result carries full permission to a fresh outcome object.
    Ensures(Acc(Result().is_coords) and Acc(Result().canvas))
    # Coordinate-system parent: flagged as coordinates, belongs to the canvas
    # the parent already sits on.
    Ensures(Implies(is_coords_artist(parent.tag),
                    Result().is_coords and Result().canvas == parent.host_canvas))
    # Any canvas-family parent (top-level OR nested region alike): flagged as
    # not-coordinates, belongs to the parent itself. Pinned for EVERY family
    # member so the nested region is not excluded.
    Ensures(Implies(in_canvas_family(parent.tag),
                    (not Result().is_coords) and Result().canvas == parent.tag))
    # Rejects (raises) exactly when the parent belongs to neither family.
    Exsures(ParentRejected,
            Acc(parent.tag, 1 / 2)
            and Acc(parent.host_canvas, 1 / 2)
            and (not is_coords_artist(parent.tag))
            and (not in_canvas_family(parent.tag)))
    # post-conditions-end
    # impl-start
    if is_coords_artist(parent.tag):
        return Attached(True, parent.host_canvas)
    elif in_canvas_family(parent.tag):
        return Attached(False, parent.tag)
    else:
        raise ParentRejected()
    # impl-end
