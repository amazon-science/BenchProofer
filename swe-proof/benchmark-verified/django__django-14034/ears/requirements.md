# Requirements — Per-subfield required markers for partially-required multi-value form fields

## Introduction

Django's form rendering decides where to place the HTML `required` marker for a
bound field's widget. The relevant logic lives in
`django.forms.boundfield.BoundField.build_widget_attrs(self, attrs, widget=None)`,
which assembles the attribute mapping (notably `required` and `disabled`) used
when the field's widget is rendered.

A `MultiValueField` (`django.forms.fields.MultiValueField`) groups several
subfields under a single composite widget (`django.forms.widgets.MultiWidget`,
one subwidget per subfield). Such a field exposes a `require_all_fields`
attribute. When `require_all_fields` is `False`, the subfields are validated
individually: a subfield declared `required=True` must receive a value even
though other subfields may be left blank.

Previously, the rendering logic placed a single `required` marker on the
composite widget as a whole whenever the field itself was required — it did not
account for the fact that, with `require_all_fields=False`, only *some*
subfields are required. As a result the rendered markup did not reflect the
actual per-subfield requiredness, and a composite field with a mix of required
and optional subfields could not be marked accurately.

The goal is to make `build_widget_attrs` place `required` markers per subwidget
for a partially-required multi-value field, while leaving the placement of
`required` (and `disabled`) unchanged for every other kind of field.

Throughout this document:
- "the guard holds" means all three of the following are true together: the
  widget's own `use_required_attribute(self.initial)` returns true, the bound
  field is required (`self.field.required` is true), and the form permits
  required markers (`self.form.use_required_attribute` is true).
- "the partial-multi condition holds" means all three of the following are true
  together: the field exposes a `require_all_fields` attribute, that attribute
  is `False`, and the field's widget is a `MultiWidget` (an instance of
  `django.forms.widgets.MultiWidget`).

## Requirement 1: Place required markers per subwidget for partially-required multi-value fields

**User story:** As a form author using a `MultiValueField` with
`require_all_fields=False`, I want each subwidget to be marked required only
when its own subfield is required, so that the rendered markup accurately
reflects which parts of the composite field must be filled in.

**Acceptance criteria**

1. WHEN `build_widget_attrs` runs and the guard holds and the partial-multi
   condition holds, THEN the method SHALL NOT add a `required` marker to the
   returned parent attribute mapping.
2. WHEN `build_widget_attrs` runs and the guard holds and the partial-multi
   condition holds, THEN the method SHALL walk the field's subfields paired
   with the composite widget's subwidgets in their aligned order and, for each
   pair, SHALL set that subwidget's own `required` attribute to true exactly
   when both that subwidget's `use_required_attribute(self.initial)` returns
   true AND that subfield is required, and to false otherwise.
3. WHEN a form containing a required `MultiValueField` whose subfields are
   individually optional (`require_all_fields=False`) and which renders through
   a composite multi-widget is rendered, THEN each subwidget corresponding to a
   required subfield SHALL carry the HTML `required` attribute, and each
   subwidget corresponding to a non-required subfield SHALL NOT carry it.
4. The number and order of per-subwidget `required` decisions SHALL correspond
   one-to-one with the field's subfields taken in their declared order.

## Requirement 2: Preserve single required-marker placement for ordinary fields

**User story:** As a form author using an ordinary field (or a multi-value
field that is not partially required), I want the `required` marker to keep
being placed on the field's own widget as before, so that existing rendering
behavior is unchanged.

**Acceptance criteria**

1. WHEN `build_widget_attrs` runs and the guard holds but the partial-multi
   condition does NOT hold, THEN the method SHALL add `required` set to true to
   the returned parent attribute mapping.
2. IF the guard does not hold, THEN `build_widget_attrs` SHALL NOT add any
   `required` marker to the parent attribute mapping and SHALL NOT alter any
   subwidget's `required` attribute on account of the required decision.
3. The system SHALL treat a field whose widget is not a `MultiWidget` as taking
   the ordinary single-marker placement whenever the guard holds, regardless of
   any `require_all_fields` attribute.
4. The system SHALL treat a multi-value field whose `require_all_fields`
   attribute is true as taking the ordinary single-marker placement whenever
   the guard holds.

## Requirement 3: Preserve disabled-marker placement and other attributes

**User story:** As a form author, I want the disabled marker and any incoming
attributes to be handled exactly as before, so that adding per-subwidget
required handling does not regress other attribute behavior.

**Acceptance criteria**

1. WHEN `build_widget_attrs` runs, THEN the method SHALL operate on a copy of
   the incoming `attrs` mapping and SHALL NOT mutate the caller's argument.
2. IF the bound field is disabled, THEN `build_widget_attrs` SHALL add
   `disabled` set to true to the returned parent attribute mapping.
3. IF the bound field is not disabled, THEN `build_widget_attrs` SHALL NOT add
   a `disabled` marker to the returned parent attribute mapping.
4. The system SHALL preserve every entry already present in the incoming
   attribute mapping in the returned mapping, independent of the required and
   disabled decisions.
5. The disabled decision SHALL be independent of the required decision:
   disabling behavior SHALL be identical whether or not the partial-multi
   condition holds.

## Requirement 4: Preserve validation of partially-required multi-value fields

**User story:** As a user submitting a form containing a required
`MultiValueField` with `require_all_fields=False`, I want validation to depend
on the individual subfields, so that a required subfield left blank is rejected
while an optional subfield left blank is accepted.

**Acceptance criteria**

1. WHEN such a form is bound with a non-empty value for every required subfield
   and empty values for the optional subfields, THEN `Form.is_valid()` SHALL
   return true.
2. WHEN such a form is bound with an empty value for a required subfield, THEN
   `Form.is_valid()` SHALL return false.
3. The system SHALL keep the existing cleaning, `has_changed`, disabled-value,
   invalid-choice, and insufficient-data behaviors of `MultiValueField`
   unchanged by the rendering fix.
