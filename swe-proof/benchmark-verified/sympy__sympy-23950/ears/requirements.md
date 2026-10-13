# Requirements: `Contains.as_set` should return the underlying set

## Introduction

`Contains` (in `sympy/sets/contains.py`) is a boolean-valued object that
asserts that an element `x` is a member of a set `s`, i.e. `Contains(x, s)`.
Because it subclasses a boolean function, other parts of SymPy expect to be
able to convert a boolean predicate into the set of values for which it holds
by calling its `as_set()` method (for example, `Piecewise.eval` calls
`cond.as_set().as_relational(...)` on a condition).

Today `Contains.as_set()` raises `NotImplementedError`, so any code path that
converts a `Contains` predicate to a set fails (e.g. building a `Piecewise`
whose condition is a `Contains` raises an error while trying to obtain a set
representation). The goal is to make `Contains.as_set()` return the set that
the assertion refers to, so the predicate participates correctly wherever a
boolean's set representation is required, while preserving all existing
behavior of `Contains` (construction, evaluation, and `binary_symbols`).

Affected module/function: `sympy/sets/contains.py`, method
`Contains.as_set`.

## Requirement 1: `Contains.as_set()` returns the asserted set

**User story:** As a SymPy user, I want `Contains(x, s).as_set()` to return the
set `s` that the membership assertion refers to, so that a `Contains` predicate
can be used anywhere a boolean's set representation is expected (such as inside
`Piecewise`) instead of raising an error.

**Acceptance criteria**

1. WHEN `as_set()` is called on a `Contains` instance built from an element and
   a set operand, THEN the method SHALL return the set operand exactly as it was
   supplied at construction, without modification or wrapping.
2. WHEN `as_set()` is called on a `Contains` instance, THEN the method SHALL NOT
   raise `NotImplementedError` (nor any other exception) for a well-formed
   `Contains` object.
3. WHEN `as_set()` is called on `Contains(x, S)` where `S` is a finite set of
   elements, THEN the method SHALL return that same finite set (equal to the
   original set operand).
4. WHEN `as_set()` is called on `Contains(x, S)` where `S` is an unbounded,
   symbolic domain such as the set of all integers or the set of all reals,
   THEN the method SHALL return that same domain set (equal to the original set
   operand).
5. The value returned by `as_set()` SHALL be an object of the SymPy set type
   (the second operand of `Contains`), so that it supports the standard set
   protocol (including `as_relational`) that callers rely upon.

## Requirement 2: Preserve existing `Contains` construction and evaluation

**User story:** As a maintainer, I want the existing behavior of constructing
and evaluating `Contains` to remain unchanged, so that adding a set
representation does not regress element-membership semantics.

**Acceptance criteria**

1. WHEN `Contains` is constructed with a second argument that is not a SymPy
   set, THEN construction SHALL raise a `TypeError`.
2. WHEN `Contains` is given a concrete element that provably belongs to the set
   (e.g. an integer in the integers), THEN evaluation SHALL produce the boolean
   true value.
3. WHEN `Contains` is given a concrete element that provably does not belong to
   the set (e.g. a negative integer in the naturals), THEN evaluation SHALL
   produce the boolean false value.
4. WHEN `Contains` is given a symbolic element whose membership cannot be
   decided, THEN it SHALL remain an unevaluated `Contains` expression equal to
   the explicitly non-evaluated form of the same arguments.
5. IF the element cannot be shown to lie in the set, THEN evaluation SHALL NOT
   collapse the predicate to the boolean false value (an undecided membership
   stays unevaluated).
6. WHEN a symbolic element is tested against an interval, THEN `Contains` SHALL
   remain unevaluated, while the interval's own containment query SHALL yield
   the corresponding pair of inequality conditions.
7. WHEN a value equal to positive or negative infinity is tested for membership
   in a real interval that has those infinities as open endpoints, THEN the
   result SHALL be the boolean false value.

## Requirement 3: Preserve `binary_symbols`

**User story:** As a maintainer, I want the `binary_symbols` property of
`Contains` to keep returning the same symbols, so that boolean-substitution
logic that depends on it is unaffected by the change.

**Acceptance criteria**

1. WHEN `binary_symbols` is accessed on a `Contains` whose set operand contains
   symbols and equality relations, THEN it SHALL return exactly the set of
   symbols occurring as bare symbols and as members of those boolean/equality
   relations (unchanged from current behavior).
