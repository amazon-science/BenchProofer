"""Twin-artifact model for sympy__sympy-18698.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A square-free factorisation is reported as a collection of (factor,
  multiplicity) contributions. The report must be CONSOLIDATED by multiplicity:
  a multiplicity may appear at most once in the whole report, and the single
  factor recorded for a multiplicity is the product of every contributing factor
  that carries that multiplicity. So whenever several factors share one
  multiplicity they are merged into one product entry; a multiplicity that
  occurs once is left as it is.

  Concretely, given the raw collection of (factor, multiplicity) contributions
  (carried as two parallel sequences ``factors`` / ``mults`` of equal length),
  the reported multiplicities are exactly the DISTINCT multiplicities occurring
  among the contributions, each kept once (at its first occurrence). The factor
  recorded against the j-th reported multiplicity is the PRODUCT, over every
  contribution whose multiplicity equals that reported multiplicity, of the
  contributing factors -- so several factors sharing a multiplicity collapse to
  one product entry, while a multiplicity that occurs once keeps its single
  factor unchanged.

Modelling choices (Nagini fragment):
  * Each contribution is modelled as a multiplicity (an `int`) paired with a
    factor token (an `int`), carried as two parallel `List[int]` (``factors`` /
    ``mults``) of equal length and specified over `PSeq[int]` via ``ToSeq``.
    mapping.md gives the bijection token <-> factor expression.
  * The merged factor of a group is the PRODUCT of the group. Factor expressions
    form a commutative/associative monoid under multiplication; integer
    multiplication of the distinct factor tokens is a faithful model of that
    monoid (the consolidation depends only on WHICH factors are multiplied for a
    given multiplicity, never on the internal spelling of an expression --
    mapping.md). The product is therefore modelled DEEPLY: ``prod_k`` is the
    spelled-out product fold over exactly the contributions of a given
    multiplicity, and the verified construction proves the recorded factor equals
    that fold. The product over a group is thereby pinned exactly by the inputs.
  * The reported multiplicities are likewise modelled DEEPLY: ``dedup`` is the
    distinct-keeping fold over the multiplicity sequence (keeping each
    multiplicity at its first occurrence). The order in which the distinct
    multiplicities are listed is canonicalised here (first occurrence); it is
    unobservable because the report is sorted downstream (refinement.md), so this
    faithfully refines an unordered distinct collection.

Consolidating a finite collection of contributions is bounded work that must
actually deliver the report, so both operations carry a total-correctness
obligation (MustTerminate in the pre-conditions region, discharged by a per-loop
measure at the end of each loop's invariants region): without it an
implementation that never reaches its return would satisfy every postcondition
vacuously while never producing a merged factor.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# No consumed axioms. Both dimensions of the consolidation are modelled deeply:
# the reported multiplicities (keeping each distinct multiplicity once) by the
# `dedup` fold, and the merged factor of a group by the `prod_k` product fold --
# each discharged by the verified construction loops, not by a @ContractOnly
# Ensures. The only library fact relied on is that the factor expressions form a
# commutative/associative monoid under multiplication (so integer multiplication
# of the distinct factor tokens faithfully models the per-group product); that
# monoid correspondence is validated out-of-band by axiom_check.py (G-AX) and is
# NOT consumed as an axiom.
# axioms-end


# pure-start
@Pure
def empty_seq() -> PSeq[int]:
    """The empty multiplicity sequence."""
    Ensures(len(Result()) == 0)
    return PSeq(0).take(0)


@Pure
def occurs(s: PSeq[int], k: int) -> bool:
    """Whether the value ``k`` occurs in ``s``. Front-recursive so a single
    unfold is available per step (value-based membership)."""
    if len(s) == 0:
        return False
    if s[0] == k:
        return True
    return occurs(s.drop(1), k)


@Pure
def dedup(s: PSeq[int]) -> PSeq[int]:
    """The distinct values of ``s`` in order of FIRST occurrence: each value is
    kept once. Defined by recursion on the final element so it pairs with a
    forward-building loop -- the prefix is deduplicated, and the last value is
    appended only if it has not already appeared."""
    if len(s) == 0:
        return empty_seq()
    if occurs(dedup(s.take(len(s) - 1)), s[len(s) - 1]):
        return dedup(s.take(len(s) - 1))
    return dedup(s.take(len(s) - 1)) + PSeq(s[len(s) - 1])


@Pure
def prod_k(facs: PSeq[int], mlts: PSeq[int], k: int, n: int) -> int:
    """The product of exactly the factors whose multiplicity is ``k``, taken over
    the first ``n`` contributions (axes ``0 <= i < n``): the merged factor of the
    multiplicity-``k`` group. A contribution enters the product iff its
    multiplicity equals ``k``; the empty product is 1. Prefix-recursive (extends
    by one contribution per step) so an accumulation loop's invariant tracks
    ``acc == prod_k(facs, mlts, k, i)``. Defensive on bounds: a contribution
    enters the product only when both parallel sequences carry an axis ``n-1``,
    so the fold is total over any ``n >= 0`` (out-of-range axes contribute the
    empty product 1)."""
    Requires(n >= 0)
    if n == 0:
        return 1
    if n - 1 < len(mlts) and n - 1 < len(facs) and mlts[n - 1] == k:
        return prod_k(facs, mlts, k, n - 1) * facs[n - 1]
    return prod_k(facs, mlts, k, n - 1)


@Pure
def lemma_prod_unfold(facs: PSeq[int], mlts: PSeq[int], k: int, n: int) -> bool:
    """The prefix-recursion equation of ``prod_k``, exposed for callers (its body
    unfolded once): the product over the first ``n`` contributions multiplies the
    product over the first ``n-1`` by ``facs[n-1]`` exactly when the ``n-1``-th
    contribution has multiplicity ``k`` and is within both sequences."""
    Requires(0 < n and n <= len(mlts) and n <= len(facs))
    Ensures(Result())
    Ensures(prod_k(facs, mlts, k, n) ==
            (prod_k(facs, mlts, k, n - 1) * facs[n - 1] if mlts[n - 1] == k
             else prod_k(facs, mlts, k, n - 1)))
    return True
# pure-end


def occurs_in(xs: List[int], k: int) -> bool:
    """Whether the value ``k`` occurs in the list ``xs`` (== ``occurs`` over its
    sequence). A read-only membership scan."""
    # pre-conditions-start
    Requires(Acc(list_pred(xs), 1 / 2))
    # TERMINATION: the membership answer must actually be DELIVERED -- a scan
    # that never reaches its return satisfies the Ensures vacuously. LEVEL 2 is
    # the base level for a method that owns a loop and calls nothing obligated
    # of its own (it reads `xs` and builds no list), leaving room below it.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(xs), 1 / 2))
    Ensures(Result() == occurs(ToSeq(xs), k))
    # post-conditions-end
    # impl-start
    n = len(xs)
    found = False
    j = n
    while j > 0:
        # invariants-start
        Invariant(Acc(list_pred(xs), 1 / 2))
        Invariant(0 <= j and j <= n and n == len(xs))
        Invariant(found == occurs(ToSeq(xs).drop(j), k))
        # This down-counting scan consumes the caller's obligation on the
        # strictly decreasing, bounded-below measure `j`: `j` falls by exactly
        # one per pass and the guard keeps j > 0, so the remaining-iteration
        # bound j + 1 falls by one and stays >= 1 (the + 1 matters -- the last
        # pass has 0 iterations left and MustTerminate(0) is unsatisfiable).
        Invariant(MustTerminate(j + 1))
        # invariants-end
        Assert(ToSeq(xs).drop(j - 1) == PSeq(ToSeq(xs)[j - 1]) + ToSeq(xs).drop(j))
        if xs[j - 1] == k:
            found = True
        j = j - 1
    Assert(ToSeq(xs).drop(0) == ToSeq(xs))
    return found
    # impl-end


def consolidate_by_multiplicity(factors: List[int],
                                mults: List[int]) -> List[int]:
    """Consolidate the contributions (parallel ``factors`` / ``mults``) into the
    list of merged factors of the report. The report carries one entry per
    distinct multiplicity that occurs among the contributions (kept once, at its
    first occurrence); the merged factor recorded for the j-th reported
    multiplicity is the product of exactly the contributions whose multiplicity
    equals that reported multiplicity. Returns those merged factors, in the order
    the distinct multiplicities first occur."""
    # pre-conditions-start
    Requires(Acc(list_pred(factors), 1 / 2))
    Requires(Acc(list_pred(mults), 1 / 2))
    Requires(len(factors) == len(mults))
    # TERMINATION: the consolidated report must actually be DELIVERED -- an
    # implementation that never reaches its return satisfies every Ensures
    # vacuously. The LEVEL 3 strictly exceeds the level 2 of the obligated
    # membership scan `occurs_in`, which the consolidation may invoke, and still
    # leaves room below for the list-building calls; at level 2 Nagini reports
    # `Obligation leak check failed. Callee occurs_in might not take all
    # unsatisfied obligations from the caller.`
    Requires(MustTerminate(3))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(factors), 1 / 2))
    Ensures(Acc(list_pred(mults), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # One merged factor per distinct contribution multiplicity.
    Ensures(len(Result()) == len(dedup(ToSeq(mults))))
    # The j-th merged factor is the product of EXACTLY the contributions whose
    # multiplicity is the j-th distinct multiplicity -- the deep per-group product
    # fold over the whole contribution sequence. Pins the merged factor value
    # (not just which multiplicities are reported) to the input group product.
    Ensures(Forall(int, lambda j: (
        Implies(0 <= j and j < len(Result()),
                Result()[j] == prod_k(ToSeq(factors), ToSeq(mults),
                                      dedup(ToSeq(mults))[j], len(mults))))))
    # post-conditions-end
    # impl-start
    # PRE-PATCH skeleton: the report is returned WITHOUT consolidating by
    # multiplicity -- every contribution is kept as its own entry, so a
    # multiplicity shared by several factors yields several entries (each carrying
    # that factor alone) instead of one merged product entry. This mirrors the
    # pre-fix code, which appends every contribution and returns them unchanged.
    # It FAILS the postcondition `len(Result()) == len(dedup(mults))` (too many
    # entries) and the per-group product clause (each kept factor is the lone
    # contribution, not the product) whenever a multiplicity repeats (G-DIFF).
    ms = ToSeq(mults)  # type: PSeq[int]
    fs = ToSeq(factors)  # type: PSeq[int]
    out = []  # type: List[int]
    i = 0
    while i < len(factors):
        # invariants-start
        Invariant(Acc(list_pred(factors), 1 / 2))
        Invariant(Acc(list_pred(mults), 1 / 2))
        Invariant(len(factors) == len(mults))
        Invariant(0 <= i and i <= len(factors))
        Invariant(Acc(list_pred(out)))
        Invariant(fs == ToSeq(factors))
        Invariant(ms == ToSeq(mults))
        Invariant(ToSeq(out) == fs.take(i))
        # This loop consumes the caller's obligation on the strictly decreasing,
        # bounded-below measure len(factors) - i: `i` rises by exactly one per
        # pass and the guard keeps i < len(factors), so the remaining-iteration
        # bound falls by one and stays >= 1 (`factors` is only read, so
        # len(factors) is fixed across the loop).
        Invariant(MustTerminate(len(factors) - i + 1))
        # invariants-end
        f = factors[i]  # type: int
        Assert(fs.take(i + 1) == fs.take(i) + PSeq(f))
        out = out + [f]
        i = i + 1
    Assert(fs.take(len(factors)) == fs)
    return out
    # impl-end
