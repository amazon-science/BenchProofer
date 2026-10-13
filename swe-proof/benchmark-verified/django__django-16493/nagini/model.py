"""Twin-artifact model for django__django-16493.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A configurable file-store attribute on a field may be supplied either as a
  concrete store, or as a deferred producer (a callable) that is evaluated once
  at construction time to obtain the concrete store. When the field is later
  reduced to its reconstructible form, the store attribute must be reported
  faithfully so the field can be rebuilt identically:

    * if a deferred producer was supplied, the reconstructible form must carry
      the PRODUCER itself (so the deferral is preserved on rebuild), never the
      already-evaluated concrete store;
    * if no producer was supplied, the reconstructible form carries the
      concrete store directly.

  In either case the store attribute is OMITTED from the reconstructible form
  exactly when the value that WOULD be reported is the canonical default store
  (the one a freshly built field assumes when nothing is supplied) -- because
  that value is then redundant and is re-supplied automatically on rebuild.

  The decisive point: the include/omit test and the reported value must be
  taken from the SAME quantity -- the value that will actually be reported
  (the producer when one exists, else the concrete store). The specification
  is TOTAL: it pins the result on every field configuration and assumes
  nothing about which identities may coincide. In the real repository a held
  producer is never the canonical default store (a producer is a callable,
  the default store a concrete store instance), so on all reachable states a
  field built from a producer is always reported -- even when that producer
  happens to evaluate to the default store. The general include-iff-non-default
  rule specialises to exactly that behaviour there.

The reduction is read-only: it observes the field's attributes and does not
mutate them. Object identities (the canonical default store, the concrete
store, the producer) are modelled as integer identity tags; equality of tags
means object identity. The presence/absence of a producer is a boolean. No
callee is axiomatized: the behaviour is pure identity/decision logic, modelled
deeply.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import Optional, Tuple
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# No consumed axioms: the reduction is pure identity/decision logic (an
# attribute-presence lookup plus two object-identity comparisons), modelled
# deeply. There is no opaque library callee under specification here.
# axioms-end


# pure-start
@Pure
def default_store_id() -> int:
    """Identity tag of the canonical default store (the sentinel a field
    assumes when nothing is supplied). A single distinguished constant."""
    return 0


@Pure
def reported_value(has_producer: bool, producer_id: int, store_id: int) -> int:
    """The store identity that the reconstructible form reports: the deferred
    producer when one was supplied, otherwise the concrete store."""
    if has_producer:
        return producer_id
    return store_id
# pure-end


class FileBackedField:
    def __init__(self) -> None:
        # Constructor of the minimal field stand-in (no marked spec region: the
        # modeled changed behaviour is `deconstruct_storage` below). A freshly
        # built field with nothing supplied carries the canonical default store
        # and holds no producer.
        Ensures(Acc(self.store_id) and Acc(self.has_producer) and Acc(self.producer_id))  # type: ignore
        Ensures(self.store_id == default_store_id())  # type: ignore
        Ensures(self.has_producer == False)  # type: ignore
        Ensures(self.producer_id == default_store_id())  # type: ignore
        self.store_id = default_store_id()  # type: int
        self.has_producer = False  # type: bool
        self.producer_id = default_store_id()  # type: int


def deconstruct_storage(self: FileBackedField) -> Tuple[bool, int]:
    # pre-conditions-start
    # The field is read-only throughout the reduction: its attributes are
    # required (and ensured) only at fractional permission. The specification
    # is TOTAL: no field configuration is excluded, so a verifying
    # implementation is pinned on every input (no excluded corner admits
    # divergent behaviour).
    Requires(Acc(self.store_id, 1 / 2) and Acc(self.has_producer, 1 / 2) and Acc(self.producer_id, 1 / 2))
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    # The field is left exactly as it was (read-only).
    Ensures(Acc(self.store_id, 1 / 2) and Acc(self.has_producer, 1 / 2) and Acc(self.producer_id, 1 / 2))
    Ensures(self.store_id == Old(self.store_id))
    Ensures(self.has_producer == Old(self.has_producer))
    Ensures(self.producer_id == Old(self.producer_id))

    # The result is (included, value):
    #   `value` is the quantity that would be reported -- the producer when one
    #   was supplied, otherwise the concrete store -- and is meaningful whenever
    #   the store attribute is included.
    Ensures(Result()[1] == reported_value(self.has_producer, self.producer_id, self.store_id))
    #   the store attribute is included exactly when that SAME reported value is
    #   not the canonical default store. (Both the test and the value derive
    #   from the one reported quantity.)
    Ensures(Result()[0] == (reported_value(self.has_producer, self.producer_id, self.store_id) != default_store_id()))
    # Discriminating consequence (implied by the two clauses above; restated
    # for emphasis): whenever a producer is held, the producer itself is the
    # reported value, and -- since on every reachable real-world state a held
    # producer is a distinct object from the canonical default store -- the
    # field is then reported even when the producer evaluates to the default
    # store. Stated conditionally so the spec stays total and consistent on
    # ALL inputs, including the real-world-unreachable coincidence
    # producer == default store (where the general include-iff-non-default
    # rule above still pins the result exactly).
    Ensures(Implies(self.has_producer and self.producer_id != default_store_id(), Result()[0]))
    Ensures(Implies(self.has_producer, Result()[1] == self.producer_id))
    # post-conditions-end
    # impl-start
    # Compute the value to report first (producer if present, else store),
    # then decide inclusion from that same value.
    if self.has_producer:
        value = self.producer_id
    else:
        value = self.store_id
    included = value != default_store_id()
    return (included, value)
    # impl-end
