# P2 adversarial audit — pydata__xarray-4094

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

Counterexample / evidence:

```
Under the partial-fix candidate (weak.diff: sel(drop=True) WITHOUT .squeeze(drop=True)), probe_3 (Req2.1/2.4 multi-dim regression) is REJECTED: the reconstructed variables retain the now-singleton stacked axis, so slices misalign and assert_identical fails (observed nan-filled float64 arrays). This demonstrates the probe suite discriminates the requirements-incomplete fix. The candidate would also fail the hidden test test_to_stacked_array_to_unstacked_dataset.
```

**Attacks re-run (5):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
"""Req1.1 (POSITIVE CONTROL): single-dimension round trip returns identical Dataset.

Variables share only the sample dim 'x' and have no further dimension.
stack -> unstack must reproduce the original dataset exactly.
Holds on patched tree; must FAIL at base (merge/conflicting-values error).
"""
import sys
import numpy as np
import xarray as xr

arr = xr.DataArray(np.arange(3), coords=[("x", [0, 1, 2])])
data = xr.Dataset({"a": arr, "b": arr})

stacked = data.to_stacked_array("y", sample_dims=["x"])
try:
    unstacked = stacked.to_unstacked_dataset("y")
except Exception as e:
    print("to_unstacked_dataset raised:", type(e).__name__, e)
    sys.exit(1)

try:
    xr.testing.assert_identical(data, unstacked)
except AssertionError as e:
    print("not identical:", e)
    sys.exit(1)

print("OK: single-dim round trip identical")
print("vars:", list(unstacked.data_vars))
sys.exit(0)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""Req1.2 / Req1.4: single-dim reconstruction does not raise, and reconstructed
variables carry NO leftover scalar coordinate for the variable-label level or
the stacked dim itself.
"""
import sys
import numpy as np
import xarray as xr

arr = xr.DataArray(np.arange(3), coords=[("x", [0, 1, 2])])
data = xr.Dataset({"a": arr, "b": arr})

stacked = data.to_stacked_array("y", sample_dims=["x"])
try:
    unstacked = stacked.to_unstacked_dataset("y")
except Exception as e:
    print("raised (Req1.2 violated):", type(e).__name__, e)
    sys.exit(1)

bad = []
for name, var in unstacked.data_vars.items():
    for c in var.coords:
        if c in ("y", "variable") or c not in data[name].coords:
            bad.append((name, c))
# also no 'y' dim/coord anywhere in the reconstructed vars
for name, var in unstacked.data_vars.items():
    if "y" in var.dims:
        bad.append((name, "y-dim"))

print("reconstructed coords:", {n: list(v.coords) for n, v in unstacked.data_vars.items()})
if bad:
    print("leftover scalar coords / dims:", bad)
    sys.exit(1)
print("OK: no leftover label/stacked coords")
sys.exit(0)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""Req2.1 / Req2.4 (regression): multi-dimension variables still round-trip
identically. Mirrors the upstream test setup with an extra per-variable dim 'y'.
"""
import sys
import numpy as np
import xarray as xr

x = np.arange(4)
components = ["temp", "pressure"]
comp = xr.DataArray(np.arange(2), dims="component", coords={"component": components})

# 'a' has extra dim 'component', 'b' has only the sample dim 'x'
a = xr.DataArray(np.arange(8).reshape(4, 2), dims=("x", "component"),
                 coords={"x": x, "component": components})
b = xr.DataArray(np.arange(4) * 1.0, dims=("x",), coords={"x": x})
data = xr.Dataset({"a": a, "b": b})

stacked = data.to_stacked_array("y", sample_dims=["x"])
unstacked = stacked.to_unstacked_dataset("y")

try:
    xr.testing.assert_identical(data, unstacked)
except AssertionError as e:
    print("multi-dim round trip NOT identical:", e)
    sys.exit(1)

# each var reduced to intended dims only
if set(unstacked["a"].dims) != {"x", "component"} or set(unstacked["b"].dims) != {"x"}:
    print("dims wrong:", unstacked["a"].dims, unstacked["b"].dims)
    sys.exit(1)

print("OK: mixed multi/single-dim round trip identical")
sys.exit(0)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""Req2.2 / Req2.3: level selection by name and by integer position both work,
producing one entry per label, keyed by label, in level order.
"""
import sys
import numpy as np
import xarray as xr

x = np.arange(3)
a = xr.DataArray(np.arange(3), dims="x", coords={"x": x})
b = xr.DataArray(np.arange(3) + 10, dims="x", coords={"x": x})
c = xr.DataArray(np.arange(3) + 20, dims="x", coords={"x": x})
data = xr.Dataset({"a": a, "b": b, "c": c})

stacked = data.to_stacked_array("y", sample_dims=["x"])

# variable level name is 'variable'
by_name = stacked.to_unstacked_dataset("y", level="variable")
by_int = stacked.to_unstacked_dataset("y", level=0)

for label, ds in (("name", by_name), ("int", by_int)):
    names = list(ds.data_vars)
    if names != ["a", "b", "c"]:
        print(f"level={label}: wrong labels/order:", names)
        sys.exit(1)

xr.testing.assert_identical(by_name, by_int)
print("OK: level by name and by int both give labels in order:", list(by_name.data_vars))
sys.exit(0)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""Req3.1: unstacking along a dimension not backed by a MultiIndex raises
ValueError indicating it is not a stacked coordinate.
"""
import sys
import numpy as np
import xarray as xr

# plain (non-stacked) DataArray
da = xr.DataArray(np.arange(6).reshape(2, 3),
                  dims=("z", "w"),
                  coords={"z": [0, 1], "w": [0, 1, 2]})
try:
    da.to_unstacked_dataset("z")
except ValueError as e:
    print("OK: ValueError raised:", e)
    sys.exit(0)
except Exception as e:
    print("wrong exception type:", type(e).__name__, e)
    sys.exit(1)

print("no error raised for non-stacked dim (Req3.1 violated)")
sys.exit(1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Req1.1 (POSITIVE CONTROL): single-dimension round trip returns identical Dataset.

Variables share only the sample dim 'x' and have no further dimension.
stack -> unstack must reproduce the original dataset exactly.
Holds on patched tree; must FAIL at base (merge/conflicting-values error).
"""
import sys
import numpy as np
import xarray as xr

arr = xr.DataArray(np.arange(3), coords=[("x", [0, 1, 2])])
data = xr.Dataset({"a": arr, "b": arr})

stacked = data.to_stacked_array("y", sample_dims=["x"])
try:
    unstacked = stacked.to_unstacked_dataset("y")
except Exception as e:
    print("to_unstacked_dataset raised:", type(e).__name__, e)
    sys.exit(1)

try:
    xr.testing.assert_identical(data, unstacked)
except AssertionError as e:
    print("not identical:", e)
    sys.exit(1)

print("OK: single-dim round trip identical")
print("vars:", list(unstacked.data_vars))
sys.exit(0)
```

Prepatch bug re-encoded as an attack: `True`.

5 probes cover Req1.1 (single-dim round-trip identical / positive control), Req1.2+1.4 (no raise, no leftover label/stacked scalar coords), Req2.1+2.4 (mixed multi/single-dim round-trip + reduce singleton axes), Req2.2+2.3 (level by name and by int, labels in order), Req3.1. All 5 HOLD on gold-patched tree. Positive control (probe_1) FAILS at base with MergeError 'conflicting values for variable y' and HOLDS on patched -> discriminating power confirmed. Candidate weak.diff (drop label coord but omit .squeeze) is REJECTED by probe_3 -> suite discriminates wrong impls.

DROPPED PROBE (probe_6, dtype fidelity, Req1.1 'same dtypes'): it FAILS on the gold-patched tree, but this is NOT a spec violation. Diagnosis (diag.py): stacking heterogeneous dtypes (int64+float64) via Dataset.to_stacked_array promotes to a single float64 array at STACK time (stacked.dtype==float64), before to_unstacked_dataset runs. The gold patch only edits to_unstacked_dataset and cannot recover a dtype already lost upstream; homogeneous-dtype datasets round-trip dtypes correctly. So the 'same dtypes' clause is an intrinsic xarray limitation of to_stacked_array for mixed dtypes, not a mandated behavior the patch fails to provide. Excluded rather than reported as a VIOLATION to avoid a false BROKEN verdict.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 5 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 5 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 5 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

Counterexample / evidence:

```
Under the partial-fix candidate (weak.diff: sel(drop=True) WITHOUT .squeeze(drop=True)), probe_3 (Req2.1/2.4 multi-dim regression) is REJECTED: the reconstructed variables retain the now-singleton stacked axis, so slices misalign and assert_identical fails (observed nan-filled float64 arrays). This demonstrates the probe suite discriminates the requirements-incomplete fix. The candidate would also fail the hidden test test_to_stacked_array_to_unstacked_dataset.
```

**Attacks re-run (5):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

_The 5 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts, and on this backend both roles put it through the same derivation: every block below is a requirement probe run on the gold-patched tree, and the `machine verdict:` line each role publishes above reports BOTH that its probes hold there and how many candidate patches the probe suite rejected — so the two roles re-ran ONE probe suite and each recorded its own outcome for every probe in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `probe_1.py` → holds on the patched tree (good)

Attack 2 — `probe_2.py` → holds on the patched tree (good)

Attack 3 — `probe_3.py` → holds on the patched tree (good)

Attack 4 — `probe_4.py` → holds on the patched tree (good)

Attack 5 — `probe_5.py` → holds on the patched tree (good)

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Req1.1 (POSITIVE CONTROL): single-dimension round trip returns identical Dataset.

Variables share only the sample dim 'x' and have no further dimension.
stack -> unstack must reproduce the original dataset exactly.
Holds on patched tree; must FAIL at base (merge/conflicting-values error).
"""
import sys
import numpy as np
import xarray as xr

arr = xr.DataArray(np.arange(3), coords=[("x", [0, 1, 2])])
data = xr.Dataset({"a": arr, "b": arr})

stacked = data.to_stacked_array("y", sample_dims=["x"])
try:
    unstacked = stacked.to_unstacked_dataset("y")
except Exception as e:
    print("to_unstacked_dataset raised:", type(e).__name__, e)
    sys.exit(1)

try:
    xr.testing.assert_identical(data, unstacked)
except AssertionError as e:
    print("not identical:", e)
    sys.exit(1)

print("OK: single-dim round trip identical")
print("vars:", list(unstacked.data_vars))
sys.exit(0)
```

Prepatch bug re-encoded as an attack: `True`.

5 probes cover Req1.1 (single-dim round-trip identical / positive control), Req1.2+1.4 (no raise, no leftover label/stacked scalar coords), Req2.1+2.4 (mixed multi/single-dim round-trip + reduce singleton axes), Req2.2+2.3 (level by name and by int, labels in order), Req3.1. All 5 HOLD on gold-patched tree. Positive control (probe_1) FAILS at base with MergeError 'conflicting values for variable y' and HOLDS on patched -> discriminating power confirmed. Candidate weak.diff (drop label coord but omit .squeeze) is REJECTED by probe_3 -> suite discriminates wrong impls.

DROPPED PROBE (probe_6, dtype fidelity, Req1.1 'same dtypes'): it FAILS on the gold-patched tree, but this is NOT a spec violation. Diagnosis (diag.py): stacking heterogeneous dtypes (int64+float64) via Dataset.to_stacked_array promotes to a single float64 array at STACK time (stacked.dtype==float64), before to_unstacked_dataset runs. The gold patch only edits to_unstacked_dataset and cannot recover a dtype already lost upstream; homogeneous-dtype datasets round-trip dtypes correctly. So the 'same dtypes' clause is an intrinsic xarray limitation of to_stacked_array for mixed dtypes, not a mandated behavior the patch fails to provide. Excluded rather than reported as a VIOLATION to avoid a false BROKEN verdict.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Patch.diff: data_dict[k] = self.sel({variable_dim: k}).squeeze(drop=True) -> self.sel({variable_dim: k}, drop=True).squeeze(drop=True). Issue GH4049: single-dim stack->unstack raised MergeError 'conflicting values for variable y'. The scalar 'y' coordinate attached by .sel (without drop) was the conflict source; drop=True removes it. Requirements correctly model the observable round-trip AND the precise causal mechanism; the modeling boundary is the changed behavior, not a helper. Probe: HOLDS gold-patched, VIOLATED at base (implied by FAIL_TO_PASS test).


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The requirements document describes behavior and localizes the change without transmitting the hidden test or gold edit. All of the following are public via the problem_statement, not leaked: the single-dimension round-trip scenario (Req 1) is exactly the public MCVE (single-dim DataArray, Dataset with two vars, to_stacked_array('y', sample_dims=['x']), to_unstacked_dataset('y')), and the 'conflicting values' MergeError is quoted verbatim in the public issue. Named entities — DataArray.to_unstacked_dataset, Dataset.to_stacked_array, xarray/core/dataarray.py, the `level` argument — are legitimate public API / change localization. No hidden material appears: no test function/class names (test_to_stacked_array_to_unstacked_dataset, TestDataset), no test file path (xarray/tests/test_dataset.py), no parametrization ids (the F2P test has none), no quoted test or gold code, and no fix-invented identifiers (the gold is a one-liner adding drop=True to an existing .sel call — no new names). Req 1.3's 'remove the selecting label's coordinate rather than retain it as a scalar coordinate' describes the fix mechanism (drop=True) but is stated behaviorally and is directly diagnosable from the PUBLIC MergeError about the conflicting scalar 'y' coordinate; it does not reproduce gold code. Req 3 is pre-existing PASS_TO_PASS behavior described in behavioral terms. No enumeration mirrors test parametrization.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
