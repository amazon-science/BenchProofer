# P2 adversarial audit — scikit-learn__scikit-learn-14087

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 requirement probes hold on the patched tree; 2/2 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 8 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 8 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py`, `probe_7.py`, `probe_8.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 2 alternative candidate patches, claimed to satisfy every cited requirement, and ran the same suite against them. The suite rejected all 2: a probe encoding a cited requirement fails under each of those, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_8.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (8):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
#!/usr/bin/env python
# R1: fit with refit=False, multi_class='auto' (default resolving), l2 penalty,
# 3 classes -> must complete without exception. Positive control.
import sys
import numpy as np
from sklearn.datasets import make_classification
from sklearn.linear_model import LogisticRegressionCV

n_classes = 3
n_features = 20
X, y = make_classification(n_samples=200, n_classes=n_classes, n_features=n_features,
                           n_informative=n_features, n_redundant=0, n_repeated=0,
                           random_state=0)
Cs = np.logspace(-4, 4, 3)
try:
    lrcv = LogisticRegressionCV(penalty='l2', Cs=Cs, solver='saga',
                                random_state=0, multi_class='auto', refit=False,
                                max_iter=50)
    lrcv.fit(X, y)
except Exception as e:
    print("FAIL: fit raised %r" % (e,))
    sys.exit(1)
print("OK: fit completed; coef_ shape=%s" % (lrcv.coef_.shape,))
sys.exit(0)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
#!/usr/bin/env python
# R1 ac2: refit=False completes for each of ovr, multinomial, auto (l2 penalty).
import sys
import numpy as np
from sklearn.datasets import make_classification
from sklearn.linear_model import LogisticRegressionCV

X, y = make_classification(n_samples=200, n_classes=3, n_features=20,
                           n_informative=20, n_redundant=0, n_repeated=0,
                           random_state=0)
Cs = np.logspace(-4, 4, 3)
ok = True
for mc in ('ovr', 'multinomial', 'auto'):
    try:
        lrcv = LogisticRegressionCV(penalty='l2', Cs=Cs, solver='saga',
                                    random_state=0, multi_class=mc, refit=False,
                                    max_iter=50)
        lrcv.fit(X, y)
        print("OK multi_class=%s coef_ shape=%s" % (mc, lrcv.coef_.shape))
    except Exception as e:
        print("FAIL multi_class=%s raised %r" % (mc, e))
        ok = False
sys.exit(0 if ok else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
#!/usr/bin/env python
# R2 ac1/ac3: with non-elasticnet penalty (l2), refit=False, each class's
# l1_ratio_ entry SHALL be None (not a numeric derived from placeholder).
import sys
import numpy as np
from sklearn.datasets import make_classification
from sklearn.linear_model import LogisticRegressionCV

X, y = make_classification(n_samples=200, n_classes=3, n_features=20,
                           n_informative=20, n_redundant=0, n_repeated=0,
                           random_state=0)
Cs = np.logspace(-4, 4, 3)
ok = True
for mc in ('ovr', 'multinomial', 'auto'):
    lrcv = LogisticRegressionCV(penalty='l2', Cs=Cs, solver='saga',
                                random_state=0, multi_class=mc, refit=False,
                                max_iter=50)
    lrcv.fit(X, y)
    l1r = list(np.ravel(lrcv.l1_ratio_))
    print("multi_class=%s l1_ratio_=%r" % (mc, l1r))
    if not all(v is None for v in l1r):
        print("FAIL: expected all None for l2 penalty, got %r" % (l1r,))
        ok = False
sys.exit(0 if ok else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
#!/usr/bin/env python
# R2 ac2 / R4 ac1: elasticnet + refit=False -> fit completes, l1_ratio_ entries
# are numeric (means of requested l1_ratios), NOT None. Also correct shape.
import sys
import numpy as np
from sklearn.datasets import make_classification
from sklearn.linear_model import LogisticRegressionCV

X, y = make_classification(n_samples=200, n_classes=3, n_features=20,
                           n_informative=20, n_redundant=0, n_repeated=0,
                           random_state=0)
Cs = np.logspace(-4, 4, 3)
l1_ratios = np.linspace(0, 1, 2)
ok = True
for mc in ('ovr', 'multinomial', 'auto'):
    lrcv = LogisticRegressionCV(penalty='elasticnet', Cs=Cs, solver='saga',
                                l1_ratios=l1_ratios, random_state=0,
                                multi_class=mc, refit=False, max_iter=50)
    lrcv.fit(X, y)
    l1r = list(np.ravel(lrcv.l1_ratio_))
    print("multi_class=%s l1_ratio_=%r" % (mc, l1r))
    if any(v is None for v in l1r):
        print("FAIL: elasticnet must give numeric l1_ratio_, got None")
        ok = False
    for v in l1r:
        if v is None:
            continue
        fv = float(v)
        if fv < l1_ratios.min() - 1e-9 or fv > l1_ratios.max() + 1e-9:
            print("FAIL: l1_ratio_ %r outside requested range" % (fv,))
            ok = False
sys.exit(0 if ok else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
#!/usr/bin/env python
# R3 ac1/ac2/ac3: C_ is mean of inverse-reg strengths from best per-fold indices,
# in the configured Cs range; coef_/intercept_ correctly shaped; l1_ratio_ has
# one entry per modeled class (tiled for multinomial).
import sys
import numpy as np
from sklearn.datasets import make_classification
from sklearn.linear_model import LogisticRegressionCV

n_classes = 3
X, y = make_classification(n_samples=200, n_classes=n_classes, n_features=20,
                           n_informative=20, n_redundant=0, n_repeated=0,
                           random_state=0)
Cs = np.logspace(-4, 4, 3)
ok = True
for mc in ('ovr', 'multinomial', 'auto'):
    lrcv = LogisticRegressionCV(penalty='l2', Cs=Cs, solver='saga',
                                random_state=0, multi_class=mc, refit=False,
                                max_iter=50)
    lrcv.fit(X, y)
    C_ = np.ravel(lrcv.C_)
    l1r = np.ravel(lrcv.l1_ratio_)
    print("mc=%s coef_=%s intercept_=%s len(C_)=%d len(l1_ratio_)=%d C_=%s"
          % (mc, lrcv.coef_.shape, lrcv.intercept_.shape, len(C_), len(l1r), C_))
    # coef_ rows == n_classes
    if lrcv.coef_.shape[0] != n_classes:
        print("FAIL: coef_ first dim %d != n_classes %d" % (lrcv.coef_.shape[0], n_classes))
        ok = False
    if lrcv.coef_.shape[1] != X.shape[1]:
        print("FAIL: coef_ second dim wrong")
        ok = False
    # C_ and l1_ratio_ one entry per modeled class
    if len(C_) != n_classes:
        print("FAIL: len(C_) %d != n_classes %d" % (len(C_), n_classes))
        ok = False
    if len(l1r) != n_classes:
        print("FAIL: len(l1_ratio_) %d != n_classes %d" % (len(l1r), n_classes))
        ok = False
    # C_ values must be among/within the configured Cs range (means of chosen Cs)
    for c in C_:
        if c < Cs.min() - 1e-6 or c > Cs.max() + 1e-6:
            print("FAIL: C_ value %r outside Cs range" % (c,))
            ok = False
sys.exit(0 if ok else 1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
#!/usr/bin/env python
# R4 ac2: refit=True path unchanged - fit completes and coef_ properly shaped.
# R4 ac3: coefs_paths_, scores_, Cs_, l1_ratios_ correctly shaped incl. l1 dim.
import sys
import numpy as np
from sklearn.datasets import make_classification
from sklearn.linear_model import LogisticRegressionCV

n_classes = 3
X, y = make_classification(n_samples=200, n_classes=n_classes, n_features=20,
                           n_informative=20, n_redundant=0, n_repeated=0,
                           random_state=0)
Cs = np.logspace(-4, 4, 3)
l1_ratios = np.linspace(0, 1, 2)
ok = True

# refit=True default path with elasticnet
lrcv = LogisticRegressionCV(penalty='elasticnet', Cs=Cs, solver='saga',
                            l1_ratios=l1_ratios, random_state=0,
                            multi_class='auto', refit=True, max_iter=50)
lrcv.fit(X, y)
print("refit=True coef_=%s" % (lrcv.coef_.shape,))
if lrcv.coef_.shape[0] != n_classes:
    print("FAIL refit=True coef_ shape")
    ok = False

# coefs_paths_ / scores_ / l1_ratios_ shapes with elasticnet l1 dim present
key = list(lrcv.coefs_paths_.keys())[0]
cp = lrcv.coefs_paths_[key]
sc = lrcv.scores_[key]
print("coefs_paths_ shape=%s scores_ shape=%s Cs_=%s l1_ratios_=%s"
      % (cp.shape, sc.shape, lrcv.Cs_.shape, lrcv.l1_ratios_))
# last-but-... elasticnet adds mixing dim: scores_ per class shape (folds, Cs, l1)
if sc.shape[-1] != len(l1_ratios):
    print("FAIL: scores_ missing l1 dim; got %s expected last %d" % (sc.shape, len(l1_ratios)))
    ok = False
if len(lrcv.Cs_) != len(Cs):
    print("FAIL: Cs_ len wrong")
    ok = False
sys.exit(0 if ok else 1)
```

Attack 7 — `probe_7.py` → holds on the patched tree (good)

```python
#!/usr/bin/env python
# R4 ac4: existing validation errors preserved - invalid l1_ratio raises.
import sys
import numpy as np
from sklearn.datasets import make_classification
from sklearn.linear_model import LogisticRegressionCV

X, y = make_classification(n_samples=100, n_classes=3, n_features=20,
                           n_informative=20, n_redundant=0, n_repeated=0,
                           random_state=0)
ok = True
# invalid l1_ratios value (>1) with elasticnet must raise ValueError
try:
    LogisticRegressionCV(penalty='elasticnet', solver='saga',
                         l1_ratios=[2.0], refit=False, max_iter=20).fit(X, y)
    print("FAIL: no error for invalid l1_ratios=2.0")
    ok = False
except ValueError as e:
    print("OK invalid l1_ratios raised ValueError: %s" % (str(e)[:60],))
except Exception as e:
    print("FAIL: wrong exception type %r" % (e,))
    ok = False
sys.exit(0 if ok else 1)
```

Attack 8 — `probe_8.py` → holds on the patched tree (good)

```python
#!/usr/bin/env python
# R1 ac4/ac5: branch selected by EFFECTIVE strategy, not configured self.multi_class.
# Binary problem + multi_class='auto' resolves to 'ovr' (auto->ovr for binary),
# while self.multi_class stays 'auto'. Original code checks self.multi_class=='ovr'
# -> False -> multinomial(else) layout on an ovr-shaped coefs_paths -> IndexError.
import sys
import numpy as np
from sklearn.datasets import make_classification
from sklearn.linear_model import LogisticRegressionCV

X, y = make_classification(n_samples=200, n_classes=2, n_features=20,
                           n_informative=10, n_redundant=0, n_repeated=0,
                           random_state=0)
Cs = np.logspace(-4, 4, 3)
try:
    lrcv = LogisticRegressionCV(penalty='l2', Cs=Cs, solver='lbfgs',
                                random_state=0, multi_class='auto', refit=False,
                                max_iter=50)
    lrcv.fit(X, y)
except Exception as e:
    print("FAIL: binary auto refit=False raised %r" % (e,))
    sys.exit(1)
print("OK: binary+auto fit completed; coef_ shape=%s" % (lrcv.coef_.shape,))
sys.exit(0)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_8.py`

```python
#!/usr/bin/env python
# R1 ac4/ac5: branch selected by EFFECTIVE strategy, not configured self.multi_class.
# Binary problem + multi_class='auto' resolves to 'ovr' (auto->ovr for binary),
# while self.multi_class stays 'auto'. Original code checks self.multi_class=='ovr'
# -> False -> multinomial(else) layout on an ovr-shaped coefs_paths -> IndexError.
import sys
import numpy as np
from sklearn.datasets import make_classification
from sklearn.linear_model import LogisticRegressionCV

X, y = make_classification(n_samples=200, n_classes=2, n_features=20,
                           n_informative=10, n_redundant=0, n_repeated=0,
                           random_state=0)
Cs = np.logspace(-4, 4, 3)
try:
    lrcv = LogisticRegressionCV(penalty='l2', Cs=Cs, solver='lbfgs',
                                random_state=0, multi_class='auto', refit=False,
                                max_iter=50)
    lrcv.fit(X, y)
except Exception as e:
    print("FAIL: binary auto refit=False raised %r" % (e,))
    sys.exit(1)
print("OK: binary+auto fit completed; coef_ shape=%s" % (lrcv.coef_.shape,))
sys.exit(0)
```

Prepatch bug re-encoded as an attack: `True`.

Requirements for scikit-learn-14087 (LogisticRegressionCV refit=False). Two defects: (1) branch chosen from raw self.multi_class instead of effective multi_class -> IndexError; (2) l1_ratio_ recorded numeric even for non-elasticnet. Gold patch changes `self.multi_class=='ovr'` -> `multi_class=='ovr'` and appends None for non-elasticnet l1_ratio_.

8 probes, ALL HOLD on the gold-patched tree:
- probe_1 (R1 ac1): refit=False, multi_class='auto', l2, 3 classes -> fit completes. HOLDS patched / VIOLATED base (IndexError).
- probe_2 (R1 ac2): completes for ovr/multinomial/auto (l2). HOLDS patched / VIOLATED base.
- probe_3 (R2 ac1/ac3): non-elasticnet l1_ratio_ entries all None. HOLDS patched / VIOLATED base (TypeError indexing placeholder).
- probe_4 (R2 ac2 / R4 ac1): elasticnet l1_ratio_ numeric within requested range. HOLDS patched.
- probe_5 (R3): C_ mean within Cs range, coef_/intercept_ shapes, len(C_)==len(l1_ratio_)==n_classes. HOLDS patched.
- probe_6 (R4 ac2/ac3): refit=True path + coefs_paths_/scores_/Cs_ shapes incl elasticnet l1 dim. HOLDS patched.
- probe_7 (R4 ac4): invalid l1_ratios=2.0 still raises ValueError. HOLDS patched.
- probe_8 (R1 ac4/ac5, POSITIVE CONTROL): binary problem + multi_class='auto' (resolves to 'ovr' but self.multi_class stays 'auto') -> effective-strategy branch must be used. HOLDS patched (coef_ (1,20)) / VIOLATED base (IndexError: 3-dim array, 4 indexed).

Candidate wrong patches (both REJECTED by the suite -> suite discriminates):
- weakA (multi_class fix only, no l1_ratio fix): REJECTED by probe_3 & probe_5 (TypeError indexing l1_ratios placeholder for l2).
- weakB (l1_ratio fix only, keeps buggy self.multi_class check): passes probes 1-7 but REJECTED by probe_8 (binary+auto IndexError), the R1 ac4/ac5 effective-vs-configured discriminator. This confirms both halves of the gold fix are load-bearing and pinned by the requirements/probe suite.

Positive control discriminates (holds patched, fails at base). No probe fails on patched; no requirements-conforming alternative patch survives. Verdict SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 requirement probes hold on the patched tree; 2/2 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 8 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 8 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py`, `probe_7.py`, `probe_8.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 2 alternative candidate patches, claimed to satisfy every cited requirement, and ran the same suite against them. The suite rejected all 2: a probe encoding a cited requirement fails under each of those, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_8.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

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

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_8.py`

```python
#!/usr/bin/env python
# R1 ac4/ac5: branch selected by EFFECTIVE strategy, not configured self.multi_class.
# Binary problem + multi_class='auto' resolves to 'ovr' (auto->ovr for binary),
# while self.multi_class stays 'auto'. Original code checks self.multi_class=='ovr'
# -> False -> multinomial(else) layout on an ovr-shaped coefs_paths -> IndexError.
import sys
import numpy as np
from sklearn.datasets import make_classification
from sklearn.linear_model import LogisticRegressionCV

X, y = make_classification(n_samples=200, n_classes=2, n_features=20,
                           n_informative=10, n_redundant=0, n_repeated=0,
                           random_state=0)
Cs = np.logspace(-4, 4, 3)
try:
    lrcv = LogisticRegressionCV(penalty='l2', Cs=Cs, solver='lbfgs',
                                random_state=0, multi_class='auto', refit=False,
                                max_iter=50)
    lrcv.fit(X, y)
except Exception as e:
    print("FAIL: binary auto refit=False raised %r" % (e,))
    sys.exit(1)
print("OK: binary+auto fit completed; coef_ shape=%s" % (lrcv.coef_.shape,))
sys.exit(0)
```

Prepatch bug re-encoded as an attack: `True`.

Requirements for scikit-learn-14087 (LogisticRegressionCV refit=False). Two defects: (1) branch chosen from raw self.multi_class instead of effective multi_class -> IndexError; (2) l1_ratio_ recorded numeric even for non-elasticnet. Gold patch changes `self.multi_class=='ovr'` -> `multi_class=='ovr'` and appends None for non-elasticnet l1_ratio_.

8 probes, ALL HOLD on the gold-patched tree:
- probe_1 (R1 ac1): refit=False, multi_class='auto', l2, 3 classes -> fit completes. HOLDS patched / VIOLATED base (IndexError).
- probe_2 (R1 ac2): completes for ovr/multinomial/auto (l2). HOLDS patched / VIOLATED base.
- probe_3 (R2 ac1/ac3): non-elasticnet l1_ratio_ entries all None. HOLDS patched / VIOLATED base (TypeError indexing placeholder).
- probe_4 (R2 ac2 / R4 ac1): elasticnet l1_ratio_ numeric within requested range. HOLDS patched.
- probe_5 (R3): C_ mean within Cs range, coef_/intercept_ shapes, len(C_)==len(l1_ratio_)==n_classes. HOLDS patched.
- probe_6 (R4 ac2/ac3): refit=True path + coefs_paths_/scores_/Cs_ shapes incl elasticnet l1 dim. HOLDS patched.
- probe_7 (R4 ac4): invalid l1_ratios=2.0 still raises ValueError. HOLDS patched.
- probe_8 (R1 ac4/ac5, POSITIVE CONTROL): binary problem + multi_class='auto' (resolves to 'ovr' but self.multi_class stays 'auto') -> effective-strategy branch must be used. HOLDS patched (coef_ (1,20)) / VIOLATED base (IndexError: 3-dim array, 4 indexed).

Candidate wrong patches (both REJECTED by the suite -> suite discriminates):
- weakA (multi_class fix only, no l1_ratio fix): REJECTED by probe_3 & probe_5 (TypeError indexing l1_ratios placeholder for l2).
- weakB (l1_ratio fix only, keeps buggy self.multi_class check): passes probes 1-7 but REJECTED by probe_8 (binary+auto IndexError), the R1 ac4/ac5 effective-vs-configured discriminator. This confirms both halves of the gold fix are load-bearing and pinned by the requirements/probe suite.

Positive control discriminates (holds patched, fails at base). No probe fails on patched; no requirements-conforming alternative patch survives. Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Gold patch changes exactly two things in the refit=False summary loop: (a) `if self.multi_class == 'ovr'` -> `if multi_class == 'ovr'` (use the effective strategy resolved via _check_multi_class), fixing the IndexError; (b) guard l1_ratio_ recording on `self.penalty == 'elasticnet'`, appending None otherwise. Requirements pin exactly this changed observable behavior at the correct boundary (not a narrow single-branch slice). Probe on gold tree: all 6 (multi_class x penalty) combos fit without error; l1_ratio_ None-filled for l2, numeric for elasticnet. Probe on base: exit 1 (IndexError). FAIL_TO_PASS covers the l2 cases across ovr/multinomial/auto, matching Req1.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** requirements.md translates the gold patch (multi_class resolution fix and l1_ratio_=None branch outside elasticnet) into behavioral EARS requirements. All identifiers named (self.multi_class, _check_multi_class, coef_/intercept_/C_/l1_ratio_, coefs_paths, logistic.py) are legitimate public API / localization of the change, not fix-invented names. The enumerated multiclass strategies 'ovr'/'multinomial'/'auto' are standard documented sklearn API values, not test-derived; likewise the penalty distinction elasticnet vs non-elasticnet is the gold behavior, not test code. No test function names, file paths, parametrization ids (e.g. [ovr-l2]), or quoted test/gold code appear. Enumerations describe behavior across the API surface rather than mirroring the specific test cases.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
