# Requirements: Suppress spurious categorical-unit notifications for empty data

## Introduction

Matplotlib's categorical (string) unit machinery lives in
`lib/matplotlib/category.py`. Two code paths inspect an incoming sequence of
values and, based on a per-element scan, may emit a user-facing notification:

- `StrCategoryConverter.convert(value, unit, axis)` scans the values and, when
  every element is a non-string numeric value, emits a
  `MatplotlibDeprecationWarning` about "passing numbers through unit
  converters" before returning the values as a float array.
- `UnitData.update(data)` scans the values and, when every element is a string
  that is individually parsable as a number or a date, emits an informational
  log message advising that the strings might have been meant as numbers.

Both decisions use an "all elements satisfy property P" test. Over an **empty**
sequence, such a universal test is vacuously true, so both notifications fire
even though there is nothing to convert. In practice this happens when an empty
data structure is plotted on an axis that already uses categorical (string)
units — e.g. after registering string categories, calling a plotting method
with empty x/y data. The vacuous deprecation warning was then re-raised as a
`ConversionError`, breaking a previously harmless operation, and the warning was
non-actionable (its suggested alternative did not avoid it).

Goal: neither notification may fire for an empty sequence, while every existing
behavior for non-empty sequences is preserved exactly.

## Requirement 1: No deprecation warning for empty values in categorical conversion

**User story:** As a user plotting empty data on an axis that already uses
string/categorical units, I want the conversion to complete quietly, so that I
do not get a confusing, non-actionable deprecation warning (and the failure it
caused).

**Acceptance criteria**

1. WHEN `StrCategoryConverter.convert` is invoked with a *value* that is empty
   (contains no elements), THEN the converter SHALL NOT emit the
   "passing numbers through unit converters" `MatplotlibDeprecationWarning`.
2. WHEN `StrCategoryConverter.convert` is invoked with an empty *value* against
   a valid `UnitData` unit, THEN the converter SHALL complete without raising,
   returning an empty float array (rather than propagating a conversion
   failure).
3. IF an empty sequence is plotted on an axis whose units are already set to
   categorical string units, THEN the plotting call SHALL complete without
   emitting any deprecation warning arising from the categorical converter.

## Requirement 2: Preserve the numeric-passthrough deprecation warning for non-empty numeric input

**User story:** As a maintainer, I want the existing deprecation of numeric
pass-through to remain in force for real (non-empty) numeric input, so that the
deprecation cycle proceeds as intended.

**Acceptance criteria**

1. WHEN `StrCategoryConverter.convert` receives a non-empty *value* in which
   every element is a non-string numeric value (e.g. integers or floats, not
   `str`/`bytes`), THEN the converter SHALL emit the
   "passing numbers through unit converters" `MatplotlibDeprecationWarning`.
2. WHEN the numeric-passthrough case above holds, THEN the converter SHALL
   return the values converted to a float array.
3. The system SHALL treat the notification decision as the conjunction of
   "the sequence is non-empty" AND "every element is a non-string numeric
   value"; neither condition alone SHALL trigger the warning.

## Requirement 3: Preserve categorical mapping and validation behavior in conversion

**User story:** As a user plotting string categories, I want conversion of
non-numeric values to keep mapping strings to their integer category ids, so
that categorical plotting is unaffected.

**Acceptance criteria**

1. WHEN `StrCategoryConverter.convert` receives a non-empty *value* that is not
   entirely non-string numeric (i.e. it contains string/categorical values),
   THEN the converter SHALL map each value to its integer category id via the
   unit's mapping and return the result as a float array, without emitting the
   deprecation warning.
2. WHEN converting such values, THEN the converter SHALL first update the unit
   mapping so that previously unseen categories are assigned ids and type
   checking is performed.
3. IF the *unit* argument is `None`, THEN the converter SHALL raise a
   `ValueError` indicating missing category information.
4. WHEN a single (scalar) string or bytes value is passed, THEN the converter
   SHALL convert it as a one-element sequence and return the corresponding
   float value(s).

## Requirement 4: No informational log for empty data in unit-mapping update

**User story:** As a developer, I want `UnitData.update` to stay quiet when
given empty data, so that empty updates produce no misleading "these look like
numbers" advisory.

**Acceptance criteria**

1. WHEN `UnitData.update` is called with empty *data* (no elements), THEN it
   SHALL NOT emit the informational "using categorical units to plot ... all
   parsable as floats or dates" log message.
2. WHEN `UnitData.update` is called with empty *data*, THEN it SHALL leave the
   existing string-to-integer mapping unchanged and SHALL NOT raise.

## Requirement 5: Preserve the parsable-strings informational log for non-empty data

**User story:** As a user, I want the advisory that warns when all my category
strings are actually parsable as numbers/dates to keep working for real input,
so that the guidance remains available.

**Acceptance criteria**

1. WHEN `UnitData.update` is called with non-empty *data* in which every unique
   string is individually parsable as a number or a date, THEN it SHALL emit the
   informational log message.
2. The system SHALL treat the informational-log decision as the conjunction of
   "the data is non-empty" AND "every element is parsable as a number or date";
   neither condition alone SHALL trigger the message.

## Requirement 6: Preserve mapping construction and type checking in unit-mapping update

**User story:** As a maintainer, I want `UnitData.update` to keep building the
category mapping and rejecting invalid types, so that categorical semantics and
error handling are unchanged.

**Acceptance criteria**

1. WHEN `UnitData.update` is called with non-empty *data*, THEN each unique
   value SHALL be assigned a new consecutive integer id if not already present,
   preserving first-seen ordering, and existing ids SHALL be left unchanged.
2. IF any element of *data* is neither `str` nor `bytes`, THEN `UnitData.update`
   SHALL raise a `TypeError`.
3. WHEN a `UnitData` object is constructed with initial data, THEN it SHALL
   populate its mapping from that data using the same rules as `update`.
