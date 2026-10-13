# P2 adversarial audit — scikit-learn__scikit-learn-12973

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
"""Positive control. Req 1.3 / 3.2: fit with explicit copy_X=False and default
init copy_X (True) MUST allow the feature matrix to be overwritten in place.
Holds on patched (explicit False reaches _preprocess_data); fails at base
(base always forwards self.copy_X == True, so X is copied and stays equal)."""
import numpy as np
from sklearn.linear_model import LassoLarsIC

rng = np.random.RandomState(0)
X = rng.normal(0, 1, (100, 5))
X_copy = X.copy()
y = X[:, 2]
est = LassoLarsIC(precompute=False)          # init copy_X defaults to True
est.fit(X, y, copy_X=False)                   # explicit per-call False
unchanged = np.array_equal(X, X_copy)
print("X unchanged after fit(copy_X=False):", unchanged)
# behavior holds iff X was allowed to be overwritten (i.e. NOT unchanged)
import sys
sys.exit(0 if not unchanged else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""Req 1.2 / 1.1: fit with explicit copy_X=True overrides init copy_X=False and
MUST leave the caller's feature matrix unchanged."""
import numpy as np, sys
from sklearn.linear_model import LassoLarsIC

rng = np.random.RandomState(0)
X = rng.normal(0, 1, (100, 5))
X_copy = X.copy()
y = X[:, 2]
est = LassoLarsIC(copy_X=False, precompute=False)  # init says overwrite allowed
est.fit(X, y, copy_X=True)                          # explicit True must win
unchanged = np.array_equal(X, X_copy)
print("X unchanged after fit(copy_X=True) with init copy_X=False:", unchanged)
sys.exit(0 if unchanged else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""Req 2.2: constructed copy_X=False, fit without explicit per-call value MUST
be permitted to overwrite X in place (fall back to configured False)."""
import numpy as np, sys
from sklearn.linear_model import LassoLarsIC

rng = np.random.RandomState(0)
X = rng.normal(0, 1, (100, 5))
X_copy = X.copy()
y = X[:, 2]
est = LassoLarsIC(copy_X=False, precompute=False)
est.fit(X, y)                                       # no per-call value
unchanged = np.array_equal(X, X_copy)
print("X unchanged after fit() with init copy_X=False:", unchanged)
sys.exit(0 if not unchanged else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""Req 2.3 / 2.1: constructed copy_X=True, fit without explicit value MUST leave
X unchanged (fall back to configured True)."""
import numpy as np, sys
from sklearn.linear_model import LassoLarsIC

rng = np.random.RandomState(0)
X = rng.normal(0, 1, (100, 5))
X_copy = X.copy()
y = X[:, 2]
est = LassoLarsIC(copy_X=True, precompute=False)
est.fit(X, y)
unchanged = np.array_equal(X, X_copy)
print("X unchanged after fit() with init copy_X=True:", unchanged)
sys.exit(0 if unchanged else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""Req 3.3: a fit call supplying a per-call value SHALL NOT mutate the estimator's
configuration attribute copy_X. Also Req 2.4: default distinguishable from bool."""
import numpy as np, sys, inspect
from sklearn.linear_model import LassoLarsIC

rng = np.random.RandomState(0)
X = rng.normal(0, 1, (100, 5))
y = X[:, 2]

est = LassoLarsIC(copy_X=True, precompute=False)
before = est.copy_X
est.fit(X.copy(), y, copy_X=False)      # per-call differs from config
after = est.copy_X
print("est.copy_X before:", before, "after:", after)

# Req 2.4: fit signature default must be distinguishable from explicit bool
sig = inspect.signature(LassoLarsIC.fit)
default = sig.parameters['copy_X'].default
print("fit copy_X default:", default)
ok = (before is True and after is True) and (default is None or not isinstance(default, bool))
sys.exit(0 if ok else 1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
"""Req 4.1 / 4.3: the ordinary path (no explicit per-call copy_X, default init
copy_X=True) computes the SAME fitted coefficients and IC selection as an
explicit copy_X=True fit, for both AIC and BIC, and leaves X unchanged. This is
the 'no regression' criterion: the resolved boolean only governs copying, and the
default (True) path must be numerically identical to the pre-fix behavior (which
always forwarded copy_X=True)."""
import numpy as np, sys
from sklearn.linear_model import LassoLarsIC

rng = np.random.RandomState(1)
Xbase = rng.normal(0, 1, (80, 6))
ybase = Xbase[:, 0] * 2.0 - Xbase[:, 3] + 0.1 * rng.normal(0, 1, 80)

ok = True
for crit in ("aic", "bic"):
    Xd = Xbase.copy()
    ed = LassoLarsIC(criterion=crit, precompute=False).fit(Xd, ybase.copy())  # ordinary
    et = LassoLarsIC(criterion=crit, precompute=False).fit(Xbase.copy(), ybase.copy(), copy_X=True)
    same_coef = np.allclose(ed.coef_, et.coef_)
    same_alpha = np.isclose(ed.alpha_, et.alpha_)
    x_unchanged = np.array_equal(Xd, Xbase)
    print(crit, "coef==:", same_coef, "alpha==:", same_alpha, "X unchanged:", x_unchanged,
          "coef:", np.round(ed.coef_, 4))
    ok = ok and same_coef and same_alpha and x_unchanged
sys.exit(0 if ok else 1)
```

Attack 7 — `probe_7.py` → holds on the patched tree (good)

```python
"""Req 4.2: existing Lars / LassoLars / lars_path code paths remain unchanged,
including precomputed Gram, positivity, multi-target, and fit_path=False. Smoke
these to ensure the patch did not disturb them."""
import numpy as np, sys
from sklearn.linear_model import Lars, LassoLars, LassoLarsIC, lars_path

rng = np.random.RandomState(2)
X = rng.normal(0, 1, (60, 5))
y = X[:, 0] - 0.5 * X[:, 2] + 0.05 * rng.normal(0, 1, 60)
Y = np.c_[y, X[:, 1]]  # multi-target

ok = True
# lars_path with precomputed Gram
Xc = X - X.mean(0)
Gram = Xc.T.dot(Xc)
alphas, active, coefs = lars_path(Xc, y - y.mean(), Gram=Gram, method='lar')
ok = ok and coefs.shape[0] == 5
print("lars_path Gram coefs shape:", coefs.shape)

# positivity constraint
ll = LassoLars(alpha=0.01, positive=True).fit(X, y)
ok = ok and np.all(ll.coef_ >= -1e-12)
print("LassoLars positive all>=0:", bool(np.all(ll.coef_ >= -1e-12)))

# multi-target Lars
lm = Lars(n_nonzero_coefs=3).fit(X, Y)
ok = ok and lm.coef_.shape[0] == 2
print("Lars multitarget coef shape:", lm.coef_.shape)

# fit_path=False on LassoLarsIC still fits
ic = LassoLarsIC(criterion='bic', precompute=False).fit(X.copy(), y.copy())
ok = ok and ic.coef_.shape == (5,)
print("LassoLarsIC coef shape:", ic.coef_.shape)

sys.exit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Positive control. Req 1.3 / 3.2: fit with explicit copy_X=False and default
init copy_X (True) MUST allow the feature matrix to be overwritten in place.
Holds on patched (explicit False reaches _preprocess_data); fails at base
(base always forwards self.copy_X == True, so X is copied and stays equal)."""
import numpy as np
from sklearn.linear_model import LassoLarsIC

rng = np.random.RandomState(0)
X = rng.normal(0, 1, (100, 5))
X_copy = X.copy()
y = X[:, 2]
est = LassoLarsIC(precompute=False)          # init copy_X defaults to True
est.fit(X, y, copy_X=False)                   # explicit per-call False
unchanged = np.array_equal(X, X_copy)
print("X unchanged after fit(copy_X=False):", unchanged)
# behavior holds iff X was allowed to be overwritten (i.e. NOT unchanged)
import sys
sys.exit(0 if not unchanged else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance forwards a resolved copy_X to _preprocess_data: fit(copy_X=None default) falls back to self.copy_X, an explicit value overrides it, and self.copy_X is never mutated.

Probes (requirement -> observed patched / base):
- probe_1 (POSITIVE CONTROL, Req 1.3/3.2): fit(copy_X=False) with init default True must allow X overwrite. Patched: HOLDS (X mutated). Base: FAILS (X copied, unchanged). Discriminates.
- probe_2 (Req 1.1/1.2): init copy_X=False, fit(copy_X=True) must leave X unchanged. Patched HOLDS; base VIOLATED (base ignored per-call arg, used self.copy_X=False -> mutated).
- probe_3 (Req 2.2): init copy_X=False, fit() no per-call must allow overwrite. Patched HOLDS; base HOLDS (base already forwarded self.copy_X here) -> not itself discriminating vs base, but REJECTS the weak candidate.
- probe_4 (Req 2.1/2.3): init copy_X=True, fit() leaves X unchanged. Patched HOLDS.
- probe_5 (Req 3.3/2.4): fit(copy_X=False) does not mutate est.copy_X (stays True) AND fit's copy_X default is non-bool (None). Patched HOLDS; base VIOLATED (default was True, a bool -> 'no value' indistinguishable from explicit True).
- probe_6 (Req 4.1/4.3, regression): ordinary default fit == explicit copy_X=True fit for AIC and BIC (coef, alpha) and leaves X unchanged. Patched HOLDS. (Initial draft comparing copy_X=True vs copy_X=False fits FAILED on patched — a pre-existing sklearn numeric quirk where the in-place-overwrite preprocessing path diverges numerically; that is NOT mandated by the requirements, which only pin the ordinary no-per-call path. Rewrote to test the actual regression criterion.)
- probe_7 (Req 4.2, regression): Lars multi-target, LassoLars positivity, lars_path with precomputed Gram, LassoLarsIC fit all still work. Patched HOLDS.

Candidate patch weak_default_true: keeps fit signature default copy_X=True (does NOT switch to None) but changes _preprocess_data to receive the parameter copy_X. This is the lazy fix that makes the FAIL_TO_PASS test pass (explicit per-call value is honored) but silently overrides a construction-time copy_X=False when fit() is called with no arg (default True clobbers it) and leaves 'no value' indistinguishable from explicit True. My suite REJECTS it: probe_3 VIOLATED (fallback to configured False lost) and probe_5 VIOLATED (default is a bool, Req 2.4). Demonstrates the suite discriminates a requirements-plausible wrong fix.

>=5 distinct probes all hold on patched; positive control holds patched and fails at base (prepatch reproduced); >=1 candidate exercised and rejected. SOUND.

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
"""Positive control. Req 1.3 / 3.2: fit with explicit copy_X=False and default
init copy_X (True) MUST allow the feature matrix to be overwritten in place.
Holds on patched (explicit False reaches _preprocess_data); fails at base
(base always forwards self.copy_X == True, so X is copied and stays equal)."""
import numpy as np
from sklearn.linear_model import LassoLarsIC

rng = np.random.RandomState(0)
X = rng.normal(0, 1, (100, 5))
X_copy = X.copy()
y = X[:, 2]
est = LassoLarsIC(precompute=False)          # init copy_X defaults to True
est.fit(X, y, copy_X=False)                   # explicit per-call False
unchanged = np.array_equal(X, X_copy)
print("X unchanged after fit(copy_X=False):", unchanged)
# behavior holds iff X was allowed to be overwritten (i.e. NOT unchanged)
import sys
sys.exit(0 if not unchanged else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance forwards a resolved copy_X to _preprocess_data: fit(copy_X=None default) falls back to self.copy_X, an explicit value overrides it, and self.copy_X is never mutated.

Probes (requirement -> observed patched / base):
- probe_1 (POSITIVE CONTROL, Req 1.3/3.2): fit(copy_X=False) with init default True must allow X overwrite. Patched: HOLDS (X mutated). Base: FAILS (X copied, unchanged). Discriminates.
- probe_2 (Req 1.1/1.2): init copy_X=False, fit(copy_X=True) must leave X unchanged. Patched HOLDS; base VIOLATED (base ignored per-call arg, used self.copy_X=False -> mutated).
- probe_3 (Req 2.2): init copy_X=False, fit() no per-call must allow overwrite. Patched HOLDS; base HOLDS (base already forwarded self.copy_X here) -> not itself discriminating vs base, but REJECTS the weak candidate.
- probe_4 (Req 2.1/2.3): init copy_X=True, fit() leaves X unchanged. Patched HOLDS.
- probe_5 (Req 3.3/2.4): fit(copy_X=False) does not mutate est.copy_X (stays True) AND fit's copy_X default is non-bool (None). Patched HOLDS; base VIOLATED (default was True, a bool -> 'no value' indistinguishable from explicit True).
- probe_6 (Req 4.1/4.3, regression): ordinary default fit == explicit copy_X=True fit for AIC and BIC (coef, alpha) and leaves X unchanged. Patched HOLDS. (Initial draft comparing copy_X=True vs copy_X=False fits FAILED on patched — a pre-existing sklearn numeric quirk where the in-place-overwrite preprocessing path diverges numerically; that is NOT mandated by the requirements, which only pin the ordinary no-per-call path. Rewrote to test the actual regression criterion.)
- probe_7 (Req 4.2, regression): Lars multi-target, LassoLars positivity, lars_path with precomputed Gram, LassoLarsIC fit all still work. Patched HOLDS.

Candidate patch weak_default_true: keeps fit signature default copy_X=True (does NOT switch to None) but changes _preprocess_data to receive the parameter copy_X. This is the lazy fix that makes the FAIL_TO_PASS test pass (explicit per-call value is honored) but silently overrides a construction-time copy_X=False when fit() is called with no arg (default True clobbers it) and leaves 'no value' indistinguishable from explicit True. My suite REJECTS it: probe_3 VIOLATED (fallback to configured False lost) and probe_5 VIOLATED (default is a bool, Req 2.4). Demonstrates the suite discriminates a requirements-plausible wrong fix.

>=5 distinct probes all hold on patched; positive control holds patched and fails at base (prepatch reproduced); >=1 candidate exercised and rejected. SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Patch: fit(copy_X=None); if copy_X is None: copy_X=self.copy_X; then _preprocess_data(...,copy_X) instead of self.copy_X. Req3 (single resolved boolean, None sentinel, attribute unchanged) and Req4 (preservation of Lars/lars_path etc.) are consistent with the minimal 2-line change and not contradicted by any code path. Modeling boundary is correct: requirements are keyed to the resolution logic + observable copy behavior, matching the diff.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** requirements.md stays within the public problem_statement, which already names LassoLarsIC, copy_X, fit(self,X,y,copy_X=True), sklearn/linear_model/least_angle.py, and the proposed resolution (fit default None, override construction value only if explicitly passed). Behavioral criteria (leave matrix unchanged vs may overwrite; explicit-per-call precedence; single resolved boolean to _preprocess_data) are translations of copy_X semantics, not copies of the hidden test assertions. The true/false enumeration is intrinsic to a boolean flag, not a mirror of parametrize('copy_X',[True,False]). No test names/paths/ids (test_lasso_lars_copyX_behaviour, test_lasso_lars_fit_copyX_behaviour), no quoted test/gold code, no fix-invented identifiers, and the preserved-behavior class list (Lars/LarsCV/LassoLars/LassoLarsCV/lars_path, AIC/BIC) is public API scope for regression, not PASS_TO_PASS reconstruction.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
