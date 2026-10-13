import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The set of HTTP methods the resource permits is
--  produced by an UNCHANGED helper; this routine merely consumes that set, so it
--  is taken as the read-only free input `allowed` and owed no contract. There is
--  no `axiom` declaration and no A-reference deep model of an outside callee:
--  the only behaviour under spec — how the 405 response is HANDED BACK — is
--  modeled deeply in the `pure`/`impl` regions. See mapping.md §3.)
-- axioms-end

-- pure-start
/- The "405 — method not allowed" response: it reports the set of HTTP methods
   the resource does permit. Its content does not depend on how it is delivered. -/
structure NotAllowed where
  allowed : List String
  deriving DecidableEq, Inhabited

/- How a produced response is handed back to the caller:
     * `immediate r` — the response object `r` itself, returned directly;
     * `awaitable r` — an awaitable object that yields the response `r` when it
                       is awaited.
   Only the outer delivery wrapper differs between the two; the underlying
   response `r` is the same. -/
inductive Delivery where
  | immediate (resp : NotAllowed)
  | awaitable (resp : NotAllowed)
  deriving DecidableEq, Inhabited

/- Whether the handed-back object is an awaitable (must be awaited to obtain the
   response) rather than the response object itself. -/
def Delivery.isAwaitable : Delivery → Bool
  | .immediate _ => false
  | .awaitable _ => true

/- The response ultimately obtained — directly, or after awaiting. -/
def Delivery.response : Delivery → NotAllowed
  | .immediate r => r
  | .awaitable r => r

/- The desired delivery of a "method not allowed" outcome: build the 405 response
   listing the permitted methods `allowed`, then hand it back as an awaitable
   exactly when the view runs asynchronously (so a caller may await it), and as
   the plain response object otherwise. The response content is identical in
   both cases — only the wrapper differs. -/
def deliverNotAllowed (asynchronous : Bool) (allowed : List String) : Delivery :=
  let resp : NotAllowed := { allowed := allowed }
  if asynchronous then Delivery.awaitable resp else Delivery.immediate resp
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Produce the response handed back when a request uses an HTTP method the view
   does not permit.

   `asynchronous` records whether the view runs asynchronously; `allowed` is the
   set of methods the resource permits (read-only — the value an unchanged helper
   reports). Both are read-only (neither `mut`): the routine reads them and
   returns a delivery, mutating nothing it is handed (directive 5).

   The 405 response listing `allowed` is delivered as an awaitable precisely when
   the view is asynchronous, and as the plain response object otherwise; either
   way the underlying response is the same 405 response listing `allowed`. -/
method notAllowedResponse (asynchronous : Bool) (allowed : List String) return (out : Delivery)
  ensures out = deliverNotAllowed asynchronous allowed
  ensures out.isAwaitable = asynchronous
  ensures out.response = { allowed := allowed }
  ensures asynchronous = true  → out = Delivery.awaitable { allowed := allowed }
  ensures asynchronous = false → out = Delivery.immediate { allowed := allowed }
  do
    -- impl-start
    -- Build the 405 response listing the permitted methods, then choose the
    -- delivery wrapper by whether the view runs asynchronously: an awaitable in
    -- the asynchronous case (so the caller may await it), the response object
    -- itself otherwise.
    let resp : NotAllowed := { allowed := allowed }
    let out := if asynchronous then Delivery.awaitable resp else Delivery.immediate resp
    return out
    -- impl-end

prove_correct notAllowedResponse by
  loom_solve <;>
    cases asynchronous <;>
    simp_all [deliverNotAllowed, Delivery.isAwaitable, Delivery.response]
