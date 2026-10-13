import Mathlib
-- imports-end

/-!
Computing the solution set of a univariate relation.

A univariate relation (an equation or inequality in a single unknown) can be
turned into the set of values of that unknown which satisfy it. The computation
delegates to a general set-solving routine for univariate relations.

For some relations the set-solving routine cannot produce an explicit solution
set and signals that it is unable to handle the relation. The desired behavior
is that such an inability is TOLERATED rather than escaping the computation:
when the routine cannot produce a set, the computation falls back to the
symbolic conditional set — the set of all real numbers constrained by the
relation itself — and returns it. When the routine succeeds, its set is returned
unchanged. The computation therefore always yields a set and never propagates
the routine's inability outward.

We model the outcome as `Except Unit SetExpr`. `Except.ok s` carries a returned
set `s`; `Except.error ()` denotes the routine's inability escaping the
computation. A correct computation never yields `Except.error ()`.

This is stated abstractly as an input→output relation; the implementation and
correctness proof are supplied separately.
-/

-- axioms-start
/-- A univariate relation, identified by its canonical representation. The
behavior under specification observes it only as the argument threaded to the
two set-producing routines below, so a representation-tagged carrier is a
faithful model. -/
structure Relation where
  repr : String
deriving DecidableEq, Inhabited, Repr

/-- A set value (the kind of object the computation returns), identified by its
canonical representation. Observed only through equality. -/
structure SetExpr where
  repr : String
deriving DecidableEq, Inhabited, Repr

/-- The unchanged general routine that attempts to compute the solution set of a
univariate relation. `Except.ok s` is a successfully computed set `s`;
`Except.error ()` is the routine signalling that it cannot handle the given
relation. Its internal algorithm lies outside this behavior and is left
abstract: the specification constrains none of its inner workings, only its
result shape. -/
opaque solveSet : Relation → Except Unit SetExpr

/-- The unchanged constructor of the symbolic conditional set for a relation:
the set of all real numbers constrained by the relation. Newly invoked on the
tolerated branch; left abstract — it is an outside callee, not part of the
behavior under specification. -/
opaque fallbackSet : Relation → SetExpr
-- axioms-end

-- pure-start
-- No additional functional helpers are needed: the behavior is the control flow
-- around the two unchanged routines above.
-- pure-end

-- post-conditions-start
/-- The outcome of computing the solution set of the univariate relation `rel`.

If the set-solving routine succeeds with `s`: the result is `Except.ok s`, the
routine's set returned unchanged.

If the routine cannot produce a set: the inability is tolerated — the result is
`Except.ok (fallbackSet rel)` (the symbolic conditional set for `rel`). The
computation never yields `Except.error ()`. -/
def problem_spec_asSet (rel : Relation) (result : Except Unit SetExpr) : Prop :=
  match solveSet rel with
  | Except.ok s => result = Except.ok s
  | Except.error () => result = Except.ok (fallbackSet rel)
-- post-conditions-end

-- impl-start
def implementation_asSet (rel : Relation) : Except Unit SetExpr := Id.run do
  -- prepatch: the set-solving routine's inability is NOT tolerated; it escapes
  -- the computation directly instead of falling back to the conditional set.
  match solveSet rel with
  | Except.ok s =>
      return Except.ok s
  | Except.error () =>
      return Except.error ()
-- impl-end

-- proof-start
-- Gold proof body carried over from Solution.lean (SPEC_GUIDE §1.1). Against this
-- implementation it cannot close: when the set-solving routine cannot produce a
-- set (`solveSet rel = Except.error ()`), the specification requires the
-- inability be tolerated (`result = Except.ok (fallbackSet rel)`), but this
-- prepatch impl lets it escape and returns `Except.error ()` — the
-- discriminating clause.
theorem correct_asSet :
    ∀ (rel : Relation),
      problem_spec_asSet rel (implementation_asSet rel) := by
  sorry
-- proof-end
