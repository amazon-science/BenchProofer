# Requirements: full-precision rational rendering for the mpmath lambda printer

## Introduction

When SymPy generates code for the arbitrary-precision `mpmath` backend
(via `lambdify(..., modules='mpmath')`, which internally uses the mpmath lambda
printer `MpmathPrinter` in `sympy/printing/pycode.py`), rational numbers are
emitted as a plain textual quotient such as `232/3`. Because that quotient is
evaluated as an ordinary Python division at machine precision, any downstream
consumer that expects arbitrary precision — most notably `nsolve` — silently
loses precision: solving an equation whose constant term is a rational returns
only ~15–16 correct digits regardless of the requested `prec`.

The goal is to make the mpmath lambda printer render each rational so that its
numerator and denominator are each constructed as mpmath floating-point values,
so the division happens at the working precision of mpmath rather than in native
Python floats. This must not change how other code printers render rationals,
and must not disturb any other behavior of the mpmath printer.

Affected code:
- `sympy/printing/pycode.py` — the `MpmathPrinter` class (the mpmath lambda
  printer), which currently defines `_print_Float`, `_print_uppergamma`,
  `_print_lowergamma`, `_print_log2`, `_print_log1p` but has no rational-specific
  rendering, so rationals fall through to the base string printer.
- `sympy/solvers/numeric.py` — `nsolve`, the numeric solver that consumes the
  mpmath-lambdified expression and is the visible beneficiary of the fix.

## Requirement 1: mpmath printer renders rationals at full precision

**User story:** As a user lambdifying a SymPy expression to the mpmath backend,
I want rational constants to be constructed as mpmath floats, so that arithmetic
on them is carried out at mpmath's working precision instead of native Python
double precision.

**Acceptance criteria**

1. WHEN the mpmath lambda printer (`MpmathPrinter`) prints a SymPy `Rational`
   with numerator `p` and denominator `q`, THEN the printer SHALL produce the
   string `mpmath.mpf(<p>)/mpmath.mpf(<q>)`, where `<p>` and `<q>` are the
   decimal integer texts of `p` and `q` respectively.
2. WHEN the mpmath lambda printer prints a `Rational`, THEN each of the
   numerator and the denominator SHALL be wrapped in a separate `mpmath.mpf(...)`
   constructor call, and the two constructor calls SHALL be combined with a
   single `/` division operator.
3. WHEN the mpmath lambda printer prints the rational constant shown in the
   reported issue (two hundred thirty-two over three), THEN it SHALL produce
   `mpmath.mpf(232)/mpmath.mpf(3)` — the wrapped-and-divided form — rather than
   the bare textual quotient `232/3` that the printer emitted before the fix.
4. IF the numerator or denominator is negative, THEN the rendered integer text
   SHALL carry a leading minus sign exactly as Python's `str` of that integer
   would render it (no other reformatting of the integer value).
5. The rendered `mpmath` name used for the constructor SHALL be the module-
   qualified name produced by the printer's existing module-name resolution
   (i.e. `mpmath.mpf` under the printer's default fully-qualified-module
   configuration), not a hard-coded literal that bypasses that resolution.
6. WHEN a rational is rendered by this printer, THEN the output SHALL NOT be the
   bare textual quotient `<p>/<q>` of unwrapped integers.

## Requirement 2: preserve all other mpmath-printer behavior

**User story:** As a maintainer, I want the new rational handling to be additive,
so that every other expression the mpmath printer already handled keeps printing
exactly as before.

**Acceptance criteria**

1. WHEN the mpmath lambda printer prints any expression it already supported
   before this change — including symbolic functions it maps to a
   module-qualified `mpmath.<name>(...)` call via its inherited function-name
   dispatch — THEN it SHALL render that expression exactly as it did before,
   with byte-identical output; the newly added rational handling SHALL be
   purely additive and SHALL NOT alter any pre-existing rendering.
2. The mpmath printer SHALL continue to render `Float` values by wrapping the
   float in an `mpmath.mpf(...)` constructor built from the float's internal
   mpf representation, unchanged by this work.
3. The system SHALL leave the mpmath printer's existing special-case renderings
   (upper/lower incomplete gamma, base-2 logarithm, and log-of-one-plus) exactly
   as they were.

## Requirement 3: do not affect other code printers

**User story:** As a user of the other code backends, I want their rational
output unchanged, so that only the mpmath backend gains full-precision wrapping.

**Acceptance criteria**

1. WHEN the plain Python code printer prints an expression, THEN its rendering of
   rationals and all other constructs SHALL remain exactly as before (the mpmath
   wrapping SHALL NOT leak into it).
2. WHEN the NumPy code printer or the SciPy code printer prints an expression,
   THEN its output SHALL remain exactly as before.
3. The system SHALL keep the reserved-word handling, the custom print-method
   dispatch, and the code-generation AST node renderings of the code printers
   behaving as they did before.

## Requirement 4: nsolve returns results at the requested precision

**User story:** As a user calling `nsolve` with a high `prec`, I want the answer
to be accurate to that many digits even when the equation contains rational
constants, so that the requested precision is actually delivered.

**Acceptance criteria**

1. WHEN `nsolve` solves an equation whose expression contains a rational
   constant and the caller requests a precision of `prec` digits, THEN the
   returned root SHALL be accurate to the requested precision (limited only by
   the conditioning of the problem), not truncated to native double precision.
2. WHEN `nsolve` is asked to solve a linear equation whose only non-symbolic
   term is a single non-terminating rational constant, requesting a precision
   well beyond native double precision, THEN the returned root SHALL agree with
   that rational evaluated to the requested precision across all requested
   digits, not merely to the ~15–16 digits of a double-precision approximation.
3. The system SHALL keep every previously supported `nsolve` usage working
   unchanged; adding rational wrapping to the mpmath printer SHALL be a purely
   additive change that does not regress any existing solving behavior for the
   full range of inputs and options `nsolve` already accepted.
