import Mathlib
-- imports-end

/-!
Selecting array elements by label from a mapping of dimension names to labels.

A label-based selection is requested as a mapping `{dimension-name → label}`. The
whole mapping describes WHICH position to select along each named dimension. The
selection routine that performs the lookup also accepts, separately, a few
optional *matching* parameters that tune how labels are matched (an inexact-match
mode, a numeric matching tolerance, and a coordinate-dropping flag); when a
selection is requested purely by a mapping of dimensions, none of those tuning
parameters is being set.

The desired behavior: building the selection from such a mapping must treat the
mapping *as a whole* as the dimension→label selection, so that EVERY entry of the
mapping is used to select along its dimension — regardless of what that dimension
happens to be named — and none of the optional matching parameters is populated
from the mapping. In particular, a dimension whose name happens to coincide with
the name of one of those optional matching parameters must still be used as an
ordinary selector, not diverted into tuning the matcher.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The behavior
-- modeled is the construction of the selection request from the input mapping;
-- it is modeled structurally over the mapping itself, so no `opaque`/`axiom`
-- callee contract is needed. The downstream lookup routine that consumes the
-- request is out of scope.
-- axioms-end

-- pure-start
/-- A tick-label value supplied for one dimension. Selection routing never
inspects the value, so it is modeled by its representation. -/
abbrev Label := String

/-- The argument bundle handed to the label-based selection routine: the
dimension→label `indexers` mapping plus the three optional matching parameters
(`none` means "left at its default / not supplied"). -/
structure SelArgs where
  indexers : List (String × Label)
  method : Option Label
  tolerance : Option Label
  drop : Option Label
deriving DecidableEq, Repr

/-- The selection request that treats the whole mapping as the dimension→label
selection: the mapping becomes `indexers` verbatim and no optional matching
parameter is populated. -/
def canonicalSelArgs (key : List (String × Label)) : SelArgs :=
  { indexers := key, method := none, tolerance := none, drop := none }
-- pure-end

-- post-conditions-start
/-- The selection request built from the mapping uses the entire mapping as the
dimension→label `indexers` (every entry preserved, in order) and leaves all three
optional matching parameters unset. Each output component is pinned: `indexers`
equals the input mapping and `method`/`tolerance`/`drop` are all `none`. -/
def problem_spec_labelSelection
    (key : List (String × Label)) (result : SelArgs) : Prop :=
  result = canonicalSelArgs key
-- post-conditions-end

-- impl-start
def implementation_labelSelection (key : List (String × Label)) : SelArgs := Id.run do
  let mut indexers : List (String × Label) := []
  for entry in key do
    indexers := indexers ++ [entry]
  return { indexers := indexers, method := none, tolerance := none, drop := none }
-- impl-end

-- proof-start
/-- The `for entry in key do indexers := indexers ++ [entry]` loop accumulates
the entries onto the initial list, i.e. it computes `init ++ key`. Generalized
over the accumulator so the induction goes through. -/
theorem labelSelection_loop (key : List (String × Label)) (init : List (String × Label)) :
    (forIn key init
        (fun entry r => do pure PUnit.unit; pure (ForInStep.yield (r ++ [entry])))
      : Id (List (String × Label)))
      = pure (init ++ key) := by
  induction key generalizing init with
  | nil => simp
  | cons a as ih =>
    rw [List.forIn_cons]
    simp only [pure_bind] at ih ⊢
    rw [ih]
    simp

theorem correct_labelSelection :
    ∀ (key : List (String × Label)),
      problem_spec_labelSelection key (implementation_labelSelection key) := by
  intro key
  unfold problem_spec_labelSelection implementation_labelSelection canonicalSelArgs
  simp only [Id.run]
  rw [labelSelection_loop]
  rfl
-- proof-end
