# refinement.md — django__django-16100

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`processBatch` `do` block + the deep `committedAtomic` model) and `patch.diff`
(the gold patch). Each step is tagged **R** (type refinement), **A**
(axiomatized/deep-modeled callee — **A-consumed** where the proof uses an
axiom's `ensures`, **A-reference** where a deep model is validated == the real
callee by G-AX), or **I** (identical concrete op).

The R/I legs are mechanically refuted by **G-CONF** — here G-CONF is `conf_skip`
(§C below); the A legs and this narrative are audited by **G-EQ**. Claim: any
impl verifying against this frozen spec, refined per the map below, is
behaviourally equal to the gold patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The list-editable save loop — `changelist_view` (`options.py:2011-2025`)

Gold hunk (abridged):
```
  if formset.is_valid():
      changecount = 0
-     for form in formset.forms:
-         if form.has_changed():
-             obj = self.save_form(request, form, change=True)
-             self.save_model(request, obj, form, change=True)
-             self.save_related(request, form, formsets=[], change=True)
-             change_msg = self.construct_change_message(request, form, None)
-             self.log_change(request, obj, change_msg)
-             changecount += 1
+     with transaction.atomic(using=router.db_for_write(self.model)):
+         for form in formset.forms:
+             if form.has_changed():
+                 obj = self.save_form(request, form, change=True)
+                 self.save_model(request, obj, form, change=True)
+                 self.save_related(request, form, formsets=[], change=True)
+                 change_msg = self.construct_change_message(request, form, None)
+                 self.log_change(request, obj, change_msg)
+                 changecount += 1
```
The fix changes NO per-row computation — it only wraps the existing loop in a
single transaction, so the batch of writes becomes all-or-nothing.

| # | Solution.lean impl op (`processBatch`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `updates : List Upd` | `formset.forms` iterated by `for form in formset.forms` | R | `forms` ↔ `List Upd`, order-preserving (mapping.md §2). |
| A2 | `if u.changed then … stage …` (`staged := (if u.changed then [u.value] else []) ++ staged`) | `if form.has_changed():` then `save_form`/`save_model`/`save_related` | R + I | only an edited row stages a write; `has_changed()` ↔ `Upd.changed`; the staged write ↔ `Upd.value`. The branch + staging is concrete (I); the form→`Upd` carrier is R. |
| A3 | `failed := (u.changed && u.raises) \|\| failed` | a processing step of the row raising (the F2P mocks `log_change` → `DatabaseError`) | R + I | an exception on an edited row makes the unit fail; `raises` ↔ "this row's processing throws". Concrete tracking (I) over the R carrier. |
| A4 | commit point `let committed := if failed then [] else staged`; result `out = committedAtomic updates` | `with transaction.atomic(using=router.db_for_write(self.model)):` deciding commit-vs-rollback of the whole loop | **A-reference** | the all-or-nothing semantics is modeled **deeply**: `committedAtomic = [] if anyFail else changedVals`. There is no consumed `atomic` axiom. The fold ops (`anyFail`, `changedVals`, the loop, the commit `if`) are **I** (concrete); the equality of that deep model to the real `transaction.atomic` (a mid-batch raise rolls back ALL staged writes, a clean batch commits ALL) is the **A-reference** G-AX validates. mapping.md §3.1. |
| A5 | `using` not modeled (commit alias) | `using=router.db_for_write(self.model)` | A-reference (orthogonal) | the write alias the atomic unit commits to; G-AX confirms it resolves to a real alias and is orthogonal to the rollback property (mapping.md §3.2). The F2P uses a single default DB. |

The twin artifacts use **total-correctness** semantics
(`loom.semantics.termination "total"`, with `decreasing i` on the loop): the
real save loop is a bounded pass over the finite `formset.forms` that always
terminates and reports its outcome, so a diverging implementation (e.g. a save
loop that never makes progress and never returns) must NOT satisfy the spec —
partial correctness would admit it vacuously.

Discriminating content of the change — *on any error, NOTHING is committed* —
lives in `committedAtomic us = if anyFail us then [] else changedVals us`
(model) ⇔ `transaction.atomic`'s rollback on an escaping exception (real). The
pre-patch loop has no atomic wrapper, so it commits each write as it happens;
`Solution_prepatch.lean` reproduces that (commit `staged` with no rollback) and
**fails** `out = committedAtomic updates` exactly on the clause
`anyFail updates = true → staged = []` (G-DIFF — confirmed: the unsolved goal is
`i_1 = true → staged_1 = []`).

## B. The atomicity property — why the deep model is the load-bearing claim

The single behavioural fact the F2P test `test_list_editable_atomicity`
observes: after a `DatabaseError` raised mid-batch (mocked on `log_change`), the
edited rows are **unchanged in the database** — i.e. every write staged before
the failure is rolled back. Pre-patch, the first row's write is already
committed when the second row fails, so the row is left modified (test fails).

This rollback is not a per-row computation but a property of the surrounding
`transaction.atomic` block. It is modeled deeply by `committedAtomic` and its
soundness against the real transaction manager is the A-reference audited by
axiom_check.py (G-AX), which runs the actual save loop inside a real
`transaction.atomic(using=router.db_for_write(...))` over a transaction-capable
backend and confirms the committed DB state == `committedAtomic(batch)` on 9
boundary + 2000 fuzz batches.

## C. No kind-3 (inexpressible-changed-op) steps; conf_skip rationale

Every step is R, A, or I. The one operation that genuinely *changed* — making
the save loop atomic — is modeled **deeply** (`committedAtomic`, step A4, an
A-reference + I), not hidden behind an axiom about the function under change;
there is **no consumed axiom** at all.

G-CONF is `conf_skip=true`: the impl region's only observable is a **live
database commit/rollback side effect** (durable writes vs. rollback on a
mid-batch error). There is no DB-free, input-dependent R/I shadow to fuzz — the
discriminating fact is a property of the unchanged `transaction.atomic`
machinery, reproducible only by the live save/commit/rollback path (the F2P
integration test itself). Soundness is carried by G-VERIFY + G-DIFF + G-AX. This
mirrors the sibling `transaction.atomic` instance django__django-11066.

## D. verify(Solution) ⇒ resolved

`processBatch` verifies only if its result equals `committedAtomic updates` —
i.e. `[]` whenever any edited row raises (A4), and `changedVals` otherwise. By R
(`forms ↔ List Upd`, `has_changed ↔ changed`, a row's persisted write ↔ `value`,
a raising step ↔ `raises`) the verified loop equals the gold patch's atomic save
loop on the tested batch: by G-AX the deep model `committedAtomic` equals the
real `transaction.atomic` behaviour (A-reference) — a mid-batch exception rolls
back all staged writes, a clean batch commits all. Therefore a model satisfying
this spec, refined by the map above, is the gold patch up to type refinement and
the audited transaction callee — and the gold patch resolves (G-RESOLVE). The
one trust point is axiom/deep-model soundness (G-AX, plan §1.1); refinement
fidelity is this doc (G-EQ), with G-CONF skipped per §C.
