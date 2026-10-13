"""Twin-artifact model for django__django-9296.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A paginated collection exposes a natural traversal over all of its pages.
  Given the collection's ordered run of 1-based page numbers, walking the
  collection produces — in that same order, one item per page number, none
  skipped, none repeated, none reordered — the page obtained by looking up each
  page number through the collection's existing page-by-number accessor.

  In particular: the traversal has exactly as many items as there are page
  numbers; the k-th item produced is the page for the k-th page number; and an
  empty run of page numbers yields an empty traversal.

The collection's ordered run of page numbers (an UNCHANGED property of the
collection) is the input, modelled as a `List[int]` and carried in the
specification by the pure sequence theory `PSeq[int]`. The page-by-number
accessor is an UNCHANGED callee (`page_lookup`), abstracted to an opaque pure
function of the page number; the traversal does not alter what a single page
contains, only that every page number is visited in order and mapped through
this accessor. The result is the per-page-number image of that accessor,
specified as the front-recursive map `mapped` (one unfold per traversal step).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
@Pure
@ContractOnly
def page_lookup(number: int) -> int:
    """The collection's UNCHANGED page-by-number accessor, abstracted to an
    opaque per-page-number value. It is a pure function of the 1-based page
    number alone (the value for a given page number does not depend on when in
    the traversal it is visited), which is all the traversal relies on.
    Provenance + executable soundness check: mapping.md / axiom_check.py."""
    Ensures(True)
# axioms-end


# pure-start
@Pure
def mapped(s: PSeq[int]) -> PSeq[int]:
    """The traversal image of a run of page numbers `s`: the page accessor
    applied to each page number, in order. Front-recursive over the sequence so
    a single unfold is available per traversal step (the canonical
    `f(s) == g(s[0]) + f(s.drop(1))` pattern)."""
    if len(s) == 0:
        return PSeq(0).take(0)
    return PSeq(page_lookup(s[0])) + mapped(s.drop(1))
# pure-end


def paginate_iter(page_numbers: List[int]) -> List[int]:
    # pre-conditions-start
    # The ordered run of page numbers is read-only: the traversal consumes it
    # but does not mutate it, so it is required AND ensured at fractional
    # permission (directive 5).
    Requires(Acc(list_pred(page_numbers), 1 / 2))
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(page_numbers), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The traversal produces exactly one item per page number, in the same
    # order, each item being the page accessor applied to that page number.
    # This pins the count (== number of page numbers), the order preservation
    # (item k is the page for page number k), and that no page number is
    # skipped, repeated, or reordered. An empty run yields an empty result.
    Ensures(ToSeq(Result()) == mapped(ToSeq(page_numbers)))
    # post-conditions-end
    # impl-start
    # Pre-patch skeleton: the collection provides no page traversal at all, so
    # walking it produces no items (the absent-iterator pre-image). This fails
    # the postcondition for every non-empty run of page numbers.
    result = []  # type: List[int]
    return result
    # impl-end
