import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No consumed axioms. The branch that responds to a detected set of pending
--  changes is modeled DEEPLY in the `pure` region (`stepOutcome`): whether the
--  process aborts with a non-zero status and whether any migration artifacts are
--  emitted are spelled out directly from the two mode flags. The one callee
--  whose runtime behaviour the deep model relies on — the non-zero abort
--  primitive, which raises and unwinds so that statements sequenced after it do
--  not run — is an A-reference (validated against the real standard-library
--  primitive by axiom_check.py / G-AX), NOT a consumed contract.)
-- axioms-end

-- pure-start
/- What a migration-emitting step can produce, observably, when a non-empty set
   of pending changes has been detected. `noWrite` means no migration artifact
   was emitted at all; `latest` means the changes were folded into the most
   recent existing migration; `standard` means a fresh migration was emitted.
   These are the only emission outcomes the desired behaviour distinguishes. -/
inductive WriteKind where
  | noWrite
  | latest
  | standard
  deriving DecidableEq

/- The two observable effects of the step on a detected change set: which
   migration artifact (if any) was emitted, and whether the process terminated
   with a non-zero status. The downstream scripting use depends on BOTH being
   pinned together (an exit with a non-zero status is meaningless to a caller if
   artifacts were silently emitted as a side effect anyway). -/
structure StepOutcome where
  written : WriteKind
  exited  : Bool
  deriving DecidableEq

/- The desired step behaviour, modeled deeply. In a check-only mode the step
   must terminate with a non-zero status and emit NO migration artifact — the
   check is a pure query about whether the model layer is in sync, consistent
   with the other check-only entry points that merely report and exit. Outside
   check-only mode the step emits an artifact: folded into the most recent
   migration when an update is requested, otherwise a fresh migration; and the
   process does not abort. Pinned by the method's `ensures`. -/
def stepOutcome (checkOnly update : Bool) : StepOutcome :=
  if checkOnly then
    { written := WriteKind.noWrite, exited := true }
  else
    { written := (if update then WriteKind.latest else WriteKind.standard),
      exited := false }
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- A migration-management step that has already detected a non-empty set of
   pending model changes decides what to do with them. The step runs in one of
   two independent modes: a check-only mode (a query: "are migrations missing?")
   and an emit mode. In check-only mode the step must terminate with a non-zero
   status and emit NO migration artifact, so that scripting a missing-migration
   check never has the side effect of creating migrations — matching the other
   check-only entry points, which just report and exit. Outside check-only mode
   the step emits an artifact (folded into the most recent migration when an
   update is requested, otherwise a fresh migration) and does not abort.

   `checkOnly` and `update` are read-only mode flags (neither is `mut`; the step
   mutates none of its inputs — directive 5). The result records both observable
   effects: the emitted-artifact kind and whether the process aborted. -/
method runCheckedWrite (checkOnly : Bool) (update : Bool) return (out : StepOutcome)
  ensures out = stepOutcome checkOnly update
  -- The discriminating guarantee: a check-only run emits NO artifact (it must
  -- not write migrations as a side effect of querying).
  ensures checkOnly = true → out.written = WriteKind.noWrite
  ensures out.exited = checkOnly
  do
    -- impl-start
    if checkOnly then
      -- Query mode: abort with a non-zero status before any artifact is emitted.
      return { written := WriteKind.noWrite, exited := true }
    else
      -- Emit mode: fold into the most recent migration on update, else emit a
      -- fresh migration; do not abort.
      let wk := if update then WriteKind.latest else WriteKind.standard
      return { written := wk, exited := false }
    -- impl-end

prove_correct runCheckedWrite by
  loom_solve <;> simp_all [stepOutcome]
