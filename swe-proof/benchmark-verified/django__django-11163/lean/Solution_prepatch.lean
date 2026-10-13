import Mathlib
-- imports-end

/-!
Projecting a record's editable fields into an ordered association list.

We are given a sequence of field records, each carrying a name, an "editable"
flag, and an extracted value. We build an association list of `(name, value)`
pairs by walking the sequence in order and keeping a field exactly when all of
the following hold:

  * the field is editable;
  * an OPTIONAL inclusion selection includes it — the selection is either absent
    or an explicit list of names. When the selection is ABSENT, every field is
    included. When the selection is PRESENT, only fields whose name occurs in it
    are included; in particular an empty selection includes NOTHING;
  * an OPTIONAL exclusion list does not bar it — the exclusion is either absent
    or an explicit list of names. A field is barred exactly when its name occurs
    in that list; an absent or empty exclusion bars nothing.

The two options are independent of each other and of the field order: the result
keeps the surviving fields in their original sequence order, pairing each with
its own name and its own extracted value.

The salient point is the meaning of the inclusion selection: being ABSENT
(no selection supplied) and being PRESENT-BUT-EMPTY are different requests. An
absent selection imposes no inclusion constraint, whereas an empty selection is
a genuine request that includes no field at all.
-/

-- axioms-start
-- No unchanged outside callee is consumed as an axiom. The only per-field datum
-- the projection reads beyond a field's name and editability is its extracted
-- value; that value is unchanged by the modeled behavior, so it is carried as a
-- given attribute `Field.val` (a type refinement) rather than axiomatized. Hence
-- the spec needs no `opaque`/`axiom` callee contract.
-- axioms-end

-- pure-start
/-- A field record, restricted to the three attributes the projection reads:
its name, whether it is editable, and its extracted value. -/
structure FieldRec (α : Type) where
  name : String
  editable : Bool
  val : α

/-- Whether a field survives the projection, given the optional inclusion
selection and the optional exclusion list. A field survives iff it is editable,
the inclusion selection includes it (absent ⇒ include all; present ⇒ name must occur,
so an empty selection includes none), and the exclusion list does not contain its
name (absent ⇒ bar none). -/
def keep {α : Type} (fields exclude : Option (List String)) (f : FieldRec α) : Bool :=
  f.editable
  && (match fields with
      | none => true
      | some sel => sel.contains f.name)
  && (match exclude with
      | none => true
      | some ex => !ex.contains f.name)
-- pure-end

-- post-conditions-start
/-- The result is fully pinned to the inputs: it is exactly the surviving fields
(in their original order) paired with their own name and extracted value. Order,
membership, names, and values are all determined — no output component is free.

In particular, when the inclusion selection is present and empty no field
survives (the result is empty), and when it is absent every editable, non-barred
field survives. -/
def problem_spec_modelToDict {α : Type} (fields exclude : Option (List String))
    (fs : List (FieldRec α)) (result : List (String × α)) : Prop :=
  result = (fs.filter (keep fields exclude)).map (fun f => (f.name, f.val))
-- post-conditions-end

-- impl-start
def implementation_modelToDict {α : Type} (fields exclude : Option (List String))
    (fs : List (FieldRec α)) : List (String × α) := Id.run do
  let mut data : List (String × α) := []
  for f in fs do
    -- skip non-editable fields
    if !f.editable then
      continue
    -- a non-empty inclusion selection must name the field; an empty selection
    -- imposes no constraint (treated the same as no selection)
    if let some sel := fields then
      if !sel.isEmpty then
        if !(sel.contains f.name) then
          continue
    -- a present exclusion list bars the field if it names it
    if let some ex := exclude then
      if ex.contains f.name then
        continue
    data := data ++ [(f.name, f.val)]
  return data
-- impl-end

-- proof-start
theorem correct_modelToDict :
    ∀ {α : Type} (fields exclude : Option (List String)) (fs : List (FieldRec α)),
      problem_spec_modelToDict fields exclude fs
        (implementation_modelToDict fields exclude fs) := by
  intro α fields exclude fs
  unfold problem_spec_modelToDict implementation_modelToDict keep
  simp   -- carries the gold proof body; UNCLOSABLE against the buggy impl (G-DIFF)
-- proof-end
