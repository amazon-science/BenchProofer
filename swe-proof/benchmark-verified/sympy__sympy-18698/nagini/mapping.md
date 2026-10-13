# mapping.md — sympy__sympy-18698

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 3dff1b98a78f28c953ae2140b69356b8391e399c`, states the type
abstraction, and gives the provenance of the one kind-A relationship (an
A-reference — there are no consumed axioms).

Repo file under change: `sympy/polys/polytools.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `consolidate_by_multiplicity(factors, mults)` | the post-loop consolidation added to `_symbolic_factor_list(expr, opt, method)` — `sympy/polys/polytools.py:5898` (function), the new block inserted before `return coeff, factors` at `:5953` | the modeled changed behaviour: when `method == 'sqf'`, the factor list is rebuilt so each distinct multiplicity appears once, its factor being the product of all factors of that multiplicity |
| `dedup(s)` *(deep model)* | the multiplicity-keying `set(i for _, i in factors)` of the patch's comprehension (`polytools.py`, new block) | pure spec: the distinct multiplicities, each kept once |
| `prod_k(facs, mlts, k, n)` *(deep model)* | the per-multiplicity product `reduce(mul, (f for f, _ in factors if _ == k))` of the patch's comprehension (`polytools.py`, new block) | pure spec: the product over EXACTLY the contributions of multiplicity `k` (filter `_ == k`, then left-product). **Consumed by the proof** — the postcondition pins `Result()[j] == prod_k(...)`, so the merged-factor value the F2P test grades is in the verified spec. The monoid faithfulness of integer multiplication for the real `Mul` is the A-reference of §3.1 |
| `occurs(s, k)` / `occurs_in(xs, k)` | (proof helpers) value membership used to build the dedup — no direct repo symbol; mirror the `if v not in seen` semantics of de-duplication | pure/loop helper for the construction |
| the product operator on the factor tokens (`*`) *(A-reference)* | `mul` ⇒ `Mul` for SymPy expressions — `from operator import mul` (post-patch), applied by `reduce` (`from functools import reduce`, `polytools.py:5` post-patch) | the monoid the merged factor is computed in: `Mul` is commutative/associative, so integer `*` of the distinct factor tokens faithfully models `reduce(mul, group)`; validated by axiom_check.py (G-AX), NOT consumed as an axiom (the product STRUCTURE is consumed via `prod_k`; only the token↔`Mul` monoid correspondence is the reference) |

The pre-patch repo state the change rebuilds (for the refinement audit, not
referenced from the consumer spec view): `_symbolic_factor_list` returned
`coeff, factors` with `factors` holding EVERY contribution separately
(`polytools.py:5953`), so two factors of the same multiplicity stayed as two
entries — the reported bug (`(x-3, 3)` and `(x-2, 3)` instead of
`(x**2-5*x+6, 3)`).

A second, behaviourally-inert hunk in the same gold patch — replacing
`if arg.is_Mul: args.extend(arg.args); continue` / `if arg.is_Pow:`
(`polytools.py:5908-5911`) with `elif arg.is_Pow:` — is a refactor that does NOT
change any FAIL_TO_PASS- or PASS_TO_PASS-observable behaviour (confirmed by
executing each hunk in isolation at base_commit: the `is_Mul` removal alone
leaves `sqf_list((x**2+1)*(x-1)**2*(x-2)**3*(x-3)**3)` and `sqf_list(x*(x+y))`
identical to pre-patch; only the consolidation block changes them). It is
therefore NOT modeled; see refinement.md §B. `Mul.make_args(expr)` already
flattens nested `Mul`s, so the removed branch was dead.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| the list `factors` of `(expr, k)` pairs built by `_symbolic_factor_list` | two parallel `List[int]`: `factors` (factor token) and `mults` (multiplicity `k`), equal length; specified over `PSeq[int]` via `ToSeq` | the i-th repo pair `(expr_i, k_i)` ↔ `(factors[i], mults[i])`; `factors[i]` is a distinct integer token standing for the distinct factor expression `expr_i`; `mults[i] == k_i` |
| a factor expression `expr` (a SymPy `Expr`/`Poly`) | a distinct `int` token | the consolidation depends only on WHICH factors are grouped and on their PRODUCT, never on the internal spelling of an expression; a distinct token per distinct expression suffices, with the per-group product modelled by integer multiplication of the tokens (the monoid faithfulness is the A-reference, §3.1) |
| `set(i for _, i in factors)` (the distinct multiplicities) | `dedup(ToSeq(mults))` | the set of distinct multiplicities; the model canonicalises the order to first-occurrence, which is unobservable because `_generic_factor_list` sorts the result via `_sorted_factors(fp, method)` (`polytools.py:5998`) before returning — refinement.md §A |
| `reduce(mul, (f for f, _ in factors if _ == k))` (the merged factor of group `k`) | `prod_k(ToSeq(factors), ToSeq(mults), k, len(mults))` (deep model) | the product over EXACTLY the contributions of multiplicity `k`; **consumed** by the proof — the postcondition pins `Result()[j] == prod_k(...)` for the j-th distinct multiplicity. The token product `*` models the real `Mul` monoid (A-reference §3.1) |
| the result list `[(product_k, k) for k in set(...)]` | `Result()` = the `List[int]` of MERGED FACTORS, one per distinct `k` in first-occurrence order; entry j is `prod_k(..., dedup(mults)[j], len(mults))` | one merged factor per distinct multiplicity; both the reported multiplicity (via `dedup`) and the merged factor VALUE (via `prod_k`) are pinned in the verified postcondition (§3) |
| `k`/multiplicity (a Python `int`, exponent) | `int` | identity |

`str`/expression indexing is not used; the carriers are `List[int]` and the
specification is carried by `PSeq[int]` via `ToSeq`.

## 3. The kind-A relationship — A-reference (checked by G-AX / axiom_check.py)

### 3.1 the per-group product monoid: token `*` ↔ `reduce(operator.mul, group)` (A-reference, NOT consumed)
**Callee:** `functools.reduce` with `operator.mul` (the patch's
`from functools import reduce` / `from operator import mul`), applied as
`reduce(mul, (f for f, _ in factors if _ == k))`. For SymPy expressions `mul`
is `Expr.__mul__` ⇒ `Mul`, which is **commutative and associative**.

The merged factor recorded for a reported multiplicity `k` is the product of
**exactly** the factors of multiplicity `k`, taken over the contributions. The
product STRUCTURE — *which* factors enter (the filter `_ == k`) and that they are
folded by left-product — is modelled **deeply** by `prod_k` and **consumed** by
the proof: the postcondition pins `Result()[j] == prod_k(ToSeq(factors),
ToSeq(mults), dedup(ToSeq(mults))[j], len(mults))`, and the phase-2 loop
discharges it. So a verifying impl MUST record the product of exactly the group
(a keep-first / wrong-factor impl fails — confirmed by an explicit non-verifying
counterexample).

What remains an **A-reference** (NOT consumed) is the *faithfulness of the
monoid model*: that integer multiplication of the distinct factor tokens stands
for the real SymPy `Mul`. Because `Mul` is commutative/associative, the merged
factor is a function of the group alone (independent of contribution order), and
integer `*` (likewise commutative/associative) is a faithful monoid model of it.
axiom_check.py (G-AX) validates this: it re-executes the patch's comprehension
`[(reduce(mul, (f for f, _ in factors if _ == k)), k) for k in set(i for _, i in
factors)]` and asserts, on boundary + 20 000 fuzz inputs (and, when `sympy` is
importable, symbolically on the issue's own examples), that the merged factor
for each `k` equals `reduce(mul, [contributions of multiplicity k])` — no factor
of `k` dropped and none of another multiplicity mixed in — and that
`reduce(mul, ·)` is order-independent (the commutative/associative monoid
property), exactly as `prod_k` over the integer tokens computes it.

### 3.2 No consumed axioms
Both dimensions of the consolidation are modelled **deeply** in model.py's
`pure` region and discharged by the verified construction loops: the
distinct-keeping fold `dedup` (the reported multiplicities) and the per-group
product fold `prod_k` (the merged factor). There is no `@ContractOnly` the proof
consumes. The only library fact relied on out-of-band — that the SymPy `Mul`
monoid is faithfully modelled by integer multiplication of the distinct tokens —
is the A-reference of §3.1, validated by G-AX, never an `Ensures` the proof
leans on. axiom_check.py imports only the standard library (`operator`,
`functools`, `random`) plus an optional `sympy` for the symbolic leg — nothing
repo-specific beyond the very callees the patch uses.
