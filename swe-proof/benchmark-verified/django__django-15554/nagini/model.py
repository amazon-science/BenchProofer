"""Twin-artifact model for django__django-15554.

Behaviour under specification (stated as desired behaviour, not as an edit):

A query maintains a registry of relation-join descriptors. Each descriptor has
a *base relation identity* (which underlying relation and connection it joins)
and an optional *refinement tag* (an extra per-join filtering refinement; tag 0
means "no refinement", a positive tag denotes a specific refinement). When a new
join descriptor must be installed, the registry first looks for an existing slot
it may reuse:

  - In the default mode the candidate is permitted to reuse a slot only when
    that slot matches the new descriptor on BOTH its base relation identity AND
    its refinement tag. Two descriptors that share the same base relation but
    carry DIFFERENT refinement tags are therefore NOT collapsed onto one slot:
    the second one is installed into a fresh slot of its own.

  - In the constrained mode the candidate may reuse only a slot drawn from an
    explicitly supplied reuse set, and the match is taken on the base relation
    identity alone (the refinement is supplied by the constrained caller).

If a reusable slot exists the existing slot is returned; otherwise a fresh slot
is appended and its index returned. The function reports whether a fresh slot
was created — the observable consequence the registry guarantees.

The decisive property: with two same-base, distinct-refinement descriptors and
default reuse, installing the second must create a NEW slot rather than reusing
the first — so distinct refinements of one relation are preserved, not merged.

The registry is modelled with parallel `List[int]` arrays (base identity and
refinement tag of each slot) plus the reuse set as a `List[bool]` mask and an
"all reusable" flag (the unconstrained case). Marker regions delimit the spec /
proof / impl.
"""
from typing import List, Optional
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# (no axioms: the modelled operation is integer/equality comparison over the
#  slot registry, fully expressible in Nagini; no opaque callee is consumed.)
# axioms-end


# pure-start
@Pure
def reusable(i: int, n: int, reuse_all: bool, reuse_mask: List[bool]) -> bool:
    """A slot index i is reuse-eligible if all slots are reusable (the
    unconstrained case) or i is flagged in the supplied reuse mask."""
    Requires(Acc(list_pred(reuse_mask), 1 / 8))
    Requires(0 <= i and i < n and n == len(reuse_mask))
    return reuse_all or reuse_mask[i]


@Pure
def matches_default(i: int, n: int, jb: int, jf: int,
                    base: List[int], frel: List[int]) -> bool:
    """The default-mode match predicate: slot i matches the incoming
    descriptor (jb, jf) on BOTH the base relation identity AND the refinement
    tag."""
    Requires(Acc(list_pred(base), 1 / 8))
    Requires(Acc(list_pred(frel), 1 / 8))
    Requires(0 <= i and i < n and n == len(base) and n == len(frel))
    return base[i] == jb and frel[i] == jf


@Pure
def matches_constrained(i: int, n: int, jb: int,
                        base: List[int]) -> bool:
    """The constrained-mode match predicate: slot i matches on the base
    relation identity alone."""
    Requires(Acc(list_pred(base), 1 / 8))
    Requires(0 <= i and i < n and n == len(base))
    return base[i] == jb


@Pure
def no_eligible_match(base: List[int], frel: List[int],
                      reuse_all: bool, reuse_mask: List[bool],
                      jb: int, jf: int, constrained: bool) -> bool:
    """True iff NO reuse-eligible slot matches the incoming descriptor under
    the active match predicate — the condition that forces a fresh slot."""
    Requires(Acc(list_pred(base), 1 / 8))
    Requires(Acc(list_pred(frel), 1 / 8))
    Requires(Acc(list_pred(reuse_mask), 1 / 8))
    Requires(len(base) == len(frel) and len(base) == len(reuse_mask))
    if constrained:
        return Forall(int, lambda k: (
            Implies(0 <= k and k < len(base),
                    not (reuse_mask[k]
                         and matches_constrained(k, len(base), jb, base)))))
    return Forall(int, lambda k: (
        Implies(0 <= k and k < len(base),
                not (reusable(k, len(base), reuse_all, reuse_mask)
                     and matches_default(k, len(base), jb, jf, base, frel)))))
# pure-end


def install_join(base: List[int], frel: List[int],
                 reuse_all: bool, reuse_mask: List[bool],
                 jb: int, jf: int,
                 constrained: bool) -> bool:
    # pre-conditions-start
    Requires(Acc(list_pred(base), 1 / 2))
    Requires(Acc(list_pred(frel), 1 / 2))
    Requires(Acc(list_pred(reuse_mask), 1 / 2))
    # registry arrays are aligned; the reuse mask covers every slot.
    Requires(len(base) == len(frel))
    Requires(len(base) == len(reuse_mask))
    # in constrained mode reuse is genuinely constrained (reuse set supplied).
    Requires(Implies(constrained, not reuse_all))
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(base), 1 / 2))
    Ensures(Acc(list_pred(frel), 1 / 2))
    Ensures(Acc(list_pred(reuse_mask), 1 / 2))
    # The registry arrays are read-only here (the caller appends a fresh slot
    # separately when Result() reports a new slot is needed).
    Ensures(ToSeq(base) == Old(ToSeq(base)))
    Ensures(ToSeq(frel) == Old(ToSeq(frel)))
    # Registry arrays stay aligned (read-only here).
    Ensures(len(base) == len(frel))
    Ensures(len(base) == len(reuse_mask))
    # Result() is True iff a FRESH slot must be created, i.e. NO reuse-eligible
    # slot matches the incoming descriptor under the active match predicate.
    Ensures(Result() == no_eligible_match(
        base, frel, reuse_all, reuse_mask, jb, jf, constrained))
    # post-conditions-end
    # impl-start
    n = len(base)
    found = False
    i = 0
    while i < n:
        # invariants-start
        Invariant(Acc(list_pred(base), 1 / 2))
        Invariant(Acc(list_pred(frel), 1 / 2))
        Invariant(Acc(list_pred(reuse_mask), 1 / 2))
        Invariant(len(base) == n and len(frel) == n and len(reuse_mask) == n)
        Invariant(0 <= i and i <= n)
        Invariant(Implies(constrained, not reuse_all))
        Invariant(ToSeq(base) == Old(ToSeq(base)))
        Invariant(ToSeq(frel) == Old(ToSeq(frel)))
        # While no match has been seen, no eligible slot among 0..i matches.
        Invariant(Implies(
            not found,
            Implies(not constrained, Forall(int, lambda k: (
                Implies(0 <= k and k < i,
                        not (reusable(k, n, reuse_all, reuse_mask)
                             and matches_default(k, n, jb, jf, base, frel)))
            )))))
        Invariant(Implies(
            not found,
            Implies(constrained, Forall(int, lambda k: (
                Implies(0 <= k and k < i,
                        not (reuse_mask[k]
                             and matches_constrained(k, n, jb, base)))
            )))))
        # Once a match has been seen, an eligible matching slot provably exists.
        Invariant(Implies(
            found,
            not no_eligible_match(
                base, frel, reuse_all, reuse_mask, jb, jf, constrained)))
        Invariant(MustTerminate(n - i + 1))
        # invariants-end
        if constrained:
            if reuse_mask[i] and matches_constrained(i, n, jb, base):
                found = True
        else:
            if reusable(i, n, reuse_all, reuse_mask) and \
                    matches_default(i, n, jb, jf, base, frel):
                found = True
        i = i + 1
    return not found
    # impl-end
