import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee needs an opaque signature here. The schema operations the
-- procedure issues are reified as `SchemaOp` data (below) and threaded through
-- structurally; nothing about the internal effect of issuing an operation is
-- modeled or assumed, so the proof consumes no callee axiom. The proof agent may
-- add `_prop` axioms only if genuinely stuck.
-- axioms-end

-- pure-start
/-- A schema-editor operation emitted while carrying a model rename to the
database. `renameTable old new` renames the main table from `old` to `new`; any
other emitted operation (the dependent-field / many-to-many follow-ups) is
represented opaquely as `other`. -/
inductive SchemaOp where
  | renameTable (old new : String) : SchemaOp
  | other (tag : Nat) : SchemaOp
  deriving DecidableEq, Repr, Inhabited
-- pure-end

-- post-conditions-start
/-- The procedure issues a sequence of schema operations for a model rename.

Inputs: `allowMigrate` is the applicability guard; `oldDbTable` / `newDbTable`
are the stored table names before and after the rename; `tailOps` is the
sequence of dependent follow-up operations the rename would otherwise issue.

The emitted sequence is pinned in every case:
* when the operation is not applicable, nothing is emitted;
* when the stored table name is unchanged by the rename, nothing is emitted
  (the rename is a no-op at the database level);
* otherwise the main table rename is emitted first, followed by exactly the
  dependent follow-up operations, unchanged and in order. -/
def problem_spec_renameModel
    (allowMigrate : Bool) (oldDbTable newDbTable : String)
    (tailOps : List SchemaOp) (result : List SchemaOp) : Prop :=
  (allowMigrate = false → result = []) ∧
  (allowMigrate = true → oldDbTable = newDbTable → result = []) ∧
  (allowMigrate = true → oldDbTable ≠ newDbTable →
      result = SchemaOp.renameTable oldDbTable newDbTable :: tailOps)
-- post-conditions-end

-- impl-start
-- Pre-patch (buggy) skeleton: there is no guard for an unchanged table name, so
-- whenever the operation is applicable the main table rename and all dependent
-- follow-up operations are emitted — even when the stored table name does not
-- change (where the database-level rename should be a no-op).
def implementation_renameModel
    (allowMigrate : Bool) (oldDbTable newDbTable : String)
    (tailOps : List SchemaOp) : List SchemaOp := Id.run do
  if !allowMigrate then
    return []
  let mut acc : List SchemaOp := []
  acc := acc ++ [SchemaOp.renameTable oldDbTable newDbTable]
  acc := acc ++ tailOps
  return acc
-- impl-end

-- proof-start
theorem correct_renameModel :
    ∀ (allowMigrate : Bool) (oldDbTable newDbTable : String) (tailOps : List SchemaOp),
      problem_spec_renameModel allowMigrate oldDbTable newDbTable tailOps
        (implementation_renameModel allowMigrate oldDbTable newDbTable tailOps) := by
  sorry   -- carries the gold proof body; UNCLOSABLE against the buggy impl (G-DIFF)
-- proof-end
