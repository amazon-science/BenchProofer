import Mathlib
-- imports-end

/-!
Collecting the parent-link mapping while a model class is assembled.

When a model participates in multi-table inheritance, one of its one-to-one
relations to a base model is the *parent link*: the relation whose column is
promoted to the child's primary key. A model may declare several one-to-one
relations pointing at the very same base model — only the one explicitly
designated as the parent link should fill that role; the others are ordinary
relations and must not be mistaken for the link.

The mapping under construction associates each related-model identity with the
field that links to it. It is built by scanning the candidate fields in order and
recording, keyed by the related-model identity, the field that links to that
model. The association is last-write-wins: recording a field for a key that is
already present replaces the earlier entry.

Each candidate field exposes:

  * `isOneToOne`   — whether it is a one-to-one relation;
  * `parentLink`   — whether it is designated the parent link for its target;
  * `relatedKey`   — the identity of the related model it points at (the map key);
  * `name`         — the field's own stable identity.

A field is recorded into the mapping exactly when it is a one-to-one relation AND
it is designated the parent link for its target. Fields that are not one-to-one,
and one-to-one fields not designated as the parent link, are skipped entirely —
they never enter the mapping and so can never displace a genuine parent link that
shares their target.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. Each candidate
-- field's observable attributes (whether it is a one-to-one relation, whether it
-- is designated the parent link, its related-model identity, its own identity)
-- enter as plain data on the `FieldInfo` record. The only operation is the guarded
-- last-write-wins insertion into the mapping, modeled directly below. Hence no
-- `opaque`/`axiom` callee contract is required.
-- axioms-end

-- pure-start
/-- A candidate field, carrying only the attributes the mapping build observes.
`relatedKey` is the identity of the model the relation points at (the map key);
`name` is the field's own identity. -/
structure FieldInfo where
  isOneToOne : Bool
  parentLink : Bool
  relatedKey : String
  name : String
deriving Repr, DecidableEq

/-- Insert `(k, v)` into an association list with last-write-wins semantics:
drop any existing entry for key `k`, then append the new entry. This mirrors a
dictionary assignment `d[k] = v`, which keeps the most recently written value for
`k` and leaves every other key untouched. -/
def dictInsert (d : List (String × FieldInfo)) (k : String) (v : FieldInfo) :
    List (String × FieldInfo) :=
  d.filter (fun p => p.1 ≠ k) ++ [(k, v)]

/-- The parent-link mapping built from the candidate fields, scanned in order.
A field is recorded (keyed by its related-model identity) exactly when it is a
one-to-one relation that is designated the parent link for its target; every
other field is skipped. Last-write-wins resolves repeated keys. -/
def buildParentLinks (fields : List FieldInfo) : List (String × FieldInfo) :=
  fields.foldl
    (fun d f => if f.isOneToOne && f.parentLink then dictInsert d f.relatedKey f else d)
    []
-- pure-end

-- post-conditions-start
/-- The resulting mapping is fully determined by the candidate fields: it is
exactly the mapping obtained by scanning the fields in order and recording, with
last-write-wins, each one-to-one field that is designated the parent link for its
target. No part of the result is left free. -/
def problem_spec_collectParentLinks
    (fields : List FieldInfo) (result : List (String × FieldInfo)) : Prop :=
  result = buildParentLinks fields
-- post-conditions-end

-- impl-start
def implementation_collectParentLinks (fields : List FieldInfo) :
    List (String × FieldInfo) := Id.run do
  let mut parentLinks : List (String × FieldInfo) := []
  for field in fields do
    if field.isOneToOne && field.parentLink then
      parentLinks := dictInsert parentLinks field.relatedKey field
  return parentLinks
-- impl-end

-- proof-start
/-- Helper: the desugared `forIn` loop over the cleaned (branch-only) body equals
the `List.foldl` from `buildParentLinks`, generalized over the accumulator. -/
theorem forIn_collectParentLinks (fields : List FieldInfo)
    (init : List (String × FieldInfo)) :
    Id.run (forIn fields init (fun field r =>
        (if (field.isOneToOne && field.parentLink) = true then
          ForInStep.yield (dictInsert r field.relatedKey field)
        else ForInStep.yield r : Id _))) =
      List.foldl
        (fun d f => if (f.isOneToOne && f.parentLink) = true then dictInsert d f.relatedKey f else d)
        init fields := by
  induction fields generalizing init with
  | nil => rfl
  | cons a as ih =>
    rw [List.forIn_cons]
    simp only [Id.run, bind] at ih ⊢
    by_cases h : (a.isOneToOne && a.parentLink) = true
    · simp only [h, List.foldl_cons, if_true, ih]
    · simp only [Bool.not_eq_true] at h
      simp only [h, List.foldl_cons, ih, Bool.false_eq_true, if_false]

theorem correct_collectParentLinks :
    ∀ (fields : List FieldInfo),
      problem_spec_collectParentLinks fields
        (implementation_collectParentLinks fields) := by
  intro fields
  unfold problem_spec_collectParentLinks implementation_collectParentLinks buildParentLinks
  have h2 : (forIn fields ([] : List (String × FieldInfo)) (fun field r =>
              (if (field.isOneToOne && field.parentLink) = true then
                (do pure PUnit.unit; pure (ForInStep.yield (dictInsert r field.relatedKey field)))
              else (do pure PUnit.unit; pure (ForInStep.yield r)) : Id _)))
          = (forIn fields ([] : List (String × FieldInfo)) (fun field r =>
              (if (field.isOneToOne && field.parentLink) = true then
                ForInStep.yield (dictInsert r field.relatedKey field)
              else ForInStep.yield r : Id _))) := rfl
  simp only [Id.run]
  rw [h2]
  exact forIn_collectParentLinks fields []
-- proof-end
