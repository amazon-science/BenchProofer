# P2 adversarial audit — scikit-learn__scikit-learn-25973

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 6 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 6 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 6 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (6):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
# Requirement 1.1 / 1.2 / positive control:
# cv as a single-pass generator of (train,test) splits -> fit completes, sets attrs.
import numpy as np
from sklearn.datasets import make_classification
from sklearn.model_selection import LeaveOneGroupOut
from sklearn.neighbors import KNeighborsClassifier
from sklearn.feature_selection import SequentialFeatureSelector

X, y = make_classification(random_state=0)
groups = np.zeros_like(y, dtype=int)
groups[y.size // 2:] = 1
cv = LeaveOneGroupOut()
splits = cv.split(X, y, groups=groups)   # a one-pass generator
knc = KNeighborsClassifier(n_neighbors=5)
sfs = SequentialFeatureSelector(knc, n_features_to_select=5, cv=splits)
try:
    sfs.fit(X, y)
except Exception as e:
    print("FAIL: fit raised", type(e).__name__, e)
    raise SystemExit(1)
assert hasattr(sfs, "support_") and sfs.support_ is not None
assert int(sfs.support_.sum()) == 5, sfs.support_.sum()
assert sfs.n_features_to_select_ == 5, sfs.n_features_to_select_
print("OK: fit completed with generator cv; support sum=5, n_features_to_select_=5")
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
# Requirement 1.2 / 1.3: the SAME set of splits is reused for every evaluation.
# A one-pass generator must yield the identical result to a materialized reusable
# list of the same splits (i.e. it is normalized once and reused, not exhausted).
import numpy as np
from sklearn.datasets import make_classification
from sklearn.model_selection import LeaveOneGroupOut
from sklearn.neighbors import KNeighborsClassifier
from sklearn.feature_selection import SequentialFeatureSelector

X, y = make_classification(random_state=0)
groups = np.zeros_like(y, dtype=int)
groups[y.size // 2:] = 1
cv = LeaveOneGroupOut()

split_list = list(cv.split(X, y, groups=groups))    # reusable list
gen = cv.split(X, y, groups=groups)                  # fresh one-pass generator

knc = KNeighborsClassifier(n_neighbors=5)
sfs_list = SequentialFeatureSelector(knc, n_features_to_select=5, cv=list(split_list)).fit(X, y)
sfs_gen  = SequentialFeatureSelector(knc, n_features_to_select=5, cv=gen).fit(X, y)

m_list = sfs_list.support_
m_gen = sfs_gen.support_
print("list mask :", m_list.astype(int).tolist())
print("gen  mask :", m_gen.astype(int).tolist())
if not np.array_equal(m_list, m_gen):
    print("FAIL: generator cv did not reuse the same splits as the list")
    raise SystemExit(1)
print("OK: generator cv yields identical mask to reusable list of splits")
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
# Requirement 2.1 / 3.6: integer cv still works; backward direction produces
# complementary support mask. Deterministic behavior preserved.
import numpy as np
from sklearn.datasets import make_regression
from sklearn.linear_model import LinearRegression
from sklearn.feature_selection import SequentialFeatureSelector

X, y = make_regression(n_features=10, n_informative=5, random_state=0)
lr = LinearRegression()

fwd = SequentialFeatureSelector(lr, n_features_to_select=5, cv=3, direction="forward").fit(X, y)
bwd = SequentialFeatureSelector(lr, n_features_to_select=5, cv=3, direction="backward").fit(X, y)
print("forward  sum:", int(fwd.support_.sum()), "n_:", fwd.n_features_to_select_)
print("backward sum:", int(bwd.support_.sum()), "n_:", bwd.n_features_to_select_)
assert fwd.support_.dtype == bool
assert int(fwd.support_.sum()) == 5 and fwd.n_features_to_select_ == 5
assert int(bwd.support_.sum()) == 5 and bwd.n_features_to_select_ == 5
# determinism: same fit again -> same mask
fwd2 = SequentialFeatureSelector(lr, n_features_to_select=5, cv=3, direction="forward").fit(X, y)
assert np.array_equal(fwd.support_, fwd2.support_)
print("OK: integer cv forward/backward work, boolean mask, deterministic")
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
# Requirement 3.1 / 3.2 / 3.3: validation ValueErrors preserved.
import numpy as np
from sklearn.datasets import make_regression
from sklearn.linear_model import LinearRegression
from sklearn.feature_selection import SequentialFeatureSelector

X, y = make_regression(n_features=5, random_state=0)
lr = LinearRegression()

def expect_valueerror(kwargs, label):
    try:
        SequentialFeatureSelector(lr, **kwargs).fit(X, y)
    except ValueError as e:
        print(f"OK {label}: ValueError -> {e}")
        return
    print(f"FAIL {label}: no ValueError raised")
    raise SystemExit(1)

# 3.1 n_features_to_select out of range (n_features=5 => valid 1..4)
expect_valueerror(dict(n_features_to_select=10), "3.1 out-of-range")
# 3.2 tol set while n_features_to_select left at deprecated default ("warn")
expect_valueerror(dict(tol=1e-3), "3.2 tol-with-default")
# 3.3 negative tol with forward selection
expect_valueerror(dict(tol=-1e-3, n_features_to_select="auto", direction="forward"),
                  "3.3 neg-tol-forward")
print("OK: all validation ValueErrors preserved")
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
# Requirement 3.4: FutureWarning emitted when n_features_to_select left at
# deprecated default.
import warnings
import numpy as np
from sklearn.datasets import make_regression
from sklearn.linear_model import LinearRegression
from sklearn.feature_selection import SequentialFeatureSelector

X, y = make_regression(n_features=5, n_informative=3, random_state=0)
lr = LinearRegression()
with warnings.catch_warnings(record=True) as w:
    warnings.simplefilter("always")
    SequentialFeatureSelector(lr, cv=3).fit(X, y)  # default n_features_to_select
fw = [x for x in w if issubclass(x.category, FutureWarning)]
for x in fw:
    print("FutureWarning:", x.message)
if not fw:
    print("FAIL: no FutureWarning emitted for deprecated default")
    raise SystemExit(1)
print("OK: FutureWarning emitted")
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
# Requirement 1.4: normalization takes classifier-ness into account so that an
# integer cv on a classifier selects the STRATIFIED default. Discriminating:
# with an ordered (unshuffled) target, integer cv=3 on a classifier must match
# StratifiedKFold(3) splits and (for imbalanced ordering) differ from plain
# KFold(3) splits, proving check_cv(..., classifier=True) was used.
import numpy as np
from sklearn.model_selection import StratifiedKFold, KFold
from sklearn.neighbors import KNeighborsClassifier
from sklearn.feature_selection import SequentialFeatureSelector

rng = np.random.RandomState(0)
n = 60
X = rng.randn(n, 8)
# strongly ordered labels so KFold vs StratifiedKFold give very different folds
y = np.array([0]*(n//2) + [1]*(n//2))
knc = KNeighborsClassifier(n_neighbors=3)

base = SequentialFeatureSelector(knc, n_features_to_select=4, cv=3).fit(X, y)
strat = SequentialFeatureSelector(
    knc, n_features_to_select=4, cv=list(StratifiedKFold(3).split(X, y))).fit(X, y)
plain = SequentialFeatureSelector(
    knc, n_features_to_select=4, cv=list(KFold(3).split(X, y))).fit(X, y)

print("int-cv  mask:", base.support_.astype(int).tolist())
print("strat   mask:", strat.support_.astype(int).tolist())
print("plain   mask:", plain.support_.astype(int).tolist())
if not np.array_equal(base.support_, strat.support_):
    print("FAIL: integer cv on classifier did not match StratifiedKFold (not stratified)")
    raise SystemExit(1)
print("OK: integer cv on classifier matches StratifiedKFold (stratified default honored)")
# informational: whether it also differs from plain KFold
print("differs from plain KFold:", not np.array_equal(base.support_, plain.support_))
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
# Requirement 1.1 / 1.2 / positive control:
# cv as a single-pass generator of (train,test) splits -> fit completes, sets attrs.
import numpy as np
from sklearn.datasets import make_classification
from sklearn.model_selection import LeaveOneGroupOut
from sklearn.neighbors import KNeighborsClassifier
from sklearn.feature_selection import SequentialFeatureSelector

X, y = make_classification(random_state=0)
groups = np.zeros_like(y, dtype=int)
groups[y.size // 2:] = 1
cv = LeaveOneGroupOut()
splits = cv.split(X, y, groups=groups)   # a one-pass generator
knc = KNeighborsClassifier(n_neighbors=5)
sfs = SequentialFeatureSelector(knc, n_features_to_select=5, cv=splits)
try:
    sfs.fit(X, y)
except Exception as e:
    print("FAIL: fit raised", type(e).__name__, e)
    raise SystemExit(1)
assert hasattr(sfs, "support_") and sfs.support_ is not None
assert int(sfs.support_.sum()) == 5, sfs.support_.sum()
assert sfs.n_features_to_select_ == 5, sfs.n_features_to_select_
print("OK: fit completed with generator cv; support sum=5, n_features_to_select_=5")
```

Prepatch bug re-encoded as an attack: `True`.

Instance scikit-learn-25973: SequentialFeatureSelector must accept single-pass iterables of CV splits (normalize cv once via check_cv at start of fit, classifier-aware).

Probes (all HOLD on gold-patched tree):
- probe_1 (Req 1.1/1.2, POSITIVE CONTROL): generator cv (LeaveOneGroupOut.split) -> fit completes, support sum=5, n_features_to_select_=5. HOLDS patched; VIOLATED at base (IndexError list index out of range). Discriminates.
- probe_2 (Req 1.2/1.3, second positive control): generator cv yields identical support mask to a reusable list of the same splits (proves splits reused, not exhausted). HOLDS patched; VIOLATED at base (IndexError in cross_val_score).
- probe_3 (Req 2.1/2.3/3.6): integer cv forward+backward produce boolean masks of exactly 5 features, deterministic. HOLDS patched.
- probe_4 (Req 3.1/3.2/3.3): ValueError preserved for out-of-range n_features_to_select, tol-with-deprecated-default, negative-tol+forward. HOLDS patched.
- probe_5 (Req 3.4): FutureWarning emitted for deprecated default n_features_to_select. HOLDS patched.
- probe_6 (Req 1.4, discriminating regression): integer cv=3 on a classifier with strongly-ordered labels must match StratifiedKFold(3), not plain KFold(3). HOLDS patched; HOLDS at base (base stratifies inside cross_val_score).

Candidate wrong-fix exercised & REJECTED:
- weak_A: uses check_cv(self.cv, y) WITHOUT classifier=is_classifier(self.estimator) (lazy reading of Req 1.3 that ignores Req 1.4). probes 1-5 HOLD but probe_6 VIOLATED (int-cv mask [0,1,0,0,1,1,1,0] matches plain KFold, not StratifiedKFold [1,0,1,1,1,0,0,0]) — the classifier-unaware normalization degrades integer-cv stratification. Suite discriminates this wrong implementation, confirming Req 1.4 is properly encoded and not too weak.

Verdict: SOUND. 6 distinct probes all hold on patched tree; positive controls (probe_1, probe_2) fail at base and hold patched; weak-fix candidate rejected by the suite. No violation found; requirements are not satisfiable by the probe-conforming lazy fix that would misbehave on stratification.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 6 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 6 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (6):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

_The 6 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts, and on this backend both roles put it through the same derivation: every block below is a requirement probe run on the gold-patched tree, and the `machine verdict:` line each role publishes above reports BOTH that its probes hold there and how many candidate patches the probe suite rejected — so the two roles re-ran ONE probe suite and each recorded its own outcome for every probe in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `probe_1.py` → holds on the patched tree (good)

Attack 2 — `probe_2.py` → holds on the patched tree (good)

Attack 3 — `probe_3.py` → holds on the patched tree (good)

Attack 4 — `probe_4.py` → holds on the patched tree (good)

Attack 5 — `probe_5.py` → holds on the patched tree (good)

Attack 6 — `probe_6.py` → holds on the patched tree (good)

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
# Requirement 1.1 / 1.2 / positive control:
# cv as a single-pass generator of (train,test) splits -> fit completes, sets attrs.
import numpy as np
from sklearn.datasets import make_classification
from sklearn.model_selection import LeaveOneGroupOut
from sklearn.neighbors import KNeighborsClassifier
from sklearn.feature_selection import SequentialFeatureSelector

X, y = make_classification(random_state=0)
groups = np.zeros_like(y, dtype=int)
groups[y.size // 2:] = 1
cv = LeaveOneGroupOut()
splits = cv.split(X, y, groups=groups)   # a one-pass generator
knc = KNeighborsClassifier(n_neighbors=5)
sfs = SequentialFeatureSelector(knc, n_features_to_select=5, cv=splits)
try:
    sfs.fit(X, y)
except Exception as e:
    print("FAIL: fit raised", type(e).__name__, e)
    raise SystemExit(1)
assert hasattr(sfs, "support_") and sfs.support_ is not None
assert int(sfs.support_.sum()) == 5, sfs.support_.sum()
assert sfs.n_features_to_select_ == 5, sfs.n_features_to_select_
print("OK: fit completed with generator cv; support sum=5, n_features_to_select_=5")
```

Prepatch bug re-encoded as an attack: `True`.

Instance scikit-learn-25973: SequentialFeatureSelector must accept single-pass iterables of CV splits (normalize cv once via check_cv at start of fit, classifier-aware).

Probes (all HOLD on gold-patched tree):
- probe_1 (Req 1.1/1.2, POSITIVE CONTROL): generator cv (LeaveOneGroupOut.split) -> fit completes, support sum=5, n_features_to_select_=5. HOLDS patched; VIOLATED at base (IndexError list index out of range). Discriminates.
- probe_2 (Req 1.2/1.3, second positive control): generator cv yields identical support mask to a reusable list of the same splits (proves splits reused, not exhausted). HOLDS patched; VIOLATED at base (IndexError in cross_val_score).
- probe_3 (Req 2.1/2.3/3.6): integer cv forward+backward produce boolean masks of exactly 5 features, deterministic. HOLDS patched.
- probe_4 (Req 3.1/3.2/3.3): ValueError preserved for out-of-range n_features_to_select, tol-with-deprecated-default, negative-tol+forward. HOLDS patched.
- probe_5 (Req 3.4): FutureWarning emitted for deprecated default n_features_to_select. HOLDS patched.
- probe_6 (Req 1.4, discriminating regression): integer cv=3 on a classifier with strongly-ordered labels must match StratifiedKFold(3), not plain KFold(3). HOLDS patched; HOLDS at base (base stratifies inside cross_val_score).

Candidate wrong-fix exercised & REJECTED:
- weak_A: uses check_cv(self.cv, y) WITHOUT classifier=is_classifier(self.estimator) (lazy reading of Req 1.3 that ignores Req 1.4). probes 1-5 HOLD but probe_6 VIOLATED (int-cv mask [0,1,0,0,1,1,1,0] matches plain KFold, not StratifiedKFold [1,0,1,1,1,0,0,0]) — the classifier-unaware normalization degrades integer-cv stratification. Suite discriminates this wrong implementation, confirming Req 1.4 is properly encoded and not too weak.

Verdict: SOUND. 6 distinct probes all hold on patched tree; positive controls (probe_1, probe_2) fail at base and hold patched; weak-fix candidate rejected by the suite. No violation found; requirements are not satisfiable by the probe-conforming lazy fix that would misbehave on stratification.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Probed both directions. Patched: 'HOLDS exit=0; support sum 5 n_sel 5'. Base: 'VIOLATED exit=1 IndexError: list index out of range' in cross_val_score/_aggregate_score_dicts — the exact failure from the problem_statement. Requirement 1.4 correctly captures the classifier=is_classifier(...) argument to check_cv (stratified-vs-plain default). Boundary is the changed behavior (cv normalized once + reused), not a narrow helper slice.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The requirements describe behavior derivable from the PUBLIC problem_statement (which itself contains the full LeaveOneGroupOut/KNeighborsClassifier/cv=splits reproduction that the sole FAIL_TO_PASS test test_cv_generator_support replicates). Identifiers named in the doc (check_cv, is_classifier, cross_val_score, _get_best_new_feature_score, SequentialFeatureSelector.fit) are all pre-existing public scikit-learn APIs / existing methods — legitimate localization, not fix-invented names. No test file paths, test function names, parametrization ids, or quoted test/gold code appear. Requirement 3's validation/deprecation enumeration corresponds to PASS_TO_PASS tests but describes existing, source-discoverable class behavior as regression preservation rather than transmitting the tests. Requirement 1.4's classifier/stratification detail reflects correct use of check_cv (behavioral), not hidden-test reconstruction.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
