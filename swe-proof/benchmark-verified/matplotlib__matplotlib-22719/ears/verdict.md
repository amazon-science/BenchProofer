# P2 adversarial audit — matplotlib__matplotlib-22719

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 9 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 9 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 9 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py`, `probe_7.py`, `probe_8.py`, `probe_9.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (9):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
"""R1.1 (positive control): convert() with EMPTY value against a valid UnitData
unit SHALL NOT emit the numeric-passthrough MatplotlibDeprecationWarning.
Patched: no warning (HOLD). Base: warning fires (FAIL)."""
import sys, warnings
import numpy as np
import matplotlib.category as cat
from matplotlib import MatplotlibDeprecationWarning

unit = cat.UnitData(["a", "b", "c"])
with warnings.catch_warnings(record=True) as rec:
    warnings.simplefilter("always")
    res = cat.StrCategoryConverter.convert([], unit, None)
dep = [w for w in rec if issubclass(w.category, MatplotlibDeprecationWarning)]
print("n_dep_warnings=", len(dep), "result=", repr(res))
for w in dep:
    print("  warn:", w.message)
if dep:
    print("FAIL: deprecation warning emitted for empty value")
    sys.exit(1)
print("HOLD: no deprecation warning for empty value")
sys.exit(0)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""R1.2: convert() with empty value against a valid UnitData unit SHALL complete
without raising and return an empty float array."""
import sys
import numpy as np
import matplotlib.category as cat

unit = cat.UnitData(["a", "b", "c"])
try:
    res = cat.StrCategoryConverter.convert([], unit, None)
except Exception as e:
    print("FAIL: raised", type(e).__name__, e)
    sys.exit(1)
arr = np.asarray(res)
print("result=", repr(res), "size=", arr.size, "dtype=", arr.dtype)
if arr.size != 0:
    print("FAIL: expected empty array")
    sys.exit(1)
if not np.issubdtype(arr.dtype, np.floating):
    print("FAIL: expected float dtype")
    sys.exit(1)
print("HOLD: empty float array, no raise")
sys.exit(0)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""R2.1 + R2.2 + R2.3 (regression): non-empty numeric input STILL emits the
numeric-passthrough deprecation warning AND returns a float array of the values."""
import sys, warnings
import numpy as np
import matplotlib.category as cat
from matplotlib import MatplotlibDeprecationWarning

unit = cat.UnitData(["a", "b"])
with warnings.catch_warnings(record=True) as rec:
    warnings.simplefilter("always")
    res = cat.StrCategoryConverter.convert([1, 2, 3], unit, None)
dep = [w for w in rec if issubclass(w.category, MatplotlibDeprecationWarning)]
arr = np.asarray(res)
print("n_dep=", len(dep), "result=", repr(res))
if not dep:
    print("FAIL: no deprecation warning for non-empty numeric input")
    sys.exit(1)
if not np.allclose(arr, [1.0, 2.0, 3.0]):
    print("FAIL: values not returned as floats")
    sys.exit(1)
if not np.issubdtype(arr.dtype, np.floating):
    print("FAIL: not a float array")
    sys.exit(1)
print("HOLD: warning fired and float array returned")
sys.exit(0)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""R3.1 + R3.2 (regression): non-empty string/categorical input maps to integer
category ids as a float array, WITHOUT the deprecation warning, and updates the
unit mapping for previously-unseen categories."""
import sys, warnings
import numpy as np
import matplotlib.category as cat
from matplotlib import MatplotlibDeprecationWarning

unit = cat.UnitData(["a", "b"])
with warnings.catch_warnings(record=True) as rec:
    warnings.simplefilter("always")
    res = cat.StrCategoryConverter.convert(["a", "b", "c"], unit, None)
dep = [w for w in rec if issubclass(w.category, MatplotlibDeprecationWarning)]
arr = np.asarray(res)
print("result=", repr(res), "mapping=", dict(unit._mapping))
if dep:
    print("FAIL: deprecation warning emitted for categorical input")
    sys.exit(1)
# 'c' previously unseen -> assigned id 2
if not np.allclose(arr, [0.0, 1.0, 2.0]):
    print("FAIL: category ids wrong")
    sys.exit(1)
if unit._mapping.get(b"c") != 2 and unit._mapping.get("c") != 2:
    print("FAIL: unseen category 'c' not added to mapping")
    sys.exit(1)
print("HOLD: mapped to ids, mapping updated, no warning")
sys.exit(0)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""R3.3 + R3.4 (regression): unit=None raises ValueError; a scalar string is
converted as a one-element sequence returning the corresponding float."""
import sys
import numpy as np
import matplotlib.category as cat

# R3.3: None unit -> ValueError
raised = False
try:
    cat.StrCategoryConverter.convert(["a"], None, None)
except ValueError as e:
    raised = True
    print("R3.3 ValueError:", e)
except Exception as e:
    print("FAIL R3.3: wrong exception", type(e).__name__)
    sys.exit(1)
if not raised:
    print("FAIL R3.3: no ValueError for unit=None")
    sys.exit(1)

# R3.4: scalar string
unit = cat.UnitData(["a", "b"])
res = cat.StrCategoryConverter.convert("b", unit, None)
arr = np.atleast_1d(np.asarray(res))
print("R3.4 scalar result=", repr(res))
if not np.allclose(arr, [1.0]):
    print("FAIL R3.4: scalar string not mapped to its id")
    sys.exit(1)
print("HOLD: R3.3 and R3.4 satisfied")
sys.exit(0)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
"""R4.1 + R4.2: UnitData.update([]) SHALL NOT emit the informational log message
and SHALL leave the mapping unchanged (and not raise). We capture the log via a
handler on matplotlib.category's logger."""
import sys, logging, copy
import matplotlib.category as cat

records = []
class H(logging.Handler):
    def emit(self, r):
        records.append(r.getMessage())
logger = logging.getLogger("matplotlib.category")
logger.addHandler(H())
logger.setLevel(logging.INFO)

unit = cat.UnitData(["a", "b"])
before = dict(unit._mapping)
try:
    unit.update([])
except Exception as e:
    print("FAIL: update([]) raised", type(e).__name__, e)
    sys.exit(1)
after = dict(unit._mapping)
info = [m for m in records if "parsable as floats or dates" in m]
print("n_info=", len(info), "mapping_before=", before, "mapping_after=", after)
if info:
    print("FAIL: info log emitted for empty data")
    sys.exit(1)
if before != after:
    print("FAIL: mapping changed on empty update")
    sys.exit(1)
print("HOLD: no log, mapping unchanged")
sys.exit(0)
```

Attack 7 — `probe_7.py` → holds on the patched tree (good)

```python
"""R5.1 (regression): UnitData.update with non-empty data where every unique
string is parsable as a number/date SHALL emit the informational log message."""
import sys, logging
import matplotlib.category as cat

records = []
class H(logging.Handler):
    def emit(self, r):
        records.append(r.getMessage())
logger = logging.getLogger("matplotlib.category")
logger.addHandler(H())
logger.setLevel(logging.INFO)

unit = cat.UnitData()
unit.update(["1", "2", "3"])
info = [m for m in records if "parsable as floats or dates" in m]
print("n_info=", len(info))
for m in info:
    print("  ", m[:60])
if not info:
    print("FAIL: no info log for non-empty all-parsable data")
    sys.exit(1)
print("HOLD: info log emitted for non-empty parsable data")
sys.exit(0)
```

Attack 8 — `probe_8.py` → holds on the patched tree (good)

```python
"""R6.1 + R6.2 + R6.3 (regression): update assigns consecutive ids preserving
first-seen order, leaves existing ids unchanged; non-str/bytes raises TypeError;
construction with initial data populates mapping by same rules."""
import sys
import matplotlib.category as cat

# R6.3 construction populates mapping in first-seen order
unit = cat.UnitData(["c", "a", "c", "b"])
def norm(m):
    return {(k.decode() if isinstance(k, bytes) else k): v for k, v in m.items()}
m = norm(unit._mapping)
print("initial mapping=", m)
if m != {"c": 0, "a": 1, "b": 2}:
    print("FAIL R6.3: mapping not first-seen consecutive")
    sys.exit(1)

# R6.1 update assigns new consecutive ids, existing unchanged
unit.update(["a", "d"])
m2 = norm(unit._mapping)
print("after update mapping=", m2)
if m2 != {"c": 0, "a": 1, "b": 2, "d": 3}:
    print("FAIL R6.1: ids not preserved/extended correctly")
    sys.exit(1)

# R6.2 TypeError for non-str/bytes element
raised = False
try:
    unit.update([1])
except TypeError as e:
    raised = True
    print("R6.2 TypeError:", e)
if not raised:
    print("FAIL R6.2: no TypeError for numeric element")
    sys.exit(1)
print("HOLD: R6.1/6.2/6.3 satisfied")
sys.exit(0)
```

Attack 9 — `probe_9.py` → holds on the patched tree (good)

```python
"""R1.3 (end-to-end): plotting empty data on an axis already using categorical
string units SHALL complete without emitting a deprecation warning from the
categorical converter (and without raising a ConversionError)."""
import sys, warnings
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import MatplotlibDeprecationWarning

fig, ax = plt.subplots()
ax.plot(["a", "b", "c"], [1, 2, 3])  # establish categorical units on x-axis
with warnings.catch_warnings(record=True) as rec:
    warnings.simplefilter("always")
    try:
        ax.plot([], [])
        fig.canvas.draw()
    except Exception as e:
        print("FAIL: raised", type(e).__name__, e)
        sys.exit(1)
dep = [w for w in rec if issubclass(w.category, MatplotlibDeprecationWarning)]
print("n_dep=", len(dep))
for w in dep:
    print("  ", w.message)
if dep:
    print("FAIL: deprecation warning on empty plot over categorical axis")
    sys.exit(1)
print("HOLD: empty plot over categorical axis quiet")
sys.exit(0)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""R1.1 (positive control): convert() with EMPTY value against a valid UnitData
unit SHALL NOT emit the numeric-passthrough MatplotlibDeprecationWarning.
Patched: no warning (HOLD). Base: warning fires (FAIL)."""
import sys, warnings
import numpy as np
import matplotlib.category as cat
from matplotlib import MatplotlibDeprecationWarning

unit = cat.UnitData(["a", "b", "c"])
with warnings.catch_warnings(record=True) as rec:
    warnings.simplefilter("always")
    res = cat.StrCategoryConverter.convert([], unit, None)
dep = [w for w in rec if issubclass(w.category, MatplotlibDeprecationWarning)]
print("n_dep_warnings=", len(dep), "result=", repr(res))
for w in dep:
    print("  warn:", w.message)
if dep:
    print("FAIL: deprecation warning emitted for empty value")
    sys.exit(1)
print("HOLD: no deprecation warning for empty value")
sys.exit(0)
```

Prepatch bug re-encoded as an attack: `True`.

Requirements track the gold patch exactly: two guards `values.size and is_numlike` in StrCategoryConverter.convert and `data.size and convertible` in UnitData.update, suppressing spurious notifications on empty sequences while preserving all non-empty behavior.

Probes (all HOLD on gold-patched tree):
- probe_1 (R1.1, POSITIVE CONTROL): convert([], valid unit) emits NO deprecation warning. Patched: 0 warnings (HOLD). Base: 1 warning (FAIL) => discriminates, prepatch reproduced.
- probe_2 (R1.2): convert([]) returns empty float64 array, no raise. Holds both trees (behavior unchanged by patch on this axis) but pins the return shape.
- probe_3 (R2.1/2.2/2.3): non-empty numeric [1,2,3] STILL warns and returns float array. HOLD.
- probe_4 (R3.1/3.2): non-empty categorical maps to ids [0,1,2], no warning, unseen category added. HOLD.
- probe_5 (R3.3/3.4): unit=None -> ValueError; scalar string 'b' -> [1.0]. HOLD.
- probe_6 (R4.1/4.2): update([]) emits NO info log and leaves mapping unchanged. Patched HOLD; Base FAIL (info log fires) => second discriminating leg.
- probe_7 (R5.1): update(['1','2','3']) emits info log. HOLD.
- probe_8 (R6.1/6.2/6.3): first-seen consecutive ids, existing ids preserved, TypeError on numeric element, construction populates mapping. HOLD.
- probe_9 (R1.3): end-to-end plot of empty data over categorical x-axis raises nothing and emits no deprecation warning. Patched HOLD; Base FAIL => discriminates end-to-end.

Candidate wrong-fix (weak.diff = partial fix: guards only convert(), leaves update() unguarded — the lazy half-fix a weak reading of R1 alone permits). Result: probe_1 HOLDS but probe_6 REJECTS it (info log still fires on empty update, violating R4.1). This proves the suite discriminates a probe-nonconforming partial patch; no requirements-conforming-yet-wrong patch was found. Verdict SOUND: 9 distinct probes all hold on patched; positive control (probe_1) and additionally probe_6/probe_9 fail at base.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 9 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 9 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 9 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py`, `probe_7.py`, `probe_8.py`, `probe_9.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (9):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

_The 9 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts, and on this backend both roles put it through the same derivation: every block below is a requirement probe run on the gold-patched tree, and the `machine verdict:` line each role publishes above reports BOTH that its probes hold there and how many candidate patches the probe suite rejected — so the two roles re-ran ONE probe suite and each recorded its own outcome for every probe in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `probe_1.py` → holds on the patched tree (good)

Attack 2 — `probe_2.py` → holds on the patched tree (good)

Attack 3 — `probe_3.py` → holds on the patched tree (good)

Attack 4 — `probe_4.py` → holds on the patched tree (good)

Attack 5 — `probe_5.py` → holds on the patched tree (good)

Attack 6 — `probe_6.py` → holds on the patched tree (good)

Attack 7 — `probe_7.py` → holds on the patched tree (good)

Attack 8 — `probe_8.py` → holds on the patched tree (good)

Attack 9 — `probe_9.py` → holds on the patched tree (good)

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""R1.1 (positive control): convert() with EMPTY value against a valid UnitData
unit SHALL NOT emit the numeric-passthrough MatplotlibDeprecationWarning.
Patched: no warning (HOLD). Base: warning fires (FAIL)."""
import sys, warnings
import numpy as np
import matplotlib.category as cat
from matplotlib import MatplotlibDeprecationWarning

unit = cat.UnitData(["a", "b", "c"])
with warnings.catch_warnings(record=True) as rec:
    warnings.simplefilter("always")
    res = cat.StrCategoryConverter.convert([], unit, None)
dep = [w for w in rec if issubclass(w.category, MatplotlibDeprecationWarning)]
print("n_dep_warnings=", len(dep), "result=", repr(res))
for w in dep:
    print("  warn:", w.message)
if dep:
    print("FAIL: deprecation warning emitted for empty value")
    sys.exit(1)
print("HOLD: no deprecation warning for empty value")
sys.exit(0)
```

Prepatch bug re-encoded as an attack: `True`.

Requirements track the gold patch exactly: two guards `values.size and is_numlike` in StrCategoryConverter.convert and `data.size and convertible` in UnitData.update, suppressing spurious notifications on empty sequences while preserving all non-empty behavior.

Probes (all HOLD on gold-patched tree):
- probe_1 (R1.1, POSITIVE CONTROL): convert([], valid unit) emits NO deprecation warning. Patched: 0 warnings (HOLD). Base: 1 warning (FAIL) => discriminates, prepatch reproduced.
- probe_2 (R1.2): convert([]) returns empty float64 array, no raise. Holds both trees (behavior unchanged by patch on this axis) but pins the return shape.
- probe_3 (R2.1/2.2/2.3): non-empty numeric [1,2,3] STILL warns and returns float array. HOLD.
- probe_4 (R3.1/3.2): non-empty categorical maps to ids [0,1,2], no warning, unseen category added. HOLD.
- probe_5 (R3.3/3.4): unit=None -> ValueError; scalar string 'b' -> [1.0]. HOLD.
- probe_6 (R4.1/4.2): update([]) emits NO info log and leaves mapping unchanged. Patched HOLD; Base FAIL (info log fires) => second discriminating leg.
- probe_7 (R5.1): update(['1','2','3']) emits info log. HOLD.
- probe_8 (R6.1/6.2/6.3): first-seen consecutive ids, existing ids preserved, TypeError on numeric element, construction populates mapping. HOLD.
- probe_9 (R1.3): end-to-end plot of empty data over categorical x-axis raises nothing and emits no deprecation warning. Patched HOLD; Base FAIL => discriminates end-to-end.

Candidate wrong-fix (weak.diff = partial fix: guards only convert(), leaves update() unguarded — the lazy half-fix a weak reading of R1 alone permits). Result: probe_1 HOLDS but probe_6 REJECTS it (info log still fires on empty update, violating R4.1). This proves the suite discriminates a probe-nonconforming partial patch; no requirements-conforming-yet-wrong patch was found. Verdict SOUND: 9 distinct probes all hold on patched; positive control (probe_1) and additionally probe_6/probe_9 fail at base.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Probe RESULTS on gold-patched image: {'empty_convert_no_warn': True, 'numeric_warns': True, 'unit_none': 'ValueError', 'empty_update_nochange': True, 'nonstr_type': 'TypeError'} and log-boundary {'nonempty_logged': True, 'empty_logged': False}. The conjunction framing in R2.3/R5.2 precisely mirrors `values.size AND is_numlike` / `data.size AND convertible`. Requirements correctly model the changed observable behavior (the notification firing decision), not a narrow branch/helper. Faithful.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Requirements describe the empty-sequence suppression behavior for StrCategoryConverter.convert and UnitData.update. Module/function names are named in the public problem_statement traceback, so localization is legitimate. The reproduction (update_units(['a','b']) + plot([],[])) and the deprecation-warning/ConversionError symptom are all public. No hidden-test artifacts leak: no test names/paths (test_no_deprecation_on_empty_data, TestUnitData, TestStrCategoryConverter), no parametrization ids ([single]/[mixed]/[scatter-ascii]), no quoted test/gold code, no fix-invented identifiers. The conjunction framing ('non-empty AND property P') derives from the one-line fix logic, and the preservation clauses (Req 2,3,5,6 incl. scalar-string handling and TypeError-on-non-str) describe pre-existing behavior readable from the module source rather than mirroring the hidden test parametrization. Faithful behavioral translation, not test reconstruction.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
