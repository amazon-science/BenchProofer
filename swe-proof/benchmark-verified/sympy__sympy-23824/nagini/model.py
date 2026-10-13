"""Twin-artifact model for sympy__sympy-23824.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A product of gamma matrices may begin with a run of leading uncontracted
  ("free") factors before the first contracted factor. The simplification
  algorithm sets those leading factors aside while it rewrites the contracted
  part, then must restore them in front of each resulting term. Restoring them
  must PRESERVE their original left-to-right order: a result term is the leading
  run, in its original order, followed by the term the core rewrite produced.

  Concretely, given the leading run `leading = [g_0, g_1, ..., g_{k-1}]` (the
  factors that precede the first contracted factor, in their original order) and
  a core-result term `tail`, the restored term is the concatenation

      leading[0], leading[1], ..., leading[k-1],  tail[0], tail[1], ...

  i.e. `leading ++ tail`, with the leading factors in the SAME left-to-right
  order in which they appeared in the input.

Gamma-matrix factors are identified by their integer index labels, so a term is
modelled as a `List[int]` (Nagini bans `str` indexing; the same `List` carrier
is the natural model for the algorithm's list-of-index-labels). The
specification is carried by `PSeq[int]` via `ToSeq`, and `+` is sequence
concatenation.

The two read-only inputs (`leading`, `tail`) carry fractional permission; the
operation builds and returns a fresh list. No callee is axiomatized: the entire
modelled operation is sequence concatenation, spelled out deeply in the impl.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# (no axioms: the modelled operation is the order-preserving prepend of the
# leading run onto a core-result term — pure sequence concatenation, spelled
# out deeply in the impl region. The factors set aside / the core-result term
# are read-only inputs, an R-refinement of the unchanged surrounding algorithm.)
# axioms-end


# pure-start
# (no pure helpers: the specification is stated directly over PSeq[int]
# concatenation via ToSeq.)
# pure-end


def restore_leading(leading: List[int], tail: List[int]) -> List[int]:
    """Restore the leading run in front of a core-result term, preserving the
    leading factors' original left-to-right order: `leading ++ tail`."""
    # pre-conditions-start
    Requires(Acc(list_pred(leading), 1 / 2))
    Requires(Acc(list_pred(tail), 1 / 2))
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(leading), 1 / 2))
    Ensures(Acc(list_pred(tail), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The result is the leading run, in its original order, followed by `tail`.
    Ensures(ToSeq(Result()) == ToSeq(leading) + ToSeq(tail))
    # post-conditions-end
    # impl-start
    result = []  # type: List[int]
    i = 0
    while i < len(leading):
        # invariants-start
        Invariant(Acc(list_pred(leading), 1 / 2))
        Invariant(Acc(list_pred(tail), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(leading))
        Invariant(ToSeq(result) == ToSeq(leading).take(i))
        Invariant(MustTerminate(len(leading) - i + 1))
        # invariants-end
        result.append(leading[i])
        i = i + 1
    j = 0
    while j < len(tail):
        # invariants-start
        Invariant(Acc(list_pred(leading), 1 / 2))
        Invariant(Acc(list_pred(tail), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= j and j <= len(tail))
        Invariant(ToSeq(result) == ToSeq(leading) + ToSeq(tail).take(j))
        Invariant(MustTerminate(len(tail) - j + 1))
        # invariants-end
        result.append(tail[j])
        j = j + 1
    return result
    # impl-end
