# Requirements: Commutative combination of `Q` objects with conditional expressions

## Introduction

In Django's ORM, filter conditions are represented by `Q` objects
(`django.db.models.query_utils.Q`) and can be combined with the bitwise
operators `&` (logical AND) and `|` (logical OR). Certain query expressions —
notably `Exists` and other boolean-valued expressions in
`django.db.models.expressions` — are also usable directly as filter conditions.
Such expressions advertise this by exposing a truthy `conditional` attribute
(for example `Exists` inherits a `conditional` property that is true when its
output field is a boolean field).

Combining an expression with a `Q` object already worked when the expression was
on the left-hand side (`Exists(...) & Q(...)`), because the expression's own
`&`/`|` operators wrap both operands in `Q` objects. But the reverse order
(`Q(...) & Exists(...)`) raised `TypeError`, because `Q`'s combination logic
rejected any right-hand operand that was not itself a `Q`. The operators were
therefore not commutative for `Q`/expression pairs.

The goal is to make `&` and `|` behave commutatively for a `Q` object combined
with a conditional expression: combining in either order must succeed and
produce a combined filter that yields the same query results, while preserving
all existing behavior for `Q`-with-`Q` combinations and continuing to reject
operands that are neither `Q` objects nor conditional expressions.

The affected code is the internal combination routine of `Q`
(`Q._combine`), reached through `Q.__and__` and `Q.__or__` in
`django/db/models/query_utils.py`.

## Requirement 1: Combine a `Q` object with a conditional expression

**User story:** As a developer building queries, I want to combine a `Q` object
with a conditional expression (such as `Exists`) using `&` or `|` regardless of
operand order, so that I can compose filter conditions naturally without hitting
a `TypeError`.

**Acceptance criteria**

1. WHEN a `Q` object is combined with `&` and the right-hand operand exposes a
   `conditional` attribute whose value is `True`, THEN `Q._combine` SHALL accept
   the operand and return a combined filter condition instead of raising an
   error.
2. WHEN a `Q` object is combined with `|` and the right-hand operand exposes a
   `conditional` attribute whose value is `True`, THEN `Q._combine` SHALL accept
   the operand and return a combined filter condition instead of raising an
   error.
3. WHEN a non-empty `Q` object is combined with a non-empty conditional
   expression using `&`, THEN the resulting filter, when applied to a queryset,
   SHALL select exactly the rows that satisfy both the `Q` condition and the
   expression condition.
4. WHEN a non-empty `Q` object is combined with a non-empty conditional
   expression using `|`, THEN the resulting filter, when applied to a queryset,
   SHALL select exactly the rows that satisfy the `Q` condition, the expression
   condition, or both.
5. WHEN a `Q` object is combined with a conditional expression, THEN the
   resulting query results SHALL be identical to those obtained by combining the
   same two operands in the opposite order (the `&` and `|` operators SHALL be
   commutative for `Q`/conditional-expression pairs).

## Requirement 2: Empty-operand shortcuts with a conditional expression

**User story:** As a developer, I want combining an empty `Q()` with a
conditional expression to reduce to the expression alone (and vice versa), so
that empty conditions act as neutral elements in either operand position.

**Acceptance criteria**

1. WHEN an empty `Q` object is combined with a conditional expression using `&`
   or `|`, THEN the resulting filter SHALL be equivalent to filtering on the
   conditional expression alone, and applying it to a queryset SHALL select
   exactly the rows that satisfy the expression.
2. WHEN a non-empty `Q` object is combined with an empty `Q` object using `&` or
   `|`, THEN the result SHALL be equivalent to the non-empty `Q` object alone
   (existing empty-operand behavior SHALL be preserved).
3. The system SHALL produce, for a conditional expression combined with an empty
   `Q` object, query results identical to those for the same empty `Q` object
   combined with that conditional expression, in both `&` and `|` forms.

## Requirement 3: Reject operands that are neither `Q` nor conditional

**User story:** As a maintainer, I want combination of a `Q` object with an
unsupported operand to keep failing loudly, so that meaningless combinations are
caught rather than silently mis-handled.

**Acceptance criteria**

1. IF a `Q` object is combined via `&` or `|` with an operand that is neither a
   `Q` object nor an object whose `conditional` attribute is `True`, THEN
   `Q._combine` SHALL raise `TypeError`.
2. IF the right-hand operand exposes a `conditional` attribute that is absent or
   not truthy and the operand is not a `Q` object, THEN the combination SHALL
   raise `TypeError` (mere presence of the operand SHALL NOT be sufficient to
   accept it).

## Requirement 4: Preserve existing `Q`-with-`Q` and expression-first behavior

**User story:** As a maintainer, I want the previously working combinations to
remain unchanged, so that this fix does not regress existing query composition.

**Acceptance criteria**

1. The system SHALL keep combining two `Q` objects with `&` and `|` exactly as
   before, producing the same combined conditions and results.
2. The system SHALL keep supporting a conditional expression as the left-hand
   operand combined with a `Q` object (for example `Exists(...) & Q()` and
   `Exists(...) | Q()`), producing the same results as before.
3. The system SHALL keep raising the documented error for bitwise-style
   combination of two non-conditional expressions (combining expressions that
   are not both conditional SHALL continue to be rejected as before).
4. WHEN two operands that are both conditional expressions are combined with `&`
   or `|`, THEN the result SHALL continue to be a combined filter condition, as
   before.
