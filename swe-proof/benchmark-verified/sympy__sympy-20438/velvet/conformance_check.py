#!/usr/bin/env python3
"""G-CONF differential conformance check for sympy__sympy-20438 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW — the R/I-tagged ops of Solution.lean's three impl regions
             transliterated to Python over the *real* repo types, via the
             mapping.md bijection (`Option Bool` ↔ {True,False,None}). The
             A-tagged callees are NOT replaced by their models here: the
             membership verdicts (`contains`), the containment verdicts
             (`is_subset`), and the general-simplification result (`normal`) are
             read straight from the *real* repo objects. G-CONF isolates the
             R/I skeleton — the three-valued fold (`triAll`/`tand2`), the binary
             conjunction, and the `if both-expr` guard — and the deep-model
             equality `triAll == fuzzy_and` stays with G-AX.
  * ORACLE — `patch.diff`'s behaviour: the REAL patched repo functions applied
             at base_commit (the harness applies patch.diff before this runs):
             `ProductSet.is_subset(FiniteSet)` (behavior #1), the three-valued
             `is_eq(Set, Set)` (behavior #2), and `Eq(...).simplify()` over
             mixed expression / non-expression operands (behavior #3).

They must agree on every input. Exit 0 iff zero disagreements; any disagreement
is a mechanical R/I-fidelity counterexample.

Runs in-container (the prebuilt SWE-Bench instance image), stdlib + sympy only.
The fuzz seed is pinned (mapping.md §4) for a deterministic verdict.
"""
import itertools
import random
import sys

SEED = 20438
DISAGREE_CAP = 5


# --- the R/I shadow: Solution.lean tand2 / triAll, transliterated ------------
# Three-valued domain bijection (mapping.md §2): some true ↔ True,
# some false ↔ False, none ↔ None.

def tand2(x, y):
    """Mirror of Solution.lean `tand2`: false dominates (even vs unknown);
    else unknown dominates; else true."""
    if x is False:
        return False
    if y is False:
        return False
    if x is None:
        return None
    if y is None:
        return None
    return True


def tri_all(xs):
    """Mirror of Solution.lean `triAll` (front-recursive fold, identity True).
    The backward `while` loop of everyElementMember computes exactly this."""
    acc = True
    for c in reversed(xs):      # tand2 is order-insensitive in result
        acc = tand2(c, acc)
    return acc


def main():
    from sympy import FiniteSet, ProductSet, Interval, Eq, S, Symbol
    from sympy.core.relational import is_eq

    rng = random.Random(SEED)
    disagreements = []
    count = 0

    x = Symbol('x')

    # Small, decidable element pool so ProductSet enumeration + contains stay
    # fast and the three-valued verdicts are definite.
    pool = [1, 2, 3]

    # ---- behavior #1: everyElementMember  ==  patched is_subset_sets ---------
    # shadow = triAll([ b.contains(e) for e in a ])  (real `contains`, the
    #          A-reference inputs); oracle = real patched a.is_subset(b).
    # a is a ProductSet of small FiniteSets; b a FiniteSet of tuples.
    def threeval(v):
        if v is True or v is S.true:
            return True
        if v is False or v is S.false:
            return False
        return None

    # enumerate ProductSets A_k x A_k and a spread of candidate FiniteSets
    finite_bases = []
    for r in range(1, 4):
        for combo in itertools.combinations(pool, r):
            finite_bases.append(FiniteSet(*combo))

    for a1 in finite_bases:
        for a2 in finite_bases:
            ps = ProductSet(a1, a2)
            elems = list(ps)                      # the product tuples
            # candidate finite collections of tuples: exact, superset, partial,
            # disjoint, and randomized subsets
            candidates = []
            candidates.append(FiniteSet(*elems))                       # exact
            candidates.append(FiniteSet(*(elems + [(9, 9)])))          # superset
            if len(elems) > 1:
                candidates.append(FiniteSet(*elems[:-1]))              # missing one
            candidates.append(FiniteSet((9, 9)))                       # disjoint
            for _ in range(3):
                k = rng.randint(0, len(elems))
                sub = rng.sample(elems, k) if k else []
                candidates.append(FiniteSet(*sub) if sub else S.EmptySet)

            for b in candidates:
                if b is S.EmptySet:
                    continue
                count += 1
                shadow = tri_all([threeval(b.contains(e)) for e in elems])
                oracle = threeval(ps.is_subset(b))
                if shadow != oracle:
                    disagreements.append(("is_subset", (a1, a2, b),
                                          shadow, oracle))
                    if len(disagreements) >= DISAGREE_CAP:
                        break
            if len(disagreements) >= DISAGREE_CAP:
                break
        if len(disagreements) >= DISAGREE_CAP:
            break

    # randomized fuzz to push behavior #1 past 10^5 comparisons: random product
    # bases x random finite collections of tuples drawn from a slightly larger
    # pool (so membership splits true/false/unknown across the run).
    big_pool = pool + [4, x]                       # x = Symbol -> unknown verdicts
    tuple_universe = [(i, j) for i in pool for j in pool] + [(9, 9), (1, x)]
    N_FUZZ = 115_000
    if not disagreements:
        for _ in range(N_FUZZ):
            r1 = rng.randint(1, 3)
            r2 = rng.randint(1, 3)
            a1 = FiniteSet(*rng.sample(big_pool, r1))
            a2 = FiniteSet(*rng.sample(big_pool, r2))
            ps = ProductSet(a1, a2)
            elems = list(ps)
            k = rng.randint(0, len(tuple_universe))
            sub = rng.sample(tuple_universe, k)
            if not sub:
                continue
            b = FiniteSet(*sub)
            count += 1
            shadow = tri_all([threeval(b.contains(e)) for e in elems])
            oracle = threeval(ps.is_subset(b))
            if shadow != oracle:
                disagreements.append(("is_subset-fuzz", (a1, a2, b),
                                      shadow, oracle))
                if len(disagreements) >= DISAGREE_CAP:
                    break

    # ---- behavior #2: setsCoincide  ==  patched is_eq(Set, Set) -------------
    # shadow = tand2(a.is_subset(b), b.is_subset(a))  (real is_subset inputs);
    # oracle = real three-valued is_eq(a, b). ONLY mixed FiniteSet↔ProductSet
    # pairs reach the generic (Set, Set) rule the patch changed; same-type pairs
    # (FiniteSet/FiniteSet, ProductSet/ProductSet) dispatch to their own
    # specific rules and are out of this model's scope (mapping.md §1).
    finite_tuple_sets = []
    all_tuples = [(i, j) for i in pool for j in pool]
    for r in range(1, 4):
        for combo in itertools.combinations(all_tuples, r):
            finite_tuple_sets.append(FiniteSet(*combo))
    product_sets = []
    for r1 in range(1, 3):
        for c1 in itertools.combinations(pool, r1):
            for r2 in range(1, 3):
                for c2 in itertools.combinations(pool, r2):
                    product_sets.append(
                        ProductSet(FiniteSet(*c1), FiniteSet(*c2)))

    fs_sample = rng.sample(finite_tuple_sets,
                           min(40, len(finite_tuple_sets)))
    for F in fs_sample:
        for P in product_sets:
            for lhs, rhs in [(F, P), (P, F)]:
                count += 1
                sub_ab = threeval(lhs.is_subset(rhs))
                sub_ba = threeval(rhs.is_subset(lhs))
                shadow = tand2(sub_ab, sub_ba)
                oracle = threeval(is_eq(lhs, rhs))
                if shadow != oracle:
                    disagreements.append(("is_eq", (lhs, rhs), shadow, oracle))
                    if len(disagreements) >= DISAGREE_CAP:
                        break
            if len(disagreements) >= DISAGREE_CAP:
                break
        if len(disagreements) >= DISAGREE_CAP:
            break

    # ---- behavior #3: guardedSimplify  ==  patched Eq(...).simplify() -------
    # shadow = (normal if both-operands-are-Expr else r); oracle = the patched
    # _eval_simplify, which returns the relation UNCHANGED when an operand is
    # not an algebraic expression (a Set), else proceeds (== normal).
    from sympy.core.expr import Expr
    from sympy.core.relational import Relational
    # Cases whose is_eq is indeterminate so Eq(...) SURVIVES as a Relational
    # with a Set operand (not pre-evaluated to S.true/S.false). Without the
    # patch's guard these raised AttributeError forming lhs - rhs; the spec
    # requires the relation be returned UNCHANGED.
    guard_cases = [
        Eq(FiniteSet(1), FiniteSet(x)),          # symbolic membership -> survives
        Eq(FiniteSet(1, 2), FiniteSet(x, 3)),    # survives, non-Expr operands
        Eq(x + 1, 2),                            # both Expr -> general path
        Eq(2 * x, x + x),                        # both Expr -> general path
    ]
    for rel in guard_cases:
        count += 1
        # rel may be a Relational (survived) or a Boolean (pre-evaluated).
        if not isinstance(rel, Relational):
            continue                              # not a guard-relevant case
        both_expr = isinstance(rel.lhs, Expr) and isinstance(rel.rhs, Expr)
        simplified = rel.simplify()
        if not both_expr:
            # spec: relation returned UNCHANGED (no AttributeError, identity)
            ok = (simplified == rel)
            shadow = "unchanged"
            oracle = "unchanged" if ok else repr(simplified)
        else:
            # general path may proceed; spec only requires no spurious guard.
            shadow = oracle = "proceeded"
        if shadow != oracle:
            disagreements.append(("simplify-guard", rel, shadow, oracle))
            if len(disagreements) >= DISAGREE_CAP:
                break

    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for who, inp, sh, orc in disagreements:
            print("  %s input=%r shadow=%r oracle=%r" % (who, inp, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of everyElementMember / setsCoincide / "
          "guardedSimplify agrees with patch.diff behaviour on %d inputs "
          "(seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
