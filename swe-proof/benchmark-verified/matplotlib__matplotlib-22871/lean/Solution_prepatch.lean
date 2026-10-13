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
  -- Pre-patch behavior: whenever the varying level is one of the two coarsest
  -- components, the summary label is hidden UNCONDITIONALLY — without checking
  -- whether the value `1` actually occurs in that component. This hides the
  -- summary even when no start-of-year tick is present.
  let mut level : Nat := 5
  let mut showOffset : Bool := s0
  for lvl in levels do
    let column := colVals td lvl
    if 1 < column.dedup.length then
      level := lvl
      if decide (lvl < 2) then
        showOffset := false
      return (level, showOffset)
    else if lvl = 0 then
      level := 5
  return (level, showOffset)
-- impl-end

-- proof-start
theorem correct_tickOffset :
    ∀ (td : List (List Nat)) (s0 : Bool),
      problem_spec_tickOffset td s0 (implementation_tickOffset td s0) := by
  sorry   -- LEFT FOR THE PROOF AGENT — construction agent does NOT close this
-- proof-end
