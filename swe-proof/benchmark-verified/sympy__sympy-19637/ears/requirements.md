# Requirements: robust marker-substitution flag in `kernS`

## Introduction

`kernS`, in `sympy/core/sympify.py`, is a helper that sympifies a string while
using a "kerning" hack to keep autosimplification from distributing a leading
number or minus sign across the terms of an `Add` (for example, keeping
`2*(x + y)` and `-(x + 1)` unexpanded). To do this it optionally enters a
bracket-handling branch (taken when the input contains a `(` and is not quoted),
rewrites the string, and — if the rewritten string still contains a space —
substitutes a freshly generated unique marker for the spaces. It then records
whether that marker is present so it can later be cleared from the result.

The problem: the flag that records marker presence was only assigned along the
code path where a space was actually present. When the bracket-handling branch
was entered but the rewritten string contained no space (so no marker was ever
generated), the code still tried to read that flag, raising
`UnboundLocalError: local variable 'kern' referenced before assignment`. As a
result, valid inputs such as `"(2*x)/(x-1)"` crashed instead of sympifying.

The goal: ensure the marker-presence flag is always well-defined so `kernS`
never aborts with an `UnboundLocalError`, that parenthesized inputs which
produce no space after rewriting are sympified normally, and that all previously
supported `kernS` behaviors are preserved.

## Requirement 1: `kernS` must not fail on parenthesized inputs that produce no space

**User story:** As a user calling `kernS` on a parenthesized expression string,
I want it to return the parsed expression instead of raising an internal error,
so that valid inputs are handled reliably.

**Acceptance criteria**

1. WHEN `kernS` is called with a string containing `(` and no quote characters
   whose rewritten form contains no space (so no unique marker is generated),
   THEN `kernS` SHALL return the sympified expression WITHOUT raising an
   `UnboundLocalError` or any other unexpected exception.
2. WHEN `kernS` is called with the string `"(2*x)/(x-1)"`, THEN `kernS` SHALL
   return the SymPy expression equal to `2*x/(x - 1)`.
3. IF the bracket-handling branch is entered but no space is present at the
   marker-substitution point, THEN `kernS` SHALL treat the marker as absent
   (the marker-presence flag is unset) and SHALL return the sympified expression
   directly without attempting any marker-clearing substitution.

## Requirement 2: the marker-presence flag is always defined

**User story:** As a maintainer of `kernS`, I want the flag that records whether
the unique marker was inserted to be defined on every code path, so that reading
it can never reference an unassigned variable.

**Acceptance criteria**

1. The system SHALL ensure the marker-presence flag has a defined value for
   every input, regardless of whether the bracket-handling branch is entered and
   regardless of whether a space is present within that branch.
2. WHEN the bracket-handling branch is entered AND a space is present so the
   unique marker is substituted for the spaces, THEN `kernS` SHALL record the
   marker as present and SHALL clear that marker from the resulting expression
   before returning.
3. WHEN the bracket-handling branch is NOT entered (the input has no `(` or is
   quoted), THEN `kernS` SHALL record the marker as absent and SHALL return the
   sympified expression directly.

## Requirement 3: preserve existing `kernS` behavior (regression protection)

**User story:** As an existing user of `kernS`, I want all previously supported
conversions to keep working exactly as before, so that the fix introduces no
behavioral regressions.

**Acceptance criteria**

1. WHEN `kernS` is given a leading numeric coefficient multiplying a
   parenthesized sum, such as the documented example `"2*(x + y)"`, THEN it
   SHALL return an expression that preserves the unexpanded product rather than
   distributing the coefficient across the sum's terms.
2. WHEN `kernS` is given a sign-prefixed (e.g. negated) parenthesized sum, such
   as the documented example `"-(x + 1)"`, THEN it SHALL return an expression
   that preserves the unexpanded grouped sum rather than distributing the sign
   across the terms.
3. WHEN `kernS` is given an input in which a numeric coefficient or sign
   multiplies a grouped sum that itself contains further nested groups or
   function calls, THEN it SHALL keep every such grouped sum unexpanded rather
   than distributing coefficients or signs into it.
4. WHEN `kernS` is given an input in which arithmetic appears inside the
   argument of a constructor or function call, THEN it SHALL preserve that
   argument arithmetic in unevaluated form (as unevaluated `Add`/`Mul`) rather
   than folding it into a single pre-computed number.
5. WHEN `kernS` is given an input whose grouped factor carries a negative
   integer power, THEN it SHALL return an expression that keeps the grouped sum
   unexpanded and reflects that negative power (as the corresponding reciprocal
   scaling of the group).
6. WHEN `kernS` is given an input whose leading coefficient is written as a
   floating-point literal, THEN it SHALL preserve that coefficient as a
   floating-point number (not silently promote it to an exact rational).
7. WHEN `kernS` is given two inputs that denote the same expression but differ
   only in insignificant whitespace or in the ordering of a commutative product,
   THEN it SHALL return equal expressions for both.
8. WHEN `kernS` is given an input that names a recognized mathematical constant
   raised to a signed grouped exponent, THEN it SHALL return the corresponding
   SymPy expression for that construct (e.g. the exponential of the negated
   argument) with the grouping honored.
9. WHEN `kernS` is given an input that subtracts a parenthesized group which
   algebraically cancels to a constant, THEN it SHALL return an expression that
   is NOT structurally equal to that constant but whose expansion equals it (the
   cancellation stays deferred, not auto-simplified away).
10. WHEN `kernS` is given a string whose only content is a symbol name that
    begins with an underscore, THEN it SHALL return the corresponding `Symbol`
    unchanged, with no marker characters accidentally introduced into or removed
    from the name.
11. WHEN `kernS` is given a list or tuple of expression strings (including nested
    containers), THEN it SHALL return the same container structure with each
    element sympified using the same unexpanded-grouping behavior.
12. WHENEVER a unique marker was substituted for spaces during processing, the
    system SHALL leave no residual marker characters in any returned expression:
    every such marker SHALL be cleared from the result before it is returned.
