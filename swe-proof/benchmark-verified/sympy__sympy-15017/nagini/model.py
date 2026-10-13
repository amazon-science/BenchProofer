"""Twin-artifact model for sympy__sympy-15017.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A multidimensional array is described by its shape: a finite sequence of
  axis lengths `shape[0], shape[1], ..., shape[k-1]` (each a non-negative
  integer dimension count). The number of stored elements of the array — the
  value reported as its length — is the PRODUCT of the axis lengths over every
  axis of the shape:

      element_count = shape[0] * shape[1] * ... * shape[k-1]

  The product is taken with the empty-product convention: a shape with NO axes
  (the rank-zero / scalar case, an empty sequence) has element count ONE, not
  zero, because a scalar holds exactly one element (its single stored value).
  In particular the count is the neutral multiplicative element 1 when the
  shape is empty, and the running product of the lengths otherwise; a shape
  containing a zero-length axis yields count zero.

The axis lengths are modelled as `int`; which integers enter the product and
the empty-shape convention are precision-independent (refinement.md R0). The
shape is a `List[int]`; the specification is carried by `PSeq[int]` via
`ToSeq`. The product is spelled out deeply as a prefix-recursive fold whose
base case (no axes) is 1.

The count is computed by ONE bounded pass over the finitely many axes — the
real operation (`functools.reduce` over a finite tuple) always ANSWERS. Nagini
verifies partial correctness by default, so without a total-correctness
obligation a diverging implementation (bare self-recursion, an endless loop)
would satisfy every `Ensures` vacuously; the obligation is carried as
`MustTerminate` in the precondition and consumed by the loop with a strictly
decreasing, bounded-below measure. Markers (machine-parsed) delimit the spec /
proof / impl regions; provenance binding to the repository is in mapping.md.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# (no axiomatized callees: the changed operation — the running product of the
# axis lengths with empty-product == 1 — is modelled deeply in the pure region
# below, not behind an opaque axiom.)
# axioms-end


# pure-start
@Pure
def axis_count(shape: PSeq[int], k: int) -> int:
    """The element count contributed by the first `k` axes `0 <= i < k`: the
    running product of their lengths. Prefix-recursive (extends by one axis per
    step) so the multiplication loop's invariant can track `acc ==
    axis_count(shape, i)`. The base case — zero axes — is the empty product 1,
    which is exactly the rank-zero (scalar) element count."""
    Requires(0 <= k and k <= len(shape))
    if k == 0:
        return 1
    return axis_count(shape, k - 1) * shape[k - 1]


@Pure
def lemma_axis_count_unfold(shape: PSeq[int], k: int) -> bool:
    """The prefix-recursion equation of `axis_count`, exposed for callers (its
    body unfolded once)."""
    Requires(0 < k and k <= len(shape))
    Ensures(Result())
    Ensures(axis_count(shape, k) == axis_count(shape, k - 1) * shape[k - 1])
    return True
# pure-end


def array_element_count(shape: List[int]) -> int:
    # pre-conditions-start
    Requires(Acc(list_pred(shape), 1 / 2))
    # Total-correctness obligation: the count must ANSWER. The real operation
    # is one bounded fold over the finitely many axes (`reduce(mul, shape, 1)`)
    # and always returns; without this a diverging impl (bare self-recursion,
    # endless loop) satisfies the Ensures vacuously. Measure 2: the impl may
    # invoke the pure helpers but may NOT re-invoke this routine itself.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(shape), 1 / 2))
    # The element count is the product of the axis lengths over EVERY axis,
    # taken with the empty-product convention: a shape with no axes (rank zero /
    # scalar) has count 1, never 0; otherwise the running product of the lengths.
    Ensures(Result() == axis_count(ToSeq(shape), len(shape)))
    # At the rank-zero boundary: a shape with no axes counts exactly one
    # element (the single scalar value), not zero.
    Ensures(Implies(len(shape) == 0, Result() == 1))
    # post-conditions-end
    # impl-start
    acc = 1
    i = 0
    while i < len(shape):
        # invariants-start
        Invariant(Acc(list_pred(shape), 1 / 2))
        Invariant(0 <= i and i <= len(shape))
        Invariant(acc == axis_count(ToSeq(shape), i))
        # The loop consumes the caller's termination obligation with the
        # strictly decreasing, bounded-below measure len(shape) - i + 1,
        # discharging MustTerminate(2) from the precondition.
        Invariant(MustTerminate(len(shape) - i + 1))
        # invariants-end
        Assert(lemma_axis_count_unfold(ToSeq(shape), i + 1))
        acc = acc * shape[i]
        i = i + 1
    Assert(i == len(shape))
    return acc
    # impl-end
