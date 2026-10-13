"""Twin-artifact model for django__django-15022.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A keyword search over a list of search terms is performed against the related
  rows reachable from one candidate object. For the candidate there is a finite
  sequence of related rows and a finite sequence of search terms. The relation
  `matches(row, term)` holds when that related row satisfies that search term
  (at least one searched field of the row matches the term).

  The candidate object is RETAINED by the search exactly when a SINGLE related
  row satisfies EVERY search term simultaneously:

        retained  <=>  exists a related row that, for all terms, matches.

  In particular, when no single row satisfies all the terms together the
  candidate is dropped, even if every individual term is satisfied by some
  (different) related row. The quantifier order is "exists-row then for-all-
  terms", never "for-all-terms then exists-row".

The related-row and search-term collections are modelled by `PSeq[int]`
sequences of opaque identifiers; the per-(row, term) comparison is the abstract
relation `matches`. No machinery internal to a single field/term comparison is
modelled (it is unchanged). The specification pins only the combination
semantics — which row must satisfy which terms for the object to be retained.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
@Pure
@ContractOnly
def matches(row: int, term: int) -> bool:
    """Abstract per-(row, term) match relation: related row `row` satisfies
    search term `term` (the OR over that row's searched fields for the term).
    An uninterpreted total relation on the identifier domains; the combination
    semantics under specification do not depend on how a single comparison is
    computed. Provenance: mapping.md (the per-term OR-query evaluated against
    one related row by the database)."""
    Ensures(Implies(Result(), Result()))
# axioms-end


# pure-start
@Pure
def row_matches_all(row: int, terms: PSeq[int]) -> bool:
    """Related row `row` satisfies every term in the sequence. Front-recursive
    so a single unfold is available per loop step."""
    if len(terms) == 0:
        return True
    return matches(row, terms[0]) and row_matches_all(row, terms.drop(1))


@Pure
def some_row_matches_all(rows: PSeq[int], terms: PSeq[int]) -> bool:
    """Some related row satisfies every term: exists-row then for-all-terms.
    This is the retention predicate. Front-recursive over the rows."""
    if len(rows) == 0:
        return False
    return row_matches_all(rows[0], terms) or \
        some_row_matches_all(rows.drop(1), terms)
# pure-end


def search_retains_object(rows: PSeq[int], terms: PSeq[int]) -> bool:
    # pre-conditions-start
    # pre-conditions-end
    # post-conditions-start
    # The object is retained exactly when one related row satisfies all terms
    # together (exists-row, for-all-terms) — not when each term is met by some
    # (possibly different) row.
    Ensures(Result() == some_row_matches_all(rows, terms))
    # post-conditions-end
    # impl-start
    # Pre-patch skeleton: each term is filtered against the rows independently,
    # so the candidate is retained when every term is matched by SOME related
    # row, even if no single row satisfies all of them (for-all-terms then
    # exists-row). This does NOT establish the postcondition's exists-row,
    # for-all-terms retention predicate, so verification fails (G-DIFF).
    retained = True
    j = len(terms)
    while j > 0:
        # invariants-start
        Invariant(0 <= j and j <= len(terms))
        Invariant(retained == some_row_matches_all(rows, terms))
        # invariants-end
        term = terms[j - 1]
        term_seen = False
        i = len(rows)
        while i > 0:
            # invariants-start
            Invariant(0 <= i and i <= len(rows))
            # invariants-end
            row = rows[i - 1]
            if matches(row, term):
                term_seen = True
            i = i - 1
        if not term_seen:
            retained = False
        j = j - 1
    return retained
    # impl-end
