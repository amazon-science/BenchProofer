"""Twin-artifact model for django__django-14915.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A lightweight wrapper that carries a stored lookup value together with the
  domain object it was derived from must be usable as a dictionary key / set
  member. Its membership identity is the membership identity of the *stored
  value* it wraps, and ONLY that value: the object it was derived from does
  not participate. Consequently two wrappers carrying the same stored value
  share one membership identity even when they were derived from different
  domain objects (or from none at all), and a wrapper carrying value ``v`` has
  the same membership identity as the bare value ``v`` would. Distinct stored
  values keep the distinct membership identities the values themselves have.

  Concretely: the wrapper's membership identity equals the membership identity
  of its wrapped value (``Result() == value_identity(self.value)``), computed
  from ``value`` alone and never from the derived-object field.

The wrapper is modelled as a minimal class carrying only the two touched
facets: the stored value (an integer key) and an integer standing for the
identity of the derived domain object. The membership identity of a bare
stored value is the one unchanged stdlib callee the operation defers to; it is
axiomatized as a single pure (hence deterministic) function of its argument.

The operation is a bounded, straight-line delegation to that primitive: it
MUST terminate (a total-correctness obligation, carried as MustTerminate in
the precondition). An implementation that diverges — e.g. hangs instead of
returning the wrapped value's identity — would satisfy the value
postconditions only vacuously and would hang every membership lookup (and
the F2P test) forever.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
@Pure
@ContractOnly
def value_identity(v: int) -> int:
    """The unchanged stdlib membership-identity primitive applied to a bare
    stored value. As a `@Pure` function it is a single mathematical function of
    its one argument: the same value always yields the same identity, and
    the result is derived from `v` and nothing else. This is the weakest
    sufficient contract; it deliberately does NOT claim global injectivity,
    which the primitive does not provide (distinct values may, in principle,
    collide). Provenance + executable soundness check: mapping.md /
    axiom_check.py.
    """
# axioms-end


# pure-start
# (no auxiliary pure spec functions are required for this behaviour)
# pure-end


class ChoiceValue:
    def __init__(self, value: int, instance: int) -> None:
        Ensures(Acc(self.value) and self.value == value)        # type: ignore
        Ensures(Acc(self.instance) and self.instance == instance)  # type: ignore
        self.value = value
        self.instance = instance

    def membership_identity(self) -> int:
        # pre-conditions-start
        Requires(Acc(self.value, 1 / 2) and Acc(self.instance, 1 / 2))
        # Total correctness: the real operation is a bounded, straight-line
        # delegation to the unchanged stdlib primitive — it must TERMINATE.
        # Without this obligation a diverging impl (e.g. an infinite loop)
        # satisfies every value postcondition vacuously yet would hang every
        # membership lookup (and the F2P test) forever.
        Requires(MustTerminate(1))
        # pre-conditions-end
        # post-conditions-start
        Ensures(Acc(self.value, 1 / 2) and Acc(self.instance, 1 / 2))
        # The wrapper is read-only: its facets are unchanged.
        Ensures(self.value == Old(self.value))
        Ensures(self.instance == Old(self.instance))
        # The discriminating guarantee: the membership identity is exactly the
        # membership identity of the WRAPPED VALUE, computed from `value` alone.
        # It therefore does not depend on the derived-object facet `instance`,
        # so two wrappers with equal `value` agree, and a wrapper agrees with
        # the bare value it wraps.
        Ensures(Result() == value_identity(self.value))
        # post-conditions-end
        # impl-start
        # Pre-patch (buggy) skeleton: the wrapper has no membership identity of
        # its own, so it falls back to the identity of the derived domain object
        # it was built from. This depends on `instance`, not on the wrapped
        # `value` — two wrappers carrying the same value but built from
        # different objects then disagree, and the identity is NOT the one the
        # wrapped value carries.
        return value_identity(self.instance)
        # impl-end
