import Mathlib
-- imports-end

/-!
Behavior of a unit-aware numeric operation's dispatch protocol when it is asked
to combine a unit-carrying value with one or more operands.

A single evaluation of the operation has one of two outcomes:

* it COMPLETES, producing some return value (a unit-carrying result, a plain
  value for comparisons, the "no value" result, or the "unhandled" sentinel);
* it FAILS to make sense of its operands (a type / value mismatch).

The protocol's contract is:

* When the evaluation completes, its return value is handed back unchanged.
* When the evaluation fails, the operation reports the "unhandled" sentinel —
  so that an operand able to handle the request itself may be tried instead —
  UNLESS every operand defers to the default handling (i.e. none of them
  supplies its own handler), in which case the original failure is surfaced.

Stated as an input→output relation on (evaluation outcome, operands) ↦ result.
The implementation and correctness proof are supplied separately.
-/

-- axioms-start
-- No unchanged dependency callee needs a contract: the evaluation outcome and
-- each operand's "defers to default handling" status are taken as the modeled
-- inputs (their production by the underlying numeric machinery is unchanged by
-- this behavior and is exercised end-to-end by the differential check), so there
-- is no `axiom <callee>_prop` for the proof to consume.

/-- One operand of the operation, abstracted to the only property this behavior
observes: whether it defers to the default handling (`true`) or supplies its own
handler (`false`). The operand list models the inputs together with any
preallocated outputs. -/
structure Operand where
  defersToDefault : Bool
deriving DecidableEq, Repr

/-- The outcome of a single evaluation of the operation:
* `completes r` — the evaluation finished and would return the value `r`;
* `fails`       — the evaluation could not make sense of its operands. -/
inductive Outcome (α : Type)
  | completes : α → Outcome α
  | fails : Outcome α
deriving Repr

/-- What the operation hands back:
* `value r`        — the completed evaluation's return value, unchanged;
* `unhandled`      — the "unhandled" sentinel (defer to another operand);
* `surfacedError`  — the original failure is surfaced. -/
inductive Result (α : Type)
  | value : α → Result α
  | unhandled : Result α
  | surfacedError : Result α
deriving Repr
-- axioms-end

-- pure-start
-- (no shared pure helpers required)
-- pure-end

-- post-conditions-start
/-- The operation's result as a function of the evaluation outcome and the
operand list:
* a completed evaluation hands back its value unchanged;
* a failed evaluation surfaces the error only when every operand defers to the
  default handling; otherwise it reports the "unhandled" sentinel. -/
def problem_spec_dispatchOp {α : Type}
    (inner : Outcome α) (operands : List Operand) (result : Result α) : Prop :=
  result = (match inner with
    | Outcome.completes r => Result.value r
    | Outcome.fails =>
        if operands.all (·.defersToDefault)
        then Result.surfacedError
        else Result.unhandled)
-- post-conditions-end

-- impl-start
-- PRE-PATCH (buggy) skeleton: a failed evaluation has no recovery path, so the
-- failure is ALWAYS surfaced regardless of whether some operand could handle
-- the request itself — the "unhandled" sentinel is never reported.
def implementation_dispatchOp {α : Type}
    (inner : Outcome α) (operands : List Operand) : Result α := Id.run do
  match inner with
  | Outcome.completes r =>
      return Result.value r
  | Outcome.fails =>
      return Result.surfacedError
-- impl-end

-- proof-start
-- Gold proof body carried over; it does NOT close against the buggy impl
-- (when the evaluation fails and some operand supplies its own handler, the
-- spec demands the "unhandled" sentinel but the buggy impl surfaces the error).
theorem correct_dispatchOp {α : Type} :
    ∀ (inner : Outcome α) (operands : List Operand),
      problem_spec_dispatchOp inner operands
        (implementation_dispatchOp inner operands) := by
  intro inner operands
  unfold problem_spec_dispatchOp implementation_dispatchOp
  cases inner with
  | completes r => rfl
  | fails => rfl
-- proof-end
