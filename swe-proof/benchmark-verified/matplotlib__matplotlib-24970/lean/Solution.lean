import Mathlib
-- imports-end

/-!
Mapping integer data values to palette slot indices.

A palette of `N` colors is stored together with extra slots reserved for values
that fall outside the palette's valid range: an `under` slot at index `N` for
values below the range, an `over` slot at index `N + 1` for values above it, and
a further `bad` slot at index `N + 2`. Given a list of integer data values, each
value is converted to the index of the slot whose color represents it:

* a value `v` with `0 ≤ v < N` indexes its own palette color `v`;
* a value `v < 0` indexes the `under` slot `N`;
* a value `v ≥ N` indexes the `over` slot `N + 1`.

The reserved slot numbers must be recorded faithfully no matter how wide the
range of the input value type is, so the conversion always succeeds and every
out-of-range value selects its dedicated reserved slot. The container holding
the indices is given a value type with capacity `M` (representing values
`0 … M - 1`); the conversion must not fail even when `M` is too small to hold a
reserved slot number on its own.

The behavior is stated abstractly as an input→output relation; the
implementation and correctness proof are supplied separately.
-/

-- axioms-start
-- No unchanged dependency callee requires a contract: the index assignment is
-- spelled out concretely (in-range values keep their own index; out-of-range
-- values are sent to the dedicated reserved slots `N` and `N + 1`).
-- axioms-end

-- pure-start
/-- The slot index a single integer data value `x` maps to, for a palette of
`N` colors: `N` (under) when `x < 0`, `N + 1` (over) when `x ≥ N`, and `x`
itself when `0 ≤ x < N`. -/
def desiredIndex (N : Nat) (x : Int) : Nat :=
  if x < 0 then N
  else if (N : Int) ≤ x then N + 1
  else x.toNat
-- pure-end

-- post-conditions-start
/-- `result` is the conversion of the integer data values `xs` to slot indices
under a palette of `N` colors. The conversion always succeeds (`Except.ok`) and
yields one index per input value, each equal to the exact slot the corresponding
input value maps to (`desiredIndex`). -/
def problem_spec_index (N : Nat) (xs : List Int)
    (result : Except Unit (List Nat)) : Prop :=
  ∃ out, result = Except.ok out ∧
    out.length = xs.length ∧
    ∀ i, i < xs.length → out.getD i 0 = desiredIndex N (xs.getD i 0)
-- post-conditions-end

-- impl-start
/-- The indices are recorded in a container whose value type is widened so it
can always hold a reserved slot number, independently of the input value type's
capacity `M`. The reserved slot numbers therefore always fit and the conversion
never fails. -/
def implementation_index (N M : Nat) (xs : List Int) :
    Except Unit (List Nat) := Id.run do
  let mut out : List Nat := []
  for x in xs do
    let mut idx : Int := x
    -- send values above the valid range to the `over` slot first, then values
    -- below it to the `under` slot
    if idx > (N : Int) - 1 then
      idx := (N : Int) + 1
    if idx < 0 then
      idx := (N : Int)
    out := out ++ [idx.toNat]
  return Except.ok out
-- impl-end

-- proof-start
-- The desugared loop body equals a clean body that appends `desiredIndex N x`.
theorem body_eq_index (N : Nat) (x : Int) (r : List Nat) :
    (if x > (N:Int) - 1 then
        (if (N:Int) + 1 < 0 then ForInStep.yield (r ++ [((N:Int)).toNat])
         else ForInStep.yield (r ++ [((N:Int) + 1).toNat]))
      else
        (if x < 0 then ForInStep.yield (r ++ [((N:Int)).toNat])
         else ForInStep.yield (r ++ [x.toNat])))
      = ForInStep.yield (r ++ [desiredIndex N x]) := by
  have hidx : desiredIndex N x =
      (if x > (N:Int) - 1 then
        (if (N:Int) + 1 < 0 then ((N:Int)).toNat else ((N:Int) + 1).toNat)
       else
        (if x < 0 then ((N:Int)).toNat else x.toNat)) := by
    unfold desiredIndex
    by_cases h1 : x > (N:Int) - 1
    · have hneg : ¬ ((N:Int) + 1 < 0) := by omega
      have hx0 : ¬ (x < 0) := by omega
      have hxN : (N:Int) ≤ x := by omega
      simp only [h1, hneg, hx0, hxN, if_true, if_false]; omega
    · have hxN : ¬ ((N:Int) ≤ x) := by omega
      by_cases h2 : x < 0
      · simp only [h1, h2, hxN, if_true, if_false]; omega
      · simp only [h1, h2, hxN, if_false]
  rw [hidx]
  by_cases h1 : x > (N:Int) - 1 <;> by_cases h2 : (N:Int) + 1 < 0 <;>
    by_cases h3 : x < 0 <;> simp only [h1, h2, h3, if_true, if_false]

theorem helper_index (N : Nat) (xs : List Int) (init : List Nat) :
    (Id.run (forIn xs init (fun x r =>
        ForInStep.yield (r ++ [desiredIndex N x]))) : List Nat)
      = init ++ xs.map (desiredIndex N) := by
  induction xs generalizing init with
  | nil => simp only [List.forIn_nil, Id.run, pure, List.map_nil, List.append_nil]
  | cons a as ih =>
    rw [List.forIn_cons]
    simp only [Id.run, bind] at ih ⊢
    rw [ih]
    simp [List.map_cons, List.append_assoc]

theorem correct_index :
    ∀ (N M : Nat) (xs : List Int),
      problem_spec_index N xs (implementation_index N M xs) := by
  intro N M xs
  refine ⟨xs.map (desiredIndex N), ?_, ?_, ?_⟩
  · unfold implementation_index
    simp only [Id.run]
    have hbody : (forIn xs ([]:List Nat) (fun x r =>
        if x > (N:Int) - 1 then do
          pure PUnit.unit
          if (N:Int)+1 < 0 then do pure PUnit.unit; pure PUnit.unit; pure (ForInStep.yield (r ++ [((N:Int)).toNat]))
            else do pure PUnit.unit; pure PUnit.unit; pure (ForInStep.yield (r ++ [((N:Int)+1).toNat]))
        else do
          pure PUnit.unit
          if x < 0 then do pure PUnit.unit; pure PUnit.unit; pure (ForInStep.yield (r ++ [((N:Int)).toNat]))
            else do pure PUnit.unit; pure PUnit.unit; pure (ForInStep.yield (r ++ [x.toNat]))) : Id (List Nat))
      = (forIn xs ([]:List Nat) (fun x r =>
        ForInStep.yield (r ++ [desiredIndex N x])) : Id (List Nat)) := by
      congr 1
      funext x r
      simp only [bind, pure]
      exact body_eq_index N x r
    rw [hbody]
    have := helper_index N xs []
    simp only [Id.run] at this
    rw [this]; rfl
  · simp
  · intro i hi
    rw [List.getD_eq_getElem?_getD, List.getD_eq_getElem?_getD]
    simp only [List.getElem?_map]
    rw [List.getElem?_eq_getElem hi]
    simp
-- proof-end
