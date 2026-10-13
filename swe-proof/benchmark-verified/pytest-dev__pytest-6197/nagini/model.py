"""Twin-artifact model for pytest-dev__pytest-6197.

Behaviour under specification (stated as desired behaviour, not as an edit):

A directory-backed test container is discovered in two distinct phases.

  (1) Enumerating the children of such a container (the discovery phase) must
      NOT load the container's own underlying object. Loading that object is an
      observable, possibly-failing side effect; it must be deferred. After the
      enumeration phase returns, the load side effect has happened exactly as
      many times as it had before the phase began (i.e. discovery performs zero
      loads), and the loaded/unloaded status of the container is unchanged.

  (2) Reading the container's underlying object (the access phase) loads it on
      demand: if it has not yet been loaded, exactly one load side effect is
      performed and the container becomes loaded; if it was already loaded, no
      further load happens. After an access the container is always loaded, and
      the access never performs more than one load.

The container is modelled as a minimal class carrying only the two touched
pieces of state: a boolean recording whether its underlying object has been
loaded, and a counter recording how many times the (side-effecting) load
primitive has run. The load primitive that produces the underlying object is
modelled directly as the single state transition that performs one load.

Both phases are bounded, straight-line operations: each MUST terminate and
return (a total-correctness obligation, carried as MustTerminate in the
preconditions). An implementation that diverges would satisfy the value
postconditions only vacuously and would never hand control back to the
test-collection run.

The load side effect is IRREVERSIBLE: once performed it cannot be undone, so
a merely net-unchanged counter is not the specified behaviour. The contracts
therefore grant each phase write permission on the load state only where a
load is legitimately allowed to happen: nowhere during the enumeration phase
(read-only fractional permission), and only on a not-yet-loaded container
during the access phase. Any body that touches the load state outside those
windows — even if it later restores the old values — fails verification.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import Optional
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


class Container:
    def __init__(self) -> None:
        Requires(MustTerminate(1))  # type: ignore
        Ensures(Acc(self.loaded) and Acc(self.load_count))  # type: ignore
        Ensures(self.loaded is False and self.load_count == 0)  # type: ignore
        self.loaded = False        # underlying object not yet loaded
        self.load_count = 0        # number of load side effects performed


# axioms-start
# (no @ContractOnly callee axioms: the load primitive is modelled deeply below
#  as the in-line state transition `loaded := True; load_count += 1`, so the
#  proof consumes no opaque callee. See refinement.md / mapping.md.)
# axioms-end


# pure-start
# (no auxiliary pure spec functions are required for this behaviour)
# pure-end


def access_object(c: Container) -> None:
    """The on-demand access phase: load the underlying object iff not already
    loaded, then leave the container loaded. At most one load is performed."""
    # pre-conditions-start
    Requires(Acc(c.loaded))
    Requires(Acc(c.load_count, 1/2))
    # The load side effect is irreversible, so write permission on the load
    # counter is granted only in the window where a load may legitimately
    # happen: when the container is not yet loaded. On an already-loaded
    # container the counter is read-only for this phase, so even a
    # transient, later-reverted touch of it cannot verify.
    Requires(Implies(not c.loaded, Acc(c.load_count, 1/2)))
    Requires(c.load_count >= 0)
    # Total correctness: the access phase must terminate and hand back
    # control. A diverging body would satisfy the value postconditions only
    # vacuously (it never returns), which is not the specified behaviour.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(c.loaded))
    Ensures(Acc(c.load_count, 1/2))
    Ensures(Implies(not Old(c.loaded), Acc(c.load_count, 1/2)))
    # After an access the container is loaded.
    Ensures(c.loaded is True)
    # A load happens exactly once, and only when it had not been loaded before:
    #   - already loaded  -> no further load
    #   - not yet loaded   -> exactly one load
    Ensures(Implies(Old(c.loaded), c.load_count == Old(c.load_count)))
    Ensures(Implies(not Old(c.loaded), c.load_count == Old(c.load_count) + 1))
    # post-conditions-end
    # impl-start
    if not c.loaded:
        c.loaded = True
        c.load_count = c.load_count + 1
    # impl-end


def enumerate_children(c: Container) -> None:
    """The discovery phase: enumerate the container's children WITHOUT loading
    its own underlying object. No load side effect is performed; the
    loaded/unloaded status is preserved."""
    # pre-conditions-start
    # Discovery may READ the container's load state but must never perform
    # (nor transiently perform-and-revert) a load: the load side effect is
    # irreversible, so a net-unchanged counter is not good enough. Read-only
    # fractional permission makes ANY write to the load state — even one
    # later restored to the old value — a verification failure.
    Requires(Acc(c.loaded, 1/2) and Acc(c.load_count, 1/2))
    Requires(c.load_count >= 0)
    # Total correctness: the discovery phase must terminate and hand back
    # control to the collection run. A diverging body would satisfy the
    # "discovery loads nothing" postconditions only vacuously (discovery
    # never finishes), which is not the specified behaviour.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(c.loaded, 1/2) and Acc(c.load_count, 1/2))
    # The discriminating guarantee: discovery loads nothing.
    Ensures(c.load_count == Old(c.load_count))
    # The loaded/unloaded status is left untouched by discovery.
    Ensures(c.loaded == Old(c.loaded))
    # post-conditions-end
    # impl-start
    # Enumeration of children proceeds without touching the container's own
    # underlying object; no load is triggered here.
    pass
    # impl-end
