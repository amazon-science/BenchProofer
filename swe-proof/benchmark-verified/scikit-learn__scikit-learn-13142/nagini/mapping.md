# mapping.md — scikit-learn__scikit-learn-13142

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 1c8668b0a021832386470ddf740d834e02c66f69`, states the type
abstraction, and gives the provenance of the axiomatized callee.

Repo file under change: `sklearn/mixture/base.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `fit_and_label(inst, run_config, run_score)` | `BaseMixture.fit_predict(self, X, y=None)` — `sklearn/mixture/base.py:194` (body 217-276) | the modeled changed function (fits `n_init` trials, persists the best, returns labels) |
| `Estimator.config` | the estimator's fitted parameters (`weights_`, `means_`, `covariances_`/`precisions_…`) held on `self`, set by `_set_parameters` (`base.py:320` abstract; concrete in `gaussian_mixture.py` / `bayesian_mixture.py`) and read by every estimate routine | the mutable parameter state the routine selects and persists |
| `labels_of(config)` *(axiom — A-consumed)* | the deterministic label assignment from the held parameters: `_e_step(X)` (`base.py:278`) → `log_resp.argmax(axis=1)` (`base.py:276`), and equivalently `predict(X)`'s `self._estimate_weighted_log_prob(X).argmax(axis=1)` (`base.py:374`) | unchanged query primitive: a deterministic function of the held parameters (for fixed data) |
| `run_config` | the per-trial parameter sets — `best_params = self._get_parameters()` snapshots captured per initialization (`base.py:257`); the running `self`-parameters are mutated by `_m_step` (`base.py:242`) each EM step | per-trial parameter identifiers |
| `run_score` | the per-trial converged lower bound `lower_bound` compared against `max_lower_bound` (`base.py:236-256`) | per-trial scores driving best-trial selection |
| `best_config(config, score)` / `best_score(score)` | the loop's `if lower_bound > max_lower_bound: max_lower_bound = lower_bound; best_params = self._get_parameters()` selection (`base.py:255-258`) | pure spec: argmax-trial selection (earliest trial on a tie) |

The selection loop visits trials `init = 0 … n_init-1` in order and updates the
running best **only on a strictly greater** lower bound, so the *earliest* trial
achieving the maximum is selected. `best_config` encodes exactly this
"earliest-max" rule (`>=` at the recursion head, scanning suffixes).

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| an estimator parameter set (`weights_`, `means_`, `covariances_`, …) | `int` configuration identifier (`Estimator.config`) | each distinct fitted parameter set ↔ a distinct identifier; equality of identifiers ↔ equality of the parameter sets that drive `_e_step`/`predict` |
| the per-trial converged `lower_bound` (`float`) | `int` score (`run_score[i]`) | the trial-selection depends only on the **order** of the lower bounds under `>` (the loop never uses their magnitudes), so an order-preserving `int` carrier is observationally identical for selection; this is **not** a precision bug — the F2P tests compare label arrays, never the bound values. |
| `n_init` independent trials | a non-empty `List[int]` of trials (`run_config`, `run_score`, equal length, `len >= 1`) | trial `i` ↔ index `i`; `n_init >= 1` ↔ `len >= 1`; the routine requires at least one run (`_check_initial_parameters` rejects `n_init < 1`, `base.py:102`). |
| label array `np.ndarray` returned by `argmax(axis=1)` | `int` (the label assignment, an opaque deterministic value) | the F2P tests assert `fit_predict(X) == predict(X)` element-wise; modeling the label assignment as one opaque deterministic value of the held config captures "the two assignments are equal iff they are computed from equal configs". |
| `self` (the estimator instance) | `Estimator` with the one touched field `config` | only the held parameter state is observed by the change; other attributes (`n_iter_`, `lower_bound_`, `converged_`) are untouched bookkeeping and omitted. |

`X` (the data) is a read-only input of `fit_predict`/`predict`; it is fixed
across the comparison and folded into the deterministic `labels_of`
(label = function of config, for that fixed `X`). It is therefore not a
separate model parameter.

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `labels_of` ↔ the label-assignment query primitive (A-consumed)
**Callee:** the estimator's deterministic label assignment from its held
parameters. In `fit_predict` this is `_, log_resp = self._e_step(X)` followed by
`log_resp.argmax(axis=1)` (`base.py:263/276`); in `predict` it is
`self._estimate_weighted_log_prob(X).argmax(axis=1)` (`base.py:374`). Both read
**only** the held parameters (`weights_`, `means_`, `covariances_`/`precisions_`)
and the fixed data `X`:

```python
def _e_step(self, X):
    log_prob_norm, log_resp = self._estimate_log_prob_resp(X)
    return np.mean(log_prob_norm), log_resp
# _estimate_log_prob_resp -> _estimate_weighted_log_prob
#                         -> _estimate_log_prob(X) + _estimate_log_weights()
```

and `argmax(axis=1)` of `_e_step`'s `log_resp` equals `argmax(axis=1)` of
`_estimate_weighted_log_prob` (the per-row `log_prob_norm` subtraction in
`_estimate_log_prob_resp`, `base.py:507`, is a per-row constant shift that does
not move the row-wise argmax). This query primitive is **unchanged** by the
patch; the only thing the patch changes is **when** it is invoked relative to
`_set_parameters(best_params)`.

The **weakest contract** the proof needs is just that the label assignment is a
**pure function of the held configuration** (same config ⇒ same labels). That is
captured by `labels_of` being a `@Pure @ContractOnly` of `config` alone (no
`Ensures` body) — Nagini gives `config1 == config2 ⇒ labels_of(config1) ==
labels_of(config2)` for free from purity. We deliberately do **not** ensure any
particular label value (that would over-claim the callee's exact output).

**Soundness check (G-AX):** `axiom_check.py` fits real `GaussianMixture` /
`BayesianGaussianMixture` estimators and asserts (a) determinism — the label
assignment is a pure function of the held parameters: running the query twice on
the same fitted object, and on two objects whose parameters were set to the same
snapshot via `_set_parameters`, yields identical labels; and (b) the standing
equivalence the patch restores — `_e_step(X).argmax` computed *from the persisted
best parameters* equals `predict(X)`. It also exhibits the differential witness:
with `n_init > 1`, the labels from the **final-trial** parameters differ from the
labels from the **selected-best** parameters (so the order of the two operations
is observable), while the labels from the **selected-best** parameters match
`predict`. Imports only `sklearn` + `numpy` (the package under test). Exit 0 iff
every obligation holds.
