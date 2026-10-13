import Mathlib
-- imports-end

/-!
Joining two matrices edge-to-edge.

A matrix is modelled by its row/column dimensions, a value accessor
`get i j` (row `i`, column `j`), and a `kind` tag identifying the concrete
class of matrix it is (different in-memory representations of a matrix are
different kinds; two matrices can hold the same values yet be of different
kinds).

Two joins are described:

* a **horizontal join** places `other` to the right of `self`, producing a matrix
  `[self other]`. When `self` has no columns it contributes no entries, so the
  join has `other`'s shape and entries; otherwise the result has
  `self.cols + other.cols` columns and every entry is read from `self` in the
  left block and from `other` in the right block.

* a **vertical join** places `other` beneath `self`, producing a matrix
  `[self; other]`. When `self` has no rows it contributes no entries, so the
  join has `other`'s shape and entries; otherwise the result has
  `self.rows + other.rows` rows and every entry is read from `self` in the top
  block and from `other` in the bottom block.

In every case the result is a matrix of the same kind as `self` (joining is an
operation OF the left/top operand: even when `self` contributes no entries the
result is a `self`-kind matrix holding `other`'s values, never `other` itself),
and the result's dimensions and every entry are pinned to the two operands, so
no component of the output is left free. A null-dimensioned operand never
silently discards the other operand's contribution.
-/

-- axioms-start
-- No unchanged outside callee is consumed. Both joins are modelled deeply: each
-- output entry is read directly off one of the two input accessors at an index
-- computed from the inputs, so no `opaque`/`axiom` callee contract is needed.
-- axioms-end

-- pure-start
/-- A matrix: its row/column dimensions, a value accessor `get i j` giving the
value at row `i`, column `j`, and a `kind` tag identifying the concrete class
of matrix it is. -/
structure Mat where
  rows : Nat
  cols : Nat
  get  : Nat → Nat → Int
  kind : Nat

/-- A matrix of the given height and kind with no columns; its accessor is
identically 0. -/
def zeroColsMat (rows kind : Nat) : Mat := ⟨rows, 0, fun _ _ => 0, kind⟩

/-- A matrix of the given width and kind with no rows; its accessor is
identically 0. -/
def zeroRowsMat (cols kind : Nat) : Mat := ⟨0, cols, fun _ _ => 0, kind⟩

/-- `A` with `B` placed to its right: width `A.cols + B.cols`; the left block
reads from `A`, the right block from `B` at the offset past `A.cols`. The
result is of `A`'s kind. -/
def concatCols (A B : Mat) : Mat :=
  ⟨A.rows, A.cols + B.cols,
    fun i j => if j < A.cols then A.get i j else B.get i (j - A.cols),
    A.kind⟩

/-- `A` with `B` placed beneath it: height `A.rows + B.rows`; the top block reads
from `A`, the bottom block from `B` at the offset past `A.rows`. The result is
of `A`'s kind. -/
def concatRows (A B : Mat) : Mat :=
  ⟨A.rows + B.rows, A.cols,
    fun i j => if i < A.rows then A.get i j else B.get (i - A.rows) j,
    A.kind⟩
-- pure-end

-- post-conditions-start
/-- Horizontal join `[self other]`, fully pinned to the operands. The result is
always of `self`'s kind, and:

  * if `self` has no columns the result has `other`'s shape and entries;
  * otherwise the result has `self.rows` rows and `self.cols + other.cols`
    columns, with the left `self.cols` columns read from `self` and the rest read
    from `other` shifted left by `self.cols`. -/
def problem_spec_hJoin (self other : Mat) (result : Mat) : Prop :=
  result.kind = self.kind
  ∧ (self.cols = 0 →
        result.rows = other.rows
      ∧ result.cols = other.cols
      ∧ ∀ i j, result.get i j = other.get i j)
  ∧ (self.cols ≠ 0 →
        result.rows = self.rows
      ∧ result.cols = self.cols + other.cols
      ∧ ∀ i j, result.get i j =
          (if j < self.cols then self.get i j else other.get i (j - self.cols)))
-- post-conditions-end

-- impl-start
def implementation_hJoin (self other : Mat) : Mat := Id.run do
  if self.rows = 0 ∨ self.cols = 0 then
    return { other with kind := self.kind }
  return concatCols self other
-- impl-end

-- proof-start
theorem correct_hJoin :
    ∀ (self other : Mat), (self.cols = 0 ∨ self.rows = other.rows) →
      problem_spec_hJoin self other (implementation_hJoin self other) := by
  sorry
-- proof-end

-- post-conditions-start
/-- Vertical join `[self; other]`, fully pinned to the operands. The result is
always of `self`'s kind, and:

  * if `self` has no rows the result has `other`'s shape and entries;
  * otherwise the result has `self.rows + other.rows` rows and `self.cols`
    columns, with the top `self.rows` rows read from `self` and the rest read
    from `other` shifted up by `self.rows`. -/
def problem_spec_vJoin (self other : Mat) (result : Mat) : Prop :=
  result.kind = self.kind
  ∧ (self.rows = 0 →
        result.rows = other.rows
      ∧ result.cols = other.cols
      ∧ ∀ i j, result.get i j = other.get i j)
  ∧ (self.rows ≠ 0 →
        result.rows = self.rows + other.rows
      ∧ result.cols = self.cols
      ∧ ∀ i j, result.get i j =
          (if i < self.rows then self.get i j else other.get (i - self.rows) j))
-- post-conditions-end

-- impl-start
def implementation_vJoin (self other : Mat) : Mat := Id.run do
  if self.rows = 0 ∧ self.cols ≠ other.cols then
    return concatRows (zeroRowsMat other.cols self.kind) other
  return concatRows self other
-- impl-end

-- proof-start
theorem correct_vJoin :
    ∀ (self other : Mat), (self.rows = 0 ∨ self.cols = other.cols) →
      problem_spec_vJoin self other (implementation_vJoin self other) := by
  sorry
-- proof-end
