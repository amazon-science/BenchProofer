import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The database-computed compatible maximum is taken as
--  a plain non-zero input — the operation under spec does not change how that
--  maximum is produced; the floor-at-one is captured by `require`.)
-- axioms-end

-- pure-start
-- (No pure helpers needed.)
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- When records are written to the store in chunks, two chunk-size figures meet:
   a size the caller may explicitly request, and a size the store reports as the
   largest it can accept in one round-trip. The caller's request is optional — a
   value of zero means "no explicit request, decide for me."

   The effective chunk size must always honour BOTH figures. When the caller
   makes no request, the store's reported maximum is used as-is. When the caller
   does request a size, that request must still be capped at the store's
   maximum — the smaller of the two wins — so a caller can never force a chunk
   larger than the store can handle.

   The reported maximum is read-only (not `mut`) and is always at least one (the
   store never reports a zero capacity); the requested size is read-only too. The
   operation derives a single size and mutates nothing (directive 5). Both inputs
   and the result are modeled as `Nat`. -/
method effectiveBatchSize (batchSize : Nat) (maxBatchSize : Nat) return (n : Nat)
  require maxBatchSize ≥ 1
  ensures (batchSize = 0 → n = maxBatchSize) ∧ (batchSize > 0 → n = min batchSize maxBatchSize)
  do
    -- impl-start
    if batchSize = 0 then
      return maxBatchSize
    else
      return min batchSize maxBatchSize
    -- impl-end

prove_correct effectiveBatchSize by
  loom_solve
