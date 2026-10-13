# Requirements: Allow overriding the widget in `formfield_for_manytomany()`

## Introduction

Django's admin builds form fields for a model's database fields through
`BaseModelAdmin.formfield_for_dbfield` in
`django/contrib/admin/options.py`. For relation fields this delegates to
`formfield_for_foreignkey` (for `ForeignKey`) and
`formfield_for_manytomany` (for `ManyToManyField`). Before either is called,
`formfield_for_dbfield` merges any `formfield_overrides` entry for the field's
class into the keyword arguments, so a developer who configures the
`formfield_overrides` mapping on a `ModelAdmin` to supply a `widget` for the
`ManyToManyField` class expects that supplied widget to be used.

`formfield_for_foreignkey` already respects a caller-supplied widget: it only
picks an admin default widget (autocomplete, raw-id, or radio) when no `widget`
key is present in its keyword arguments. `formfield_for_manytomany`, however,
runs its widget-selection cascade unconditionally: whenever the field name
matches one of the admin's classification lists (`autocomplete_fields`,
`raw_id_fields`, `filter_vertical`, or `filter_horizontal`), it assigns
`kwargs['widget']`, overwriting whatever widget the caller already provided.
As a result, a `formfield_overrides` widget for a `ManyToManyField` is silently
discarded whenever the field is also configured for one of those admin widgets.

The goal is to make `formfield_for_manytomany` behave like
`formfield_for_foreignkey`: honor a caller-supplied widget when one is present,
and otherwise fall back to the existing admin widget-selection cascade — while
preserving all of that cascade's existing behavior, the many-to-many help-text
augmentation, and the unrelated single-field/foreign-key widget behavior.

## Requirement 1: Honor a caller-supplied widget for many-to-many fields

**User story:** As a developer configuring a `ModelAdmin`, I want a widget I
specify for a `ManyToManyField` (for example via `formfield_overrides`) to be
used, so that my chosen widget is not silently replaced by an admin default.

**Acceptance criteria**

1. WHEN `formfield_for_manytomany` is called for a `ManyToManyField` and a
   `widget` value is already present in the incoming keyword arguments, THEN the
   method SHALL leave that widget in place and SHALL NOT replace it with any
   admin-selected widget.
2. WHEN a `ModelAdmin` sets `formfield_overrides` for `ManyToManyField` to a
   mapping that specifies a `widget`, AND the same field is also listed in the
   admin's `filter_vertical`, `filter_horizontal`, `raw_id_fields`, or
   `autocomplete_fields`, THEN the form field produced by `formfield_for_dbfield`
   for that field SHALL use the widget from `formfield_overrides` rather than the
   widget the classification cascade would otherwise select.
3. WHEN the form field for such a field is produced, THEN the widget actually
   used by that field SHALL be an instance of the class the developer supplied
   through `formfield_overrides` (as observed on the resulting form field's
   widget, allowing for the admin's relation-field widget wrapper around it).
4. IF a `widget` value is present in the incoming keyword arguments, THEN
   `formfield_for_manytomany` SHALL skip the entire widget-selection cascade,
   evaluating none of the `autocomplete_fields`, `raw_id_fields`,
   `filter_vertical`, or `filter_horizontal` membership checks for the purpose of
   choosing a widget.

## Requirement 2: Preserve the default widget-selection cascade when no widget is supplied

**User story:** As a Django admin user, I want the automatic many-to-many widget
selection to keep working when I have not overridden the widget, so that
autocomplete, raw-id, and filtered-select fields still render as before.

**Acceptance criteria**

1. WHEN `formfield_for_manytomany` is called and no `widget` value is present in
   the incoming keyword arguments, THEN the method SHALL choose the widget using
   the existing cascade in this priority order: autocomplete first, then raw-id,
   then filtered-select.
2. WHEN no widget is supplied AND the field name is among the fields returned by
   `get_autocomplete_fields(request)`, THEN the method SHALL select the
   autocomplete multi-select widget for the field.
3. WHEN no widget is supplied AND the field name is not an autocomplete field but
   is listed in `raw_id_fields`, THEN the method SHALL select the many-to-many
   raw-id widget for the field.
4. WHEN no widget is supplied AND the field name is neither an autocomplete field
   nor a raw-id field but appears in `filter_vertical` or `filter_horizontal`,
   THEN the method SHALL select the filtered multi-select widget, configured as
   vertical when the field name is in `filter_vertical` and horizontal otherwise.
5. WHEN no widget is supplied AND the field name matches none of those
   classification lists, THEN the method SHALL leave the widget unset and let the
   field's own default widget apply.

## Requirement 3: Preserve surrounding many-to-many and related-field behavior (regression protection)

**User story:** As a maintainer, I want every other behavior of
`formfield_for_manytomany` and its neighbors to be unchanged, so that this fix
introduces no regressions in the admin's form-field construction.

**Acceptance criteria**

1. WHEN the many-to-many field uses an intermediary (`through`) model that was
   not auto-created, THEN `formfield_for_manytomany` SHALL return no form field
   (the field is not shown), exactly as before.
2. WHEN no `queryset` value is present in the incoming keyword arguments, THEN
   the method SHALL keep computing and applying the ordering-aware related
   queryset exactly as before; a caller-supplied `queryset` SHALL be left in
   place.
3. WHEN the produced form field uses a plain multiple-select widget that is
   neither a checkbox multi-select nor the autocomplete multi-select, THEN the
   method SHALL keep augmenting the field's help text with the existing
   "hold down Control/Command to select more than one" guidance; and it SHALL NOT
   add that guidance for checkbox or autocomplete multi-select widgets.
4. The behavior of `formfield_for_foreignkey` — honoring a supplied widget and
   otherwise selecting autocomplete, raw-id, or radio widgets — SHALL remain
   unchanged.
5. WHEN `formfield_for_dbfield` builds a form field for a relation field
   (`ForeignKey` or `ManyToManyField`) that is not a raw-id field, THEN it SHALL
   continue to wrap the field's widget in the admin's related-field widget
   wrapper as before, so that a caller-supplied many-to-many widget is observed
   as the wrapper's inner widget.
6. The construction of form fields for non-relation database fields, for
   choice/radio fields, and the merging of `formfield_overrides` and explicit
   keyword arguments in `formfield_for_dbfield` SHALL remain unchanged.
