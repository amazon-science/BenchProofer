# mapping.md — django__django-14559

Binds every `model.py` symbol to its repository counterpart at
`base_commit = d79be3ed39b76d3e34431873eec16f6dd354ab17`, states the type
abstraction, and gives the provenance of the one axiom (callee source + the
exact behaviour the axiom encodes).

Repo file under change: `django/db/models/query.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `bulk_apply_count(keys, group_size)` | `QuerySet.bulk_update(self, objs, fields, batch_size=None)` — `django/db/models/query.py:527-569` (the batched-update body) | the modeled changed function (the batched persistence operation) |
| `keys` (`List[int]`) | `objs` after `objs = tuple(objs)` (`query.py:535`), reduced to the per-object primary keys `[obj.pk for obj in batch_objs]` (`query.py:565`) | the ordered collection of stored objects, projected to their primary-key values |
| `group_size` (`int`) | the effective batch size `batch_size = min(batch_size, max_batch_size) if batch_size else max_batch_size` (`query.py:548`) | the positive fixed group size objects are split into (`objs[i:i + batch_size]`, `query.py:550`) |
| `matched_rows(group_keys)` *(axiom — A-consumed)* | `self.filter(pk__in=pks).update(**update_kwargs)` — `QuerySet.update` (`django/db/models/query.py:769-786`) called once per group at `query.py:568` | unchanged community callee: the per-group database update; returns the number of rows it matched/affected |
| `batched_total(keys, group_size)` | the per-group sum the patch introduces (`rows_updated += ...` accumulated over `updates`, `query.py:566-568` post-patch) | pure spec: the total reported across the successive groups |
| `Result()` (`Optional[int]`) | the `bulk_update` return value (`return rows_updated`, post-patch; pre-patch bare `return` / implicit `None`) | the surfaced affected-row count |

The contract additionally carries a termination obligation
(`Requires(MustTerminate(2))`, consumed by the impl loop's decreasing measure
`Invariant(MustTerminate(len(keys) - off))`): the real operation walks a finite
tuple of per-group updates and returns in finite time, so the count is actually
delivered; without the obligation Nagini's partial-correctness semantics would
let a never-returning implementation discharge the value postconditions
vacuously.

The gold patch makes two edits inside `bulk_update`:
1. the empty-collection early exit `return` → `return 0` (`query.py:544`); and
2. introduces `rows_updated = 0`, accumulates `rows_updated += self.filter(pk__in=pks).update(**update_kwargs)` per group, and ends with `return rows_updated` (`query.py:566-568`).
Pre-patch, both paths reach a bare `return` and yield `None`.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `objs` (a tuple of model instances) projected to `[obj.pk for obj in batch_objs]` | `keys : List[int]` of primary-key values | the only property of each object the affected-row count depends on is its primary key; an object ↔ its `pk` value. The positional order and multiplicity of `objs` are preserved by the projection (`tuple(objs)` then per-group `[obj.pk ...]`), and are preserved in `keys`. |
| `batch_size` (a positive `int`; computed as `min(batch_size, max_batch_size)` or `max_batch_size`, both `>= 1`) | `group_size : int`, `Requires(group_size >= 1)` | the effective batch size is always a positive integer (`bulk_batch_size` returns a positive count; a user `batch_size` of `0`/negative is rejected earlier or falls back to `max_batch_size`). Position-based chunking `objs[i:i+batch_size]` ↔ `keys` split into front-to-back groups of `group_size`. |
| `self.filter(pk__in=pks).update(**update_kwargs)` → an `int` of affected rows | `matched_rows(group_keys) : int` (axiom) | `update()` returns the DB-reported affected-row count; `pk__in` matches each present distinct key once, so duplicate keys inside one group are matched once (a single-group count), which is precisely why a key repeated across *separate* groups is summed twice. Carrier of one group's report. |
| the return value (`None` pre-patch, `int` post-patch) | `Optional[int]` (`Result()`) | `None` ↔ the absent value (no count reported); the accumulated `int` ↔ the produced non-negative count. The postcondition `Result() is not None` is exactly "report a count instead of nothing". |

The `fields`, `update_kwargs`, `When`/`Case`/`Cast` machinery (`query.py:551-565`) builds the SQL the per-group `update()` issues; it does not affect *how many* rows are matched (that is the `pk__in` filter), so it is abstracted into the `matched_rows` callee and not modelled field-by-field. The `transaction.atomic` wrapper (`query.py:566`) does not change the counts returned by the individual `update()` calls.

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `matched_rows` ↔ `QuerySet.update` (A-consumed)
**Callee:** `django.db.models.query.QuerySet.update(**kwargs)`
(`django/db/models/query.py:769-786`). Source:

```python
def update(self, **kwargs):
    ...
    self._for_write = True
    query = self.query.chain(sql.UpdateQuery)
    query.add_update_values(kwargs)
    query.annotations = {}
    with transaction.mark_for_rollback_on_error(using=self.db):
        rows = query.get_compiler(self.db).execute_sql(CURSOR)
    self._result_cache = None
    return rows
update.alters_data = True
```

`rows` is `cursor.rowcount` from the executed UPDATE — always a **non-negative
integer** (the number of rows the WHERE clause matched; `0` when nothing
matches). `bulk_update` invokes it as `self.filter(pk__in=pks).update(...)`, so
the WHERE clause is `pk IN (pks)`: each *distinct, present* primary key is
matched once. Within one group the pk list may contain duplicates
(`[obj.pk for obj in batch_objs]` with a repeated object), but `pk__in` is a set
membership, so the single-group count collapses duplicates; across groups the
counts are summed, so a key in two groups contributes twice. This is exactly
the duplicate behaviour the F2P test `test_updated_rows_when_passing_duplicates`
pins (`[note, note]` in one group → 1; with `batch_size=1` → two groups → 2).

The axiom encodes only the obligation the proof consumes: the per-group report
is non-negative (`Ensures(Result() >= 0)`). That suffices to discharge the
spec's `Result() >= 0` and the `Result() is not None` clauses, while the
*structure* of the total (the per-group sum `batched_total`) is modelled deeply
and is independent of the concrete per-group value. It is the **weakest**
contract the modeled return value needs; the patch does not change `update()`,
so this is a genuine kind-A (A-consumed) axiom — not the operation under change.

**Soundness check (G-AX):** `axiom_check.py` configures an in-memory sqlite
database and a minimal dependency-free model, creates rows, and runs the real
`Model.objects.filter(pk__in=pks).update(field=...)` on:
  - a single present key (count `1`),
  - an absent key (count `0`),
  - a group with duplicate present keys `[pk, pk]` (count `1` — `pk__in`
    collapses duplicates),
  - mixed present/absent groups,
  - randomized fuzz groups (every observed count equals the number of *distinct
    present* keys, hence `>= 0`).
Every observation satisfies `Result() >= 0`. It additionally records, as the
G-AX evidence for the duplicate subtlety, that `update([pk, pk])` reports `1`
(single group) while summing `update([pk]) + update([pk])` reports `2` (two
groups) — the property `batched_total` relies on. It imports only Django (the
module the patch lives in); nothing test-private. Exit `0` iff sound. (Outside
the container Django is absent, so it prints `G-AX SKIP` and returns `0`; the
orchestrator runs it in-container.)

The axiom is flag-independent: `update()`'s return is the DB-reported matched
row count regardless of backend; G-AX exercises the default `sqlite3` backend
the harness uses.
