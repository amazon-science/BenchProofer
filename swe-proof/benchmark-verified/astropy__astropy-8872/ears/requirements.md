# Requirements: Preserve low-precision float dtypes when building a Quantity

## Introduction

`astropy.units.Quantity` is an `numpy.ndarray` subclass that attaches a physical
unit to a numeric array. Its constructor (`Quantity.__new__` in
`astropy/units/quantity.py`) decides which element type (numpy `dtype`) the
stored array should have when the caller does not pass an explicit `dtype`.

Historically the constructor coerced any input whose element type "cannot
represent a single-precision float" to the default floating type
(`float`/float64). That test misclassifies half-precision floats: because a
`numpy.float16` cannot losslessly hold a `numpy.float32`, a `float16` input was
silently upgraded to `float64`, e.g. `(np.float16(1) * u.km).dtype` returned
`float64` while `float32`, `float64`, and `float128` inputs kept their dtype.

The goal is to make the constructor preserve **every** floating-point element
type — including half precision (`float16`) — while still coercing the input
types that genuinely cannot represent fractional values (integers and generic
Python-object arrays) to the default floating type. The same decision is made in
two places inside the constructor: the general construction path (a freshly
materialised array) and the fast path that reuses an input that already carries
a unit; both must be corrected consistently.

## Requirement 1: Preserve all floating-point element types, including half precision

**User story:** As a user creating a `Quantity` from a low-precision floating
array or scalar, I want the resulting quantity to keep the element type I gave
it, so that I retain control over memory footprint and precision instead of
being silently upgraded to double precision.

**Acceptance criteria**

1. WHEN a `Quantity` is constructed from a value whose element type is a
   half-precision float (`numpy.float16`) and no explicit `dtype` is supplied,
   THEN `Quantity.__new__` SHALL store the value with a `float16` element type
   (the resulting quantity's `dtype` SHALL equal the input's `dtype`).
2. WHEN a `Quantity` is constructed from a value whose element type is
   single-precision float (`numpy.float32`) and no explicit `dtype` is supplied,
   THEN the resulting quantity's `dtype` SHALL equal the input's `float32`
   dtype.
3. WHEN a `Quantity` is constructed from a value whose element type is a
   floating type of any other precision (`float64`, and extended precision such
   as `float128` where available) and no explicit `dtype` is supplied, THEN the
   resulting quantity's `dtype` SHALL equal the input's dtype.
4. The system SHALL preserve the input element type unchanged for every
   floating-point and complex element type when no explicit `dtype` is given;
   preservation SHALL NOT depend on whether the element type can hold a
   single-precision float without loss.

## Requirement 2: Coerce integer and object inputs to the default float type

**User story:** As a user creating a `Quantity` from integer data or from
arbitrary numeric Python objects, I want it converted to floating point by
default, so that unit arithmetic behaves numerically rather than truncating.

**Acceptance criteria**

1. WHEN a `Quantity` is constructed from a value whose element type is a signed
   or unsigned integer and no explicit `dtype` is supplied, THEN the resulting
   quantity's `dtype` SHALL be the default floating type (`float`, i.e.
   float64).
2. WHEN a `Quantity` is constructed on the general construction path from a
   value stored by numpy as generic Python objects (object dtype) — for example
   an arbitrary-precision numeric Python object — and no explicit `dtype` is
   supplied, THEN the resulting quantity SHALL be stored with the default
   floating type (`float`).
3. IF the caller supplies an explicit `dtype`, THEN `Quantity.__new__` SHALL
   store the value using that requested `dtype` and SHALL NOT apply any default
   coercion.

## Requirement 3: Apply the same corrected decision on the unit-carrying fast path

**User story:** As a user constructing a `Quantity` from a value that already
carries a unit (e.g. another `Quantity`), I want the dtype-preservation rule to
be identical to the general path, so that low-precision floats survive
re-wrapping.

**Acceptance criteria**

1. WHEN a `Quantity` is constructed from an input that is already a `Quantity`
   (or otherwise reused on the fast path) with no explicit `dtype`, THEN the
   result SHALL keep the input's floating (including `float16`) or complex
   element type unchanged.
2. WHEN such a reused input has an integer (signed or unsigned) element type and
   no explicit `dtype` is supplied, THEN the result SHALL be coerced to the
   default floating type (`float`).
3. The system SHALL make the preservation-vs-coercion decision on this fast path
   depend only on the input element type's category, consistently with the
   general construction path.

## Requirement 4: Preserve existing Quantity construction behavior (regression protection)

**User story:** As an existing user of `astropy.units`, I want all previously
working `Quantity` construction, conversion, arithmetic, comparison, and display
behavior to remain unchanged, so that this dtype fix introduces no regressions.

**Acceptance criteria**

1. The system SHALL continue to construct quantities correctly from Python
   scalars, lists, tuples, numpy arrays, strings with embedded units, and
   sequences of quantities, applying the default float coercion only to integer
   and object inputs as described above.
2. WHEN a `Quantity` is constructed from a value that is neither a valid Python
   nor numpy numeric type (e.g. an unparseable string or a non-numeric object),
   THEN `Quantity.__new__` SHALL raise a `TypeError`.
3. The system SHALL keep unchanged all quantity conversion, decomposition,
   arithmetic (addition, subtraction, multiplication, division, power, matrix
   multiplication), comparison, unit handling, iteration, copy/deepcopy,
   pickling, and string/`repr` display behavior.
4. The system SHALL keep unchanged the constructor's handling of the `copy`,
   `order`, `subok`, `ndmin`, and `unit` arguments.
