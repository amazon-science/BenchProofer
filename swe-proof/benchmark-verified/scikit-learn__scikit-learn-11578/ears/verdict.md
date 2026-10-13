# P2 adversarial audit — scikit-learn__scikit-learn-11578

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 6 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 6 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 6 | `probe_pc.py`, `probe_softmax.py`, `probe_ovr.py`, `probe_label.py`, `probe_valueerror.py`, `probe_norefit.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_pc.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (6):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_pc.py` → holds on the patched tree (good)

```python
# Positive control / R1.3 + R1.2: multinomial probabilistic scorer (neg_log_loss).
# _log_reg_scoring_path's score for a given C, under the multinomial regime,
# must equal the score of a LogisticRegression configured multinomial carrying
# the same fitted coef/intercept, on the same held-out data.
import numpy as np
from sklearn.datasets import make_classification
from sklearn.linear_model import LogisticRegression
from sklearn.linear_model.logistic import _log_reg_scoring_path
from sklearn.metrics.scorer import get_scorer

X, y = make_classification(n_samples=100, random_state=0, n_classes=3,
                           n_informative=6)
train, test = np.arange(80), np.arange(80, 100)
lr = LogisticRegression(C=1., solver='lbfgs', multi_class='multinomial')
params = lr.get_params()
for key in ['C', 'n_jobs', 'warm_start']:
    del params[key]
lr.fit(X[train], y[train])

scorer = get_scorer('neg_log_loss')
path_score = _log_reg_scoring_path(X, y, train, test, Cs=[1.],
                                   scoring=scorer, **params)[2][0]
ref_multinomial = scorer(lr, X[test], y[test])
print("path_score      =", path_score)
print("ref_multinomial =", ref_multinomial)
diff = abs(path_score - ref_multinomial)
print("abs diff        =", diff)
ok = diff < 1e-6
print("HOLDS" if ok else "VIOLATED")
import sys
sys.exit(0 if ok else 1)
```

Attack 2 — `probe_softmax.py` → holds on the patched tree (good)

```python
# R1.2: under multinomial regime, probability estimates driving a probabilistic
# scorer must be the SOFTMAX of the per-sample decision score rows, NOT the
# one-vs-rest logistic-then-normalize values. We recompute the neg_log_loss the
# path SHOULD produce from softmax probabilities of the path coefs, and from OVR
# probabilities, and assert the path score matches SOFTMAX (and not OVR).
import numpy as np
from sklearn.datasets import make_classification
from sklearn.linear_model import LogisticRegression
from sklearn.linear_model.logistic import _log_reg_scoring_path
from sklearn.metrics import log_loss
from sklearn.metrics.scorer import get_scorer
from sklearn.utils.extmath import softmax

X, y = make_classification(n_samples=100, random_state=0, n_classes=3,
                           n_informative=6)
train, test = np.arange(80), np.arange(80, 100)
lr = LogisticRegression(C=1., solver='lbfgs', multi_class='multinomial')
params = lr.get_params()
for key in ['C', 'n_jobs', 'warm_start']:
    del params[key]
lr.fit(X[train], y[train])

scorer = get_scorer('neg_log_loss')
path_score = _log_reg_scoring_path(X, y, train, test, Cs=[1.],
                                   scoring=scorer, **params)[2][0]

# Reconstruct decision scores from the fitted multinomial estimator.
scores = lr.decision_function(X[test])           # (n_samples, n_classes)
proba_softmax = softmax(scores.copy())
# OVR-style probabilities (logistic then normalize) via _predict_proba_lr
proba_ovr = 1. / (1. + np.exp(-scores))
proba_ovr /= proba_ovr.sum(axis=1)[:, np.newaxis]

nll_softmax = -log_loss(y[test], proba_softmax, labels=lr.classes_)
nll_ovr = -log_loss(y[test], proba_ovr, labels=lr.classes_)
print("path_score  =", path_score)
print("nll_softmax =", nll_softmax)
print("nll_ovr     =", nll_ovr)
print("|softmax gap|=", abs(path_score - nll_softmax))
print("|ovr gap|    =", abs(path_score - nll_ovr))
ok = (abs(path_score - nll_softmax) < 1e-6) and (abs(path_score - nll_ovr) > 1e-6)
print("HOLDS" if ok else "VIOLATED")
import sys
sys.exit(0 if ok else 1)
```

Attack 3 — `probe_ovr.py` → holds on the patched tree (good)

```python
# R1.4 + R2.2 (ovr): under the ovr regime, the estimator handed to the scorer
# must produce OVR probability estimates, and classes_ set to [-1, 1] (two-class
# pos/neg). We verify the path's neg_log_loss under ovr matches the reference
# from a LogisticRegression(multi_class='ovr') carrying the same coefs.
# ovr scoring path scores a single class (pos_class) as binary. We check that
# the returned score equals the ovr reference (not the multinomial one).
import numpy as np
from sklearn.datasets import make_classification
from sklearn.linear_model import LogisticRegression
from sklearn.linear_model.logistic import _log_reg_scoring_path
from sklearn.metrics.scorer import get_scorer

# binary problem so pos_class handling is clean
X, y = make_classification(n_samples=100, random_state=0, n_classes=2,
                           n_informative=6)
train, test = np.arange(80), np.arange(80, 100)
lr = LogisticRegression(C=1., solver='lbfgs', multi_class='ovr')
params = lr.get_params()
for key in ['C', 'n_jobs', 'warm_start']:
    del params[key]
lr.fit(X[train], y[train])

scorer = get_scorer('neg_log_loss')
path_score = _log_reg_scoring_path(X, y, train, test, Cs=[1.],
                                   scoring=scorer, **params)[2][0]
ref = scorer(lr, X[test], y[test])
print("path_score(ovr) =", path_score)
print("ref(ovr)        =", ref)
diff = abs(path_score - ref)
print("abs diff        =", diff)
ok = diff < 1e-6
print("HOLDS" if ok else "VIOLATED")
import sys
sys.exit(0 if ok else 1)
```

Attack 4 — `probe_label.py` → holds on the patched tree (good)

```python
# R2.1: label-based scorers (accuracy, precision_macro/weighted, f1_*, recall_*)
# under multinomial regime must return, per C, the score that scorer produces for
# a LogisticRegression configured multinomial with the same coefs, on same data.
import numpy as np
from sklearn.datasets import make_classification
from sklearn.linear_model import LogisticRegression
from sklearn.linear_model.logistic import _log_reg_scoring_path
from sklearn.metrics.scorer import get_scorer

X, y = make_classification(n_samples=100, random_state=0, n_classes=3,
                           n_informative=6)
train, test = np.arange(80), np.arange(80, 100)
lr = LogisticRegression(C=1., solver='lbfgs', multi_class='multinomial')
params = lr.get_params()
for key in ['C', 'n_jobs', 'warm_start']:
    del params[key]
lr.fit(X[train], y[train])

names = ['accuracy', 'precision_macro', 'precision_weighted',
         'f1_macro', 'f1_weighted', 'recall_macro', 'recall_weighted']
ok = True
for name in names:
    scorer = get_scorer(name)
    ps = _log_reg_scoring_path(X, y, train, test, Cs=[1.],
                               scoring=scorer, **params)[2][0]
    ref = scorer(lr, X[test], y[test])
    d = abs(ps - ref)
    print(f"{name:20s} path={ps:.6f} ref={ref:.6f} diff={d:.2e}")
    if d >= 1e-6:
        ok = False
print("HOLDS" if ok else "VIOLATED")
import sys
sys.exit(0 if ok else 1)
```

Attack 5 — `probe_valueerror.py` → holds on the patched tree (good)

```python
# R2.3: an invalid multi_class string must raise ValueError.
# R2.4: return contract: (coefs, Cs, scores, n_iter) shapes/order preserved.
import numpy as np
from sklearn.datasets import make_classification
from sklearn.linear_model import LogisticRegression
from sklearn.linear_model.logistic import _log_reg_scoring_path
from sklearn.metrics.scorer import get_scorer

X, y = make_classification(n_samples=100, random_state=0, n_classes=3,
                           n_informative=6)
train, test = np.arange(80), np.arange(80, 100)
lr = LogisticRegression(C=1., solver='lbfgs', multi_class='multinomial')
params = lr.get_params()
for key in ['C', 'n_jobs', 'warm_start']:
    del params[key]
lr.fit(X[train], y[train])
scorer = get_scorer('neg_log_loss')

ok = True
# ValueError on bad regime
bad = dict(params)
bad['multi_class'] = 'not_a_regime'
try:
    _log_reg_scoring_path(X, y, train, test, Cs=[1.], scoring=scorer, **bad)
    print("no ValueError raised -> VIOLATED")
    ok = False
except ValueError as e:
    print("ValueError raised as required:", str(e)[:60])

# return contract
Cs = [0.1, 1.0, 10.0]
ret = _log_reg_scoring_path(X, y, train, test, Cs=Cs, scoring=scorer, **params)
print("len(ret) =", len(ret))
coefs, Cs_out, scores, n_iter = ret
print("coefs.shape =", np.asarray(coefs).shape)
print("Cs_out =", np.asarray(Cs_out))
print("scores.shape =", np.asarray(scores).shape)
print("n_iter.shape =", np.asarray(n_iter).shape)
if len(ret) != 4:
    ok = False
if np.asarray(scores).shape[0] != len(Cs):
    ok = False
if not np.allclose(np.asarray(Cs_out), np.asarray(Cs)):
    ok = False
print("HOLDS" if ok else "VIOLATED")
import sys
sys.exit(0 if ok else 1)
```

Attack 6 — `probe_norefit.py` → holds on the patched tree (good)

```python
# R2.5: scores computed from the exact path coefficients; the internal estimator
# is NOT refit on the held-out data. We verify by constructing a reference
# estimator whose coef_/intercept_ are set to the path coefs (NOT refit) and
# checking the multinomial score equals the path score. A refit on X[test]
# would produce different coefficients (test set is tiny + different), so a
# match with the coef-injected estimator (and mismatch with a refit-on-test
# estimator) confirms no refit.
import numpy as np
from sklearn.datasets import make_classification
from sklearn.linear_model import LogisticRegression
from sklearn.linear_model.logistic import _log_reg_scoring_path
from sklearn.metrics.scorer import get_scorer

X, y = make_classification(n_samples=100, random_state=0, n_classes=3,
                           n_informative=6)
train, test = np.arange(80), np.arange(80, 100)
lr = LogisticRegression(C=1., solver='lbfgs', multi_class='multinomial')
params = lr.get_params()
for key in ['C', 'n_jobs', 'warm_start']:
    del params[key]
lr.fit(X[train], y[train])   # fit on TRAIN -> same as path coefs
scorer = get_scorer('neg_log_loss')

coefs, Cs, scores, n_iter = _log_reg_scoring_path(
    X, y, train, test, Cs=[1.], scoring=scorer, **params)
path_score = scores[0]

# estimator carrying path coefs (train-fitted), scored on test -> should MATCH
ref_train = scorer(lr, X[test], y[test])

# estimator REFIT on the held-out test data -> should DIFFER (proves no refit)
lr_test = LogisticRegression(C=1., solver='lbfgs', multi_class='multinomial')
lr_test.fit(X[test], y[test])
ref_refit = scorer(lr_test, X[test], y[test])

print("path_score      =", path_score)
print("ref (train coef)=", ref_train)
print("ref (refit test)=", ref_refit)
match_train = abs(path_score - ref_train) < 1e-6
differ_refit = abs(path_score - ref_refit) > 1e-6
print("matches train-coef estimator :", match_train)
print("differs from refit-on-test   :", differ_refit)
ok = match_train and differ_refit
print("HOLDS" if ok else "VIOLATED")
import sys
sys.exit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_pc.py`

```python
# Positive control / R1.3 + R1.2: multinomial probabilistic scorer (neg_log_loss).
# _log_reg_scoring_path's score for a given C, under the multinomial regime,
# must equal the score of a LogisticRegression configured multinomial carrying
# the same fitted coef/intercept, on the same held-out data.
import numpy as np
from sklearn.datasets import make_classification
from sklearn.linear_model import LogisticRegression
from sklearn.linear_model.logistic import _log_reg_scoring_path
from sklearn.metrics.scorer import get_scorer

X, y = make_classification(n_samples=100, random_state=0, n_classes=3,
                           n_informative=6)
train, test = np.arange(80), np.arange(80, 100)
lr = LogisticRegression(C=1., solver='lbfgs', multi_class='multinomial')
params = lr.get_params()
for key in ['C', 'n_jobs', 'warm_start']:
    del params[key]
lr.fit(X[train], y[train])

scorer = get_scorer('neg_log_loss')
path_score = _log_reg_scoring_path(X, y, train, test, Cs=[1.],
                                   scoring=scorer, **params)[2][0]
ref_multinomial = scorer(lr, X[test], y[test])
print("path_score      =", path_score)
print("ref_multinomial =", ref_multinomial)
diff = abs(path_score - ref_multinomial)
print("abs diff        =", diff)
ok = diff < 1e-6
print("HOLDS" if ok else "VIOLATED")
import sys
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance fixes _log_reg_scoring_path to construct the internal LogisticRegression with multi_class=multi_class (was defaulting to 'ovr'). Six probes cover the requirements:

- probe_pc.py (R1.3, POSITIVE CONTROL): multinomial neg_log_loss path score == score of multinomial LogisticRegression carrying same coefs on same test fold. PATCHED diff=0.0 HOLDS; BASE diff=0.0431 VIOLATED (discriminates). WEAK VIOLATED.
- probe_softmax.py (R1.2): reconstructs probabilities and asserts path multinomial score matches SOFTMAX-of-decision-scores neg_log_loss (gap 0.0) and NOT the OVR logistic-then-normalize value (gap 0.043). PATCHED HOLDS; BASE VIOLATED (path matched OVR); WEAK VIOLATED.
- probe_ovr.py (R1.4/R2.2): OVR-regime neg_log_loss path score == OVR reference. HOLDS on patched AND base (behavior preserved) — regression guard.
- probe_label.py (R2.1): accuracy, precision/f1/recall macro & weighted under multinomial all equal the multinomial reference estimator (diff 0). HOLDS patched & base (label scorers unaffected).
- probe_valueerror.py (R2.3/R2.4): invalid multi_class raises ValueError; return contract is 4-tuple (coefs, Cs, scores, n_iter) with scores.shape==(len(Cs),) and Cs preserved. HOLDS both trees.
- probe_norefit.py (R2.5): multinomial path score matches train-coef estimator and DIFFERS from an estimator refit on the held-out test fold (proves no refit). PATCHED HOLDS; BASE VIOLATED.

Positive control failed at base (prepatch reproduced) and holds patched. Candidate patch weak.diff (a no-op that keeps the default OVR regime — the lazy fix a weak reading permits) is REJECTED by probe_pc and probe_softmax, so the suite discriminates wrong implementations. No probe fails on the patched tree and no probe-conforming alternative patch was found. Requirements faithfully characterize the gold fix.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 6 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 6 | `probe_pc.py`, `probe_softmax.py`, `probe_ovr.py`, `probe_label.py`, `probe_valueerror.py`, `probe_norefit.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_pc.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (6):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

_The 6 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts, and on this backend both roles put it through the same derivation: every block below is a requirement probe run on the gold-patched tree, and the `machine verdict:` line each role publishes above reports BOTH that its probes hold there and how many candidate patches the probe suite rejected — so the two roles re-ran ONE probe suite and each recorded its own outcome for every probe in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `probe_pc.py` → holds on the patched tree (good)

Attack 2 — `probe_softmax.py` → holds on the patched tree (good)

Attack 3 — `probe_ovr.py` → holds on the patched tree (good)

Attack 4 — `probe_label.py` → holds on the patched tree (good)

Attack 5 — `probe_valueerror.py` → holds on the patched tree (good)

Attack 6 — `probe_norefit.py` → holds on the patched tree (good)

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_pc.py`

```python
# Positive control / R1.3 + R1.2: multinomial probabilistic scorer (neg_log_loss).
# _log_reg_scoring_path's score for a given C, under the multinomial regime,
# must equal the score of a LogisticRegression configured multinomial carrying
# the same fitted coef/intercept, on the same held-out data.
import numpy as np
from sklearn.datasets import make_classification
from sklearn.linear_model import LogisticRegression
from sklearn.linear_model.logistic import _log_reg_scoring_path
from sklearn.metrics.scorer import get_scorer

X, y = make_classification(n_samples=100, random_state=0, n_classes=3,
                           n_informative=6)
train, test = np.arange(80), np.arange(80, 100)
lr = LogisticRegression(C=1., solver='lbfgs', multi_class='multinomial')
params = lr.get_params()
for key in ['C', 'n_jobs', 'warm_start']:
    del params[key]
lr.fit(X[train], y[train])

scorer = get_scorer('neg_log_loss')
path_score = _log_reg_scoring_path(X, y, train, test, Cs=[1.],
                                   scoring=scorer, **params)[2][0]
ref_multinomial = scorer(lr, X[test], y[test])
print("path_score      =", path_score)
print("ref_multinomial =", ref_multinomial)
diff = abs(path_score - ref_multinomial)
print("abs diff        =", diff)
ok = diff < 1e-6
print("HOLDS" if ok else "VIOLATED")
import sys
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance fixes _log_reg_scoring_path to construct the internal LogisticRegression with multi_class=multi_class (was defaulting to 'ovr'). Six probes cover the requirements:

- probe_pc.py (R1.3, POSITIVE CONTROL): multinomial neg_log_loss path score == score of multinomial LogisticRegression carrying same coefs on same test fold. PATCHED diff=0.0 HOLDS; BASE diff=0.0431 VIOLATED (discriminates). WEAK VIOLATED.
- probe_softmax.py (R1.2): reconstructs probabilities and asserts path multinomial score matches SOFTMAX-of-decision-scores neg_log_loss (gap 0.0) and NOT the OVR logistic-then-normalize value (gap 0.043). PATCHED HOLDS; BASE VIOLATED (path matched OVR); WEAK VIOLATED.
- probe_ovr.py (R1.4/R2.2): OVR-regime neg_log_loss path score == OVR reference. HOLDS on patched AND base (behavior preserved) — regression guard.
- probe_label.py (R2.1): accuracy, precision/f1/recall macro & weighted under multinomial all equal the multinomial reference estimator (diff 0). HOLDS patched & base (label scorers unaffected).
- probe_valueerror.py (R2.3/R2.4): invalid multi_class raises ValueError; return contract is 4-tuple (coefs, Cs, scores, n_iter) with scores.shape==(len(Cs),) and Cs preserved. HOLDS both trees.
- probe_norefit.py (R2.5): multinomial path score matches train-coef estimator and DIFFERS from an estimator refit on the held-out test fold (proves no refit). PATCHED HOLDS; BASE VIOLATED.

Positive control failed at base (prepatch reproduced) and holds patched. Candidate patch weak.diff (a no-op that keeps the default OVR regime — the lazy fix a weak reading permits) is REJECTED by probe_pc and probe_softmax, so the suite discriminates wrong implementations. No probe fails on the patched tree and no probe-conforming alternative patch was found. Requirements faithfully characterize the gold fix.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Probed inside the instance image via nl_attack. Note the fitted subtlety: the patch drops the explicit fit_intercept kwarg, but fit_intercept defaults to True and the coefs are assigned manually with the correct slicing, so behavior is unchanged — requirements do not over-claim about fit_intercept. All acceptance criteria are satisfied by the patched code; no mandated-but-absent, forbidden-but-present, wrong-boundary, or invented behavior found.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The requirements localize the change to _log_reg_scoring_path / LogisticRegression / multi_class and describe OvR-logistic-normalize vs multinomial-softmax probability semantics, predict_proba, neg_log_loss, coef/intercept assignment, the ValueError on unknown regime, and the 4-tuple return contract. ALL of this is public in problem_statement, which even quotes the exact one-line gold fix (LogisticRegression(fit_intercept=fit_intercept, multi_class=multi_class)) and the full minimal repro. Closest concern: Req 2.1 (lines 67-68) enumerates 'accuracy, precision, recall, or f1, including their macro- and weighted-averaged variants,' which mirrors the hidden test's parametrize list (accuracy[''], precision[_macro,_weighted], f1[_macro,_weighted], neg_log_loss[''], recall[_macro,_weighted]) and does not appear in problem_statement. However these are the canonical label-based sklearn scorers and canonical multiclass averaging schemes — generic domain vocabulary, not test-derived. The doc does NOT transmit the test's idiosyncratic/test-only content: no micro-averaging mention or its omission rationale, no parametrization ids, no test names (test_logistic_cv_multinomial_score), no test file path, no quoted test/gold code, no invented identifiers. It translates test-checked behavior into requirements (the legitimate objective) rather than transmitting the tests. Mechanical G-LEAK already passed; no semantic reconstruction found.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
