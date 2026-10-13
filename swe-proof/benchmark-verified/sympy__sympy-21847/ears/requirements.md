# Requirements: correct total-degree filtering in `itermonomials`

## Introduction

The generator `itermonomials(variables, max_degrees, min_degrees=None)` in
`sympy/polys/monomials.py` yields the monomials in a given set of variables whose
degree falls within a requested range. Its documented contract, when
`max_degrees` and `min_degrees` are supplied as plain integers, is to yield every
monomial `monom` whose **total degree** satisfies
`min_degree <= total_degree(monom) <= max_degree`.

The function instead applies the lower bound to the **largest single-variable
exponent** of each candidate monomial rather than to the sum of its exponents.
As a result, when `min_degrees` is a positive integer it silently drops every
mixed monomial whose total degree meets the bound but whose individual exponents
are each below it. For example, with three variables and `max_degrees =
min_degrees = 3`, only the pure powers (`x1**3`, `x2**3`, `x3**3`) are returned,
while genuinely-degree-3 mixed monomials such as `x1*x2**2` are lost. The same
defect affects both commutative and non-commutative variables.

The goal is to make the integer-degree behavior match the documented total-degree
contract, for both commutative and non-commutative variables, while preserving
every other behavior of the function (the list-of-degrees mode, degenerate
cases, validation, and result deduplication).

## Requirement 1: Integer min_degree selects on total degree (commutative)

**User story:** As a user generating monomials over commutative symbols with an
integer degree window, I want every monomial whose total degree lies between
`min_degrees` and `max_degrees` to be produced, so that the result matches the
documented `min_degree <= total_degree(monom) <= max_degree` contract.

**Acceptance criteria**

1. WHEN `itermonomials` is called with commutative `variables`, an integer
   `max_degrees`, and an integer `min_degrees`, THEN the generator SHALL yield a
   monomial for each distinct product of the variables whose total degree (the
   sum of the exponents of all variables in the monomial) is greater than or
   equal to `min_degrees` and less than or equal to `max_degrees`.
2. WHEN such a monomial has total degree within the window but no single variable
   is raised to a power as large as `min_degrees`, THEN that monomial SHALL still
   be included (e.g. for two commutative variables with `max_degrees = 3` and
   `min_degrees = 3`, the result SHALL contain the mixed monomials of total
   degree 3 in addition to the pure cubes).
3. WHEN `min_degrees` equals `max_degrees` (both positive integers), THEN the
   generator SHALL yield exactly the monomials whose total degree equals that
   common value, and no monomial of any other total degree.
4. IF a candidate product has total degree strictly less than `min_degrees`,
   THEN the generator SHALL NOT yield it.
5. The generator SHALL yield each qualifying monomial expression at most once
   (duplicates arising from enumeration SHALL be collapsed).

## Requirement 2: Integer min_degree selects on total degree (non-commutative)

**User story:** As a user generating monomials over non-commutative symbols with
an integer degree window, I want the same total-degree selection to apply, so
that ordered products of the requested total degree are all produced.

**Acceptance criteria**

1. WHEN `itermonomials` is called with non-commutative `variables`, an integer
   `max_degrees`, and an integer `min_degrees`, THEN the generator SHALL yield a
   monomial for each distinct ordered product of the variables whose total degree
   (the sum of the exponents over all variable positions) is greater than or
   equal to `min_degrees` and less than or equal to `max_degrees`.
2. WHEN two non-commutative variables appear in different orders within products
   of the same total degree, THEN each distinct ordered product that meets the
   total-degree window SHALL be yielded (order-distinct products are treated as
   distinct monomials).
3. WHEN `min_degrees` equals `max_degrees` (both positive integers), THEN the
   generator SHALL yield exactly the ordered products whose total degree equals
   that common value.
4. IF an ordered product has total degree strictly less than `min_degrees`, THEN
   the generator SHALL NOT yield it.
5. The generator SHALL yield each distinct monomial expression at most once.

## Requirement 3: Preserve existing integer-degree and range behavior

**User story:** As an existing caller, I want the previously-correct behaviors of
`itermonomials` to remain unchanged, so that the fix corrects only the faulty
lower-bound test and introduces no regressions.

**Acceptance criteria**

1. WHEN an integer `max_degrees` is given with `min_degrees` left unspecified (or
   `0`), THEN the generator SHALL yield every monomial whose total degree is
   between `0` and `max_degrees` inclusive, including the constant monomial `1`.
2. WHEN an integer `min_degrees` of `1` is used, THEN the generator SHALL yield
   every monomial of total degree between `1` and `max_degrees` inclusive and
   SHALL exclude the constant monomial `1`.
3. IF the integer `min_degrees` is greater than `max_degrees`, THEN the generator
   SHALL yield nothing.
4. WHEN `max_degrees` is the integer `0` (with an empty degree window at zero) or
   `variables` is empty, THEN the generator SHALL yield only the constant
   monomial `1`.
5. WHEN `max_degrees` and `min_degrees` are supplied as lists of per-variable
   bounds, THEN the generator SHALL yield each monomial whose per-variable degree
   `degree_list(monom)[i]` satisfies `min_degrees[i] <= degree_list(monom)[i] <=
   max_degrees[i]` for every variable `i`, unchanged by this fix.

## Requirement 4: Preserve input validation

**User story:** As a caller supplying malformed arguments, I want the existing
validation errors to remain, so that misuse is still reported.

**Acceptance criteria**

1. IF an integer `max_degrees` is negative, THEN the function SHALL raise a
   `ValueError`.
2. IF an integer `min_degrees` is negative, THEN the function SHALL raise a
   `ValueError`.
3. WHEN `max_degrees` is a list, IF its length differs from the number of
   variables, THEN the function SHALL raise a `ValueError`.
4. WHEN `max_degrees` is a list, IF `min_degrees` is provided but is not a list,
   THEN the function SHALL raise a `ValueError`; IF any entry of a list
   `min_degrees` is negative, THEN the function SHALL raise a `ValueError`.
