# mapping.md — sympy__sympy-13551

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 9476425b9e34363c2d9ac38e9f04aa75ae54a775`, states the type
abstraction, and gives the provenance of the one kind-A obligation (a deep-model
reference, validated against the real callee by axiom_check.py / G-AX).

Repo file under change: `sympy/concrete/products.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `product_of_sum(base, comp)` | the `elif term.is_Add:` / `if q.is_Number:` block of `Product._eval_product(self, term, limits)` — `sympy/concrete/products.py:277-289` (the changed statement is line 286) | the modeled changed behaviour: evaluating a finite product whose multiplicand is a *sum* |
| `prod_of_totals(base, comp)` *(deep model — A-reference)* | `exp(Sum(log(p), (k, a, n)))` — the patched product-of-the-multiplicand operation (`sympy/concrete/products.py:286` post-patch); equivalently `Product(p, (k, a, n)).doit()` routed through this branch | pure spec: the genuine product over the index range of the per-index total; the deep model of the real fixed operation, validated `prod_of_totals == exp(Sum(log(p)))` by axiom_check.py (G-AX), NOT consumed as an axiom |
| `prod_one(xs)` | `_eval_product(part, (k, a, n))` applied to one summand `part` of `p.as_coeff_Add()` (the pre-patch line 286 building block) | pure spec: the product of a single part's contributions; used only to STATE the wrong pre-patch identity (sum of the two part-products), never the answer |
| `base[i]` | the leading element of `p.as_coeff_Add()` (the additive coefficient part) evaluated at index `k = a + i` | per-index value of the first part of the sum |
| `comp[i]` | the remaining element of `p.as_coeff_Add()` (the non-coefficient part) evaluated at index `k = a + i` | per-index value of the second part of the sum |

The pre-patch repo statement the change replaces (for the refinement audit, not
referenced from the consumer spec view) is `sympy/concrete/products.py:286`:

```python
p = sum([self._eval_product(i, (k, a, n)) for i in p.as_coeff_Add()])
```

i.e. `Σ_part _eval_product(part)` — the product distributed across the two parts
of the sum and the part-products added. The post-patch statement is:

```python
from sympy.concrete.summations import Sum
p = exp(Sum(log(p), (k, a, n)))
```

i.e. the genuine product `∏_{k=a}^{n} p`.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| the multiplicand `p` is a sympy `Add`; `p.as_coeff_Add()` returns a 2-tuple `(coeff, rest)` (a leading coefficient part + the remaining part) | two parallel `List[int]` `base`, `comp` | `base[i]` ↔ value of `coeff` at `k = a + i`; `comp[i]` ↔ value of `rest` at `k = a + i`. The binary split mirrors `as_coeff_Add()` exactly: the pre-patch loop `for i in p.as_coeff_Add()` iterates over precisely those two parts (refinement.md). |
| the index `k` ranging `a .. n` (a finite range of length `L = n - a + 1`) | the list index `i` ranging `0 .. L-1` | `len(base) == len(comp) == L` |
| the multiplicand `p` is nonzero at every index of the range (a vanishing multiplicand makes `log(p) = zoo`, so the patched reduction `exp(Sum(log(p)))` evaluates to the **undefined** `exp(zoo)`, not the integer `0`) | precondition `Forall i: base[i] + comp[i] != 0` | zero-total inputs are **outside the modeled domain**: on them the real callee returns an undefined symbolic value where the integer model has no faithful counterpart, so the model's `Requires` excludes them; axiom_check.py confirms the boundary (zero-total inputs give `exp(zoo)` in both the routed `Product.doit` and the direct `exp(Sum(log))` forms) |
| product `∏_{k=a}^{n} p(k)` over symbolic integers, computed as `exp(Sum(log(p)))` | integer product `∏_i (base[i] + comp[i])` (`prod_of_totals`) | the symbolic `exp(Sum(log(·)))` evaluates, on any concrete instantiation, to the literal product of the per-index totals (`e^{Σ log x} = ∏ x`); axiom_check.py (G-AX) confirms the equality on the real callee |
| sympy integer arithmetic (`Integer`, exact rationals) | Python `int` | the tested behaviour is exact integer/rational; no precision modeling needed (no `--float-encoding`). The F2P observes exact values `15/2` vs `9/2`; the numerator-product (this branch) is exact integer arithmetic. |

Nagini bans `str` indexing; here the carrier is `List[int]` of per-index part
values and the specification is carried over `PSeq[int]` via `ToSeq`. The product
is proven by a backward per-index fold (front-recursive `prod_of_totals` gives a
single unfold per loop step).

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `prod_of_totals` deep model ↔ `exp(Sum(log(p), (k, a, n)))` (A-reference)

**Callee:** the patched operation `exp(Sum(log(p), (k, a, n)))` in
`Product._eval_product` (`sympy/concrete/products.py:286` post-patch), with
`Sum`/`exp`/`log` from `sympy.concrete.summations` and
`sympy.functions.elementary.exponential`. The changed product-of-a-sum operation
is modelled **deeply** by the `@Pure` front-recursive fold `prod_of_totals` (with
`prod_one` only stating the wrong identity); there is **no `@ContractOnly` axiom**
the proof consumes. The deep model is validated equal to the real callee
out-of-band by axiom_check.py (G-AX).

Why the equality holds: `exp(Sum(log(p), (k, a, n)))` is the symbolic-engine
expression of the genuine product `∏_{k=a}^{n} p(k)` (because
`e^{Σ_k log p(k)} = ∏_k e^{log p(k)} = ∏_k p(k)`). On any concrete index range
and integer-valued multiplicand `p(k) = base[k] + comp[k]`, that product is
exactly `∏_k (base[k] + comp[k]) = prod_of_totals(base, comp)`. G-AX
substitutes concrete bounds into `Product(p, (k, 0, n-1)).doit()` (and the direct
`exp(Sum(log(p), (k, 0, N-1)))`) and asserts equality with the deep model.

**Branch dependency (recorded so G-AX fuzzes the right configuration):** the
patched `is_Add` / `q.is_Number` branch fires only for a **non-polynomial** `Add`
multiplicand evaluated with **symbolic** limits (a polynomial `Add` takes the
`term.is_polynomial(k)` roots branch; concrete limits take the
`dif.is_Integer` finite-range branch). axiom_check.py therefore uses exponential
multiplicands of the shape `d + c·2**k` — exactly the F2P numerator
`2**k*n + 1` (a constant part `1` plus an exponential part `2**k*n`) — and
asserts the `exp(Sum(log(...)))` form actually fired before comparing values.

**Soundness check (G-AX):** `axiom_check.py` runs the real
`Product(...).doit()` / `exp(Sum(log(...)))` on boundary cases (range lengths
1..6 over ten multiplicand shapes incl. the F2P shape and negative constant
parts) plus 300 randomized `(d, c, N)` fuzz draws with `d ∈ -9..9 \ {0}`
(`d = 0` makes `p` a pure power, not an `Add`, so the modeled branch cannot
fire; zero-total draws are outside the modeled domain per the `Requires` and
are skipped). It asserts `prod_of_totals(base, comp)` equals the real callee
on every in-domain input (317 of them) and that the pre-patch
sum-of-part-products (`prod_one(base) + prod_one(comp)`) differs on the
witnesses (267 of them) — the exact discriminator the F2P test
`test_issue_13546` observes (`15/2` correct vs `9/2` pre-patch). It also
confirms the domain boundary: on 4 zero-total inputs the real callee yields
the undefined `exp(zoo)` (never the integer `0`) in both the routed and the
direct form — exactly the inputs the model's `Requires` excludes. It imports
only `sympy` (the repo under test, whose `_eval_product`/`exp`/`Sum`/`log` ARE
the real callee) and the standard library. Exit 0 iff sound.
