# mapping.md — sympy__sympy-13551

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 9476425b9e34363c2d9ac38e9f04aa75ae54a775`, states the type
abstraction (the bijection G-CONF uses to bridge Lean↔Python), and records the
provenance of the modeled operation. There are **no axioms / A-references** in
this bundle (§3): the only operation the patch changes is modeled **deeply**,
and it calls no unchanged repo callee that the proof must axiomatize.

Repo file under change: `sympy/concrete/products.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `productOverRange (M : List (List Rat)) (width : Nat)` | the recomputation of `p` (the numerator) on the additive branch of `Product._eval_product` — `sympy/concrete/products.py:277-289` (the changed statement is the assignment to `p`, body around line 286) | the modeled changed computation: the value the iterated multiplication produces over the finite range when the summand is additive with numeric denominator |
| `rowSum (r : List Rat)` | the total contributed at one index position by all additive parts of the numerator at that position — i.e. `p.subs(k, k0)` re-summed over the parts of `p.as_coeff_Add()` | pure spec: a single position's total |
| `prodOfSums (M : List (List Rat))` | the post-patch value of `p`: `exp(Sum(log(p), (k, a, n)))` — the genuine product, over every index position of the range, of that position's total | pure spec: deep model of the changed product computation |

The pre-patch repo expression this change removes (refinement audit only, not in
the consumer spec view): `sum([self._eval_product(i, (k, a, n)) for i in
p.as_coeff_Add()])` — the *sum, over the additive parts, of each part's product
across the range*. That is `sumOfProds` (the prepatch skeleton): the transpose
aggregation, equal to `prodOfSums` only when at most one part is nonzero at each
position, and wrong in general (the issue's `n + 1/2**k` example).

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) uses to translate values between the Lean value
domain and the Python repo values. A wrong entry surfaces as a spurious G-CONF
disagreement.

| repo reality | Lean carrier | bijection |
|---|---|---|
| a finite range `(k, a, n)` of integer index positions, `a..n` inclusive | the list of rows `M`, one row per position, `M.length = n - a + 1` | position `k0 = a + p` (0-based offset `p`) ↔ row `M[p]`; an empty range ↔ `M = []` |
| the additive numerator `p` with parts `[c₀, c₁, …]` from `p.as_coeff_Add()`, each part a concrete rational once `k` and the outer symbol are substituted to integers | the inner list `M[p] : List Rat`, the parts' values at that position | `cᵢ.subs(k, k0).subs(<outer symbol>, N)` (a `Rational`) ↔ `M[p][i] : Rat`; `len(parts)` ↔ `width` |
| sympy `Rational` / `Integer` arithmetic (exact) | Lean `Rat` (exact rational) | value-equal; modeling is **order-only/exact**, so `Rat` (not `Float`) per project convention — no precision behavior is at stake, only the order of the `+`/`*` aggregation |
| the patched product `exp(Sum(log(p), (k, a, n)))` evaluated at a concrete range | `prodOfSums M` | `exp(Sum(log(p),(k,a,n)))` is sympy's closed form for `∏_{k=a}^{n} p(k)`; on a concrete integer range this equals `Mul(*[p.subs(k,k0) for k0 in range(a,n+1)])`, whose factor at each position is that position's `rowSum`. Validated as an identity in conformance_check.py §oracle. |

The `require ∀ r ∈ M, r.length = width` encodes that every position contributes
the same set of additive parts (the parts of one fixed `p`); it is the
rectangularity the bridge needs to read `M` either row-wise (`prodOfSums`) or
column-wise (the prepatch `sumOfProds`).

The `require ∀ r ∈ M, rowSum r ≠ 0` is the **modeling boundary** for the
zero-total degeneracy of the patched expression: when some position's total
`p.subs(k, k0)` is 0, the patched `exp(Sum(log(p), (k, a, n)))` hits
`log(0) = zoo` and the repo returns the *undefined symbolic* value `exp(zoo)`
(verified against the patched repo: `Product(1-2**k,(k,0,n-1)).doit().subs(n,m)`
is `exp(zoo)` for m = 1, 2, 3), **not** the rational 0 that the idealized
iterated product would give. `exp(zoo)` has no image in the `Rat` carrier, so
inputs containing a zero-total position lie outside the modeled domain and the
method claims nothing about them. On the required domain (all positional totals
nonzero) the closed form and the iterated product coincide exactly, which is
what `prodOfSums` computes. The F2P behavior (all totals positive: 3 and 5 at
n=2) is squarely inside the domain, and the discriminating pre-patch bug
(sum-of-part-products, 9/2 vs 15/2) is still fully pinned.

The outer integer `N` substituted for the symbolic upper-bound symbol (the `n`
of the issue's `Product(n + 1/2**k, (k,0,n-1))`) is part of the bridge: the
buggy branch only fires for a **symbolic** range (a concrete integer `dif`
takes the earlier `dif.is_Integer` branch, line 255), so the observable value is
symbolic and is read off only after `subs(<symbol>, N)` — exactly the shape of
the F2P test `p.subs(n, 2).doit() == S(15)/2`.

## 3. Callee provenance — none

The changed statement assigns `p` from `exp(Sum(log(p), (k, a, n)))`. `exp`,
`log`, `Sum` are **not** axiomatized: their net effect on a concrete integer
range is exactly the iterated product, which is what `prodOfSums` computes
directly (a **deep model of the changed op**, §3 — not an A-reference, because
A-reference is reserved for a deeply-modeled *unchanged* callee). The recursion
into `self._eval_product(q, …)` and the trailing `/q` are **unchanged** by the
patch and lie outside the modeled statement; they are R/I context (refinement.md
rows R3/I2), not callees the proof reasons about. Hence: no `axiom`, no `:|`
stub, no A-reference. `axiom_check.py` is a `status=skip` stub (G-AX N/A);
`conf_skip = false` (the impl region is all R/I, G-CONF applies).

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`13551`** so the
consumer-side verdict is reproducible. The R/I shadow transliterates
`rowSum`/`prodOfSums` to Python rationals; the oracle is the patched product
(`Mul(*[p.subs(k,k0) …])`), anchored to the literal patch text
`exp(Sum(log(p),(k,a,n)))` by a sympy symbolic-identity cross-check on a sample.
