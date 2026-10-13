# refinement.md — sympy__sympy-13551

The operation-by-operation correspondence between `model.py`'s implementation
(the `product_of_sum` impl region and the deep `prod_of_totals` model) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A** (axiomatized callee — split into **A-consumed**, where the proof uses the
axiom's `Ensures`, and **A-reference**, where a deep model is validated == the
real callee by axiom_check.py / G-AX), or **I** (identical concrete operation).
The claim: *any implementation that verifies against this frozen spec, refined
per the map below, is behaviourally equal to the gold patch on the tested
inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The changed site — `Product._eval_product`, the `is_Add` / `q.is_Number` branch

`sympy/concrete/products.py:277-289`. Gold hunk (line 286):

```
-                p = sum([self._eval_product(i, (k, a, n)) for i in p.as_coeff_Add()])
+                from sympy.concrete.summations import Sum
+                p = exp(Sum(log(p), (k, a, n)))
```

Here `p` is the numerator (a sympy `Add`) of the multiplicand and `(k, a, n)` is
the product's index limit. The change replaces *the product of the sum, computed
wrongly as the sum of the per-part products* with *the genuine product of the
multiplicand over the index range*.

| # | model.py impl op (`product_of_sum`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameters `base: List[int]`, `comp: List[int]` (per-index values of the two parts of the sum) | the two elements of `p.as_coeff_Add()` (a leading coefficient part + the remaining part), evaluated over the index range | R | `as_coeff_Add()` returns a 2-tuple, so the sum splits into exactly two parts; `base`/`comp` are their per-index integer values (mapping.md §2). The binary split is faithful: the pre-patch `for i in p.as_coeff_Add()` iterates precisely these two parts. |
| A2 | `len(base) == len(comp) == L` and the loop index `i` over `0 .. L-1` | the index `k` ranging `a .. n` (range length `L = n - a + 1`) | R | finite index range ↔ list indices (mapping.md §2). |
| A2b | precondition `Forall i: base[i] + comp[i] != 0` (every per-index total nonzero) | the multiplicand `p` is nonzero at every index of the range; if some `p(k) = 0` then `log(p) = zoo` and the patched `exp(Sum(log(p)))` evaluates to the **undefined** `exp(zoo)`, not the integer `0` | R | domain boundary (mapping.md §2): zero-total inputs have no faithful integer counterpart — the real callee returns an undefined symbolic value there — so the model's `Requires` excludes them; axiom_check.py confirms the boundary (zero-total inputs → `exp(zoo)` in both the routed and direct forms). |
| A3 | `result = ∏_i (base[i] + comp[i])`, i.e. `prod_of_totals(ToSeq(base), ToSeq(comp))`, computed by the verified backward loop multiplying the per-index totals `base[i] + comp[i]` | `exp(Sum(log(p), (k, a, n)))` | A-reference | the changed product-of-a-sum operation is modelled **deeply**: `prod_of_totals` (the spelled-out per-index product fold in the `pure` region) and the verified loop in `product_of_sum` ARE the product of the per-index totals. There is no consumed product axiom — the proof never depends on one. The deep model is validated **== the real callee** out-of-band: G-AX (axiom_check.py) runs `exp(Sum(log(p)))` / `Product.doit` and asserts `exp(Sum(log(p))) == prod_of_totals(base, comp)` (mapping.md §3.1). Both compute the genuine product `∏_k (base[k] + comp[k])` (since `e^{Σ log p} = ∏ p`). |
| A4 | `result` returned (an `int`, the numerator product) | the value bound to `p`, then `return p / q` (the surrounding code, unchanged) | I | the division by the already-evaluated denominator product `q` is identical, unchanged code on both sides; only the numerator-product computation `p = …` changed. The numerator product is what this bundle models. |

The discriminating content of the change — *product of a sum is the product of
the per-index totals, NOT the sum of the per-part products* — lives in
`Result() == prod_of_totals(ToSeq(base), ToSeq(comp))` (model) ⇔
`p = exp(Sum(log(p), (k, a, n)))` (real). The pre-patch `_eval_product`
computed `sum([_eval_product(part) for part in p.as_coeff_Add()])` =
`prod_one(base) + prod_one(comp)` (the total of the two part-products);
`model_prepatch.py` reproduces exactly that (two part-product loops, then their
sum) and **fails** the postcondition
`Result() == prod_of_totals(ToSeq(base), ToSeq(comp))`, which is precisely the
spec sensing the change (G-DIFF). On the F2P inner product (`base=[1,1]`,
`comp=[2,4]` at `n=2`): the spec requires `(1+2)·(1+4) = 15`; the prepatch
produces `(1·1)+(2·4) = 9` — the `15/2` vs `9/2` of the issue.

## B. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-reference, or I. The one operation that genuinely
*changed* — the product of a sum — is modelled **deeply** (the spelled-out
per-index product fold `prod_of_totals` consumed in `product_of_sum`, step A3,
an **A-reference**), not hidden behind an axiom about the function under change:
there is **no consumed product axiom**. The only kind-A obligation,
`prod_of_totals` (**A-reference**), is the deep model that G-AX validates equal
to the real fixed callee `exp(Sum(log(p)))`. `prod_one` is a pure helper used
only to STATE the wrong pre-patch identity in the prepatch impl; it is not an
axiom and the model.py proof does not consume it.

## C. verify(model) ⇒ resolved

`product_of_sum` verifies only if its output equals the exact product of the
per-index totals `∏_i (base[i] + comp[i])` (A3) — never the sum of the per-part
products. By R (the sum's two parts ↔ `base`/`comp`; the finite index range ↔
list indices; sympy exact integer arithmetic ↔ `int`) the verified product
equals the numerator `p = exp(Sum(log(p), (k, a, n)))` of the gold patch on the
tested inputs; by G-AX the deep model `prod_of_totals` equals the real
`exp(Sum(log(p)))` (A-reference). The surrounding `return p / q` is identical (I).
Therefore a model satisfying this spec, refined by the map above, is the gold
patch up to type refinement and the audited deep-model reference — and the gold
patch resolves (G-RESOLVE: F2P `test_issue_13546` → `15/2`; all product P2P
tests pass). The trust points are exactly the two of PLAN §1.1: the deep-model
reference soundness (G-AX) and refinement fidelity (this document, G-EQ).
