# mapping.md — django__django-16100

Binds every `model.py` symbol to its repository counterpart at
`base_commit = c6350d594c359151ee17b0c4f354bb44f28ff69e`, states the type
abstraction, and gives the provenance of the deep model reference (the
write-grouping primitive whose failure path discards the grouped writes).

Repo file under change: `django/contrib/admin/options.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `apply_batch(original, newvals, fails)` | the list-editable bulk-save block of `ModelAdmin.changelist_view` — `django/contrib/admin/options.py:2012-2021` (the `if formset.is_valid(): ... for form in formset.forms: if form.has_changed(): save_form/save_model/save_related/construct_change_message/log_change` loop) | the modeled changed behaviour: process the batch of edited forms and decide what persists |
| `committed_value(original, newval, batch_fails)` *(deep model — A-reference)* | the commit/rollback verdict of `transaction.atomic(using=router.db_for_write(self.model))` wrapping the loop (post-patch `django/contrib/admin/options.py:2014`) | pure spec: the value a row ends up holding — its replacement on full-batch success, its original value on any failure (rollback) |
| `any_fails(fails, i)` *(deep model — A-reference)* | "did processing any form in the batch raise" — the condition under which the `atomic` block exits with an exception and rolls back (an unhandled raise from any of `save_form`/`save_model`/`save_related`/`construct_change_message`/`log_change`) | pure spec: whether the batch tail from `i` contains a failing edit |

The post-patch repo line the modeled behaviour adds (for the refinement audit;
NOT referenced from the consumer spec view):
`with transaction.atomic(using=router.db_for_write(self.model)):`
(`options.py:2014` after the gold patch). The identical idiom already exists in
the same file for the bulk-delete action at `options.py:1745`, and the helper
imports (`from django.db import models, router, transaction`) are present at
`options.py:39` at base_commit.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| the persistent store rows touched by the batch (`Swallow` objects' edited fields in the F2P test) | `List[int]` `original`, one stored value per row | row `r`'s pre-batch stored value ↔ `original[r]`; row count ↔ `len(original)` |
| each form's submitted replacement value (`save_form`/`save_model` would write it) | `List[int]` `newvals`, parallel to `original` | the value form `r` would persist ↔ `newvals[r]`; "no change" rows are simply rows whose `newvals[r] == original[r]` |
| whether processing one form raises (the F2P test injects this via `mock.patch(... log_change, side_effect=DatabaseError)`) | `List[int]` `fails`, parallel; `fails[r] ∈ {0,1}` | form `r`'s processing raises ↔ `fails[r] == 1` |
| the committed database state after the request | `List[int]` `Result()`, one value per row | post-request stored value of row `r` ↔ `Result()[r]` |
| `transaction.atomic(...)` block + its rollback-on-exception | the `committed_value` / `any_fails` fold (deep model) | a raise inside the block ↔ `any_fails == True`; block exits normally ↔ `any_fails == False`; rollback ↔ every row reverts to `original`; commit ↔ every row holds `newvals` |

`str`/ORM objects are not modeled (the tested property is purely about WHICH
values persist, an integer-per-row abstraction); the specification is phrased
over `PSeq[int]` via `ToSeq`. The three input lists are read-only (the impl
rebuilds a fresh result carrier), so each carries `Acc(list_pred(·), 1/2)`,
Required and Ensured.

## 3. Deep-model reference (A-reference — checked by G-AX / axiom_check.py)

### 3.1 `committed_value` / `any_fails` deep model ↔ `transaction.atomic` rollback semantics
**Primitive:** `django.db.transaction.atomic(using=...)` as a context manager
wrapping a block that performs a sequence of writes. The *changed* operation is
the grouping of the per-form writes into one atomic unit; it is modeled
**deeply** by the pure fold `committed_value`/`any_fails` (model.py `pure`
region). There is **no consumed `atomic` @ContractOnly axiom** — the proof never
calls an axiom; it spells out the verdict directly.

The well-documented, contractually-guaranteed semantics of `atomic` that the
deep model encodes (Django docs, "Database transactions →
`transaction.atomic`"; https://docs.djangoproject.com/en/4.2/topics/db/transactions/#django.db.transaction.atomic):

> `atomic` allows us to create a block of code within which the atomicity on the
> database is guaranteed. If the block of code is successfully completed, the
> changes are committed to the database. If there is an exception, the changes
> are rolled back.

So for a block that writes replacement values row-by-row:
  * block completes (no edit raised) ⇒ **commit** ⇒ every row holds its
    replacement ⇒ `committed_value(orig, new, False) == new`;
  * any edit raises ⇒ the exception propagates out of the block ⇒ **rollback**
    ⇒ every row reverts to its pre-block value ⇒
    `committed_value(orig, new, True) == orig`, for EVERY row — including rows
    written before the failing one (their writes are inside the same atomic
    unit and are discarded together). That "no committed prefix on failure" is
    exactly the property the deep model pins and the pre-patch (un-grouped,
    autocommit-per-write) violates.

**Soundness check (G-AX):** `axiom_check.py` realizes the two regimes with a
real SQLite-backed `transaction.atomic` block (the same `django.db.transaction`
the gold patch calls): it stages a batch of row writes inside `atomic`, injects
a failure at each possible position (and none), and asserts the committed rows
match the deep model `committed_value`/`any_fails` — full replacement on
success, full revert on any failure, on boundary + fuzz batches. It imports only
Django's own `django.db` (the module the patch calls) configured against an
in-memory SQLite database; nothing instance-specific. Exit 0 iff sound.
