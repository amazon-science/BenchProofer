# Requirements: Negated existence subquery over an empty queryset must not drop the WHERE clause

## Introduction

Django's ORM lets a queryset filter on an existence test over a subquery,
expressed with the `Exists` expression in `django/db/models/expressions.py`
(`class Exists(Subquery)`). Such an expression can be negated (via the `~`
operator / its inversion behavior), meaning "no matching rows exist".

When the subquery is statically known to match nothing (for example a queryset
produced by `.none()`), rendering that subquery to SQL signals an empty result
by raising `django.core.exceptions.EmptyResultSet`. In `Exists.as_sql`, the call
that renders the subquery is not guarded, so this signal propagates out of the
expression unconditionally — even when the existence test is negated.

Because a *negated* existence test over an always-empty subquery is trivially
true ("there are no rows, so 'not exists' holds"), letting the empty-result
signal escape is incorrect: the query compiler treats the whole surrounding
condition as unsatisfiable and drops the entire `WHERE` block. The observable
bug is that a filter such as
`Model.objects.filter(~Exists(Model.objects.none()), name='test')` loses all of
its conditions and renders as an empty result set instead of applying the
remaining conditions.

The goal is to make `Exists.as_sql` treat an always-empty subquery correctly:
for a negated existence test it must contribute a trivially-true (empty) SQL
fragment so the rest of the `WHERE` clause is preserved; for a non-negated
existence test the empty-result signal must still propagate as before; and all
other rendering behavior must remain unchanged.

## Requirement 1: Negated existence test over an empty subquery renders as trivially true

**User story:** As a developer building a queryset, I want a negated existence
test over an empty subquery combined with other conditions to keep those other
conditions, so that my filter returns the rows matching them instead of
silently matching nothing.

**Acceptance criteria**

1. WHEN `Exists.as_sql` renders an existence test whose subquery is statically
   empty (rendering the subquery signals an empty result via `EmptyResultSet`)
   AND the existence test is negated, THEN `Exists.as_sql` SHALL return an empty
   SQL fragment: an empty SQL string together with an empty sequence of
   parameters, rather than allowing the empty-result signal to propagate.
2. WHEN such a negated-empty existence test is combined with additional
   conditions in a queryset's filter, THEN the compiled query SHALL retain those
   additional conditions in its `WHERE` clause rather than dropping the whole
   `WHERE` block.
3. WHEN a queryset filters on the conjunction of a negated existence test over
   an empty subquery and a condition selecting a specific existing row, THEN
   evaluating that queryset SHALL return exactly the rows satisfying the other
   condition (e.g. the single matching row), not an empty result.

## Requirement 2: Non-negated existence test over an empty subquery still signals empty result

**User story:** As a maintainer relying on query optimization, I want a
non-negated existence test over an always-empty subquery to keep signalling an
empty result, so that queries known to match nothing are still optimized away
correctly.

**Acceptance criteria**

1. WHEN `Exists.as_sql` renders an existence test whose subquery is statically
   empty (the subquery render signals `EmptyResultSet`) AND the existence test
   is NOT negated, THEN `Exists.as_sql` SHALL let the empty-result signal
   propagate to its caller (it SHALL NOT swallow it or return an empty
   fragment).

## Requirement 3: Only the empty-result signal is handled; other rendering is unchanged

**User story:** As a maintainer, I want the fix scoped narrowly to the
empty-subquery case, so that no other error handling or SQL generation behavior
changes.

**Acceptance criteria**

1. IF rendering the subquery raises any signal other than the empty-result
   signal, THEN `Exists.as_sql` SHALL let that other signal propagate unchanged,
   regardless of whether the existence test is negated.
2. WHEN `Exists.as_sql` renders an existence test whose subquery is NOT empty
   AND the existence test is NOT negated, THEN it SHALL return the same SQL text
   and parameters as produced by rendering the underlying existence-test
   template.
3. WHEN `Exists.as_sql` renders an existence test whose subquery is NOT empty
   AND the existence test IS negated, THEN it SHALL return the rendered
   existence-test SQL prefixed to produce its logical negation, together with
   the unchanged parameters.
4. The system SHALL preserve the existing behavior of the `Exists` expression's
   construction, inversion (negation toggling), grouping/column-reference
   handling, and backend-specific wrapping of the existence expression in the
   SELECT/GROUP BY list; none of these SHALL be altered by the empty-subquery
   handling.
