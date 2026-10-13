"""Twin-artifact model for django__django-16901.

Behaviour under specification (stated as desired behaviour, not as an edit):

  An exclusive-disjunction connective is combined over a list of operand
  predicates on a backend that cannot evaluate the connective natively, so it
  is re-expressed using only conjunction, disjunction and integer arithmetic
  over the per-operand truth values (each operand contributes 1 when true and
  0 when false).

  The combined predicate must hold for an assignment exactly when an ODD number
  of the operands are true — the genuine semantics of a repeated exclusive
  disjunction. The arithmetic re-expression therefore tests the PARITY of the
  number of true operands, not whether that number equals one. For one or two
  operands the count of true operands can be at most two, so "the count is one"
  and "the count is odd" coincide; for three or more operands they diverge and
  only the parity test is correct (e.g. three true operands must satisfy the
  predicate).

  Concretely the re-expression is the conjunction of
    (i) the disjunction of the operands ("at least one true"), and
    (ii) a comparison of a derived count against one, where the derived count
         is the number of true operands when there are at most two operands,
         and the parity (remainder modulo two) of that number when there are
         three or more operands.

Operand truth assignments are modelled as a `List[int]`; an operand counts as
true exactly when its entry is 1 (each entry contributes 1 when true and 0
otherwise). The SQL builder objects (the per-operand 1/0 choice, the running
sum, the modulo, the equality and the disjunction) are modelled by the integer
arithmetic they denote at evaluation time. No callee is axiomatized — the
changed operation is the integer arithmetic itself and is modelled deeply.

Evaluating the re-expression is a bounded, straight-line computation over a
finite operand list: the operation MUST terminate and actually deliver its
truth value (a total-correctness obligation, carried as MustTerminate in the
precondition). An implementation that diverges instead of answering would
satisfy the value postconditions only vacuously and would never produce the
match decision the caller observes.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# (none — the changed operation is integer arithmetic, modelled deeply below)
# axioms-end


# pure-start
@Pure
def count_true(s: PSeq[int]) -> int:
    """Number of true operands: the sum of the per-operand 1/0 contributions
    (an operand contributes 1 exactly when its entry is 1). Front-recursive so
    a single unfold is available per loop step."""
    Ensures(Result() >= 0)
    Ensures(Result() <= len(s))
    if len(s) == 0:
        return 0
    return (1 if s[0] == 1 else 0) + count_true(s.drop(1))


@Pure
def any_true(s: PSeq[int]) -> bool:
    """Disjunction of the operands: at least one operand is true."""
    Ensures(Result() == (count_true(s) >= 1))
    if len(s) == 0:
        return False
    return s[0] == 1 or any_true(s.drop(1))


@Pure
def derived_count(s: PSeq[int]) -> int:
    """The count compared against one by the re-expression: the raw number of
    true operands when there are at most two operands, its parity (remainder
    modulo two) when there are three or more."""
    if len(s) > 2:
        return count_true(s) % 2
    return count_true(s)


@Pure
def xor_holds(s: PSeq[int]) -> bool:
    """The truth value of the arithmetic re-expression on this assignment:
    the disjunction of the operands AND the derived count equals one."""
    return any_true(s) and derived_count(s) == 1
# pure-end


def xor_fallback_matches(operands: List[int]) -> bool:
    # pre-conditions-start
    Requires(Acc(list_pred(operands), 1 / 2))
    # Evaluating the constructed predicate on one row's finite operand
    # assignment is a bounded computation and MUST terminate — the fallback
    # must actually answer whether the row matches. Without this obligation a
    # diverging implementation satisfies every Ensures vacuously (Nagini is a
    # partial-correctness verifier by default).
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(operands), 1 / 2))
    # The result is the re-expression's truth value: at least one operand true
    # AND the derived count (parity when >2 operands) equals one.
    Ensures(Result() == xor_holds(ToSeq(operands)))
    # Behavioural pinning derived from the issue: the predicate holds exactly
    # when an ODD number of operands are true.
    Ensures(Result() == (count_true(ToSeq(operands)) % 2 == 1))
    # post-conditions-end
    # impl-start
    total = 0
    any_t = False
    i = len(operands)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(operands), 1 / 2))
        Invariant(0 <= i and i <= len(operands))
        Invariant(total == count_true(ToSeq(operands).drop(i)))
        Invariant(any_t == any_true(ToSeq(operands).drop(i)))
        # The loop consumes the termination obligation: i is the strictly
        # decreasing, bounded-below measure.
        Invariant(MustTerminate(i))
        # invariants-end
        c = operands[i - 1]
        Assert(ToSeq(operands).drop(i - 1)[0] == c)
        Assert(ToSeq(operands).drop(i - 1).drop(1) == ToSeq(operands).drop(i))
        # Case(When(c, then=1), default=0): 1 if the operand is true else 0.
        contribution = 1 if c == 1 else 0
        total = contribution + total
        any_t = (c == 1) or any_t
        i = i - 1
    Assert(ToSeq(operands).drop(0) == ToSeq(operands))
    # rhs_sum derivation: the raw running sum is compared directly, with no
    # parity reduction regardless of the operand count.
    rhs = total
    # Exact(1, rhs_sum): the derived count equals one; conjoined with the OR.
    return any_t and rhs == 1
    # impl-end
