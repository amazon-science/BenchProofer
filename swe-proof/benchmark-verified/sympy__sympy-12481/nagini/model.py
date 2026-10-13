"""Twin-artifact model for sympy__sympy-12481.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A finite arrangement is described in cyclic form by a sequence of cycles
  over the points 0..n-1. The arrangement these cycles denote is their
  composition applied in LEFT-TO-RIGHT order: the first cycle acts first, the
  next acts on that outcome, and so on. The points NOT named keep their place.

  This composition is well defined for ANY collection of cycles, including
  cycles that share points (non-disjoint cycles): two cycles that touch a
  common point compose into a single arrangement just as disjoint ones do, and
  the resulting arrangement is still a genuine one-to-one rearrangement of
  0..n-1. There is therefore no input of two cycles for which the construction
  is undefined; every such input yields a rearrangement.

  This module specifies the building of the two-line "array form": position i
  of the result is the point that 0..n-1's i-th point is sent to after both
  cycles have acted in order. The smallest two-element cycles (point swaps)
  carry the whole content of the composition, so the construction is modelled
  over a pair of point-swaps `(a b)` then `(c d)` acting on the n points.

Each cycle here is a two-element swap on integer points; the carrier is the
array form as a `List[int]`, and the specification is phrased over `PSeq[int]`
of points via `ToSeq`. Strings are not involved.

The whole computation is modelled DEEPLY (the per-point swap is spelled out as
a verified loop, not hidden behind an axiom); its equality to the real cycle
composition is checked out-of-band by axiom_check.py (G-AX). There is no
consumed axiom.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# (none) — the composition is modelled deeply; no callee is axiomatized.
# axioms-end


# pure-start
@Pure
def swap_val(x: int, a: int, b: int) -> int:
    """Image of point x under the swap (a b): a and b trade places, every
    other point keeps its value."""
    if x == a:
        return b
    if x == b:
        return a
    return x


# pure-end


def compose_cycles(n: int, a: int, b: int, c: int, d: int) -> List[int]:
    """Array form of the composition of the swap (a b) then the swap (c d) over
    the n points 0..n-1, applied left to right."""
    # pre-conditions-start
    Requires(n >= 1)
    Requires(0 <= a and a < n)
    Requires(0 <= b and b < n)
    Requires(0 <= c and c < n)
    Requires(0 <= d and d < n)
    # Each cycle names two DISTINCT points: a point may not appear twice within
    # one cycle.  The two cycles MAY share a point with each other (that is the
    # non-disjoint case this construction must accept); only within-cycle
    # repetition is excluded.
    Requires(a != b)
    Requires(c != d)
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(Result())))
    Ensures(len(Result()) == n)
    # Position i holds the point that i is sent to after (a b) then (c d) act,
    # i.e. the left-to-right composition.  This is defined for EVERY (a,b,c,d),
    # disjoint or not: there is no rejected input.
    Ensures(Forall(int, lambda i: (Implies(0 <= i and i < n,
                   ToSeq(Result())[i] == swap_val(swap_val(i, a, b), c, d)),
                   [[ToSeq(Result())[i]]])))
    # The result is a genuine rearrangement: every position holds a point in
    # range, so the clause above cannot be met by a degenerate
    # (e.g. rejection-sentinel) array.
    Ensures(Forall(int, lambda i: (Implies(0 <= i and i < n,
                   0 <= ToSeq(Result())[i] and ToSeq(Result())[i] < n),
                   [[ToSeq(Result())[i]]])))
    # post-conditions-end
    # impl-start
    # Build the identity array 0..n-1 (the points in their original order).
    result = []  # type: List[int]
    j = 0
    while j < n:
        # invariants-start
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= j and j <= n)
        Invariant(len(result) == j)
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < j,
                       ToSeq(result)[k] == k), [[ToSeq(result)[k]]])))
        Invariant(MustTerminate(n - j + 1))
        # invariants-end
        old_seq = ToSeq(result)  # type: PSeq[int]
        result.append(j)
        Assert(ToSeq(result) == old_seq + PSeq(j))
        Assert(Forall(int, lambda k: (Implies(0 <= k and k < j,
                      ToSeq(result)[k] == old_seq[k]), [[ToSeq(result)[k]]])))
        Assert(ToSeq(result)[j] == j)
        j = j + 1
    # Apply the first swap (a b) point-wise, then the second swap (c d).
    i = 0
    while i < n:
        # invariants-start
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= n)
        Invariant(len(result) == n)
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
                       ToSeq(result)[k] == swap_val(k, a, b)),
                       [[ToSeq(result)[k]]])))
        Invariant(Forall(int, lambda k: (Implies(i <= k and k < n,
                       ToSeq(result)[k] == k), [[ToSeq(result)[k]]])))
        Invariant(MustTerminate(n - i + 1))
        # invariants-end
        prev = ToSeq(result)  # type: PSeq[int]
        result[i] = swap_val(i, a, b)
        Assert(ToSeq(result) == prev.update(i, swap_val(i, a, b)))
        Assert(Forall(int, lambda k: (Implies(0 <= k and k < n and k != i,
                      ToSeq(result)[k] == prev[k]), [[ToSeq(result)[k]]])))
        Assert(ToSeq(result)[i] == swap_val(i, a, b))
        i = i + 1
    i = 0
    while i < n:
        # invariants-start
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= n)
        Invariant(len(result) == n)
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
                       ToSeq(result)[k] == swap_val(swap_val(k, a, b), c, d)),
                       [[ToSeq(result)[k]]])))
        Invariant(Forall(int, lambda k: (Implies(i <= k and k < n,
                       ToSeq(result)[k] == swap_val(k, a, b)),
                       [[ToSeq(result)[k]]])))
        Invariant(MustTerminate(n - i + 1))
        # invariants-end
        prev2 = ToSeq(result)  # type: PSeq[int]
        Assert(ToSeq(result)[i] == swap_val(i, a, b))
        Assert(result[i] == swap_val(i, a, b))
        new_val = swap_val(result[i], c, d)  # type: int
        Assert(new_val == swap_val(swap_val(i, a, b), c, d))
        result[i] = new_val
        Assert(ToSeq(result) == prev2.update(i, new_val))
        Assert(Forall(int, lambda k: (Implies(0 <= k and k < n and k != i,
                      ToSeq(result)[k] == prev2[k]), [[ToSeq(result)[k]]])))
        Assert(ToSeq(result)[i] == swap_val(swap_val(i, a, b), c, d))
        i = i + 1
    return result
    # impl-end
