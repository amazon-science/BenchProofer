"""Twin-artifact model for scikit-learn__scikit-learn-15100.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A text-normalisation routine maps an input string of Unicode code points to
  the string obtained by (1) decomposing it into its canonical decomposed form
  and then (2) dropping every combining mark. The result therefore contains no
  combining marks, regardless of the form the input arrived in: two inputs that
  are canonically equivalent (e.g. a precomposed accented letter and the same
  letter followed by a separate combining mark) yield the same output. In
  particular an input that is ALREADY in decomposed form but still carries
  combining marks must have those marks removed, not be returned untouched.

  When the input is provably already in final form (it carries no combining
  marks and is canonically stable), it may be returned unchanged via a
  behaviour-preserving fast path -- the same result the general transform
  would produce, not a different one.

Strings are modelled as `List[int]` of Unicode code points (Nagini bans `str`
indexing); the specification is carried by `PSeq[int]`.

Two unchanged library callees are axiomatized: the canonical decomposition
(`nfkd`, used to obtain the decomposed form) and the combining-mark classifier
(`is_combining`). The mark-dropping selection itself is the unchanged operation
and is modelled DEEPLY as a verified order-preserving filter (`strip_combining`)
over the decomposed code points. The axioms' soundness against the real callees
is checked out-of-band by axiom_check.py (G-AX).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
@Pure
@ContractOnly
def is_combining(c: int) -> bool:
    """Combining-mark classifier (the unchanged callee), as a pure predicate of
    a single code point: True iff the code point is a combining mark (a mark
    that attaches to a preceding base character). Weakest contract the proof
    needs: a code point below 128 is never a combining mark.
    Provenance + executable soundness check: mapping.md / axiom_check.py.
    """
    Ensures(Implies(c < 128, not Result()))


@Pure
@ContractOnly
def nfkd(s: PSeq[int]) -> PSeq[int]:
    """Canonical decomposition of a code-point sequence (the unchanged callee),
    as a pure function. Weakest contract the proof needs: a sequence consisting
    solely of code points below 128 is canonically stable, i.e. returned unchanged.
    Provenance + executable soundness check: mapping.md / axiom_check.py.
    """
    Ensures(Implies(Forall(int, lambda k: (Implies(0 <= k and k < len(s),
                                                    s[k] < 128))),
                    Result() == s))


@ContractOnly
def decompose(s: List[int]) -> List[int]:
    """Runtime counterpart of `nfkd`: the actual decomposition call, returning
    the decomposed code points as a fresh list. Its observable content is
    `nfkd` of the input (the A-consumed axiom, same callee)."""
    Requires(Acc(list_pred(s), 1 / 2))
    Ensures(Acc(list_pred(s), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    Ensures(ToSeq(Result()) == nfkd(ToSeq(s)))


@ContractOnly
def is_fixed_form_guard(s: List[int]) -> bool:
    """Runtime guard for the unchanged-input fast path: returns whether `s` is
    provably already in its final form, so that returning it unchanged is
    behaviour-preserving. Its truth coincides with the structural property
    `all_ascii(s)` of the input carrier (see below)."""
    Requires(Acc(list_pred(s), 1 / 2))
    Ensures(Acc(list_pred(s), 1 / 2))
    Ensures(Result() == all_ascii(ToSeq(s)))
# axioms-end


# pure-start
@Pure
def all_ascii(s: PSeq[int]) -> bool:
    """Every code point of the sequence is below 128."""
    return Forall(int, lambda k: (Implies(0 <= k and k < len(s), s[k] < 128)))


@Pure
def strip_combining(s: PSeq[int]) -> PSeq[int]:
    """The mark-dropping selection: the order-preserving sub-sequence of `s`
    obtained by removing every combining mark. Front-recursive so a single
    unfold is available per code point."""
    if len(s) == 0:
        return PSeq(0).take(0)
    if is_combining(s[0]):
        return strip_combining(s.drop(1))
    return PSeq(s[0]) + strip_combining(s.drop(1))


def lemma_ascii_is_fixed_point(s: PSeq[int]) -> None:
    """Proof lemma: a sequence whose code points are all below 128 has no
    combining marks, so dropping combining marks leaves it unchanged. Proven by
    front-recursion; the inductive step uses the `is_combining` axiom
    (code point < 128 ⇒ not combining)."""
    Requires(all_ascii(s))
    Ensures(strip_combining(s) == s)
    if len(s) > 0:
        Assert(s[0] < 128)
        Assert(Forall(int, lambda k: (Implies(0 <= k and k < len(s.drop(1)),
                                               s.drop(1)[k] == s[k + 1]))))
        Assert(all_ascii(s.drop(1)))
        lemma_ascii_is_fixed_point(s.drop(1))
        Assert(PSeq(s[0]) + s.drop(1) == s)
# pure-end


def strip_marks(s: List[int]) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(s), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(s), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The result is the canonical decomposition of the input with every
    # combining mark removed -- independent of the form the input arrived in.
    Ensures(ToSeq(Result()) == strip_combining(nfkd(ToSeq(s))))
    # post-conditions-end
    # impl-start
    in_fixed_form = is_fixed_form_guard(s)
    if in_fixed_form:
        # Already-final-form input: canonically stable and mark-free, so its
        # decomposition carries no combining marks and equals the input -- the
        # fast path returns the input string unchanged (modelled as its
        # code-point copy, str being immutable: returning s == returning a
        # copy of s).
        Assert(all_ascii(ToSeq(s)))
        out = []  # type: List[int]
        j = 0
        while j < len(s):
            # invariants-start
            Invariant(Acc(list_pred(s), 1 / 2))
            Invariant(Acc(list_pred(out)))
            Invariant(0 <= j and j <= len(s))
            Invariant(all_ascii(ToSeq(s)))
            Invariant(ToSeq(out) == ToSeq(s).take(j))
            # invariants-end
            Assert(ToSeq(s).take(j + 1) == ToSeq(s).take(j) + PSeq(s[j]))
            out = out + [s[j]]
            j = j + 1
        Assert(ToSeq(s).take(len(s)) == ToSeq(s))
        Assert(all_ascii(ToSeq(s)))
        lemma_ascii_is_fixed_point(ToSeq(s))
        return out
    normalized = decompose(s)
    result = []  # type: List[int]
    i = len(normalized)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(s), 1 / 2))
        Invariant(Acc(list_pred(normalized)))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(normalized))
        Invariant(ToSeq(normalized) == nfkd(ToSeq(s)))
        Invariant(ToSeq(result) == strip_combining(ToSeq(normalized).drop(i)))
        # invariants-end
        c = normalized[i - 1]
        Assert(ToSeq(normalized).drop(i - 1)[0] == c)
        Assert(ToSeq(normalized).drop(i - 1).drop(1) == ToSeq(normalized).drop(i))
        if not is_combining(c):
            result = [c] + result
        i = i - 1
    return result
    # impl-end
