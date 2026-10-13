import Mathlib
-- imports-end

/-!
Restricting the set of selectable options for a relational choice field.

A choice field is initialized from a collection of candidate objects. An optional
constraint may be supplied to narrow that collection to the candidates that
satisfy it. When the constraint reaches across a multi-valued relation, a single
candidate can satisfy it through several related rows.

We model each candidate together with the number of related rows that satisfy the
constraint for it (`matchRows`). The narrowing is governed by two gates:

  * `applicable` — whether this field exposes a candidate collection that the
    constraint can be applied to at all; and
  * `constraintActive` — whether a constraint is actually present.

When both gates hold, the candidate collection is narrowed to exactly those
candidates that satisfy the constraint, and each such candidate is offered AT
MOST ONCE — its presence depends only on whether at least one related row
satisfies the constraint, never on how many do. When either gate fails, the
candidate collection is returned unchanged.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification: the narrowing is
-- modeled structurally over the per-candidate match counts the collection already
-- exposes, so no `opaque`/`axiom` callee contract is needed.
-- axioms-end

-- pure-start
/-- A candidate object offered by the choice field, paired with the number of
related rows that satisfy the constraint for it.
* `id` — the candidate's identity;
* `matchRows` — how many related rows satisfy the constraint for this candidate
  (`0` means the candidate does not satisfy the constraint). -/
structure Candidate where
  id : Nat
  matchRows : Nat

/-- A candidate qualifies iff at least one related row satisfies the constraint. -/
def qualifies (c : Candidate) : Bool := c.matchRows != 0
-- pure-end

-- post-conditions-start
/-- When the field is applicable and a constraint is present, the result is the
incoming collection narrowed to the qualifying candidates — each kept exactly as
often as it occurs in the input, i.e. at most once for a collection with distinct
candidates, independent of its match count. Otherwise the collection is unchanged. -/
def problem_spec_applyChoiceLimit
    (applicable constraintActive : Bool) (base : List Candidate)
    (result : List Candidate) : Prop :=
  result =
    (if applicable && constraintActive then base.filter qualifies else base)
-- post-conditions-end

-- impl-start
def implementation_applyChoiceLimit
    (applicable constraintActive : Bool) (base : List Candidate) : List Candidate :=
  Id.run do
    let mut queryset := base
    if applicable then
      if constraintActive then
        queryset := queryset.filter qualifies
    return queryset
-- impl-end

-- proof-start
theorem correct_applyChoiceLimit :
    ∀ (applicable constraintActive : Bool) (base : List Candidate),
      problem_spec_applyChoiceLimit applicable constraintActive base
        (implementation_applyChoiceLimit applicable constraintActive base) := by
  intro applicable constraintActive base
  unfold problem_spec_applyChoiceLimit implementation_applyChoiceLimit
  cases applicable <;> cases constraintActive <;> rfl
-- proof-end
