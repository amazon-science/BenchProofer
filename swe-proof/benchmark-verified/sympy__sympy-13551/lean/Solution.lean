import Mathlib
-- imports-end

/-!
The value of a finite product of a separable additive term over a range of
integer positions, divided by a constant.

The term multiplied across the range has the shape `c + r(k)`, where `c` is a
constant (independent of the position) and `r(k)` is the position-dependent
remainder, evaluated at every position `k` of the range `0, 1, …, n-1`. The whole
product is then divided by a constant `q` — the value that the range-product of
the term's denominator collapses to, which is a plain number.

The value of the construct is the genuine product over the range: multiply the
term `c + r(k)` across every position `k < n`, then divide by `q`. No component of
the result is left free — it is fully determined by `c`, the length `n`, the
remainder function `r`, and the divisor `q`.

The modeled slice is the non-degenerate case: the divisor `q` is nonzero and
every factor `c + r(k)` over the range is nonzero (a zero factor makes the real
construct's evaluation degenerate rather than a plain number, and lies outside
the modeled slice).
-/

-- axioms-start
-- No unchanged outside callee is consumed: the range-product is modelled
-- directly as the product of the per-position term values, so no `opaque`/`axiom`
-- callee contract is needed.
-- axioms-end

-- pure-start
-- (no shared pure helpers needed)
-- pure-end

-- post-conditions-start
/-- The value equals the genuine product of the term `c + r k` taken over every
position `k < n` of the range, divided by the constant `q`. The product of the
additive term is its true product across the range — not any summand-wise
shortcut — so the result is pinned to `c`, the length `n`, the remainder function
`r`, and the divisor `q`. -/
def problem_spec_finiteProduct (c : ℚ) (n : ℕ) (r : ℕ → ℚ) (q : ℚ) (result : ℚ) : Prop :=
  result = ((List.range n).map (fun k => c + r k)).prod / q
-- post-conditions-end

-- impl-start
def implementation_finiteProduct (c : ℚ) (n : ℕ) (r : ℕ → ℚ) (q : ℚ) : ℚ := Id.run do
  let mut acc : ℚ := 1
  for k in [0:n] do
    acc := acc * (c + r k)
  return acc / q
-- impl-end

-- proof-start
theorem correct_finiteProduct :
    ∀ (c : ℚ) (n : ℕ) (r : ℕ → ℚ) (q : ℚ), q ≠ 0 → (∀ k, k < n → c + r k ≠ 0) →
      problem_spec_finiteProduct c n r q (implementation_finiteProduct c n r q) := by
  intro c n r q _ _
  unfold problem_spec_finiteProduct implementation_finiteProduct
  simp [List.range_eq_range', List.prod_eq_foldl, List.foldl_map]
-- proof-end
