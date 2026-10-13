# Requirements: Recursive numeric evaluation of implemented functions

## Introduction

SymPy lets a user attach a concrete numeric implementation to a symbolic
function via `implemented_function` (in `sympy.utilities.lambdify`), which
stores the callable on the function class as its `_imp_` attribute. When such a
function is asked for a floating-point value through `evalf`, the numeric
evaluation is handled by `Function._eval_evalf` in `sympy/core/function.py`.

For a function that has no direct mpmath counterpart, `_eval_evalf` falls back
to invoking the attached `_imp_` implementation. The defect: it applies the
implementation to the function's *symbolic* arguments as-is. When an argument is
itself an unevaluated application of another implemented function (a
composition, e.g. `f(g(2))`), the inner application is never reduced to a
number, so the implementation cannot produce a numeric result and the whole
expression comes back unevaluated instead of a float.

The goal is to make numeric evaluation of implemented functions recursive:
before applying the attached implementation, each argument must itself be
numerically evaluated, so compositions of implemented functions evaluate to a
number. Existing single-level evaluation, the mpmath-backed evaluation path, and
the graceful "cannot evaluate" fallback must all be preserved.

## Requirement 1: Recursively evaluate arguments before applying the attached implementation

**User story:** As a user who composes functions built with
`implemented_function`, I want `evalf` on a nested composition to produce a
numeric result, so that a value like `f(g(2))` evaluates instead of being
returned symbolically.

**Acceptance criteria**

1. WHEN `evalf` is invoked on an application of a function that carries an
   attached numeric implementation (`_imp_`) and that has no direct mpmath
   counterpart, THEN `Function._eval_evalf` SHALL numerically evaluate each of
   the function's arguments before applying the implementation.
2. WHEN an argument of such a function is itself an unevaluated application of
   another implemented function, THEN the argument SHALL be reduced to its
   numeric value and that value SHALL be passed to the outer implementation.
3. WHEN a composition of implemented functions such as `f(g(2))` (where `f`
   maps its input to its square and `g` maps its input to twice its value, or
   any analogous numeric implementations) is evaluated with `evalf`, THEN the
   result SHALL be the numeric value obtained by applying the outer
   implementation to the numeric value of its evaluated argument (for the
   squaring example composed on the value 4, the result SHALL equal `Float(16)`).
4. WHEN each argument is numerically evaluated, THEN it SHALL be evaluated at
   the precision requested for the overall evaluation.
5. WHEN the attached implementation has been applied to the evaluated
   arguments, THEN the returned value SHALL be a `Float` carrying the requested
   precision.

## Requirement 2: Preserve single-level and non-evaluable behavior

**User story:** As a maintainer, I want the existing behavior of `evalf` on
implemented functions to be unchanged for all cases other than the composition
bug, so that no previously working evaluation regresses.

**Acceptance criteria**

1. WHEN `evalf` is invoked on a single-level application of an implemented
   function whose argument is already a concrete number (e.g. the squaring
   implementation applied to 2), THEN the result SHALL be the numeric value of
   the implementation applied to that argument (`Float(4)` for that example).
2. IF applying the attached implementation to the evaluated arguments raises an
   `AttributeError`, `TypeError`, or `ValueError`, THEN `Function._eval_evalf`
   SHALL return no value (i.e. leave the expression unevaluated) rather than
   propagating the error.
3. WHEN the function being evaluated has a direct mpmath counterpart (directly
   by name or via the mpmath name-translation table), THEN evaluation SHALL use
   that mpmath-backed path and SHALL NOT be affected by this change.
4. The system SHALL continue to build implemented functions through
   `implemented_function` such that the numeric implementation is reachable as
   the function's `_imp_` attribute and is used by `evalf` as described above.
