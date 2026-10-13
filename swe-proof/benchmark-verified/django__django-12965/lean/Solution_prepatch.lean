import Mathlib
-- imports-end

/-!
Deciding, while compiling a row-deletion, whether the deletion targets exactly
ONE table — the condition under which the deletion can be issued as a single
direct statement rather than as a statement guarded by a self-referential
membership subquery.

A deletion carries a collection of recorded table references; each reference has
a non-negative reference count, and a reference is "active" when its count is
positive. The decision is "exactly one active table reference".

Before counting, the deletion's own PRIMARY table is guaranteed to be present
among the recorded references:

  * if no reference has been recorded yet, the primary table is added as a brand
    new reference with reference count one;
  * otherwise the first-recorded reference (the primary one) has its reference
    count increased by one.

The decision is then: after this guarantee, is the number of active references
exactly one?
-/

-- axioms-start
-- No unchanged outside callee is consumed as an `axiom`. The step that guarantees
-- the primary table is present among the recorded references (and adjusts the
-- relevant reference count) is modeled DEEPLY below as the pure helper
-- `includePrimary`; it is validated == the real repo callee by the conformance
-- gate (an A-reference, not a consumed axiom). Hence no `opaque`/`axiom` callee
-- contract is needed.
-- axioms-end

-- pure-start
/-- Number of active references: those whose reference count is positive. -/
def activeCount (refs : List Nat) : Nat :=
  (refs.filter (fun c => c > 0)).length

/-- Guarantee the primary table is present among the recorded references and
adjust its reference count, exactly as the unchanged primary-table step does:

  * with no references recorded yet (`[]`), the primary table is added as a new
    reference with count one;
  * otherwise the first-recorded (primary) reference's count is increased by one.

This is a deep model of the unchanged primary-table step (validated == the real
callee by the conformance gate), NOT an axiom. -/
def includePrimary (refs : List Nat) : List Nat :=
  match refs with
  | []          => [1]
  | c :: rest   => (c + 1) :: rest
-- pure-end

-- post-conditions-start
/-- The decision is fully pinned to the input reference counts: it is `true`
exactly when, AFTER the primary table is guaranteed present (`includePrimary`),
the number of active references (positive reference count) is exactly one.

No output component is left free: the result is a single boolean and it is pinned
to the active-reference count of `includePrimary refs`. -/
def problem_spec_isSingleTableDelete (refs : List Nat) (result : Bool) : Prop :=
  result = (activeCount (includePrimary refs) == 1)
-- post-conditions-end

-- impl-start
def implementation_isSingleTableDelete (refs : List Nat) : Bool := Id.run do
  -- PRE-PATCH (buggy): counts the active references directly, WITHOUT first
  -- guaranteeing the primary table is among the recorded references. For a
  -- deletion that has recorded no references yet, the count is zero (not one),
  -- so the predicate is false and the caller takes the subquery branch.
  let mut active := 0
  for c in refs do
    if c > 0 then
      active := active + 1
  return active == 1
-- impl-end

-- proof-start
theorem activeCount_cons (a : Nat) (as : List Nat) :
    activeCount (a :: as) = (if a > 0 then 1 else 0) + activeCount as := by
  unfold activeCount; rw [List.filter_cons]; by_cases h : a > 0 <;> simp [h] <;> omega

theorem count_helper (xs : List Nat) (init : Nat) :
    (Id.run (forIn xs init (fun c r =>
        (if c > 0 then ForInStep.yield (r + 1) else ForInStep.yield r : Id (ForInStep Nat)))))
    = init + activeCount xs := by
  induction xs generalizing init with
  | nil => simp [activeCount]
  | cons a as ih =>
    rw [List.forIn_cons]
    simp only [Id.run, bind] at ih ⊢
    rw [activeCount_cons]
    by_cases h : a > 0
    · simp only [h, if_pos, ih]; omega
    · simp only [h, if_false, ih]; omega

theorem correct_isSingleTableDelete :
    ∀ (refs : List Nat),
      problem_spec_isSingleTableDelete refs
        (implementation_isSingleTableDelete refs) := by
  intro refs
  unfold problem_spec_isSingleTableDelete implementation_isSingleTableDelete
  have h2 : (Id.run (forIn (includePrimary refs) 0 fun c r =>
        (have active := r;
         if c > 0 then
           (have active := active + 1; (do pure PUnit.unit; pure (ForInStep.yield active)))
         else (do pure PUnit.unit; pure (ForInStep.yield active)) : Id (ForInStep Nat)))
      : Nat)
      = Id.run (forIn (includePrimary refs) 0 fun c r =>
        (if c > 0 then ForInStep.yield (r+1) else ForInStep.yield r : Id (ForInStep Nat))) := rfl
  show (Id.run _ == 1) = (activeCount (includePrimary refs) == 1)
  rw [h2, count_helper]
  simp
-- proof-end
