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
/-- PRE-PATCH (buggy) skeleton: the indices are recorded in a container that
keeps the input value type's capacity `M`. Assigning a reserved slot number that
does not fit in `0 … M - 1` is rejected — the conversion fails (`Except.error`)
instead of recording the reserved slot, so it does not always succeed. -/
def implementation_index (N M : Nat) (xs : List Int) :
    Except Unit (List Nat) := Id.run do
  let mut out : List Nat := []
  for x in xs do
    let mut idx : Int := x
    if idx > (N : Int) - 1 then
      idx := (N : Int) + 1
    if idx < 0 then
      idx := (N : Int)
    if idx ≥ (M : Int) then
      return Except.error ()
    out := out ++ [idx.toNat]
  return Except.ok out
-- impl-end

-- proof-start
-- Gold proof body carried over; it does NOT close against the buggy impl (when
-- the reserved over-slot `N + 1 ≥ M` the conversion returns `Except.error`,
-- contradicting the `∃ out, result = Except.ok out` requirement of the spec).
theorem correct_index :
    ∀ (N M : Nat) (xs : List Int),
      problem_spec_index N xs (implementation_index N M xs) := by
  sorry
-- proof-end
