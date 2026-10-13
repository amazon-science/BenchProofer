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
  -- The layer under fix now pins its instance memory layout to a fixed attribute
  -- set, so it contributes no per-instance attribute dictionary.
  let mut immutable : Bool := true
  -- Fold the conjunction over every remaining ancestry layer: a single layer that
  -- leaves its layout open reopens the attribute dictionary for the instance.
  for pins in otherLayers do
    immutable := immutable && pins
  return immutable
-- impl-end

-- proof-start
theorem correct_immutableInstances : ∀ otherLayers : List LayerPins,
    problem_spec_immutableInstances otherLayers
      (implementation_immutableInstances otherLayers) := by
  intro otherLayers
  unfold problem_spec_immutableInstances implementation_immutableInstances allPin
  -- Helper: the cleaned `forIn` loop equals a `List.foldl` conjunction (Route B).
  have helper : ∀ (xs : List LayerPins) (init : Bool),
      Id.run (forIn xs init (fun pins r => (pure (ForInStep.yield (r && pins)) : Id _)))
        = xs.foldl (fun r pins => r && pins) init := by
    intro xs
    induction xs with
    | nil => intro init; rfl
    | cons a as ih =>
      intro init
      rw [List.forIn_cons]; simp only [Id.run, bind] at ih ⊢; rw [ih]; rfl
  -- Helper: the fold over the conjunction equals `init && all`.
  have foldl_all : ∀ (xs : List LayerPins) (init : Bool),
      xs.foldl (fun r pins => r && pins) init = (init && xs.all (fun b => b)) := by
    intro xs
    induction xs with
    | nil => intro init; simp
    | cons a as ih =>
      intro init
      rw [List.foldl_cons, List.all_cons, ih, Bool.and_assoc]
  -- Bridge the desugared loop body to the cleaned one (definitional).
  show Id.run (forIn otherLayers true
      (fun pins r => (do pure PUnit.unit; pure (ForInStep.yield (r && pins)) : Id _))) = _
  have hbody : (fun pins r => (do pure PUnit.unit; pure (ForInStep.yield (r && pins)) : Id _))
      = (fun pins r => (pure (ForInStep.yield (r && pins)) : Id _)) := rfl
  rw [hbody, helper, foldl_all, Bool.true_and]
-- proof-end
