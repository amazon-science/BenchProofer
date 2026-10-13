# refinement.md — django__django-14034

Operation correspondence between `implementation_requiredAttrs` (Solution.lean)
and the gold `patch.diff`. Tags: **R** (type refinement), **A-consumed** (proof
uses an axiom's property), **A-reference** (deep model validated == real callee by
G-AX), **I** (identical concrete op).

## Modeled function: `build_widget_attrs`

The post-patch Python body, with the touched block:

```python
attrs = dict(attrs)
if widget.use_required_attribute(self.initial) and self.field.required and self.form.use_required_attribute:
    if (hasattr(self.field, 'require_all_fields') and
            not self.field.require_all_fields and
            isinstance(self.field.widget, MultiWidget)):
        for subfield, subwidget in zip(self.field.fields, widget.widgets):
            subwidget.attrs['required'] = subwidget.use_required_attribute(self.initial) and subfield.required
    else:
        attrs['required'] = True
if self.field.disabled:
    attrs['disabled'] = True
return attrs
```

The modeled behavior is the *placement of the HTML required marker* (and the
disabled marker). The `attrs = dict(attrs)` copy and the pass-through of all other
attribute entries are identity on content and outside the modeled decision; they
are not represented in the impl (which produces exactly the marker decisions).

| # | `implementation_requiredAttrs` op | `patch.diff` counterpart | tag | justification |
|---|---|---|---|---|
| 1 | inputs `widgetUseReq formUseReq : Bool`, `field : FieldInfo` | `widget.use_required_attribute(self.initial)`, `self.form.use_required_attribute`, and the bound field's attribute-relevant fields | R | Python bools/objects ↔ Lean `Bool`/`FieldInfo` (mapping.md). `use_required_attribute` is an UNCHANGED callee whose result is consumed as an input boolean (per mapping.md), not recomputed. |
| 2 | `if widgetUseReq && field.required && formUseReq then …` | `if widget.use_required_attribute(self.initial) and self.field.required and self.form.use_required_attribute:` | I | the same three-way conjunction guard. |
| 3 | `if field.hasRequireAllFields && (!field.requireAllFields) && field.isMultiWidget then …` | `if (hasattr(self.field, 'require_all_fields') and not self.field.require_all_fields and isinstance(self.field.widget, MultiWidget)):` | R / I | `hasattr(...)`↔`hasRequireAllFields`, `not require_all_fields`↔`!requireAllFields`, `isinstance(widget, MultiWidget)`↔`isMultiWidget` (mapping.md). Same boolean structure. |
| 4 | `for (su, sr) in field.subPairs do subwidgetRequired := subwidgetRequired ++ [su && sr]` | `for subfield, subwidget in zip(self.field.fields, widget.widgets): subwidget.attrs['required'] = subwidget.use_required_attribute(self.initial) and subfield.required` | R / I | The Python `zip(fields, widgets)` pairing is modeled as a single ordered list `subPairs : List (Bool × Bool)`, each entry `(subUseReq, subRequired)`. Pre-zipping fixes the field↔widget alignment by construction (no implicit invariant left to a wrong abstraction); G-CONF materializes `subPairs` back into the two real sequences the method zips, in the same order. Each written flag is `su && sr` ↔ `subwidget.use_required_attribute(...) and subfield.required`. `subwidget.use_required_attribute` is the same unchanged callee, its result an input boolean. |
| 5 | `else parentRequired := true` | `else: attrs['required'] = True` | I | parent gets the required marker in the ordinary case. |
| 6 | `if field.disabled then parentDisabled := true` | `if self.field.disabled: attrs['disabled'] = True` | I | disabled marker placement (unchanged by the patch, but a framed output component — directive 5). |

## Frame / unchanged-component discipline (directive 5)

The per-subwidget pairing is itself fixed by the type model: `subPairs` is a
single ordered list of `(subUseReq, subRequired)` pairs, so the field↔widget
alignment that Python's `zip(self.field.fields, widget.widgets)` establishes is
not an implicit side condition but is baked into the input carrier — there is no
mis-pairing a wrong impl could exploit.

`problem_spec_requiredAttrs` pins ALL four observable components:
`parentDisabled` (= `field.disabled`, the unchanged disabled decision),
`parentRequired`, `perSubBranch`, and `subwidgetRequired`. The `parentRequired`
and `subwidgetRequired` clauses are mutually exclusive on the `subBranch`
condition, so no wrong impl can both descend into subwidgets AND set the parent
marker, nor leave the placement unconstrained. The empty `subwidgetRequired` in
the non-sub-branch case is pinned explicitly (`= []`).

## No consumed axiom / no opaque callee

`use_required_attribute` is the only unchanged callee touched; its result is taken
as an input boolean (it is not the operation the patch changes, and is not
recomputed in the impl). So the `axioms` region is empty, there is no opaque
callee, and the proof discharges by case analysis on the booleans + induction on
the subfield list (the `for`/`zip`/`map` correspondence). `axiom_check.py` is a
skip stub; G-CONF (R/I) bridges the input by driving the real method.

## conf_skip

The impl region has R/I content (the guard, the nested branch, the per-subwidget
`for` loop, the parent assignments), so `conf_skip = false`: `conformance_check.py`
runs a full ≥10⁵-input differential against the real patched method.

## patch.diff == gold

`patch.diff` is the gold patch verbatim.
