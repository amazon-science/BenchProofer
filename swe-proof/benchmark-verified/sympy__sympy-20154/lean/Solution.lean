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
  for s in states do
    -- emit the state current at this step as its own entry
    out := out ++ [s]
  return out
-- impl-end

-- proof-start
/-- The append-accumulating `forIn` loop over `states`, generalized over the
accumulator, is just `init ++ states`. -/
theorem forIn_append_eq (states : List PartMap) (init : List PartMap) :
    (Id.run (forIn states init (fun s r =>
        (ForInStep.yield (r ++ [s]) : Id (ForInStep (List PartMap))))))
    = init ++ states := by
  induction states generalizing init with
  | nil => simp [Id.run, List.forIn_nil, pure]
  | cons a as ih =>
    rw [List.forIn_cons]
    simp only [Id.run, bind] at ih ⊢
    rw [ih]
    simp

theorem partitions_eq (states : List PartMap) :
    implementation_partitions states = states := by
  unfold implementation_partitions
  have h2 : (forIn states ([] : List PartMap) fun s r =>
        (do pure PUnit.unit; pure (ForInStep.yield (r ++ [s]))
          : Id (ForInStep (List PartMap))))
      = (forIn states ([] : List PartMap) fun s r =>
        (ForInStep.yield (r ++ [s]) : Id (ForInStep (List PartMap)))) := rfl
  show Id.run (forIn states ([] : List PartMap) fun s r =>
        (do pure PUnit.unit; pure (ForInStep.yield (r ++ [s]))
          : Id (ForInStep (List PartMap)))) = states
  rw [h2, forIn_append_eq]
  simp

theorem correct_partitions :
    ∀ (states : List PartMap),
      problem_spec_partitions states (implementation_partitions states) := by
  intro states
  unfold problem_spec_partitions
  rw [partitions_eq]
  exact ⟨rfl, fun i _ => rfl⟩
-- proof-end
