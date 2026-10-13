# mapping.md — scikit-learn__scikit-learn-13142

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 1c8668b0a021832386470ddf740d834e02c66f69`, states the type
abstraction (the bijection a differential gate would use to bridge Lean↔Python),
and records callee provenance.

Repo file under change: `sklearn/mixture/base.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `finalizeLabels (transientParams : Params) (storedParams : Params) (labelsFor : Params → Labels)` | the tail of `BaseMixture.fit_predict(self, X, y=None)` — `sklearn/mixture/base.py:194` (the finalization block, body lines 257–276) | the modeled changed function — the label-finalization tail of the fit-then-predict routine |
| `transientParams : Params` | the parameter state left in `self` (`self.weights_`, `self.means_`, `self.covariances_`, …) when the `for init in range(n_init)` loop finishes — i.e. the LAST attempt's parameters | read-only free input |
| `storedParams : Params` | `best_params = self._get_parameters()` captured for the argmax-scoring attempt — `sklearn/mixture/base.py:257`; installed by `self._set_parameters(best_params)` — line 272 | read-only free input |
| `labelsFor : Params → Labels` | the UNCHANGED label-computing pipeline: a final E-step `_, log_resp = self._e_step(X)` (line 263 pre / 268-area post) followed by `log_resp.argmax(axis=1)` (line 276), read as a pure function of the parameter set currently in force on `self` (X is fixed) | read-only free input (opaque function) |
| `reportedLabels (storedParams) (labelsFor)` | the value `fit_predict` returns: `log_resp.argmax(axis=1)` computed with the best parameters in force | pure spec: the labels reported for the best parameter set |

The pre-patch behaviour the change fixes (refinement audit only, not in the
consumer spec view): in the pre-patch source the final E-step
(`_, log_resp = self._e_step(X)`, line 263) runs BEFORE
`self._set_parameters(best_params)` (line 272), so `log_resp` — and the returned
`argmax` — reflect the LAST attempt's parameters rather than the best ones. The
fix moves the final E-step to AFTER `_set_parameters`.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

The modeled behaviour is purely about WHICH parameter set the reported labels are
derived from; no concrete numeric content is observed, so the carriers are
deliberately opaque.

| repo reality | Lean carrier | bijection |
|---|---|---|
| a complete parameter set (`self.weights_`, `self.means_`, `self.covariances_`, `self.precisions_cholesky_`, the tuple returned by `_get_parameters()`) | `Params` (opaque, `abbrev Params := Nat`) | two parameter sets are identified iff they are the same set; only set IDENTITY is observed, never element values |
| the per-sample label vector `log_resp.argmax(axis=1)` (a NumPy `ndarray` of `int`, shape `(n_samples,)`) | `Labels` (`abbrev Labels := List Nat`) | element-wise; `len` ↔ `length` (unused — the labels are observed only as the value the unchanged routine yields for a parameter set) |
| the final-E-step-then-argmax pipeline `_e_step(X)` + `.argmax(axis=1)` as a function of the active parameters (X fixed) | `labelsFor : Params → Labels` | a deterministic function of the active parameter set; the spec quantifies over ALL such functions, so no concrete numeric bridge is needed |

`labelsFor` is left fully free: the spec never inspects what labels a parameter
set yields, only that the REPORTED labels are the ones `labelsFor` gives for
`storedParams`. This is the abstraction that makes the ordering bug the sole observable.

## 3. Callee provenance

There are **no axioms** and **no deep-model references** in this bundle.

The only callees the modeled tail touches — `self._e_step(X)` and the implicit
`.argmax(axis=1)`, together with `self._set_parameters` / `self._get_parameters`
— are all **UNCHANGED** by the patch. The patch changes only their relative
ORDER. Their input→output behaviour is therefore carried abstractly:

- `_e_step` ∘ `argmax`, as a function of the active parameters, is the free input
  `labelsFor`. The spec asserts nothing about its concrete values, so there is no
  contract to check against the real callee (no G-AX). It holds for every
  function `labelsFor` could be.
- `_set_parameters(best_params)` is modeled as the assignment `active := storedParams`
  (installing the selected parameter set); `_get_parameters()` for the
  attempt whose parameters the estimator ends up storing is the free input `storedParams`.

Because no contract is consumed about any callee, `axiom_check.py` is a `skip`
stub (G-AX = skip).

## 4. Differential / fuzz status (G-CONF)

`conf_skip = true`. The modeled `do` block's only discriminating observable is
the IDENTITY of the parameter set the labels are computed from — a control-flow
ORDERING fact, not an input-dependent numeric computation. The label-producing
routine `labelsFor` is an UNCHANGED callee carried as a free input; its R/I
shadow is a constant pass-through with no input-dependent computation to refute,
and the discriminator (best-vs-leftover parameters) materializes only against a
live `GaussianMixture`/`BayesianGaussianMixture` object fitted with `n_init > 1`
— i.e. the F2P tests themselves (`test_gaussian_mixture_fit_predict_n_init`,
`test_bayesian_mixture_fit_predict_n_init`), not a pure transliteration this gate
could fuzz over ≥10⁵ inputs. Per SPEC_GUIDE §0 and the worker prompt (precedent:
astropy__astropy-14096, django__django-11451), `conformance_check.py` is a
`status=skip` stub; soundness is carried by G-VERIFY + G-DIFF.
