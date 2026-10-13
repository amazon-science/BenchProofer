# refinement.md — django__django-14631

The operation-by-operation correspondence between `model.py`'s implementation
(the `clean_bound_initial_field` impl region, plus the deep `bound_initial` /
`normalise` models) and `patch.diff` (the gold patch). Each step is tagged
**R** (type refinement), **A-consumed** (the proof uses a `@ContractOnly`
axiom's `Ensures`), **A-reference** (a deep model validated == the real callee
by axiom_check.py / G-AX, NOT consumed), or **I** (identical concrete
operation). The claim: *any implementation that verifies against this frozen
spec, refined per the map below, is behaviourally equal to the gold patch on the
tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The modelled behavioural change — `_clean_fields()` disabled-field value

Gold hunk (`django/forms/forms.py`, `_clean_fields`):
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
The behavioural change F2P observes is the disabled-field source:
`self.get_initial_for_field(field, name)` (a fresh, un-normalised re-evaluation)
→ `bf.initial` (the single cached, microsecond-normalised evaluation).

| # | model.py impl op (`clean_bound_initial_field`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A0 | `Requires(MustTerminate(2))` | the disabled-field branch of `_clean_fields` is straight-line bounded code (`value = bf.initial`, one cached-property read): it always terminates | R | total-correctness obligation. A same-spec impl that diverges (hangs) before returning the correct value satisfies the value postconditions only vacuously, and its faithful patch (`while True: pass` inside the disabled branch) hangs `form.is_valid()` and the F2P test — verified but NOT resolved (the partial-correctness gap the G-EQ audit demonstrated with atk_4/atk_6/atk_7). `MustTerminate(2)` pins termination; the gold impl is loop-free and discharges it trivially. |
| A0b | the precondition grants **NO permission** to `fs.fresh_eval` (no `Acc`) | `_clean_fields` has no right to re-evaluate the initial source: the gold disabled branch performs NO `get_initial_for_field` call of its own — it only reads the cached `bf.initial` | R (permission-as-effect) | evaluating the initial source is STATEFUL (the F2P `FakeTime().now` advances one second per call), so ANY extra evaluation — even a dead one whose value is discarded — shifts which value `bf.initial` caches (the cache captures the next evaluation when the extra call precedes the first `bf.initial` read). The G-EQ audit's atk_8 (`value = fs.fresh_eval; value = bound_initial(fs)`) satisfied the value postconditions yet its faithful patch (a dead `value = self.get_initial_for_field(field, name)` line before `value = bf.initial`) fails the hidden tests: the dead call consumes `...:46`, so `bf.initial` caches `...:47` and `cleaned != datetime(...,46)`. Removing all permission to `fresh_eval` makes even a dead READ of it fail verification (INSUFFICIENT PERMISSION), closing exactly this gap. The gold impl never touches `fresh_eval` and is unaffected. |
| A1 | parameter `fs: FieldState` (fields `first_eval`, `fresh_eval`: `int`) | the field whose disabled value is being cleaned | R | the touched quantities are the value of the first evaluation of the initial source (`first_eval`) and a fresh re-evaluation (`fresh_eval`), each a date/time encoded as `whole_seconds*1e6 + sub_seconds` (mapping.md §2). |
| A2 | `value = bound_initial(fs)` | `value = bf.initial` (the disabled branch) | R + A-reference | `bf.initial` is `BoundField.initial`, a `@cached_property` that evaluates the source once and strips sub-second precision; modelled **deeply** as `bound_initial(fs) == normalise(fs.first_eval)` (no consumed axiom). G-AX validates `BoundField.initial == normalise(first_eval)` against the real callee (mapping.md §3.1, R1). |
| A3 | `cleaned = value` (identity) | `value = field.clean(value)` (inside the `try`, the non-FileField branch — `forms.py:400` post-patch) | I (identity on the tested input) | `Field.clean` on a disabled `DateTimeField` is the identity on a `datetime` value (`to_python` returns it unchanged with `USE_TZ=False`; validators do not mutate it). mapping.md §3.2; G-AX confirms `cleaned == bf.initial` end-to-end (R2). |
| A4 | `return cleaned` → cleaned value | `self.cleaned_data[name] = value` | I | the cleaned value the form records for the field. |

The discriminating content of the change — the disabled value must be the
field's **bound initial** (single, cached, microsecond-stripped evaluation),
NOT a fresh un-normalised re-evaluation — lives in the postcondition
`Result() == bound_initial(fs) == normalise(fs.first_eval)`. The pre-patch
`get_initial_for_field` re-evaluation is reproduced in `model_prepatch.py`
(`value = fs.fresh_eval`) and **fails** that postcondition, which is exactly the
spec sensing the change (G-DIFF). G-AX (R3) confirms the real pre-patch path
disagrees with `bf.initial` on the F2P input (fresh second, microseconds kept),
so the differential witness is non-vacuous.

## B. The non-behavioural refactor hunks (no separate modelling needed)

The gold patch also makes pure refactors with NO F2P-observable behaviour
change; they are not modelled (they cannot break the verify⟹resolve link):

| gold hunk | tag | justification |
|---|---|---|
| `BoundField.data`: `self.form._field_data_value(self.field, self.html_name)` → `self.form._widget_data_value(self.field.widget, self.html_name)` | I (inline) | `_field_data_value(field, n)` was *defined* as `self._widget_data_value(field.widget, n)` (`forms.py:200-201`); the change inlines that one-line helper. Same call, same result. |
| add `_bound_items()`; `_html_output`/`_clean_fields`/`changed_data` iterate `self._bound_items()` instead of `self.fields.items()` + `self[name]` | I | `_bound_items` yields `(name, self[name])` for `name in self.fields` — the identical `(name, bf)` pairs the old code built field-by-field. |
| add `BoundField._has_changed()`; `changed_data` → `[name for name, bf in self._bound_items() if bf._has_changed()]` | I | `_has_changed` is the verbatim move of the per-field changed-data logic (`show_hidden_initial` branch, `to_python`/`ValidationError` handling, `field.has_changed(initial, data)`) from `changed_data` into the BoundField; the computed predicate is identical (the `test_datetime_changed_data_callable_with_microseconds` and `#23674` invalid-initial tests are in PASS_TO_PASS and keep passing). |
| remove `_field_data_value`; `__iter__` docstring added | I | dead-helper removal / doc only. |

These are observationally inert, so there is no separate `model_prepatch_<k>`
for them; the single F2P-observable behaviour (the `_clean_fields` disabled
value source) is covered by `model_prepatch.py`.

## C. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-reference, or I. The one operation that genuinely
*changed* — the disabled-field value source becoming the field's bound initial —
is modelled **deeply** (`bound_initial`/`normalise`, an **A-reference** validated
by G-AX), not hidden behind an axiom about the function under change. There is
**no consumed `@ContractOnly` axiom** in this bundle.

## D. verify(model) ⇒ resolved

`clean_bound_initial_field` verifies only if it TERMINATES (the
`MustTerminate(2)` precondition — no vacuous satisfaction via divergence, A0),
NEVER re-evaluates the initial source (no permission to `fs.fresh_eval` — no
verified impl can even read it, so no faithful patch can carry an extra
`get_initial_for_field` call that would advance the stateful source and shift
the cached bound initial, A0b), and its result equals
`bound_initial(fs) == normalise(fs.first_eval)` — the single, cached,
sub-second-normalised evaluation of the initial source (A2/A3). By R (the
date/time integer encoding; `BoundField.initial`'s cache+strip ↔
`normalise(first_eval)`) and by G-AX (the deep model `bound_initial` equals the
real `BoundField.initial`, and the disabled field's cleaned value equals
`bf.initial`, on the F2P scenario), the verified computation equals the gold
patch's `value = bf.initial` on the tested input. The pre-patch fresh
re-evaluation fails the postcondition (G-DIFF) and really disagrees with
`bf.initial` (G-AX R3). Therefore a model satisfying this spec, refined by the
map above, is the gold patch up to type refinement and the audited deep-model
reference — and the gold patch resolves (G-RESOLVE). The trust points are
exactly the two of PLAN §1.1: deep-model/axiom soundness (G-AX, here the
A-reference) and refinement fidelity (this document, G-EQ).
