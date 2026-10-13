"""Twin-artifact model for matplotlib__matplotlib-25311.

Behaviour under specification (stated as desired behaviour, not as an edit):

  An interactive helper that lets a figure element be repositioned with the
  mouse needs the figure's drawing surface (its "canvas") to redraw during a
  drag. That drawing-surface object belongs to the live, possibly GUI-bound
  runtime; it is deliberately NOT part of the figure's serialisable state.

  The required behaviour of the helper's set-up is therefore twofold:

    (1) Read access is preserved. Asking the helper for its drawing surface
        yields exactly the figure's current surface, every time -- so the
        redraw path during a drag keeps seeing the live surface.

    (2) The helper's *serialisable state* -- the values that are written out
        when the helper (reachable from the figure through its registered
        callbacks) is serialised -- must NOT include the drawing-surface
        object. The genuine helper attributes (its reference element, its
        in-progress-drag flag, its connection ids, its blit flag) are retained
        in that state, but the drawing surface is obtained on demand rather
        than held, so a serialisation of the figure carries no reference to it.

The drawing-surface object and the other retained values are modelled by
distinct integer object identities. The helper's serialisable state -- the
sequence of object identities that a serialisation of the helper would emit --
is modelled as a ``List[int]``; specification is carried by ``PSeq[int]``.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# (no unchanged callee is axiomatized: the behaviour under specification is the
# structure of the helper's serialisable state, modelled deeply below.)
# axioms-end


# pure-start
@Pure
def read_surface(surface: int) -> int:
    """The drawing surface the helper hands back when asked for its surface:
    exactly the figure's current surface, read on demand and unchanged."""
    return surface


@Pure
def contains(s: PSeq[int], v: int) -> bool:
    """Front-recursive membership over a pure sequence: ``v`` occurs in ``s``.
    Front-recursion gives one auto-unfold per construction step so callers can
    discharge membership facts element by element."""
    if len(s) == 0:
        return False
    return s[0] == v or contains(s.drop(1), v)
# pure-end


def build_helper_state(surface: int, element_id: int,
                       drag_flag: int, blit_flag: int,
                       cid_pick: int, cid_release: int) -> List[int]:
    # pre-conditions-start
    # The drawing surface is a distinct object from each genuine retained
    # attribute value (distinct runtime object identities), so "the surface is
    # absent from the serialisable state" is not vacuously implied by it
    # coinciding with a retained value.
    Requires(surface != element_id)
    Requires(surface != drag_flag)
    Requires(surface != blit_flag)
    Requires(surface != cid_pick)
    Requires(surface != cid_release)
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(Result())))
    # (1) Read access preserved: asking the helper for its surface returns it.
    Ensures(read_surface(surface) == surface)
    # (2) The serialisable state carries NO reference to the drawing surface.
    Ensures(not contains(ToSeq(Result()), surface))
    # The genuine helper attributes ARE retained in the serialisable state, so
    # the result is the real instance state and not a vacuously-empty one.
    Ensures(contains(ToSeq(Result()), element_id))
    Ensures(contains(ToSeq(Result()), drag_flag))
    Ensures(contains(ToSeq(Result()), blit_flag))
    Ensures(contains(ToSeq(Result()), cid_pick))
    Ensures(contains(ToSeq(Result()), cid_release))
    # post-conditions-end
    # impl-start
    # The serialisable state holds the genuine helper attributes; the drawing
    # surface is obtained on demand (read_surface) rather than stored.
    state = [element_id, drag_flag, blit_flag,
             cid_pick, cid_release]  # type: List[int]
    # The sequence view of the literal state, spelled out so the front-recursive
    # membership predicate unfolds one element per step.
    s = ToSeq(state)  # type: PSeq[int]
    Assert(len(s) == 5)
    Assert(s[0] == element_id)
    Assert(s[1] == drag_flag)
    Assert(s[2] == blit_flag)
    Assert(s[3] == cid_pick)
    Assert(s[4] == cid_release)
    Assert(s.drop(1)[0] == drag_flag)
    Assert(s.drop(2)[0] == blit_flag)
    Assert(s.drop(3)[0] == cid_pick)
    Assert(s.drop(4)[0] == cid_release)
    Assert(len(s.drop(5)) == 0)
    # The drawing surface is absent: prove `not contains(..., surface)` from the
    # empty tail upward, each step discharging `head != surface` from the
    # distinctness preconditions.
    Assert(not contains(s.drop(5), surface))
    Assert(not contains(s.drop(4), surface))
    Assert(not contains(s.drop(3), surface))
    Assert(not contains(s.drop(2), surface))
    Assert(not contains(s.drop(1), surface))
    Assert(not contains(s, surface))
    # Each genuine attribute IS present: prove `contains` at its position by
    # unfolding to the element it sits at.
    Assert(contains(s, element_id))
    Assert(contains(s.drop(1), drag_flag))
    Assert(contains(s, drag_flag))
    Assert(contains(s.drop(2), blit_flag))
    Assert(contains(s.drop(1), blit_flag))
    Assert(contains(s, blit_flag))
    Assert(contains(s.drop(3), cid_pick))
    Assert(contains(s.drop(2), cid_pick))
    Assert(contains(s.drop(1), cid_pick))
    Assert(contains(s, cid_pick))
    Assert(contains(s.drop(4), cid_release))
    Assert(contains(s.drop(3), cid_release))
    Assert(contains(s.drop(2), cid_release))
    Assert(contains(s.drop(1), cid_release))
    Assert(contains(s, cid_release))
    return state
    # impl-end
