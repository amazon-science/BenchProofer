# refinement.md — django__django-14559

Maps every operation in `implementation_bulkUpdate` to its `patch.diff`
counterpart in `django/db/models/query.py::QuerySet.bulk_update`. Tags:
**R** type-refinement, **A-consumed** proof uses a callee axiom, **A-reference**
deep-modeled changed op validated == real callee, **I** identical concrete op.

## Patch (post-patch `bulk_update`, modeled core)
```python
if not objs:
    return 0                                   # was: return
...
rows_updated = 0
with transaction.atomic(using=self.db, savepoint=False):
    for pks, update_kwargs in updates:
        rows_updated += self.filter(pk__in=pks).update(**update_kwargs)
return rows_updated
```
where `updates` holds one `(pks, update_kwargs)` entry per batch, the batches
being `objs[i:i+batch_size] for i in range(0, len(objs), batch_size)`.

## Operation correspondence
| # | Lean op (`implementation_bulkUpdate`) | patch.diff op | tag | note |
|---|---|---|---|---|
| 1 | `if keys.isEmpty then return some 0` | `if not objs: return 0` | R | empty input ⇒ present count of zero. The edit `return` → `return 0` (line 541) is exactly this branch. `objs` empty ↔ `keys` empty. |
| 2 | `let batches := List.toChunks batchSize keys` | `updates` built from `objs[i:i+batch_size] for i in range(0, len(objs), batch_size)` (unchanged batching) | R | `toChunks batchSize` ≡ the `range`-stride consecutive fixed-size slices for `batchSize ≥ 1` (precondition). Identifiers carried as `keys`. |
| 3 | `let mut rowsUpdated := 0` | `rows_updated = 0` (added) | I | accumulator init; the introduced `rows_updated = 0`. |
| 4 | `for batch in batches do rowsUpdated := rowsUpdated + batch.dedup.length` | `for pks, update_kwargs in updates: rows_updated += self.filter(pk__in=pks).update(**update_kwargs)` (the accumulation edit) | R | `batch.dedup.length` deeply models the UNCHANGED `update(pk__in=pks)` return value = rows matched by `WHERE pk IN (…)` = number of *distinct* pks in the batch (SQL `IN` dedups; all referenced rows exist in the modeled domain). The `transaction.atomic` wrapper does not affect the count and is not modeled. |
| 5 | `return some rowsUpdated` | `return rows_updated` | R | return the accumulated present count. |

Every op is R or I. **No A row** (no consumed axiom, no A-reference): the only
unchanged callee whose result is consumed (`update`'s matched-row count) is
modeled *deeply* as `batch.dedup.length` (a total list operation), not
axiomatized. Therefore `meta.json axioms = []`, `deep_model_references = []`,
and `axiom_check.py` is a skip stub.

## R/I legs ⇒ G-CONF
The impl is all R/I (no A-tagged op), so `conf_skip = false` and
`conformance_check.py` mechanically differential-tests the impl shadow against
`patch.diff` behavior over ≥10^5 fuzzed `(keys, batchSize)` inputs (drawn from
the modeled domain: positive batch size, every key an existing row). The oracle
reproduces the patched accumulation with `update(pk__in=pks)`'s matched count
realized as the distinct-pk count of each batch. Zero disagreements ⇒ exit 0.

## Prepatch = the real bug
`Solution_prepatch.lean` makes the impl return `none` in every branch
(`return none` for empty input, `return none` after the accumulation loop) —
exactly the pre-patch behavior `bulk_update` had: it returned `None` instead of
a count (the empty branch `return`, and no `return` at the end → implicit
`None`). It cannot satisfy `problem_spec_bulkUpdate` (which demands `result =
some (batchedMatchCount …)`, a *present* count) for ANY input, so its
`correct_bulkUpdate` (carrying the gold proof body) is unclosable ⇒ G-DIFF fails
verification as required. There is a single independently-observable fixed
behavior (return a count rather than `None`), so one prepatch file.

## Duplicate-across-batches subtlety (the F2P discriminator)
`test_updated_rows_when_passing_duplicates` pins the precise semantics: two
copies of the same object in ONE batch ⇒ matched count 1 (`batchSize ≥ 2`); the
same two copies split across batches (`batch_size=1`) ⇒ matched count 2. The
deep model captures this exactly: the tally is `batch.dedup.length` *per batch*,
summed across batches, so within-batch duplicates collapse (`dedup`) while
across-batch duplicates are counted once per batch. A naive `keys.length`
(rows-sent) or `keys.dedup.length` (global-distinct) model would fail one of the
two assertions; `batchedMatchCount` matches both.
