import Mathlib
-- imports-end

/-!
Identity, ordering, and hashing of model-field descriptors.

A field descriptor carries a creation-order counter and, optionally, the identity
of the model it is attached to. A model's identity is the pair of strings
(its application label, its model name); a descriptor that is not attached to any
model has no such identity.

The behaviour pinned below is how two field descriptors relate:

  * EQUALITY — two descriptors are equal exactly when they share the same
    creation-order counter AND the same attached-model identity (both unattached
    counts as the same identity).

  * ORDERING — descriptors are ordered primarily by creation-order counter (so
    descriptors with different counters keep their historical order). When two
    descriptors share a counter, an unattached descriptor precedes an attached
    one, and two attached descriptors are ordered lexicographically by their
    model identity (application label, then model name).

  * HASH KEY — the value a descriptor hashes by is the triple of its
    creation-order counter together with its attached-model identity split into
    its application-label and model-name components (absent when unattached). This
    key is what equal descriptors must share and unequal descriptors must be free
    to differ on.
-/

-- axioms-start
-- No unchanged outside callee is consumed as an axiom and none is referenced as a
-- deep model: every operation is a total read/comparison over the field
-- descriptor's own data, captured by the `FieldId` carrier below. Hence no
-- `opaque`/`axiom` declaration is required.
-- axioms-end

-- pure-start
/-- A field descriptor: its creation-order counter and, optionally, the identity
of the model it is attached to (application label, model name). `none` models a
descriptor with no attached model. -/
structure FieldId where
  creationCounter : Int
  model : Option (String × String)
deriving DecidableEq

/-- Lexicographic comparison of two model identities (application label first,
then model name). -/
def keyLt (a b : String × String) : Bool :=
  if a.1 = b.1 then decide (a.2 < b.2) else decide (a.1 < b.1)

/-- The ordering relation on field descriptors (functional reference for the
ordering spec): order by creation-order counter unless the counters are equal and
at least one descriptor is attached, in which case an unattached descriptor comes
first and two attached descriptors compare by model identity. -/
def fieldLtPure (a b : FieldId) : Bool :=
  if a.creationCounter ≠ b.creationCounter ∨ (a.model.isNone ∧ b.model.isNone) then
    decide (a.creationCounter < b.creationCounter)
  else if a.model.isSome ≠ b.model.isSome then
    a.model.isNone
  else
    match a.model, b.model with
    | some ka, some kb => keyLt ka kb
    | _, _ => false
-- pure-end

-- post-conditions-start
/-- Equality is pinned to BOTH the creation-order counter and the attached-model
identity: no output freedom remains. -/
def problem_spec_fieldEq (a b : FieldId) (result : Bool) : Prop :=
  result = ((a.creationCounter == b.creationCounter) && (a.model == b.model))
-- post-conditions-end

-- post-conditions-start
/-- The ordering result is pinned to the full ordering relation `fieldLtPure`. -/
def problem_spec_fieldLt (a b : FieldId) (result : Bool) : Prop :=
  result = fieldLtPure a b
-- post-conditions-end

-- post-conditions-start
/-- The hash key is pinned to the triple of the creation-order counter and the
two components of the attached-model identity (each absent when unattached). -/
def problem_spec_fieldHashKey
    (a : FieldId) (result : Int × Option String × Option String) : Prop :=
  result = (a.creationCounter, a.model.map Prod.fst, a.model.map Prod.snd)
-- post-conditions-end

-- impl-start
def implementation_fieldEq (a b : FieldId) : Bool := Id.run do
  return (a.creationCounter == b.creationCounter) && (a.model == b.model)
-- impl-end

-- impl-start
def implementation_fieldLt (a b : FieldId) : Bool := Id.run do
  -- Order by creation-order counter first (so descriptors with differing
  -- counters, or both unattached, keep their historical order).
  if a.creationCounter ≠ b.creationCounter ∨ (a.model.isNone ∧ b.model.isNone) then
    return decide (a.creationCounter < b.creationCounter)
  else if a.model.isSome ≠ b.model.isSome then
    -- exactly one is attached: the unattached descriptor comes first
    return a.model.isNone
  else
    -- counters equal and both attached: compare by model identity
    match a.model, b.model with
    | some ka, some kb => return keyLt ka kb
    | _, _ => return false
-- impl-end

-- impl-start
def implementation_fieldHashKey
    (a : FieldId) : Int × Option String × Option String := Id.run do
  return (a.creationCounter, a.model.map Prod.fst, a.model.map Prod.snd)
-- impl-end

-- proof-start
theorem correct_fieldEq :
    ∀ (a b : FieldId),
      problem_spec_fieldEq a b (implementation_fieldEq a b) := by
  intro a b
  unfold problem_spec_fieldEq implementation_fieldEq
  rfl
-- proof-end

-- proof-start
theorem correct_fieldLt :
    ∀ (a b : FieldId),
      problem_spec_fieldLt a b (implementation_fieldLt a b) := by
  intro a b
  unfold problem_spec_fieldLt implementation_fieldLt fieldLtPure
  simp only [Id.run]
  split <;> rfl
-- proof-end

-- proof-start
theorem correct_fieldHashKey :
    ∀ (a : FieldId),
      problem_spec_fieldHashKey a (implementation_fieldHashKey a) := by
  intro a
  unfold problem_spec_fieldHashKey implementation_fieldHashKey
  rfl
-- proof-end
