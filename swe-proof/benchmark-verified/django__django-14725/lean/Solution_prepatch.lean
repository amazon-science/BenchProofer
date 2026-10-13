import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee needs an opaque signature here. The function under spec
-- composes the result lists of two collaborators: the list of persisted
-- already-existing objects, and the list of persisted freshly-created objects.
-- Those two lists are the genuine input carriers of this function (modeled as
-- the `existing` / `new` arguments — an R refinement, mapping.md), so they are
-- not axiomatized and not opaque. The proof agent may add `_prop` axioms only
-- if stuck (none are expected).
-- axioms-end

-- pure-start
-- No auxiliary pure helpers are required: the behavior is a single selection
-- between two ways of combining the two input lists.
-- pure-end

-- post-conditions-start
/-- The returned collection of persisted objects.

When the formset is restricted to editing the objects it already manages, the
result is exactly the list of persisted already-present objects, in order, and
nothing else — no freshly-created objects are added. Otherwise the result is the
list of persisted already-present objects followed by the list of persisted
freshly-created objects, in order.

Both components are pinned to the inputs in every case: in the restricted mode
the freshly-created list contributes nothing, and in the unrestricted mode it is
appended after the existing list with order preserved. -/
def problem_spec_saveFormset {α : Type}
    (editOnly : Bool) (existing new : List α) (result : List α) : Prop :=
  result = if editOnly then existing else existing ++ new
-- post-conditions-end

-- impl-start
-- Pre-patch (buggy) skeleton: the restricted-mode selection does not exist, so
-- the freshly-created objects are ALWAYS appended, even when the formset is
-- meant to only edit the objects it already manages.
def implementation_saveFormset {α : Type}
    (editOnly : Bool) (existing new : List α) : List α := Id.run do
  return existing ++ new
-- impl-end

-- proof-start
theorem correct_saveFormset {α : Type} :
    ∀ (editOnly : Bool) (existing new : List α),
      problem_spec_saveFormset editOnly existing new
        (implementation_saveFormset editOnly existing new) := by
  intro editOnly existing new
  unfold problem_spec_saveFormset implementation_saveFormset
  simp   -- carries the gold proof shape; UNCLOSABLE against the buggy impl (G-DIFF)
-- proof-end
