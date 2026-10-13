import Mathlib
-- imports-end

/-!
Installing a prepared query into a result set, and keeping the row-building
strategy consistent with what the query projects.

A result set carries two pieces of state: the prepared query it will run, and the
strategy used to turn each raw database row into a Python-level result value. Some
queries project a specific set of named fields (so each row is naturally a mapping
from field name to value); others project no specific fields (so each row is a
full model instance).

When a prepared query is installed into a result set, the stored query is replaced
by exactly that query. In addition, if the installed query projects a specific set
of fields, the row-building strategy is set to the one that yields field-value
mappings — so that a result set fed a field-projecting query produces field-value
mappings rather than model instances. If the installed query projects no specific
fields, the existing row-building strategy is left untouched.
-/

-- axioms-start
-- No unchanged outside callee is consumed as an axiom and none is deep-modeled.
-- Installing a query reads one thing off the query — the set of fields it
-- projects — and performs two state updates (store the query; possibly switch the
-- row-building strategy). The available row-building strategies are modeled
-- directly as the constructors of `RowMode` (sentinel choices that are selected,
-- never invoked), so the bundle needs no `opaque`/`axiom` callee contract.
-- axioms-end

-- pure-start
/-- The row-building strategy a result set uses to turn each raw row into a
result value. The distinguished value here is `fieldValuesDict` (each row becomes
a mapping from projected field name to value); `modelInstances` builds a full
model instance per row; the remaining three are alternative field-projecting
strategies (tuple / single-value / named-tuple per row). -/
inductive RowMode where
  | modelInstances
  | fieldValuesDict
  | fieldValuesTuple
  | fieldValuesFlat
  | fieldValuesNamed
deriving DecidableEq, Repr

/-- A prepared query, observed only by the list of field names it projects
(empty ⇔ it projects no specific fields). -/
structure StoredQuery where
  selectedFields : List String
deriving DecidableEq, Repr

/-- A result set: the row-building strategy plus the prepared query it will run. -/
structure ResultSet where
  rowMode : RowMode
  storedQuery : StoredQuery
deriving Repr
-- pure-end

-- post-conditions-start
/-- Installing `value` into `rs` is fully pinned to the inputs:

  * the stored query of the result is exactly the installed `value`
    (directive-5 frame: the query component always equals its input);
  * if `value` projects a specific set of fields (`selectedFields ≠ []`) the
    row-building strategy of the result is the field-value-mapping strategy
    (`fieldValuesDict`), regardless of the prior strategy;
  * if `value` projects no specific fields (`selectedFields = []`) the
    row-building strategy is left equal to its prior value `rs.rowMode`
    (directive-5 frame: the unchanged branch pins the component to its input).

Both output components are pinned in every case, so no incorrect installer can
fill a free hole. -/
def problem_spec_installQuery
    (rs : ResultSet) (value : StoredQuery) (result : ResultSet) : Prop :=
  result.storedQuery = value ∧
  (value.selectedFields ≠ [] → result.rowMode = RowMode.fieldValuesDict) ∧
  (value.selectedFields = [] → result.rowMode = rs.rowMode)
-- post-conditions-end

-- impl-start
def implementation_installQuery
    (rs : ResultSet) (value : StoredQuery) : ResultSet := Id.run do
  -- PRE-PATCH (buggy): installing a query only stores it; the row-building
  -- strategy is left untouched, even when the installed query projects a specific
  -- set of fields — so a result set fed a field-projecting query keeps whatever
  -- strategy it had (e.g. the model-instance strategy) instead of switching to
  -- the field-value-mapping strategy.
  let mut rs := rs
  rs := { rs with storedQuery := value }
  return rs
-- impl-end

-- proof-start
theorem correct_installQuery :
    ∀ (rs : ResultSet) (value : StoredQuery),
      problem_spec_installQuery rs value (implementation_installQuery rs value) := by
  intro rs value
  unfold problem_spec_installQuery implementation_installQuery
  simp only [Id.run, bind, pure]
  split
  · next h => exact ⟨rfl, fun _ => rfl, fun hc => absurd hc h⟩
  · next h => exact ⟨rfl, fun hc => absurd hc h, fun _ => rfl⟩
-- proof-end
