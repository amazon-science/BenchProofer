# refinement.md — scikit-learn__scikit-learn-11578

Maps every op in `implementation_scoringProbs` (Solution.lean impl region) to its
`patch.diff` counterpart. Tags: **R** (type refinement), **A-consumed** (proof
uses an axiom), **A-reference** (deep model validated == real callee by G-AX),
**I** (identical concrete op).

## The patch

```
-    log_reg = LogisticRegression(fit_intercept=fit_intercept)
+    log_reg = LogisticRegression(multi_class=multi_class)
```

The behavioral effect: the model used to produce the probability estimates for
the probabilistic scorer now carries the requested `multi_class`, so its
`predict_proba` uses the requested regime (softmax for `'multinomial'`, otherwise
one-vs-rest) instead of always defaulting to one-vs-rest.

## Operation correspondence

| # | impl op (Lean) | patch.diff / repo counterpart | tag |
|---|---|---|---|
| 1 | `let mode := parseMode multiClass` | post-patch: the scoring model's regime is selected by the requested `multi_class` (the `predict_proba` branch `if self.multi_class == "ovr" … else softmax`); the patch makes `multi_class` flow into that model | **R** (string→`ProbMode`; the dispatch the patch enables) |
| 2 | `for d in decisions do …` accumulate `out := out ++ [predictProba mode d]` | the `for w in coefs:` loop calling `scoring(log_reg, X_test, y_test)`, where each `w`/`C` gives one candidate model whose `predict_proba` is evaluated, in order | **R/I** (loop over candidates, order + count preserved — frame discipline §0.5) |
| 3 | `predictProba mode d` → `ovrRow` / `softmaxRow` per row | `LogisticRegression.predict_proba`: `_predict_proba_lr` (base.py) for ovr, `softmax` (extmath) for multinomial — UNCHANGED callees the fix routes into | **A-reference** (modeled deeply as `ovrRow`/`softmaxRow`; G-AX validates == real callees) |
| 4 | `return out` | the per-candidate probability matrices the scorer consumes | **I** |

No op is changed-inexpressible. The thing the patch CHANGES (which regime is
used) is modeled deeply via the mode dispatch (op 1) over the real transforms
(op 3); per SPEC_GUIDE §3 the transforms — unchanged callees the fix merely
re-routes — are A-reference (deeply modeled, G-AX-checked), NOT consumed axioms.
There are therefore no `axiom _prop` declarations and `axioms` region is empty.

## Discriminating clause (G-DIFF / G-PANEL)

Prepatch fixes `mode := ProbMode.ovr` (the default the un-propagated constructor
took). On any candidate whose requested mode is `'multinomial'`, the prepatch
returns `ovrRow` rows while the spec demands `softmaxRow` rows; since the two
transforms disagree on every nontrivial score row, `correct_scoringProbs`
(stating `result = decisions.map (predictProba (parseMode multiClass) …)`) is
unprovable for the prepatch — exactly the F2P expectation
`test_logistic_cv_multinomial_score[neg_log_loss-...]`.

## Modeled domain (refinement faithfulness)

The modeled observable is the MULTICLASS regime: `decision_function` returns a
2-D score matrix with `n_classes ≥ 2` columns per row, and `predict_proba` maps
it row-wise via `softmax` (multinomial) or `_predict_proba_lr`'s 2-D
normalisation (ovr). This is exactly the regime the fix's observable lives in —
the F2P test uses `n_classes = 3`, so every score row has ≥ 2 entries.

The distinct BINARY (1-D decision) `predict_proba` path — sklearn's
`np.vstack([1-p, p]).T` for ovr and the `np.c_[-decision, decision]` softmax
workaround for multinomial — is a SEPARATE code path that the changed line does
not exercise for this instance, so it is intentionally out of the modeled domain.
G-AX and G-CONF fuzz only `n_classes ≥ 2` rows, matching this domain. (`ovrRow`
on a hypothetical single-entry row would give `[1]`, which is not sklearn's
binary output — but no such row is producible by the modeled multiclass
observable, so it is unreachable, not a refinement gap.)

## G-CONF scope

R/I legs (mode dispatch + framing) are differential-tested by
conformance_check.py with the A-reference transforms left as the real repo
callees. conf_skip = false.
