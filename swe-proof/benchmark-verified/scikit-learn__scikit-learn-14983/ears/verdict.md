# P2 adversarial audit — scikit-learn__scikit-learn-14983

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 6 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 6 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 6 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_3.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (6):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
import sys, re
from sklearn.model_selection import RepeatedKFold

r = repr(RepeatedKFold())
print("repr:", r)
# Req1.1: begins with class name + "(", no default object form
if "object at 0x" in r:
    print("FAIL: default object repr")
    sys.exit(1)
if not r.startswith("RepeatedKFold("):
    print("FAIL: does not start with class name + '('")
    sys.exit(1)
if not r.rstrip().endswith(")"):
    print("FAIL: not enclosed in parentheses")
    sys.exit(1)
print("PASS")
sys.exit(0)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
import sys
from sklearn.model_selection import RepeatedStratifiedKFold

r = repr(RepeatedStratifiedKFold())
print("repr:", r)
# Req1.2
if "object at 0x" in r:
    print("FAIL: default object repr")
    sys.exit(1)
if not r.startswith("RepeatedStratifiedKFold("):
    print("FAIL: does not start with class name + '('")
    sys.exit(1)
if not r.rstrip().endswith(")"):
    print("FAIL: not enclosed in parentheses")
    sys.exit(1)
print("PASS")
sys.exit(0)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
import sys
from sklearn.model_selection import RepeatedKFold

# Req1.3,1.4,1.5,1.6: exact form, alphabetical order, configured values
r = repr(RepeatedKFold(n_splits=5, n_repeats=10, random_state=None))
print("repr:", r)
expected = "RepeatedKFold(n_repeats=10, n_splits=5, random_state=None)"
if r != expected:
    print("FAIL: expected", repr(expected))
    sys.exit(1)
print("PASS")
sys.exit(0)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
import sys
from sklearn.model_selection import RepeatedKFold, RepeatedStratifiedKFold

# Req2.2 / Req1.7: n_splits stored in cvargs must be reported (not None),
# and non-default random_state must show through.
rk = RepeatedKFold(n_splits=3, n_repeats=7, random_state=42)
r = repr(rk)
print("repr RK:", r)
# verify it really stores n_splits in cvargs, not direct attr
print("cvargs:", getattr(rk, "cvargs", None), "direct n_splits attr:", getattr(rk, "n_splits", "MISSING"))
exp = "RepeatedKFold(n_repeats=7, n_splits=3, random_state=42)"
if r != exp:
    print("FAIL: expected", repr(exp))
    sys.exit(1)

rsk = RepeatedStratifiedKFold(n_splits=2, n_repeats=4, random_state=0)
r2 = repr(rsk)
print("repr RSK:", r2)
exp2 = "RepeatedStratifiedKFold(n_repeats=4, n_splits=2, random_state=0)"
if r2 != exp2:
    print("FAIL: expected", repr(exp2))
    sys.exit(1)
# ensure not None substitution
if "n_splits=None" in r or "n_splits=None" in r2:
    print("FAIL: n_splits rendered as None")
    sys.exit(1)
print("PASS")
sys.exit(0)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
import sys
from sklearn.model_selection import KFold, StratifiedKFold, GroupKFold

# Req3.3: an object storing all constructor params as direct attributes
# renders exactly as before (cvargs fallback must not perturb it).
r = repr(KFold(n_splits=4, shuffle=True, random_state=1))
print("KFold repr:", r)
exp = "KFold(n_splits=4, random_state=1, shuffle=True)"
if r != exp:
    print("FAIL: KFold repr changed, expected", repr(exp))
    sys.exit(1)

# These have no cvargs attribute; must still render.
for obj, pref in [(StratifiedKFold(n_splits=3), "StratifiedKFold("),
                  (GroupKFold(n_splits=2), "GroupKFold(")]:
    rr = repr(obj)
    print(rr)
    if "object at 0x" in rr or not rr.startswith(pref):
        print("FAIL: regression on", pref)
        sys.exit(1)
print("PASS")
sys.exit(0)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
import sys
from sklearn.model_selection import RepeatedKFold, RepeatedStratifiedKFold
import numpy as np

# Req3.4: constructors/public params unchanged; splitting & split-count unchanged.
X = np.arange(20).reshape(10, 2)
y = np.array([0,1]*5)

rk = RepeatedKFold(n_splits=5, n_repeats=3, random_state=123)
n = rk.get_n_splits()
print("RK n_splits:", n)
if n != 15:
    print("FAIL: expected 15 splits")
    sys.exit(1)
folds = list(rk.split(X))
if len(folds) != 15:
    print("FAIL: split() yielded", len(folds))
    sys.exit(1)
# each split partitions indices
for tr, te in folds:
    if set(tr.tolist()) & set(te.tolist()):
        print("FAIL: train/test overlap")
        sys.exit(1)
    if sorted(tr.tolist()+te.tolist()) != list(range(10)):
        print("FAIL: not a partition")
        sys.exit(1)

rsk = RepeatedStratifiedKFold(n_splits=2, n_repeats=4, random_state=1)
if rsk.get_n_splits() != 8:
    print("FAIL: RSK n_splits")
    sys.exit(1)
if len(list(rsk.split(X, y))) != 8:
    print("FAIL: RSK split count")
    sys.exit(1)
print("PASS")
sys.exit(0)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_3.py`

```python
import sys
from sklearn.model_selection import RepeatedKFold

# Req1.3,1.4,1.5,1.6: exact form, alphabetical order, configured values
r = repr(RepeatedKFold(n_splits=5, n_repeats=10, random_state=None))
print("repr:", r)
expected = "RepeatedKFold(n_repeats=10, n_splits=5, random_state=None)"
if r != expected:
    print("FAIL: expected", repr(expected))
    sys.exit(1)
print("PASS")
sys.exit(0)
```

Prepatch bug re-encoded as an attack: `True`.

6 probes cover Req1-3. probe_1/2: RepeatedKFold/RepeatedStratifiedKFold repr begins with class name+'(' and is not the default object form (Req1.1,1.2). probe_3: exact form RepeatedKFold(n_repeats=10, n_splits=5, random_state=None) — alphabetical order, configured values, random_state=None default (Req1.3-1.6). probe_4: n_splits stored in cvargs must be reported (verified direct n_splits attr is MISSING, cvargs={'n_splits':3}); non-default random_state shown; no None substitution (Req2.1,2.2,1.7). probe_5: KFold/StratifiedKFold/GroupKFold reprs unchanged incl. exact KFold(n_splits=4, random_state=1, shuffle=True) — cvargs fallback does not perturb direct-attr objects (Req3.1,3.3). probe_6: RepeatedKFold/RepeatedStratifiedKFold split counts (15, 8) and partition semantics unchanged (Req3.4).

Results: ALL 6 HOLD on gold-patched tree. On BASE: probes 1-4 VIOLATED (default object repr / n_splits=None), probes 5-6 hold (regression criteria) => positive control probe_3 discriminates (fails at base, holds patched). prepatch_reproduced=true.

Candidate weak_naive: adds _RepeatedSplits.__repr__=_build_repr(self) WITHOUT the cvargs fallback in _build_repr (a partial/lazy fix a weak reading of Req1.1/1.2 alone permits). Under it probes 3 & 4 REJECT (renders n_splits=None), proving the suite discriminates the wrong implementation. This confirms Req2's cvargs-resolution criterion is load-bearing and the requirements are not too weak.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 6 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 6 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_3.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (6):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

_The 6 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts, and on this backend both roles put it through the same derivation: every block below is a requirement probe run on the gold-patched tree, and the `machine verdict:` line each role publishes above reports BOTH that its probes hold there and how many candidate patches the probe suite rejected — so the two roles re-ran ONE probe suite and each recorded its own outcome for every probe in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `probe_1.py` → holds on the patched tree (good)

Attack 2 — `probe_2.py` → holds on the patched tree (good)

Attack 3 — `probe_3.py` → holds on the patched tree (good)

Attack 4 — `probe_4.py` → holds on the patched tree (good)

Attack 5 — `probe_5.py` → holds on the patched tree (good)

Attack 6 — `probe_6.py` → holds on the patched tree (good)

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_3.py`

```python
import sys
from sklearn.model_selection import RepeatedKFold

# Req1.3,1.4,1.5,1.6: exact form, alphabetical order, configured values
r = repr(RepeatedKFold(n_splits=5, n_repeats=10, random_state=None))
print("repr:", r)
expected = "RepeatedKFold(n_repeats=10, n_splits=5, random_state=None)"
if r != expected:
    print("FAIL: expected", repr(expected))
    sys.exit(1)
print("PASS")
sys.exit(0)
```

Prepatch bug re-encoded as an attack: `True`.

6 probes cover Req1-3. probe_1/2: RepeatedKFold/RepeatedStratifiedKFold repr begins with class name+'(' and is not the default object form (Req1.1,1.2). probe_3: exact form RepeatedKFold(n_repeats=10, n_splits=5, random_state=None) — alphabetical order, configured values, random_state=None default (Req1.3-1.6). probe_4: n_splits stored in cvargs must be reported (verified direct n_splits attr is MISSING, cvargs={'n_splits':3}); non-default random_state shown; no None substitution (Req2.1,2.2,1.7). probe_5: KFold/StratifiedKFold/GroupKFold reprs unchanged incl. exact KFold(n_splits=4, random_state=1, shuffle=True) — cvargs fallback does not perturb direct-attr objects (Req3.1,3.3). probe_6: RepeatedKFold/RepeatedStratifiedKFold split counts (15, 8) and partition semantics unchanged (Req3.4).

Results: ALL 6 HOLD on gold-patched tree. On BASE: probes 1-4 VIOLATED (default object repr / n_splits=None), probes 5-6 hold (regression criteria) => positive control probe_3 discriminates (fails at base, holds patched). prepatch_reproduced=true.

Candidate weak_naive: adds _RepeatedSplits.__repr__=_build_repr(self) WITHOUT the cvargs fallback in _build_repr (a partial/lazy fix a weak reading of Req1.1/1.2 alone permits). Under it probes 3 & 4 REJECT (renders n_splits=None), proving the suite discriminates the wrong implementation. This confirms Req2's cvargs-resolution criterion is load-bearing and the requirements are not too weak.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Gold patch does two things, both pinned by requirements: (1) adds _RepeatedSplits.__repr__ returning _build_repr(self) -> R1.1/R1.2/R1.3 (probed: both RepeatedKFold and RepeatedStratifiedKFold get parameter-listing repr, no 'object at 0x'); (2) adds cvargs fallback in _build_repr: 'if value is None and hasattr(self,"cvargs"): value = self.cvargs.get(key, None)' -> R2.1/R2.2/R2.3/R3.3/R7 (probed: n_splits stored in cvargs renders as 5, not None; guard is exactly value is None). R3.1 (sorted constructor params excluding self/VAR_KEYWORD) and R3.2 (skip DeprecationWarning params) match unchanged _build_repr source. R3.4 (constructors/splitting unchanged) holds — patch only touches __repr__ and one guarded line. Probe of custom args RepeatedKFold(n_splits=3,n_repeats=7,random_state=42) -> 'RepeatedKFold(n_repeats=7, n_splits=3, random_state=42)' confirms R5/R6. Modeling boundary is correct: requirements pin the changed observable repr behavior plus the exact cvargs mechanism, not a narrow slice.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Requirements localize the change to real pre-existing module identifiers (_RepeatedSplits, _build_repr, cvargs) — legitimate, not fix-invented. Both class names, all three param names, and the exact repr format `RepeatedKFold(n_splits=5, n_repeats=10, random_state=None)` are already disclosed in the public problem_statement. No test names/paths/ids, no quoted test or gold code, no test-value enumeration (the hidden test's n_splits=2/n_repeats=6 do not appear). Only borderline item: Req 1.4 asserts alphabetical parameter order (n_repeats, n_splits, random_state), which contradicts the problem_statement's shown order and is thus confirmable only against the gold repr string — but this is a genuine behavioral property of _build_repr's output, a legitimate behavioral translation rather than transmission of the test itself. Naming both parametrized classes mirrors public info, not the parametrization. NO-LEAKAGE.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
