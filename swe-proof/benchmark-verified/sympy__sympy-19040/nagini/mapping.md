# mapping.md — sympy__sympy-19040

Binds every `model.py` symbol to its repository counterpart at
`base_commit = b9179e80d2daa1bb6cba1ffe35ca9e6612e115c9`, states the type
abstraction, and gives the provenance of each axiom (callee source + the exact
behaviour the axiom encodes).

Repo file under change: `sympy/polys/factortools.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `ext_factor(lc, poly)` | `dmp_ext_factor(f, u, K)` — `sympy/polys/factortools.py:1138` (changed body line 1150; selection branch lines 1154-1163) | the modeled changed function (multivariate factorisation over an algebraic number field) |
| `other_poly(poly)` *(axiom — A-consumed)* | `dmp_sqf_part(f, u, K)` — `sympy/polys/sqfreetools.py:229` (called at `factortools.py:1149` in `f, F = dmp_sqf_part(f, u, K), f`) | unchanged callee producing the related, simpler polynomial (the square-free part); the polynomial the pre-patch erroneously feeds to the recovery |
| `factor_list(poly)` *(axiom — A-consumed)* | the factor-recovery pipeline `dmp_sqf_norm(·, u, K)` (`sqfreetools.py:122`) → `dmp_factor_list_include(r, u, K.dom)` (`factortools.py:1331`, called :1152) → the recovery loop (:1157-1163) → `dmp_trial_division(F, factors, u, K)` (`factortools.py:103`, called :1165) | unchanged callee group: applied to a polynomial it reads back that polynomial's complete factor list. The PATCH changes only WHICH polynomial is passed to `dmp_sqf_norm` (line 1150). |
| `lone(poly)` *(axiom — A-consumed)* | the `factors = [f]` fallback at `factortools.py:1155` (the `len(factors) == 1` branch) | the single, un-split element the selection branch falls back to (a one-element list) |
| `lc` | `lc = dmp_ground_LC(f, u, K)` — `densebasic.py:59`, returned at `factortools.py:1165` | leading coefficient, returned unchanged (opaque scalar) |

The patched body and its two relevant local names:
- `F` — the original monic polynomial (`f, F = dmp_sqf_part(f, u, K), f` keeps the
  pre-`sqf_part` value in `F`).
- `f` — after that assignment, the **square-free part** (a different,
  possibly-fewer-factor polynomial). The gold edit replaces `dmp_sqf_norm(f, …)`
  with `dmp_sqf_norm(F, …)` (which polynomial the recovery is applied to).
- The selection branch (`if len(factors) == 1: factors = [f]` else recover each)
  is the `lone` vs recovered-list choice; when the recovery collapses to a
  single element, the code returns the representative `f` as ONE element.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| a polynomial (`Poly` / dense `dmp` list over the algebraic field `K`), as the function RECEIVES it (an expanded coefficient form, NOT a factor list) | an opaque polynomial identity `int` (`poly`, in the modeled domain `0..4`) | each polynomial the F2P / PASS_TO_PASS extension tests exercise is assigned a distinct identity; the identity is NOT its factor list (so returning the input unchanged is NOT a factorisation) |
| the factorisation the function RETURNS (a list of factor polynomials) | `List[int]` of distinct factor identities; specification phrased over `PSeq[int]` via `ToSeq` | a returned factorisation `[q₁,…,q_k]` ↔ the `List[int]` of the `qᵢ`'s identities |
| `factor_list(poly)` *(axiom)* | the complete factor list the unchanged factoring reads off `poly` | the factoring depends only on its argument; applying it to a different polynomial gives a different list |
| `dmp_ground_monic(f, u, K)` / the returned `lc` | a unit/scalar pass-through (identity on the factorisation) | making the polynomial monic and the ground LC do not add/remove factors; the tests observe the factor list, not `lc` |
| the dense-representation parameters `u` (gens − 1) and the domain `K` | omitted | structural parameters that do not enter the factorisation property being specified |

`Poly`/`dmp` carriers and coefficient indexing are not Nagini-expressible. The
key faithfulness point: the INPUT (an expanded polynomial identity) and the
OUTPUT (a factor list) are DISTINCT values, so the "answer encoded into the
input" anti-pattern is avoided — echoing the input, or returning it as a
length-one list, does not satisfy the contract.

**No ungrounded answer-key oracle.** The postcondition is expressed PURELY
STRUCTURALLY over the input-driven factoring `factor_list(poly)` (sequence
equality and length only):

```
Ensures(Implies(len(factor_list(poly)) >= 2, ToSeq(Result()) == factor_list(poly)))
Ensures(Implies(len(factor_list(poly)) <= 1, ToSeq(Result()) == lone(poly)))
```

`factor_list` is NOT a hardcoded lookup the impl can echo — it is an A-consumed
axiom of a REAL unchanged callee (the recovery pipeline), validated by G-AX
(axiom_check.py): driving `factor(.,extension=[I])` reconstructs the original on
re-expansion (complete, 8/8). So an impl that computes `factor_list(poly)` and
materialises it (the legitimate gold computation) is a genuinely RESOLVING
refinement — the exemplar A-reference pattern — whereas any impl that does NOT
produce the input's own factoring (echo, single blob, off-by-one, the related
polynomial, a constant, or applying the factoring to `other_poly(poly)`) cannot
discharge the contract. There is no opaque oracle in the spec signature for an
impl to read the answer from.

## 3. Modeled domain (every F2P / PASS_TO_PASS input shape)

The modeled domain `0 ≤ poly ≤ 4` covers every multivariate-extension input
shape the discriminating tests exercise, INCLUDING the input that fails first.
Because `factor_list` and `lone` are uninterpreted (the proof reasons over an
ARBITRARY `factor_list(poly)`), the spec pins BOTH branches: the impl must
produce `factor_list(poly)` when it has ≥ 2 elements AND `lone(poly)` when it has
≤ 1 — neither branch is vacuous, so an unconditional single-element answer or an
unconditional materialise-the-recovery answer is rejected.

| poly | repo input shape | which test exercises it |
|---|---|---|
| 0 | `(x−1)(y−1)` expanded, `extension=[I]` | the issue / StackOverflow witness; the dropped-`y−1` regime |
| 1 | `(x−Iy)(z−It)` expanded, `extension=[I]` | **F2P** `test_issue_5786` (the round-trip) |
| 2 | `x²−2y²`, `extension=sqrt(2)` | **P2P** `test_factor` (line 2423) — the discriminating proper factorisation |
| 3 | `(x−1)(y−1)(z−1)`, `extension=[I]` | a 3-factor multivariate extension product |
| 4 | an irreducible polynomial | **P2P** single-factor / `len==1` branch (`test_factor`, `test_sqf`) |

The F2P `test_issue_5786` is a *round-trip* (`expand(factor(expand(e),ext))==e`),
which a trivial length-one factorisation can pass; the discriminating power lives
in the PASS_TO_PASS suite (`test_factor` demands `x²−2y²` split into TWO factors
over `√2`). The spec therefore pins the result to the COMPLETE input-driven
factoring (≥ 2 separate factors for a splitting input), not merely completeness —
closing the spec-too-weak hole where `return poly` (an un-factored single blob)
verified.

## 4. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 4.1 `other_poly` ↔ `dmp_sqf_part` (A-consumed)
**Callee:** `dmp_sqf_part(f, u, K)` (`sqfreetools.py:229`) returns the
square-free part `f / gcd(f, ∂f)` (monic). In the multivariate algebraic-field
setting it can DROP factor content: measured in-container,
`dmp_sqf_part((x−1)(y−1))` has degree list `(1,0)` — it has lost the `y`
dependence entirely.
**Axiom (weakest sufficient):** `Ensures(True)` — the model promises NOTHING
about the returned polynomial; in particular it is NOT assumed to denote the
same polynomial (same factor content) as its argument. This weakest contract is
exactly what makes the pre-patch use of `factor_list(other_poly(poly))` unable
to discharge the postcondition (the proof cannot conclude
`factor_list(other_poly(poly)) == factor_list(poly)`).
**Soundness check (G-AX):** `axiom_check.py` confirms the real `dmp_sqf_part` is
genuinely factor-losing (degree list `(1,0)` vs input `(1,1)`), so any axiom
stronger than `Ensures(True)` (e.g. "same factor content") would be UNSOUND.

### 4.2 `factor_list` ↔ `dmp_sqf_norm` → `dmp_factor_list_include` → `dmp_trial_division` (A-consumed)
**Callee group:** `dmp_sqf_norm(source, u, K)` (`sqfreetools.py:122`) returns
`s, g, r` with `g(x)=source(x − s·a)` and `r=Norm(g)` square-free over the ground
domain; `dmp_factor_list_include(r, u, K.dom)` (`factortools.py:1331`) factors
`r`; the recovery loop maps each factor back through `dmp_inner_gcd`/`dmp_compose`;
and `dmp_trial_division(F, factors, u, K)` (`factortools.py:103`) reads the
multiplicities off `F`. The factors recoverable are exactly the factors PRESENT
in the polynomial the recovery is applied to.
**Axiom (behaviour the proof needs):** the model declares `factor_list(poly)` an
abstract `@Pure @ContractOnly` operation — it returns SOME determinate sequence
as a function of its argument (nothing relating different arguments). The
contract narrates no edit and no "use the original, not the reduced" diagnosis.
The differential lives entirely in the impl's choice of argument:
`factor_list(poly)` (post-patch, the full polynomial) vs
`factor_list(other_poly(poly))` (pre-patch, the simpler polynomial).
**Soundness check (G-AX):** `axiom_check.py`
  (a) **faithfulness:** drives the public entry point `factor(expand(e),
      extension=[I])` (which post-patch applies the recovery to the FULL
      polynomial `F`) on 8 square-free products of distinct factors — including
      the issue witness `(x−1)(y−1)` and the F2P polynomial `(x−Iy)(z−It)` — and
      asserts the re-expanded factorisation reconstructs the original
      (completeness: nothing dropped). This is what makes
      `return factor_list(poly)` a genuinely RESOLVING refinement (the A-reference
      exemplar pattern), not an echo of an opaque answer key;
  (b) **argument load-bearing:** building the recovery from the square-free PART
      collapses a resultant variable (`dmp_sqf_norm(sqf_part)` → degree list
      `(2,0)` vs `dmp_sqf_norm(F)` → `(2,2)`), so the factoring tracks the factor
      content of its ARGUMENT — applying it to `other_poly(poly)` yields a
      strictly smaller list (drops `y−1`).

### 4.3 `lone` ↔ the `factors = [f]` fallback (A-consumed)
**Callee:** the `if len(factors) == 1: factors = [f]` fallback
(`factortools.py:1155`) — the recovered representative returned as a single
element.
**Axiom (weakest sufficient):** `Ensures(len(Result()) == 1)` — the model
promises only that the fallback is a one-element list; nothing about its
contents. This length fact is what lets the single-element branch discharge the
`len(factor_list(poly)) <= 1` clause, while the contents are NOT pinned to any
hardcoded value (so `return [poly]` / `return [other_poly(poly)]` / a constant do
NOT satisfy the contract).
**Soundness check (G-AX):** `axiom_check.py` confirms the real fallback
`factors = [f]` is a length-1 list, so `Ensures(len(Result()) == 1)` is sound and
nothing stronger is assumed.

**In-container note (G-AX):** the real callees are sympy's own functions, so
`axiom_check.py` imports `sympy` (the repo at `base_commit`, version `1.6`). It
uses the stable public polynomial-ring API (`sympy.polys.ring(...).dmp_sqf_part /
.dmp_sqf_norm / .dmp_factor_list_include` and `.degrees()`) and the public
`factor(...)` entry point. **`axiom_check.py` MUST be run with `apply_gold=True`
(post-patch worktree):** at `base_commit` `factor(.,extension=[I])` routes through
the buggy `dmp_ext_factor` and would report a spurious completeness violation;
under the gold patch it applies the recovery to `F` and is complete (validated:
8/8). The factor-losing and load-bearing structural facts (4.1, 4.2b) use the
dense API directly and are stable across the 1.5/1.6 sympy. Repeated-factor
inputs route through an expensive resultant in 1.6 and are intentionally
excluded; the dropped-factor phenomenon is about the DISTINCT-factor set, fully
exercised by the square-free witnesses.
