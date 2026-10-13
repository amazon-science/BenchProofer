# Requirements: Reduce integer coefficients when taking a symbolic modulo of a product

## Introduction

SymPy represents an unevaluated modulo operation with the `Mod` class in
`sympy/core/mod.py`. Its classmethod `Mod.eval(p, q)` is responsible for
simplifying `Mod(p, q)` (equivalently `p % q`) at construction time.

When the dividend `p` is a product (a `Mul`) and the divisor `q` is a concrete
integer, integer coefficient factors of the product can be reduced modulo the
divisor without changing the value of the modulo. Historically `Mod.eval` did
not perform this reduction unless the product also contained a nested `Mod`
factor sharing the same divisor, so an expression such as `Mod(3*i, 2)` (with
`i` a symbol) was returned unsimplified as `Mod(3*i, 2)` instead of the
equivalent, smaller `Mod(i, 2)`.

The goal is to make `Mod.eval` reduce integer factors of a product modulo an
integer divisor so that these expressions collapse to their simplest equivalent
form, while leaving every other established `Mod` simplification unchanged.

## Requirement 1: Reduce integer factors of a product modulo an integer divisor

**User story:** As a user simplifying arithmetic expressions, I want
`Mod(3*i, 2)` to reduce to `Mod(i, 2)`, so that modular expressions of products
are returned in their simplest equivalent form.

**Acceptance criteria**

1. WHEN `Mod(p, q)` is evaluated with `p` a product of factors and `q` a
   concrete integer other than 1, THEN `Mod.eval` SHALL replace each integer
   factor of the product by that factor reduced modulo `q` before forming the
   result, so that the returned expression is equivalent to the original
   modulo `q`.
2. WHEN the product's integer coefficient is congruent to a smaller nonzero
   residue modulo `q`, THEN the evaluation SHALL use that residue in place of
   the original coefficient (for example, evaluating `Mod(3*i, 2)` with `i` an
   integer symbol SHALL produce a result equal to `Mod(i, 2)`).
3. The system SHALL return a result that is mathematically equal to the
   original `Mod(p, q)` for all integer values of the symbolic factors.

## Requirement 2: Do not prematurely zero out factors divisible by the divisor

**User story:** As a user, I want the coefficient reduction to keep other
established simplifications intact, so that products whose integer coefficient
is a multiple of the divisor still simplify correctly rather than collapsing to
a wrong value.

**Acceptance criteria**

1. IF an integer factor of the product is divisible by the divisor `q` (its
   remainder modulo `q` is zero), THEN that factor SHALL NOT be reduced to zero
   in place, but SHALL be left for the subsequent common-factor (gcd)
   extraction step to handle.
2. WHEN the product's integer coefficient is a multiple of the divisor and the
   product as a whole is divisible by the divisor, THEN the result SHALL be
   `0`, produced by the common-factor extraction step rather than by zeroing the
   coefficient in place (for example, `Mod(4*i, 4)` with `i` an integer symbol
   equals `0`).
3. WHEN the product's integer coefficient is a multiple of the divisor but the
   product as a whole is not divisible by the divisor (for instance because the
   product also contains a division by a symbolic factor), THEN the result
   SHALL NOT collapse to `0`; the coefficient reduction SHALL leave such a
   factor untouched so that the returned expression remains mathematically
   equal to the original `Mod(p, q)` for all integer values of the symbolic
   factors.

## Requirement 3: Preserve all existing Mod simplification behavior

**User story:** As a maintainer, I want the new reduction to be additive, so
that no previously supported `Mod` simplification regresses.

**Acceptance criteria**

1. The system SHALL keep numeric evaluation of modulo unchanged, including the
   Python sign convention where the remainder has the same sign as the divisor
   (for example, `Mod(-5, 3)` equals `1` and `Mod(5, -3)` equals `-1`).
2. The system SHALL keep returning `nan` when either operand is `nan`, and SHALL
   raise `ZeroDivisionError` when the divisor is zero.
3. The system SHALL keep the parity-based results `Mod(n, 2) == 0` for an even
   symbol `n` and `Mod(n, 2) == 1` for an odd symbol `n`.
4. The system SHALL keep denesting nested modulo expressions (for example,
   `Mod(Mod(x, t), t)` equals `Mod(x, t)` and `Mod(Mod(x, 2*t), t)` equals
   `Mod(x, t)`).
5. The system SHALL keep distributing modulo over sums when the divisor allows
   it (for example, `(x + y + 2) % x` equals `(y + 2) % x`).
6. The system SHALL keep extracting common factors between dividend and divisor
   (for example, `(12*x) % (2*y)` equals `2*Mod(6*x, y)`, `(3*i*x) % (2*i*y)`
   equals `i*Mod(3*x, 2*y)`, and `Mod(4*i, 4)` equals `0`).
7. The system SHALL keep the established handling of floating-point
   coefficients, of modular exponentiation of powers, and of the
   difference-based reduction for near-in-magnitude operands, unchanged from
   their prior results.
8. WHILE simplifying, the system SHALL keep `Mod` of an integer expression by
   `1` equal to `0`.
