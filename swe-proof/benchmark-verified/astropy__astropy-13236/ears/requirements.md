# Requirements: Structured ndarray columns become ordinary Columns

## Introduction

When a value is added to an `astropy.table.Table` (during construction, via
`t['name'] = data`, or by adding a column), the table wraps that value in a
column object and chooses the *class* of that column from observable properties
of the value. Historically, a plain (non-masked) NumPy `ndarray` that carried a
**structured dtype** (a dtype with more than one field) was automatically
re-viewed as an `NdarrayMixin` column. That auto-conversion was a workaround from
a time when structured-dtype `Column` objects were not fully supported (notably
for serialization). Structured-dtype columns are now fully supported, so the
auto-conversion is unnecessary and undesirable: it produces a mixin column with
reduced capability (I/O, table repr) where an ordinary `Column` would serve.

This change concerns the column-class decision performed in
`astropy.table.table.Table._convert_data_to_col` (in `astropy/table/table.py`).
The goal is to stop special-casing structured plain arrays: a structured
`ndarray` must be treated like any other plain array when choosing the column
class, while all pre-existing routes for choosing `Column`, `MaskedColumn`,
`NdarrayMixin`, and other mixin classes remain unchanged.

## Requirement 1: Structured plain arrays yield an ordinary Column

**User story:** As a user adding a structured (multi-field) NumPy array to a
table, I want it stored as an ordinary `Column`, so that it has the full
capabilities of a standard column rather than the reduced capabilities of a
mixin.

**Acceptance criteria**
1. WHEN a plain (non-masked) `numpy.ndarray` whose dtype has more than one field
   is added to a `Table` — whether at table construction, as a new column via
   item assignment, or via a column-add operation — THEN the resulting column
   SHALL be an instance of the table's ordinary column class (`Column`), and
   SHALL NOT be converted to `NdarrayMixin`.
2. WHEN such a structured plain array is stored as a `Column`, THEN the stored
   column SHALL preserve the input's structured dtype, including every field
   name and each field's dtype and order.
3. WHEN elements of the resulting column are accessed by row index, by field
   name, or by a combination of the two, THEN the returned values SHALL equal
   the corresponding values of the original input array.
4. WHEN a structured array is added both as part of the initial table data and
   as a subsequently assigned column, THEN both SHALL be stored as ordinary
   `Column` objects with identical class and value behavior.

## Requirement 2: Masked structured arrays yield a MaskedColumn with per-field masks

**User story:** As a user adding a masked structured array to a table, I want it
stored as a `MaskedColumn` that keeps each field's per-element mask, so that
masking information for a multi-field record is not lost.

**Acceptance criteria**
1. WHEN a `numpy.ma` masked array with a structured (multi-field) dtype is added
   to a `Table`, THEN the resulting column SHALL be an instance of `MaskedColumn`.
2. The system SHALL preserve, for each field of the structured masked array, the
   per-element mask exactly as supplied in the input, so that accessing a given
   field's mask returns the same boolean mask that was provided for that field.
3. WHEN the field values of the stored masked column are accessed, THEN the
   unmasked values SHALL equal the corresponding values of the original input
   array.

## Requirement 3: Values already presented as a mixin keep the mixin class

**User story:** As a user who explicitly views an array as an `NdarrayMixin`
before adding it, I want it to remain an `NdarrayMixin` column, so that existing
code relying on the mixin route is unaffected.

**Acceptance criteria**
1. WHEN a value that is already an instance of `NdarrayMixin` (for example, a
   structured or multi-dimensional array explicitly viewed as `NdarrayMixin`) is
   added to a `Table`, THEN the resulting column SHALL remain an `NdarrayMixin`
   and SHALL retain its class.
2. WHEN an `NdarrayMixin` value is added, THEN its stored element and field
   values SHALL equal those of the original input.

## Requirement 4: All other column-class decisions are unchanged

**User story:** As a maintainer, I want the removal of the structured-array
special case to leave every other column-class decision exactly as before, so
that no existing behavior regresses.

**Acceptance criteria**
1. WHEN the added value is already a `Column` (or `MaskedColumn`), THEN the
   resulting column class SHALL be determined by the table's existing
   column-class upgrade rule, unchanged by this modification.
2. WHEN the added value is a recognized mixin column (such as `Quantity`,
   `Time`, `TimeDelta`, `SkyCoord`, `EarthLocation`, representation and
   differential objects, or an `NdarrayMixin`), THEN the resulting column SHALL
   preserve that mixin's class.
3. WHEN the added value is a sequence whose first element is a mixin scalar,
   THEN the resulting column SHALL be built from that element's own class, with
   the pre-existing fallback behavior preserved.
4. WHEN the added value is a non-structured masked array, THEN the resulting
   column SHALL be a `MaskedColumn` as before.
5. WHEN the added value is a plain array with a single-field or unstructured
   dtype, THEN the resulting column SHALL be an ordinary `Column` as before.
6. The system SHALL continue to support serialization and I/O, joins, stacks,
   copying, pickling, insertion, renaming, and conversion operations for mixin
   columns exactly as before this change.
7. IF a registered mixin conversion handler applies to the value, THEN the value
   SHALL still be converted through that handler before the column class is
   chosen, unchanged by this modification.
