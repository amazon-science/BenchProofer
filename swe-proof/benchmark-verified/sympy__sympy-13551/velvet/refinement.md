# refinement.md — sympy__sympy-13551

Operation-by-operation correspondence between `Solution.lean`'s impl region
(the `productOverRange` `do` block and the deep `prodOfSums` model) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A** (axiomatized callee — A-consumed / A-reference), or **I** (identical
concrete op). The R/I legs are mechanically refuted by **G-CONF**
(`conformance_check.py`, §4.1). There are **no A legs** in this bundle.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The changed site — `Product._eval_product`, additive branch

Repo: `sympy/concrete/products.py`, the `elif term.is_Add:` branch
(lines 277-289). Gold hunk:

```
-
-                p = sum([self._eval_product(i, (k, a, n)) for i in p.as_coeff_Add()])
+                from sympy.concrete.summations import Sum
+                p = exp(Sum(log(p), (k, a, n)))
```

Only the assignment to `p` (the numerator) inside the `if q.is_Number:` arm
changes. The surrounding `p, q = term.as_numer_denom()`, `q =
self._eval_product(q, …)`, the `q.is_Number` test, and the trailing
`return p / q` are **unchanged**.

| # | Solution.lean impl op (`productOverRange`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| R1 | parameter `M : List (List Rat)`, `require ∀ r ∈ M, r.length = width`, `require ∀ r ∈ M, rowSum r ≠ 0` | the finite range `(k,a,n)` and the additive parts `p.as_coeff_Add()` of the numerator, restricted to ranges where no positional total `p.subs(k,k0)` is 0 | R | range position `k0=a+p` ↔ row `M[p]`; additive part value ↔ `M[p][i]`; `width` = number of parts (mapping.md §2). The new `p` depends only on these values, so the carrier is the rectangular `Rat` matrix. The nonzero-total precondition is the modeling boundary: at a zero total the patched `exp(Sum(log(p),…))` evaluates to the undefined symbolic `exp(zoo)` (log(0)=zoo), which has no `Rat` image, so those inputs are outside the modeled domain (mapping.md §2). |
| R2 | `rowSum r = r.foldr (·+·) 0` | the total of the parts at one position: each part evaluated at `k=k0` then summed (the value `p.subs(k,k0)`) | R | exact-rational sum; order-only, modeled with `Rat` (mapping.md §2). |
| A3→**I/deep** | `prodOfSums M = ∏ positions, rowSum(position)`, computed by the backward `while` fold | `exp(Sum(log(p), (k, a, n)))` | I (deep model) | the changed op is modeled **deeply**: on a concrete integer range with every positional total nonzero (the R1 precondition), `exp(Sum(log(p),(k,a,n)))` *is* `Mul(*[p.subs(k,k0) for k0 in range(a,n+1)])`, i.e. the product over positions of each position's `rowSum` — which is what `prodOfSums`/`rowSum` and the verified loop encode. When some total is 0 the closed form is instead the undefined `exp(zoo)`; that region is excluded by the precondition, not silently identified with 0. The fold ops (`rowSum r`, `*`, the loop) are concrete (**I**, transliterated by G-CONF over the required domain); the equality of `exp(Sum(log·))` to that iterated product on the domain is a sympy symbolic identity, cross-checked in conformance_check.py. No callee is axiomatized (mapping.md §3). |
| I2 | (not modeled; outside the method) `return p / q` and `q = self._eval_product(q,…)` | the unchanged numer/denom split and division | I | unchanged by the patch; the modeled `p` is divided by the same `q` on both sides, so it cancels in any behavioural comparison. Out of the method's scope by design. |

Discriminating content of the change — for the issue's `Product(n + 1/2**k,
(k,0,n-1))` at `n=2` the numerator parts at the two positions are `[1, 2]` and
`[1, 4]`; the patched product of positional totals is `(1+2)(1+4)=15`, whereas
the pre-patch *sum of part-products* is `1·1 + 2·4 = 9`. After the shared `/q`
(=2) these give the correct `15/2` vs. the buggy `9/2`.
`Solution_prepatch.lean` reproduces the `sum`-of-part-products skeleton and
**fails** `out = prodOfSums M` (G-DIFF) at exactly this discrepancy.

## B. No second changed site

The patch touches one statement in one function; there is no second
independently-fixed behavior, so a single `Solution_prepatch.lean` suffices.

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R or I. The one operation that genuinely *changed* — the value
assigned to `p` — is modeled **deeply** (`prodOfSums`, the spelled-out product
of positional totals), not hidden behind an axiom about `exp`/`log`/`Sum` or
about the function under change. There is **no consumed axiom and no
A-reference**: the patch introduces no call to an unchanged repo callee whose
contract the proof must assume; `exp(Sum(log(p),…))` is simply sympy's closed
form for the iterated product the deep model computes.

## D. verify(Solution) ⇒ resolved

`productOverRange` verifies only if its output equals `prodOfSums M`: the genuine
product, over every index position, of that position's total (A3/R2). By R
(range↔rows, part-value↔`Rat`) this equals `exp(Sum(log(p),(k,a,n)))` evaluated
on the range, which is the patched value of the numerator `p`; the unchanged
`/q` (I2) is applied identically on both sides. By G-CONF the R/I shadow of the
fold agrees with the patched-sympy oracle on ≥10⁵ fuzzed (range, additive-term)
inputs. Therefore any model satisfying this spec, refined by the map above, is
the gold patch up to type refinement — and the gold patch resolves (G-RESOLVE).
The single trust point is refinement fidelity (this doc + G-CONF); there are no
axioms (G-AX N/A).
