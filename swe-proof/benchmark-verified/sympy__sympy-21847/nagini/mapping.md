# mapping.md — sympy__sympy-21847

Binds every `model.py` symbol to its repository counterpart at
`base_commit = d9b18c518d64d0ebe8e35a98c2fb519938b9b151`, states the type
abstraction, and records callee provenance.

Repo file under change: `sympy/polys/monomials.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `keep_comm(powers, min_degree)` | the retention test of the **commutative** branch of `itermonomials` — `sympy/polys/monomials.py:130` (`if max(powers.values()) >= min_degree:` inside the `combinations_with_replacement` loop) | the modeled changed predicate, site 1 (hunk 1) |
| `keep_noncomm(powers, min_degree)` | the retention test of the **non-commutative** branch of `itermonomials` — `sympy/polys/monomials.py:142` (`if max(powers.values()) >= min_degree:` inside the `product` loop) | the modeled changed predicate, site 2 (hunk 2) |
| `deg_sum(p)` *(deep model, the spec carrier)* | `sum(powers.values())` — the post-patch reduction (`monomials.py:130,142` after the fix); the total degree of the candidate term | pure spec: total degree as the arithmetic sum of the exponent vector |
| pre-patch reduction *(model_prepatch.py only, inline)* | `max(powers.values())` — the pre-patch reduction (`monomials.py:130,142` before the fix); the largest single per-variable exponent | modeled INLINE in model_prepatch.py as a running-max loop (invariant `forall j in [i,len): powers[j] <= running`); NOT a named pure helper and NOT in model.py's consumer-visible spec view (removed in refinement to fix the fix-mechanism leak); the reference fold `deg_max` lives only in axiom_check.py |

The function under change is `itermonomials(variables, max_degrees, min_degrees=None)`
(`sympy/polys/monomials.py:14-152`). The two changed hunks are the two retention
tests above; both change `max(...)` to `sum(...)`. The modeled `powers` vector
is the `powers` dict's value list (`powers.values()`) built in the loop body
(`monomials.py:124-129` / `136-141`): for each candidate `item` (a length-`max_degree`
multiset/tuple of variables drawn from `variables + [S.One]`), `powers[v]` counts
the occurrences of each real variable `v` (the `S.One` padding is skipped by the
`if variable != 1` guard). So `powers.values()` is exactly the exponent vector of
the candidate monomial.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `powers` — a `dict` mapping each variable to its non-negative integer exponent in the candidate term | `powers: List[int]` of the exponent values | `powers.values()` ↔ the list elements; order is irrelevant to `sum`/`max` (both are order-independent), so any enumeration order of the dict values is a faithful witness. Every value is `>= 0` (initialised to 0, only `+= 1`). |
| `max_degrees` (an int, the `total_degree` branch) | implicit: `len(powers)` is the number of variables; the candidate has total degree `<= max_degree` by construction of `combinations_with_replacement(variables, max_degree)` / `product(variables, repeat=max_degree)` | the upper bound is already enforced by the enumeration; the *changed* logic is solely the lower-bound retention test, which is what is modeled |
| `min_degrees` (an int → `min_degree`, the `total_degree` branch) | `min_degree: int`, `Requires(min_degree >= 0)` | `min_degrees` is validated `>= 0` and `<= max_degree` upstream (`monomials.py:104-115`); the modeled predicate receives it directly |
| `sum(powers.values())` | `deg_sum(ToSeq(powers))` | `sum` over the value list ↔ the front-recursive arithmetic fold |
| `max(powers.values())` (pre-patch) | inline running-max loop in model_prepatch.py | `max` over the value list ↔ a running-max loop with invariant `forall j in [i,len): powers[j] <= running` (no named pure helper; model_prepatch.py only) |
| `Mul(*item)` build + `set(...)` dedup + `yield from` | omitted (unchanged plumbing) | the *enumeration* and term construction are unchanged by the patch; only the per-candidate retention predicate changed. The membership of the yielded set is determined entirely by which candidates pass the predicate, so pinning the predicate pins the change the F2P test observes. |

`powers.values()` is non-empty in the real code (the dict always contains every
variable, including the `S.One` padding key), but `sum`/`max` over the modeled
exponent list are well-defined for any length; the empty case (`deg_sum == 0`,
`deg_max == 0`) is handled and is consistent with the documented `min_degree <=
total_degree` contract.

## 3. Callee provenance (kind-A)

**None.** No `@ContractOnly` axiom is shipped. The only operation the patch
changes — the reduction over the exponent vector — is modeled DEEPLY by the
pure fold `deg_sum` (and, for the pre-patch reduction, inline in
model_prepatch.py); it is not an unchanged opaque callee, so it is not
axiomatized (SPEC_GUIDE directive 7: never axiomatize the operation the patch
changes). The unchanged plumbing (`combinations_with_replacement`, `product`,
`Mul`, `set`) does not appear in the spec or proof and needs no axiom: it is
enumeration/construction that the patch does not touch and the modeled predicate
abstracts over (§2, last row).

Because there is no axiom, there is no G-AX obligation for this bundle; the deep
fold `deg_sum` (and the inline pre-patch running-max) are total,
side-effect-free integer arithmetic whose correspondence to `sum`/`max` over the
exponent multiset is immediate. `axiom_check.py` records this (part 1) and
exercises the discriminating witness on the real `itermonomials` (part 2,
guarded to run only when the gold patch is applied; it skips cleanly at
base_commit so the script exits rc 0 as shipped in the pinned container).
