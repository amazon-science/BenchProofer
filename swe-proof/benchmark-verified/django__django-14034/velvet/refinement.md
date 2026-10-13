# refinement.md — django__django-14034

Operation-by-operation correspondence between `Solution.lean`'s impl region
(the `requiredFlags` `do` block, plus the deep `subRequired`/`requiredPlan`
models) and `patch.diff` (the gold patch). Each step is tagged **R** (type
refinement), **A-reference** (deep model validated == real callee by G-AX),
**A-consumed** (proof uses an axiom's `ensures`), or **I** (identical concrete
op).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the A legs and this narrative are audited by **G-EQ**. Claim: any impl
verifying against this frozen spec, refined per the map below, is behaviourally
equal to the gold patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The modeled change — per-sub-widget required marking in `build_widget_attrs`

Gold hunk (`django/forms/boundfield.py:233`):
```
         if widget.use_required_attribute(self.initial) and self.field.required and self.form.use_required_attribute:
-            attrs['required'] = True
+            # MultiValueField has require_all_fields: if False, fall back
+            # on subfields.
+            if (
+                hasattr(self.field, 'require_all_fields') and
+                not self.field.require_all_fields and
+                isinstance(self.field.widget, MultiWidget)
+            ):
+                for subfield, subwidget in zip(self.field.fields, widget.widgets):
+                    subwidget.attrs['required'] = subwidget.use_required_attribute(self.initial) and subfield.required
+            else:
+                attrs['required'] = True
```

| # | Solution.lean impl op (`requiredFlags`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `outerRequired : Bool` | the `if widget.use_required_attribute(self.initial) and self.field.required and self.form.use_required_attribute:` guard (`boundfield.py:235`) | R + A-reference | the composed outer gate ↔ a single `Bool` (mapping.md §2); its constituent callees are unchanged (A-reference, G-AX). The closed-gate case (`outerRequired = false`) ⇒ `requiredPlan` is all-`false`, matching the patch leaving no `required` set. |
| A2 | parameter `requireAll : Bool` | `not self.field.require_all_fields` together with the `hasattr(...,'require_all_fields')` + `isinstance(self.field.widget, MultiWidget)` guards (`boundfield.py:238-242`) | R | identity on `Bool` (mapping.md §2): `requireAll = field.require_all_fields` exactly when the field is a `MultiValueField` over a `MultiWidget`; the modeled per-sub-widget regime is the `not require_all_fields` branch, the uniform regime is `else` (and `require_all_fields=True`). |
| A3 | parameter `subs : List SubField`; `subs` is read-only (not `mut`) | `zip(self.field.fields, widget.widgets)` (`boundfield.py:243`) | R | sub-field index order ↔ list order; one `SubField` per `(subfield, subwidget)` pair (mapping.md §2). `subs` is never mutated (directive 5). |
| A4 | per-element `subRequired oR rA s` (the `requireAll`-vs-`marksRequired ∧ required` regime) | `subwidget.attrs['required'] = subwidget.use_required_attribute(self.initial) and subfield.required` in the `not require_all_fields` branch, vs `attrs['required'] = True` in the `else` branch | A-reference + I | the changed marking is modeled **deeply**: `subwidget.use_required_attribute(self.initial)` IS `s.marksRequired` (A-reference, G-AX), `subfield.required` IS `s.required` (R), the `&&`/`||` are concrete `Bool` ops (I). When `requireAll`/`else`, every sub-widget inherits the uniform `True` under the open gate — captured by the `requireAll` disjunct. mapping.md §3.1. |
| A5 | result list `= requiredPlan oR rA subs`, built by the backward `while` fold | the sequence of `subwidget.attrs['required']` values written across the `zip` loop, then rendered (`boundfield.py:243-244`) | I | a `True` assignment renders the boolean `required` attribute, `False`/unset omits it (G-AX render-faithfulness); the loop's per-sub-widget output is exactly `subRequired oR rA s`. |

Discriminating content of the change — in a **required** MultiValueField with
**`require_all_fields = False`** over a `MultiWidget`, a sub-widget gets the
required marker only if **its own** sub-field is required (and the sub-widget
opts in); a *non-required* sub-field's widget must **not** be marked. This lives
in `subRequired oR rA s = oR && (rA || (s.marksRequired && s.required))` (model)
⇔ the per-sub-field `subwidget.use_required_attribute(...) and subfield.required`
assignment (real). The pre-patch marked **every** sub-widget uniformly under the
open gate; `Solution_prepatch.lean` reproduces that (`v := outerRequired`) and
**fails** `out = requiredPlan ...` (G-DIFF) on exactly a non-required sub-field.

## B. The import addition (not separately modeled)

The gold patch also adds `MultiWidget` to the `from django.forms.widgets import`
line (`boundfield.py:5`). This is a pure name import required by the new
`isinstance(self.field.widget, MultiWidget)` guard; it has no observable
behaviour of its own and needs no separate `method` or prepatch.

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R, A-reference, or I. The one operation that genuinely *changed* —
deciding each sub-widget's required marker per-sub-field instead of uniformly —
is modeled **deeply** (the spelled-out `subRequired`/`requiredPlan`, steps
A4/A5, an A-reference + I), not hidden behind an axiom about the function under
change. There is **no consumed axiom**: the bundle ships none (`axioms` region
empty), so G-CONF carries the full R/I load and G-AX validates the A-references
(`use_required_attribute` opt-in, the composed outer gate, boolean→markup
rendering).

## D. verify(Solution) ⇒ resolved

`requiredFlags` verifies only if its output equals `requiredPlan oR rA subs`,
i.e. each sub-widget's marker is `subRequired oR rA s` (A4) — under the open
outer gate and `not requireAll`, the marker is `marksRequired ∧ required` per
sub-field (the F2P discriminator), and the uniform/closed regimes are the
`requireAll` and `oR = false` cases. By R (sub-field order, `Bool` bijections of
mapping.md §2) the verified loop equals the patched `build_widget_attrs`
sub-widget marking on the tested inputs; by G-AX the deep model's boolean inputs
equal the real callees (A-reference) and a `True` assignment renders the
`required` attribute (I); by G-CONF the R/I transliteration agrees with
`patch.diff`'s rendered per-sub-widget `required` on ≥10⁵ inputs. The import
addition (§B) is observationally inert. Therefore a model satisfying this spec,
refined by the map above, is the gold patch up to type refinement and the
audited references — and the gold patch resolves (G-RESOLVE). The single trust
point is the A-reference soundness of plan §1.1 (G-AX); there are no consumed
axioms.
