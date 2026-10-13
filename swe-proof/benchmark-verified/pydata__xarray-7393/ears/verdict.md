# P2 adversarial audit — pydata__xarray-7393

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
# Req 2.4 (positive control): int32 coordinate stacked into composite index and
# read back must keep its dtype (int32), not widen to int64.
import numpy as np
import xarray as xr

ds = xr.Dataset(
    coords={
        "x": np.array([1, 2, 3], dtype="int32"),
        "y": np.array([10, 20], dtype="int32"),
    }
)
stacked = ds.stack(z=("x", "y"))
got = stacked["x"].values.dtype
print("original x dtype: int32, read-back dtype:", got)
assert got == np.dtype("int32"), f"dtype widened to {got}"
print("OK")
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
# Req 2.4 float variant: float32 coordinate stacked and read back keeps float32.
import numpy as np
import xarray as xr

ds = xr.Dataset(
    coords={
        "x": np.array([1.5, 2.5, 3.5], dtype="float32"),
        "y": np.array([10, 20], dtype="int64"),
    }
)
stacked = ds.stack(z=("x", "y"))
got = stacked["x"].values.dtype
print("original x dtype: float32, read-back dtype:", got)
assert got == np.dtype("float32"), f"dtype widened to {got}"
print("OK")
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
# Req 2.1/2.3 + Req1.2: directly exercise PandasMultiIndexingAdapter.__array__
# on a level-bound wrapper with no explicit dtype -> must use stored dtype AND
# carry element values through unchanged.
import numpy as np
import pandas as pd
from xarray.core.indexing import PandasMultiIndexingAdapter

mi = pd.MultiIndex.from_arrays(
    [np.array([1, 2, 3], dtype="int32"), np.array([10, 20, 30], dtype="int64")],
    names=["a", "b"],
)
# wrapper stored dtype = int32, bound to level "a"
adapter = PandasMultiIndexingAdapter(mi, dtype=np.dtype("int32"), level="a")
arr = np.asarray(adapter)  # __array__ with no dtype
print("stored dtype:", adapter.dtype, "result dtype:", arr.dtype, "values:", arr)
assert arr.dtype == np.dtype("int32"), f"got {arr.dtype}"
assert list(arr) == [1, 2, 3], f"values changed: {arr}"
print("OK")
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
# Req 1.3: explicit target dtype passed to __array__ is honored (level-bound).
import numpy as np
import pandas as pd
from xarray.core.indexing import PandasMultiIndexingAdapter

mi = pd.MultiIndex.from_arrays(
    [np.array([1, 2, 3], dtype="int32"), np.array([10, 20, 30], dtype="int64")],
    names=["a", "b"],
)
adapter = PandasMultiIndexingAdapter(mi, dtype=np.dtype("int32"), level="a")
arr = adapter.__array__(np.dtype("int64"))
print("requested int64, result dtype:", arr.dtype, "values:", arr)
assert arr.dtype == np.dtype("int64"), f"got {arr.dtype}"
assert list(arr) == [1, 2, 3]
print("OK")
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
# Req 3.1: non-level case (level is None) defers to base conversion producing
# the SAME result as the base PandasIndexingAdapter over the same index.
import numpy as np
import pandas as pd
from xarray.core.indexing import PandasMultiIndexingAdapter, PandasIndexingAdapter

mi = pd.MultiIndex.from_arrays(
    [np.array([1, 2, 3], dtype="int64"), np.array([10, 20, 30], dtype="int64")],
    names=["a", "b"],
)
adapter = PandasMultiIndexingAdapter(mi, level=None)  # not bound
base = PandasIndexingAdapter(mi, dtype=adapter.dtype)
a1 = np.asarray(adapter)
a2 = np.asarray(base)
print("adapter (no level):", a1.dtype, "base:", a2.dtype)
assert a1.dtype == a2.dtype, f"{a1.dtype} vs {a2.dtype}"
assert np.array_equal(a1, a2), "values differ from base conversion"
print("OK")
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
# Req 3.4: indexing a level-bound wrapper into another wrapper retains the level.
# Req 2.3 values unchanged after read-back; also regression: stack/unstack round-trip.
import numpy as np
import pandas as pd
import xarray as xr
from xarray.core.indexing import PandasMultiIndexingAdapter

mi = pd.MultiIndex.from_arrays(
    [np.array([1, 2, 3, 4], dtype="int32"), np.array([10, 20, 30, 40], dtype="int64")],
    names=["a", "b"],
)
adapter = PandasMultiIndexingAdapter(mi, dtype=np.dtype("int32"), level="a")
from xarray.core.indexing import BasicIndexer
sub = adapter[BasicIndexer((slice(0, 2),))]
print("subwrapper type:", type(sub).__name__, "level:", getattr(sub, "level", "MISSING"))
assert isinstance(sub, PandasMultiIndexingAdapter)
assert sub.level == "a", f"level lost: {sub.level}"

# regression: stack then unstack preserves values and dtype
ds = xr.Dataset(coords={"x": np.array([1, 2, 3], dtype="int32"),
                        "y": np.array([5, 6], dtype="int32")})
un = ds.stack(z=("x", "y")).unstack("z")
assert un["x"].values.dtype == np.dtype("int32"), un["x"].values.dtype
assert list(un["x"].values) == [1, 2, 3]
print("OK")
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
# Req 2.4 (positive control): int32 coordinate stacked into composite index and
# read back must keep its dtype (int32), not widen to int64.
import numpy as np
import xarray as xr

ds = xr.Dataset(
    coords={
        "x": np.array([1, 2, 3], dtype="int32"),
        "y": np.array([10, 20], dtype="int32"),
    }
)
stacked = ds.stack(z=("x", "y"))
got = stacked["x"].values.dtype
print("original x dtype: int32, read-back dtype:", got)
assert got == np.dtype("int32"), f"dtype widened to {got}"
print("OK")
```

Prepatch bug re-encoded as an attack: `True`.

Requirements: preserve coordinate dtype when reading a level of a composite index (xarray PandasMultiIndexingAdapter.__array__). 6 probes written, all HOLD on gold-patched tree. Coverage: probe_1 (Req 2.4 int32 stack round-trip, POSITIVE CONTROL), probe_2 (Req 2.4 float32), probe_3 (Req 1.2/2.1/2.3 level-bound __array__ defaults to stored dtype AND values unchanged), probe_4 (Req 1.3 explicit dtype honored), probe_5 (Req 3.1/3.2 non-level case defers to base, same result), probe_6 (Req 3.4 __getitem__ retains level + stack/unstack regression). Positive control probe_1 FAILS at base (dtype widened int32->int64) and HOLDS patched -> discriminates.

TOO-WEAK check: candidate patch weak.diff adds the `if dtype is None: dtype = self.dtype` default (a plausible partial reading of Req 1.2) but does NOT wrap get_level_values(...).values in np.asarray(..., dtype=dtype), so the level values are never re-cast. It applies cleanly at base. Probes 1, 2, 3 REJECT it (still widens to int64/float64), demonstrating the suite discriminates the lazy fix that satisfies only the dtype-defaulting requirement while violating Req 2.2. No probe-conforming alternative patch found that would fail the hidden tests. Verdict SOUND.

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
# Req 2.4 (positive control): int32 coordinate stacked into composite index and
# read back must keep its dtype (int32), not widen to int64.
import numpy as np
import xarray as xr

ds = xr.Dataset(
    coords={
        "x": np.array([1, 2, 3], dtype="int32"),
        "y": np.array([10, 20], dtype="int32"),
    }
)
stacked = ds.stack(z=("x", "y"))
got = stacked["x"].values.dtype
print("original x dtype: int32, read-back dtype:", got)
assert got == np.dtype("int32"), f"dtype widened to {got}"
print("OK")
```

Prepatch bug re-encoded as an attack: `True`.

Requirements: preserve coordinate dtype when reading a level of a composite index (xarray PandasMultiIndexingAdapter.__array__). 6 probes written, all HOLD on gold-patched tree. Coverage: probe_1 (Req 2.4 int32 stack round-trip, POSITIVE CONTROL), probe_2 (Req 2.4 float32), probe_3 (Req 1.2/2.1/2.3 level-bound __array__ defaults to stored dtype AND values unchanged), probe_4 (Req 1.3 explicit dtype honored), probe_5 (Req 3.1/3.2 non-level case defers to base, same result), probe_6 (Req 3.4 __getitem__ retains level + stack/unstack regression). Positive control probe_1 FAILS at base (dtype widened int32->int64) and HOLDS patched -> discriminates.

TOO-WEAK check: candidate patch weak.diff adds the `if dtype is None: dtype = self.dtype` default (a plausible partial reading of Req 1.2) but does NOT wrap get_level_values(...).values in np.asarray(..., dtype=dtype), so the level values are never re-cast. It applies cleanly at base. Probes 1, 2, 3 REJECT it (still widens to int64/float64), demonstrating the suite discriminates the lazy fix that satisfies only the dtype-defaulting requirement while violating Req 2.2. No probe-conforming alternative patch found that would fail the hidden tests. Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Probed on the gold-patched instance image. Base PandasIndexingAdapter.__array__ source: `if dtype is None: dtype = self.dtype ... return np.asarray(array.values, dtype=dtype)`. Multi wrapper __array__ matches patch.diff exactly. dtype property returns self._dtype (the constructed dtype). Requirements pin the changed OBSERVABLE behavior (dtype preservation via __array__ on the level path) as a biconditional round-trip (Req 2.4), not a narrow helper slice; modeling boundary is correct. No mandated behavior the code lacks, nothing forbidden that it has, no invented behavior.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Requirements describe the dtype-preservation fix behaviorally and localize it to public symbols (PandasMultiIndexingAdapter.__array__, get_level_values, self.dtype, self.level) that appear in the public problem_statement/source pointer and are legitimate for localizing the change. No test names/paths/ids, no quoted test or gold code, no fix-invented identifiers (the gold introduces none). Closest concern: the requirements add a float32→float64 example (lines 16-17, Req 2.4) alongside the int32→int64 case that is public, and the pair loosely mirrors the hidden parametrization ['int32','float32']. However this is a natural generalization of numeric-dtype widening and does not reconstruct test structure (no dataset construction, no stack(baz=('bar',)) call, no assertion form). This is translating behavior into requirements, which is the intended task, not transmitting the tests.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
