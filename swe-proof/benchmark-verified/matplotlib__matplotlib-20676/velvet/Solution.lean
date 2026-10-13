import Velvet.Std
-- imports-end

/- Total correctness: the real marker-placement choice is a straight-line pure
   computation (an orientation dispatch over two already-known limit pairs)
   that always terminates and returns, so a diverging implementation must NOT
   satisfy this spec. Partial correctness would let a non-terminating body
   discharge the postcondition vacuously. -/
set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms and no deep-model references. The two unchanged callees
   this slice relies on — the queries that report the lower/upper view limits of
   the two coordinate axes — are pure value sources whose results are taken as
   the inputs `horizontalLimits` / `verticalLimits` of the modeled operation
   (the order-preserving `(lower, upper)` pair of each axis). Their provenance
   and the input bijection are recorded in mapping.md; the end-to-end behaviour
   is differential-tested by conformance_check.py (G-CONF). -/
-- axioms-end

-- pure-start
/- The two coordinate axes a planar drawing surface exposes. The orientation of
   an interactive range picker selects which axis its movable boundary markers
   live on. -/
inductive Orientation where
  | horizontal
  | vertical
  deriving DecidableEq

/- The intended initial placement of the two boundary markers: the markers must
   start on the limits of the axis that matches the picker's orientation — the
   lower/upper view limit pair of that axis — so that introducing the markers
   leaves the view of every axis exactly where it already was. The opposite
   axis's limits and the picker's current (possibly degenerate) selection span
   never enter this choice. -/
def initialMarkerSpec
    (o : Orientation) (horizontalLimits verticalLimits : Rat × Rat) : Rat × Rat :=
  match o with
  | .horizontal => horizontalLimits
  | .vertical   => verticalLimits

@[grind] lemma initialMarkerSpec_h (hl vl : Rat × Rat) :
    initialMarkerSpec .horizontal hl vl = hl := rfl
@[grind] lemma initialMarkerSpec_v (hl vl : Rat × Rat) :
    initialMarkerSpec .vertical hl vl = vl := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- `currentSpan` is the picker's present selection span at the moment the
   markers are introduced. It is read-only and must NOT influence the initial
   marker placement; the postcondition pins the result to the orientation-
   matched axis limits alone, so any implementation that lets `currentSpan`
   leak into the result fails to verify. -/
method initialMarkerPositions
    (o : Orientation) (horizontalLimits : Rat × Rat) (verticalLimits : Rat × Rat)
    (currentSpan : Rat × Rat)
    return (out : Rat × Rat)
  ensures out = initialMarkerSpec o horizontalLimits verticalLimits
  do
    -- impl-start
    -- Choose the boundary-marker positions by orientation: the limits of the
    -- horizontal axis for a horizontal picker, the limits of the vertical axis
    -- otherwise. `currentSpan` is deliberately unused.
    let positions : Rat × Rat :=
      match o with
      | .horizontal => horizontalLimits
      | .vertical   => verticalLimits
    return positions
    -- impl-end

prove_correct initialMarkerPositions by
  loom_solve
