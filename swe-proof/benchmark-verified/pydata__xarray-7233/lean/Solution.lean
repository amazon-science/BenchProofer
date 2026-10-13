import Mathlib
-- imports-end

/-!
Determining which names remain coordinates after a grouping/reshaping operation
that splits a dimension into two.

A labelled container carries some named variables; a subset of those names are
distinguished as *coordinates*. A reshaping operation rebuilds the container —
each reshaped dimension is replaced by a pair of new dimensions — and then must
decide which names are coordinates of the result.

The operation is given two pieces of information:

* the names of the dimensions being reshaped, and
* the names that were coordinates beforehand.

It reports the names that are coordinates afterwards. The guarantee is that the
coordinate set is *preserved exactly*: every name that was a coordinate before
remains a coordinate, and no other name becomes one. In particular the outcome
does not depend on which dimensions happen to be reshaped — a name that was a
coordinate but is unrelated to any reshaped dimension is still a coordinate of
the result.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The behavior
-- modeled — deciding which names are coordinates of the result — is computed
-- DEEPLY over the observable inputs (the names being reshaped and the names that
-- were coordinates), as a filter (the common names) followed by a union with the
-- prior coordinate names. SPEC_GUIDE §3 forbids axiomatizing a deeply-modeled
-- changed op, so no `opaque`/`axiom` callee contract is needed.
-- axioms-end

-- pure-start
-- No shared pure helpers are needed; the computation is inlined in the impl.
-- pure-end

-- post-conditions-start
/-- The names reported as coordinates of the result are exactly the names that
were coordinates beforehand: a name is a coordinate of the result iff it was a
coordinate before. This pins the coordinate set to be preserved in full — no
prior coordinate is dropped and no new name is introduced — regardless of which
dimensions are being reshaped. -/
def problem_spec_retainedCoordNames
    (reshapedDims priorCoordNames : List String) (result : List String) : Prop :=
  ∀ name, name ∈ result ↔ name ∈ priorCoordNames
-- post-conditions-end

-- impl-start
def implementation_retainedCoordNames
    (reshapedDims priorCoordNames : List String) : List String := Id.run do
  -- the names common to the reshaped dimensions and the prior coordinates
  let common := reshapedDims.filter (fun d => priorCoordNames.contains d)
  -- together with every prior coordinate name
  let result := common ++ priorCoordNames
  return result
-- impl-end

-- proof-start
theorem correct_retainedCoordNames :
    ∀ (reshapedDims priorCoordNames : List String),
      problem_spec_retainedCoordNames reshapedDims priorCoordNames
        (implementation_retainedCoordNames reshapedDims priorCoordNames) := by
  intro reshapedDims priorCoordNames
  unfold problem_spec_retainedCoordNames implementation_retainedCoordNames
  intro name
  simp only [Id.run, pure, List.mem_append,
    List.mem_filter, List.elem_eq_mem, decide_eq_true_eq]
  constructor
  · rintro (⟨_, hc⟩ | h)
    · exact hc
    · exact h
  · intro h
    exact Or.inr h
-- proof-end
