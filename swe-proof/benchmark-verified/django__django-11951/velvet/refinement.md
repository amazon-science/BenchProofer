# refinement.md — django__django-11951

Correspondence between `Solution.lean`'s `effectiveBatchSize` impl and
`patch.diff` (the gold patch caps the caller-requested batch size at the
database-compatible maximum). `patch.diff` is the gold verbatim (applies at
base_commit, resolves — G-RESOLVE).

## A. The corrected derivation — `_batched_insert`'s `batch_size`

Gold hunk:
```
         ops = connections[self.db].ops
-        batch_size = (batch_size or max(ops.bulk_batch_size(fields, objs), 1))
+        max_batch_size = max(ops.bulk_batch_size(fields, objs), 1)
+        batch_size = min(batch_size, max_batch_size) if batch_size else max_batch_size
```

| # | Solution.lean impl op (`effectiveBatchSize`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | param `batchSize : Nat` | the `batch_size` arg (0/None ⇒ unspecified) | R | `int|None` ↔ `Nat`, `None`/`0 ↔ 0` (Python truthiness; mapping.md §2). |
| A2 | param `maxBatchSize : Nat` with `require maxBatchSize ≥ 1` | `max_batch_size = max(ops.bulk_batch_size(fields, objs), 1)` | R | UNCHANGED callee result abstracted as a plain input (mapping.md §3); the `max(…, 1)` floor IS the `require`. Identical on both sides of the fix ⇒ abstracted, NOT axiomatized. |
| A3 | `if batchSize = 0 then return maxBatchSize` | `… else max_batch_size` (the `else` of `if batch_size`) | I | identical: no request ⇒ use the store maximum. Truthiness `not batch_size` ↔ `batchSize = 0`. |
| A4 | `else return min batchSize maxBatchSize` | `min(batch_size, max_batch_size) if batch_size` (the `then` of `if batch_size`) | I | identical: a request is capped at the maximum — the smaller wins. `min` ↔ `Nat.min`. |

No A (axiom) steps; no kind-3 (changed inexpressible) steps. The DB callee
`bulk_batch_size` is an **R-abstracted input** (its result is `maxBatchSize`,
identical pre/post-fix), not a consumed axiom — hence no `axiom_check.py`. The
min/max arithmetic combining request and maximum is the changed logic, modeled
deeply and tagged **I**.

## B. verify(Solution) ⇒ resolved

`effectiveBatchSize` verifies only if
`(batchSize = 0 → n = maxBatchSize) ∧ (batchSize > 0 → n = min batchSize maxBatchSize)`
(A3–A4). By R (mapping.md §2) the verified result equals the patched
`min(batch_size, max_batch_size) if batch_size else max_batch_size` on the real
arguments. The F2P test
(`test_explicit_batch_size_respects_max_batch_size`) requests
`batch_size = max_batch_size + 1` and asserts the number of queries equals
`ceil(len(objs) / max_batch_size)` — i.e. the effective chunk size was capped at
`max_batch_size`, exactly what the spec pins via the `min` in the
`batchSize > 0` clause.

The prepatch impl returns the raw `batchSize` in the non-zero branch against the
byte-identical spec, leaving the unsolved goal `batchSize = min batchSize
maxBatchSize` (under `batchSize > 0`), which fails whenever `batchSize >
maxBatchSize` (G-DIFF) — precisely the cap-ignoring bug: the caller's request
overrode the store maximum. The Lean error reports the discriminating
counterexample `batchSize - maxBatchSize ≥ 1`.

G-CONF differential-tests the R/I shadow (the modeled formula) against the
patched source line over fuzzed `(batchSize, maxBatchSize)` pairs with
`maxBatchSize ≥ 1` (seed 11951). No trust points beyond the type bijection
(mapping.md §2): there are no axioms.
