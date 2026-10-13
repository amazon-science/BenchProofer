# Requirements: symmetric signed/unsigned integer decoding in the `_Unsigned` CF convention

## Introduction

When xarray reads a variable that carries the `_Unsigned` attribute, the
`UnsignedIntegerCoder.decode` method in `xarray/coding/variables.py` may
reinterpret the stored integer array between the signed and unsigned
two's-complement representations of the same byte width. This supports the
netCDF best-practices convention where a signed-typed array is flagged
`_Unsigned="true"` to convey unsigned data.

The mirror-image case is currently unhandled: some servers/backends (e.g. the
OPeNDAP/pydap path) can only carry *unsigned* integer types, so they store
genuinely signed data in an unsigned-typed array and flag it `_Unsigned="false"`.
xarray previously ignored this flag on an unsigned array (emitting a
serialization warning and returning the raw unsigned values), so a value that
should decode to `-1` was returned as `255`.

The goal is to make decoding symmetric: reinterpret an unsigned-kind array
declared `_Unsigned="false"` into the signed integer type of the same width,
while preserving all existing decoding behavior (the signed→unsigned direction,
the encode direction, the fill-value handling, and the warning for non-integer
types).

The affected code is `UnsignedIntegerCoder.decode` (and, for the regression
guarantees, `UnsignedIntegerCoder.encode`) in `xarray/coding/variables.py`.

## Requirement 1: Decode unsigned-typed arrays declared as signed

**User story:** As a user opening a dataset whose backend can only store
unsigned integer types, I want an array flagged `_Unsigned="false"` to be
returned as signed integers, so that values intended to be negative are decoded
correctly rather than as large positive numbers.

**Acceptance criteria**

1. WHEN `UnsignedIntegerCoder.decode` receives a variable whose data array has
   an unsigned integer dtype (dtype kind `"u"`) and whose attributes contain
   `_Unsigned` equal to the string `"false"`, THEN the coder SHALL return a
   variable whose data has the signed integer dtype of the same byte width
   (item size) as the input array.
2. WHEN the condition in criterion 1 holds, THEN each element SHALL be
   reinterpreted using the same-width two's-complement mapping: for a width of
   `bits` bits and `m = 2**bits`, an unsigned value `x` SHALL become `x - m`
   when `x >= m/2` and SHALL remain `x` otherwise (for example, an 8-bit `255`
   SHALL decode to `-1`, `128` SHALL decode to `-128`, and `127` SHALL remain
   `127`).
3. The system SHALL apply this reinterpretation for every supported integer
   byte width (1-, 2-, 4-, and 8-byte unsigned types), producing the signed
   type of the correspondingly matching width in each case.
4. IF a `_FillValue` attribute is present when the condition in criterion 1
   holds, THEN the coder SHALL convert that fill value to the same signed dtype
   using the same width-preserving reinterpretation, so that the returned fill
   value is consistent with the decoded data dtype.
5. WHEN the condition in criterion 1 holds, THEN the coder SHALL NOT emit the
   "has _Unsigned attribute but is not of integer type" serialization warning
   for this variable.

## Requirement 2: Preserve decoding of signed-typed arrays declared as unsigned

**User story:** As an existing user relying on the established `_Unsigned="true"`
convention, I want the current signed→unsigned decoding to keep working, so that
adding the new case does not regress the original behavior.

**Acceptance criteria**

1. WHEN `UnsignedIntegerCoder.decode` receives a variable whose data array has a
   signed integer dtype (dtype kind `"i"`) and whose attributes contain
   `_Unsigned` equal to the string `"true"`, THEN the coder SHALL return a
   variable whose data has the unsigned integer dtype of the same byte width as
   the input array.
2. WHEN the condition in criterion 1 holds, THEN each element SHALL be
   reinterpreted using the inverse same-width two's-complement mapping (`x mod m`
   for `m = 2**bits`); for example, an 8-bit `-1` SHALL decode to `255`.
3. The system SHALL preserve this behavior for every supported integer byte
   width (1-, 2-, 4-, and 8-byte signed types).
4. IF a `_FillValue` attribute is present when the condition in criterion 1
   holds, THEN the coder SHALL convert that fill value to the matching unsigned
   dtype.

## Requirement 3: Leave unaffected inputs unchanged

**User story:** As a maintainer, I want the decoder to change nothing outside the
two reinterpreting cases, so that unrelated variables and metadata are untouched.

**Acceptance criteria**

1. IF the data array has a signed integer dtype but the `_Unsigned` attribute is
   not `"true"`, THEN the coder SHALL return the data with its dtype and values
   unchanged.
2. IF the data array has an unsigned integer dtype but the `_Unsigned` attribute
   is not `"false"`, THEN the coder SHALL return the data with its dtype and
   values unchanged.
3. IF a variable carries an `_Unsigned` attribute but its data array is not of
   integer type, THEN the coder SHALL leave the data unchanged and SHALL emit a
   serialization warning stating that the `_Unsigned` attribute is ignored
   because the variable is not of integer type.
4. IF a variable has no `_Unsigned` attribute, THEN the coder SHALL return the
   variable unchanged.
5. WHEN a variable is decoded, THEN the coder SHALL move the `_Unsigned`
   attribute out of the variable's attributes into its encoding (so the returned
   variable no longer exposes `_Unsigned` as an attribute), and SHALL leave the
   dimensions, encoding, and all other attributes otherwise unchanged.
6. WHEN reinterpreting in either direction, THEN the coder SHALL preserve the
   array's byte width (item size); only the signedness of the integer dtype
   changes.

## Requirement 4: Preserve the encode direction and unrelated coders

**User story:** As a user round-tripping data, I want encoding and the other
CF coders to keep their current behavior, so that this change is confined to the
unsigned/signed decode fix.

**Acceptance criteria**

1. The system SHALL keep `UnsignedIntegerCoder.encode` behavior unchanged: when
   the encoding declares `_Unsigned="true"`, an unsigned-typed array SHALL be
   encoded to the signed integer dtype of the same width (with the matching
   `_FillValue` conversion), and the `_Unsigned` marker SHALL be moved from
   encoding into attributes.
2. The system SHALL keep the behavior of the other coding transforms in
   `xarray/coding/variables.py` (mask/fill-value decoding and encoding, and
   scale/offset conversion to floating point) unchanged.
