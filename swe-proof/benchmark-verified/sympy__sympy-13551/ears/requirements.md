# Requirements: Correct symbolic products of additive terms with a numeric denominator

## Introduction

`Product` (in `sympy.concrete.products`) represents a symbolic product of a
general term over an integer index range, and `Product.doit()` evaluates that
product to a closed form. Evaluation is performed by the internal helper
`Product._eval_product(term, (k, a, n))`, which dispatches on the structure of
the term (constant in the index, polynomial, additive, multiplicative, etc.).

When the general term is an **additive** expression (a sum of parts) whose
denominator, taken as a product over the range, collapses to a plain number,
the evaluator previously replaced the product of that additive numerator with a
**sum of the products of its summands**. That is algebraically invalid: the
product of a sum is not the sum of the products of the summands. As a result,
`doit()` returned incorrect closed forms for such products.

A concrete demonstration from the issue: the product of `n + 1/2**k` for the
position variable running from `0` through `n - 1`. Evaluating and substituting
`n = 2` must reproduce the hand-computed value `(2 + 2**0) * (2 + 2**(-1)) = 15/2`, but
the buggy evaluator produced `9/2`. Another demonstration from the issue: the
product of `k**(2/3) + 1` over `0 … n - 1` was collapsed to the meaningless
value `1`.

The goal is to make `Product.doit()` return the genuine product for additive
terms of this shape, while preserving every other product evaluation that
already worked (constant, polynomial, rational, factorial, delta, and
multiplicative terms, and rewriting to a sum of logarithms).

The affected module/function: `sympy/concrete/products.py`, the additive-term
branch of `Product._eval_product`.

## Requirement 1: Genuine product for additive terms with a numeric denominator

**User story:** As a user computing a symbolic product whose general term is a
sum with a denominator that reduces to a number over the range, I want
`Product.doit()` to compute the true product, so that the closed form is
mathematically correct rather than a summand-wise approximation.

**Acceptance criteria**

1. WHEN `Product(term, (k, a, n)).doit()` is evaluated for a general `term`
   that is an additive expression whose per-position denominator forms a
   numeric product over the range, THEN `Product.doit()` SHALL return a closed
   form equal to the genuine product of the term evaluated at every index
   position from `a` through `n` (each factor multiplied together), and SHALL
   NOT return the sum of the per-summand products.
2. WHEN the product of `n + 1/2**k` over the index from `0` through `n - 1` is
   evaluated with `doit()`, THEN the result, after substituting `n = 2` and
   re-evaluating, SHALL equal `15/2`.
3. IF a specific integer is substituted for the free upper-bound parameter of
   such a product's evaluated closed form and the result is re-evaluated, THEN
   the value SHALL equal the direct product of the individual factors for that
   integer (e.g. `(2 + 2**0) * (2 + 2**(-1))` for the `n = 2` case).
4. The evaluated closed form SHALL be fully determined by the term and the
   index range, leaving no factor of the true product silently dropped or
   collapsed.

## Requirement 2: Preserve existing product evaluations (regression protection)

**User story:** As a user relying on `Product.doit()` for the product forms
that already evaluate correctly, I want those results to remain unchanged, so
that fixing the additive case does not regress other cases.

**Acceptance criteria**

1. WHEN the general term does not contain the index variable, THEN
   `Product.doit()` SHALL keep returning the term raised to the number of
   positions in the range (and `1` when that term is identically `1`).
2. WHEN the index range consists of a definite (integer) number of positions,
   THEN `Product.doit()` SHALL keep returning the explicit product of the term
   evaluated at each position.
3. WHEN the general term is a polynomial in the index, THEN `Product.doit()`
   SHALL keep returning the closed form built from the polynomial's leading
   coefficient, rising factorials of its roots, and the remaining quotient
   factor.
4. WHEN the general term is a rational function of the index, THEN
   `Product.doit()` SHALL keep returning the correct rational closed form.
5. WHEN the general term is a product of factors, THEN `Product.doit()` SHALL
   keep evaluating the product factor-wise, returning the product of the
   individually evaluated factors.
6. WHEN the range has a single position (lower and upper bounds coincide),
   THEN `Product.doit()` SHALL keep returning the term evaluated at that single
   position.
7. The system SHALL keep returning the previously correct closed forms for the
   known special and rational product cases, including finite and convergent
   infinite products, so that behavior other than the additive-with-numeric-
   denominator case is unchanged.

## Requirement 3: Preserve rewriting a product as an exponential of a summation

**User story:** As a user who rewrites a `Product` into a `Sum`, I want the
existing rewrite behavior to be preserved, so that expressing a product as the
exponential of a sum of logarithms continues to work.

**Acceptance criteria**

1. WHEN a `Product` is rewritten to a `Sum`, THEN the result SHALL keep being
   the exponential of the summation of the logarithm of the general term over
   the same index range.
2. The system SHALL keep producing evaluations that are consistent with this
   product-as-exponential-of-logarithmic-sum relationship for the additive
   case handled in Requirement 1.
