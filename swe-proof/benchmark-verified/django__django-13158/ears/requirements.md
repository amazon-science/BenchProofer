# Requirements: `none()` must empty combined (union/intersection/difference) querysets

## Introduction

Django lets a `QuerySet` be built by combining several other querysets with the
set operators `union()`, `intersection()`, and `difference()`. Internally the
resulting query keeps the list of the querysets it was built from on the
`Query` object as `combined_queries` (a tuple of `Query` instances), together
with a combinator marker; when the SQL is generated, the combined query returns
the *combination* (e.g. the union) of the rows selected by each of those
sub-queries.

`QuerySet.none()` is supposed to produce a queryset that yields **no rows** at
all. It does this by forcing the underlying `Query` to select nothing:
`django/db/models/sql/query.py`'s `Query.set_empty()` adds a `NothingNode` to
the query's `where` clause, so the top-level query's own row selection matches
nothing.

The defect: `set_empty()` only touched the top-level query's `where` clause and
ignored `combined_queries`. For a combined query the rows come from the
sub-queries, not from the top node's own `where` clause, so emptying only the
top node left every sub-query still selecting its rows — and the combined result
still returned all of them. Concretely, calling `.none()` on a `union()` (or
`intersection()`/`difference()`) queryset returned the full combined result
instead of an empty one. A related gap: `Query.clone()` did not copy
`combined_queries`, so a cloned query shared the *same* sub-query objects with
its source, and mutating one query's sub-queries (as `set_empty()` now does)
could leak into the other.

The goal is to make `none()` reliably yield an empty result for combined
querysets by (a) having `set_empty()` force emptiness on the whole query tree —
the top query and every combined sub-query, recursively — and (b) having
`clone()` produce independent clones of the combined sub-queries so that
emptying a clone does not affect the original, and vice versa. All non-combined
behavior of `none()`, `clone()`, and the combinator operations must be
preserved.

## Requirement 1: `none()` empties a combined queryset completely

**User story:** As a Django developer who builds a queryset with `union()`,
`intersection()`, or `difference()`, I want `.none()` on that combined queryset
to return no rows, so that "select nothing" behaves consistently whether or not
the queryset was built by combining others (for example, an unsubmitted
`ModelMultipleChoiceField` adds nothing rather than every combined object).

**Acceptance criteria**

1. WHEN `Query.set_empty()` is invoked on a query that has one or more combined
   sub-queries (its `combined_queries` is non-empty), THEN it SHALL force the
   top-level query to select nothing AND SHALL additionally force every combined
   sub-query in `combined_queries` to select nothing.
2. WHEN a combined queryset (built via `union()`, `intersection()`, or
   `difference()`) has `none()` applied to it, THEN evaluating the resulting
   queryset SHALL return an empty result — zero rows — regardless of how many
   rows the individual combined querysets would otherwise select.
3. The emptying of combined sub-queries SHALL apply recursively: WHEN a combined
   sub-query is itself a combined query, THEN forcing the outer query empty SHALL
   also force that sub-query's own combined sub-queries to select nothing, so
   that no query anywhere in the combination tree still selects rows.
4. WHEN `none()` empties a combined queryset, THEN the operation SHALL preserve
   the structure of the combination (the combinator, and the number and nesting
   of combined sub-queries): it SHALL only force selections empty and SHALL NOT
   add, drop, or reorder combined sub-queries.

## Requirement 2: Cloning a query copies its combined sub-queries independently

**User story:** As a maintainer, I want cloning a `Query` to give the clone its
own independent copies of the combined sub-queries, so that forcing one query
(or its clone) empty — as `none()` now does — never mutates the other.

**Acceptance criteria**

1. WHEN `Query.clone()` is called, THEN the cloned query's `combined_queries`
   SHALL consist of independent clones of the source query's combined
   sub-queries, one per source sub-query, in the same order — not references to
   the same sub-query objects held by the source.
2. The cloned query's `combined_queries` SHALL have the same length and
   combination structure as the source query's, so that the clone represents the
   same combination of sub-queries.
3. WHEN a query with combined sub-queries is cloned and then one of the two
   (source or clone) is forced to select nothing, THEN the other SHALL be
   unaffected — its combined sub-queries SHALL still select their original rows.
4. WHEN `Query.clone()` is called on a query that has no combined sub-queries
   (`combined_queries` is empty), THEN the clone's `combined_queries` SHALL also
   be empty.

## Requirement 3: Preserve existing queryset and combinator behavior (regression protection)

**User story:** As a maintainer, I want every other queryset behavior — simple
`none()`, ordinary cloning, and the results of `union()`, `intersection()`, and
`difference()` themselves — to remain exactly as before, so that fixing
combined-queryset `none()` does not disturb anything else.

**Acceptance criteria**

1. WHEN `none()` is applied to a non-combined queryset, THEN it SHALL continue
   to return an empty result, exactly as before.
2. The results of `union()`, `intersection()`, and `difference()` on
   non-emptied querysets SHALL be unchanged: a simple union SHALL return the
   combined distinct rows, `union(all=True)` SHALL retain duplicates, and
   intersection and difference SHALL return their respective row sets.
3. WHEN one of the operands of a combinator operation is itself an empty
   queryset, THEN the combined result SHALL follow the established set-operation
   semantics (e.g. union with an empty queryset yields the non-empty operand's
   rows; intersection with an empty queryset yields nothing).
4. WHEN `count()` is called on a combined queryset, THEN it SHALL return the
   number of rows in the combined result, including the case where the combined
   result is empty.
5. Ordering of a combined queryset SHALL continue to work as before — including
   ordering by column, by alias, and by expression — and the established errors
   for ordering by a non-selected column and for unsupported operations
   (unsupported ordering/slicing, and unsupported query methods on a combined
   queryset) SHALL still be raised.
6. Combining querysets across multiple models, and combining querysets that use
   `values()`/`values_list()`, annotations, extra selects, or nested
   sub-compound combinations, SHALL continue to produce their previous results.
7. WHEN a query with no combined sub-queries has `set_empty()` applied, THEN its
   behavior SHALL be unchanged from before (only the top-level query is forced to
   select nothing, and there are no sub-queries to recurse into).
