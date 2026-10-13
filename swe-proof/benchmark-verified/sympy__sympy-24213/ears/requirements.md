# Requirements: Dimension consistency of sums in unit-system factor/dimension collection

## Introduction

`sympy.physics.units.unitsystem.UnitSystem._collect_factor_and_dimension`
walks a symbolic expression built from physical `Quantity` objects and returns
a `(scale_factor, dimension)` pair. When the expression is an addition (an
`Add`), every addend must share the same physical dimension, otherwise the
sum is meaningless and the method raises `ValueError`.

The affected behavior lives in the `Add` branch of
`UnitSystem._collect_factor_and_dimension`. Its notion of "same dimension"
currently compares the two `Dimension` objects by their surface symbolic
identity. That is too strict: two dimensions can be written differently yet
reduce to the same base-dimension powers — for example `velocity` versus
`acceleration * time`, which both reduce to length / time. Because of the
surface comparison, adding an acceleration-times-time quantity to a velocity
quantity wrongly raised `ValueError` even though the terms are dimensionally
equivalent.

The goal is to make the addition branch accept addends whose dimensions are
*physically equivalent* (equal once reduced to canonical base-dimension
powers), while still rejecting additions of genuinely incompatible
dimensions, and while preserving the scale-factor and returned-dimension
behavior for all previously working cases.

The canonical reduction of a `Dimension` to base-dimension powers, and the
equivalence test on those reductions, are provided by the dimension system
returned by `UnitSystem.get_dimension_system()` (an equivalence predicate that
compares two dimensions' base-dimension dependency maps).

## Requirement 1: Accept dimensionally-equivalent addends in a sum

**User story:** As a user computing the factor and dimension of an expression
involving sums of physical quantities, I want terms that reduce to the same
physical dimension to be treated as compatible, so that valid physical
expressions such as `acceleration*time + velocity` are evaluated instead of
raising an error.

**Acceptance criteria**

1. WHEN `_collect_factor_and_dimension` processes an addition whose addends
   have dimensions that are written with different surface symbols but reduce
   to the same base-dimension powers (for example one addend of dimension
   `velocity` and another of dimension `acceleration*time`), THEN the method
   SHALL NOT raise `ValueError` and SHALL return a `(scale_factor, dimension)`
   result.
2. The system SHALL determine whether two addend dimensions match by comparing
   their canonical base-dimension dependency maps (as provided by the
   dimension system obtained from `get_dimension_system()`), rather than by
   comparing the dimensions' surface symbolic identities.
3. WHEN every addend of an addition has a dimension equivalent to that of the
   first addend, THEN the returned scale factor SHALL equal the sum of the
   individual addends' scale factors.
4. WHEN an addition is evaluated and all addend dimensions are equivalent,
   THEN the returned dimension SHALL be the dimension of the first addend,
   carried through unchanged.

## Requirement 2: Continue rejecting genuinely incompatible sums

**User story:** As a user relying on dimensional-consistency checking, I want
additions of physically incompatible quantities to keep failing, so that real
modeling errors are still caught.

**Acceptance criteria**

1. IF an addition contains an addend whose dimension does not reduce to the
   same base-dimension powers as the first addend's dimension (for example
   adding a length to a time), THEN `_collect_factor_and_dimension` SHALL raise
   `ValueError`.
2. WHEN such an incompatible addition is rejected, THEN the raised error
   message SHALL identify the offending addend together with its dimension and
   the expected dimension.

## Requirement 3: Preserve existing factor-and-dimension behavior

**User story:** As a maintainer, I want all previously supported factor and
dimension computations to keep producing the same results, so that this change
fixes the equivalence handling without regressing other behavior.

**Acceptance criteria**

1. WHEN `_collect_factor_and_dimension` receives a bare `Quantity`, THEN it
   SHALL return that quantity's scale factor paired with its dimension.
2. WHEN the expression is a product (`Mul`), THEN the method SHALL return the
   product of the addends' scale factors paired with the product of their
   dimensions.
3. WHEN the expression is a power (`Pow`), THEN the method SHALL raise the
   base's scale factor and dimension to the exponent, treating a dimensionless
   exponent as an ordinary numeric exponent.
4. WHEN the expression is a derivative or an applied function, THEN the method
   SHALL compute its scale factor and dimension using the existing rules for
   those forms (dividing out the dimensions of the differentiation variables
   for derivatives; treating fully dimensionless function arguments as
   dimensionless).
5. WHEN two addends in a sum already have identical surface dimensions, THEN
   the method SHALL continue to accept the sum and add their scale factors, as
   before.
6. The system SHALL keep the public behavior of related unit operations
   (quantity definition, equality, string/representation, unit conversion,
   consistency checking, addition and subtraction of compatible quantities,
   multiplication and division, absolute value, and prefixed-quantity
   detection) unchanged by this modification.
