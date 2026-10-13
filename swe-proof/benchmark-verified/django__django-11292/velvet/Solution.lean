import Velvet.Std
-- imports-end

/- Total correctness: both modeled operations are straight-line option-list /
   boolean assembly in the real code and always terminate, so a diverging
   implementation must NOT satisfy this spec. Partial correctness would let a
   non-terminating body discharge every postcondition vacuously. -/
set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. Both modeled operations are pure boolean / list-frame
--  logic over FREE INPUTS: the set of command-line options a command already
--  recognises, whether the command performs project validation, and whether the
--  user asked to skip that validation. The argument registry and the validation
--  routine are stdlib / command-specific code the operations only invoke, never
--  reshape — so there is no callee contract to assume and nothing for G-AX.)
-- axioms-end

-- pure-start
/- The standard option string that lets a user opt out of the project-validation
   step from the command line. Public token (it is named in the task). -/
def skipChecksFlag : String := "--skip-checks"
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Assemble the recognised command-line options for a command, modeled as the
   list of accepted option strings (argument acceptance is membership-based;
   ordering only affects help display, not what parses). When the command
   performs project validation, the opt-out option is added to those it already
   recognises so a user can request that the validation be bypassed; when the
   command performs no validation, the opt-out option is not offered and the
   recognised options are unchanged. The options already recognised
   (`commonOptions`) are read-only and all preserved; the command's validation
   flag (`requiresSystemChecks`) is read-only. The opt-out option is assumed not
   to be among the already-recognised ones. -/
method registeredCommandOptions
    (requiresSystemChecks : Bool) (commonOptions : List String)
    return (out : List String)
  require skipChecksFlag ∉ commonOptions
  ensures requiresSystemChecks = true  → out = commonOptions ++ [skipChecksFlag]
  ensures requiresSystemChecks = false → out = commonOptions
  ensures requiresSystemChecks = true  → skipChecksFlag ∈ out
  ensures requiresSystemChecks = false → skipChecksFlag ∉ out
  ensures ∀ s, s ∈ commonOptions → s ∈ out
  do
    -- impl-start
    let out : List String :=
      if requiresSystemChecks then
        commonOptions ++ [skipChecksFlag]
      else
        commonOptions
    return out
    -- impl-end

prove_correct registeredCommandOptions by
  loom_solve

/- Decide whether to run the project-validation step before handling a command.
   Validation runs exactly when the command performs validation AND the user has
   not requested to skip it; if either the command performs no validation or the
   user asked to skip, it does not run. Both inputs are read-only. -/
method shouldRunSystemChecks
    (requiresSystemChecks : Bool) (skipRequested : Bool)
    return (result : Bool)
  ensures result = (requiresSystemChecks && (! skipRequested))
  do
    -- impl-start
    let result : Bool := requiresSystemChecks && (! skipRequested)
    return result
    -- impl-end

prove_correct shouldRunSystemChecks by
  loom_solve
