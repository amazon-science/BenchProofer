"""Twin-artifact model for matplotlib__matplotlib-25775.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A drawable glyph object carries its own per-object edge-smoothing preference,
  rather than always deferring to a single global default. The desired
  behaviour is exactly:

    (1) Construction. A glyph is created with an optional preference argument.
        When that argument is omitted (the absent value), the object's stored
        preference is the global default supplied at construction time. When
        the argument is supplied, the object's stored preference is exactly the
        supplied value, overriding the global default.

    (2) Read-back. Querying a glyph's preference returns exactly the value it
        currently stores.

    (3) Update. Setting a glyph's preference to a value makes a subsequent query
        return that value, and marks the object as needing redraw.

    (4) Copying. Adopting another glyph's visual state copies the source glyph's
        stored preference, so the destination subsequently reports the source's
        value.

The preference is a boolean; "absent" is modelled by the optional ``None``.
The object is modelled as a minimal class carrying only the one touched field
(its stored preference) plus a redraw flag.  This is the per-object state whose
presence/absence the tested behaviour distinguishes from the global default.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import Optional
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# (no callee is axiomatized: the behaviour is pure in-object state — a stored
# preference, its read-back, its update, and its copy — modelled deeply.)
# axioms-end


# pure-start
# (no auxiliary pure spec functions are required for this behaviour)
# pure-end


class Glyph:
    def __init__(self, pref: bool) -> None:
        Requires(MustTerminate(2))
        Ensures(Acc(self.pref) and self.pref == pref)        # type: ignore
        Ensures(Acc(self.dirty) and self.dirty)              # type: ignore
        self.pref = pref      # type: bool
        self.dirty = True     # type: bool


def build_glyph(default: bool, supplied: Optional[bool]) -> Glyph:
    # pre-conditions-start
    Requires(MustTerminate(18))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(Result().pref))
    Ensures(Acc(Result().dirty))
    # (1) absent argument -> the global default; supplied argument -> that value
    Ensures(Implies(supplied is None, Result().pref == default))
    Ensures(Implies(supplied is not None, Result().pref == supplied))
    # post-conditions-end
    # impl-start
    # Pre-patch skeleton: the supplied per-object argument is ignored; the
    # object always takes the single global default.
    g = Glyph(default)
    return g
    # impl-end


def set_pref(g: Glyph, value: bool) -> None:
    # pre-conditions-start
    Requires(Acc(g.pref))
    Requires(Acc(g.dirty))
    Requires(MustTerminate(6))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(g.pref) and g.pref == value)
    # (3) update marks the object as needing redraw
    Ensures(Acc(g.dirty) and g.dirty)
    # post-conditions-end
    # impl-start
    g.pref = value
    g.dirty = True
    # impl-end


def get_pref(g: Glyph) -> bool:
    # pre-conditions-start
    Requires(Acc(g.pref, 1 / 2))
    Requires(MustTerminate(10))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(g.pref, 1 / 2))
    # (2) read-back returns exactly the stored preference
    Ensures(Result() == g.pref)
    # post-conditions-end
    # impl-start
    return g.pref
    # impl-end


def copy_state(dst: Glyph, src: Glyph) -> None:
    # pre-conditions-start
    Requires(Acc(dst.pref))
    Requires(Acc(dst.dirty))
    Requires(Acc(src.pref, 1 / 2))
    Requires(MustTerminate(14))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(src.pref, 1 / 2))
    Ensures(Acc(dst.pref) and Acc(dst.dirty))
    # (4) destination adopts the source's stored preference
    Ensures(dst.pref == src.pref)
    Ensures(dst.dirty)
    # post-conditions-end
    # impl-start
    dst.pref = src.pref
    dst.dirty = True
    # impl-end
