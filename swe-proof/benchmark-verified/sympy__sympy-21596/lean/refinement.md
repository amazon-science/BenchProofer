# refinement.md — sympy__sympy-21596

Operation correspondence between `implementation_realParams` (Solution.lean impl
region) and `patch.diff` (the gold edit to the `other == S.Reals` branch of
`intersection_sets(ImageSet, Set)`). Every row is tagged **R** (type refinement),
**A-consumed** (proof uses an axiom), **A-reference** (deep model validated ==
real callee by G-AX), or **I** (identical concrete op).

The modeled quantity is the *surviving parameter set* `base_set` after the
intersect-then-difference. The outer `imageset(lam, base_set)` is unchanged and is
a monotone image map on the parameter set, so equal surviving parameter sets ⟺
equal image sets (up to the unchanged lambda). Modeling the parameter set exactly
captures the patch's full observable effect (which parameters survive).

| # | impl op (Lean) | patch.diff counterpart (Python) | tag | note |
|---|---|---|---|---|
| 1 | `for f in vanish do sols1 := sols1 ∪ {x \| f x = 0}` (init `sols1 := ∅`) | `_solution_union(Mul.make_args(numer(im)), n)` = `Union(*[FiniteSet(root) or ConditionSet(Eq(f,0)) for f in factors])` | R / A-reference | `zeroUnion vanish` is the union of the factors' zero sets. The Python `FiniteSet(root)` vs `ConditionSet(Eq(f,0))` split is just a representation of one factor's zero set `{x \| f x = 0}`; the union over the factor list is the same set either way. `numer(im)` factors ↔ `vanish : List (ℚ→ℚ)`. |
| 2 | `let mut base_set := base ∩ sols1` | `base_set &= _solution_union(numer(im) factors, n)` | I | the `&=` intersection — the corrected op. KEEP the parameters that make the value real. `base : Set ℚ` ↔ `self.base_sets[0]`; `∩` ↔ `&=`. |
| 3 | `for d in poles do sols2 := sols2 ∪ {x \| d x = 0}` (init `sols2 := ∅`) | `_solution_union(denoms(f), n)` | R / A-reference | `zeroUnion poles` is the union of the denominator factors' zero sets, same construction as row 1. `denoms(f)` ↔ `poles : List (ℚ→ℚ)`. |
| 4 | `base_set := base_set \ sols2` | `base_set -= _solution_union(denoms(f), n)` | I | the `-=` difference — exclude parameters that make a denominator vanish (value undefined). `\` ↔ `-=`. |
| 5 | `return base_set` | the `base_set` handed to `imageset(lam, base_set)` | R | the surviving parameter set; `imageset` is the wrapped-away outer step (not modeled as an op — see header). |

## Coverage of the gold's branch structure
The gold `_solution_union` produces, per factor, a `FiniteSet(root)` (linear,
`solve_linear` succeeds with `x == sym`) or a `ConditionSet(sym, Eq(expr, 0))`
(non-linear / unsolved), then unions them. Both are representations of the
factor's zero set `{x | f x = 0}`; `zeroUnion` models the union of those zero
sets directly, so the single Lean construction covers both the FiniteSet branch
(linear factors — the F2P `(n-1)(n+1)` case → `{-1, 1}`) and the ConditionSet
branch (e.g. `n**2 - n/2 - 1/2` → an `ImageSet(... ConditionSet ...)`), because in
both cases the *set* of surviving parameters is identical. The two call sites
(imaginary part via `&=`, denominators via `-=`) are rows 1–2 and 3–4
respectively.

G-CONF (conformance_check.py) mechanically refutes any divergence over ≥10⁵
fuzzed `(base, vanish, poles)` inputs spanning linear and higher-degree factors,
empty factor lists, and overlapping vanish/pole roots; zero disagreements.

## Axioms
None. No `axiom <callee>_prop` is consumed (axiom_check.py is a skip stub). The
factor zero-set union (`_solution_union` / `numer` / `denoms` / `solve_linear`) is
modeled deeply by `zeroUnion`, and `imageset` — the only unchanged callee in the
returned line — is modeled away rather than axiomatized.

## No changed-inexpressible op
Every changed op (the `&=` intersection that replaced the buggy `-=`, the
`_solution_union` factor-union, the pole `-=`) is modeled deeply as a concrete set
computation. Nothing the patch changes is axiomatized.
