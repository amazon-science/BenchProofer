# Requirements — Intersecting an image set with the reals

## Introduction

When a symbolic image set `S = imageset(Lambda(n, f(n)), D)` (the family of
values `f(n)` as the parameter `n` ranges over a base domain `D` such as
`S.Integers` or `S.Naturals0`) is intersected with `S.Reals`, the result must be
exactly the subset of images whose value is real.

The behavior is produced by the `ImageSet` / real-set branch of
`intersection_sets` in `sympy/sets/handlers/intersection.py` — specifically the
`if other == S.Reals:` branch of the handler dispatched on an `ImageSet`. That
branch splits `f(n)` into its real part `re` and imaginary part `im`, and must
return the image of `Lambda(n, re)` restricted to the parameters `n` for which
`f(n)` is a well-defined real number.

A defect in that branch caused it to *remove* (set-difference) the parameters
whose imaginary part vanishes instead of *keeping* (intersecting) them, and to
mishandle imaginary parts and denominators that are products of several factors.
As a result `imageset(Lambda(n, n + (n - 1)*(n + 1)*I), S.Integers).intersect(S.Reals)`
wrongly retained non-real members (for example the value `2`) and dropped the
genuinely real members `{-1, 1}`. The goal is to make this branch compute the
surviving parameter set correctly for single- and multi-factor imaginary parts,
for rational images with parameter-dependent denominators, and for both linear
and non-linear vanishing conditions, while leaving every other intersection
branch and the outer image re-wrapping unchanged.

Throughout, "the imaginary part vanishes" means the imaginary component of
`f(n)` equals zero, and "the value is defined" means no denominator of `f(n)`
evaluates to zero.

## Requirement 1: Keep exactly the parameters whose value is real

**User story:** As a user computing `image_set.intersect(S.Reals)`, I want the
result to contain precisely the images that are real numbers, so that set
membership over the intersection agrees with membership over the reals.

**Acceptance criteria**

1. WHEN a univariate image set `imageset(Lambda(n, f(n)), D)` is intersected
   with `S.Reals` and the imaginary part of `f(n)` is not identically zero and
   is not provably nonzero, THEN the handler SHALL return the image under
   `Lambda(n, re)` of the parameters in `D` at which the imaginary part of
   `f(n)` is zero and every denominator of `f(n)` is nonzero.
2. WHEN determining the parameters that make the value real, THEN the handler
   SHALL restrict (intersect) the base parameter domain to the zero set of the
   imaginary part, rather than removing that zero set from the domain.
3. WHEN the parameters that make the imaginary part vanish are computed, THEN
   the handler SHALL exclude (set-difference) from that set the parameters at
   which any denominator of `f(n)` is zero.
4. WHEN `imageset(Lambda(n, n + (n - 1)*(n + 1)*I), S.Integers)` is intersected
   with `S.Reals`, THEN the result SHALL equal the finite set `{-1, 1}`.
5. IF a candidate value such as `2` is not among the real images of the family,
   THEN membership of that value in `image_set.intersect(S.Reals)` SHALL be
   reported as false.
6. The system SHALL make membership over `image_set.intersect(S.Reals)`
   consistent with membership over the original image set: a value SHALL be a
   member of the intersection only if it is both a member of the image set and
   real.

## Requirement 2: Respect the base parameter domain

**User story:** As a user whose image set ranges over a specific domain
(integers, naturals, etc.), I want only parameters within that domain to
contribute, so that domain-limited families are handled correctly.

**Acceptance criteria**

1. WHEN the vanishing condition of the imaginary part has a root that lies
   outside the base parameter domain `D`, THEN the handler SHALL NOT include the
   image of that root in the result.
2. WHEN a family whose imaginary part vanishes only at a non-integer parameter
   value is intersected with `S.Reals` over `S.Integers`, THEN only the
   integer-valued roots SHALL contribute to the result.
3. WHEN the base parameter domain is `S.Naturals0`, THEN the handler SHALL
   restrict the surviving parameters to that domain, so roots outside the
   naturals are excluded.

## Requirement 3: Handle multi-factor and non-linear vanishing conditions

**User story:** As a user with an imaginary part that is a product of several
factors or is non-linear in the parameter, I want every factor's zero set
accounted for, so that no real member is missed or spuriously included.

**Acceptance criteria**

1. WHEN the imaginary part is a product of several factors in the parameter,
   THEN the handler SHALL treat the imaginary part as vanishing wherever the
   numerator vanishes, i.e. wherever any single factor of the numerator is zero,
   and SHALL form the union of those factors' zero sets.
2. WHEN a factor of the numerator is linear in the parameter, THEN the handler
   SHALL represent that factor's zero set as the finite set of its explicit root.
3. IF a factor of the numerator cannot be solved linearly for the parameter,
   THEN the handler SHALL represent that factor's zero set as a condition set
   constraining the parameter to satisfy the factor-equals-zero equation over
   the base domain.
4. WHEN a family whose imaginary part is non-linear in the parameter (so no
   explicit linear root exists) is intersected with `S.Reals`, THEN the result
   SHALL be expressed as the image, under the real-part lambda, of a condition
   set that constrains the parameter to make the imaginary part zero over the
   base domain.

## Requirement 4: Exclude parameters that make the value undefined

**User story:** As a user whose image expression is a rational function of the
parameter, I want parameters that make a denominator zero to be excluded, so
that no undefined value is reported as real.

**Acceptance criteria**

1. WHEN the image expression `f(n)` has one or more denominators depending on
   the parameter, THEN the handler SHALL remove from the surviving parameter set
   every parameter at which any denominator is zero.
2. WHEN excluding poles, THEN the handler SHALL derive the excluded parameters
   from the actual denominators of `f(n)`, not from the imaginary part.
3. WHEN a denominator is a product of several factors, THEN the handler SHALL
   exclude the union of those factors' zero sets, using an explicit finite root
   for a linear factor and a condition set for a factor that is not linearly
   solvable.
4. WHEN, after excluding poles, no surviving parameter makes the value both real
   and defined, THEN the result SHALL be the empty set.
5. WHEN a rational family has real images only at parameters that are not poles,
   THEN the result SHALL contain exactly those non-pole real values (for
   example, a single finite real value where the construction admits one).

## Requirement 5: Preserve unrelated intersection behavior

**User story:** As a maintainer, I want the fix confined to the reals branch of
the image-set intersection, so that all previously correct set computations keep
working.

**Acceptance criteria**

1. The system SHALL keep the outer construction of the result as the image of
   `Lambda(n, re)` over the surviving parameter set unchanged; only which
   parameters survive changes.
2. WHEN the imaginary part of `f(n)` is identically zero, THEN the handler SHALL
   preserve its prior behavior of allowing re-evaluation so the result is
   canonical.
3. WHEN the imaginary part of `f(n)` is provably nonzero for all parameters,
   THEN the handler SHALL return the empty set.
4. WHEN the imaginary part depends on symbols other than the single parameter
   `n`, THEN the handler SHALL decline to compute a result (return no
   simplification) as before.
5. The system SHALL keep intersections of image sets with intervals, with the
   integers via the diophantine path, and with other sets behaving exactly as
   before the fix.
6. The system SHALL keep intersecting an image set built from a more complex
   real-valued construction (such as one involving logarithms and trigonometric
   terms over the integers) producing its previously expected result.
