# refinement.md — scikit-learn__scikit-learn-12682

The operation-by-operation correspondence between `model.py`'s implementations
(`encode_iteration_budget`, `coder_solver_budget`, `estimator_encode_budget`,
and the `Estimator` field) and `patch.diff` (the gold patch). Each step is
tagged **R** (type refinement), **A-consumed** (proof uses an axiom's Ensures),
**A-reference** (a deep model validated == the real callee by G-AX), or **I**
(identical concrete operation). The claim: *any implementation that verifies
against this frozen spec, refined per the map below, is behaviourally equal to
the gold patch on the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies cleanly at
`base_commit` — checked — and is the real correctness oracle, G-RESOLVE).

This fix has **no axiomatized callees** and **no A-reference deep model of a
library callee**: the changed operation is pure integer parameter propagation,
spelled out directly. Every step below is therefore **R** or **I**.

## A. Site B2 — the generic coder builds the least-angle solver with the budget

`encode_iteration_budget` models `_sparse_encode` (`dict_learning.py:32`).
Gold hunk (`dict_learning.py:127-130`):
```
  lasso_lars = LassoLars(alpha=alpha, fit_intercept=False,
                         verbose=verbose, normalize=False,
                         precompute=gram, fit_path=False,
-                        positive=positive)
+                        positive=positive, max_iter=max_iter)
```
(The `lasso_cd` branch already passed `max_iter=max_iter` to `Lasso` —
`dict_learning.py:142-144` — and is unchanged.)

| # | model.py impl op (`encode_iteration_budget`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | param `algorithm: int` (`0`=lasso_lars, `1`=lasso_cd) | the string `algorithm` and its `== 'lasso_lars'` / `== 'lasso_cd'` branch tests | R | int selector ↔ string selector (mapping.md §2); `is_iterative_lasso` ↔ `algorithm in {'lasso_lars','lasso_cd'}`. |
| A2 | param `max_iter: int` | the `max_iter` parameter of `_sparse_encode` | R | int ↔ int (identity). |
| A3 | `if algorithm == 0: budget = max_iter` | `LassoLars(..., max_iter=max_iter)` | I + R | the constructed least-angle solver receives `max_iter`; the model's "iteration budget the constructor receives" is exactly the `max_iter` argument bound on the `LassoLars` constructor (mapping.md §2 solver-budget abstraction). |
| A4 | `else: budget = max_iter` | `Lasso(..., max_iter=max_iter, ...)` (unchanged hunk) | I + R | the coordinate-descent solver already received `max_iter`; identical pre/post. |
| A5 | `return budget` | the solver is then `.fit`; its iteration count is the configured budget | R | the F2P test observes only convergence-vs-warning, a monotone function of the configured budget; the budget is what the fix changes. |

Pre-patch skeleton (`model_prepatch_2.py`): A3 becomes
`budget = lars_builtin_default()` (`500`) — the missing-`max_iter` constructor,
which silently used `LassoLars`'s class default. It **fails** the postcondition
`Result() == max_iter` (any `max_iter != 500`). That is the spec sensing B2
(G-DIFF).

## B. Site B1 — the estimator transform path forwards the configured budget

`estimator_encode_budget` models `SparseCodingMixin.transform`
(`dict_learning.py:877`); the `Estimator.configured_max_iter` field (model
symbol) models the repo field `transform_max_iter` added by
`_set_sparse_coding_params`/`__init__`; `coder_solver_budget` models
`sparse_encode` (`dict_learning.py:187`).

Gold hunks:
```
# transform() call (dict_learning.py:899-903):
  code = sparse_encode(
      X, self.components_, algorithm=self.transform_algorithm,
      n_nonzero_coefs=self.transform_n_nonzero_coefs,
-     alpha=self.transform_alpha, n_jobs=self.n_jobs,
-     positive=self.positive_code)
+     alpha=self.transform_alpha, max_iter=self.transform_max_iter,
+     n_jobs=self.n_jobs, positive=self.positive_code)

# _set_sparse_coding_params + __init__: add `transform_max_iter` parameter and
#   `self.transform_max_iter = transform_max_iter`.
```

| # | model.py construct | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1 | `Estimator.__init__` stores `self.configured_max_iter = configured_max_iter` (model field) | `_set_sparse_coding_params(..., transform_max_iter=1000)` sets `self.transform_max_iter = transform_max_iter`; `SparseCoder.__init__`/`DictionaryLearning.__init__`/`MiniBatch…__init__` thread the new `transform_max_iter` argument into it | I + R | identical store of the single touched field (model `configured_max_iter` ↔ repo `transform_max_iter`); the omitted estimator fields are untouched (mapping.md §2). |
| B2 | `coder_solver_budget(algorithm, max_iter)` returns `encode_iteration_budget(algorithm, max_iter)` | `sparse_encode` forwards `max_iter=max_iter` into `_sparse_encode` (`dict_learning.py:308-316`/`323-333`) | I + R | pure forwarding; the caller's spec uses the callee's spec (a modeled function, not an axiom). |
| B3 | `estimator_encode_budget` calls `coder_solver_budget(algorithm, self.configured_max_iter)` | `transform` calls `sparse_encode(..., max_iter=self.transform_max_iter, ...)` | I + R | the transform path forwards the configured field as the budget; `Result() == self.configured_max_iter` (model) ↔ the threaded `self.transform_max_iter` (repo) is the end-to-end guarantee. |

Pre-patch skeleton (`model_prepatch.py`): B3 becomes
`coder_solver_budget(algorithm, coder_param_default())` (`1000`) — `transform`
did not forward `max_iter`, so `sparse_encode`'s own default `1000` was used and
the configured value was dropped. It **fails** the postcondition
`Result() == self.configured_max_iter` (any configured value `!= 1000`). That is
the spec sensing B1 (G-DIFF), and B1 is exactly the path the F2P
`test_max_iter` exercises (`transform_algorithm='lasso_cd'`,
`transform_max_iter=1` vs `2000`, via `SparseCoder(...).fit_transform`).

## C. The example-file hunk (no tested behaviour)

The gold also edits `examples/decomposition/plot_sparse_coding.py`'s
`ricker_function` (a parenthesisation fix: `np.pi ** 1 / 4` → `np.pi ** .25`).
That module is an example script imported by no test; `test_max_iter` defines
its own local `ricker_function`. The hunk is cosmetic w.r.t. resolution and is
carried verbatim in `patch.diff` for fidelity to the gold. It is not modelled
(nothing observable depends on it).

## D. No kind-3 (unexpressible-changed-op) steps

Every step above is R or I. The changed operation — *which integer iteration
budget the constructed solver receives, threaded from the estimator field
through the two coder layers* — is integer data flow, modelled directly
(no axiom, no deep callee model). There is therefore no kind-3 step and no
`@ContractOnly` to over-claim. `axiom_check.py` discharges only the executable
PROVENANCE of the two prepatch fallback constants (`500`, `1000`) against the
real library (mapping.md §3).

## E. verify(model) ⇒ resolved

`encode_iteration_budget` verifies only if the built least-angle solver
receives `max_iter` (A3), and `estimator_encode_budget` verifies only if the
transform path forwards the estimator's configured budget end-to-end
(`Result() == self.configured_max_iter`, B3). By R (int ↔ int, int selector ↔
string selector, "iteration budget the constructor receives" ↔ the solver's
`max_iter` constructor argument) the verified skeleton equals the gold patch's
data flow on the tested inputs. The gold patch resolves (G-RESOLVE). There are
no trust points beyond the type refinement audited in this document (G-EQ): no
axiom soundness obligation, since no callee behaviour is relied upon.
