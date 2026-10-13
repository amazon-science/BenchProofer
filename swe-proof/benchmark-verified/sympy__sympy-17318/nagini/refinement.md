# refinement.md — sympy__sympy-17318

The operation-by-operation correspondence between `model.py`'s implementation
(the `match_additive` impl region, the deep guard/depth folds in the `pure`
region, and the consumed `split_by_radicand_gcd` axiom) and `patch.diff` (the
gold patch). Each step is tagged **R** (type refinement), **A** (axiomatized
callee — **A-consumed**, the proof uses the axiom's `Ensures`; or **A-reference**,
a deep model validated == the real callee by axiom_check.py / G-AX), or **I**
(identical concrete operation). The claim: *any implementation that verifies
against this frozen spec, refined per the map below, is behaviourally equal to
the gold patch on the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The behavioural hunk — `_sqrt_match`, the `p.is_Add` branch (`sympy/simplify/sqrtdenest.py:159`)

Gold hunk:
```
- if all((x**2).is_Rational for x in pargs):
+ sqargs = [x**2 for x in pargs]
+ if all(sq.is_Rational and sq.is_positive for sq in sqargs):
      r, b, a = split_surds(p)
      res = a, b, r
      return list(res)
```

| # | model.py impl op (`match_additive`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `codes: List[int]` | `pargs = sorted(p.args, ...)`, the addend list of the `Add` `p` | R | each SymPy addend ↔ its integer category code; `len(pargs)` ↔ `len(codes)` (mapping.md §2–3). |
| A2 | `all_fast_facet(ToSeq(codes))` (the fold: every code ∈ {0,1}) | `all(sq.is_Rational and sq.is_positive for sq in sqargs)` over `sqargs = [x**2 for x in pargs]` | R + I | the deep fold spells out the post-patch guard: `code_fast_facet(c)` (`c==0 or c==1`, facet E) ⟺ `(x**2).is_Rational and (x**2).is_positive`; the `all(...)` quantifier is the front-recursive `all_fast_facet` (mapping.md §3). The two conjuncts of the guard are exactly the two real-world tests facet E packs. (The model-symbol name is abstract — "fast-path eligible" rather than "positive-rational square" — because that diagnosis is hints_text-only and would leak in the spec view, SPEC_GUIDE §6.) |
| A3 | `k = num_surds(ToSeq(codes))`; `return split_by_radicand_gcd(ToSeq(codes), k)` | `r, b, a = split_surds(p); res = a, b, r; return list(res)` | A-consumed | the unchanged helper is axiomatized: under `all_fast_facet` and `num_surds >= 1` it returns normally with a match whose value is an OPAQUE SPLIT outcome (`Result() != 1`, exact value unpinned). The proof consumes this `Ensures` to discharge the matcher's **grounded** fast-path postcondition `Implies(all_fast_facet and num_surds>=1, Result() == split_by_radicand_gcd(ToSeq(codes), num_surds(ToSeq(codes))))` — the result is pinned equal to the helper's own output, so it can be discharged ONLY by actually invoking the helper (a literal cannot be proved equal to the opaque value). The model establishes the axiom's `k >= 1` precondition from the spec's frame fact (A5). G-AX runs the real `split_surds` to confirm the axiom (mapping.md §4.1). |
| A4 | `if not any_has_depth(ToSeq(codes)): raise NoMatch()` else `return 1` | the depth-based fallback: `nmax = max(v, key=...)`; `if nmax[0] == 0: res = []` else build `(a, b, r**2)`; `return list(res)` (`sqrtdenest.py:166-208,215`) | R | the fallback is reached exactly when the guard is false (not every addend has facet E). `any_has_depth` ⟺ `nmax[0] != 0` (some addend carries facet N, `sqrt_depth >= 1`). No facet N → empty list `[]` (modeled as `NoMatch`); some facet N → a non-empty match produced by the DEPTH analysis, modeled as the marker `1` (which the opaque SPLIT outcome is constrained to differ from), discharging the matcher's `not all_fast_facet => Result()==1`. The concrete triple *contents* are not pinned (mapping.md §2); the producing *mechanism* is, plus — on the fast path — the helper's exact opaque output. |
| A5 | precondition `all_fast_facet(codes) ⇒ num_surds(codes) >= 1` | (no code — a frame property of a genuine `Add`) | R (frame fact) | a multi-term `Add` whose addends all have facet E always has ≥ 1 irrational square-root term (a pure-rational sum collapses to a `Number` and never reaches `p.is_Add`). This is the property that the imaginary input violates and that makes the fast path safe. Validated on the real `Add` by axiom_check.py (mapping.md §3). |

The discriminating content of the change — tightening the fast-path eligibility
facet (facet E) so a non-eligible addend no longer admits the fast path — lives
in `all_fast_facet` consuming `code_fast_facet` (`c==0 or c==1`, facet E only;
the underlying repo test is `(x**2).is_Rational and (x**2).is_positive`). The
pre-patch guard tested only the looser facet; `model_prepatch.py` reproduces
that (an inline loop admitting every code ≠ 3, i.e. every non-nested-or-eligible
addend including the non-eligible non-nested code 2) and **fails** the axiom
precondition `all_fast_facet(codes)` at the `split_by_radicand_gcd` call site —
exactly the spec sensing the bug (G-DIFF):

```
model_prepatch.py:197: The precondition of function split_by_radicand_gcd
might not hold. Assertion all_fast_facet(codes) might not hold.
```

For the imaginary input `4 + I` (codes `[0, 2]`): pre-patch admits it to the
fast path, where `num_surds == 0` ⇒ the real `split_surds` hands `_split_gcd` an
empty tuple ⇒ `IndexError`. Post-patch the guard is false, the depth fallback
runs, `any_has_depth` is false (both depths 0), and the result is the empty match
— precisely `_sqrt_match(4 + I) == []`.

## B. No second prepatch needed

There is a single independently-fixed behaviour (the guard on the `p.is_Add`
fast path); one `model_prepatch.py` exercises it. The `split_surds`/`_split_gcd`
helpers are not changed, so they are not separately modeled as fixed behaviours
— they are the axiomatized callee whose soundness G-AX checks.

## C. The radsimp.py hunk is docstring-only (no refinement step)

The gold patch's `radsimp.py` hunk changes only docstrings of `rad_rationalize`
and `split_surds` ("sum of terms whose squares are rationals" → "…positive
rationals"). It alters no executable behaviour, produces no operation in any
impl, and is not part of the verified skeleton. It merely *documents* the
positive-rational domain that the `split_by_radicand_gcd` axiom encodes
(mapping.md §1, §4.1). No R/A/I row is required for it.

## D. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A, or I. The one operation that genuinely *changed* —
the guard tightening the fast-path eligibility facet (the real test
`(x**2).is_Rational` to `(x**2).is_Rational and (x**2).is_positive`) — is modeled
**deeply** (the spelled-out per-addend facets and the `all_fast_facet` fold in
the `pure` region, step A2), not hidden behind an axiom about the function under
change. The only consumed axiom, `split_by_radicand_gcd` (**A-consumed**, step
A3), covers the **unchanged** callee `split_surds` the guarded code invokes; the
change never touches it — it only restricts who may call it.

## E. verify(model) ⇒ resolved

`match_additive` verifies only if (A2) it takes the fast path exactly when every
addend has facet E, (A3) it then calls the helper under the helper's
precondition (`all_fast_facet ∧ num_surds ≥ 1`, established via the frame fact
A5) **and returns the helper's own (opaque) output**, and (A4) otherwise falls
to the depth analysis, **returning the DEPTH marker 1** for a nested addend or
the empty match when no addend is nested. The grounded path-distinguishing
postcondition — fast path `Result() == split_by_radicand_gcd(ToSeq(codes),
num_surds(ToSeq(codes)))` (the OUTPUT of the modeled helper, an opaque value),
depth path `¬all_fast_facet ⇒ Result()==1` — closes the batch02 panel's DEFECT-1
(marker-collapse) AND the re-audit's residual hole (a fabricatable marker): an
impl that produces the match by the wrong mechanism — routing a fast-path input
through the depth analysis (returns 1, ≠ the helper output), returning a literal
on the guard-passing case (cannot prove the literal equals the opaque helper
output), or invoking the helper with the wrong `k` (violates `k == num_surds`) —
fails verification. Because the SPLIT value is opaque, the ONLY way to discharge
the fast-path clause is to actually call the helper. By R (addend ↔ code; match
↔ the helper's output / the depth marker; empty list ↔ `NoMatch`) the verified
matcher equals the gold
`_sqrt_match` `p.is_Add` branch on the tested inputs; by G-AX the real
`split_surds` meets the consumed axiom (A-consumed) and the frame fact holds on
real `Add`s. Therefore a model satisfying this spec, refined by the map above,
is the gold patch up to type refinement and the audited callee — and the gold
patch resolves (G-RESOLVE). The trust points are exactly the two of PLAN §1.1:
axiom soundness (G-AX) and refinement fidelity (this document, G-EQ).
