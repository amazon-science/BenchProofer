# mapping.md — scikit-learn__scikit-learn-10297

## Symbol binding (file:line @ base_commit b90661d6a4)
Modeled function: the configuration constructor of the cross-validated ridge
*classifier* estimator, `RidgeClassifierCV.__init__`
(`sklearn/linear_model/ridge.py:1335-1340` @ base). At base the constructor's
parameter list omits the cross-validation-values retention flag and does not
forward it to the parent estimator initializer
(`_BaseRidgeCV.__init__`, `ridge.py:1088-1098`), which DOES accept and store it
(`self.store_cv_values = store_cv_values`, `ridge.py:1098`). The gold patch adds
the flag to the classifier constructor's signature (default `False`) and forwards
it to the parent initializer; it also touches two docstrings (non-behavioral).

Lean modeled function name: `initClassifierCV` — names the *behavior* ("build the
classifier estimator's stored configuration from the supplied options"), not a
non-public patched symbol. `RidgeClassifierCV` and `store_cv_values` are both in
the public `problem_statement`, so they are not leakage; the non-public ancestor
names (`_BaseRidgeCV`, the regression-only `RidgeCV`, the mixins) appear nowhere
in the spec view.

| Lean symbol | Python binding (file:line @ base) |
|---|---|
| `initClassifierCV` (modeled constructor) | `RidgeClassifierCV.__init__`, `ridge.py:1335-1340` (post-patch `:1335-1342`) |
| `alphas` | `alphas` ctor arg → `self.alphas` (set by parent init, `ridge.py:1092`) |
| `fitIntercept` | `fit_intercept` → `self.fit_intercept` (`ridge.py:1093`) |
| `normalize` | `normalize` → `self.normalize` (`ridge.py:1094`) |
| `scoring` | `scoring` → `self.scoring` (`ridge.py:1095`) |
| `cv` | `cv` → `self.cv` (`ridge.py:1096`) |
| `classWeight` | `class_weight` → `self.class_weight` (`ridge.py:1340`) |
| `storeCvValues` | `store_cv_values` → `self.store_cv_values` (parent init, `ridge.py:1098`); added to the classifier ctor + super() call by the gold patch |
| result | the constructed estimator's stored configuration (the touched `self.*` attributes) |

## Lean ↔ Python type bijection (used by G-CONF and G-AX)
| Python | Lean |
|---|---|
| `alphas` sequence of regularization values (order-preserving, stored verbatim) | `alphas : List Rat` |
| `fit_intercept : bool` | `fitIntercept : Bool` |
| `normalize : bool` | `normalize : Bool` |
| `scoring : None \| str` (scorer name; identity-compared) | `scoring : Option Nat` (`None ↔ none`, a scorer ↔ `some k`) |
| `cv : None \| int` (splitter; `None` selects efficient leave-one-out) | `cv : Option Nat` (`None ↔ none`, otherwise `some k`) |
| `class_weight : None \| dict` (identity-compared) | `classWeight : Option Nat` (`None ↔ none`, otherwise `some k`) |
| `store_cv_values : bool` | `storeCvValues : Bool` |
| constructed estimator's stored config (the touched attributes) | `result : ClassifierCVConfig` (one field per attribute above) |

The values `alphas`, `scoring`, `cv`, `class_weight` are *stored verbatim* by the
constructor — only their identity (equality with the supplied argument) is
observable at construction time, so the encodings above are exact bijections for
the construction step. Float regularization values are modeled as `Rat` to keep
the impl computable and equality decidable (DECISIONS.md: kernel `Float` equality
is opaque to tactics); construction never does float arithmetic, only storage, so
`Rat` is a faithful stand-in for the stored sequence.

## Callee provenance + flag deps
No unchanged callee is *consumed* as an axiom and no A-reference is declared. The
parent initializer `_BaseRidgeCV.__init__` is the forwarding target; its effect
on the touched attributes (it assigns each kwarg to the like-named `self.*`) is
modeled DIRECTLY as field storage, op-for-op, not axiomatized. G-CONF validates
this by exercising the REAL patched constructor and reading back every attribute.

There is no flag-dependent branch in the modeled constructor: every supplied
option is stored unconditionally. The retention flag's *downstream* effect (the
inherited `_BaseRidgeCV.fit` populating `cv_values_` when `store_cv_values` is set
and `cv=None`) is UNCHANGED by the patch and therefore out of scope — the patch
edits only the constructor's parameter forwarding.

## G-LEAK
The `problem_statement` contains `RidgeClassifierCV`, `store_cv_values`,
`cv_values_`, `cv=None`, and "Generalized Cross-Validation"; these are public.
The spec view names no non-public patched symbol: `_BaseRidgeCV`, `RidgeCV`,
`RegressorMixin`, `LinearClassifierMixin`, `gcv_mode`, `__init__` do not appear in
any spec-view identifier or comment. The modeled identifiers (`initClassifierCV`,
`ClassifierCVConfig`, `storeCvValues`, …) embed none of those substrings.
Comments describe the desired behavior (each supplied option is recorded into the
stored configuration), never the edit or a diagnosis.

## Pinned G-CONF fuzz seed
`10297`.
