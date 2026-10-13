# P2 adversarial audit — scikit-learn__scikit-learn-10297

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
import sys
# Req 1.1 / positive control: constructing RidgeClassifierCV with the
# store_cv_values flag (True or False) SHALL succeed, no TypeError.
from sklearn.linear_model import RidgeClassifierCV

try:
    c1 = RidgeClassifierCV(alphas=(0.1, 1.0, 10.0), store_cv_values=True)
    c2 = RidgeClassifierCV(alphas=(0.1, 1.0, 10.0), store_cv_values=False)
except TypeError as e:
    print("FAIL: constructor raised TypeError:", e)
    sys.exit(1)
print("OK: constructed with store_cv_values=True and False without TypeError")
sys.exit(0)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
import sys
# Req 1.2 & 1.3: default is False; the exact given value is recorded as attribute.
from sklearn.linear_model import RidgeClassifierCV

ok = True
c_default = RidgeClassifierCV()
if getattr(c_default, "store_cv_values", "MISSING") is not False:
    print("FAIL: default store_cv_values not False:", getattr(c_default, "store_cv_values", "MISSING"))
    ok = False
else:
    print("OK: default store_cv_values is False")

c_true = RidgeClassifierCV(store_cv_values=True)
if c_true.store_cv_values is not True:
    print("FAIL: store_cv_values=True not recorded:", c_true.store_cv_values)
    ok = False
else:
    print("OK: store_cv_values=True recorded exactly")

c_false = RidgeClassifierCV(store_cv_values=False)
if c_false.store_cv_values is not False:
    print("FAIL: store_cv_values=False not recorded:", c_false.store_cv_values)
    ok = False
else:
    print("OK: store_cv_values=False recorded exactly")

sys.exit(0 if ok else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
import sys
# Req 1.4: preserve other constructor options recorded as supplied.
from sklearn.linear_model import RidgeClassifierCV

c = RidgeClassifierCV(alphas=(0.01, 0.5, 5.0, 50.0), fit_intercept=False,
                      normalize=True, scoring="accuracy", cv=None,
                      class_weight="balanced", store_cv_values=True)
ok = True
checks = {
    "alphas": (c.alphas, (0.01, 0.5, 5.0, 50.0)),
    "fit_intercept": (c.fit_intercept, False),
    "normalize": (c.normalize, True),
    "scoring": (c.scoring, "accuracy"),
    "cv": (c.cv, None),
    "class_weight": (c.class_weight, "balanced"),
    "store_cv_values": (c.store_cv_values, True),
}
for name, (got, exp) in checks.items():
    if got != exp:
        print("FAIL: %s got %r expected %r" % (name, got, exp))
        ok = False
    else:
        print("OK: %s == %r" % (name, got))
sys.exit(0 if ok else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
import sys
# Req 2.1 & 2.2 & 2.4: after fitting with 1-D labels (binary), cv=None, store
# enabled, cv_values_ exists with shape (n_samples, 1, n_alphas); last dim ==
# len(alphas). Binary classification -> LabelBinarizer yields a single column.
import numpy as np
from sklearn.linear_model import RidgeClassifierCV

rng = np.random.RandomState(0)
n_samples, n_features = 40, 5
X = rng.randn(n_samples, n_features)
y = rng.randint(0, 2, size=n_samples)  # binary -> single response column
alphas = (0.1, 1.0, 10.0, 100.0)
n_alphas = len(alphas)

clf = RidgeClassifierCV(alphas=alphas, store_cv_values=True)
clf.fit(X, y)

if not hasattr(clf, "cv_values_"):
    print("FAIL: no cv_values_ attribute after fit")
    sys.exit(1)
shape = clf.cv_values_.shape
print("observed cv_values_ shape:", shape, "n_samples=", n_samples, "n_alphas=", n_alphas)
if shape != (n_samples, 1, n_alphas):
    print("FAIL: expected", (n_samples, 1, n_alphas), "got", shape)
    sys.exit(1)
print("OK: cv_values_ shape is (n_samples, 1, n_alphas) and last dim == len(alphas)")
sys.exit(0)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
import sys
# Req 3.1: store_cv_values=True with explicit cv (cv != None) -> ValueError at fit.
# Req 3.2: store_cv_values disabled -> no cv_values_ attribute after fit.
import numpy as np
from sklearn.linear_model import RidgeClassifierCV

rng = np.random.RandomState(1)
X = rng.randn(30, 4)
y = rng.randint(0, 2, size=30)

ok = True

# 3.1
clf = RidgeClassifierCV(alphas=(0.1, 1.0, 10.0), store_cv_values=True, cv=3)
try:
    clf.fit(X, y)
    print("FAIL: expected ValueError with store_cv_values=True and cv=3, none raised")
    ok = False
except ValueError as e:
    print("OK: ValueError raised for store_cv_values=True with cv=3:", str(e)[:80])

# 3.2
clf2 = RidgeClassifierCV(alphas=(0.1, 1.0, 10.0), store_cv_values=False)
clf2.fit(X, y)
if hasattr(clf2, "cv_values_"):
    print("FAIL: cv_values_ present though store_cv_values=False")
    ok = False
else:
    print("OK: no cv_values_ attribute when store disabled")

sys.exit(0 if ok else 1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
import sys
# Req 4.1 & 4.2: preserve RidgeCV behavior. 1-D target -> (n_samples, n_alphas);
# 2-D target -> (n_samples, n_targets, n_alphas).
import numpy as np
from sklearn.linear_model import RidgeCV

rng = np.random.RandomState(2)
n_samples, n_features = 50, 6
X = rng.randn(n_samples, n_features)
alphas = (0.1, 1.0, 10.0)
n_alphas = len(alphas)

ok = True
# 1-D
y1 = rng.randn(n_samples)
r1 = RidgeCV(alphas=alphas, store_cv_values=True)
r1.fit(X, y1)
s1 = r1.cv_values_.shape
print("1-D cv_values_ shape:", s1)
if s1 != (n_samples, n_alphas):
    print("FAIL: expected", (n_samples, n_alphas), "got", s1)
    ok = False
else:
    print("OK: 1-D RidgeCV cv_values_ (n_samples, n_alphas)")

# 2-D
n_targets = 3
y2 = rng.randn(n_samples, n_targets)
r2 = RidgeCV(alphas=alphas, store_cv_values=True)
r2.fit(X, y2)
s2 = r2.cv_values_.shape
print("2-D cv_values_ shape:", s2)
if s2 != (n_samples, n_targets, n_alphas):
    print("FAIL: expected", (n_samples, n_targets, n_alphas), "got", s2)
    ok = False
else:
    print("OK: 2-D RidgeCV cv_values_ (n_samples, n_targets, n_alphas)")

sys.exit(0 if ok else 1)
```

Attack 7 — `probe_7.py` → holds on the patched tree (good)

```python
import sys
# Req 5.1: enabling store_cv_values must NOT change alpha_, coef_, intercept_.
import numpy as np
from sklearn.linear_model import RidgeClassifierCV

rng = np.random.RandomState(3)
X = rng.randn(60, 5)
y = rng.randint(0, 3, size=60)
alphas = (0.1, 1.0, 10.0, 100.0)

a = RidgeClassifierCV(alphas=alphas, store_cv_values=False)
a.fit(X, y)
b = RidgeClassifierCV(alphas=alphas, store_cv_values=True)
b.fit(X, y)

ok = True
if not np.allclose(a.alpha_, b.alpha_):
    print("FAIL: alpha_ differs:", a.alpha_, b.alpha_); ok = False
else:
    print("OK: alpha_ unchanged:", a.alpha_)
if not np.allclose(a.coef_, b.coef_):
    print("FAIL: coef_ differs"); ok = False
else:
    print("OK: coef_ unchanged")
if not np.allclose(a.intercept_, b.intercept_):
    print("FAIL: intercept_ differs"); ok = False
else:
    print("OK: intercept_ unchanged")
sys.exit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
import sys
# Req 1.1 / positive control: constructing RidgeClassifierCV with the
# store_cv_values flag (True or False) SHALL succeed, no TypeError.
from sklearn.linear_model import RidgeClassifierCV

try:
    c1 = RidgeClassifierCV(alphas=(0.1, 1.0, 10.0), store_cv_values=True)
    c2 = RidgeClassifierCV(alphas=(0.1, 1.0, 10.0), store_cv_values=False)
except TypeError as e:
    print("FAIL: constructor raised TypeError:", e)
    sys.exit(1)
print("OK: constructed with store_cv_values=True and False without TypeError")
sys.exit(0)
```

Prepatch bug re-encoded as an attack: `True`.

7 probes, all HOLD on gold-patched tree; all discriminate at base (probe_1 positive control: TypeError at base, OK patched; probe_4 also TypeErrors at base). Coverage: probe_1=Req1.1 (construct with flag True/False, no TypeError); probe_2=Req1.2/1.3 (default False, exact value recorded); probe_3=Req1.4 (other ctor options preserved) + Req1.3; probe_4=Req2.1/2.2/2.4 (1-D binary label -> cv_values_ shape (n_samples,1,n_alphas), last dim==len(alphas)); probe_5=Req3.1 & Req3.2 (no cv_values_ when disabled); probe_6=Req4.1/4.2 (RidgeCV regression 1-D (n_samples,n_alphas) and 2-D (n_samples,n_targets,n_alphas) unchanged); probe_7=Req5.1 (alpha_/coef_/intercept_ unchanged by flag).

CANDIDATE PATCH weak.diff = the lazy fix: adds store_cv_values kwarg to RidgeClassifierCV.__init__ (kills the TypeError, so probe_1 passes) but does NOT forward it to super().__init__ nor set self.store_cv_values. This requirements-conforming-only-on-Req1.1 fix is REJECTED by probes 2,3 (flag not recorded), 4 (no cv_values_ stored), and 5 (no ValueError raised, since base sees store_cv_values=False). Suite thus discriminates wrong implementations. No too-weak finding: every plausible partial fix that would fail the hidden tests is caught by at least one probe.

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
import sys
# Req 1.1 / positive control: constructing RidgeClassifierCV with the
# store_cv_values flag (True or False) SHALL succeed, no TypeError.
from sklearn.linear_model import RidgeClassifierCV

try:
    c1 = RidgeClassifierCV(alphas=(0.1, 1.0, 10.0), store_cv_values=True)
    c2 = RidgeClassifierCV(alphas=(0.1, 1.0, 10.0), store_cv_values=False)
except TypeError as e:
    print("FAIL: constructor raised TypeError:", e)
    sys.exit(1)
print("OK: constructed with store_cv_values=True and False without TypeError")
sys.exit(0)
```

Prepatch bug re-encoded as an attack: `True`.

7 probes, all HOLD on gold-patched tree; all discriminate at base (probe_1 positive control: TypeError at base, OK patched; probe_4 also TypeErrors at base). Coverage: probe_1=Req1.1 (construct with flag True/False, no TypeError); probe_2=Req1.2/1.3 (default False, exact value recorded); probe_3=Req1.4 (other ctor options preserved) + Req1.3; probe_4=Req2.1/2.2/2.4 (1-D binary label -> cv_values_ shape (n_samples,1,n_alphas), last dim==len(alphas)); probe_5=Req3.1 & Req3.2 (no cv_values_ when disabled); probe_6=Req4.1/4.2 (RidgeCV regression 1-D (n_samples,n_alphas) and 2-D (n_samples,n_targets,n_alphas) unchanged); probe_7=Req5.1 (alpha_/coef_/intercept_ unchanged by flag).

CANDIDATE PATCH weak.diff = the lazy fix: adds store_cv_values kwarg to RidgeClassifierCV.__init__ (kills the TypeError, so probe_1 passes) but does NOT forward it to super().__init__ nor set self.store_cv_values. This requirements-conforming-only-on-Req1.1 fix is REJECTED by probes 2,3 (flag not recorded), 4 (no cv_values_ stored), and 5 (no ValueError raised, since base sees store_cv_values=False). Suite thus discriminates wrong implementations. No too-weak finding: every plausible partial fix that would fail the hidden tests is caught by at least one probe.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** The gold patch adds store_cv_values to RidgeClassifierCV.__init__ and forwards it to _BaseRidgeCV. The requirements correctly capture the changed observable behavior at the right boundary: the classifier's constructor acceptance/recording (R1), the classifier's cv_values_ shape with its always-3D (n_samples, n_targets, n_alphas) convention where 1D y gives n_targets=1 (R2 — matches the FAIL_TO_PASS test and probe output (5,1,3)), the GCV-only restriction (R3), and the unchanged RidgeCV regressor behavior with its distinct 2D (n_samples, n_alphas) convention for 1D y (R4 — correctly distinguishes classifier's (5,1,3) from regressor's (8,3)). R5's invariance of alpha_/coef_/intercept_ under the flag holds since store_cv_values only adds an attribute. No modeling-boundary error: R2.2's (n_samples,1,n_alphas) is the actual patched classifier shape, not a narrow/wrong slice. Probe ran clean, exit 0.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** requirements.md describes the store_cv_values / cv_values_ feature entirely in terms of public information (problem_statement) and legitimate localization of the change (naming RidgeClassifierCV, RidgeCV, _BaseRidgeCV, _RidgeGCV — the modules that must be touched). All identifiers (store_cv_values, cv_values_, alphas, fit_intercept, normalize, scoring, cv, class_weight, alpha_, coef_, intercept_) are public sklearn API, not fix-invented. No test file path, no test function name (test_ridge_classifier_cv_store_cv_values), no parametrization ids, no quoted test/gold code, no concrete test arrays (x=[[-1,-1],...], y=[1,1,1,-1,-1], alphas=[1e-1,1e0,1e1]) appear in the document. The one non-public-doc detail — Req 2.2 stating the classifier's 1D-target cv_values_ has shape (n_samples, 1, n_alphas) whereas the public docstring shows [n_samples, n_alphas] — is a genuine BEHAVIORAL fact (LinearClassifierMixin binarizes labels, yielding an explicit target axis) and is exactly the kind of test-behavior→requirement translation that is the document's purpose; it does not transmit the test itself. The 1D/2D case split mirrors the two documented shape regimes, not test parametrization. Requirement 3 and Req 4 (RidgeCV 1D shape (n_samples, n_alphas)) are documented/public behavior. No semantic leakage.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
