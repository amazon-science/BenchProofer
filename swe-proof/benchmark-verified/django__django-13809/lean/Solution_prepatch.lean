import Mathlib
-- imports-end

/-!
Optionally skipping system checks when starting the development server.

The development server's startup routine performs a set sequence of steps
before it begins serving requests. One of those steps runs the project's system
checks, which can be slow during iterative development. A boolean control
(`skipChecks`) selects whether that step is performed.

We model the startup routine as the ordered list of observable actions it emits.
The system-check step consists of two observable actions: announcing that checks
are about to be performed, and running the checks themselves. When `skipChecks`
holds, both actions are omitted and the routine proceeds directly to the
remaining steps. When it does not hold, the system-check step is emitted first,
in order, ahead of the remaining steps. The remaining steps — verifying pending
migrations, writing the startup banner, and beginning to serve requests — are
always emitted, in the same order, regardless of the control.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification: the startup
-- routine's observable behavior is modeled structurally as the ordered list of
-- actions it emits, gated on a boolean control, so no `opaque`/`axiom` callee
-- contract is needed.
-- axioms-end

-- pure-start
/-- An observable action emitted by the development server's startup routine.
* `announceChecks` — announce that the system-check step is about to run;
* `runChecks` — run the project's system checks;
* `checkMigrations` — verify that there are no unapplied migrations;
* `writeBanner` — write the startup banner (version, address, port);
* `serve` — begin serving requests. -/
inductive StartupAction
  | announceChecks
  | runChecks
  | checkMigrations
  | writeBanner
  | serve
deriving DecidableEq, Repr, Inhabited

/-- The steps that are always emitted, in order, after the (optional)
system-check step. -/
def tailSteps : List StartupAction :=
  [StartupAction.checkMigrations, StartupAction.writeBanner, StartupAction.serve]
-- pure-end

-- post-conditions-start
/-- The startup routine emits the system-check step (announcement then the
checks themselves) iff checks are not skipped, followed always by the remaining
steps in their set order. The result is fully determined by `skipChecks`:
the unchanged tail is pinned to its constant value in both cases, and the gated
prefix is present exactly when `skipChecks` is false. -/
def problem_spec_serverStartup (skipChecks : Bool) (result : List StartupAction) : Prop :=
  result =
    (if skipChecks then [] else [StartupAction.announceChecks, StartupAction.runChecks]) ++ tailSteps
-- post-conditions-end

-- impl-start
def implementation_serverStartup (skipChecks : Bool) : List StartupAction := Id.run do
  let mut log : List StartupAction := []
  -- The system-check step is always emitted, ignoring the control.
  log := log ++ [StartupAction.announceChecks]
  log := log ++ [StartupAction.runChecks]
  log := log ++ [StartupAction.checkMigrations]
  log := log ++ [StartupAction.writeBanner]
  log := log ++ [StartupAction.serve]
  return log
-- impl-end

-- proof-start
-- Gold proof body carried over from Solution.lean (SPEC_GUIDE §1.1). Against this
-- impl it cannot close: when `skipChecks = true` the spec requires the
-- system-check step to be absent, but this impl always emits it, so the
-- `skipChecks = true` branch of `cases skipChecks <;> rfl` fails to reduce.
theorem correct_serverStartup :
    ∀ (skipChecks : Bool),
      problem_spec_serverStartup skipChecks
        (implementation_serverStartup skipChecks) := by
  intro skipChecks
  unfold problem_spec_serverStartup implementation_serverStartup tailSteps
  cases skipChecks <;> rfl
-- proof-end
