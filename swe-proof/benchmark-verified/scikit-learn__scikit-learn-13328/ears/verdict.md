# P2 adversarial audit — scikit-learn__scikit-learn-13328

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
"""R1.1 + R1.2 (POSITIVE CONTROL): bool X fit completes without error and
populates fitted attributes. Must HOLD patched, FAIL at base (TypeError)."""
import sys
import numpy as np
from sklearn.datasets import make_regression
from sklearn.linear_model import HuberRegressor

X, y = make_regression(n_samples=200, n_features=2, noise=4.0, random_state=0)
X_bool = X > 0
try:
    est = HuberRegressor().fit(X_bool, y)
except Exception as e:
    print("FAIL: fit on bool X raised %r" % (e,))
    sys.exit(1)

for attr in ("coef_", "intercept_", "scale_", "n_iter_"):
    if not hasattr(est, attr):
        print("FAIL: missing fitted attribute %s" % attr)
        sys.exit(1)
print("OK: bool fit succeeded; coef_=%s intercept_=%s scale_=%s n_iter_=%s"
      % (est.coef_, est.intercept_, est.scale_, est.n_iter_))
sys.exit(0)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""R1.4: bool fit result equivalent (within tolerance) to fitting on the same
data cast to float beforehand."""
import sys
import numpy as np
from sklearn.datasets import make_regression
from sklearn.linear_model import HuberRegressor

X, y = make_regression(n_samples=200, n_features=2, noise=4.0, random_state=0)
X_bool = X > 0
X_float = np.asarray(X_bool, dtype=float)

e_bool = HuberRegressor().fit(X_bool, y)
e_float = HuberRegressor().fit(X_float, y)

ok = (np.allclose(e_bool.coef_, e_float.coef_, atol=1e-6)
      and np.allclose(e_bool.intercept_, e_float.intercept_, atol=1e-6)
      and np.allclose(e_bool.scale_, e_float.scale_, atol=1e-6))
print("bool coef=%s float coef=%s" % (e_bool.coef_, e_float.coef_))
print("bool intercept=%s float intercept=%s" % (e_bool.intercept_, e_float.intercept_))
if not ok:
    print("FAIL: bool fit differs from float-cast fit")
    sys.exit(1)
print("OK: bool fit equivalent to float-cast fit")
sys.exit(0)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""R2.2: sparse CSR input still accepted, fit completes without densifying it
away (the estimator stores/uses sparse path). Also R2.1 float dtype preserved."""
import sys
import numpy as np
from scipy import sparse
from sklearn.datasets import make_regression
from sklearn.linear_model import HuberRegressor

X, y = make_regression(n_samples=200, n_features=5, noise=4.0, random_state=0)
X_csr = sparse.csr_matrix(X)

try:
    est = HuberRegressor(fit_intercept=True, alpha=0.1, max_iter=100).fit(X_csr, y)
except Exception as e:
    print("FAIL: sparse CSR fit raised %r" % (e,))
    sys.exit(1)

# compare to dense float fit -> should match (sparse path preserved & correct)
est_dense = HuberRegressor(fit_intercept=True, alpha=0.1, max_iter=100).fit(X, y)
if not np.allclose(est.coef_, est_dense.coef_, atol=1e-4):
    print("FAIL: sparse fit coef differs from dense: %s vs %s"
          % (est.coef_, est_dense.coef_))
    sys.exit(1)
print("OK: sparse CSR fit accepted; coef=%s matches dense" % (est.coef_,))
sys.exit(0)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""R1.3: non-float integer X is converted to float and fit succeeds; result
equals fit on the float-cast data."""
import sys
import numpy as np
from sklearn.datasets import make_regression
from sklearn.linear_model import HuberRegressor

X, y = make_regression(n_samples=200, n_features=3, noise=4.0, random_state=0)
X_int = np.round(X).astype(np.int64)
X_flt = X_int.astype(float)

try:
    e_int = HuberRegressor().fit(X_int, y)
except Exception as e:
    print("FAIL: integer X fit raised %r" % (e,))
    sys.exit(1)
e_flt = HuberRegressor().fit(X_flt, y)
if not (np.allclose(e_int.coef_, e_flt.coef_, atol=1e-6)
        and np.allclose(e_int.intercept_, e_flt.intercept_, atol=1e-6)):
    print("FAIL: int fit != float-cast fit: %s vs %s"
          % (e_int.coef_, e_flt.coef_))
    sys.exit(1)
print("OK: integer X converted; coef=%s matches float-cast" % (e_int.coef_,))
sys.exit(0)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""R3.1: analytic gradient of _huber_loss_and_gradient matches finite-difference
of its loss (with sample_weight). Regression criterion."""
import sys
import numpy as np
from scipy import optimize
from sklearn.datasets import make_regression
from sklearn.linear_model.huber import _huber_loss_and_gradient

rng = np.random.RandomState(1)
X, y = make_regression(n_samples=50, n_features=3, noise=4.0, random_state=0)
sample_weight = rng.randint(1, 3, (y.shape[0]))

def loss_func(x, *args):
    return _huber_loss_and_gradient(x, *args)[0]

def grad_func(x, *args):
    return _huber_loss_and_gradient(x, *args)[1]

n_features = X.shape[1]
worst = 0.0
for _ in range(5):
    w = rng.randn(n_features + 2)
    w[-1] = np.abs(w[-1])
    err = optimize.check_grad(
        loss_func, grad_func, w, X, y, 1.35, 0.01, sample_weight)
    worst = max(worst, err)
print("max check_grad error = %g" % worst)
if worst > 1e-3:
    print("FAIL: gradient mismatch")
    sys.exit(1)
print("OK: analytic gradient matches finite differences")
sys.exit(0)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
"""R3.3 + R3.4: scaling invariance of coefficients and high-epsilon -> OLS.
Regression criteria."""
import sys
import numpy as np
from sklearn.datasets import make_regression
from sklearn.linear_model import HuberRegressor, LinearRegression

X, y = make_regression(n_samples=200, n_features=3, noise=4.0, random_state=0)

# scaling invariance
h1 = HuberRegressor(fit_intercept=True, alpha=0.0, max_iter=100).fit(X, y)
h2 = HuberRegressor(fit_intercept=True, alpha=0.0, max_iter=100).fit(2.0 * X, 2.0 * y)
if not np.allclose(h1.coef_, h2.coef_, atol=1e-3):
    print("FAIL: not scale-invariant: %s vs %s" % (h1.coef_, h2.coef_))
    sys.exit(1)

# high epsilon -> OLS
lr = LinearRegression().fit(X, y)
hb = HuberRegressor(epsilon=1 + 1e-6, alpha=0.0, max_iter=10000,
                    tol=1e-8).fit(X, y)
# not asserting equality here beyond direction; use a generous check
hb_big = HuberRegressor(epsilon=1e6, alpha=0.0, max_iter=10000, tol=1e-8).fit(X, y)
if not (np.allclose(hb_big.coef_, lr.coef_, atol=1e-2)
        and np.allclose(hb_big.intercept_, lr.intercept_, atol=1e-2)):
    print("FAIL: high-epsilon huber != OLS: %s vs %s"
          % (hb_big.coef_, lr.coef_))
    sys.exit(1)
print("OK: scale-invariant and high-epsilon approaches OLS")
sys.exit(0)
```

Attack 7 — `probe_7.py` → holds on the patched tree (good)

```python
"""R4.2: epsilon < 1.0 raises ValueError describing invalid epsilon.
Regression / error-reporting criterion (should hold at base AND patched)."""
import sys
import numpy as np
from sklearn.datasets import make_regression
from sklearn.linear_model import HuberRegressor

X, y = make_regression(n_samples=50, n_features=2, noise=4.0, random_state=0)
try:
    HuberRegressor(epsilon=0.5).fit(X, y)
except ValueError as e:
    msg = str(e).lower()
    print("raised ValueError: %s" % e)
    if "epsilon" in msg:
        print("OK: ValueError mentions epsilon")
        sys.exit(0)
    print("FAIL: ValueError does not describe epsilon")
    sys.exit(1)
except Exception as e:
    print("FAIL: wrong exception type %r" % (e,))
    sys.exit(1)
print("FAIL: no exception raised for epsilon<1")
sys.exit(1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""R1.1 + R1.2 (POSITIVE CONTROL): bool X fit completes without error and
populates fitted attributes. Must HOLD patched, FAIL at base (TypeError)."""
import sys
import numpy as np
from sklearn.datasets import make_regression
from sklearn.linear_model import HuberRegressor

X, y = make_regression(n_samples=200, n_features=2, noise=4.0, random_state=0)
X_bool = X > 0
try:
    est = HuberRegressor().fit(X_bool, y)
except Exception as e:
    print("FAIL: fit on bool X raised %r" % (e,))
    sys.exit(1)

for attr in ("coef_", "intercept_", "scale_", "n_iter_"):
    if not hasattr(est, attr):
        print("FAIL: missing fitted attribute %s" % attr)
        sys.exit(1)
print("OK: bool fit succeeded; coef_=%s intercept_=%s scale_=%s n_iter_=%s"
      % (est.coef_, est.intercept_, est.scale_, est.n_iter_))
sys.exit(0)
```

Prepatch bug re-encoded as an attack: `True`.

Requirements: HuberRegressor.fit should coerce non-float X (bool/int) to float via check_X_y dtype=[float64,float32], accepting bool X while preserving all prior behavior (sparse CSR, gradient correctness, sample-weight/scaling/high-epsilon semantics, epsilon<1 ValueError).

Probes (all HOLD on gold-patched tree):
- probe_1 (R1.1/R1.2, POSITIVE CONTROL): bool X fit completes & populates coef_/intercept_/scale_/n_iter_. HOLDS patched; FAILS at base with the exact reported TypeError ('numpy boolean negative ... not supported'). Discriminates.
- probe_2 (R1.4): bool fit == float-cast fit within tol. HOLDS patched; at base raises TypeError (the same bug), so also discriminates.
- probe_3 (R2.2/R2.1): sparse CSR still accepted & matches dense fit. HOLDS patched.
- probe_4 (R1.3): integer X coerced & matches float-cast. HOLDS patched; NOTE also holds at base (integer arrays were already accepted; only bool triggered the bug), so it is a regression-preservation probe, not a discriminator.
- probe_5 (R3.1): analytic gradient vs finite-difference w/ sample_weight (check_grad err 5.4e-4). HOLDS patched.
- probe_6 (R3.3/R3.4): scaling invariance + high-epsilon->OLS. HOLDS patched.
- probe_7 (R4.2): epsilon<1 raises ValueError mentioning epsilon. HOLDS patched (and base).

Candidate wrong-fix (REQUIRED floor): weak_nosparse.diff applies the correct dtype coercion but DROPS accept_sparse=['csr']. It fixes bool (probe_1 holds) but is REJECTED by probe_3 (sparse CSR now raises 'A sparse matrix was passed, but dense data is required'), violating R2.2. This proves the suite discriminates a plausibly-wrong partial fix.

Verdict SOUND: 7 distinct probes all hold on the patched tree, positive control (probe_1) fails at base and holds patched (prepatch reproduced), and a requirement-motivated alternative patch is rejected by the suite. No too-weak finding: every probe-conforming candidate that also keeps sparse support reduces to the gold change.

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
"""R1.1 + R1.2 (POSITIVE CONTROL): bool X fit completes without error and
populates fitted attributes. Must HOLD patched, FAIL at base (TypeError)."""
import sys
import numpy as np
from sklearn.datasets import make_regression
from sklearn.linear_model import HuberRegressor

X, y = make_regression(n_samples=200, n_features=2, noise=4.0, random_state=0)
X_bool = X > 0
try:
    est = HuberRegressor().fit(X_bool, y)
except Exception as e:
    print("FAIL: fit on bool X raised %r" % (e,))
    sys.exit(1)

for attr in ("coef_", "intercept_", "scale_", "n_iter_"):
    if not hasattr(est, attr):
        print("FAIL: missing fitted attribute %s" % attr)
        sys.exit(1)
print("OK: bool fit succeeded; coef_=%s intercept_=%s scale_=%s n_iter_=%s"
      % (est.coef_, est.intercept_, est.scale_, est.n_iter_))
sys.exit(0)
```

Prepatch bug re-encoded as an attack: `True`.

Requirements: HuberRegressor.fit should coerce non-float X (bool/int) to float via check_X_y dtype=[float64,float32], accepting bool X while preserving all prior behavior (sparse CSR, gradient correctness, sample-weight/scaling/high-epsilon semantics, epsilon<1 ValueError).

Probes (all HOLD on gold-patched tree):
- probe_1 (R1.1/R1.2, POSITIVE CONTROL): bool X fit completes & populates coef_/intercept_/scale_/n_iter_. HOLDS patched; FAILS at base with the exact reported TypeError ('numpy boolean negative ... not supported'). Discriminates.
- probe_2 (R1.4): bool fit == float-cast fit within tol. HOLDS patched; at base raises TypeError (the same bug), so also discriminates.
- probe_3 (R2.2/R2.1): sparse CSR still accepted & matches dense fit. HOLDS patched.
- probe_4 (R1.3): integer X coerced & matches float-cast. HOLDS patched; NOTE also holds at base (integer arrays were already accepted; only bool triggered the bug), so it is a regression-preservation probe, not a discriminator.
- probe_5 (R3.1): analytic gradient vs finite-difference w/ sample_weight (check_grad err 5.4e-4). HOLDS patched.
- probe_6 (R3.3/R3.4): scaling invariance + high-epsilon->OLS. HOLDS patched.
- probe_7 (R4.2): epsilon<1 raises ValueError mentioning epsilon. HOLDS patched (and base).

Candidate wrong-fix (REQUIRED floor): weak_nosparse.diff applies the correct dtype coercion but DROPS accept_sparse=['csr']. It fixes bool (probe_1 holds) but is REJECTED by probe_3 (sparse CSR now raises 'A sparse matrix was passed, but dense data is required'), violating R2.2. This proves the suite discriminates a plausibly-wrong partial fix.

Verdict SOUND: 7 distinct probes all hold on the patched tree, positive control (probe_1) fails at base and holds patched (prepatch reproduced), and a requirement-motivated alternative patch is rejected by the suite. No too-weak finding: every probe-conforming candidate that also keeps sparse support reduces to the gold change.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Req 1.3 (coerce non-float X to float during validation) precisely describes the patch. Req 2/3/4 are behavior-preservation obligations consistent with a pure dtype-coercion change; none contradicts patched behavior. Boundary is correctly pinned to the dtype coercion / bool-acceptance behavior rather than a narrow helper branch.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The core fix (boolean/integer X coerced to float during input validation, the TypeError, _huber_loss_and_gradient, axis0_safe_slice, HuberRegressor.fit, huber.py, the make_regression/X>0 reproduction, LinearRegression-coerces comparison) is entirely present in the public problem_statement and its traceback. The gold patch's dtype=[np.float64, np.float32] is only paraphrased behaviorally as 'single- or double-precision floating-point' — no verbatim gold line, no invented identifier. Req 3/4 describe PASS_TO_PASS regression properties (finite-difference gradient check, sample-weight-repeat equivalence, scaling invariance, epsilon->OLS, Ridge robustness, warm_start, max_iter); these are behavioral descriptions of the estimator's contract, i.e. the sanctioned translation of what tests check into requirements. No test function names, file paths, parametrization ids, or quoted test/gold code leak. The hidden FAIL_TO_PASS test (test_huber_bool) name/path/code is not disclosed and its content is already public via problem_statement. Naming modules/functions is legitimate localization.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
