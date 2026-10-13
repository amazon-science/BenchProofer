# mapping.md — scikit-learn__scikit-learn-12682

## Symbol binding (@ base_commit `d360ffa7c5`)
- File: `sklearn/decomposition/dict_learning.py`.
- `SparseCodingMixin._set_sparse_coding_params` (def @ line 864) — records the
  per-estimator coding options onto `self.*`. The gold patch adds a
  `transform_max_iter=1000` parameter and `self.transform_max_iter = transform_max_iter`
  (added @ line 873 in the patched file).
- `SparseCodingMixin.transform` (def @ line 879) — the encoding step. It builds
  the keyword-argument bundle passed to `sparse_encode(...)` (the underlying
  sparse-solver entry point) from `self.*`. The gold patch adds
  `max_iter=self.transform_max_iter` to that call (@ line 900–903 in base; the
  `max_iter=` kwarg is added by the patch).
- `SparseCoder.__init__` / `DictionaryLearning.__init__` /
  `MiniBatchDictionaryLearning.__init__` — each gains a `transform_max_iter=1000`
  constructor parameter forwarded into `_set_sparse_coding_params(...)`.
- Downstream, `sparse_encode` forwards `max_iter` to the per-algorithm solver:
  for `lasso_cd` → `Lasso(max_iter=max_iter, …)` (@ line ~145), and (also via the
  patch) for `lasso_lars` → `LassoLars(max_iter=max_iter, …)` (@ line 128). At
  base, `transform()` never supplies `max_iter`, so the solver runs at its own
  default (1000) regardless of what the user configured.

## Modeled value
The argument bundle the estimator hands to the underlying sparse-solver when it
encodes data, as a pure function of the construction-time options. Modeled
function: `codingSolverArgs`. The construction step (`_set_sparse_coding_params`)
and the encoding step's argument assembly (`transform`'s call to `sparse_encode`)
are composed into one pure config→solver-args map; the iteration budget reaching
the solver is the bit the fix restores.

## Lean ↔ Python type bijection (used by G-CONF)
| Python | Lean | bijection |
|---|---|---|
| `n_components : int` | `nComponents : Nat` | identity on ℕ |
| `transform_algorithm : str` (one of omp/lasso_lars/lasso_cd/lars/threshold) | `algorithm : Nat` | injective enum code 0..4 |
| `transform_n_nonzero_coefs : None\|int` | `nNonzeroCoefs : Option Nat` | `None↔none`, `k↔some k` |
| `transform_alpha : None\|float` | `alpha : Option Rat` | `None↔none`, identity on stored value |
| `split_sign : bool` | `splitSign : Bool` | identity |
| `n_jobs : None\|int` | `nJobs : Option Nat` | `None↔none`, `j↔some j` |
| `positive_code : bool` | `positive : Bool` | identity |
| `transform_max_iter : int` (→ `max_iter` kwarg of `sparse_encode`) | `maxIter : Nat` | identity on ℕ |

The solver-arg bundle `SolverArgs` mirrors the keyword arguments `transform()`
passes to `sparse_encode`: `algorithm`, `n_nonzero_coefs`, `alpha`, `max_iter`,
`n_jobs`, `positive`. (`X`, `dictionary` are data, not config; `check_input`,
`verbose` are not part of the modeled config→arg map and are omitted.)

## Callee provenance / flag deps
No consumed callee axiom and no A-reference. The two composed steps are field
storage + field reads, modeled directly (R/I). `sparse_encode` and the per-algorithm
solvers (`Lasso`/`LassoLars`) are NOT modeled — the bundle stops at the argument
boundary (what the estimator hands the solver), which is exactly what the fix and
the F2P test (`transform_max_iter=1` ⇒ ConvergenceWarning; `=2000` ⇒ none)
distinguish.

## G-CONF fuzz seed
Pinned seed: **12682**.
