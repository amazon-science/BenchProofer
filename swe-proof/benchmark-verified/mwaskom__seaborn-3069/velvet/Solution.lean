import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees and no A-reference deep model. The operation under
--  specification — the per-axis finalization decision (which gridlines to show
--  and what view limits to set) — is modeled deeply as pure functions plus the
--  `do` block below. The tick count and the would-be default margin limits are
--  read-only environment observations passed in as inputs; the decision is pure
--  arithmetic over them, so nothing is borrowed from an outside contract and
--  there is no axiom to validate. meta.json G-AX = skip.)
-- axioms-end

-- pure-start
/- The view limits of an axis after finalization, as an exact (lo, hi) pair of
   rationals (half-integer offsets are exact, so `Rat` models them without IEEE
   rounding — mapping.md §2).

   Three cases, in priority order:

     * the consumer pinned explicit limits for this axis  → those limits are
       used verbatim (already unit-resolved into `userLo`/`userHi`);
     * otherwise, on a CATEGORICAL axis the view runs from half a step before
       the first tick to half a step past the last tick — `[-1/2, n - 1/2]` for
       `n` ticks — and that interval is reversed on a vertical axis (so the
       first category sits at the top);
     * otherwise the ordinary default margin limits apply, unchanged.

   This matches the public requirement: a categorical scale "is drawn to ±0.5
   from the first and last tick" and, "if on the y axis, the axis is inverted." -/
def decidedLimits (isCategorical hasUserLimit isY : Bool) (nticks : Nat)
    (userLo userHi autoLo autoHi : Rat) : Rat × Rat :=
  if hasUserLimit then (userLo, userHi)
  else
    if isCategorical then
      if isY then ((nticks : Rat) - 1 / 2, -1 / 2)
      else (-1 / 2, (nticks : Rat) - 1 / 2)
    else (autoLo, autoHi)

/- Whether gridlines remain visible on an axis after finalization. On a
   categorical axis the grid is suppressed regardless of the active style;
   otherwise the style's choice (`gridWasOn`) stands. Matches the public
   requirement that "a grid is not shown" for such scales. -/
def decidedGrid (isCategorical gridWasOn : Bool) : Bool :=
  if isCategorical then false else gridWasOn
-- pure-end

/- What finalization decides for one axis, abstracted to the observable state
   the requirement constrains:

     * `lo`, `hi`        — the view limits actually set on the axis;
     * `gridVisible`     — whether gridlines are shown. -/
structure AxisFinal where
  lo : Rat
  hi : Rat
  gridVisible : Bool
  deriving Inhabited

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Finalizing one axis of a finished figure.

   The inputs are read-only observations of the axis and its scale, and are not
   mutated by the decision (directive 5):

     * `isCategorical`   — the axis carries a categorical (discrete-level) scale;
     * `hasUserLimit`    — the consumer pinned explicit limits for this axis;
     * `isY`             — this is the vertical axis;
     * `nticks`          — the number of major ticks currently on the axis (one
                           per level, for a categorical scale);
     * `userLo`,`userHi` — the consumer's pinned limits, already unit-resolved
                           (meaningful only when `hasUserLimit`);
     * `autoLo`,`autoHi` — the limits the ordinary default margin logic would
                           set (meaningful when the categorical/user cases do
                           not apply);
     * `gridWasOn`       — whether the active style would show gridlines here.

   The result records the view limits set and whether gridlines remain visible.
   A categorical axis with no pinned limits is drawn to ±1/2 of its ticks
   (reversed on the vertical axis) with its grid suppressed; every other axis is
   left to the consumer's pinned limits or the default margin logic, with its
   grid governed by the active style. -/
method finalizeAxis (isCategorical : Bool) (hasUserLimit : Bool) (isY : Bool) (nticks : Nat) (userLo : Rat) (userHi : Rat) (autoLo : Rat) (autoHi : Rat) (gridWasOn : Bool) return (out : AxisFinal)
  ensures out.gridVisible = decidedGrid isCategorical gridWasOn
  ensures out.lo = (decidedLimits isCategorical hasUserLimit isY nticks userLo userHi autoLo autoHi).1
  ensures out.hi = (decidedLimits isCategorical hasUserLimit isY nticks userLo userHi autoLo autoHi).2
  do
    -- impl-start
    -- Start from the limits the prior (user-limit / default-margin) logic
    -- resolves and the grid the active style chose.
    let mut lo : Rat := autoLo
    let mut hi : Rat := autoHi
    let mut grid : Bool := gridWasOn
    if hasUserLimit then
      lo := userLo
      hi := userHi
    else
      pure ()
    -- Categorical special-casing: suppress the grid, and (only when the
    -- consumer did not pin limits) draw to ±1/2 of the tick range, reversed on
    -- the vertical axis.
    if isCategorical then
      grid := false
      if hasUserLimit then
        pure ()
      else
        let edge : Rat := (nticks : Rat) - 1 / 2
        if isY then
          lo := edge
          hi := -1 / 2
        else
          lo := -1 / 2
          hi := edge
    else
      pure ()
    return { lo := lo, hi := hi, gridVisible := grid }
    -- impl-end

prove_correct finalizeAxis by
  loom_solve <;> simp_all [decidedGrid, decidedLimits]
