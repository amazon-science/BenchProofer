# Requirements: DISTINCT support for Avg and Sum aggregates

## Introduction

Django's ORM exposes aggregate functions in `django.db.models.aggregates`
(`Aggregate` base class and its concrete subclasses `Avg`, `Count`, `Max`,
`Min`, `StdDev`, `Sum`, `Variance`). Each aggregate can be constructed with a
`distinct` keyword requesting that the underlying computation range over only
the distinct values of its argument, which is rendered as a `DISTINCT`
keyword inside the emitted SQL aggregate call.

Whether an aggregate accepts `distinct=True` is a per-class policy controlled
by the `allow_distinct` attribute. Historically only `Count` permitted it.
Before Django 2.2 the other aggregates silently ignored the `distinct`
parameter; since 2.2, constructing an aggregate that does not permit distinct
with `distinct=True` raises `TypeError`. The averaging (`Avg`) and summation
(`Sum`) aggregates are semantically meaningful over distinct values, so they
must now permit distinct operation, while the remaining aggregates keep
rejecting it.

The goal of this change is to allow `Avg` and `Sum` to be constructed with
`distinct=True` and to compute correctly over distinct values, without
loosening the policy for aggregates for which distinct is not offered, and
without disturbing any existing non-distinct behavior.

## Requirement 1: Avg permits and applies DISTINCT

**User story:** As a developer building a query, I want to average only the
distinct values of a column, so that repeated values are counted once.

**Acceptance criteria**
1. WHEN an `Avg` aggregate is constructed with `distinct=True`, THEN the
   constructor SHALL succeed and SHALL NOT raise `TypeError`.
2. WHEN an `Avg` aggregate constructed with `distinct=True` is compiled to SQL,
   THEN the system SHALL include the `DISTINCT` keyword inside the emitted
   `AVG(...)` call so the average is computed over the distinct values of the
   argument.
3. WHEN a queryset is aggregated with an `Avg` over a field using
   `distinct=True`, THEN the returned value SHALL equal the arithmetic mean of
   the set of distinct values of that field (equivalently, the average after
   duplicate values are removed).
4. The `Avg` aggregate SHALL report that it permits distinct operation (its
   distinct policy SHALL be enabled).

## Requirement 2: Sum permits and applies DISTINCT

**User story:** As a developer building a query, I want to total only the
distinct values of a column, so that repeated values contribute once.

**Acceptance criteria**
1. WHEN a `Sum` aggregate is constructed with `distinct=True`, THEN the
   constructor SHALL succeed and SHALL NOT raise `TypeError`.
2. WHEN a `Sum` aggregate constructed with `distinct=True` is compiled to SQL,
   THEN the system SHALL include the `DISTINCT` keyword inside the emitted
   `SUM(...)` call so the total is computed over the distinct values of the
   argument.
3. WHEN a queryset is aggregated with a `Sum` over a field using
   `distinct=True`, THEN the returned value SHALL equal the total of the set of
   distinct values of that field (equivalently, the sum after duplicate values
   are removed).
4. The `Sum` aggregate SHALL report that it permits distinct operation (its
   distinct policy SHALL be enabled).

## Requirement 3: Count continues to permit DISTINCT (regression protection)

**User story:** As a maintainer, I want counting distinct values to keep
working, so that existing queries are unaffected.

**Acceptance criteria**
1. WHEN a `Count` aggregate is constructed with `distinct=True`, THEN the
   constructor SHALL succeed and the compiled SQL SHALL include the `DISTINCT`
   keyword inside the emitted `COUNT(...)` call.
2. WHEN a queryset is aggregated with a `Count` over a field using
   `distinct=True`, THEN the returned value SHALL equal the number of distinct
   values of that field.
3. The `Count` aggregate SHALL continue to report that it permits distinct
   operation.

## Requirement 4: Aggregates without a distinct policy keep rejecting DISTINCT

**User story:** As a maintainer, I want aggregates for which distinct is not
offered to keep rejecting `distinct=True`, so that unsupported usage fails
loudly rather than silently.

**Acceptance criteria**
1. IF an aggregate whose distinct policy is disabled (for example `Min`, `Max`,
   `StdDev`, `Variance`, or the base `Aggregate` itself) is constructed with
   `distinct=True`, THEN the constructor SHALL raise `TypeError`.
2. The base `Aggregate` class SHALL default to NOT permitting distinct
   operation, so that any subclass that does not explicitly enable the policy
   rejects `distinct=True`.
3. The raised `TypeError` SHALL indicate that the specific aggregate class does
   not allow distinct.

## Requirement 5: Non-distinct behavior is unchanged

**User story:** As a developer, I want ordinary (non-distinct) aggregation to
behave exactly as before, so that this change is additive.

**Acceptance criteria**
1. The `distinct` parameter SHALL default to `False` for every aggregate.
2. WHEN any aggregate is constructed without requesting distinct operation,
   THEN the compiled SQL SHALL NOT include the `DISTINCT` keyword.
3. WHEN a queryset is aggregated with `Avg`, `Sum`, or `Count` over a field
   without `distinct=True`, THEN the returned value SHALL be computed over all
   values of the field including duplicates (unchanged from prior behavior).

## Requirement 6: Empty aggregate call returns an empty result

**User story:** As a developer, I want calling `aggregate()` with no aggregate
expressions to be a well-defined no-op, so that it returns nothing to
summarize.

**Acceptance criteria**
1. WHEN `aggregate()` is called on a queryset with no aggregate expressions
   supplied, THEN the system SHALL return an empty mapping (`{}`).
