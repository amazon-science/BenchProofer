import Mathlib
-- imports-end

/-!
Targeting the right rows when an update must cascade to a model's inheritance
ancestors.

When a model inherits from several base models, a single update may have to be
propagated to one update per ancestor. The set of identifiers used to target an
ancestor's rows must be that ancestor's *own* identifiers, read from a
materialized table of identifier rows. An ancestor that shares the
model's primary key reuses the model's identifier column (column `0`); an
ancestor that does not has its own dedicated identifier column, gathered
independently. Each ancestor is then paired, in order, with the identifiers read
from the column dedicated to it.
-/

-- axioms-start
-- No unchanged callee is consumed as an axiom: the surrounding query machinery
-- (identifier materialization, inheritance-path inspection) is abstracted into
-- this function's inputs — the table of identifier rows and the per-ancestor
-- flag recording whether the ancestor shares the model's primary key.
-- axioms-end

-- pure-start
/-- Assign each ancestor the column of the identifier-row table that carries its
identifiers. An ancestor that shares the model's primary key (`sharesPrimaryKey`)
reuses column `0`; otherwise it is given the next dedicated column, numbered from
`next`. Front-recursive companion of the accumulating loop in the impl. -/
def columnAssignment (sharesPrimaryKey : Nat → Bool) : List Nat → Nat → List (Nat × Nat)
  | [], _ => []
  | a :: rest, next =>
      if sharesPrimaryKey a then
        (a, 0) :: columnAssignment sharesPrimaryKey rest next
      else
        (a, next) :: columnAssignment sharesPrimaryKey rest (next + 1)
-- pure-end

-- post-conditions-start
/-- Correct targeting: each ancestor is paired, in its original order, with the
identifiers read from the table column dedicated to it — column `0` when the
ancestor shares the model's primary key, otherwise its own dedicated column,
numbered consecutively from `1` across the non-sharing ancestors. -/
def problem_spec_relatedTargetIds (ancestors : List Nat) (sharesPrimaryKey : Nat → Bool)
    (rows : List (List Int)) (result : List (Nat × List Int)) : Prop :=
  result =
    (columnAssignment sharesPrimaryKey ancestors 1).map
      (fun ac => (ac.1, rows.map (fun r => r.getD ac.2 0)))
-- post-conditions-end

-- impl-start
def implementation_relatedTargetIds (ancestors : List Nat) (sharesPrimaryKey : Nat → Bool)
    (rows : List (List Int)) : List (Nat × List Int) := Id.run do
  -- Gather only the model's own identifier column and reuse it for every
  -- ancestor, regardless of whether the ancestor actually shares it.
  let primaryIds := rows.map (fun r => r.getD 0 0)
  let mut result : List (Nat × List Int) := []
  for ancestor in ancestors do
    result := result ++ [(ancestor, primaryIds)]
  return result
-- impl-end

-- proof-start
theorem correct_relatedTargetIds : ∀ (ancestors : List Nat) (sharesPrimaryKey : Nat → Bool)
    (rows : List (List Int)),
    ancestors.Nodup →
    (∀ r ∈ rows, r.length = 1 + (ancestors.filter (fun a => !sharesPrimaryKey a)).length) →
    problem_spec_relatedTargetIds ancestors sharesPrimaryKey rows
      (implementation_relatedTargetIds ancestors sharesPrimaryKey rows) := by
  sorry
-- proof-end
