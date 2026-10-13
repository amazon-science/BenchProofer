import Mathlib
-- imports-end

/-!
A cross-validation routine selects regularization hyper-parameters by scoring
candidate settings across folds, and — in the mode where it does NOT refit a
final model on the full data — summarizes its choice into per-class output
attributes. This bundle models two independent decisions taken while building
those summaries.

First decision: choosing how to aggregate the per-fold coefficient estimates.
There are two aggregation layouts. The choice must be driven by the *effective*
multiclass strategy actually in force — the strategy after configuration has been
resolved to a concrete one — and never by the raw, possibly-unresolved configured
request. Concretely, the per-class aggregation layout is used exactly when the
effective strategy is the per-class one, and the joint layout exactly when the
effective strategy is the joint one. The raw requested setting does not influence
this choice at all: two runs with the same effective strategy aggregate the same
way regardless of how that strategy was originally requested.

Second decision: recording the mixing-ratio summary entry. A mixing ratio between
the two penalty components is only meaningful when the model is run in the
combined-penalty regime. When it is, the recorded entry is the computed mixing
ratio. When it is not, there is no meaningful ratio and the recorded entry is
absent. The entry is fully determined by whether the combined-penalty regime is in
force: it is never the computed ratio outside that regime.
-/

-- axioms-start
-- No unchanged outside callee is CONSUMED as an axiom by either specification.
-- The effective strategy and the computed mixing ratio are produced by unchanged
-- upstream routines; they enter each modeled decision as free inputs, so the
-- decisions are proved correct for ALL of their possible values and no callee
-- property is consumed. Hence no `opaque`/`axiom` declaration is needed.
-- axioms-end

-- pure-start
/-- The effective (already-resolved) multiclass strategy in force. It is always a
concrete strategy — never an unresolved placeholder. -/
inductive EffStrategy where
  | perClass
  | joint
  deriving DecidableEq, Repr

/-- The raw requested multiclass strategy, which may still be an unresolved
placeholder (`autoStrategy`) in addition to the two concrete choices. -/
inductive ReqStrategy where
  | autoStrategy
  | perClass
  | joint
  deriving DecidableEq, Repr

/-- The coefficient-aggregation layout that is selected. -/
inductive AggLayout where
  | perClassLayout
  | jointLayout
  deriving DecidableEq, Repr
-- pure-end

-- post-conditions-start
/-- The selected aggregation layout is pinned solely to the EFFECTIVE strategy:
the per-class layout exactly when the effective strategy is per-class, and the
joint layout exactly when it is joint. The raw requested strategy is intentionally
unconstrained in the relation — the result must not depend on it. -/
def problem_spec_chooseLayout
    (req : ReqStrategy) (eff : EffStrategy) (result : AggLayout) : Prop :=
  (eff = EffStrategy.perClass → result = AggLayout.perClassLayout) ∧
  (eff = EffStrategy.joint → result = AggLayout.jointLayout)
-- post-conditions-end

-- impl-start
-- PRE-PATCH (buggy): the aggregation layout is selected from the RAW requested
-- strategy instead of the effective one. When the request is the unresolved
-- placeholder (`autoStrategy`) but the effective strategy is per-class, this
-- wrongly selects the joint layout.
def implementation_chooseLayout
    (req : ReqStrategy) (eff : EffStrategy) : AggLayout := Id.run do
  let mut layout := AggLayout.jointLayout
  if req = ReqStrategy.perClass then
    layout := AggLayout.perClassLayout
  else
    layout := AggLayout.jointLayout
  return layout
-- impl-end

-- proof-start
theorem correct_chooseLayout :
    ∀ (req : ReqStrategy) (eff : EffStrategy),
      problem_spec_chooseLayout req eff (implementation_chooseLayout req eff) := by
  intro req eff
  unfold problem_spec_chooseLayout implementation_chooseLayout
  simp only [Id.run]
  refine ⟨fun he => ?_, fun he => ?_⟩ <;> subst he <;> rfl
-- proof-end

-- post-conditions-start
/-- The recorded mixing-ratio entry is pinned solely to whether the combined
penalty regime is in force: it is the computed ratio when in that regime, and
absent (`none`) otherwise. The computed ratio is irrelevant outside the regime. -/
def problem_spec_ratioEntry
    (combinedPenalty : Bool) (ratio : ℚ) (result : Option ℚ) : Prop :=
  (combinedPenalty = true → result = some ratio) ∧
  (combinedPenalty = false → result = none)
-- post-conditions-end

-- impl-start
def implementation_ratioEntry
    (combinedPenalty : Bool) (ratio : ℚ) : Option ℚ := Id.run do
  let mut entry : Option ℚ := none
  if combinedPenalty then
    entry := some ratio
  else
    entry := none
  return entry
-- impl-end

-- proof-start
theorem correct_ratioEntry :
    ∀ (combinedPenalty : Bool) (ratio : ℚ),
      problem_spec_ratioEntry combinedPenalty ratio
        (implementation_ratioEntry combinedPenalty ratio) := by
  intro combinedPenalty ratio
  unfold problem_spec_ratioEntry implementation_ratioEntry
  refine ⟨fun hc => ?_, fun hc => ?_⟩ <;>
    simp only [hc] <;> rfl
-- proof-end
