# Requirements: sound zero-detection for sums (`Add.is_zero`)

## Introduction

In SymPy, every expression exposes a three-valued `is_zero` assumption query:
it may answer `True` (the expression is definitely zero), `False` (the
expression is definitely nonzero), or `None` (it cannot be decided). The
soundness contract for this query is absolute: it may return `None` whenever it
is unsure, but it must never return a definite `True`/`False` that is wrong.

The zero-test for a sum is implemented by the `_eval_is_zero` method of the
`Add` class in `sympy/core/add.py`. This method is one input the wider
assumption engine consults when it resolves the observable `is_zero` property of
an `Add` expression; the engine may refine the method's return value into a
sound definite verdict using other facts (for example `is_positive` or
`is_imaginary`). It is therefore important to distinguish two boundaries:

- the **observable property** `Add.is_zero`, which is what user code reads; and
- the **return value of the sum's own zero-test method** `_eval_is_zero`, which
  is the local decision the patched code changes and which the wider engine may
  subsequently override with a sound definite answer.

`_eval_is_zero` inspects the summands, sorting them into categories — real terms
known to be zero, real terms known to be nonzero, real terms of undecidable
zero-ness, purely imaginary terms, terms that are either purely imaginary or
zero, and terms that fit none of these — and combines those observations into a
returned verdict (`True`, `False`, or `None`).

A defect existed in that combination logic: for certain sums whose summands are
imaginary (or possibly-imaginary/zero) but which contain **no real summand
known to be nonzero**, the method concluded the sum was definitely nonzero and
its verdict propagated to the observable property as `False`, even though the
sum was in fact zero (for example, a sum of complex terms that cancel to zero
once expanded). This produced a wrong definite observable answer, violating the
soundness contract and, downstream, corrupting results that depend on it (such
as matrix rank computation).

The goal is to make this situation sound: when there is no definitely-nonzero
real term to anchor the real part of the sum, the sum's zero-test method must
leave the verdict undecided (`None`) rather than returning a definite `False`,
so that the observable `is_zero` is `None` for the offending case, while every
already-correct verdict — both the method's own returns and the observable
property — is preserved.

## Requirement 1: The observable zero-query never returns a wrong definite verdict

**User story:** As a user relying on `is_zero` to reason about complex-valued
sums, I want the query to admit uncertainty instead of guessing, so that I
never receive a definite answer that is actually wrong.

**Acceptance criteria**

1. WHEN `is_zero` is evaluated for a sum of a purely-imaginary term and a
   squared complex term whose expansion is the negation of that imaginary term
   (so that the sum in fact cancels to zero yet is not simplified), THEN the
   observable `Add.is_zero` SHALL evaluate to `None` and SHALL NOT evaluate to
   `False`.
2. The observable `is_zero` query on any `Add` expression SHALL NOT return a
   definite `True` or `False` unless that value is a correct statement about
   whether the expression equals zero.

## Requirement 2: Return contract of the sum's zero-test method

**User story:** As a maintainer of the sum zero-test, I want the method that
decides an `Add`'s zero-ness locally to return exactly the sound value for each
category of summands, so that the observable property it feeds is never handed a
wrong definite verdict and every already-correct local verdict is preserved.

The following criteria describe the value returned by the sum's zero-test method
`_eval_is_zero` (which the wider assumption engine may afterwards refine into a
sound definite observable verdict).

**Acceptance criteria**

1. WHILE an `Add` expression is non-commutative, its zero-test method SHALL
   return `None`.
2. IF a commutative sum contains at least one real summand whose zero-ness
   cannot be decided, THEN its zero-test method SHALL return `None`.
3. IF a commutative sum contains at least one summand that is neither real, nor
   purely imaginary, nor a term whose product with the imaginary unit is real,
   THEN its zero-test method SHALL return `None`.
4. WHEN every summand of a commutative sum is a real term already known to be
   zero, THEN its zero-test method SHALL return `True`.
5. WHEN a commutative sum's summands are all classifiable (each is real, purely
   imaginary, or a term whose product with the imaginary unit is real) and the
   number of summands known to be nonzero real numbers is either zero or equal
   to the total number of summands, and the sum is not composed entirely of
   real terms known to be zero, THEN its zero-test method SHALL return `None`.
6. WHEN a commutative sum contains at least one summand known to be a nonzero
   real number but not exclusively such summands, and the sub-sum formed from
   its known-nonzero-real summands is itself zero, THEN its zero-test method
   SHALL return `True` if the sum has no purely-imaginary summand and no
   possibly-imaginary-or-zero summand, and SHALL return `False` if the sum has
   exactly one purely-imaginary summand and no possibly-imaginary-or-zero
   summand.
7. WHEN a commutative sum contains at least one summand known to be a nonzero
   real number but not exclusively such summands, and the sub-sum formed from
   its known-nonzero-real summands is definitely nonzero, THEN its zero-test
   method SHALL return `False`.

## Requirement 3: Zero-test behavior for the broader arithmetic core stays intact

**User story:** As a user of SymPy's core arithmetic, I want the surrounding
assumption queries on `Add`, `Mul`, and `Pow` to keep behaving as before, so
that this correction to sum zero-detection introduces no collateral change.

**Acceptance criteria**

1. The system SHALL keep the existing `is_zero`, `is_positive`, `is_negative`,
   `is_integer`, `is_rational`, `is_even`, `is_odd`, `is_real`, `is_imaginary`,
   and `is_finite` results for `Add`, `Mul`, and `Pow` expressions unchanged
   apart from the correction described in Requirements 1 and 2.
2. WHEN any arithmetic expression is evaluated for `is_zero` whose verdict is
   unaffected by the no-nonzero-real-anchor case, THEN that expression SHALL
   produce the same three-valued result it produced before this change.
