import Mathlib
-- imports-end

/-!
Multiplication in an operator algebra and its absorption by the identity element.

The algebra has a distinguished *identity element* `I` that acts as a two-sided
multiplicative identity: for any operator-like factor `x`, both `I * x` and
`x * I` are supposed to collapse to `x` rather than being left as an unevaluated
product. Besides plain operators and the identity element, the algebra contains
the *conjugate* of an operator (its Hermitian conjugate) and ordinary scalar/other
expressions.

Two products are modeled, each deciding its result purely from the KIND of the
right-hand factor:

* **A conjugated operator times another factor.** When the right factor is the
  identity element, the product collapses to the conjugated operator itself (the
  identity is absorbed). For every other right factor the product is left as the
  unevaluated product of the two factors.

* **The identity element times another factor.** When the right factor is any
  operator-like thing — a plain operator, the identity element itself, or a
  conjugated operator — the product collapses to that right factor. Only when the
  right factor is a non-operator (a scalar or other expression) is the product
  left unevaluated.

The operator-like classification used by the second product is broader than that
used by the first: the identity element and plain operators are operators, and a
conjugated operator is also operator-like for the purpose of identity absorption,
whereas only the bare identity element triggers absorption on the left of the
first product.
-/

-- axioms-start
-- No unchanged outside callee is consumed. The dispatch — classifying the
-- right-hand factor and choosing between returning a factor unchanged and forming
-- the unevaluated product — IS the modeled behavior and is spelled out
-- structurally over the finite operand/result carriers below. The unevaluated
-- product is an opaque result shape (`Result.product`); its internal construction
-- is irrelevant to the pinned behavior, so no `opaque`/`axiom` callee contract is
-- required.
-- axioms-end

-- pure-start
/-- The kind of a right-hand factor, as far as the products care:

* `identity`  — the distinguished identity element;
* `operator`  — a plain operator (not the identity element);
* `conjugate` — the conjugate of an operator;
* `other`     — any other expression that is neither an operator nor a conjugate
                (a scalar/number/generic product). -/
inductive Operand where
  | identity
  | operator
  | conjugate
  | other
deriving DecidableEq, Repr

/-- The shape of a product result:

* `lhs`     — the left factor returned unchanged;
* `rhs`     — the right factor returned unchanged;
* `product` — the unevaluated product of the two factors. -/
inductive Result where
  | lhs
  | rhs
  | product
deriving DecidableEq, Repr

/-- Whether a factor is the identity element. -/
def isIdentityKind : Operand → Bool
  | .identity => true
  | _ => false

/-- Whether a factor is an operator (the identity element is itself an operator,
plain operators are operators; a conjugate or any other expression is not). -/
def isOperatorKind : Operand → Bool
  | .identity => true
  | .operator => true
  | .conjugate => false
  | .other => false

/-- Whether a factor is a conjugated operator. -/
def isConjugateKind : Operand → Bool
  | .conjugate => true
  | _ => false
-- pure-end

-- post-conditions-start
/-- A conjugated operator multiplied by a right factor `other`: when `other` is the
identity element the result is the conjugated operator itself (the left factor);
otherwise the result is the unevaluated product. -/
def problem_spec_conjugateProduct (other : Operand) (result : Result) : Prop :=
  if isIdentityKind other then result = Result.lhs
  else result = Result.product
-- post-conditions-end

-- impl-start
def implementation_conjugateProduct (other : Operand) : Result := Id.run do
  if isIdentityKind other then
    return Result.lhs
  return Result.product
-- impl-end

-- proof-start
theorem correct_conjugateProduct :
    ∀ (other : Operand),
      problem_spec_conjugateProduct other (implementation_conjugateProduct other) := by
  sorry   -- LEFT FOR THE PROOF AGENT — construction agent does NOT close this
-- proof-end

-- post-conditions-start
/-- The identity element multiplied by a right factor `other`: when `other` is
operator-like — an operator (including the identity element) or a conjugated
operator — the result is that right factor; otherwise the result is the
unevaluated product. -/
def problem_spec_identityProduct (other : Operand) (result : Result) : Prop :=
  if isOperatorKind other || isConjugateKind other then result = Result.rhs
  else result = Result.product
-- post-conditions-end

-- impl-start
/-- PRE-PATCH (variant 2): the identity element absorbs only plain operators (and
the identity element itself), but a conjugated operator is NOT recognised as
operator-like, so `identity * conjugate` is left as the unevaluated product instead
of collapsing to the conjugated operator — exactly the reported defect. -/
def implementation_identityProduct (other : Operand) : Result := Id.run do
  if isOperatorKind other then
    return Result.rhs
  return Result.product
-- impl-end

-- proof-start
theorem correct_identityProduct :
    ∀ (other : Operand),
      problem_spec_identityProduct other (implementation_identityProduct other) := by
  sorry   -- LEFT FOR THE PROOF AGENT — construction agent does NOT close this
-- proof-end
