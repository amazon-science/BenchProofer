"""Twin-artifact model for sympy__sympy-13551.

Behaviour under specification (stated as desired behaviour, not as an edit):

  Reducing a finite product whose multiplicand is a *sum* of two parts.

  Over an index that ranges across a finite set of values, the multiplicand at
  each index is the arithmetic sum of two contributions: a base contribution
  `base[i]` and a companion contribution `comp[i]`. The product being evaluated
  is therefore

        result = (base[0]+comp[0]) * (base[1]+comp[1]) * ... * (base[L-1]+comp[L-1])

  i.e. the product, over every index, of the per-index TOTAL.

  The single property that matters: the product of the per-index totals is NOT
  the same number as the total of the two per-part products
  (`prod(base) + prod(comp)`). A correct reduction multiplies the per-index
  totals together; it must not distribute the product across the two parts of
  the sum. (For example for base=[1,2], comp=[1,3] the product of totals is
  (1+1)*(2+3)=10, whereas the total of the part-products is (1*2)+(1*3)=5.)

  Domain boundary: the multiplicand is nonzero at every index. When some
  per-index total is zero the repo's reduction yields an undefined symbolic
  value rather than the integer 0, so such inputs are outside the modeled
  scenario; the precondition excludes them (mapping.md §2).

Modelling choices (Nagini fragment):
  * The index ranges over a finite set; the value the i-th part-contribution
    takes at each index is carried in a parallel `List[int]` (`base`, `comp`),
    one entry per index. A multiplicand that is a sum splits into exactly two
    such parts (a leading part and the remaining part); this binary split is the
    faithful skeleton (mapping.md / refinement.md).
  * The per-index total `base[i] + comp[i]` and its running product are spelled
    out deeply: `prod_of_totals` is a `@Pure` front-recursive fold so a single
    unfold is available to the verified loop. There is no axiom for the product
    operation -- it is modelled directly.

No string indexing is used (Nagini bans it). List access under quantifiers is
guarded by explicit in-bounds conjuncts. Markers (machine-parsed) delimit the
spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# axioms-end


# pure-start
@Pure
def prod_of_totals(base: PSeq[int], comp: PSeq[int]) -> int:
    """Product, over every index, of the per-index TOTAL `base[i] + comp[i]`.
    Front-recursive so a single unfold is available to callers. The empty
    product is 1."""
    Requires(len(base) == len(comp))
    if len(base) == 0:
        return 1
    return (base[0] + comp[0]) * prod_of_totals(base.drop(1), comp.drop(1))


@Pure
def prod_one(xs: PSeq[int]) -> int:
    """Product of a single part's contributions across every index. Used only
    to STATE the property that distributing the product across the sum (the
    total of the two part-products) is a different number; never the answer."""
    if len(xs) == 0:
        return 1
    return xs[0] * prod_one(xs.drop(1))
# pure-end


def product_of_sum(base: List[int], comp: List[int]) -> int:
    # pre-conditions-start
    Requires(Acc(list_pred(base), 1 / 2))
    Requires(Acc(list_pred(comp), 1 / 2))
    # The two parts describe the same indices.
    Requires(len(base) == len(comp))
    # Every per-index total is nonzero: a vanishing multiplicand makes the
    # repo's reduction undefined (not the integer 0), so zero totals are
    # outside the modeled domain (mapping.md §2).
    Requires(Forall(int, lambda i: Implies(0 <= i and i < len(base),
                                           base[i] + comp[i] != 0)))
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(base), 1 / 2))
    Ensures(Acc(list_pred(comp), 1 / 2))
    Ensures(len(base) == len(comp))
    # The reduction returns the product of the per-index totals.
    Ensures(Result() == prod_of_totals(ToSeq(base), ToSeq(comp)))
    # post-conditions-end
    # impl-start
    # PRE-PATCH (buggy): distribute the product across the two parts of the sum
    # and add the per-part products, instead of multiplying the per-index
    # totals. This is the wrong "product of a sum equals sum of products" step.
    pb = 1
    i = len(base)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(base), 1 / 2))
        Invariant(Acc(list_pred(comp), 1 / 2))
        Invariant(len(base) == len(comp))
        Invariant(0 <= i and i <= len(base))
        Invariant(pb == prod_one(ToSeq(base).drop(i)))
        Invariant(MustTerminate(i + 1))
        # invariants-end
        Assert(ToSeq(base).drop(i - 1)[0] == base[i - 1])
        Assert(ToSeq(base).drop(i - 1).drop(1) == ToSeq(base).drop(i))
        pb = base[i - 1] * pb
        i = i - 1
    pc = 1
    j = len(comp)
    while j > 0:
        # invariants-start
        Invariant(Acc(list_pred(base), 1 / 2))
        Invariant(Acc(list_pred(comp), 1 / 2))
        Invariant(len(base) == len(comp))
        Invariant(0 <= j and j <= len(comp))
        Invariant(pc == prod_one(ToSeq(comp).drop(j)))
        Invariant(MustTerminate(j + 1))
        # invariants-end
        Assert(ToSeq(comp).drop(j - 1)[0] == comp[j - 1])
        Assert(ToSeq(comp).drop(j - 1).drop(1) == ToSeq(comp).drop(j))
        pc = comp[j - 1] * pc
        j = j - 1
    result = pb + pc
    return result
    # impl-end
