# refinement.md — scikit-learn__scikit-learn-13142

The operation-by-operation correspondence between `model.py`'s implementation
(the `fit_and_label` impl region, the `best_config`/`best_score` deep selection
model, and the `labels_of` axiom) and `patch.diff` (the gold patch). Each step
is tagged **R** (type refinement), **A-consumed** (the proof uses the axiom's
guarantee), **A-reference** (a deep model validated == the real callee by
axiom_check.py / G-AX), or **I** (identical concrete operation). The claim:
*any implementation that verifies against this frozen spec, refined per the map
below, is behaviourally equal to the gold patch on the tested inputs, so it
resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The single change site — `fit_predict()` (`sklearn/mixture/base.py:194`)

The gold patch **moves** the final label-deriving query so it runs *after* the
selected-best parameters are persisted, rather than *before*:

```
@@ fit_predict, end of the n_init loop @@
-        # Always do a final e-step ...
-        _, log_resp = self._e_step(X)            # (removed: ran on the LAST-trial params)
-
         if not self.converged_:
             warnings.warn(...)

         self._set_parameters(best_params)         # persist the SELECTED-best params
         self.n_iter_ = best_n_iter
         self.lower_bound_ = max_lower_bound

+        # Always do a final e-step ...
+        _, log_resp = self._e_step(X)            # (added: now runs on the SELECTED-best params)
+
         return log_resp.argmax(axis=1)
```

| # | model.py impl op (`fit_and_label`) | patch.diff / repo op | tag | justification |
|---|---|---|---|---|
| A1 | `inst: Estimator` with mutable `inst.config` | `self` carrying the fitted parameters (`weights_`/`means_`/`covariances_`…) | R | parameter set ↔ `int` config id (mapping.md §2); only the held-parameter field is touched. |
| A2 | `run_config: List[int]`, `run_score: List[int]`, `len >= 1` | the `n_init` trials; each contributes a `_get_parameters()` snapshot and a converged `lower_bound` (`base.py:230-258`) | R | trial `i` ↔ index `i`; `n_init >= 1` ↔ `len >= 1`; `lower_bound: float` ↔ `int` score, order-only (mapping.md §2). |
| A3 | `inst.config = run_config[n-1]` (transient state = final trial) | the EM loop leaves `self`'s parameters at the **last** initialization's values (each `_m_step` mutates them; `_set_parameters` has not yet been called) | R + I | the residual `self`-state after the `for init` loop is the final trial's params; modeled as assigning the last list element. |
| A4 | the backward scan selecting `selected`/`selected_score` == `best_config`/`best_score` over the trials | `if lower_bound > max_lower_bound: max_lower_bound = lower_bound; best_params = self._get_parameters()` (`base.py:255-258`) | A-reference | the trial-selection is modeled **deeply** by the verified loop + the pure `best_config`/`best_score` (earliest-max). It is validated == the real loop's `best_params` by G-AX (the persisted-best params equal the largest-lower-bound trial). No consumed axiom stands in for selection. |
| A5 | `inst.config = selected` (persist the selected best) | `self._set_parameters(best_params)` (`base.py:272`) | R + I | restore the selected-best parameters onto `self`. |
| A6 | `labels = labels_of(inst.config)` **after** A5, then `return labels` | `_, log_resp = self._e_step(X)` **after** `_set_parameters` (post-patch position), then `return log_resp.argmax(axis=1)` | A-consumed | the label assignment is the unchanged query primitive `labels_of`, a pure function of the held config (mapping.md §3.1). The proof consumes only its purity (same config ⇒ same labels). **The ordering A5-before-A6 is the entire content of the change.** |

## B. The discriminating clause and the prepatch

The spec's load-bearing postcondition is

```
Ensures(Result() == labels_of(inst.config))
```

i.e. the returned labels equal the label assignment of the configuration the
object *ends up holding*. Because `predict(X)` is `labels_of(persisted config)`
(same primitive, same config), this is exactly "fit-time labels agree with
query-time labels" — the property the F2P tests assert (`fit_predict(X) ==
predict(X)` with `n_init > 1`).

`model_prepatch.py` keeps the spec **byte-identical** and only swaps the order of
A5/A6 (derive labels from the *transient* final-trial config, then persist the
selected best — the pre-patch position of the query). It **fails** verification
precisely on `Result() == labels_of(inst.config)`: the returned value is
`labels_of(final-trial config)` while `inst.config` ends as the selected-best
config, and these differ whenever the best trial is not the last (G-DIFF). This
is the one independently-observable fixed behaviour, so one prepatch suffices.

## C. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-reference, A-consumed, or I. The operation that
genuinely *changed* — the **ordering** of "persist selected-best params" before
"derive labels" — is modeled **directly** as the impl statement order (A5 then
A6), the very thing the prepatch reverses. The trial-selection (A4) is modeled
**deeply** (`best_config`/`best_score` + the verified loop), an **A-reference**
validated by G-AX, not hidden behind an axiom. The only **consumed** axiom,
`labels_of` (A6), abstracts an **unchanged** callee (the `_e_step`/`predict`
label-assignment chain) and uses only its purity. There is no axiom about the
function under change.

## D. verify(model) ⇒ resolved

`fit_and_label` verifies only if (i) `inst.config` ends equal to the
earliest-largest-score trial's config (`best_config`, A4) and (ii) `Result()`
equals `labels_of` of that *persisted* config (A6 after A5). By R (config ↔
parameter set, order-only score, trial ↔ index) the verified routine equals the
gold `fit_predict`: it persists `best_params` (the largest-`lower_bound` trial)
and returns `argmax` of the e-step computed **from those persisted params**.
By the `labels_of` purity axiom (G-AX-checked: the label assignment is a
deterministic function of the held params, and equals `predict` on those params),
the returned labels equal `predict(X)` — exactly the F2P requirement. Therefore a
model satisfying this spec, refined by the map above, is the gold patch up to
type refinement and the one audited callee, and the gold patch resolves
(G-RESOLVE). The trust points are exactly the two of PLAN §1.1: axiom soundness
(G-AX) and refinement fidelity (this document, G-EQ).
