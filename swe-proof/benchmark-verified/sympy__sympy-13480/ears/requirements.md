# Requirements — coth evaluation of additive arguments with an imaginary half-period part

## Introduction

The hyperbolic cotangent class `coth` (in
`sympy/functions/elementary/hyperbolic.py`) automatically simplifies its
argument at construction time through its `eval` classmethod. When the argument
is a sum (`Add`), `coth.eval` splits it into a "rest" part and a multiple of the
imaginary half-period `I*pi/2` (via the module helper `_peeloff_ipi`), and uses
the value of `coth` applied to that multiple to decide how to reduce the whole
expression to a periodicity-shifted form.

This additive-argument branch is currently broken: after computing `coth` of the
half-period multiple, it tests a name that was never assigned in that branch, so
evaluating `coth` of any sum whose imaginary part is a nonzero multiple of
`pi/2` raises a `NameError` instead of returning a simplified result. The user-
visible symptom is that `coth(log(tan(x))).subs(x, n)` errors for integer values
of `x` whose tangent forces such a shift (e.g. 2, 3, 5, 6, 8, 9, …).

The goal is to make `coth.eval` complete this additive-argument reduction
correctly for every such argument, using the value it actually computed, while
leaving all other `coth` simplifications and the behavior of the other
hyperbolic functions unchanged.

## Requirement 1: coth of a sum with a half-period imaginary part reduces without error

**User story:** As a user building symbolic expressions, I want `coth` of a sum
that contains an imaginary multiple of `pi/2` to simplify automatically instead
of raising an error, so that I can substitute and manipulate such expressions.

**Acceptance criteria**

1. WHEN `coth` is constructed with an additive argument from which a nonzero
   multiple of the imaginary half-period `I*pi/2` can be separated, THEN
   `coth.eval` SHALL return a simplified expression and SHALL NOT raise a
   `NameError` (or any other exception) for that argument.
2. WHEN such an additive argument is split into a remaining part `x` and a
   nonzero half-period multiple `m`, THEN `coth.eval` SHALL base its reduction on
   the value obtained by applying `coth` to that multiple `m`, not on any other
   quantity.
3. IF applying `coth` to the separated multiple `m` yields complex infinity
   (the `zoo` singleton, `S.ComplexInfinity`), THEN `coth.eval` SHALL return
   `coth` of the remaining part `x`.
4. IF applying `coth` to the separated multiple `m` yields zero (the remaining
   case, i.e. it is not complex infinity), THEN `coth.eval` SHALL return `tanh`
   of the remaining part `x`.
5. WHEN the argument is a sum whose separable half-period multiple is an even
   multiple of `I*pi/2` (an integer multiple of `I*pi`), THEN the reduction
   SHALL follow the complex-infinity case and yield `coth` of the remaining
   part.
6. WHEN the argument is a sum whose separable half-period multiple is an odd
   multiple of `I*pi/2`, THEN the reduction SHALL follow the zero case and yield
   `tanh` of the remaining part.

## Requirement 2: periodicity-shift outcomes hold automatically

**User story:** As a user, I want the reductions implied by the `I*pi/2`
periodicity of `coth` to hold at evaluation time, so that arguments related by
such a shift compare equal after automatic evaluation.

**Acceptance criteria**

1. WHEN two additive arguments differ only by a nonzero integer multiple of the
   full imaginary period `I*pi` (equivalently, by an even multiple of the
   half-period `I*pi/2`), THEN `coth` SHALL evaluate both arguments to equal
   expressions, because the even-multiple reduction yields `coth` of the common
   remaining part in each case.
2. WHEN `coth` is applied to a sum of a remaining part `x` and an odd multiple
   of the imaginary half-period `I*pi/2`, THEN the evaluated result SHALL equal
   `tanh(x)`.
3. The system SHALL produce these results at construction/evaluation time,
   without requiring an explicit simplification or substitution call beyond
   normal expression building.

## Requirement 3: preserve existing coth and hyperbolic-function behavior

**User story:** As a maintainer, I want the fix to be surgical, so that the
established simplifications of `coth` and the other hyperbolic functions keep
working exactly as before.

**Acceptance criteria**

1. The system SHALL keep all pre-existing `coth` argument simplifications
   unchanged: `coth(nan)` is `nan`; `coth` of positive infinity is `1`; `coth`
   of negative infinity is `-1`; `coth(0)` is complex infinity; `coth` of a
   negative numeric argument is the negation of `coth` of its negation; and
   `coth` of complex infinity is `nan`.
2. WHEN the argument is a nonzero real multiple of the imaginary unit, THEN
   `coth` SHALL continue to reduce to the corresponding imaginary-unit multiple
   of `cot` of the real coefficient (with the sign handling for negative
   coefficients preserved).
3. WHEN the argument is one of the inverse-hyperbolic functions `asinh`,
   `acosh`, `atanh`, or `acoth`, THEN `coth` SHALL continue to reduce to its
   established closed form for that inverse function.
4. The system SHALL leave the automatic evaluation, series expansion, rewriting,
   and derivative behavior of the other hyperbolic and inverse-hyperbolic
   functions (`sinh`, `cosh`, `tanh`, `csch`, `sech`, and the inverse forms)
   unchanged.
5. WHEN `coth` is applied to an integer multiple of `pi*I`, THEN it SHALL
   continue to reduce to the established `-cot(...)*I` form.
