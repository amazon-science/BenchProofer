import Mathlib
-- imports-end

/-!
Inserting a block of columns into a matrix.

A matrix is modelled by its dimensions together with its value accessor
`get i j` (row `i`, column `j`). Inserting the columns of a second matrix
`other` into a host matrix `self` at column position `pos` produces a new matrix
with `self.cols + other.cols` columns whose value at `(i, j)` is determined,
column-region by column-region, entirely from the two operands:

  * for a column strictly left of the insertion point the value is the host's
    own value at that very column;
  * for a column inside the inserted block the value is taken from `other`, at
    the column offset measured from the insertion point;
  * for a column to the right of the inserted block the value is again the
    host's, taken from the column it occupied before the block was inserted —
    i.e. the same column index shifted left by the width of the inserted block.

Every output column region is pinned to a specific input value, so no part of
the result is left free.
-/

-- axioms-start
-- No unchanged outside callee is consumed. Each region of the produced matrix
-- is read directly off one of the two input accessors at an index computed from
-- the inputs, so no `opaque`/`axiom` callee contract is needed.
-- axioms-end

-- pure-start
/-- A matrix: its row/column dimensions together with a value accessor
`get i j` giving the value at row `i`, column `j`. -/
structure Mat where
  rows : Nat
  cols : Nat
  get  : Nat → Nat → Int
-- pure-end

-- post-conditions-start
/-- The value of the column-inserted matrix at row `i`, column `j` is fully
pinned to the inputs, region by region:

  * a column left of the insertion point reads the host at the same column;
  * a column within the inserted block reads `other` at the offset from `pos`;
  * a column to the right of the block reads the host at that column shifted
    left by the inserted width.

All three regions partition every column index, so the result is determined for
every `(i, j)`. -/
def problem_spec_colInsert
    (self other : Mat) (pos i j : Nat) (result : Int) : Prop :=
  (j < pos → result = self.get i j) ∧
  (pos ≤ j ∧ j < pos + other.cols → result = other.get i (j - pos)) ∧
  (pos + other.cols ≤ j → result = self.get i (j - other.cols))
-- post-conditions-end

-- impl-start
def implementation_colInsert
    (self other : Mat) (pos i j : Nat) : Int := Id.run do
  if j < pos then
    return self.get i j
  if pos ≤ j ∧ j < pos + other.cols then
    return other.get i (j - pos)
  return self.get i (j - other.cols)
-- impl-end

-- proof-start
theorem correct_colInsert :
    ∀ (self other : Mat) (pos i j : Nat),
      problem_spec_colInsert self other pos i j
        (implementation_colInsert self other pos i j) := by
  intro self other pos i j
  unfold problem_spec_colInsert implementation_colInsert
  simp only [Id.run, bind, pure]
  refine ⟨?_, ?_, ?_⟩
  · intro h
    simp [h]
  · rintro ⟨h1, h2⟩
    have hlt : ¬ j < pos := by omega
    simp [hlt, h1, h2]
  · intro h
    have hlt : ¬ j < pos := by omega
    have hmid : ¬ (pos ≤ j ∧ j < pos + other.cols) := by omega
    simp [hlt, hmid]
-- proof-end
