import Mathlib
-- imports-end

/-!
Constructing a request-processing component from its optional request handler.

A component is built from an optional handler. The component advertises that it
is capable of operating in an asynchronous fashion, but whether a *particular*
instance actually operates asynchronously must follow the handler it was built
from: an instance built from an asynchronous handler must itself report as
asynchronous, and an instance built from an ordinary (non-asynchronous) handler
must report as ordinary.

Construction is fully determined by the handler:

  * the constructed instance keeps exactly the handler it was given;
  * when no handler is supplied, construction raises a "missing handler"
    notice (and none otherwise);
  * the instance reports itself as asynchronous exactly when the handler it was
    built from is asynchronous.

The third component is the behavior at issue: an instance must not silently
default to "ordinary" regardless of its handler; it must reflect the handler's
asynchronous nature.
-/

-- axioms-start
-- No UNCHANGED callee needs an opaque signature here. The two effects the
-- constructor performs — emitting a notice when no handler is supplied, and
-- determining whether the handler is asynchronous — are modeled DEEPLY as
-- properties of the input handler (`Option.isNone` and `Handler.isAsync`),
-- not axiomatized. Their reference behavior is validated by G-CONF as
-- A-references. The proof agent may add `_prop` axioms only if genuinely stuck.
-- axioms-end

-- pure-start
/-- A request handler, observed through the only property the constructor's
behavior depends on: whether it operates asynchronously. -/
structure Handler where
  /-- whether this handler operates asynchronously -/
  isAsync : Bool
deriving Repr, DecidableEq

/-- The constructed component. Its observable, construction-determined state:
the handler it was built from, whether a "missing handler" notice was raised,
and whether the instance reports itself as asynchronous. -/
structure Component where
  /-- the handler the component was built from -/
  handler : Option Handler
  /-- whether construction raised the "missing handler" notice -/
  missingHandlerFlagged : Bool
  /-- whether the instance reports itself as operating asynchronously -/
  reportsAsync : Bool
deriving Repr, DecidableEq

/-- Whether the (optional) handler operates asynchronously. A supplied handler
is asynchronous iff its own `isAsync` flag is set; the absence of a handler is
never asynchronous. -/
def handlerIsAsync : Option Handler → Bool
  | some h => h.isAsync
  | none => false
-- pure-end

-- post-conditions-start
/-- A constructed component is fully pinned to its input handler:
  * it keeps exactly the handler given (`result.handler = handler`);
  * the "missing handler" notice is raised exactly when no handler was supplied;
  * it reports as asynchronous exactly when its handler is asynchronous.
Directive 5 (frame): every output component is tied to the input — no field is
left free. Directive 8: each field is grounded in the actual input `handler`,
so the asynchronous report must be *produced by* inspecting the handler, not
defaulted. -/
def problem_spec_initComponent (handler : Option Handler) (result : Component) : Prop :=
  result.handler = handler ∧
  result.missingHandlerFlagged = handler.isNone ∧
  result.reportsAsync = handlerIsAsync handler
-- post-conditions-end

-- impl-start
def implementation_initComponent (handler : Option Handler) : Component := Id.run do
  -- raise the "missing handler" notice when no handler is supplied
  let mut missingFlag := false
  if handler.isNone then
    missingFlag := true
  -- keep the handler the component was built from
  let stored := handler
  -- PRE-PATCH BUG: the asynchronous-capability check is omitted, so the
  -- instance always reports as ordinary regardless of its handler.
  let async := false
  return { handler := stored, missingHandlerFlagged := missingFlag, reportsAsync := async }
-- impl-end

-- proof-start
theorem correct_initComponent : ∀ handler : Option Handler,
    problem_spec_initComponent handler (implementation_initComponent handler) := by
  sorry   -- carries the gold proof body; UNCLOSABLE against the buggy impl (G-DIFF)
-- proof-end
