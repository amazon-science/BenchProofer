# mapping.md — django__django-14034

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = db1fc5cd3c5d36cdb5d0fe4404efd6623dd3e8fb`, states the type
abstraction (the bijection G-CONF and G-AX use to bridge Lean↔Python), and
gives the provenance of each deep-model reference.

Repo file under change: `django/forms/boundfield.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `requiredFlags (outerRequired) (requireAll) (subs)` | the per-sub-widget `required`-attribute assignment loop added to `BoundField.build_widget_attrs` (`django/forms/boundfield.py:232`) | the modeled changed function: which sub-widgets of a multi-part field carry the required marker |
| `SubField` | one sub-field of a `MultiValueField` together with its sub-widget (`self.field.fields[i]` / `widget.widgets[i]`, `django/forms/fields.py:1001`, `django/forms/widgets.py:813`) | a single sub-field slot the loop walks |
| `SubField.required` | `subfield.required` (`django/forms/fields.py` `Field.required`) | whether the sub-field is itself a required field |
| `SubField.marksRequired` *(A-reference)* | `subwidget.use_required_attribute(self.initial)` (`django/forms/widgets.py:280`: `return not self.is_hidden`) | whether the sub-widget opts into the required marker on its own |
| `outerRequired` | `widget.use_required_attribute(self.initial) and self.field.required and self.form.use_required_attribute` (`django/forms/boundfield.py:235`) | the overall gate guarding any required marking |
| `requireAll` | `self.field.require_all_fields` (`django/forms/fields.py:989`), with the `hasattr(...,'require_all_fields')` and `isinstance(self.field.widget, MultiWidget)` guards | whether the field requires every sub-field jointly |
| `subRequired (oR) (rA) (s)` | the value assigned to `subwidget.attrs['required']` (`boundfield.py:244` post): `subwidget.use_required_attribute(self.initial) and subfield.required`, under the outer gate, vs the uniform `attrs['required'] = True` fallback | the required marker decided for one sub-widget |
| `requiredPlan (oR) (rA) (subs)` | the sequence of `attrs['required']` values written across `zip(self.field.fields, widget.widgets)` (`boundfield.py:243-244`) | the per-sub-widget required markers across the sub-field list |

The pre-patch repo path the change replaces (refinement audit only, not in the
consumer spec view): for a required field whose outer gate is open,
`build_widget_attrs` set `attrs['required'] = True` **uniformly**
(`boundfield.py:236` pre), so the multi-part widget propagated the marker to
every sub-widget regardless of the individual sub-field's `required` flag. The
post-patch code, when the field exposes `require_all_fields = False` over a
`MultiWidget`, instead assigns each sub-widget's marker from its own
`use_required_attribute(...) and subfield.required`.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) and G-AX use to translate values between the
Lean value domain and the Python repo types. A wrong entry surfaces as spurious
G-CONF disagreements (the falsifiability the plan §4 trust statement refers to).

| repo reality | Lean carrier | bijection |
|---|---|---|
| the ordered `zip(self.field.fields, widget.widgets)` pairs | `List SubField` | sub-field index order ↔ list order; `len(fields)` ↔ `subs.length`; one `SubField` per `(subfield, subwidget)` pair |
| `subfield.required` (bool) | `SubField.required` | identity on `Bool` |
| `subwidget.use_required_attribute(self.initial)` (bool) | `SubField.marksRequired` | identity on `Bool` (A-reference, §3.1) |
| the composed outer gate (bool) | `outerRequired` | identity on `Bool`; the conjunction `widget.use_required_attribute(initial) and field.required and form.use_required_attribute` (A-reference, §3.1) |
| `self.field.require_all_fields` (bool) | `requireAll` | identity on `Bool` |
| `subwidget.attrs['required']` assigned then rendered | element of `requiredPlan ...` (`Bool`) | a `True` assignment renders the boolean `required` attribute; `False`/unset omits it (tag I, validated by G-AX render-faithfulness) |

`Bool` is the right carrier throughout: the entire observable change is which
sub-widgets emit the `required` markup attribute, a per-element boolean.

## 3. Deep-model reference (kind A-reference — checked by G-AX / axiom_check.py)

### 3.1 `subRequired` inputs ↔ unchanged callees (A-reference)
**Callees (unchanged):**
- `Widget.use_required_attribute(initial)` (`django/forms/widgets.py:280`,
  `return not self.is_hidden`) — the sub-widget's own opt-in into the required
  marker. A visible text-style input opts in (`True`); a hidden input does not
  (`False`). The composed **outer gate** also calls the *outer* widget's
  `use_required_attribute`, `self.field.required`, and
  `self.form.use_required_attribute`.
- `MultiValueField.require_all_fields` (`django/forms/fields.py:989`) and the
  `hasattr`/`isinstance(MultiWidget)` guards — these decide which branch the
  patched code takes; modeled directly as the `requireAll` flag (the guard's
  outcome) and the field-list shape.

The changed decision itself — `subwidget.use_required_attribute(self.initial)
and subfield.required` under the outer gate — is modeled **deeply** by
`subRequired`/`requiredPlan` in the `pure` region; there is **no consumed
axiom**.

**Soundness check (G-AX, `axiom_check.py`):** constructs real Django forms with a
`MultiValueField` over a `MultiWidget`, fuzzing the per-sub-field `required`
flags, the sub-widget kinds (text = opts in; hidden = does not), the outer
`required`, and `require_all_fields`, and asserts (a) the real composed outer
gate is well-defined, (b) each `subwidget.use_required_attribute(initial)` equals
the model's `marksRequired` input (text⇒True, hidden⇒False), and (c) the
boolean→markup leg is faithful: an `attrs['required']` assigned `True` renders
the `required` attribute, `False`/unset omits it. Exit 0 iff sound.

Note (G-AX-relevant subtlety): `MultiValueField.__init__` FORCES each
sub-field's `required` to `False` when `require_all_fields=True`
(`django/forms/fields.py:996-1000`). The model is robust to this: under
`requireAll`, the `requireAll` disjunct in `subRequired` short-circuits the
per-sub-field term, so the forced flag is never observed. G-CONF reads
`subfield.required` from the real object, so its R-leg honours this exactly.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`14034`** so the
consumer-side verdict (§11.3) is reproducible. The R/I shadow it builds
transliterates `subRequired`/`requiredPlan` (the R/I-tagged decision) to Python,
reads the model's boolean inputs from the REAL field/widget objects (the
A-reference callees), and compares against the patched form's actually-rendered
per-sub-widget `required` attribute (oracle = patch.diff at base_commit). There
are no A-tagged callees left as opaque models (the bundle ships no consumed
axioms), so G-CONF carries the full R/I load.
