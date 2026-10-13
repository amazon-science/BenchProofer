# Requirements: `model_to_dict()` field-selection semantics

## Introduction

`django.forms.models.model_to_dict(instance, fields=None, exclude=None)` builds
a dictionary of a model instance's editable field data, suitable for use as a
form's `initial` argument. It walks the instance's concrete fields, private
fields, and many-to-many fields in their model-declared order and, for each
retained field, stores the value extracted from the instance under the field's
name.

The function accepts two optional filtering arguments:

- `fields` — an optional inclusion selection. When supplied, only fields whose
  names appear in it are returned.
- `exclude` — an optional exclusion list. When supplied, any field whose name
  appears in it is dropped, even if it also appears in `fields`.

The defect being corrected is that the inclusion selection was tested for truth
rather than for presence: an **empty** `fields` list was treated the same as an
**absent** one (i.e. "no selection"), so `model_to_dict(instance, fields=[])`
returned every editable field instead of nothing. The goal is to distinguish an
absent selection (no inclusion constraint) from a present-but-empty selection (a
genuine request that selects no field), while leaving all other behavior
unchanged.

## Requirement 1: Absent inclusion selection imposes no constraint

**User story:** As a caller who omits the `fields` argument, I want every
editable field returned, so that the default behavior of extracting all of an
instance's editable data is preserved.

**Acceptance criteria**

1. WHEN `model_to_dict` is called with the `fields` argument absent or `None`,
   THEN the function SHALL include every field that is editable and not barred
   by the exclusion argument.
2. The system SHALL treat an absent `fields` argument as imposing no inclusion
   constraint whatsoever.

## Requirement 2: Empty inclusion selection selects no field

**User story:** As a caller who passes an empty `fields` list, I want an empty
result, so that requesting "no fields" actually returns no fields.

**Acceptance criteria**

1. WHEN `model_to_dict` is called with `fields` supplied as an empty list,
   THEN the function SHALL return an empty mapping.
2. The system SHALL distinguish a present-but-empty inclusion selection from an
   absent inclusion selection: the former SHALL include no field, whereas the
   latter SHALL include all otherwise-eligible fields.
3. IF an inclusion selection is present, THEN a field SHALL be included only
   when its name occurs in that selection, regardless of whether the selection
   is empty or non-empty.

## Requirement 3: Non-empty inclusion selection restricts to named fields

**User story:** As a caller who passes a list of field names, I want only those
fields returned, so that I can fetch a specific subset of an instance's data.

**Acceptance criteria**

1. WHEN `model_to_dict` is called with `fields` supplied as a non-empty list,
   THEN the function SHALL include only those editable fields whose names occur
   in that list and which are not barred by the exclusion argument.
2. The system SHALL preserve the model-declared order of the retained fields in
   the result; it SHALL NOT reorder fields to match the order given in the
   inclusion selection.
3. The system SHALL omit any name in the inclusion selection that does not
   correspond to an editable field of the instance.

## Requirement 4: Exclusion argument semantics are unchanged

**User story:** As a caller using the `exclude` argument, I want its existing
behavior kept intact, so that upgrading does not change how excluded fields are
handled.

**Acceptance criteria**

1. WHEN `model_to_dict` is called with `exclude` supplied as a non-empty list,
   THEN the function SHALL drop every field whose name occurs in that list, even
   if that field's name also occurs in the inclusion selection.
2. WHEN `model_to_dict` is called with `exclude` absent, `None`, or an empty
   list, THEN the function SHALL treat the exclusion as barring no field.
3. The system SHALL keep the result for `exclude` supplied as an empty list
   identical to the result obtained when `exclude` is absent, given the same
   instance and inclusion selection.

## Requirement 5: Editability and value extraction are unchanged

**User story:** As a maintainer, I want the retained-field data to be produced
exactly as before, so that only the empty-`fields` case changes.

**Acceptance criteria**

1. The system SHALL consider only editable fields; a field that is not editable
   SHALL never appear in the result, regardless of the inclusion or exclusion
   arguments.
2. WHEN a field is retained, THEN the function SHALL pair the field's own name
   with the value extracted from that field for the given instance.
3. The system SHALL consider the instance's concrete fields, private fields, and
   many-to-many fields, walking them in their model-declared order.
