import Mathlib
-- imports-end

/-!
Drawing a categorical (nominal) plot axis the way categorical axes are drawn.

When the scale assigned to a plot axis is a nominal/categorical scale, the axis
gets a distinctive treatment at figure-finalization time, mirroring the way the
classic categorical plots draw their category axis:

  * its grid is not shown, even when the active style would otherwise draw one;
  * its extent is pinned to run half a unit beyond the first and last category
    position — i.e. from `-1/2` to `nticks - 1/2`, where `nticks` is the number
    of category tick marks — rather than using the ordinary data-margin logic;
  * on a vertical (`y`) axis that pinned extent is reversed, so the categories
    read from top to bottom.

The pinned extent is applied ONLY when the user has not pinned an explicit limit
on that axis; an explicit limit takes precedence and the categorical extent is
left unset. The grid is hidden for every nominal axis regardless of any explicit
limit. A non-nominal axis is untouched by this step.

We model the two finalization decisions for a single axis as `AxisLayout`:
  * `gridHidden`  — whether finalization forces the grid off for this axis;
  * `fixedLimit`  — `some (lo, hi)` when finalization pins the categorical extent,
                    or `none` when it leaves the extent to the ordinary logic.
Coordinates are exact half-integers, so they are modeled as `ℚ` (rational),
whose order is transparent to the logic.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The number of
-- category tick marks (`nticks`) is taken as an input observation, and the two
-- decisions are a closed expression over the axis orientation, the nominal flag,
-- the explicit-limit flag, and that count. No `opaque`/`axiom` callee contract
-- is needed.
-- axioms-end

-- pure-start
/-- The two finalization decisions for one plot axis. `gridHidden` records
whether the grid is forced off; `fixedLimit` is `some (lo, hi)` when the extent
is pinned, `none` when it is left to the ordinary data-margin logic. -/
structure AxisLayout where
  gridHidden : Bool
  fixedLimit : Option (ℚ × ℚ)
deriving DecidableEq
-- pure-end

-- post-conditions-start
/-- The finalization decisions for a single axis. `isY` is true on a vertical
axis; `isNominal` is true when the axis carries a nominal/categorical scale;
`hasLimit` is true when the user pinned an explicit limit on the axis; `nticks`
is the number of category tick marks.

The grid is hidden exactly when the axis is nominal. The extent is pinned to
`(-1/2, nticks - 1/2)` (reversed on a vertical axis) exactly when the axis is
nominal AND no explicit limit is present; in every other case the extent is left
unset. -/
def problem_spec_nominalAxis
    (isY isNominal hasLimit : Bool) (nticks : Nat) (result : AxisLayout) : Prop :=
  (result.gridHidden = isNominal) ∧
  (isNominal = true → hasLimit = false →
      result.fixedLimit
        = some (if isY then ((nticks : ℚ) - 1/2, -1/2)
                else (-1/2, (nticks : ℚ) - 1/2))) ∧
  (isNominal = false → result.fixedLimit = none) ∧
  (hasLimit = true → result.fixedLimit = none)
-- post-conditions-end

-- impl-start
def implementation_nominalAxis
    (isY isNominal hasLimit : Bool) (nticks : Nat) : AxisLayout := Id.run do
  -- The categorical axis receives no special treatment at finalization: the
  -- grid decision and the extent are both left to the ordinary logic.
  let mut gridHidden := false
  let mut fixedLimit : Option (ℚ × ℚ) := none
  return ⟨gridHidden, fixedLimit⟩
-- impl-end

-- proof-start
-- Gold proof body carried over from Solution.lean (SPEC_GUIDE §1.1). Against this
-- implementation it cannot close: the specification requires `gridHidden` to
-- equal the nominal flag, but this implementation always leaves it off, so the
-- first conjunct fails on a nominal axis — the discriminating clause. (The proof
-- agent carries the real closed gold body here once Solution.lean is proved.)
theorem correct_nominalAxis :
    ∀ (isY isNominal hasLimit : Bool) (nticks : Nat),
      problem_spec_nominalAxis isY isNominal hasLimit nticks
        (implementation_nominalAxis isY isNominal hasLimit nticks) := by
  sorry
-- proof-end
