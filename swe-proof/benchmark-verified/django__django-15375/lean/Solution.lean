import Mathlib
-- imports-end

/-!
Resolving an aggregate expression that carries a fallback value for the
empty-result case.

A terminal aggregation (one applied to the whole queryset at once) is marked as
such while it is being resolved. When the aggregate additionally carries a
fallback value to substitute when there is no row to aggregate, resolving it does
not return the bare aggregate: it returns a *wrapper* node — a coalescing node
whose first operand is the aggregate and whose second operand is the fallback —
so that the fallback is supplied at evaluation time.

The wrapper node carries its own "this is a terminal aggregation" marker. For the
resolved expression to be emitted in the correct position, that marker on the
wrapper must agree with the marker the aggregate itself was resolved with: a
wrapper produced while resolving a terminal aggregation must itself be marked as
terminal, and otherwise must not be.

So resolving an aggregate yields a node that is:
  * the coalescing wrapper exactly when a fallback value was supplied, and the
    bare aggregate otherwise; and
  * marked as a terminal aggregation exactly when the aggregate was resolved as a
    terminal aggregation — in both the wrapped and the unwrapped case.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The resolution
-- is modeled over two boolean observables (whether the aggregate is being
-- resolved as a terminal aggregation, and whether a fallback value was supplied);
-- constructing the coalescing wrapper and propagating the terminal marker are
-- modeled directly, so no `opaque`/`axiom` callee contract is required.
-- axioms-end

-- pure-start
/-- The resolved aggregate expression, recording only the two observable aspects
the resolution decides:

  * `wrapped` — the returned node is the coalescing wrapper (a fallback value was
    supplied) rather than the bare aggregate; and
  * `terminal` — the returned node is marked as a terminal aggregation (one
    applied to the whole queryset at once). -/
structure ResolvedExpr where
  wrapped  : Bool
  terminal : Bool
  deriving Repr, DecidableEq
-- pure-end

-- post-conditions-start
/-- The resolved node is fully pinned to the two inputs:

  * it is the coalescing wrapper exactly when a fallback value was supplied
    (`result.wrapped = hasFallback`); and
  * it is marked as a terminal aggregation exactly when the aggregate is being
    resolved as a terminal aggregation (`result.terminal = isTerminalAggregation`)
    — this holds whether or not the node is the wrapper, so the marker is never
    left to default to non-terminal on the wrapper.

Both components are determined for every input, so no output is left free. -/
def problem_spec_resolveAggregate
    (isTerminalAggregation hasFallback : Bool) (result : ResolvedExpr) : Prop :=
  result.wrapped = hasFallback ∧ result.terminal = isTerminalAggregation
-- post-conditions-end

-- impl-start
def implementation_resolveAggregate
    (isTerminalAggregation hasFallback : Bool) : ResolvedExpr := Id.run do
  -- The aggregate is marked as terminal exactly when it is resolved as a
  -- terminal aggregation.
  let mut terminal := isTerminalAggregation
  if !hasFallback then
    -- No fallback supplied: return the bare aggregate node.
    return { wrapped := false, terminal := terminal }
  -- A fallback is supplied: build the coalescing wrapper (which starts out
  -- non-terminal) and carry the aggregate's terminal marker onto it.
  let mut wrapperTerminal := false
  wrapperTerminal := terminal
  return { wrapped := true, terminal := wrapperTerminal }
-- impl-end

-- proof-start
theorem correct_resolveAggregate :
    ∀ (isTerminalAggregation hasFallback : Bool),
      problem_spec_resolveAggregate isTerminalAggregation hasFallback
        (implementation_resolveAggregate isTerminalAggregation hasFallback) := by
  intro isTerminalAggregation hasFallback
  unfold problem_spec_resolveAggregate implementation_resolveAggregate
  cases hasFallback <;> simp [Id.run, pure, bind]
-- proof-end
