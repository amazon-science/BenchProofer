"""Twin-artifact model for django__django-13112.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A model reference is given as text. When the text contains a separator dot,
  it names a model qualified by an application label: everything before the
  first dot is the application label, everything after it is the model name.
  The normalized reference preserves the application label's letter case
  exactly as written and folds ONLY the model-name portion to lower case; the
  separator dot is retained in place. When the text contains no separator dot
  it is a bare model name and is folded to lower case in its entirety.

  Letter-case folding here is the ASCII lower-casing of identifier text: each
  upper-case ASCII letter (U+0041..U+005A) maps to the corresponding lower-case
  letter (code point + 32); every other code point is left unchanged.

Strings are modelled as `List[int]` of Unicode code points (Nagini bans `str`
indexing); the specification is carried by the pure sequence theory `PSeq[int]`.
The whole transformation is modelled DEEPLY (spelled out as verified pure folds
over the code-point sequence); there is no consumed axiom. The ASCII
lower-casing fold is validated equal to the real `str.lower()` on identifier
text out-of-band by axiom_check.py (G-AX) as an A-reference.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# (none) — the transformation is modelled deeply; no callee is axiomatized.
# axioms-end


# pure-start
@Pure
def lower_cp(c: int) -> int:
    """ASCII lower-casing of a single code point: an upper-case ASCII letter
    (U+0041..U+005A) maps to + 32; every other code point is unchanged."""
    if 65 <= c and c <= 90:
        return c + 32
    return c


@Pure
def first_dot(s: PSeq[int]) -> int:
    """Index of the first separator dot (U+002E) in the sequence, or len(s)
    if there is none. Front-recursive."""
    Ensures(0 <= Result() and Result() <= len(s))
    if len(s) == 0:
        return 0
    if s[0] == 46:
        return 0
    return 1 + first_dot(s.drop(1))


@Pure
def normfold(s: PSeq[int], keep: int) -> PSeq[int]:
    """Keep the first `keep` code points verbatim and ASCII-lower-case the rest.
    Front-recursive so a single unfold is available to callers."""
    Requires(keep >= 0)
    Ensures(len(Result()) == len(s))
    if len(s) == 0:
        return PSeq(0).take(0)
    if keep > 0:
        return PSeq(s[0]) + normfold(s.drop(1), keep - 1)
    return PSeq(lower_cp(s[0])) + normfold(s.drop(1), 0)


@Pure
def keep_count(s: PSeq[int]) -> int:
    """Number of leading code points kept verbatim: the application-label
    length when a separator dot is present (so the label keeps its case), else
    zero so a bare name is lower-cased in full."""
    Ensures(0 <= Result() and Result() <= len(s))
    if first_dot(s) < len(s):
        return first_dot(s)
    return 0


@Pure
def normalized(s: PSeq[int]) -> PSeq[int]:
    """The normalized reference: the application label (the prefix before the
    first dot, if any) is kept verbatim and everything from the dot onward is
    lower-cased; with no dot the whole text is lower-cased."""
    return normfold(s, keep_count(s))
# pure-end


def normalize_reference(text: List[int]) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(text), 1 / 2))
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(text), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The result is exactly the normalized reference of the input.
    Ensures(ToSeq(Result()) == normalized(ToSeq(text)))
    # post-conditions-end
    # impl-start
    # PRE-PATCH (buggy): the reference is treated as a single bare name and
    # lower-cased in its entirety, with no separator-dot handling — so a
    # qualifying application label is wrongly folded to lower case too.
    s = ToSeq(text)
    keep = 0
    result = []  # type: List[int]
    i = len(text)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(text), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(s == ToSeq(text))
        Invariant(0 <= keep and keep <= len(s))
        Invariant(0 <= i and i <= len(text))
        Invariant(ToSeq(result) == normfold(s.drop(i), keep - i if keep - i > 0 else 0))
        Invariant(MustTerminate(i + 1))
        # invariants-end
        c = text[i - 1]
        Assert(s.drop(i - 1)[0] == c)
        Assert(s.drop(i - 1).drop(1) == s.drop(i))
        Assert(normfold(s.drop(i - 1), keep - (i - 1) if keep - (i - 1) > 0 else 0) ==
               PSeq(lower_cp(c)) + normfold(s.drop(i), keep - i if keep - i > 0 else 0))
        result = [lower_cp(c)] + result
        i = i - 1
    Assert(s.drop(0) == s)
    return result
    # impl-end
