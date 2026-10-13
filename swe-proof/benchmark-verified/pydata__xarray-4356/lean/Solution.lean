import Mathlib
-- imports-end

/-!
Applying a minimum-valid-count threshold to the cells of a reduced array.

After a missing-value-aware reduction (a sum or product that skips missing
entries) over one or more axes, each output cell aggregates a block of the
original entries — the block of all entries that collapse onto that cell. A
cell is only trustworthy if enough of the entries reduced into it were actually
present; otherwise the reduction had too little data and the cell must be
discarded (overwritten with the fill sentinel).

For each output cell we therefore compare the number of *valid* (present)
entries reduced into it against the required minimum:

* the total number of entries reduced into one cell is the product of the sizes
  of all reduced axes;
* of those, some number were missing (this missing count is supplied per cell);
* the cell is kept with its computed value when
  `total − missing ≥ minimum`, and replaced by the fill sentinel otherwise.

This rule applies uniformly however many axes are reduced — reducing over a
single axis, or over several axes at once, is the same per-cell threshold; the
only difference is that the per-cell total is a product over all the reduced
axes rather than a single axis size. Reducing over several axes at once is a
perfectly valid request and produces a thresholded result rather than being
rejected.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The per-cell
-- valid-entry count (the product of the reduced-axis sizes minus the supplied
-- missing count) and its comparison to the required minimum are modeled DEEPLY
-- over the observable inputs (the reduced-axis sizes, the per-cell value and
-- missing count, the minimum, the fill sentinel), so no `opaque`/`axiom` callee
-- contract is needed.
-- axioms-end

-- pure-start
/-- The value an output cell keeps after the minimum-count threshold.

`total` is the number of entries reduced into the cell (the product of the
reduced-axis sizes). `cell = (value, missing)` is the cell's computed value
together with how many of those entries were missing. The cell keeps its value
when the number of valid entries `total − missing` is at least `minCount`,
otherwise it is replaced by `fillValue`. The subtraction is carried out over the
integers so that the comparison matches the original signed test
`(total − missing − minCount) < 0`. -/
def reducedCellValue (total : Int) (minCount : Nat) (fillValue : Float)
    (cell : Float × Nat) : Float :=
  if total - (cell.2 : Int) < (minCount : Int) then fillValue else cell.1
-- pure-end

-- post-conditions-start
/-- The thresholding completes without error and, position by position, the
output cell is grounded in the corresponding input cell: at every index `i` the
output value present there is exactly the fill sentinel when fewer than
`minCount` of the `axisSizes.prod` entries reduced into that cell were present
(`axisSizes.prod − missingᵢ < minCount`), and the cell's own computed value
otherwise. Quantifying over every index pins the length and every element to the
input carrier, so only the genuine cell-wise computation can satisfy it. -/
def problem_spec_enforceMinCount (axisSizes : List Nat) (cells : List (Float × Nat))
    (minCount : Nat) (fillValue : Float) (result : Except String (List Float)) : Prop :=
  ∃ out : List Float, result = Except.ok out ∧
    ∀ i : Nat, out[i]? =
      (cells[i]?).map (fun cell =>
        if (axisSizes.prod : Int) - (cell.2 : Int) < (minCount : Int)
          then fillValue else cell.1)
-- post-conditions-end

-- impl-start
def implementation_enforceMinCount (axisSizes : List Nat) (cells : List (Float × Nat))
    (minCount : Nat) (fillValue : Float) : Except String (List Float) := Id.run do
  let total : Int := (axisSizes.prod : Int)
  let mut out : List Float := []
  for cell in cells do
    out := out ++ [reducedCellValue total minCount fillValue cell]
  return .ok out
-- impl-end

-- proof-start
/-- The imperative `for`-accumulation desugars to appending the per-cell map.
Stated on the cleaned `forIn` body and generalized over the accumulator so the
induction goes through. -/
private theorem enforceMinCount_forIn (f : Float × Nat → Float)
    (cells : List (Float × Nat)) (init : List Float) :
    (forIn cells init (fun cell r => (pure (ForInStep.yield (r ++ [f cell])))) : Id (List Float)) =
      init ++ cells.map f := by
  induction cells generalizing init with
  | nil => simp only [List.forIn_nil, List.map_nil, List.append_nil]; rfl
  | cons a as ih =>
    rw [List.forIn_cons]
    simp only [bind] at ih ⊢
    rw [ih]
    simp [List.append_assoc]

theorem correct_enforceMinCount :
    ∀ (axisSizes : List Nat) (cells : List (Float × Nat))
      (minCount : Nat) (fillValue : Float),
      problem_spec_enforceMinCount axisSizes cells minCount fillValue
        (implementation_enforceMinCount axisSizes cells minCount fillValue) := by
  intro axisSizes cells minCount fillValue
  refine ⟨cells.map (reducedCellValue (axisSizes.prod : Int) minCount fillValue), ?_, ?_⟩
  · -- the loop builds exactly the per-cell map; bridge the desugared body to the helper
    unfold implementation_enforceMinCount
    simp only [Id.run, bind]
    rw [enforceMinCount_forIn (reducedCellValue (axisSizes.prod : Int) minCount fillValue) cells []]
    rfl
  · -- each index matches: `getElem?` commutes with `map`, and the mapped function
    -- is definitionally `reducedCellValue`'s `if`
    intro i
    rw [List.getElem?_map]
    rfl
-- proof-end
