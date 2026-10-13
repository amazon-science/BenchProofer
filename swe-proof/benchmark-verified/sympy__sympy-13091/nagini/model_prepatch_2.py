"""Twin-artifact model for sympy__sympy-13091.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A symbolic value participates in Python's rich-comparison protocol against an
  arbitrary right-hand object. Two obligations are pinned:

  (1) The equality query of a symbolic value against a right-hand object is
      THREE-VALUED, mirroring Python's data model. It answers:
        * "equal"      when the right-hand object is a comparable peer whose
                       content coincides with the symbolic value;
        * "not equal"  when the right-hand object is a comparable peer whose
                       content differs;
        * "undecided"  (the protocol's delegation sentinel) when the right-hand
                       object is NOT a comparable peer at all -- so that the
                       operator consults the right-hand object's own reflected
                       method instead of unilaterally declaring inequality.
      Declaring a flat "not equal" against an incomparable object (instead of
      "undecided") is what breaks symmetry: a foreign object that considers
      itself equal to the symbolic value can then never be honoured.

  (2) The inequality query is the boolean complement of the FULLY-RESOLVED
      equality OPERATOR (the operator that, on an "undecided" answer, delegates
      to the right-hand object's reflected method and only then falls back to
      object identity), NOT the complement of the symbolic value's own raw
      three-valued answer. The two differ exactly when the symbolic value is
      undecided: the resolved operator yields a genuine boolean from the other
      side, whereas complementing the raw three-valued "undecided" sentinel
      collapses (the sentinel is truthy) to a constant "equal-ish" verdict that
      disagrees with the fully-resolved operator whenever it reports unequal.

The three-valued equality answer is modelled as a small integer code
(0 = not-equal, 1 = equal, 2 = undecided/delegation-sentinel). The fully
resolved `==` operator is modelled deeply (`op_eq`, the pure region) and
validated == real Python `==` dispatch out-of-band by axiom_check.py (G-AX),
not consumed as an axiom.

Both contracted operations are bounded, straight-line computations: they MUST
terminate and return their reply (a total-correctness obligation, carried as
MustTerminate in the preconditions). An implementation that diverges before
returning would satisfy the value postconditions only vacuously and would
never deliver a reply to the rich-comparison protocol at all.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# (No @ContractOnly axiom is consumed. The fully-resolved `==` operator is
#  modelled deeply as `op_eq` in the pure region below and is validated equal
#  to real Python `==` dispatch by axiom_check.py / G-AX -- an A-reference,
#  not a consumed axiom.)
# axioms-end


# pure-start
@Pure
def EQ_FALSE() -> int:
    # the comparison answers a definite "not equal"
    return 0


@Pure
def EQ_TRUE() -> int:
    # the comparison answers a definite "equal"
    return 1


@Pure
def EQ_NI() -> int:
    # the delegation sentinel: "undecided, ask the other side"
    return 2


@Pure
def eq_code(sympifiable: bool, content_equal: bool) -> int:
    """The symbolic value's three-valued equality reply (pure form, used in
    contracts). Incomparable peer -> the delegation sentinel; otherwise a
    definite verdict driven by content."""
    Ensures(Result() == EQ_FALSE() or Result() == EQ_TRUE() or Result() == EQ_NI())
    Ensures(Implies(not sympifiable, Result() == EQ_NI()))
    Ensures(Implies(sympifiable and content_equal, Result() == EQ_TRUE()))
    Ensures(Implies(sympifiable and not content_equal, Result() == EQ_FALSE()))
    if not sympifiable:
        return EQ_NI()
    if content_equal:
        return EQ_TRUE()
    return EQ_FALSE()


@Pure
def op_eq(self_answer: int, other_answer: int) -> bool:
    """The fully-resolved `==` operator on two three-valued answers.

    `self_answer` is the symbolic value's own three-valued reply
    (`sym_eq`); `other_answer` is what the right-hand object's reflected
    equality would reply (also three-valued). The operator resolves:
      * if the symbolic value is decided, take its boolean;
      * else if the right-hand object is decided, take its boolean
        (delegation to the reflected method);
      * else fall back to object identity -> distinct objects are not equal.
    """
    Requires(self_answer == EQ_FALSE() or self_answer == EQ_TRUE() or self_answer == EQ_NI())
    Requires(other_answer == EQ_FALSE() or other_answer == EQ_TRUE() or other_answer == EQ_NI())
    if self_answer != EQ_NI():
        return self_answer == EQ_TRUE()
    if other_answer != EQ_NI():
        return other_answer == EQ_TRUE()
    return False
# pure-end


def sym_eq(sympifiable: bool, content_equal: bool) -> int:
    """Three-valued equality of a symbolic value against a right-hand object.

    `sympifiable` -- the right-hand object is a comparable peer.
    `content_equal` -- meaningful only when `sympifiable`; the peer's content
    coincides with the symbolic value.
    """
    # pre-conditions-start
    # The equality reply is a bounded, straight-line computation: it MUST
    # terminate and return its three-valued reply (total correctness). A
    # diverging implementation would satisfy the value postconditions only
    # vacuously and would never deliver a reply to the protocol at all.
    Requires(MustTerminate(1))
    # pre-conditions-end
    # post-conditions-start
    # the three-valued answer is exactly the protocol reply: incomparable
    # right-hand object -> the delegation sentinel (never a flat "not equal",
    # the symmetry-preserving obligation); a comparable peer -> a definite
    # verdict driven by content.
    Ensures(Result() == eq_code(sympifiable, content_equal))
    Ensures(Implies(not sympifiable, Result() == EQ_NI()))
    Ensures(Implies(sympifiable and content_equal, Result() == EQ_TRUE()))
    Ensures(Implies(sympifiable and not content_equal, Result() == EQ_FALSE()))
    # post-conditions-end
    # impl-start
    if not sympifiable:
        return EQ_NI()
    if content_equal:
        return EQ_TRUE()
    return EQ_FALSE()
    # impl-end


def sym_ne(sympifiable: bool, content_equal: bool, other_answer: int) -> bool:
    """Inequality of a symbolic value against a right-hand object.

    `other_answer` is the right-hand object's own three-valued equality reply,
    consulted by the resolved `==` operator on the delegation sentinel.
    """
    # pre-conditions-start
    Requires(other_answer == EQ_FALSE() or other_answer == EQ_TRUE() or other_answer == EQ_NI())
    # The inequality reply is a bounded, straight-line computation: it MUST
    # terminate and return its boolean (total correctness; measure 2 leaves
    # room for the sym_eq sub-call's own MustTerminate(1) obligation). A
    # diverging implementation would satisfy the value postconditions only
    # vacuously and would never deliver a reply to the protocol at all.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    # inequality is the complement of the FULLY-RESOLVED equality operator.
    Ensures(Result() == (not op_eq(eq_code(sympifiable, content_equal), other_answer)))
    # behavioural consequence the protocol demands: an incomparable peer that
    # considers itself equal to the symbolic value must NOT be reported unequal
    # (symmetry), and an incomparable peer that is genuinely unequal MUST be.
    Ensures(Implies(not sympifiable and other_answer == EQ_TRUE(), Result() == False))
    Ensures(Implies(not sympifiable and other_answer != EQ_TRUE(), Result() == True))
    # post-conditions-end
    # impl-start
    e = sym_eq(sympifiable, content_equal)
    # PRE-PATCH BUG: complement the symbolic value's OWN raw three-valued reply
    # rather than the fully-resolved operator. In Python `not self.__eq__(o)`
    # treats the truthy delegation sentinel as "equal-ish", so a raw "undecided"
    # collapses to False here (only a definite "not equal" yields True), and the
    # other side is never consulted.
    return e == EQ_FALSE()
    # impl-end
