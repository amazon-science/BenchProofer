# mapping.md — django__django-14559

## Symbol binding
- Modeled function: `QuerySet.bulk_update(self, objs, fields, batch_size=None)`
  at `django/db/models/query.py:527` @ base_commit
  `d79be3ed39b76d3e34431873eec16f6dd354ab17`. The behavioral edit is at lines
  541 (`return` → `return 0`) and 563–567 (introduce `rows_updated`, accumulate
  each batch's `update()` return value, `return rows_updated`).
- Lean triple: `problem_spec_bulkUpdate` / `implementation_bulkUpdate` /
  `correct_bulkUpdate` in `Solution.lean`.

## Type bijection (Lean ↔ Python) — used by G-CONF and G-AX
| Lean | Python | note |
|---|---|---|
| `keys : List Int` | `[obj.pk for obj in tuple(objs)]` — the primary keys of the supplied objects, in order | each object carries the identifier of the stored row it updates. The other observables of `objs`/`fields` (field values, model meta) do not affect the modeled output (the *count* of matched rows), only the per-batch identifier multiset does. |
| `batchSize : Nat` (with `1 ≤ batchSize`) | the effective batch size `min(batch_size, max_batch_size)` (a positive int; `bulk_batch_size` ≥ 1) | the fix's batching `objs[i:i+batch_size] for i in range(0, len(objs), batch_size)`. |
| `List.toChunks batchSize keys` | `(objs[i:i+batch_size] for i in range(0, len(objs), batch_size))` projected onto pks | for `batchSize ≥ 1`, `toChunks` produces exactly the consecutive fixed-size slices Python's `range`-stride loop produces. |
| `batch.dedup.length` | `Note.objects.filter(pk__in=pks).update(**kwargs)` return value, for a batch whose pks all reference existing stored rows | `update()` returns rows matched by `WHERE pk IN (…)`; SQL `IN` matches each *distinct* pk at most once, so the matched count is the number of distinct pks in the batch (under the modeled domain: every referenced row exists). |
| `result : Option Nat` | `bulk_update`'s return value | post-fix it is always an `int` (a present count) — `some n`; pre-fix it is always `None` — `none`. |

## Callee provenance + flag deps
- `QuerySet.update` (`django/db/models/query.py`, ~line 783) is **UNCHANGED** by
  the patch. Its row-match semantics (distinct-pk count under `pk__in`) are
  modeled *deeply* as `batch.dedup.length` rather than axiomatized, so there is
  no consumed callee axiom and no `opaque` decl. The deep model is sound under
  the modeled domain (all referenced rows exist); G-CONF fuzzes that domain.
- `transaction.atomic(using=…, savepoint=False)` wraps the accumulation loop;
  it is a control-flow/durability wrapper that does not change the returned
  count, so it is not modeled.
- `connections[self.db].ops.bulk_batch_size(...)` and the `When/Case/Cast`
  query construction affect only *how* each batch's UPDATE is built, not the
  matched-row count; not modeled (they are upstream of the modeled output).
- No flag dependency (no boolean-gated callee behavior).

## Modeled domain / preconditions
- `1 ≤ batchSize` (precondition binder in `correct_bulkUpdate`): batch size is a
  positive integer (the real `batch_size`/`bulk_batch_size` is ≥ 1; a non-positive
  `batch_size` raises before reaching the modeled code).
- Every key references an existing stored row (the domain `bulk_update`
  operates on — it updates already-stored objects). Under this domain
  `update(pk__in=pks)` matches exactly the distinct pks of the batch.

## G-CONF fuzz seed
Pinned seed: **14559** (also in `conformance_check.py`).
