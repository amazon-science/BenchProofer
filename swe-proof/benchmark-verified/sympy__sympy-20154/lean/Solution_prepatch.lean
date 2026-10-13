import Mathlib
-- imports-end

/-!
A generator computes a sequence of intermediate states (here, integer
partitions, each represented as a finite map from a part-value to its
multiplicity) by repeatedly advancing a working state. A consumer that drains
the generator into a concrete list expects the materialized list to contain, at
each position, the state that was current when that position was produced — in
the same order, and one entry per produced state.

A partition is modeled as `List (Nat × Nat)`: an association list pairing a
part-value with the number of copies of it in that partition (e.g. the partition
`{2: 3}` ↦ `[(2, 3)]`). The generated sequence of partitions is the input
carrier `states`; materialization relates the produced list to it position-wise.
-/

-- axioms-start
-- No unchanged callee is consumed: the generated state sequence is taken as the
-- input carrier, and materialization is modeled deeply (position-wise), so there
-- is nothing to axiomatize.
-- axioms-end

-- pure-start
/-- A single produced state: an integer partition as a multiplicity map
(part-value ↦ count). -/
abbrev PartMap := List (Nat × Nat)
-- pure-end

-- post-conditions-start
/-- Materializing the produced sequence `states` into `result`:
* `result` has exactly one entry per produced state (count preserved); and
* the entry at each position is the state produced at that position, in order.
Together these pin `result` to be `states` element-for-element — every produced
state appears, distinctly, at its own position. -/
def problem_spec_partitions (states : List PartMap) (result : List PartMap) : Prop :=
  result.length = states.length ∧
  (∀ i, i < states.length → result.getD i [] = states.getD i [])
-- post-conditions-end

-- impl-start
def implementation_partitions (states : List PartMap) : List PartMap := Id.run do
  let mut out : List PartMap := []
  for _s in states do
    -- bug: each emitted entry observes the single shared working state, which
    -- by the time the list is read holds the final produced value
    out := out ++ [states.getLastD []]
  return out
-- impl-end

-- proof-start
theorem correct_partitions :
    ∀ (states : List PartMap),
      problem_spec_partitions states (implementation_partitions states) := by
  sorry
-- proof-end
