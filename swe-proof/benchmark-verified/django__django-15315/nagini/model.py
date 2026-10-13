"""Twin-artifact model for django__django-15315.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A descriptor object owns a constant integer identity assigned once at
  creation (its creation order). It MAY later be attached to an owner class, at
  which point it gains owner-derived attributes (an owning-class label and
  name).

  The required behaviour: the value used to locate the object in a hash-based
  container is a function of the creation-order identity ALONE. It must NOT
  depend on whether the object has been attached to an owner, nor on any
  owner-derived attribute. Consequently the located-value is stable across the
  later attachment of the object to an owner: an object placed in a hash
  container before attachment remains findable in it afterwards.

The descriptor is modelled as a minimal class carrying only the touched
fields: the creation-order identity (``int``), an attachment flag
(``has_owner``), and the two owner-derived attributes that become available
once attached (modelled as ``int`` identities). Crucially, the owner-derived
attributes EXIST only once the object is attached: in the real program an
unattached object simply lacks the owner attribute, and reading it raises an
error. The spec mirrors this by granting read permission on the owner-derived
attributes only under ``has_owner`` — an implementation may observe them only
after establishing attachment. The unchanged standard hashing primitive over a
single integer is axiomatized.

The operation is a bounded, straight-line delegation to that primitive: it
MUST terminate (a total-correctness obligation, carried as MustTerminate in
the precondition). An implementation that diverges — e.g. loops or recurses
forever instead of returning the located-value — would satisfy the value
postconditions only vacuously and would hang every hash-container lookup
(and the F2P test) forever.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import Optional
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


class Descriptor:
    def __init__(self, order: int, has_owner: bool, owner_label: int,
                 owner_name: int) -> None:
        # The constructor is a bounded sequence of field stores; it carries a
        # termination obligation so callers under their own termination
        # obligation may construct descriptors.
        Requires(MustTerminate(1))
        Ensures(Acc(self.order) and self.order == order)            # type: ignore
        Ensures(Acc(self.has_owner) and self.has_owner == has_owner)  # type: ignore
        Ensures(Acc(self.owner_label) and self.owner_label == owner_label)  # type: ignore
        Ensures(Acc(self.owner_name) and self.owner_name == owner_name)  # type: ignore
        self.order = order
        self.has_owner = has_owner
        self.owner_label = owner_label
        self.owner_name = owner_name


# axioms-start
@Pure
@ContractOnly
def hash_int(value: int) -> int:
    """The unchanged standard hashing primitive applied to a single integer.
    It is a deterministic pure function of that integer alone (Nagini treats a
    @Pure function as deterministic, so the spec need not restate it).
    Provenance + executable soundness check: mapping.md / axiom_check.py.
    """
# axioms-end


# pure-start
# (no auxiliary pure spec functions are required for this behaviour)
# pure-end


def located_value(self: Descriptor) -> int:
    # pre-conditions-start
    # Read-only: the operation never mutates the descriptor, so only a
    # fractional permission is required (and returned) on every field.
    # The owner-derived attributes exist ONLY once the object is attached
    # (in the real program an unattached object lacks them and reading them
    # raises), so read permission on them is granted only under the
    # attachment flag: an implementation may touch them only after
    # establishing attachment, never unconditionally.
    Requires(Acc(self.order, 1 / 2))
    Requires(Acc(self.has_owner, 1 / 2))
    Requires(Implies(self.has_owner, Acc(self.owner_label, 1 / 2)))
    Requires(Implies(self.has_owner, Acc(self.owner_name, 1 / 2)))
    # Total correctness: the operation is a bounded delegation to the
    # hashing primitive and must TERMINATE. Without this obligation a
    # diverging implementation (infinite loop or unbounded self-recursion)
    # satisfies every value postcondition vacuously yet would hang every
    # hash-container lookup (and the F2P test) forever.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(self.order, 1 / 2))
    Ensures(Acc(self.has_owner, 1 / 2))
    Ensures(Implies(self.has_owner, Acc(self.owner_label, 1 / 2)))
    Ensures(Implies(self.has_owner, Acc(self.owner_name, 1 / 2)))
    # The located-value is a function of the creation-order identity ALONE:
    # it is exactly the standard hash of that identity, independent of the
    # attachment flag and of either owner-derived attribute. This is precisely
    # the stability-under-attachment guarantee the behaviour demands.
    Ensures(Result() == hash_int(self.order))
    # post-conditions-end
    # impl-start
    return hash_int(self.order)
    # impl-end
