import Mathlib
-- imports-end

/-!
Evaluating a power whose base is a tensor product.

A tensor product is a non-commutative product of two or more factors. Raising a
tensor product to a power should be evaluated by distributing the exponent across
each factor, producing a tensor product whose factors are the original factors
each raised to that power:

  (a ⊗ b ⊗ … ⊗ z) ^ n   evaluates to   (a^n) ⊗ (b^n) ⊗ … ⊗ (z^n).

Any other expression — a power whose base is not a tensor product, a bare tensor
product, or an atom — carries no such simplification and is returned unchanged.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The power-of-a-
-- tensor-product evaluation is modeled structurally over the expression carrier:
-- forming a factor's own power and assembling the factors into a tensor product
-- are concrete operations on the carrier (type-only refinement, see
-- refinement.md / mapping.md), so no `opaque`/`axiom` callee contract is needed.
-- axioms-end

-- pure-start
/-- The fragment of a symbolic expression this specification observes.

* `atom n`     — an opaque leaf (any factor the evaluation does not destructure);
* `tp args`    — a tensor product of the factor expressions `args`;
* `pow b e`    — the expression `b` raised to the power `e`. -/
inductive QExpr where
  | atom (n : Nat)
  | tp   (args : List QExpr)
  | pow  (base exp : QExpr)
deriving Repr

/-- Reference evaluation of a power-of-a-tensor-product.

A power whose base is a tensor product distributes the exponent across each
factor: the result is the tensor product of each original factor raised to that
exponent. Every other expression is returned unchanged. -/
def specTensorPow : QExpr → QExpr
  | .pow (.tp args) exp => .tp (args.map (fun b => QExpr.pow b exp))
  | e                   => e
-- pure-end

-- post-conditions-start
/-- The evaluated expression is exactly the reference evaluation: when the input
is a power whose base is a tensor product, the exponent is distributed across
every factor (a tensor product of each factor raised to that exponent);
otherwise the input is returned unchanged. -/
def problem_spec_tensorPow (e : QExpr) (result : QExpr) : Prop :=
  result = specTensorPow e
-- post-conditions-end

-- impl-start
def implementation_tensorPow (e : QExpr) : QExpr := Id.run do
  match e with
  | .pow base exp =>
      match base with
      -- PRE-PATCH BUG: a power whose base is a tensor product is left undistributed
      -- (the exponent is NOT pushed onto the factors), so the power simplifies to
      -- itself instead of to a tensor product of powers.
      | .tp _ => return e
      | _     => return e
  | _ => return e
-- impl-end

-- proof-start
theorem correct_tensorPow :
    ∀ e : QExpr, problem_spec_tensorPow e (implementation_tensorPow e) := by
  -- carries the gold proof intent; UNCLOSABLE against the buggy impl (G-DIFF)
  intro e
  unfold problem_spec_tensorPow implementation_tensorPow specTensorPow
  rfl
-- proof-end
