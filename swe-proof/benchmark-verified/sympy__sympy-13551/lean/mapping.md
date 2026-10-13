# mapping.md — sympy__sympy-13551

## Symbol binding (file:line @ base_commit `9476425b9e`)

| Lean triple | Python symbol | file:line @ base_commit |
|---|---|---|
| `implementation_finiteProduct` / `problem_spec_finiteProduct` / `correct_finiteProduct` | the `term.is_Add` branch of `Product._eval_product(self, term, limits)` — specifically the `q.is_Number` sub-branch that evaluates the numerator's range-product | `sympy/concrete/products.py:278-289` (patched lines 285-286) |

## What the patched branch does

`_eval_product` recursively evaluates a symbolic finite product `∏_{k=a}^{n} term`.
For an additive `term` it splits `term = p/q` via `as_numer_denom()`, evaluates the
denominator product `q` recursively, and — when that denominator product is a plain
number — must evaluate the numerator product `∏_{k=a}^{n} p`. The numerator `p` is an
`Add` (a sum `c + r(k)` of a constant `c` and an index-dependent remainder `r(k)`).

- **Pre-patch (buggy):**
  `p = sum([self._eval_product(i, (k,a,n)) for i in p.as_coeff_Add()])`
  `as_coeff_Add()` splits `p` into `(c, r(k))`; `_eval_product(c)` over the range is
  `c**(n-a+1)` (= `c**len`) and `_eval_product(r(k))` is the genuine product of the
  remainder. Their **sum** is returned — i.e. it assumes
  `∏(c + r(k)) = c**len + ∏ r(k)`, which is false. For the F2P input this yields `9/2`.
- **Post-patch (fixed):**
  `p = exp(Sum(log(p), (k,a,n)))` — `exp(∑ log p) = ∏ p`, the genuine finite product
  of the whole additive term. For the F2P input this yields `15/2`.

The final returned value is `p / q` in both cases (`q` the evaluated denominator).

## F2P test (`test_issue_13546`)

`Product(n + 1/2**k, (k, 0, n-1)).doit().subs(n, 2) == S(15)/2`.
With `n=2`: term `2 + 1/2**k` over `k ∈ {0,1}`. The recursion splits to numerator
`p = 2**k*2 + 1` (an `Add` `c + r(k)` with `c = 1`… in the actual recursion the
constant/remainder split is presented to the modelled construct as `c` plus the list
of remainder values; for the value at `n=2` the genuine product is
`(2 + 1)·(2 + 1/2) = 15/2`, while the buggy sum-of-products gives `9/2`).

## Lean ↔ Python type bijection (used by G-CONF / G-AX)

| Python | Lean |
|---|---|
| an exact rational value (the F2P products are exact rationals) | `ℚ` (`Rat`) |
| the index-independent constant `c` of the additive term | `c : ℚ` |
| the number of positions in the range, `n - a + 1` | `n : ℕ` |
| the remainder value `r(k)` at position `k` (the range mapped to `0 … n-1`) | `r : ℕ → ℚ` |
| the (numeric) value the denominator range-product collapses to | `q : ℚ` |
| the genuine range-product `∏_{k} (c + r(k))` | `((List.range n).map (fun k => c + r k)).prod` |
| division by the evaluated denominator product `p / q` | `… / q` |
| pre-patch `c**(n-a+1) + ∏ r(k)` | `c ^ n + (∏_{k<n} r k)` |

Rationale for `ℚ` (not `Real`): the fix is an exact symbolic identity and the F2P
test asserts an exact rational (`S(15)/2`). Modelling the values as exact `ℚ` keeps
the impl computable and the order/equality decidable, per SPEC_GUIDE §2 (float with an
exact-valued fix → exact `Rat`).

## Preconditions (binders of `correct_finiteProduct`, not spec conjuncts)

- `q ≠ 0` — the divisor (evaluated denominator product) is a nonzero number; division
  by it is the real operation's final step. The branch is only reached when the
  denominator product is a plain (nonzero) `Number`. Per SPEC_GUIDE §1, preconditions
  are binders of `correct_*`, not conjuncts of `problem_spec` (kept a clean
  input→output relation). On `ℚ`, `/` is totalized, so `q ≠ 0` is the genuine
  well-formedness side-condition of the modelled division.
- `∀ k, k < n → c + r k ≠ 0` — every factor of the range-product is nonzero. The
  post-patch code evaluates the numerator product as `exp(Sum(log(p), (k,a,n)))`;
  if any per-position value of `p` is 0, `log(0) = zoo` and the real evaluation
  yields `exp(zoo)` — an undefined/unevaluated symbolic residue, NOT a rational
  number. The ℚ-valued observable therefore only exists on the nonzero-factor
  slice; a zero factor is outside the modeled slice (re-gate G-PANEL-2 witness:
  `Product(n - 2*2**k, (k,0,n-1)).doit().subs(n,2).doit() == exp(zoo)`, whereas
  a spec without this binder would have forced the value 0).

## Callees / axioms

None consumed. The range-product is modelled directly as the product of the per-index
term values (`List.map` then `List.prod`), so there is no `opaque` callee and no
`axiom _prop`. G-AX is a skip stub; G-CONF carries the full differential burden.

## Flag dependencies

None.

## G-CONF fuzz seed

`13551` (pinned in meta.json `verifier_pins.conf_seed`).
