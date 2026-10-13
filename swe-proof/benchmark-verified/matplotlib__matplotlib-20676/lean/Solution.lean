import Mathlib
-- imports-end

/-!
Placing the initial boundary markers of an interactive range selector.

An interactive one-dimensional range selector draws a pair of movable boundary
marker lines on a plotting axis. When the selector is first set up, those two
marker lines have to be given an initial pair of positions, expressed in the
axis' data coordinates along the selection direction (the horizontal axis for a
horizontal selector, the vertical axis for a vertical selector).

Each marker line is drawn at its given coordinate, and drawing a line at a
coordinate that lies outside the axis' current visible range would force the
visible range to grow to include it. The desired behavior is therefore that
setting up the selector must leave the axis' visible range exactly as it was: the
initial marker positions are chosen to be the axis' current view bounds (its
lower and upper visible limits) along the selection direction. Reading the marker
positions back then returns that same pair.

So the selected pair of initial marker positions equals:

  * the axis' current view bounds along the horizontal axis, for a horizontal
    selector;
  * the axis' current view bounds along the vertical axis, for a vertical
    selector.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The placement
-- is modeled DEEPLY as a pure selection between the two candidate coordinate
-- pairs (the axis' horizontal vs. vertical view bounds), governed only by the
-- selection direction, so no `opaque`/`axiom` callee contract is needed. The
-- marker container is an identity pass-through of the positions it is given
-- (reading them back returns the same pair), an `I` refinement, not an axiom.
-- axioms-end

-- pure-start
/-- The direction along which the range selector operates. -/
inductive SelectDirection where
  | horizontal
  | vertical
deriving DecidableEq, Repr

/-- The inputs the initial-position choice reads:

* `axis` — the selection direction;
* `selectorSpan` — the selector's own current span (its lower/upper extent);
* `xViewBounds` — the axis' current view bounds (lower, upper) along the
  horizontal axis;
* `yViewBounds` — the axis' current view bounds along the vertical axis.

Coordinates are exact rationals: the choice never does arithmetic on them, it
only selects which existing pair to use, so the exact ordered field keeps
equality decidable. -/
structure MarkerSetup where
  axis : SelectDirection
  selectorSpan : ℚ × ℚ
  xViewBounds : ℚ × ℚ
  yViewBounds : ℚ × ℚ
deriving Repr

/-- The initial marker positions: the axis' current view bounds along the
selection direction. -/
def initialMarkers (inp : MarkerSetup) : ℚ × ℚ :=
  match inp.axis with
  | SelectDirection.horizontal => inp.xViewBounds
  | SelectDirection.vertical => inp.yViewBounds
-- pure-end

-- post-conditions-start
/-- The pair of initial marker positions is exactly the axis' current view bounds
along the selection direction — the horizontal view bounds for a horizontal
selector, the vertical view bounds for a vertical selector. Pinning it to a view
bound (rather than the selector's own span) is what leaves the axis' visible
range undisturbed. -/
def problem_spec_initialMarkers
    (inp : MarkerSetup) (result : ℚ × ℚ) : Prop :=
  (inp.axis = SelectDirection.horizontal → result = inp.xViewBounds) ∧
  (inp.axis = SelectDirection.vertical → result = inp.yViewBounds)
-- post-conditions-end

-- impl-start
def implementation_initialMarkers (inp : MarkerSetup) : ℚ × ℚ := Id.run do
  let positions ←
    if inp.axis = SelectDirection.horizontal then
      pure inp.xViewBounds
    else
      pure inp.yViewBounds
  return positions
-- impl-end

-- proof-start
theorem correct_initialMarkers :
    ∀ (inp : MarkerSetup),
      problem_spec_initialMarkers inp
        (implementation_initialMarkers inp) := by
  intro inp
  refine ⟨fun h => ?_, fun h => ?_⟩ <;>
    simp only [implementation_initialMarkers, Id.run, h, if_true, pure] <;> rfl
-- proof-end
