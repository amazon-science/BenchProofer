import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee needs an opaque signature here. The canonicalisation of a
-- field-name sequence into a hashable form is modeled DEEPLY (the `canonTF` map
-- below) rather than axiomatized, so the standard-library reference routine it
-- mirrors is validated as an A-reference by G-AX. The proof agent may add
-- `_prop` axioms only if it gets stuck.
-- axioms-end

-- pure-start
/-- A Python value as it appears inside the comparison/identity key of a related
relation. We only model the shapes that occur in the identity key: atomic
strings, the absence of a value, hashable tuples, and (non-hashable) lists. -/
inductive HVal where
  | hstr   (s : String)
  | hnone
  | htuple (xs : List HVal)
  | hlist  (xs : List HVal)
deriving Repr

/-- A field-name sequence parameter. It is either absent, a tuple of names, or a
list of names. Tuples are already in hashable form; a list is not. -/
inductive FieldSeq where
  | absent
  | astuple (xs : List String)
  | aslist  (xs : List String)
deriving Repr

/-- Canonical hashable form of a field-name sequence: an absent value stays
absent, and any present sequence (tuple or list) becomes a tuple of its names.
Mirrors the standard-library routine that normalises an arbitrary value into one
that produces a stable hash for equal values. -/
def canonTF : FieldSeq → HVal
  | .absent     => HVal.hnone
  | .astuple xs => HVal.htuple (xs.map HVal.hstr)
  | .aslist  xs => HVal.htuple (xs.map HVal.hstr)

/-- A value is in hashable form when it is not a list and, recursively at the one
level of nesting we model, contains no list element. -/
def hvalHashable : HVal → Bool
  | .hstr _    => true
  | .hnone     => true
  | .hlist _   => false
  | .htuple xs => xs.all (fun v => match v with | .hlist _ => false | _ => true)
-- pure-end

-- post-conditions-start
/-- The identity key of the relation is the unchanged prefix `base` followed by
the `through` model, then the field-name sequence in CANONICAL HASHABLE form, and
finally the `dbConstraint` flag. The unchanged components are pinned to their
inputs; the field-name slot is exactly the canonical hashable form of the input
sequence, so the whole key is always hashable. -/
def problem_spec_m2mIdentity
    (base : List HVal) (through : HVal)
    (throughFields : FieldSeq) (dbConstraint : HVal)
    (result : List HVal) : Prop :=
  result = base ++ [through, canonTF throughFields, dbConstraint]
-- post-conditions-end

-- impl-start
def implementation_m2mIdentity
    (base : List HVal) (through : HVal)
    (throughFields : FieldSeq) (dbConstraint : HVal) : List HVal := Id.run do
  let mut acc : List HVal := base
  acc := acc ++ [through]
  acc := acc ++ [canonTF throughFields]
  acc := acc ++ [dbConstraint]
  return acc
-- impl-end

-- proof-start
theorem correct_m2mIdentity :
    ∀ (base : List HVal) (through : HVal)
      (throughFields : FieldSeq) (dbConstraint : HVal),
      problem_spec_m2mIdentity base through throughFields dbConstraint
        (implementation_m2mIdentity base through throughFields dbConstraint) := by
  intro base through throughFields dbConstraint
  unfold problem_spec_m2mIdentity implementation_m2mIdentity
  simp only [Id.run, pure, List.append_assoc, List.cons_append, List.nil_append]
-- proof-end
