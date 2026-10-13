# mapping.md — scikit-learn__scikit-learn-11578

Binds every `model.py` symbol to its repository counterpart at
`base_commit = dd69361a0d9c6ccde0d2353b00b86e0e7541a3e3`, states the type
abstraction, and gives the provenance of each opaque reference (callee source +
the exact behaviour the reference encodes, validated by axiom_check.py / G-AX).

Repo file under change: `sklearn/linear_model/logistic.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `scoring_estimator_proba(caller_mode, d)` | the throw-away scoring estimator built in `_log_reg_scoring_path` (`sklearn/linear_model/logistic.py:925`) and the class-probability vector it yields to the scorer at line 958 (`scoring(log_reg, X_test, y_test)`) | the modeled changed behaviour: which multiclass mode the scoring estimator runs in, and hence which probability transform a probabilistic scorer observes |
| `caller_mode` | the `multi_class` argument of `_log_reg_scoring_path` (`logistic.py:779`) | the multiclass mode the helper itself was asked to run in |
| `proba_softmax(d)` *(A-reference)* | `LogisticRegression.predict_proba` multinomial branch = `softmax(decision_2d)` (`logistic.py:1346-1353`); `softmax` is `sklearn/utils/extmath.py:588` | multinomial class-probability transform of a decision row |
| `proba_ovr(d)` *(A-reference)* | `LogisticRegression.predict_proba` ovr branch = `super()._predict_proba_lr(X)` (`logistic.py:1343-1344`); `_predict_proba_lr` is `sklearn/linear_model/base.py:280-297` | one-vs-rest class-probability transform of a decision row (sigmoid then row-normalise) |
| `scoring_proba(mode, d)` | the mode-dispatch inside `predict_proba` (`logistic.py:1343-1353`) | pure spec: selects the transform by mode |
| `witness_decision()` *(A-reference)* | the existence of a multiclass decision row (`len(Result()) >= 2`); the len Ensures is dead for the proof, validated as documentation by axiom_check.py (G-AX) | a multiclass decision row exists |
| `transforms_differ()` *(A-consumed)* | the EXISTENTIAL fact that the two real transforms (extmath.softmax vs base._predict_proba_lr) differ on the witness multiclass row; its Ensures discharges post-condition #4, validated by axiom_check.py (G-AX) | the two transforms are distinct functions on a witness row |

The pre-patch repo expression the change replaces (for the refinement audit,
not referenced from the consumer spec view): `LogisticRegression(fit_intercept=fit_intercept)`
(`logistic.py:925`), which omits `multi_class` and so defaults it to `'ovr'`
(`LogisticRegression.__init__` signature `multi_class='ovr'`, `logistic.py:1169`).
The gold replacement is `LogisticRegression(multi_class=multi_class)`.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `multi_class` string in `{'ovr','multinomial'}` (`logistic.py:779,928`) | `int` tag in `{OVR=0, MULTINOMIAL=1}` | `'ovr'` ↔ `OVR`, `'multinomial'` ↔ `MULTINOMIAL`; `multi_class == 'multinomial'` ↔ `mode == MULTINOMIAL` |
| the per-class real-valued `decision_function(X)` row of one test sample (`base.py:227-258`) | `PSeq[int]` `d` | per-class score vector; only the SELECTION between the two transforms is the modeled behaviour, so coordinate values are abstracted to ints and the transforms are opaque references (numeric content validated by G-AX) |
| the `n_classes`-vector of class probabilities `predict_proba(X)` row (`logistic.py:1318-1353`) | `PSeq[int]` of the same length | `len(Result()) == len(d)` mirrors `predict_proba`'s row width == `n_classes` == decision width |
| the OvR special-case `w = w[np.newaxis, :]` and the manual `coef_`/`intercept_` assignment (`logistic.py:946-953`) | omitted | unchanged framing; they set the same coefficients in both modes, so the decision row `d` is mode independent (validated: `decision_function` equal across modes, G-AX), leaving the mode's only observable effect on `predict_proba` |

`str` indexing is banned in Nagini, so `multi_class` is an `int` tag and the
probability/decision vectors are `PSeq[int]`.

## 3. Callee provenance (A-reference + one A-consumed — checked by G-AX / axiom_check.py)

The only behaviour that changed — which `multi_class` mode the scoring estimator
inherits, hence which probability transform a probabilistic scorer sees — is
modeled deeply by the selector `scoring_proba` consumed in
`scoring_estimator_proba`. The opaque transforms it composes (`proba_softmax`,
`proba_ovr`) are **A-references** validated against the real callees. There is
exactly **one A-consumed `@ContractOnly` axiom**, `transforms_differ` (§3.3): its
`Ensures` discharges post-condition #4. It is sound (an existential distinctness,
not a universal — validated by `check_transforms_differ`) and is not
load-bearing for the differential (post-condition #1 carries that, grounded in
the modeled inputs via `scoring_proba`).

### 3.1 `proba_softmax` ↔ multinomial `predict_proba` (A-reference)
**Callee:** `LogisticRegression.predict_proba`, multinomial branch
(`logistic.py:1345-1353`): `decision = self.decision_function(X)`, then
`softmax(decision_2d, copy=False)` where `softmax` is
`sklearn/utils/extmath.py:588` (`exp(X - max) / sum(exp(X - max))`). G-AX
asserts the real multinomial `predict_proba` equals `softmax(decision)`.

### 3.2 `proba_ovr` ↔ one-vs-rest `predict_proba` (A-reference)
**Callee:** `LogisticRegression.predict_proba`, ovr branch
(`logistic.py:1343-1344`): `super()._predict_proba_lr(X)`, i.e.
`LinearClassifierMixin._predict_proba_lr` (`base.py:280-297`):
`prob = 1/(1+exp(-decision))`, then for the multiclass case
`prob /= prob.sum(axis=1)`. G-AX asserts the real ovr `predict_proba` equals
this normalised one-vs-rest transform.

### 3.3 `transforms_differ` (A-consumed)
**Fact:** there EXISTS a multiclass decision row (the witness) on which the
softmax and one-vs-rest probability vectors DIFFER (so a probabilistic scorer
like `neg_log_loss` distinguishes the modes — the FAIL_TO_PASS test). This is an
**existential** distinctness, not a universal claim over all rows. Its `Ensures`
(`Implies(Result(), proba_softmax(witness) != proba_ovr(witness))`, `model.py:74-75`)
is **consumed** via `Requires(transforms_differ())` (`model.py:101`) to discharge
post-condition #4 (`model.py:115-116`); independently confirmed load-bearing for
#4 only (the result-pinning post-condition #1 and the G-DIFF differential hold
with the `Requires` removed). G-AX (`check_transforms_differ`) validates the
witness existence and the neg-log-loss-style score sensitivity. Because it is an
existential validated against the real callees — and the result itself is
grounded by post-condition #1 over the modeled inputs, not by echoing this
axiom — it is sound and not an answer-key oracle.

**Deliberately NOT modeled:** an arg-max (predicted-class) agreement between the
two transforms. The prediction-consuming PASS_TO_PASS scorers (accuracy /
precision / recall / f1) happen to be unaffected by the mode on the actual
fitted F2P/P2P data (decision absmax ≈ 6.82, well below the sigmoid-saturation
ceiling), but arg-max agreement is **not** a universal float64 fact: once a
decision coordinate saturates the sigmoid (≈ 36.74), one-vs-rest
row-normalisation ties and `np.argmax` resolves the tie differently from
softmax, so the two transforms' arg-max can disagree. Encoding arg-max agreement
as a contract/axiom would therefore be an over-claim unsound in general; it is
intentionally absent from the spec and from `axiom_check.py`. P2P preservation
is documentation of the real (non-saturating) test data, not a proof obligation.

**Soundness check (G-AX):** `axiom_check.py` builds real `LogisticRegression`
instances with `multi_class='multinomial'` and `multi_class='ovr'`, sets equal
`coef_`/`intercept_`/`classes_`, and asserts (a) `decision_function` is mode
independent, (b) `predict_proba` routes to `softmax` vs the normalised
one-vs-rest transform by `multi_class`, (c) a witness decision row exists where
the two probability vectors differ, and (d) the neg-log-loss-style score
distinguishes the two modes. It imports `numpy` + `scikit-learn` (the package
under change — the same code the harness runs). Exit 0 iff sound. `softmax`,
`_predict_proba_lr`, and the `predict_proba` mode dispatch are all UNCHANGED by
the gold patch, so validating against them is sound for the equivalent patch.
