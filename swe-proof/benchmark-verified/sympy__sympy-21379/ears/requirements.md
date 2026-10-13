# Requirements: Tolerate factor-extraction failures in modulo evaluation

## Introduction

Evaluating a symbolic modulo operation (`Mod`, exposed through the `%`
operator on SymPy expressions in `sympy/core/mod.py`) includes an optional
simplification step: before reducing `p % q`, the evaluator asks the polynomial
`gcd` routine (`sympy.polys.polytools.gcd`) for a common factor of the dividend
`p` and divisor `q`, and — when a non-trivial factor is found — divides it out
of both operands via `gcd_terms`.

For some symbolic operands the `gcd` routine cannot form a polynomial and
raises `PolynomialError`. A prominent case is an operand containing a
`Piecewise` expression, where `gcd` reports that "Piecewise generators do not
make sense". Because `Mod.eval` called `gcd` without guarding against this
error, the exception escaped `Mod` and propagated up through every caller that
constructs a `Mod` — most damagingly through assumption queries (e.g.
`is_zero`/`is_real` of hyperbolic functions such as `sinh`, `cosh`, `tanh`,
which internally compute `im % pi`). The observable symptom was that operations
as ordinary as `expr.subs({1: 1.0})` on `exp(sinh(Piecewise(...)/z))` raised an
unexpected `PolynomialError`.

The goal is to make modulo evaluation *tolerant* of a failed common-factor
extraction: the failure must be caught and the step must fall back to treating
the common factor as the unit `1`, leaving the operands unchanged, so that
`Mod` construction and all downstream queries complete normally instead of
aborting. Every pre-existing modulo simplification behavior must be preserved.

## Requirement 1: Tolerate a failing common-factor extraction

**User story:** As a user building expressions that involve `Mod` (directly via
`%`, or indirectly through functions and assumption queries), I want modulo
evaluation to succeed even when the internal common-factor extraction cannot
handle the operands, so that ordinary operations do not abort with an
unexpected error.

**Acceptance criteria**

1. WHEN `Mod.eval` performs its common-factor extraction step and the
   polynomial `gcd` routine raises `PolynomialError` for the given dividend and
   divisor, THEN `Mod.eval` SHALL catch that error and continue evaluation
   rather than allowing it to propagate to the caller.
2. IF the common-factor extraction fails with `PolynomialError`, THEN
   `Mod.eval` SHALL treat the common factor as the unit `1` and SHALL leave
   both the dividend and the divisor unchanged for the remainder of the
   evaluation (no division-out step is applied).
3. WHEN a modulo expression is constructed whose operands cause `gcd` to raise
   `PolynomialError` (for example, an operand containing a `Piecewise`), THEN
   the construction SHALL complete and return a `Mod` result without raising.
4. The system SHALL restrict this tolerance to the common-factor extraction
   step only; any error not arising from that step SHALL continue to propagate
   unchanged (e.g. modulo by zero SHALL still raise `ZeroDivisionError`).

## Requirement 2: Preserve successful common-factor simplification

**User story:** As a user relying on `Mod`'s existing simplifications, I want
the common-factor extraction to behave exactly as before whenever it succeeds,
so that no results change for the many expressions that already worked.

**Acceptance criteria**

1. WHEN the common-factor extraction succeeds and returns a factor different
   from `1`, THEN `Mod.eval` SHALL divide that factor out of both the dividend
   and the divisor (via the existing `gcd_terms` reduction) before completing
   evaluation, exactly as it did previously.
2. WHEN the common-factor extraction succeeds and returns the unit `1`, THEN
   `Mod.eval` SHALL leave both operands unchanged.
3. The system SHALL keep all other modulo simplification and evaluation rules
   intact, including: `Mod` of purely numeric operands returning the numeric
   remainder; `Mod` by zero raising `ZeroDivisionError`; results involving a
   non-finite operand yielding `nan`; the `Mod(p, q)` result being zero when
   `p` is zero, when `p == q` or `p == -q`, or when `p` is an integer and
   `q == 1`; and the sign of the result following the sign of the divisor.
4. The system SHALL preserve the integer/rational/non-negative assumption
   behavior and the interaction of `Mod` with powers, so that expressions
   combining `Mod` with exponentiation and the established `Mod` arithmetic
   identities continue to evaluate to their prior results.

## Requirement 3: Restore reliable assumption queries through modulo

**User story:** As a user querying assumptions or substituting into expressions
that internally invoke `Mod`, I want those queries to complete without raising,
so that expression manipulation is deterministic and does not depend on cache
state.

**Acceptance criteria**

1. WHEN an assumption query (such as `is_zero` or `is_real`) on an expression
   causes a `Mod`/`%` operation on operands containing a `Piecewise`, THEN the
   query SHALL complete and return its result (which may be an
   indeterminate/`None` answer) without raising `PolynomialError`.
2. WHEN a substitution (such as replacing integer `1` with float `1.0`) is
   applied to an expression like `exp(sinh(Piecewise((x, y > x), (y, True)) /
   z))` built from real symbols, THEN the substitution SHALL complete without
   raising.
3. WHEN a modulo operation (`%`) is applied directly to a symbolic operand
   that contains a `Piecewise` expression — for example reducing a
   `Piecewise`-based quotient modulo an integer — THEN evaluation SHALL
   complete and return a result without raising.
4. WHEN the same expression that previously triggered the error is evaluated
   repeatedly, THEN each evaluation SHALL behave identically and SHALL NOT
   raise, so that behavior does not depend on prior cached assumption state.
