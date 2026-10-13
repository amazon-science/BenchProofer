# P2 adversarial audit — scikit-learn__scikit-learn-25931

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 8 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 8 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py`, `probe_7.py`, `probe_8.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (8):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
"""Req1.1 (POSITIVE CONTROL): fit DataFrame + numeric contamination -> no feature-name UserWarning."""
import warnings
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest

rng = np.random.RandomState(0)
X = pd.DataFrame(rng.randn(100, 4), columns=["a", "b", "c", "d"])

with warnings.catch_warnings(record=True) as w:
    warnings.simplefilter("always")
    clf = IsolationForest(random_state=0, contamination=0.05).fit(X)

msgs = [str(x.message) for x in w]
feat_warns = [m for m in msgs if "feature names" in m]
print("all warnings:", msgs)
print("feature-name warnings:", feat_warns)
if feat_warns:
    print("FAIL: spurious feature-name warning emitted during fit")
    raise SystemExit(1)
print("PASS: no feature-name warning during fit")
raise SystemExit(0)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""Req2.1: contamination='auto' -> offset_ == -0.5."""
import numpy as np
from sklearn.ensemble import IsolationForest

rng = np.random.RandomState(0)
X = rng.randn(80, 3)
clf = IsolationForest(random_state=0, contamination="auto").fit(X)
print("offset_ =", clf.offset_)
if clf.offset_ != -0.5:
    print("FAIL: offset_ not -0.5")
    raise SystemExit(1)
print("PASS")
raise SystemExit(0)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""Req2.2: numeric contamination -> offset_ == percentile of score_samples(X) at 100*contamination."""
import numpy as np
from sklearn.ensemble import IsolationForest

rng = np.random.RandomState(0)
X = rng.randn(120, 5)
cont = 0.1
clf = IsolationForest(random_state=0, contamination=cont).fit(X)
expected = np.percentile(clf.score_samples(X), 100.0 * cont)
print("offset_   =", clf.offset_)
print("expected  =", expected)
if not np.isclose(clf.offset_, expected, rtol=1e-9, atol=1e-9):
    print("FAIL: offset_ != percentile of public score_samples")
    raise SystemExit(1)
print("PASS")
raise SystemExit(0)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""Req3.2: public score_samples STILL warns on an unnamed array when fitted with feature names."""
import warnings
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest

rng = np.random.RandomState(0)
X = pd.DataFrame(rng.randn(100, 4), columns=["a", "b", "c", "d"])
clf = IsolationForest(random_state=0, contamination=0.05).fit(X)

with warnings.catch_warnings(record=True) as w:
    warnings.simplefilter("always")
    clf.score_samples(X.to_numpy())  # unnamed array -> should warn

msgs = [str(x.message) for x in w]
feat_warns = [m for m in msgs if "feature names" in m]
print("warnings:", msgs)
if not feat_warns:
    print("FAIL: expected feature-name warning on public score_samples with unnamed array, got none")
    raise SystemExit(1)
print("PASS: public validation preserved")
raise SystemExit(0)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""Req3.3: decision_function == score_samples - offset_; predict == -1 where decision<0 else +1."""
import numpy as np
from sklearn.ensemble import IsolationForest

rng = np.random.RandomState(0)
X = rng.randn(150, 4)
clf = IsolationForest(random_state=0, contamination=0.1).fit(X)

ss = clf.score_samples(X)
df = clf.decision_function(X)
pred = clf.predict(X)

if not np.allclose(df, ss - clf.offset_, atol=1e-9):
    print("FAIL: decision_function != score_samples - offset_")
    raise SystemExit(1)
expected_pred = np.where(df < 0, -1, 1)
if not np.array_equal(pred, expected_pred):
    print("FAIL: predict mismatch")
    raise SystemExit(1)
print("PASS: decision_function and predict semantics hold")
raise SystemExit(0)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
"""Req3.4: scoring before fit raises NotFittedError."""
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.exceptions import NotFittedError

rng = np.random.RandomState(0)
X = rng.randn(20, 3)

for name, fn in [("score_samples", lambda c: c.score_samples(X)),
                 ("decision_function", lambda c: c.decision_function(X)),
                 ("predict", lambda c: c.predict(X))]:
    clf = IsolationForest(random_state=0)
    try:
        fn(clf)
    except NotFittedError:
        print(name, "-> NotFittedError OK")
        continue
    print("FAIL:", name, "did not raise NotFittedError")
    raise SystemExit(1)
print("PASS")
raise SystemExit(0)
```

Attack 7 — `probe_7.py` → holds on the patched tree (good)

```python
"""Req4.1: CSR-sparse accepted in public scoring methods, and in fit with contamination='auto'."""
import numpy as np
from scipy.sparse import csr_matrix
from sklearn.ensemble import IsolationForest

rng = np.random.RandomState(0)
Xd = rng.randn(100, 4)
Xd[Xd < 0.5] = 0.0  # sparsify
Xcsr = csr_matrix(Xd)

# fit with auto on CSR
clf = IsolationForest(random_state=0, contamination="auto").fit(Xcsr)
# public scoring methods accept CSR
ss = clf.score_samples(Xcsr)
df = clf.decision_function(Xcsr)
pred = clf.predict(Xcsr)
print("shapes:", ss.shape, df.shape, pred.shape)
if ss.shape != (100,) or df.shape != (100,) or pred.shape != (100,):
    print("FAIL: unexpected output shapes for CSR scoring")
    raise SystemExit(1)
print("PASS: CSR accepted in fit(auto) and public scoring")
raise SystemExit(0)
```

Attack 8 — `probe_8.py` → holds on the patched tree (good)

```python
"""Req4.4: no-variance data (all identical) fits and scores without error."""
import numpy as np
from sklearn.ensemble import IsolationForest

X = np.ones((50, 3))
clf = IsolationForest(random_state=0, contamination=0.05).fit(X)
ss = clf.score_samples(X)
pred = clf.predict(X)
print("offset_ =", clf.offset_, "scores[:3] =", ss[:3], "pred[:3] =", pred[:3])
if ss.shape != (50,) or pred.shape != (50,):
    print("FAIL: bad shapes")
    raise SystemExit(1)
print("PASS: no-variance data fit/scored without error")
raise SystemExit(0)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Req1.1 (POSITIVE CONTROL): fit DataFrame + numeric contamination -> no feature-name UserWarning."""
import warnings
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest

rng = np.random.RandomState(0)
X = pd.DataFrame(rng.randn(100, 4), columns=["a", "b", "c", "d"])

with warnings.catch_warnings(record=True) as w:
    warnings.simplefilter("always")
    clf = IsolationForest(random_state=0, contamination=0.05).fit(X)

msgs = [str(x.message) for x in w]
feat_warns = [m for m in msgs if "feature names" in m]
print("all warnings:", msgs)
print("feature-name warnings:", feat_warns)
if feat_warns:
    print("FAIL: spurious feature-name warning emitted during fit")
    raise SystemExit(1)
print("PASS: no feature-name warning during fit")
raise SystemExit(0)
```

Prepatch bug re-encoded as an attack: `True`.

Probes cover: Req1.1 (probe_1, POSITIVE CONTROL — DataFrame + numeric contamination=0.05 fit emits no feature-name UserWarning; HOLDS patched, FAILS at base with the exact spurious warning), Req2.1 (probe_2 offset_==-0.5 for auto), Req2.2 (probe_3 offset_==percentile of public score_samples at 100*contamination), Req3.2 (probe_4 public score_samples STILL warns on unnamed array), Req3.3 (probe_5 decision_function==score_samples-offset_ and predict sign semantics), Req3.4 (probe_6 NotFittedError before fit), Req4.1 (probe_7 CSR accepted in fit-auto and public scoring), Req4.4 (probe_8 no-variance data). ALL 8 HOLD on patched tree. Positive control discriminates (fails at base).

Candidate 'drop_public_validation' (the lazy fix that removes the warning by deleting _validate_data from public score_samples) is REJECTED by probes 3,4,5,7 (breaks dtype conversion / drops the mandated public validation of Req3.2) — suite discriminates wrong implementations. NOTE: the previously-recorded G-EQ/G-PANEL-1 fail used a probe (probe_sparse.py) testing CSR-sparse fit with NUMERIC contamination, but Req4.1 EXPLICITLY disclaims that combination as NOT part of the guaranteed behavior (the validation-free internal path skips the sparse csc conversion). That was an out-of-scope probe, not a genuine spec violation; the requirements are faithful and discriminating.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 8 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 8 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py`, `probe_7.py`, `probe_8.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (8):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts, and on this backend both roles put it through the same derivation: every block below is a requirement probe run on the gold-patched tree, and the `machine verdict:` line each role publishes above reports BOTH that its probes hold there and how many candidate patches the probe suite rejected — so the two roles re-ran ONE probe suite and each recorded its own outcome for every probe in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `probe_1.py` → holds on the patched tree (good)

Attack 2 — `probe_2.py` → holds on the patched tree (good)

Attack 3 — `probe_3.py` → holds on the patched tree (good)

Attack 4 — `probe_4.py` → holds on the patched tree (good)

Attack 5 — `probe_5.py` → holds on the patched tree (good)

Attack 6 — `probe_6.py` → holds on the patched tree (good)

Attack 7 — `probe_7.py` → holds on the patched tree (good)

Attack 8 — `probe_8.py` → holds on the patched tree (good)

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Req1.1 (POSITIVE CONTROL): fit DataFrame + numeric contamination -> no feature-name UserWarning."""
import warnings
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest

rng = np.random.RandomState(0)
X = pd.DataFrame(rng.randn(100, 4), columns=["a", "b", "c", "d"])

with warnings.catch_warnings(record=True) as w:
    warnings.simplefilter("always")
    clf = IsolationForest(random_state=0, contamination=0.05).fit(X)

msgs = [str(x.message) for x in w]
feat_warns = [m for m in msgs if "feature names" in m]
print("all warnings:", msgs)
print("feature-name warnings:", feat_warns)
if feat_warns:
    print("FAIL: spurious feature-name warning emitted during fit")
    raise SystemExit(1)
print("PASS: no feature-name warning during fit")
raise SystemExit(0)
```

Prepatch bug re-encoded as an attack: `True`.

Probes cover: Req1.1 (probe_1, POSITIVE CONTROL — DataFrame + numeric contamination=0.05 fit emits no feature-name UserWarning; HOLDS patched, FAILS at base with the exact spurious warning), Req2.1 (probe_2 offset_==-0.5 for auto), Req2.2 (probe_3 offset_==percentile of public score_samples at 100*contamination), Req3.2 (probe_4 public score_samples STILL warns on unnamed array), Req3.3 (probe_5 decision_function==score_samples-offset_ and predict sign semantics), Req3.4 (probe_6 NotFittedError before fit), Req4.1 (probe_7 CSR accepted in fit-auto and public scoring), Req4.4 (probe_8 no-variance data). ALL 8 HOLD on patched tree. Positive control discriminates (fails at base).

Candidate 'drop_public_validation' (the lazy fix that removes the warning by deleting _validate_data from public score_samples) is REJECTED by probes 3,4,5,7 (breaks dtype conversion / drops the mandated public validation of Req3.2) — suite discriminates wrong implementations. NOTE: the previously-recorded G-EQ/G-PANEL-1 fail used a probe (probe_sparse.py) testing CSR-sparse fit with NUMERIC contamination, but Req4.1 EXPLICITLY disclaims that combination as NOT part of the guaranteed behavior (the validation-free internal path skips the sparse csc conversion). That was an out-of-scope probe, not a genuine spec violation; the requirements are faithful and discriminating.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** The gold patch routes end-of-fit re-scoring through a new validation-free _score_samples helper while public score_samples keeps _validate_data. Requirements model the observable behavior (warning gone only inside fit; public scoring still validates; offset/score/predict unchanged) at the correct boundary — not a narrow helper/branch. The private method name _score_samples is not leaked; Req1.2 describes it behaviorally. The meta.json G-EQ/G-PANEL-1 fail concerns spec-too-WEAK (an attacker probe mandating CSR+numeric fit succeed), which is a coverage question, NOT faithfulness — and the requirements explicitly and correctly carve that path out in Req4.1, matching the patched code's actual ValueError. No requirement mandates absent behavior, forbids present behavior, mispins the boundary, or invents behavior. FAITHFUL.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The document localizes the change to sklearn/ensemble/_iforest.py fit and score_samples (legitimate) and translates the public problem_statement (DataFrame + non-default contamination -> spurious 'X does not have valid feature names' warning) into behavioral requirements. No hidden-test content is transmitted: the FAIL_TO_PASS test name/path (test_iforest_preserve_feature_names), its fixture code (columns=['a'], rng.randn(4), contamination=0.05, warnings.simplefilter('error', UserWarning)) are not quoted or near-quoted. The gold's fix-invented private identifier `_score_samples` is NOT named; requirements refer only to an 'internal/validation-free path' (behavioral). Details such as accept_sparse='csr', dtype=np.float32, reset=False, and offset_=-0.5 describe pre-existing public source preserved by the fix, not the new gold edit or the tests. There is a single F2P test, so no case enumeration mirrors a parametrization. Req 4.1's CSR+numeric-contamination caveat is behavioral reasoning about the fix's consequence, not a leaked test case.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
