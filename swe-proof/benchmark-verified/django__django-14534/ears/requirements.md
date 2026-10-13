# Requirements: Correct label identifier for iterable choice-widget options

## Introduction

Django's forms layer lets a template iterate over the individual options of a
multi-option choice widget (for example a `CheckboxSelectMultiple` or a radio
`Select`) via `BoundField.subwidgets`. Each iterated option is wrapped in a
`BoundWidget` (`django/forms/boundfield.py`), a small container holding the
option's presentation data in its `data` mapping. Templates commonly render a
`<label for="…">` for each option and obtain the target identifier from
`BoundWidget.id_for_label`.

The option's presentation data is produced by the widget layer
(`ChoiceWidget.create_option` / `options` in `django/forms/widgets.py`). That
layer already computes the exact HTML `id` the option's input element will carry
— honoring the form's `auto_id` format string, any per-widget `attrs['id']`, and
the option's positional index — and stores it in the option data under
`attrs['id']`.

The defect: `BoundWidget.id_for_label` ignores that computed value and instead
rebuilds an identifier from a hard-coded `'id_%s_%s'` template using the
option's name and index. As a result, when a non-default `auto_id` scheme is
used (or when no id applies), the label target reported for a subwidget does not
match the id actually rendered on the input element. The goal is to make
`BoundWidget.id_for_label` report exactly the identifier already stored in the
option's data, so the label always points at the real element id.

## Requirement 1: Report the option's actual rendered identifier

**User story:** As a template author iterating over the options of a choice
widget, I want each option's `id_for_label` to return the same identifier that
the option's input element is actually rendered with, so that my
`<label for="…">` correctly targets that option.

**Acceptance criteria**

1. WHEN `id_for_label` is read on a `BoundWidget` describing one option of an
   iterable choice widget, THEN the property SHALL return the value stored under
   the `'id'` key of that option's attributes mapping (`self.data['attrs']`).
2. WHEN the option's attributes mapping contains an `'id'` entry, THEN
   `id_for_label` SHALL return exactly that stored value unchanged, without
   reconstructing or reformatting it from the option's name or index.
3. IF the option's attributes mapping contains no `'id'` entry, THEN
   `id_for_label` SHALL return `None` rather than a synthesized identifier.
4. The system SHALL derive the reported identifier solely from the option's
   attributes mapping; the option's `name` and `index` fields SHALL NOT
   influence the returned value.

## Requirement 2: Honor the form's auto_id scheme in subwidget identifiers

**User story:** As a developer who initializes a form with a custom `auto_id`
format string, I want the identifiers reported for a widget's subwidgets to
reflect that prefix, so that generated labels are consistent with the rendered
element ids.

**Acceptance criteria**

1. WHEN a form is initialized with a custom `auto_id` format string and a field
   using a multi-option choice widget is expanded into its subwidgets, THEN each
   subwidget's `id_for_label` SHALL reflect that `auto_id`-derived prefix as
   applied to the field, together with the subwidget's positional index.
2. WHEN successive subwidgets of the same field are inspected, THEN their
   `id_for_label` values SHALL differ by the per-option index component supplied
   by the widget layer, matching the ids emitted on the corresponding input
   elements.
3. WHILE a per-widget explicit `id` attribute or the form's default `auto_id`
   scheme is in effect, the reported subwidget identifier SHALL still equal the
   id that the widget layer places in the option's attributes mapping.

## Requirement 3: Preserve existing subwidget behavior (regression protection)

**User story:** As a maintainer, I want the change confined to how the label
identifier is looked up, so that all other subwidget behavior continues to work
unchanged.

**Acceptance criteria**

1. WHEN a form field backed by an iterable choice widget is expanded, THEN the
   number of subwidgets and their ordering SHALL remain unchanged, one per
   available option.
2. WHEN a subwidget's `choice_label` is read, THEN it SHALL continue to return
   the option's human-readable label from the option data.
3. WHEN a subwidget is rendered (its `tag`/string form), THEN the produced markup
   SHALL be unaffected by this change.
4. WHEN a field is expanded with no applicable identifier (for example when
   automatic id generation is disabled for the form), THEN each subwidget's
   `id_for_label` SHALL return `None` and the option SHALL still render and
   expose its label.
5. The system SHALL leave `BoundField.id_for_label` (the field-level label
   identifier, distinct from the per-option `BoundWidget.id_for_label`)
   behaving as before, continuing to honor an explicit widget `id` attribute and
   otherwise the field's automatically generated id.
