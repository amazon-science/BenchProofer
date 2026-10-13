import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee needs an opaque signature here. The two values the handler
-- consults — whether the view operates in asynchronous mode, and the list of
-- permitted request methods carried by the response — are unchanged inputs and
-- are modeled as plain parameters, so nothing is abstracted behind a callee.
-- The proof agent may add `_prop` axioms only if it gets stuck.
-- axioms-end

-- pure-start
/-- The object produced when a request uses a method the view does not permit.
It always denotes the standard "method not allowed" (HTTP 405) response and
carries the list of permitted method names. `awaitable` records whether the
returned object is an awaitable wrapper (to be resolved by the caller) rather
than the bare response value. -/
structure DisallowedResponse where
  /-- Whether the returned object must be awaited before the response is obtained. -/
  awaitable : Bool
  /-- The permitted request-method names carried by the response. -/
  allowed : List String
deriving DecidableEq, Repr
-- pure-end

-- post-conditions-start
/-- The handler must yield the "method not allowed" response carrying exactly the
permitted methods it was given, and that object must be an awaitable wrapper
precisely when the view operates in asynchronous mode (so the caller can resolve
it uniformly); in synchronous mode the bare response is returned directly. The
permitted-method payload is identical in both modes. -/
def problem_spec_disallowedResponse
    (isAsync : Bool) (allowed : List String) (result : DisallowedResponse) : Prop :=
  result.awaitable = isAsync ∧ result.allowed = allowed
-- post-conditions-end

-- impl-start
/-- Pre-patch behavior: the "method not allowed" response carrying the permitted
methods is always handed back directly as the bare response value, with no
asynchronous-mode wrapper. In asynchronous mode the caller therefore receives a
non-awaitable object where an awaitable one is required. -/
def implementation_disallowedResponse
    (isAsync : Bool) (allowed : List String) : DisallowedResponse := Id.run do
  let response : DisallowedResponse := { awaitable := false, allowed := allowed }
  return response
-- impl-end

-- proof-start
theorem correct_disallowedResponse :
    ∀ (isAsync : Bool) (allowed : List String),
    problem_spec_disallowedResponse isAsync allowed
      (implementation_disallowedResponse isAsync allowed) := by
  sorry   -- carries the gold proof body; UNCLOSABLE against the buggy impl (G-DIFF)
-- proof-end
