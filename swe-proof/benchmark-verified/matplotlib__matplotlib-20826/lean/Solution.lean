import Mathlib
-- imports-end

/-!
Re-initialising an axis' tick configuration.

An axis carries two keyword tables that record per-tick appearance settings —
one for the major ticks and one for the minor ticks. Each table maps a setting
name (a string key such as the grid-visibility flag, or the per-side tick and
label visibility flags) to its value. These tables are populated over the life
of the axis: in particular, when two axes share a common scale, several
per-side visibility entries are written so that interior ticks and labels are
suppressed.

The behaviour modeled here is the step that re-initialises this configuration.
It must recompute exactly one designated entry — the grid-visibility flag — from
the current global drawing preferences, while leaving every other entry of each
table exactly as it already stood. The grid flag is on for the major table when
grids are globally enabled AND the global "which ticks" preference selects the
major ticks (either the dedicated major selection or the combined selection);
symmetrically for the minor table. No other key of either table is created,
removed, or altered: their values carry through unchanged.

The two tables are handled by the same rule and differ only in which "which
ticks" preference value enables their grid flag.
-/

-- axioms-start
-- No unchanged outside callee is invoked: the grid-flag value is computed from
-- the two global drawing preferences with concrete boolean logic, and the
-- preservation of the remaining entries is a pure structural property. Hence
-- there is no `opaque` callee to declare and no consumed `_prop` axiom.
-- axioms-end

-- pure-start
/-- The string key naming the grid-visibility entry of a tick-keyword table. -/
def gridKey : String := "gridOn"

/-- A tick-keyword table: each setting name maps to an optional boolean value
(`none` = the entry is absent, `some b` = present with value `b`). The setting
values relevant to the modeled behaviour are visibility flags, hence booleans
(see mapping.md for the refinement). -/
abbrev TickKw := String → Option Bool

/-- The pair of tables touched together: the major-tick table and the
minor-tick table. -/
structure TickKwPair where
  major : TickKw
  minor : TickKw

/-- Grid flag for the major table: grids globally enabled, and the global
"which ticks" preference selects the major ticks. -/
def majorGridOn (gridEnabled : Bool) (which : String) : Bool :=
  gridEnabled && (which == "both" || which == "major")

/-- Grid flag for the minor table: grids globally enabled, and the global
"which ticks" preference selects the minor ticks. -/
def minorGridOn (gridEnabled : Bool) (which : String) : Bool :=
  gridEnabled && (which == "both" || which == "minor")
-- pure-end

-- post-conditions-start
/-- Re-initialising the tick configuration. The result is pinned completely
(frame discipline):

* the grid-visibility entry of each table equals that table's freshly computed
  grid flag;
* every OTHER key of each table is unchanged from its prior value — nothing
  about the previously-recorded entries is left free.

This is what guarantees that the per-side visibility entries written for shared
axes survive the re-initialisation. -/
def problem_spec_clear
    (s : TickKwPair) (gridEnabled : Bool) (which : String)
    (result : TickKwPair) : Prop :=
  result.major gridKey = some (majorGridOn gridEnabled which) ∧
  result.minor gridKey = some (minorGridOn gridEnabled which) ∧
  (∀ k, k ≠ gridKey → result.major k = s.major k) ∧
  (∀ k, k ≠ gridKey → result.minor k = s.minor k)
-- post-conditions-end

-- impl-start
def implementation_clear
    (s : TickKwPair) (gridEnabled : Bool) (which : String) : TickKwPair := Id.run do
  let mut major := s.major
  let mut minor := s.minor
  major := Function.update major gridKey (some (majorGridOn gridEnabled which))
  minor := Function.update minor gridKey (some (minorGridOn gridEnabled which))
  return ⟨major, minor⟩
-- impl-end

-- proof-start
theorem correct_clear :
    ∀ (s : TickKwPair) (gridEnabled : Bool) (which : String),
      problem_spec_clear s gridEnabled which
        (implementation_clear s gridEnabled which) := by
  intro s gridEnabled which
  unfold problem_spec_clear implementation_clear
  simp only [Id.run, pure]
  refine ⟨?_, ?_, ?_, ?_⟩
  · rw [Function.update_self]
  · rw [Function.update_self]
  · intro k hk
    rw [Function.update_of_ne hk]
  · intro k hk
    rw [Function.update_of_ne hk]
-- proof-end
