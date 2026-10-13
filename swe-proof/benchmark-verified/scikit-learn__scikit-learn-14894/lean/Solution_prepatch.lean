import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee needs an opaque signature. The operations the change
-- guards — building the repeated column-index block, the row-offset vector, and
-- assembling the compressed-sparse-row record — are modeled DIRECTLY (deep
-- model) as the `tileRange` / `List.range`-map helpers and record fields below,
-- not axiomatized. The proof agent may add `_prop` axioms only if genuinely
-- stuck.
-- axioms-end

-- pure-start
/-- A compressed-sparse-row matrix: the three parallel storage arrays plus the
logical shape. `data` holds the stored values, `indices` the column index of
each stored value, `indptr` the per-row start offsets (length `nrows + 1`). -/
structure CSRMatrix (α : Type) where
  data : List α
  indices : List Nat
  indptr : List Nat
  nrows : Nat
  ncols : Nat
deriving Repr

/-- `nClass` copies of `block`, concatenated front-first (front-recursive). -/
def tileCopies (block : List Nat) : Nat → List Nat
  | 0 => []
  | n + 1 => block ++ tileCopies block n

/-- The column-index vector: the contiguous block `[0, 1, …, width-1]` repeated
`copies` times. Models repeating a ramp `copies` times. -/
def tileRange (width copies : Nat) : List Nat :=
  tileCopies (List.range width) copies

/-- The row-offset vector `[0, width, 2·width, …, rows·width]` (length
`rows + 1`): the evenly spaced offsets stepping by `width`. -/
def rowOffsets (rows width : Nat) : List Nat :=
  (List.range (rows + 1)).map (· * width)

/-- The canonical empty sparse matrix: no stored values, a single (degenerate)
row offset pair, shape one-by-zero. -/
def emptyCSR (α : Type) : CSRMatrix α :=
  { data := [], indices := [], indptr := [0, 0], nrows := 1, ncols := 0 }
-- pure-end

-- post-conditions-start
/-- The coefficient matrix assembled from a stored coefficient buffer `data`, a
support-set size `width`, and a per-class repeat count `rows`.

The assembly must always succeed (return a matrix, never abort). When the
support set is empty (`width = 0`) the result is the canonical empty matrix.
Otherwise the result is the block matrix whose stored values are exactly the
supplied buffer, whose column indices are the support ramp repeated once per
class, whose row offsets are evenly spaced by the support-set size, and whose
shape is `rows × width`. Every output component is pinned to the inputs. -/
def problem_spec_dualCoef {α : Type} (width rows : Nat) (data : List α)
    (result : Except String (CSRMatrix α)) : Prop :=
  ∃ m : CSRMatrix α, result = Except.ok m ∧
    (width = 0 →
      m.data = [] ∧ m.indices = [] ∧ m.indptr = [0, 0] ∧
      m.nrows = 1 ∧ m.ncols = 0) ∧
    (width ≠ 0 →
      m.data = data ∧
      m.indices = tileRange width rows ∧
      m.indptr = rowOffsets rows width ∧
      m.nrows = rows ∧ m.ncols = width)
-- post-conditions-end

-- impl-start
def implementation_dualCoef {α : Type} (width rows : Nat) (data : List α) :
    Except String (CSRMatrix α) := Id.run do
  -- the column indices: the support ramp repeated once per class
  let indices := tileRange width rows
  -- PRE-PATCH BUG: the evenly spaced row offsets are built unconditionally. When
  -- the support set is empty the spacing step collapses to zero and the offset
  -- construction aborts (no matrix is produced) instead of returning the
  -- canonical empty matrix.
  if width = 0 then
    return Except.error "row-offset construction aborted: zero spacing step"
  let indptr := rowOffsets rows width
  return Except.ok
    { data := data, indices := indices, indptr := indptr,
      nrows := rows, ncols := width }
-- impl-end

-- proof-start
theorem correct_dualCoef {α : Type} (width rows : Nat) (data : List α)
    (hrows : 1 ≤ rows) :
    problem_spec_dualCoef width rows data
      (implementation_dualCoef width rows data) := by
  -- carries the gold proof body; UNCLOSABLE against the buggy impl because for
  -- width = 0 the impl returns `Except.error …`, so the witnessed `Except.ok m`
  -- equality in the empty branch cannot hold.
  unfold problem_spec_dualCoef implementation_dualCoef
  by_cases h : width = 0
  · subst h
    refine ⟨emptyCSR α, by simp [Id.run, pure], ?_, ?_⟩
    · intro _; simp [emptyCSR]
    · intro hne; exact absurd rfl hne
  · refine ⟨{ data := data, indices := tileRange width rows,
              indptr := rowOffsets rows width, nrows := rows, ncols := width },
            by simp only [Id.run, h, if_false]; rfl, ?_, ?_⟩
    · intro h0; exact absurd h0 h
    · intro _; exact ⟨rfl, rfl, rfl, rfl, rfl⟩
-- proof-end
