# P2 adversarial audit — scikit-learn__scikit-learn-13779

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 8 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 8 | `probe_1_none_slot_fit.py`, `probe_2_only_present_stored.py`, `probe_3_refit_after_removal.py`, `probe_4_present_unsupported_raises.py`, `probe_5_no_sw_skips_check.py`, `probe_6_all_none_raises.py`, `probe_7_weights_len_mismatch.py`, `probe_8_no_none_weighted_regression.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1_none_slot_fit.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (8):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1_none_slot_fit.py` → holds on the patched tree (good)

```python
# Req 1.1/1.2 + positive control: fit with sample_weight and a None slot succeeds.
import sys
import numpy as np
from sklearn.ensemble import VotingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.naive_bayes import GaussianNB

X = np.array([[0, 0], [1, 1], [2, 2], [3, 3], [4, 4], [5, 5]], dtype=float)
y = np.array([0, 0, 0, 1, 1, 1])
sw = np.ones(len(y))

eclf = VotingClassifier(estimators=[('lr', LogisticRegression(solver='liblinear')),
                                    ('nb', GaussianNB())])
eclf.set_params(lr=None)
try:
    ret = eclf.fit(X, y, sample_weight=sw)
except Exception as e:
    print("FAIL: fit raised %s: %s" % (type(e).__name__, e))
    sys.exit(1)
if ret is not eclf:
    print("FAIL: fit did not return self")
    sys.exit(1)
print("PASS: fit with None slot + sample_weight succeeded, returned self")
sys.exit(0)
```

Attack 2 — `probe_2_only_present_stored.py` → holds on the patched tree (good)

```python
# Req 1.4: only present (non-None) estimators are trained and stored.
import sys
import numpy as np
from sklearn.ensemble import VotingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.naive_bayes import GaussianNB

X = np.array([[0, 0], [1, 1], [2, 2], [3, 3], [4, 4], [5, 5]], dtype=float)
y = np.array([0, 0, 0, 1, 1, 1])
sw = np.ones(len(y))

eclf = VotingClassifier(estimators=[('lr', LogisticRegression(solver='liblinear')),
                                    ('nb', GaussianNB())])
eclf.set_params(lr=None)
eclf.fit(X, y, sample_weight=sw)

n = len(eclf.estimators_)
print("n fitted estimators_:", n)
if n != 1:
    print("FAIL: expected 1 fitted estimator, got %d" % n)
    sys.exit(1)
# the stored one should be the GaussianNB (present slot)
from sklearn.naive_bayes import GaussianNB as GNB
if not isinstance(eclf.estimators_[0], GNB):
    print("FAIL: stored estimator is not the present GaussianNB:", type(eclf.estimators_[0]))
    sys.exit(1)
print("PASS: only the present estimator was trained and stored")
sys.exit(0)
```

Attack 3 — `probe_3_refit_after_removal.py` → holds on the patched tree (good)

```python
# Req 1.3 + Req 2.1: fit, then remove via set_params, refit with weights, predict shape matches y.
import sys
import numpy as np
from sklearn.ensemble import VotingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.naive_bayes import GaussianNB

X = np.array([[0, 0], [1, 1], [2, 2], [3, 3], [4, 4], [5, 5]], dtype=float)
y = np.array([0, 0, 0, 1, 1, 1])
sw = np.ones(len(y))

eclf = VotingClassifier(estimators=[('lr', LogisticRegression(solver='liblinear')),
                                    ('nb', GaussianNB())])
eclf.fit(X, y, sample_weight=sw)          # first fit, both present
eclf.set_params(lr=None)                  # remove one
try:
    eclf.fit(X, y, sample_weight=sw)      # refit
except Exception as e:
    print("FAIL: refit raised %s: %s" % (type(e).__name__, e))
    sys.exit(1)

pred = eclf.predict(X)
print("pred shape:", np.shape(pred), "y shape:", np.shape(y))
if np.shape(pred) != np.shape(y):
    print("FAIL: prediction shape mismatch")
    sys.exit(1)
print("PASS: refit after removal succeeded and predict shape matches y")
sys.exit(0)
```

Attack 4 — `probe_4_present_unsupported_raises.py` → holds on the patched tree (good)

```python
# Req 3.1/3.2/3.3: present estimator lacking sample_weight support -> ValueError naming it (first in roster order).
import sys
import numpy as np
from sklearn.ensemble import VotingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.neighbors import KNeighborsClassifier

X = np.array([[0, 0], [1, 1], [2, 2], [3, 3], [4, 4], [5, 5]], dtype=float)
y = np.array([0, 0, 0, 1, 1, 1])
sw = np.ones(len(y))

# knn (no sample_weight) and knn2 both unsupported; None slot present too.
eclf = VotingClassifier(estimators=[('nb_removed', LogisticRegression(solver='liblinear')),
                                     ('knn', KNeighborsClassifier()),
                                     ('knn2', KNeighborsClassifier())])
eclf.set_params(nb_removed=None)
try:
    eclf.fit(X, y, sample_weight=sw)
except ValueError as e:
    msg = str(e)
    print("Got ValueError:", msg)
    if 'knn' not in msg:
        print("FAIL: message does not name offending estimator")
        sys.exit(1)
    if 'sample weight' not in msg.lower():
        print("FAIL: message does not mention sample weights")
        sys.exit(1)
    # first unsupported in roster order is 'knn' (not knn2)
    if "'knn'" not in msg:
        print("FAIL: did not report first offender 'knn':", msg)
        sys.exit(1)
    print("PASS: ValueError names first offender 'knn' and mentions sample weights")
    sys.exit(0)
except Exception as e:
    print("FAIL: raised %s instead of ValueError: %s" % (type(e).__name__, e))
    sys.exit(1)
print("FAIL: no error raised for unsupported present estimator")
sys.exit(1)
```

Attack 5 — `probe_5_no_sw_skips_check.py` → holds on the patched tree (good)

```python
# Req 3.4: when sample_weight is None, no support check -> unsupported present estimator fits fine.
import sys
import numpy as np
from sklearn.ensemble import VotingClassifier
from sklearn.neighbors import KNeighborsClassifier
from sklearn.naive_bayes import GaussianNB

X = np.array([[0, 0], [1, 1], [2, 2], [3, 3], [4, 4], [5, 5]], dtype=float)
y = np.array([0, 0, 0, 1, 1, 1])

eclf = VotingClassifier(estimators=[('knn', KNeighborsClassifier(n_neighbors=1)),
                                    ('nb', GaussianNB())])
try:
    eclf.fit(X, y)  # no sample_weight
except Exception as e:
    print("FAIL: fit without weights raised %s: %s" % (type(e).__name__, e))
    sys.exit(1)
print("PASS: fit without sample_weight skips support check (KNN accepted)")
sys.exit(0)
```

Attack 6 — `probe_6_all_none_raises.py` → holds on the patched tree (good)

```python
# Req 4.3: all estimators None -> ValueError "at least one is required". Also with sample_weight present,
# the None-skip must not swallow this: still must raise.
import sys
import numpy as np
from sklearn.ensemble import VotingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.naive_bayes import GaussianNB

X = np.array([[0, 0], [1, 1], [2, 2], [3, 3], [4, 4], [5, 5]], dtype=float)
y = np.array([0, 0, 0, 1, 1, 1])
sw = np.ones(len(y))

eclf = VotingClassifier(estimators=[('lr', LogisticRegression(solver='liblinear')),
                                    ('nb', GaussianNB())])
eclf.set_params(lr=None, nb=None)
try:
    eclf.fit(X, y, sample_weight=sw)
except ValueError as e:
    msg = str(e)
    print("Got ValueError:", msg)
    if 'None' in msg or 'at least one' in msg.lower() or 'required' in msg.lower():
        print("PASS: all-None roster raises ValueError requiring at least one estimator")
        sys.exit(0)
    print("FAIL: ValueError but wrong message")
    sys.exit(1)
except Exception as e:
    print("FAIL: raised %s instead of ValueError: %s" % (type(e).__name__, e))
    sys.exit(1)
print("FAIL: no error for all-None roster")
sys.exit(1)
```

Attack 7 — `probe_7_weights_len_mismatch.py` → holds on the patched tree (good)

```python
# Req 4.2: weights length != number of estimators -> ValueError. (regression guard)
import sys
import numpy as np
from sklearn.ensemble import VotingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.naive_bayes import GaussianNB

X = np.array([[0, 0], [1, 1], [2, 2], [3, 3], [4, 4], [5, 5]], dtype=float)
y = np.array([0, 0, 0, 1, 1, 1])
sw = np.ones(len(y))

eclf = VotingClassifier(estimators=[('lr', LogisticRegression(solver='liblinear')),
                                    ('nb', GaussianNB())],
                        weights=[1, 2, 3])  # 3 weights, 2 estimators
try:
    eclf.fit(X, y, sample_weight=sw)
except ValueError as e:
    print("Got ValueError:", e)
    print("PASS: weights/estimators length mismatch raises ValueError")
    sys.exit(0)
except Exception as e:
    print("FAIL: raised %s instead of ValueError: %s" % (type(e).__name__, e))
    sys.exit(1)
print("FAIL: no error for weights length mismatch")
sys.exit(1)
```

Attack 8 — `probe_8_no_none_weighted_regression.py` → holds on the patched tree (good)

```python
# Req 4.6: no-None roster still supports weighted fit + per-member weights honored in prediction.
import sys
import numpy as np
from sklearn.ensemble import VotingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.naive_bayes import GaussianNB

X = np.array([[0, 0], [1, 1], [2, 2], [3, 3], [4, 4], [5, 5]], dtype=float)
y = np.array([0, 0, 0, 1, 1, 1])
sw = np.ones(len(y))

eclf = VotingClassifier(estimators=[('lr', LogisticRegression(solver='liblinear')),
                                    ('nb', GaussianNB())],
                        voting='soft', weights=[1, 5])
try:
    eclf.fit(X, y, sample_weight=sw)
except Exception as e:
    print("FAIL: weighted fit (no None) raised %s: %s" % (type(e).__name__, e))
    sys.exit(1)

# _weights_not_none must reflect both weights when no slot is None
wnn = eclf._weights_not_none
print("_weights_not_none:", wnn)
if list(wnn) != [1, 5]:
    print("FAIL: per-member weights not honored:", wnn)
    sys.exit(1)

pred = eclf.predict(X)
if np.shape(pred) != np.shape(y):
    print("FAIL: predict shape mismatch:", np.shape(pred))
    sys.exit(1)
print("PASS: no-None weighted fit works and weights honored")
sys.exit(0)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1_none_slot_fit.py`

```python
# Req 1.1/1.2 + positive control: fit with sample_weight and a None slot succeeds.
import sys
import numpy as np
from sklearn.ensemble import VotingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.naive_bayes import GaussianNB

X = np.array([[0, 0], [1, 1], [2, 2], [3, 3], [4, 4], [5, 5]], dtype=float)
y = np.array([0, 0, 0, 1, 1, 1])
sw = np.ones(len(y))

eclf = VotingClassifier(estimators=[('lr', LogisticRegression(solver='liblinear')),
                                    ('nb', GaussianNB())])
eclf.set_params(lr=None)
try:
    ret = eclf.fit(X, y, sample_weight=sw)
except Exception as e:
    print("FAIL: fit raised %s: %s" % (type(e).__name__, e))
    sys.exit(1)
if ret is not eclf:
    print("FAIL: fit did not return self")
    sys.exit(1)
print("PASS: fit with None slot + sample_weight succeeded, returned self")
sys.exit(0)
```

Prepatch bug re-encoded as an attack: `True`.

Gold patch: in _BaseVoting.fit, add `if step is None: continue` to the sample_weight support loop so None slots are skipped instead of dereferenced.

8 probes, all HOLD on gold-patched tree; probes 1/2/3 also all VIOLATE at base (AttributeError: 'NoneType' object has no attribute 'fit'), confirming discriminating power. Positive control = probe_1 (fit with None slot + sample_weight succeeds and returns self): HOLDS patched, FAILS at base.

Coverage: probe_1 Req1.1/1.2; probe_2 Req1.4 (only present estimator trained/stored, n=1); probe_3 Req1.3+Req2.1 (refit after set_params removal, predict shape==y); probe_4 Req3.1/3.2/3.3 (present KNN unsupported -> ValueError naming first offender 'knn', mentions sample weights); probe_5 Req3.4 (sample_weight=None skips check, KNN accepted); probe_6 Req4.3 (all-None -> ValueError 'at least one required'); probe_7 Req4.2 (weights length mismatch -> ValueError); probe_8 Req4.6 (no-None weighted fit, per-member weights [1,5] honored via _weights_not_none).

Wrong-fix candidate weak.diff: skips None AND silently skips any unsupported present estimator (drops the ValueError). Probe suite REJECTS it — probe_4 gets TypeError('unexpected keyword sample_weight') at parallel fit instead of the mandated ValueError. Demonstrates the suite discriminates the too-weak reading of Req3. No requirements-conforming alternative found that would fail hidden tests; the gold one-liner is the minimal faithful fix.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 8 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 8 | `probe_1_none_slot_fit.py`, `probe_2_only_present_stored.py`, `probe_3_refit_after_removal.py`, `probe_4_present_unsupported_raises.py`, `probe_5_no_sw_skips_check.py`, `probe_6_all_none_raises.py`, `probe_7_weights_len_mismatch.py`, `probe_8_no_none_weighted_regression.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1_none_slot_fit.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (8):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts, and on this backend both roles put it through the same derivation: every block below is a requirement probe run on the gold-patched tree, and the `machine verdict:` line each role publishes above reports BOTH that its probes hold there and how many candidate patches the probe suite rejected — so the two roles re-ran ONE probe suite and each recorded its own outcome for every probe in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `probe_1_none_slot_fit.py` → holds on the patched tree (good)

Attack 2 — `probe_2_only_present_stored.py` → holds on the patched tree (good)

Attack 3 — `probe_3_refit_after_removal.py` → holds on the patched tree (good)

Attack 4 — `probe_4_present_unsupported_raises.py` → holds on the patched tree (good)

Attack 5 — `probe_5_no_sw_skips_check.py` → holds on the patched tree (good)

Attack 6 — `probe_6_all_none_raises.py` → holds on the patched tree (good)

Attack 7 — `probe_7_weights_len_mismatch.py` → holds on the patched tree (good)

Attack 8 — `probe_8_no_none_weighted_regression.py` → holds on the patched tree (good)

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1_none_slot_fit.py`

```python
# Req 1.1/1.2 + positive control: fit with sample_weight and a None slot succeeds.
import sys
import numpy as np
from sklearn.ensemble import VotingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.naive_bayes import GaussianNB

X = np.array([[0, 0], [1, 1], [2, 2], [3, 3], [4, 4], [5, 5]], dtype=float)
y = np.array([0, 0, 0, 1, 1, 1])
sw = np.ones(len(y))

eclf = VotingClassifier(estimators=[('lr', LogisticRegression(solver='liblinear')),
                                    ('nb', GaussianNB())])
eclf.set_params(lr=None)
try:
    ret = eclf.fit(X, y, sample_weight=sw)
except Exception as e:
    print("FAIL: fit raised %s: %s" % (type(e).__name__, e))
    sys.exit(1)
if ret is not eclf:
    print("FAIL: fit did not return self")
    sys.exit(1)
print("PASS: fit with None slot + sample_weight succeeded, returned self")
sys.exit(0)
```

Prepatch bug re-encoded as an attack: `True`.

Gold patch: in _BaseVoting.fit, add `if step is None: continue` to the sample_weight support loop so None slots are skipped instead of dereferenced.

8 probes, all HOLD on gold-patched tree; probes 1/2/3 also all VIOLATE at base (AttributeError: 'NoneType' object has no attribute 'fit'), confirming discriminating power. Positive control = probe_1 (fit with None slot + sample_weight succeeds and returns self): HOLDS patched, FAILS at base.

Coverage: probe_1 Req1.1/1.2; probe_2 Req1.4 (only present estimator trained/stored, n=1); probe_3 Req1.3+Req2.1 (refit after set_params removal, predict shape==y); probe_4 Req3.1/3.2/3.3 (present KNN unsupported -> ValueError naming first offender 'knn', mentions sample weights); probe_5 Req3.4 (sample_weight=None skips check, KNN accepted); probe_6 Req4.3 (all-None -> ValueError 'at least one required'); probe_7 Req4.2 (weights length mismatch -> ValueError); probe_8 Req4.6 (no-None weighted fit, per-member weights [1,5] honored via _weights_not_none).

Wrong-fix candidate weak.diff: skips None AND silently skips any unsupported present estimator (drops the ValueError). Probe suite REJECTS it — probe_4 gets TypeError('unexpected keyword sample_weight') at parallel fit instead of the mandated ValueError. Demonstrates the suite discriminates the too-weak reading of Req3. No requirements-conforming alternative found that would fail hidden tests; the gold one-liner is the minimal faithful fix.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Patch: sklearn/ensemble/voting.py, `if sample_weight is not None:` loop gains `if step is None: continue`. Verified in-image: (1) fit-with-weights after set_params(lr=None) succeeds on patched (exit 0), and on base raises `AttributeError: 'NoneType' object has no attribute 'fit'` at has_fit_parameter(step,...) (Req1 exactly — the changed observable behavior, correct boundary). (2) predict returns shape (150,) matching y (Req2). (3) Present KNeighborsClassifier that lacks sample_weight raises ValueError containing 'knn' and 'does not support sample weights'; loop raises on first offender in roster order (Req3.1/3.2/3.3); guarded by outer `if sample_weight is not None` so no check when None (Req3.4). (4) Regression guards preserved: all-None roster and empty estimators raise as required (Req4.1/4.3); weights-length, unique-name, set_params(None), and no-None weighted behavior are untouched pre-existing validation (Req4.2/4.4/4.5/4.6). Requirements correctly scope the change as narrow None-slot tolerance and do not invent, forbid, or mispin any behavior.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** requirements.md describes behavior and localizes the fix to sklearn/ensemble/voting.py / _BaseVoting.fit and the two public voting classes (VotingClassifier, VotingRegressor). All identifiers used (VotingClassifier, VotingRegressor, LogisticRegression, RandomForestClassifier, set_params(lr=None), sample_weight, the AttributeError) are either already in the public problem_statement or are public API names / legitimate localization. The fix introduces no new identifiers (it only adds `if step is None: continue`). The doc contains no test function/class names (test_none_estimator_with_weights), no test file path (sklearn/ensemble/tests/test_voting.py), no parametrization ids (X0-y0-voter0 / X1-y1-voter1), no quoted test or gold code, and no case enumeration mirroring the classifier/regressor parametrization beyond the fact — already implied — that _BaseVoting serves both. The prediction-shape criterion (Req 2) is a behavioral translation of the intended output contract, not a verbatim transmission of the assert y_pred.shape == y.shape test line. Req 3's preserved ValueError message reflects pre-existing (context-line) code, not test-derived content. No semantic gold/test reconstruction found.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
