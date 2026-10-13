import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- No consumed axioms. The canonical construction a middleware is built through
-- is modeled DEEPLY in the `pure` region (`construct`); it is an A-reference —
-- validated `construct == the real construction routine` by axiom_check.py
-- (G-AX), NOT consumed as an outside contract. There is no module-level `axiom`.
-- axioms-end

-- pure-start
/- The observable face of a constructed middleware. The only property the desired
   behaviour constrains is `asyncCapable`: whether the middleware advertises that
   it operates asynchronously (so that an asynchronous caller hands it values to
   await rather than treating it as synchronous). Everything else about a
   middleware is orthogonal to this behaviour (mapping.md §2). -/
structure Middleware where
  asyncCapable : Bool
deriving DecidableEq, Inhabited

/- The canonical construction of a middleware around a response handler. A
   middleware built around an asynchronous handler must itself advertise
   asynchronous operation; one built around a synchronous handler must not. So
   the constructed middleware's async-capability is exactly the async-ness of the
   handler it wraps. `handlerIsAsync` is the only input the behaviour observes
   (mapping.md §2); it is the per-construction classification of the handler.
   Modeled deeply (no consumed axiom); validated == the real construction routine
   by G-AX (mapping.md §3). -/
def construct (handlerIsAsync : Bool) : Middleware :=
  { asyncCapable := handlerIsAsync }
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Build a middleware around its response handler. Desired behaviour: the built
   middleware advertises asynchronous operation EXACTLY when the handler it wraps
   is asynchronous. A middleware around a synchronous handler must report itself
   non-asynchronous; one around an asynchronous handler must report itself
   asynchronous — otherwise an asynchronous caller mistakes it for a synchronous
   middleware and hands it a value of the unintended kind.

   `handlerIsAsync` is the read-only classification of the response handler (not
   `mut`): the construction consumes it and never alters it (directive 5). It is
   modeled as a `Bool` — the handler is asynchronous, or it is not (mapping.md
   §2). The result is exactly `construct handlerIsAsync`, whose `asyncCapable`
   field is that same classification. -/
method initMiddleware (handlerIsAsync : Bool) return (out : Middleware)
  ensures out = construct handlerIsAsync
  ensures out.asyncCapable = handlerIsAsync
  do
    -- impl-start
    -- Build the middleware through the canonical construction routine, which
    -- records the handler's async-capability on the result.
    let out := construct handlerIsAsync
    return out
    -- impl-end

prove_correct initMiddleware by
  loom_solve
  all_goals simp [construct]
