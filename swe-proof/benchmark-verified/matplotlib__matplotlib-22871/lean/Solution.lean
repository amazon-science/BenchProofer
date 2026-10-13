import Mathlib
-- imports-end

/-!
Choosing the calendar resolution of a set of tick dates, and whether a separate
higher-level summary label (such as the year) should be displayed alongside the
ticks.

Each tick has a calendar breakdown into six ordered components, from coarsest to
finest: year, month, day, hour, minute, second. Given the breakdowns of all the
ticks we decide two things:

* the LEVEL — the finest of these components that is not constant across the
  ticks (scanning from finest to coarsest, the first component whose values are
  not all equal). If every component is constant across the ticks, the level is
  taken to be the finest one.
* whether to DISPLAY the separate summary label. It is displayed by default. It
  is hidden only when the varying level is one of the two coarsest components
  (year or month) AND the value `1` occurs among that component across the ticks
  — i.e. a start-of-year tick is already present, so the summary would be
  redundant. In particular, when a coarse component varies but never takes the
  value `1`, the summary label remains displayed.

We model this as an input→output relation
  (the per-tick calendar breakdowns, the default display flag)
      ↦ (the chosen level, the resulting display flag).
The implementation and correctness proof are supplied separately.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The per-tick
-- calendar breakdowns are taken as an opaque INPUT (each tick is a list of its
-- six calendar components); the distinct-value test over a component and the
-- membership test for the value `1` are modeled directly (deeply), so no
-- `opaque`/`axiom` callee contract is needed.
-- axioms-end

-- pure-start
/-- The values that calendar component `j` takes across all the ticks. -/
def colVals (td : List (List Nat)) (j : Nat) : List Nat :=
  td.map (fun r => r.getD j 0)

/-- How many DISTINCT values component `j` takes across the ticks. -/
def colDistinct (td : List (List Nat)) (j : Nat) : Nat :=
  (colVals td j).dedup.length

/-- Whether the value `1` occurs in component `j` across the ticks. -/
def colHasOne (td : List (List Nat)) (j : Nat) : Bool :=
  (colVals td j).contains 1

/-- Component indices from finest (5 = second) to coarsest (0 = year). -/
def levels : List Nat := [5, 4, 3, 2, 1, 0]

/-- The chosen level: the first component (finest→coarsest) that is not constant
across the ticks; the finest component (5) if all components are constant. -/
def specLevel (td : List (List Nat)) : Nat :=
  (levels.find? (fun j => decide (1 < colDistinct td j))).getD 5

/-- The resulting display flag: the default flag `s0`, turned off only when the
varying level is one of the two coarsest components and the value `1` occurs in
that component. -/
def specShowOffset (td : List (List Nat)) (s0 : Bool) : Bool :=
  match levels.find? (fun j => decide (1 < colDistinct td j)) with
  | some j => if decide (j < 2) && colHasOne td j then false else s0
  | none => s0
-- pure-end

-- post-conditions-start
/-- The chosen level equals `specLevel` and the display flag equals
`specShowOffset`, each determined structurally from the per-tick calendar
breakdowns and the default flag. -/
def problem_spec_tickOffset
    (td : List (List Nat)) (s0 : Bool) (result : Nat × Bool) : Prop :=
  result.1 = specLevel td ∧ result.2 = specShowOffset td s0
-- post-conditions-end

-- impl-start
def implementation_tickOffset
    (td : List (List Nat)) (s0 : Bool) : Nat × Bool := Id.run do
  let mut level : Nat := 5
  let mut showOffset : Bool := s0
  for lvl in levels do
    let column := colVals td lvl
    if 1 < column.dedup.length then
      level := lvl
      if decide (lvl < 2) && column.contains 1 then
        showOffset := false
      return (level, showOffset)
    else if lvl = 0 then
      level := 5
  return (level, showOffset)
-- impl-end


-- proof-start
/-- The implementation loop, fully unfolded over the literal `levels` into a
pure nested-`if` term with NO monadic binds. -/
def runReduce (td : List (List Nat)) (s0 : Bool) : Nat × Bool :=
  if 1 < (colVals td 5).dedup.length then
    (5, if decide (5 < 2) && (colVals td 5).contains 1 then false else s0)
  else if 1 < (colVals td 4).dedup.length then
    (4, if decide (4 < 2) && (colVals td 4).contains 1 then false else s0)
  else if 1 < (colVals td 3).dedup.length then
    (3, if decide (3 < 2) && (colVals td 3).contains 1 then false else s0)
  else if 1 < (colVals td 2).dedup.length then
    (2, if decide (2 < 2) && (colVals td 2).contains 1 then false else s0)
  else if 1 < (colVals td 1).dedup.length then
    (1, if decide (1 < 2) && (colVals td 1).contains 1 then false else s0)
  else if 1 < (colVals td 0).dedup.length then
    (0, if decide (0 < 2) && (colVals td 0).contains 1 then false else s0)
  else (5, s0)

/-- `levels.find? (fun j => decide (1 < colDistinct td j))` unfolded over the
literal `levels` into an explicit nested-`if` term. -/
def findReduce (td : List (List Nat)) : Option Nat :=
  if 1 < colDistinct td 5 then some 5
  else if 1 < colDistinct td 4 then some 4
  else if 1 < colDistinct td 3 then some 3
  else if 1 < colDistinct td 2 then some 2
  else if 1 < colDistinct td 1 then some 1
  else if 1 < colDistinct td 0 then some 0
  else none

/-- Definitional bridge: the three column helpers unfold to their bodies. -/
theorem col_defeqs (td : List (List Nat)) (j : Nat) :
    colDistinct td j = (colVals td j).dedup.length ∧
    colHasOne td j = (colVals td j).contains 1 ∧
    colVals td j = td.map (fun r => r.getD j 0) := ⟨rfl, rfl, rfl⟩

/-- Spec normalization: the `find?` scan over the literal `levels` equals the
explicit nested-`if` term `findReduce`. -/
theorem find_to_nestedIf (td : List (List Nat)) :
    levels.find? (fun j => decide (1 < colDistinct td j)) = findReduce td := by
  simp only [levels, List.find?, findReduce]
  grind

/-- Implementation normalization (blocker fix): the `Id.run` loop reduces to the
pure nested-`if` term `runReduce`, eliminating every monadic bind up front. -/
theorem impl_to_nestedIf (td : List (List Nat)) (s0 : Bool) :
    implementation_tickOffset td s0 = runReduce td s0 := by
  simp only [implementation_tickOffset, levels, Id.run, runReduce,
    List.forIn_cons, List.forIn_nil, bind_pure_comp, map_pure, bind_assoc]
  by_cases h5 : 1 < (colVals td 5).dedup.length
  · simp only [h5, if_true]; split <;> rfl
  simp only [h5, if_false, ite_self, pure_bind]
  by_cases h4 : 1 < (colVals td 4).dedup.length
  · simp only [h4, if_true]; split <;> rfl
  simp only [h4, if_false, ite_self, pure_bind]
  by_cases h3 : 1 < (colVals td 3).dedup.length
  · simp only [h3, if_true]; split <;> rfl
  simp only [h3, if_false, ite_self, pure_bind]
  by_cases h2 : 1 < (colVals td 2).dedup.length
  · simp only [h2, if_true]; split <;> rfl
  simp only [h2, if_false, ite_self, pure_bind]
  by_cases h1 : 1 < (colVals td 1).dedup.length
  · simp only [h1, if_true]; split <;> rfl
  simp only [h1, if_false, ite_self, pure_bind]
  by_cases h0 : 1 < (colVals td 0).dedup.length
  · simp only [h0, if_true]; split <;> rfl
  simp only [h0, if_false, pure_bind]
  rfl

/-- Atom 1: the returned level equals `specLevel`. -/
theorem level_eq (td : List (List Nat)) (s0 : Bool) :
    (implementation_tickOffset td s0).1 = specLevel td := by
  rw [impl_to_nestedIf]
  unfold specLevel
  rw [find_to_nestedIf]
  unfold runReduce findReduce
  rw [(col_defeqs td 5).1, (col_defeqs td 4).1, (col_defeqs td 3).1,
      (col_defeqs td 2).1, (col_defeqs td 1).1, (col_defeqs td 0).1]
  split_ifs <;> rfl

/-- Atom 2: the returned display flag equals `specShowOffset`. -/
theorem show_eq (td : List (List Nat)) (s0 : Bool) :
    (implementation_tickOffset td s0).2 = specShowOffset td s0 := by
  rw [impl_to_nestedIf]
  rw [specShowOffset, find_to_nestedIf]
  simp only [runReduce, findReduce, colDistinct, colHasOne]
  split_ifs <;> simp_all

theorem correct_tickOffset :
    ∀ (td : List (List Nat)) (s0 : Bool),
      problem_spec_tickOffset td s0 (implementation_tickOffset td s0) := by
  intro td s0
  exact ⟨level_eq td s0, show_eq td s0⟩

-- proof-end
