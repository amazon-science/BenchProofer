# refinement.md — django__django-11433

The operation-by-operation correspondence between `model.py`'s implementation
(the `construct_writes` impl region + the deep `write_value` decision) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A-consumed** (proof uses an axiom's `Ensures`), **A-reference** (a deep model
validated == the real callee by G-AX), or **I** (identical concrete operation).
The claim: *any implementation that verifies against this frozen spec, refined
per the map below, is behaviourally equal to the gold patch on the tested
inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## The single change site — `construct_instance` (`django/forms/models.py:51`)

Gold hunk (the "leave defaults" guard gains a third conjunct):
```
-        if (f.has_default() and
-                form[f.name].field.widget.value_omitted_from_data(form.data, form.files, form.add_prefix(f.name))):
+        if (
+            f.has_default() and
+            form[f.name].field.widget.value_omitted_from_data(form.data, form.files, form.add_prefix(f.name)) and
+            cleaned_data.get(f.name) in form[f.name].field.empty_values
+        ):
             continue
```

A field that reaches this guard is left at its model default (the loop
`continue`s, nothing is written) iff the guard is true; otherwise its cleaned
value is written via `save_form_data`. The patch adds the conjunct
`cleaned_data.get(f.name) in form[f.name].field.empty_values`, so a field whose
cleaned value is NON-empty is no longer skipped — its value overwrites the
default.

| # | model.py impl op (`construct_writes`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| 1 | iterate `i` over the four index-aligned `List[bool]` | `for f in opts.fields:` | R | field in iteration order ↔ index `i`; `len` ↔ filtered field count (mapping.md §2). |
| 2 | `selected[i]` (gate the write) | the four earlier `continue` filters (lines 42–48: `not editable`/`AutoField`/`name not in cleaned_data`/`fields`/`exclude`) | R | the conjunction of the four candidacy filters is folded into one boolean carrier; a non-`selected` field is `continue`-skipped and writes nothing, `write_value(False,…) == False` (mapping.md §2). |
| 3 | `has_default[i]` | `f.has_default()` | R | unchanged primitive returning a `bool` → `bool` carrier (mapping.md §2). |
| 4 | `omitted[i]` | `form[f.name].field.widget.value_omitted_from_data(form.data, form.files, form.add_prefix(f.name))` | R | unchanged primitive returning a `bool` → `bool` carrier (mapping.md §2). |
| 5 | `value_empty[i]` | `cleaned_data.get(f.name) in form[f.name].field.empty_values` | R | the `in`-membership test against `EMPTY_VALUES = (None,'',[],(),{})` is a `bool` → `bool` carrier; this is the operand the patch ADDS to the guard (mapping.md §2, §3). |
| 6 | `write_value(...) = selected and not (has_default and omitted and value_empty)` ⇒ `result[i] = True/False` | the negated guard deciding `continue` vs `save_form_data(instance, cleaned_data[f.name])` | I | identical boolean control flow: written ⇔ reached guard ∧ guard false; the guard is `has_default ∧ omitted ∧ value_empty`. `write_value` is the spelled-out (deep) decision, NOT an axiom — there is no `@ContractOnly` to consume. |
| 7 | (no node) | FileField deferral re-ordering (lines 54–62) | I | identity on the modeled "whether written" observation: both branches run exactly one `save_form_data`; deferral only changes WHEN, not WHETHER (mapping.md §3). |

## A. The discriminating clause (G-DIFF)

The behavioural change lives entirely in step 6's added conjunct
`value_empty`. For a field that reached the guard with
`has_default ∧ omitted ∧ ¬value_empty`:

* **post-patch** (model.py): the guard is false (because `value_empty` is
  false), so the cleaned value is written — `write_value == True`, the
  postcondition `Result()[k] == write_value(...)` and the explicit
  "non-empty cleaned value is written" clause both demand `Result()[k]`.
* **pre-patch** (model_prepatch.py): the guard was `has_default ∧ omitted`
  only, so such a field is skipped — `result[k] == False`, which **violates**
  the frozen postcondition (and the loop invariant tying `result[k]` to
  `write_value(...)`). `model_prepatch.py` reproduces exactly this
  (`not (has_default[i] and omitted[i])`) and FAILS verification on that
  invariant — the spec sensing the change (G-DIFF).

This is precisely the F2P test
`test_default_not_populated_on_non_empty_value_in_cleaned_data`: with
`cleaned_data['mode'] = 'de'` (non-empty, `value_empty == False`) on a field
with a default whose value is omitted from `{}`, post-patch writes `'de'`
(pre-patch leaves the default `'di'`); and iterating each empty value
(`value_empty == True`) leaves the default `'di'` under both — captured by the
"empty cleaned value leaves the default" postcondition.

## B. No kind-3 (unexpressible-changed-op) steps

Every step above is R or I. The one operation that genuinely *changed* — the
boolean guard gaining the `value_empty` conjunct — is modeled **deeply** as the
spelled-out `write_value` decision and the verified loop, not hidden behind an
axiom. There is **no consumed axiom** (`@ContractOnly`) and **no A-reference**
deep model: the three pre-existing operands and the added membership test are
unchanged primitives whose `bool` outcomes are the inputs (R), and the decision
itself is the patch (I). `axiom_check.py` (G-AX) carries a soundness check of
the empty-sentinel membership semantics and the decision truth table for
uniformity, though no axiom is consumed.

## C. verify(model) ⇒ resolved

`construct_writes` verifies only if, for every field `i`, `result[i]` equals
`selected[i] and not (has_default[i] and omitted[i] and value_empty[i])` (the
exact post-patch guard, steps 2–6) — in particular `result[i]` is true for a
defaulted, omitted, non-empty-cleaned field and false for a defaulted, omitted,
empty-cleaned field. By R (fields ↔ indices, the four predicates ↔ their `bool`
outcomes, FileField deferral identity) this verified decision equals the gold
guard `not (has_default and omitted and value_empty)` governing
`save_form_data` at `django/forms/models.py:51`. Therefore an implementation
satisfying this spec, refined by the map above, is the gold patch up to type
refinement — and the gold patch resolves (G-RESOLVE). There are no trust
points beyond refinement fidelity (this document, G-EQ): no axiom is consumed.
