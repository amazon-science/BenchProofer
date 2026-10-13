# refinement.md — sympy__sympy-13551

Tags: **R** = type-only refinement (state bijection), **A-consumed** = proof uses an
axiom's property, **A-reference** = deep model validated `== real callee` by G-AX,
**I** = identical concrete op. Every op is R, A, or I. R/I legs refuted by G-CONF.

## `implementation_finiteProduct` ↔ patched `_eval_product` Add/`q.is_Number` branch (products.py:285-289)

The carrier models a finite product `∏_{k=0}^{n-1} (c + r(k))` of an additive term
`c + r(k)` (constant `c`, position-dependent remainder `r`), divided by the numeric
denominator range-product `q`.

| Lean op | patch.diff op | tag | note |
|---|---|---|---|
| `c : ℚ`, `n : ℕ`, `r : ℕ → ℚ`, `q : ℚ` carriers | the additive term's constant `c`, the range length `n` (= `n - a + 1` positions), the remainder values `r(k)` over the range, and the evaluated denominator product `q` | R | exact-rational bijection (mapping.md); the symbolic term's product-relevant content is its per-position values over `k = 0 … n-1` |
| `let mut acc := 1; for k in [0:n] do acc := acc * (c + r k)` | `p = exp(Sum(log(p), (k,a,n)))` ≡ `∏_{k=a}^{n} (c + r(k))` | R | `exp(∑ log)` is the genuine finite product; the impl multiplies `c + r(k)` across every position — same value, modelled directly as `(List.range n).map (c + r ·) |>.prod`. This is the line the patch ADDED. The product is modelled DEEPLY (spelled out), not axiomatized. |
| `return acc / q` | `return p / q` | I | the unchanged final division by the evaluated denominator product (the `return p / q` line below the patched branch) |

## Pre-patch (buggy) skeleton — `Solution_prepatch.lean`

| variant | buggy op | gold op | observable bug |
|---|---|---|---|
| prepatch | `return (c ^ n + accRem) / q` where `accRem = ∏_{k<n} r(k)` | `return (∏_{k<n} (c + r k)) / q` | the pre-patch `sum([_eval_product(i) for i in p.as_coeff_Add()])` splits the additive numerator into `(c, r(k))`: `_eval_product(c)` over the range is `c**(n-a+1) = c**n` and `_eval_product(r(k))` is `∏ r(k)`; their SUM assumes `∏(c+r) = c**n + ∏r`. On the F2P witness (`c=2, n=2, r k = 2**(-k), q=1`) the buggy value is `2**2 + (1·1/2) = 9/2`; the correct value is `(2+1)(2+1/2) = 15/2` — exactly the issue's `9/2` vs `15/2`. |

The prepatch's `correct_finiteProduct` is FALSE (`9/2 ≠ 15/2` on the F2P witness),
so it cannot close → G-DIFF satisfied. One independently-fixed behavior ⇒ one prepatch.

## Modeled-slice boundary (2026-08 repair)

The re-gate G-PANEL-2 exhibited a zero-factor witness: with `c=2, n=2, r k = -2**k`
(i.e. `Product(n - 2*2**k, (k,0,n-1)).subs(n,2)`), the factor at `k=0` is `2-2=0`, and
the real post-patch evaluation `exp(Sum(log(p),(k,0,1)))` produces `exp(zoo)` — an
undefined symbolic residue, not the rational `0` the unconditional spec demanded. The
fix keeps the spec relation unchanged (`result = ∏(c + r k) / q`) and narrows the
modeled slice via a `correct_*` binder `∀ k, k < n → c + r k ≠ 0`: the ℚ-valued
observable only exists when every factor is nonzero (`log` of a zero factor makes the
real construct degenerate). The G-CONF families (`c + base**(-k)` with `c ≥ 1`,
`base ≥ 2`) all have strictly positive factors, so the differential burden is
unaffected.

## A-tags

None. No consumed callee axiom, no A-reference: the range-product is modelled deeply
as `(List.range n).map (c + r ·) |>.prod`, so G-AX is a skip stub and G-CONF carries
the full differential burden. `conf_skip` is FALSE (the impl region is all R/I).
