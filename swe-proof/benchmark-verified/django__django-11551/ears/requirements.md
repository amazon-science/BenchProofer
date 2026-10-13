# Requirements: Correct `list_display` validation for fields reachable only via an instance

## Introduction

During system checks, Django's admin validates each entry of a `ModelAdmin`'s
`list_display` list/tuple. This validation lives in
`django.contrib.admin.checks` in the `ModelAdmin` checks routine that validates
a single `list_display` entry (`_check_list_display_item`), which is driven for
every entry by `_check_list_display`.

An entry is acceptable when it can be resolved to something usable: a callable,
an attribute of the admin object, a concrete model field obtainable from the
model's metadata, or an attribute/method reachable on the model class. When an
entry cannot be resolved at all, the check must emit `admin.E108`; when it
resolves to a many-to-many relation, the check must emit `admin.E109`.

A regression was introduced when the routine began gating the model-field lookup
behind a `hasattr(obj.model, item)` test. Some fields are exposed through a
descriptor that deliberately raises `AttributeError` when accessed on the model
*class* (rather than on a model instance) — for example a custom position/order
field. For such a field `hasattr(obj.model, item)` is `False`, so the routine
never attempted the metadata field lookup and wrongly rejected a perfectly valid
column with `admin.E108`, preventing the admin (and thus system startup) from
validating.

The goal is to make single-entry validation resolve a field whenever *either*
the model metadata lookup *or* model attribute access can supply one, and to
reject only when neither route succeeds — while preserving the existing
many-to-many and callable/admin-attribute behaviors.

## Requirement 1: Accept callable and admin-object attribute entries

**User story:** As a developer configuring a `ModelAdmin`, I want callables and
attributes of my admin class to be accepted as `list_display` entries, so that
existing display customizations continue to validate.

**Acceptance criteria**
1. WHEN a `list_display` entry is itself callable, THEN the single-entry check
   SHALL report no error for that entry.
2. WHEN a `list_display` entry is not callable BUT is an attribute of the admin
   object being validated, THEN the single-entry check SHALL report no error for
   that entry.
3. IF a `list_display` entry is callable, THEN the single-entry check SHALL NOT
   attempt to resolve a model field for that entry.
4. IF a `list_display` entry is a non-callable attribute of the admin object,
   THEN the single-entry check SHALL NOT attempt to resolve a model field for
   that entry.

## Requirement 2: Resolve a field via model metadata or model attribute access

**User story:** As a developer using a custom field that is accessible only via a
model instance, I want my column to validate as long as the field exists in the
model's metadata, so that upgrading Django does not break my working admin.

**Acceptance criteria**
1. WHEN a `list_display` entry is neither callable nor an attribute of the admin
   object, THEN the single-entry check SHALL attempt to obtain a field for the
   entry by first requesting it from the model's metadata field lookup
   (`obj.model._meta.get_field(item)`).
2. IF the model metadata field lookup reports that no such field exists (raises
   `FieldDoesNotExist`), THEN the single-entry check SHALL attempt to obtain a
   value for the entry by accessing it as an attribute on the model class
   (`getattr(obj.model, item)`).
3. The single-entry check SHALL determine whether a field is resolvable
   independently of whether the entry is accessible as an attribute on the model
   *class*; specifically it SHALL NOT skip the model metadata field lookup merely
   because model-class attribute access for the entry would fail.
4. WHEN the model metadata field lookup succeeds for an entry, THEN the
   single-entry check SHALL treat that entry as resolved and SHALL NOT report
   `admin.E108` for it, regardless of whether the entry is otherwise accessible
   as an attribute on the model class.

## Requirement 3: Reject only unresolvable entries with `admin.E108`

**User story:** As a developer, I want a genuinely misspelled or nonexistent
`list_display` entry to be reported, so that configuration mistakes are caught.

**Acceptance criteria**
1. WHEN a `list_display` entry is neither callable nor an attribute of the admin
   object, AND the model metadata field lookup reports no such field, AND
   accessing the entry as an attribute on the model class fails (raises
   `AttributeError`), THEN the single-entry check SHALL report exactly one error
   with id `admin.E108`.
2. The `admin.E108` error message SHALL state that the value of the given label
   refers to the given entry, which is not a callable, an attribute of the admin
   class, or an attribute or method on the model (identified by its app label and
   object name).
3. IF a field is resolved for an entry by either the model metadata lookup or by
   model-class attribute access, THEN the single-entry check SHALL NOT report
   `admin.E108` for that entry.

## Requirement 4: Report many-to-many fields with `admin.E109`

**User story:** As a developer, I want a many-to-many field used as a
`list_display` column to be flagged, so that unsupported column types are caught.

**Acceptance criteria**
1. WHEN a field is resolved for an entry (by either the model metadata lookup or
   by model-class attribute access) AND that field is a many-to-many relation
   (an instance of `ManyToManyField`), THEN the single-entry check SHALL report
   exactly one error with id `admin.E109`.
2. The `admin.E109` error message SHALL state that the value of the given label
   must not be a many-to-many field.
3. WHEN a field is resolved for an entry and that field is NOT a many-to-many
   relation, THEN the single-entry check SHALL report no error for that entry.
4. IF a field is resolved via model-class attribute access (the metadata lookup
   having reported no such field) AND that resolved field is a many-to-many
   relation, THEN the single-entry check SHALL report `admin.E109` (and SHALL NOT
   report `admin.E108`) for that entry.

## Requirement 5: Preserve full `list_display` validation behavior

**User story:** As a maintainer, I want the overall `list_display` validation to
keep working across all previously supported cases, so that no existing
configuration regresses.

**Acceptance criteria**
1. The system SHALL produce at most one error per `list_display` entry and SHALL
   aggregate the per-entry results across all entries of `list_display`.
2. WHEN `list_display` is not a list or tuple, THEN the check SHALL report the
   pre-existing `admin.E107` error and SHALL NOT evaluate individual entries.
3. The single-entry check SHALL emit an error whose reported label matches the
   position of the offending entry within `list_display`.
4. The system SHALL keep accepting entries that name a concrete, non-relational
   model field, a valid model attribute/method, a callable, or an admin-object
   attribute, reporting no error for such entries.
