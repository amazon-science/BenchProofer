# refinement.md — sympy__sympy-19040 (Velvet bundle)

Operation-by-operation correspondence between `Solution.lean`'s `extFactor` impl
region (plus the consumed axioms) and `patch.diff` (the gold patch). Each
step is tagged **R** (type refinement), **A-consumed** (axiomatised callee whose
behaviour the proof consumes), **A-reference** (axiomatised callee materialised
as the resolving computation), or **I** (identical concrete operation).

`patch.diff` is the gold patch **verbatim** (applies at `base_commit`; the real
correctness oracle, G-RESOLVE).

> POLICY NOTE: under SPEC_GUIDE §0.7, the factoring operation — a self-contained
> library routine the changed function delegates to — is modelled as an
> axiomatised oracle (`factorList`) validated executably by G-AX. The factoring
> op is therefore an **A-consumed** axiom, NOT a kind-3 unexpressible-changed-op.

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
polynomial and `f` its square-free PART (a possibly-fewer-factor polynomial). The
recovery `r` (whose factor list is read back and trial-divided against `F`) must
be built from `F`, not `f`; otherwise factors `f` has lost cannot be recovered,
and when the recovery collapses to a single element the selection branch returns
the representative `f` as ONE un-split factor (the issue: `factor((x-1)(y-1),
extension=[I])` returns `x - 1`, dropping `y - 1`).

### Carrier abstraction
`dmp_ext_factor` receives an EXPANDED polynomial (a dense coefficient form),
modelled by an opaque identity `poly : Int` (mapping.md §2). It returns a factor
list, modelled by `List Int` of factor identities. Input identity ≠ output factor
list, so echoing the input or returning it as a length-one list is NOT a valid
factorisation.

### Declared domain and the empty case (faithfulness of the contract's shape)
The modeled operation is TOTAL (`loom.semantics.termination "total"`), so its
clauses — and the promise that it RETURNS AT ALL — are asserted exactly where the
reference is defined. TWO unbounded loops stand between the entry point and a
result, so the domain has one half per loop:
```
require noRepeatedFactor poly = true
require isConstant poly = false → hasMainDegree poly = true
```
(a) The reference reaches a reportable image by the UNBOUNDED shift search in
`dmp_sqf_norm` (`sqfreetools.py:160-167`). The first `require` is the ARGUMENT-level
hypothesis under which that search is guaranteed to reach one (Trager: for an
argument with no repeated factor only finitely many shifts are bad); it is NOT the
search's per-step exit test `dmp_sqf_p(r, u, K.dom)`, which speaks about the SHIFTED
NORM at the current step and is a different function of the argument — measured, 4
of the 5 multivariate calls the three graded tests that reach this operation make
(6 of the 8 recorded by the whole-module sweep) have a no-repeated-factor argument
yet a non-square-free norm at step 0, and exit at step 1 (G-AX §10,
mapping.md §3.2(a)). Reading the `require` as the per-step test would put those 4
calls outside the domain and is not a faithful materialisation of the axiom, whose
docstring states a property of the argument as given. (b) It then reads
multiplicities off with
`dmp_trial_division` (`factortools.py:103-124`, reached from :1165), a `while True`
that divides while the remainder is zero; when the `len(factors) == 1` fallback
(:1155) hands it the representative `f = dmp_sqf_part(…)` and that representative
is a UNIT, `dmp_div(f, 1) = (f, 0)` is a FIXED POINT and the loop never exits.
`dmp_sqf_part` divides by `gcd(f, ∂f/∂x₀)` — a derivative in the MAIN generator
only — so it collapses to a unit exactly when the argument has no main-generator
degree. Hence the second `require`.

Measured DIRECTLY on the patched callee (G-AX §7, each probe in a forked child
SIGKILLed at a hard budget, since these loops cannot be interrupted in-process):
every in-domain witness RETURNS — the constants, six square-free products, the F2P
`(x − I·y)(z − I·t)` and the P2P `x² − 2y²` over `√2` — while `(x−1)²(y−1)` (main
degree 2, so it satisfies the second half) and `y−1` (square-free, so it satisfies
the first) do NOT return. So an unconditional termination claim would be UNSOUND
and NEITHER half is decoration; G-AX §9 measures the mechanism of each half, and
records that both are CONSERVATIVE (`(x−1)(y−1)²` has a repeated factor yet
returns; `y(y−1)` has no main degree yet returns), i.e. they ask for more than is
strictly needed — a direction that only removes obligations.

Both conditions are decidable on the real carrier, and a constant satisfies the
first vacuously while being EXEMPT from the second (the implication's antecedent is
false), so the empty-factorisation clause below lies INSIDE the domain. The
restriction costs no discrimination: every one of the 8 multivariate calls recorded
while every `test_*` of the graded module runs satisfies BOTH halves (G-AX §8,
mapping.md §3.3), including the F2P polynomial `(x − I·y)(z − I·t)` (degree list
`(1,1,1,1)`, so main degree 1, square-free).

**Faithful materialisation of the two `require`s** — the only readings the axioms
license, each a function of the ARGUMENT `f` that `dmp_ext_factor` receives (after
the unit normalisation `dmp_ground_monic`) and of nothing else:

| axiom | materialises as | NOT as |
|---|---|---|
| `noRepeatedFactor poly` | no irreducible factor of `f` occurs twice — exactly `gcd(f, ∂f/∂x₀, …, ∂f/∂x_u)` a unit (char 0); the library's main-generator-only approximation is `dmp_sqf_p(f, u, K)` | `dmp_sqf_p(r, u, K.dom)` on a NORM (`dmp_sqf_norm`'s per-step exit test), nor any property of `dmp_sqf_part(f)` |
| `hasMainDegree poly` | `dmp_degree_list(f, u)[0] > 0` | the main degree of `dmp_sqf_part(f)` or of any other derived value |

Both are decidable, both are computed from the argument alone, and both hold for
EVERY graded call (G-AX §8 and §10). An impl that guards its output with a
DIFFERENT predicate and returns something else where that predicate fails is not a
refinement of this contract: the two conditions above are the only hypotheses it
may assume, and they hold wherever the graded tests exercise the operation.

The reference also short-circuits before any factoring when its argument has no
positive degree in any generator (`factortools.py:1146-1147`,
`if all(d <= 0 …): return lc, []`, patch-independent and publicly reachable as
`Poly(2, x, y, extension=[I]).factor_list() == (2, [])`). That branch is MODELLED
rather than excluded: the contract carries its own clause and the impl its own
early return (step 3a below).

### Grounding of the postcondition (no answer-key oracle)
The contract is stated purely structurally over the two shape tests and the
input-driven factoring `factorList poly`:
```
ensures out = expectedFactors poly
ensures isConstant poly = true → out = []
ensures isConstant poly = false → (factorList poly).length ≥ 2 → out = factorList poly
ensures isConstant poly = false → ¬ (factorList poly).length ≥ 2 → out = lone poly
```
where `expectedFactors poly = if isConstant poly then [] else if
(factorList poly).length ≥ 2 then factorList poly else lone poly`. `isConstant`
and `noRepeatedFactor` are A-consumed axioms of two real, unchanged shape tests
the function performs on its argument (mapping.md §4.4/§4.5), each promising only
that it is a determinate Boolean function of the argument — neither is related to
`factorList`, so neither leaks an answer. `factorList` is an A-consumed axiom of the real, unchanged
recovery pipeline (mapping.md §4), NOT a hardcoded lookup. So materialising
`factorList poly` is the genuine, RESOLVING gold computation (the A-reference
exemplar pattern), while no opaque answer is exposed for an impl to echo. Because
`factorList`/`lone` are uninterpreted, the proof reasons over an arbitrary
`factorList poly`, pinning BOTH branches — an impl cannot satisfy the spec by
unconditionally returning a single element or unconditionally materialising the
recovery.

| # | `Solution.lean` impl op (`extFactor`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| 1 | `lc : Int` parameter, carried through (spec fixes the factor list; `lc` not load-bearing) | `lc = dmp_ground_LC(f, u, K)` then `return lc, ...` | R | leading coefficient is an opaque scalar returned unchanged (mapping.md §2). |
| 2 | `poly : Int` — the original polynomial's identity | `f` after `f = dmp_ground_monic(f, u, K)` / `F` (the original kept by `f, F = …, f`) | R | dense-`dmp` carrier ↔ opaque polynomial identity; `dmp_ground_monic` is a unit normalisation not changing the factorisation (mapping.md §2). |
| 2a | `require noRepeatedFactor poly = true` | **no irreducible factor occurs more than once IN THE ARGUMENT `f` of `dmp_ext_factor` itself** — exactly, in characteristic 0, `gcd(f, ∂f/∂x₀, …, ∂f/∂x_u)` a unit (the library's own main-generator-only approximation is `dmp_sqf_p(f, u, K)`, `sqfreetools.py:56`); the hypothesis under which the unbounded search of `dmp_sqf_norm` (`sqfreetools.py:160-167`, reached from `factortools.py:1150`) is guaranteed to reach a reportable image | A-consumed (domain) | the reference's factor recovery is an unbounded search; the modeled operation is total, so its domain excludes arguments for which that search is not guaranteed to reach an image it can report on. G-AX §7 measures the real patched callee: it does NOT return for `(x−1)²(y−1)` (which satisfies the OTHER half of the domain), so this half is necessary; §9 measures the mechanism (no exit within 12 shifts, vs 0-1 shifts in-domain). **NOT the search's per-step exit test `dmp_sqf_p(r, u, K.dom)`**, which speaks about the shifted NORM at the current step: measured, 4 of the 5 graded multivariate calls made by the three tests that reach this operation — 6 of the 8 recorded by the whole-module sweep — have a no-repeated-factor argument and a non-square-free norm at step 0 (they exit at step 1), so the per-step reading would place them outside the domain (G-AX §10, mapping.md §3.2(a)). |
| 2b | `require isConstant poly = false → hasMainDegree poly = true` | the main-generator degree behind the SECOND unbounded loop: `dmp_sqf_part` at `factortools.py:1149` (divides by `gcd(f, ∂f/∂x₀)`) feeding the `len(factors) == 1` fallback (:1155) into `dmp_trial_division`'s `while True` (`factortools.py:103-124`, called :1165) | A-consumed (domain) | with no main-generator degree the square-free part collapses to a UNIT, and dividing by a unit is a fixed point (`dmp_div(f, 1) = (f, 0)`), so the multiplicity loop never exits and no result is reachable. G-AX §7 measures that the real patched callee does NOT return for `y−1` (which satisfies the OTHER half), so this half is necessary; §9 measures the mechanism (unit collapse for `y−1`, `y²+1`, `y(y−1)`; main degree ≥ 1 kept for `(x−1)(y−1)`, `xy`; `dmp_div(f, 1) = (f, 0)`). A CONSTANT argument is exempt: it is reported before any of that begins (row 3a). G-PBT's `pos-control-main-degree-guard` verifies only because this half is assumed. |
| 3a | `if isConstant poly then return ([] : List Int)` | `if all(d <= 0 for d in dmp_degree_list(f, u)): return lc, []` (`factortools.py:1146-1147`) | I + A-consumed | identity transcription of the reference's own short circuit: a constant argument is reported with NO factors. `isConstant` is the weakest axiom for that guard (a determinate Boolean of the argument). G-AX §6 measures `[]` for constants and non-empty for non-constants, on both bodies and through `Poly(...).factor_list()`. |
| 3 | `let other := otherPoly poly` (computed, NOT fed to the factoring) | `f = dmp_sqf_part(f, u, K)` (the `f` of `f, F = dmp_sqf_part(f,u,K), f`) | A-consumed | `otherPoly` is the weakest contract on `dmp_sqf_part`: nothing promised — in particular NOT the same factor content. Exactly why feeding it to the factoring (prepatch) cannot discharge the postcondition. G-AX confirms `dmp_sqf_part` is genuinely factor-losing, so no stronger axiom is admissible (axiom_check.py §otherPoly). In the gold impl this value is bound (faithful to the `f, F = …` assignment) but, per the gold edit, NOT passed to the recovery. |
| 4 | `let images := factorList poly` | `s, g, r = dmp_sqf_norm(F, u, K)` then `factors = dmp_factor_list_include(r, …)` + recovery loop + `dmp_trial_division(F, factors, …)` | A-consumed (resolving / A-reference role) | `factorList poly` is the whole recovery pipeline applied to a polynomial: it reads back that polynomial's COMPLETE factor list. The model passes `poly` (the original) — the refinement image of `dmp_sqf_norm(F, …)` with `F` the original. The abstract single-argument contract narrates no edit. G-AX checks faithfulness (completeness via real `factor(.,extension=[I])`, 8/8) and that the factoring tracks its argument (axiom_check.py §factorList). |
| 5 | the selection branch `if images.length ≥ 2 then materialise images else materialise (lone poly)`, copied element-by-element by the backward `while` loop into `result` | the `if len(factors) == 1: factors = [f]` / `else: recover each` branch (`factortools.py:1154-1163`) then `return lc, dmp_trial_division(F, factors, u, K)` | I + A | identity transcription of the `len(factors)==1` selection: a single recovered element ⇒ representative `f` as one element (`lone`, an A-consumed length-1 fallback, axiom_check.py §lone); ≥ 2 elements ⇒ the recovered list. For a splitting input the else-branch returns `factorList poly`; for a non-splitting input `lone poly` IS that lone factor. The list materialisation (`drop`-fold loop) is `I`; the `List Int`↔factor-list view is `R`. |

## Why the prepatch fails on the right clause (G-DIFF)

`Solution_prepatch.lean` is byte-identical in spec (axioms + pure + pre/post
regions and the method signature; verified `diff`-clean) and reproduces the gold
bug in its impl: it computes `images := factorList (otherPoly poly)` — the exact
refinement image of the pre-patch `dmp_sqf_norm(f, u, K)` with `f` the square-free
part — and branches/materialises off THAT list. Since `otherPoly`'s contract
promises nothing and `factorList` relates nothing across different arguments, the
proof cannot conclude `factorList (otherPoly poly) = factorList poly`. Velvet
leaves the postcondition goals UNSOLVED exactly on the completeness clauses:
```
ensures_1: isConstant poly = false → ¬ (factorList poly).length ≥ 2 → out = lone poly
ensures_2: isConstant poly = false → (factorList poly).length ≥ 2 → out = factorList poly
ensures_4: out = expectedFactors poly
```
(`Solution_prepatch.lean` prove_correct) — the spec sensing the dropped factor.
The loop-body fold steps DO close (the bookkeeping is unaffected) and so does the
constant clause `ensures_3` (the twin keeps the same early return, since the
short-circuit line is not what the patch changes); only the completeness
obligations fail, which is the intended discriminating clause. Note that the
domain restriction does not rescue the twin. Both halves are hypotheses about
uninterpreted Booleans that relate nothing to `factorList`, so no `require` can
supply the missing equation `factorList (otherPoly poly) = factorList poly`; and
the graded input `(x − I·y)(z − I·t)` satisfies BOTH halves (square-free, main
degree 1), so the twin is refuted on an argument the graded tests actually drive
(mapping.md §3.3).

## No kind-3 (unexpressible-changed-op) steps

Every step is R, A, or I. The operation that genuinely *changed* — which
polynomial the recovery is applied to — is captured by the **argument of
`factorList`**: `poly` (original) in `Solution.lean` versus `otherPoly poly`
(related/simpler) in `Solution_prepatch.lean`, spelled out in the impl.
`otherPoly`, `factorList`, and `lone` all axiomatise UNCHANGED callees the
function invokes (`dmp_sqf_part`; the `dmp_sqf_norm`→`dmp_factor_list_include`→
`dmp_trial_division` recovery pipeline; the `factors = [f]` fallback); none
axiomatises the changed *control* itself (the argument selection lives in the
impl). No dead axiom: completeness consumes `factorList` (steps 4–5) and `lone`
(step 5, via `loneLen`), and `otherPoly`'s deliberately-weak contract is what
makes the prepatch's argument unable to discharge the postcondition (step 3).

## verify(model) ⇒ resolved

`extFactor` verifies only if, for every argument in the declared domain, its
returned factor list is the one the reference reports: EMPTY for a constant
argument, otherwise the input polynomial's COMPLETE factoring — `factorList poly`
when that splits into ≥ 2 elements, the one-element `lone poly` otherwise —
achieved only by applying the recovery to the original (`factorList poly`). By R
(the `dmp` ↔ identity / factor-list refinement and the `dmp_ground_monic`/`lc`
pass-throughs) this is exactly the post-patch `dmp_ext_factor`: the
`all(d <= 0 …): return lc, []` short circuit, then `dmp_sqf_norm(F, …)` and the
complete factorisation through the selection branch. By G-AX the real
`dmp_sqf_part` is genuinely factor-losing (justifying `otherPoly`'s weakest
contract), the real recovery pipeline (via `factor(.,extension=[I])`) returns the
complete factor list of the polynomial it is applied to (`factorList`, validated
8/8 GOLD-complete, 8/8 PREPATCH-drops), the constant branch really reports no
factors (§6), the declared domain is measured to be a region where the PATCHED
reference RETURNS with each half necessary (§7) and traceable to its own unbounded
loop (§9), and that domain contains every graded input (§8). §10 pins the BINDING
of the first half to the argument-level condition — the reading the axiom docstring
states — and measures that the alternative "the search exits at its first step"
reading would exclude 6 of the 8 graded multivariate calls it records, so it is not a faithful
materialisation of the axiom.

The domain restriction does not weaken the gate. It removes obligations only on
arguments where the patched reference itself does not return (measured, §7), and it
is confined to two `require`s — no `ensures` was dropped; on the contrary the
constant case ADDED one, and G-PBT's `weak-ignores-constant-guard` case (an impl
with no constant test — i.e. what an unrestricted contract demanded) is REJECTED.
Each half has its OWN liveness control: `pos-control-domain-guard` verifies only
because the first is assumed and `pos-control-main-degree-guard` only because the
second is, so neither is decoration. And the 8 rejected rival impls each bind BOTH
`noRepeatedFactor poly = true` and `hasMainDegree poly = true` in their witness and
discharge the method precondition from them (with the gate's consistency probe
required to FAIL), so the restricted contract is satisfiable and still refutes
every rival INSIDE the domain.

Therefore a model satisfying this spec, refined by the map above, is the gold patch
up to type refinement and audited callees — and the gold patch resolves
(G-RESOLVE). The trust points are axiom soundness (G-AX / axiom_check.py) and
refinement fidelity (this document, G-EQ).
