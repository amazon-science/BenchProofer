import Velvet.Std
-- imports-end

/- Total correctness: the real preparation step is a straight-line branch (wrap
   the fallback form or return the bare aggregation) that always terminates, so
   a diverging implementation must NOT satisfy this spec. Partial correctness
   would let a non-terminating body discharge the postconditions vacuously. -/
set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- No axiomatized callees: the modeled operation is spelled out directly over the
-- observable shape of the prepared clause (see `pure` region). The unchanged
-- callees the model relies on (how base resolution sets the terminal marker, and
-- what marker a freshly built fallback wrapper carries) are facts about real
-- objects, audited executably by axiom_check.py (G-AX) — not assumed here.
-- axioms-end

-- pure-start
/- The observable shape of a prepared aggregation clause, restricted to the two
   aspects that decide how the query builder later places it:

   * `isTerminal` — whether the clause is marked as a terminal (top-level)
     aggregation. The query builder consults exactly this marker to decide
     whether the clause is computed at the outer level; a clause that is
     terminal-in-fact but unmarked is mis-placed and yields malformed output.
   * `hasFallback` — whether the clause is the fallback form that substitutes a
     supplied value when the aggregation has no rows, rather than the bare
     aggregation.

   Other attributes of the clause (the column, the function name, output type)
   are untouched by this preparation step and are not part of this carrier
   (mapping.md §2). -/
structure Resolved where
  isTerminal : Bool
  hasFallback : Bool
  deriving DecidableEq, Inhabited, Repr

/- Preparing an aggregation clause to be added to a query, given whether it is
   requested as a terminal (top-level) aggregation and whether a fallback value
   is supplied for the empty-rows case.

   * With no fallback supplied, the clause is the bare aggregation, carrying the
     terminal marker as requested.
   * With a fallback supplied, the clause becomes the fallback form — and it
     MUST carry the SAME terminal marker the bare aggregation would have. The
     terminal status is a property of the aggregation itself and may not be
     dropped merely because the empty-rows fallback was wrapped around it. -/
def prepared (terminal : Bool) (defaultVal : Option Int) : Resolved :=
  match defaultVal with
  | none   => { isTerminal := terminal, hasFallback := false }
  | some _ => { isTerminal := terminal, hasFallback := true }
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Prepare an aggregation clause as it is added to a query. `terminal` says the
   aggregation is requested at the top level; `defaultVal` optionally supplies a
   value to substitute when the aggregation matches no rows.

   The frozen guarantee: the prepared clause ALWAYS carries the requested
   terminal marker — whether or not a fallback value is supplied — and reports
   the fallback form exactly when a fallback value is supplied. The terminal
   marker must never be lost when the fallback form is produced; otherwise a
   top-level aggregation with a fallback would be mis-placed by the query builder
   and produce malformed output.

   `terminal` and `defaultVal` are read-only inputs (not `mut`); the routine
   produces a fresh clause description and mutates nothing (directive 5). -/
method prepareAggregate (terminal : Bool) (defaultVal : Option Int) return (out : Resolved)
  ensures out = prepared terminal defaultVal
  ensures out.isTerminal = terminal
  ensures out.hasFallback = defaultVal.isSome
  do
    -- impl-start
    if defaultVal.isSome then
      return { isTerminal := terminal, hasFallback := true }
    else
      return { isTerminal := terminal, hasFallback := false }
    -- impl-end

prove_correct prepareAggregate by
  loom_solve
  all_goals (cases defaultVal <;> simp_all [prepared])
