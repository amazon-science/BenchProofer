# P2 adversarial audit — pydata__xarray-6721

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
import numpy as np
from xarray.tests import InaccessibleArray, UnexpectedDataAccess
from xarray.core.variable import Variable
from xarray.core.common import get_chunksizes

arr = InaccessibleArray(np.zeros((3, 4)))
v = Variable(("x", "y"), arr)
assert not hasattr(v._data, "chunks"), "precondition: inaccessible array has no chunks"
try:
    r = get_chunksizes([v])
except UnexpectedDataAccess as e:
    print("VIOLATION: realized lazy data:", e)
    raise SystemExit(1)
print("get_chunksizes returned", dict(r))
assert dict(r) == {}, "expected empty mapping for non-chunked lazy variable"
print("OK: no realization, empty mapping")
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
import numpy as np
from xarray.tests import InaccessibleArray, UnexpectedDataAccess
from xarray.core.variable import Variable
from xarray import Dataset

arr = InaccessibleArray(np.zeros((3, 4)))
ds = Dataset({"foo": Variable(("x", "y"), arr)})
try:
    ch = ds.chunks
except UnexpectedDataAccess as e:
    print("VIOLATION: Dataset.chunks realized lazy data:", e)
    raise SystemExit(1)
print("Dataset.chunks =", dict(ch))
assert ch == {}, "expected empty mapping"
# chunksizes too
try:
    cs = ds.chunksizes
except UnexpectedDataAccess as e:
    print("VIOLATION: Dataset.chunksizes realized lazy data:", e)
    raise SystemExit(1)
assert cs == {}, "expected empty chunksizes"
print("OK: Dataset.chunks/chunksizes safe & empty")
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
import numpy as np
import dask.array as da
from xarray.core.variable import Variable
from xarray.core.common import get_chunksizes

arr = da.zeros((6, 8), chunks=(3, 4))
v = Variable(("x", "y"), arr)
assert hasattr(v._data, "chunks")
r = dict(get_chunksizes([v]))
print("chunksizes:", r)
assert r == {"x": (3, 3), "y": (4, 4)}, r
print("OK: multi-dim chunked reporting preserved")
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
import numpy as np
import dask.array as da
from xarray.core.variable import Variable
from xarray.core.common import get_chunksizes

# same block lengths on shared dim x
a = Variable(("x",), da.zeros(6, chunks=3))
b = Variable(("x",), da.zeros(6, chunks=3))
r = dict(get_chunksizes([a, b]))
print("shared-consistent:", r)
assert r == {"x": (3, 3)}, r

# differing block lengths on shared dim -> ValueError
c = Variable(("x",), da.zeros(6, chunks=2))
try:
    get_chunksizes([a, c])
    print("VIOLATION: no ValueError for inconsistent chunks")
    raise SystemExit(1)
except ValueError as e:
    print("OK ValueError:", str(e).splitlines()[0])
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
import numpy as np
import dask.array as da
from xarray.core.variable import Variable
from xarray.core.common import get_chunksizes

chunked = Variable(("x",), da.zeros(6, chunks=3))
plain = Variable(("z",), np.zeros(4))  # not chunked, dim z should be omitted
r = get_chunksizes([chunked, plain])
d = dict(r)
print("mixed:", d)
assert d == {"x": (3, 3)}, d
assert "z" not in d, "non-chunked-only dim leaked"
# immutability
mutated = False
try:
    r["x"] = (1,)
    mutated = True
except (TypeError, AttributeError, Exception) as e:
    print("immutable as expected:", type(e).__name__)
if mutated:
    print("VIOLATION: mapping is mutable")
    raise SystemExit(1)
# values are tuples
assert isinstance(d["x"], tuple), "block lengths must be a tuple"
print("OK: mixed omission + immutable tuple mapping")
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
import numpy as np
from xarray.tests import InaccessibleArray, UnexpectedDataAccess
from xarray import DataArray

# Build normally, then replace the underlying stored array with an inaccessible
# lazy handle so that ONLY the chunk-aggregation path is exercised (Req 3.1/3.2),
# not DataArray construction (which legitimately builds indexes).
da_ = DataArray(np.zeros((3, 4)), dims=("x", "y"))
da_.variable._data = InaccessibleArray(np.zeros((3, 4)))
assert not hasattr(da_.variable._data, "chunks")
try:
    ch = da_.chunks
    cs = da_.chunksizes
except UnexpectedDataAccess as e:
    print("VIOLATION: DataArray chunk aggregation realized lazy data:", e)
    raise SystemExit(1)
print("DataArray.chunks =", ch, "chunksizes =", dict(cs))
assert ch is None, f"non-chunked DataArray.chunks should be None, got {ch!r}"
assert dict(cs) == {}, "expected empty chunksizes"
print("OK: DataArray aggregation non-realizing + empty")
```

Attack 7 — `probe_7.py` → holds on the patched tree (good)

```python
import numpy as np
from xarray.core.indexing import ExplicitlyIndexed
from xarray.core.utils import NDArrayMixin
from xarray.core.variable import Variable
from xarray.core.common import get_chunksizes

ACCESS = {"n": 0}

class SpyArray(NDArrayMixin, ExplicitlyIndexed):
    def __init__(self, array):
        self.array = array
    def __array__(self, dtype=None):
        ACCESS["n"] += 1
        return np.asarray(self.array, dtype=dtype)
    def __getitem__(self, key):
        ACCESS["n"] += 1
        return self.array[key]

v = Variable(("x", "y"), SpyArray(np.zeros((3, 4))))
assert not hasattr(v._data, "chunks")
r = get_chunksizes([v])
print("access count:", ACCESS["n"], "result:", dict(r))
if ACCESS["n"] != 0:
    print("VIOLATION: chunk inspection triggered realization/conversion of the array")
    raise SystemExit(1)
assert dict(r) == {}
print("OK: no realization attempted (metadata-only)")
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
import numpy as np
from xarray.tests import InaccessibleArray, UnexpectedDataAccess
from xarray.core.variable import Variable
from xarray.core.common import get_chunksizes

arr = InaccessibleArray(np.zeros((3, 4)))
v = Variable(("x", "y"), arr)
assert not hasattr(v._data, "chunks"), "precondition: inaccessible array has no chunks"
try:
    r = get_chunksizes([v])
except UnexpectedDataAccess as e:
    print("VIOLATION: realized lazy data:", e)
    raise SystemExit(1)
print("get_chunksizes returned", dict(r))
assert dict(r) == {}, "expected empty mapping for non-chunked lazy variable"
print("OK: no realization, empty mapping")
```

Prepatch bug re-encoded as an attack: `True`.

Instance pydata__xarray-6721: gold fix changes get_chunksizes in xarray/core/common.py from `hasattr(v.data, 'chunks')` to `hasattr(v._data, 'chunks')`, so chunk inspection reads the stored array metadata instead of going through Variable.data (which falls back to Variable.values and realizes lazy/backend-backed arrays).

7 probes written; all HOLD on gold-patched tree, all run in the official Docker image via nl_attack.

Probe->requirement mapping and observed results (patched / base):
- probe_1 (POSITIVE CONTROL) Req 1.1/1.2/1.4: get_chunksizes over an InaccessibleArray-backed Variable returns {} without raising. patched=HOLD, base=FAIL (UnexpectedDataAccess). Discriminates.
- probe_2 Req 1.2/1.3: Dataset.chunks and .chunksizes over inaccessible-backed var return {} without raising. patched=HOLD, base=FAIL.
- probe_3 Req 2.1/2.2: dask-backed 2-D var reports {'x':(3,3),'y':(4,4)}. patched=HOLD.
- probe_4 Req 2.3/2.4: shared dim consistent -> single entry; differing block lengths -> ValueError. patched=HOLD.
- probe_5 Req 2.5/2.6: mixed chunked/non-chunked omits non-chunked-only dim; result is read-only Frozen with tuple values (mutation raises TypeError). patched=HOLD.
- probe_6 Req 3.1/3.2: DataArray chunk aggregation over an inaccessible backing (swapped in post-construction to avoid the legitimate index build) returns None/{} without realizing. patched=HOLD, base=FAIL. Discriminates.
- probe_7 Req 1.1/1.4 (STRONGEST): uses a SpyArray that COUNTS __array__/__getitem__ access without raising; access count must be 0. patched=HOLD (0 accesses), base=FAIL (1 access). This encodes 'SHALL NOT cause realization/conversion' beyond merely 'SHALL NOT raise'.

Candidate wrong patch (weak.diff): wraps `hasattr(v.data,'chunks')` in try/except swallowing the exception -> has_chunks=False. This is the lazy fix a weak reading of Req 1.2 ('shall not raise') permits: it stops the raise but STILL realizes/converts the array (Req 1.4 violation), and would still trigger a full load for a real remote store that returns data instead of raising. Result under weak.diff: probes 1-6 HOLD but probe_7 REJECTS it (access count=1). So the suite discriminates this requirements-plausible wrong fix.

Conclusion: >=5 probes all hold on patched; positive control discriminates base->patched (prepatch_reproduced=true); >=1 candidate exercised and REJECTED by the suite. No requirement found that the gold patch fails to satisfy; no probe-conforming alternative found that resolves the true behavior while the gold does not. Verdict SOUND (advisory; runner re-checks). Note: construction of a DataArray directly on an inaccessible array realizes at index-build time independent of this fix, hence probe_6 swaps _data after construction to isolate the aggregation path.

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
import numpy as np
from xarray.tests import InaccessibleArray, UnexpectedDataAccess
from xarray.core.variable import Variable
from xarray.core.common import get_chunksizes

arr = InaccessibleArray(np.zeros((3, 4)))
v = Variable(("x", "y"), arr)
assert not hasattr(v._data, "chunks"), "precondition: inaccessible array has no chunks"
try:
    r = get_chunksizes([v])
except UnexpectedDataAccess as e:
    print("VIOLATION: realized lazy data:", e)
    raise SystemExit(1)
print("get_chunksizes returned", dict(r))
assert dict(r) == {}, "expected empty mapping for non-chunked lazy variable"
print("OK: no realization, empty mapping")
```

Prepatch bug re-encoded as an attack: `True`.

Instance pydata__xarray-6721: gold fix changes get_chunksizes in xarray/core/common.py from `hasattr(v.data, 'chunks')` to `hasattr(v._data, 'chunks')`, so chunk inspection reads the stored array metadata instead of going through Variable.data (which falls back to Variable.values and realizes lazy/backend-backed arrays).

7 probes written; all HOLD on gold-patched tree, all run in the official Docker image via nl_attack.

Probe->requirement mapping and observed results (patched / base):
- probe_1 (POSITIVE CONTROL) Req 1.1/1.2/1.4: get_chunksizes over an InaccessibleArray-backed Variable returns {} without raising. patched=HOLD, base=FAIL (UnexpectedDataAccess). Discriminates.
- probe_2 Req 1.2/1.3: Dataset.chunks and .chunksizes over inaccessible-backed var return {} without raising. patched=HOLD, base=FAIL.
- probe_3 Req 2.1/2.2: dask-backed 2-D var reports {'x':(3,3),'y':(4,4)}. patched=HOLD.
- probe_4 Req 2.3/2.4: shared dim consistent -> single entry; differing block lengths -> ValueError. patched=HOLD.
- probe_5 Req 2.5/2.6: mixed chunked/non-chunked omits non-chunked-only dim; result is read-only Frozen with tuple values (mutation raises TypeError). patched=HOLD.
- probe_6 Req 3.1/3.2: DataArray chunk aggregation over an inaccessible backing (swapped in post-construction to avoid the legitimate index build) returns None/{} without realizing. patched=HOLD, base=FAIL. Discriminates.
- probe_7 Req 1.1/1.4 (STRONGEST): uses a SpyArray that COUNTS __array__/__getitem__ access without raising; access count must be 0. patched=HOLD (0 accesses), base=FAIL (1 access). This encodes 'SHALL NOT cause realization/conversion' beyond merely 'SHALL NOT raise'.

Candidate wrong patch (weak.diff): wraps `hasattr(v.data,'chunks')` in try/except swallowing the exception -> has_chunks=False. This is the lazy fix a weak reading of Req 1.2 ('shall not raise') permits: it stops the raise but STILL realizes/converts the array (Req 1.4 violation), and would still trigger a full load for a real remote store that returns data instead of raising. Result under weak.diff: probes 1-6 HOLD but probe_7 REJECTS it (access count=1). So the suite discriminates this requirements-plausible wrong fix.

Conclusion: >=5 probes all hold on patched; positive control discriminates base->patched (prepatch_reproduced=true); >=1 candidate exercised and REJECTED by the suite. No requirement found that the gold patch fails to satisfy; no probe-conforming alternative found that resolves the true behavior while the gold does not. Verdict SOUND (advisory; runner re-checks). Note: construction of a DataArray directly on an inaccessible array realizes at index-build time independent of this fix, hence probe_6 swaps _data after construction to isolate the aggregation path.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Gold patch is a one-line change in get_chunksizes (xarray/core/common.py): hasattr(v.data,'chunks') -> hasattr(v._data,'chunks'). v.data falls back to v.values (np.asarray realization) for non-duck arrays; v._data is the raw stored handle, so chunked-ness is inspected as pure metadata. Behavioral probes with the canonical InaccessibleVariableDataStore (the F2P test's fixture): BASE Dataset.chunks RAISES UnexpectedDataAccess; PATCHED: Dataset.chunks=={} , Dataset.chunksizes=={}, DataArray.chunks is None, DataArray.chunksizes=={}, all without raising (Req1 AC1-4, Req3 AC1-2). Dask-chunked preserved: Dataset.chunks={'dim1':(8,),'dim2':(9,),'dim3':(10,)}, DataArray.chunks=((8,),(9,)) (Req2 AC1-2,5). ValueError-on-inconsistency and Frozen(read-only) mapping remain in unchanged source (Req2 AC4,6). Change confined to inspection during aggregation; Variable.chunks/chunksizes untouched (Req3 AC3). Requirements correctly model the changed observable behavior (non-realizing metadata inspection) rather than the issue's incidental 'inspect encoding' suggestion, and pin the biconditional chunked-ness determination — the right boundary, not a narrow slice.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The requirements describe the behavioral fix (chunk inspection must not realize lazily-backed data) using only identifiers and mechanics already public in problem_statement: get_chunksizes in xarray/core/common.py, the Variable.data->Variable.values->np.asarray realization chain (quoted verbatim in the issue traceback), the duck-array fallback, and the store-raises-on-access scenario (issue shows KeyboardInterrupt/unavailable store). No hidden content is transmitted: the test name test_chunks_does_not_load_data, its path, the helpers InaccessibleVariableDataStore/create_test_data/dump_to_store/open_dataset, and the gold identifier `_data` (v.data->v._data) never appear. Req 1.3/3.2's 'empty mapping == {}' parallels the test assertion ds.chunks=={} but is the natural behavioral consequence of 'no chunked variables', not a reconstruction of test structure. Reqs 2 and 3 generalize to chunked/mixed/DataArray behavior — broader than the single F2P test, i.e. behavior description, not test enumeration. Localizing the change to the named modules/functions is legitimate.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
