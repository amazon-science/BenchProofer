"""Twin-artifact model for django__django-11885.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When cascading deletion plans the set of "fast" bulk removals it can issue
  without first fetching rows into memory, several distinct relations may point
  at the SAME related table (e.g. two foreign keys of one model both referencing
  another model). Each such relation contributes one referencing column.

  The plan must issue ONE bulk removal per distinct related table, combining all
  the columns that reference it, rather than one removal per referencing column.
  Concretely, the number of bulk removals issued equals the number of DISTINCT
  related tables among the fast-removable relations -- so two relations that
  share a related table are served by a single combined removal, never two.

  Every fast-removable relation is accounted for (no related table is dropped),
  and a related table is counted once no matter how many of its columns
  participate; a related table referenced by k relations still yields exactly
  one removal whose combined predicate covers all k referencing columns.

Each fast-removable candidate relation is modelled by the integer identity of
the related table it targets; the ordered run of candidates is a `List[int]` of
those identities, with the specification carried over `PSeq[int]` via `ToSeq`.
The count of distinct related tables is spelled out deeply as a front-recursive
fold (`distinct_count`), paired with a matching loop. No callee is axiomatized:
the grouping is membership/counting logic over the candidate identities,
modelled deeply.

Markers (machine-parsed) delimit the spec / proof / impl regions; provenance
binding to the repository is in mapping.md.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# (No consumed axiom: the combine-by-related-table grouping is membership /
# counting logic over the candidate related-table identities, modelled deeply
# below. The unchanged callees that decide fast-removability and that build the
# per-table combined query from a list of referencing columns are independent of
# this count and are not invoked by the modelled behaviour; their provenance is
# recorded in mapping.md.)
# axioms-end


# pure-start
@Pure
def contains(s: PSeq[int], x: int) -> bool:
    """True iff related-table identity `x` occurs in sequence `s`. Front-
    recursive so a single unfold is available per fold/loop step."""
    if len(s) == 0:
        return False
    return s[0] == x or contains(s.drop(1), x)


@Pure
def distinct_count(s: PSeq[int]) -> int:
    """Number of DISTINCT related-table identities in `s`: the number of
    combined bulk removals to issue. An identity is counted at its FIRST
    occurrence -- i.e. it is counted iff it does not occur anywhere later in the
    sequence. Front-recursive so a single unfold is available per loop step."""
    Ensures(Result() >= 0)
    Ensures(Result() <= len(s))
    Ensures(Implies(len(s) > 0, Result() >= 1))
    if len(s) == 0:
        return 0
    rest = distinct_count(s.drop(1))
    if contains(s.drop(1), s[0]):
        return rest
    return 1 + rest
# pure-end


def combined_fast_delete_count(related_tables: List[int]) -> int:
    # pre-conditions-start
    # The candidate run is read-only: required and ensured at fractional
    # permission only.
    Requires(Acc(list_pred(related_tables), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(related_tables), 1 / 2))
    # The number of bulk removals issued equals the number of DISTINCT related
    # tables among the fast-removable candidates: two candidates sharing a
    # related table are served by one combined removal, never two.
    Ensures(Result() == distinct_count(ToSeq(related_tables)))
    # At least one removal per non-empty candidate run, and never more than one
    # per candidate (the combining never increases the number of removals).
    Ensures(Result() >= 0 and Result() <= len(related_tables))
    Ensures(Implies(len(related_tables) > 0, Result() >= 1))
    # post-conditions-end
    # impl-start
    # PRE-PATCH SKELETON: one bulk removal is issued per fast-removable candidate
    # relation, with no grouping by related table -- so a related table
    # referenced by several columns is removed by several separate queries. The
    # count is therefore the number of candidates, not the number of distinct
    # related tables.
    count = 0
    i = len(related_tables)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(related_tables), 1 / 2))
        Invariant(0 <= i and i <= len(related_tables))
        Invariant(count == len(related_tables) - i)
        # invariants-end
        count = count + 1
        i = i - 1
    return count
    # impl-end
