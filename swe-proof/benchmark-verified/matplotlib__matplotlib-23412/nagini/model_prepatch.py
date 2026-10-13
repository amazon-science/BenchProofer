"""Twin-artifact model for matplotlib__matplotlib-23412.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A filled outline shape stores its boundary stroke style as a dash pattern: a
  scalar phase (the starting position along the on/off cycle) together with the
  even-length on/off ink-length sequence. When the shape is rendered, the dash
  pattern handed to the drawing back end must be the shape's OWN dash pattern:
  its phase is preserved exactly, and the on/off sequence is preserved exactly.

  In particular, two shapes whose stored dash patterns differ only in their
  phase must be handed dash patterns that still differ in that same phase; the
  phase a caller supplies is honoured.

The phase and the on/off ink lengths are modelled as integers (the tested
behaviour is whether the stored phase is carried through to the renderer
exactly -- this is independent of any floating-point magnitude, so an exact
integer carrier is faithful; see mapping.md). The dash pattern handed to the
renderer is modelled as a single `List[int]` whose head element is the phase
passed to the back end and whose tail is the on/off sequence passed to the
back end.

There are no axiomatized callees: the modelled behaviour is a pure
construction of the render-time dash pattern from the stored one.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# axioms-end


# pure-start
# pure-end


def render_dash_pattern(phase: int, onoff: List[int]) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(onoff), 1 / 2))
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    # The stored on/off sequence is read-only: it is returned at the same
    # fractional permission it was required at, unmutated.
    Ensures(Acc(list_pred(onoff), 1 / 2))
    Ensures(ToSeq(onoff) == Old(ToSeq(onoff)))
    # The render-time pattern is freshly owned and never shorter than its head.
    Ensures(Acc(list_pred(Result())))
    Ensures(len(Result()) == len(onoff) + 1)
    Ensures(len(Result()) >= 1)
    # The phase handed to the renderer equals the stored phase exactly,
    # followed by the stored on/off sequence element-for-element in order. This
    # pins both the discriminating phase clause (a shape with a nonzero stored
    # phase must be rendered with that same phase) and the on/off passthrough.
    Ensures(ToSeq(Result()) == PSeq(phase) + Old(ToSeq(onoff)))
    Ensures(Result()[0] == phase)
    # post-conditions-end
    # impl-start
    # Pre-patch behaviour: when constructing the render-time pattern the stored
    # phase is discarded and replaced by zero; only the on/off sequence is
    # carried through. A shape with a nonzero stored phase is therefore rendered
    # as if its phase were zero.
    result = [0]  # type: List[int]
    i = 0
    while i < len(onoff):
        # invariants-start
        Invariant(Acc(list_pred(onoff), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(onoff))
        Invariant(len(result) == i + 1)
        Invariant(ToSeq(onoff) == Old(ToSeq(onoff)))
        Invariant(ToSeq(result) == PSeq(0) + ToSeq(onoff).take(i))
        Invariant(MustTerminate(len(onoff) - i + 1))
        # invariants-end
        Assert(ToSeq(onoff).take(i + 1) == ToSeq(onoff).take(i) + PSeq(onoff[i]))
        result.append(onoff[i])
        i = i + 1
    Assert(ToSeq(onoff).take(len(onoff)) == ToSeq(onoff))
    return result
    # impl-end
