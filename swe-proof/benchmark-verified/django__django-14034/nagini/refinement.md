# refinement.md — django__django-14034

The operation-by-operation correspondence between `model.py`'s implementation
(the `build_required_attrs` impl region, the deep `constituent_marker` model)
and `patch.diff` (the gold patch). Each step is tagged **R** (type
refinement), **A** (axiomatized callee — split into **A-consumed**, where the
proof uses the axiom's `Ensures`, and **A-reference**, where a deep model is
validated == the real callee by axiom_check.py / G-AX), or **I** (identical
concrete operation). The claim: *any implementation that verifies against this
frozen spec, refined per the map below, is behaviourally equal to the gold
patch on the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## The single change site — `BoundField.build_widget_attrs` (`django/forms/boundfield.py:232`)

Gold hunk (body, `boundfield.py:235-242`):
```python
 if widget.use_required_attribute(self.initial) and self.field.required and self.form.use_required_attribute:
-    attrs['required'] = True
+    # MultiValueField has require_all_fields: if False, fall back on subfields.
+    if (
+        hasattr(self.field, 'require_all_fields') and
+        not self.field.require_all_fields and
+        isinstance(self.field.widget, MultiWidget)
+    ):
+        for subfield, subwidget in zip(self.field.fields, widget.widgets):
+            subwidget.attrs['required'] = subwidget.use_required_attribute(self.initial) and subfield.required
+    else:
+        attrs['required'] = True
```
(Plus the import hunk `from django.forms.widgets import MultiWidget, Textarea, TextInput` — a non-behavioral name import, no model op.)

| # | model.py impl op (`build_required_attrs`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| 1 | `if widget_mark and field_required and form_marks:` | `if widget.use_required_attribute(self.initial) and self.field.required and self.form.use_required_attribute:` | R | the three boolean callee/attribute reads collapse to three bool inputs (`widget_mark`, `field_required`, `form_marks`); the `and` chain is identical. The truthiness of `use_required_attribute(initial)` is what the chain consumes — coerced via `bool(...)` in axiom_check (mapping.md §2, §3.1). |
| 2 | `if is_partial_multi:` | `if (hasattr(self.field,'require_all_fields') and not self.field.require_all_fields and isinstance(self.field.widget, MultiWidget)):` | R | the three-way regime guard collapses to one bool input `is_partial_multi`; its truth value is all the modeled behavior consumes. `hasattr(...)` is False for ordinary fields ⇒ `is_partial_multi` False ⇒ regime B, faithfully (mapping.md §2). |
| 3 | `while i < len(subs): ... sub = subs[i]` | `for subfield, subwidget in zip(self.field.fields, widget.widgets):` | R | index loop over `List[Constituent]` ↔ the `zip` iteration over the (subfield, subwidget) pairs; `subs[i]` ↔ the i-th pair. `zip` truncates to the shorter, and Django builds the two lists equal-length, so the lengths match (mapping.md §2). |
| 4 | `sub.marker = 1 if (sub.widget_mark and sub.field_required) else 0` (the if/else assigning the per-constituent marker, equal to `constituent_marker(...)`) | `subwidget.attrs['required'] = subwidget.use_required_attribute(self.initial) and subfield.required` | A-reference | the changed per-constituent assignment is modeled **deeply** by `constituent_marker` (pure region) + the loop body. There is no consumed axiom. The deep model is validated **== the real callees** out-of-band: G-AX runs the real `subwidget.use_required_attribute(initial)` for every (widget kind, initial) and asserts `constituent_marker(widget_mark, field_required)` equals the boolean product `use_required_attribute(initial) and subfield.required`; and that the rendered `required` token appears iff the assigned marker is `True` (mapping.md §3.1, §3.2). `True`↔`marker==1`, `False`↔`marker==0`. |
| 5 | `else: out.required_attr = 1` | `else: attrs['required'] = True` | R | the aggregate marker slot ↔ the `attrs['required']` key; `1` ↔ assigning `True`; the `else` (regime B) is identical control flow (mapping.md §2). |
| 6 | `if field_disabled: out.disabled_attr = 1` | `if self.field.disabled: attrs['disabled'] = True` (`boundfield.py:237-238`, unchanged) | I | the disabled marker assignment is unchanged by the patch and identical under the same R-refinement of `attrs['disabled']`. Included so the model's frame is exact (the spec pins it). |

## The discriminating behaviour (G-DIFF)

The change content lives in steps 2–5: when the aggregate guard holds **and**
the field is a partially-required multi-value field with a composite widget
(regime A), the patch assigns **per-constituent** markers
(`subwidget.attrs['required'] = use_required_attribute(initial) and subfield.required`)
and does NOT set the aggregate `attrs['required']`; otherwise (regime B) it sets
the aggregate marker. The pre-patch code lacks the regime-A branch entirely and
always sets the aggregate marker inside the guard.

`model_prepatch.py` reproduces the pre-patch impl (`if guard: out.required_attr
= 1`, no regime-A branch) and **fails** the postcondition

  `Implies((widget_mark and field_required and form_marks) and is_partial_multi, out.required_attr == -1)`

— exactly the spec sensing the change (G-DIFF). It would also violate the
per-constituent clause (`subs[k].marker == constituent_marker(...)`), since the
pre-patch leaves every constituent marker unset; the verifier reports the
aggregate-slot clause first. This is the single independently-fixed behavior, so
one `model_prepatch.py` suffices.

## No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-reference, or I. The one operation that genuinely
*changed* — the per-constituent marker assignment — is modeled **deeply**
(`constituent_marker` + the verified loop, step 4, an **A-reference**), not
hidden behind an axiom about the function under change. There is **no consumed
axiom** (`# axioms-start/end` is empty by design): nothing opaque is referenced
inside an `Ensures`; the only callees (`use_required_attribute`, the rendering
template) are **unchanged** and are validated by G-AX as A-references.

## verify(model) ⇒ resolved

`build_required_attrs` verifies only if, in regime A, the aggregate marker is
left unset (`required_attr == -1`) and each constituent marker equals
`constituent_marker(widget_mark, field_required)` (step 4); in regime B the
aggregate marker is set (step 5); and the guard/disabled framing matches (steps
1, 6). By R (the `attrs`-dict ↔ tri-state-slot and bool-input refinements) and
by G-AX (the deep model `constituent_marker` == the real `use_required_attribute
and subfield.required`, and the rendering rule), the verified method equals the
gold-patched `build_widget_attrs` on the tested inputs: the required subinput
renders `required`, the optional one does not, and ordinary fields are
unchanged. The gold patch resolves (G-RESOLVE). The trust points are exactly the
two of PLAN §1.1: axiom/deep-model soundness (G-AX) and refinement fidelity
(this document, G-EQ).
