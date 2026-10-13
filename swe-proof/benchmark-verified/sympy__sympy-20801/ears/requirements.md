# Requirements: Order-independent equality between a floating-point number and a logic boolean

## Introduction

In the SymPy core numbers module (`sympy/core/numbers.py`), the `Float`
class defines equality through its `__eq__` method (with `__ne__` derived from
it). Equality of a `Float` against another operand is decided by dispatching on
the *kind* of the operand (logic boolean, named numeric constant, another
float, a rational, some other numeric value, or something non-numeric).

A defect exists in how a **zero-valued** `Float` (for example `S(0.0)`) is
compared. The equality routine applied an "empty/zero-like" shortcut for a zero
float *before* it examined the kind of the operand. As a result, comparing a
zero float to the logic constant `S.false` produced the wrong answer and, worse,
an *asymmetric* one:

```
S(0.0) == S.false   ->  True    (wrong)
S.false == S(0.0)   ->  False
```

whereas the analogous integer comparison is correctly symmetric and false:

```
S(0)   == S.false   ->  False
S.false == S(0)     ->  False
```

The goal is to make a zero `Float` behave like other numbers when compared to a
logic boolean: the two are never equal, and the result must be the same
regardless of comparison order. This must be achieved without disturbing any
of the other, already-correct equality behaviors of `Float`.

The affected symbol is `Float.__eq__` (and, by delegation, `Float.__ne__`) in
`sympy/core/numbers.py`.

## Requirement 1: A zero float is never equal to a logic boolean

**User story:** As a user comparing SymPy objects, I want a zero-valued float to
be treated as a number rather than as a truth value when compared with a logic
boolean, so that numeric zero and boolean false are correctly distinguished.

**Acceptance criteria**

1. WHEN a zero-valued `Float` is compared for equality with the logic constant
   `S.false`, THEN `Float.__eq__` SHALL evaluate the comparison to `False`.
2. WHEN a zero-valued `Float` is compared for equality with the logic constant
   `S.true`, THEN `Float.__eq__` SHALL evaluate the comparison to `False`.
3. IF the operand of a `Float` equality comparison is a logic boolean, THEN the
   result SHALL be `False` regardless of whether the float's value is zero or
   non-zero.
4. WHEN a zero-valued `Float` is compared for inequality with a logic boolean,
   THEN `Float.__ne__` SHALL evaluate the comparison to `True`.

## Requirement 2: Order independence of float-versus-boolean equality

**User story:** As a user, I want equality between a float and a logic boolean to
give the same answer no matter which operand is written first, so that
comparisons are consistent and predictable.

**Acceptance criteria**

1. WHEN a zero-valued `Float` and the logic constant `S.false` are compared for
   equality, THEN the result SHALL be `False` for both orderings of the two
   operands.
2. WHEN an integer zero (`S(0)`) and the logic constant `S.false` are compared
   for equality, THEN the result SHALL remain `False` for both orderings of the
   two operands.
3. The system SHALL produce identical equality results for a float-versus-boolean
   comparison irrespective of which operand appears on the left-hand side.

## Requirement 3: Preserve the empty/zero-like fallback for genuinely non-numeric operands

**User story:** As a maintainer, I want the existing "zero float matches an
empty/zero-like operand" behavior to survive, but only for operands that are
neither boolean nor numeric, so that the bug fix does not remove legitimate
behavior.

**Acceptance criteria**

1. The system SHALL apply the zero-float "empty/zero-like" equality shortcut
   ONLY to operands that are neither a logic boolean nor any recognized numeric
   kind (named numeric constant, float, rational, or other number).
2. WHEN a zero-valued `Float` is compared with an operand that is a recognized
   numeric or boolean kind, THEN the result SHALL be determined by that kind's
   own comparison rule and SHALL NOT be short-circuited by the zero-float
   shortcut.

## Requirement 4: Preserve existing numeric equality semantics (regression protection)

**User story:** As a maintainer, I want all previously-correct `Float` equality
results to be unchanged by this fix, so that no existing behavior regresses.

**Acceptance criteria**

1. WHEN a `Float` is compared for equality with another `Float`, THEN the result
   SHALL be `True` exactly when the two hold the same exact value at their
   respective precisions, and `False` otherwise.
2. WHEN a `Float` is compared for equality with a `Rational` or an `Integer`,
   THEN the result SHALL reflect the exact numeric equality of the two values.
3. WHEN a `Float` is compared for equality with a named numeric constant that is
   irrational, THEN the result SHALL be `False`.
4. WHEN a `Float` is compared for equality with any other numeric value, THEN the
   result SHALL be `True` exactly when the two values agree once compared at a
   shared precision.
5. IF the operand cannot be brought into SymPy's symbolic domain, THEN
   `Float.__eq__` SHALL defer the comparison (returning the not-implemented
   sentinel) rather than raising.
6. WHEN a `Float` is compared for equality with a non-numeric, non-boolean
   operand that is not empty/zero-like, THEN the result SHALL be `False`.
