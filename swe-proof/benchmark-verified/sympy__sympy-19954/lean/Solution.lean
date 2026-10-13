import Mathlib
-- imports-end

/-!
Maintaining a collection of candidate partition systems for a transitive action,
keeping only the coarsest ones.

We track three parallel collections of equal length, one entry per partition
system retained so far:

* `blocks`   — a concrete description of each retained system;
* `numBlocks` — a canonical numbering of each retained system;
* `repBlocks` — the representative cell (the set containing the point `0`) of
  each retained system.

A fresh candidate arrives, described by the same three pieces of data
(`block`, `numBlock`, `rep`). We compare its representative cell `rep` against
the representative cell `r` of every retained system, in order:

* if a retained `r` strictly contains `rep` (more points, and every point of
  `rep` lies in `r`), that retained system is superseded by the candidate and is
  marked for removal;
* if instead a retained `r` is strictly contained in `rep`, then the candidate
  is itself superseded; the candidate is rejected and no further comparisons are
  made;
* otherwise the retained system is left untouched.

After the scan, every system marked for removal is dropped from ALL THREE
collections together, so the three collections stay aligned to the same set of
surviving indices. The candidate is then appended to all three collections
exactly when it was not rejected AND its numbering does not already appear among
the surviving numberings.

The essential guarantee is alignment: a system is removed from `blocks`,
`numBlocks` and `repBlocks` at the same indices, never from one collection by
position while another is pruned by value, so the three collections describe the
same surviving systems in the same order.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The candidate
-- data (`block`, `numBlock`, `rep`) and the retained collections are the inputs;
-- the comparison, the aligned removal and the conditional append are modeled
-- DEEPLY over those inputs, so no `opaque`/`axiom` callee contract is needed.
-- axioms-end

-- pure-start
/-- `rep` is strictly coarser-dominated by `r`: `r` has strictly more points and
contains every point of `rep`. A retained system whose representative cell `r`
satisfies this against the candidate's `rep` is superseded by the candidate. -/
def supersededBy (rep r : Finset Nat) : Bool := r.card > rep.card && rep ⊆ r

/-- The candidate's `rep` is itself dominated by `r`: `r` has strictly fewer
points and all of them lie in `rep`. -/
def dominates (rep r : Finset Nat) : Bool := r.card < rep.card && r ⊆ rep

/-- Scan the retained representative cells in order, producing the per-index
removal flags together with whether the candidate survives the scan.
The boolean is `true` while the candidate is still viable. On encountering a
representative cell that dominates the candidate, the candidate is rejected and
the scan stops; all remaining indices are left unflagged. -/
def scanReps (rep : Finset Nat) : List (Finset Nat) → (List Bool × Bool)
  | [] => ([], true)
  | r :: rs =>
    if supersededBy rep r then
      let (m, keep) := scanReps rep rs
      (true :: m, keep)
    else if dominates rep r then
      (false :: List.replicate rs.length false, false)
    else
      let (m, keep) := scanReps rep rs
      (false :: m, keep)

/-- Drop every entry of `xs` whose aligned mask flag is `true`. -/
def dropFlagged {α : Type} : List α → List Bool → List α
  | [], _ => []
  | a :: as, [] => a :: as
  | a :: as, b :: bs => if b then dropFlagged as bs else a :: dropFlagged as bs

/-- The full update step: scan, prune all three collections by the same mask,
then conditionally append the candidate. -/
def pruneSystems
    (blocks : List (List Int)) (numBlocks : List (List Nat)) (repBlocks : List (Finset Nat))
    (block : List Int) (numBlock : List Nat) (rep : Finset Nat) :
    List (List Int) × List (List Nat) × List (Finset Nat) :=
  let (mask, candidateKept) := scanReps rep repBlocks
  let blocks'   := dropFlagged blocks mask
  let numBlocks' := dropFlagged numBlocks mask
  let repBlocks' := dropFlagged repBlocks mask
  if candidateKept && !(numBlocks'.contains numBlock) then
    (blocks' ++ [block], numBlocks' ++ [numBlock], repBlocks' ++ [rep])
  else
    (blocks', numBlocks', repBlocks')
-- pure-end

-- post-conditions-start
/-- The result is exactly the aligned-pruned-then-conditionally-appended update
of the three collections dictated by the rule above. -/
def problem_spec_pruneSystems
    (blocks : List (List Int)) (numBlocks : List (List Nat)) (repBlocks : List (Finset Nat))
    (block : List Int) (numBlock : List Nat) (rep : Finset Nat)
    (result : List (List Int) × List (List Nat) × List (Finset Nat)) : Prop :=
  result = pruneSystems blocks numBlocks repBlocks block numBlock rep
-- post-conditions-end

-- impl-start
def implementation_pruneSystems
    (blocks : List (List Int)) (numBlocks : List (List Nat)) (repBlocks : List (Finset Nat))
    (block : List Int) (numBlock : List Nat) (rep : Finset Nat) :
    List (List Int) × List (List Nat) × List (Finset Nat) := Id.run do
  let mut minimal := true
  let mut mask : List Bool := []
  for r in repBlocks do
    if r.card > rep.card && rep ⊆ r then
      mask := mask ++ [true]
    else if r.card < rep.card && r ⊆ rep then
      minimal := false
      break
    else
      mask := mask ++ [false]
  mask := mask ++ List.replicate (repBlocks.length - mask.length) false
  let blocks' := dropFlagged blocks mask
  let numBlocks' := dropFlagged numBlocks mask
  let repBlocks' := dropFlagged repBlocks mask
  if minimal && !(numBlocks'.contains numBlock) then
    return (blocks' ++ [block], numBlocks' ++ [numBlock], repBlocks' ++ [rep])
  else
    return (blocks', numBlocks', repBlocks')
-- impl-end


-- proof-start
/-- Loop invariant relating the running `(mask, minimal)` to `scanReps` for a
processed prefix `pre` with remaining suffix `suf`. While `minimal = true`, no
dominating cell has been seen in `pre`, `mask` equals the mask-part `scanReps`
produces on `pre`, and `scanReps` on the full list splits as the accumulated
mask followed by the suffix's scan. Once `minimal = false`, a dominating cell
was hit (the loop broke) and the full scan is the accumulated mask padded with
`false` over the remaining suffix. -/
def LoopState (rep : Finset Nat) (pre suf : List (Finset Nat))
    (mask : List Bool) (minimal : Bool) : Prop :=
  (minimal = true →
      mask = (scanReps rep pre).1 ∧
      scanReps rep (pre ++ suf) = (mask ++ (scanReps rep suf).1, (scanReps rep suf).2)) ∧
  (minimal = false →
      scanReps rep (pre ++ suf) = (mask ++ List.replicate suf.length false, false))

theorem scanReps_cons_super (rep r : Finset Nat) (rs : List (Finset Nat))
    (h : supersededBy rep r = true) :
    scanReps rep (r :: rs) = (true :: (scanReps rep rs).1, (scanReps rep rs).2) := by
  simp only [scanReps, h, if_true]

theorem scanReps_cons_dom (rep r : Finset Nat) (rs : List (Finset Nat))
    (h1 : supersededBy rep r = false) (h2 : dominates rep r = true) :
    scanReps rep (r :: rs) = (false :: List.replicate rs.length false, false) := by
  unfold scanReps
  simp only [h1, h2, if_false, if_true, Bool.false_eq_true]

theorem scanReps_cons_neither (rep r : Finset Nat) (rs : List (Finset Nat))
    (h1 : supersededBy rep r = false) (h2 : dominates rep r = false) :
    scanReps rep (r :: rs) = (false :: (scanReps rep rs).1, (scanReps rep rs).2) := by
  conv_lhs => rw [scanReps]
  simp only [h1, h2, Bool.false_eq_true, if_false]

theorem scanReps_mask_length (rep : Finset Nat) (rs : List (Finset Nat)) :
    (scanReps rep rs).1.length = rs.length := by
  induction rs with
  | nil => rfl
  | cons r rs ih =>
    by_cases hs : supersededBy rep r = true
    · rw [scanReps_cons_super rep r rs hs]
      simp [ih]
    · simp only [Bool.not_eq_true] at hs
      by_cases hd : dominates rep r = true
      · rw [scanReps_cons_dom rep r rs hs hd]
        simp
      · simp only [Bool.not_eq_true] at hd
        rw [scanReps_cons_neither rep r rs hs hd]
        simp [ih]

theorem forIn_reifies_scan (rep : Finset Nat) :
    ∀ (L : List (Finset Nat)) (acc : List Bool),
      (Id.run do
        let mut minimal := true
        let mut mask : List Bool := acc
        for r in L do
          if r.card > rep.card && rep ⊆ r then
            mask := mask ++ [true]
          else if r.card < rep.card && r ⊆ rep then
            minimal := false
            break
          else
            mask := mask ++ [false]
        mask := mask ++ List.replicate (acc.length + L.length - mask.length) false
        return (mask, minimal))
        = (acc ++ (scanReps rep L).1, (scanReps rep L).2) := by
  intro L
  induction L with
  | nil => intro acc; simp [scanReps, Id.run, bind, pure]
  | cons r rs ih =>
    intro acc
    simp only [List.forIn_cons, bind, pure, Id.run]
    split_ifs with h1 h2
    · -- superseded: mask ++ [true], continue
      have hs : supersededBy rep r = true := h1
      rw [scanReps_cons_super rep r rs hs]
      have hih := ih (acc ++ [true])
      simp only [bind, pure, Id.run] at hih
      dsimp only
      rw [show acc.length + (r::rs).length = (acc++[true]).length + rs.length by simp; omega]
      rw [hih]; simp [List.append_assoc]
    · -- dominated: break
      have hs : supersededBy rep r = false := by
        simpa [supersededBy] using h1
      have hd : dominates rep r = true := by
        simpa [dominates] using h2
      rw [scanReps_cons_dom rep r rs hs hd]
      dsimp only
      rw [show acc.length + (r::rs).length - acc.length = rs.length + 1 by simp]
      rw [List.replicate_succ]
    · -- neither: mask ++ [false], continue
      have hs : supersededBy rep r = false := by
        simpa [supersededBy] using h1
      have hnd : dominates rep r = false := by
        simpa [dominates] using h2
      rw [scanReps_cons_neither rep r rs hs hnd]
      have hih := ih (acc ++ [false])
      simp only [bind, pure, Id.run] at hih
      dsimp only
      rw [show acc.length + (r::rs).length = (acc++[false]).length + rs.length by simp; omega]
      rw [hih]; simp [List.append_assoc]

theorem loop_scan_eq (rep : Finset Nat) (repBlocks : List (Finset Nat)) :
    (Id.run do
      let mut minimal := true
      let mut mask : List Bool := []
      for r in repBlocks do
        if r.card > rep.card && rep ⊆ r then
          mask := mask ++ [true]
        else if r.card < rep.card && r ⊆ rep then
          minimal := false
          break
        else
          mask := mask ++ [false]
      mask := mask ++ List.replicate (repBlocks.length - mask.length) false
      return (mask, minimal))
      = scanReps rep repBlocks := by
  have h := forIn_reifies_scan rep repBlocks []
  simpa using h

theorem tail_eq (blocks : List (List Int)) (numBlocks : List (List Nat))
    (repBlocks : List (Finset Nat)) (block : List Int) (numBlock : List Nat) (rep : Finset Nat)
    (hloop : (Id.run do
      let mut minimal := true
      let mut mask : List Bool := []
      for r in repBlocks do
        if r.card > rep.card && rep ⊆ r then
          mask := mask ++ [true]
        else if r.card < rep.card && r ⊆ rep then
          minimal := false
          break
        else
          mask := mask ++ [false]
      mask := mask ++ List.replicate (repBlocks.length - mask.length) false
      return (mask, minimal))
      = scanReps rep repBlocks) :
    implementation_pruneSystems blocks numBlocks repBlocks block numBlock rep
      = pruneSystems blocks numBlocks repBlocks block numBlock rep := by
  unfold implementation_pruneSystems pruneSystems
  rw [← hloop]
  rfl

theorem correct_pruneSystems :
    ∀ (blocks : List (List Int)) (numBlocks : List (List Nat)) (repBlocks : List (Finset Nat))
      (block : List Int) (numBlock : List Nat) (rep : Finset Nat),
      problem_spec_pruneSystems blocks numBlocks repBlocks block numBlock rep
        (implementation_pruneSystems blocks numBlocks repBlocks block numBlock rep) := by
  intro blocks numBlocks repBlocks block numBlock rep
  unfold problem_spec_pruneSystems
  exact tail_eq blocks numBlocks repBlocks block numBlock rep (loop_scan_eq rep repBlocks)

-- proof-end
