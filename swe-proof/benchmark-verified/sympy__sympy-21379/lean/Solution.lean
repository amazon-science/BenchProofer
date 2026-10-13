import Mathlib
-- imports-end

/-!
Tolerating a failure of common-factor extraction during expression
simplification.

A symbolic-simplification step works on two expressions `p` and `q`. It first
asks a helper routine for a common factor shared by the two expressions:

  * If the routine succeeds with a factor `g`, that factor is recorded. When the
    factor is nontrivial (different from the unit `1`), both expressions are
    rewritten by dividing out the factor; when the factor is the unit, the two
    expressions are left unchanged.
  * For some symbolic expressions the factor-extraction routine cannot produce a
    result and signals a failure.

The desired behavior is that such a failure is TOLERATED rather than propagated:
when extraction fails the step falls back to treating the common factor as the
unit `1` and leaves both expressions unchanged, and the overall step always
produces a result instead of aborting.

We model the outcome as `Except Unit (Expr × Expr × Expr)`. `Except.ok (G, p, q)`
carries the recorded factor `G` together with the (possibly rewritten)
expressions forward; `Except.error ()` denotes the failure escaping the step. A
correct step never yields `Except.error ()`.
-/

-- axioms-start
/-- A symbolic expression, identified by its canonical representation. The
behavior under specification observes expressions only through equality
(comparing a factor against the unit) and through the unchanged helper routines
below, so a representation-tagged carrier is a faithful model. -/
structure Expr where
  repr : String
deriving DecidableEq, Inhabited, Repr

/-- The unit expression `1`. -/
opaque one : Expr

/-- The unchanged helper routine that attempts to extract a common factor of two
expressions. `Except.ok g` is a successfully extracted factor `g`; `Except.error
()` is the routine signalling that it cannot handle the given expressions. Its
internal algorithm is outside this behavior and is left abstract: the
specification constrains none of its inner workings, only its result shape. -/
opaque extractFactor : Expr → Expr → Except Unit Expr

/-- The unchanged helper routine that rewrites an expression by dividing out a
factor (the per-expression rewrite applied when a nontrivial common factor was
found). Left abstract — it is an outside callee, not part of the behavior under
specification. -/
opaque reduceByFactor : Expr → Expr → Expr
-- axioms-end

-- pure-start
-- No additional functional helpers are needed: the behavior is the control flow
-- around the two unchanged helper routines above.
-- pure-end

-- post-conditions-start
/-- The outcome of the common-factor simplification step on `(p, q)`.

If factor extraction succeeds with `g`: the result is `Except.ok (g, p', q')`
where, when `g` is the unit, both expressions are unchanged, and otherwise each
is rewritten by dividing out `g`.

If factor extraction fails: the failure is tolerated — the result is
`Except.ok (1, p, q)` (the factor recorded as the unit, both expressions
unchanged). The step never yields `Except.error ()`. -/
def problem_spec_factorReduce (p q : Expr)
    (result : Except Unit (Expr × Expr × Expr)) : Prop :=
  match extractFactor p q with
  | Except.ok g =>
      result = Except.ok
        (g,
         (if g = one then p else reduceByFactor p g),
         (if g = one then q else reduceByFactor q g))
  | Except.error () =>
      result = Except.ok (one, p, q)
-- post-conditions-end

-- impl-start
def implementation_factorReduce (p q : Expr) :
    Except Unit (Expr × Expr × Expr) := Id.run do
  let mut G : Expr := one
  let mut p' := p
  let mut q' := q
  match extractFactor p q with
  | Except.ok g =>
      G := g
      if g ≠ one then
        p' := reduceByFactor p g
        q' := reduceByFactor q g
  | Except.error () =>
      G := one
  return Except.ok (G, p', q')
-- impl-end

-- proof-start
theorem correct_factorReduce :
    ∀ (p q : Expr),
      problem_spec_factorReduce p q (implementation_factorReduce p q) := by
  intro p q
  unfold problem_spec_factorReduce implementation_factorReduce
  cases h : extractFactor p q with
  | ok g =>
      by_cases hg : g = one
      · simp only [Id.run, hg, ne_eq, not_true_eq_false, if_false, if_true]
        rfl
      · simp only [Id.run, hg, ne_eq, if_false]
        rfl
  | error e =>
      cases e
      rfl
-- proof-end
