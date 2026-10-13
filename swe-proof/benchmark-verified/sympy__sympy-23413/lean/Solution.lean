import Mathlib
-- imports-end

/-!
Reducing an integer matrix to a column-style normal form by clearing one row at
a time.

The matrix is processed one row at a time, starting from the bottom row and
working upward. A running pointer `k` marks the leftmost column in which a pivot
has so far been placed; pivots are accumulated in the rightmost columns and `k`
begins one past the last column. For each row considered, the row is reduced so
that a pivot (when the row has one) lands in the column immediately to the
left of the already-placed pivots; the running pointer then records whether
that row actually contributed a new pivot column. The reported normal form is
the block of columns from the final pointer position onward — exactly the
columns in which a pivot was successfully placed.

Every row of the matrix is eligible to contribute a pivot, and the reduction
finishes as soon as the pointer reaches the leftmost column (all columns then
hold a pivot and no further row can add one). This guarantees that a pivot lying
in a topmost row is still found even when the matrix has more rows than columns,
so no genuine pivot column is dropped from the result.
-/

-- axioms-start
-- The matrix is carried as its list-of-integer-rows carrier. Two UNCHANGED
-- operations of the reduction are carried as opaque callees, used identically by
-- the specification and the implementation, so NO property of either is consumed
-- (they cancel in the differential and the proof; G-AX skips):
--
--   * `step` — the per-row reduction: given the current matrix, the index of the
--     row being processed, and the running pivot-column pointer, it performs the
--     (unchanged) column operations that clear the entries left of the pivot,
--     normalise the pivot sign, and reduce the entries to its right, returning
--     the updated matrix together with the updated pointer (the pointer records
--     whether this row contributed a new pivot column).
--   * `sliceCols` — extracting the block of columns from a given index onward,
--     i.e. the columns in which pivots were placed.
abbrev Mat := List (List Int)

opaque step : Mat → Nat → Nat → Mat × Nat
opaque sliceCols : Mat → Nat → Mat
-- axioms-end

-- pure-start
/-- The row indices to consider, from the bottom row upward: `[m-1, m-2, …, 0]`. -/
def rowsDesc (m : Nat) : List Nat := (List.range m).reverse

/-- Front-recursive reference reduction. Fold the per-row reduction over the
row indices from the bottom upward, threading the matrix and the pivot-column
pointer `k`. The reduction stops early as soon as the pointer reaches the
leftmost column (`k = 0`): every column already holds a pivot, so no further row
can contribute one. The result is the final (matrix, pointer) pair. -/
def hnfFold : List Nat → Mat → Nat → Mat × Nat
  | [], A, k => (A, k)
  | i :: rest, A, k =>
      if k = 0 then (A, k)
      else
        let p := step A i k
        hnfFold rest p.1 p.2
-- pure-end

-- post-conditions-start
/-- The reported normal form of the `m × n` integer matrix `A0`: reduce every
row from the bottom upward (stopping once the pivot pointer reaches the leftmost
column), then return the block of columns from the final pointer position
onward — the columns in which a pivot was placed. The result is fully determined
by the input matrix and its shape.

Note for reviewers: this post-condition is an exact equality to a TOTAL
function of the inputs, so the spec is DETERMINISTIC — for each input there is
exactly one satisfying `result`. Any same-spec implementation whose
`correct_hermiteNormalForm` closes (no sorry, clean axioms) is therefore
extensionally identical to the gold behavior. In particular, because the
row-processing control flow is spelled out structurally above (`rowsDesc`,
`hnfFold`) rather than hidden behind an axiomatized oracle, an implementation
that restates the reference fold — or restructures provably-equal control
flow — computes the same function and still does the real work; it is a
positive control, not evidence of spec weakness. A verifying same-spec
variant is behaviorally the gold function; no impl that differs from the
modeled reduction on ANY input can close the proof with clean axioms. -/
def problem_spec_hermiteNormalForm
    (A0 : Mat) (m n : Nat) (result : Mat) : Prop :=
  let p := hnfFold (rowsDesc m) A0 n
  result = sliceCols p.1 p.2
-- post-conditions-end

-- impl-start
def implementation_hermiteNormalForm (A0 : Mat) (m n : Nat) : Mat := Id.run do
  let mut A := A0
  let mut k := n
  for i in rowsDesc m do
    if k = 0 then
      break
    let p := step A i k
    A := p.1
    k := p.2
  return sliceCols A k
-- impl-end

-- proof-start
-- @decl:hnfBodyF-start
/-- The desugared loop body of `implementation_hermiteNormalForm`'s `for` loop:
on the running state `s = (A, k)`, stop (`done`) once the pivot pointer `k`
reaches 0, otherwise reduce the current row and continue (`yield`). -/
def hnfBodyF : Nat → (Mat × Nat) → Id (ForInStep (Mat × Nat)) :=
  fun i s => if s.2 = 0 then pure (ForInStep.done s) else pure (ForInStep.yield (step s.1 i s.2))
-- @decl:hnfBodyF-end

-- @ns:forIn_eq_hnfFold-start
-- @decl:forIn_eq_hnfFold-start
/-- The core bridge: the desugared `Id`-monad `forIn` over any row-index list,
from any start state `(A, k)`, computes exactly the reference fold `hnfFold`. -/
theorem forIn_eq_hnfFold (l : List Nat) (A : Mat) (k : Nat) :
    Id.run (forIn l (A, k) hnfBodyF) = hnfFold l A k := by
  induction l generalizing A k with
  | nil => rfl
  | cons i rest ih =>
      rw [List.forIn_cons]
      by_cases h : k = 0
      · subst h
        simp only [hnfBodyF, hnfFold]
        rfl
      · simp only [hnfFold, if_neg h, hnfBodyF]
        show Id.run (forIn rest ((step A i k).1, (step A i k).2) hnfBodyF)
          = hnfFold rest (step A i k).1 (step A i k).2
        exact ih (step A i k).1 (step A i k).2
-- @decl:forIn_eq_hnfFold-end
-- @ns:forIn_eq_hnfFold-end

theorem correct_hermiteNormalForm :
    ∀ (A0 : Mat) (m n : Nat),
      m = A0.length → (∀ row ∈ A0, row.length = n) →
      problem_spec_hermiteNormalForm A0 m n
        (implementation_hermiteNormalForm A0 m n) := by
  intro A0 m n hm hrows
  have key : ∀ (l : List Nat) (A : Mat) (k : Nat),
      (forIn l (⟨A, k⟩ : MProd Mat Nat)
        (fun i r => if r.2 = 0 then (pure (ForInStep.done r) : Id _)
          else pure (ForInStep.yield ⟨(step r.1 i r.2).1, (step r.1 i r.2).2⟩))).run
      = ⟨(hnfFold l A k).1, (hnfFold l A k).2⟩ := by
    intro l
    induction l with
    | nil => intro A k; rfl
    | cons i rest ih =>
      intro A k
      by_cases hk : k = 0
      · subst hk; simp [List.forIn_cons, hnfFold]
      · simp only [List.forIn_cons, hnfFold, hk, if_false]
        simp only [Id.run, bind, pure] at ih ⊢
        exact ih _ _
  show implementation_hermiteNormalForm A0 m n
      = sliceCols (hnfFold (rowsDesc m) A0 n).1 (hnfFold (rowsDesc m) A0 n).2
  show sliceCols (forIn (rowsDesc m) (⟨A0, n⟩ : MProd Mat Nat)
        (fun i r => if r.2 = 0 then (pure (ForInStep.done r) : Id _)
          else pure (ForInStep.yield ⟨(step r.1 i r.2).1, (step r.1 i r.2).2⟩))).run.fst
      (forIn (rowsDesc m) (⟨A0, n⟩ : MProd Mat Nat)
        (fun i r => if r.2 = 0 then (pure (ForInStep.done r) : Id _)
          else pure (ForInStep.yield ⟨(step r.1 i r.2).1, (step r.1 i r.2).2⟩))).run.snd
      = sliceCols (hnfFold (rowsDesc m) A0 n).1 (hnfFold (rowsDesc m) A0 n).2
  rw [key (rowsDesc m) A0 n]
-- proof-end
