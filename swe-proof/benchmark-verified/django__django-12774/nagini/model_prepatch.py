"""Twin-artifact model for django__django-12774.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A bulk-lookup helper accepts a lookup field and must accept exactly those
  fields whose value identifies at most one row. It rejects a field (by
  signalling an error) unless AT LEAST ONE of the following holds:

    (1) the field is the primary-key field; or
    (2) the field is individually unique on its own; or
    (3) the field is the SOLE member of an UNCONDITIONAL uniqueness guarantee
        declared on the model (a uniqueness guarantee that applies to every row,
        not one restricted by a condition, and that ranges over that one field
        alone).

  A uniqueness guarantee that is conditional (applies only to a subset of rows)
  or that ranges over several fields together does NOT make any one of its
  fields acceptable on its own; such a field is still rejected unless it also
  satisfies (1) or (2).

Field names are modelled as integer identities (distinct names <-> distinct
integers; the primary-key field is the distinguished identity ``PK``). A
declared uniqueness guarantee is reduced to its two touched attributes carried
as an immutable value pair: ``g[0]`` is True iff it is unconditional, and
``g[1]`` is the (pure) sequence of field identities it ranges over. The decision
is a pure predicate over these; the helper signals rejection by returning
``True``.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List, Tuple
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


PK = 0  # the distinguished primary-key field identity


# axioms-start
# (no @ContractOnly callee axioms: the field's own uniqueness flag and the
#  declared-guarantee list are passed in as data; the unconditional-guarantee
#  filter and the single-field extraction are modelled deeply below.)
# axioms-end


# pure-start
@Pure
def permits_alone(g: Tuple[bool, PSeq[int]], field_name: int) -> bool:
    """Whether the declared guarantee ``g`` makes ``field_name`` acceptable on
    its own: it must be unconditional (``g[0]``) AND range over ``field_name``
    as its sole field (``g[1]`` has length 1 and that single field is
    ``field_name``). Conditional or multi-field guarantees never permit a field
    alone."""
    return g[0] and len(g[1]) == 1 and g[1][0] == field_name


@Pure
def any_permits(guarantees: List[Tuple[bool, PSeq[int]]], idx: int,
                field_name: int) -> bool:
    """Whether SOME declared guarantee from position ``idx`` onward makes
    ``field_name`` acceptable on its own. Front-recursive so a single unfold is
    available per loop step."""
    Requires(Acc(list_pred(guarantees), 1 / 4))
    Requires(0 <= idx and idx <= len(guarantees))
    if idx == len(guarantees):
        return False
    return permits_alone(guarantees[idx], field_name) or \
        any_permits(guarantees, idx + 1, field_name)
# pure-end


def should_reject(field_name: int, field_unique: bool,
                  guarantees: List[Tuple[bool, PSeq[int]]]) -> bool:
    # pre-conditions-start
    Requires(Acc(list_pred(guarantees), 1 / 2))
    # The decision must actually be delivered: this termination obligation
    # forbids implementations that would satisfy the value postcondition only
    # vacuously by never returning (the scan over the finite guarantee list is
    # bounded work).
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(guarantees), 1 / 2))
    # The field is rejected exactly when it is neither the primary key, nor
    # individually unique, nor made acceptable on its own by any declared
    # unconditional single-field guarantee.
    Ensures(Result() == (
        field_name != PK and
        not field_unique and
        not any_permits(guarantees, 0, field_name)))
    # A primary-key or individually-unique field is always accepted.
    Ensures(Implies(field_name == PK or field_unique, not Result()))
    # A field that is the sole member of some unconditional guarantee is
    # accepted even if it is neither the primary key nor individually unique.
    Ensures(Implies(any_permits(guarantees, 0, field_name), not Result()))
    # post-conditions-end
    # impl-start
    if field_name == PK:
        return False
    if field_unique:
        return False
    # Pre-patch skeleton: a field is rejected whenever it is neither the
    # primary key nor individually unique. The declared uniqueness guarantees
    # are not consulted at all.
    return True
    # impl-end
