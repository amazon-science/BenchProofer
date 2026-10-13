# Requirements: correct two-argument Rational construction from non-integer inputs

## Introduction

SymPy represents exact rational numbers with the `Rational` class in
`sympy/core/numbers.py`. Its constructor `Rational.__new__(cls, p, q=None, gcd=None)`
accepts a numerator `p` and an optional denominator `q`, each of which may be an
ordinary Python integer, a Python `float`, a numeric string (for example
`'0.5'` or `'1.5'`), or an existing `Rational`. When both `p` and `q` are
supplied, the intended value is the exact quotient `p / q`.

Reported defect: `Rational('0.5', '100')` returned `1/100100` instead of the
correct value `1/200`, while `Rational(0.5, 100)` (with numeric, non-string
arguments) returned the correct `1/200`. The construction path that normalizes a
non-integer numerator or denominator into integer numerator/denominator parts
reused the denominator argument as its own running accumulator. When the
denominator was still a non-integer at that point (such as the string `'100'`),
the accumulation combined values of incompatible kinds (e.g. repeating the
string `'100'` into `'100100'`) instead of multiplying integer factors, so the
resulting denominator was wrong. Earlier SymPy releases computed this correctly.

For the purpose of these requirements, the *exact rational value* of an argument
is: for a Python integer, the integer itself; for an existing `Rational`, its own
value; for a numeric string, the exact rational denoted by the decimal (or
single-`'/'` fraction) it spells (so `'0.5'` denotes one half and `'100'` denotes
one hundred); and for a Python `float`, the exact value the float actually holds
in binary floating point (which for a value such as one tenth is not the tidy
decimal it prints, but the nearby binary fraction).

The goal is to make the two-argument `Rational(p, q)` constructor always produce
the exact quotient of the exact rational values of `p` and `q` — in fully reduced
(lowest-terms) form — for every mixture of integer, float, string, and `Rational`
arguments, while leaving all other `Rational` and `Integer` construction behavior
unchanged.

## Requirement 1: Two-argument Rational equals the exact quotient of the arguments' exact values

**User story:** As a user constructing exact rationals, I want `Rational(p, q)`
to equal the exact rational value of `p` divided by the exact rational value of
`q`, regardless of whether the arguments are integers, floats, strings, or
rationals, so that I get the true mathematical value.

**Acceptance criteria**

1. WHEN `Rational` is called with two arguments `p` and `q`, THEN the result
   SHALL equal the exact quotient of the exact rational value of `p` divided by
   the exact rational value of `q`, reduced to lowest terms with a positive
   denominator, for every combination in which each argument is a Python integer,
   a Python `float`, a numeric string, or an existing `Rational`.
2. WHEN a supplied argument is a non-integer (a numeric string, a `float`, or a
   `Rational`) whose own denominator differs from 1, THEN that argument's
   denominator SHALL contribute to the final result exactly as it would in exact
   arithmetic — a non-integer numerator multiplies the final denominator, and a
   non-integer denominator multiplies the final numerator — so that no
   denominator or numerator factor is dropped, duplicated, or combined with a
   value of a different kind.
3. WHEN `Rational('0.5', '100')` is constructed, THEN the result SHALL equal
   `Rational(1, 200)` (that is, one two-hundredth).

## Requirement 2: Consistency with the single-string quotient form

**User story:** As a user, I want `Rational(p, q)` and the single-string
`Rational("p/q")` form to agree whenever the two arguments denote the same exact
rational in both spellings, so that the two ways of writing the same quotient
give the same number.

**Acceptance criteria**

1. WHEN the numerator and denominator are both supplied as integers or as numeric
   strings, and the identical values are alternatively written as a single string
   consisting of the numerator spelling, one `'/'`, and the denominator spelling,
   THEN the two-argument `Rational` and the single-string `Rational` SHALL be
   equal values.
2. WHEN an argument is a Python `float`, THEN its contribution SHALL be that
   float's exact binary value; consequently the two-argument result equals the
   single-string form only when that float's exact value coincides with the
   rational denoted by the decimal text of the corresponding string, and it is
   NOT required to agree with a string spelling whose decimal denotes a different
   rational — the two-argument result SHALL still equal the exact quotient of the
   arguments' exact rational values in every case.

## Requirement 3: Preserve existing Rational and Integer construction behavior

**User story:** As a user, I want the fix to be localized so that all other ways
of constructing rationals and integers keep working exactly as before.

**Acceptance criteria**

1. WHEN `Rational` is called with two integer arguments, THEN it SHALL keep
   returning the reduced quotient of those integers (for example a numerator of
   -2 and denominator of 4 SHALL reduce to -1/2), unchanged from current
   behavior.
2. WHEN `Rational` is called with a single argument (an integer, a float, a
   numeric string with no `'/'`, a single-`'/'` fraction string, or an existing
   `Rational`), THEN it SHALL keep its current result and SHALL NOT be affected
   by this change.
3. WHEN a constructed rational reduces to an integer (denominator 1 after
   reduction) or to one-half, THEN it SHALL keep returning the corresponding
   `Integer` or the canonical one-half singleton, as before.
4. IF the effective denominator is zero, THEN construction SHALL keep its current
   behavior (raising for the indeterminate `0/0` case when division errors are
   enabled, otherwise returning the NaN or complex-infinity result as it does
   today).
5. WHEN a numeric string containing more than one `'/'` is supplied, THEN
   construction SHALL keep raising the existing invalid-input error.
6. The sign normalization, lowest-terms reduction, and greatest-common-divisor
   handling SHALL be kept unchanged, so that results remain fully reduced with a
   positive denominator.
