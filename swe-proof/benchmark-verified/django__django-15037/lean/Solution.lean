import Mathlib
-- imports-end

-- axioms-start
/-- The transform from a database table name to the corresponding model class
identifier. It is a pure, deterministic function of the table name; the bundle
only relies on it being a function, so it is declared opaque and validated as a
reference against the real callee by G-AX. -/
opaque dbTableToModelName : String → String
-- axioms-end

-- pure-start
/-- The relation-column outputs computed for an introspected database column
that participates in a relation: the relation field kind, the referenced target
(the literal `"self"` or a model identifier), and the optional explicit target
column name. -/
structure RelationField where
  relType : String
  relTo : String
  toField : Option String
deriving DecidableEq, Repr
-- pure-end

-- post-conditions-start
/-- Specification of the relation-column outputs.

Inputs describe an introspected column that references another column
`refDbColumn` in table `refDbTable` (the current table is `tableName`), together
with whether the column is treated as unique / a primary key, and the referenced
table's detected primary-key column `refPkColumn` (`none` when the referenced
table has no detectable primary key).

* The field kind is the one-to-one kind exactly when the column is unique or a
  primary key, otherwise the plain foreign-key kind.
* The referenced target is `"self"` when the relation points back at the current
  table, otherwise the model identifier of the referenced table.
* An explicit target column is recorded exactly when the field is a plain
  foreign key AND the referenced table has a detected primary-key column that
  differs from the referenced column; in that case it is the referenced column.
  In every other case there is no explicit target column. -/
def problem_spec_relationField
    (isUnique isPrimaryKey : Bool)
    (refDbColumn refDbTable tableName : String)
    (refPkColumn : Option String)
    (result : RelationField) : Prop :=
  result.relType = (if isUnique || isPrimaryKey then "OneToOneField" else "ForeignKey") ∧
  result.relTo = (if refDbTable = tableName then "self" else dbTableToModelName refDbTable) ∧
  result.toField =
    (if isUnique || isPrimaryKey then none
     else
       match refPkColumn with
       | some pk => if pk ≠ refDbColumn then some refDbColumn else none
       | none => none)
-- post-conditions-end

-- impl-start
def implementation_relationField
    (isUnique isPrimaryKey : Bool)
    (refDbColumn refDbTable tableName : String)
    (refPkColumn : Option String) : RelationField := Id.run do
  let mut relType : String := "ForeignKey"
  let mut toField : Option String := none
  if isUnique || isPrimaryKey then
    relType := "OneToOneField"
  else
    relType := "ForeignKey"
    match refPkColumn with
    | some pk => if pk ≠ refDbColumn then toField := some refDbColumn
    | none => pure ()
  let relTo : String :=
    if refDbTable = tableName then "self" else dbTableToModelName refDbTable
  return { relType := relType, relTo := relTo, toField := toField }
-- impl-end

-- proof-start
theorem correct_relationField :
    ∀ (isUnique isPrimaryKey : Bool) (refDbColumn refDbTable tableName : String)
      (refPkColumn : Option String),
      problem_spec_relationField isUnique isPrimaryKey refDbColumn refDbTable tableName refPkColumn
        (implementation_relationField isUnique isPrimaryKey refDbColumn refDbTable tableName refPkColumn) := by
  intro isUnique isPrimaryKey refDbColumn refDbTable tableName refPkColumn
  unfold problem_spec_relationField implementation_relationField
  simp only [Id.run, bind, pure]
  by_cases h : isUnique || isPrimaryKey
  · simp only [h, if_true, and_self]
  · cases refPkColumn with
    | none => simp only [h, Bool.not_eq_true] at *; exact ⟨rfl, rfl, rfl⟩
    | some pk =>
      by_cases hk : pk = refDbColumn
      · simp only [h, hk, Bool.not_eq_true, ne_eq, not_true_eq_false] at *
        exact ⟨rfl, rfl, rfl⟩
      · simp only [h, hk, Bool.not_eq_true, ne_eq, not_false_eq_true] at *
        exact ⟨rfl, rfl, rfl⟩
-- proof-end
