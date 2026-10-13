# P2 adversarial audit — scikit-learn__scikit-learn-26194

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
"""Req1.1 (positive control): thresholds[0] == np.inf.

Holds on patched tree; must FAIL at base (base sets it to max(y_score)+1).
"""
import numpy as np
from sklearn.metrics import roc_curve

y_true = np.array([0, 0, 1, 1])
y_score = np.array([0.1, 0.4, 0.35, 0.8])
fpr, tpr, thr = roc_curve(y_true, y_score)
print("thresholds =", thr)
print("thresholds[0] =", thr[0])
ok = np.isinf(thr[0]) and thr[0] > 0
print("thresholds[0] is +inf:", ok)
raise SystemExit(0 if ok else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""Req1.2 & 1.4: with probability scores in [0,1], thresholds[0] is infinite
(not a finite value >1), AND remains strictly greater than every other
(finite) threshold, so thresholds stays strictly decreasing.
"""
import numpy as np
from sklearn.metrics import roc_curve

rng = np.random.RandomState(0)
for trial in range(20):
    n = rng.randint(6, 40)
    y_true = rng.randint(0, 2, size=n)
    if y_true.sum() == 0 or y_true.sum() == n:
        continue
    y_score = rng.rand(n)  # in [0,1]
    fpr, tpr, thr = roc_curve(y_true, y_score)
    assert np.isinf(thr[0]) and thr[0] > 0, ("not inf", thr[0])
    # strictly decreasing overall
    assert np.all(np.diff(thr) < 0), ("not strictly decreasing", thr)
    # rest are finite
    assert np.all(np.isfinite(thr[1:])), ("finite rest", thr)
print("all trials: thresholds[0]=+inf, strictly decreasing, rest finite")
raise SystemExit(0)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""Req2.1 & 2.4: with drop_intermediate=False, thresholds[1:] equal exactly the
finite score thresholds from _binary_clf_curve (same order/values as the raw
decreasing score thresholds); leading value is the only prepended one.
"""
import numpy as np
from sklearn.metrics import roc_curve
from sklearn.metrics._ranking import _binary_clf_curve

rng = np.random.RandomState(1)
for trial in range(15):
    n = rng.randint(6, 30)
    y_true = rng.randint(0, 2, size=n)
    if y_true.sum() == 0 or y_true.sum() == n:
        continue
    y_score = rng.rand(n)
    fps, tps, raw_thr = _binary_clf_curve(y_true, y_score, pos_label=1)
    fpr, tpr, thr = roc_curve(y_true, y_score, drop_intermediate=False)
    assert thr.shape[0] == raw_thr.shape[0] + 1, (thr.shape, raw_thr.shape)
    assert np.allclose(thr[1:], raw_thr), (thr[1:], raw_thr)
print("drop_intermediate=False: thresholds[1:] == raw score thresholds; +1 leading position")
raise SystemExit(0)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""Req2.2 & 2.5: fpr and tpr are unchanged - lead with (0,0), same lengths as
thresholds, and match the expected values from the documented example.
Also Req2.3: drop_intermediate=True still thins, giving fewer points than False.
"""
import numpy as np
from sklearn.metrics import roc_curve

# documented worked example
y_true = np.array([1, 1, 2, 2])
y_score = np.array([0.1, 0.4, 0.35, 0.8])
fpr, tpr, thr = roc_curve(y_true, y_score, pos_label=2)
print("fpr =", fpr, "tpr =", tpr, "thr =", thr)
assert np.allclose(fpr, [0., 0., 0.5, 0.5, 1.]), fpr
assert np.allclose(tpr, [0., 0.5, 0.5, 1., 1.]), tpr
assert fpr[0] == 0.0 and tpr[0] == 0.0, "curve must start at (0,0)"
assert len(fpr) == len(tpr) == len(thr), "equal lengths"
assert np.isinf(thr[0]), thr
assert np.allclose(thr[1:], [0.8, 0.4, 0.35, 0.1]), thr

# drop_intermediate thinning still active
rng = np.random.RandomState(3)
yt = rng.randint(0, 2, size=200)
ys = rng.rand(200)
_, _, thr_drop = roc_curve(yt, ys, drop_intermediate=True)
_, _, thr_full = roc_curve(yt, ys, drop_intermediate=False)
print("len drop=%d len full=%d" % (len(thr_drop), len(thr_full)))
assert len(thr_drop) < len(thr_full), "drop_intermediate should thin points"
print("fpr/tpr unchanged, lengths equal, drop_intermediate thins")
raise SystemExit(0)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""Req3.1 & 3.2: degenerate-input warnings + NaN handling preserved.
No negative samples -> "No negative samples" UndefinedMetricWarning + fpr all NaN.
No positive samples -> "No positive samples" warning + tpr all NaN.
"""
import warnings
import numpy as np
from sklearn.metrics import roc_curve
from sklearn.exceptions import UndefinedMetricWarning

# no negative samples
with warnings.catch_warnings(record=True) as w:
    warnings.simplefilter("always")
    fpr, tpr, thr = roc_curve(np.array([1, 1, 1, 1]), np.array([0.1, 0.4, 0.35, 0.8]))
    msgs = " ".join(str(x.message) for x in w)
print("no-neg warnings:", msgs)
assert "No negative samples" in msgs, msgs
assert np.all(np.isnan(fpr)), ("fpr not all nan", fpr)

# no positive samples
with warnings.catch_warnings(record=True) as w:
    warnings.simplefilter("always")
    fpr, tpr, thr = roc_curve(np.array([0, 0, 0, 0]), np.array([0.1, 0.4, 0.35, 0.8]))
    msgs = " ".join(str(x.message) for x in w)
print("no-pos warnings:", msgs)
assert "No positive samples" in msgs, msgs
assert np.all(np.isnan(tpr)), ("tpr not all nan", tpr)

# multiclass still raises
try:
    roc_curve(np.array([0, 1, 2, 1]), np.array([0.1, 0.4, 0.35, 0.8]))
    raise AssertionError("expected error for multiclass")
except ValueError:
    pass
print("degenerate warnings + NaN handling + multiclass error preserved")
raise SystemExit(0)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
"""Req1.3: leading threshold SHALL NOT be max(y_score)+1 nor any offset of the
largest score. Use scores whose max is well below any plausible finite sentinel
and check the leading value is NOT a finite offset of the max. On base tree
thr[0] == max+1 (finite); on patched tree it's inf.
"""
import numpy as np
from sklearn.metrics import roc_curve

y_true = np.array([0, 0, 1, 1, 0, 1])
y_score = np.array([0.10, 0.42, 0.31, 0.77, 0.05, 0.63])
fpr, tpr, thr = roc_curve(y_true, y_score)
mx = y_score.max()
print("max(y_score) =", mx, "thresholds[0] =", thr[0])
# must not be a finite offset of the max score
assert not np.isfinite(thr[0]) or not np.isclose(thr[0], mx + 1), \
    ("leading threshold is max+1 offset", thr[0])
assert np.isinf(thr[0]), ("leading not inf", thr[0])
print("leading threshold is not derived by offsetting the largest score")
raise SystemExit(0)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Req1.1 (positive control): thresholds[0] == np.inf.

Holds on patched tree; must FAIL at base (base sets it to max(y_score)+1).
"""
import numpy as np
from sklearn.metrics import roc_curve

y_true = np.array([0, 0, 1, 1])
y_score = np.array([0.1, 0.4, 0.35, 0.8])
fpr, tpr, thr = roc_curve(y_true, y_score)
print("thresholds =", thr)
print("thresholds[0] =", thr[0])
ok = np.isinf(thr[0]) and thr[0] > 0
print("thresholds[0] is +inf:", ok)
raise SystemExit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Requirements: roc_curve leading threshold changed from max(y_score)+1 to np.inf; all other outputs unchanged. Six probes cover: R1.1 thresholds[0]==+inf (probe_1, positive control), R1.2/R1.4 prob-scores -> inf & strictly decreasing (probe_2), R2.1/R2.4 drop_intermediate=False thresholds[1:]==raw score thresholds (probe_3), R2.2/R2.3/R2.5 fpr/tpr unchanged + doc example + drop_intermediate thinning + equal lengths (probe_4), R3.1/R3.2/R3.3 no-neg/no-pos warnings + NaN + multiclass error (probe_5), R1.3 not max+1 offset (probe_6). ALL 6 HOLD on gold-patched tree. Positive control probe_1 discriminates: HOLDS patched (thr[0]=inf), FAILS at base (thr[0]=1.8); probes 2 and 6 also fail at base. Candidate wrong-fix weak.diff uses a large FINITE sentinel np.finfo(dtype).max instead of np.inf (the lazy 'above every score' reading a weak spec might admit); the suite REJECTS it (probes 1,2,4,6 fail) because R1.1/R1.2 mandate strictly np.inf. This demonstrates discriminating power and shows no requirement-conforming wrong fix survives. Verdict SOUND.

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
"""Req1.1 (positive control): thresholds[0] == np.inf.

Holds on patched tree; must FAIL at base (base sets it to max(y_score)+1).
"""
import numpy as np
from sklearn.metrics import roc_curve

y_true = np.array([0, 0, 1, 1])
y_score = np.array([0.1, 0.4, 0.35, 0.8])
fpr, tpr, thr = roc_curve(y_true, y_score)
print("thresholds =", thr)
print("thresholds[0] =", thr[0])
ok = np.isinf(thr[0]) and thr[0] > 0
print("thresholds[0] is +inf:", ok)
raise SystemExit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Requirements: roc_curve leading threshold changed from max(y_score)+1 to np.inf; all other outputs unchanged. Six probes cover: R1.1 thresholds[0]==+inf (probe_1, positive control), R1.2/R1.4 prob-scores -> inf & strictly decreasing (probe_2), R2.1/R2.4 drop_intermediate=False thresholds[1:]==raw score thresholds (probe_3), R2.2/R2.3/R2.5 fpr/tpr unchanged + doc example + drop_intermediate thinning + equal lengths (probe_4), R3.1/R3.2/R3.3 no-neg/no-pos warnings + NaN + multiclass error (probe_5), R1.3 not max+1 offset (probe_6). ALL 6 HOLD on gold-patched tree. Positive control probe_1 discriminates: HOLDS patched (thr[0]=inf), FAILS at base (thr[0]=1.8); probes 2 and 6 also fail at base. Candidate wrong-fix weak.diff uses a large FINITE sentinel np.finfo(dtype).max instead of np.inf (the lazy 'above every score' reading a weak spec might admit); the suite REJECTS it (probes 1,2,4,6 fail) because R1.1/R1.2 mandate strictly np.inf. This demonstrates discriminating power and shows no requirement-conforming wrong fix survives. Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Patch changes only the prepended leading threshold from thresholds[0]+1 to np.inf, plus docstring. Probed on instance image: patched th=[inf,0.8,0.4,0.35,0.1], base th=[1.8,0.8,0.4,0.35,0.1]; fpr/tpr identical. Requirements pin the changed behavior biconditionally at the correct boundary (the observable leading-threshold value), not a narrow slice or helper. No mandated behavior absent from code, no forbidden behavior present, nothing invented.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The requirements describe the target behavior (leading threshold set to +inf / np.inf, other outputs unchanged, preserved warnings, docstring updated) as behavioral requirements. This translates what the hidden F2P test verifies (np.isinf(thresholds[0])) into prose, which is the legitimate purpose of a spec, not a transmission of the tests. No test file paths, test/function names (test_roc_curve_with_probablity_estimates is public via problem_statement anyway), parametrization ids (e.g. [42], global_random_seed), or quoted test/gold code appear. Crucially the doc does NOT reproduce the parametrized assertion vectors from test_roc_curve_drop_intermediate ([np.inf, 1.0, 0.7, 0.0] / [np.inf, 1.0, 0.9, 0.7, 0.6, 0.0]) nor the docstring example array — Req 2/4 stay at the behavioral level. The one piece beyond problem_statement is the concrete choice np.inf (the problem_statement suggested clipping to <=1), but stating the fixed behavior a spec targets, expressed as behavior rather than quoted gold code, is legitimate localization, not leakage. Module/function names (roc_curve, sklearn.metrics._ranking) are legitimate and also public.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
