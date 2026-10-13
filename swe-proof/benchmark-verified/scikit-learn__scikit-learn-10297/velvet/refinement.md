# refinement.md — scikit-learn__scikit-learn-10297

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`initEstimator` `do` block and the deep `construct` model) and `patch.diff` (the
gold patch). Each step is tagged **R** (type refinement; state the bijection),
**A-consumed** (proof uses an axiom's `ensures`), **A-reference** (deep model
validated == real callee by G-AX), or **I** (identical concrete op). EVERY step
is R, A, or I.

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the A legs + narrative by G-EQ. This bundle has **no A legs** (no axioms,
no `:|` stubs), so the entire correspondence is R/I and is covered end-to-end by
G-CONF against the real patched class.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## The change

The behaviourally-relevant gold hunk (`sklearn/linear_model/ridge.py`); the
remaining hunks are docstring-only (no runtime effect):
```
 def __init__(self, alphas=(0.1, 1.0, 10.0), fit_intercept=True,
-                 normalize=False, scoring=None, cv=None, class_weight=None):
+                 normalize=False, scoring=None, cv=None, class_weight=None,
+                 store_cv_values=False):
     super(RidgeClassifierCV, self).__init__(
         alphas=alphas, fit_intercept=fit_intercept, normalize=normalize,
-            scoring=scoring, cv=cv)
+            scoring=scoring, cv=cv, store_cv_values=store_cv_values)
     self.class_weight = class_weight
```

The edit exposes the retention option on the classifier constructor and forwards
it to the **unchanged** shared base constructor `_BaseRidgeCV.__init__`
(`ridge.py:1093-1102`), which records `self.store_cv_values = store_cv_values`.
That recorded attribute is then read by the **unchanged** downstream
`_BaseRidgeGCV.fit` (`ridge.py:1077`): `if self.store_cv_values:` decides whether
the `cv_values_` attribute is populated. Before the patch the classifier
constructor did not accept the keyword, so `cls(..., store_cv_values=True)`
raised `TypeError` — the issue's reported symptom.

## initEstimator — the classifier estimator constructor (`ridge.py:1339` → base `:1093`)

| # | Solution.lean impl op (`initEstimator`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| 1 | parameter `storeCvValues : Bool` | the added `store_cv_values` keyword arg of `__init__` (default `False`) | R | `bool ↔ Bool`, identity (mapping.md §2). |
| 2 | `let acceptsStore : Bool := true` | the constructor now exposes `store_cv_values` and forwards it to the base, i.e. the estimator supports the retention option | I | the concrete capability the construction reads; the gold patch establishes exactly this for the classifier estimator by adding the parameter and the forwarding call. mapping.md §1. |
| 3 | `if storeCvValues && !acceptsStore then return Except.error .storeNotAccepted` | the (now unreachable) refusal path: a constructor not exposing the keyword would raise `TypeError` | I | models the construction guard; the error variant ↔ the `TypeError` (mapping.md §2). Post-patch this branch is dead because `acceptsStore = true`; it is what the prepatch re-activates. |
| 4 | `else return Except.ok { storeCvValues := storeCvValues }` | `super().__init__(..., store_cv_values=store_cv_values)` → `self.store_cv_values = store_cv_values` records the requested option on the built estimator | R + I | success ↔ `Except.ok`; `storeCvValues` is the touched/recorded field (mapping.md §2); the rest of `super().__init__` (alphas/fit_intercept/… field-setting) is the R-identity callee independent of the modeled behaviour (mapping.md §2). |

## Discriminating content + prepatch

The single behavioural change the method observes is `acceptsStore := true`
(step 2) ⇔ the constructor exposing and forwarding `store_cv_values`. With
`storeCvValues = true`:
- patched: construction succeeds and records the option ⇒
  `Except.ok { storeCvValues := true }`. The F2P test
  `test_ridge_classifier_cv_store_cv_values` then constructs with the option set
  and reads `r.cv_values_` after `fit` — which only exists because the recorded
  option reached `fit`;
- pre-patch: the constructor does not expose the option ⇒ the request is refused
  ⇒ `Except.error .storeNotAccepted` (the reported `TypeError`).

`Solution_prepatch.lean` restores `acceptsStore := false` (the pre-patch reality:
the option not exposed). It **fails** `prove_correct` on the `storeCvValues = true`
branch (the spec requires `Except.ok` recording the option, the buggy skeleton
produces `Except.error`) — one failing prepatch for the one independently-fixed
behaviour (G-DIFF). The frozen spec is byte-identical across both files.

The spec also pins, on the success branch, that the constructed estimator
**records the requested option** (`storeCvValues := storeCvValues`), not merely
that construction succeeds. This is load-bearing: the F2P test reads
`r.cv_values_` after `fit`, and `fit` populates `cv_values_` only when the
recorded `self.store_cv_values` is true. An impl that accepted the keyword but
dropped it (e.g. always stored `False`) would satisfy a "succeeds" spec yet fail
F2P (no `cv_values_` attribute → `AttributeError`); the
`storeCvValues := storeCvValues` clause rules it out (G-PANEL attacker-1 /
SPEC_GUIDE §0.4).

## No kind-3 (inexpressible-changed-op) steps; no axioms

Every step is R or I. The one thing that genuinely changed — exposing and
forwarding the retention option — is concrete data modeled directly (step 2, an
`I` op), and the construction guard plus recording that consume it are modeled
deeply (`construct`). There is **no consumed axiom and no `:|` stub**: the
orthogonal `super().__init__` field-setting is an R-identity (its outcome is
independent of the modeled behaviour, mapping.md §2), not an axiom. Hence G-AX is
skipped and G-CONF carries the full R/I burden.

## verify(Solution) ⇒ resolved

`initEstimator` verifies only if, with `storeCvValues = true`, it returns
`Except.ok` recording `storeCvValues := true` (and refuses only when the
capability is absent — which, for this estimator post-patch, it is not). By R
(`bool ↔ Bool`, the `store_cv_values` field bijection, `super().__init__`
field-setting identity) the verified method equals the patched classifier
constructor on every input; by G-CONF the R/I transliteration agrees with
`patch.diff`'s behaviour on 100 002 inputs (full cross product + fuzz) and
disagrees with the unpatched repo (the discriminator is real). Therefore a model
satisfying this spec, refined by the map above, is the gold patch up to type
refinement — and the gold patch resolves (G-RESOLVE). The single trust point (no
axioms here) is refinement fidelity, mechanized by G-CONF and audited by G-EQ.
