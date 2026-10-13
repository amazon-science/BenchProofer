import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- No consumed axioms. Gathering the walk and recording an independent per-step
-- snapshot are pure value/structure logic, modelled deeply below. The
-- record-duplication primitive the enumerator builds on is validated against
-- its real semantics out-of-band by axiom_check.py (G-AX) as an A-reference,
-- not consumed here.
-- axioms-end

-- pure-start
/- The working value recorded for step i. Successive steps genuinely change the
   working state, so the per-step values are pairwise distinct; modelled as the
   strictly-increasing value `i + 1`, so step i differs from step j whenever
   i ≠ j. This is exactly the observable an aliasing enumerator (whose gathered
   records all collapse to one final value) cannot reproduce. -/
def stateAt (i : Nat) : Int := (i : Int) + 1

@[grind] lemma stateAt_def (i : Nat) : stateAt i = (i : Int) + 1 := rfl

/- The gathered record list of an n-step walk: one independent per-step snapshot
   per step, element i being the working state as it was AT step i. Modelled as
   the per-step values laid out in order. -/
def walkSeq (n : Nat) : List Int := (List.range n).map (fun i => stateAt i)

@[grind] lemma walkSeq_length (n : Nat) : (walkSeq n).length = n := by
  simp [walkSeq]

@[grind] lemma walkSeq_get (n i : Nat) (h : i < n) :
    (walkSeq n)[i]! = stateAt i := by
  have hr : i < (List.range n).length := by simpa using h
  simp [walkSeq, List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hr,
    List.getElem_range]
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method gatherWalk (steps : Nat) return (out : List Int)
  ensures out.length = steps
  -- Record i recovers the working state AT ITS OWN step. Because `stateAt` is
  -- strictly increasing, the gathered records are pairwise different: this is
  -- precisely the per-step history that an aliasing enumerator -- whose gathered
  -- records all collapse onto the final state -- cannot satisfy.
  ensures ∀ i, i < steps → out[i]! = stateAt i
  do
    -- impl-start
    let mut result : List Int := []
    let mut i := steps
    while i > 0
      invariant 0 ≤ i ∧ i ≤ steps
      -- Every already-gathered record holds the snapshot of its OWN step -- an
      -- independent value that later steps never disturb. The tail `[i .. steps)`
      -- has been gathered so far (this loop walks the steps in reverse, each
      -- iteration prepending one freshly-captured per-step record).
      invariant result = (List.range' i (steps - i)).map (fun k => stateAt k)
      done_with i = 0
      decreasing i
    do
      -- Capture an INDEPENDENT snapshot of the working state for step `i - 1`
      -- (the snapshot step): the current per-step value is recorded by value, so
      -- a later mutation of the working state leaves this gathered record alone.
      let snap := stateAt (i - 1)
      result := snap :: result
      i := i - 1
    return result
    -- impl-end

/- The backward gather step: prepending step `i-1`'s snapshot to the records for
   `[i .. steps)` gives the records for `[i-1 .. steps)`. This is the single goal
   `loom_solve` leaves for the loop body. -/
lemma gather_step (steps i : Nat) (hi : 0 < i) (hle : i ≤ steps) :
    stateAt (i - 1) :: (List.range' i (steps - i)).map (fun k => stateAt k)
      = (List.range' (i - 1) (steps - (i - 1))).map (fun k => stateAt k) := by
  have h1 : steps - (i - 1) = (steps - i) + 1 := by omega
  have h2 : i - 1 + 1 = i := by omega
  rw [h1, List.range'_succ, List.map_cons, h2]

lemma gather_final (steps : Nat) :
    (List.range' 0 steps).map (fun k => stateAt k) = walkSeq steps := by
  simp [walkSeq, List.range_eq_range']

prove_correct gatherWalk by
  loom_solve
  subst result
  rw [gather_step steps i (by omega) (by omega)]
