# Requirements: Zero-argument Min() and Max()

## Introduction

The symbolic `Max` and `Min` functions (class `MinMaxBase` and its subclasses
`Max` and `Min` in `sympy/functions/elementary/miscellaneous.py`) historically
rejected being called with no arguments, raising a `ValueError`. Mathematically,
however, the maximum and minimum over the empty set of extended real numbers are
well defined: the maximum of the empty set is negative infinity and the minimum
of the empty set is positive infinity (each equal to the respective identity
element of the operation).

The goal is to make zero-argument `Max()` and `Min()` return these mathematical
identity values instead of raising, while preserving every existing behavior of
`Max`/`Min` for one or more arguments.

## Requirement 1: Zero-argument Max and Min return their identity element

**User story:** As a user of SymPy's symbolic maximum/minimum, I want `Max()`
and `Min()` with no arguments to return the mathematically correct extended-real
value, so that empty-set aggregations compose without special-casing.

**Acceptance criteria**
1. WHEN `Max` is instantiated with no arguments, THEN the system SHALL return
   negative infinity (the SymPy singleton `S.NegativeInfinity`, i.e. `-oo`).
2. WHEN `Min` is instantiated with no arguments, THEN the system SHALL return
   positive infinity (the SymPy singleton `S.Infinity`, i.e. `oo`).
3. WHEN either `Max` or `Min` is instantiated with no arguments, THEN the system
   SHALL NOT raise `ValueError` (or any other exception) for the empty-argument
   case.

## Requirement 2: Single-argument Max and Min return that argument

**User story:** As a user, I want `Max(e)` and `Min(e)` of a single expression
to evaluate to that expression, so that degenerate one-element cases behave
transparently.

**Acceptance criteria**
1. WHEN `Max` is instantiated with exactly one argument `e`, THEN the system
   SHALL return `e` itself.
2. WHEN `Min` is instantiated with exactly one argument `e`, THEN the system
   SHALL return `e` itself.

## Requirement 3: Preserve existing multi-argument Max/Min behavior

**User story:** As a maintainer, I want all previously supported `Max`/`Min`
behavior for two or more arguments to remain unchanged, so that removing the
empty-argument guard introduces no regression.

**Acceptance criteria**
1. The system SHALL keep `Max`/`Min` symmetric in their arguments: for
   expressions `x` and `y`, `Min(x, y)` SHALL equal `Min(y, x)` and
   `Max(x, y)` SHALL equal `Max(y, x)`.
2. The system SHALL keep `Max`/`Min` associative and order-independent across
   nesting: e.g. `Min(x, Min(y, z))`, `Min(z, y, x)`, and `Min(x, y, z)` SHALL
   all be equal (and analogously for `Max`).
3. The system SHALL continue to evaluate and simplify comparable/numeric
   arguments as before (e.g. redundant-argument collapsing and local-zero
   detection), leaving an unevaluated `Max`/`Min` object only when arguments
   are not orderable.
4. The system SHALL continue to derive assumption/property queries
   (such as sign, zero-ness, and other mathematical assumptions) of a
   `Max`/`Min` expression from its arguments exactly as before.
5. The system SHALL continue to support rewriting `Max`/`Min` into equivalent
   forms (such as `Heaviside`, `Piecewise`, and `Abs`) with unchanged results.
6. The system SHALL preserve the existing evaluation, root/real_root, and
   instantiation behaviors that interact with `Max`/`Min` so that no
   previously passing behavior changes as a result of the empty-argument fix.
