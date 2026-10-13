"""Twin-artifact model for django__django-15629.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A relational field that references another model's column borrows that
  column's storage characteristics. The database parameters a relational field
  reports for its own column must therefore include the SAME collation as the
  column it points at — alongside the type and the check it already reported.
  When the referenced column declares no collation, the relational field
  reports no collation either (the two agree on "absent").

  Two consequences are pinned, because two consumers read these parameters:

    (1) Column emission. The storage definition emitted for a column carries an
        explicit collation clause exactly when that column's parameters declare
        a collation. Hence a relational field's column gets a collation clause
        precisely when, and matching, the column it references — so a freshly
        created reference agrees with its target out of the box.

    (2) Re-derivation on change. When an existing referenced column is altered,
        every column referencing it must be re-derived (dropped and rebuilt to
        match) when the referenced column's type or its collation differs
        between the old and new shape.

Modelling choices (Nagini fragment):
  * A column's database parameters are a ``Dict[int, int]`` from a
    parameter-name token (module-level constants: type / check / collation) to
    its abstract value. A key being ABSENT means "this parameter is not reported
    at all"; a key present with the sentinel ``none_value()`` means "declared,
    but empty (no collation)". Absent vs. present-but-equal is an observable
    distinction here, so the carrier separates ``k in d`` membership from
    ``d[k]``.
  * A type / collation identity is an ``int``: ``none_value()`` is "no
    collation"/"no type"; every other int is a distinct identity. Only equality
    and membership are observed (mapping.md §2), so integer identity is faithful
    and ``!=`` is plain integer comparison.

The referenced column's own parameters are read, not mutated; held at fractional
permission. The behaviour is modelled deeply (the dict construction and the
change-decision are spelled out in the impl regions); there is no axiomatised
callee. Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import Dict
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# No axioms: both modeled behaviours are spelled out deeply in the impl
# regions. There is no unchanged opaque callee the proof relies on.
# axioms-end


# pure-start
@Pure
def key_type() -> int:
    # Parameter-name token for the storage type.
    return 1


@Pure
def key_check() -> int:
    # Parameter-name token for the column check.
    return 2


@Pure
def key_collation() -> int:
    # Parameter-name token for the column collation.
    return 3


@Pure
def none_value() -> int:
    # Sentinel value meaning "declared, but empty" (no type / no collation).
    return 0


@Pure
def differs(before: int, after: int) -> bool:
    # Whether a storage characteristic changed between the old and new shape.
    return before != after


@Pure
def emits_collation_clause(params: Dict[int, int]) -> bool:
    """A column's storage definition carries an explicit collation clause
    exactly when its parameters declare a (non-empty) collation: the clause is
    emitted iff the collation key is present AND its value is not the empty
    sentinel."""
    Requires(Acc(dict_pred(params), 1 / 4))
    return key_collation() in params and params[key_collation()] != none_value()
# pure-end


def reported_reference_parameters(target_params: Dict[int, int],
                                  own_type: int,
                                  own_check: int) -> Dict[int, int]:
    # pre-conditions-start
    # The referenced column's parameters are read only (fractional permission).
    Requires(Acc(dict_pred(target_params), 1 / 2))
    # The referenced column reports a collation entry (possibly the empty
    # sentinel).
    Requires(key_collation() in target_params)
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(dict_pred(target_params), 1 / 2))
    Ensures(dict_pred(Result()))
    # The reported parameters expose exactly the three expected entries, and
    # each carries the expected value (membership precedes each lookup).
    Ensures(key_type() in Result())
    Ensures(Result()[key_type()] == own_type)
    Ensures(key_check() in Result())
    Ensures(Result()[key_check()] == own_check)
    Ensures(key_collation() in Result())
    # The referenced column still reports its collation entry (read-only).
    Ensures(key_collation() in target_params)
    # (1) The reported collation is exactly the referenced column's collation
    #     — the discriminating clause: same value, and present (not absent).
    Ensures(Result()[key_collation()] == target_params[key_collation()])
    # No spurious entries are reported.
    Ensures(Forall(int, lambda k: (Implies(k in Result(),
            k == key_type() or k == key_check() or k == key_collation()))))
    # (1') Consequently the field's column emits a collation clause exactly when
    #      the referenced column does, with the matching value. This is the
    #      property the create-time column emission depends on.
    Ensures(emits_collation_clause(Result())
            == (key_collation() in target_params
                and target_params[key_collation()] != none_value()))
    # post-conditions-end
    # impl-start
    result = {}  # type: Dict[int, int]
    result[key_type()] = own_type
    result[key_check()] = own_check
    result[key_collation()] = target_params[key_collation()]
    return result
    # impl-end


def references_need_rebuild(old_type: int, new_type: int,
                            old_collation: int, new_collation: int) -> bool:
    # pre-conditions-start
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    # (2) Columns referencing an altered column must be re-derived whenever a
    #     storage characteristic differs between the old and new shape — its
    #     type OR its collation. The clauses below fully characterise the
    #     decision by cases (complete, so the spec is tight).
    # A type change triggers a rebuild.
    Ensures(Implies(differs(old_type, new_type), Result()))
    # A collation change ALSO triggers a rebuild, including the case where the
    # type is unchanged.
    Ensures(Implies(differs(old_collation, new_collation), Result()))
    # When NEITHER characteristic differs, no rebuild is triggered.
    Ensures(Implies(not differs(old_type, new_type)
                    and not differs(old_collation, new_collation),
                    not Result()))
    # post-conditions-end
    # impl-start
    return differs(old_type, new_type)
    # impl-end
