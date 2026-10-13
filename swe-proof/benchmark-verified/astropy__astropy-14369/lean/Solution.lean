import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee needs an `opaque` signature here. The only operation the
-- modeled routine performs is combining unit terms under multiplication and the
-- quotient operator. Those terms live in an algebra that is a commutative group
-- under multiplication (each term is invertible; multiplication is associative
-- and commutative; the quotient `a / b` is `a * b⁻¹`). We model that algebra
-- DEEPLY as an arbitrary `CommGroup`, so the term-combining operators are the
-- group's own `*`, `⁻¹`, `/`. That `CommGroup` structure is validated as an
-- A-reference against the real unit algebra by G-AX (associativity/commutativity
-- of `*`, the `a / b = a * b⁻¹` law, equality by combined exponents). No custom
-- `axiom` is consumed; the proof uses Mathlib's `CommGroup` laws. The proof
-- agent may add `_prop` axioms only if genuinely stuck.
-- axioms-end

-- pure-start
-- (No extra functional helpers: the spec is a direct relation built from the
-- group's product over the trailing terms.)
-- pure-end

-- post-conditions-start
/-- Combining a sequence of unit terms under the quotient operator.

The terms form a left-associated chain: starting from the leading term `head`,
each subsequent term in `rest` (in order) divides the running result. Read as a
single closed form, the result is therefore the leading term divided by the
product of all the following terms:

  `head / (rest₀ * rest₁ * … * restₙ)`.

Frame discipline: the result is pinned entirely to the inputs — it is fully
determined by `head` and the ordered list `rest`, with no other freedom. -/
def problem_spec_divChain {G : Type*} [CommGroup G]
    (head : G) (rest : List G) (result : G) : Prop :=
  result = head / rest.prod
-- post-conditions-end

-- impl-start
def implementation_divChain {G : Type*} [CommGroup G]
    (head : G) (rest : List G) : G := Id.run do
  let mut acc := head
  for u in rest do
    acc := acc / u
  return acc
-- impl-end

-- proof-start
theorem correct_divChain {G : Type*} [CommGroup G] :
    ∀ (head : G) (rest : List G),
      problem_spec_divChain head rest (implementation_divChain head rest) := by
  have helper : ∀ (rest : List G) (acc : G),
      Id.run (forIn rest acc (fun u r => (pure (.yield (r / u)) : Id (ForInStep G)))) = acc / rest.prod := by
    intro rest
    induction rest with
    | nil => intro acc; simp [Id.run, pure]
    | cons a as ih =>
      intro acc
      rw [List.forIn_cons]
      simp only [Id.run, bind] at ih ⊢
      rw [ih]
      simp [div_div]
  intro head rest
  unfold problem_spec_divChain implementation_divChain
  exact helper rest head
-- proof-end
