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
  -- Pre-patch behavior: superseded systems are deleted from `blocks` and
  -- `numBlocks` by running index WHILE the scan is still in progress, so those
  -- two collections shrink underneath the loop counter; `repBlocks` is pruned
  -- afterwards by value. Once two systems are superseded the running index no
  -- longer addresses the intended entries, deleting the wrong rows (or none),
  -- and the three collections fall out of alignment.
  let mut blocks' := blocks
  let mut numBlocks' := numBlocks
  let mut toRemove : List (Finset Nat) := []
  let mut minimal := true
  let mut i := 0
  for r in repBlocks do
    if supersededBy rep r then
      blocks' := blocks'.eraseIdx i
      numBlocks' := numBlocks'.eraseIdx i
      toRemove := toRemove ++ [r]
    else if dominates rep r then
      minimal := false
      break
    i := i + 1
  let repBlocks' := repBlocks.filter (fun r => !(toRemove.contains r))
  if minimal && !(numBlocks'.contains numBlock) then
    return (blocks' ++ [block], numBlocks' ++ [numBlock], repBlocks' ++ [rep])
  else
    return (blocks', numBlocks', repBlocks')
-- impl-end

-- proof-start
theorem correct_pruneSystems :
    ∀ (blocks : List (List Int)) (numBlocks : List (List Nat)) (repBlocks : List (Finset Nat))
      (block : List Int) (numBlock : List Nat) (rep : Finset Nat),
      problem_spec_pruneSystems blocks numBlocks repBlocks block numBlock rep
        (implementation_pruneSystems blocks numBlocks repBlocks block numBlock rep) := by
  sorry   -- carries the gold proof body; UNCLOSABLE against the buggy impl (G-DIFF)
-- proof-end
