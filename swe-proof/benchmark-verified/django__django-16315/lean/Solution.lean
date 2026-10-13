import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee needs an opaque signature here. The two attributes of a
-- resolved field that this behavior reads (its declared name and its database
-- column) are carried explicitly by the `FieldRef` carrier below, and the
-- identifier-quoting and separator-joining are reproduced concretely (R/I), not
-- abstracted behind an axiom. The proof agent may add `_prop` axioms only if it
-- gets stuck.
-- axioms-end

-- pure-start
/-- A resolved schema field, carrying only the two attributes this behavior
reads: its declared `name` and the `column` it occupies in the database (which
may differ from the name when an explicit database column is configured). -/
structure FieldRef where
  name : List Char
  column : List Char
deriving DecidableEq, Repr

/-- Quote a database identifier for embedding in SQL: wrap it in double quotes,
unless it is already wrapped in double quotes (quoting once is enough). -/
def quoteName (s : List Char) : List Char :=
  match s.head?, s.getLast? with
  | some '"', some '"' => s
  | _, _ => '"' :: (s ++ ['"'])

/-- The text assigning one updated column from the conflicting row: the quoted
column, ` = EXCLUDED.`, then the same quoted column. -/
def assignColumn (f : FieldRef) : List Char :=
  let q := quoteName f.column
  q ++ " = EXCLUDED.".toList ++ q
-- pure-end

-- post-conditions-start
/-- The upsert suffix renders the conflict-target list and the assignment list,
both keyed by each field's database `column` (never its declared name), separated
by `", "`. The literal template text framing the two slots is pinned verbatim,
and both rendered slots are pinned element-wise to the input field lists, so no
component is left unconstrained. -/
def problem_spec_renderUpsertClause
    (uniqueFields updateFields : List FieldRef) (result : List Char) : Prop :=
  result =
    "ON CONFLICT(".toList
      ++ List.intercalate ", ".toList (uniqueFields.map (fun f => quoteName f.column))
      ++ ") DO UPDATE SET ".toList
      ++ List.intercalate ", ".toList (updateFields.map assignColumn)
-- post-conditions-end

-- impl-start
def implementation_renderUpsertClause
    (uniqueFields updateFields : List FieldRef) : List Char := Id.run do
  let mut uniqueCols : List (List Char) := []
  for f in uniqueFields do
    uniqueCols := uniqueCols ++ [quoteName f.column]
  let mut assigns : List (List Char) := []
  for f in updateFields do
    assigns := assigns ++ [assignColumn f]
  return "ON CONFLICT(".toList ++ List.intercalate ", ".toList uniqueCols
    ++ ") DO UPDATE SET ".toList ++ List.intercalate ", ".toList assigns
-- impl-end

-- proof-start
/-- The cleaned `forIn` accumulation loop `acc := acc ++ [g f]`, generalized
over the accumulator, computes `init ++ xs.map g`. -/
theorem foldMapHelper_renderUpsertClause
    (g : FieldRef → List Char) (xs : List FieldRef) (init : List (List Char)) :
    (forIn (m := Id) xs init (fun f acc => pure (ForInStep.yield (acc ++ [g f]))))
      = init ++ xs.map g := by
  induction xs generalizing init with
  | nil => simp only [List.map_nil, List.append_nil]; rfl
  | cons a as ih =>
    rw [List.forIn_cons]
    simp only [bind] at ih ⊢
    rw [ih]
    simp [List.append_assoc]

theorem correct_renderUpsertClause :
    ∀ (uniqueFields updateFields : List FieldRef),
    problem_spec_renderUpsertClause uniqueFields updateFields
      (implementation_renderUpsertClause uniqueFields updateFields) := by
  intro uf vf
  unfold problem_spec_renderUpsertClause implementation_renderUpsertClause
  simp only [Id.run, bind]
  rw [foldMapHelper_renderUpsertClause (fun f => quoteName f.column) uf [],
      foldMapHelper_renderUpsertClause assignColumn vf []]
  simp only [List.nil_append]
  rfl
-- proof-end
