# Requirements: Strip unused annotations from count/aggregate queries

## Introduction

When a `QuerySet` that carries extra named clauses (annotations added via
`QuerySet.annotate(...)` or unselected aliases added via `QuerySet.alias(...)`)
is reduced to a single summary value — e.g. by `QuerySet.count()` or
`QuerySet.aggregate(...)` — Django builds the SQL for that summary in
`Query.get_aggregation` (`django/db/models/sql/query.py`). Historically this
method treated *every* existing named clause as a reason to (a) wrap the query
in an extra subquery and (b) emit that clause into the SQL, even when the clause
plays no part in producing the requested summary. The result is needless
subquery wrapping and needless columns/`GROUP BY` — for example
`Book.objects.annotate(Count("chapters")).count()` produced a wrapping subquery
containing the unused count, though it returns the same value as
`Book.objects.count()`.

The goal is to make the summary-query planner recognise which already-present
clauses are actually needed to compute the requested aggregate and to leave the
rest out. A clause is "needed" only if it is itself a genuine aggregation
(or window), participates in a post-grouping filter, or is referenced by the
requested aggregate. Everything else is dropped: it must not force a wrapping
subquery, and it must not appear in the emitted SQL. Pruning changes only which
clauses are emitted and whether a wrapping subquery is used; it adds or removes
no grouping/deduplication step beyond dropping the subquery that the pruned
clause would otherwise have forced. It preserves every case where a subquery is
genuinely required. It leaves counts and aggregates unchanged in the cases that
still use a subquery and in the flat cases whose remaining table/join structure
matches the un-annotated summary — with the one consequence that dropping an
*unselected* aliased aggregate defined over a multi-valued relationship reduces
the summary to a flat query that retains the joining relation and therefore
counts the joined rows (the planner deliberately adds no compensating
deduplication).

Throughout, "existing clause" means a named clause already present on the query
before the summary aggregate(s) are injected — as opposed to the injected
summary aggregate itself (e.g. the row counter that `count()` adds). "Selected"
means the clause is part of the query's selected output set (as `annotate(...)`
produces), in contrast to an `alias(...)` clause, which is available for
reference but is not selected. "Referenced by" means the requested aggregate's
expression tree names the clause's alias, directly or transitively through other
clauses.

## Requirement 1: Do not wrap a count/aggregate in a subquery for clauses that are not aggregations

**User story:** As a developer who annotates or aliases a queryset for
convenience and then calls `count()`, I want the emitted SQL to stay a single
flat query when those extra clauses are not aggregations, so that adding an
unused annotation does not silently make my counts slower.

**Acceptance criteria**

1. WHEN `Query.get_aggregation` plans a summary query and the only existing
   clauses are selected non-aggregate expressions (they contain neither an
   aggregate function nor a window/`OVER` clause) that no requested aggregate
   references, THEN the planner SHALL NOT introduce a wrapping subquery, so that
   the emitted SQL contains exactly one `SELECT`.
2. WHEN `Query.get_aggregation` plans a summary query and an existing clause was
   added as an unselected alias (present for reference but not part of the
   selected output), THEN that alias SHALL NOT by itself cause a wrapping
   subquery to be introduced; if no other condition requires one, the emitted
   SQL SHALL contain exactly one `SELECT`.
3. The decision to introduce a wrapping subquery SHALL be driven by the presence
   of a genuine existing aggregation — a selected existing clause that contains
   an aggregate function or a window/`OVER` clause — or by a filter applied
   against such an aliased aggregate/window (a `HAVING`/`QUALIFY`-style
   post-grouping filter), and SHALL otherwise remain driven only by the
   pre-existing triggers (the query is grouped by an explicit `GROUP BY` set, is
   sliced, is `distinct`, or uses a set-operation combinator).
4. WHEN none of the subquery triggers in criterion 3 hold, THEN the planner
   SHALL compute the summary directly on the outer query without a wrapping
   subquery.

## Requirement 2: Omit unreferenced existing clauses from the emitted summary SQL

**User story:** As a developer, I want annotations that contribute nothing to
the requested summary to be left out of the generated SQL entirely, so that the
database does no work for values I never use.

**Acceptance criteria**

1. WHEN a summary query is planned and an existing selected clause is neither a
   genuine aggregation/window nor referenced by any requested aggregate, THEN
   that clause SHALL NOT appear in the emitted SQL (its alias name SHALL be
   absent from the generated statement).
2. WHEN a summary query is planned over an existing selected aggregate clause
   that no requested aggregate references, THEN a wrapping subquery SHALL be
   used (because a genuine existing aggregation is present), but the unreferenced
   aggregate clause SHALL still be omitted from the emitted SQL (its alias name
   SHALL be absent from the generated statement).
3. WHEN a subquery is used and the requested summary aggregate(s) reference only
   a subset of the existing clauses, THEN the inner query SHALL materialise only
   the referenced existing clauses (together with the summary aggregate(s)) and
   SHALL exclude every existing clause that is not referenced.
4. The set of existing clauses retained for a non-`distinct` summary query SHALL
   be exactly those reachable from the requested aggregate(s): each requested
   aggregate together with every clause named in its expression tree, resolved
   transitively so that a referenced clause that itself names further clauses
   pulls those in as well.

## Requirement 3: Keep clauses that the requested aggregate references

**User story:** As a developer who aggregates over an annotation I defined (for
example averaging a per-row count), I want that annotation to remain in the
query, so that the aggregate still computes the correct value.

**Acceptance criteria**

1. WHEN a requested aggregate references an existing annotation (for example an
   aggregate computed over a previously annotated per-group count), THEN the
   referenced annotation SHALL be retained in the emitted SQL so that the
   requested aggregate can be computed from it.
2. WHEN such a reference exists, THEN a wrapping subquery SHALL be used and the
   referenced annotation's alias SHALL appear in the emitted SQL (both where it
   is defined in the inner query and where the outer aggregate refers to it).
3. IF the query is `distinct`, THEN the planner SHALL retain every existing
   selected clause in the summary query (it SHALL NOT prune to the
   referenced-only set), because re-masking the selected clauses could change
   which rows are considered distinct and therefore the result.

## Requirement 4: Preserve summary-result correctness and existing behavior (regression protection)

**User story:** As a maintainer, I want the pruning optimisation to change only
which unused clauses are emitted and whether a wrapping subquery is used —
preserving every case that genuinely needs a subquery and every numeric result
except where dropping the now-unnecessary subquery unavoidably changes the
join-cardinality the flat query counts — so that existing behavior is preserved
to the extent the optimisation allows.

**Acceptance criteria**

1. WHEN pruning removes a selected non-aggregate expression, or omits an
   unreferenced *selected* aggregate while still wrapping the query in a
   subquery, or retains a referenced aggregate, THEN the numeric result of
   `count()` and of every `aggregate(...)` SHALL be identical to the result the
   same query would produce with the pruned clauses removed by hand; in these
   cases pruning SHALL affect only the emitted SQL, never the computed values.
2. WHEN the pruned clause is an *unselected* aliased aggregate (an `alias(...)`
   clause containing an aggregate function) defined over a multi-valued
   relationship, and dropping it collapses the summary to a single flat query,
   THEN the planner SHALL emit that flat query over the retained joining
   relation without adding any compensating grouping or deduplication, so that
   `count()` reflects the joined-row cardinality of that flat query (which, for
   rows matching more than one related row, exceeds the base-table count) rather
   than the pre-pruning subquery result.
3. WHEN the query is grouped by an explicit `GROUP BY` set, is sliced, is
   `distinct`, or uses a set-operation combinator, THEN the planner SHALL
   continue to use a wrapping subquery so that slicing, distinctness, and set
   operations are applied before aggregation, exactly as before.
4. WHEN a wrapping subquery is used and the inner query would otherwise select no
   column, THEN the planner SHALL continue to select at least the model's
   primary key so that the subquery remains valid.
5. WHEN a wrapping subquery is used with default column selection and a genuine
   existing aggregation is present, THEN the inner query SHALL continue to be
   grouped by the model's primary key so that the aggregation is computed per
   row of the base model.
6. WHEN a filter clause is evaluated in the context of computing a summary
   aggregate, THEN a lookup that names an existing annotation SHALL resolve to a
   reference to that annotation (rather than re-embedding the annotation's full
   expression), so that filtering against an aliased aggregate/window in a
   summary query continues to behave correctly.
7. The system SHALL treat a clause whose aggregate/window status cannot be
   determined as if it were an aggregation (the conservative choice), so that an
   unknown clause is never wrongly pruned or wrongly kept out of a subquery.
