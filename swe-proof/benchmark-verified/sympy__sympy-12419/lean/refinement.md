# refinement.md — sympy__sympy-12419

Operation-by-operation correspondence between `implementation_identityElement`
(Solution.lean impl region) and `patch.diff` (the POST-PATCH `Identity._entry`).
Tags: **R** type refinement, **A-consumed** proof uses an axiom, **A-reference**
deep model validated == real callee, **I** identical concrete op.

| # | Lean impl op | patch.diff / post-patch Python op | tag |
|---|---|---|---|
| 1 | `match cmp with` (dispatch on the three-valued comparison status) | `eq = Eq(i, j)` then test `eq is S.true` / `eq is S.false` | R |
| 2 | `\| .known_equal => return .one` | `if eq is S.true: return S.One` | R |
| 3 | `\| .known_distinct => return .zero` | `elif eq is S.false: return S.Zero` | R |
| 4 | `match ind with` (nested dispatch, reached only on `.undetermined`) | evaluating `KroneckerDelta(i, j)` on the fall-through: `KroneckerDelta.eval` settles the pair or leaves it symbolic | R |
| 5 | `\| .settled_zero => return .zero` | `return KroneckerDelta(i, j)` where the constructor auto-evaluated to `S.Zero` | R |
| 6 | `\| .left_symbolic => return .deferred i j` | `return KroneckerDelta(i, j)` where the constructor returned a genuine term | R |

Notes:

- **Every step is R — no A, no I-with-callee.** The element decision is modeled
  DEEPLY over the two observable comparison outcomes (`IdxCmp`, `IndOutcome`) and
  the returned value is represented structurally (`Elem α`). SPEC_GUIDE §3 forbids
  axiomatizing a deeply-modeled changed decision, so the `axioms` region is empty
  and **G-AX skips**.
- The R tag is the *carried-observation* refinement, and there are TWO carried
  observations because the real method consults the index pair through two
  different mechanisms. `Eq(i, j)` with its `is S.true` / `is S.false` identity
  tests is one UNCHANGED upstream operation, whose trichotomous outcome enters as
  the `IdxCmp` input. `KroneckerDelta.eval` is the other: constructing the
  indicator runs its own settling procedure — a fuzzy `(i - j).is_zero` test AND a
  fermi-level branch on the operands' assumptions, which `Eq` has no analogue for —
  and may auto-evaluate the term to `S.Zero` before `_entry` returns it. That
  outcome enters as the `IndOutcome` input. Neither is re-derived in the model;
  both are unchanged by the patch (it imports `KroneckerDelta`, it does not modify
  it). The bijection is the `IdxCmp` / `IndOutcome` / `Elem` map in mapping.md.
- **Both observations are load-bearing, measured.** Over 6970 real index pairs the
  `undetermined` classification splits 4525 / 801 between a surviving symbolic
  indicator and one that settled itself to a plain zero, so a model over `IdxCmp`
  alone would predict a non-zero indicator on 801 pairs where the real method
  returns `S.Zero` (witness: `p` below-fermi, `q` above-fermi — `Eq(p, q)` is
  unevaluated while `_entry(p, q)` is `0`). No output component is left free:
  `result` is fully pinned to `elemOf cmp ind i j`, and crucially the undetermined
  case with a SURVIVING indicator is pinned to `deferred i j`, a value DISTINCT
  from `zero` — which is the arm the defect and the graded test both live on.
- The **fix itself** is ops #4–#6 together with the three-way split of op #1:
  base_commit's two-valued `if i == j: S.One else: S.Zero` collapses the
  known-distinct case AND both undetermined sub-cases to `S.Zero`. The post-patch
  code splits them, returning the deferred indicator in the undetermined case —
  where that indicator survives symbolically, which is the class the aggregation
  needs. The pre-patch impl (`Solution_prepatch.lean`) re-introduces the collapse
  as `match cmp with | .known_equal => .one | _ => .zero`, which is behaviourally
  identical to the buggy `if i == j` (every non-equal status yields `zero`,
  whatever the indicator delivered). It satisfies the spec on the `known_equal`,
  `known_distinct` and `undetermined`/`settled_zero` rows but VIOLATES it on the
  `undetermined`/`left_symbolic` row (`zero ≠ deferred i j`), so its
  `correct_identityElement` is unclosable (G-DIFF). Verified directly: the
  refutation `¬ problem_spec_identityElement .undetermined .left_symbolic 0 1
  (implementation_identityElement ...)` ELABORATES against the prepatch impl
  (exit 0) and fails against the frozen solution (exit 1).
- **G-CONF** mechanically refutes the R legs (no A legs): the Python shadow of the
  impl, driven by the two observations read off real SymPy objects, is diffed
  against the **REAL** patched `Identity._entry` over 120000 index pairs
  (`checked=120000 disagreements=0`, every modeled cell populated, including 11111
  in the `undetermined`/`settled_zero` cell). The oracle is the real callee rather
  than an in-process replica of the modeled decision — a replica tests the model
  against itself and is exactly how the earlier revision of this bundle drifted
  from the repo. Regression control: the one-observation shadow, run against the
  same oracle, is CAUGHT at the first fermi-level pair.
