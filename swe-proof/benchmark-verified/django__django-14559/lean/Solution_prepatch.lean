import Mathlib
-- imports-end

/-!
Applying a batched bulk modification to a collection of stored records and
reporting how many stored rows were matched by the modification.

The records to modify are supplied as a sequence; each carries the identifier
of the stored row it stands for. The operation processes the sequence in
fixed-size batches: every batch issues a single set-based modification keyed on
the identifiers occurring in that batch, and a set-based modification matches
each distinct identifier at most once (so an identifier that appears more than
once within the same batch is still matched a single time).

The desired behavior is that the operation reports the total number of rows
matched across all batches: the sum, over the batches, of the count of distinct
identifiers in each batch. Because the tally is per batch, an identifier that
recurs within one batch contributes once, while an identifier that recurs across
two different batches contributes once per batch it lands in. When the input
sequence is empty the operation performs no modification and reports a matched
count of zero. The reported total is always present (a count is returned in
every case).
-/

-- axioms-start
-- No unchanged callee is consumed as an opaque carrier here: the per-batch
-- matched-row tally and the batching are modeled directly as total operations
-- over the identifier sequence (see the `pure` region). No callee property is
-- consumed by the correctness proof.
-- axioms-end

-- pure-start
/-- The number of rows matched by one batch's set-based modification: a set-based
match keyed on a multiset of identifiers matches each *distinct* identifier once,
so the per-batch tally is the number of distinct identifiers in the batch. -/
def batchMatched (batch : List Int) : Nat := batch.dedup.length

/-- The total number of rows matched when the identifier sequence is processed in
fixed-size batches: split the sequence into consecutive batches of size
`batchSize`, then sum each batch's distinct-identifier count. Front-recursive
shape paired with the accumulator loop in the implementation. -/
def batchedMatchCount (batchSize : Nat) (keys : List Int) : Nat :=
  (List.toChunks batchSize keys).foldl (fun acc batch => acc + batchMatched batch) 0
-- pure-end

-- post-conditions-start
/-- The reported result is always a present count, and that count equals the
total number of rows matched across the fixed-size batches: the sum over batches
of the distinct-identifier count of each batch. This fully pins the result —
both its presence and its value are determined by the identifier sequence and
the batch size. -/
def problem_spec_bulkUpdate
    (keys : List Int) (batchSize : Nat) (result : Option Nat) : Prop :=
  result = some (batchedMatchCount batchSize keys)
-- post-conditions-end

-- impl-start
def implementation_bulkUpdate (keys : List Int) (batchSize : Nat) : Option Nat := Id.run do
  if keys.isEmpty then
    return none
  let batches := List.toChunks batchSize keys
  let mut rowsUpdated := 0
  for batch in batches do
    rowsUpdated := rowsUpdated + batch.dedup.length
  return none
-- impl-end

-- proof-start
theorem correct_bulkUpdate :
    ∀ (keys : List Int) (batchSize : Nat), 1 ≤ batchSize →
      problem_spec_bulkUpdate keys batchSize
        (implementation_bulkUpdate keys batchSize) := by
  sorry
-- proof-end
