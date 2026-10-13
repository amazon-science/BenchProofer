"""Twin-artifact model for sphinx-doc__sphinx-10435.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When a highlighted inline-code fragment is emitted into a LaTeX body, the
  fragment is delivered to the renderer as a wrapper of the form

        OPEN_WRAP <line-break> <highlighted-content> <line-break> CLOSE_WRAP

  where OPEN_WRAP opens the inline-code group and CLOSE_WRAP closes it. A bare
  line-break that sits directly adjacent to the opening wrapper or directly
  before the closing wrapper is significant to the renderer: it is rendered as
  one space of horizontal material. To deliver inline code with NO spurious
  leading or trailing space, the line-break that follows the opening wrapper
  and the line-break that precedes the closing wrapper must each be neutralised
  by a line-suppression marker (the renderer's end-of-line comment character),
  placed at the END of the opening-wrapper line and at the END of the content,
  so that those two line-breaks contribute no horizontal material.

  Concretely the assembled output must be

        OPEN_WRAP  SUPPRESS  BREAK  content  SUPPRESS  BREAK  CLOSE_WRAP

  i.e. a suppression marker immediately after the opening wrapper and another
  immediately after the content, each directly preceding a line-break — so that
  neither line-break renders as a space.

The carrier produced upstream is a single text string of the documented shape
above. Strings are modelled as `List[int]` of code points (Nagini bans `str`
indexing); the specification is carried by `PSeq[int]`.

The string surgery that derives the assembled output from the upstream carrier
is modelled DEEPLY (spelled out as sequence take/drop/concat operations); the
upstream highlighter that produces the carrier is an unchanged producer whose
documented output shape is the precondition, NOT a consumed axiom.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# (none) — the transformation is modelled deeply; the upstream highlighter that
# produces the carrier is captured by the documented input-shape precondition,
# not by a consumed @ContractOnly axiom.
# axioms-end


# pure-start
@Pure
def cp_break() -> int:
    # the line-break code point ('\n')
    return 10


@Pure
def cp_suppress() -> int:
    # the renderer's end-of-line line-suppression / comment marker ('%')
    return 37


@Pure
def open_wrap() -> PSeq[int]:
    # the opening inline-code wrapper after substitution
    # (`\sphinxcode{\sphinxupquote{`)
    return PSeq(92, 115, 112, 104, 105, 110, 120, 99, 111, 100, 101, 123,
                92, 115, 112, 104, 105, 110, 120, 117, 112, 113, 117, 111,
                116, 101, 123)


@Pure
def close_wrap() -> PSeq[int]:
    # the closing inline-code wrapper appended last (`}}`)
    return PSeq(125, 125)
# pure-end


def assemble_inline_code(content: List[int]) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(content), 1 / 2))
    # The upstream highlighter delivers the fragment as the documented shape:
    #   OPEN ++ BREAK ++ content ++ BREAK ++ CLOSE ++ BREAK
    # (an opening marker, the content, a closing marker, and one trailing
    # line-break).
    # The content carries no internal line-break adjacent to the markers that
    # would itself rstrip away (its final code point is not a line-break), so
    # the only trailing whitespace of the carrier is the single closing break.
    Requires(len(content) > 0)
    Requires(content[len(content) - 1] != cp_break())
    # The assembly must COMPLETE (total correctness): without this obligation
    # every Ensures below is claimed only of runs that reach the return, so an
    # implementation that never gets there satisfies the whole postcondition
    # vacuously. Level 2 leaves room for the list allocations the assembly
    # performs (at level 1 an allocation's own obligation has nowhere below the
    # caller to go); it calls no other obligated method.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(content), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The assembled output is exactly:
    #   open_wrap ++ [SUPPRESS] ++ [BREAK] ++ content ++ [SUPPRESS] ++ [BREAK]
    #     ++ close_wrap
    Ensures(ToSeq(Result()) ==
            open_wrap()
            + PSeq(cp_suppress())
            + PSeq(cp_break())
            + ToSeq(content)
            + PSeq(cp_suppress())
            + PSeq(cp_break())
            + close_wrap())
    # The two line-breaks adjacent to the wrappers are each preceded by a
    # suppression marker (so neither renders as horizontal space):
    # a suppression marker sits immediately after the opening wrapper, directly
    # before the line-break that follows it ...
    Ensures(Result()[len(open_wrap())] == cp_suppress())
    Ensures(Result()[len(open_wrap()) + 1] == cp_break())
    # ... and a suppression marker sits immediately after the content, directly
    # before the line-break that precedes the closing wrapper.
    Ensures(Result()[len(Result()) - len(close_wrap()) - 2] == cp_suppress())
    Ensures(Result()[len(Result()) - len(close_wrap()) - 1] == cp_break())
    # post-conditions-end
    # impl-start
    # The documented upstream carrier is
    #   OPEN ++ BREAK ++ content ++ BREAK ++ CLOSE ++ BREAK,
    # where OPEN is the upstream opening marker and CLOSE the upstream closing
    # marker (both opaque here — their concrete shape is the producer's, not
    # part of the desired behaviour).
    #
    # op1: replace OPEN by open_wrap on a carrier that begins with OPEN
    #      ==>  open_wrap ++ tail, where
    #      tail = BREAK ++ content ++ BREAK ++ CLOSE ++ BREAK.
    # op2 (rstrip): drop the trailing whitespace BREAK.
    # op3 (drop the trailing CLOSE marker only): the remaining prefix is
    #      open_wrap ++ BREAK ++ content ++ BREAK.
    # op4: append close_wrap.
    br = cp_break()

    # prefix = open_wrap ++ [BREAK]  (literal opening wrapper, no suppressor)
    result = [92, 115, 112, 104, 105, 110, 120, 99, 111, 100, 101, 123,
              92, 115, 112, 104, 105, 110, 120, 117, 112, 113, 117, 111,
              116, 101, 123, br]  # type: List[int]
    Assert(ToSeq(result) == open_wrap() + PSeq(br))
    # copy the content
    k = 0
    while k < len(content):
        # invariants-start
        Invariant(Acc(list_pred(content), 1 / 2))
        Invariant(0 <= k and k <= len(content))
        Invariant(Acc(list_pred(result)))
        Invariant(ToSeq(result) ==
                  open_wrap() + PSeq(br) + ToSeq(content).take(k))
        # At most len(content) - k + 1 passes remain: the content is held
        # read-only (Acc(...,1/2)) by the invariant above so its length cannot
        # change, and k rises by exactly one per pass, so the bound strictly
        # decreases; the guard k < len(content) keeps it >= 2 on entry to a pass
        # (so it never reaches the unsatisfiable 0).
        Invariant(MustTerminate(len(content) - k + 1))
        # invariants-end
        result = result + [content[k]]
        k = k + 1
    Assert(ToSeq(content).take(len(content)) == ToSeq(content))
    # suffix = [BREAK] ++ close_wrap  (no suppressor before the closer)
    result = result + [br, 125, 125]
    Assert(PSeq(125, 125) == close_wrap())
    return result
    # impl-end
