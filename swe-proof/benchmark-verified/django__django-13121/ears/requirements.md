# Requirements — Duration-only arithmetic expressions on non-native-duration backends

## Introduction

Django's ORM lets a query annotate or filter using arithmetic over model
fields, e.g. `Experiment.objects.annotate(duration=F('estimated_time') + delta)`
where `estimated_time` is a `DurationField` and `delta` is a
`datetime.timedelta`. On database backends that have no native duration/interval
type (notably SQLite and MySQL, where
`connection.features.has_native_duration_field` is `False`), durations are
stored and computed as integer microseconds and Django rewrites duration
arithmetic through a dedicated code path so the result can be converted back to
a `timedelta`.

The affected code lives in `django/db/models/expressions.py`, in the arithmetic
combination machinery: `Combinable._combine` (which wraps a raw Python literal
operand into an expression), `CombinedExpression.as_sql` (which decides which
SQL-generation strategy an arithmetic expression uses), and
`DurationExpression` (the duration-arithmetic strategy). Related backend hooks
live in `django/db/backends/base/operations.py` and the SQLite/MySQL operations
classes.

Currently, an expression whose operands are *both* durations — for example a
`DurationField` combined with a `timedelta` constant, so both sides are of
duration type — is misrouted through the duration-arithmetic strategy on
non-native backends. That strategy emits a raw microsecond interval literal for
the constant operand, and when the query result is later run through the
duration-field value converter the interval literal cannot be parsed as a
decimal number of microseconds, so evaluating the queryset raises an error
instead of returning a `timedelta`. The goal is to make duration-only
arithmetic expressions evaluate correctly on every backend while preserving all
existing arithmetic, temporal-subtraction, and mixed date/duration behavior.

## Requirement 1: Duration + timedelta arithmetic evaluates correctly on non-native backends

**User story:** As a developer using SQLite or MySQL, I want to annotate a
queryset with a `DurationField` combined with a `timedelta` constant so that I
can read back a correct duration value without the query raising an error.

**Acceptance criteria**

1. WHEN a queryset is annotated with an arithmetic expression that adds a
   `datetime.timedelta` constant to a `DurationField` model field (e.g.
   `F('estimated_time') + delta`) and the queryset is evaluated on a backend
   whose `connection.features.has_native_duration_field` is `False`, THEN
   iterating the queryset SHALL complete without raising, and each row's
   annotated value SHALL equal that row's stored duration plus the given
   `timedelta`.
2. WHEN such an annotation is evaluated for a range of `timedelta` operands,
   including negative durations and durations containing a microsecond
   component, THEN the system SHALL return, for every operand, an annotated
   value exactly equal to the stored duration combined with that operand.
3. The system SHALL produce the same evaluated result for duration + timedelta
   arithmetic regardless of whether the backend has a native duration field,
   so that the value read back is always the arithmetic combination of the two
   durations.

## Requirement 2: A raw timedelta operand is typed as a duration

**User story:** As a maintainer of the expression system, I want a bare
`timedelta` literal used in an arithmetic expression to be classified as a
duration-typed value, so that duration arithmetic is recognized consistently no
matter which operand supplies the duration.

**Acceptance criteria**

1. WHEN `Combinable._combine` wraps a non-expression operand that is a
   `datetime.timedelta` instance, THEN the resulting value expression SHALL
   report an output field whose internal type is that of a `DurationField`.
2. WHEN `Combinable._combine` wraps a non-expression operand that is not a
   `datetime.timedelta`, THEN the resulting value expression SHALL behave as an
   ordinary literal value with no duration output type imposed.
3. The system SHALL classify duration arithmetic by the resolved output-field
   types of both operands, so that a `timedelta` constant and a stored
   `DurationField` are treated as the same kind of operand.

## Requirement 3: Only mixed duration/non-duration operands use the duration-arithmetic strategy

**User story:** As a developer, I want duration-only arithmetic to compute
correctly on non-native backends, so that adding two durations does not fall
into the interval-literal path that cannot be converted back.

**Acceptance criteria**

1. IF the backend has no native duration field AND at least one operand of an
   arithmetic expression resolves to a duration internal type AND the two
   operands' resolved internal types differ, THEN `CombinedExpression.as_sql`
   SHALL delegate to the duration-arithmetic strategy (`DurationExpression`).
2. IF the backend has no native duration field AND both operands of an
   arithmetic expression resolve to the same internal type (for example a
   duration combined with another duration), THEN the expression SHALL NOT be
   routed through the duration-arithmetic strategy and SHALL instead be built
   by the ordinary arithmetic-combination path so its value converts back
   correctly.
3. WHILE the backend reports a native duration field, arithmetic expressions
   SHALL never be diverted to the non-native duration-arithmetic strategy.
4. WHEN the duration-arithmetic strategy compiles an operand whose resolved
   output field is of duration internal type, THEN it SHALL format that operand
   for duration arithmetic; otherwise it SHALL compile the operand normally.

## Requirement 4: Temporal subtraction behavior is preserved

**User story:** As a developer, I want subtracting two date/time values to keep
producing a duration, so that existing temporal-difference queries continue to
work.

**Acceptance criteria**

1. IF the arithmetic connector is subtraction AND both operands resolve to the
   same date/time internal type (`DateField`, `DateTimeField`, or `TimeField`),
   THEN `CombinedExpression.as_sql` SHALL delegate to the temporal-subtraction
   strategy (`TemporalSubtraction`).
2. WHEN two `DateField`, two `DateTimeField`, or two `TimeField` operands are
   subtracted, THEN evaluating the query SHALL yield the correct time
   difference as a duration, including cases whose difference includes a
   microsecond component.
3. The system SHALL keep supporting temporal subtraction expressed through
   nested queries and subqueries, returning the same difference as the direct
   form.

## Requirement 5: Existing mixed date/duration and general arithmetic is unchanged

**User story:** As a developer, I want date-plus-duration, date-minus-duration,
and ordinary numeric arithmetic to keep working, so that this change fixes only
the duration-only case without regressions.

**Acceptance criteria**

1. WHEN a date or datetime field is combined with a duration operand (addition
   or subtraction), THEN evaluating the query SHALL return the correctly
   shifted date/datetime value, including operands with a microsecond
   component.
2. WHEN durations are added to or subtracted from stored duration values in an
   update or annotation, THEN the stored/returned values SHALL reflect the
   correct combined duration.
3. The system SHALL keep evaluating non-temporal arithmetic (numeric addition,
   subtraction, multiplication, division, modulo, power, and bitwise operators,
   in both left-hand and right-hand operand positions) with unchanged results.
4. WHEN an unsupported operator is applied to duration operands, THEN the
   system SHALL continue to reject it in the same way as before this change.
5. The system SHALL preserve the construction, equality, hashing, pickling,
   deconstruction, and representation semantics of expression objects
   (`F`, `Value`, `CombinedExpression`, and related expressions), so that value
   literals with or without an explicit output field remain distinguishable and
   consistent.
