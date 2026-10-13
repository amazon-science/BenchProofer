# Requirements: Preserve arbitrary objects with a `values` attribute when wrapping data into a Variable

## Introduction

When an `xarray.Variable` (and therefore any `DataArray`/`Dataset` backed by
one) is constructed or assigned into, the incoming payload is first normalized
by the data-preparation routine `as_compatible_data` in
`xarray/core/variable.py`. As part of avoiding doubly-nested self-describing
arrays, this routine unwraps a payload's underlying array before storing it.

Historically the unwrap step replaced the payload with the contents of its
`values` attribute for *any* object that happened to expose such an attribute.
This over-broadly coerced ordinary Python objects: any user object that merely
defines a `values` attribute (a very common name — e.g. curve-fitting result
objects and many third-party library types) was silently replaced by whatever
that attribute held, instead of being stored as an opaque object inside an
`object`-dtype array. For example, assigning an instance of a class whose
`values` attribute is `5` into an `object`-dtype `DataArray` element stored the
integer `5` rather than the instance itself.

The goal is to restrict this unwrapping to the recognized pandas container
types that genuinely re-expose an underlying numpy array
(`pandas.Series`, `pandas.Index`, `pandas.DataFrame`), and to leave every other
object untouched — so that arbitrary objects, including ones that incidentally
have a `values` attribute, can be stored inside `object`-dtype variables. The
affected code is the "we don't want nested self-described arrays" step of
`as_compatible_data`; all pre-existing conversions (pandas containers,
datetime/timedelta, masked arrays, datetime64/timedelta64/object dtype
normalization, index adapters) must continue to behave exactly as before.

## Requirement 1: Store arbitrary objects that expose a `values` attribute unchanged

**User story:** As a user storing rich Python objects inside an
`object`-dtype xarray container, I want an object that merely defines a `values`
attribute to be stored as-is, so that I can keep instances of third-party
classes (such as fitting-result objects) without them being silently coerced to
the contents of their `values` attribute.

**Acceptance criteria**
1. WHEN `as_compatible_data` receives an object that is not one of the
   recognized pandas container types (`pandas.Series`, `pandas.Index`,
   `pandas.DataFrame`) and is not otherwise specially handled, THEN
   `as_compatible_data` SHALL treat that object as an opaque element and SHALL
   NOT replace it with the contents of its `values` attribute, even when such an
   attribute is present.
2. WHEN a scalar (zero-dimensional) assignment or construction stores such an
   object into an `object`-dtype `Variable`, THEN the stored element SHALL be
   the original object itself (identity/instance preserved), not the value of
   its `values` attribute.
3. IF an object defines a `values` attribute whose value differs from the object
   (for example an attribute holding an unrelated scalar or array), THEN the
   resulting stored element SHALL still be the original object and SHALL NOT be
   the attribute's value.
4. WHEN such an object is stored into a `Variable`, THEN retrieving the stored
   scalar element SHALL yield an object that is an instance of the original
   object's type.

## Requirement 2: Continue unwrapping recognized pandas container types

**User story:** As a maintainer, I want pandas containers to keep being reduced
to their underlying numpy array, so that the existing behavior of avoiding
nested self-described arrays is preserved for the types it was designed for.

**Acceptance criteria**
1. WHEN `as_compatible_data` receives a `pandas.Series`, `pandas.Index`, or
   `pandas.DataFrame`, THEN it SHALL replace that object with the numpy array
   exposed by its `values` attribute before further processing.
2. The system SHALL preserve, for these recognized pandas container inputs, the
   same resulting data (dtype and values) as before the change, including the
   subsequent conversions applied to object/datetime/timedelta dtypes.
3. WHEN a `pandas.Index` is supplied as data, THEN `as_compatible_data` SHALL
   continue to wrap it using the existing index adapter rather than storing the
   raw object.

## Requirement 3: Preserve all other data-preparation behavior

**User story:** As a user of xarray's existing data types, I want every other
conversion performed when building a Variable to remain unchanged, so that the
narrowed unwrap does not regress any supported input.

**Acceptance criteria**
1. The system SHALL keep converting supported inputs exactly as before,
   including: leaving already-supported array types unchanged, converting plain
   Python sequences and scalars to numpy arrays, and applying the existing
   datetime64/timedelta64 and object-array normalizations.
2. WHEN the input is a `numpy.ma.MaskedArray`, THEN `as_compatible_data` SHALL
   continue to apply the existing mask-handling (promoting dtype and filling
   masked entries, or converting to a plain array when no entries are masked).
3. WHEN the input is a `pandas.Timestamp` or a `datetime.timedelta`, THEN
   `as_compatible_data` SHALL continue to convert it to the corresponding
   nanosecond-precision `datetime64`/`timedelta64` value as before.
4. WHEN the input is a tuple, THEN `as_compatible_data` SHALL continue to store
   it as a zero-dimensional object array as before.
5. WHILE processing any input, the system SHALL leave the results of
   construction, indexing, copying, concatenation, reduction, and other Variable
   operations unchanged for all previously-supported data types.
