import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- An opaque physical dimension value. Its internal structure is irrelevant to
   this decision; only equality and whether it is dimensionless matter.
   Provenance + executable soundness check: mapping.md / axiom_check.py (G-AX). -/
axiom Dimension : Type

/- The canonical dimensionless dimension — the distinguished value every
   dimensionless quantity must be reported as. An UNCHANGED constructed constant;
   left fully opaque (the weakest sufficient contract is none, directive 7).
   Provenance + soundness: mapping.md §3.3 / axiom_check.py (G-AX). -/
axiom dimOne : Dimension

/- Whether a dimension carries no physical dimension. An UNCHANGED predicate;
   total (it either holds or does not) and left fully opaque — the spec needs
   only that the SAME predicate decides each element, never any equational fact
   about it. CRUCIALLY this is NOT the same as `d = dimOne`: a dimension can be
   dimensionless yet not be the canonical value (mapping.md §3.2). Provenance +
   soundness: mapping.md / axiom_check.py (G-AX). -/
axiom isDimensionless : Dimension → Bool
-- axioms-end

-- pure-start
/- A dimension value is always available, so an out-of-range probe has a
   harmless default; derived from `dimOne` rather than postulated. -/
noncomputable instance : Inhabited Dimension := ⟨dimOne⟩

/- Canonicalize one dimension: a dimensionless dimension is reported as the
   single canonical dimensionless value; any other dimension is kept as-is. This
   is the per-element rule the sequence canonicalization applies. -/
noncomputable def normDim (d : Dimension) : Dimension :=
  if isDimensionless d then dimOne else d

/- Canonicalize a whole sequence of dimensions: apply `normDim` to each element,
   order preserved. Front-recursive so a single unfold is available per loop
   step (the fold pattern, plan §5.4). -/
noncomputable def normSeq : List Dimension → List Dimension
  | []      => []
  | d :: ds => normDim d :: normSeq ds

@[grind] lemma normSeq_nil : normSeq [] = [] := rfl
@[grind] lemma normSeq_cons (d : Dimension) (ds : List Dimension) :
    normSeq (d :: ds) = normDim d :: normSeq ds := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Canonicalize the dimensions of a sequence of operands so that each
   dimensionless operand is reported with the single canonical dimensionless
   value, while every dimensionful operand keeps its own dimension and position.
   `dims` are the operand dimensions in order; `out` is the canonicalized
   sequence. -/
noncomputable section
method normalizeDimensions (dims : List Dimension) return (out : List Dimension)
  ensures out = normSeq dims
  do
    -- impl-start
    -- Pre-image skeleton: each operand's dimension is reported VERBATIM, with no
    -- canonicalization of dimensionless operands (they pass straight through).
    -- The frozen spec requires `normSeq dims` (which reports every dimensionless
    -- operand as the single canonical value), so prove_correct MUST fail
    -- wherever an operand is dimensionless but not already canonical.
    let mut result : List Dimension := []
    let mut i := dims.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ dims.length
      invariant result = normSeq (dims.drop i)
      done_with i = 0
      decreasing i
    do
      let d := dims[i - 1]!
      result := d :: result
      i := i - 1
    return result
    -- impl-end
end

/- The backward-fold step: dropping one fewer element exposes the element at
   `i-1` on the front, so `normSeq` peels one `normDim`. This is the single goal
   `loom_solve` leaves for the loop body. -/
lemma normSeq_drop_step (dims : List Dimension) (i : Nat)
    (hi : 0 < i) (hle : i ≤ dims.length) :
    normSeq (dims.drop (i - 1)) = normDim dims[i - 1]! :: normSeq (dims.drop i) := by
  have hlt : i - 1 < dims.length := by omega
  have hcons : dims.drop (i - 1) = dims[i - 1]! :: dims.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, normSeq_cons]

prove_correct normalizeDimensions by
  loom_solve
  rw [normSeq_drop_step dims i (by omega) (by omega)]
  simp_all
