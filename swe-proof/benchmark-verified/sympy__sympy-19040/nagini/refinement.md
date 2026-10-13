# refinement.md — sympy__sympy-19040

The operation-by-operation correspondence between `model.py`'s implementation
(the `ext_factor` impl region and the three consumed axioms) and `patch.diff`
(the gold patch). Each step is tagged **R** (type refinement), **A** (axiomatized
callee — **A-consumed**, the proof uses the axiom's behaviour), or **I**
(identical concrete operation). The claim: *any implementation that verifies
against this frozen spec, refined per the map below, is behaviourally equal to
the gold patch on the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## The single change site — `dmp_ext_factor` (`sympy/polys/factortools.py:1138`)

Gold hunk (body line 1150):
```
  f, F = dmp_sqf_part(f, u, K), f
- s, g, r = dmp_sqf_norm(f, u, K)
+ s, g, r = dmp_sqf_norm(F, u, K)
  factors = dmp_factor_list_include(r, u, K.dom)
  if len(factors) == 1:
      factors = [f]
  else:
      ... recover each factor ...
  return lc, dmp_trial_division(F, factors, u, K)
```

After `f, F = dmp_sqf_part(f, u, K), f`, `F` holds the original (monic)
polynomial and `f` holds its square-free part — a possibly-fewer-factor
polynomial. The recovery `r` (whose factor list is read back and trial-divided
against `F`) must be built from `F`, not from `f`; otherwise factors that `f` has
lost cannot be recovered and the factorisation is incomplete — and when the
recovery collapses to a single element the selection branch returns the
representative `f` as ONE un-split factor (the issue: `factor((x−1)(y−1),
extension=[I])` returns `x − 1`, dropping `y − 1`).

### Carrier abstraction
The function receives an EXPANDED polynomial (a coefficient form), modelled by an
opaque identity `poly` (mapping.md §2). It returns a factor list, modelled by
`List[int]` of factor identities. Input identity ≠ output factor list, so echoing
the input or returning it as a length-one list is NOT a valid factorisation.

### Grounding of the postcondition (no answer-key oracle)
The contract is stated purely structurally over the input-driven factoring
`factor_list(poly)`:
```
Ensures(Implies(len(factor_list(poly)) >= 2, ToSeq(Result()) == factor_list(poly)))
Ensures(Implies(len(factor_list(poly)) <= 1, ToSeq(Result()) == lone(poly)))
```
`factor_list` is an A-consumed axiom of the real, unchanged recovery pipeline
(mapping.md §4.2), NOT a hardcoded lookup. So `return factor_list(poly)` is the
genuine, RESOLVING gold computation (the A-reference exemplar pattern), while no
opaque answer is exposed for an impl to echo. Because `factor_list`/`lone` are
uninterpreted, the proof reasons over an arbitrary `factor_list(poly)`, pinning
BOTH branches — so an impl cannot satisfy the spec by unconditionally returning a
single element or unconditionally materialising the recovery.

| # | model.py impl op (`ext_factor`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| 1 | `lc: int` parameter, carried through (the spec fixes the factor list; `lc` is not load-bearing) | `lc = dmp_ground_LC(f, u, K)` then `return lc, ...` | R | leading coefficient is an opaque scalar the function returns unchanged (mapping.md §2). |
| 2 | `poly: int` — the original polynomial's identity | `f` after `f = dmp_ground_monic(f, u, K)` / `F` (the original kept by `f, F = …, f`) | R | `Poly`/dense-`dmp` carrier ↔ opaque polynomial identity; `dmp_ground_monic` is a unit normalisation that does not change the factorisation (mapping.md §2). |
| 3 | `other = other_poly(poly)` | `f = dmp_sqf_part(f, u, K)` (the `f` of `f, F = dmp_sqf_part(f,u,K), f`) | A-consumed | `other_poly` is the weakest contract on `dmp_sqf_part` the proof needs: `Ensures(True)` — nothing is promised, in particular NOT that the polynomial has the same factor content. This is precisely why feeding it to the factoring (pre-patch) cannot discharge the postcondition. G-AX confirms `dmp_sqf_part` is genuinely factor-losing, so no stronger axiom is admissible (axiom_check.py §other_poly). |
| 4 | `images = factor_list(poly)` | `s, g, r = dmp_sqf_norm(F, u, K)` then `factors = dmp_factor_list_include(r, …)` + the recovery loop + `dmp_trial_division(F, factors, …)` | A-consumed | `factor_list(poly)` is the whole recovery pipeline applied to a polynomial: it reads back that polynomial's complete factor list. The model passes `poly` (the original) — the refinement image of `dmp_sqf_norm(F, …)` with `F` the original. The abstract, single-argument contract narrates no edit/diagnosis. G-AX checks faithfulness (completeness on the real pipeline via `factor(., extension=[I])`, 8/8) and that the factoring tracks its argument (axiom_check.py §factor_list). |
| 5 | the selection branch: `if len(images) <= 1: result = lone(poly)` else `result = images`, materialised into `result` by the loop | the `if len(factors) == 1: factors = [f]` / `else: recover each` branch (`factortools.py:1154-1163`), then `return lc, dmp_trial_division(F, factors, u, K)` | I + A | the branch is the identity transcription of the `len(factors)==1` selection: a single recovered element ⇒ the representative `f` as one element (`lone`, an A-consumed length-1 fallback, axiom_check.py §lone); ≥ 2 elements ⇒ the recovered list. For a splitting input (`len ≥ 2`) the else-branch returns the complete factorisation `factor_list(poly)`, and for a non-splitting input (`len == 1`) `lone(poly)` IS that lone factor. The list materialisation is `I`; the `List[int]`↔factor-list view is `R`. |

## Why the prepatch fails on the right clause (G-DIFF)

`model_prepatch.py` is byte-identical in spec (`same_spec == True`) and reproduces
the gold bug in its impl: it applies the factoring to the **related** polynomial,
`images = factor_list(other_poly(poly))` — the exact refinement image of the
pre-patch `dmp_sqf_norm(f, u, K)` with `f` the square-free part. Since
`other_poly`'s contract is `Ensures(True)` and `factor_list` relates nothing
across different arguments, the proof cannot conclude
`factor_list(other_poly(poly)) == factor_list(poly)`, so neither branch nor the
result is pinned to `factor_list(poly)`. Nagini reports the failure exactly on the
completeness clause `Implies(len(factor_list(poly)) >= 2, ToSeq(Result()) ==
factor_list(poly))` (`model_prepatch.py:93`) — the spec sensing the dropped
factor.

## No kind-3 (unexpressible-changed-op) steps

Every step is R, A, or I. The operation that genuinely *changed* — which
polynomial the recovery is applied to — is captured by the **argument of
`factor_list`**: `poly` (original) in `model.py` versus `other_poly(poly)`
(related/simpler) in `model_prepatch.py`, spelled out in the impl. `other_poly`,
`factor_list`, and `lone` all axiomatise UNCHANGED callees the function invokes
(`dmp_sqf_part`; the `dmp_sqf_norm`→`dmp_factor_list_include`→`dmp_trial_division`
recovery pipeline; the `factors = [f]` fallback); none axiomatises the changed
operation itself (the argument selection). No dead axiom: the proof of
completeness consumes `factor_list` (steps 4–5) and `lone` (step 5), and
`other_poly`'s deliberately-weak `Ensures(True)` is what makes the prepatch's
argument unable to discharge the postcondition (step 3, the differential witness).

## verify(model) ⇒ resolved

`ext_factor` verifies only if its returned factor list equals the input
polynomial's COMPLETE factoring — `factor_list(poly)` when that splits into ≥ 2
elements, the one-element `lone(poly)` otherwise — achieved only by applying the
recovery to the original (`factor_list(poly)`). By R (the `Poly`/`dmp` ↔ identity
/ factor-list refinement and the `dmp_ground_monic`/`lc` pass-throughs) this is
exactly the post-patch `dmp_ext_factor` computing `dmp_sqf_norm(F, …)` and
returning the complete factorisation through the selection branch. By G-AX the
real `dmp_sqf_part` is genuinely factor-losing (justifying `other_poly`'s weakest
`Ensures(True)`) and the real recovery pipeline (via `factor(., extension=[I])`)
returns the complete factor list of the polynomial it is applied to
(`factor_list`), completeness validated on distinct-factor products including the
issue's `(x−1)(y−1)` and the F2P `(x−Iy)(z−It)`. Therefore a model satisfying this
spec, refined by the map above, is the gold patch up to type refinement and
audited callees — and the gold patch resolves (G-RESOLVE). The trust points are
exactly the two of PLAN §1.1: axiom soundness (G-AX) and refinement fidelity
(this document, G-EQ).
