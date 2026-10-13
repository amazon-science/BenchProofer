import Mathlib
-- imports-end

/-!
Choosing how a newly-added column is materialized on a backend whose in-place
column-addition statement is restricted.

Some backends can append a column to an existing table only when the column is
"plain": it permits nulls, carries no stored default value, and is neither a
primary-key column nor a uniqueness-bearing column. For any column outside that
plain class the column cannot be appended in place and the table must instead be
reconstructed to accommodate it.

The decision modeled here returns whether the table must be reconstructed. The
table must be reconstructed exactly when the column is a primary-key column, or a
uniqueness-bearing column, or a non-nullable column, or a column that carries a
stored default value; otherwise the plain in-place column addition suffices.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. Whether the
-- column carries a stored default value is computed elsewhere by machinery that
-- is identical regardless of the decision modeled here; it is abstracted into
-- the input as a single boolean observation rather than recomputed, so no
-- `opaque`/`axiom` callee contract is needed.
-- axioms-end

-- pure-start
/-- The properties of a freshly-added column that determine how the column is
materialized on the restricted backend. Each component is the boolean
observation the decision consults:

* `isPrimaryKey`   — the column is the table's primary-key column;
* `isUnique`       — the column carries a uniqueness requirement;
* `allowsNull`     — the column permits null values;
* `hasStoredDefault` — the column carries a stored default value. -/
structure ColumnProps where
  isPrimaryKey : Bool
  isUnique : Bool
  allowsNull : Bool
  hasStoredDefault : Bool
-- pure-end

-- post-conditions-start
/-- The table must be reconstructed exactly when the column is a primary-key
column, or a uniqueness-bearing column, or a non-nullable column, or a column
that carries a stored default value. Each of these four conditions independently
forces reconstruction; only a column that is none of them is materialized by the
plain in-place column addition. -/
def problem_spec_requiresTableRebuild (c : ColumnProps) (result : Bool) : Prop :=
  result = (c.isPrimaryKey || c.isUnique || !c.allowsNull || c.hasStoredDefault)
-- post-conditions-end

-- impl-start
def implementation_requiresTableRebuild (c : ColumnProps) : Bool := Id.run do
  if c.isPrimaryKey || c.isUnique || !c.allowsNull || c.hasStoredDefault then
    return true
  return false
-- impl-end

-- proof-start
theorem correct_requiresTableRebuild :
    ∀ (c : ColumnProps),
      problem_spec_requiresTableRebuild c
        (implementation_requiresTableRebuild c) := by
  intro c
  unfold problem_spec_requiresTableRebuild implementation_requiresTableRebuild
  simp only [Id.run, bind, pure]
  by_cases h : (c.isPrimaryKey || c.isUnique || !c.allowsNull || c.hasStoredDefault) = true
  · simp [h]
  · simp only [Bool.not_eq_true] at h
    simp [h]
-- proof-end
