# mapping.md — django__django-11951

Binds `Solution.lean` symbols to the repo at
`base_commit = 312049091288dbba2299de8d07ea3e3311ed7238`.

Repo file under change:
`django/db/models/query.py` (method `QuerySet._batched_insert`).

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `effectiveBatchSize (batchSize maxBatchSize : Nat)` | the `batch_size` reassignment at `django/db/models/query.py:1212` (was `:1212` pre-patch) inside `_batched_insert` | the modeled chunk-size derivation |
| `batchSize` | the `batch_size` parameter of `_batched_insert` (0/None ⇒ "unspecified") | caller-requested chunk size |
| `maxBatchSize` | `max(ops.bulk_batch_size(fields, objs), 1)` — the database-compatible maximum, floored at 1 | store-reported maximum |
| `n` (result) | the reassigned `batch_size` local used to slice `objs` into chunks | effective chunk size |

`bulk_batch_size` is an UNCHANGED callee (`django/db/backends/base/operations.py:BaseDatabaseOperations.bulk_batch_size`). The patch does not change it; its result is captured by the model as the plain input `maxBatchSize`. Therefore NO axiom is needed — see §3.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

| repo reality | Lean carrier | bijection |
|---|---|---|
| `batch_size` : non-negative `int` or `None` | `Nat` | `None`/`0 ↔ 0` (the Python `if batch_size:` truthiness test maps `None` and `0` alike to the "unspecified" branch); positive int `k ↔ k` |
| `max(ops.bulk_batch_size(fields, objs), 1)` : `int ≥ 1` | `Nat` with `require maxBatchSize ≥ 1` | exact; the `max(…, 1)` floor IS the `require` precondition |
| effective `batch_size` (post-assignment) | `Nat` (result `n`) | exact |
| `min(a, b)` | `min a b` (`Nat.min`) | identical: numeric minimum |
| `x if c else y` (Python conditional expr) | `if c then x else y` | identical control |
| `if batch_size:` (truthiness) | `if batchSize = 0 then … else …` | `batch_size` is a count ≥ 0, so truthiness ≡ `≠ 0`; the model tests `= 0` and swaps the branches accordingly |

## 3. Callee provenance

`bulk_batch_size(fields, objs)` (the DB backend's compatible-row-count estimate)
is UNCHANGED by the patch. Both prepatch and postpatch compute
`max_batch_size = max(ops.bulk_batch_size(fields, objs), 1)` identically; only the
combination of that value with the caller's request changes. Because the callee's
result is the same on both sides of the fix, it is abstracted as the plain input
`maxBatchSize` (tagged **R** in refinement.md — an abstracted-input refinement),
NOT axiomatized. There is therefore no `axiom_check.py` for this bundle. The
`max(…, 1)` floor is captured by `require maxBatchSize ≥ 1`.

## 4. G-CONF fuzz seed

`conformance_check.py` seeds with **11951**. The R/I shadow is the modeled
formula `maxBatchSize if batchSize == 0 else min(batchSize, maxBatchSize)`; the
oracle is the patched source line transliterated verbatim
(`min(batch_size, max_batch_size) if batch_size else max_batch_size`). The DB
callee `bulk_batch_size` is abstracted as the `maxBatchSize` input and fuzzed
directly over `maxBatchSize ≥ 1`. SHADOW vs ORACLE are differential-tested over
fuzzed `(batchSize, maxBatchSize)` pairs (plus boundary cases); exit 0 iff zero
disagreements.
