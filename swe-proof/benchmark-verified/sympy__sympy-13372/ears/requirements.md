# Requirements: Robust numeric fallback in `evalf` for partially symbolic expressions

## Introduction

The numeric-evaluation routine `evalf` in `sympy/core/evalf.py` (invoked through
`EvalfMixin.evalf` / `.n()` on SymPy expressions) contains a fallback branch that
is used when an expression's head function has no dedicated numeric-evaluation
handler. In that branch the expression is split into its real and imaginary
parts, and each part is classified as one of: exactly zero, a concrete number,
or something else (a value that is still symbolic and cannot be reduced to a
machine float).

For the real part and the imaginary part the routine sets a machine-float value
and a precision when the part is zero or a concrete number. However, when a part
is neither zero nor a concrete number, the routine failed to establish a value
for that part's precision variable. It then unconditionally packaged the four
results (real value, imaginary value, real precision, imaginary precision) into
a tuple, which raised an `UnboundLocalError` (referencing an unassigned
precision variable) instead of signalling that the numeric reduction is
unsupported.

Because the classification of an expression's parts can depend on incidental
factors such as the ordering of a product's arguments, an expression could
evaluate successfully in one argument order and crash in another. The goal is to
make this fallback total: whenever a part cannot be reduced to a concrete
number, the numeric reduction must cleanly report that it is unsupported so the
caller falls back to returning the expression unchanged, and the result must not
depend on the incidental ordering of a product's arguments.

The affected code is the `KeyError` fallback inside `evalf` in
`sympy/core/evalf.py`, together with its consumer `EvalfMixin.evalf`.

## Requirement 1: Symbolic parts make the numeric reduction cleanly unsupported

**User story:** As a user calling `.evalf()` on an expression whose head has no
dedicated numeric handler and whose real or imaginary part remains symbolic, I
want the numeric reduction to report that it cannot proceed rather than crash,
so that evaluation degrades gracefully.

**Acceptance criteria**

1. WHEN the fallback numeric reduction in `evalf` computes the real and
   imaginary parts of an expression and the real part is neither exactly zero
   nor a concrete number, THEN `evalf` SHALL signal that numeric reduction is
   unsupported (by raising `NotImplementedError`) instead of raising
   `UnboundLocalError` or any other unhandled exception.
2. WHEN the fallback numeric reduction computes the real and imaginary parts and
   the imaginary part is neither exactly zero nor a concrete number, THEN
   `evalf` SHALL signal that numeric reduction is unsupported (by raising
   `NotImplementedError`) instead of raising `UnboundLocalError` or any other
   unhandled exception.
3. The system SHALL never assemble the four-value result tuple (real value,
   imaginary value, real precision, imaginary precision) unless a value and a
   corresponding precision have been established for both the real and the
   imaginary part.
4. IF the fallback numeric reduction reports that it is unsupported, THEN the
   public `EvalfMixin.evalf` entry point SHALL catch that signal and return the
   original expression unchanged rather than propagate an error.

## Requirement 2: Numeric evaluation is independent of product argument order

**User story:** As a user, I want `.evalf()` to give the same result regardless
of the order in which the factors of an unevaluated product were written, so
that mathematically equal inputs behave identically.

**Acceptance criteria**

1. WHEN an unevaluated product contains a symbolic factor whose head has no
   dedicated numeric handler together with a plain symbol, THEN calling
   `.evalf()` on that product SHALL return the product expression unchanged.
2. WHEN the same factors are combined into an unevaluated product in the
   opposite order, THEN calling `.evalf()` on that product SHALL return the same
   expression it returns for the original order, and SHALL NOT raise an error.
3. The system SHALL preserve the original (symbolic) expression as the result in
   these cases rather than returning a partially-numeric or malformed value.

## Requirement 3: Preserve existing numeric-evaluation behavior

**User story:** As a maintainer, I want the existing behavior of numeric
evaluation to remain intact for all cases that already worked, so that the fix
introduces no regressions.

**Acceptance criteria**

1. WHEN a component (real or imaginary part) is exactly zero, THEN the system
   SHALL contribute no value and no precision for that component, exactly as
   before.
2. WHEN a component is a concrete number, THEN the system SHALL contribute that
   component's machine-float value together with the working precision, exactly
   as before.
3. IF either the real or the imaginary part still contains an unevaluated
   symbolic real/imaginary marker, THEN `evalf` SHALL continue to report the
   reduction as unsupported.
4. The system SHALL keep producing correct numeric results for expressions that
   were already evaluable — including real and complex numbers, powers,
   exponentials, logarithms, trigonometric functions, sums, products, integrals,
   floor/ceiling and integer-part evaluations, relationals, and substitution via
   the `subs` option — with their previous values, precision, and chopping
   behavior unchanged.
5. The system SHALL preserve the behavior of evaluating a product of numeric
   factors so that such products continue to reduce to their numeric value.
