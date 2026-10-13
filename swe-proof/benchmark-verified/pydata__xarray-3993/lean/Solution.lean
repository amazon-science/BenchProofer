import Mathlib
-- imports-end

/-!
Integrating an array along a coordinate, with a consistent coordinate-selection
argument convention.

The operation integrates the array along one (or more) coordinate(s) using the
trapezoidal rule. The coordinate to integrate along may be supplied in two ways:

  * `coord` — the preferred argument naming the coordinate(s) to use;
  * `dim` — an older alternative spelling of the same choice, kept for
    compatibility but deprecated.

The argument-resolution rules are:

  * supplying BOTH `coord` and `dim` is contradictory and is rejected (an error);
  * supplying ONLY `dim` selects that coordinate to integrate along, but because
    this spelling is on its way out the call additionally signals a
    deprecation notice;
  * otherwise the coordinate named by `coord` (which may itself be absent) is
    used, with no notice.

Once the effective coordinate has been resolved, the integration itself is the
unchanged downstream step: integrating the array along the chosen coordinate.
The result therefore equals that downstream integration applied to whichever
coordinate the rules above select, and the deprecation notice is raised in
exactly the one case described.
-/

-- axioms-start
-- No unchanged outside callee is consumed as a logical contract. The downstream
-- integration step (integrating the array along a resolved coordinate) is left
-- UNIVERSALLY QUANTIFIED as a parameter `integrateAlong : Option α → DS`: the
-- specification holds for EVERY such step, so it pins only that the correctly
-- resolved coordinate reaches it (plus the error / deprecation-notice logic),
-- which is exactly the behavior under specification. Hence no `opaque`/`axiom`
-- callee contract is required.
-- axioms-end

-- pure-start
-- No additional pure helpers are needed: the coordinate selection is expressed
-- directly in the post-condition and the implementation.
-- pure-end

-- post-conditions-start
/-- The outcome of resolving the integration coordinate and integrating.

`α` is the type of a coordinate selector and `DS` the type of an integrated
result. `integrateAlong c` is the unchanged downstream integration of the array
along the (optional) coordinate `c`. The result is `Except.error ()` when the
call is rejected, or `Except.ok (value, warned)` where `value` is the integrated
result and `warned` records whether a deprecation notice was raised.

The result is fully pinned for every input (directive 5 frame):

  * if both `coord` and `dim` are supplied, the call is rejected;
  * if only `dim` is supplied, the array is integrated along `dim` and a
    deprecation notice is raised (`warned = true`);
  * if `dim` is absent, the array is integrated along `coord` (which may itself
    be absent) and no notice is raised (`warned = false`).

These three antecedents are mutually exclusive and exhaustive, so no component
of the result is left free. -/
def problem_spec_integrate {α DS : Type}
    (integrateAlong : Option α → DS) (coord dim : Option α)
    (result : Except Unit (DS × Bool)) : Prop :=
  (coord.isSome = true ∧ dim.isSome = true →
      result = Except.error ()) ∧
  (dim.isSome = true ∧ coord = none →
      result = Except.ok (integrateAlong dim, true)) ∧
  (dim = none →
      result = Except.ok (integrateAlong coord, false))
-- post-conditions-end

-- impl-start
def implementation_integrate {α DS : Type}
    (integrateAlong : Option α → DS) (coord dim : Option α) :
    Except Unit (DS × Bool) := Id.run do
  if dim.isSome && coord.isSome then
    return Except.error ()
  let mut effective := coord
  let mut warned := false
  if dim.isSome && coord.isNone then
    effective := dim
    warned := true
  return Except.ok (integrateAlong effective, warned)
-- impl-end

-- proof-start
theorem correct_integrate {α DS : Type}
    (integrateAlong : Option α → DS) (coord dim : Option α) :
    problem_spec_integrate integrateAlong coord dim
      (implementation_integrate integrateAlong coord dim) := by
  refine ⟨?_, ?_, ?_⟩ <;> intro h <;>
    cases coord <;> cases dim <;>
    simp_all [implementation_integrate, Id.run] <;> rfl
-- proof-end
