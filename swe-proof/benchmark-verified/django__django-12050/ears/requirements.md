# Requirements: Preserve iterable type when resolving lookup values

## Introduction

When Django's ORM builds a query, lookup values supplied by the caller are
normalized by `Query.resolve_lookup_value` in
`django/db/models/sql/query.py`. A lookup value may be a query expression
(anything exposing a `resolve_expression` method, including `F` references), an
ordinary scalar value, or an ordered collection (a `list` or a `tuple`) whose
elements are themselves lookup values.

A recent change made the collection branch always rebuild the collection as a
`tuple`, regardless of whether the caller passed a `list` or a `tuple`. This
coerces the value's type, which breaks equality/`exact` lookups for ORM field
types whose stored representation is sensitive to the concrete container type
(for example a field that pickles or otherwise serializes the raw Python value):
a `list` given by the caller is turned into a `tuple`, so the value that reaches
the database layer no longer matches what was stored.

The goal is that resolving a collection lookup value preserves the caller's
container type — a `list` resolves to a `list`, a `tuple` resolves to a
`tuple` — while still resolving each element independently exactly as before.

## Requirement 1: Preserve the container type of collection lookup values

**User story:** As a developer issuing an ORM lookup whose value is a `list` (or
a `tuple`), I want the resolved value to keep the same container type, so that
field types that depend on the exact input type (such as a pickled field)
continue to match stored values.

**Acceptance criteria**

1. WHEN `Query.resolve_lookup_value` receives a value that is a `list`, THEN the
   method SHALL return a `list`.
2. WHEN `Query.resolve_lookup_value` receives a value that is a `tuple`, THEN the
   method SHALL return a `tuple`.
3. The system SHALL NOT change the container type of a collection lookup value
   (a `list` SHALL NOT be returned as a `tuple`, and a `tuple` SHALL NOT be
   returned as a `list`).
4. WHEN a lookup is constructed from a keyword whose value is a `list` of plain
   scalar values, THEN the resulting exact-comparison lookup's right-hand side
   SHALL be that `list` (equal in both value and container type to the input),
   and SHALL NOT be a `tuple`.

## Requirement 2: Resolve each element of a collection independently and in order

**User story:** As a developer whose lookup value collection may contain query
expressions, I want every element resolved on its own, so that expression
elements are still resolved correctly while plain elements pass through.

**Acceptance criteria**

1. WHEN `Query.resolve_lookup_value` receives a collection value, THEN it SHALL
   produce a collection whose elements are, position for position, the resolved
   form of the corresponding input element.
2. The system SHALL preserve the number of elements (arity) and their order when
   resolving a collection value.
3. IF an element of the collection is a query expression (it exposes a
   `resolve_expression` method), THEN that element SHALL be replaced by the
   result of resolving that expression in the current query context.
4. IF an element of the collection is an `F` reference, THEN it SHALL be resolved
   with the same column-simplification behavior (`simple_col`) that is applied to
   a top-level `F` value.
5. IF an element of the collection carries no resolution behavior (it is a plain
   scalar), THEN it SHALL be left unchanged.
6. WHEN an element of the collection is itself a collection, THEN that nested
   collection SHALL be resolved by the same rule, preserving its own container
   type, arity, and order.

## Requirement 3: Preserve existing resolution of non-collection lookup values

**User story:** As a maintainer, I want the existing handling of expression and
scalar lookup values to remain unchanged, so that the fix does not regress
current query behavior.

**Acceptance criteria**

1. IF the lookup value is a query expression (it exposes a `resolve_expression`
   method), THEN `Query.resolve_lookup_value` SHALL return the result of
   resolving that expression in the current query context, using the given
   join-reuse and join-allowance settings.
2. IF the lookup value is an `F` reference, THEN it SHALL be resolved with the
   column-simplification (`simple_col`) setting applied.
3. IF the lookup value is neither an expression nor a collection (it is a plain
   scalar), THEN `Query.resolve_lookup_value` SHALL return it unchanged.
4. The system SHALL confine this change to the collection branch: for a lookup
   value that is not a `list` or `tuple` (an expression, an `F` reference, or a
   plain scalar), `Query.resolve_lookup_value` SHALL return exactly the value it
   returned before this change, so that query conditions built from such values
   are unaffected.
