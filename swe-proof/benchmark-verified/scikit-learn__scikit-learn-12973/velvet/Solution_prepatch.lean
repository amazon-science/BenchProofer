import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- The caller's data buffer is handed to TWO numeric routines in sequence, and
   each of them may work IN PLACE on the buffer it receives. Both are OPAQUE:
   neither routine is under specification here and neither is altered, so their
   numeric results are not modeled. What is modeled about each is (a) its FRAME
   effect — whether the buffer it was handed is left intact or is left holding
   what the routine produced — and (b) that this effect is a FUNCTION of data
   this model carries, so every buffer named below is determined by the inputs in
   the signature and by nothing else.

   Both routines take further settings besides the buffers named here, and each
   such setting is PINNED to one value throughout: the arities below are claims
   about the modeled configuration, not about the routines in general. The
   configuration is listed, justified setting by setting, and shown to be
   complete in mapping.md §3.3, and every claim in this paragraph and the next
   two is measured AT it. Two properties of the buffer ITSELF — the format of
   its entries, and the order they are laid out in — are likewise inputs of both
   routines that no argument below carries, because each routine reduces ALONG
   the buffer; they are PINNED structurally by that same section, so a buffer
   holding the same entries in another format or another order is a DIFFERENT
   input and nothing is claimed of it.

   `prepareInPlace` is the FIRST routine's transform. Within that configuration
   its result is a function of the entry contents TOGETHER WITH the companion
   target vector, and of nothing else. The target is carried for a STRUCTURAL
   reason rather than a numeric one: the first routine reduces over the buffer in
   GROUPS, and how the buffer's entries fall into groups is settled by how many
   entries the target has. Two runs whose buffers hold the same entries under
   targets of DIFFERENT lengths group them differently, and the routine's output
   differs, so a symbol of the buffer alone could not equal both. Once that
   count is held, the target's own entries are NOT read for it — measured, and
   that is what makes this argument a grouping witness rather than a licence to
   vary with the target — and its result does not depend on whether that routine
   worked on the caller's buffer or on a buffer of its own (both measured —
   mapping.md §3.1). Off that pinned configuration this would be false, which is
   why the settings it reads are held constant rather than passed.

   `searchInPlace` is the SECOND routine's transform. It works on whatever the
   first routine produced, and it DOES read the target vector's ENTRIES, so
   within the configuration its result is a function of BOTH. Its second argument is what
   makes the modeled buffers determinate: with the target dropped, one entry
   buffer would have to equal several distinct exit buffers, and no instantiation
   of an opaque unary symbol can do that. The settings this routine reads beyond
   the buffer and the target are likewise pinned, for the same reason.

   Two buffers are therefore observable per run, and they are NOT the same
   buffer: the caller's, and the one the second routine is handed. When the first
   routine works on a buffer of its own, the caller's buffer no longer reflects
   what the second routine does — but the second buffer does, and the run's
   consumer reads it after both routines have returned (mapping.md §1, §3.4).

   Provenance + executable soundness check (each routine's frame effect, its
   determinacy, which arguments it genuinely reads, and the settings the modeled
   region pins): mapping.md §3 / axiom_check.py (G-AX). Both are deep-model
   references, NOT consumed equational axioms: the proof discharges the
   postconditions purely by the impl's assignments, never by an equation about
   either symbol. -/
axiom prepareInPlace : Array Int → Array Int → Array Int
axiom searchInPlace : Array Int → Array Int → Array Int

/- Both routines DELIVER a buffer on this pair — the domain of the two-routine
   sequence, as a fact about the buffer and the target TOGETHER.

   Neither routine is total. Each one reduces ALONG the buffer, and each checks
   the entries it computes before handing them on; on some pairs a reduction
   leaves an entry the next check refuses, and the routine then SIGNALS rather
   than returning a buffer. This is not a property of any single entry — a pair
   every one of whose entries is individually acceptable can still have a
   reduction that is not, because the reduction combines them — so no condition
   on the entries one at a time expresses it, and it is stated of the pair.

   It is a PRECONDITION and not an assumption about either routine's result: off
   it the real sequence has no answer to be equal to. On such a pair the run
   signals, the two symbols above name nothing, and the buffer the consumer would
   read is never formed — so the postconditions below assert nothing there rather
   than asserting something false.

   Opaque, and nothing about a buffer is derivable from it: it records only that
   the sequence delivers here. It is a function of `(buffer, target)` and of the
   pinned configuration, and of NOTHING ELSE — in particular it does NOT depend
   on the copy choice, so ONE predicate covers every leg. That independence is
   what licenses stating it once, ahead of the choice: measured, over the modeled
   region, on every copy-choice combination (mapping.md §3.5 / axiom_check.py). -/
axiom bothRoutinesDeliver : Array Int → Array Int → Prop
-- axioms-end

-- pure-start
/- The effective copy decision. An explicitly supplied choice takes precedence;
   when no choice is supplied (`none`), the configured default is used. This is
   exactly `Option.getD`: `requested.getD configured`. -/
def effectiveCopy (configured : Bool) (requested : Option Bool) : Bool :=
  requested.getD configured

@[grind] lemma effectiveCopy_none (configured : Bool) :
    effectiveCopy configured none = configured := rfl
@[grind] lemma effectiveCopy_some (configured : Bool) (b : Bool) :
    effectiveCopy configured (some b) = b := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Run the caller's data buffer through both numeric routines under a copy
   choice, and report the buffer the second routine was handed as it stands after
   that routine returned.

   `configuredCopy` is the choice set when the consumer was configured;
   `requestedCopy` is the optional per-call choice. The effective choice is the
   per-call one when supplied, otherwise the configured one. `target` is the
   companion target vector the run is given alongside the buffer.

   The guarantee tied down here is that ONE effective choice governs EVERY
   routine the data reaches, and it is stated of BOTH observable buffers, because
   either routine alone can hide the other:

   * effective copy = `true`  ⇒ the caller's buffer is preserved verbatim, AND
     the buffer handed on to the second routine still holds exactly what the
     first routine produced — the second routine worked on a buffer of its own
     and left the one it was handed alone;
   * effective copy = `false` ⇒ both buffers end holding what the two routines
     produce in sequence: the first routine's transform of the entry contents
     under `target`, then the second routine's transform of that under `target`.

   The three clauses that name a routine's OUTPUT are stated where the sequence
   delivers one (`bothRoutinesDeliver dataOld target`), because off that pair the
   routines produce no buffer for a clause to be equal to. The hypothesis is on
   the CLAUSES rather than on the method because it is not needed by all of them:
   the caller's buffer is preserved on the `true` leg whether the sequence
   delivers or signals — the first routine copies BEFORE it reduces, so a signal
   mid-reduction cannot reach the caller's buffer on that leg — so the frame
   clause is stated with NO hypothesis and holds over the whole domain (measured
   on the signalling class, mapping.md §3.5). Weakening it to the delivering pairs
   would drop a guarantee the routines genuinely make.

   The second clause of the `true` leg is the one a caller's buffer cannot
   express: on that leg the first routine works on a buffer of its own, so the
   caller's buffer is preserved no matter what the second routine is told to do,
   and only `work` records whether the second routine was told the same thing.
   The run's consumer reads `work` after both routines return, so a run that
   lets the second routine rework it reports different results.

   Every clause pins its buffer to a FUNCTION of `(dataOld, target)` and the
   choice, so a run may not leave either buffer holding a value the model's own
   inputs fail to determine. The delivery hypothesis does not loosen that: it
   ranges over `(dataOld, target)` only, so it cannot be read as licence to vary
   a delivered buffer with the choice, and on every pair where it holds all four
   clauses are in force exactly as before.

   `data` is `mut` solely so the `false` case can overwrite it; the `true` case
   pins it equal to its entry value (`dataOld`) — the read-only frame is stated
   explicitly, and it is stated of the run as a whole. -/
noncomputable section
method applyWithCopyChoice (mut data : Array Int) (target : Array Int)
    (configuredCopy : Bool) (requestedCopy : Option Bool)
    return (work : Array Int)
  ensures effectiveCopy configuredCopy requestedCopy = true  → data = dataOld
  ensures bothRoutinesDeliver dataOld target →
            effectiveCopy configuredCopy requestedCopy = true  →
            work = prepareInPlace dataOld target
  ensures bothRoutinesDeliver dataOld target →
            effectiveCopy configuredCopy requestedCopy = false →
            data = searchInPlace (prepareInPlace dataOld target) target
  ensures bothRoutinesDeliver dataOld target →
            effectiveCopy configuredCopy requestedCopy = false →
            work = searchInPlace (prepareInPlace dataOld target) target
  do
    -- impl-start
    -- BASELINE SKELETON: the two routines are gated INDEPENDENTLY, and neither
    -- gate is the effective choice: the first goes by the configured choice, the
    -- second by the per-call one read raw (absent reads as "leave it alone").
    let stageOne := configuredCopy
    let stageTwo := requestedCopy.getD true
    if stageOne then
      let w := prepareInPlace data target
      if stageTwo then
        return w
      else
        return searchInPlace w target
    else
      data := prepareInPlace data target
      if stageTwo then
        return data
      else
        data := searchInPlace data target
        return data
    -- impl-end
end

prove_correct applyWithCopyChoice by
  loom_solve
