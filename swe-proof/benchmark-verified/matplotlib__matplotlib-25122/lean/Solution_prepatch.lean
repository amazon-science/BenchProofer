import Mathlib
-- imports-end

/-!
Computing the normalization factor used to compensate a windowed spectrum for the
energy/amplitude lost to the analysis window.

When a signal segment is multiplied by an analysis window before its spectrum is
taken, the spectrum must be divided by a *window-correction factor* to undo the
scaling the window introduced. The factor is built from the window's own samples
and depends on which spectrum is being produced:

* for an amplitude-style spectrum (a magnitude spectrum, or a complex spectrum),
  the factor is the (signed) total of the window samples;
* for a power-style spectrum:
  - when the spectrum is expressed as a density per unit frequency, the factor is
    the total of the squared window samples;
  - otherwise (power preserved per segment), the factor is the square of the
    signed total of the window samples;
* for a phase-style spectrum (an angle or phase spectrum), no window correction is
  applied (the factor is `1`).

The window samples are real numbers and MAY BE NEGATIVE (for example, windows
whose side lobes dip below zero). The total of the window samples must therefore
be taken with sign — it is the arithmetic sum of the samples, NOT the sum of their
sizes. These two agree for an all-nonnegative window but differ once any sample is
negative.

Stated as an input→output relation (window samples, spectrum kind, density flag) ↦
factor. The implementation and correctness proof are supplied separately.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The window
-- samples enter as plain data (`List Rat`) and the only operations are the
-- reductions that build the factor (a sum and a sum of squares), both modeled
-- deeply below. Hence no `opaque`/`axiom` callee contract is required.

/-- Which spectrum is being produced. Each constructor selects a different
window-correction factor (see `problem_spec_windowCorrectionFactor`). -/
inductive Mode
  | magnitude
  | complex
  | psd
  | angle
  | phase
deriving DecidableEq, Repr
-- axioms-end

-- pure-start
-- (no shared pure helpers needed)
-- pure-end

-- post-conditions-start
/-- The window-correction factor as a function of the window samples, the
spectrum kind, and the density flag. Every case is pinned to the inputs:

* `magnitude` / `complex` → the signed total of the window samples;
* `psd` with `scaleByFreq = true` → the total of the squared samples;
* `psd` with `scaleByFreq = false` → the square of the signed total;
* `angle` / `phase` → `1` (no correction).

The signed total `window.sum` is the discriminating quantity: it is the
arithmetic sum (which may be reduced by negative samples), never the sum of
sample magnitudes. -/
def problem_spec_windowCorrectionFactor
    (window : List Rat) (mode : Mode) (scaleByFreq : Bool) (result : Rat) : Prop :=
  result = (match mode with
    | Mode.magnitude => window.sum
    | Mode.complex   => window.sum
    | Mode.psd       =>
        if scaleByFreq then (window.map (fun w => w * w)).sum
        else window.sum * window.sum
    | Mode.angle     => 1
    | Mode.phase     => 1)
-- post-conditions-end

-- impl-start
def implementation_windowCorrectionFactor
    (window : List Rat) (mode : Mode) (scaleByFreq : Bool) : Rat := Id.run do
  match mode with
  | Mode.magnitude | Mode.complex =>
      -- PRE-PATCH BUG: normalize by the total of the sample MAGNITUDES instead of
      -- the signed total, which over-counts negative samples.
      let mut s : Rat := 0
      for w in window do
        s := s + |w|
      return s
  | Mode.psd =>
      if scaleByFreq then
        let mut sq : Rat := 0
        for w in window do
          sq := sq + |w| * |w|
        return sq
      else
        -- PRE-PATCH BUG: square of the total of the sample MAGNITUDES.
        let mut s : Rat := 0
        for w in window do
          s := s + |w|
        return s * s
  | Mode.angle | Mode.phase =>
      return 1
-- impl-end

-- proof-start
theorem correct_windowCorrectionFactor :
    ∀ (window : List Rat) (mode : Mode) (scaleByFreq : Bool),
      problem_spec_windowCorrectionFactor window mode scaleByFreq
        (implementation_windowCorrectionFactor window mode scaleByFreq) := by
  sorry
-- proof-end
