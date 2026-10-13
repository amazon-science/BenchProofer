import Mathlib
-- imports-end

/-!
Choosing which resolution value to record when a figure's drawing state is
serialized for later restoration.

A figure has a current working resolution (dots per inch). On some display
surfaces this working resolution is temporarily rescaled to match the surface's
pixel density; when that happens the figure also keeps a record of its baseline
resolution — the resolution it had before any such rescaling. A figure that has
never been rescaled carries no such baseline record.

When the figure's state is captured for serialization, the resolution value
written into that state should be the figure that will be reconstructed from it.
The desired rule is:

  * if the figure carries a recorded baseline resolution, the serialized state
    records that baseline value;
  * otherwise (no baseline was ever recorded) the serialized state records the
    figure's current working resolution.

This keeps the resolution that round-trips through serialization equal to the
baseline whenever one is known, independent of any display-surface rescaling in
effect at the moment of capture.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The current
-- working resolution and the optional recorded baseline resolution both enter
-- as plain data (the baseline modeled as `Option`), and the only operation is
-- the baseline-or-current selection, modeled directly below. Hence no
-- `opaque`/`axiom` callee contract is required.
-- axioms-end

-- pure-start
-- (no shared pure helpers needed)
-- pure-end

-- post-conditions-start
/-- The recorded resolution value is fully pinned to the inputs:

  * if a baseline resolution `d` is recorded, the result is exactly `d`
    (the baseline is recorded, whatever the current working resolution is);
  * if no baseline is recorded, the result is exactly the current working
    resolution.

Both cases together determine the result for every input, so no output is left
free. -/
def problem_spec_serializedFigureDpi
    (currentDpi : Rat) (baselineDpi : Option Rat) (result : Rat) : Prop :=
  (∀ d, baselineDpi = some d → result = d) ∧
  (baselineDpi = none → result = currentDpi)
-- post-conditions-end

-- impl-start
def implementation_serializedFigureDpi
    (currentDpi : Rat) (baselineDpi : Option Rat) : Rat := Id.run do
  let mut value := currentDpi
  match baselineDpi with
  | some d => value := d
  | none   => pure ()
  return value
-- impl-end

-- proof-start
theorem correct_serializedFigureDpi :
    ∀ (currentDpi : Rat) (baselineDpi : Option Rat),
      problem_spec_serializedFigureDpi currentDpi baselineDpi
        (implementation_serializedFigureDpi currentDpi baselineDpi) := by
  intro currentDpi baselineDpi
  unfold problem_spec_serializedFigureDpi implementation_serializedFigureDpi
  cases baselineDpi with
  | none =>
    refine ⟨?_, ?_⟩
    · intro d h; exact absurd h (by simp)
    · intro _; rfl
  | some d =>
    refine ⟨?_, ?_⟩
    · intro d' h; simp only [Option.some.injEq] at h; subst h; rfl
    · intro h; exact absurd h (by simp)
-- proof-end
