"""Twin-artifact model for matplotlib__matplotlib-24177.

Behavioural contract (what the operation must guarantee):

  Given a non-empty sequence of numeric values, the operation returns an upper
  bound that is at least as large as EVERY element of the sequence: for all k,
  Result() >= values[k]. Equivalently, the returned bound encloses the whole
  sequence -- no element exceeds it -- and the bound is attained, i.e. it equals
  one of the input values rather than an arbitrary larger number.

The carrier is a sequence of numeric values; it is modelled as `List[int]`
(Nagini bans `str`/array indexing, and the tested behaviour is about WHICH
values are covered, not floating-point precision -- see refinement.md /
mapping.md). The pure sequence theory `PSeq[int]` carries the specification.

One unchanged helper is axiomatized: a sub-selection over the input sequence
whose only guaranteed property is MEMBERSHIP -- every value it yields already
occurs among the input values, and it never yields more values than the input
has. It carries no guarantee about which values it keeps (in particular, no
guarantee that the largest value is among them). Its soundness is checked
out-of-band by axiom_check.py (G-AX).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
@Pure
@ContractOnly
def subsel_len(verts: PSeq[int]) -> int:
    """Number of values a sub-selection over `verts` yields: between zero and
    the full count (a sub-selection never yields more values than the input)."""
    Ensures(0 <= Result() and Result() <= len(verts))


@Pure
@ContractOnly
def subsel_at(verts: PSeq[int], idx: int) -> int:
    """The `idx`-th value of a sub-selection over `verts`. Its ONLY guaranteed
    property (the weakest sound contract) is MEMBERSHIP: every yielded value
    already occurs among the input values -- the result equals `verts[j]` for
    some in-bounds `j`. It carries no promise about which values are kept; in
    particular, no promise that the largest input value is among them.

    Provenance + executable soundness check: mapping.md / axiom_check.py.
    """
    Requires(0 <= idx and idx < subsel_len(verts))
    Ensures(Exists(int, lambda j: (0 <= j and j < len(verts)
                                   and Result() == verts[j])))
# axioms-end


# pure-start
@Pure
def seq_max(s: PSeq[int]) -> int:
    """Largest value over a non-empty sequence. Front-recursive so a single
    unfold is available per loop step (index-recursion does not auto-unfold in
    Nagini 1.2.0)."""
    Requires(len(s) >= 1)
    if len(s) == 1:
        return s[0]
    return _imax(s[0], seq_max(s.drop(1)))


@Pure
def _imax(a: int, b: int) -> int:
    return a if a >= b else b
# pure-end


def lemma_seq_max_dominates(s: PSeq[int]) -> None:
    """The front-recursive maximum dominates every element of the sequence."""
    # pre-conditions-start
    Requires(len(s) >= 1)
    # The proof recurses on the tail, so the obligation must be a MEASURE that
    # shrinks with the sequence: a constant could never be strictly below itself
    # at the recursive site.
    Requires(MustTerminate(len(s)))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Forall(int, lambda k: (Implies(0 <= k and k < len(s),
                                           seq_max(s) >= s[k]))))
    # post-conditions-end
    # invariants-start
    # invariants-end
    # impl-start
    if len(s) > 1:
        lemma_seq_max_dominates(s.drop(1))
        t = s.drop(1)  # type: PSeq[int]
        Assert(seq_max(s) == _imax(s[0], seq_max(t)))
        Assert(seq_max(s) >= seq_max(t))
        Assert(Forall(int, lambda k: (Implies(1 <= k and k < len(s),
                                              s[k] == t[k - 1]))))
    # impl-end


def lemma_seq_max_attained(s: PSeq[int]) -> None:
    """The front-recursive maximum is attained: it equals some element of the
    sequence (tightness -- the bound is one of the inputs, not larger)."""
    # pre-conditions-start
    Requires(len(s) >= 1)
    # As above: the proof recurses on the tail, so the obligation shrinks with
    # the sequence rather than being a constant.
    Requires(MustTerminate(len(s)))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Exists(int, lambda j: (0 <= j and j < len(s)
                                   and seq_max(s) == s[j])))
    # post-conditions-end
    # invariants-start
    # invariants-end
    # impl-start
    if len(s) == 1:
        Assert(seq_max(s) == s[0])
    else:
        t = s.drop(1)  # type: PSeq[int]
        lemma_seq_max_attained(t)
        Assert(seq_max(s) == _imax(s[0], seq_max(t)))
        Assert(Forall(int, lambda k: (Implies(0 <= k and k < len(t),
                                              t[k] == s[k + 1]))))
    # impl-end


def enclosing_upper_bound(verts: List[int]) -> int:
    # pre-conditions-start
    Requires(Acc(list_pred(verts), 1 / 2))
    Requires(len(verts) >= 1)
    # Strictly above the two lemmas' own measure (len of the sequence they are
    # applied to, i.e. len(verts)), which is what lets this method call them.
    Requires(MustTerminate(len(verts) + 1))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(verts), 1 / 2))
    # The result is an upper bound over the whole input: it is at least as large
    # as every element. (Enclosing direction.)
    Ensures(Forall(int, lambda k: (Implies(0 <= k and k < len(verts),
                                           Result() >= verts[k]))))
    # The bound is ATTAINED: it equals one of the input elements, not an
    # arbitrary larger number. (Tightness direction -- excludes any padded
    # over-approximation of the true bound.)
    Ensures(Exists(int, lambda j: (0 <= j and j < len(verts)
                                   and Result() == verts[j])))
    # post-conditions-end
    # impl-start
    lemma_seq_max_dominates(ToSeq(verts))
    best = verts[len(verts) - 1]
    i = len(verts) - 1
    sq = ToSeq(verts)  # type: PSeq[int]
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(verts), 1 / 2))
        Invariant(0 <= i and i < len(verts))
        Invariant(best == seq_max(ToSeq(verts).drop(i)))
        # Carries the element count across the scan, so the enclosing method's
        # own measure is still known once the scan is done and the lemmas below
        # can still be applied.
        Invariant(sq == ToSeq(verts))
        # The scan counts down to 0, so i + 1 stays positive and strictly
        # decreases each step.
        Invariant(MustTerminate(i + 1))
        # invariants-end
        Assert(ToSeq(verts).drop(i - 1)[0] == verts[i - 1])
        Assert(ToSeq(verts).drop(i - 1).drop(1) == ToSeq(verts).drop(i))
        if verts[i - 1] > best:
            best = verts[i - 1]
        i = i - 1
    Assert(i == 0)
    Assert(ToSeq(verts).drop(0) == ToSeq(verts))
    Assert(best == seq_max(ToSeq(verts)))
    lemma_seq_max_dominates(ToSeq(verts))
    lemma_seq_max_attained(ToSeq(verts))
    Assert(Forall(int, lambda k: (Implies(0 <= k and k < len(verts),
                                          seq_max(ToSeq(verts)) >= ToSeq(verts)[k]))))
    Assert(Forall(int, lambda k: (Implies(0 <= k and k < len(verts),
                                          ToSeq(verts)[k] == verts[k]))))
    return best
    # impl-end
