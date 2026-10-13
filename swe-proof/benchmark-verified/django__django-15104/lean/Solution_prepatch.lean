import Mathlib
-- imports-end

/-!
Normalizing a model's field deconstructions so that related-field targets are
ignored (used when detecting renamed models).

Each field of a model is reduced to a deconstruction: an import path, a list of
positional arguments, and a keyword mapping (unique keys). For the purpose of
comparing models up to renames, a field that points at another model must be
made target-agnostic: the entry recording its target model is dropped from the
keyword mapping, while every other component of the deconstruction is carried
over verbatim. A field that does not point at another model is carried over
unchanged.

The normalization visits the fields in their given order and collects the
transformed deconstructions in that same order. It is defined for every field —
in particular, dropping the target entry of a related field is well defined even
when that field's keyword mapping does not record a target at all (in which case
there is nothing to drop and the mapping is carried over as is). The result is
therefore always produced (it is never undefined) and is fully determined by the
input fields.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. Producing each
-- field's deconstruction (its path, positional arguments, and keyword mapping)
-- and the test of whether a field points at another model are folded into the
-- input representation `FieldDef`; the only operation the normalization performs
-- on its own — removing the target entry from a related field's keyword mapping
-- — is modeled directly as an association-list filter. So no `opaque`/`axiom`
-- callee contract is required.
-- axioms-end

-- pure-start
/-- A field's deconstruction: an import path, positional arguments, and a keyword
mapping with unique keys (modeled as an association list of key → value-token). -/
structure Decon where
  path : String
  args : List String
  kwargs : List (String × String)
deriving DecidableEq, Repr

/-- A field as the normalization observes it: whether it points at another model
(`isRelation`), together with its deconstruction. -/
structure FieldDef where
  isRelation : Bool
  decon : Decon
deriving DecidableEq, Repr

/-- The distinguished keyword key recording a related field's target model. -/
def targetKey : String := "to"

/-- Drop the target-model entry from a deconstruction's keyword mapping. Removing
an entry that is absent leaves the mapping unchanged (the keys are unique, so at
most one such entry exists). -/
def removeTarget (d : Decon) : Decon :=
  { d with kwargs := d.kwargs.filter (fun kv => kv.1 != targetKey) }

/-- The transform applied to a single field: a related field is made
target-agnostic; any other field is carried over unchanged. -/
def transformField (f : FieldDef) : Decon :=
  if f.isRelation then removeTarget f.decon else f.decon
-- pure-end

-- post-conditions-start
/-- The normalization is total (it always produces a result) and that result is
the list of per-field transforms, in the input order: each related field has its
target entry removed, every other field is carried over verbatim, and no field is
dropped, duplicated, or reordered (directive 5 frame — the path, the positional
arguments, and the non-target keyword entries are pinned to their input values
for every field). -/
def problem_spec_relationAgnosticFields
    (fields : List FieldDef) (result : Option (List Decon)) : Prop :=
  result = some (fields.map transformField)
-- post-conditions-end

-- impl-start
def implementation_relationAgnosticFields
    (fields : List FieldDef) : Option (List Decon) := Id.run do
  let mut acc : List Decon := []
  for f in fields do
    if f.isRelation then
      if f.decon.kwargs.any (fun kv => kv.1 == targetKey) then
        acc := acc ++ [removeTarget f.decon]
      else
        return none
    else
      acc := acc ++ [f.decon]
  return some acc
-- impl-end

-- proof-start
-- Gold proof body carried over from Solution.lean (SPEC_GUIDE §1.1). Against this
-- prepatch impl it cannot close: the spec demands the result is ALWAYS `some` of the
-- per-field transform, but this impl returns `none` (the real KeyError) whenever a
-- relation field's keyword mapping records no target entry, so the final `rw [h]; simp`
-- step faces `none = some …` and fails to typecheck (G-DIFF).
theorem correct_relationAgnosticFields :
    ∀ (fields : List FieldDef),
      problem_spec_relationAgnosticFields fields
        (implementation_relationAgnosticFields fields) := by
  intro fields
  unfold problem_spec_relationAgnosticFields implementation_relationAgnosticFields
  have h : ∀ (init : List Decon),
      (Id.run (forIn fields init (fun f acc =>
        (ForInStep.yield (acc ++ [if f.isRelation then removeTarget f.decon else f.decon])
          : Id (ForInStep (List Decon))))))
      = init ++ fields.map transformField := by
    intro init
    induction fields generalizing init with
    | nil => simp only [List.forIn_nil, List.map_nil, List.append_nil]; rfl
    | cons a as ih =>
      rw [List.forIn_cons]
      simp only [Id.run, bind] at ih ⊢
      rw [ih]
      simp only [transformField, List.map_cons, List.append_assoc, List.singleton_append]
  show some (Id.run (forIn fields ([] : List Decon) (fun f acc =>
      (ForInStep.yield (acc ++ [if f.isRelation then removeTarget f.decon else f.decon])
        : Id (ForInStep (List Decon))))))
    = some (fields.map transformField)
  rw [h]; simp
-- proof-end
