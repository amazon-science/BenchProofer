import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee needs an opaque signature here. The decoration count is
-- modeled DEEPLY over an abstraction of each decoration (below): whether it binds
-- a named attribute, whether its replacement is one of the recognised sentinel
-- defaults, and whether comparing that replacement for equality yields an
-- ordinary boolean. No outside callee property is consumed; the proof agent may
-- add `_prop` axioms only if genuinely stuck.
-- axioms-end

-- pure-start
/-- Abstraction of a single mock-patch decoration attached to a test function.

* `attributeName` — `true` when the decoration binds a named attribute (so it
  does NOT consume one of the function's positional arguments).
* `isSentinel` — `true` when the decoration's replacement value is one of the
  recognised sentinel "default" objects (the marker meaning "auto-create a mock
  for this argument").
* `eqWellDefined` — `true` when comparing this replacement value for equality
  against another object yields an ordinary boolean. It is `false` for values
  (such as numeric arrays) whose equality comparison produces a non-boolean and
  therefore has an ambiguous truth value. -/
structure Patching where
  attributeName : Bool
  isSentinel : Bool
  eqWellDefined : Bool
deriving DecidableEq, Repr

/-- A decoration consumes one mandatory argument exactly when it does not bind a
named attribute and its replacement is one of the recognised sentinel defaults. -/
def isCounted (p : Patching) : Bool := !p.attributeName && p.isSentinel
-- pure-end

-- post-conditions-start
/-- The number of mandatory arguments consumed by mock-patch decorations is
returned as `some n`, where `n` is exactly the count of decorations that consume
an argument (do not bind a named attribute and replace with a sentinel default).
The count is always produced (`some _`): determining it must never depend on the
ambiguous truth value of an equality comparison, so a decoration whose
replacement compares with an ill-defined truth value is still classified totally
by the structural criterion above. -/
def problem_spec_num_mock_patch_args
    (patchings : List Patching) (result : Option Nat) : Prop :=
  result = some ((patchings.filter isCounted).length)
-- post-conditions-end

-- impl-start
def implementation_num_mock_patch_args (patchings : List Patching) : Option Nat := Id.run do
  if patchings.isEmpty then
    return some 0
  let mut count : Nat := 0
  for p in patchings do
    if isCounted p then
      count := count + 1
  return some count
-- impl-end

-- proof-start
/-- Helper (Route B): the conditional `forIn` loop, generalized over the
accumulator, counts exactly the decorations satisfying `isCounted`. -/
theorem forIn_count_eq (xs : List Patching) (init : Nat) :
    Id.run (forIn xs init (fun p r =>
      if isCounted p = true then pure (ForInStep.yield (r + 1)) else pure (ForInStep.yield r)))
      = init + (xs.filter isCounted).length := by
  induction xs generalizing init with
  | nil => rfl
  | cons a as ih =>
    rw [List.forIn_cons]
    simp only [Id.run, bind, pure] at ih ⊢
    by_cases h : isCounted a = true
    · simp only [h, if_true, ih, List.filter_cons, List.length_cons]; omega
    · simp only [Bool.not_eq_true] at h
      simp only [h, ih, List.filter_cons, Bool.false_eq_true, if_false]

theorem correct_num_mock_patch_args : ∀ patchings : List Patching,
    problem_spec_num_mock_patch_args patchings
      (implementation_num_mock_patch_args patchings) := by
  intro patchings
  unfold problem_spec_num_mock_patch_args implementation_num_mock_patch_args
  by_cases he : patchings.isEmpty = true
  · simp only [Id.run, he, if_true]
    rw [List.isEmpty_iff] at he
    subst he
    rfl
  · simp only [Id.run]
    rw [if_neg he]
    -- bridge the desugared loop body to the helper's clean body (definitionally equal)
    have h2 : (do
        pure PUnit.unit
        let r ← forIn patchings 0 (fun p r =>
          if isCounted p = true then do pure PUnit.unit; pure (ForInStep.yield (r + 1))
          else do pure PUnit.unit; pure (ForInStep.yield r))
        pure (some r) : Id (Option Nat))
      = some (Id.run (forIn patchings 0 (fun p r =>
          if isCounted p = true then pure (ForInStep.yield (r + 1)) else pure (ForInStep.yield r)))) := rfl
    rw [h2, forIn_count_eq, Nat.zero_add]
-- proof-end
