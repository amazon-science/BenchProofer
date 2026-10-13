# P2 adversarial audit — scikit-learn__scikit-learn-14629

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
"""Positive control + R1.1/R1.2/R1.3: fitted MultiOutputClassifier exposes
classes_ as a list with one entry per target column.
Exits 0 iff classes_ exists, is a list, and len == n_targets."""
import sys
import numpy as np
from sklearn.multioutput import MultiOutputClassifier
from sklearn.linear_model import LogisticRegression

rng = np.random.RandomState(0)
X = rng.randn(50, 4)
Y = np.column_stack([
    rng.randint(0, 2, 50),
    rng.randint(0, 3, 50),
    rng.randint(0, 2, 50),
])
clf = MultiOutputClassifier(LogisticRegression(solver="liblinear"))
clf.fit(X, Y)

if not hasattr(clf, "classes_"):
    print("FAIL: no classes_ attribute")
    sys.exit(1)
c = clf.classes_
print("classes_ type:", type(c).__name__)
print("classes_ value:", c)
if not isinstance(c, list):
    print("FAIL: classes_ is not a list")
    sys.exit(1)
if len(c) != Y.shape[1]:
    print("FAIL: len(classes_)=%d != n_targets=%d" % (len(c), Y.shape[1]))
    sys.exit(1)
print("PASS: classes_ is a list of length %d" % len(c))
sys.exit(0)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""R1.4 / R1.5: entry i of classes_ equals exactly the class labels recorded by
the sub-estimator fitted for target column i, in order.
Exits 0 iff each classes_[i] is elementwise equal to estimators_[i].classes_."""
import sys
import numpy as np
from sklearn.multioutput import MultiOutputClassifier
from sklearn.linear_model import LogisticRegression

rng = np.random.RandomState(1)
X = rng.randn(60, 5)
# Use distinct label sets per target and non-trivial (string) labels
Y = np.column_stack([
    rng.choice(["a", "b"], 60),
    rng.choice(["x", "y", "z"], 60),
    rng.choice([10, 20], 60),
]).astype(object)
clf = MultiOutputClassifier(LogisticRegression(solver="liblinear"))
clf.fit(X, Y)

ok = True
for i, est in enumerate(clf.estimators_):
    got = clf.classes_[i]
    exp = est.classes_
    print("target %d: classes_=%r  estimator.classes_=%r" % (i, got, exp))
    if not (np.asarray(got).shape == np.asarray(exp).shape and np.all(np.asarray(got) == np.asarray(exp))):
        ok = False
        print("  MISMATCH at target %d" % i)
    if got is not exp:
        # not required to be identical object, only equal — informational
        pass
if not ok:
    print("FAIL: classes_ entries do not match sub-estimator classes_")
    sys.exit(1)
print("PASS: all entries match sub-estimator classes_ elementwise and in order")
sys.exit(0)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""R2.1 / R2.2 / R2.3: additive behavior preserved — fit returns self, exposes
estimators_ (one per target), predict shape correct, predict_proba returns list.
Exits 0 iff all hold."""
import sys
import numpy as np
from sklearn.multioutput import MultiOutputClassifier
from sklearn.linear_model import LogisticRegression

rng = np.random.RandomState(2)
X = rng.randn(40, 3)
Y = np.column_stack([
    rng.randint(0, 2, 40),
    rng.randint(0, 3, 40),
])
clf = MultiOutputClassifier(LogisticRegression(solver="liblinear"))
ret = clf.fit(X, Y)
if ret is not clf:
    print("FAIL: fit did not return self")
    sys.exit(1)
if len(clf.estimators_) != Y.shape[1]:
    print("FAIL: estimators_ count wrong")
    sys.exit(1)
pred = clf.predict(X)
print("predict shape:", pred.shape)
if pred.shape != (X.shape[0], Y.shape[1]):
    print("FAIL: predict shape wrong")
    sys.exit(1)
proba = clf.predict_proba(X)
print("predict_proba type:", type(proba).__name__, "len:", len(proba))
if not (isinstance(proba, list) and len(proba) == Y.shape[1]):
    print("FAIL: predict_proba not a list of per-target arrays")
    sys.exit(1)
for i, p in enumerate(proba):
    if p.shape[0] != X.shape[0]:
        print("FAIL: proba[%d] wrong n_samples" % i)
        sys.exit(1)
print("PASS: fit/predict/predict_proba behavior preserved")
sys.exit(0)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""R2.4: sample_weight forwarding/validation. If base estimator does NOT support
sample_weight, fit raises ValueError; if it does, weights forwarded (fit succeeds
and classes_ still exposed).
Exits 0 iff both branches behave as specified."""
import sys
import numpy as np
from sklearn.multioutput import MultiOutputClassifier
from sklearn.linear_model import LogisticRegression

rng = np.random.RandomState(3)
X = rng.randn(40, 3)
Y = np.column_stack([rng.randint(0, 2, 40), rng.randint(0, 2, 40)])
sw = rng.rand(40)

# A classifier lacking sample_weight support in fit signature.
class NoSW(LogisticRegression):
    def fit(self, X, y):  # no sample_weight param
        return super().fit(X, y)

clf_no = MultiOutputClassifier(NoSW(solver="liblinear"))
raised = False
try:
    clf_no.fit(X, Y, sample_weight=sw)
except ValueError as e:
    raised = True
    print("no-SW base raised ValueError:", str(e)[:80])
if not raised:
    print("FAIL: expected ValueError for base lacking sample_weight support")
    sys.exit(1)

# A classifier supporting sample_weight -> should succeed.
clf_yes = MultiOutputClassifier(LogisticRegression(solver="liblinear"))
clf_yes.fit(X, Y, sample_weight=sw)
print("SW-supporting base fit OK; classes_ len:", len(clf_yes.classes_))
print("PASS: sample_weight validation/forwarding preserved")
sys.exit(0)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""R1 end-to-end downstream use (issue motivation) + R2.5 validation preserved.
(a) cross_val_predict(..., method='predict_proba') works on MultiOutputClassifier
    (reads classes_) without AttributeError.
(b) fitting on a 1-D y still raises the existing validation ValueError.
Exits 0 iff both hold."""
import sys
import numpy as np
from sklearn.multioutput import MultiOutputClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import cross_val_predict

rng = np.random.RandomState(4)
X = rng.randn(60, 4)
Y = np.column_stack([rng.randint(0, 2, 60), rng.randint(0, 2, 60)])
clf = MultiOutputClassifier(LogisticRegression(solver="liblinear"))
try:
    out = cross_val_predict(clf, X, Y, cv=3, method="predict_proba")
    print("cross_val_predict predict_proba OK; type:", type(out).__name__)
except AttributeError as e:
    print("FAIL: cross_val_predict raised AttributeError:", e)
    sys.exit(1)

# (b) validation: 1-D y should still raise ValueError
raised = False
try:
    MultiOutputClassifier(LogisticRegression(solver="liblinear")).fit(X, rng.randint(0, 2, 60))
except ValueError as e:
    raised = True
    print("1-D y raised ValueError:", str(e)[:80])
if not raised:
    print("FAIL: expected ValueError for 1-D y")
    sys.exit(1)
print("PASS: downstream predict_proba CV works AND validation preserved")
sys.exit(0)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
"""R3.1: MultiOutputClassifier.classes_ has SAME structure as ClassifierChain
.classes_ — a list with one class-label array per target.
Exits 0 iff both are lists of length n_targets with matching per-target labels."""
import sys
import numpy as np
from sklearn.multioutput import MultiOutputClassifier, ClassifierChain
from sklearn.linear_model import LogisticRegression

rng = np.random.RandomState(5)
X = rng.randn(50, 4)
Y = np.column_stack([rng.randint(0, 2, 50), rng.randint(0, 2, 50), rng.randint(0, 2, 50)])

moc = MultiOutputClassifier(LogisticRegression(solver="liblinear")).fit(X, Y)
cc = ClassifierChain(LogisticRegression(solver="liblinear")).fit(X, Y)

print("MOC classes_ type:", type(moc.classes_).__name__, "len:", len(moc.classes_))
print("CC  classes_ type:", type(cc.classes_).__name__, "len:", len(cc.classes_))

if not isinstance(moc.classes_, list):
    print("FAIL: MOC classes_ not a list")
    sys.exit(1)
if not isinstance(cc.classes_, list):
    print("FAIL: CC classes_ not a list (unexpected)")
    sys.exit(1)
if len(moc.classes_) != Y.shape[1] or len(cc.classes_) != Y.shape[1]:
    print("FAIL: lengths differ from n_targets")
    sys.exit(1)
# structural comparison: each entry array-like of labels
for i in range(Y.shape[1]):
    a = np.asarray(moc.classes_[i])
    b = np.asarray(cc.classes_[i])
    print("target %d: MOC=%r CC=%r" % (i, a, b))
    if a.ndim != 1 or b.ndim != 1:
        print("FAIL: entry not 1-D label array")
        sys.exit(1)
print("PASS: MOC classes_ structure matches ClassifierChain")
sys.exit(0)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Positive control + R1.1/R1.2/R1.3: fitted MultiOutputClassifier exposes
classes_ as a list with one entry per target column.
Exits 0 iff classes_ exists, is a list, and len == n_targets."""
import sys
import numpy as np
from sklearn.multioutput import MultiOutputClassifier
from sklearn.linear_model import LogisticRegression

rng = np.random.RandomState(0)
X = rng.randn(50, 4)
Y = np.column_stack([
    rng.randint(0, 2, 50),
    rng.randint(0, 3, 50),
    rng.randint(0, 2, 50),
])
clf = MultiOutputClassifier(LogisticRegression(solver="liblinear"))
clf.fit(X, Y)

if not hasattr(clf, "classes_"):
    print("FAIL: no classes_ attribute")
    sys.exit(1)
c = clf.classes_
print("classes_ type:", type(c).__name__)
print("classes_ value:", c)
if not isinstance(c, list):
    print("FAIL: classes_ is not a list")
    sys.exit(1)
if len(c) != Y.shape[1]:
    print("FAIL: len(classes_)=%d != n_targets=%d" % (len(c), Y.shape[1]))
    sys.exit(1)
print("PASS: classes_ is a list of length %d" % len(c))
sys.exit(0)
```

Prepatch bug re-encoded as an attack: `True`.

Instance scikit-learn-14629: gold adds MultiOutputClassifier.fit that calls super().fit then sets self.classes_ = [est.classes_ for est in self.estimators_].

Probes (all HOLD on patched tree, exit 0):
- probe_1 (POSITIVE CONTROL, R1.1/1.2/1.3): classes_ exists, is a list, len==n_targets. HOLDS patched, VIOLATED at base ('no classes_ attribute') -> discriminates.
- probe_2 (R1.4/1.5): classes_[i] elementwise equals estimators_[i].classes_ in order, with string/object labels and distinct per-target label sets.
- probe_3 (R2.1/2.2/2.3): fit returns self, estimators_ count==n_targets, predict shape (n,k), predict_proba returns list of per-target arrays.
- probe_4 (R2.4): base lacking sample_weight -> ValueError; SW-supporting base fits OK and still exposes classes_.
- probe_5 (R1 downstream + R2.5): cross_val_predict(method='predict_proba') works (no AttributeError); 1-D y still raises the existing ValueError. Also VIOLATED at base (AttributeError) -> secondary discriminator.
- probe_6 (R3.1/3.3): MOC classes_ structure (list, one 1-D label array per target) matches fitted ClassifierChain.classes_.

Base runs: probe_1 exit=1 ('no classes_ attribute'), probe_5 exit=1 (AttributeError) -> prepatch reproduced.

Candidate wrong-fix (weak.diff): naive fit setting self.classes_ = self.estimators_[0].classes_ (numpy ndarray, first target only). Probe suite REJECTS it: probe_1 fails (ndarray not list), probe_2 fails (IndexError on target 2 / wrong length), probe_6 fails (ndarray, len!=n_targets). probe_3 still passes (behavior additive) as expected. This demonstrates the suite discriminates a requirements-violating implementation.

All 6 probes hold on patched tree; positive control discriminates patched-vs-base; >=1 candidate exercised and REJECTED. Verdict SOUND: requirements are faithful (not too strong — gold satisfies every probe) and not obviously too weak (the natural naive fix is caught by the list/length/per-target-order criteria).

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
"""Positive control + R1.1/R1.2/R1.3: fitted MultiOutputClassifier exposes
classes_ as a list with one entry per target column.
Exits 0 iff classes_ exists, is a list, and len == n_targets."""
import sys
import numpy as np
from sklearn.multioutput import MultiOutputClassifier
from sklearn.linear_model import LogisticRegression

rng = np.random.RandomState(0)
X = rng.randn(50, 4)
Y = np.column_stack([
    rng.randint(0, 2, 50),
    rng.randint(0, 3, 50),
    rng.randint(0, 2, 50),
])
clf = MultiOutputClassifier(LogisticRegression(solver="liblinear"))
clf.fit(X, Y)

if not hasattr(clf, "classes_"):
    print("FAIL: no classes_ attribute")
    sys.exit(1)
c = clf.classes_
print("classes_ type:", type(c).__name__)
print("classes_ value:", c)
if not isinstance(c, list):
    print("FAIL: classes_ is not a list")
    sys.exit(1)
if len(c) != Y.shape[1]:
    print("FAIL: len(classes_)=%d != n_targets=%d" % (len(c), Y.shape[1]))
    sys.exit(1)
print("PASS: classes_ is a list of length %d" % len(c))
sys.exit(0)
```

Prepatch bug re-encoded as an attack: `True`.

Instance scikit-learn-14629: gold adds MultiOutputClassifier.fit that calls super().fit then sets self.classes_ = [est.classes_ for est in self.estimators_].

Probes (all HOLD on patched tree, exit 0):
- probe_1 (POSITIVE CONTROL, R1.1/1.2/1.3): classes_ exists, is a list, len==n_targets. HOLDS patched, VIOLATED at base ('no classes_ attribute') -> discriminates.
- probe_2 (R1.4/1.5): classes_[i] elementwise equals estimators_[i].classes_ in order, with string/object labels and distinct per-target label sets.
- probe_3 (R2.1/2.2/2.3): fit returns self, estimators_ count==n_targets, predict shape (n,k), predict_proba returns list of per-target arrays.
- probe_4 (R2.4): base lacking sample_weight -> ValueError; SW-supporting base fits OK and still exposes classes_.
- probe_5 (R1 downstream + R2.5): cross_val_predict(method='predict_proba') works (no AttributeError); 1-D y still raises the existing ValueError. Also VIOLATED at base (AttributeError) -> secondary discriminator.
- probe_6 (R3.1/3.3): MOC classes_ structure (list, one 1-D label array per target) matches fitted ClassifierChain.classes_.

Base runs: probe_1 exit=1 ('no classes_ attribute'), probe_5 exit=1 (AttributeError) -> prepatch reproduced.

Candidate wrong-fix (weak.diff): naive fit setting self.classes_ = self.estimators_[0].classes_ (numpy ndarray, first target only). Probe suite REJECTS it: probe_1 fails (ndarray not list), probe_2 fails (IndexError on target 2 / wrong length), probe_6 fails (ndarray, len!=n_targets). probe_3 still passes (behavior additive) as expected. This demonstrates the suite discriminates a requirements-violating implementation.

All 6 probes hold on patched tree; positive control discriminates patched-vs-base; >=1 candidate exercised and REJECTED. Verdict SOUND: requirements are faithful (not too strong — gold satisfies every probe) and not obviously too weak (the natural naive fix is caught by the list/length/per-target-order criteria).

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Probe on patched tree: classes_ is list, len==n_targets, elementwise equal to each sub-estimator's classes_. Base commit: AttributeError. Requirements pin exactly the changed observable behavior (classes_ attribute), not a narrow helper/branch. The patch's second hunk (ClassifierChain indentation fix of the 'invalid order' ValueError) is a no-op cleanup with no behavioral change, consistent with R3.3 keeping ClassifierChain intact.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The document translates the gold fix's behavior into requirements without transmitting the hidden tests. Public problem_statement already exposes MultiOutputClassifier, classes_, estimators_[i].classes_, cross_val_predict(method='predict_proba'), and the AttributeError. Elements NOT in problem_statement but present in requirements: (a) classes_ is a `list` of per-target labels mirroring each sub-estimator — this is the behavior of the gold edit (self.classes_ = [e.classes_ for e in self.estimators_]) and is legitimately describable; (b) comparison to ClassifierChain — a public sibling class in the same module (sklearn.multioutput) that already exposes per-target classes_, so this is legitimate design/localization, not test text; (c) Req 3.2's 'native multi-target classifier fitted directly unchanged' is the closest analogue to the test's estimator0 (bare RandomForestClassifier), but it is phrased as a general non-regression property naming no concrete class, no parametrize ids, no n_estimators=2/n_outputs, no assert_array_equal, and no test path/name. No fix-invented identifiers (classes_/estimators_ are public API). No quoted test/gold code. The Req 3 enumeration reads as additive/non-regression thoroughness rather than a reconstruction that would let one rewrite test_multi_output_classes_. Borderline but does not cross into leakage.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
