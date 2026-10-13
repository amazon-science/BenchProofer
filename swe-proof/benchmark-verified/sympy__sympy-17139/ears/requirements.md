# Requirements: Guard trigonometric power simplification against non-real exponents

## Introduction

`sympy.simplify.fu` provides the Fu-style trigonometric simplification
transformations. Two of them, `TR5` and `TR6`, share a helper `_TR56` that
rewrites even powers of `sin`/`cos` (for example `sin(x)**2` into `1 -
cos(x)**2`). Inside `_TR56` the local rewrite routine inspects the exponent of a
matching power by comparing it against numeric bounds — it checks whether the
exponent is negative and whether it exceeds a configured maximum.

These order comparisons are only defined for real exponents. When a matching
power carries a non-real (complex) exponent — such as `cos(x)**I` — the
comparison `exponent < 0` raises
`TypeError: Invalid comparison of complex I`. Because `_TR56` is reached through
`TR6` during `trigsimp`/`futrig`, this makes ordinary calls such as
`simplify(cos(x)**I)` crash instead of returning a result.

The goal is to make the `_TR56` rewrite (and therefore `TR5`, `TR6`, and the
`simplify`/`trigsimp` pipeline that invokes them) leave a matching power with a
non-real exponent untouched, while preserving every existing rewrite for
matching powers with real exponents. The affected code is the `_TR56` helper in
`sympy/simplify/fu.py`.

## Requirement 1: Do not attempt order-based rewriting of powers with non-real exponents

**User story:** As a user calling `simplify` (or `trigsimp`) on a trigonometric
power whose exponent is complex, I want the call to succeed and return a
well-formed expression, so that a non-real exponent does not crash
simplification.

**Acceptance criteria**

1. WHEN `_TR56` in `sympy/simplify/fu.py` processes a sub-expression that is a
   power whose base is an application of the targeted trigonometric function
   (the `f` function, e.g. `sin` or `cos`) and whose exponent is not real, THEN
   `_TR56` SHALL return that power unchanged.
2. WHEN `_TR56` encounters such a matching power with a non-real exponent, THEN
   `_TR56` SHALL NOT evaluate any order comparison (less-than / greater-than)
   against that exponent, so that no `TypeError` for comparison of a complex
   quantity is raised.
3. IF the exponent of a matching power is a purely imaginary quantity (for
   example `I`), THEN `_TR56` SHALL return the power unchanged.
4. IF the exponent of a matching power is complex with a non-zero imaginary part
   (whether or not it also has a non-zero real part), THEN `_TR56` SHALL return
   the power unchanged.
5. WHEN `TR5` or `TR6` is applied to an expression containing a matching power
   with a non-real exponent, THEN the transformation SHALL return that power
   unchanged and SHALL NOT raise an error.
6. WHEN `simplify` (or `trigsimp`) is invoked on an expression that is a
   trigonometric power with a non-real exponent, THEN the call SHALL complete
   without raising an error and SHALL return an expression equal to the input
   power (the power is left unchanged by this transformation).

## Requirement 2: Preserve all existing rewriting for real exponents

**User story:** As a maintainer relying on the established behavior of `TR5`,
`TR6`, and `_TR56`, I want the non-real-exponent guard to change nothing for
powers with real exponents, so that existing trigonometric simplifications keep
working exactly as before.

**Acceptance criteria**

1. WHEN `_TR56` processes a matching power whose exponent is real and equal to
   the value that triggers the squared-form rewrite, THEN `_TR56` SHALL produce
   the same rewritten result it produced before this change (the base's argument
   substituted through the replacement mapping, squared).
2. WHEN `_TR56` processes a matching power whose exponent is a real value within
   the allowed range and reducible under the configured power/parity rules, THEN
   `_TR56` SHALL produce the same higher-power rewritten result it produced
   before this change.
3. WHEN `_TR56` processes a matching power whose real exponent is negative,
   exceeds the configured maximum, or fails the perfect-power / parity condition,
   THEN `_TR56` SHALL return that power unchanged, as before.
4. WHEN `_TR56` processes a sub-expression that is not a power of the targeted
   trigonometric function, THEN `_TR56` SHALL return it unchanged.
5. The system SHALL keep the previously supported results of `TR5`, `TR6`, and
   the broader Fu-simplification and `simplify`/`trigsimp` behavior for all
   inputs whose relevant exponents are real, producing outputs identical to
   those produced before this change.
