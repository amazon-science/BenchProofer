# refinement.md — scikit-learn__scikit-learn-11578

The operation-by-operation correspondence between `model.py`'s implementation
(the `scoring_estimator_proba` impl region + the deep `scoring_proba` selector)
and `patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A** (axiomatized callee — **A-consumed** where the proof uses an axiom's
`Ensures`, **A-reference** where a deep model is validated `== the real callee`
by axiom_check.py / G-AX), or **I** (identical concrete operation). The claim:
*any implementation that verifies against this frozen spec, refined per the map
below, is behaviourally equal to the gold patch on the tested inputs, so it
resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

The only operation that changed — which `multi_class` mode the scoring estimator
inherits, hence which probability transform a probabilistic scorer observes — is
modeled **deeply** (`scoring_proba` in the `pure` region), and the two
probability transforms it selects between are validated as **A-references**
(`proba_softmax`, `proba_ovr`; their `len` `Ensures` is dead for the proof and
validated only as documentation). There is exactly **one A-consumed
`@ContractOnly` axiom**: `transforms_differ` — its `Ensures` (an EXISTENTIAL
distinctness of the two transforms on a witness row) discharges the derived
discriminating consequence post-condition #4. It is sound (existential, not a
universal — validated by `axiom_check.py`'s `check_transforms_differ`) and is
**not** load-bearing for the differential, which post-condition #1 carries
independently (see §A row A3 and the G-DIFF discussion below).

## A. The scoring-estimator site — `_log_reg_scoring_path` (`logistic.py:925`)

Gold hunk:
```
-    log_reg = LogisticRegression(fit_intercept=fit_intercept)
+    log_reg = LogisticRegression(multi_class=multi_class)
```

This is the entire change. The throw-away estimator used purely for scoring
(`scoring(log_reg, X_test, y_test)`, line 958) must run in the SAME multiclass
mode the helper was asked for, so that a probabilistic scorer — which reads
`log_reg.predict_proba(X_test)` — sees the caller's mode's probabilities. The
pre-patch constructor omitted `multi_class` and so defaulted it to `'ovr'`
(`LogisticRegression.__init__(..., multi_class='ovr', ...)`), forcing the
one-vs-rest probability transform regardless of the caller's request.

(Note: the gold also drops the now-unneeded `fit_intercept=` argument; the
intercept is set manually at lines 949-953 in BOTH the pre- and post-patch code,
so `fit_intercept` has no effect on the scoring estimator's observable output —
it is mode that matters. The model therefore abstracts the constructor down to
the single observable: the multiclass mode the estimator runs in.)

| # | model.py impl op (`scoring_estimator_proba`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | `caller_mode: int` parameter (`OVR`/`MULTINOMIAL`) | the `multi_class` argument of `_log_reg_scoring_path` | R | `'ovr'`/`'multinomial'` string ↔ `OVR`/`MULTINOMIAL` int tag (mapping.md §2). |
| A2 | `effective_mode = caller_mode` | `LogisticRegression(multi_class=multi_class)` | R + I | the scoring estimator's effective mode is set to the caller's mode — identical control flow under the string↔int bijection. The pre-patch `LogisticRegression(fit_intercept=fit_intercept)` is the omission that defaults the mode to `OVR`. |
| A3 | `result = scoring_proba(effective_mode, d)` — the probability vector the estimator yields, `proba_softmax(d)` if `effective_mode == MULTINOMIAL` else `proba_ovr(d)` | `log_reg.predict_proba(X_test)` consumed by `scoring(log_reg, X_test, y_test)` (line 958), whose branch is `softmax(decision)` if `multi_class=='multinomial'` else `_predict_proba_lr` | A-reference | the two probability transforms are modeled as opaque references `proba_softmax` / `proba_ovr` (A-reference) and validated `== the real predict_proba branches` by axiom_check.py (G-AX). The decision row `d` is mode independent (`decision_function` equal across modes, validated G-AX), so the mode's only observable effect is the transform selection, which `scoring_proba` spells out. The proof depends on neither transform's exact numeric content nor on any arg-max relationship between them. The single fact it consumes about the transforms is their EXISTENTIAL distinctness on the witness row — the **A-consumed** axiom `transforms_differ` (validated G-AX) — and that feeds only the derived consequence post-condition #4, not the result-pinning post-condition #1. |
| A4 | `return result` | the probability vector flows into the scorer to produce the score | I | the modeled output is the probability vector the probabilistic scorer reads; the scorer and the surrounding `scores.append(...)` loop are unchanged framing, not part of the modeled delta. |

The discriminating content — in multinomial mode the scoring estimator produces
the multinomial (softmax) probability vector, NOT the one-vs-rest one — lives in
the postconditions
`Implies(caller_mode == MULTINOMIAL, Result() == proba_softmax(d))` and, on the
witness decision row where the transforms differ,
`Implies(caller_mode == MULTINOMIAL and d == witness_decision(), Result() != proba_ovr(d))`.
The pre-patch estimator forced `OVR`; `model_prepatch.py` reproduces that
(`effective_mode = OVR`) and **fails** post-condition #1
`Result() == scoring_proba(caller_mode, d)` exactly on the
`caller_mode == MULTINOMIAL` case (it returns `proba_ovr(d)` where
`proba_softmax(d)` is required, and the verifier cannot prove the two opaque
transforms equal) — the spec sensing the change (G-DIFF). This differential is
grounded in the modeled inputs via the deep `scoring_proba` selector and does
**not** rely on the A-consumed `transforms_differ` axiom (which carries only the
derived consequence #4); confirmed by re-running the differential with the
`Requires(transforms_differ())` removed.

The prediction-consuming PASS_TO_PASS scorers (`accuracy / precision / recall /
f1` variants of the multinomial-score test, which read `predict` = arg-max) are
preserved across the change in the real repo — they are unaffected by the mode
on the fitted F2P/P2P data — only the `neg_log_loss` (probabilistic) variant is
the FAIL_TO_PASS. This preservation is **documentation, not a proof obligation**:
the spec deliberately makes **no** claim about arg-max agreement between the two
transforms. Such an agreement is *not* a universal float64 fact (it is false once
a decision coordinate saturates the sigmoid, where one-vs-rest row-normalisation
ties and `np.argmax` breaks ties differently from softmax), so encoding it as a
contract would be an over-claimed/unsound axiom. The gold patch resolves the
FAIL_TO_PASS regardless, and the P2P scorers pass on the actual non-saturating
fitted data (decision absmax ≈ 6.82), so no arg-max postcondition is needed.

## B. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-reference (`proba_softmax`/`proba_ovr`), A-consumed
(`transforms_differ`), or I — no kind-3 (unexpressible-changed-op) step. The one
operation that genuinely *changed* — the scoring estimator inheriting the
caller's multiclass mode rather than defaulting to one-vs-rest — is modeled
**deeply** (`scoring_proba` in the `pure` region, consumed by
`scoring_estimator_proba`), not hidden behind an axiom about the function under
change. The unchanged numeric transforms it selects between (multinomial
`softmax`, one-vs-rest `_predict_proba_lr`) are the **A-references** that G-AX
validates the deep model against (axiom_check.py asserts the real `predict_proba`
routes by `multi_class`, the transforms differ on a witness, and the
neg-log-loss score distinguishes the modes).

There is exactly **one A-consumed `@ContractOnly` axiom**, `transforms_differ`
(`model.py:68-75`), consumed via `Requires(transforms_differ())`
(`model.py:101`). Its `Ensures` — `proba_softmax(witness) != proba_ovr(witness)`
— discharges post-condition #4 (`model.py:115-116`); independently confirmed
load-bearing for #4 (removing the `Requires` makes verification fail on exactly
that post-condition) but **not** for the differential: post-condition #1 catches
the prepatch bug with `transforms_differ` removed. It is sound: the claim is an
EXISTENTIAL distinctness on a witness row (NOT a universal over all rows, and NOT
the arg-max universal dropped in the first refinement, which was false at float64
sigmoid saturation), validated in-container by `axiom_check.py`'s
`check_transforms_differ`. It is NOT an answer-key oracle the impl can echo: the
result is grounded by post-condition #1 over the modeled inputs `caller_mode`/`d`
via the deep selector `scoring_proba`; `transforms_differ` only lets the derived
consequence #4 follow from the already-pinned #1. The two opaque numeric
transforms are intrinsically inexpressible in Nagini's int fragment, so an
existential A-consumed distinctness fact validated by G-AX is the principled,
non-over-claimed modeling.

## C. verify(model) ⇒ resolved

`scoring_estimator_proba` verifies only if its output equals the caller's mode's
transform of the decision row (`Result() == scoring_proba(caller_mode, d)`) and,
on the witness, is the softmax (not one-vs-rest) vector in multinomial mode (A3
postconditions). By R (`'multinomial'`↔`MULTINOMIAL`, the decision/probability
rows ↔ `PSeq[int]`) the verified selector equals the gold
`LogisticRegression(multi_class=multi_class).predict_proba(X_test)`; by the
A-references (G-AX) the two opaque transforms equal the real `predict_proba`
branches and they differ on a multiclass row. The FAIL_TO_PASS probabilistic-scorer
test (`test_logistic_cv_multinomial_score[neg_log_loss-...]`) passes because the
multinomial score now reads softmax probabilities; the PASS_TO_PASS prediction
scorers are preserved on the actual non-saturating fitted data (documentation,
not a modeled obligation, since arg-max agreement is not a universal float64
fact). Therefore a model
satisfying this spec, refined by the map above, is the gold patch up to type
refinement and the audited references — and the gold patch resolves
(G-RESOLVE). The trust points are exactly the two of PLAN §1.1: the A-reference
and A-consumed axiom soundness (G-AX validates both `proba_softmax`/`proba_ovr`
and the existential `transforms_differ`) and refinement fidelity (this document,
G-EQ).
