import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee needs an opaque signature here. The referenced column's
-- already-computed parameter mapping is taken as an INPUT (grounded data, read
-- directly from the input carrier), and the choice between the two
-- column-alteration strategies is modeled DEEPLY as a sum type below rather than
-- axiomatized. The proof agent may add `_prop` axioms only if it gets stuck.
-- axioms-end

-- pure-start
/-- The database-level parameters describing a single column: its column type
text, an optional check-constraint expression, and an optional collation. -/
structure ColumnParams where
  colType : String
  checkExpr : Option String
  collation : Option String
deriving DecidableEq, Repr

/-- Which strategy is used to re-alter a column that references a key whose
parameters are changing: align its collation, or align its type. -/
inductive RelAlterKind where
  | collationAlter
  | typeAlter
deriving DecidableEq, Repr
-- pure-end

-- post-conditions-start
/-- The parameter mapping for a column that references another column. Its type
text and check expression are its own; its collation is pinned to the collation
of the referenced column's parameter mapping, so a referencing column always
carries the same collation as the column it points at. Every component is pinned
to its input. -/
def problem_spec_fkColumnParams
    (fkType : String) (fkCheck : Option String) (targetParams : ColumnParams)
    (result : ColumnParams) : Prop :=
  result.colType = fkType ∧
  result.checkExpr = fkCheck ∧
  result.collation = targetParams.collation
-- post-conditions-end

-- impl-start
def implementation_fkColumnParams
    (fkType : String) (fkCheck : Option String) (targetParams : ColumnParams) :
    ColumnParams := Id.run do
  -- Pre-patch (buggy): a referencing column's parameters omit the collation, so
  -- the collation of the referenced column is never carried over.
  let mut params : ColumnParams :=
    { colType := fkType, checkExpr := fkCheck, collation := none }
  return params
-- impl-end

-- proof-start
theorem correct_fkColumnParams :
    ∀ (fkType : String) (fkCheck : Option String) (targetParams : ColumnParams),
    problem_spec_fkColumnParams fkType fkCheck targetParams
      (implementation_fkColumnParams fkType fkCheck targetParams) := by
  sorry   -- LEFT FOR THE PROOF AGENT
-- proof-end

-- post-conditions-start
/-- Whether incoming references to this key must be torn down and rebuilt while
its parameters change. This is required when the backend supports such
references, the key is a stable primary/unique key on both sides, AND something
the referencing columns must mirror is changing — either the column type or the
collation. The result is determined by all inputs. -/
def problem_spec_rebuildIncomingFks
    (supportsFk oldPk newPk oldUnique newUnique : Bool)
    (oldType newType : String) (oldCollation newCollation : Option String)
    (result : Bool) : Prop :=
  result =
    (supportsFk &&
      ((oldPk && newPk) || (oldUnique && newUnique)) &&
      ((oldType != newType) || (oldCollation != newCollation)))
-- post-conditions-end

-- impl-start
def implementation_rebuildIncomingFks
    (supportsFk oldPk newPk oldUnique newUnique : Bool)
    (oldType newType : String) (oldCollation newCollation : Option String) :
    Bool := Id.run do
  let mut decision := supportsFk
  decision := decision && ((oldPk && newPk) || (oldUnique && newUnique))
  decision := decision && ((oldType != newType) || (oldCollation != newCollation))
  return decision
-- impl-end

-- proof-start
theorem correct_rebuildIncomingFks :
    ∀ (supportsFk oldPk newPk oldUnique newUnique : Bool)
      (oldType newType : String) (oldCollation newCollation : Option String),
    problem_spec_rebuildIncomingFks supportsFk oldPk newPk oldUnique newUnique
      oldType newType oldCollation newCollation
      (implementation_rebuildIncomingFks supportsFk oldPk newPk oldUnique
        newUnique oldType newType oldCollation newCollation) := by
  sorry   -- LEFT FOR THE PROOF AGENT
-- proof-end

-- post-conditions-start
/-- Which strategy re-aligns a referencing column when the referenced key's
parameters change. When the referencing column's collation differs from what it
should now be, the collation-aligning strategy is used; otherwise the
type-aligning strategy is used. The result is determined by the two collation
inputs. -/
def problem_spec_relatedColumnAlterKind
    (oldRelCollation relCollation : Option String)
    (result : RelAlterKind) : Prop :=
  result =
    (if oldRelCollation != relCollation then RelAlterKind.collationAlter
     else RelAlterKind.typeAlter)
-- post-conditions-end

-- impl-start
def implementation_relatedColumnAlterKind
    (oldRelCollation relCollation : Option String) : RelAlterKind := Id.run do
  if oldRelCollation != relCollation then
    return RelAlterKind.collationAlter
  return RelAlterKind.typeAlter
-- impl-end

-- proof-start
theorem correct_relatedColumnAlterKind :
    ∀ (oldRelCollation relCollation : Option String),
    problem_spec_relatedColumnAlterKind oldRelCollation relCollation
      (implementation_relatedColumnAlterKind oldRelCollation relCollation) := by
  sorry   -- LEFT FOR THE PROOF AGENT
-- proof-end
