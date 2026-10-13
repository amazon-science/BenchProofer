# mapping.md — sympy__sympy-21596

## Instance
- repo: sympy/sympy
- base_commit: 110997fe18b9f7d5ba7d22f624d156a29bf40759
- spec_provenance: cold (derived from problem_statement + gold patch + base-commit
  source only)

## The logical change (one behavior)
`intersection_sets(ImageSet, Set)` for `other == S.Reals`
(`sympy/sets/handlers/intersection.py`, the `if other == S.Reals:` branch,
lines 279–322 @ base_commit). The branch keeps the parameters `n` of the image
family `{f(n) : n ∈ base_set}` whose value is real (imaginary part zero) and
defined (no denominator zero), then re-wraps with `imageset(lam, base_set)`.

The imaginary part `im` is a univariate expression in `n`; it vanishes iff some
factor of its numerator vanishes. The buggy code took `solve_linear` over
`Mul.make_args(im)`, bundled all the roots into ONE tuple `xis`, and *subtracted*
that finite set from `base_set` (`base_set -= FiniteSet(xis)`). Two defects:
1. **Wrong set op:** it SUBTRACTED the root set from `base_set`, whereas the
   parameters that make the value real are exactly the roots — they must be KEPT
   (intersection), not removed. Hence `2 ∈ S1.intersect(Reals)` returned `True`
   for `S1 = imageset(Lambda(n, n+(n-1)(n+1)I), ℤ)`: `2` is not a root, so it
   wrongly survived; and the genuine reals `{-1, 1}` were wrongly dropped.
2. **Root bundling:** zipping `solve_linear` results into a single `(x, xis)`
   tuple and one `FiniteSet(xis)` mishandles multi-factor / non-linear / fractional
   cases. The pole loop reused the imaginary-part `im` (a copy-paste bug) instead
   of the denominator `i`.

The gold fix introduces `_solution_union(exprs, sym)`: for each factor expr it
appends `FiniteSet(root)` if `solve_linear` solves it linearly, else
`ConditionSet(sym, Eq(expr,0))`, and returns the **Union** of all of them — i.e.
the zero set of the product (the set where SOME factor vanishes). The
imaginary-part handling becomes `base_set &= _solution_union(Mul.make_args(numer(im)), n)`
(INTERSECT) and the pole handling `base_set -= _solution_union(denoms(f), n)`
(DIFFERENCE).

Concretely (problem_statement): `S1 = imageset(Lambda(n, n+(n-1)(n+1)I), ℤ)`;
`2 ∈ S1.intersect(Reals)` must be `False`; `S1.intersect(Reals) == {-1, 1}`.

## Modeled function — the `other == S.Reals` branch of `intersection_sets`
| field | value |
|---|---|
| file @ base_commit | `sympy/sets/handlers/intersection.py` |
| function | `@dispatch(ImageSet, Set) intersection_sets(self, other)` (def at line 223; `if other == S.Reals:` branch at line 279) |
| pre-patch behavior | builds the surviving parameter set as `base_set - FiniteSet(roots)` (subtract) then a buggy pole loop using `im` |
| post-patch behavior | `base_set & _solution_union(numer(im) factors)` (intersect) then `base_set - _solution_union(denoms(f))` (subtract) |

Supporting facts from the source @ base_commit:
- `base_set = self.base_sets[0]` (line 231) — the parameter domain (e.g. `ℤ`).
- `lam = Lambda(n, re)` (line 295) and the final `return imageset(lam, base_set)`
  (line 322) — the family-building rule; UNCHANGED by the patch.
- `Mul.make_args(numer(im))` is the list of multiplicative factors of the
  numerator of `im`; the imaginary part is zero iff the numerator is zero iff
  some factor is zero — a UNION of the factors' zero sets.
- `denoms(f)` is the list of denominators of `f`; the value is undefined iff some
  denominator is zero — again a UNION of zero sets.
- `solve_linear(expr, 0, [sym])` returns `(sym, root)` when `expr` is linear in
  `sym` (so `{root}` is its zero set) and a non-`sym` first component otherwise
  (the `ConditionSet` fallback). In either case `_solution_union` yields exactly
  the zero set of the factor list; the FiniteSet/ConditionSet split is a
  representation detail of the SAME set.

## What is modeled vs. wrapped away
- **Modeled (the soundness-critical quantity):** the surviving parameter set
  `base_set` after the intersect-then-difference, expressed over the base
  parameter domain. This is exactly what the patch changes (which parameters
  survive).
- **Wrapped away:** the outer `imageset(lam, base_set)` re-wrapping. It is
  unchanged by the patch and is a monotone image map on the parameter set
  (`A ⊆ B ⇒ image A ⊆ image B`, and on the integer/rational base sets the lambda
  is applied pointwise), so two runs yield equal image sets iff their surviving
  parameter sets are equal up to the (unchanged) lambda. Modeling the parameter
  set exactly captures the full observable behavior of the fix without pulling in
  symbolic `ImageSet`/`Lambda` machinery.

## Lean ↔ Python type bijection (G-CONF / G-AX use this)
| Lean | Python | note |
|---|---|---|
| `base : Set ℚ` | `base_set = self.base_sets[0]` | the parameter domain; modeled as a `Set ℚ` (e.g. `Set.range ((↑):ℤ→ℚ)` for `S.Integers`) |
| `vanish : List (ℚ → ℚ)` | `Mul.make_args(numer(im))` | each factor of the imaginary-part numerator, as a function of the parameter |
| `poles : List (ℚ → ℚ)` | `denoms(f)` | each denominator factor of `f`, as a function of the parameter |
| `{x \| f x = 0}` | the zero set of a factor (`FiniteSet(root)` if linear, else `ConditionSet(sym, Eq(f,0))`) | both Python forms denote the SAME zero set |
| `zeroUnion fs` | `_solution_union(fs, sym)` = `Union(*[zero set of f for f in fs])` | union of the factors' zero sets |
| `(base ∩ zeroUnion vanish) \ zeroUnion poles` | `base_set &= _solution_union(numer(im)); base_set -= _solution_union(denoms(f))` | surviving parameters |
| `imageset(lam, ·)` | `return imageset(lam, base_set)` | the wrapped-away outer step |

### Note — `&=` (intersection) is the heart of the fix
The pre-patch code wrote `base_set -= FiniteSet(xis)` (difference); the gold writes
`base_set &= _solution_union(...)` (intersection). For the parameters that make the
value REAL the correct op is to KEEP the roots (intersection); the pole exclusion
correctly stays a DIFFERENCE. The prepatch Lean impl reproduces the bug by using
`base \ zeroUnion vanish` where the spec demands `base ∩ zeroUnion vanish`.

## Callee provenance / flag deps
- No separately-defined unchanged callee is consumed by the proof as an axiom.
  `_solution_union` / `numer` / `denoms` / `solve_linear` collectively compute the
  union of the factors' zero sets; this is modeled deeply by `zeroUnion` (an
  in-spec list computation, refinement.md tag R / A-reference), not axiomatized.
  `imageset` is the wrapped-away outer step and needs no contract.
- Flag/branch dependency: the modeled branch is `other == S.Reals` and reached
  only in the univariate case `ifree == {n}` with `im` not provably zero / nonzero.
  The Lean model takes the two factor lists directly, which is the post-`numer`/
  `denoms` decomposition that branch performs.

## G-CONF fuzz seed
Pinned seed: **21596** (used in `conformance_check.py`).
