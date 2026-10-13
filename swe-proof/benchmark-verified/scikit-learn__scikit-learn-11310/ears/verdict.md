# P2 adversarial audit — scikit-learn__scikit-learn-11310

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 7 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 7 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py`, `probe_7.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (7):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
"""Req1.1/1.3/1.4: refit enabled -> refit_time_ present, is a float, >= 0.
POSITIVE CONTROL: holds on patched, fails at base (AttributeError)."""
import numpy as np
from sklearn.datasets import load_iris
from sklearn.svm import SVC
from sklearn.model_selection import GridSearchCV

X, y = load_iris(return_X_y=True)
clf = GridSearchCV(SVC(gamma='scale'), {'C': [0.1, 1.0]}, cv=3, refit=True)
clf.fit(X, y)

if not hasattr(clf, 'refit_time_'):
    print("FAIL: no refit_time_ attribute after refit=True fit")
    raise SystemExit(1)
rt = clf.refit_time_
print("refit_time_ =", repr(rt), "type=", type(rt).__name__)
if not isinstance(rt, float):
    print("FAIL: refit_time_ is not a python float")
    raise SystemExit(1)
if not (rt >= 0):
    print("FAIL: refit_time_ < 0")
    raise SystemExit(1)
print("PASS")
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""Req2.1/2.2: refit disabled -> NO refit_time_ attribute, but cv_results_ still populated."""
import numpy as np
from sklearn.datasets import load_iris
from sklearn.svm import SVC
from sklearn.model_selection import GridSearchCV

X, y = load_iris(return_X_y=True)
clf = GridSearchCV(SVC(gamma='scale'), {'C': [0.1, 1.0]}, cv=3, refit=False)
clf.fit(X, y)

if hasattr(clf, 'refit_time_'):
    print("FAIL: refit_time_ present despite refit=False:", clf.refit_time_)
    raise SystemExit(1)
if not hasattr(clf, 'cv_results_') or 'mean_test_score' not in clf.cv_results_:
    print("FAIL: cv_results_ not populated with refit=False")
    raise SystemExit(1)
print("PASS: no refit_time_, cv_results_ has", len(clf.cv_results_['mean_test_score']), "candidates")
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""Req1.5: refit_time_ measures ONLY the final refit, not the whole search.
A single-candidate search's total fit wall-clock must be substantially larger
than refit_time_ (search does cv splits + refit). refit_time_ must be much
smaller than the overall fit and must be plausible for a single fit.
We assert refit_time_ < total_fit_time (it measures a strict sub-interval),
and refit_time_ is roughly on the order of one fit, not cv-many fits."""
import time
import numpy as np
from sklearn.datasets import load_iris
from sklearn.svm import SVC
from sklearn.model_selection import GridSearchCV

X, y = load_iris(return_X_y=True)
# single candidate, many folds -> search fits estimator cv+1 times total,
# refit is exactly one of them.
clf = GridSearchCV(SVC(gamma='scale'), {'C': [1.0]}, cv=10, refit=True)
t0 = time.time()
clf.fit(X, y)
total = time.time() - t0
rt = clf.refit_time_
print("refit_time_ =", rt, "total fit wall =", total)
# refit is a strict sub-interval of the whole fit
if not (rt <= total):
    print("FAIL: refit_time_ exceeds total fit time")
    raise SystemExit(1)
# sanity: measure one bare refit for scale comparison
from sklearn.base import clone
est = clone(clf.best_estimator_)
t0 = time.time(); est.fit(X, y); one = time.time() - t0
print("one bare fit ~", one)
# refit_time_ should be within a small multiple of a single fit, NOT cv-many.
# Allow generous slack (timing noise) but reject if it looks like the full search.
if one > 0 and rt > 20 * one + 0.05:
    print("FAIL: refit_time_ looks like it includes candidate fits, not just refit")
    raise SystemExit(1)
print("PASS")
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""Req3.1/3.3: best_estimator_ usable for predict/score; best_index_/params/score/n_splits_ present and consistent."""
import numpy as np
from sklearn.datasets import load_iris
from sklearn.svm import SVC
from sklearn.model_selection import GridSearchCV

X, y = load_iris(return_X_y=True)
clf = GridSearchCV(SVC(gamma='scale'), {'C': [0.1, 1.0, 10.0]}, cv=5, refit=True)
clf.fit(X, y)

# best_estimator_ usable
pred = clf.predict(X)
if pred.shape[0] != X.shape[0]:
    print("FAIL: predict returned wrong shape")
    raise SystemExit(1)
sc = clf.score(X, y)
print("score =", sc)

for attr in ('best_index_', 'best_params_', 'best_score_', 'n_splits_'):
    if not hasattr(clf, attr):
        print("FAIL: missing", attr)
        raise SystemExit(1)
if clf.n_splits_ != 5:
    print("FAIL: n_splits_ != 5:", clf.n_splits_)
    raise SystemExit(1)
# best_index_ consistency with cv_results_
bi = clf.best_index_
if clf.cv_results_['params'][bi] != clf.best_params_:
    print("FAIL: best_index_/best_params_ inconsistent")
    raise SystemExit(1)
if abs(clf.cv_results_['mean_test_score'][bi] - clf.best_score_) > 1e-12:
    print("FAIL: best_score_ inconsistent with cv_results_")
    raise SystemExit(1)
print("PASS: best_params_=", clf.best_params_, "best_score_=", clf.best_score_)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""Req3.2: cv_results_ still has candidate fit/score timing entries with sensible values."""
import numpy as np
from sklearn.datasets import load_iris
from sklearn.svm import SVC
from sklearn.model_selection import GridSearchCV

X, y = load_iris(return_X_y=True)
clf = GridSearchCV(SVC(gamma='scale'), {'C': [0.1, 1.0]}, cv=3, refit=True)
clf.fit(X, y)

req = ['mean_fit_time', 'std_fit_time', 'mean_score_time', 'std_score_time']
for k in req:
    if k not in clf.cv_results_:
        print("FAIL: missing cv_results_ key", k)
        raise SystemExit(1)
    arr = np.asarray(clf.cv_results_[k])
    if arr.shape[0] != 2:
        print("FAIL: wrong number of candidates for", k)
        raise SystemExit(1)
    if np.any(arr < 0) or np.any(~np.isfinite(arr)):
        print("FAIL: invalid timing values in", k, arr)
        raise SystemExit(1)
print("PASS: fit/score timing entries present and non-negative")
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
"""Req3.4: refit works both WITH y and WITHOUT y (unsupervised), and
refit_time_ is set in both cases. Uses KMeans (fit(X) no y)."""
import numpy as np
from sklearn.datasets import load_iris
from sklearn.cluster import KMeans
from sklearn.model_selection import GridSearchCV

X, _ = load_iris(return_X_y=True)
# unsupervised: no y passed to fit; scoring via estimator's own score
clf = GridSearchCV(KMeans(n_init=3, random_state=0), {'n_clusters': [2, 3]},
                   cv=3, refit=True)
clf.fit(X)  # no y

if not hasattr(clf, 'refit_time_'):
    print("FAIL: no refit_time_ for no-y refit")
    raise SystemExit(1)
if not isinstance(clf.refit_time_, float) or clf.refit_time_ < 0:
    print("FAIL: bad refit_time_ for no-y refit:", clf.refit_time_)
    raise SystemExit(1)
# best_estimator_ usable
labels = clf.predict(X)
if labels.shape[0] != X.shape[0]:
    print("FAIL: predict shape wrong")
    raise SystemExit(1)
print("PASS: no-y refit_time_ =", clf.refit_time_)
```

Attack 7 — `probe_7.py` → holds on the patched tree (good)

```python
"""Req1.2/1.5: refit_time_ is an ACTUAL wall-clock measurement of the refit,
not a constant. Use a slow estimator that sleeps SLEEP seconds per fit;
refit_time_ must reflect that (>= most of one sleep), discriminating a
constant/zero placeholder from a real before/after measurement."""
import time
import numpy as np
from sklearn.base import BaseEstimator, ClassifierMixin
from sklearn.model_selection import GridSearchCV

SLEEP = 0.5

class SlowClf(BaseEstimator, ClassifierMixin):
    def __init__(self, p=1):
        self.p = p
    def fit(self, X, y):
        time.sleep(SLEEP)
        self.classes_ = np.unique(y)
        return self
    def predict(self, X):
        return np.full(np.asarray(X).shape[0], self.classes_[0])
    def score(self, X, y=None):
        return 1.0

X = np.random.RandomState(0).rand(30, 3)
y = np.array([0, 1, 2] * 10)
clf = GridSearchCV(SlowClf(), {'p': [1]}, cv=3, refit=True)
clf.fit(X, y)
rt = clf.refit_time_
print("refit_time_ =", rt, "expected ~>=", SLEEP)
# A genuine measurement of the single slow refit must be at least ~most of SLEEP.
if rt < 0.8 * SLEEP:
    print("FAIL: refit_time_ too small -> not an actual measurement of the refit")
    raise SystemExit(1)
# And it must not include the cv candidate fits (3 folds -> would be ~>=3*SLEEP)
if rt > 2 * SLEEP:
    print("FAIL: refit_time_ too large -> includes candidate fits, not just refit")
    raise SystemExit(1)
print("PASS")
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Req1.1/1.3/1.4: refit enabled -> refit_time_ present, is a float, >= 0.
POSITIVE CONTROL: holds on patched, fails at base (AttributeError)."""
import numpy as np
from sklearn.datasets import load_iris
from sklearn.svm import SVC
from sklearn.model_selection import GridSearchCV

X, y = load_iris(return_X_y=True)
clf = GridSearchCV(SVC(gamma='scale'), {'C': [0.1, 1.0]}, cv=3, refit=True)
clf.fit(X, y)

if not hasattr(clf, 'refit_time_'):
    print("FAIL: no refit_time_ attribute after refit=True fit")
    raise SystemExit(1)
rt = clf.refit_time_
print("refit_time_ =", repr(rt), "type=", type(rt).__name__)
if not isinstance(rt, float):
    print("FAIL: refit_time_ is not a python float")
    raise SystemExit(1)
if not (rt >= 0):
    print("FAIL: refit_time_ < 0")
    raise SystemExit(1)
print("PASS")
```

Prepatch bug re-encoded as an attack: `True`.

7 probes covering all 3 requirements. PATCHED: all 7 HOLD. BASE: positive control probe_1 FAILS (AttributeError, no refit_time_) and HOLDS patched -> discriminating power confirmed. Also probe_7 fails at base.

Probe -> criterion:
- probe_1: Req1.1/1.3/1.4 (refit=True -> refit_time_ present, is python float, >=0). POSITIVE CONTROL.
- probe_2: Req2.1/2.2 (refit=False -> NO refit_time_ attribute, cv_results_ still populated).
- probe_3: Req1.5 (refit_time_ is a strict sub-interval of total fit; not cv-many fits).
- probe_4: Req3.1/3.3 (best_estimator_ predict/score usable; best_index_/params_/score_/n_splits_ present & consistent).
- probe_5: Req3.2 (cv_results_ fit/score timing entries present, correct count, non-negative).
- probe_6: Req3.4 (no-y unsupervised refit still sets refit_time_; best_estimator_ usable).
- probe_7: Req1.2/1.5 (refit_time_ is an ACTUAL wall-clock measurement via a 0.5s-sleep estimator, not a constant, and excludes candidate fits).

CANDIDATE PATCH (wrong fix): weak_always.diff sets `self.refit_time_ = 0.0` as a constant placed OUTSIDE the `if self.refit` guard (naive/lazy reading). REJECTED by probe_2 (sets attribute when refit=False, violating Req2.1) and probe_7 (constant 0.0 is not a measurement, violating Req1.2). This demonstrates the suite discriminates wrong implementations along both the omission requirement and the actual-measurement requirement.

Env: python via python; bare `python` not on PATH.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 7 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 7 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py`, `probe_7.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (7):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts, and on this backend both roles put it through the same derivation: every block below is a requirement probe run on the gold-patched tree, and the `machine verdict:` line each role publishes above reports BOTH that its probes hold there and how many candidate patches the probe suite rejected — so the two roles re-ran ONE probe suite and each recorded its own outcome for every probe in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `probe_1.py` → holds on the patched tree (good)

Attack 2 — `probe_2.py` → holds on the patched tree (good)

Attack 3 — `probe_3.py` → holds on the patched tree (good)

Attack 4 — `probe_4.py` → holds on the patched tree (good)

Attack 5 — `probe_5.py` → holds on the patched tree (good)

Attack 6 — `probe_6.py` → holds on the patched tree (good)

Attack 7 — `probe_7.py` → holds on the patched tree (good)

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Req1.1/1.3/1.4: refit enabled -> refit_time_ present, is a float, >= 0.
POSITIVE CONTROL: holds on patched, fails at base (AttributeError)."""
import numpy as np
from sklearn.datasets import load_iris
from sklearn.svm import SVC
from sklearn.model_selection import GridSearchCV

X, y = load_iris(return_X_y=True)
clf = GridSearchCV(SVC(gamma='scale'), {'C': [0.1, 1.0]}, cv=3, refit=True)
clf.fit(X, y)

if not hasattr(clf, 'refit_time_'):
    print("FAIL: no refit_time_ attribute after refit=True fit")
    raise SystemExit(1)
rt = clf.refit_time_
print("refit_time_ =", repr(rt), "type=", type(rt).__name__)
if not isinstance(rt, float):
    print("FAIL: refit_time_ is not a python float")
    raise SystemExit(1)
if not (rt >= 0):
    print("FAIL: refit_time_ < 0")
    raise SystemExit(1)
print("PASS")
```

Prepatch bug re-encoded as an attack: `True`.

7 probes covering all 3 requirements. PATCHED: all 7 HOLD. BASE: positive control probe_1 FAILS (AttributeError, no refit_time_) and HOLDS patched -> discriminating power confirmed. Also probe_7 fails at base.

Probe -> criterion:
- probe_1: Req1.1/1.3/1.4 (refit=True -> refit_time_ present, is python float, >=0). POSITIVE CONTROL.
- probe_2: Req2.1/2.2 (refit=False -> NO refit_time_ attribute, cv_results_ still populated).
- probe_3: Req1.5 (refit_time_ is a strict sub-interval of total fit; not cv-many fits).
- probe_4: Req3.1/3.3 (best_estimator_ predict/score usable; best_index_/params_/score_/n_splits_ present & consistent).
- probe_5: Req3.2 (cv_results_ fit/score timing entries present, correct count, non-negative).
- probe_6: Req3.4 (no-y unsupervised refit still sets refit_time_; best_estimator_ usable).
- probe_7: Req1.2/1.5 (refit_time_ is an ACTUAL wall-clock measurement via a 0.5s-sleep estimator, not a constant, and excludes candidate fits).

CANDIDATE PATCH (wrong fix): weak_always.diff sets `self.refit_time_ = 0.0` as a constant placed OUTSIDE the `if self.refit` guard (naive/lazy reading). REJECTED by probe_2 (sets attribute when refit=False, violating Req2.1) and probe_7 (constant 0.0 is not a measurement, violating Req1.2). This demonstrates the suite discriminates wrong implementations along both the omission requirement and the actual-measurement requirement.

Env: python via python; bare `python` not on PATH.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Patch adds `import time`, wraps the refit fit() call in the `if self.refit:` block with refit_start_time/refit_end_time = time.time() and sets self.refit_time_ = end - start (inside the refit branch, covering both y-present and y-absent paths). Requirements correctly (a) mandate presence+float+>=0 only when refit performed (R1), (b) forbid the attribute when refit disabled (R2), (c) keep everything else additive incl. both y cases (R3). Modeling boundary is the changed observable itself, not a narrow slice. Probe HOLDS patched / VIOLATED base.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The document localizes the change to sklearn/model_selection/_search.py and BaseSearchCV.fit's refit block, and describes the new `refit_time_` attribute. All of this is public: the problem_statement explicitly requests "an attribute `refit_time_` which is simply the time it took to refit the best model" and names BaseSearchCV, GridSearchCV/RandomizedSearchCV, fit/score timing and cv_results_. No test file path (tests/test_search.py), test function name (test_search_cv_timing), or parametrization ids appear. The enumerated properties (attribute present only when refit; value is a Python float; >= 0; measures only the final refit; omitted when refit disabled) coincide with the test's three assertions (hasattr / isinstance float / assert_greater_equal 0) but these are the natural observable properties of an elapsed-time value — translating test checks into behavioral requirements is the intended purpose, not leakage. No fix-invented identifier is transmitted: `refit_time_` originates in the issue itself; the gold's internal locals (refit_start_time/refit_end_time) are NOT present in the document. Requirement 3 (preserving best_index_, best_params_, best_score_, n_splits_, cv_results_ timing, y/no-y fitting) reflects general additive-change reasoning, not the hidden PASS_TO_PASS list.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
