# mapping.md — sympy__sympy-19040 (Velvet bundle)

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = b9179e80d2daa1bb6cba1ffe35ca9e6612e115c9` (sympy 1.6), states the
type abstraction, and gives the provenance of each axiom (callee source + the
exact behaviour the axiom encodes).

Repo file under change: `sympy/polys/factortools.py`.

> POLICY NOTE: under SPEC_GUIDE §0.7, the factoring operation — a self-contained
> library routine the changed function delegates to — is modelled as an
> axiomatised oracle validated executably by G-AX.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `extFactor (lc poly)` | `dmp_ext_factor(f, u, K)` — `sympy/polys/factortools.py:1138` (changed body line 1150; selection branch lines 1154-1163) | the modeled changed function (multivariate factorisation over an algebraic number field) |
| `otherPoly : Int → Int` *(axiom — A-consumed)* | `dmp_sqf_part(f, u, K)` — `sympy/polys/sqfreetools.py:229` (called at `factortools.py:1149` in `f, F = dmp_sqf_part(f, u, K), f`) | unchanged callee producing the related, simpler polynomial (the square-free part); the polynomial the pre-patch erroneously feeds to the recovery |
| `factorList : Int → List Int` *(axiom — A-consumed)* | the factor-recovery pipeline `dmp_sqf_norm(·, u, K)` (`sqfreetools.py:122`) → `dmp_factor_list_include(r, u, K.dom)` (`factortools.py:1331`, called :1152) → the recovery loop (:1157-1163) → `dmp_trial_division(F, factors, u, K)` (`factortools.py:103`, called :1165) | unchanged callee group: applied to a polynomial it reads back that polynomial's COMPLETE factor list. The PATCH changes only WHICH polynomial is passed to `dmp_sqf_norm` (line 1150). |
| `lone : Int → List Int`, `loneLen` *(axiom — A-consumed)* | the `factors = [f]` fallback at `factortools.py:1155` (the `len(factors) == 1` branch) | the single, un-split element the selection branch falls back to (a one-element list) |
| `lc : Int` | `lc = dmp_ground_LC(f, u, K)` — `densebasic.py:59`, returned at `factortools.py:1165` | leading coefficient, returned unchanged (opaque scalar) |
| `isConstant : Int → Bool` *(axiom — A-consumed)* | the guard `all(d <= 0 for d in dmp_degree_list(f, u))` — `factortools.py:1146`, whose body is `return lc, []` (:1147) | the shape test the function makes on its (monic) argument BEFORE any factoring: true exactly when the argument carries no positive degree in any generator. Its branch returns NO factors at all. Untouched by the patch. |
| `noRepeatedFactor : Int → Bool` *(axiom — A-consumed, used as the `require`)* | a property of the ARGUMENT `f` of `dmp_ext_factor` ITSELF: no irreducible factor occurs in it more than once, i.e. `gcd(f, ∂f/∂x₀, …, ∂f/∂x_u)` is a unit (exact in characteristic 0; the library's own main-generator-only approximation of the same test is `dmp_sqf_p(f, u, K)`, `sqfreetools.py:56`). Under it the recovery search reached from `factortools.py:1150` is guaranteed to reach a reportable image in FINITELY MANY steps | the property of the ARGUMENT that makes the recovery search terminate at all; it delimits the arguments on which the function is DEFINED (see §3.2). **It is NOT the search's per-step exit test `dmp_sqf_p(r, u, K.dom)` (`sqfreetools.py:160-167`), which is a predicate on the SHIFTED NORM at the current step rather than on the argument. Measured (G-AX §(10)): of the 5 multivariate calls the three graded tests that reach this operation make, 4 have a no-repeated-factor ARGUMENT but a non-square-free norm at step 0 (they exit at step 1) — 6 of the 8 calls recorded by the whole-module sweep — so materialising this axiom as the per-step test would place those calls OUTSIDE the domain. That reading is NOT a faithful materialisation of this axiom.** |
| `hasMainDegree : Int → Bool` *(axiom — A-consumed, used as the second `require`)* | the shape test behind the OTHER unbounded loop: `dmp_degree_list(f, u)[0] > 0`, the degree in the FIRST (main) generator, which decides whether `dmp_sqf_part` (`factortools.py:1149`) collapses to a unit and hence whether `dmp_trial_division`'s `while True` (`factortools.py:103-124`, reached from :1165) can ever exit | the second property of the ARGUMENT the function's ability to report a result depends on; with the row above it delimits the arguments on which the function is DEFINED (see §3.2). |

The patched body and its two relevant local names:
- `F` — the original monic polynomial (`f, F = dmp_sqf_part(f, u, K), f` keeps the
  pre-`sqf_part` value in `F`).
- `f` — after that assignment, the **square-free part** (a different,
  possibly-fewer-factor polynomial). The gold edit replaces `dmp_sqf_norm(f, …)`
  with `dmp_sqf_norm(F, …)` (which polynomial the recovery is applied to).
- The selection branch (`if len(factors) == 1: factors = [f]` else recover each)
  is the `lone` vs recovered-list choice; when the recovery collapses to a single
  element, the code returns the representative `f` as ONE element.

## 2. Type abstraction (R-refinements) — Lean ↔ Python bijection

| repo reality | Lean carrier | bijection |
|---|---|---|
| a polynomial (`Poly` / dense `dmp` list over the algebraic field `K`), as the function RECEIVES it (an expanded coefficient form, NOT a factor list) | an opaque polynomial identity `poly : Int` | each polynomial the F2P / PASS_TO_PASS extension tests exercise is assigned a distinct identity; the identity is NOT its factor list (so returning the input unchanged is NOT a factorisation) |
| the factorisation the function RETURNS (a list of factor polynomials) | `List Int` of distinct factor identities | a returned factorisation `[q₁,…,q_k]` ↔ the `List Int` of the `qᵢ`'s identities |
| `factorList poly` *(axiom)* | `List Int` — the complete factor list the unchanged factoring reads off `poly` | the factoring depends only on its argument; applying it to a different polynomial gives a different list |
| `dmp_ground_monic(f, u, K)` / the returned `lc` | a unit/scalar pass-through (identity on the factorisation; `lc : Int` returned unchanged) | making the polynomial monic and the ground LC do not add/remove factors; tests observe the factor list, not `lc` |
| the dense-representation parameters `u` (gens − 1) and the domain `K` | omitted | structural parameters that do not enter the factorisation property being specified |

`Poly`/`dmp` carriers and coefficient indexing are not Lean-expressible at the
fragment level used. The key faithfulness point: the INPUT (an expanded
polynomial identity) and the OUTPUT (a factor list) are DISTINCT values, so the
"answer encoded into the input" anti-pattern is avoided.

**No ungrounded answer-key oracle.** The postcondition is expressed PURELY
STRUCTURALLY over the two shape tests and the input-driven factoring
`factorList poly` (sequence equality and length only):
```
ensures isConstant poly = true → out = []
ensures isConstant poly = false → (factorList poly).length ≥ 2 → out = factorList poly
ensures isConstant poly = false → ¬ (factorList poly).length ≥ 2 → out = lone poly
```
`factorList` is NOT a hardcoded lookup the impl can echo — it is an A-consumed
axiom of a REAL unchanged callee (the recovery pipeline), validated by G-AX
(axiom_check.py): driving `factor(.,extension=[I])` under the GOLD body
reconstructs the original on re-expansion (complete, 8/8), and under the PREPATCH
body drops a factor (8/8). So an impl that materialises `factorList poly` (the
legitimate gold computation) is a genuinely RESOLVING refinement, whereas any
impl that does NOT produce the input's own factoring (echo, single blob,
off-by-one, the related polynomial, a constant, or applying the factoring to
`otherPoly poly`) cannot discharge the contract.

## 3. Modeled domain (every F2P / PASS_TO_PASS input shape)

`poly` is an UNINTERPRETED `Int` identity, so the proof reasons over an ARBITRARY
`factorList poly` and `lone poly`. The spec pins ALL THREE branches: the impl must
produce `[]` for a constant argument, `factorList poly` when the factoring has ≥ 2
elements, AND `lone poly` when it has ≤ 1 — no branch is vacuous, so an
unconditional single-element answer, an unconditional materialise-the-recovery
answer, and an unconditional empty answer are all rejected.

### 3.1 The empty (constant) case is MODELLED, not excluded

Before any factoring the real function tests the shape of its monic argument and,
if it has no positive degree in any generator, reports NO factors at all:
```
    if all(d <= 0 for d in dmp_degree_list(f, u)):     # factortools.py:1146
        return lc, []                                  # factortools.py:1147
```
This line is untouched by the patch and the behaviour is publicly reachable:
`Poly(2, x, y, extension=[I]).factor_list() == (2, [])`, and the repo's own unit
test asserts it (`sympy/polys/tests/test_factortools.py:477`,
`assert R.dmp_ext_factor(0) == (anp([]), [])`). It is also reachable for inputs
that are *not literally* constants, because `dmp_factor_list` strips
`dmp_terms_gcd` / `dmp_ground_primitive` before delegating, so the primitive part
handed to `dmp_ext_factor` can be a unit. The model therefore has an explicit
clause `ensures isConstant poly = true → out = []` and a matching early return in
the impl, rather than forcing a non-empty result for every argument. G-AX §(6)
measures the branch on the real callee under BOTH bodies and through the public
entry point.

### 3.2 The declared DOMAIN: two `require`s, one per unbounded loop

```
require noRepeatedFactor poly = true
require isConstant poly = false → hasMainDegree poly = true
```

`Solution.lean` declares `loom.semantics.termination "total"`, so every clause —
and the promise that the operation RETURNS AT ALL — is asserted only where the
function is claimed to be DEFINED. TWO unbounded loops stand between the entry
point and a result, and each contributes one half of the domain.

**(a) the shift search of `dmp_sqf_norm`** (`sqfreetools.py:160-167`, reached from
`factortools.py:1150`), which reports only once it reaches an image whose norm has
no repeated factor:
```
    while True:
        h, _ = dmp_inject(f, u, K, front=True)
        r = dmp_resultant(g, h, u + 1, K.dom)
        if dmp_sqf_p(r, u, K.dom):    # reportable image reached
            break
        else:
            f, s = dmp_compose(f, F, u, K), s + 1
```

The `require` is **not** that per-step test. The loop's exit condition is a
predicate on the SHIFTED NORM `r` at the current step; the DOMAIN condition is a
predicate on the ARGUMENT (no irreducible factor of it occurs twice —
`gcd(f, ∂f/∂x₀, …, ∂f/∂x_u)` a unit). The two are INEQUIVALENT, and only the
argument-level one is a domain: for an argument with no repeated factor only
finitely many shifts leave the norm non-square-free, so the loop exits after
finitely many steps; an argument in which some irreducible factor recurs keeps a
square in the norm at EVERY shift and the loop never exits. Measured over the
graded suite (G-AX §(10), a spy on `dmp_ext_factor` under the patched body): all 5
multivariate calls have a no-repeated-factor ARGUMENT, but only ONE of them exits
at step 0:

| graded test | u | degree list | coefficient domain | argument has no repeated factor? | norm square-free at step 0? | steps to exit |
|---|---|---|---|---|---|---|
| `test_issue_5786` (**F2P**) | 3 | `(1,1,1,1)` | `QQ<I>` | yes | yes | 0 |
| `test_factor` (×2) | 1 | `(2,2)` | `QQ<√2>` | yes | **no** | 1 |
| `test_factor_large` (×2) | 1 | `(2,2)` | `QQ<I>` | yes | **no** | 1 |

The whole-module sweep of §(8)/§(10) — every `test_*` of the graded module, a
superset of the graded list — records 8 multivariate calls, 6 of which exit only
at step 1; the five above are those made by the three graded tests that reach this
operation directly.

So materialising the axiom as the per-step exit test would push 4 of those 5 (6 of
the 8) graded calls OUT of the declared domain — vacating the contract exactly where
`test_factor` / `test_factor_large` discriminate — while the argument-level reading
stated by the axiom docstring keeps all 5 INSIDE. The axiom is bound to the
argument-level condition (§1, §4.5); G-AX §(10) re-measures this table and reports
a VIOLATION if any graded call fails the argument-level condition.

**(b) the trial division `while True`** (`factortools.py:103-124`, reached from
:1165), which divides by each recovered factor while the remainder is zero:
```
    while True:
        q, r = dmp_div(f, factor, u, K)
        if dmp_zero_p(r, u):
            f, k = q, k + 1
        else:
            break
```
When the `len(factors) == 1` branch (:1155) falls back to the representative
`f = dmp_sqf_part(…)` and that representative is a UNIT, the division is a FIXED
POINT (`dmp_div(f, 1) == (f, 0)`) and the loop never exits. `dmp_sqf_part` divides
by `gcd(f, ∂f/∂x₀)` — a derivative in the MAIN generator only — so it collapses to
a unit exactly when the argument has no main-generator degree, and keeps main
degree ≥ 1 when it has some. Hence the second `require`.

Measured facts (G-AX §(7)) — a DIRECT measurement of the real PATCHED callee, each
probe run in a FORKED CHILD with a hard wall-clock budget, since these loops
cannot be interrupted in-process:

| argument | inside the declared domain? | patched callee returns? |
|---|---|---|
| `2`, `1` | yes — constant, short-circuited (§3.1) | yes |
| `(x−1)(y−1)`, `(x+1)(y−1)`, `x−Iy`, `(x−1)(x+1)(y−1)`, `(xy−1)(y−1)`, `xy` | yes — main degree > 0, no repeated factor | yes |
| `(x−Iy)(z−It)` (**F2P**), `x²−2y²` over `√2` (**P2P**) | yes | yes |
| `(x−1)²(y−1)` | NO — main degree 2 but `(x−1)` twice (leg a) | **no**, not within the budget |
| `y−1` | NO — square-free but no main degree (leg b) | **no**, not within the budget |

So an UNCONDITIONAL termination claim would be UNSOUND, and NEITHER half of the
domain is decoration: each has a witness that satisfies the OTHER half and still
fails to return. Both conditions are decidable and observable on the real carrier
(`gcd(f, ∂f/∂x₀, …, ∂f/∂x_u)` a unit — exact in characteristic 0; and
`dmp_degree_list(f, u)[0] > 0`). A constant is EXEMPT from the second (the
implication's antecedent is false) and satisfies the first vacuously, so §3.1's
empty-factorisation clause lies INSIDE the domain.

Both halves are CONSERVATIVE, not tight, and G-AX §(9) measures that too:
`dmp_sqf_p` tests square-freeness of the NORM, so some arguments WITH a repeated
factor still exit the search (`(x−1)(y−1)²` exits after 1 shift and the callee
returns); and the unit collapse only becomes divergence when the recovery ALSO
collapses to a single element, so some arguments with no main degree still return
(`y(y−1)` does). Separating those cases would need statements about which
generator a repeated factor involves and how the norm of the argument factors —
stronger claims than the model can justify. Erring on the side of asking for more
only REMOVES obligations on arguments where the reference itself does not return;
it admits no rival (the eight G-PBT reject cases are each refuted at a point where
BOTH halves HOLD, and §3.3 measures that the graded behaviour stays inside).

### 3.3 The restriction retains the graded behaviour (no hidden discrimination)

Measured by G-AX §(8): a spy on `dmp_ext_factor` records every call made while
EVERY `test_*` of `sympy/polys/tests/test_polytools.py` runs — all 150 of them, a
SUPERSET of this instance's graded list (the check asserts it covers 149/149 of
the FAIL_TO_PASS + PASS_TO_PASS names), so the conclusion does not depend on how a
test happens to reach an algebraic-field factorisation. Result: **8 multivariate
calls, every one satisfying BOTH halves** of the domain — distinct degree lists
`(1,1,1,1)` (×2) and `(2,2)` (×6), so main degree 1 or 2 (> 0) in every case,
and none with a repeated factor — every graded input lies INSIDE the declared
domain. In particular the
F2P polynomial `(x − I·y)(z − I·t)` (`u = 3`,
degree_list `(1,1,1,1)`, so main degree 1) is square-free and non-constant, so it
lands on the
`isConstant poly = false → (factorList poly).length ≥ 2 → out = factorList poly`
clause — precisely the clause `Solution_prepatch.lean` cannot discharge (G-DIFF).
The narrowing therefore cannot hide the graded discrimination. Independently:
G-RESOLVE passes, i.e. the patched tree passes F2P + all 148 P2P tests, which it
could not do if a graded input drove the operation outside the terminating region.

The witness families (checked in axiom_check.py) cover every multivariate-extension
input shape the discriminating tests exercise:

| witness | repo input shape | which test exercises it |
|---|---|---|
| `(x−1)(y−1)` | expanded, `extension=[I]` | the issue / StackOverflow witness; the dropped-`y−1` regime |
| `(x−Iy)(z−It)` | expanded, `extension=[I]` | **F2P** `test_issue_5786` (the round-trip) |
| `x²−2y²` | `extension=sqrt(2)` | **P2P** `test_factor` — the discriminating proper factorisation |
| `(x−1)(y−1)(z−1)` | `extension=[I]` | a 3-factor multivariate extension product |
| irreducible | `extension=[I]` | **P2P** single-factor / `len==1` branch |

The F2P `test_issue_5786` is a *round-trip* (`expand(factor(expand(e),ext))==e`),
which a trivial length-one factorisation can pass; the discriminating power lives
in the PASS_TO_PASS suite (`test_factor` demands `x²−2y²` split into TWO factors
over `√2`). The spec pins the result to the COMPLETE input-driven factoring
(≥ 2 separate factors for a splitting input), closing the spec-too-weak hole.

## 4. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 4.1 `otherPoly` ↔ `dmp_sqf_part` (A-consumed)
**Callee:** `dmp_sqf_part(f, u, K)` (`sqfreetools.py:229`) returns the square-free
part `f / gcd(f, ∂f)` (monic). In the multivariate algebraic-field setting it can
DROP factor content: measured in-container, `dmp_sqf_part((x−1)(y−1))` has degree
list `(1,0)` — it has lost the `y` dependence entirely.
**Axiom (weakest sufficient):** `axiom otherPoly : Int → Int` with NO property —
the model promises NOTHING about the returned polynomial; in particular it is NOT
assumed to denote the same polynomial (same factor content) as its argument. This
weakest contract is exactly what makes the prepatch use of
`factorList (otherPoly poly)` unable to discharge the postcondition.
**Soundness check (G-AX):** `axiom_check.py` confirms the real `dmp_sqf_part` is
genuinely factor-losing (degree list `(1,0)` vs input `(1,1)`), so any axiom
stronger than "nothing promised" would be UNSOUND.

### 4.2 `factorList` ↔ `dmp_sqf_norm` → `dmp_factor_list_include` → `dmp_trial_division` (A-consumed)
**Callee group:** `dmp_sqf_norm(source, u, K)` (`sqfreetools.py:122`) returns
`s, g, r` with `g(x)=source(x − s·a)` and `r=Norm(g)` square-free over the ground
domain; `dmp_factor_list_include(r, u, K.dom)` (`factortools.py:1331`) factors `r`;
the recovery loop maps each factor back through `dmp_inner_gcd`/`dmp_compose`; and
`dmp_trial_division(F, factors, u, K)` (`factortools.py:103`) reads the
multiplicities off `F`. The factors recoverable are exactly the factors PRESENT
in the polynomial the recovery is applied to.
**Axiom (behaviour the proof needs):** `axiom factorList : Int → List Int` — an
abstract operation returning SOME determinate sequence as a function of its
argument (nothing relating different arguments). The contract narrates no edit and
no "use the original, not the reduced" diagnosis. The differential lives entirely
in the impl's choice of argument: `factorList poly` (post-patch, the full
polynomial) vs `factorList (otherPoly poly)` (pre-patch, the simpler one).
**Soundness check (G-AX):** `axiom_check.py`
  (a) **faithfulness / completeness:** toggles the one-token edit IN-PROCESS and
      drives the public `factor(expand(e), extension=[I])` entry point on 8
      square-free products of distinct factors (including the issue witness
      `(x−1)(y−1)` and the F2P polynomial `(x−Iy)(z−It)`); under the GOLD body the
      re-expanded factorisation reconstructs the original (8/8 complete);
  (b) **discrimination:** under the PREPATCH body the recovery from the
      square-free part DROPS a factor on 8/8 witnesses (`(x−1)(y−1) → x−1`), so the
      axiom genuinely discriminates gold from prepatch;
  (c) **argument load-bearing:** `dmp_sqf_norm(F)` → degree list `(2,2)` vs
      `dmp_sqf_norm(sqf_part)` → `(2,0)`, so the factoring tracks the factor
      content of its ARGUMENT.

### 4.3 `lone` / `loneLen` ↔ the `factors = [f]` fallback (A-consumed)
**Callee:** the `if len(factors) == 1: factors = [f]` fallback
(`factortools.py:1155`) — the recovered representative returned as a single
element.
**Axiom (weakest sufficient):** `axiom lone : Int → List Int` with
`axiom loneLen : ∀ p, (lone p).length = 1` — only that the fallback is a
one-element list; nothing about its contents. This length fact lets the
single-element branch discharge the `¬ (factorList poly).length ≥ 2` clause, while
the contents are NOT pinned to a hardcoded value.
**Soundness check (G-AX):** `axiom_check.py` confirms the real fallback
`factors = [f]` is a length-1 list, so `loneLen` is sound and nothing stronger is
assumed.

### 4.4 `isConstant` ↔ the `return lc, []` short circuit (A-consumed)
**Callee:** the guard `all(d <= 0 for d in dmp_degree_list(f, u))`
(`factortools.py:1146`) and its body `return lc, []` (:1147) — the shape test the
function makes on its monic argument before any factoring, and the branch in which
it reports no factors at all. Patch-independent (the gold hunk is at :1150).
**Axiom (weakest sufficient):** `axiom isConstant : Int → Bool` — a determinate
Boolean function of the argument, NOTHING else promised (in particular it is not
related to `factorList`, so the model cannot deduce anything about one from the
other). That is exactly enough to state the empty-factorisation clause and to let
the impl branch on it.
**Soundness check (G-AX §6):** `axiom_check.py` drives the real callee (both the
gold and the prepatch body — the branch is argument-independent) on constant
arguments `2` and `1` and measures `factors == []`; on the non-constant arguments
`(x−1)(y−1)` and `x·y` it measures a NON-empty list; and it repeats the
measurement through the public entry point
(`Poly(2, x, y, extension=[I]).factor_list() -> (2, [])`). So the clause
`isConstant poly = true → out = []` is faithful and `isConstant` is not a
disguised answer key.

### 4.5 `noRepeatedFactor` ↔ no repeated irreducible factor IN THE ARGUMENT (A-consumed; the `require`)
**Callee / quantity:** a property of the argument `f` of `dmp_ext_factor` itself,
not of anything computed from it: no irreducible factor occurs in it more than
once, decided exactly in characteristic 0 by `gcd(f, ∂f/∂x₀, …, ∂f/∂x_u)` being a
unit (`dmp_diff_in` + `dmp_gcd` + `dmp_ground_p`; the library's own
main-generator-only approximation of the same test is `dmp_sqf_p(f, u, K)`,
`sqfreetools.py:56`). It is the hypothesis of the classical fact behind the
algorithm (Trager): for an argument with no repeated factor only finitely many
shifts are bad, so `dmp_sqf_norm`'s unbounded search (`sqfreetools.py:160-167`,
reached from `factortools.py:1150`) terminates; with a repeated factor the norm
keeps a square at every shift and the search need never exit.
**Explicitly NOT the search's exit predicate.** That exit predicate,
`dmp_sqf_p(r, u, K.dom)`, tests the SHIFTED NORM at the current step, which is a
different function of the argument: measured, 4 of the 5 graded multivariate calls
made by the three tests that reach this operation (6 of the 8 recorded by the
whole-module sweep) have a no-repeated-factor argument and a NON-square-free norm
at step 0 (they exit at step 1) — see §3.2(a) and G-AX §(10). An impl that materialised the axiom that
way would treat those 4 calls as out-of-domain, which the axiom does not license.
**Axiom (weakest sufficient):** `axiom noRepeatedFactor : Int → Bool` — a
determinate Boolean function of the argument, nothing else promised. Used ONLY as
the method's `require`, i.e. to delimit the arguments on which the modeled
operation is claimed to be defined; it appears in no `ensures`.
**Soundness check (G-AX §7, §9):** §7 measures the CLAIM directly on the real
patched callee — every in-domain witness RETURNS, and `(x−1)²(y−1)` (main degree 2,
so it satisfies the OTHER half) does NOT return within the budget, so an
unconditional termination claim would be unsound and this `require` is necessary,
not decorative. Each probe runs in a forked child that is SIGKILLed at the budget;
the real loop hangs, so nothing unbounded is run in-process. §9 measures the
MECHANISM by replicating the `while True` with a HARD BOUND of 12 shifts: in-domain
witnesses exit after 0-1 shifts, `(x−1)²(y−1)` does not exit within the bound. A
constant satisfies the condition vacuously, so §4.4's clause is inside the domain.
**G-AX §8** additionally proves the restriction costs no discrimination: a spy
records every call made while every `test_*` of the graded module runs (149/149
graded names covered) and all 8 multivariate inputs satisfy BOTH halves (§3.3).
**G-AX §10** pins the BINDING itself: for every multivariate call the graded tests
drive it records the argument-level condition, the norm's square-freeness at step 0
and the number of steps the search actually takes, VIOLATING if any graded call
fails the argument-level condition and reporting how many the per-step reading would
exclude (currently 6 of the 8 the whole-module sweep records) — the measurement that distinguishes the two readings.

### 4.6 `hasMainDegree` ↔ the main-generator degree behind the trial division (A-consumed; the second `require`)
**Callee:** `dmp_degree_list(f, u)[0]`, the degree in the FIRST (main) generator of
the dense form — the quantity that decides whether
`f, F = dmp_sqf_part(f, u, K), f` (`factortools.py:1149`) collapses to a UNIT,
because `dmp_sqf_part` divides by `gcd(f, ∂f/∂x₀)`, a derivative in the MAIN
generator only. If it does collapse and the recovery reaches the
`len(factors) == 1` fallback (:1155), `dmp_trial_division`'s `while True`
(`factortools.py:103-124`, reached from :1165) divides by that unit forever:
`dmp_div(f, 1) = (f, 0)` is a fixed point of exactly that loop.
**Axiom (weakest sufficient):** `axiom hasMainDegree : Int → Bool` — a determinate
Boolean function of the argument, nothing else promised; in particular nothing
relates it to `factorList`, `lone` or `isConstant`, so it leaks no answer. Used
ONLY inside the method's second `require`, and only for NON-constant arguments
(`isConstant poly = false → hasMainDegree poly = true`); it appears in no
`ensures`.
**Soundness check (G-AX §7, §9):** §7 measures that the patched callee does NOT
return for `y−1` — square-free, so it satisfies the OTHER half of the domain —
while returning on every in-domain witness, so this `require` is necessary rather
than decorative. §9 measures the mechanism: `dmp_sqf_part` collapses to a unit for
`y−1`, `y²+1` and `y(y−1)` (main degree 0) and keeps main degree ≥ 1 for
`(x−1)(y−1)` and `xy`; and `dmp_div(f, 1) == (f, 0)`. §9 also records that the
condition is CONSERVATIVE (`y(y−1)` has no main degree yet returns, because its
recovery does not collapse to one element), so the `require` asks for more than is
strictly needed — a direction that removes obligations and admits no rival.
**Liveness (G-PBT):** `pos-control-main-degree-guard` is an impl whose `else` arm,
reachable exactly when a non-constant argument fails this `require`, returns a
value no `ensures` admits; it VERIFIES, which is the machine-checked statement that
the second half of the domain is genuinely assumed by the proof.

**In-container note (G-AX):** the real callees are sympy's own functions, so
`axiom_check.py` imports `sympy` (the repo worktree at `base_commit`, version
1.6) via `PYTHONPATH=$SCRATCH`. It uses the stable public
polynomial-ring API (`sympy.polys.ring(...).dmp_sqf_part / .dmp_sqf_norm /
.degrees()`) and the public `factor(...)` entry point. The completeness /
discrimination checks toggle the single-token edit IN-PROCESS (reconstructing
`dmp_ext_factor` with its module globals), so the check is self-contained and does
NOT depend on whether the worktree is at gold or prepatch.

## 5. G-CONF fuzz seed

conf_skip = true (impl region all-A-tagged; see conformance_check.py). Pinned seed
for any future shadow build: **19040**. Differential soundness is carried by G-AX
(axiom_check.py), not G-CONF.
