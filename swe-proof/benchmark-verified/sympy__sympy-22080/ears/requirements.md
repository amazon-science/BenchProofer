# Requirements: correct operator precedence for modulo and leading unary minus in generated code

## Introduction

SymPy's code printers (the Python/pycode printer built on
`sympy.printing.codeprinter.CodePrinter` and its `_print_Mul`, the C printer,
etc.) turn symbolic expressions into source-code strings. Two related
parenthesization defects produce source text that no longer represents the
original expression:

1. The remainder operation (`Mod`, printed with an infix `%`) has no assigned
   operator precedence, so when it appears as a factor under a leading unary
   minus the minus binds only to the left operand of `%`. For example
   `-Mod(x, y)` printed as `-x % y` computes `(-x) % y`, changing the value.
2. When a product carries a leading unary minus and reduces to a single
   numerator factor, that factor is compared against the product's *own*
   precedence, which drops to the additive level for a negative coefficient.
   As a result a lower-binding factor (a bare product, or the remainder
   operation) is emitted without the parentheses the minus requires — e.g.
   `-x**4` printed as `-x*x*x*x`.

Because the printed strings are used by `sympy.utilities.lambdify` to build
executable functions, the wrong parenthesization silently changes numeric
results when the target namespace uses the native `%`/`-` operators (e.g.
`modules=[]`) rather than a `mod` function.

The goal is to fix the precedence handling in
`sympy/printing/precedence.py` and `sympy/printing/codeprinter.py` so the
generated source preserves the meaning of the expression, while leaving all
already-correct printings unchanged.

## Requirement 1: Modulo operator has multiplicative precedence

**User story:** As a user printing expressions containing `Mod`, I want the
remainder operation to be treated with the same binding strength as
multiplication, so that surrounding operators parenthesize it correctly.

**Acceptance criteria**
1. The system SHALL assign the remainder operation (`Mod`) an operator
   precedence equal to that of multiplication.
2. WHEN a `Mod` expression appears as an operand of an operator that binds more
   tightly than multiplication, THEN the printer SHALL wrap the `Mod` operand in
   parentheses.
3. WHEN a `Mod` expression is printed at top level with no surrounding operator,
   THEN the Python-code printer SHALL emit it as `<lhs> % <rhs>` without adding
   outer parentheses (e.g. `Mod(x, 2)` prints as `x % 2`).

## Requirement 2: A negated single factor is parenthesized by minus binding strength

**User story:** As a user printing negated expressions, I want a leading unary
minus to govern the whole factor it applies to, so that the printed source
computes the negation of the entire factor rather than of only its first piece.

**Acceptance criteria**
1. WHEN a code printer renders a product whose overall sign is negative and
   whose numerator consists of exactly one factor, THEN that factor SHALL be
   parenthesized whenever it binds less tightly than an exponentiation (that is,
   its operator precedence is below that of exponentiation), so that the leading
   minus governs the whole factor.
2. WHEN the single negated factor is a remainder operation, THEN the Python-code
   printer SHALL emit it wrapped, so that `-Mod(x, y)` prints as `-(x % y)`.
3. WHEN the single negated factor is a product of two or more factors, THEN the
   printer SHALL emit that product wrapped, so that the negation of `x*x*x*x`
   prints as `-(x*x*x*x)` and the negation of `x*x` prints as `-(x*x)`.
4. WHEN the single negated factor binds at least as tightly as an exponentiation
   (for example a `Pow` such as `x**2`, so that `-x**2` prints as `-x**2`), THEN
   the printer SHALL NOT add parentheses around that factor.
5. IF a product carries a leading minus but has more than one numerator factor,
   OR has a non-negative sign, THEN each numerator factor SHALL be
   parenthesized against the product's own precedence exactly as before (the
   special single-negated-factor handling SHALL NOT apply).

## Requirement 3: Modulo of a negated operand keeps its inner parentheses

**User story:** As a user printing a modulo whose dividend is itself negative, I
want the dividend to be parenthesized, so that the printed source applies the
remainder to the negated value.

**Acceptance criteria**
1. WHEN the left operand of a `Mod` prints with a precedence below that of the
   remainder operation, THEN the Python-code printer SHALL wrap that operand in
   parentheses.
2. WHEN a `Mod` has a negated left operand, THEN the Python-code printer SHALL
   emit it with the dividend parenthesized, so that `Mod(-x, y)` prints as
   `(-x) % y`.

## Requirement 4: lambdify produces the same numeric result regardless of module backend

**User story:** As a user calling `lambdify`, I want a function built for the
native-operator backend to compute the same values as one built for the default
math backend, so that choosing an empty module list does not change results.

**Acceptance criteria**
1. WHEN an expression containing a negated remainder such as `-(x % y)` is
   lambdified with no explicit modules and separately with an empty module list,
   THEN both generated functions SHALL return equal results for the same inputs.
2. WHEN the negated-modulo function is evaluated at dividend `3` and divisor `7`,
   THEN the result SHALL equal `-3`.

## Requirement 5: Preserve existing correct printings (regression protection)

**User story:** As a maintainer, I want the precedence fix to leave all
previously-correct code-printer output unchanged, so that no other expression
form regresses.

**Acceptance criteria**
1. The system SHALL keep printing an exponentiation as `<base>**<exp>` (e.g.
   `x**y`).
2. The system SHALL keep printing boolean conjunction and disjunction as
   `<a> and <b>` and `<a> or <b>`.
3. The system SHALL leave the expand-power optimization's rendering of
   negative-exponent (reciprocal) powers unchanged: a reciprocal power whose
   magnitude is small enough to expand SHALL still be rendered as a
   floating-point reciprocal of the expanded product of the repeated base
   factors, and a reciprocal power whose magnitude is too large to expand SHALL
   still be rendered through the `pow` function.
4. WHEN the expand-power optimization rewrites a positive integer power into an
   explicit product of repeated base factors and that expanded product occurs as
   a negated term within a larger sum, THEN the C printer SHALL wrap the negated
   repeated-factor product in parentheses (consistently with the
   single-negated-factor rule of Requirement 2), while leaving any non-negated
   expanded product and any `pow`-function-rendered term without added
   parentheses.
5. The system SHALL leave unchanged the printing of products that are not a
   single negated factor, including numerator/denominator assembly and the
   parenthesization of denominator groups.
