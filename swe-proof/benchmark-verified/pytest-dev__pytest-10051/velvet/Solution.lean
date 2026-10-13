import Velvet.Std
-- imports-end

-- Total-correctness semantics: the operation under spec is straight-line
-- (no loops or recursion; it always returns), so the contract also demands
-- termination — under partial semantics a diverging body would vacuously
-- satisfy every postcondition.
set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- No axiomatized callees. The operation under spec is spelled out directly over
-- the observable capture state (see the `pure` region): it allocates no value
-- from, and assumes no contract of, any unchanged callee. There is therefore
-- nothing for G-AX to validate against a real callee (mapping.md §3).
-- axioms-end

-- pure-start
/- A captured log record, abstracted to an opaque token: the behavior under
   spec only ever observes the *sequence* of captured records (which records are
   present, and in particular whether the sequence is empty), never the contents
   of an individual record. -/
abbrev Rec := Nat

/- A record buffer, modeled as a heap object: an identity token (`ident`) plus
   the sequence of records it currently holds (`contents`). Two references
   denote the SAME buffer object exactly when their identity tokens are equal;
   emptying a buffer in place changes its `contents` but preserves its `ident`,
   so every reference that aliases it keeps observing the (now empty) buffer. -/
structure Buffer where
  ident : Nat
  contents : List Rec
  deriving Inhabited, DecidableEq

/- The capture state, restricted to the two aspects the operation under spec can
   touch:

   * `live`     — the buffer the capturing machinery actively appends to and
                  exposes as its current record sequence.
   * `callId`   — the identity token that the per-phase "call" reference was
                  bound to when the phase was prepared. In a well-formed phase
                  this is the identity of the `live` buffer (the precondition
                  below), i.e. the per-phase reference and the live reference
                  denote the same buffer object.
   * `callSnap` — the record sequence the per-phase "call" reference would expose
                  were it to denote a DIFFERENT buffer than the live one; it is
                  consulted only when the per-phase reference and the live
                  reference have diverged (different identity tokens). -/
structure Capture where
  live : Buffer
  callId : Nat
  callSnap : List Rec
  deriving Inhabited

/- The record sequence exposed by the live reference. -/
@[grind] def liveRecords (c : Capture) : List Rec := c.live.contents

/- The record sequence exposed by the per-phase "call" reference. When that
   reference still denotes the live buffer (its bound identity matches the live
   buffer's identity) it observes the live contents; once the two have diverged
   it observes its own detached snapshot instead. -/
@[grind] def callRecords (c : Capture) : List Rec :=
  if c.callId = c.live.ident then c.live.contents else c.callSnap
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Empty the captured record sequence for the current phase.

   The required behavior: the live buffer must be emptied IN PLACE, so that every
   reference that aliases it — in particular the per-phase "call" reference bound
   to it when the phase was prepared — observes the now-empty sequence and stays
   bound to the same buffer object. Concretely:

   * the identity of the live buffer is PRESERVED (`c.live.ident` is the
     directive-5 frame: the operation must NOT replace the buffer with a fresh
     object — `ensures c.live.ident = cOld.live.ident`);
   * the live buffer's contents become empty;
   * therefore the "call" reference, which the precondition pins to the live
     buffer's identity, also observes the empty sequence.

   `callId`/`callSnap` are read-only here and are returned unchanged. -/
method clearCapture (mut c : Capture) return (u : Unit)
  require c.callId = c.live.ident
  ensures c.live.ident = cOld.live.ident
  ensures c.callId = cOld.callId
  ensures c.callSnap = cOld.callSnap
  ensures liveRecords c = []
  ensures callRecords c = []
  do
    -- impl-start
    -- Empty the live buffer in place: keep the same buffer object (its identity
    -- token is left untouched) and set its contents to the empty sequence. Any
    -- reference aliasing this buffer therefore observes the empty sequence.
    c := { c with live := { c.live with contents := [] } }
    return
    -- impl-end

prove_correct clearCapture by
  loom_solve
