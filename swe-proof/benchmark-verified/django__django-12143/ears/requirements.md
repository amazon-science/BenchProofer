# Requirements: Literal-safe prefix matching when selecting edited primary keys in the admin changelist

## Introduction

The Django admin's changelist view supports bulk editing of rows through
`list_editable`. When such a form is submitted, the admin needs to recover the
primary-key values of the rows that were edited. This is done in
`django/contrib/admin/options.py` by two `ModelAdmin` methods:

- `ModelAdmin._get_edited_object_pks(request, prefix)` scans the submitted
  `request.POST` items and returns the values whose keys identify an editable
  row's primary-key field for the given formset `prefix`.
- `ModelAdmin._get_list_editable_queryset(request, prefix)` uses those values to
  build a queryset restricted to the edited objects.

To recognise the relevant POST keys, `_get_edited_object_pks` builds a pattern
from the formset `prefix` and the model's primary-key field name and matches it
against each submitted key. A formset prefix is caller-controlled and has no
restriction on its characters — it may contain characters that carry special
meaning inside a regular expression (for example `$`, `.`, `*`, `+`, `(`, `[`,
`\`). The original implementation interpolated the raw `prefix` into a regular
expression, so such a prefix changed the meaning of the pattern rather than
being matched literally. The result was that edited rows could be missed (or,
in principle, spuriously matched), causing the wrong set of objects to be
selected for editing — a potential silent data-loss defect.

The goal is to ensure that the formset prefix is always treated as a literal
string when identifying edited primary-key POST keys, regardless of which
characters it contains, while preserving all existing behavior for ordinary
prefixes.

## Requirement 1: Match the formset prefix literally when identifying edited primary-key keys

**User story:** As a site administrator bulk-editing rows whose formset prefix
contains regular-expression metacharacters, I want the admin to still recognise
exactly the primary-key POST keys for that prefix, so that my edits are applied
to the correct rows and no data is silently lost.

**Acceptance criteria**

1. WHEN `ModelAdmin._get_edited_object_pks` is called with a `prefix` and the
   request's POST data, THEN the method SHALL treat every character of `prefix`
   as an ordinary literal character, so that characters which would otherwise
   have special meaning in a regular expression (such as `$`, `.`, `*`, `+`,
   `?`, `(`, `)`, `[`, `]`, `{`, `}`, `|`, `^`, `\`) match only themselves.
2. WHEN a POST key has the form of the given `prefix`, followed by a hyphen, a
   non-empty run of decimal digits, another hyphen, and the model's primary-key
   field name, THEN `_get_edited_object_pks` SHALL include that key's value in
   its returned list.
3. IF a POST key does not begin with the given `prefix` matched character-for-
   character (including any metacharacters in `prefix`), THEN
   `_get_edited_object_pks` SHALL NOT include that key's value in its returned
   list.
4. WHEN a `prefix` containing regular-expression metacharacters is used and a
   POST key differs from it only in a position where a metacharacter would
   otherwise have matched a different character, THEN `_get_edited_object_pks`
   SHALL NOT treat that key as a match.
5. The values returned by `_get_edited_object_pks` SHALL be exactly the POST
   values of the qualifying keys, kept in the order in which the POST items are
   iterated, with each value carried through unchanged.

## Requirement 2: Preserve existing selection behavior for ordinary prefixes

**User story:** As a maintainer, I want bulk editing with ordinary formset
prefixes to keep behaving exactly as before, so that the fix introduces no
regression for the common case.

**Acceptance criteria**

1. WHEN `_get_edited_object_pks` is called with a `prefix` that contains no
   regular-expression metacharacters (for example the default `form`), THEN the
   method SHALL return the same primary-key values it returned prior to the fix.
2. The pattern used to identify a qualifying key SHALL continue to require a
   non-empty run of decimal digits between the prefix and the primary-key field
   name, and SHALL continue to anchor the primary-key field name at the end of
   the key.
3. WHEN the model's primary-key field is named something other than `id`
   (a custom primary key), THEN `_get_edited_object_pks` SHALL identify
   qualifying keys using that model's actual primary-key field name.

## Requirement 3: Build the edited-objects queryset from the literally matched keys

**User story:** As a site administrator, I want the queryset of edited objects
to reflect exactly the rows whose primary keys were submitted under my formset
prefix, so that the correct objects are updated.

**Acceptance criteria**

1. WHEN `_get_list_editable_queryset(request, prefix)` is called, THEN it SHALL
   determine the edited primary-key values via `_get_edited_object_pks` using
   the same `prefix`, so that a prefix containing regular-expression
   metacharacters yields the queryset for exactly the rows submitted under that
   prefix.
2. WHEN the submitted primary-key values are all valid for the model's
   primary-key field, THEN `_get_list_editable_queryset` SHALL return a queryset
   restricted to the objects whose primary keys are among those submitted
   values.
3. IF a submitted primary-key value cannot be converted to the model's
   primary-key type (indicating tampered POST data), THEN
   `_get_list_editable_queryset` SHALL return the unrestricted queryset for the
   model rather than raising an error.
4. WHEN a formset prefix contains a regular-expression metacharacter and the
   corresponding valid rows are submitted, THEN the count of objects in the
   returned queryset SHALL equal the number of distinct submitted rows whose
   keys qualify under that prefix.
