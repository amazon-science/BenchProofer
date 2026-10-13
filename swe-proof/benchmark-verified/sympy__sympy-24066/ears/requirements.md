# Requirements: dimensionless-argument handling for function applications in unit dimension collection

## Introduction

`UnitSystem._collect_factor_and_dimension` in `sympy/physics/units/unitsystem.py`
walks a symbolic physical expression and returns a pair `(scale_factor,
dimension)`. It recurses over the expression tree, handling quantities,
products (`Mul`), powers (`Pow`), sums (`Add`), derivatives (`Derivative`),
plain `Dimension` objects, and function applications (any SymPy `Function`,
such as `exp`, `sin`, `log`).

For a function application the method reduces every argument to its own
`(scale_factor, dimension)` pair, rebuilds the function over the argument scale
factors, and reports the argument dimension(s) alongside it.

There is a defect in the function-application case. When an argument is
physically dimensionless but its dimension is expressed as a non-trivial but
dimensionless combination of base dimensions (for example the quotient of a
time by the product of an impedance and a capacitance, which reduces to no net
dimension), the method reported that raw compound dimension rather than the
unit dimension `Dimension(1)`. A later consumer — for instance the `Add`
branch, which compares the dimensions of the terms of a sum and raises a
`ValueError` when they differ — then failed to recognize the function
application as dimensionless, because its reported dimension was written in a
form that is not literally equal to `Dimension(1)`.

The goal is to make the function-application case canonicalize each
dimensionless argument dimension to `Dimension(1)`, so that a function whose
argument is dimensionless is itself treated as dimensionless and can be added
to other dimensionless quantities without error, while leaving every other
behavior of the method unchanged.

## Requirement 1: canonicalize dimensionless argument dimensions of a function application

**User story:** As a user computing the scale factor and dimension of a
physical expression, I want a function applied to a dimensionless argument to be
reported as dimensionless, so that expressions such as an exponential of a
dimensionless ratio can be combined with other dimensionless quantities.

**Acceptance criteria**

1. WHEN `_collect_factor_and_dimension` is given an expression that is a
   function application (an instance of SymPy's `Function`), THEN the method
   SHALL reduce each argument to its own scale factor and dimension by
   recursively applying `_collect_factor_and_dimension` to that argument.
2. WHEN a function application is processed, THEN, for each argument whose
   collected dimension is regarded as dimensionless by the active dimension
   system (as decided by `get_dimension_system().is_dimensionless`), the method
   SHALL report that argument's dimension as the unit dimension `Dimension(1)`.
3. WHEN a function application is processed, THEN, for each argument whose
   collected dimension is NOT dimensionless, the method SHALL report that
   argument's dimension unchanged.
4. IF a function application has a single dimensionless argument, THEN the
   dimension component returned by the method SHALL be equal to `Dimension(1)`
   (that is, `get_dimension_system().is_dimensionless` SHALL hold for it and it
   SHALL compare equal to `Dimension(1)`).
5. The method SHALL return the scale-factor component of a function application
   as the function reapplied to the collected scale factors of its arguments,
   preserving the pre-existing behavior for that component.

## Requirement 2: dimensionless function applications combine additively without error

**User story:** As a user building expressions that add a constant to a
function of a dimensionless quantity, I want the sum to evaluate to a
dimensionless result, so that valid physical formulas do not raise spurious
dimension-mismatch errors.

**Acceptance criteria**

1. WHEN `_collect_factor_and_dimension` is given a sum in which one term is a
   pure number and another term is a function applied to a dimensionless
   argument, THEN the method SHALL treat both terms as dimensionless and SHALL
   NOT raise a `ValueError` reporting a dimension mismatch.
2. WHEN such a sum is processed, THEN the dimension component returned SHALL be
   dimensionless (equal to `Dimension(1)`), and the scale-factor component
   SHALL equal the numeric term added to the function reapplied to the
   argument's scale factor.
3. WHEN the argument of the function is a dimensionless combination of
   quantities whose dimensions are written as a non-trivial symbolic expression
   (for example a time divided by the product of an impedance and a
   capacitance), THEN the method SHALL still recognize it as dimensionless and
   report `Dimension(1)` for it.

## Requirement 3: preserve existing collection behavior for other expression kinds

**User story:** As a maintainer, I want the change confined to the
function-application handling, so that all previously supported expression
kinds keep their established scale-factor and dimension semantics.

**Acceptance criteria**

1. The system SHALL keep returning a quantity's stored scale factor and
   dimension unchanged when the expression is a `Quantity`.
2. The system SHALL keep computing the product of the argument scale factors and
   the product of the argument dimensions when the expression is a `Mul`.
3. The system SHALL keep computing, for a `Pow`, the base scale factor raised to
   the argument's scale factor, and the base dimension raised to the product of
   the exponent's scale factor and its dimension, treating a dimensionless
   exponent as unit-valued in that product.
4. WHEN the expression is an `Add`, THEN the method SHALL sum the term scale
   factors and SHALL raise a `ValueError` describing the offending term, its
   dimension, and the expected dimension whenever a term's dimension differs
   from the first term's dimension.
5. The system SHALL keep computing, for a `Derivative`, the scale factor and
   dimension of the differentiated expression divided by the scale factors and
   dimensions of the differentiation variables raised to their respective
   counts.
6. The system SHALL keep returning `(S.One, expr)` when the expression is a
   `Dimension`, and `(expr, Dimension(1))` for any other expression.
7. The system SHALL keep reporting an already-dimensionless function application
   (one whose argument's dimension is literally `Dimension(1)`) as dimensionless,
   so that the fix introduces no regression for that case.
