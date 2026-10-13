# mapping.md — django__django-16100

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = c6350d594c359151ee17b0c4f354bb44f28ff69e`, states the type
abstraction (the bijection G-AX / G-CONF use to bridge Lean↔Python), and gives
the provenance of the modeled callees.

Repo file under change: `django/contrib/admin/options.py`
(`ModelAdmin.changelist_view`, the list-editable bulk-save loop).

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `processBatch (updates : List Upd)` | the list-editable save loop inside `ModelAdmin.changelist_view` — `django/contrib/admin/options.py:2011-2025` (the `for form in formset.forms:` block guarded by `formset.is_valid()`) | the modeled changed function: process a batch of edited-form writes and report which writes end up committed |
| `Upd` (structure) | one `form` in `formset.forms` and the per-row work it triggers (`save_form`/`save_model`/`save_related`/`log_change`) | `changed` ↔ `form.has_changed()`; `value` ↔ the identity of the write `save_model` would persist for that row; `raises` ↔ whether any of that row's processing steps raises (the F2P mocks `log_change` to raise `DatabaseError`) |
| `committedAtomic` *(deep model — A-reference)* | the all-or-nothing commit semantics of `with transaction.atomic(using=router.db_for_write(self.model)):` wrapping the loop (`options.py:2016` post-patch) | pure spec: the set of writes durably committed after the whole batch — `[]` if any row raises, else every edited row's write. Deep model of the unchanged transaction manager, validated `committedAtomic == real transaction.atomic` by axiom_check.py (G-AX), NOT consumed as an axiom |
| `anyFail`, `changedVals` | the per-row decomposition of the loop body: which rows raise, and which rows stage a write (`if form.has_changed():`) | pure spec helpers (front-recursive folds) |

The pre-patch repo shape the change fixes (refinement audit only, not in the
consumer spec view): the same loop with **no** surrounding `transaction.atomic`,
so each `save_model`/`save_related` runs in autocommit and is durable the moment
it executes — a failure midway leaves the rows processed before it committed.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

| repo reality | Lean carrier | bijection |
|---|---|---|
| `formset.forms` (the batch of edited forms) | `List Upd` | order-preserving; `len(forms)` ↔ `updates.length`; the i-th form ↔ `updates[i]` |
| `form.has_changed()` | `Upd.changed : Bool` | the boolean the loop branches on (`if form.has_changed():`); only changed rows stage a write |
| the persisted write of one row (`save_form`+`save_model`+`save_related`) | `Upd.value : Int` (opaque identity token) | each edited row's committed write is represented by a distinct `Int`; *presence* of `value` in the result ↔ that row's write is durably committed. The fields/columns actually written are orthogonal (only durability is observed). |
| any processing step of a row raising (the F2P mocks `log_change` → `DatabaseError`) | `Upd.raises : Bool` | `raises = true` ↔ processing that row throws; an exception can only arise on an edited row (an unedited row stages no work), matching `anyFail` only counting `changed && raises` |
| the committed database state after the batch | `List Int` (the result `out`) | the multiset/sequence of durably-committed row writes ↔ `out`; rollback ↔ `out = []` |
| `transaction.atomic(using=router.db_for_write(self.model))` | the `committedAtomic` semantics (deep model) | the atomic block makes the batch one unit of work; `using=` is the write alias the unit commits to (G-AX confirms it resolves to a real alias and is orthogonal to the all-or-nothing property) |

`List Int` / `List Upd` indexing is total and sound (no `List[int]` workaround
needed); the carrier is a `List` because the operation is a left-to-right scan
of the batch.

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `committedAtomic` deep model ↔ `transaction.atomic` (A-reference)
**Callee:** `django.db.transaction.atomic` (unchanged stdlib-of-Django
transaction manager). The changed behaviour — making the per-row save loop a
single all-or-nothing unit of work — is modeled **deeply** by `committedAtomic`
(with `anyFail`/`changedVals`) in the `pure` region; there is **no consumed
axiom**. The relied-on property of `transaction.atomic` is exactly:

> writes performed inside the block are durable **iff** the block is exited
> without an exception escaping; if any exception escapes, **every** write made
> inside the block is rolled back.

This is the documented contract of `transaction.atomic`
(https://docs.djangoproject.com/en/4.1/topics/db/transactions/#django.db.transaction.atomic)
and is what `committedAtomic` encodes: `[] if anyFail else changedVals`.

**Soundness check (G-AX):** `axiom_check.py` stands up a real sqlite backend (a
backend with `supports_transactions`, as the F2P requires via
`@skipUnlessDBFeature`), defines a real `Row` model + table, and runs the patch's
save loop **inside a real `transaction.atomic(using=router.db_for_write(Row))`**
over 9 boundary batches (empty, all-clean, fail-first/last/middle, no-edited-row,
single-clean, single-failing) + 2000 randomized fuzz batches. It asserts the
durably-committed table state equals `committedAtomic(batch)` for every batch:
a mid-batch exception rolls back ALL staged writes (commit set `[]`), and a clean
batch commits every edited row's write (`== changedVals`). Imports only stdlib +
`django.db`. Exit 0 iff sound.

### 3.2 `router.db_for_write` (the `using=` argument) — A-reference (orthogonal)
`router.db_for_write(self.model)` chooses the alias the atomic unit commits to.
G-AX confirms it resolves to a real connection alias (`"default"` in the check)
and that the all-or-nothing rollback property holds on that connection
regardless of the alias. The alias choice is not part of the modeled
behaviour (the F2P uses a single default DB); it is recorded here for provenance.

## 4. G-CONF fuzz seed — N/A (conf_skip=true)

`conformance_check.py` is a `status=skip` stub: the impl region's only observable
is a **live database commit/rollback side effect** (whether the batch of row
UPDATEs is durable or rolled back on a mid-batch error). There is no DB-free,
input-dependent R/I shadow this gate could fuzz — the discriminating fact is a
property of the unchanged `transaction.atomic` machinery, exercised only by the
live save/commit/rollback path (the F2P integration test
`test_list_editable_atomicity` itself). Soundness is carried instead by
G-VERIFY + G-DIFF + G-AX (§3.1). For provenance, the G-AX fuzz seed is pinned at
**`16100`**.
