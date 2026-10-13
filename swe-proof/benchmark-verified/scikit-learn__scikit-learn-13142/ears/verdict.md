# P2 adversarial audit — scikit-learn__scikit-learn-13142

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
"""
Positive control / Req 1.1: with n_init > 1, fit_predict(X) labels must equal
predict(X) labels on the same fitted estimator, for the same X.
Holds on patched tree; must FAIL at base (bug uses last-trial responsibilities).
"""
import numpy as np
from sklearn.mixture import GaussianMixture

rng = np.random.RandomState(0)
# Well-separated-ish clusters so labels are meaningful.
X = rng.randn(200, 3)
X[:100] += 6.0

all_equal = True
for rs in range(10):
    gm = GaussianMixture(n_components=4, n_init=5, random_state=rs)
    fp = gm.fit_predict(X)
    pr = gm.predict(X)
    eq = np.array_equal(fp, pr)
    n_diff = int(np.sum(fp != pr))
    print("rs=%d n_init=5 equal=%s n_diff=%d" % (rs, eq, n_diff))
    if not eq:
        all_equal = False

if all_equal:
    print("PASS: fit_predict == predict for all random_states with n_init=5")
    raise SystemExit(0)
else:
    print("FAIL: fit_predict disagrees with predict for some random_state")
    raise SystemExit(1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""
Req 1.2: with n_init == 1, fit_predict(X) labels must equal predict(X).
This equivalence already held; SHALL be preserved. Holds on base AND patched.
"""
import numpy as np
from sklearn.mixture import GaussianMixture, BayesianGaussianMixture

rng = np.random.RandomState(1)
X = rng.randn(150, 2)
X[:75] += 5.0

ok = True
for Est in (GaussianMixture, BayesianGaussianMixture):
    for rs in range(6):
        est = Est(n_components=3, n_init=1, random_state=rs)
        fp = est.fit_predict(X)
        pr = est.predict(X)
        eq = np.array_equal(fp, pr)
        print("%s rs=%d n_init=1 equal=%s" % (Est.__name__, rs, eq))
        if not eq:
            ok = False

if ok:
    print("PASS: n_init=1 equivalence preserved")
    raise SystemExit(0)
print("FAIL")
raise SystemExit(1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""
Req 1.4 / 1.3: equivalence holds for any max_iter, tol, random_state,
INCLUDING non-converging cases (max_iter=1). And labels derive from the
retained fitted parameters. Test BayesianGaussianMixture too.
"""
import warnings
import numpy as np
from sklearn.mixture import GaussianMixture, BayesianGaussianMixture

rng = np.random.RandomState(7)
X = rng.randn(180, 4)
X[:60] += 4.0
X[60:120] -= 4.0

ok = True
configs = [
    dict(max_iter=1, tol=1e-3),
    dict(max_iter=2, tol=1e-1),
    dict(max_iter=100, tol=1e-9),
]
for Est in (GaussianMixture, BayesianGaussianMixture):
    for cfg in configs:
        for rs in range(4):
            est = Est(n_components=5, n_init=4, random_state=rs, **cfg)
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                fp = est.fit_predict(X)
                pr = est.predict(X)
            eq = np.array_equal(fp, pr)
            if not eq:
                print("FAIL %s cfg=%s rs=%d n_diff=%d" % (
                    Est.__name__, cfg, rs, int(np.sum(fp != pr))))
                ok = False

if ok:
    print("PASS: equivalence across max_iter/tol/random_state incl non-convergence")
    raise SystemExit(0)
raise SystemExit(1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""
Req 2.1/2.3: after fit_predict with n_init>1, the estimator SHALL retain the
best-scoring trial's parameters, and the stored attributes (lower_bound_,
n_iter_, component params) SHALL match those obtained by fit() -- which is
known to correctly select the best trial. Also lower_bound_ SHALL be the max
over trials (>= any single-init trial's bound... practically: fit and
fit_predict must store identical selected parameters).
Model selection must NOT be disturbed by the label-consistency fix.
"""
import numpy as np
from sklearn.mixture import GaussianMixture

rng = np.random.RandomState(3)
X = rng.randn(220, 3)
X[:110] += 5.0

ok = True
for rs in range(8):
    a = GaussianMixture(n_components=4, n_init=5, random_state=rs)
    a.fit_predict(X)
    b = GaussianMixture(n_components=4, n_init=5, random_state=rs)
    b.fit(X)
    # fit() picks the best trial; fit_predict must store the SAME selected params.
    same_lb = np.isclose(a.lower_bound_, b.lower_bound_)
    same_ni = (a.n_iter_ == b.n_iter_)
    same_means = np.allclose(a.means_, b.means_)
    same_w = np.allclose(a.weights_, b.weights_)
    print("rs=%d lb=%s n_iter=%s means=%s weights=%s (fp_lb=%.6f fit_lb=%.6f)" % (
        rs, same_lb, same_ni, same_means, same_w, a.lower_bound_, b.lower_bound_))
    if not (same_lb and same_ni and same_means and same_w):
        ok = False

if ok:
    print("PASS: fit_predict retains the same best-trial params as fit")
    raise SystemExit(0)
raise SystemExit(1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""
Req 3.1: if no initialization converges within max_iter, a ConvergenceWarning
SHALL still be raised (unchanged). Use max_iter=1 so no trial converges.
"""
import warnings
import numpy as np
from sklearn.exceptions import ConvergenceWarning
from sklearn.mixture import GaussianMixture

rng = np.random.RandomState(11)
X = rng.randn(120, 3)

with warnings.catch_warnings(record=True) as w:
    warnings.simplefilter("always")
    gm = GaussianMixture(n_components=6, n_init=3, max_iter=1, random_state=0)
    gm.fit_predict(X)
    conv = [x for x in w if issubclass(x.category, ConvergenceWarning)]
    print("n_convergence_warnings=%d converged_=%s" % (len(conv), gm.converged_))

if len(conv) >= 1 and not gm.converged_:
    print("PASS: ConvergenceWarning raised when no init converges")
    raise SystemExit(0)
print("FAIL: expected a ConvergenceWarning")
raise SystemExit(1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
"""
Req 3.3/3.4: fit_predict returns one integer label per sample, in input order,
values in valid component index range; predict/predict_proba unchanged and
consistent with the labels (argmax of predict_proba == labels).
"""
import numpy as np
from sklearn.mixture import GaussianMixture

rng = np.random.RandomState(5)
X = rng.randn(160, 3)
X[:80] += 5.0

gm = GaussianMixture(n_components=4, n_init=5, random_state=2)
labels = gm.fit_predict(X)

ok = True
if labels.shape != (X.shape[0],):
    print("FAIL shape", labels.shape); ok = False
if not np.issubdtype(labels.dtype, np.integer):
    print("FAIL dtype", labels.dtype); ok = False
if labels.min() < 0 or labels.max() >= 4:
    print("FAIL range", labels.min(), labels.max()); ok = False

# predict_proba argmax must equal predict (predict semantics unchanged)
proba = gm.predict_proba(X)
if not np.array_equal(proba.argmax(axis=1), gm.predict(X)):
    print("FAIL predict_proba argmax != predict"); ok = False

print("shape=%s dtype=%s min=%d max=%d proba_ok=%s" % (
    labels.shape, labels.dtype, labels.min(), labels.max(),
    np.array_equal(proba.argmax(axis=1), gm.predict(X))))

if ok:
    print("PASS: output shape/label semantics valid and predict_proba consistent")
    raise SystemExit(0)
raise SystemExit(1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""
Positive control / Req 1.1: with n_init > 1, fit_predict(X) labels must equal
predict(X) labels on the same fitted estimator, for the same X.
Holds on patched tree; must FAIL at base (bug uses last-trial responsibilities).
"""
import numpy as np
from sklearn.mixture import GaussianMixture

rng = np.random.RandomState(0)
# Well-separated-ish clusters so labels are meaningful.
X = rng.randn(200, 3)
X[:100] += 6.0

all_equal = True
for rs in range(10):
    gm = GaussianMixture(n_components=4, n_init=5, random_state=rs)
    fp = gm.fit_predict(X)
    pr = gm.predict(X)
    eq = np.array_equal(fp, pr)
    n_diff = int(np.sum(fp != pr))
    print("rs=%d n_init=5 equal=%s n_diff=%d" % (rs, eq, n_diff))
    if not eq:
        all_equal = False

if all_equal:
    print("PASS: fit_predict == predict for all random_states with n_init=5")
    raise SystemExit(0)
else:
    print("FAIL: fit_predict disagrees with predict for some random_state")
    raise SystemExit(1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance scikit-learn-13142: gold fix moves the final e-step in BaseMixture.fit_predict to AFTER _set_parameters(best_params), so labels are computed from the selected best-scoring trial (agreeing with predict) rather than the last trial.

Probes (all HOLD on gold-patched tree):
- probe_1 (POSITIVE CONTROL, Req 1.1/1.3): n_init=5, fit_predict(X)==predict(X) elementwise across 10 random_states. PATCHED: HOLDS (n_diff=0 all). BASE: FAILS (n_diff up to 200, 8/10 seeds disagree). Discriminates.
- probe_2 (Req 1.2): n_init=1 equivalence preserved for GaussianMixture & BayesianGaussianMixture. HOLDS patched AND base (regression criterion).
- probe_3 (Req 1.4/1.3): equivalence across max_iter in {1,2,100}, tol, random_state incl. non-convergence (max_iter=1), both estimators. HOLDS patched.
- probe_4 (Req 2.1/2.3): fit_predict stores same selected params (lower_bound_, n_iter_, means_, weights_) as fit(). HOLDS patched AND base (model selection unchanged).
- probe_5 (Req 3.1): ConvergenceWarning still raised when no init converges (max_iter=1). HOLDS patched.
- probe_6 (Req 3.3/3.4): one integer label/sample in valid index range, predict_proba argmax==predict. HOLDS patched.

Wrong-fix candidate weak.diff (partial fix: stores best_params but derives returned labels from the LAST trial's e-step, i.e. leaves the label bug): REJECTED by probe_1 (VIOLATED, same n_diff pattern as base) while probes 2/4/5 still HOLD. Demonstrates the suite discriminates a requirements-plausible wrong implementation. No probe-conforming alternative patch found that fails hidden tests; positive control discriminates base vs patched. Verdict SOUND.

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
"""
Positive control / Req 1.1: with n_init > 1, fit_predict(X) labels must equal
predict(X) labels on the same fitted estimator, for the same X.
Holds on patched tree; must FAIL at base (bug uses last-trial responsibilities).
"""
import numpy as np
from sklearn.mixture import GaussianMixture

rng = np.random.RandomState(0)
# Well-separated-ish clusters so labels are meaningful.
X = rng.randn(200, 3)
X[:100] += 6.0

all_equal = True
for rs in range(10):
    gm = GaussianMixture(n_components=4, n_init=5, random_state=rs)
    fp = gm.fit_predict(X)
    pr = gm.predict(X)
    eq = np.array_equal(fp, pr)
    n_diff = int(np.sum(fp != pr))
    print("rs=%d n_init=5 equal=%s n_diff=%d" % (rs, eq, n_diff))
    if not eq:
        all_equal = False

if all_equal:
    print("PASS: fit_predict == predict for all random_states with n_init=5")
    raise SystemExit(0)
else:
    print("FAIL: fit_predict disagrees with predict for some random_state")
    raise SystemExit(1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance scikit-learn-13142: gold fix moves the final e-step in BaseMixture.fit_predict to AFTER _set_parameters(best_params), so labels are computed from the selected best-scoring trial (agreeing with predict) rather than the last trial.

Probes (all HOLD on gold-patched tree):
- probe_1 (POSITIVE CONTROL, Req 1.1/1.3): n_init=5, fit_predict(X)==predict(X) elementwise across 10 random_states. PATCHED: HOLDS (n_diff=0 all). BASE: FAILS (n_diff up to 200, 8/10 seeds disagree). Discriminates.
- probe_2 (Req 1.2): n_init=1 equivalence preserved for GaussianMixture & BayesianGaussianMixture. HOLDS patched AND base (regression criterion).
- probe_3 (Req 1.4/1.3): equivalence across max_iter in {1,2,100}, tol, random_state incl. non-convergence (max_iter=1), both estimators. HOLDS patched.
- probe_4 (Req 2.1/2.3): fit_predict stores same selected params (lower_bound_, n_iter_, means_, weights_) as fit(). HOLDS patched AND base (model selection unchanged).
- probe_5 (Req 3.1): ConvergenceWarning still raised when no init converges (max_iter=1). HOLDS patched.
- probe_6 (Req 3.3/3.4): one integer label/sample in valid index range, predict_proba argmax==predict. HOLDS patched.

Wrong-fix candidate weak.diff (partial fix: stores best_params but derives returned labels from the LAST trial's e-step, i.e. leaves the label bug): REJECTED by probe_1 (VIOLATED, same n_diff pattern as base) while probes 2/4/5 still HOLD. Demonstrates the suite discriminates a requirements-plausible wrong implementation. No probe-conforming alternative patch found that fails hidden tests; positive control discriminates base vs patched. Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** The gold patch only relocates the final `_, log_resp = self._e_step(X)` from before the best-param bookkeeping to after `_set_parameters(best_params); self.n_iter_ = best_n_iter; self.lower_bound_ = max_lower_bound`, so labels are computed from the selected best-scoring trial's stored parameters. R1 (fit_predict==predict for all n_init incl. n_init==1 preserved, and under non-convergence) verified by probe. R2 (best-trial selection loop + tie=earliest via strict `>` comparison + stored attributes) is untouched by the diff — preserved. R3 (convergence warning still emitted before storing params; predict/predict_proba/score paths untouched; correct label shape/range) holds. The modeling boundary — the observable fit_predict/predict equivalence — is the changed behavior itself, not a narrow branch/helper slice. FAITHFUL.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The document describes the fix behaviorally without transmitting hidden-test/gold content. Localization to BaseMixture.fit_predict / sklearn/mixture/base.py and naming GaussianMixture and BayesianGaussianMixture is legitimate: the gold fix lives on the shared base class both classes inherit, so naming both consumers is proper localization, not leakage. BayesianGaussianMixture is exercised only by the hidden test (not the problem_statement), but its inclusion follows necessarily from the change site, not from reading the test. The 'move the final e-step to after storing selected parameters' mechanism (Req 2.4, 3.2) is a behavioral translation of the gold edit, which is the intended purpose. Req 1.4's 'any combination of max_iter, tol, random_state' echoes standard estimator params / the gold code comment as generality, not fix-invented identifiers. No test function names (test_*_fit_predict_n_init), file paths, parametrization ids (e.g. [0-2-1e-07]), specific n_init/n_components test values, or quoted test/gold code appear. No case enumeration mirroring the test parametrization. This reconstructs behavior, not the tests.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
