import Mathlib
-- imports-end

/-!
Forwarding a flush request through a thin stream wrapper to the stream it wraps.

A wrapper sits in front of an underlying output stream and relays operations to
it. When a caller asks the wrapper to flush, the request must reach the
underlying stream so that any buffered output is pushed out immediately, rather
than being held back until later.

The underlying stream is observed through two things:

  * whether it actually supports flushing at all; and
  * how many times its own flush operation has been invoked.

The desired behavior of a single flush request on the wrapper:

  * if the underlying stream supports flushing, its flush operation is invoked
    exactly once (so a caller's flush is honored immediately);
  * if it does not support flushing, nothing happens to it;
  * either way, whether the stream supports flushing is itself unchanged.
-/

-- axioms-start
-- No unchanged outside callee is consumed as an axiom. The two observable
-- operations involved — testing whether the underlying stream supports flushing,
-- and invoking that stream's flush once — are modeled structurally over the
-- stream's observables (its flush-support flag and its flush-invocation count),
-- so the specification needs no `opaque`/`axiom` callee contract.
-- axioms-end

-- pure-start
/-- The underlying stream, restricted to the two touched observables:
* `hasFlush` — whether the stream supports a flush operation at all;
* `flushCount` — how many times the stream's own flush operation has been
  invoked. -/
structure OutStream where
  hasFlush : Bool
  flushCount : Nat
deriving DecidableEq
-- pure-end

-- post-conditions-start
/-- The underlying stream's observable state after one flush request on the
wrapper is fully pinned to its prior state:

  * the support flag is unchanged (`result.hasFlush = s.hasFlush`);
  * the flush-invocation count goes up by exactly one when the stream supports
    flushing, and is left unchanged otherwise. -/
def problem_spec_flush (s : OutStream) (result : OutStream) : Prop :=
  result.hasFlush = s.hasFlush ∧
  result.flushCount = (if s.hasFlush then s.flushCount + 1 else s.flushCount)
-- post-conditions-end

-- impl-start
def implementation_flush (s : OutStream) : OutStream := Id.run do
  -- PRE-PATCH (buggy): the wrapper's flush request never reaches the underlying
  -- stream — the request is absorbed as a no-op even when the stream supports
  -- flushing, so its flush operation is never invoked.
  return s
-- impl-end

-- proof-start
theorem correct_flush :
    ∀ (s : OutStream), problem_spec_flush s (implementation_flush s) := by
  intro s
  unfold problem_spec_flush implementation_flush
  simp only [Id.run]
  by_cases h : s.hasFlush <;> simp [h]
-- proof-end
