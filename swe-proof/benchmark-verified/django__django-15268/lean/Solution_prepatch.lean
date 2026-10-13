import Mathlib
-- imports-end

/-!
Whether a schema-altering migration operation may be optimized across a later
operation. An "alter-together" operation adjusts a model's grouped column
options; there are two independent flavours (the unique-together flavour and the
index-together flavour). Such an operation may be optimized across a later
operation when either the later operation does not affect the same model, or the
later operation is an alter-together operation of the OTHER flavour (so the two
touch disjoint option groups and may be safely reordered/merged).
-/

-- axioms-start
/-- The two flavours of an alter-together operation. -/
inductive Kind where
  | unique
  | index
deriving DecidableEq

/-- The classification of an arbitrary later operation, as far as the decision
needs it: an alter-together operation of either flavour, or anything else. -/
inductive OpType where
  | alterUnique
  | alterIndex
  | other
deriving DecidableEq

/-- A later operation, reduced to the data the decision observes. -/
structure Op where
  ty : OpType
  name : String

/-- Whether the given operation affects (references) the model with the given
name. The decision below observes only its boolean value, never any finer
property of it. -/
opaque affectsModel : Op → String → Bool
-- axioms-end

-- pure-start
/-- Is this an alter-together operation (of either flavour)? -/
def isAlterTogether : OpType → Bool
  | .alterUnique => true
  | .alterIndex => true
  | .other => false

/-- The operation-type tag corresponding to a flavour. -/
def kindTag : Kind → OpType
  | .unique => .alterUnique
  | .index => .alterIndex

/-- The baseline rule, common to every model operation: it may be optimized
across a later operation exactly when that operation does not affect this
operation's model. -/
def baseCanOptimizeAcross (selfName : String) (operation : Op) : Bool :=
  !(affectsModel operation selfName)
-- pure-end

-- post-conditions-start
/-- An alter-together operation may be optimized across `operation` iff either
the later operation does not affect the same model, or the later operation is an
alter-together operation of a flavour different from this one. -/
def problem_spec_canOptimizeAcross
    (selfKind : Kind) (selfName : String) (operation : Op) (result : Bool) : Prop :=
  result = true ↔
    (affectsModel operation selfName = false) ∨
    (isAlterTogether operation.ty = true ∧ operation.ty ≠ kindTag selfKind)
-- post-conditions-end

-- impl-start
/-- PRE-PATCH (buggy): an alter-together operation used only the baseline rule,
with no special-case for a later alter-together operation of the other flavour. -/
def implementation_canOptimizeAcross
    (selfKind : Kind) (selfName : String) (operation : Op) : Bool :=
  baseCanOptimizeAcross selfName operation
-- impl-end

-- proof-start
theorem correct_canOptimizeAcross :
    ∀ (selfKind : Kind) (selfName : String) (operation : Op),
      problem_spec_canOptimizeAcross selfKind selfName operation
        (implementation_canOptimizeAcross selfKind selfName operation) := by
  intro selfKind selfName operation
  unfold problem_spec_canOptimizeAcross implementation_canOptimizeAcross baseCanOptimizeAcross
  simp only [Bool.or_eq_true, Bool.and_eq_true, Bool.not_eq_true', decide_eq_true_eq]
-- proof-end

#print axioms correct_canOptimizeAcross
