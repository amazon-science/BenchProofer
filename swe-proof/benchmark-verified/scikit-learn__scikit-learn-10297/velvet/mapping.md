# mapping.md — scikit-learn__scikit-learn-10297

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = b90661d6a46aa3619d3eec94d5281f5888add501`, states the type
abstraction (the bijection G-CONF uses to bridge Lean↔Python), and gives the
provenance of each modeled callee.

Repo file under change: `sklearn/linear_model/ridge.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `initEstimator (storeCvValues : Bool)` | the cross-validated classifier estimator's constructor `__init__` — `sklearn/linear_model/ridge.py:1339` | the modeled changed function: a constructor that gains the retention option and forwards it to the shared base constructor |
| `construct (acceptsStore) (storeCvValues)` *(deep model — R/I)* | the shared base constructor `_BaseRidgeCV.__init__` (`ridge.py:1093-1102`), which stores `self.store_cv_values`, **plus** the downstream read `if self.store_cv_values:` in `_BaseRidgeGCV.fit` (`ridge.py:1077`) that decides whether `cv_values_` is populated | pure spec: the construction outcome (refuse-if-unsupported else build-and-record), modeled deeply; validated `== real class` by G-CONF, NOT consumed as an axiom |
| `EstimatorState.storeCvValues` | the `self.store_cv_values` attribute set in `_BaseRidgeCV.__init__` (`ridge.py:1101`) | the recorded option the unchanged `fit` later reads |
| `InitErr.storeNotAccepted` | the `TypeError("__init__() got an unexpected keyword argument 'store_cv_values'")` Python raises when the constructor does not expose the option | a refused construction |

The pre-patch repo reality the change removes (refinement audit only, not in the
consumer spec view): the classifier constructor's parameter list at
`ridge.py:1340-1341` lacked `store_cv_values`, and its `super().__init__(...)`
call at `ridge.py:1342-1344` did not forward it — so `cls(..., store_cv_values=True)`
raised `TypeError`.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) uses to translate values between the Lean value
domain and the Python repo types.

| repo reality | Lean carrier | bijection |
|---|---|---|
| the `store_cv_values` keyword argument (`bool`, default `False`) | `Bool` | `True ↔ true`, `False ↔ false` (identity) |
| a successfully constructed estimator exposing `self.store_cv_values` | `EstimatorState { storeCvValues : Bool }` | the only behaviourally-constrained field is the recorded option; `agg.store_cv_values` (Python `bool`) ↔ `storeCvValues` (Lean `Bool`). Every other constructor field (`alphas`, `fit_intercept`, …) is orthogonal to the modeled behaviour and omitted. |
| `TypeError` (unexpected keyword argument) raised by `__init__` | `Except.error InitErr.storeNotAccepted` | construction-refused ↔ the error variant |
| a successful construction | `Except.ok _` | construction-succeeded ↔ the ok variant |
| the per-estimator capability "supports the retention option" | `acceptsStore : Bool` | the classifier estimator supports it ⇒ `acceptsStore = true`. Concrete datum the gold patch establishes (by adding the parameter and forwarding it). |

The other constructor arguments (`alphas`, `fit_intercept`, `normalize`,
`scoring`, `cv`, `class_weight`) are passed through unchanged by both the
pre-patch and post-patch constructors; they do not affect whether the retention
option is accepted or recorded, so they are not modeled (mapping.md §2,
directive-5 frame: no field the modeled behaviour constrains is left
unconstrained).

## 3. Callee provenance (kind-A — none)

This bundle has **no consumed axioms and no `:|` stubs**. The construction
behaviour is modeled deeply (`construct`, R/I) and validated end-to-end against
the real patched class by G-CONF. The orthogonal `super().__init__` field-setting
(for `alphas`, `fit_intercept`, …) is an R-identity callee whose outcome is
independent of the modeled retention behaviour, not an axiom. Hence G-AX is
skipped (no `axiom_check.py`).

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`10297`** so the
consumer-side verdict (§11.3) is reproducible. The R/I shadow it builds
transliterates `construct`/`initEstimator` to Python and observes the real
patched classifier estimator constructor (accept/refuse + recorded
`store_cv_values`). There are no A-tagged callees in the impl region, so the
shadow is pure R/I.
