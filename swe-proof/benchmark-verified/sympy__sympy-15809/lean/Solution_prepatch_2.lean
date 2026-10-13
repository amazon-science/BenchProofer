import Mathlib
-- imports-end

/-!
Reduction of a finite collection of comparable extended-real values to its
greatest-lower-bound (`min`) and least-upper-bound (`max`).

Values are modeled as `WithTop (WithBot ℚ)`: a finite rational, the top element
`⊤` (positive infinity), or the bottom element `⊥` (negative infinity). The
collection is processed in call order with mutable accumulation, starting from
the neutral element of the reduction (`⊤` for the minimum, `⊥` for the maximum);
an empty collection therefore reduces to that neutral element. The reduction is
always defined (returns a value, never the failure branch `Except.error`).
-/

-- axioms-start
-- No unchanged callee is consumed as an axiom: the reduction over comparable
-- extended reals is modeled deeply as a fold (see the impl regions). A result
-- is `Except.ok v` for a produced value `v`, or `Except.error ()` for failure.
abbrev EVal := WithTop (WithBot ℚ)
-- axioms-end

-- pure-start
-- (no shared pure helpers needed)
-- pure-end

/-! ## Minimum reduction -/

-- post-conditions-start
/-- The reduction always succeeds with some value `v` which is a lower bound of
every input, equals the neutral element `⊤` exactly when there is no input, and
is otherwise itself one of the inputs (the attained greatest lower bound). -/
def problem_spec_min (args : List EVal) (result : Except Unit EVal) : Prop :=
  ∃ v : EVal, result = Except.ok v ∧
    (args = [] → v = ⊤) ∧
    (∀ x ∈ args, v ≤ x) ∧
    (args ≠ [] → v ∈ args)
-- post-conditions-end

-- impl-start
def implementation_min (args : List EVal) : Except Unit EVal := Id.run do
  let mut acc : EVal := ⊤
  for x in args do
    acc := min acc x
  return Except.ok acc
-- impl-end

-- proof-start
theorem correct_min : ∀ args : List EVal,
    problem_spec_min args (implementation_min args) := by
  sorry
-- proof-end

/-! ## Maximum reduction -/

-- post-conditions-start
/-- The reduction always succeeds with some value `v` which is an upper bound of
every input, equals the neutral element `⊥` exactly when there is no input, and
is otherwise itself one of the inputs (the attained least upper bound). -/
def problem_spec_max (args : List EVal) (result : Except Unit EVal) : Prop :=
  ∃ v : EVal, result = Except.ok v ∧
    (args = [] → v = ⊥) ∧
    (∀ x ∈ args, x ≤ v) ∧
    (args ≠ [] → v ∈ args)
-- post-conditions-end

-- impl-start
def implementation_max (args : List EVal) : Except Unit EVal := Id.run do
  if args = [] then return Except.error ()
  let mut acc : EVal := ⊥
  for x in args do
    acc := max acc x
  return Except.ok acc
-- impl-end

-- proof-start
theorem correct_max : ∀ args : List EVal,
    problem_spec_max args (implementation_max args) := by
  sorry
-- proof-end
