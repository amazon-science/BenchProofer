# P2 adversarial audit — scikit-learn__scikit-learn-14053

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
import numpy as np
from sklearn.tree import DecisionTreeClassifier
from sklearn.tree.export import export_text
# single-feature dataset
X = np.array([[0.0],[1.0],[2.0],[3.0]])
y = np.array([0,0,1,1])
clf = DecisionTreeClassifier(random_state=0).fit(X, y)
try:
    rep = export_text(clf, feature_names=['f0'])
except IndexError as e:
    print("FAIL: IndexError raised:", e)
    raise SystemExit(1)
print("REPORT:\n", rep)
assert isinstance(rep, str) and len(rep) > 0
assert 'f0' in rep, "feature name f0 not present"
print("OK single-feature export succeeded")
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
import numpy as np
from sklearn.datasets import load_iris
from sklearn.tree import DecisionTreeClassifier
from sklearn.tree.export import export_text
X, y = load_iris(return_X_y=True)
clf = DecisionTreeClassifier(max_depth=3, random_state=0).fit(X, y)
names = ['sepal_len','sepal_wid','petal_len','petal_wid']
rep = export_text(clf, feature_names=names)
print(rep)
# at least one supplied name must appear on split lines
assert any(n in rep for n in names), "no supplied feature name in output"
# and comparison operators present for splits
assert '<=' in rep and '>' in rep, "split comparison lines missing"
print("OK split nodes labeled with feature_names")
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
import numpy as np
from sklearn.datasets import load_iris
from sklearn.tree import DecisionTreeClassifier
from sklearn.tree.export import export_text
X, y = load_iris(return_X_y=True)
clf = DecisionTreeClassifier(max_depth=3, random_state=0).fit(X, y)
rep = export_text(clf)
print(rep)
import re
assert re.search(r'feature_\d+', rep), "generic feature_{index} names absent"
# leaf lines must NOT contain feature_-2 (sentinel indexed)
assert 'feature_-2' not in rep, "sentinel leaked into generic labels"
print("OK generic feature_{index} labels present, no sentinel")
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
import numpy as np
from sklearn.datasets import load_iris
from sklearn.tree import DecisionTreeClassifier
from sklearn.tree.export import export_text
X, y = load_iris(return_X_y=True)
clf = DecisionTreeClassifier(max_depth=3, random_state=0).fit(X, y)
try:
    export_text(clf, feature_names=['only_one'])  # needs 4
    print("FAIL: no exception")
    raise SystemExit(1)
except IndexError as e:
    print("FAIL: IndexError instead of ValueError:", e)
    raise SystemExit(1)
except ValueError as e:
    msg = str(e)
    print("ValueError:", msg)
    # must report required and received counts
    assert '4' in msg and '1' in msg, "counts not reported: "+msg
print("OK ValueError with counts, before name resolution")
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
import numpy as np
from sklearn.datasets import load_iris
from sklearn.tree import DecisionTreeClassifier
from sklearn.tree.export import export_text
X, y = load_iris(return_X_y=True)
clf = DecisionTreeClassifier(max_depth=3, random_state=0).fit(X, y)
names = ['a','b','c','d']
def expect_ve(**kw):
    try:
        export_text(clf, feature_names=names, **kw)
    except ValueError as e:
        print("OK ValueError:", kw, "->", e)
        return
    except Exception as e:
        print("FAIL wrong exception:", kw, type(e).__name__, e); raise SystemExit(1)
    print("FAIL no exception:", kw); raise SystemExit(1)
expect_ve(max_depth=-1)
expect_ve(decimals=-1)
expect_ve(spacing=0)
expect_ve(spacing=-2)
print("OK all validation errors preserved")
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
import numpy as np
from sklearn.tree import DecisionTreeRegressor
from sklearn.tree.export import export_text
X = np.array([[0.0],[1.0],[2.0],[3.0]])
y = np.array([0.0,0.0,1.0,1.0])
reg = DecisionTreeRegressor(random_state=0).fit(X, y)
rep = export_text(reg, feature_names=['x'])
print(rep)
# leaves must render a value line
assert 'value:' in rep, "leaf value line missing"
# no sentinel-based garbage: feature name 'x' should appear only on split lines, never a None literal misrendered
lines = rep.splitlines()
for ln in lines:
    if 'value:' in ln:
        assert 'x ' not in ln and '<=' not in ln and '> ' not in ln, "leaf line has feature label: "+ln
print("OK leaves emit value, no feature label")
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
import numpy as np
from sklearn.tree import DecisionTreeClassifier
from sklearn.tree.export import export_text
# single-feature dataset
X = np.array([[0.0],[1.0],[2.0],[3.0]])
y = np.array([0,0,1,1])
clf = DecisionTreeClassifier(random_state=0).fit(X, y)
try:
    rep = export_text(clf, feature_names=['f0'])
except IndexError as e:
    print("FAIL: IndexError raised:", e)
    raise SystemExit(1)
print("REPORT:\n", rep)
assert isinstance(rep, str) and len(rep) > 0
assert 'f0' in rep, "feature name f0 not present"
print("OK single-feature export succeeded")
```

Prepatch bug re-encoded as an attack: `True`.

Instance scikit-learn-14053: export_text IndexError when sentinel TREE_UNDEFINED (-2) indexes feature_names. Gold patch resolves leaf nodes to None instead of indexing.

Probe suite (all HOLD on gold-patched tree):
- probe_1 (POSITIVE CONTROL, R1.1/R1.3): single-feature tree + one-element feature_names ['f0'] must export without IndexError AND include 'f0'. Patched: HOLDS (exit0). Base: VIOLATED (IndexError: list index out of range) -> discriminates.
- probe_2 (R1.4/R2.1): iris multi-feature, supplied names appear on split lines, '<=' and '>' comparison lines present. HOLDS.
- probe_3 (R2.3): no feature_names -> generic feature_{index} present, no 'feature_-2' sentinel leak. HOLDS.
- probe_4 (R3.1): wrong-length feature_names -> ValueError reporting required(4)/received(1) counts, NOT IndexError. HOLDS.
- probe_5 (R3.2/3.3/3.4): max_depth<0, decimals<0, spacing<=0 each raise ValueError. HOLDS.
- probe_6 (R1.2/R2.2): single-feature regressor, leaves emit 'value:' line and carry no feature label. HOLDS.

Candidate wrong-fix 'generic_fallback_on_indexerror' (weak.diff): wraps the resolution in try/except IndexError and falls back to generic feature_{i} names. It avoids the crash but drops the SUPPLIED feature name for single-feature trees. Probe results under this patch: probe_1 REJECTED (exit1 — output shows 'feature_0' fallback instead of required 'f0', violating R1.4/R2.1 total resolution with the supplied name); probes 2-6 HOLD. This demonstrates the suite discriminates a plausible partial fix that a weak reading of the requirements would permit.

>=5 distinct probes all hold on the patched tree; positive control fails at base and holds patched; >=1 candidate exercised and rejected. Verdict SOUND.

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
import numpy as np
from sklearn.tree import DecisionTreeClassifier
from sklearn.tree.export import export_text
# single-feature dataset
X = np.array([[0.0],[1.0],[2.0],[3.0]])
y = np.array([0,0,1,1])
clf = DecisionTreeClassifier(random_state=0).fit(X, y)
try:
    rep = export_text(clf, feature_names=['f0'])
except IndexError as e:
    print("FAIL: IndexError raised:", e)
    raise SystemExit(1)
print("REPORT:\n", rep)
assert isinstance(rep, str) and len(rep) > 0
assert 'f0' in rep, "feature name f0 not present"
print("OK single-feature export succeeded")
```

Prepatch bug re-encoded as an attack: `True`.

Instance scikit-learn-14053: export_text IndexError when sentinel TREE_UNDEFINED (-2) indexes feature_names. Gold patch resolves leaf nodes to None instead of indexing.

Probe suite (all HOLD on gold-patched tree):
- probe_1 (POSITIVE CONTROL, R1.1/R1.3): single-feature tree + one-element feature_names ['f0'] must export without IndexError AND include 'f0'. Patched: HOLDS (exit0). Base: VIOLATED (IndexError: list index out of range) -> discriminates.
- probe_2 (R1.4/R2.1): iris multi-feature, supplied names appear on split lines, '<=' and '>' comparison lines present. HOLDS.
- probe_3 (R2.3): no feature_names -> generic feature_{index} present, no 'feature_-2' sentinel leak. HOLDS.
- probe_4 (R3.1): wrong-length feature_names -> ValueError reporting required(4)/received(1) counts, NOT IndexError. HOLDS.
- probe_5 (R3.2/3.3/3.4): max_depth<0, decimals<0, spacing<=0 each raise ValueError. HOLDS.
- probe_6 (R1.2/R2.2): single-feature regressor, leaves emit 'value:' line and carry no feature label. HOLDS.

Candidate wrong-fix 'generic_fallback_on_indexerror' (weak.diff): wraps the resolution in try/except IndexError and falls back to generic feature_{i} names. It avoids the crash but drops the SUPPLIED feature name for single-feature trees. Probe results under this patch: probe_1 REJECTED (exit1 — output shows 'feature_0' fallback instead of required 'f0', violating R1.4/R2.1 total resolution with the supplied name); probes 2-6 HOLD. This demonstrates the suite discriminates a plausible partial fix that a weak reading of the requirements would permit.

>=5 distinct probes all hold on the patched tree; positive control fails at base and holds patched; >=1 candidate exercised and rejected. Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Probed gold-patched tree in image: (R1.1/R1.3) export_text on single-feature DecisionTreeClassifier with feature_names=['sepal_length'] returns full report, no IndexError. (R1.2) leaf nodes resolve to None placeholder, not sentinel index — confirmed by patch source `feature_names[i] if i != _tree.TREE_UNDEFINED else None`. (R1.4) split nodes labeled with feature_names[i] (output shows 'sepal_length <= 5.45'). (R2.3) generic feature_{i} path unchanged in the else branch. (R3.1) length mismatch raises ValueError('feature_names must contain 1 elements, got 2') and the length check precedes the list comprehension in source — validation not masked by IndexError. (R3.2-3.4) negative max_depth/decimals and non-positive spacing all raise ValueError. Modeling boundary is correct: requirements pin the changed observable behavior (sentinel→None resolution) rather than a narrow slice or invented behavior.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** requirements.md describes behavior and legitimately localizes the change to export_text in sklearn/tree/export.py. The single-feature / one-element feature_names scenario is straight from the PUBLIC problem_statement (reproducer uses X[:,0].reshape(-1,1) with feature_names=['sepal_length']). No hidden-test content leaks: the test's feature name 'first', X_single=[[-2],...], y_mo, the expected_report layout, and the test function name/path (test_export.py::test_export_text) are absent. The gold's only invented value is the None leaf placeholder; the doc says 'non-name placeholder' generically. TREE_UNDEFINED/-2 is a pre-existing sklearn sentinel constant describing tree internals (legitimate domain localization), not a fix-invented identifier. Requirement 3's validation list (max_depth/decimals/spacing/length mismatch) describes export_text's pre-existing argument validation derivable from source, translating PASS_TO_PASS behavior rather than transmitting the test_export_text_errors cases; no parametrization ids or test-shaped enumeration. show_weights is a public parameter. This is behavioral translation, not test reconstruction.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
