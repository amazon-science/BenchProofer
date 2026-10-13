# Requirements: Automatic closed-form evaluation of the polylogarithm

## Introduction

The polylogarithm special function `polylog(s, z)` lives in
`sympy/functions/special/zeta_functions.py` as the `polylog` class. When a
`polylog(s, z)` object is constructed, SymPy invokes the class method
`polylog.eval(cls, s, z)`, which either returns a closed-form expression for the
value (in which case the constructed object *is* that expression) or returns
nothing, leaving the call in unevaluated `polylog(s, z)` form.

At the base revision, `polylog.eval` recognizes only the arguments `z = 1`,
`z = -1`, and `z = 0`; for every other pair it stays unevaluated. As a result,
well-known closed forms such as `polylog(2, 1/2)` are never produced
automatically, and `polylog(0, z)` / `polylog(-1, z)` are not reduced to their
elementary rational forms.

Separately, the function-expansion routine `polylog._eval_expand_func`
(reached through `expand_func`) rewrites `polylog(1, z)` using a spurious
polar-exponential factor `exp_polar(-I*pi)`, so that `expand_func(polylog(1, z))`
yields `-log(z*exp_polar(-I*pi) + 1)` instead of the mathematically equivalent,
branch-consistent `-log(1 - z)`.

The goals are: (1) extend `polylog.eval` so that recognized orders and arguments
evaluate to correct closed forms that numerically agree with the polylogarithm's
true value; (2) clean up the `s = 1` expansion in `polylog._eval_expand_func` so
it no longer carries the polar-exponential factor; and (3) preserve all existing
evaluation behavior of `polylog` and of the neighbouring functions in the same
module (`zeta`, `dirichlet_eta`, and `stieltjes`).

Throughout, "numerically agree" means: the floating-point evaluation of the
returned closed-form expression matches the floating-point evaluation of the
same `polylog(s, z)` call taken in its unevaluated form, to within a tolerance
on the order of 1e-15.

## Requirement 1: Evaluate order-2 polylogarithm at recognized arguments

**User story:** As a user of SymPy's special functions, I want
`polylog(2, z)` to automatically produce its known closed form for the classic
dilogarithm arguments, so that these values simplify without extra effort.

**Acceptance criteria**
1. WHEN `polylog` is constructed with order `s = 2` and argument `z = 1/2`
   (the SymPy rational one-half), THEN the constructed result SHALL equal the
   closed form "π²⁄12 − (log 2)²⁄2".
2. WHEN `polylog` is constructed with order `s = 2` and argument `z = 2`, THEN
   the constructed result SHALL equal the closed form "π²⁄4 − iπ·log 2", where
   `i` is the imaginary unit.
3. WHEN `polylog` is constructed with order `s = 2` and the argument is any one
   of the six recognized dilogarithm arguments — one-half; two; the golden-ratio
   values (√5 − 1)⁄2, −(√5 − 1)⁄2, −(√5 + 1)⁄2, and (3 − √5)⁄2 — THEN the
   constructed result SHALL be a closed-form expression (built from π, `log`, and
   `√5`) rather than an unevaluated `polylog` call.
4. WHILE evaluating any of the six recognized order-2 arguments in criterion 3,
   the returned closed-form expression SHALL numerically agree with the
   unevaluated `polylog(2, z)` value.
5. IF the order is `2` but the argument is none of the six recognized values,
   THEN `polylog.eval` SHALL return nothing so the call remains the unevaluated
   `polylog(2, z)`.

## Requirement 2: Evaluate the polylogarithm at orders 0 and −1

**User story:** As a user, I want `polylog(0, z)` and `polylog(-1, z)` to reduce
to their elementary rational forms, so that non-positive integer orders evaluate
to closed forms.

**Acceptance criteria**
1. WHEN `polylog` is constructed with order `s = 0` and a general argument `z`,
   THEN the constructed result SHALL equal the rational expression `z / (1 − z)`.
2. WHEN `polylog` is constructed with order `s = -1` and a general argument `z`,
   THEN the constructed result SHALL equal the rational expression
   `z / (1 − z)²`.
3. The system SHALL ensure that the closed forms for orders `0` and `-1`
   numerically agree with the corresponding unevaluated `polylog(s, z)` value
   for arbitrary complex `z` (away from the singularity at `z = 1`).

## Requirement 3: Preserve consistent numeric evaluation at order 1

**User story:** As a user, I want `polylog(1, z)` to keep evaluating to the same
numeric value whether or not automatic evaluation is applied, so that adding the
new closed forms does not disturb order-1 behavior.

**Acceptance criteria**
1. WHEN `polylog` is constructed with order `s = 1` and a general complex
   argument `z`, THEN the floating-point value of the constructed result SHALL
   numerically agree with the floating-point value of the unevaluated
   `polylog(1, z)`.
2. The system SHALL NOT introduce a spurious imaginary offset or branch shift at
   order 1 that would make the automatically-evaluated value differ from the
   unevaluated value.

## Requirement 4: Preserve the existing argument special cases

**User story:** As a maintainer, I want the previously handled arguments to keep
their established results, so that the new evaluation table extends rather than
replaces existing behavior.

**Acceptance criteria**
1. WHEN `polylog` is constructed with argument `z = 1` for any order `s`, THEN
   the result SHALL be `zeta(s)`.
2. WHEN `polylog` is constructed with argument `z = -1` for any order `s`, THEN
   the result SHALL be `-dirichlet_eta(s)`.
3. WHEN `polylog` is constructed with argument `z = 0` for any order `s`, THEN
   the result SHALL be the SymPy symbolic zero (an object that is a SymPy
   expression, equal to zero).

## Requirement 5: Remove the spurious polar factor from the order-1 expansion

**User story:** As a user calling `expand_func`, I want `expand_func(polylog(1, z))`
to return the plain logarithmic form, so that the expansion is
branch-consistent and its derivative matches the polylogarithm's derivative.

**Acceptance criteria**
1. WHEN `expand_func` is applied to `polylog(1, z)`, THEN `polylog._eval_expand_func`
   SHALL return `-log(1 - z)`, with no `exp_polar` factor present in the result.
2. The system SHALL keep the expansion of `polylog(s, z)` for non-positive
   integer orders (`s` an integer with `s ≤ 0`) producing the elementary rational
   expression obtained from the standard `u/(1 − u)` derivative recurrence
   evaluated at `u = z`; in particular `expand_func(polylog(0, z))` SHALL equal
   `z / (1 − z)`.

## Requirement 6: Preserve evaluation and derivative structure of the polylog API

**User story:** As a maintainer, I want the polylogarithm's other public
behaviors to remain intact, so that this change is additive.

**Acceptance criteria**
1. The system SHALL keep the derivative of `polylog(s, z)` with respect to `z`
   equal to `polylog(s - 1, z) / z`.
2. The system SHALL keep the rewrite of `polylog(s, z)` in terms of the Lerch
   transcendent equal to `z · lerchphi(z, s, 1)`.
3. WHEN order and argument are both left symbolic (no recognized special case),
   THEN `polylog(s, z)` SHALL remain unevaluated.

## Requirement 7: Preserve neighbouring special-function behavior

**User story:** As a maintainer, I want the sibling functions defined in the same
module to be unaffected, so that editing the polylogarithm does not regress them.

**Acceptance criteria**
1. The system SHALL keep the evaluation behavior of `zeta` (including its special
   values and unevaluated cases) unchanged.
2. The system SHALL keep the evaluation behavior of `dirichlet_eta` unchanged.
3. The system SHALL keep the evaluation and floating-point behavior of the
   `stieltjes` constants function unchanged.
4. The system SHALL keep the `zeta_functions` module importable, so that all of
   its exported special functions continue to load without error.
