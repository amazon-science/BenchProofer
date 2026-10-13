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
  -- Pre-patch (buggy): the suffix is keyed by each field's declared name rather
  -- than its database column, so a field configured with a distinct database
  -- column is referenced by the wrong identifier.
  let mut uniqueCols : List (List Char) := []
  for f in uniqueFields do
    uniqueCols := uniqueCols ++ [quoteName f.name]
  let mut assigns : List (List Char) := []
  for f in updateFields do
    let q := quoteName f.name
    assigns := assigns ++ [q ++ " = EXCLUDED.".toList ++ q]
  return "ON CONFLICT(".toList ++ List.intercalate ", ".toList uniqueCols
    ++ ") DO UPDATE SET ".toList ++ List.intercalate ", ".toList assigns
-- impl-end

-- proof-start
theorem correct_renderUpsertClause :
    ∀ (uniqueFields updateFields : List FieldRef),
    problem_spec_renderUpsertClause uniqueFields updateFields
      (implementation_renderUpsertClause uniqueFields updateFields) := by
  -- Gold proof body carried over; UNCLOSABLE against the name-keyed buggy impl
  -- (the spec keys on `.column`). (G-DIFF.)
  intro uniqueFields updateFields
  unfold problem_spec_renderUpsertClause implementation_renderUpsertClause
  simp [Id.run, assignColumn]
-- proof-end
