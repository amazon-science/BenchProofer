import Mathlib
-- imports-end

/-!
Multiplying a plain expression by a polynomial object.

A polynomial object and a plain (non-polynomial) expression can be multiplied in
either order. Whether the product is carried out depends on whether the plain
expression is CONVERTIBLE into a polynomial over the polynomial operand's
generators:

* convertible (e.g. a generator, a number): the product is ALWAYS carried out —
  a polynomial value is produced — regardless of which side the polynomial is
  on; it is never left as an unevaluated symbolic product.
* not convertible (e.g. it involves a generator non-polynomially): the product
  is expressed as a plain symbolic expression instead — no polynomial value is
  produced, for either operand order.

The outcome is modeled as `evaluated` (a polynomial value is produced) versus
`symbolic` (a plain, non-polynomial expression results). The contract below
pins the outcome for both operand orders, `poly * expr` and `expr * poly`, as a
function of convertibility.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The dispatch
-- decision (which operand performs the product, and hence whether the product is
-- carried out or left symbolic) is modeled DEEPLY over the operands' numeric
-- operator precedences, so no `opaque`/`axiom` callee contract is needed. The
-- polynomial's own multiplication routine (coerce the other factor when
-- convertible, else fall back to a plain symbolic product) is an UNCHANGED
-- callee whose net effect is folded into the `coercible` input and the
-- `MulResult` observable; it is validated against the real repo by G-AX.
-- axioms-end

-- pure-start
/-- Which factor of the product is the polynomial. `polyLeft` is `poly * expr`;
`polyRight` is `expr * poly`. -/
inductive Side where
  | polyLeft
  | polyRight
deriving DecidableEq, Repr

/-- The observable outcome of the product: `evaluated` means a polynomial value
is produced; `symbolic` means a plain, non-polynomial expression results. -/
inductive MulResult where
  | evaluated
  | symbolic
deriving DecidableEq, Repr
-- pure-end

-- post-conditions-start
/-- A product mixing a plain expression and a polynomial is always carried out
when the expression is convertible into a polynomial over the polynomial's
generators (`coercible = true`): the outcome is `evaluated` for either operand
order. When the expression is not convertible (`coercible = false`), the
product is expressed as a plain symbolic expression: the outcome is `symbolic`
for either operand order. -/
def problem_spec_polyMul (side : Side) (coercible : Bool) (result : MulResult) : Prop :=
  result = (if coercible then MulResult.evaluated else MulResult.symbolic)
-- post-conditions-end

-- impl-start
def implementation_polyMul (side : Side) (coercible : Bool) : MulResult := Id.run do
  -- Operator precedences advertised by the two operand kinds.
  let exprPriority : Rat := 10            -- a plain expression
  let polyPriority : Rat := 10.001        -- a polynomial object
  match side with
  | Side.polyLeft =>
    -- The polynomial's own multiplication routine runs directly: it coerces the
    -- expression into a polynomial when convertible and multiplies; otherwise
    -- it falls back to the plain symbolic product of expressions.
    if coercible then
      return MulResult.evaluated
    else
      return MulResult.symbolic
  | Side.polyRight =>
    -- The precedence dispatch hands the product to the operand advertising the
    -- strictly greater precedence; only then does the polynomial's reflected
    -- multiplication run (coerce when convertible, else fall back symbolic).
    if polyPriority > exprPriority then
      if coercible then
        return MulResult.evaluated
      else
        return MulResult.symbolic
    else
      -- No delegation: the unevaluated symbolic product is returned.
      return MulResult.symbolic
-- impl-end

-- proof-start
theorem correct_polyMul :
    ∀ (side : Side) (coercible : Bool),
      problem_spec_polyMul side coercible (implementation_polyMul side coercible) := by
  intro side coercible
  unfold problem_spec_polyMul implementation_polyMul
  cases side
  · cases coercible <;> rfl
  · simp only [Id.run]
    rw [if_pos (by norm_num : (10.001 : Rat) > 10)]
    cases coercible <;> rfl
-- proof-end
