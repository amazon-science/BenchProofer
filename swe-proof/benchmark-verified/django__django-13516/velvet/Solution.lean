import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- No axiomatized callees: the modeled operation is spelled out directly over
-- the observable state (see `pure` region). There is no unchanged callee whose
-- internal behavior the proof must assume.
-- axioms-end

-- pure-start
/- The observable state of a thin output stream wrapper, restricted to the two
   aspects a flush request can touch:

   * `flushable` — whether the underlying stream the wrapper forwards to is one
     that supports flushing (it exposes a flush operation of its own);
   * `flushes`   — how many times a flush has actually been driven through to
     that underlying stream (the outward observable effect of forwarding).

   Other wrapper state (text content already written, the line ending, styling)
   is untouched by a flush request and is therefore not part of this carrier
   (mapping.md §2). -/
structure OutputSink where
  flushable : Bool
  flushes : Nat
  deriving Inhabited
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- A flush request on the wrapper. The required behavior: when the underlying
   stream supports flushing, the request must be carried through to it exactly
   once; when it does not, the request is a no-op. The `flushable` aspect is a
   read-only property of the wrapper and is never altered by a flush. -/
method propagateFlush (mut sink : OutputSink) return (u : Unit)
  ensures sink.flushable = sinkOld.flushable
  ensures sinkOld.flushable = true  → sink.flushes = sinkOld.flushes + 1
  ensures sinkOld.flushable = false → sink.flushes = sinkOld.flushes
  do
    -- impl-start
    if sink.flushable then
      sink := { sink with flushes := sink.flushes + 1 }
    else
      return
    return
    -- impl-end

prove_correct propagateFlush by
  loom_solve
