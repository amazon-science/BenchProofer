# mapping.md — django__django-12209

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 5a68f024987e6d16c2626a31bf653a2edddea579`, states the type
abstraction, and gives the provenance of the one axiom (callee source + the
exact behaviour the axiom encodes).

Repo file under change: `django/db/models/base.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `store_single_table(pk_explicit, force_insert, pk_set, adding, pk_has_default)` | `Model._save_table(self, raw=False, cls=None, force_insert=False, force_update=False, using=None, update_fields=None)` — `django/db/models/base.py:829-890` | the modeled changed function (the single-table save routine) |
| `pk_explicit` | the `raw` parameter (`base.py:829`) | the model symbol carries the repo `raw` parameter (unprocessed-data mode: True for (de)serialisation/`loaddata` re-saves, `Model.save_base(..., raw=True)`); the conjunct the change adds. Behaviourally, this is exactly the case where the identifier was caller-supplied rather than field-generated — the spec view (consumer-facing) uses the abstract behavioural name `pk_explicit`, the repo binding is `raw` |
| `force_insert` | the `force_insert` parameter (`base.py:829`) | caller-forced insertion |
| `pk_set` | `pk_set = pk_val is not None` (`base.py:846`) | whether an identifier value is present |
| `adding` | `self._state.adding` (`base.py:853`) | whether the object is being added (not yet persisted) |
| `pk_has_default` | `self._meta.pk.default and self._meta.pk.default is not NOT_PROVIDED` (`base.py:854-855`) | the identifier field has a generating default (the conjunction of the two operands, one bool) |
| `force_insert_eff` (impl local) | the re-assigned `force_insert` after the guard block (`base.py:851-857`) — `if (...): force_insert = True` | the effective straight-to-insertion decision |
| `update_matched_row()` *(axiom — A-consumed)* | `self._do_update(base_qs, using, pk_val, values, update_fields, forced_update)` — `Model._do_update` (`django/db/models/base.py:892-917`) | unchanged community callee: the UPDATE primitive; returns True iff a stored row matched the identifier and was updated |
| `Result()` (the `bool` returned) | `updated` in `return updated` (`base.py:849,864,890`) | whether the routine reported updating an existing row |

The gold patch (the one change, `base.py:852`) inserts the conjunct `not raw and`
at the head of the `if (...)` guard that, when satisfied, re-assigns
`force_insert = True` (the straight-to-insertion short-cut). Pre-patch, that
conjunct is absent, so the short-cut also engages in unprocessed-data mode.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `Model` instance `self` with `_state.adding`, `_meta.pk.default`, `_get_pk_val(meta)`, and the `raw` parameter | five plain `bool` parameters | only the booleans that feed the changed decision are carried; every other field/operation of the routine is untouched by the change and abstracted away |
| the `raw` parameter (`base.py:829`) | `pk_explicit: bool` | repo `raw` (True for (de)serialisation re-saves) ↔ model `pk_explicit`; behaviourally the case where the identifier was caller-supplied rather than field-generated. Spec-view name is the abstract `pk_explicit`; repo symbol is `raw` |
| `pk_val = self._get_pk_val(meta)` then `pk_set = pk_val is not None` (`base.py:842-846`) | `pk_set: bool` | the presence of an identifier value (`pk_val is not None`) ↔ `pk_set` |
| `self._state.adding` (`base.py:853`) | `adding: bool` | identical boolean |
| `self._meta.pk.default and self._meta.pk.default is not NOT_PROVIDED` (`base.py:854-855`) | `pk_has_default: bool` | the conjunction of the two unchanged operands collapsed to one bool: True iff the primary-key field carries a real generating default (a callable/value distinct from the `NOT_PROVIDED` sentinel) |
| the body of the `if pk_set and not force_insert:` block — `_do_update(...)` and the `_do_insert(...)` fallback (`base.py:858-890`) | `update_matched_row(): bool` axiom + the `updated` flag | only the UPDATE outcome `updated` is behaviourally observed by this change; the INSERT fallback and the row-value gathering are untouched and abstracted (refinement.md) |
| `return updated` (`base.py:890`) | `Result(): bool` | identical boolean: whether an existing row was updated |

`force_update` / `update_fields` / `using` / `cls` / `meta` / the
`order_with_respect_to` block / the row-value list comprehension are all
unchanged by the patch and observe no part of the changed decision; they are
abstracted away (refinement.md, §C confirms no kind-3 step).

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `update_matched_row` ↔ `Model._do_update` (A-consumed)
**Callee:** `django.db.models.base.Model._do_update(base_qs, using, pk_val, values, update_fields, forced_update)`
(`django/db/models/base.py:892-917`). Source (abridged):

```python
def _do_update(self, base_qs, using, pk_val, values, update_fields, forced_update):
    filtered = base_qs.filter(pk=pk_val)
    if not values:
        return update_fields is not None or filtered.exists()
    if self._meta.select_on_save and not forced_update:
        return (filtered.exists() and
                (filtered._update(values) > 0 or filtered.exists()))
    return filtered._update(values) > 0
```

`_do_update` returns a **bool**: True iff an UPDATE matched a stored row for the
instance's primary key (`filtered._update(values) > 0`, or `filtered.exists()`
in the no-values/select-on-save branches). It is invoked **only** along the
`if pk_set and not force_insert:` path (`base.py:859-865`), i.e. only when an
identifier is present; it issues SQL against the stored row and reports whether
a row matched. For an instance whose identifier already exists in storage
(the re-save case the fix targets) it returns **True**; for an absent
identifier it returns **False**.

The axiom encodes only the obligation the proof consumes: the UPDATE primitive
yields a single, instance-fixed boolean outcome (`update_matched_row()`), which
the routine returns as `updated` along the update path. The patch does NOT
change `_do_update`; it changes only whether that path is reached. So
`update_matched_row` is a genuine kind-A axiom (the unchanged callee), not the
operation under change.

**Soundness check (G-AX):** `axiom_check.py` configures an in-memory sqlite
database and a minimal model whose primary key carries a generating default
(`uuid.uuid4`) — the structural twin of the test's `UUIDDefaultData`. It then
drives the **real** `_save_table` decision both ways:
  (a) re-saving an instance whose explicit identifier already exists, in
      unprocessed-data mode (`raw=True`) — asserting the routine reaches the
      UPDATE path and reports an update (no duplicate-key INSERT), and
  (b) the same re-save in processed-data mode (`raw=False`) — asserting the
      short-cut engages and the UPDATE path is skipped.
This directly exercises that the real `_do_update` returns True for a present
row (the axiom's consumed value along the raw path) and that the patched guard
routes control as the model specifies. It imports only Django itself (the
module the patch lives in); nothing test-private. Exit 0 iff sound. (Outside the
container Django is absent, so it prints `G-AX SKIP` and returns 0; the
orchestrator runs it in-container.)

The axiom is flag/backend-independent: `_do_update`'s return is the
DB-reported match regardless of backend; G-AX exercises the default `sqlite3`
backend the harness uses.
