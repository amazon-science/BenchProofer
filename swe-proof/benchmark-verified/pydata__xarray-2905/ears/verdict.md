# P2 adversarial audit — pydata__xarray-2905

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 requirement probes hold on the patched tree; 1/2 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 7 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 7 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py`, `probe_7.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 2 alternative candidate patches, claimed to satisfy every cited requirement, and ran the same suite against them. The suite rejected 1 of the 2: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. The other 1 was not rejected by the suite. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

Counterexample / evidence:

```
At base and under weak.diff, Variable(dims=(), data=HasValues()) stores int 5 (or coerces the .values array) instead of the HasValues instance; probes 1 & 2 exit 1. Patched tree stores the object itself.
```

**Attacks re-run (7):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
"""Positive control. Req 1/2/4: object with a `values` attribute stored into a
0-d object Variable must remain the original instance, not its `.values`."""
import sys
import numpy as np
from xarray.core.variable import Variable

class HasValues:
    def __init__(self, array):
        self.values = array

obj = HasValues(np.arange(3))
v = Variable(dims=(), data=obj)
stored = v._data.item()
print("stored type:", type(stored).__name__, "is HasValues:", isinstance(stored, HasValues))
if not isinstance(stored, HasValues):
    print("FAIL: object was coerced to its .values contents")
    sys.exit(1)
print("OK")
sys.exit(0)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""Req 1.3: object whose `values` attr is an unrelated scalar (5) must be stored
as the object itself, not 5. Mirrors the issue's HasValues example."""
import sys
import numpy as np
from xarray.core.variable import Variable

class HasValues:
    values = 5

obj = HasValues()
v = Variable(dims=(), data=obj)
stored = v._data.item()
print("stored:", repr(stored), "type:", type(stored).__name__)
if stored == 5 or not isinstance(stored, HasValues):
    print("FAIL: stored the .values scalar instead of the object")
    sys.exit(1)
print("OK")
sys.exit(0)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""Req 2.1/2.2: pandas.Series and DataFrame must still be unwrapped to their
underlying numpy array (values preserved)."""
import sys
import numpy as np
import pandas as pd
from xarray.core.variable import as_compatible_data

s = pd.Series([1, 2, 3])
out = as_compatible_data(s)
print("series ->", type(out).__name__, getattr(out, "dtype", None))
ok = isinstance(out, np.ndarray) and np.array_equal(out, np.array([1, 2, 3]))

df = pd.DataFrame({"a": [1, 2], "b": [3, 4]})
outd = as_compatible_data(df)
print("dataframe ->", type(outd).__name__)
ok = ok and isinstance(outd, np.ndarray) and np.array_equal(outd, df.values)

if not ok:
    print("FAIL: pandas container not unwrapped to its numpy array")
    sys.exit(1)
print("OK")
sys.exit(0)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""Req 2.3: pandas.Index supplied as data must be wrapped via the index adapter
(PandasIndexAdapter), not stored raw and not left as a plain ndarray only."""
import sys
import numpy as np
import pandas as pd
from xarray.core.variable import as_compatible_data
from xarray.core.indexing import PandasIndexAdapter

idx = pd.Index([1, 2, 3])
out = as_compatible_data(idx)
print("index ->", type(out).__name__)
if not isinstance(out, PandasIndexAdapter):
    print("FAIL: pandas.Index not wrapped by PandasIndexAdapter")
    sys.exit(1)
# and the underlying values are preserved
vals = np.asarray(out)
print("values:", vals)
if not np.array_equal(vals, np.array([1, 2, 3])):
    print("FAIL: index values not preserved")
    sys.exit(1)
print("OK")
sys.exit(0)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""Req 3.2: numpy.ma.MaskedArray handling preserved (masked entries filled;
all-unmasked converts to plain array)."""
import sys
import numpy as np
from xarray.core.variable import as_compatible_data

m = np.ma.MaskedArray([1.0, 2.0, 3.0], mask=[False, True, False])
out = as_compatible_data(m)
print("masked ->", type(out).__name__, out)
ok = isinstance(out, np.ndarray) and not isinstance(out, np.ma.MaskedArray)
ok = ok and out[0] == 1.0 and out[2] == 3.0 and np.isnan(out[1])

m2 = np.ma.MaskedArray([1, 2, 3], mask=[False, False, False])
out2 = as_compatible_data(m2)
ok = ok and isinstance(out2, np.ndarray) and np.array_equal(out2, np.array([1, 2, 3]))

if not ok:
    print("FAIL: masked array handling changed")
    sys.exit(1)
print("OK")
sys.exit(0)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
"""Req 3.3: pandas.Timestamp -> datetime64[ns]; datetime.timedelta ->
timedelta64[ns]."""
import sys
import datetime
import numpy as np
import pandas as pd
from xarray.core.variable import as_compatible_data

ts = pd.Timestamp("2019-01-01")
out = as_compatible_data(ts)
print("timestamp ->", out.dtype, out)
ok = out.dtype == np.dtype("datetime64[ns]")

td = datetime.timedelta(seconds=1)
outt = as_compatible_data(td)
print("timedelta ->", outt.dtype, outt)
ok = ok and outt.dtype == np.dtype("timedelta64[ns]")

if not ok:
    print("FAIL: timestamp/timedelta conversion changed")
    sys.exit(1)
print("OK")
sys.exit(0)
```

Attack 7 — `probe_7.py` → holds on the patched tree (good)

```python
"""Req 3.4: a tuple is stored as a zero-dimensional object array."""
import sys
import numpy as np
from xarray.core.variable import as_compatible_data

out = as_compatible_data((1, 2, 3))
print("tuple ->", type(out).__name__, out.dtype, out.shape, out.item())
ok = isinstance(out, np.ndarray) and out.dtype == object and out.shape == ()
ok = ok and out.item() == (1, 2, 3)
if not ok:
    print("FAIL: tuple not stored as 0-d object array")
    sys.exit(1)
print("OK")
sys.exit(0)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Positive control. Req 1/2/4: object with a `values` attribute stored into a
0-d object Variable must remain the original instance, not its `.values`."""
import sys
import numpy as np
from xarray.core.variable import Variable

class HasValues:
    def __init__(self, array):
        self.values = array

obj = HasValues(np.arange(3))
v = Variable(dims=(), data=obj)
stored = v._data.item()
print("stored type:", type(stored).__name__, "is HasValues:", isinstance(stored, HasValues))
if not isinstance(stored, HasValues):
    print("FAIL: object was coerced to its .values contents")
    sys.exit(1)
print("OK")
sys.exit(0)
```

Prepatch bug re-encoded as an attack: `True`.

Requirements map: probe_1 (Req 1.2/1.4/2 positive control: object w/ .values array stored as instance; FAILS base+weak.diff, HOLDS patched). probe_2 (Req 1.3: HasValues.values==5 stored as object not 5; REJECTS weak.diff). probe_3 (Req 2.1/2.2: pd.Series/DataFrame unwrapped to ndarray). probe_4 (Req 2.3: pd.Index -> PandasIndexAdapter). probe_5 (Req 3.2: MaskedArray fill/convert). probe_6 (Req 3.3: Timestamp->datetime64[ns], timedelta->timedelta64[ns]). probe_7 (Req 3.4: tuple -> 0-d object array). All 7 HOLD patched. positive control discriminates (base ValueError/int-5). CANDIDATE weak.diff = `if hasattr(data,'values'): data=data.values` (behaviorally the buggy original) -> REJECTED by probes 1&2, confirming discrimination.

CANDIDATE weak2.diff = only `pd.Series` unwrapped (drops Index/DataFrame branch) -> passes all my probes because pd.DataFrame/Index still normalize downstream to equivalent arrays in these cases; flagged for official-harness re-check as a potential too-weak reading, though it likely still resolves since the F2P test only exercises the object case and P2P pandas cases survive downstream conversion. Verdict advisory: >=5 probes hold, positive control discriminates, >=1 candidate rejected -> SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 requirement probes hold on the patched tree; 1/2 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 7 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 7 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py`, `probe_7.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 2 alternative candidate patches, claimed to satisfy every cited requirement, and ran the same suite against them. The suite rejected 1 of the 2: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. The other 1 was not rejected by the suite. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

Counterexample / evidence:

```
At base and under weak.diff, Variable(dims=(), data=HasValues()) stores int 5 (or coerces the .values array) instead of the HasValues instance; probes 1 & 2 exit 1. Patched tree stores the object itself.
```

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
"""Positive control. Req 1/2/4: object with a `values` attribute stored into a
0-d object Variable must remain the original instance, not its `.values`."""
import sys
import numpy as np
from xarray.core.variable import Variable

class HasValues:
    def __init__(self, array):
        self.values = array

obj = HasValues(np.arange(3))
v = Variable(dims=(), data=obj)
stored = v._data.item()
print("stored type:", type(stored).__name__, "is HasValues:", isinstance(stored, HasValues))
if not isinstance(stored, HasValues):
    print("FAIL: object was coerced to its .values contents")
    sys.exit(1)
print("OK")
sys.exit(0)
```

Prepatch bug re-encoded as an attack: `True`.

Requirements map: probe_1 (Req 1.2/1.4/2 positive control: object w/ .values array stored as instance; FAILS base+weak.diff, HOLDS patched). probe_2 (Req 1.3: HasValues.values==5 stored as object not 5; REJECTS weak.diff). probe_3 (Req 2.1/2.2: pd.Series/DataFrame unwrapped to ndarray). probe_4 (Req 2.3: pd.Index -> PandasIndexAdapter). probe_5 (Req 3.2: MaskedArray fill/convert). probe_6 (Req 3.3: Timestamp->datetime64[ns], timedelta->timedelta64[ns]). probe_7 (Req 3.4: tuple -> 0-d object array). All 7 HOLD patched. positive control discriminates (base ValueError/int-5). CANDIDATE weak.diff = `if hasattr(data,'values'): data=data.values` (behaviorally the buggy original) -> REJECTED by probes 1&2, confirming discrimination.

CANDIDATE weak2.diff = only `pd.Series` unwrapped (drops Index/DataFrame branch) -> passes all my probes because pd.DataFrame/Index still normalize downstream to equivalent arrays in these cases; flagged for official-harness re-check as a potential too-weak reading, though it likely still resolves since the F2P test only exercises the object case and P2P pandas cases survive downstream conversion. Verdict advisory: >=5 probes hold, positive control discriminates, >=1 candidate rejected -> SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Probe (gold-patched vs --base) results: obj identity preserved True vs False (the changed behavior); pandas Series -> int64 ndarray (both); pd.Index -> PandasIndexAdapter (both); tuple -> 0-d object array (both); MaskedArray -> float64 with nan fill (both); pd.Timestamp -> datetime64[ns] (both). Req1's pandas type list matches the patch's isinstance tuple exactly. Modeling boundary = the changed observable (values-attr discriminator), not a single branch/helper. FAIL_TO_PASS test asserts isinstance(orig._data.item(), CustomWithValuesAttr), consistent with Req 2/4.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The document localizes the change to as_compatible_data in xarray/core/variable.py — legitimate, and also public since the problem_statement links the exact changed line (PR #1746, variable.py L641). The pandas triple (Series/Index/DataFrame) that the spec says must still be unwrapped mirrors the gold condition `isinstance(data, (pd.Series, pd.Index, pd.DataFrame))`, but these are public pandas API types describing the intended behavioral BOUNDARY of the fix, not fix-invented identifiers — translating what must remain unwrapped vs. left opaque is exactly the behavioral spec's job. The 'scalar (zero-dimensional)' / 'retrieving the stored scalar element SHALL be an instance of the original type' criteria track the hidden test's Variable(dims=(), data=array) + isinstance(orig._data.item(), CustomWithValuesAttr) assertion, yet scalar .loc assignment and instance-preservation are already public in the problem_statement's HasValues/values=5/set() example. No hidden-test artifacts are transmitted: no test name (test_unsupported_type), no path/class name (CustomWithValuesAttr), no parametrization ids, no verbatim test/gold code lines, and no case enumeration mirroring parametrization. Faithful behavioral translation, not test reconstruction.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
