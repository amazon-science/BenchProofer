# refinement.md — scikit-learn__scikit-learn-11578

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`probabilityMethodForScoring` `do` block, plus the deep `probaMethodOf` model)
and `patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A** (axiomatized callee — **A-consumed** where the proof uses an axiom's
`ensures`, **A-reference** where a deep model is validated == the real callee by
G-AX), or **I** (identical concrete op).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the A legs and this narrative are audited by **G-EQ**. Claim: any impl
verifying against this frozen spec, refined per the map below, is behaviourally
equal to the gold patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The flag-propagation site — `_log_reg_scoring_path` (`logistic.py:925`)

Gold hunk:
```
-    log_reg = LogisticRegression(fit_intercept=fit_intercept)
+    log_reg = LogisticRegression(multi_class=multi_class)
```

The estimator `log_reg` is the one handed to the scorer at `logistic.py:958`
(`scoring(log_reg, X_test, y_test)`). Its `multi_class` attribute selects which
branch `predict_proba` takes (`logistic.py:1343-1353`), and hence — for a
probabilistic scorer — the probability values that determine the returned score.

| # | Solution.lean impl op (`probabilityMethodForScoring`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `requested : MultiClass` | the `multi_class` argument of `_log_reg_scoring_path` | R | `'ovr'`/`'multinomial'` str ↔ `MultiClass.ovr`/`.multinomial` (mapping.md §2); the domain is exactly these two (the routine raises on anything else). |
| A2 | `out := match requested with \| .ovr => .ovrNormalize \| .multinomial => .softmax` | `log_reg = LogisticRegression(multi_class=multi_class)` … `scoring(log_reg, …)` | A-reference + I | the changed op makes the scored estimator's mode EQUAL the requested mode; the probability method it then applies is `predict_proba`'s mode selection. That selection is modeled DEEPLY as `probaMethodOf` (`.ovr→ovrNormalize`, `.multinomial→softmax`); the equality of that deep model to the real `predict_proba` branch is the **A-reference** G-AX validates. The impl op explicitly *reconstructs* that selection branch-by-branch (`match requested`), and the postcondition is grounded in structural predicates on `requested` (`requested=multinomial → out=softmax`, `requested=ovr → out=ovrNormalize`) so a verifying impl must produce the answer via the modeled branch rather than echo the oracle — that branch reconstruction is **I** against `probaMethodOf`. mapping.md §3.1. |
| A3 | `return out` (`ProbaMethod`) | the probabilistic score `scoring(log_reg, …)` returned for the fold | R | the score is a deterministic function of which probability method is used (OvR-normalize vs softmax) given the fixed decision scores; observed as that method's identity (mapping.md §2). |

Discriminating content of the change — a `multinomial` request must be scored
with `softmax`, not the one-vs-rest normalization — lives in
the postcondition clause `requested = .multinomial → out = .softmax` (model) ⇔ the
scored estimator inheriting `multi_class='multinomial'` so `predict_proba` takes
its `else: softmax(...)` branch (real). The pre-patch built
`LogisticRegression(fit_intercept=fit_intercept)`, whose `multi_class` defaults to
`'ovr'`, so it always used OvR-normalize; `Solution_prepatch.lean` reproduces that
(`out := ProbaMethod.ovrNormalize`) and **fails** the clause
`requested = .multinomial → out = .softmax` at `requested = .multinomial`
(unsolved goal `ProbaMethod.ovrNormalize = ProbaMethod.softmax`) — G-DIFF.

## B. The dropped `fit_intercept` constructor kwarg (R — observationally inert)

The gold hunk also removes `fit_intercept=fit_intercept` from the constructor.
This is **R (identity)**: it has no observable effect on any score. The scored
estimator never consults `self.fit_intercept` — `_log_reg_scoring_path` sets
`log_reg.coef_` and `log_reg.intercept_` **directly** from the path coefficients
(`logistic.py:945-952`, guarded by the routine's own `fit_intercept` local, not
the estimator attribute), and `decision_function` (`base.py:227`) computes
`X·coefᵀ + intercept_` from those attributes alone. So whether the constructor
received `fit_intercept` changes nothing downstream. No separate modeled method
or prepatch is needed: dropping it is a no-op carried by G-RESOLVE (`patch.diff`
== gold) and confirmed by G-CONF (the oracle runs the real patched routine, with
the kwarg already gone, and still agrees with the shadow).

## C. No axioms, no kind-3 (inexpressible-changed-op) steps

Every step is R, I, or the single A-reference. There is **no consumed axiom**:
the operation the proof leans on — `predict_proba`'s mode selection — is an
**unchanged** callee modeled DEEPLY (`probaMethodOf`, an A-reference validated
== the real callee by G-AX), not hidden behind a `axiom` the proof consumes, and
NOT the function under change. The operation that genuinely *changed* — threading
`multi_class` into the scored estimator — is modeled **directly** in the `do`
block (A2: `out := probaMethodOf requested`). The impl region contains no
A-tagged callee invocation in the computed `out` (the A-reference is the
deep-modeled selection function, which is itself transliterated by G-CONF), so
`conf_skip = false` and G-CONF runs.

## D. verify(Solution) ⇒ resolved

`probabilityMethodForScoring` verifies only if it returns the probability method
MATCHING the requested mode — `softmax` for `multinomial`, `ovrNormalize` for
`ovr` (A2) — and because the postcondition is grounded as two implications over
`requested`, the proof must case-split on `requested` (it is not a definitional
`rfl`); a constant or swapped impl fails. By R (the `multi_class` str ↔ `MultiClass`, branch-identity ↔
`ProbaMethod`, and `fit_intercept`-drop = identity bijections, mapping.md §2) the
verified selection equals the gold patch's behavior: the scored estimator
inherits the requested mode and `predict_proba` applies the matching method. By
G-AX the deep model `probaMethodOf` equals the real `predict_proba` branch
selection (A-reference); by G-CONF the R/I transliteration agrees with
`patch.diff`'s observed probability method over both modes. The downstream score
computation (the scorer's formula, the decision scores) is unchanged by the patch
and is a deterministic function of the probability method, so equal method ⇒
equal probabilistic score. Therefore a model satisfying this spec, refined by the
map above, is the gold patch up to type refinement and the audited unchanged
callee — and the gold patch resolves (G-RESOLVE). The one trust point is the type
bijection + the A-reference's fidelity (this doc, G-EQ + G-CONF + G-AX).
