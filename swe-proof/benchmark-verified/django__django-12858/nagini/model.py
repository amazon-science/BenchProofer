"""Twin-artifact model for django__django-12858.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When validating the ordering specification of a model, each multi-part path
  whose trailing segment cannot be resolved as a concrete model field is
  examined to decide whether it should be reported as an invalid ordering
  reference. A path is accepted (NOT reported) exactly when a field was reached
  just before the unresolved trailing segment AND that segment denotes at least
  one of the two recognised kinds of registered query operator: a value-
  producing operator (one that yields a new value to continue resolving) OR a
  comparison operator (one usable as a terminal predicate). A trailing segment
  that IS a recognised comparison operator is therefore a legitimate ordering
  target and must NOT be reported, exactly as a value-producing operator already
  is not. Otherwise — no field was reached, or the segment is neither operator
  kind — the path is reported as an invalid ordering reference.

  Concretely, for each path the decision is a function of three observations
  about its trailing segment: whether a field was reached before it
  (`reached_field`), whether the segment is a registered value-producing
  operator (`is_value_op`), and whether it is a registered comparison operator
  (`is_compare_op`). The path is flagged invalid iff no field was reached OR the
  segment is neither operator kind. The result lists, in input order, the
  flag (1 = reported invalid, 0 = accepted) of every examined path.

The three per-path observations are carried as parallel `List[int]` of 0/1
booleans (Nagini bans richer object graphs cheaply here; the tested behaviour
observes only these three predicates per path). The two operator-recognition
predicates correspond to two unchanged lookup-registry queries that the
validator calls but does not change; they are modelled as the boolean inputs
and their real semantics are recorded in mapping.md / checked by axiom_check.py
(A-reference) rather than consumed as axioms — the decision itself is modelled
deeply.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# No consumed axioms. The two registry queries that classify a path segment
# (value-producing vs. comparison operator) are unchanged callees; here their
# results enter the decision as the boolean inputs is_value_op / is_compare_op.
# Their real semantics (each returns a non-None object iff the named operator of
# that kind is registered) are validated out-of-band by axiom_check.py (G-AX)
# as A-references, not consumed as @ContractOnly Ensures. The reporting decision
# itself is modelled deeply below.
# axioms-end


# pure-start
@Pure
def flag_path(reached_field: int, is_value_op: int, is_compare_op: int) -> int:
    """The per-path decision: report the path as an invalid ordering reference
    iff EITHER no field was reached before its unresolved trailing segment, OR
    that segment is neither a value-producing operator nor a comparison
    operator. A path is accepted only when a field was reached AND the trailing
    segment is at least one of the two recognised operator kinds. Returns 1
    (report invalid) or 0 (accept)."""
    if reached_field == 0 or (is_value_op == 0 and is_compare_op == 0):
        return 1
    return 0
# pure-end


def select_reported_paths(reached_field: List[int],
                          is_value_op: List[int],
                          is_compare_op: List[int]) -> List[int]:
    # pre-conditions-start
    # The three per-path observation lists are read-only (fractional permission,
    # Required and Ensured) and index-aligned.
    Requires(Acc(list_pred(reached_field), 1 / 2))
    Requires(Acc(list_pred(is_value_op), 1 / 2))
    Requires(Acc(list_pred(is_compare_op), 1 / 2))
    Requires(len(reached_field) == len(is_value_op))
    Requires(len(reached_field) == len(is_compare_op))
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(reached_field), 1 / 2))
    Ensures(Acc(list_pred(is_value_op), 1 / 2))
    Ensures(Acc(list_pred(is_compare_op), 1 / 2))
    # The three observation lists remain index-aligned (read-only).
    Ensures(len(reached_field) == len(is_value_op))
    Ensures(len(reached_field) == len(is_compare_op))
    # The result is a fresh, fully-owned list with one flag per examined path.
    Ensures(Acc(list_pred(Result())))
    Ensures(len(Result()) == len(reached_field))
    # Each flag is exactly the per-path decision: a path is reported invalid iff
    # no field was reached OR the trailing segment is neither operator kind. In
    # particular a path whose segment IS a comparison operator (is_compare_op),
    # with a field reached, is accepted (flag 0) — exactly as a value-producing
    # operator already is.
    Ensures(Forall(int, lambda k: (Implies(
            0 <= k and k < len(reached_field),
            Result()[k] == flag_path(reached_field[k], is_value_op[k],
                                     is_compare_op[k])))))
    # post-conditions-end
    # impl-start
    errors = []  # type: List[int]
    i = 0
    while i < len(reached_field):
        # invariants-start
        Invariant(Acc(list_pred(reached_field), 1 / 2))
        Invariant(Acc(list_pred(is_value_op), 1 / 2))
        Invariant(Acc(list_pred(is_compare_op), 1 / 2))
        Invariant(len(reached_field) == len(is_value_op))
        Invariant(len(reached_field) == len(is_compare_op))
        Invariant(Acc(list_pred(errors)))
        Invariant(0 <= i and i <= len(reached_field))
        Invariant(len(errors) == i)
        Invariant(Forall(int, lambda k: (Implies(
                0 <= k and k < i,
                errors[k] == flag_path(reached_field[k], is_value_op[k],
                                       is_compare_op[k])))))
        Invariant(MustTerminate(len(reached_field) - i + 1))
        # invariants-end
        if reached_field[i] == 0 or (is_value_op[i] == 0 and is_compare_op[i] == 0):
            errors.append(1)
        else:
            errors.append(0)
        Assert(errors[i] == flag_path(reached_field[i], is_value_op[i],
                                      is_compare_op[i]))
        i = i + 1
    return errors
    # impl-end
