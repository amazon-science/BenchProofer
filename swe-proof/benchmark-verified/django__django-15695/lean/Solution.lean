import Mathlib
-- imports-end

/-!
Deciding whether a schema operation that relabels a database index from one name
to another should actually emit the underlying relabel, and with which index
pair.

The operation works on a model whose migration may or may not be permitted on the
current connection. When migration is not permitted the operation does nothing.
Otherwise it has in hand the index it would relabel *from* (identified earlier in
the operation) and the index it would relabel *to*; each index carries a name.

The relabel is only meaningful when it actually changes the name: if the starting
entry already bears the target name, there is nothing to do and no relabel is
emitted. In every other permitted case the operation emits exactly one relabel of
the starting entry to the target entry.
-/

-- axioms-start
-- No unchanged outside callee is consumed. Whether migration is permitted, the
-- starting index, the target index, and the target name all enter as plain data
-- (already resolved upstream); the only operation modeled is the decision of
-- which relabel to emit, if any, spelled out directly below. Hence no
-- `opaque`/`axiom` callee contract is required.
-- axioms-end

-- pure-start
/-- The touched view of a database index: only its `name` is consulted by the
decision modeled here. -/
structure Index where
  name : String
deriving DecidableEq, Repr
-- pure-end

-- post-conditions-start
/-- The emitted relabel action is fully pinned to the inputs:

  * if migration is not permitted, no relabel is emitted (`result = none`);
  * if migration is permitted but the starting index already carries the target
    name, no relabel is emitted (`result = none`);
  * if migration is permitted and the starting index's name differs from the
    target name, exactly the relabel of the starting index to the target index is
    emitted (`result = some (oldIndex, newIndex)`).

Every input configuration determines the result, so no output is left free. -/
def problem_spec_applyIndexRenameForward
    (canMigrate : Bool) (oldIndex newIndex : Index) (newName : String)
    (result : Option (Index × Index)) : Prop :=
  (canMigrate = false → result = none) ∧
  (canMigrate = true → oldIndex.name = newName → result = none) ∧
  (canMigrate = true → oldIndex.name ≠ newName →
      result = some (oldIndex, newIndex))
-- post-conditions-end

-- impl-start
def implementation_applyIndexRenameForward
    (canMigrate : Bool) (oldIndex newIndex : Index) (newName : String) :
    Option (Index × Index) := Id.run do
  if canMigrate = false then
    return none
  if oldIndex.name = newName then
    return none
  return some (oldIndex, newIndex)
-- impl-end

-- proof-start
theorem correct_applyIndexRenameForward :
    ∀ (canMigrate : Bool) (oldIndex newIndex : Index) (newName : String),
      problem_spec_applyIndexRenameForward canMigrate oldIndex newIndex newName
        (implementation_applyIndexRenameForward canMigrate oldIndex newIndex newName) := by
  intro canMigrate oldIndex newIndex newName
  unfold problem_spec_applyIndexRenameForward implementation_applyIndexRenameForward
  refine ⟨?_, ?_, ?_⟩
  · intro h
    simp [Id.run, h, pure]
  · intro h1 h2
    simp [Id.run, h1, h2, pure, bind]
  · intro h1 h2
    simp [Id.run, h1, h2, pure, bind]
-- proof-end
