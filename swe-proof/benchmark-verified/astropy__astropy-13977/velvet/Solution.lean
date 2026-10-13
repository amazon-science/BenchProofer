import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- The two shapes a failure of the wrapped computation can take.

     * `recoverable` — a failure of the kind that arises when the operands are
       incompatible with the requested operation (an operand whose value cannot
       be brought into the form the operation expects). This is the failure the
       desired behavior is allowed to turn into a deferral.
     * `fatal` — any other failure; it is never intercepted and always
       propagates out unchanged.

   The distinction is exactly the set of failure shapes the desired behavior
   distinguishes; provenance + executable soundness check: mapping.md §3 /
   axiom_check.py (G-AX). -/
inductive UfuncErr where
  | recoverable
  | fatal
  deriving DecidableEq

/- The shape of a normal (non-failing) return of the dispatch.

     * `deferred` — the distinguished sentinel meaning "this object does not
       implement the requested operation; another participant may"; returning it
       lets the operation be retried against the other operand's handler.
     * `result v` — an ordinary returned value, carried verbatim as an opaque
       handle `v` (the dispatch never inspects it). -/
inductive Outcome where
  | deferred
  | result (v : Int)
  deriving DecidableEq

/- The wrapped computation the dispatch consults (an UNCHANGED helper invoked,
   never redefined). It does NOT always succeed: on operands incompatible with
   the requested operation it fails, and the failure may be `recoverable` or
   `fatal`; otherwise it yields a value. Declared `opaque` (computable inside the
   `do` block) and given NO `ensures` — the desired behavior assumes nothing
   about WHICH value it returns, only how a success vs a failure is handled.
   Provenance + executable soundness check (that the real computation indeed
   fails recoverably on incompatible operands and succeeds on compatible ones):
   mapping.md §3.1 / axiom_check.py (G-AX). -/
opaque coreUfunc : Int → Except UfuncErr Int

/- Whether some participant in the operation advertises its own handler for it,
   so that — should the computation fail recoverably — deferring would give that
   participant a chance to perform the operation instead. An UNCHANGED predicate
   over the operands; modeled `opaque` with no asserted `ensures`. Provenance:
   mapping.md §3.2 / axiom_check.py (G-AX). -/
opaque canDefer : Int → Bool
-- axioms-end

-- pure-start
/- The intended outcome of the whole dispatch, as `Except UfuncErr Outcome`
   (`error` = a failure propagates out, `ok` = a value is returned):

     * if the wrapped computation SUCCEEDS, its value is returned verbatim;
     * if it fails RECOVERABLY, the failure is intercepted: when some other
       participant advertises a handler (`canDefer`), the dispatch returns the
       deferral sentinel instead of failing; otherwise the very same recoverable
       failure is re-propagated unchanged;
     * if it fails in any OTHER way, that failure propagates out unchanged — it
       is never intercepted.

   Only a recoverable failure with an available alternate handler is turned into
   a deferral; every other case preserves the wrapped computation's behavior
   exactly. -/
def ufuncSpec (call : Int) : Except UfuncErr Outcome :=
  match coreUfunc call with
  | Except.ok v => Except.ok (Outcome.result v)
  | Except.error UfuncErr.recoverable =>
      if canDefer call then Except.ok Outcome.deferred
      else Except.error UfuncErr.recoverable
  | Except.error UfuncErr.fatal => Except.error UfuncErr.fatal
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Dispatch an operation over operands, taking care of the operands'
   compatibility with it.

   Desired behavior: the dispatch consults a wrapped computation over the
   operands. That computation does not always succeed — on operands incompatible
   with the requested operation it fails, and a failure is either `recoverable`
   (an incompatibility that another participant might still resolve) or `fatal`.
   When it fails recoverably AND some participant advertises its own handler for
   the operation, the dispatch must RECOVER by returning the deferral sentinel
   (`Outcome.deferred`) rather than letting the failure escape — so the operation
   can be retried against that participant (the missing behavior the public
   problem statement reports). When it fails recoverably but no alternate handler
   is available, the same recoverable failure is re-propagated unchanged. A fatal
   failure always propagates unchanged. On success the computed value is returned
   verbatim.

   `call` is the read-only operation descriptor (not `mut`): the dispatch
   computes an outcome and mutates no input (directive 5). The descriptor is
   modeled as an opaque handle (`Int`); the only observations are the wrapped
   computation's outcome (`coreUfunc`) and the alternate-handler classification
   (`canDefer`) (mapping.md §2). -/
method dispatchUfunc (call : Int)
    return (out : Except UfuncErr Outcome)
  ensures out = ufuncSpec call
  do
    -- impl-start
    -- Consult the wrapped computation and branch on its OUTCOME rather than
    -- letting every failure escape: a recoverable failure is turned into the
    -- deferral sentinel when an alternate handler is available, else the same
    -- failure is re-propagated; a fatal failure always propagates; a success is
    -- returned verbatim.
    let result : Except UfuncErr Outcome :=
      match coreUfunc call with
      | Except.ok v => Except.ok (Outcome.result v)
      | Except.error UfuncErr.recoverable =>
          if canDefer call then Except.ok Outcome.deferred
          else Except.error UfuncErr.recoverable
      | Except.error UfuncErr.fatal => Except.error UfuncErr.fatal
    return result
    -- impl-end

prove_correct dispatchUfunc by
  loom_solve
  simp_all [ufuncSpec]
