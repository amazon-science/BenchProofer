import Mathlib
-- imports-end

/-!
Resolving a possibly-absent measurement context before a placement computation.

A placement routine positions a sub-region inside a host region. To do its
arithmetic it needs a *measurement context* — an object that lets it turn
abstract sizes into concrete extents. Callers may either hand this context in
explicitly or omit it (passing "nothing"), leaving the routine to obtain one on
its own.

Every host region is attached to a drawing surface, and that surface can always
furnish a measurement context. So when no context is supplied, the routine has a
guaranteed source to fall back on: the context belonging to the host's drawing
surface.

The routine's arithmetic proceeds in two consecutive steps, and each step has to
be handed a measurement context of its own:

  * an EXTENT step, which measures how large the sub-region wants to be, and
  * a PLACEMENT step, which turns that size into an offset inside the host
    region.

The desired behavior at the start of the routine: settle on exactly one concrete
measurement context, and hand THAT one to both steps.

  * If the caller supplied a context, both steps are handed that one unchanged.
  * If the caller supplied nothing, both steps are handed the context obtained
    from the host's drawing surface instead.

Every step must therefore receive a genuine, present context — never "nothing" —
because neither the extent arithmetic nor the placement arithmetic can proceed
without one. Handing "nothing" to a step when the caller omitted the context is
exactly the failure this contract rules out, and so is settling the question for
one step while leaving the other still holding "nothing": one resolution, shared
by every step, is what the contract demands.

We model the supplied context as an optional opaque token (`none` ↔ "nothing
supplied"), the surface's always-available context as a plain token, and the
result as the pair of contexts the two steps are handed, in order (each
necessarily present).
-/

-- axioms-start
/-- The opaque measurement context consumed by the placement computation. Its
internal structure is irrelevant to the resolution behavior modeled here: all
that matters is WHICH context each step is handed, not what the context
measures. The caller-supplied context is optional (`none` denotes "the caller
supplied nothing"); the drawing surface's own context is always present. -/
opaque RenderContext : Type
-- axioms-end

-- pure-start
-- No additional pure helpers are required: the modeled behavior is the single
-- resolution of which measurement context the routine settles on, together with
-- the contexts its two consecutive steps are handed (`.1` the extent step, `.2`
-- the placement step).
-- pure-end

-- post-conditions-start
/-- Resolving the measurement context at the start of the placement routine. The
result is the pair of contexts the routine hands to its two consecutive steps —
`result.1` to the extent step, `result.2` to the placement step — and BOTH are
always present (`some _`): when the caller supplied a context each step receives
that very context, and when the caller supplied nothing each step receives the
context obtained from the host's drawing surface. Pinned exactly to the two
inputs, componentwise — no part of either component left free. In particular the
"nothing supplied" case is forced to the surface's context for EVERY step, so a
routine that settles the question for the earlier step and lets the later one
proceed with "nothing" is excluded just as firmly as one that resolves neither. -/
def problem_spec_resolveRenderContext
    (suppliedContext : Option RenderContext) (surfaceContext : RenderContext)
    (result : Option RenderContext × Option RenderContext) : Prop :=
  result.1 = some (suppliedContext.getD surfaceContext) ∧
  result.2 = some (suppliedContext.getD surfaceContext)
-- post-conditions-end

-- impl-start
def implementation_resolveRenderContext
    (suppliedContext : Option RenderContext) (surfaceContext : RenderContext) :
    Option RenderContext × Option RenderContext := Id.run do
  -- The caller-supplied context is used as-is and the "nothing supplied" case is
  -- never resolved against the host's drawing surface, so either step can be
  -- handed "nothing" with no concrete context for its arithmetic.
  let mut ctx := suppliedContext
  let extentStepContext := ctx
  let placementStepContext := ctx
  return (extentStepContext, placementStepContext)
-- impl-end

-- proof-start
-- Gold proof body carried over from Solution.lean (SPEC_GUIDE §1.1). Against this
-- impl it cannot close: when the caller supplied nothing
-- (`suppliedContext = none`), the impl hands `none` to both steps while the spec
-- requires the resolved value `some surfaceContext` for each of them.
theorem correct_resolveRenderContext :
    ∀ (suppliedContext : Option RenderContext) (surfaceContext : RenderContext),
      problem_spec_resolveRenderContext suppliedContext surfaceContext
        (implementation_resolveRenderContext suppliedContext surfaceContext) := by
  intro suppliedContext surfaceContext
  unfold problem_spec_resolveRenderContext implementation_resolveRenderContext
  cases suppliedContext <;> exact ⟨rfl, rfl⟩
-- proof-end
