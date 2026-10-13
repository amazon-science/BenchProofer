"""Twin-artifact model for sympy__sympy-11618.

Behaviour under specification (stated as desired behaviour, not as an edit):

  Two points are described by their coordinate vectors `u` (this point) and `v`
  (the other point), each a finite sequence of scalar coordinates over a common
  axis indexing `0, 1, 2, ...`. The two vectors may have DIFFERENT lengths,
  i.e. live in spaces of different dimension. A point of dimension `d` is
  understood to occupy the larger ambient space by treating every axis beyond
  its own as carrying the coordinate zero.

  The Euclidean distance between the points is the non-negative real number
  whose square is the sum, over EVERY axis `i` of the larger ambient dimension
  `n = max(len(u), len(v))`, of the squared coordinate difference on that axis:

      squared = sum_{i=0}^{n-1} (coord(u, i) - coord(v, i))**2

  where `coord(s, i)` is the i-th coordinate of `s` when `i < len(s)` and zero
  otherwise. In particular, when the two vectors have different lengths the
  axes present only in the longer vector still contribute `(coordinate - 0)**2`
  to the sum; they are NOT dropped. The returned distance is the square root of
  that sum, where the square root is a single, deterministic, order-respecting
  function of its non-negative argument (so two equal sums give one distance and
  a larger sum gives at least as large a distance).

Scalar coordinates are modelled as `int`: the contract concerns WHICH squared
differences enter the sum (the set of axes summed over and the zero-padding of
the shorter vector), which is precision-independent (refinement.md R0). Vectors
are `List[int]`; the specification is carried by `PSeq[int]` via `ToSeq`. The
square root is an opaque, deterministic, monotone callee (axiomatized: equal
arguments give equal results, so the distance is a function of the EXACT
padded sum). Markers (machine-parsed) delimit the spec / proof / impl regions;
provenance binding to the repository is in mapping.md.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
@Pure
@ContractOnly
def root(x: int) -> int:
    """The (unchanged) square-root applied to the squared distance: a single,
    deterministic function of its non-negative argument. The contract encodes
    only what the proof consumes — that it is a deterministic function (equal
    arguments give equal results, automatic for a pure function), so the
    distance is a function of the EXACT padded sum and never an exact value.
    Provenance and the executable soundness check are in mapping.md §3 /
    axiom_check.py (G-AX).
    """
    Requires(x >= 0)
    Ensures(Result() >= 0)
# axioms-end


# pure-start
@Pure
def coord(s: PSeq[int], i: int) -> int:
    """The coordinate of vector `s` on axis `i`: the stored value when the axis
    is within the vector's own dimension, and zero on every axis beyond it
    (the zero-padding of the shorter vector into the larger ambient space)."""
    Requires(i >= 0)
    if i < len(s):
        return s[i]
    return 0


@Pure
def term(u: PSeq[int], v: PSeq[int], i: int) -> int:
    """The squared coordinate difference contributed by axis `i`."""
    Requires(i >= 0)
    return (coord(u, i) - coord(v, i)) * (coord(u, i) - coord(v, i))


@Pure
def psum(u: PSeq[int], v: PSeq[int], k: int) -> int:
    """The sum of the squared coordinate differences over the first `k` axes
    `0 <= i < k`. Prefix-recursive (extends by one axis per step) so the
    accumulation loop's invariant tracks `acc == psum(u, v, i)`. Non-negative,
    since every summand is a square."""
    Requires(k >= 0)
    Ensures(Result() >= 0)
    if k == 0:
        return 0
    return psum(u, v, k - 1) + term(u, v, k - 1)


@Pure
def lemma_psum_unfold(u: PSeq[int], v: PSeq[int], k: int) -> bool:
    """The prefix-recursion equation of `psum`, exposed for callers (its body
    unfolded once)."""
    Requires(k > 0)
    Ensures(Result())
    Ensures(psum(u, v, k) == psum(u, v, k - 1) + term(u, v, k - 1))
    return True
# pure-end


def point_distance(u: List[int], v: List[int]) -> int:
    # pre-conditions-start
    Requires(Acc(list_pred(u), 1 / 2))
    Requires(Acc(list_pred(v), 1 / 2))
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(u), 1 / 2))
    Ensures(Acc(list_pred(v), 1 / 2))
    # The distance is the square root of the sum of squared coordinate
    # differences over EVERY axis of the larger ambient dimension, with the
    # shorter vector zero-padded. The axes present only in the longer vector
    # contribute their squared coordinate; they are not dropped.
    Ensures(Result() == root(psum(ToSeq(u), ToSeq(v),
                                  len(u) if len(u) >= len(v) else len(v))))
    # post-conditions-end
    # impl-start
    # PRE-PATCH (buggy) skeleton: the two coordinate streams are walked in
    # lock-step only as far as the SHORTER one reaches; axes present in only the
    # longer vector are dropped (the truncating pairwise zip).
    n = len(u)
    if len(v) < n:
        n = len(v)
    acc = 0
    i = 0
    while i < n:
        # invariants-start
        Invariant(Acc(list_pred(u), 1 / 2))
        Invariant(Acc(list_pred(v), 1 / 2))
        Invariant(0 <= i and i <= n)
        Invariant(n == (len(u) if len(u) <= len(v) else len(v)))
        Invariant(acc == psum(ToSeq(u), ToSeq(v), i))
        Invariant(MustTerminate(n - i + 1))
        # invariants-end
        cu = 0
        if i < len(u):
            cu = u[i]
        cv = 0
        if i < len(v):
            cv = v[i]
        Assert(cu == coord(ToSeq(u), i))
        Assert(cv == coord(ToSeq(v), i))
        Assert((cu - cv) * (cu - cv) == term(ToSeq(u), ToSeq(v), i))
        Assert(lemma_psum_unfold(ToSeq(u), ToSeq(v), i + 1))
        acc = acc + (cu - cv) * (cu - cv)
        i = i + 1
    Assert(i == n)
    total = psum(ToSeq(u), ToSeq(v), len(u) if len(u) <= len(v) else len(v))
    Assert(acc == total)
    return root(total)
    # impl-end
