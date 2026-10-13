# mapping.md — django__django-11433

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 21b1d239125f1228e579b1ce8d94d4d5feadd2a6`, states the type
abstraction (the bijection G-CONF and G-AX use to bridge Lean↔Python), and
gives the provenance of every modeled operation.

Repo file under change: `django/forms/models.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `assignCleanedValues (fields : List Field)` | `construct_instance(form, instance, fields=None, exclude=None)` — `django/forms/models.py:31` (loop body `:40-59`) | the modeled changed function (decide, per model field, whether the loop hands the form's cleaned value to that field's `save_form_data` write step, vs skipping the field so the model fallback stands) |
| `Field.eligible` | the four gating `continue` conditions at `models.py:42-47` evaluated together: `f.editable and not isinstance(f, models.AutoField) and f.name in cleaned_data and (fields is None or f.name in fields) and not (exclude and f.name in exclude)` | whether this field is one the form may assign at all (unchanged by the patch) |
| `Field.modelHasDefault` | `f.has_default()` — `models.py:51`, returns `self.default is not NOT_PROVIDED` (`db/models/fields/__init__.py:788`) | the model declares a fallback value for this field |
| `Field.noIncomingValue` | `form[f.name].field.widget.value_omitted_from_data(form.data, form.files, form.add_prefix(f.name))` — `models.py:52` (e.g. `Widget.value_omitted_from_data` = `name not in data`, `forms/widgets.py:260`) | the submitted payload carried no incoming value for this field |
| `Field.cleanedValueEmpty` | `cleaned_data.get(f.name) in form[f.name].field.empty_values` — `models.py:53` post-patch (the **added** conjunct); `empty_values = list(validators.EMPTY_VALUES)` = `[None, '', [], (), {}]` (`forms/fields.py:55`, `core/validators.py:13`) | the cleaned value for this field is itself an empty value |
| `applies (f : Field)` | the post-patch decision: hand off iff eligible and NOT (`has_default()` and `value_omitted_from_data(...)` and cleaned value empty); i.e. `models.py:51-54` negated and conjoined with eligibility | per-field "is the cleaned value handed to `save_form_data`" predicate (I — identical concrete op) |
| `applyPlan (fs : List Field)` | the per-field decisions produced by the `for f in opts.fields` loop (`models.py:40`); each iteration either skips (`continue`) or calls `f.save_form_data(instance, cleaned_data[f.name])` | deep, identical model of the per-field decision sequence (R + I) |

The loop structure (`for f in opts.fields`), the file-field deferral
(`file_field_list`, `models.py:55-62`), and `save_form_data` itself are
**unchanged** by the patch; only the per-field skip guard at `models.py:51-54`
changed (one conjunct added). The traversal is therefore a type refinement (R),
not an axiom. The file-field deferral only reorders *when* eligible hand-offs
happen, not *which* fields are handed off, so the observable — the per-field
"is this field's cleaned value handed to its `save_form_data` write step"
decision — is order-independent and flattens losslessly to `List Bool`.

**Boundary note (write step is downstream of the modeled observable).** The
modeled decision is the *hand-off*: `save_form_data(instance,
cleaned_data[f.name])` is reached for the field, vs the loop `continue`s past
it and the model fallback stands. What the write step then does with the handed
value is each field class's own **unchanged** behavior and is outside the
boundary — e.g. a field class may treat certain handed tokens as "no change"
and leave the attribute untouched even though the hand-off happened. The patch
touches only the skip guard, never any `save_form_data`, so drawing the
boundary at the hand-off captures exactly the changed behavior.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) uses to translate values between the Lean
value domain and the Python repo types. A wrong entry surfaces as spurious
G-CONF disagreements (the falsifiability the plan §4 trust statement refers to).

| repo reality | Lean carrier | bijection |
|---|---|---|
| the sequence of model fields `opts.fields` that `construct_instance` iterates | `List Field` | each model field `f` the loop visits ↔ one `Field`; visit order is preserved (one `List Bool` entry per visited field) but is observably irrelevant — each field's decision is independent |
| the four gating conditions (`f.editable`, `not AutoField`, `f.name in cleaned_data`, the `fields`/`exclude` selection) | `Field.eligible : Bool` | all gates pass (field is assignable) ↔ `eligible = true`; any gate trips (`continue`) ↔ `eligible = false` |
| `f.has_default()` | `Field.modelHasDefault : Bool` | `True` ↔ `modelHasDefault = true`; `False` ↔ `false` |
| `form[f.name].field.widget.value_omitted_from_data(form.data, form.files, form.add_prefix(f.name))` | `Field.noIncomingValue : Bool` | `True` (omitted) ↔ `noIncomingValue = true`; `False` ↔ `false` |
| `cleaned_data.get(f.name) in form[f.name].field.empty_values` | `Field.cleanedValueEmpty : Bool` | cleaned value ∈ `[None, '', [], (), {}]` ↔ `cleanedValueEmpty = true`; otherwise ↔ `false` |
| `f.save_form_data(instance, cleaned_data[f.name])` is reached for `f` (vs the loop `continue`s past it) | the `Bool` entry `applies f` | the field's cleaned value is handed to its write step ↔ `true`; the field is skipped (model fallback stands) ↔ `false` |

`construct_instance` returns the mutated `instance`; the observable the F2P test
reads is the per-field outcome "did the loop hand the form's cleaned value to
this field's write step, or skip it so the model's fallback stands". For the
field classes the F2P test exercises the hand-off is directly visible as
`getattr(instance, f.name)` moving off the fallback; for field classes whose
unchanged `save_form_data` interprets some handed tokens as "no change", the
hand-off is still the modeled observable (the write step's token handling is
unchanged, downstream behavior — §1 boundary note). Because each field's
decision is independent of the others and of order, the loop flattens
losslessly to the `List Field → List Bool` carrier.

## 3. Callee provenance

**No axioms; no deep-model references (A-reference); no consumed axioms
(A-consumed).** The single operation the patch changes — the per-field skip
guard — is modeled **identically** (`applies`), and the surrounding per-field
loop is a structural refinement (`applyPlan` over the flattened field list).
Every step is therefore R or I (see refinement.md), all mechanically checked by
G-CONF against the real patched `construct_instance`. There is no unchanged
opaque callee whose contract the proof must assume, so `axiom_check.py` (G-AX)
has no axiom to validate and exits 0 after confirming the bundle declares none
and that the builtins the refinement leans on (`has_default`,
`value_omitted_from_data`, the `in empty_values` membership) carry the fixed
semantics the §2 bijection claims.

The booleans the guard reads are computed by real Django callees with fixed
semantics, refined to the `Field` fields per §2; G-CONF exercises all of them on
fuzzed real form/model objects (with/without defaults, with/without submitted
data, empty/non-empty cleaned values) so the §2 bijection is falsifiable, not
merely asserted.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`11433`** so the
consumer-side verdict (§11.3) is reproducible. The R/I shadow it builds
transliterates `applies`/`applyPlan` (R/I-tagged ops) to Python and compares the
resulting per-field decision against the real patched `construct_instance`'s
observable (whether each field's cleaned value lands on the constructed
instance) over fuzzed real Django forms/models. There are no A-tagged callees to
leave as real-callee calls (§3).
