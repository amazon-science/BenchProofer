"""Twin-artifact model for django__django-13028.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A guard screens the comparison operands of a stored query before the query is
  built, rejecting any operand that is BOTH (a) a query-expression operand —
  one that participates in query resolution — AND (b) marked by that expression
  as not permitted on this side of the comparison. The guard walks the operand
  together with every operand nested inside it (a query-expression operand may
  carry sub-operands) and applies the same screen to each.

  The behaviour pinned here is the CONJUNCTION the screen requires. An ordinary
  data operand that merely happens to expose a same-named "not-permitted" marker
  — without being a query-expression operand at all — must NOT be rejected: it
  is plain data, supplied as the right-hand side of a comparison, and is carried
  through untouched. Only an operand that is genuinely a query expression AND
  carries the not-permitted marker may be rejected. So the guard rejects the set
  of operands iff at least one operand in the walk is simultaneously a
  query-expression operand and not-permitted; otherwise it accepts (returns
  normally), even if some operand is not-permitted but is plain data.

The operand walk is modelled as the flattened traversal order of the operand
and its nested sub-operands: two index-aligned ``List[int]`` carry, per visited
operand, whether it is a query-expression operand (``is_expr[i]`` in {0,1}) and
whether it is permitted on this side (``permitted[i]`` in {0,1}; an operand that
exposes no marker defaults to permitted = 1). The discriminating observable is
purely WHICH outcome the guard produces (accept vs. reject), not the operands'
contents; Nagini bans ``str`` indexing, so operand identity is abstracted to
these two per-operand booleans. The rejection the guard raises is a user-defined
exception class (a builtin exception in an ``Exsures`` crashes the translator).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


class OperandNotAllowed(Exception):
    """The rejection the guard raises when a disallowed query-expression operand
    is encountered. User-defined stand-in for the not-supported error the
    desired behaviour requires (a builtin exception in an ``Exsures`` crashes the
    Nagini translator; mapping.md §2)."""
    pass


# axioms-start
# No consumed axioms: the guard's decision is a conjunction of two per-operand
# observations (is-a-query-expression and is-permitted) over the operand walk,
# modelled deeply over index-aligned integer carriers. There is no unchanged
# library callee the proof must stand in for.
# axioms-end


# pure-start
# (no auxiliary pure spec functions are required: the decision is stated inline
#  over the two per-operand carriers.)
# pure-end


def check_operands(is_expr: List[int], permitted: List[int]) -> None:
    # pre-conditions-start
    # The two index-aligned carriers describe the flattened operand walk; the
    # guard only READS them (fractional permission, directive 5).
    Requires(Acc(list_pred(is_expr), 1 / 2))
    Requires(Acc(list_pred(permitted), 1 / 2))
    # one entry per visited operand: the walk has a single shape.
    Requires(len(is_expr) == len(permitted))
    # each entry is a boolean flag in {0, 1}.
    Requires(Forall(int, lambda k: (Implies(0 <= k and k < len(is_expr),
                                            is_expr[k] == 0 or is_expr[k] == 1))))
    Requires(Forall(int, lambda k: (Implies(0 <= k and k < len(permitted),
                                            permitted[k] == 0 or permitted[k] == 1))))
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    # The inputs are read-only: returned untouched at the same fractional
    # permission. Holding only fractional permission throughout, the guard
    # cannot have mutated either carrier (directive 5); their lengths and
    # contents are therefore unchanged with no further clause needed.
    Ensures(Acc(list_pred(is_expr), 1 / 2))
    Ensures(Acc(list_pred(permitted), 1 / 2))
    Ensures(len(is_expr) == len(permitted))
    # Accept (return normally) ONLY when NO operand in the walk is BOTH a
    # query-expression operand AND not-permitted. An ordinary data operand that
    # is merely not-permitted (is_expr == 0) does not block acceptance.
    Ensures(Forall(int, lambda k: (Implies(0 <= k and k < len(is_expr),
                                            not (is_expr[k] == 1 and permitted[k] == 0)))))
    # Reject (raise) iff at least one operand in the walk is SIMULTANEOUSLY a
    # query-expression operand and not-permitted. This is the discriminating
    # conjunction: the query-expression test must hold too, so plain not-permitted
    # data passes through. The read-only carriers are re-established at the same
    # fractional permission on the rejecting path as well.
    Exsures(OperandNotAllowed,
            Acc(list_pred(is_expr), 1 / 2) and Acc(list_pred(permitted), 1 / 2)
            and len(is_expr) == len(permitted)
            and Exists(int, lambda k: (0 <= k and k < len(is_expr)
                                       and is_expr[k] == 1 and permitted[k] == 0)))
    # post-conditions-end
    # impl-start
    # Pre-patch skeleton: the disallow test screens ONLY the not-permitted
    # marker, without first requiring the operand to be a query expression. A
    # plain data operand that merely exposes a not-permitted marker is therefore
    # wrongly rejected.
    i = 0
    while i < len(is_expr):
        # invariants-start
        Invariant(Acc(list_pred(is_expr), 1 / 2))
        Invariant(Acc(list_pred(permitted), 1 / 2))
        Invariant(len(is_expr) == len(permitted))
        Invariant(0 <= i and i <= len(is_expr))
        # no not-permitted operand has been seen among the visited prefix.
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
                                                  permitted[k] == 1))))
        Invariant(MustTerminate(len(is_expr) - i + 1))
        # invariants-end
        if permitted[i] == 0:
            raise OperandNotAllowed()
        i = i + 1
    # impl-end
