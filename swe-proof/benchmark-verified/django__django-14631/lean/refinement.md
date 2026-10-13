# refinement.md — django__django-14631

Maps every operation in `implementation_cleanFields` to its `patch.diff`
counterpart. Tags: **R** (type refinement), **A-consumed** (proof uses an axiom),
**A-reference** (deep model, G-AX-validated == real callee), **I** (identical op).

The modeled function is the per-field value selection in `BaseForm._clean_fields`
(`django/forms/forms.py`). The gold patch rewrites the loop to iterate
`self._bound_items()` and to take `value = bf.initial if field.disabled else
bf.data`. The behavioral content of that rewrite is what is modeled. The other
edits in the patch (`changed_data`, `_html_output`, `_bound_items`, `__iter__`,
`BoundField._has_changed`, `BoundField.data`) are behavior-preserving code
movement and carry no separate discriminator — see mapping.md "Unmodeled".

| # | impl op (Solution.lean) | patch.diff counterpart | tag | note |
|---|---|---|---|---|
| 1 | `for f in fields do …` | `for name, bf in self._bound_items():` (loop over `self.fields` in declared order) | R | `List FieldModel` ↔ ordered form fields; field-order traversal preserved. `_bound_items` enumerates `self.fields` exactly as the pre-patch `self.fields.items()` did. |
| 2 | `cleaned := cleaned ++ [value]` (append in order) | `self.cleaned_data[name] = value` (per-field, success path) | R | dict-keyed-by-name ↔ list-in-field-order bijection (mapping.md). One entry produced per field. |
| 3 | `if f.disabled then … else f.data` | `value = bf.initial if field.disabled else bf.data` | I | branch on `field.disabled`; the disabled/editable split is identical. |
| 4 | editable branch `f.data` | `bf.data` = `self.form._widget_data_value(self.field.widget, self.html_name)` | A-reference | `bf.data` is supplied as the input `FieldModel.data` (the submitted value extracted for the field). No transform applied ⇒ identity; validated by G-CONF. |
| 5 | disabled branch `boundInitial f` | `bf.initial` (`BoundField.initial`, `boundfield.py:212-220`) | A-reference | modeled DEEPLY as `boundInitial`: temporal value drops its sub-second component iff `not supports_microseconds`; else unchanged. This IS the patch's behavioral fix (pre-patch used raw `get_initial_for_field`). Validated by G-AX (boundInitial == real `bf.initial`). NOT axiomatized — it is the changed op, modeled deeply. |
| 6 | `value` then result entry = `cleanedValue f` | `field.clean(value)` storing into `cleaned_data` | A-reference | in the modeled success case (`form.errors == {}`, the F2P scenario) `field.clean`/`to_python` is the identity on an already-typed value, so the cleaned entry equals the selected value. Validated by G-CONF (success-path replica). |

## Inputs vs callees
- `FieldModel.rawInitial` ← `get_initial_for_field(field, name)` AFTER callable
  evaluation (an INPUT, not a callee — its value is given). Modeling the
  *post-evaluation* value sidesteps the temporal/re-evaluation aspect of the fix,
  which is not separately expressible; the microsecond-stripping aspect is the
  modeled discriminator.
- `FieldModel.data` ← `bf.data` (an INPUT).

## No dead axioms
The `axioms` region is empty. `boundInitial` is a deep model of the changed op
(A-reference, G-AX-validated), not a consumed axiom. No `axiom _prop` is shipped;
the proof closes `result = fields.map cleanedValue` directly from the impl.

## Changed-op expressibility
Every changed op is modeled (R or A-reference). The only inexpressible aspect of
the gold patch is the *re-evaluation-count / side-effect timing* of a callable
initial (cached_property), which is a temporal property, not an input→output one;
it is documented (mapping.md) and is NOT a separate observable discriminator
beyond the microsecond-stripping one already modeled.
