import Mathlib
-- imports-end

/-!
Abstract behavior under specification.

A preparation step normalizes an incoming object before it is stored. Some
objects are recognized *wrapper containers* that merely re-expose an underlying
payload; for those, the step must replace the object by that underlying payload.
Every other object — including ones that incidentally expose a payload — must be
stored unchanged.
-/

-- axioms-start
-- No unchanged callee needs an axiomatized contract: the changed decision is
-- modeled deeply (a structural case split on the object), not assumed.
-- axioms-end

-- pure-start
/-- An incoming object, modeled by the only two properties the preparation step
observes: whether it is a recognized wrapper container, and the underlying
payload it exposes (if any). The payload is itself such an object, since the
result is stored the same way as the original. -/
inductive Obj where
  | node (isContainer : Bool) (payload : Option Obj)

/-- Whether the object is a recognized wrapper container kind. -/
def Obj.isContainer : Obj → Bool
  | .node c _ => c

/-- The underlying payload the object exposes, if any. -/
def Obj.payload : Obj → Option Obj
  | .node _ p => p
-- pure-end

-- post-conditions-start
/-- The prepared object: a recognized wrapper container is replaced by its
underlying payload; every other object (even one that exposes a payload) is kept
unchanged. -/
def problem_spec_prepare (data : Obj) (result : Obj) : Prop :=
  (data.isContainer = true  → result = data.payload.getD data) ∧
  (data.isContainer = false → result = data)
-- post-conditions-end

-- impl-start
def implementation_prepare (data : Obj) : Obj := Id.run do
  let mut result := data
  if data.isContainer then
    result := data.payload.getD data
  return result
-- impl-end

-- proof-start
theorem correct_prepare : ∀ data : Obj,
    problem_spec_prepare data (implementation_prepare data) := by
  intro data
  refine ⟨fun h => ?_, fun h => ?_⟩
  · simp only [implementation_prepare, Id.run, h, if_true, bind_pure_comp,
      map_pure]
    rfl
  · simp only [implementation_prepare, Id.run, h, Bool.false_eq_true,
      if_false, bind_pure_comp, map_pure]
    rfl
-- proof-end
