import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee needs an opaque signature: the instance-layout rule is a
-- pure fold over the type's ancestry layers, modeled DEEPLY below (no outside
-- callee is invoked, hence no consumed axiom and no A-reference). The proof agent
-- may add `_prop` axioms only if genuinely stuck.
-- axioms-end

-- pure-start
/-- One ancestry layer of a type contributes a per-instance attribute dictionary
unless it pins its instance memory layout to a closed, predeclared attribute set.
`b = true` means the layer pins its layout (adds no attribute dictionary);
`b = false` means it leaves the layout open (so instances would gain an attribute
dictionary, i.e. become freely mutable). -/
abbrev LayerPins := Bool

/-- An instance is immutable (carries no per-instance attribute dictionary) iff
EVERY ancestry layer pins its memory layout. This is the conjunction-fold of the
per-layer pinning flags. -/
def allPin (layers : List LayerPins) : Bool := layers.all (fun b => b)
-- pure-end

-- post-conditions-start
/-- Given the layout-pinning flags of the ancestry layers (`otherLayers`), the
instance is immutable (`result = true`) exactly when all of those layers pin
their memory layout. The result is a single boolean, fully determined by the
inputs (frame: nothing is left unconstrained). -/
def problem_spec_immutableInstances (otherLayers : List LayerPins) (result : Bool) : Prop :=
  result = allPin otherLayers
-- post-conditions-end

-- impl-start
def implementation_immutableInstances (otherLayers : List LayerPins) : Bool := Id.run do
  -- PRE-PATCH BUG: the layer under fix leaves its instance memory layout OPEN, so
  -- it contributes a per-instance attribute dictionary regardless of the other
  -- layers — the accumulator starts `false`.
  let mut immutable : Bool := false
  for pins in otherLayers do
    immutable := immutable && pins
  return immutable
-- impl-end

-- proof-start
theorem correct_immutableInstances : ∀ otherLayers : List LayerPins,
    problem_spec_immutableInstances otherLayers
      (implementation_immutableInstances otherLayers) := by
  sorry   -- carries the gold proof body; UNCLOSABLE against the buggy impl (G-DIFF)
-- proof-end
