import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The behavior under spec is a pure DATA-FLOW property:
--  a user-configured iteration budget is recorded on the estimator's
--  configuration and then handed, unchanged, to the underlying iterative solver
--  as its iteration limit. Nothing is claimed about the solver's numerical
--  output — only about WHICH budget value reaches it — so there is no callee
--  property to consume and nothing for G-AX to check. The budget is modeled as a
--  free natural number (an exact, order-faithful carrier for an iteration count);
--  the spec holds for EVERY budget the user may configure.)
-- axioms-end

-- pure-start
/- The observable configuration the desired behavior constrains: the maximum
   number of solver iterations the estimator is configured to allow. Every other
   configuration field is orthogonal to this behavior and omitted (mapping.md §2).
   `iterationBudget` is an exact `Nat`: an iteration count is a non-negative whole
   number, and the only thing pinned is the precise value carried through, an
   exact-value fact, so an exact carrier is faithful. -/
structure CodingConfig where
  iterationBudget : Nat
  deriving DecidableEq, Inhabited
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Build the estimator's coding configuration from the budget the user supplies
   at construction time. Desired behavior: the configured iteration budget must
   be the value the user actually requested — it is recorded faithfully, so a
   later encoding step can hand exactly that budget to the solver. (A budget the
   configuration silently replaced with a constant default could not control the
   solver, which is the whole point of letting the user configure it.)

   `userBudget` is the read-only requested budget (not `mut`): the routine records
   it and never alters it (directive 5). -/
method recordIterationBudget (userBudget : Nat) return (cfg : CodingConfig)
  ensures cfg.iterationBudget = userBudget
  do
    -- impl-start
    -- PRE-PATCH BUG: the construction path does not accept or store a
    -- user-configured iteration budget at all; the configuration is left to
    -- carry the solver's fixed built-in default (1000). The user's requested
    -- value is silently dropped here.
    let cfg : CodingConfig := { iterationBudget := 1000 }
    return cfg
    -- impl-end

prove_correct recordIterationBudget by
  loom_solve

/- Encode under a given configuration: determine the iteration budget that the
   underlying iterative solver is run with. Desired behavior: the solver's
   iteration limit is the budget recorded on the configuration — the configured
   value is read and forwarded to the solver as-is, rather than the solver being
   left to fall back on a constant built-in default. The returned value is precisely
   the iteration limit handed to the solver.

   `cfg` is the read-only configuration (not `mut`): encoding consults it and
   never mutates it (directive 5). -/
method encodeWithConfig (cfg : CodingConfig) return (solverBudget : Nat)
  ensures solverBudget = cfg.iterationBudget
  do
    -- impl-start
    let solverBudget := cfg.iterationBudget
    return solverBudget
    -- impl-end

prove_correct encodeWithConfig by
  loom_solve

/- End-to-end: the budget the user configures at construction reaches the solver.
   Desired behavior: the iteration limit the solver is ultimately run with equals
   the budget the user requested — configuring the budget actually governs the
   solver. This is the composition of recording the budget on the configuration
   and then encoding under that configuration.

   `userBudget` is the read-only requested budget (not `mut`, directive 5). -/
method configuredBudgetReachesSolver (userBudget : Nat) return (solverBudget : Nat)
  ensures solverBudget = userBudget
  do
    -- impl-start
    let cfg ← recordIterationBudget userBudget
    let solverBudget ← encodeWithConfig cfg
    return solverBudget
    -- impl-end

prove_correct configuredBudgetReachesSolver by
  loom_solve
