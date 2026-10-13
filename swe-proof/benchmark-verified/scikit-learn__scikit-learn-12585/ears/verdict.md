# P2 adversarial audit — scikit-learn__scikit-learn-12585

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
# Positive control: Req 1.1, 1.3, 1.4
# clone on an estimator whose parameter is a CLASS must complete without raising,
# and the cloned parameter must be the identical class object.
import sys
from sklearn.base import BaseEstimator, clone
from sklearn.preprocessing import StandardScaler

class Wrapper(BaseEstimator):
    def __init__(self, est_cls=StandardScaler):
        self.est_cls = est_cls

w = Wrapper(est_cls=StandardScaler)
try:
    c = clone(w)
except Exception as e:
    print("FAIL: clone raised", type(e).__name__, e)
    sys.exit(1)

print("cloned ok; est_cls is StandardScaler:", c.est_cls is StandardScaler)
if c.est_cls is not StandardScaler:
    print("FAIL: cloned param not identical class")
    sys.exit(1)
# also direct non-safe recursion path (Req 1.3)
r = clone(StandardScaler, safe=False)
print("clone(StandardScaler, safe=False) is StandardScaler:", r is StandardScaler)
if r is not StandardScaler:
    sys.exit(1)
print("PASS")
sys.exit(0)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
# Req 2.1 / 2.2: a type value with a get_params attribute (an estimator CLASS)
# must be treated as NOT a cloneable estimator. clone(cls, safe=False) returns
# the identical class object rather than introspecting parameters, and must NOT
# raise TypeError about missing 'self'.
import sys
from sklearn.base import clone
from sklearn.preprocessing import StandardScaler

# StandardScaler is a type that DOES define get_params on the class.
print("StandardScaler has get_params attr:", hasattr(StandardScaler, "get_params"))
try:
    r = clone(StandardScaler, safe=False)
except Exception as e:
    print("FAIL: raised", type(e).__name__, e)
    sys.exit(1)
print("returned identical class:", r is StandardScaler)
if r is not StandardScaler:
    sys.exit(1)

# Also a plain non-estimator class (no get_params): still returns identical class.
class Plain:
    pass
try:
    r2 = clone(Plain, safe=False)
except Exception as e:
    print("FAIL: raised on Plain", type(e).__name__, e)
    sys.exit(1)
print("Plain class returned identically:", r2 is Plain)
if r2 is not Plain:
    sys.exit(1)
print("PASS")
sys.exit(0)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
# Req 2.3: clone(type, safe=True) at top level must raise TypeError reporting
# that the object does not appear to be a scikit-learn estimator (same message
# as other non-estimator values under safe=True).
import sys
from sklearn.base import clone
from sklearn.preprocessing import StandardScaler

try:
    clone(StandardScaler, safe=True)
    print("FAIL: no exception raised")
    sys.exit(1)
except TypeError as e:
    msg = str(e)
    print("TypeError:", msg)
    if "scikit-learn estimator" not in msg:
        print("FAIL: message not the estimator message")
        sys.exit(1)
    if "missing 1 required positional argument" in msg or "self" in msg:
        print("FAIL: raised the get_params(self) TypeError instead")
        sys.exit(1)
except Exception as e:
    print("FAIL: wrong exception type", type(e).__name__, e)
    sys.exit(1)
print("PASS")
sys.exit(0)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
# Req 3.1 & 3.6: clone on an estimator INSTANCE still introspects & rebuilds:
# new object same class, equal deep=False params; estimator-valued params cloned
# to NEW non-identical instances; non-estimator leaves preserved.
import sys
import numpy as np
from sklearn.base import clone
from sklearn.feature_selection import SelectKBest, f_classif
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

sel = SelectKBest(f_classif, k=3)
c = clone(sel)
print("same class:", type(c) is type(sel), "not identical:", c is not sel)
if type(c) is not type(sel) or c is sel:
    sys.exit(1)
if c.k != 3:
    print("FAIL: param k not preserved")
    sys.exit(1)

# nested estimator param gets cloned to a new instance
scaler = StandardScaler()
pipe = Pipeline([("s", scaler)])
cp = clone(pipe)
inner = cp.get_params(deep=False)["steps"][0][1]
print("inner scaler cloned to new instance:", inner is not scaler, type(inner).__name__)
if inner is scaler:
    print("FAIL: nested estimator not re-cloned")
    sys.exit(1)
if type(inner) is not StandardScaler:
    sys.exit(1)
print("PASS")
sys.exit(0)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
# Req 3.2 & 3.3: containers of estimators cloned element-wise; numpy arrays,
# NaN, empty arrays preserved with equal values.
import sys
import numpy as np
from sklearn.base import clone
from sklearn.preprocessing import StandardScaler

# container of estimators
ests = [StandardScaler(), StandardScaler()]
cloned = clone(ests)
print("list of same length:", len(cloned) == 2, "elements new:", all(a is not b for a, b in zip(cloned, ests)))
if not (isinstance(cloned, list) and len(cloned) == 2):
    sys.exit(1)
if any(a is b for a, b in zip(cloned, ests)):
    print("FAIL: element not cloned")
    sys.exit(1)
if any(type(a) is not StandardScaler for a in cloned):
    sys.exit(1)

# tuple kind preserved
tup = clone((StandardScaler(),))
print("tuple kind preserved:", isinstance(tup, tuple))
if not isinstance(tup, tuple):
    sys.exit(1)

# numpy array leaf
arr = np.array([1.0, 2.0, 3.0])
ca = clone(arr, safe=False)
print("array equal:", np.array_equal(ca, arr))
if not np.array_equal(ca, arr):
    sys.exit(1)

# NaN
nan = clone(float("nan"), safe=False)
print("nan preserved:", nan != nan)
if not (nan != nan):
    sys.exit(1)

# empty array
empty = clone(np.array([]), safe=False)
print("empty preserved:", empty.shape == (0,))
if empty.shape != (0,):
    sys.exit(1)
print("PASS")
sys.exit(0)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
# Req 3.4: buggy estimator whose constructor modifies a param -> RuntimeError.
# Req 3.5: safe=True on a plain non-estimator (no get_params) -> TypeError;
#          safe=False -> deep copy.
import sys
from sklearn.base import BaseEstimator, clone

class Buggy(BaseEstimator):
    def __init__(self, a=1):
        self.a = a + 1  # modifies param
    def get_params(self, deep=True):
        return {"a": self.a}

try:
    clone(Buggy())
    print("FAIL: no RuntimeError")
    sys.exit(1)
except RuntimeError as e:
    print("RuntimeError:", str(e)[:80])
except Exception as e:
    print("FAIL: wrong exc", type(e).__name__, e)
    sys.exit(1)

# plain non-estimator, safe=True -> TypeError
try:
    clone(object(), safe=True)
    print("FAIL: no TypeError for plain object")
    sys.exit(1)
except TypeError as e:
    print("TypeError plain:", "scikit-learn estimator" in str(e))
    if "scikit-learn estimator" not in str(e):
        sys.exit(1)

# plain non-estimator, safe=False -> deep copy of equal value
val = [1, 2, [3, 4]]
cp = clone(val, safe=False)
print("deepcopy equal:", cp == val, "not identical inner:", cp[2] is not val[2])
if cp != val or cp[2] is val[2]:
    sys.exit(1)
print("PASS")
sys.exit(0)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
# Positive control: Req 1.1, 1.3, 1.4
# clone on an estimator whose parameter is a CLASS must complete without raising,
# and the cloned parameter must be the identical class object.
import sys
from sklearn.base import BaseEstimator, clone
from sklearn.preprocessing import StandardScaler

class Wrapper(BaseEstimator):
    def __init__(self, est_cls=StandardScaler):
        self.est_cls = est_cls

w = Wrapper(est_cls=StandardScaler)
try:
    c = clone(w)
except Exception as e:
    print("FAIL: clone raised", type(e).__name__, e)
    sys.exit(1)

print("cloned ok; est_cls is StandardScaler:", c.est_cls is StandardScaler)
if c.est_cls is not StandardScaler:
    print("FAIL: cloned param not identical class")
    sys.exit(1)
# also direct non-safe recursion path (Req 1.3)
r = clone(StandardScaler, safe=False)
print("clone(StandardScaler, safe=False) is StandardScaler:", r is StandardScaler)
if r is not StandardScaler:
    sys.exit(1)
print("PASS")
sys.exit(0)
```

Prepatch bug re-encoded as an attack: `True`.

Bundle scikit-learn-12585: clone() must tolerate estimator CLASSES as parameter values. Gold fix: `elif not hasattr(estimator,'get_params') or isinstance(estimator, type):`.

Probes (all HOLD on gold-patched tree):
- probe_1 (Req 1.1/1.3/1.4, POSITIVE CONTROL): clone(Wrapper(est_cls=StandardScaler)) completes without raising and cloned param is identical class; clone(StandardScaler, safe=False) is StandardScaler. HOLDS patched, FAILS at base (base raises TypeError: get_params() missing 1 positional arg 'self'). prepatch_reproduced=True.
- probe_2 (Req 2.1/2.2): a type WITH get_params (StandardScaler) treated as non-estimator; safe=False returns identical class; plain class too. HOLDS patched, FAILS base.
- probe_3 (Req 2.3): clone(StandardScaler, safe=True) raises TypeError with 'scikit-learn estimator' message (not the get_params self TypeError). HOLDS patched, FAILS base.
- probe_4 (Req 3.1/3.6): instance still introspected/rebuilt; new obj same class, params preserved; nested estimator cloned to NEW instance. HOLDS patched.
- probe_5 (Req 3.2/3.3): containers cloned element-wise (list/tuple kind preserved, new elements); numpy array/NaN/empty preserved. HOLDS patched.
- probe_6 (Req 3.4/3.5): buggy constructor -> RuntimeError; plain object safe=True -> TypeError; safe=False -> deep copy. HOLDS patched.

Candidate wrong-fix (weak.diff): wrap get_params(deep=False) in try/except TypeError -> return copy.deepcopy(estimator). This is the lazy fix a weak reading permits. Result under --patch: probes 1,2,4,5,6 HOLD but probe_3 REJECTS it — under safe=True on StandardScaler the candidate silently returns the class via deepcopy instead of raising the estimator TypeError, violating Req 2.3. This demonstrates the suite discriminates wrong implementations. Verdict SOUND: >=5 probes hold on gold, positive control discriminates (holds patched / fails base), and a probe-conforming-except-2.3 candidate is rejected.

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
# Positive control: Req 1.1, 1.3, 1.4
# clone on an estimator whose parameter is a CLASS must complete without raising,
# and the cloned parameter must be the identical class object.
import sys
from sklearn.base import BaseEstimator, clone
from sklearn.preprocessing import StandardScaler

class Wrapper(BaseEstimator):
    def __init__(self, est_cls=StandardScaler):
        self.est_cls = est_cls

w = Wrapper(est_cls=StandardScaler)
try:
    c = clone(w)
except Exception as e:
    print("FAIL: clone raised", type(e).__name__, e)
    sys.exit(1)

print("cloned ok; est_cls is StandardScaler:", c.est_cls is StandardScaler)
if c.est_cls is not StandardScaler:
    print("FAIL: cloned param not identical class")
    sys.exit(1)
# also direct non-safe recursion path (Req 1.3)
r = clone(StandardScaler, safe=False)
print("clone(StandardScaler, safe=False) is StandardScaler:", r is StandardScaler)
if r is not StandardScaler:
    sys.exit(1)
print("PASS")
sys.exit(0)
```

Prepatch bug re-encoded as an attack: `True`.

Bundle scikit-learn-12585: clone() must tolerate estimator CLASSES as parameter values. Gold fix: `elif not hasattr(estimator,'get_params') or isinstance(estimator, type):`.

Probes (all HOLD on gold-patched tree):
- probe_1 (Req 1.1/1.3/1.4, POSITIVE CONTROL): clone(Wrapper(est_cls=StandardScaler)) completes without raising and cloned param is identical class; clone(StandardScaler, safe=False) is StandardScaler. HOLDS patched, FAILS at base (base raises TypeError: get_params() missing 1 positional arg 'self'). prepatch_reproduced=True.
- probe_2 (Req 2.1/2.2): a type WITH get_params (StandardScaler) treated as non-estimator; safe=False returns identical class; plain class too. HOLDS patched, FAILS base.
- probe_3 (Req 2.3): clone(StandardScaler, safe=True) raises TypeError with 'scikit-learn estimator' message (not the get_params self TypeError). HOLDS patched, FAILS base.
- probe_4 (Req 3.1/3.6): instance still introspected/rebuilt; new obj same class, params preserved; nested estimator cloned to NEW instance. HOLDS patched.
- probe_5 (Req 3.2/3.3): containers cloned element-wise (list/tuple kind preserved, new elements); numpy array/NaN/empty preserved. HOLDS patched.
- probe_6 (Req 3.4/3.5): buggy constructor -> RuntimeError; plain object safe=True -> TypeError; safe=False -> deep copy. HOLDS patched.

Candidate wrong-fix (weak.diff): wrap get_params(deep=False) in try/except TypeError -> return copy.deepcopy(estimator). This is the lazy fix a weak reading permits. Result under --patch: probes 1,2,4,5,6 HOLD but probe_3 REJECTS it — under safe=True on StandardScaler the candidate silently returns the class via deepcopy instead of raising the estimator TypeError, violating Req 2.3. This demonstrates the suite discriminates wrong implementations. Verdict SOUND: >=5 probes hold on gold, positive control discriminates (holds patched / fails base), and a probe-conforming-except-2.3 candidate is rejected.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** The one-line gold patch changes the routing condition to `not hasattr(estimator,'get_params') or isinstance(estimator, type)`, moving any type value onto the non-estimator path. The requirements pin exactly this changed observable behavior at the correct boundary: R2/R6 state the routing is 'value is a type -> non-estimator path, regardless of get_params presence', which matches `isinstance(estimator, type)` including classes that DO define get_params (the exact issue-repro case). R2.3's error message text ('does not appear to be a scikit-learn estimator') is looser than the actual message ('does not seem to be a scikit-learn estimator') but is described as behavior 'exactly as it already does for other non-estimator values' — the raise itself is what's mandated and it holds; the paraphrase is not a false behavioral claim. R3 regression clauses (containers, arrays/NaN, RuntimeError on constructor-mutated params, safe=True/False on plain non-type non-estimator) all correspond to unchanged pre-existing clone behavior and the PASS_TO_PASS suite. No requirement mandates behavior the patched code lacks, forbids behavior it has, or invents behavior. Boundary is correct (type-routing), not a narrow slice.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The public problem_statement is unusually complete: it already discloses the reproduction (clone(StandardScaler(with_mean=StandardScaler))), the affected file/function (clone in sklearn/base.py), the exact TypeError, and the verbatim gold fix line (`elif not hasattr(estimator, 'get_params') or isinstance(estimator, type):`). Thus the entire core of requirements.md is public. No hidden-test artifacts appear: the test name (test_clone_estimator_types), test file path (sklearn/tests/test_base.py), the MyEstimator helper, and the empty=MyEstimator parametrization are all absent. The 'same class object by identity' requirement (Req 1.3/1.4) is a logical consequence of routing classes to deepcopy (deepcopy of a class returns the same object), not a copy of the assert clf.empty is clf2.empty test line. Req 3's regression enumeration (list/tuple/set/frozenset containers, numpy array, sparse matrix, NaN, empty array, RuntimeError on buggy constructor) describes clone's documented public behavior and the pre-existing container branch visible in sklearn/base.py source (not part of the hidden gold edit); it omits the pandas and pickle-version PASS_TO_PASS cases, showing it describes behavior rather than reconstructing the hidden test list. No fix-invented identifiers (isinstance/type are stdlib and already in the public patch).

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
