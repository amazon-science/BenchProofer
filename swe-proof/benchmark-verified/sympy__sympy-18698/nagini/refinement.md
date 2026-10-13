# refinement.md — sympy__sympy-18698

The operation-by-operation correspondence between `model.py`'s implementation
(the `consolidate_by_multiplicity` impl region, the deep `dedup` and `prod_k`
models, and the `occurs`/`occurs_in` helpers) and `patch.diff` (the gold patch).
Each step is tagged **R** (type refinement), **A-consumed** (the proof uses an
axiom's `Ensures`), **A-reference** (a deep model / determined value is validated
== the real callee by axiom_check.py / G-AX, NOT consumed), or **I** (identical
concrete operation). The claim: *any implementation that verifies against this
frozen spec, refined per the map below, is behaviourally equal to the gold
patch on the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit`, and
locally resolves the FAIL_TO_PASS test `test_factor_terms` + the new
`test_issue_8695` and regresses no PASS_TO_PASS test in `test_polytools.py`).

## A. The consolidation site — the new `method == 'sqf'` block in `_symbolic_factor_list`

Gold hunk (`sympy/polys/polytools.py`, before `return coeff, factors`):
```
+    if method == 'sqf':
+        factors = [(reduce(mul, (f for f, _ in factors if _ == k)), k)
+                   for k in set(i for _, i in factors)]
```
(plus the imports `from functools import wraps, reduce` and
`from operator import mul`.)

| # | model.py impl op (`consolidate_by_multiplicity`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameters `factors: List[int]`, `mults: List[int]` (parallel, equal length) | the local `factors` list of `(expr, k)` pairs | R | the pair list ↔ two parallel `List[int]`; `factors[i]` a distinct token for `expr_i`, `mults[i] == k_i` (mapping.md §2). The consolidation depends on the multiplicities (which factors group) AND on the product of each group; both preserved by the bijection (the factor tokens carry the multiplicative structure — mapping.md §2/§3). |
| A2 | the reported distinct multiplicities, built by the phase-1 loop appending each multiplicity only when `occurs_in(dmults, m)` is false, equal to `dedup(ToSeq(mults))` | `for k in set(i for _, i in factors)` (the distinct multiplicities) | R | `dedup(ToSeq(mults))` (the spelled-out keep-first distinct fold in the `pure` region) is the set of distinct multiplicities; `set(...)` is the unordered version. The model canonicalises to first-occurrence order; that order is **unobservable** because `_generic_factor_list` runs `_sorted_factors(fp, method)` (`polytools.py:5998`) on the result before returning, so any order of the same distinct multiplicities yields the same final, sorted `sqf_list` output. Hence model's ordered dedup R-refines the patch's unordered `set` (same multiset of reported multiplicities). The membership test `occurs_in` ↔ the dedup the `set` performs. |
| A3 | the merged factor recorded for the j-th reported multiplicity `k = dedup(ToSeq(mults))[j]` is `prod_k(ToSeq(factors), ToSeq(mults), k, len(mults))` — the spelled-out product over EXACTLY the contributions of multiplicity `k`; phase-2 computes it by the inner accumulation loop and the postcondition `Result()[j] == prod_k(...)` **pins it** (the proof consumes the deep `prod_k` model) | `reduce(mul, (f for f, _ in factors if _ == k))` — the merged factor for `k` | R + A-reference | the changed product operation is the per-group product. It is now modelled **deeply**: `prod_k` is the product fold over exactly the multiplicity-`k` contributions (the `pure` region), and the verified phase-2 loop proves the recorded factor equals it (`lemma_prod_unfold` + `acc == prod_k(...)` invariant). The model's `prod_k` is the structural twin of `reduce(mul, (f for f, _ in factors if _ == k))`: same group (filter `_ == k`), same fold (`reduce(mul, ·)` ↔ left-product). The only library fact still referenced (not consumed) is that the SymPy product `mul ⇒ Mul` is the commutative/associative monoid that integer multiplication of the tokens models — an **A-reference** validated by G-AX (axiom_check.py), so the token product faithfully stands for the real `Mul`. The merged-factor VALUE the F2P test grades is therefore pinned in the verified postcondition, not delegated. |
| A4 | `return out` (the merged factors, one per distinct multiplicity, in first-occurrence order) | the rebound `factors` list returned via `return coeff, factors` | R | `out` (the `List[int]` of merged factors) ↔ the rebuilt list of `(product_k, k)` pairs under the A1 bijection; entry j carries the A2 multiplicity `dedup(...)[j]` and the A3 product `prod_k(...)`. `coeff` is untouched by this block (identity). |

The discriminating content of the change is **two-dimensional** and both
dimensions live in the verified postcondition:
1. *several factors of one multiplicity collapse to ONE entry* — pinned by
   `len(Result()) == len(dedup(ToSeq(mults)))` (one entry per distinct
   multiplicity).
2. *the kept entry's factor is the PRODUCT of that group* — pinned by
   `Result()[j] == prod_k(ToSeq(factors), ToSeq(mults), dedup(ToSeq(mults))[j],
   len(mults))` (the deep per-group product).

The FAIL_TO_PASS test `test_factor_terms` grades the merged factor *value*
(`sqf_list(x*(x+y)) == (1, [(x**2 + x*y, 1)])`); dimension 2 pins exactly that
value, so a verifying impl cannot record a wrong factor (e.g. keep-first via
`next(...)`) — such an impl fails the `prod_k` postcondition (confirmed: the
keep-first construction does NOT verify against this spec). The pre-patch code
kept every contribution (`return coeff, factors` un-consolidated);
`model_prepatch.py` reproduces that (it copies every contribution into `out`, so
`len(out) == len(mults)` and each entry is the lone factor) and **fails** both
postcondition clauses exactly when a multiplicity repeats — which is precisely
the bug the F2P test pins (`sqf_list(x*(x+y))` had two multiplicity-1 entries
`(x, 1), (x+y, 1)` instead of the merged `(x**2+x*y, 1)`;
`sqf_list((x**2+1)(x-1)^2(x-2)^3(x-3)^3)` had two multiplicity-3 entries instead
of their product). (G-DIFF.)

## B. The behaviourally-inert refactor hunk (NOT modeled — justified)

The same gold patch also rewrites the argument-classification head of
`_symbolic_factor_list` (`polytools.py:5905-5911`):
```
-        if arg.is_Mul:
-            args.extend(arg.args)
-            continue
-        if arg.is_Pow:
+        elif arg.is_Pow:
```
This removes a dead `is_Mul` branch (`Mul.make_args(expr)` already flattens
nested `Mul`s, so `arg.is_Mul` never held for an element of `args`) and joins
`is_Pow` to the preceding `if arg.is_Number` chain with `elif`. Executing each
hunk in isolation at `base_commit` confirms this hunk **does not change any
FAIL_TO_PASS or PASS_TO_PASS observable**: with only this hunk applied,
`sqf_list(x*(x+y))` and `sqf_list((x**2+1)(x-1)^2(x-2)^3(x-3)^3)` are byte-equal
to pre-patch; only the §A consolidation block makes the F2P tests pass.

Per SPEC_GUIDE (model each *independently-observable fixed behaviour*), there is
exactly ONE fixed behaviour to model — the consolidation (§A). The refactor is
not an independently-fixed behaviour (it fixes nothing observable), so it is not
modeled and needs no `model_prepatch` variant. It is carried in `patch.diff`
verbatim (the gold), is a pure structural simplification (no kind-3 step), and
does not affect `verify ⟹ resolved`: the F2P/P2P verdicts are driven solely by
§A, which the model pins. (G-RESOLVE on the full gold confirms it: 149 passed,
1 pre-existing xfail, in `test_polytools.py`.)

## C. No kind-3 (unexpressible-changed-op) steps

Every step in §A is R, A-reference, or I. The operation that genuinely *changed*
— collapsing same-multiplicity factors into one product entry — is modelled
**deeply in BOTH of its dimensions**:
- the distinct-keeping of the multiplicities is the `dedup` fold (the `pure`
  region) discharged by the phase-1 loop;
- the per-group product is the `prod_k` fold (the `pure` region) discharged by
  the phase-2 inner loop, and is **pinned in the verified postcondition**
  (`Result()[j] == prod_k(...)`), so the F2P-discriminating value is consumed by
  the proof, not delegated.

The earlier construction routed the product to an A-reference the proof never
consumed (a kind-3 step in disguise — the changed op was invisible to the
verifier); that hole is closed. The remaining kind-A relationship is a genuine
**A-reference**: that the SymPy expression product `mul ⇒ Mul` is the
commutative/associative monoid which integer multiplication of the distinct
factor tokens models (so `prod_k` over the tokens faithfully stands for
`reduce(mul, group)` over the real `Expr`s). axiom_check.py / G-AX validates this
monoid correspondence. There is no consumed `@ContractOnly` axiom in this bundle.

## D. verify(model) ⇒ resolved

`consolidate_by_multiplicity` verifies only if (i) its output length equals
`len(dedup(ToSeq(mults)))` — exactly the distinct multiplicities, each once (A2)
— and (ii) its j-th merged factor equals `prod_k(ToSeq(factors), ToSeq(mults),
dedup(ToSeq(mults))[j], len(mults))` — the product of exactly the group of that
multiplicity (A3). By R (pair-list ↔ parallel `List[int]`; first-occurrence
order unobservable under the downstream `_sorted_factors`) the verified
distinct-keeping equals the patch's `for k in set(i for _, i in factors)`
keying; by the deep `prod_k` model (R) + the monoid A-reference (G-AX) the merged
factor for each reported `k` is exactly `reduce(mul, group)` = `Mul(*group)`, the
patch's product. Therefore a model satisfying this spec, refined by the map
above, is the gold patch's consolidation block up to type refinement and the
audited monoid correspondence — and the gold patch resolves (G-RESOLVE, verified
locally). Both F2P-graded dimensions (which multiplicities are reported AND the
product recorded for each) are pinned by the verified postcondition; no
verifying impl can ship a wrong reported multiplicity OR a wrong merged factor
(G-DIFF + the keep-first counterexample fails to verify). The trust points are
exactly the two of PLAN §1.1: A-reference soundness (G-AX on the product monoid)
and refinement fidelity (this document, G-EQ).
