import Mathlib
-- imports-end

/-!
Validating one entry of an admin screen's column configuration.

When an admin registration lists the columns to display for a model, each listed
entry must resolve to something usable: a callable, an attribute of the admin
object itself, a concrete model field, or an attribute/method reachable on the
model. This routine decides, for a SINGLE listed entry, whether the entry is
acceptable and — if not — which diagnostic to emit.

The decision rests on four independent observations made about the entry:

* whether the entry is itself callable;
* whether the admin object exposes the entry as one of its own attributes;
* whether the model's metadata can produce a concrete field for the entry (it
  either yields a field or reports that no such field exists);
* whether the entry is reachable as an attribute on the model class (this access
  either yields a value or fails).

A field obtained either way additionally carries one relevant property: whether
it is a many-to-many relation.

The acceptance rule, abstractly:

* a callable entry is always acceptable;
* otherwise, an entry that is an attribute of the admin object is acceptable;
* otherwise the routine resolves a field for the entry — preferring the model
  metadata, and falling back to model attribute access. If a field is resolved
  by EITHER route, the entry is acceptable unless that field is a many-to-many
  relation, in which case the "must not be a many-to-many" diagnostic
  (`admin.E109`) is emitted;
* only when NEITHER route yields a field is the entry rejected as unresolvable,
  with the "not a callable / attribute / field" diagnostic (`admin.E108`).

The result is the (possibly empty) list of diagnostic identifiers produced for
the entry. The behavior is stated as an input→output relation; the
implementation and correctness proof are supplied separately.
-/

-- axioms-start
-- No unchanged dependency callee requires a contract. The four observations the
-- routine makes about the entry — callability, admin-attribute presence, the
-- metadata field lookup, and model attribute access — together with whether a
-- resolved field is a many-to-many relation, are supplied as the inputs below;
-- the acceptance/diagnostic logic is spelled out concretely.
-- axioms-end

-- pure-start
-- No additional pure helpers are needed; the decision is expressed directly.
-- pure-end

-- post-conditions-start
/-- Input→output relation for validating one display-configuration entry.

Inputs (the observations available at the decision point):
* `itemCallable` — the entry is callable;
* `adminHasAttr` — the entry is an attribute of the admin object;
* `modelField`   — the model-metadata field lookup: `none` = no such field,
                    `some b` = a field whose many-to-many flag is `b`;
* `modelAttr`    — model attribute access: `none` = no such attribute,
                    `some b` = a value whose many-to-many flag is `b`.

`result` is the list of diagnostic identifiers (empty = acceptable). The relation
pins the result in every case. -/
def problem_spec_validateDisplayItem
    (itemCallable adminHasAttr : Bool) (modelField modelAttr : Option Bool)
    (result : List String) : Prop :=
  (itemCallable = true → result = []) ∧
  (itemCallable = false → adminHasAttr = true → result = []) ∧
  (itemCallable = false → adminHasAttr = false → ∀ m, modelField = some m →
      result = (if m then ["E109"] else [])) ∧
  (itemCallable = false → adminHasAttr = false → modelField = none →
      ∀ m, modelAttr = some m → result = (if m then ["E109"] else [])) ∧
  (itemCallable = false → adminHasAttr = false → modelField = none → modelAttr = none →
      result = ["E108"])
-- post-conditions-end

-- impl-start
def implementation_validateDisplayItem
    (itemCallable adminHasAttr : Bool) (modelField modelAttr : Option Bool)
    : List String := Id.run do
  if itemCallable then
    return []
  if adminHasAttr then
    return []
  -- Resolve a field for the entry: prefer the metadata lookup, then fall back to
  -- model attribute access. If neither route yields a field, the entry is
  -- unresolvable.
  let mut fieldIsM2M : Bool := false
  match modelField with
  | some m => fieldIsM2M := m
  | none =>
    match modelAttr with
    | some m => fieldIsM2M := m
    | none => return ["E108"]
  if fieldIsM2M then
    return ["E109"]
  return []
-- impl-end


-- proof-start
theorem correct_validateDisplayItem :
    ∀ (itemCallable adminHasAttr : Bool) (modelField modelAttr : Option Bool),
      problem_spec_validateDisplayItem itemCallable adminHasAttr modelField modelAttr
        (implementation_validateDisplayItem itemCallable adminHasAttr modelField modelAttr) := by
  intro itemCallable adminHasAttr modelField modelAttr
  cases itemCallable <;> cases adminHasAttr <;>
    cases modelField <;> cases modelAttr <;>
    simp_all [problem_spec_validateDisplayItem, implementation_validateDisplayItem, Id.run, bind, pure]

-- proof-end
