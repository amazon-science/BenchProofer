# refinement.md — django__django-15973

The operation-by-operation correspondence between `model.py`'s implementation
(the `through_dependency` impl region and the deep `ref_app`/`ref_name` model)
and `patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A** (axiomatized callee — split into **A-consumed**, proof uses the axiom's
`Ensures`, and **A-reference**, a deep model validated == the real callee by
axiom_check.py / G-AX), or **I** (identical concrete operation). The claim:
*any implementation that verifies against this frozen spec, refined per the map
below, is behaviourally equal to the gold patch on the tested inputs, so it
resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The intermediary-dependency hunk — `_get_dependencies_for_foreign_key` (`django/db/migrations/autodetector.py:1422-1429`)

Gold hunk (inside `if getattr(field.remote_field, "through", None):`):
```
  through_app_label, through_object_name = resolve_relation(
-     remote_field_model,
+     field.remote_field.through,
      app_label,
      model_name,
  )
  dependencies.append((through_app_label, through_object_name, None, True))
```

The dependency list always carries a primary dependency (`autodetector.py:1422`)
derived from `remote_field_model`; when the field has a `through`, a SECOND
dependency is appended. The bug fed `remote_field_model` (the **primary**
reference) to the resolver for that second dependency; the fix feeds
`field.remote_field.through` (the **intermediary** reference). The model
projects the function to exactly the intermediary dependency:
`through_dependency(primary_ref, through_ref)` returns its
`(app_label, object_name)`.

| # | model.py impl op (`through_dependency`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `primary_ref: List[int]` | `remote_field_model` (the field's primary related reference) | R | `str` reference ↔ `List[int]` code points (mapping.md §2). Read-only: required AND ensured at `Acc(list_pred(primary_ref), 1/2)` (directive 5). |
| A2 | parameter `through_ref: List[int]` | `field.remote_field.through` (the intermediary reference) | R | same `str` ↔ `List[int]` refinement; read-only at `1/2` permission. |
| A3 | the result is `(ref_app(ToSeq(through_ref)), ref_name(ToSeq(through_ref)))`, computed by the verified dot-find + prefix + lower-cased-suffix loops over **`through_ref`** | `resolve_relation(field.remote_field.through, app_label, model_name)` | A-reference | the resolver is an UNCHANGED callee modeled **deeply**: `ref_app`/`ref_name` (the dot-split + ASCII lower-case fold in the `pure` region) and the loops in `through_dependency` ARE the resolver's string-reference behaviour (mapping.md §3.1). There is no consumed `resolve_relation` axiom — the proof never depends on one. Instead the deep model is validated **== the real callee** out-of-band by G-AX (axiom_check.py runs `resolve_relation` on boundary + fuzz and asserts `ref_app/ref_name == resolve_relation`). |
| A4 | the resolver argument is `through_ref` (postconditions reference only `through_ref`; `primary_ref` is unused by the computation) | `field.remote_field.through` is passed (NOT `remote_field_model`) | I | identical control/data choice: the changed line selects which reference reaches the resolver, and the model reaches the resolver (deeply) with `through_ref`. This is the single behavioural delta — see the prepatch note. |
| A5 | `res = (app, name)` returned as a `Tuple[List[int], List[int]]` | `through_app_label, through_object_name = ...; dependencies.append((through_app_label, through_object_name, None, True))` | R | the 2-tuple ↔ `(app_label, object_name)` (mapping.md §2). The constant tuple tail `(None, True)` and the `dependencies.append` are unobserved structure around the resolved pair the F2P test's dependency assertion checks. |

The discriminating content of the change — the intermediary dependency resolves
**`field.remote_field.through`**, not `remote_field_model` — lives in the
postconditions
`ToSeq(Result()[0]) == ref_app(ToSeq(through_ref))` and
`ToSeq(Result()[1]) == ref_name(ToSeq(through_ref))`
(the resolver is applied to `through_ref`). The pre-patch resolved
`remote_field_model` instead; `model_prepatch.py` reproduces that (it builds the
result from `primary_ref`) and **fails** the postcondition
`ToSeq(Result()[0]) == ref_app(ToSeq(through_ref))` whenever the two references
name objects in different apps — which is exactly the spec sensing the change
(G-DIFF). This is the separate-apps scenario the F2P test
`test_create_with_through_model_separate_apps` exercises (the `through` model
`contract.Contract` lives in a different app from the relation target
`testapp.Publisher`).

## B. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-reference, or I. The one operation that genuinely
changed — *which reference is resolved* for the intermediary dependency — is an
**I** (a concrete data-flow selection), and the resolver it feeds is modeled
**deeply** (the spelled-out dot-split + lower-case fold consumed in
`through_dependency`, step A3, an **A-reference**), not hidden behind an axiom
about a function under change. There is **no consumed `resolve_relation`
axiom**; the `axioms` region is empty (mapping.md §4).

## C. verify(model) ⇒ resolved

`through_dependency` verifies only if its result equals the resolver applied to
the **intermediary** reference `through_ref` (A3, A4). By R (`str` ↔ `List[int]`,
the 2-tuple ↔ `(app_label, object_name)`) the verified result equals
`resolve_relation(field.remote_field.through, app_label, model_name)` on the
dotted `"app.Object"` references the autodetector resolves; by G-AX the deep
model `ref_app`/`ref_name` equals the real `resolve_relation` on that domain
(A-reference). Therefore a model satisfying this spec, refined by the map above,
appends the same intermediary dependency the gold patch does — pointing at the
through model's own app — and the gold patch resolves (G-RESOLVE). The single
trust point is the two of PLAN §1.1, here only refinement fidelity (this
document, G-EQ) plus the A-reference soundness (G-AX); no axiom is consumed.
