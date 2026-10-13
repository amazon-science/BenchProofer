# mapping.md — django__django-14034

## Modeled function

| Lean | Python | file:line @ base_commit `db1fc5cd3c` |
|---|---|---|
| `implementation_requiredAttrs` / `problem_spec_requiredAttrs` / `correct_requiredAttrs` | `BoundField.build_widget_attrs(self, attrs, widget=None)` — assemble the HTML attribute decisions (`required`, per-subwidget `required`, `disabled`) for a bound field's widget | `django/forms/boundfield.py:232-241` (the `if widget.use_required_attribute(...) and self.field.required and self.form.use_required_attribute:` block) |

## What is modeled (the touched decision)

The method copies the incoming attribute mapping, then under the guard
`widget.use_required_attribute(initial) and self.field.required and self.form.use_required_attribute`
decides where the HTML `required` flag is placed. The post-patch behavior:

- For a multi-value field whose subfields are individually optional (it exposes a
  `require_all_fields` attribute set to `False`) and whose widget is a composite
  multi-widget: the `required` flag is set **per subwidget**, each subwidget's
  value being `subwidget.use_required_attribute(initial) and subfield.required`.
  The parent mapping does **not** receive `required`.
- Otherwise: the parent mapping receives `required = True` (the ordinary case).

Independently, `disabled = True` is added to the parent mapping iff the field is
disabled. The copy of the incoming mapping's other entries is pure pass-through
(identity) and is not part of the modeled decision.

The four observable decision outputs are captured in a `Result` structure:
`parentRequired`, `parentDisabled`, `subwidgetRequired` (the list of flags written
to the subwidgets, in order), and `perSubBranch` (whether the per-subwidget branch
ran).

## Type bijection (Lean ↔ Python) — used by G-CONF (+ I/O bridging)

| Python | Lean | notes |
|---|---|---|
| `self.field.required : bool` | `FieldInfo.required : Bool` | field-level required flag |
| `self.field.disabled : bool` | `FieldInfo.disabled : Bool` | field disabled flag |
| `hasattr(self.field, 'require_all_fields')` | `FieldInfo.hasRequireAllFields : Bool` | does the field expose the per-subfield-optional attribute |
| `self.field.require_all_fields : bool` | `FieldInfo.requireAllFields : Bool` | when the attribute is absent this is irrelevant (guarded by `hasRequireAllFields`) |
| `isinstance(self.field.widget, MultiWidget)` | `FieldInfo.isMultiWidget : Bool` | is the field's widget a composite multi-widget |
| `zip(self.field.fields, widget.widgets)` — the paired walk | `FieldInfo.subPairs : List (Bool × Bool)` | one entry per `(subwidget, subfield)` pair, in the SAME aligned order Python zips; each entry is `(subUseReq, subRequired)`. Modeling the two aligned sequences as a single pre-zipped list removes the implicit field↔widget alignment invariant — the pairing is fixed by construction. |
| `subwidget.use_required_attribute(initial)` (per pair) | `subPairs[i].1 : Bool` | per-subwidget predicate result (unchanged callee; supplied as an input boolean) |
| `subfield.required` (per pair) | `subPairs[i].2 : Bool` | per-subfield required flag |
| `widget.use_required_attribute(self.initial) : bool` | `widgetUseReq : Bool` | guard predicate result (unchanged callee; input boolean) |
| `self.form.use_required_attribute : bool` | `formUseReq : Bool` | form-level switch |
| returned `attrs.get('required')` | `Result.parentRequired : Bool` | `True` iff `'required'` set on the parent mapping |
| returned `attrs.get('disabled')` | `Result.parentDisabled : Bool` | `True` iff `'disabled'` set on the parent mapping |
| `[w.attrs.get('required') for w in widget.widgets]` after the call | `Result.subwidgetRequired : List Bool` | values written to subwidgets (only when the per-subwidget branch runs) |

## Callee provenance / flag deps

- `Widget.use_required_attribute(initial)` (`django/forms/widgets.py:280`,
  base: `return not self.is_hidden`; overridden by `CheckboxInput`,
  `ClearableFileInput`, `Select`, …) is the UNCHANGED predicate the method
  consults. The patch does not touch it. Its boolean result is modeled as a
  **plain input** to the modeled decision (`widgetUseReq`, `subUseReq`), not
  computed inside the impl — so there is no opaque callee and no consumed `_prop`
  axiom. G-CONF bridges this input by calling the real predicate on real widgets
  and feeding the result to the shadow (I/O bridging); G-AX is therefore a skip
  stub (no axiom to validate).
- `MultiWidget` (`django/forms/widgets.py:793`) — the composite-widget class; the
  modeled flag `isMultiWidget` is `isinstance(self.field.widget, MultiWidget)`.
- The per-subfield-optional attribute (`require_all_fields`) lives on the
  multi-value field; `hasRequireAllFields` mirrors the `hasattr(...)` guard so a
  plain field (without the attribute) takes the ordinary branch.

## G-CONF fuzz seed

`conf_seed = 14034` (pinned; see conformance_check.py and meta.json).
