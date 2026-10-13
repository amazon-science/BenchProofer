import Velvet.Std
-- imports-end

/- Total correctness: the real reduction is a bounded loop over the matrix rows
   (at most one pass per row, stopping early once every column has a pivot) and
   always terminates, so a diverging implementation must NOT satisfy this spec.
   Partial correctness would let a non-terminating loop discharge the
   postcondition vacuously. -/
set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- An integer matrix in the working dense representation that the reduction
   mutates column-by-column. Its internal layout is irrelevant to the loop
   structure under specification — only that one and the same per-row reduction is
   applied to it, in order — so it is left fully opaque (directive 7: the
   weakest sufficient contract is none). The bijection to the repository value
   space is in mapping.md (G-AX / G-CONF use it). -/
axiom Mat : Type

/- A canonical matrix value, so an out-of-range probe has a harmless default.
   An UNCHANGED constructed value; left fully opaque. Provenance + soundness:
   mapping.md / axiom_check.py (G-AX). -/
axiom matDefault : Mat
noncomputable instance : Inhabited Mat := ⟨matDefault⟩

/- The single per-row reduction step, applied once to a single row of the matrix
   while assigning a pivot to a rightmost column. Given the column count, the
   current matrix, the current count of still-unassigned pivot columns, and the
   row index being processed, it returns the reduced matrix together with the
   updated count of unassigned pivot columns (the count drops by one when a
   pivot is successfully placed, and is unchanged when the row contributes no
   pivot). An UNCHANGED reduction callee the operation delegates to for every
   row; left fully opaque — the operation assumes nothing about the entries it
   produces, only that the SAME reduction is applied to each processed row.
   Provenance + executable soundness check: mapping.md §3 / axiom_check.py
   (G-AX). Tagged A-reference. -/
axiom stepRow : Nat → Mat → Nat → Nat → Mat × Nat

/- The final selection of the assigned pivot columns: keep the rightmost columns
   of the reduced matrix, starting from the first column that received a pivot.
   An UNCHANGED column-selection callee; left fully opaque. Provenance +
   executable soundness check: mapping.md §3 / axiom_check.py (G-AX). Tagged
   A-reference. -/
axiom slice : Mat → Nat → Mat
-- axioms-end

-- pure-start
/- Reduce the matrix one row at a time, working from the bottom row upward.

   `numCols` is the number of columns; `rowsLeft` counts how many rows are still
   eligible to be processed (so the next row to process has index
   `rowsLeft - 1`); `mat` is the matrix being reduced; `k` is the count of
   columns that have not yet received a pivot.

   A row is processed only while there remains at least one column without a
   pivot: once every column has been assigned a pivot (`k = 0`), no further row
   can contribute, so processing stops immediately. Otherwise the same per-row
   reduction is applied to the current top-eligible row and the recursion
   continues on the remaining rows. Front-recursive so a single unfold is
   available per loop step (the fold pattern, plan §5.4). -/
noncomputable def reduceRows (numCols : Nat) : Nat → Mat → Nat → Mat × Nat
  | 0,     mat, k => (mat, k)
  | r + 1, mat, k =>
      if k = 0 then (mat, k)
      else
        let p := stepRow numCols mat k r
        reduceRows numCols r p.1 p.2

@[grind] lemma reduceRows_zero (numCols : Nat) (mat : Mat) (k : Nat) :
    reduceRows numCols 0 mat k = (mat, k) := rfl

@[grind] lemma reduceRows_succ (numCols r : Nat) (mat : Mat) (k : Nat) :
    reduceRows numCols (r + 1) mat k =
      (if k = 0 then (mat, k)
       else reduceRows numCols r (stepRow numCols mat k r).1 (stepRow numCols mat k r).2) := rfl

/- The final HNF selection: the matrix reduced over all eligible rows, then its
   pivot columns kept. -/
noncomputable def hnfResult (numCols numRows : Nat) (mat : Mat) : Mat :=
  let p := reduceRows numCols numRows mat numCols
  slice p.1 p.2

/- Processing stops with the matrix and pivot count unchanged exactly when there
   are no eligible rows left or every column already has a pivot. -/
lemma reduceRows_exit (numCols rowsLeft : Nat) (mat : Mat) (k : Nat)
    (h : rowsLeft = 0 ∨ k = 0) : reduceRows numCols rowsLeft mat k = (mat, k) := by
  cases rowsLeft with
  | zero => rfl
  | succ r =>
    rcases h with h | h
    · exact absurd h (Nat.succ_ne_zero r)
    · simp [reduceRows_succ, h]

/- The backward-fold step: with eligible rows remaining and a column still
   awaiting a pivot, the top-eligible row (index `rowsLeft - 1`) is reduced and
   the recursion continues on one fewer row. This is the single goal
   `loom_solve` leaves for the loop body. -/
lemma reduceRows_step (numCols rowsLeft : Nat) (mat : Mat) (k : Nat)
    (hr : 0 < rowsLeft) (hk : 0 < k) :
    reduceRows numCols rowsLeft mat k =
      reduceRows numCols (rowsLeft - 1)
        (stepRow numCols mat k (rowsLeft - 1)).1
        (stepRow numCols mat k (rowsLeft - 1)).2 := by
  obtain ⟨r, rfl⟩ : ∃ r, rowsLeft = r + 1 := ⟨rowsLeft - 1, by omega⟩
  have hk' : k ≠ 0 := by omega
  simp [reduceRows_succ, hk']
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Compute the Hermite normal form of an integer matrix by the column-reduction
   algorithm.

   `A` is the read-only input matrix; `numRows` and `numCols` are its row and
   column counts. Desired behaviour: rows are reduced one at a time from the
   bottom upward, each placing a pivot in a rightmost column, continuing until
   either all rows have been processed or every column has received a pivot. The
   result keeps exactly the pivot columns of the fully reduced matrix. -/
noncomputable section
method hermiteNormalForm (A : Mat) (numRows : Nat) (numCols : Nat) return (out : Mat)
  ensures out = hnfResult numCols numRows A
  do
    -- impl-start
    let mut mat : Mat := A
    let mut k := numCols
    let mut rowsLeft := numRows
    while rowsLeft > 0 ∧ k > 0
      invariant 0 ≤ rowsLeft ∧ rowsLeft ≤ numRows
      invariant reduceRows numCols numRows A numCols = reduceRows numCols rowsLeft mat k
      done_with rowsLeft = 0 ∨ k = 0
      decreasing rowsLeft
    do
      let p := stepRow numCols mat k (rowsLeft - 1)
      mat := p.1
      k := p.2
      rowsLeft := rowsLeft - 1
    return slice mat k
    -- impl-end
end

prove_correct hermiteNormalForm by
  loom_solve
  · rw [← reduceRows_step numCols rowsLeft mat k (by omega) (by omega)]
    assumption
  · simp only [hnfResult]
    have hinv : reduceRows numCols numRows A numCols = reduceRows numCols rowsLeft mat k := by
      assumption
    rw [hinv, reduceRows_exit numCols rowsLeft mat k (by omega)]
    simp_all
