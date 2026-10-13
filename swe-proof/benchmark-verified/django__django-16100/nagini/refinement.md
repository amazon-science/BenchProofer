# refinement.md — django__django-16100

The operation-by-operation correspondence between `model.py`'s implementation
(the `apply_batch` impl region and the deep `committed_value`/`any_fails`
model) and `patch.diff` (the gold patch). Each step is tagged **R** (type
refinement), **A-consumed** (the proof uses an axiom's `Ensures`),
**A-reference** (a deep model is validated == the real callee by
axiom_check.py / G-AX, NOT consumed), or **I** (identical concrete operation).
The claim: *any implementation that verifies against this frozen spec, refined
per the map below, is behaviourally equal to the gold patch on the tested
inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The change site — `ModelAdmin.changelist_view` list-editable save loop (`django/contrib/admin/options.py:2012-2021`)

Gold hunk (semantic core):
```
-                for form in formset.forms:
-                    if form.has_changed():
-                        obj = self.save_form(request, form, change=True)
-                        self.save_model(request, obj, form, change=True)
-                        self.save_related(request, form, formsets=[], change=True)
-                        change_msg = self.construct_change_message(request, form, None)
-                        self.log_change(request, obj, change_msg)
-                        changecount += 1
+                with transaction.atomic(using=router.db_for_write(self.model)):
+                    for form in formset.forms:
+                        if form.has_changed():
+                            obj = self.save_form(request, form, change=True)
+                            ...
+                            self.log_change(request, obj, change_msg)
+                            changecount += 1
```
The change wraps the existing per-form save loop in a single atomic transaction.
The loop body is unchanged; the only edit is the grouping boundary that decides
what persists when a form's processing raises.

| # | model.py impl op (`apply_batch`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameters `original`, `newvals`, `fails: List[int]` | the batch of `formset.forms` against the persistent store: each row's stored value, the value its form would save, and whether its processing raises | R | rows ↔ list indices; stored/replacement values ↔ `int`; "form `i` raises" ↔ `fails[i]==1` (mapping.md §2). The F2P test injects the raise via `mock.patch(... log_change, side_effect=DatabaseError)`. |
| A2 | the first loop walks the forms in order and sets `failed` once an edit with `fails[i]==1` is reached (stopping there) | `for form in formset.forms: if form.has_changed(): save_form/save_model/save_related/construct_change_message/log_change` inside the `with` — a raise from any call aborts the block | A-reference | the per-form processing and its possible raise are modeled deeply: `any_fails(fails,0)` ⇔ "some form's processing raises inside the block". The body calls (`save_*`, `log_change`) are unchanged by the patch; their only observable effect on the tested property is whether they raise. |
| A3 | the second loop commits, for every row, `committed_value(original[i], newvals[i], any_fails(fails,0))` — `newvals[i]` iff the whole batch succeeded, else `original[i]` | `with transaction.atomic(using=router.db_for_write(self.model)):` wrapping the loop — commit on normal exit, roll back on any exception | A-reference | the changed operation (the atomic grouping) is modeled **deeply**: `committed_value`/`any_fails` ARE the commit/rollback verdict. There is no consumed `atomic` axiom; the deep model is validated **== the real callee** out-of-band by G-AX (axiom_check.py runs a real `transaction.atomic` block over SQLite, injects a failure at each position, and asserts the committed rows == the deep model). `atomic`'s documented contract — commit-on-success / rollback-on-exception — is exactly this fold (mapping.md §3.1). |
| A4 | `result` returned (a `List[int]` of committed row values) | the persisted database state after the request returns | R | post-request stored value of row `i` ↔ `Result()[i]`; the F2P test reads it back via `a.refresh_from_db()` / `assertEqual(a.load, 4)` (mapping.md §2). |

The discriminating content of the change — *a failure anywhere in the batch
discards EVERY replacement, including those of rows processed before the
failure* — lives in `committed_value(orig, new, any_fails(fails,0))` using the
**batch-global** `any_fails(fails, 0)` for every row (model) ⇔ the single
`atomic` boundary around the whole loop (real). The pre-patch had no boundary:
each successful `save_*` autocommitted, so a mid-batch failure left the earlier
rows' replacements persisted. `model_prepatch.py` reproduces that
(per-row autocommit: rows before the first failing edit keep `newvals`, the rest
keep `original`) and **fails** the postcondition
`ToSeq(Result())[k] == committed_value(orig[k], new[k], any_fails(fails,0))`,
which is exactly the spec sensing the change (G-DIFF). This matches the F2P
test's second scenario (`side_effect=[None, DatabaseError]`: first form
succeeds, second raises) where the pre-patch would persist the first form's edit
but the patch preserves both rows' originals.

## B. No kind-3 (unexpressible-changed-op) steps

Every step above is R or A-reference. The one operation that genuinely
*changed* — wrapping the save loop in an atomic transaction — is modeled
**deeply** (the spelled-out commit/rollback fold `committed_value`/`any_fails`
consumed in `apply_batch`, steps A2/A3, an **A-reference**), not hidden behind
an axiom about the function under change: there is **no consumed `atomic`
@ContractOnly axiom**. `transaction.atomic` appears only as the **A-reference**
that G-AX validates the deep model against (a real `atomic` block over SQLite).
There are no A-consumed axioms in this bundle.

## C. verify(model) ⇒ resolved

`apply_batch` verifies only if the committed value of every row is its
replacement on full-batch success and its original on ANY failure (A3, the
batch-global `any_fails`), with NO committed prefix on a mid-batch failure
(the prepatch's exact bug). By R (rows ↔ indices, values ↔ `int`, persisted
state ↔ `Result()`), the verified `apply_batch` equals the post-patch
`changelist_view` save block on the tested batches; by G-AX the deep model
`committed_value`/`any_fails` equals the real `transaction.atomic` commit/
rollback verdict (A-reference). Therefore a model satisfying this spec, refined
by the map above, is the gold patch up to type refinement and the audited
deep-model reference — and the gold patch resolves (G-RESOLVE). The single trust
point is refinement fidelity + the A-reference soundness (this document + G-AX),
exactly the two of PLAN §1.1; there is no consumed axiom.
