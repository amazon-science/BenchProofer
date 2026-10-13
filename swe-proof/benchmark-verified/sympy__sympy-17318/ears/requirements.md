# Requirements: robust surd matching for non-real additive expressions

## Introduction

The square-root denesting machinery in `sympy.simplify.sqrtdenest` attempts to
rewrite nested radicals into simpler ("denested") forms. Its core matcher,
`_sqrt_match(p)`, decomposes an additive expression `p` into a triple
`[a, b, r]` describing `a + b*sqrt(r)`, selecting the addend of maximal square
root depth. As an optimization, when every addend of the sum is a plain surd
(a term whose square is a rational number), `_sqrt_match` delegates to the fast
helper `split_surds` in `sympy.simplify.radsimp`, which in turn calls the
private helper `_split_gcd`.

`split_surds`/`_split_gcd` are designed only for sums of real surds — terms
whose squares are *positive* rationals. When an addend is complex (for example
the imaginary unit, whose square is a negative rational) or otherwise has a
non-positive rational square, the fast path is entered with no valid surds to
process, producing an empty internal list and raising `IndexError: tuple index
out of range` inside `_split_gcd`.

The goal is to make `_sqrt_match` (and therefore the public `sqrtdenest`) route
such expressions to the general depth-based matching logic instead of the fast
surd path, so that expressions that cannot be denested are returned unchanged
rather than raising an exception. The affected functions are `_sqrt_match` in
`sympy/simplify/sqrtdenest.py` and, transitively, `sqrtdenest` itself; the
docstrings of `split_surds` and `rad_rationalize` in `sympy/simplify/radsimp.py`
describe the same "positive rationals" precondition.

## Requirement 1: Guard the fast surd path with a positive-rational square test

**User story:** As a user calling denesting utilities on additive expressions
that may contain complex or otherwise non-real terms, I want the fast surd
decomposition to be attempted only when it is actually applicable, so that the
routine never dispatches an unsupported expression into helper code that fails.

**Acceptance criteria**

1. WHEN `_sqrt_match` is given an additive expression, THEN `_sqrt_match` SHALL
   compute, for each addend, the square of that addend and delegate to the fast
   surd-splitting helper only IF every addend's square is both a rational
   number AND strictly positive.
2. IF at least one addend's square is not a rational number, THEN `_sqrt_match`
   SHALL NOT delegate to the fast surd-splitting helper and SHALL instead use
   the general depth-based matching logic.
3. IF at least one addend's square is a rational number that is not strictly
   positive (for example zero or negative), THEN `_sqrt_match` SHALL NOT
   delegate to the fast surd-splitting helper and SHALL instead use the general
   depth-based matching logic.
4. WHEN every addend's square is a strictly positive rational number, THEN
   `_sqrt_match` SHALL delegate to the fast surd-splitting helper exactly as
   before and return the decomposition it produces, preserving prior behavior
   for real surd sums.

## Requirement 2: Trivial non-surd additive expressions match to the empty result

**User story:** As a caller of `_sqrt_match`, I want a well-defined,
non-crashing answer for additive expressions that do not fit the
`a + b*sqrt(r)` surd pattern, so that callers can treat "no match" as a normal
outcome.

**Acceptance criteria**

1. WHEN `_sqrt_match` is given an additive expression that contains a complex
   addend such that not all addend squares are positive rationals, and the
   expression has no nested-square-root structure to match, THEN `_sqrt_match`
   SHALL return an empty list.
2. WHEN `_sqrt_match` is given the sum of a rational number and the imaginary
   unit, THEN `_sqrt_match` SHALL return an empty list rather than raising an
   exception.
3. The system SHALL, for additive expressions handled by the general
   depth-based path, return an empty list when the maximum square-root nesting
   depth among the addends is zero.

## Requirement 3: sqrtdenest returns non-denestable expressions unchanged

**User story:** As a user of `sqrtdenest`, I want expressions that cannot be
denested to be returned unchanged instead of raising an error, so that
`sqrtdenest` is safe to call on arbitrary expressions.

**Acceptance criteria**

1. WHEN `sqrtdenest` is applied to an expression containing a square root of a
   complex quantity that cannot be denested, THEN `sqrtdenest` SHALL return that
   expression unchanged.
2. WHEN `sqrtdenest` is applied to any expression whose evaluation triggers
   surd matching on a sum containing a term whose square is a non-positive
   rational, THEN `sqrtdenest` SHALL complete without raising `IndexError` or
   any other exception.
3. WHEN an input expression auto-simplifies (before or during denesting) to a
   simpler value, THEN `sqrtdenest` SHALL return that simplified value.

## Requirement 4: Preserve existing denesting behavior (regression protection)

**User story:** As a maintainer, I want all previously correct denesting
results to remain unchanged, so that the fix narrows only the fast-path
precondition without altering established outcomes.

**Acceptance criteria**

1. The system SHALL continue to denest real nested radicals to their
   established simplified forms, including sums and differences of square roots
   that were previously denestable.
2. The system SHALL continue to correctly denest expressions requiring the
   recursive multi-surd denesting logic (sums of three or more surds).
3. The system SHALL continue to perform symbolic denesting for expressions
   involving symbols exactly as before.
4. WHEN a real surd sum is passed to `_sqrt_match`, THEN `_sqrt_match` SHALL
   produce the same decomposition triple it produced prior to this change.
5. The system SHALL keep the behavior of returning an already-simplified or
   non-denestable expression unchanged for cases that previously succeeded
   without error.
