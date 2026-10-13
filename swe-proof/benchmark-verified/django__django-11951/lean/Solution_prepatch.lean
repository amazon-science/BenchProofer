import Mathlib
-- imports-end

/-!
Splitting a collection of objects into the consecutive batches that a bulk
operation will process one at a time.

Two sizes constrain the batching:

* a caller-supplied requested size, which may be left unset (modeled as the value
  `0`, the "no request" marker);
* a compatible maximum size that the storage backend can handle for the objects
  in question. This compatible maximum is taken as given here (it is computed
  elsewhere from the objects and their fields) and is normalized to be at least
  `1`, so a usable batch size always exists.

The effective per-batch size is then:

* the compatible maximum, when the caller requested no particular size;
* otherwise the smaller of the requested size and the compatible maximum — a
  request never enlarges a batch beyond what the backend can compatibly handle,
  but a request smaller than the maximum is honored.

Given that effective size, the objects are partitioned into consecutive,
non-overlapping batches in order: each batch holds up to the effective size many
objects, the next begins exactly where the previous ended, and the final batch
holds whatever remains. The number and contents of these batches are fully
determined by the inputs.

The behavior is stated abstractly as an input→output relation; the
implementation and correctness proof are supplied separately.
-/

-- axioms-start
-- No unchanged dependency callee requires a contract. The only outside operation
-- used here — obtaining the backend's compatible maximum batch size — has its
-- result supplied as an input (`rawMax`); the size selection and the partitioning
-- of the objects are spelled out concretely below.
-- axioms-end

-- pure-start
/-- The effective per-batch size. `batchSize = 0` models "no size requested": the
compatible maximum (normalized to at least `1`) is used. Otherwise the smaller of
the requested size and the compatible maximum is used, so a request can shrink a
batch but never enlarge it past the compatible maximum. The result is always
`≥ 1`. -/
def effectiveBatchSize (batchSize rawMax : Nat) : Nat :=
  let maxBatchSize := max rawMax 1
  if batchSize = 0 then maxBatchSize else min batchSize maxBatchSize

/-- The number of consecutive batches of size `eff` needed to cover `n` objects,
i.e. `⌈n / eff⌉` for `eff ≥ 1` (the count of start offsets `0, eff, 2·eff, …`
that are `< n`). -/
def batchCount (eff n : Nat) : Nat := (n + eff - 1) / eff

/-- The consecutive batches `objs` is split into, each holding up to `eff`
elements: batch `k` is the slice of `objs` starting at offset `k · eff` and
spanning `eff` elements. There are `batchCount eff objs.length` batches. -/
def chunkBatches (eff : Nat) (objs : List α) : List (List α) :=
  (List.range (batchCount eff objs.length)).map (fun k => (objs.drop (k * eff)).take eff)
-- pure-end

-- post-conditions-start
/-- Input→output relation for splitting `objs` into bulk batches.

Inputs:
* `batchSize` — the caller-requested batch size (`0` = unset);
* `rawMax`    — the backend's compatible maximum batch size (taken as given);
* `objs`      — the objects to partition.

The result is the consecutive partition of `objs` into batches whose size is the
effective batch size derived from `batchSize` and `rawMax`. The whole output is
pinned to the inputs. -/
def problem_spec_splitBatches (batchSize rawMax : Nat) (objs : List α)
    (result : List (List α)) : Prop :=
  result = chunkBatches (effectiveBatchSize batchSize rawMax) objs
-- post-conditions-end

-- impl-start
-- PRE-PATCH skeleton (the bug): a non-zero requested size is used verbatim and
-- can exceed the compatible maximum, instead of being clamped to it. Only an
-- unset request (`0`) falls back to the compatible maximum. This produces fewer,
-- larger batches than the spec demands whenever `0 < batchSize` and
-- `maxBatchSize < batchSize`, contradicting `result = chunkBatches
-- (effectiveBatchSize batchSize rawMax) objs`.
def implementation_splitBatches (batchSize rawMax : Nat) (objs : List α) :
    List (List α) := Id.run do
  -- The compatible maximum, normalized to at least one usable slot.
  let maxBatchSize := max rawMax 1
  -- BUG: a requested size overrides the compatible maximum entirely.
  let eff := if batchSize = 0 then maxBatchSize else batchSize
  let mut batches : List (List α) := []
  for k in [0:batchCount eff objs.length] do
    batches := batches ++ [(objs.drop (k * eff)).take eff]
  return batches
-- impl-end

-- proof-start
theorem correct_splitBatches :
    ∀ {α : Type} (batchSize rawMax : Nat) (objs : List α),
      problem_spec_splitBatches batchSize rawMax objs
        (implementation_splitBatches batchSize rawMax objs) := by
  sorry
-- proof-end
