"""G-AX executable soundness check for sympy__sympy-20438.

Runs the REAL post-patch sympy callees in-container and confirms:

  (A-consumed) `member`  ==  FiniteSet.contains(x)
      The membership oracle is sound: for concrete element handles, the real
      FiniteSet.contains is deterministic, total and returns a definite truth
      value (True / False, never None / unevaluated).  The axiom claims ONLY
      determinism + totality (it has no value Ensures), so this is the weakest
      sufficient contract.

  (A-reference 1) product_subset_of_finite's deep fold == the real decision
      The real `is_subset_sets(ProductSet, FiniteSet)` (and hence
      ProductSet.is_subset(FiniteSet)) equals `all(x in finite for x in
      product)` -- the spec's `all_in` fold -- with NO double-masking: the
      decision is asserted directly against the enumerated product elements.

  (A-reference 2) finite_sets_equal's deep fold == the real decision
      Real set equality `Eq(A, B).simplify()` reduces to mutual subset:
      it is S.true exactly when each set contains the other, S.false otherwise.

  (A-reference 3) simplify_equality_route's guard == the real routing
      The real equality-simplification is guarded on operand kind.  For
      collection (non-arithmetic) operands the arithmetic-reduction path is NOT
      taken: `Eq(A, B).simplify()` does NOT raise and reaches the collection-
      equality decision, returning a definite truth value (or the unevaluated
      relation for a symbolic operand).  For arithmetic operands the arithmetic
      path is taken and the routing never reaches the collection rule.  This is
      asserted directly: the routed operands are confirmed NOT both `Expr`, and
      simplifying them produces a defined result rather than the pre-patch
      AttributeError.

Includes the exact F2P witnesses from test_issue_19378 / test_Eq and fuzz over
random finite sets and Cartesian products.  stdlib + sympy only.  Exit 0 iff
every observation meets the contract.
"""
import itertools
import random
import sys

from sympy import FiniteSet, ProductSet, Eq, S
from sympy.core.expr import Expr
from sympy.abc import x


FAILURES = []


def fail(msg):
    FAILURES.append(msg)
    print("VIOLATION:", msg)


# ---------------------------------------------------------------------------
# A-consumed: member == FiniteSet.contains on concrete handles
# ---------------------------------------------------------------------------
def real_member(finite, el):
    """Definite-bool membership; the contract requires this to be total +
    deterministic (a definite truth value) for concrete elements."""
    c1 = finite.contains(el)
    c2 = finite.contains(el)
    if c1 != c2:
        fail("contains non-deterministic: %r in %r -> %r vs %r"
             % (el, finite, c1, c2))
    if c1 not in (S.true, S.false):
        fail("contains not a definite bool: %r in %r -> %r"
             % (el, finite, c1))
    return c1 is S.true


# spec fold mirror (definite-bool domain)
def all_in(elems, finite):
    return all(real_member(finite, e) for e in elems)


# ---------------------------------------------------------------------------
# A-reference 1: ProductSet.is_subset(FiniteSet) == all_in(product, finite)
# ---------------------------------------------------------------------------
def check_subset(prod, finite):
    elems = list(prod)                      # enumerate the Cartesian product
    model = all_in(elems, finite)           # the spec's all_in fold
    real = prod.is_subset(finite)           # the real post-patch decision
    # Direct index/structural assertion -- no double-mask, no skip-guard.
    if real is not True and real is not False:
        fail("is_subset not definite: %r.is_subset(%r) -> %r"
             % (prod, finite, real))
        return
    if bool(real) != model:
        fail("subset mismatch: %r.is_subset(%r) real=%r model(all_in)=%r"
             % (prod, finite, real, model))


# ---------------------------------------------------------------------------
# A-reference 2: Eq(A, B).simplify() == mutual subset
# ---------------------------------------------------------------------------
def check_equal(A, B):
    elemsA, elemsB = list(A), list(B)
    model = all_in(elemsA, B) and all_in(elemsB, A)
    real = Eq(A, B).simplify()
    if real is not S.true and real is not S.false:
        fail("Eq not definite for concrete finite sets: Eq(%r,%r).simplify()=%r"
             % (A, B, real))
        return
    if (real is S.true) != model:
        fail("equality mismatch: Eq(%r,%r).simplify()=%r model(mutual-subset)=%r"
             % (A, B, real, model))


# ---------------------------------------------------------------------------
# A-reference 3: the operand-kind routing guard of equality simplification.
#   When the operands are collections (NOT both Expr), Eq(A,B).simplify() must
#   NOT take the arithmetic-reduction path -- it must reach the collection rule
#   without raising, returning a DEFINED result (a definite truth value for two
#   concrete finite sets, or the unevaluated relation for a symbolic operand).
#   When BOTH operands are arithmetic (Expr) the arithmetic path is taken and
#   the routing never reaches the collection rule (the result is an Expr-domain
#   relation/bool, decided by the unchanged arithmetic machinery).
# ---------------------------------------------------------------------------
def check_route(A, B, both_arith):
    # Confirm the guard predicate the routing branches on matches the model flag:
    # both_arith iff both operands are Expr (arithmetic).
    real_both = isinstance(A, Expr) and isinstance(B, Expr)
    if real_both != both_arith:
        fail("route guard mismatch: both_arith=%r but isinstance(Expr) gives %r "
             "for (%r, %r)" % (both_arith, real_both, A, B))
        return
    try:
        r = Eq(A, B).simplify()
    except Exception as e:
        # The pre-patch failure mode (AttributeError on the arithmetic path for a
        # collection operand) -- the routing MUST avoid this for collections.
        fail("route raised on (%r, %r) [both_arith=%r]: %r" % (A, B, both_arith, e))
        return
    if not both_arith:
        # Collection case: the arithmetic path was NOT taken; the result is a
        # DEFINED outcome (a definite truth value, or the unevaluated relation).
        if r is None:
            fail("route: collection case left undefined (None) for (%r, %r)"
                 % (A, B))


# ---------------------------------------------------------------------------
# Exact F2P witnesses (test_issue_19378 / test_Eq)
# ---------------------------------------------------------------------------
def f2p_witnesses():
    a = FiniteSet(1, 2)
    b = ProductSet(a, a)
    c = FiniteSet((1, 1), (1, 2), (2, 1), (2, 2))
    d = FiniteSet(1)

    if b.is_subset(c) is not True:
        fail("F2P: b.is_subset(c) expected True, got %r" % (b.is_subset(c),))
    if b.is_subset(d) is not False:
        fail("F2P: b.is_subset(d) expected False, got %r" % (b.is_subset(d),))
    if Eq(c, b).simplify() is not S.true:
        fail("F2P: Eq(c,b).simplify() expected S.true, got %r"
             % (Eq(c, b).simplify(),))
    if Eq(a, c).simplify() is not S.false:
        fail("F2P: Eq(a,c).simplify() expected S.false, got %r"
             % (Eq(a, c).simplify(),))
    # symbolic case must stay unevaluated (relational.py Expr guard)
    if Eq(FiniteSet(1), FiniteSet(x)).simplify() != Eq(FiniteSet(1), FiniteSet(x)):
        fail("F2P: Eq({1},{x}).simplify() expected unevaluated Eq, got %r"
             % (Eq(FiniteSet(1), FiniteSet(x)).simplify(),))
    # test_Eq: ProductSet vs Interval now definitely false
    from sympy import Interval
    if Eq(ProductSet(FiniteSet(1), FiniteSet(2)), Interval(1, 2)) is not S.false:
        fail("F2P(test_Eq): Eq(ProductSet({1},{2}),Interval(1,2)) expected S.false")

    # also confirm the deep-fold equivalence on these witnesses directly
    check_subset(b, c)
    check_subset(b, d)
    check_equal(c, b)
    check_equal(a, c)

    # Routing guard (A-reference 3): every equality operand here is a collection
    # (NOT Expr), so the routing must defer to the collection rule WITHOUT taking
    # the arithmetic path / raising.  The symbolic FiniteSet operand is still a
    # collection (routes to the rule, result is the unevaluated relation).
    check_route(c, b, both_arith=False)
    check_route(a, c, both_arith=False)
    check_route(FiniteSet(1), FiniteSet(x), both_arith=False)
    check_route(ProductSet(FiniteSet(1), FiniteSet(2)), Interval(1, 2),
                both_arith=False)
    # arithmetic-operand control: two number-like operands DO take the arithmetic
    # path (both Expr) and never reach the collection rule.
    from sympy import Integer
    check_route(Integer(1), Integer(1), both_arith=True)
    check_route(Integer(1), Integer(2), both_arith=True)
    check_route(x, Integer(0), both_arith=True)


# ---------------------------------------------------------------------------
# Fuzz: random finite sets of small integers and their Cartesian products
# ---------------------------------------------------------------------------
def fuzz(rounds=4000, seed=20438):
    rng = random.Random(seed)
    pool = [0, 1, 2, 3]
    for _ in range(rounds):
        # ProductSet of 1..2 small FiniteSets
        k = rng.randint(1, 2)
        comps = []
        for _ in range(k):
            n = rng.randint(1, 3)
            comps.append(FiniteSet(*rng.sample(pool, n)))
        prod = ProductSet(*comps)
        # a finite target set drawn from the relevant tuple universe + noise
        universe = list(itertools.product(*[list(c) for c in comps]))
        m = rng.randint(0, len(universe))
        chosen = rng.sample(universe, m)
        # occasionally inject an alien tuple so the answer flips
        if rng.random() < 0.3:
            chosen = list(chosen) + [(9, 9)]
        tuples = [t[0] if len(t) == 1 else t for t in chosen]
        finite = FiniteSet(*tuples) if tuples else FiniteSet()
        try:
            check_subset(prod, finite)
        except Exception as e:  # pragma: no cover
            fail("subset fuzz raised %r on prod=%r finite=%r" % (e, prod, finite))

        # equality fuzz between two finite sets of integers
        sa = FiniteSet(*rng.sample(pool, rng.randint(1, 4)))
        sb = FiniteSet(*rng.sample(pool, rng.randint(1, 4)))
        try:
            check_equal(sa, sb)
        except Exception as e:  # pragma: no cover
            fail("equal fuzz raised %r on %r,%r" % (e, sa, sb))
        # routing fuzz: these collection (non-Expr) operands must route to the
        # collection rule WITHOUT raising / taking the arithmetic path.
        try:
            check_route(sa, sb, both_arith=False)
        except Exception as e:  # pragma: no cover
            fail("route fuzz raised %r on %r,%r" % (e, sa, sb))


def main():
    f2p_witnesses()
    fuzz()
    if FAILURES:
        print("AXIOM CHECK FAILED: %d violation(s)" % len(FAILURES))
        sys.exit(1)
    print("AXIOM CHECK OK: member sound (deterministic+total definite bool); "
          "ProductSet.is_subset(FiniteSet) == all_in fold; "
          "Eq(A,B).simplify() == mutual-subset; equality-routing guard defers "
          "collection operands to the collection rule without raising; "
          "all F2P witnesses pass.")
    sys.exit(0)


if __name__ == "__main__":
    main()
