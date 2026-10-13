"""Twin-artifact model for sphinx-doc__sphinx-7440.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A glossary term is registered under a cross-reference key derived from the
  term's text. The registration key must preserve the term text EXACTLY as
  written, character for character, including the letter case the author chose.
  Two terms whose texts differ only in case are therefore distinct keys and do
  not collide; the key reported back for a term is the original text itself.

  In particular the registration is NOT case-folding: an author who writes a
  term with an upper-case letter has that upper-case letter retained in the
  registered key, rather than being silently rewritten to its lower-case form.

Text is modelled as `List[int]` of Unicode code points (Nagini bans `str`
indexing); the specification is carried over `PSeq[int]`. The contrast behaviour
that the registration must NOT perform — ASCII case folding (each code point in
the inclusive range 65..90 shifted by +32, every other code point unchanged) —
is modelled deeply as the pure front-recursive fold `casefold`, against which the
identity-preserving registration is differentiated. `casefold` is validated
equal to the real per-character lower-casing out-of-band by axiom_check.py
(G-AX); it is not consumed as an axiom.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# (No axiomatized callees. The registration key is the term text itself —
# computed deeply — and the contrast operation it must NOT apply, ASCII
# case-folding, is also modelled deeply by `casefold` in the pure region. There
# is no @ContractOnly the proof consumes; `casefold` is an A-reference validated
# against the real lower-casing by axiom_check.py / G-AX.)
# axioms-end


# pure-start
@Pure
def fold_cp(c: int) -> int:
    """ASCII case fold of a single code point: an upper-case Latin letter
    (code points 65..90, i.e. 'A'..'Z') is shifted by +32 to its lower-case
    form; every other code point is returned unchanged."""
    if 65 <= c and c <= 90:
        return c + 32
    return c


@Pure
def casefold(s: PSeq[int]) -> PSeq[int]:
    """The ASCII case fold of a whole sequence: each code point independently
    mapped by `fold_cp`. Front-recursive so a single unfold is available to a
    matching forward loop. This is the operation the registration must NOT
    apply; the identity-preserving registration differs from it on any input
    carrying an upper-case ASCII letter."""
    if len(s) == 0:
        return PSeq(0).take(0)
    return PSeq(fold_cp(s[0])) + casefold(s.drop(1))
# pure-end


def register_term_name(termtext: List[int]) -> List[int]:
    # pre-conditions-start
    # The source term text is read-only (registration never mutates it):
    # fractional permission, required AND ensured, so no implementation can
    # satisfy a postcondition vacuously by overwriting the input.
    Requires(Acc(list_pred(termtext), 1 / 2))
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(termtext), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The registered key is the term text EXACTLY: same length, same code point
    # at every position — the author's letter case is preserved verbatim.
    Ensures(ToSeq(Result()) == ToSeq(termtext))
    # Equivalently, element-wise: the key never rewrites a character (in
    # particular it never case-folds an upper-case ASCII letter to lower case).
    Ensures(len(Result()) == len(termtext))
    Ensures(Forall(int, lambda k: (Implies(0 <= k and k < len(termtext),
                                           Result()[k] == termtext[k]),
                                   [[Result()[k]]])))
    # post-conditions-end
    # impl-start
    # Build the registration key character by character, copying each code point
    # of the term text unchanged. The loop invariant tracks that the prefix
    # emitted equals the prefix of the term text verbatim.
    result = []  # type: List[int]
    i = 0
    while i < len(termtext):
        # invariants-start
        Invariant(Acc(list_pred(termtext), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(termtext))
        Invariant(ToSeq(result) == ToSeq(termtext).take(i))
        Invariant(MustTerminate(len(termtext) - i + 1))
        # invariants-end
        c = termtext[i]
        Assert(ToSeq(termtext).take(i + 1) == ToSeq(termtext).take(i) + PSeq(c))
        result = result + [c]
        i = i + 1
    Assert(ToSeq(termtext).take(len(termtext)) == ToSeq(termtext))
    return result
    # impl-end
