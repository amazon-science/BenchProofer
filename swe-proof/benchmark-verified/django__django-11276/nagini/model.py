"""Twin-artifact model for django__django-11276.

Behaviour under specification (stated as desired behaviour, not as an edit):

  (1) HTML-escaping of arbitrary text for safe inclusion in HTML markup.
      Each of the five HTML-significant code points is replaced by a constant
      entity sequence; every other code point passes through unchanged. The
      ampersand is handled first so that the ampersands inside the emitted
      entity sequences are NOT themselves re-escaped. The apostrophe (U+0027)
      is encoded as the numeric character reference `&#x27;`.

  (2) The community entity decoder used when re-deriving a raw URL from
      already-escaped link text is the exact inverse of the escaper on those
      five entity sequences: a token equal to `&#x27;` decodes back to the
      apostrophe U+0027 (and the legacy `&#39;` form decodes likewise), so the
      escape/decode round trip is the identity on every significant code point.

Strings are modelled as `List[int]` of Unicode code points (Nagini bans `str`
indexing). The pure sequence theory `PSeq[int]` carries the specification.

One stdlib callee is axiomatized (`entity_decode`, the urlize decoder); the
escaper itself is modelled deeply as a verified per-code-point substitution
(`escaped_seq`), whose equality to the real `html.escape` is checked
out-of-band by axiom_check.py (G-AX), not consumed as an axiom.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
@Pure
@ContractOnly
def entity_decode(tok: PSeq[int]) -> PSeq[int]:
    """Stdlib HTML entity decoder (the unchanged community callee), on the
    entity tokens this bundle relies on. Inverse of the escaper on the five
    emitted entities; also decodes the legacy decimal apostrophe `&#39;`.
    Provenance + executable soundness check: mapping.md / axiom_check.py.
    """
    Ensures(Implies(tok == seq_amp(), Result() == PSeq(38)))
    Ensures(Implies(tok == seq_lt(), Result() == PSeq(60)))
    Ensures(Implies(tok == seq_gt(), Result() == PSeq(62)))
    Ensures(Implies(tok == seq_quot(), Result() == PSeq(34)))
    Ensures(Implies(tok == seq_apos_hex(), Result() == PSeq(39)))
    Ensures(Implies(tok == seq_apos_dec(), Result() == PSeq(39)))
# axioms-end


# pure-start
@Pure
def seq_amp() -> PSeq[int]:
    # '&amp;'
    return PSeq(38, 97, 109, 112, 59)


@Pure
def seq_lt() -> PSeq[int]:
    # '&lt;'
    return PSeq(38, 108, 116, 59)


@Pure
def seq_gt() -> PSeq[int]:
    # '&gt;'
    return PSeq(38, 103, 116, 59)


@Pure
def seq_quot() -> PSeq[int]:
    # '&quot;'
    return PSeq(38, 113, 117, 111, 116, 59)


@Pure
def seq_apos_hex() -> PSeq[int]:
    # '&#x27;'  (the apostrophe entity required of the escaper)
    return PSeq(38, 35, 120, 50, 55, 59)


@Pure
def seq_apos_dec() -> PSeq[int]:
    # '&#39;'  (legacy decimal apostrophe entity)
    return PSeq(38, 35, 51, 57, 59)


@Pure
def entity(c: int) -> PSeq[int]:
    """Entity sequence emitted for a single code point: the five significant
    ones expand, every other code point maps to itself."""
    if c == 38:        # '&'
        return seq_amp()
    if c == 60:        # '<'
        return seq_lt()
    if c == 62:        # '>'
        return seq_gt()
    if c == 34:        # '"'
        return seq_quot()
    if c == 39:        # "'"  -> &#x27;
        return seq_apos_hex()
    return PSeq(c)


@Pure
def escaped_seq(s: PSeq[int]) -> PSeq[int]:
    """The escape of a whole sequence: concatenate the per-code-point entity
    sequences. Front-recursive so a single unfold is available to callers."""
    if len(s) == 0:
        return PSeq(0).take(0)
    return entity(s[0]) + escaped_seq(s.drop(1))
# pure-end


def escape_codepoints(text: List[int]) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(text), 1 / 2))
    # The escaped text must actually be delivered: this termination obligation
    # forbids implementations that would satisfy the value postcondition only
    # vacuously by never returning (the per-code-point substitution over a
    # finite input is bounded work).
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(text), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The escaped output is the per-code-point entity substitution.
    Ensures(ToSeq(Result()) == escaped_seq(ToSeq(text)))
    # Escape/decode round trip is the identity on every significant code point,
    # the apostrophe carrying the discriminating `&#x27;` <-> U+0027 mapping.
    Ensures(entity_decode(entity(38)) == PSeq(38))
    Ensures(entity_decode(entity(60)) == PSeq(60))
    Ensures(entity_decode(entity(62)) == PSeq(62))
    Ensures(entity_decode(entity(34)) == PSeq(34))
    Ensures(entity_decode(entity(39)) == PSeq(39))
    # post-conditions-end
    # impl-start
    result = []  # type: List[int]
    i = len(text)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(text), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(text))
        Invariant(ToSeq(result) == escaped_seq(ToSeq(text).drop(i)))
        # The loop consumes the caller's termination obligation with the
        # strictly decreasing, bounded-below measure i.
        Invariant(MustTerminate(i))
        # invariants-end
        c = text[i - 1]
        Assert(ToSeq(text).drop(i - 1)[0] == c)
        Assert(ToSeq(text).drop(i - 1).drop(1) == ToSeq(text).drop(i))
        if c == 38:
            result = [38, 97, 109, 112, 59] + result
        elif c == 60:
            result = [38, 108, 116, 59] + result
        elif c == 62:
            result = [38, 103, 116, 59] + result
        elif c == 34:
            result = [38, 113, 117, 111, 116, 59] + result
        elif c == 39:
            result = [38, 35, 120, 50, 55, 59] + result
        else:
            result = [c] + result
        i = i - 1
    return result
    # impl-end
