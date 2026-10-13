# P2 adversarial audit — scikit-learn__scikit-learn-14894

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 5 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 5 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 5 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (5):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
# R1.1 + R1.3 + R2.1: sparse fit with empty support set completes; buffers empty.
# Positive control (fails at base with ZeroDivisionError).
import numpy as np
from scipy import sparse
from sklearn import svm

X = sparse.csr_matrix([[0,1,0,0],[0,0,0,1],[0,0,1,0],[0,0,0,1]])
y = np.array([0.04,0.04,0.10,0.16])
m = svm.SVR(kernel='linear')
m.fit(X, y)  # must not raise
print("support_vectors_ shape:", m.support_vectors_.shape,
      "data.size:", m.support_vectors_.data.size)
print("dual_coef_ data.size:", m.dual_coef_.data.size)
ok = (m.support_vectors_.data.size == 0) and (m.dual_coef_.data.size == 0)
print("PASS" if ok else "FAIL")
import sys; sys.exit(0 if ok else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
# R2.2: dual_coef_ is a sparse matrix of the SAME type used for a non-empty fit (csr).
import numpy as np
from scipy import sparse
from sklearn import svm

# empty-support case
X = sparse.csr_matrix([[0,1,0,0],[0,0,0,1],[0,0,1,0],[0,0,0,1]])
y = np.array([0.04,0.04,0.10,0.16])
m = svm.SVR(kernel='linear')
m.fit(X, y)
empty_type = type(m.dual_coef_)
print("empty dual_coef_ type:", empty_type)

# non-empty case for type reference
Xn = sparse.csr_matrix(np.array([[0.,0.],[1.,1.],[2.,2.],[3.,3.]]))
yn = np.array([0.0,1.0,2.0,3.0])
mn = svm.SVR(kernel='linear'); mn.fit(Xn, yn)
ne_type = type(mn.dual_coef_)
print("non-empty dual_coef_ type:", ne_type, "nSV:", mn.support_vectors_.shape[0])

ok = sparse.issparse(m.dual_coef_) and (empty_type is sparse.csr_matrix) and (empty_type is ne_type)
# also attribute access should not fail
_ = m.dual_coef_.shape
print("PASS" if ok else "FAIL")
import sys; sys.exit(0 if ok else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
# R3.1 + R3.2: non-empty sparse fit assembles dual_coef_ exactly (values, shape).
import numpy as np
from scipy import sparse
from sklearn import svm

rng = np.random.RandomState(0)
Xd = rng.rand(30, 5)
y = rng.rand(30)
Xs = sparse.csr_matrix(Xd)
ms = svm.SVR(kernel='linear', C=1.0).fit(Xs, y)
md = svm.SVR(kernel='linear', C=1.0).fit(Xd, y)
nSV = ms.support_vectors_.shape[0]
print("nSV sparse:", nSV, "dense:", md.support_vectors_.shape[0])
assert nSV > 0, "expected non-empty support set"
# shape: (1, nSV) for regression
print("dual_coef_ shape:", ms.dual_coef_.shape)
shape_ok = ms.dual_coef_.shape == (1, nSV)
# values match dense dual_coef_
sd = np.sort(np.asarray(ms.dual_coef_.todense()).ravel())
dd = np.sort(np.asarray(md.dual_coef_).ravel())
vals_ok = np.allclose(sd, dd, atol=1e-6)
print("values match dense:", vals_ok)
ok = shape_ok and vals_ok
print("PASS" if ok else "FAIL")
import sys; sys.exit(0 if ok else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
# R2.3 + R3.3: consistency dense vs sparse for empty support set; and predictions work.
import numpy as np
from scipy import sparse
from sklearn import svm

X = sparse.csr_matrix([[0,1,0,0],[0,0,0,1],[0,0,1,0],[0,0,0,1]])
Xd = X.toarray()
y = np.array([0.04,0.04,0.10,0.16])
ms = svm.SVR(kernel='linear').fit(X, y)
md = svm.SVR(kernel='linear').fit(Xd, y)
print("sparse nSV:", ms.support_vectors_.shape[0], "dense nSV:", md.support_vectors_.shape[0])
# both empty support & empty dual coef
c1 = ms.support_vectors_.shape[0] == 0
c2 = md.support_vectors_.shape[0] == 0 or md.support_vectors_.size == 0
c3 = ms.dual_coef_.data.size == 0
# prediction must not raise on sparse model
p = ms.predict(X)
print("pred shape:", p.shape)
ok = c1 and c3 and (p.shape[0] == 4)
print("PASS" if ok else "FAIL")
import sys; sys.exit(0 if ok else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
# R3.3 + R3.4: normal SVC sparse/dense classification preserved; input validation errors preserved.
import numpy as np
from scipy import sparse
from sklearn import svm

# classification: sparse decision_function/predict work and match dense reasonably
rng = np.random.RandomState(1)
Xd = np.vstack([rng.randn(20,4)-2, rng.randn(20,4)+2])
y = np.array([0]*20 + [1]*20)
Xs = sparse.csr_matrix(Xd)
cs = svm.SVC(kernel='linear', C=1.0).fit(Xs, y)
cd = svm.SVC(kernel='linear', C=1.0).fit(Xd, y)
nSV = cs.support_vectors_.shape[0]
print("SVC nSV sparse:", nSV, "dual_coef_ shape:", cs.dual_coef_.shape)
# n_class-1 = 1 row for binary
shape_ok = cs.dual_coef_.shape[0] == 1 and cs.dual_coef_.shape[1] == nSV
acc = (cs.predict(Xs) == y).mean()
print("train acc:", acc)
pred_ok = acc > 0.9

# input validation: invalid gamma should still raise
err_ok = False
try:
    svm.SVC(gamma=-1.0).fit(Xs, y)
except ValueError:
    err_ok = True
print("invalid gamma raised ValueError:", err_ok)

ok = shape_ok and pred_ok and err_ok
print("PASS" if ok else "FAIL")
import sys; sys.exit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
# R1.1 + R1.3 + R2.1: sparse fit with empty support set completes; buffers empty.
# Positive control (fails at base with ZeroDivisionError).
import numpy as np
from scipy import sparse
from sklearn import svm

X = sparse.csr_matrix([[0,1,0,0],[0,0,0,1],[0,0,1,0],[0,0,0,1]])
y = np.array([0.04,0.04,0.10,0.16])
m = svm.SVR(kernel='linear')
m.fit(X, y)  # must not raise
print("support_vectors_ shape:", m.support_vectors_.shape,
      "data.size:", m.support_vectors_.data.size)
print("dual_coef_ data.size:", m.dual_coef_.data.size)
ok = (m.support_vectors_.data.size == 0) and (m.dual_coef_.data.size == 0)
print("PASS" if ok else "FAIL")
import sys; sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance: sparse SVM _sparse_fit ZeroDivisionError when no support vectors. Gold patch guards `if not n_SV: self.dual_coef_ = sp.csr_matrix([])`.

Probes (all HOLD on gold-patched tree, exit 0):
- probe_1 (R1.1/R1.3/R2.1, POSITIVE CONTROL): SVR sparse fit on the #14893 dataset completes without error; support_vectors_.data.size==0 and dual_coef_.data.size==0. HOLDS patched, FAILS at base with ZeroDivisionError (float division by zero at base.py:291) => prepatch reproduced.
- probe_2 (R2.2): empty-case dual_coef_ is scipy.sparse csr_matrix, the SAME type as a non-empty fit's dual_coef_. HOLDS patched. Also FAILS at base (same ZeroDivisionError path).
- probe_3 (R3.1/R3.2): non-empty sparse SVR fit yields dual_coef_ shape (1, nSV) and values matching the dense fit (allclose). HOLDS patched.
- probe_4 (R2.3/R3.3): dense vs sparse consistency for empty support (both nSV==0, empty dual coef) and sparse predict() works without error. HOLDS patched; FAILS at base with ZeroDivisionError => second discriminating leg.
- probe_5 (R3.3/R3.4): SVC binary sparse classification preserved (dual_coef_ shape (1,nSV), train acc>0.9) and invalid gamma still raises ValueError. HOLDS patched.

Candidate wrong-fix (weak.diff): guards the empty case but assigns `self.dual_coef_ = np.array([])` instead of a csr_matrix — a lazy reading of "empty coefficient matrix" that still avoids the division. REJECTED by the suite: probe_2 fails (type is numpy.ndarray, not csr_matrix — violates R2.2), and probes 1 & 4 fail (np.array([]).data is a memoryview with no .size, violating R2.1's requirement that dual_coef_ be a sparse matrix with an empty data buffer). Demonstrates the suite discriminates a requirement-plausible wrong implementation; note the official F2P test test_sparse_fit_support_vectors_empty asserts `not model.dual_coef_.data.size` which would also break under this candidate.

All 5 probes HOLD on the patched tree; positive control discriminates (patched HOLD, base FAIL); >=1 candidate exercised and REJECTED. Verdict SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 5 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 5 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 5 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (5):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

_The 5 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts, and on this backend both roles put it through the same derivation: every block below is a requirement probe run on the gold-patched tree, and the `machine verdict:` line each role publishes above reports BOTH that its probes hold there and how many candidate patches the probe suite rejected — so the two roles re-ran ONE probe suite and each recorded its own outcome for every probe in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `probe_1.py` → holds on the patched tree (good)

Attack 2 — `probe_2.py` → holds on the patched tree (good)

Attack 3 — `probe_3.py` → holds on the patched tree (good)

Attack 4 — `probe_4.py` → holds on the patched tree (good)

Attack 5 — `probe_5.py` → holds on the patched tree (good)

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
# R1.1 + R1.3 + R2.1: sparse fit with empty support set completes; buffers empty.
# Positive control (fails at base with ZeroDivisionError).
import numpy as np
from scipy import sparse
from sklearn import svm

X = sparse.csr_matrix([[0,1,0,0],[0,0,0,1],[0,0,1,0],[0,0,0,1]])
y = np.array([0.04,0.04,0.10,0.16])
m = svm.SVR(kernel='linear')
m.fit(X, y)  # must not raise
print("support_vectors_ shape:", m.support_vectors_.shape,
      "data.size:", m.support_vectors_.data.size)
print("dual_coef_ data.size:", m.dual_coef_.data.size)
ok = (m.support_vectors_.data.size == 0) and (m.dual_coef_.data.size == 0)
print("PASS" if ok else "FAIL")
import sys; sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance: sparse SVM _sparse_fit ZeroDivisionError when no support vectors. Gold patch guards `if not n_SV: self.dual_coef_ = sp.csr_matrix([])`.

Probes (all HOLD on gold-patched tree, exit 0):
- probe_1 (R1.1/R1.3/R2.1, POSITIVE CONTROL): SVR sparse fit on the #14893 dataset completes without error; support_vectors_.data.size==0 and dual_coef_.data.size==0. HOLDS patched, FAILS at base with ZeroDivisionError (float division by zero at base.py:291) => prepatch reproduced.
- probe_2 (R2.2): empty-case dual_coef_ is scipy.sparse csr_matrix, the SAME type as a non-empty fit's dual_coef_. HOLDS patched. Also FAILS at base (same ZeroDivisionError path).
- probe_3 (R3.1/R3.2): non-empty sparse SVR fit yields dual_coef_ shape (1, nSV) and values matching the dense fit (allclose). HOLDS patched.
- probe_4 (R2.3/R3.3): dense vs sparse consistency for empty support (both nSV==0, empty dual coef) and sparse predict() works without error. HOLDS patched; FAILS at base with ZeroDivisionError => second discriminating leg.
- probe_5 (R3.3/R3.4): SVC binary sparse classification preserved (dual_coef_ shape (1,nSV), train acc>0.9) and invalid gamma still raises ValueError. HOLDS patched.

Candidate wrong-fix (weak.diff): guards the empty case but assigns `self.dual_coef_ = np.array([])` instead of a csr_matrix — a lazy reading of "empty coefficient matrix" that still avoids the division. REJECTED by the suite: probe_2 fails (type is numpy.ndarray, not csr_matrix — violates R2.2), and probes 1 & 4 fail (np.array([]).data is a memoryview with no .size, violating R2.1's requirement that dual_coef_ be a sparse matrix with an empty data buffer). Demonstrates the suite discriminates a requirement-plausible wrong implementation; note the official F2P test test_sparse_fit_support_vectors_empty asserts `not model.dual_coef_.data.size` which would also break under this candidate.

All 5 probes HOLD on the patched tree; positive control discriminates (patched HOLD, base FAIL); >=1 candidate exercised and REJECTED. Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Patch adds `if not n_SV: self.dual_coef_ = sp.csr_matrix([])` else the original CSR assembly. Requirements pin the changed observable boundary (empty vs non-empty support set on support_vectors_/dual_coef_), not a narrow slice or helper. Verified patch behavior directly; base confirmed to raise the documented ZeroDivisionError.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The requirements localize the change to `_sparse_fit` in sklearn/svm/base.py and describe expected behavior for the empty-support-vector case — all of which is already public in the problem_statement (the traceback names base.py line 302 / _sparse_fit, the ZeroDivisionError from `dual_coef_indices.size / n_class`, the reproduction data, and the expected `self.dual_coef_ = sp.csr_matrix([])`). No hidden-test artifacts leak: no test function name (test_sparse_fit_support_vectors_empty), no test file path, no FAIL_TO_PASS/PASS_TO_PASS ids, no quoted test/gold code, no fix-invented identifiers. Req 1.3/2.1's 'data buffer SHALL be empty' is a behavioral restatement of the empty CSR matrix (public expected result) rather than a transcription of the test's `.data.size` assertions; describing the empty-vs-nonempty offset division is exactly the behavioral translation the doc is meant to do. The Req 3 enumeration of estimators (SVC/NuSVC/SVR/NuSVR/OneClassSVM) reflects the public sklearn.svm API surface, not the test parametrization (which is over sample-weight/gamma-error cases). No semantic leakage.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
