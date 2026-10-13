# Temporal and duration arithmetic without an explicit output field

## Introduction

In the ORM query-expression layer (`django/db/models/expressions.py`), a
`CombinedExpression` joins two operand expressions with an arithmetic operator
(for example the result of `F('end') - F('start')`). Historically, the decision
about how to treat such a combination — as an ordinary arithmetic combination, as
a *duration* combination (one duration operand mixed with a non-duration
operand), or as a *temporal subtraction* (subtracting two same-typed
date/time/datetime operands to yield a duration) — was made only at SQL-generation
time (`CombinedExpression.as_sql`). Because of this, the combination did not
acquire a determinate value-type (`output_field`) on its own during expression
resolution. Users therefore had to wrap temporal subtractions in an
`ExpressionWrapper(..., output_field=DurationField())`; omitting it raised
`django.core.exceptions.FieldError: Expression contains mixed types ... You must
set output_field.`

The goal is to make the same classification happen during
`CombinedExpression.resolve_expression`, so that a combination of two temporal
operands (or a duration mixed with a non-duration) is re-typed to the correct
specialized expression as it is resolved, giving it a determinate `DurationField`
value-type without any caller-supplied wrapper — while preserving every existing
arithmetic, duration, and SQL-generation behavior.

## Requirement 1: Classify combined expressions during resolution

**User story:** As a developer, I want an arithmetic combination of two temporal
operands to be recognized as producing a duration during resolution, so that I do
not have to wrap it in an explicit output-field declaration.

**Acceptance criteria**

1. WHEN a `CombinedExpression` is resolved via `resolve_expression`, THEN the
   system SHALL first resolve both the left-hand and right-hand operand
   expressions (passing through the same `query`, `allow_joins`, `reuse`,
   `summarize`, and `for_save` arguments) before classifying the combination.
2. WHEN a `CombinedExpression` that is an ordinary combination is resolved and
   exactly one of its two resolved operands has a `DurationField` value-type while
   the other operand has a different value-type, THEN the system SHALL re-type the
   combination as a duration combination and return the result of resolving that
   duration combination.
3. WHEN a `CombinedExpression` that is an ordinary combination is resolved, its
   operator is subtraction, and both resolved operands share the same value-type
   drawn from the date, datetime, and time families, THEN the system SHALL re-type
   the combination as a temporal-subtraction combination and return the result of
   resolving that temporal-subtraction combination.
4. IF a resolved `CombinedExpression` matches neither the duration-mixing
   condition nor the temporal-subtraction condition, THEN the system SHALL return
   an ordinary resolved combination whose left- and right-hand members are the
   already-resolved operands.
5. The temporal-subtraction combination SHALL carry a `DurationField` value-type,
   so that a subtraction of two same-typed date/datetime/time operands has a
   determinate duration `output_field` after resolution without any caller-supplied
   `output_field` or `ExpressionWrapper`.
6. IF an operand's value-type cannot be determined during resolution (its
   `output_field` lookup is unavailable or raises a field-resolution error), THEN
   the system SHALL treat that operand's value-type as an unknown that matches
   neither the duration type nor any date/datetime/time type, and SHALL NOT raise
   an error from the classification itself.

## Requirement 2: Only ordinary combinations are reclassified

**User story:** As a maintainer, I want an already-specialized combination to keep
its kind when resolved, so that repeated or nested resolution does not re-wrap or
misclassify it.

**Acceptance criteria**

1. WHEN a combination that is already a duration combination or an
   already-temporal-subtraction combination is resolved, THEN the system SHALL keep
   that specialized kind and SHALL NOT reclassify it as a different kind.
2. The classification described in Requirement 1 (criteria 2 and 3) SHALL be
   applied only to an ordinary combination and SHALL be skipped for a combination
   that is already a duration or temporal-subtraction combination.

## Requirement 3: SQL generation for ordinary combinations no longer classifies

**User story:** As a maintainer, I want SQL generation for a plain combination to
emit only the plain arithmetic SQL, so that classification is not duplicated once
it has moved to resolution time.

**Acceptance criteria**

1. WHEN an ordinary `CombinedExpression.as_sql` is invoked, THEN the system SHALL
   compile its left- and right-hand members and combine them with the ordinary
   arithmetic combiner, and SHALL NOT re-derive a duration or temporal-subtraction
   kind at SQL-generation time.
2. The system SHALL continue to produce SQL for temporal subtraction and for
   duration-mixed combinations through their specialized expression kinds (reached
   via resolution per Requirement 1), so that the emitted operations and their
   results are unchanged from before this change.

## Requirement 4: Duration expressions on native-duration backends

**User story:** As a developer using a backend with a native duration type, I want
duration arithmetic to compile to the ordinary arithmetic SQL, so that native
duration columns are handled correctly.

**Acceptance criteria**

1. IF the database backend reports that it has a native duration field, THEN when a
   duration combination's `as_sql` is invoked the system SHALL emit the ordinary
   combined-expression SQL (delegating to the base combined-expression SQL
   generation) rather than the duration-specific arithmetic formatting.
2. IF the database backend does not report a native duration field, THEN the system
   SHALL continue to emit the duration-specific arithmetic SQL (formatting each
   duration operand and combining with the duration combiner) as before.

## Requirement 5: Preserve existing arithmetic and result behavior (regression)

**User story:** As a user with existing queries, I want all prior arithmetic and
duration behaviors to keep working unchanged, so that this improvement introduces
no regressions.

**Acceptance criteria**

1. The system SHALL keep supporting temporal subtraction that is filtered or
   compared against `datetime.timedelta` values, returning the correct set of
   matching rows for both same-value and threshold (greater-than / less-than)
   comparisons.
2. The system SHALL keep supporting temporal subtraction where one operand is a
   subquery selecting a date/datetime/time value, yielding a duration result
   usable in filters.
3. WHEN a temporal subtraction has an operand whose value is SQL `NULL` (for
   example subtracting a `NULL`-valued date, time, or datetime), THEN the resulting
   duration for that row SHALL be `None`.
4. The system SHALL preserve microsecond-level precision in the resulting duration
   of a datetime subtraction, including for large timedelta magnitudes.
5. The system SHALL keep supporting a temporal subtraction whose operands are
   produced by conditional (`Case`) expressions of the appropriate date/time type.
6. The system SHALL keep supporting all existing non-temporal arithmetic — integer
   and other numeric addition, subtraction, multiplication, division, modulo,
   power, and bitwise operations, in both left-hand and right-hand operand
   positions — with unchanged results.
7. The system SHALL keep supporting existing duration behaviors — adding or
   subtracting a duration to/from a datetime, duration-with-datetime arithmetic
   (including microsecond precision), duration field addition, and duration
   updates — with unchanged results.
8. The system SHALL preserve the identity, equality, hashing, deconstruction,
   pickling, and repr behavior of expression objects, and SHALL continue to raise
   the appropriate error for genuinely unsupported or invalid operator combinations.
