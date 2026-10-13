# P2 adversarial audit — scikit-learn__scikit-learn-13496

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
"""R1.1/R1.2/R1.3/R1.4: warm_start constructor param accepted, default False,
retained, forwarded to parent. Positive control (fails at base: TypeError)."""
import sys
from sklearn.ensemble import IsolationForest

# R1.1 + R1.2: accepted, default disabled
clf = IsolationForest(n_estimators=5, behaviour='old')
print("default warm_start =", clf.warm_start)
if clf.warm_start is not False:
    print("FAIL: default not False")
    sys.exit(1)

# R1.3: explicit value retained
clf_t = IsolationForest(warm_start=True, n_estimators=5, behaviour='old')
print("explicit warm_start =", clf_t.warm_start)
if clf_t.warm_start is not True:
    print("FAIL: explicit value not retained")
    sys.exit(1)

# R1.4: forwarded to parent (get_params reflects it; parent BaseBagging owns attr)
params = clf_t.get_params()
print("get_params warm_start =", params.get("warm_start"))
if params.get("warm_start") is not True:
    print("FAIL: not forwarded/exposed in params")
    sys.exit(1)

print("PASS")
sys.exit(0)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""R2.1/R2.2/R2.3: warm-start incremental growth. After growing n_estimators,
ensemble has exactly the new count, earlier tree objects preserved by identity."""
import sys
import numpy as np
from sklearn.ensemble import IsolationForest

rng = np.random.RandomState(0)
X = rng.randn(50, 4)

clf = IsolationForest(n_estimators=10, warm_start=True, behaviour='old',
                      random_state=0)
clf.fit(X)
first = list(clf.estimators_)
print("after first fit:", len(clf.estimators_))
if len(clf.estimators_) != 10:
    print("FAIL: first fit wrong count")
    sys.exit(1)

clf.set_params(n_estimators=20)
clf.fit(X)
print("after grow fit:", len(clf.estimators_))
# R2.1: exactly newly requested count
if len(clf.estimators_) != 20:
    print("FAIL: grown count != 20")
    sys.exit(1)

# R2.2/R2.3: earlier trees are the SAME objects at same positions
for i, e in enumerate(first):
    if clf.estimators_[i] is not e:
        print("FAIL: tree", i, "not preserved by identity")
        sys.exit(1)
print("first 10 trees preserved by identity")
print("PASS")
sys.exit(0)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""R1.5: warm_start changeable via set_params and honored by subsequent fit.
Start disabled -> fit rebuilds; enable -> grow appends preserving trees."""
import sys
import numpy as np
from sklearn.ensemble import IsolationForest

rng = np.random.RandomState(1)
X = rng.randn(40, 3)

clf = IsolationForest(n_estimators=8, warm_start=False, behaviour='old',
                      random_state=0)
clf.fit(X)
old_trees = list(clf.estimators_)

# flip via set_params
clf.set_params(warm_start=True)
print("warm_start after set_params =", clf.warm_start)
if clf.warm_start is not True:
    print("FAIL: set_params did not update warm_start")
    sys.exit(1)

clf.set_params(n_estimators=15)
clf.fit(X)
print("count after honored warm-start grow:", len(clf.estimators_))
if len(clf.estimators_) != 15:
    print("FAIL: subsequent fit did not honor updated warm_start (count)")
    sys.exit(1)
# trees preserved => warm_start honored, not rebuilt
for i, e in enumerate(old_trees):
    if clf.estimators_[i] is not e:
        print("FAIL: fit did not honor warm_start (trees rebuilt)")
        sys.exit(1)
print("PASS")
sys.exit(0)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""R3.1: default (warm_start disabled) => each fit builds a fresh ensemble of
exactly requested size, independent of previous fit (no accumulation, new objs)."""
import sys
import numpy as np
from sklearn.ensemble import IsolationForest

rng = np.random.RandomState(2)
X = rng.randn(60, 5)

clf = IsolationForest(n_estimators=12, behaviour='old', random_state=0)
clf.fit(X)
trees_a = list(clf.estimators_)
print("first fit count:", len(clf.estimators_))
if len(clf.estimators_) != 12:
    print("FAIL: first fit count")
    sys.exit(1)

# refit without changing n_estimators: fresh ensemble, still 12, new objects
clf.fit(X)
print("second fit count:", len(clf.estimators_))
if len(clf.estimators_) != 12:
    print("FAIL: default fit accumulated trees")
    sys.exit(1)
# fresh => at least not the same identical object list order preserved
same = sum(1 for i, e in enumerate(trees_a) if clf.estimators_[i] is e)
print("identical trees carried over (should be 0 for fresh):", same)
if same != 0:
    print("FAIL: default refit reused old trees")
    sys.exit(1)
print("PASS")
sys.exit(0)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""R3.2/R3.3/R3.4: preserved behavior — params stored, sparse+dense fit,
established errors, and fitted scoring/decision/predict interfaces intact."""
import sys
import numpy as np
from scipy.sparse import csc_matrix
from sklearn.ensemble import IsolationForest

# R3.2: all classic params stored with meaning
clf = IsolationForest(n_estimators=7, max_samples=16, max_features=0.5,
                      bootstrap=True, contamination=0.1, behaviour='new',
                      n_jobs=1, random_state=3, verbose=0)
p = clf.get_params()
for k, v in dict(n_estimators=7, max_samples=16, max_features=0.5,
                 bootstrap=True, behaviour='new', random_state=3).items():
    if p.get(k) != v:
        print("FAIL: param", k, "=", p.get(k))
        sys.exit(1)
print("params stored OK")

# R3.3: dense + sparse fit
rng = np.random.RandomState(3)
X = rng.randn(40, 4)
clf.fit(X)
Xs = csc_matrix(X)
IsolationForest(n_estimators=5, behaviour='new', random_state=0).fit(Xs)
print("dense+sparse fit OK")

# R3.3: established error for out-of-range max_samples
try:
    IsolationForest(max_samples=1000, behaviour='new').fit(X[:20])
    # max_samples > n_samples only warns; use invalid string to force error
except Exception:
    pass
raised = False
try:
    IsolationForest(max_samples="bogus", behaviour='new').fit(X)
except ValueError:
    raised = True
print("invalid max_samples raises ValueError:", raised)
if not raised:
    print("FAIL: invalid max_samples did not raise")
    sys.exit(1)

# R3.4: fitted interfaces present and shaped
clf2 = IsolationForest(n_estimators=10, behaviour='new', contamination=0.1,
                       random_state=0).fit(X)
sc = clf2.score_samples(X)
df = clf2.decision_function(X)
pr = clf2.predict(X)
print("shapes:", sc.shape, df.shape, pr.shape, "preds set:", set(np.unique(pr)))
if not (sc.shape == (40,) and df.shape == (40,) and pr.shape == (40,)):
    print("FAIL: interface shapes")
    sys.exit(1)
if not set(np.unique(pr)).issubset({-1, 1}):
    print("FAIL: predict values")
    sys.exit(1)
print("PASS")
sys.exit(0)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
"""R3.5: warm_start enabled but n_estimators NOT increased before refit =>
ensemble not corrupted; previously fitted trees left intact (same count/objects)."""
import sys
import numpy as np
from sklearn.ensemble import IsolationForest

rng = np.random.RandomState(5)
X = rng.randn(45, 3)

clf = IsolationForest(n_estimators=9, warm_start=True, behaviour='old',
                      random_state=0)
clf.fit(X)
trees = list(clf.estimators_)
print("count after fit:", len(clf.estimators_))

# refit WITHOUT increasing n_estimators
clf.fit(X)
print("count after no-increase refit:", len(clf.estimators_))
if len(clf.estimators_) != 9:
    print("FAIL: count changed / corrupted")
    sys.exit(1)
for i, e in enumerate(trees):
    if clf.estimators_[i] is not e:
        print("FAIL: tree", i, "not intact")
        sys.exit(1)
# still usable
_ = clf.predict(X)
print("trees intact and estimator still usable")
print("PASS")
sys.exit(0)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""R1.1/R1.2/R1.3/R1.4: warm_start constructor param accepted, default False,
retained, forwarded to parent. Positive control (fails at base: TypeError)."""
import sys
from sklearn.ensemble import IsolationForest

# R1.1 + R1.2: accepted, default disabled
clf = IsolationForest(n_estimators=5, behaviour='old')
print("default warm_start =", clf.warm_start)
if clf.warm_start is not False:
    print("FAIL: default not False")
    sys.exit(1)

# R1.3: explicit value retained
clf_t = IsolationForest(warm_start=True, n_estimators=5, behaviour='old')
print("explicit warm_start =", clf_t.warm_start)
if clf_t.warm_start is not True:
    print("FAIL: explicit value not retained")
    sys.exit(1)

# R1.4: forwarded to parent (get_params reflects it; parent BaseBagging owns attr)
params = clf_t.get_params()
print("get_params warm_start =", params.get("warm_start"))
if params.get("warm_start") is not True:
    print("FAIL: not forwarded/exposed in params")
    sys.exit(1)

print("PASS")
sys.exit(0)
```

Prepatch bug re-encoded as an attack: `True`.

Instance exposes warm_start on IsolationForest.__init__ and forwards it to BaseBagging. 6 probes cover all 13 criteria across R1-R3:
- probe_1 (R1.1/1.2/1.3/1.4): warm_start accepted, defaults False, explicit value retained, exposed via get_params. POSITIVE CONTROL: FAILS at base (TypeError: __init__() got unexpected kwarg 'warm_start'), HOLDS patched.
- probe_2 (R2.1/2.2/2.3): warm-start grow => exactly new count (10->20), first 10 tree objects preserved by identity.
- probe_3 (R1.5): warm_start flippable via set_params, honored by subsequent fit (count grows, old trees preserved).
- probe_4 (R3.1): default (disabled) refit builds fresh ensemble, exactly requested size, 0 old trees reused.
- probe_5 (R3.2/3.3/3.4): all classic params stored; dense+sparse fit; invalid max_samples='bogus' raises ValueError; fitted score_samples/decision_function/predict shapes and {-1,1} preds intact. (Dropped an over-strict contamination=0.6 subcheck — this sklearn version does not raise there.)
- probe_6 (R3.5): warm_start enabled, n_estimators NOT increased => count unchanged (9), trees intact, estimator still usable.

All 6 HOLD on gold-patched tree. Positive control discriminates (base TypeError).

CANDIDATE PATCH (weak.diff): adds warm_start to signature but forwards a hardcoded warm_start=False to super() (the lazy/partial fix a weak reading permits). REJECTED by the suite: probe_1 fails (explicit True not retained -> get_params False) and probe_2 fails (no incremental growth). Demonstrates the probe suite discriminates a wrong implementation.

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
"""R1.1/R1.2/R1.3/R1.4: warm_start constructor param accepted, default False,
retained, forwarded to parent. Positive control (fails at base: TypeError)."""
import sys
from sklearn.ensemble import IsolationForest

# R1.1 + R1.2: accepted, default disabled
clf = IsolationForest(n_estimators=5, behaviour='old')
print("default warm_start =", clf.warm_start)
if clf.warm_start is not False:
    print("FAIL: default not False")
    sys.exit(1)

# R1.3: explicit value retained
clf_t = IsolationForest(warm_start=True, n_estimators=5, behaviour='old')
print("explicit warm_start =", clf_t.warm_start)
if clf_t.warm_start is not True:
    print("FAIL: explicit value not retained")
    sys.exit(1)

# R1.4: forwarded to parent (get_params reflects it; parent BaseBagging owns attr)
params = clf_t.get_params()
print("get_params warm_start =", params.get("warm_start"))
if params.get("warm_start") is not True:
    print("FAIL: not forwarded/exposed in params")
    sys.exit(1)

print("PASS")
sys.exit(0)
```

Prepatch bug re-encoded as an attack: `True`.

Instance exposes warm_start on IsolationForest.__init__ and forwards it to BaseBagging. 6 probes cover all 13 criteria across R1-R3:
- probe_1 (R1.1/1.2/1.3/1.4): warm_start accepted, defaults False, explicit value retained, exposed via get_params. POSITIVE CONTROL: FAILS at base (TypeError: __init__() got unexpected kwarg 'warm_start'), HOLDS patched.
- probe_2 (R2.1/2.2/2.3): warm-start grow => exactly new count (10->20), first 10 tree objects preserved by identity.
- probe_3 (R1.5): warm_start flippable via set_params, honored by subsequent fit (count grows, old trees preserved).
- probe_4 (R3.1): default (disabled) refit builds fresh ensemble, exactly requested size, 0 old trees reused.
- probe_5 (R3.2/3.3/3.4): all classic params stored; dense+sparse fit; invalid max_samples='bogus' raises ValueError; fitted score_samples/decision_function/predict shapes and {-1,1} preds intact. (Dropped an over-strict contamination=0.6 subcheck — this sklearn version does not raise there.)
- probe_6 (R3.5): warm_start enabled, n_estimators NOT increased => count unchanged (9), trees intact, estimator still usable.

All 6 HOLD on gold-patched tree. Positive control discriminates (base TypeError).

CANDIDATE PATCH (weak.diff): adds warm_start to signature but forwards a hardcoded warm_start=False to super() (the lazy/partial fix a weak reading permits). REJECTED by the suite: probe_1 fails (explicit True not retained -> get_params False) and probe_2 fails (no incremental growth). Demonstrates the probe suite discriminates a wrong implementation.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Patch adds warm_start param to IsolationForest.__init__ (default False) and forwards it to super().__init__. Probe on gold tree: ALL OK (exit 0). Probe on base: fails at 'warm_start not in signature'. Requirement boundary matches the change exactly.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The document stays within the public problem_statement, which already asks to expose warm_start in IsolationForest.__init__ (default False), document/forward it, and add a test. Module path sklearn/ensemble/iforest.py and the warm_start name are public. Requirement 2 (exactly the newly-requested tree count; each earlier tree object preserved at its original position; only additional trees built) is a behavioral translation of the hidden test's assertions (len(clf.estimators_)==20; clf.estimators_[0] is tree_1) — describing behavior, not transmitting the test. No test function/file names (test_iforest_warm_start), no parametrization ids, no quoted test or gold code, and no fix-invented identifiers beyond warm_start (itself public). Enumerations in Req 3 (dense/sparse, error cases) reflect general estimator behavior, not the specific PASS_TO_PASS list in a test-shaped way.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
