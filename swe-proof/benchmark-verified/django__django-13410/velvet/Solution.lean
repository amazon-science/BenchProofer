import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms and no deep-model references. The desired behaviour
   concerns only how a boolean success indicator is computed from the OUTCOME of
   the underlying operating-system lock primitive. That outcome is modeled
   directly as the input `LockOutcome` — an R-refinement of "the primitive
   completed normally" versus "under a non-blocking request the resource is
   already held". The primitive itself is unchanged; its outcome ↔ input
   correspondence, and the full decision, are validated against the real
   primitive by conformance_check.py (G-CONF). Nothing is axiomatized, so there
   is no axiom_check.py (G-AX = skip). -/
-- axioms-end

-- pure-start
/- The two observable outcomes of one call to the underlying operating-system
   lock primitive, as the caller perceives them:
   * `succeeded` — the primitive completed normally and the operation took
                   effect (on this path the primitive yields no value).
   * `contended` — under a non-blocking request the resource is already held,
                   so the primitive signals that the operation could not be
                   completed immediately. -/
inductive LockOutcome where
  | succeeded
  | contended
  deriving DecidableEq, Inhabited

/- The boolean success indicator an acquisition reports: it reports success
   exactly when the underlying primitive completed normally, and reports failure
   when a non-blocking request found the resource already held. The indicator is
   a definite boolean — completing normally is reported as `true`, never
   conflated with the primitive's no-value normal-completion result. -/
def acquiredOk (outcome : LockOutcome) : Bool :=
  decide (outcome = LockOutcome.succeeded)
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Acquire a lock and report, as a definite boolean, whether it was obtained.
   Given the outcome of the underlying lock primitive, the result is `true` when
   the primitive completed normally and `false` when a non-blocking request
   found the resource already held. A caller relying on non-blocking acquisition
   can therefore tell an already-held resource apart from a free one. -/
method acquireLock (outcome : LockOutcome) return (out : Bool)
  ensures out = acquiredOk outcome
  do
    -- impl-start
    if outcome = LockOutcome.succeeded then
      return true
    else
      return false
    -- impl-end

prove_correct acquireLock by
  loom_solve <;> cases outcome <;> simp_all [acquiredOk]

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Release a held lock and report success as a definite boolean. Releasing a
   held lock is reported as having succeeded (`true`), again a real boolean
   rather than the primitive's no-value normal-completion result. -/
method releaseLock return (out : Bool)
  ensures out = true
  do
    -- impl-start
    return true
    -- impl-end

prove_correct releaseLock by
  loom_solve
