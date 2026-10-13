import Mathlib
-- imports-end

/-!
Restricting a subquery used on the right-hand side of a membership ("in")
lookup to a single comparison column.

When a membership lookup compares a column against a subquery, and the subquery
has NOT been given an explicit column selection, and the comparison's target
column is not itself the primary key, the subquery must be narrowed to the
single target column so the comparison is column-for-column. Otherwise the
subquery's existing selection is kept unchanged.
-/

-- axioms-start
-- No unchanged callee is consumed as an axiom: the single-column narrowing of
-- the subquery yields the one target column directly (modeled as a literal
-- one-element selection), so there is nothing to axiomatize.
-- axioms-end

-- pure-start
/-- The state of the subquery appearing on the right-hand side of the lookup,
restricted to the components that decide whether it must be narrowed.

* `selectCols`             — the columns the subquery currently selects.
* `hasAnnotationSelection` — whether an annotation-selection mask is present.
* `hasExtraSelection`      — whether an extra-selection mask is present.
* `explicitValuesApplied`  — whether an explicit column selection has been
  applied to the subquery (i.e. its selected columns were chosen on purpose). -/
structure SubqueryState where
  selectCols : List String
  hasAnnotationSelection : Bool
  hasExtraSelection : Bool
  explicitValuesApplied : Bool
deriving DecidableEq, Repr

/-- Narrow a subquery so it selects exactly the given columns. -/
def restrictTo (q : SubqueryState) (fields : List String) : SubqueryState :=
  { q with selectCols := fields,
           hasAnnotationSelection := false,
           hasExtraSelection := false,
           explicitValuesApplied := true }
-- pure-end

-- post-conditions-start
/-- When the subquery has no explicit column selection and the target column is
not the primary key, the result selects exactly the single target column, has
its annotation- and extra-selection cleared, and is marked as having an explicit
selection. Otherwise the subquery is left entirely unchanged. -/
def problem_spec_prepInLookup
    (rhs : SubqueryState) (lhsTargetPrimaryKey : Bool) (targetField : String)
    (result : SubqueryState) : Prop :=
  if (!rhs.explicitValuesApplied && !lhsTargetPrimaryKey) then
    result.selectCols = [targetField]
      ∧ result.hasAnnotationSelection = false
      ∧ result.hasExtraSelection = false
      ∧ result.explicitValuesApplied = true
  else
    result = rhs
-- post-conditions-end

-- impl-start
def implementation_prepInLookup
    (rhs : SubqueryState) (lhsTargetPrimaryKey : Bool)
    (targetField : String) : SubqueryState := Id.run do
  if !rhs.explicitValuesApplied && !lhsTargetPrimaryKey then
    return restrictTo rhs [targetField]
  return rhs
-- impl-end

-- proof-start
theorem correct_prepInLookup :
    ∀ (rhs : SubqueryState) (lhsTargetPrimaryKey : Bool) (targetField : String),
      problem_spec_prepInLookup rhs lhsTargetPrimaryKey targetField
        (implementation_prepInLookup rhs lhsTargetPrimaryKey targetField) := by
  intro rhs lhsTargetPrimaryKey targetField
  unfold problem_spec_prepInLookup implementation_prepInLookup restrictTo
  by_cases h : (!rhs.explicitValuesApplied && !lhsTargetPrimaryKey) = true
  · simp only [Id.run, h, if_true]
    exact ⟨rfl, rfl, rfl, rfl⟩
  · simp only [Bool.not_eq_true] at h
    simp only [Id.run, h, Bool.false_eq_true, if_false, bind, pure]
-- proof-end
