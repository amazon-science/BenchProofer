# refinement.md — sympy__sympy-24066

Operation-by-operation correspondence between `implementation_collectFunction`
(Solution.lean impl region) and `patch.diff` (the gold edit to the `Function`
branch of `UnitSystem._collect_factor_and_dimension`). Tags: **R** type
refinement · **A-consumed** proof uses an axiom · **A-reference** deep-modeled
callee validated == real callee by G-AX · **I** identical concrete op.

The patch adds a per-argument canonicalisation: each recursively-collected
argument dimension is replaced by the unit dimension `Dimension(1)` when the
dimension system regards it as dimensionless, otherwise kept. The scale-factor
component and the function reconstruction are unchanged. Modeling the branch as a
total function of the argument pairs `fds` exposes the difference: post-patch a
dimensionless-but-non-canonical dimension is reported as the unit dimension;
pre-patch the raw dimension is propagated (which later trips the `Add`
same-dimension comparison).

| # | `implementation_collectFunction` op | `patch.diff` / post-patch Python op | tag | note |
|---|---|---|---|---|
| 1 | `for fd in fds do …` | the list comprehension `[... for d in fds]` over `fds` | I | iterate the recursively-collected argument pairs |
| 2 | `if isDimensionless fd.2 then dims := dims ++ [dimOne]` | `Dimension(1) if self.get_dimension_system().is_dimensionless(d[1])` | R | `isDimensionless : Dim → Bool` ↔ `is_dimensionless`; `dimOne` ↔ `Dimension(1)`; this IS the fix (the discriminating clause) |
| 3 | `else dims := dims ++ [fd.2]` | `else d[1]` | I | non-dimensionless argument dimension kept verbatim |
| 4 | `{ factor := applyFunc func (fds.map Prod.fst), … }` | `expr.func(*(f[0] for f in fds))` | R/I | `applyFunc func (fds.map fst)` ↔ `expr.func(*scale_factors)`; unchanged, pinned to inputs |
| 5 | `return { factor := …, dims := dims }` | `return (expr.func(...), *dims)` | R | the returned tuple ↔ `FunctionResult` (head=`factor`, trailing components=`dims`) |

Every op is R or I. No op is A-consumed or A-reference:

- The changed decision (op 2/3 — the dimensionless canonicalisation) is modeled
  DEEPLY and structurally over the observable `fds`; SPEC_GUIDE §3 forbids
  axiomatizing a deeply-modeled changed op, so it is spelled out via `canonDim`.
- `isDimensionless` and `applyFunc` are UNCHANGED callees carried as opaque
  SIGNATURES (no `_prop` axiom). They appear identically in the spec (`canonDim`
  / `problem_spec.factor`) and the impl, so they cancel in the differential test
  and the proof consumes no property of them. Hence the `axioms` region declares
  only signatures and **G-AX skips**.
- `self._collect_factor_and_dimension(arg)` is the function under spec
  (recursive); its results are carried as the grounded input `fds`, not
  axiomatized (directive 7).

The spec leaves NO output component free: `result.factor` is pinned to
`applyFunc func (fds.map fst)` and `result.dims` to the element-wise
`canonDim`-map of the argument dimensions (directive 5 frame, directive 8
grounding).

## Pre-patch (the bug)

`Solution_prepatch.lean`'s impl reproduces the defect: the loop appends `fd.2`
(the raw argument dimension) with NO `isDimensionless` test, exactly the
pre-patch `*(d[1] for d in fds)`. Its `correct_collectFunction` cannot close: the
spec requires `result.dims = fds.map (canonDim ·.2)`, and for any argument whose
dimension is dimensionless but not literally the unit dimension (`isDimensionless
d = true`, `d ≠ dimOne`) the prepatch yields `d` where the spec demands `dimOne`.
This is precisely the observable failure behind `1 + exp(second/(ohm*farad))`
before the fix. (G-DIFF: the prepatch must fail G-VERIFY.)

## G-CONF (R/I differential)

`conformance_check.py` builds the Python shadow of the impl region (op-for-op,
with `is_dimensionless` modeled identically on both sides) and diffs it against
an in-process replica of the POST-PATCH branch over the edge corpus + ≥1e5
fuzzed `fds` lists; zero disagreements expected. Pinned seed 24066. The impl
region is NOT all-A-tagged (ops 2/3/5 are R), so `conf_skip = false`.
