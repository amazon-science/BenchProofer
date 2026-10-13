import Mathlib
-- imports-end

/-!
Reducing the hyperbolic cotangent of a sum one of whose summands is a nonzero
multiple of the imaginary half-period.

When the argument of the hyperbolic cotangent is an additive expression, it is
split into a remaining part `x` and a part `m` that is a multiple of the
imaginary half-period. In the case that this multiple part is nonzero, the value
of the whole is determined by the hyperbolic cotangent of `m`:

  * if the hyperbolic cotangent of `m` is the distinguished point at (complex)
    infinity, the result is the hyperbolic cotangent of `x`;
  * otherwise the result is the hyperbolic tangent of `x`.

The reduction always produces a value for this case (it never fails to
complete). We model the outcome as `Except Unit Expr`: `Except.ok v` is a
completed reduction yielding the value `v`; `Except.error ()` denotes a
computation that does not complete and yields no value. A correct reduction of
this case is always `Except.ok …`.

The splitting of the argument and the test that the multiple part is nonzero are
unchanged surrounding context; the behavior specified here is the reduction
reached once `x` and the nonzero multiple `m` are in hand. The two hyperbolic
evaluators and the point at infinity are unchanged outside operations, left
abstract — the specification constrains none of their internals, only how the
reduction selects among their results.
-/

-- axioms-start
/-- A symbolic expression, identified by its canonical representation. The
behavior under specification observes expressions only through equality and as
the arguments threaded to the two hyperbolic evaluators below, so a
representation-tagged carrier is a faithful model. -/
structure Expr where
  repr : String
deriving DecidableEq, Inhabited, Repr

/-- The distinguished point at (complex) infinity — the sentinel expression the
reduction tests its dispatch value against. An unchanged outside value, left
abstract; observed only through equality. -/
opaque complexInfinity : Expr

/-- The (unchanged) hyperbolic cotangent evaluator applied to a subterm. Its
internal algorithm lies outside the behavior under specification and is left
abstract: the specification constrains none of its inner workings, only how its
result is used. -/
opaque cothFn : Expr → Expr

/-- The (unchanged) hyperbolic tangent evaluator applied to a subterm. Left
abstract for the same reason as `cothFn`. -/
opaque tanhFn : Expr → Expr
-- axioms-end

-- pure-start
-- No additional functional helpers are needed: the behavior is the control flow
-- selecting between the two unchanged evaluators above.
-- pure-end

-- post-conditions-start
/-- The outcome of reducing the hyperbolic cotangent of a sum, given the
remaining part `x` and the nonzero multiple part `m`.

The reduction completes with a value (`Except.ok …`); which value is decided by
the hyperbolic cotangent of `m`:

  * if `cothFn m` is the point at infinity, the result is `cothFn x`;
  * otherwise the result is `tanhFn x`.

The result is fully pinned to the inputs through the two evaluators; nothing is
left free, and the error outcome never occurs. -/
def problem_spec_cothReduce (x m : Expr) (result : Except Unit Expr) : Prop :=
  result = Except.ok (if cothFn m = complexInfinity then cothFn x else tanhFn x)
-- post-conditions-end

-- impl-start
def implementation_cothReduce (x m : Expr) : Except Unit Expr := Id.run do
  let cothm := cothFn m
  if cothm = complexInfinity then
    return Except.ok (cothFn x)
  else
    return Except.ok (tanhFn x)
-- impl-end

-- proof-start
theorem correct_cothReduce :
    ∀ (x m : Expr),
      problem_spec_cothReduce x m (implementation_cothReduce x m) := by
  intro x m
  unfold problem_spec_cothReduce implementation_cothReduce
  by_cases h : cothFn m = complexInfinity
  · simp only [Id.run, h, if_true]; rfl
  · simp only [Id.run, h, if_false]; rfl
-- proof-end
