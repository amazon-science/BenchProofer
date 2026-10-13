# mapping.md — scikit-learn__scikit-learn-12682

Binds every `model.py` symbol to its repository counterpart at
`base_commit = d360ffa7c5896a91ae498b3fb9cf464464ce8f34`, states the type
abstraction, and gives provenance for the modelled constants. There are no
`@ContractOnly` axioms in this bundle.

Repo file under change: `sklearn/decomposition/dict_learning.py` (plus a
cosmetic edit to the example `examples/decomposition/plot_sparse_coding.py`
that no test imports — see refinement.md §C).

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `encode_iteration_budget(algorithm, max_iter)` | `_sparse_encode(...)` — `sklearn/decomposition/dict_learning.py:32` (the `lasso_lars` branch builds `LassoLars(...)` at lines 127-130; the `lasso_cd` branch builds `Lasso(..., max_iter=max_iter, ...)` at lines 142-144) | modeled changed function (generic single-block coder): which iteration budget the constructed iterative-lasso solver receives |
| `coder_solver_budget(algorithm, max_iter)` | `sparse_encode(...)` — `dict_learning.py:187` (forwards `max_iter=max_iter` into `_sparse_encode` at lines 308-316 / 323-333) | modeled function (public coder): forwards the iteration budget to `_sparse_encode` |
| `Estimator` (model field `configured_max_iter`) | `SparseCodingMixin._set_sparse_coding_params` (`dict_learning.py:864`) + `SparseCoder.__init__` (`dict_learning.py:992`) — the repo field added is `transform_max_iter` | the estimator object; only the single touched field (model `configured_max_iter` ↔ repo `self.transform_max_iter`) is modelled |
| `coder_transform_budget(self, algorithm)` | `SparseCodingMixin.transform(self, X)` — `dict_learning.py:877` (the `sparse_encode(...)` call at lines 899-903) | modeled changed function (estimator transform path): end-to-end budget the built solver receives |
| `is_iterative_lasso(algorithm)` | the `algorithm == 'lasso_lars'` / `algorithm == 'lasso_cd'` branch tests (`dict_learning.py:120,136`) | pure spec: the two algorithms whose iteration budget is meaningful |
| `lars_builtin_default()` → `500` | `LassoLars.__init__` default `max_iter=500` — `sklearn/linear_model/least_angle.py:1086` | pure spec: the solver class's own built-in default (the value used pre-patch when the budget is not threaded into the `LassoLars` constructor) |
| `coder_param_default()` → `1000` | `_sparse_encode`/`sparse_encode` default `max_iter=1000` — `dict_learning.py:35,189` | pure spec: the coder routine's own parameter default (the value used pre-patch when transform does not forward the configured budget) |

Pre-patch repo facts the change removes / adds (for the refinement audit, not
referenced from the consumer spec view):
- `_sparse_encode`'s `lasso_lars` branch built `LassoLars(...)` WITHOUT
  `max_iter=max_iter` (`dict_learning.py:127-130`), so the solver silently used
  its class default `500`. The patch adds `max_iter=max_iter`.
- `SparseCodingMixin.transform` called `sparse_encode(...)` WITHOUT a `max_iter`
  argument (`dict_learning.py:899-903`), so the coder used its own default
  `1000`; the estimator had no `transform_max_iter` field at all. The patch adds
  the `transform_max_iter` field (threaded through
  `_set_sparse_coding_params`/`__init__`) and passes
  `max_iter=self.transform_max_iter` from `transform`.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `max_iter` / `transform_max_iter` / `method_max_iter` (int iteration budgets) | `int` | identity; modelled domain is `>= 1` (a positive iteration budget) |
| `algorithm` (the string selector `'lasso_lars' / 'lasso_cd' / 'lars' / 'omp' / 'threshold'`) | `int` selector: `0` = lasso_lars, `1` = lasso_cd, `2` = lars, `3` = omp, `4` = threshold | the two budget-bearing branches are exactly `{0, 1}` (`is_iterative_lasso`) |
| the constructed solver object (`LassoLars(...)` / `Lasso(...)`) and its later numerical `.fit` | the single `int` "iteration budget the constructor receives" | the solver constructor's only modelled effect is recording its `max_iter` argument; the iterative optimisation itself is NOT modelled (it is not what changed — the changed operation is purely which integer is passed). The F2P test observes convergence-vs-warning, which is a monotone function of exactly this configured budget. |
| `self.components_`, `transform_algorithm`, `n_jobs`, `positive_code`, `split_sign`, … (the estimator's other fields and the data array `X`) | omitted | untouched by the fix; modelling only the single touched field `transform_max_iter` keeps the skeleton minimal and faithful |

No `str` carriers are needed (the selector is an `int`), no floating-point
semantics are involved (iteration budgets are integers; the bug is
precision-independent), so no `--float-encoding` flag.

## 3. Axioms / callee provenance

None consumed. The fix calls solver constructors (`LassoLars`, `Lasso`) but the
*changed operation* is which integer iteration budget those constructors are
given — fully expressible as integer data flow — not any behaviour of the
solvers. Hence there is no `@ContractOnly` axiom and no A-reference deep model
of a library callee.

`axiom_check.py` (run by G-AX) still discharges an executable PROVENANCE check:
it introspects the real library signatures and asserts the two modelled
constants equal the library's actual defaults — `LassoLars.__init__`'s
`max_iter` default is `500` (`least_angle.py:1086`, the B2 prepatch value) and
`_sparse_encode`/`sparse_encode`'s `max_iter` default is `1000`
(`dict_learning.py:35,189`, the B1 prepatch value). These are the values the
pre-patch code silently fell back to; pinning them to the real library keeps
the differential witnesses faithful.
