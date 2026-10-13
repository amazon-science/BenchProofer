# refinement.md — scikit-learn__scikit-learn-12682

Maps every operation in `implementation_codingSolverArgs` to its `patch.diff`
counterpart. Tags: **R** type-refinement, **A-consumed** proof uses a callee
axiom, **A-reference** deep-modeled changed op validated == real callee, **I**
identical concrete op.

## Patch (behavioral hunks)
The behavioral content of the gold patch threads a configured iteration budget
from the constructor down to the underlying sparse-solver:

```python
# _set_sparse_coding_params gains a transform_max_iter parameter, stored:
self.transform_max_iter = transform_max_iter            # <- option recorded

# transform() builds the sparse_encode(...) argument bundle from self.*,
# now including the iteration budget:
code = sparse_encode(
    X, self.components_, algorithm=self.transform_algorithm,
    n_nonzero_coefs=self.transform_n_nonzero_coefs,
    alpha=self.transform_alpha, max_iter=self.transform_max_iter,   # <- added
    n_jobs=self.n_jobs, positive=self.positive_code)
```
The constructors (`SparseCoder`/`DictionaryLearning`/`MiniBatchDictionaryLearning`)
each gain `transform_max_iter=1000` and forward it into
`_set_sparse_coding_params`. The remaining hunks thread `max_iter`/`method_max_iter`
through `_sparse_encode`/`sparse_encode`/`dict_learning`/`dict_learning_online`
and add docstrings — all in service of the same single behavior: the
user-configured iteration budget reaches the solver. (The `plot_sparse_coding.py`
hunk is an example-script numerics tidy-up with no library effect.)

The modeled value is the argument bundle handed to the solver
(`SolverArgs`) as a function of the configured options.

## Operation correspondence
| # | Lean op (`implementation_codingSolverArgs`) | patch.diff op | tag | note |
|---|---|---|---|---|
| 1 | `let cfg : CodingConfig := { nComponents, algorithm, nNonzeroCoefs, alpha, splitSign, nJobs, positive, maxIter }` | `_set_sparse_coding_params(...)` assigns each option to the like-named `self.*`, including the new `self.transform_max_iter = transform_max_iter` | R/I | the construction-time recording of every option. Type bijections in mapping.md. |
| 2 | `let mut args : SolverArgs := { algorithm := cfg.algorithm, nNonzeroCoefs := cfg.nNonzeroCoefs, alpha := cfg.alpha, maxIter := cfg.maxIter, nJobs := cfg.nJobs, positive := cfg.positive }` | the `sparse_encode(X, self.components_, algorithm=self.transform_algorithm, n_nonzero_coefs=self.transform_n_nonzero_coefs, alpha=self.transform_alpha, max_iter=self.transform_max_iter, n_jobs=self.n_jobs, positive=self.positive_code)` keyword bundle in `transform()` | R/I | the encoding step's argument assembly; `max_iter := cfg.maxIter` ↔ `max_iter=self.transform_max_iter` is the bit the fix restores. |
| 3 | `return args` | the argument bundle consumed by the solver | I | return the assembled solver arguments. |

Every op is R or I; **no A row** (no axiom consumed, no deep-model reference of
an unchanged callee — the storage and field reads are modeled directly). Therefore
`meta.json axioms = []`, `deep_model_references = []`, and `axiom_check.py` is a
skip stub.

## R/I legs ⇒ G-CONF
The whole impl is R/I, so `conformance_check.py` mechanically differential-tests
the impl shadow against the REAL patched code's behavior: it constructs a
`SparseCoder(..., transform_max_iter=m)` and intercepts the `sparse_encode` call
made by `transform()` (monkeypatching `sparse_encode` to capture its kwargs),
asserting the captured `max_iter` (and the other forwarded options) equal the
op-for-op shadow over ≥10^5 fuzzed option tuples. `conf_skip = false`.

## Prepatch = the real bug
Pre-patch, `transform()` does not pass `max_iter` to `sparse_encode`, so the
configured `transform_max_iter` never reaches the solver, which runs at its own
default of 1000 regardless. The prepatch impl models this as the solver's
iteration budget being fixed to `1000` (`maxIter := 1000`), independent of the
configured `maxIter`. It therefore cannot satisfy `problem_spec_codingSolverArgs`
on the discriminating clause `result.maxIter = maxIter` whenever `maxIter ≠ 1000`
— precisely the case the FAIL_TO_PASS test `test_max_iter` exercises (it builds a
`SparseCoder(..., transform_max_iter=1)`, expecting a ConvergenceWarning, and a
`transform_max_iter=2000`, expecting none). The carried gold proof body (a 6-fold
`rfl`) fails to typecheck against the buggy impl on the `maxIter` conjunct
(G-DIFF, confirmed: exit 1 at the `maxIter` `rfl`).
