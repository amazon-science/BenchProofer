import Mathlib
-- imports-end

/-!
Computing the inter-application ordering constraints attached to a schema-change
operation that alters an existing field in place.

The setting: a schema migration is generated as a sequence of field-alteration
operations, one per field whose definition changed. Each such operation may
carry a list of ordering constraints ("dependencies"): other applications'
migrations that must be applied first, so that everything the altered field
refers to already exists when the alteration runs.

A field may be an ordinary value field, or it may be a RELATION — a field that
points at another model (a foreign-key-style reference). The desired behavior:

  * an alteration of an ordinary (non-relation) field needs no extra ordering
    constraint, so its operation carries an empty constraint list;

  * an alteration that makes the field a relation must carry the ordering
    constraints induced by that relation, so the referenced model's application
    is guaranteed to be migrated first. Otherwise the referenced model cannot be
    resolved when the alteration is applied.

The constraints induced by a relation are computed from the reference target:
* the application + object name of the referenced model — unless the reference
  targets a swap-configurable model, in which case the constraint names the
  configuration setting instead; and
* if the relation routes through an explicit intermediary model that was not
  auto-generated, an additional constraint naming that intermediary.

Each constraint records the target application label, the target object name, an
optional field name (here always absent), and a flag (here always set) marking
it as a "must exist before" ordering constraint.
-/

-- axioms-start
-- No opaque/axiom callee contract is consumed by this specification. The
-- relation-induced constraint computation is modeled DEEPLY as the pure helper
-- `getDependenciesForForeignKey` over the reference-target data (swap setting,
-- referenced application/object name, optional intermediary model), and is
-- validated == the real callee by G-AX. The per-operation constraint assembly
-- is modeled structurally over the field list, so no callee axiom is needed.
-- axioms-end

-- pure-start
/-- One ordering constraint: the target application label, the target object
name, an optional field name, and a flag marking it a "must exist before"
constraint (vs a "must be removed after"). -/
structure Dep where
  appLabel : String
  objectName : String
  fieldName : Option String
  create : Bool
deriving DecidableEq, Repr

/-- The reference-target data of a relation field, restricted to what the
constraint computation reads:
* `swappableSetting` — `some name` when the reference targets a swap-configurable
  model (the constraint then names the configuration setting), else `none`;
* `remoteAppLabel` / `remoteObjectName` — the referenced model's application
  label and object name (used when not swap-configurable);
* `through` — `some (app, obj, autoCreated)` when the relation routes through an
  explicit intermediary model, carrying that model's application label, object
  name, and whether it was auto-generated; `none` otherwise. -/
structure FKInfo where
  swappableSetting : Option String
  remoteAppLabel : String
  remoteObjectName : String
  through : Option (String × String × Bool)
deriving DecidableEq

/-- One altered field, restricted to the touched aspects:
* `isRelation` — whether the new field definition is a relation (points at a
  model);
* `fk` — the reference-target data (consulted only when `isRelation`; for a
  non-relation field its contents are irrelevant and never read). -/
structure AlteredField where
  isRelation : Bool
  fk : FKInfo
deriving DecidableEq

/-- One emitted field-alteration operation, restricted to the touched aspect:
* `field` — the altered field this operation alters (its identity);
* `dependencies` — the ordering constraints attached to this operation. The
  operation's other attributes are unchanged by the desired behavior and are not
  modeled. -/
structure AlterFieldOp where
  field : AlteredField
  dependencies : List Dep
deriving DecidableEq

/-- The ordering constraints induced by a relation's reference target. The base
constraint names the referenced model's application + object name, unless the
reference targets a swap-configurable model, in which case it names the
configuration setting. If the relation routes through an explicit, non
auto-generated intermediary model, a second constraint naming that intermediary
is appended. Both constraints carry no field name and are "must exist before"
constraints. -/
def getDependenciesForForeignKey (fk : FKInfo) : List Dep := Id.run do
  let base : Dep :=
    match fk.swappableSetting with
    | some s => { appLabel := "__setting__", objectName := s, fieldName := none, create := true }
    | none   => { appLabel := fk.remoteAppLabel, objectName := fk.remoteObjectName,
                  fieldName := none, create := true }
  let mut deps := [base]
  match fk.through with
  | some (tApp, tObj, autoCreated) =>
      if !autoCreated then
        deps := deps ++ [{ appLabel := tApp, objectName := tObj, fieldName := none, create := true }]
  | none => pure ()
  return deps
-- pure-end

-- post-conditions-start
/-- Exactly one alteration operation is emitted per altered field, in order, and
each operation alters precisely its field and carries: the relation-induced
ordering constraints when that field is a relation, and no constraint otherwise.
The result is element-wise pinned to the input field list — both which field
each operation alters AND the constraints it carries. -/
def problem_spec_generateAlteredFields
    (fields : List AlteredField)
    (result : List AlterFieldOp) : Prop :=
  result = fields.map (fun f =>
    { field := f,
      dependencies := if f.isRelation then getDependenciesForForeignKey f.fk else [] })
-- post-conditions-end

-- impl-start
def implementation_generateAlteredFields
    (fields : List AlteredField) : List AlterFieldOp := Id.run do
  let mut result := []
  for f in fields do
    -- The alteration operation is emitted without any ordering constraint,
    -- regardless of whether the field became a relation.
    let dependencies : List Dep := []
    result := result ++ [({ field := f, dependencies := dependencies } : AlterFieldOp)]
  return result
-- impl-end

-- proof-start
theorem correct_generateAlteredFields :
    ∀ (fields : List AlteredField),
      problem_spec_generateAlteredFields fields
        (implementation_generateAlteredFields fields) := by
  sorry   -- LEFT FOR THE PROOF AGENT — construction agent does NOT close this
-- proof-end
