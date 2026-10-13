# Requirements: filter-clause admissibility check must not reject ordinary values

## Introduction

When the ORM builds a `WHERE` clause, the query builder inspects each candidate
value to decide whether it is allowed to appear in a filter clause. That
inspection lives in `Query.check_filterable` in
`django/db/models/sql/query.py`. It exists so that expression objects that are
explicitly marked as not usable in a filter clause (for example a window
expression, which carries `filterable = False`) are rejected with a
`NotSupportedError` ("... is disallowed in the filter clause.").

The check currently rejects **any** candidate whose `filterable` attribute is
falsey, regardless of whether the candidate is a genuine query expression. This
misfires on ordinary stored values — e.g. a model instance whose model happens
to define a field literally named `filterable` (a `BooleanField` defaulting to
`False`). Filtering by such an instance raises `NotSupportedError` even though
the value is a plain right-hand-side lookup value, not an expression.

The goal is to narrow the rejection so it applies only to real query
expressions: a candidate is disallowed only when it is an expression that
participates in the expression-resolution protocol **and** is marked
non-filterable. Plain values that merely carry a like-named `filterable`
attribute must be accepted. The existing rejection of genuinely
non-filterable expressions, and the recursion into a candidate's nested source
expressions, must be preserved.

The affected function is `Query.check_filterable`
(`django/db/models/sql/query.py`), reached through `Query.build_filter` /
`Query.add_q` when a queryset filter is constructed.

## Requirement 1: Reject only non-filterable query expressions

**User story:** As a developer filtering a queryset by an expression that is not
allowed in a `WHERE` clause, I want that expression to be rejected clearly, so
that unsupported filter clauses fail fast with a descriptive error.

**Acceptance criteria**
1. WHEN `check_filterable` inspects a candidate value that participates in the
   expression-resolution protocol (it exposes the attribute used to resolve an
   expression against a query) AND that value is marked as not filterable (its
   `filterable` attribute is present and falsey), THEN `check_filterable` SHALL
   raise `NotSupportedError`.
2. WHEN such a rejection is raised, THEN the error message SHALL name the
   candidate value's class and state that it is disallowed in the filter clause.
3. The system SHALL treat a candidate that lacks a `filterable` attribute as
   filterable (i.e. absence of the attribute SHALL NOT cause rejection).

## Requirement 2: Accept ordinary values that merely carry a `filterable` attribute

**User story:** As a developer whose model defines a field named `filterable`, I
want to filter querysets using instances of that model as lookup values, so
that a coincidental attribute name does not break filtering.

**Acceptance criteria**
1. WHEN `check_filterable` inspects a candidate value that does NOT participate
   in the expression-resolution protocol (it does not expose the
   resolve-expression attribute), THEN `check_filterable` SHALL NOT raise
   `NotSupportedError` on account of that value, regardless of the value's own
   `filterable` attribute.
2. IF a candidate value is an ordinary stored value (such as a model instance)
   whose `filterable` attribute is falsey but which is not a query expression,
   THEN filtering a queryset using that value SHALL complete without raising
   `NotSupportedError`.
3. The system SHALL determine "is a query expression" solely from whether the
   candidate exposes the expression-resolution protocol, independently of the
   value of its `filterable` attribute.

## Requirement 3: Preserve recursion into nested source expressions

**User story:** As a maintainer, I want composite expressions to remain fully
validated, so that a non-filterable expression nested inside another expression
is still rejected.

**Acceptance criteria**
1. WHEN a candidate value exposes nested source sub-expressions, THEN
   `check_filterable` SHALL apply the same admissibility check to each nested
   source sub-expression.
2. IF any nested source sub-expression (transitively) is a query expression
   marked as not filterable, THEN `check_filterable` SHALL raise
   `NotSupportedError`, even when the enclosing candidate is itself admissible.
3. The system SHALL keep rejecting a genuinely non-filterable expression (such
   as a window expression, which is marked `filterable = False`) when it is used
   in a filter clause, whether it appears at the top level or nested within
   another expression.
4. WHEN a candidate value exposes no nested source sub-expressions and is itself
   admissible, THEN `check_filterable` SHALL return without raising.
