import Velvet.Std
-- imports-end

/- Total correctness: the real scoring loop runs a bounded number of rounds
   (a bounded `for` over the round count) and always terminates, so a
   diverging implementation must NOT satisfy this spec. Under partial
   correctness a non-terminating loop would discharge the postcondition
   vacuously — a spec-too-weak hole. -/
set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No consumed axioms. The buffering step `materialize` deeply models an
--  UNCHANGED community helper that turns a possibly-single-pass split source
--  into a re-readable one; it is an A-reference validated == the real helper by
--  axiom_check.py (G-AX), NOT a consumed axiom. Nothing else is axiomatized.)
-- axioms-end

-- pure-start
/- A cross-validation split source. `splits` is the full underlying sequence of
   train/test splits it represents (each split is an abstract token). A source
   may be *single-pass*: the first read returns `splits` and marks it
   `consumed`, after which every later read returns nothing. A `reusable` source
   always returns the full sequence and is never consumed. -/
abbrev Splits := List Nat

structure CvSource where
  splits   : Splits
  reusable : Bool
  consumed : Bool
  deriving Inhabited

/- The splits OBSERVED by one read of the source: a reusable source always
   yields the full sequence; a single-pass source yields it only while it has
   not yet been consumed, and the empty sequence thereafter. -/
def readObs (s : CvSource) : Splits :=
  if s.reusable then s.splits
  else if s.consumed then [] else s.splits

/- The source state AFTER one read: a reusable source is unchanged; a single-pass
   source becomes consumed once it has yielded its sequence. -/
def advance (s : CvSource) : CvSource :=
  if s.reusable then s
  else if s.consumed then s else { s with consumed := true }

/- Buffer a source into a re-readable one carrying the same split sequence:
   regardless of whether the input was single-pass, the result is `reusable`
   and unconsumed, so every read returns the full sequence. -/
def materialize (s : CvSource) : CvSource :=
  { splits := s.splits, reusable := true, consumed := false }

@[grind] lemma materialize_reusable (s : CvSource) : (materialize s).reusable = true := rfl
@[grind] lemma materialize_splits (s : CvSource) : (materialize s).splits = s.splits := rfl
@[grind] lemma materialize_consumed (s : CvSource) : (materialize s).consumed = false := rfl

@[grind] lemma readObs_reusable (s : CvSource) (h : s.reusable = true) :
    readObs s = s.splits := by simp [readObs, h]
@[grind] lemma advance_reusable (s : CvSource) (h : s.reusable = true) :
    advance s = s := by simp [advance, h]
@[grind] lemma advance_splits (s : CvSource) : (advance s).splits = s.splits := by
  unfold advance; split <;> [rfl; (split <;> rfl)]
@[grind] lemma advance_reusable_flag (s : CvSource) : (advance s).reusable = s.reusable := by
  unfold advance; split <;> [rfl; (split <;> rfl)]
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Run `k` consecutive scoring rounds against a cross-validation split `source`,
   recording the splits each round observes. The desired behaviour: EVERY one of
   the `k` rounds observes the full split sequence of `source` — independent of
   whether `source` is single-pass — so the recorded observations are the split
   sequence repeated `k` times. `source` is read-only (directive 5): the method
   does not mutate the caller's source. -/
method runScoringRounds (source : CvSource) (k : Nat) return (obs : List Splits)
  ensures obs = List.replicate k source.splits
  do
    -- impl-start
    let mut src := source
    let mut obs : List Splits := []
    let mut i := k
    while i > 0
      invariant 0 ≤ i ∧ i ≤ k
      invariant src.splits = source.splits
      done_with i = 0
      decreasing i
    do
      let o := readObs src
      src := advance src
      obs := o :: obs
      i := i - 1
    return obs
    -- impl-end

/- The backward-fold step: with one fewer round remaining, the running record
   gains one more full observation on the front. A reusable source observes its
   full sequence and is unchanged by a read, so the prepended element is exactly
   `source.splits`. This is the single goal `loom_solve` leaves for the body. -/
lemma replicate_step (a : Splits) (k i : Nat) (hi : 0 < i) (hle : i ≤ k) :
    List.replicate (k - (i - 1)) a = a :: List.replicate (k - i) a := by
  have h : k - (i - 1) = (k - i) + 1 := by omega
  rw [h, List.replicate_succ]

prove_correct runScoringRounds by
  loom_solve
