import Mathlib
-- imports-end

/-!
Relocating a filter condition into a nested subquery.

When a negated relational filter over a one-to-many relation has to be evaluated
through an auxiliary nested subquery, the right-hand side of the filter
condition must be carried into the inner query while preserving WHICH query each
reference resolves against.

A right-hand side is one of three shapes:
  * a direct literal value (resolves to itself);
  * a same-query column reference (a name pointing at a column of the query it
    sits in);
  * an outer-query reference, carrying a nesting level that says how many query
    boundaries outward it must reach to find the column it names.

Because the relocation pushes the condition one query boundary deeper, the
reference must be re-anchored:
  * a direct literal is unchanged;
  * a same-query column reference becomes an outer-query reference reaching out
    one level (so it still names the column of the query the condition came
    from);
  * an existing outer-query reference must reach out one ADDITIONAL level, since
    a new query boundary now sits between it and its target.

The left-hand side of the condition is untouched by the relocation. This is
stated abstractly as an input→output relation; the implementation and
correctness proof are supplied separately.
-/

-- axioms-start
-- No unchanged dependency callee requires a contract: the relocation is modeled
-- deeply with concrete operations (a three-way shape dispatch and a nesting-level
-- adjustment).
-- axioms-end

-- pure-start
/-- The right-hand side of a relocated filter condition. `outerRef level name`
names a column `name` reachable by crossing `level` query boundaries outward
(`level ≥ 1`); `colRef name` names a column of the current query; `value v` is a
direct literal. -/
inductive FilterRHS where
  | value (v : Int)
  | colRef (name : String)
  | outerRef (level : Nat) (name : String)
deriving DecidableEq, Repr

/-- Re-anchor a right-hand side for evaluation one query boundary deeper: a
literal is unchanged, a current-query column reference becomes an outer-query
reference reaching out one level, and an existing outer-query reference must
reach out one further level. -/
def reanchor : FilterRHS → FilterRHS
  | .value v          => .value v
  | .colRef name      => .outerRef 1 name
  | .outerRef lvl name => .outerRef (lvl + 1) name
-- pure-end

-- post-conditions-start
/-- Relocating the filter condition `(lhs, rhs)` into the nested subquery leaves
the left-hand side unchanged and re-anchors the right-hand side. -/
def problem_spec_relocateFilterIntoSubquery
    (lhs : String) (rhs : FilterRHS) (result : String × FilterRHS) : Prop :=
  result.1 = lhs ∧ result.2 = reanchor rhs
-- post-conditions-end

-- impl-start
def implementation_relocateFilterIntoSubquery
    (lhs : String) (rhs : FilterRHS) : String × FilterRHS := Id.run do
  let mut newRhs : FilterRHS := rhs
  match rhs with
  | .outerRef lvl name => newRhs := .outerRef (lvl + 1) name
  | .colRef name       => newRhs := .outerRef 1 name
  | .value _           => pure ()
  return (lhs, newRhs)
-- impl-end

-- proof-start
theorem correct_relocateFilterIntoSubquery :
    ∀ (lhs : String) (rhs : FilterRHS),
      problem_spec_relocateFilterIntoSubquery lhs rhs
        (implementation_relocateFilterIntoSubquery lhs rhs) := by
  intro lhs rhs
  cases rhs <;>
    simp [problem_spec_relocateFilterIntoSubquery,
          implementation_relocateFilterIntoSubquery, reanchor]
-- proof-end
