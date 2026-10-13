# Requirements: precomputed closed-form CDFs for continuous distributions

## Introduction

In `sympy.stats`, continuous distributions are defined by a probability density
function (PDF), and the cumulative distribution function (CDF) exposed through
the public `cdf` helper is obtained by integrating that density. For several
distributions this symbolic integration does not converge, hangs, or returns an
unevaluated `Integral`, so `cdf(...)( point )` fails to produce a usable value.

This is the case for the arcsin distribution created by
`sympy.stats.Arcsin(name, a, b)`, whose distribution object is
`ArcsinDistribution` in `sympy/stats/crv_types.py`. Its density is
`1/(pi*sqrt((x - a)*(b - x)))` on the interval `[a, b]`, and asking for its CDF
currently yields an unevaluated integral (e.g. of the form
`Integral(1/sqrt(-_x**2 + 3*_x), (_x, -oo, 1))/pi`) that does not converge —
even though the arcsin distribution has a well-known closed-form CDF (it is,
after all, the arcsine of a rescaled argument).

The arcsin distribution is the motivating case, but it is not alone: a family
of continuous distributions in `sympy/stats/crv_types.py` suffers the same
defect — their CDF queries hang, fail to converge, or come back as unevaluated
integrals or unusable expressions. The goal is to give each affected
distribution an internal precomputed closed-form CDF so that the public `cdf`
helper returns a correct, usable symbolic expression for all of them — the
arcsin case is specified in detail below, and Requirement 4 pins the full set
— while leaving every density and every unaffected distribution untouched.

## Requirement 1: Closed-form CDF for the arcsin distribution

**User story:** As a user of `sympy.stats`, I want `cdf` of an arcsin random
variable to return an exact closed-form expression, so that I can evaluate and
manipulate the arcsine cumulative distribution instead of receiving an
unevaluated integral that never converges.

**Acceptance criteria**

1. WHEN a caller builds `X = Arcsin(name, a, b)` with left boundary `a` and
   right boundary `b` and evaluates `cdf(X)(x)`, THEN the system SHALL return a
   closed-form symbolic expression that contains no unevaluated `Integral` over
   the density.

2. WHEN `cdf(X)(x)` is evaluated for `X = Arcsin(name, a, b)`, THEN the system
   SHALL return a three-case piecewise expression whose cases are, in order:
   the value `0` for the region left of the support; the arcsine closed form
   `2*asin(sqrt((x - a)/(b - a)))/pi` for the region on the support; and the
   value `1` for the remaining region.

3. IF the evaluation point `x` lies strictly to the left of the left boundary
   `a` (i.e. `x < a`), THEN the system SHALL give the CDF value `0`.

4. WHILE the evaluation point `x` lies within the support up to and including
   the right boundary `b` (i.e. `x <= b`, once the left-of-support case has been
   ruled out), the system SHALL give the CDF value
   `2*asin(sqrt((x - a)/(b - a)))/pi`.

5. IF the evaluation point `x` lies to the right of the right boundary (the
   fall-through case once neither prior condition holds), THEN the system SHALL
   give the CDF value `1`.

6. The piecewise result SHALL present its three cases in evaluation order so
   that the first case selects the region strictly left of the left boundary
   `a` (yielding `0`), the second case selects the on-support region bounded by
   the right boundary `b` (yielding the arcsine closed form), and the third case
   is an unconditional fall-through for the remaining region (yielding `1`); the
   region conditions SHALL be the boundary comparisons of `x` against `a` and
   `b`, in whatever equivalent orientation the system canonicalizes them to.

7. WHEN the boundaries `a` and `b` are symbolic (non-numeric) symbols, THEN the
   system SHALL still return the piecewise closed form described above without
   attempting numerical integration and without hanging.

## Requirement 2: CDF is a valid antiderivative of the density

**User story:** As a user relying on the arcsin CDF, I want it to be the true
cumulative distribution of the arcsin density, so that differentiating the CDF
reproduces the PDF.

**Acceptance criteria**

1. WHEN the returned arcsin CDF expression is differentiated with respect to the
   evaluation variable on the open support interval `(a, b)`, THEN the system
   SHALL yield an expression numerically equal to the arcsin density
   `1/(pi*sqrt((x - a)*(b - x)))` at points inside that interval.

2. The arcsin CDF SHALL evaluate to `0` at the left boundary and to `1` at the
   right boundary, consistent with a cumulative distribution function over
   `[a, b]`.

## Requirement 3: Preserve the existing arcsin density

**User story:** As a maintainer, I want the arcsin density to remain exactly as
before, so that adding a closed-form CDF introduces no regression.

**Acceptance criteria**

1. WHEN a caller evaluates `density(X)(x)` for `X = Arcsin(name, a, b)`, THEN
   the system SHALL keep returning `1/(pi*sqrt((-x + b)*(x - a)))`, unchanged by
   the addition of the CDF.

## Requirement 4: Precomputed CDFs for the affected distribution family

**User story:** As a `sympy.stats` user, I want every distribution whose CDF
previously hung or came back unevaluated to gain a precomputed closed form,
so that `cdf` is usable across the family, not just for arcsin.

**Acceptance criteria**

1. The system SHALL provide an internal precomputed CDF for each of these
   continuous distributions: arcsin, Dagum, Frechet, Gamma (and therefore
   Erlang, which is the integer-shape Gamma), inverse Gamma, Kumaraswamy,
   Laplace, Logistic, Nakagami, Student's t, and uniform-sum.
2. WHEN `cdf(X)(x)` is evaluated for a random variable of one of the listed
   distributions, THEN the system SHALL return an explicit symbolic
   expression (a closed form, possibly piecewise, in terms of standard and
   special functions) rather than an unevaluated integral, and the evaluation
   SHALL complete rather than hang — including cases that previously hung or
   returned unusable results (e.g. the Kumaraswamy and Laplace CDFs).
3. Each listed distribution's returned CDF SHALL be mathematically correct
   for its density: differentiating it SHALL recover the density on the
   support, and it SHALL take the value `0` at (or in the limit toward) the
   left end of the support and `1` at (or in the limit toward) the right end.
4. Because closed forms replace on-the-fly integration, a CDF value that was
   previously produced by symbolic integration MAY now be returned in a
   different but mathematically equivalent form (e.g. an exact expression such
   as `1 - exp(-1)` where a float or an unevaluated form was produced
   before); the system SHALL preserve the VALUE, not the previous textual
   shape.

## Requirement 5: No regression for unaffected distributions and helpers

**User story:** As a maintainer, I want distributions outside the listed
family and the surrounding statistics machinery to behave exactly as before,
so the change is additive.

**Acceptance criteria**

1. The system SHALL leave the observable behavior of every continuous
   distribution NOT listed in Requirement 4 unchanged: any density,
   cumulative distribution, or other `sympy.stats` query on those
   distributions that produced a given result before this change SHALL
   produce the same result after it.
2. The system SHALL keep every distribution's DENSITY unchanged (including
   the listed ones), and SHALL NOT alter the signatures or defaults of any
   public `sympy.stats` entry point.
