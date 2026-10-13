# Requirements: Include the offending field name in the readonly_fields admin check error

## Introduction

Django's admin system-check framework validates each entry configured in a
`ModelAdmin` (or `InlineModelAdmin`) subclass. When an entry listed in
`readonly_fields` cannot be resolved, the check helper
`BaseModelAdminChecks._check_readonly_fields_item` (in
`django/contrib/admin/checks.py`) emits a `checks.Error` with id `admin.E035`.

Historically that error text cited only the *position* of the offending entry
(for example the label `readonly_fields[0]`) but did **not** state the actual
value at that position. Other admin checks (such as those for `list_editable`,
`list_display`, `raw_id_fields`) already name the offending value in their
messages. The goal of this change is to unify the diagnostics so the
`readonly_fields` error also names the offending value, making the message
self-explanatory without the reader having to count list indices back to the
source configuration.

The affected code is the diagnostic produced inside
`BaseModelAdminChecks._check_readonly_fields_item`; the resolution logic that
decides *whether* an entry is acceptable is unchanged.

## Requirement 1: Name the offending value in the readonly_fields resolution error

**User story:** As a developer subclassing `ModelAdmin` or `InlineModelAdmin`, I
want the `readonly_fields` validation error to tell me exactly which configured
value is unresolvable, so that I can locate and fix the mistake without manually
mapping a list index back to my configuration.

**Acceptance criteria**

1. WHEN a `readonly_fields` entry is not callable, is not an attribute of the
   admin object, is not an attribute of the bound model, and is not a declared
   field of the bound model, THEN `_check_readonly_fields_item` SHALL return
   exactly one `checks.Error` with id `admin.E035`.
2. WHEN such an unresolvable `readonly_fields` entry is reported, THEN the error
   message SHALL include the offending value itself (the field name string that
   was configured) verbatim, in addition to the positional label.
3. WHEN such an error message is produced, THEN it SHALL state, in a single
   sentence and in this order, (a) the positional label of the entry (e.g.
   `readonly_fields[0]`), (b) that this label refers to the offending value,
   (c) that the value is not a callable, (d) that it is not an attribute of the
   admin class (named by the admin object's class name), and (e) that it is not
   an attribute of the bound model (named by the model's app-qualified label).
4. The system SHALL phrase the readonly_fields diagnostic so that it names the
   offending value using the same "refers to '<value>', which is not …"
   construction already used by comparable admin checks, unifying the wording
   across checks.
5. WHEN the admin object is an inline admin (an `InlineModelAdmin` subclass),
   THEN the produced message SHALL name that inline admin's own class name and
   its bound model's label, exactly as for a top-level `ModelAdmin`.
6. WHEN more than one `readonly_fields` entry is unresolvable, THEN each such
   entry SHALL produce its own `admin.E035` error, and each message SHALL cite
   that entry's own positional label and its own offending value.

## Requirement 2: Preserve acceptance of resolvable readonly_fields entries

**User story:** As a developer, I want valid `readonly_fields` entries to keep
passing the admin checks unchanged, so that this diagnostic improvement does not
introduce spurious errors.

**Acceptance criteria**

1. IF a `readonly_fields` entry is a callable, THEN
   `_check_readonly_fields_item` SHALL return no errors for that entry.
2. IF a `readonly_fields` entry is the name of an attribute or method defined on
   the admin object (the `ModelAdmin`/`InlineModelAdmin` instance), THEN the
   check SHALL return no errors for that entry.
3. IF a `readonly_fields` entry is the name of an attribute or method defined on
   the bound model, THEN the check SHALL return no errors for that entry.
4. IF a `readonly_fields` entry is the name of a declared field of the bound
   model, THEN the check SHALL return no errors for that entry.
5. The system SHALL keep the acceptance decision (which entries are valid versus
   unresolvable) exactly as before this change; only the text of the emitted
   error for unresolvable entries changes.

## Requirement 3: Preserve unrelated admin-check behavior

**User story:** As a maintainer, I want all other admin system checks to behave
exactly as before, so that this focused wording change to the readonly_fields
error does not regress any other validation.

**Acceptance criteria**

1. The system SHALL leave the error id for the readonly_fields resolution
   failure as `admin.E035`, and SHALL continue to attach the error to the admin
   class as its object.
2. The system SHALL leave the validation of other admin options (for example
   `list_display`, `list_editable`, `raw_id_fields`, `fields`, `fieldsets`,
   `exclude`, and inline options) — including their error ids and message text —
   unchanged.
3. WHEN a `readonly_fields` value has an invalid container type (e.g. it is not
   a list or tuple), THEN the pre-existing distinct diagnostic for that case
   SHALL continue to be produced unchanged (it is separate from the per-item
   resolution error).
4. The system SHALL continue to run readonly_fields item validation over every
   configured entry, in configuration order, so that positional labels remain
   correct.
