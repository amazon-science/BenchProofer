# mapping.md — django__django-11951

## Symbol binding (file:line @ base_commit 312049091288dbba2299de8d07ea3e3311ed7238)

| Lean symbol | Python | location |
|---|---|---|
| `implementation_batchedInsert` / `problem_spec_batchedInsert` / `correct_batchedInsert` | the effective-batch-size computation **and** the splitting of `objs` into consecutive insert batches inside the bulk-insert helper | `django/db/models/query.py:1205-1218` @ base_commit (`_batched_insert`: the `batch_size = …` line plus the `[objs[i:i + batch_size] for i in range(0, len(objs), batch_size)]` comprehension the `for` iterates) |
| `effectiveBatchSize batchSize rawMax` | `max_batch_size = max(ops.bulk_batch_size(fields, objs), 1)`; `batch_size = min(batch_size, max_batch_size) if batch_size else max_batch_size` | gold patch, `query.py:1212-1213` (post-patch). Pre-patch was the single line `batch_size = (batch_size or max(ops.bulk_batch_size(fields, objs), 1))` at `query.py:1212` |
| `(objs.drop i).take eff` over `i ∈ [0:objs.length:eff]` | `[objs[i:i + batch_size] for i in range(0, len(objs), batch_size)]` | `query.py:1215` (unchanged across the patch; it consumes the recomputed `batch_size`) |

## Modeled inputs

The function under spec is the part of the bulk-insert helper that decides the
batch boundaries: it computes the effective per-batch size from the
caller-supplied size and the backend's compatible maximum, then slices the object
list into consecutive batches. Its observable inputs are:

| Lean | Python reality | meaning |
|---|---|---|
| `batchSize : Nat` | the `batch_size` parameter | caller-requested batch size; Python treats `None`/`0` as "unset" (falsy). Modeled as `0` ⇔ unset |
| `rawMax : Nat` | `ops.bulk_batch_size(fields, objs)` | the backend's compatible batch size for these fields/objects. An UNCHANGED callee whose result is taken as the model input (it is never negative). `max(·, 1)` is applied to it identically pre- and post-patch |
| `objs : List α` | `objs` | the model objects to insert; only their count/positions matter to batching, so the element type is generic |

## Output

| Lean | Python |
|---|---|
| `result : List (List α)` | the list of batches produced by `[objs[i:i + batch_size] for i in range(0, len(objs), batch_size)]` — i.e. the consecutive slices the helper then inserts one at a time. The number of batches is exactly the query count the FAIL_TO_PASS test counts (`ceil(len(objs) / max_batch_size)`) |

## Lean ↔ Python type bijection (used by G-CONF)

| Python | Lean | bijection |
|---|---|---|
| `batch_size` (`int` ≥ 1, or `None`/`0`) | `batchSize : Nat` | identity, with `None` ↦ `0` (both falsy) |
| `ops.bulk_batch_size(fields, objs)` (`int` ≥ 0) | `rawMax : Nat` | identity |
| `objs` (list of model instances) | `objs : List α` | positional identity; element identity is all that batching observes (G-CONF uses `int` payloads) |
| `[objs[i:i+bs] for i in range(0, len(objs), bs)]` | `result : List (List α)` | per-batch slice ↦ `(objs.drop i).take eff`; list-of-lists identity |

## Callee provenance + flag dependencies

- **No consumed callee axiom.** The only repo callee the modeled code calls,
  `ops.bulk_batch_size(fields, objs)`, is UNCHANGED; its result is supplied as the
  model input `rawMax`. The `max(rawMax, 1)`, the `min`/falsy selection, and the
  slicing are all modeled DEEPLY (spelled out), so they are A-reference / I rows
  validated by G-CONF, never axiomatized (§0.7). `axiom_check.py` is a skip stub.
- **No flag dependency** beyond the `batchSize = 0` (falsy) vs `> 0` selection,
  which G-CONF fuzzes on both sides of `rawMax`.

## G-CONF fuzz seed

`SEED = 20240627` (pinned in `conformance_check.py`).
