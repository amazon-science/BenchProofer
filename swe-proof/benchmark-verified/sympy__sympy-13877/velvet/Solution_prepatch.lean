import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms. The decisive zero-recogniser this operation depends on is
   modeled DEEPLY by the `mathNonzero` field of `Entry` (see the `pure` region)
   and validated against the real recogniser by axiom_check.py (G-AX); it is an
   A-reference, not an axiom the proof consumes. -/
-- axioms-end

-- pure-start
/- A column entry, abstracted to the two boolean observations the selection step
   makes of a scalar value:

   * `litNonzero` — the cheap, structural recogniser: the value is not one of the
     recognised numeric/literal zeros.
   * `mathNonzero` — the decisive recogniser: the value is still non-zero after
     algebraic normalisation. This is the observation that decides selection.

   For every real scalar, `mathNonzero` implies `litNonzero` (a value non-zero
   after normalisation is certainly not a literal zero); the converse may fail —
   a value can look structurally non-zero yet normalise to zero. The bijection to
   the repository scalar type and the soundness check live in mapping.md §2/§3
   and axiom_check.py (G-AX). -/
structure Entry where
  litNonzero  : Bool
  mathNonzero : Bool
deriving Inhabited, Repr

/- The result of the selection step: whether a usable entry exists and, if so,
   its index in the column. -/
structure PivotResult where
  found : Bool
  idx   : Nat
deriving Inhabited, Repr

/- The standing relationship between the two recognisers on every real scalar:
   decisive non-zero ⟹ structurally non-zero. Stated over a whole column. -/
@[grind] def consistent (col : Array Entry) : Prop :=
  ∀ j, j < col.size → (col[j]!).mathNonzero = true → (col[j]!).litNonzero = true
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Select the first column entry usable for the elimination step: scan the
   column in order and choose the first index whose value is decisively non-zero
   (`mathNonzero`). Report whether such an index exists and which one. The
   decision must rest on the decisive recogniser alone — an entry that merely
   looks non-zero but normalises to zero must be skipped. -/
method selectPivot (col : Array Entry) return (res : PivotResult)
  require consistent col
  ensures res.found = true →
    res.idx < col.size ∧ (col[res.idx]!).mathNonzero = true ∧
      (∀ j, j < res.idx → (col[j]!).mathNonzero = false)
  ensures res.found = false →
    (∀ j, j < col.size → (col[j]!).mathNonzero = false)
  do
    -- impl-start
    -- Pre-image skeleton: the entry is tested with the cheap STRUCTURAL
    -- recogniser `litNonzero` rather than the decisive `mathNonzero`. An entry
    -- that looks non-zero but normalises to zero is therefore selected, so the
    -- frozen spec's `(col[res.idx]!).mathNonzero = true` clause fails — this
    -- prepatch MUST NOT verify (G-DIFF).
    let mut i := 0
    let mut found := false
    let mut idx := 0
    while i < col.size ∧ found = false
      invariant 0 ≤ i ∧ i ≤ col.size
      invariant found = false → (∀ j, j < i → (col[j]!).litNonzero = false)
      invariant found = true →
        (idx < col.size ∧ (col[idx]!).litNonzero = true ∧
          (∀ j, j < idx → (col[j]!).litNonzero = false))
      done_with (i = col.size ∨ found = true)
      decreasing col.size - i
    do
      if (col[i]!).litNonzero = true then
        idx := i
        found := true
      i := i + 1
    return ⟨found, idx⟩
    -- impl-end

prove_correct selectPivot by
  loom_solve
