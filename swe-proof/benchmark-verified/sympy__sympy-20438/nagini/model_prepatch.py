"""Twin-artifact model for sympy__sympy-20438.

Behaviour under specification (stated as desired behaviour, not as an edit):

  (1) Deciding whether a structured (Cartesian-product) collection is contained
      in a finite collection.  Enumerate the elements of the product collection
      and ask, for each, whether it belongs to the finite collection.  The
      product collection is a subset of the finite collection EXACTLY when every
      enumerated element belongs to it.  In particular the answer is a definite
      truth value computed FROM the per-element membership facts -- it is not
      left undecided when those facts are all available.

  (2) Deciding whether two finite collections are equal.  Two collections are
      equal EXACTLY when each is contained in the other -- i.e. every element of
      the first belongs to the second AND every element of the second belongs to
      the first.  Equality is therefore the conjunction of the two containment
      decisions of behaviour (1), again a definite truth value when all the
      per-element membership facts are available.

  (3) Routing the simplification of an equality between two operands.  An
      equality is simplified by first attempting an arithmetic-style reduction
      that only applies when BOTH operands are arithmetic (number-like) values:
      it forms their difference and compares it with zero.  That reduction is
      only meaningful for arithmetic operands; for operands that are collections
      (which carry no difference / zero-comparison) the reduction must NOT be
      attempted -- attempting it on a collection operand has no defined result.
      The behaviour under specification: the routing is guarded on operand kind.
      When both operands are arithmetic it takes the arithmetic-reduction path.
      When at least one operand is a collection it does NOT take that path; it
      defers to the collection-equality decision of behaviour (2) and returns
      that definite truth value.  In particular the collection case is ALWAYS
      decided through behaviour (2) and never routed into the arithmetic
      reduction that has no defined result for a collection operand.

Elements are modelled as opaque integer handles.  Membership of a handle in a
collection is an unchanged deterministic pure oracle keyed by a collection
identifier (axioms region); only totality + determinism are relied upon -- the
impl reads the SAME membership fact the spec folds read.  Each containment
decision is the front-recursive boolean fold `all_in` over the enumerated
element handles, paired with a matching loop in the impl.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
@Pure
@ContractOnly
def member(setid: int, el: int) -> bool:
    """The unchanged membership oracle: whether element handle `el` belongs to
    the finite collection identified by `setid`.  Deterministic and total -- the
    only properties relied upon -- so the impl loop reads the same membership
    fact that the specification fold reads.  Provenance + executable soundness
    check: mapping.md / axiom_check.py.
    """
# axioms-end


# pure-start
@Pure
def all_in(s: PSeq[int], setid: int) -> bool:
    """Whether every enumerated element handle in `s` belongs to the collection
    `setid`.  Front-recursive so a single unfold is available per loop step:
    empty enumerates to True; otherwise the head must be a member AND the tail
    must all be members."""
    if len(s) == 0:
        return True
    return member(setid, s[0]) and all_in(s.drop(1), setid)


@Pure
def ARITH_PATH() -> int:
    """Outcome token meaning the arithmetic-reduction path was taken (the
    unchanged behaviour for two arithmetic operands -- its result is opaque to
    this routing model)."""
    return 0


@Pure
def collection_outcome(equal: bool) -> int:
    """Outcome token of the collection-equality decision: a definite truth value
    (distinct from the arithmetic-path token).  `equal` is the collection
    equality of behaviour (2)."""
    return 1 if equal else 2
# pure-end


def product_subset_of_finite(elems: List[int], finite_id: int) -> bool:
    # pre-conditions-start
    Requires(Acc(list_pred(elems), 1 / 2))
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(elems), 1 / 2))
    # The product collection is a subset of the finite collection EXACTLY when
    # every enumerated element belongs to it -- a definite truth value derived
    # from the per-element membership facts.
    Ensures(Result() == all_in(ToSeq(elems), finite_id))
    # post-conditions-end
    # impl-start
    # PRE-PATCH SKELETON: no rule enumerates the product elements and asks for
    # their membership, so the containment fact is never computed -- the
    # decision does not depend on `member` at all.
    res = len(elems) == 0
    return res
    # impl-end


def finite_sets_equal(elems_a: List[int], id_a: int,
                      elems_b: List[int], id_b: int) -> bool:
    # pre-conditions-start
    Requires(Acc(list_pred(elems_a), 1 / 2))
    Requires(Acc(list_pred(elems_b), 1 / 2))
    Requires(MustTerminate(6))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(elems_a), 1 / 2))
    Ensures(Acc(list_pred(elems_b), 1 / 2))
    # Two finite collections are equal EXACTLY when each is contained in the
    # other: every element of the first belongs to the second AND every element
    # of the second belongs to the first.
    Ensures(Result() == (all_in(ToSeq(elems_a), id_b)
                         and all_in(ToSeq(elems_b), id_a)))
    # post-conditions-end
    # impl-start
    a_sub_b = product_subset_of_finite(elems_a, id_b)
    b_sub_a = product_subset_of_finite(elems_b, id_a)
    return a_sub_b and b_sub_a
    # impl-end


def simplify_equality_route(both_arith: bool,
                            elems_a: List[int], id_a: int,
                            elems_b: List[int], id_b: int) -> int:
    # pre-conditions-start
    # `both_arith` records whether BOTH equality operands are arithmetic
    # (number-like) values; if False, at least one is a collection.  When the
    # operands are collections, `elems_a`/`id_a` and `elems_b`/`id_b` are the
    # element handles and collection ids of behaviour (2) for the two operands.
    Requires(Acc(list_pred(elems_a), 1 / 2))
    Requires(Acc(list_pred(elems_b), 1 / 2))
    Requires(MustTerminate(10))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(elems_a), 1 / 2))
    Ensures(Acc(list_pred(elems_b), 1 / 2))
    # The routing is total: it always returns a definite outcome token -- it
    # never has an undefined result.  In particular the collection case is
    # decided, never left without a defined result.
    # When both operands are arithmetic the arithmetic-reduction path is taken.
    Ensures(Implies(both_arith, Result() == ARITH_PATH()))
    # When at least one operand is a collection the arithmetic reduction is NOT
    # attempted (its token is never returned); the routing defers to the
    # collection-equality decision of behaviour (2) and returns that definite
    # truth value as a collection outcome token.
    Ensures(Implies(not both_arith, Result() != ARITH_PATH()))
    Ensures(Implies(not both_arith,
                    Result() == collection_outcome(
                        all_in(ToSeq(elems_a), id_b)
                        and all_in(ToSeq(elems_b), id_a))))
    # post-conditions-end
    # impl-start
    if both_arith:
        # Both operands arithmetic: take the unchanged arithmetic-reduction path.
        return ARITH_PATH()
    # At least one operand is a collection: do NOT attempt the arithmetic
    # reduction (which has no defined result for a collection operand); defer to
    # the collection-equality decision of behaviour (2).
    equal = finite_sets_equal(elems_a, id_a, elems_b, id_b)
    return collection_outcome(equal)
    # impl-end
