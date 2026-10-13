import Mathlib
-- imports-end

/-!
Manually stepping through the moving windows of a one-dimensional sequence.

A moving-window view of a 1-D sequence of length `n`, with a given window
length `w` and an alignment flag, exposes one sub-window per position. The
exported behavior modeled here is *which contiguous slice of the input each
position sees*:

* When alignment is requested, each window is centered on its position: the
  positions are shifted so that the window straddles the position symmetrically
  (the leading half-window worth of positions are anchored at the start of the
  sequence).
* When alignment is not requested, each window is right-anchored: position `i`
  sees the slice ending just past `i`.

The slice for a position is taken from the input sequence in order, so the
resulting list of windows is fully determined by the input sequence, the window
length, and the alignment flag.
-/

-- axioms-start
-- (none) — the slice extraction is modeled directly as a list operation.
-- axioms-end

-- pure-start
/-- The forward shift applied to the window positions: half of the window
length (rounded up) under centered alignment, otherwise one. -/
def winOffset (window : Nat) (center : Bool) : Nat :=
  if center then (window + 1) / 2 else 1

/-- The start index of the window at position `i`: the right edge `offset + i`
pulled back by the window length, clamped to the start of the sequence for the
leading positions. -/
def winStart (window offset i : Nat) : Nat :=
  if i + offset < window then 0 else (offset + i) - window

/-- The contiguous slice of `xs` seen by the window at position `i`. -/
def windowAt (xs : List Int) (window : Nat) (center : Bool) (i : Nat) : List Int :=
  let offset := winOffset window center
  let stop := offset + i
  let start := winStart window offset i
  (xs.drop start).take (stop - start)
-- pure-end

-- post-conditions-start
/-- The list of moving windows: one entry per position of the input sequence,
in order, each entry the contiguous slice that position sees. Frame: the result
length equals the input length, and every window is a slice of the input taken
from the position dictated by the window length and the alignment flag, so the
whole result is determined by `xs`, `window`, and `center`. -/
def problem_spec_rollingWindows
    (xs : List Int) (window : Nat) (center : Bool)
    (result : List (List Int)) : Prop :=
  result = (List.range xs.length).map (windowAt xs window center)
-- post-conditions-end

-- impl-start
def implementation_rollingWindows
    (xs : List Int) (window : Nat) (center : Bool) :
    List (List Int) := Id.run do
  let n := xs.length
  let offset := if center then (window + 1) / 2 else 1
  let mut out : Array (List Int) := #[]
  for i in [0:n] do
    let stop := offset + i
    let start := if i + offset < window then 0 else stop - window
    out := out.push ((xs.drop start).take (stop - start))
  return out.toList
-- impl-end

-- proof-start
theorem correct_rollingWindows :
    ∀ (xs : List Int) (window : Nat) (center : Bool),
      1 ≤ window →
      problem_spec_rollingWindows xs window center
        (implementation_rollingWindows xs window center) := by
  intro xs window center _
  unfold problem_spec_rollingWindows implementation_rollingWindows
  simp only [Id.run, Std.Range.forIn_eq_forIn_range', Std.Range.size]
  norm_num
  rw [← List.range_eq_range']
  apply List.map_congr_left
  intro i _
  simp only [windowAt, winOffset, winStart]
-- proof-end
