"""Twin-artifact model for django__django-13343.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A file-attachment field may be configured with its backing store given
  either directly as a concrete store, or *indirectly* as a zero-argument
  producer that is evaluated once at configuration time to obtain the concrete
  store actually used at runtime. The point of the indirection is that the
  producer — not whatever concrete store it happens to yield — is the stable,
  reconfigurable description of the field.

  Two cooperating operations are specified.

  (1) Configuration. When the field is configured with a producer, the field
      both (a) records a reference to that original producer and (b) adopts the
      concrete store the producer yields as its live store. Evaluating a
      producer yields a concrete store that is a DISTINCT object from the
      producer itself. When configured directly with a concrete store, the
      field adopts it as the live store and records no producer.

  (2) Description (the inverse-of-configuration query that reproduces how the
      field was configured). The store-description it emits must be the value
      ORIGINALLY supplied at configuration: the original producer when one was
      supplied, otherwise the live store. In particular, when a producer was
      supplied the description must NOT be the concrete store the producer was
      evaluated to — that would defeat the indirection, freezing one runtime
      choice into the field's persisted description. When the live store is the
      ambient default store, no store description is emitted at all.

Store objects and producers are modelled by their object identity, carried as
distinct integer ids; the ambient default store has a reserved constant identity.
A producer's evaluation yields a store id distinct from the producer's id
(faithful to evaluating a real producer, which returns a separate store
object). The two operations communicate only through the field's recorded
state. No library callee is involved; the behaviour is pure state/identity
logic, modelled deeply.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import Optional
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# No consumed axioms: the behaviour is pure object-identity / state logic,
# modelled deeply. The identity-preservation of evaluating a real producer and
# of the identity comparison against the ambient default store are validated
# against their real Python semantics out-of-band by axiom_check.py (G-AX) as
# A-references, not consumed here.
# axioms-end


# pure-start
@Pure
def default_store_id() -> int:
    """The reserved identity of the ambient default store."""
    return 0
# pure-end


class AttachmentField:
    def __init__(self) -> None:
        # Level 1: the constructor is a leaf obligated method (it calls nothing
        # obligated), so it sits strictly below every method that builds a
        # field. Obligated callers must outrank it or the construction leaks.
        Requires(MustTerminate(1))
        Ensures(Acc(self.store))            # type: ignore
        Ensures(Acc(self.has_producer))     # type: ignore
        Ensures(Acc(self.producer_id))      # type: ignore
        self.store = 0            # type: int   # live concrete store identity
        self.has_producer = False  # type: bool  # whether a producer was recorded
        self.producer_id = 0      # type: int   # recorded original producer id


def configure(field: AttachmentField, given: int, given_is_producer: bool,
              evaluated: int) -> None:
    # pre-conditions-start
    Requires(Acc(field.store))
    Requires(Acc(field.has_producer))
    Requires(Acc(field.producer_id))
    # A concrete store is supplied (the ambient default is reserved id 0; a
    # supplied store/producer carries a non-default identity).
    Requires(given != default_store_id())
    # Evaluating a producer yields a concrete store that is a DISTINCT object
    # from the producer itself (the discriminating fact the description query
    # must respect), and which is itself a real store, not the default.
    Requires(Implies(given_is_producer,
                     evaluated != given and evaluated != default_store_id()))
    Requires(MustTerminate(6))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(field.store))
    Ensures(Acc(field.has_producer))
    Ensures(Acc(field.producer_id))
    # (1a) a producer is recorded exactly when one was supplied,
    Ensures(field.has_producer == given_is_producer)
    # (1b) and the recorded producer is the original producer supplied.
    Ensures(Implies(given_is_producer, field.producer_id == given))
    # (1b') when configured directly with a concrete store, no producer
    #       reference is written: the recorded producer id is left exactly as
    #       it was (configuration without a producer records nothing).
    Ensures(Implies(not given_is_producer,
                    field.producer_id == Old(field.producer_id)))
    # (1c) the live store is the producer's evaluation when a producer was
    #      supplied, else the supplied store itself.
    Ensures(field.store == (evaluated if given_is_producer else given))
    # post-conditions-end
    # impl-start
    field.store = given
    if given_is_producer:
        # Record a reference to the original producer, then adopt the concrete
        # store it yields as the live store.
        field.has_producer = True
        field.producer_id = given
        field.store = evaluated
    else:
        field.has_producer = False
    # impl-end


def describe_store(field: AttachmentField) -> Optional[int]:
    # pre-conditions-start
    # The field is read-only here: described, not mutated.
    Requires(Acc(field.store, 1 / 2))
    Requires(Acc(field.has_producer, 1 / 2))
    Requires(Acc(field.producer_id, 1 / 2))
    Requires(MustTerminate(10))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(field.store, 1 / 2))
    Ensures(Acc(field.has_producer, 1 / 2))
    Ensures(Acc(field.producer_id, 1 / 2))
    # No store description when the live store is the ambient default store.
    Ensures((field.store == default_store_id()) == (Result() is None))
    # When a description IS emitted, it is the originally-supplied value: the
    # recorded original producer if one was recorded, else the live store
    # itself. Crucially, with a recorded producer the description is the
    # producer, never the concrete store it was evaluated to.
    Ensures(Implies(field.store != default_store_id() and field.has_producer,
                    Result() is not None and Result() == field.producer_id))
    Ensures(Implies(field.store != default_store_id() and not field.has_producer,
                    Result() is not None and Result() == field.store))
    # post-conditions-end
    # impl-start
    # Pre-patch description: when a store description is emitted it is the live
    # concrete store, even when that store was obtained by evaluating a
    # producer (the bug — the producer indirection is lost, freezing the one
    # evaluated store into the description).
    if field.store == default_store_id():
        return None
    return field.store
    # impl-end
