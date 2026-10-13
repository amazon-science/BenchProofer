# refinement.md — django__django-11951

Operation correspondence between `implementation_splitBatches` and the gold
`patch.diff`. Tags: **R** (type refinement), **A-consumed** (proof uses an
axiom's property), **A-reference** (deep model validated == real behavior by
G-CONF), **I** (identical concrete op).

No axioms are declared or consumed. The only external operation the modeled code
calls — `ops.bulk_batch_size(fields, objs)` (UNCHANGED) — has its result supplied
as the model input `rawMax`; the effective-size selection and the partitioning
into batches are modeled DEEPLY. Every row is **R**, **A-reference**, or **I**.
The R / I / A-reference legs are differential-tested by G-CONF; G-AX is a skip
stub.

## What the gold patch changes (`django/db/models/query.py`, `_batched_insert`)

A single edit to how the effective batch size is computed before the object list
is sliced into batches:

* **pre-patch** (one line):
  ```python
  batch_size = (batch_size or max(ops.bulk_batch_size(fields, objs), 1))
  ```
  A truthy caller-supplied `batch_size` is used verbatim — it can EXCEED the
  backend's compatible maximum, defeating the cap.
* **post-patch**:
  ```python
  max_batch_size = max(ops.bulk_batch_size(fields, objs), 1)
  batch_size = min(batch_size, max_batch_size) if batch_size else max_batch_size
  ```
  A truthy `batch_size` is now clamped to `max_batch_size`; a falsy one still
  falls back to `max_batch_size`.

The subsequent slicing
`[objs[i:i + batch_size] for i in range(0, len(objs), batch_size)]` is unchanged;
it consumes the recomputed `batch_size`.

## `implementation_splitBatches` ↔ the patched body

| Lean op | patch.diff / source counterpart | tag | note |
|---|---|---|---|
| inputs `batchSize rawMax : Nat`, `objs : List α` | the `batch_size` param, `ops.bulk_batch_size(fields, objs)`, and `objs` | R | `batch_size` falsy (`None`/`0`) ↦ `0`; `bulk_batch_size` is the UNCHANGED callee whose output is the model input `rawMax`; `objs` ↦ `List α` positionally |
| `let maxBatchSize := max rawMax 1` | `max_batch_size = max(ops.bulk_batch_size(fields, objs), 1)` | I | identical normalization, present pre- and post-patch |
| `let eff := if batchSize = 0 then maxBatchSize else min batchSize maxBatchSize` (≡ `effectiveBatchSize batchSize rawMax`) | `batch_size = min(batch_size, max_batch_size) if batch_size else max_batch_size` | A-reference | the EDITED size selection: a truthy request is clamped to the maximum, a falsy one falls back to it; Python truthiness of `batch_size` ↦ `batchSize ≠ 0`; validated == real expression by G-CONF |
| `for k in [0:batchCount eff objs.length] do batches := batches ++ [(objs.drop (k*eff)).take eff]` (≡ `chunkBatches eff objs`) | `[objs[i:i + batch_size] for i in range(0, len(objs), batch_size)]` | I | the UNCHANGED slicing loop: offsets `0, eff, 2·eff, …`; `objs[i:i+eff]` ↦ `(objs.drop i).take eff`; `range(0,n,eff)` has `⌈n/eff⌉ = (n+eff-1)/eff` steps = `batchCount eff n` |
| `return batches` | the list comprehension result (the batches inserted one at a time) | R | list-of-slices ↦ `List (List α)`, positional identity |

`effectiveBatchSize` reproduces `min(batch_size, max_batch_size) if batch_size
else max_batch_size` exactly, with `batchSize = 0` modeling the falsy request.
`batchCount eff n = (n + eff - 1) / eff` is `len(range(0, n, eff))` for `eff ≥ 1`,
which holds because `effectiveBatchSize` is always `≥ 1` (`max rawMax 1 ≥ 1`, and
`min batchSize (max rawMax 1) ≥ 1` when `batchSize ≥ 1`).

## Independently-observable behavior (G-DIFF)

One prepatch variant (the patch fixes a single behavior):

- **`Solution_prepatch.lean`** — reinstates the pre-patch size selection
  `eff := if batchSize = 0 then maxBatchSize else batchSize` (a truthy request
  overrides the maximum instead of being clamped). Its `correct_splitBatches`
  cannot close on the discriminating clause whenever `0 < batchSize` and
  `maxBatchSize < batchSize`: the buggy impl produces fewer, larger batches than
  `chunkBatches (effectiveBatchSize batchSize rawMax) objs` requires. This is the
  FAIL_TO_PASS behavior (`test_explicit_batch_size_respects_max_batch_size`:
  `bulk_create(objs, batch_size=max_batch_size + 1)` must issue
  `ceil(len(objs) / max_batch_size)` queries, i.e. cap to `max_batch_size`).

The prepatch keeps the spec view byte-identical to `Solution.lean`.
