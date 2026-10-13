# refinement.md — django__django-14631

Operation-by-operation correspondence between `Solution.lean`'s impl region
(the `cleanFields` `do` block, plus the deep `initialFor`/`slotValue`/`cleanedSeq`
models) and `patch.diff` (the gold patch). Each step is tagged **R** (type
refinement), **A-reference** (deep model validated == real callee by G-AX),
**A-consumed** (proof uses an axiom's `ensures`), or **I** (identical concrete
op).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the A legs and this narrative are audited by **G-EQ**. Claim: any impl
verifying against this frozen spec, refined per the map below, is behaviourally
equal to the gold patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The modeled change — `BaseForm._clean_fields()` per-field value resolution

Gold hunk (`django/forms/forms.py:389`):
```
-        for name, field in self.fields.items():
-            if field.disabled:
-                value = self.get_initial_for_field(field, name)
-            else:
-                value = self._field_data_value(field, self.add_prefix(name))
+        for name, bf in self._bound_items():
+            field = bf.field
+            value = bf.initial if field.disabled else bf.data
```

| # | Solution.lean impl op (`cleanFields`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `fields : List FieldSlot` | iteration over `self._bound_items()` (the form's ordered fields + their `BoundField`s) | R | dict-insertion order ↔ list order; one `FieldSlot` per `(name, bf)` (mapping.md §1, §2). |
| A2 | `f.readOnly` guard in `slotValue` | `if field.disabled` (`forms.py:392` post) | R | identity on `Bool` (mapping.md §2). |
| A3 | read-only branch ⇒ `initialFor f` (coarse slot drops sub-count) | `value = bf.initial` (`forms.py:392` post) | A-reference + I | the changed value-resolution is modeled **deeply**: `initialFor` IS the `BoundField.initial` microsecond-normalization (`boundfield.py:213-220`, `#22502`). The fold/`if` ops are **I** (concrete, transliterated by G-CONF); the equality `initialFor == BoundField.initial` is the **A-reference** G-AX validates. mapping.md §3.1. |
| A4 | non-read-only branch ⇒ `f.given` | `value = bf.data` (`forms.py:393` post) | R | `bf.data` ↔ `FieldSlot.given` (mapping.md §1). |
| A5 | result list `= cleanedSeq fields`, built by the backward `while` fold | the sequence of `value`s written to `self.cleaned_data` by the loop (`forms.py:389-406`) | I | `field.clean(value)` on the resolved datetime is the identity (`DateTimeField.to_python` returns it unchanged; mapping.md §2, tag I); the loop's per-slot output is exactly `slotValue f`. |

Discriminating content of the change — a **read-only (disabled) + coarse**
slot's cleaned value must be the *normalized* stored value (`sub := 0`), i.e.
`bf.initial`, NOT the raw `get_initial_for_field` result. This lives in
`slotValue f = initialFor f` (model) ⇔ `value = bf.initial` (real). The
pre-patch took the raw stored value directly for disabled fields, keeping the
sub-count; `Solution_prepatch.lean` reproduces that (`if f.readOnly then
f.stored`) and **fails** `out = cleanedSeq fields` (G-DIFF) on exactly the coarse
read-only slot.

## B. Behaviour-preserving companion refactors (not separately modeled)

The gold patch also: adds `BaseForm._bound_items()` (yields `(name, self[name])`);
moves the per-field changed-detection logic into `BoundField._has_changed()` and
rewrites `BaseForm.changed_data` as the list comprehension
`[name for name, bf in self._bound_items() if bf._has_changed()]`; rewrites the
`_html_output` loop over `_bound_items()`; renames the `BoundField.data` access
from `self.form._field_data_value(self.field, ...)` to
`self.form._widget_data_value(self.field.widget, ...)` and deletes the now-unused
`_field_data_value`.

| # | construct | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1 | (no node) | `_bound_items()`, `_html_output` loop rewrite | I | pure re-expression of the same iteration; the values yielded and consumed are identical. Observationally the identity; PASS_TO_PASS (`test_changed_data`, `test_form_with_disabled_fields`, the `_html_output` suite) covers it. |
| B2 | (no node) | `changed_data` / `BoundField._has_changed` move; `data` property `_field_data_value`→`_widget_data_value` rename; `_field_data_value` deletion | I | `_field_data_value(field, h)` was *defined as* `_widget_data_value(field.widget, h)` (`forms.py:200-201` pre), so the rename is a literal inlining; `_has_changed` reproduces the old `changed_data` per-field logic verbatim (`forms.py:438-459` pre) on `self.data`/`self.initial`. No behaviour change; `test_datetime_changed_data_callable_with_microseconds` (P2P) pins it. |

These are **I** (identical-op) refactors with no observable delta, so they need
no separate `method` or failing prepatch: a prepatch must keep the spec
byte-identical (G-DIFF), and the only F2P-observable behaviour is site A's
disabled-field normalization, which the site-A prepatch already exercises.

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R, A-reference, or I. The one operation that genuinely *changed* —
resolving a disabled field's cleaned value through the `BoundField.initial`
normalization instead of the raw initial — is modeled **deeply** (the spelled-out
`initialFor`/`slotValue`, steps A3/A4, an A-reference + I), not hidden behind an
axiom about the function under change. There is **no consumed axiom**: the bundle
ships none (`axioms` region empty), so G-CONF carries the full R/I load and G-AX
validates the one A-reference (`initialFor == BoundField.initial`).

## D. verify(Solution) ⇒ resolved

`cleanFields` verifies only if its output equals `cleanedSeq fields`, i.e. each
read-only slot's value is `initialFor f` (the normalized stored value, A3) and
each other slot's value is `f.given` (A4). By R (field-order, `Bool`, `Stamp`
bijections of mapping.md §2) the verified loop equals the patched
`_clean_fields` value-resolution on the tested inputs; by G-AX the deep model
`initialFor` equals the real `BoundField.initial` (A-reference) and `field.clean`
is the identity on the resolved datetime (I); by G-CONF the R/I transliteration
agrees with `patch.diff`'s `cleaned_data` behaviour on ≥10⁵ inputs. The companion
refactors (§B) are observationally the identity. Therefore a model satisfying
this spec, refined by the map above, is the gold patch up to type refinement and
the one audited reference — and the gold patch resolves (G-RESOLVE). The single
trust point is the A-reference soundness of plan §1.1 (G-AX); there are no
consumed axioms.
