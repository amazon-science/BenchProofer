import Mathlib
-- imports-end

/-!
Letting a command-line invocation skip a command's pre-run checks.

A management command, before it does its work, may run a battery of project
"system checks". Whether a command runs those checks at all is an inherent
property of that command (`commandPerformsChecks`): some commands always check first,
others never check.

This bundle models the decision the command makes when it is launched from the
command line, given whether the launch *asked* to skip the checks
(`skipRequested`). There are three possible outcomes:

  * `unrecognizedOption` — the launch asked to skip checks but this command does
    not offer a skip option, so the request is not a recognised command-line
    option and the launch is rejected;
  * `ranChecks`          — the command ran its system checks before proceeding;
  * `skippedChecks`      — the command proceeded without running system checks.

The desired behavior: a command exposes a "skip" option exactly when it performs
checks. When a skip is asked of such a command, the checks are skipped; when no
skip is asked, such a command runs its checks. A command that performs no checks
proceeds without checking and offers no skip option, so a skip request aimed at
it is an unrecognised option.

Inputs:
  * `commandPerformsChecks` — whether this command runs system checks by default;
  * `skipRequested`         — whether the launch asked to skip the checks.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. Whether a
-- command runs its checks by default enters as the plain `commandPerformsChecks`
-- datum; whether the launch asked to skip enters as the plain `skipRequested`
-- datum. The act of running the checks is observed only as WHETHER it happens
-- (`ranChecks` vs `skippedChecks`), never by its internals, so no `opaque`/`axiom`
-- callee contract is required.
-- axioms-end

-- pure-start
/-- The outcome of launching a command from the command line, restricted to the
touched behavior: whether the skip request was a recognised option, and whether
the system checks ran. -/
inductive RunResult
  | unrecognizedOption
  | ranChecks
  | skippedChecks
deriving DecidableEq, Repr
-- pure-end

-- post-conditions-start
/-- The launch outcome is fully pinned to the two inputs (the Boolean × Boolean
domain is covered exhaustively, so no component of the result is left free):

  * a command that performs no checks and is not asked to skip simply proceeds
    without checking (`skippedChecks`);
  * a command that performs no checks but IS asked to skip rejects the request as
    an unrecognised option (it offers no skip option) (`unrecognizedOption`);
  * a command that performs checks and is asked to skip them skips them
    (`skippedChecks`);
  * a command that performs checks and is not asked to skip runs them
    (`ranChecks`). -/
def problem_spec_runCommand
    (commandPerformsChecks skipRequested : Bool) (result : RunResult) : Prop :=
  (commandPerformsChecks = false → skipRequested = false →
      result = RunResult.skippedChecks) ∧
  (commandPerformsChecks = false → skipRequested = true →
      result = RunResult.unrecognizedOption) ∧
  (commandPerformsChecks = true → skipRequested = true →
      result = RunResult.skippedChecks) ∧
  (commandPerformsChecks = true → skipRequested = false →
      result = RunResult.ranChecks)
-- post-conditions-end

-- impl-start
def implementation_runCommand
    (commandPerformsChecks skipRequested : Bool) : RunResult := Id.run do
  -- A skip option is registered for this command exactly when it performs checks.
  let skipOptionAvailable := commandPerformsChecks
  -- A skip request for a command with no such option is not recognised.
  if skipRequested && !skipOptionAvailable then
    return RunResult.unrecognizedOption
  -- When the option is available, an absent request reads as "do not skip".
  let skip := skipRequested
  if commandPerformsChecks && !skip then
    return RunResult.ranChecks
  return RunResult.skippedChecks
-- impl-end

-- proof-start
theorem correct_runCommand :
    ∀ (commandPerformsChecks skipRequested : Bool),
      problem_spec_runCommand commandPerformsChecks skipRequested
        (implementation_runCommand commandPerformsChecks skipRequested) := by
  intro commandPerformsChecks skipRequested
  refine ⟨?_, ?_, ?_, ?_⟩ <;>
    intro h1 h2 <;>
    subst h1 <;> subst h2 <;> rfl
-- proof-end
