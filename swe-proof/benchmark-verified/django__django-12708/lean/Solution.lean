import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee needs an opaque signature here. The selection of the
-- database constraint to drop is a total filter over the table's introspected
-- constraints (each carrying its name, the columns it covers, and its
-- index/unique flags) followed by an exactly-one count check; it is modeled
-- concretely below (R/I in refinement.md). The proof agent may add `_prop`
-- axioms only if genuinely stuck.
-- axioms-end

-- pure-start
/-- An introspected table constraint, projected onto the components the deletion
selection inspects: its `name`, the ordered list of `columns` it covers, whether
it backs an `index`, whether it backs a `unique` constraint, and whether it is
`excluded` from selection because it is declared via the model's explicit
constraint/index meta options. -/
structure DbConstraint where
  name : String
  columns : List String
  isIndex : Bool
  isUnique : Bool
  excluded : Bool
  deriving Repr, DecidableEq

/-- Whether a constraint is a candidate for deletion when removing the
composed-index entry over the columns `cols`: it covers exactly `cols`, it backs
an ordinary (non-unique) index, it does NOT back a unique constraint, and it is
not excluded by the model's explicit meta options. (Pinning the non-unique
requirement is what keeps a unique constraint over the same columns out of the
candidate set.) -/
def isDropCandidate (cols : List String) (c : DbConstraint) : Bool :=
  (c.columns == cols) && c.isIndex && (!c.isUnique) && (!c.excluded)

/-- The names of all candidate constraints to drop, in table order. -/
def dropCandidateNames (constraints : List DbConstraint) (cols : List String) :
    List String :=
  (constraints.filter (isDropCandidate cols)).map (·.name)
-- pure-end

-- post-conditions-start
/-- Removing the composed index over the columns `cols` selects, among the
table's introspected `constraints`, every constraint that covers exactly `cols`,
backs an ordinary index, is not itself a unique constraint, and is not excluded
by the model's explicit meta options. Exactly one such constraint must exist:
when it does, the result names that single constraint to delete; otherwise the
result reports the number of matching constraints found (the count that makes the
operation refuse to proceed). Both branches are pinned to the input selection, so
no result can omit the non-unique requirement, target an unrelated constraint, or
fabricate a count. -/
def problem_spec_dropComposedIndex
    (constraints : List DbConstraint) (cols : List String)
    (result : Except Nat String) : Prop :=
  let ns := dropCandidateNames constraints cols
  (ns.length = 1 → result = Except.ok ns.head!) ∧
  (ns.length ≠ 1 → result = Except.error ns.length)
-- post-conditions-end

-- impl-start
def implementation_dropComposedIndex
    (constraints : List DbConstraint) (cols : List String) :
    Except Nat String := Id.run do
  let mut names : List String := []
  for c in constraints do
    if isDropCandidate cols c then
      names := names ++ [c.name]
  if names.length != 1 then
    return Except.error names.length
  return Except.ok names.head!
-- impl-end


-- proof-start
theorem correct_dropComposedIndex :
    ∀ (constraints : List DbConstraint) (cols : List String),
      problem_spec_dropComposedIndex constraints cols
        (implementation_dropComposedIndex constraints cols) := by
  intro constraints cols
  simp only [problem_spec_dropComposedIndex, implementation_dropComposedIndex, Id.run]
  have key : ∀ (cs : List DbConstraint) (acc : List String),
      (forIn cs acc fun c r ↦
        if isDropCandidate cols c = true then do
          pure PUnit.unit
          pure (ForInStep.yield (r ++ [c.name]))
        else do
          pure PUnit.unit
          pure (ForInStep.yield r) : Id (List String)) =
      acc ++ (cs.filter (isDropCandidate cols)).map (·.name) := by
    intro cs
    induction cs with
    | nil => intro acc; simp only [List.forIn_nil, List.filter_nil, List.map_nil, List.append_nil]; rfl
    | cons c cs ih =>
      intro acc
      rw [List.forIn_cons, List.filter_cons]
      by_cases h : isDropCandidate cols c = true
      · simp only [h, if_true]
        show (forIn cs (acc ++ [c.name]) _ : Id _) = _
        rw [ih (acc ++ [c.name])]
        simp [List.append_assoc]
      · simp only [h, Bool.false_eq_true, if_false]
        show (forIn cs acc _ : Id _) = _
        rw [ih acc]
  have hrun : (forIn constraints [] fun c r ↦
        if isDropCandidate cols c = true then do
          pure PUnit.unit
          pure (ForInStep.yield (r ++ [c.name]))
        else do
          pure PUnit.unit
          pure (ForInStep.yield r) : Id (List String)) = dropCandidateNames constraints cols := by
    rw [key constraints []]
    simp only [List.nil_append, dropCandidateNames]
  rw [hrun]
  set ns := dropCandidateNames constraints cols with hns
  constructor
  · intro hlen
    have hb : (ns.length != 1) = false := by simp [hlen]
    show (if (ns.length != 1) = true then _ else _) = _
    rw [hb]
    rfl
  · intro hlen
    have hb : (ns.length != 1) = true := by simp [hlen]
    show (if (ns.length != 1) = true then _ else _) = _
    rw [hb]
    rfl

-- proof-end
