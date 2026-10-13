# P2 adversarial audit — pydata__xarray-3305

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
Naive candidate (weak.diff) makes Variable.quantile ALWAYS copy self._attrs (ignoring the keep_attrs request). Rejected by probe_2 (keep_attrs=False still carried {'units':'K'}), probe_3 (default/unspecified did not drop attrs; global-option resolution bypassed), and probe_4 (Dataset var 'a' attrs not dropped when keep_attrs=False). Demonstrates the probe suite discriminates the too-weak reading that satisfies only the keep=True criteria.
```

**Attacks re-run (5):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
"""R3.1 (positive control): DataArray.quantile(keep_attrs=True) preserves attrs.
Holds on patched, fails at base."""
import sys
import numpy as np
import xarray as xr

da = xr.DataArray(np.arange(12.0).reshape(3, 4), dims=("x", "y"),
                  attrs={"units": "K", "foo": "bar"})
res = da.quantile(0.9, dim="x", keep_attrs=True)
print("result attrs:", dict(res.attrs))
if dict(res.attrs) != {"units": "K", "foo": "bar"}:
    print("FAIL: attrs not preserved")
    sys.exit(1)
print("PASS")
sys.exit(0)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""R1.2/R1.3/R1.1: Variable.quantile accepts keep_attrs and honors True/False."""
import sys
import numpy as np
import xarray as xr
from xarray.core.variable import Variable

v = Variable(("x", "y"), np.arange(12.0).reshape(3, 4), attrs={"units": "K"})

# keep_attrs=True -> attrs equal to source
r_true = v.quantile(0.5, dim="x", keep_attrs=True)
print("keep_attrs=True attrs:", dict(r_true.attrs))
if dict(r_true.attrs) != {"units": "K"}:
    print("FAIL: True did not preserve attrs")
    sys.exit(1)

# keep_attrs=False -> no attrs
r_false = v.quantile(0.5, dim="x", keep_attrs=False)
print("keep_attrs=False attrs:", dict(r_false.attrs))
if dict(r_false.attrs) != {}:
    print("FAIL: False carried attrs")
    sys.exit(1)

print("PASS")
sys.exit(0)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""R1.4 / R4.4: Variable.quantile with keep_attrs unspecified defaults to dropping,
but follows the global set_options(keep_attrs=True)."""
import sys
import numpy as np
import xarray as xr
from xarray.core.variable import Variable

v = Variable(("x", "y"), np.arange(12.0).reshape(3, 4), attrs={"units": "K"})

# default (unspecified) -> drop
r_default = v.quantile(0.5, dim="x")
print("default attrs:", dict(r_default.attrs))
if dict(r_default.attrs) != {}:
    print("FAIL: default did not drop attrs")
    sys.exit(1)

# global option True + unspecified -> keep
with xr.set_options(keep_attrs=True):
    r_global = v.quantile(0.5, dim="x")
print("global keep_attrs=True attrs:", dict(r_global.attrs))
if dict(r_global.attrs) != {"units": "K"}:
    print("FAIL: global keep_attrs not honored")
    sys.exit(1)

print("PASS")
sys.exit(0)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""R2.1/R2.2/R2.3: Dataset.quantile forwards keep_attrs to each data variable."""
import sys
import numpy as np
import xarray as xr

ds = xr.Dataset(
    {"a": (("x", "y"), np.arange(12.0).reshape(3, 4), {"units": "K"}),
     "b": (("x",), np.arange(3.0), {"long_name": "bee"})},
    attrs={"title": "t"},
)

# keep_attrs=True -> each reduced variable keeps its attrs
r_true = ds.quantile(0.5, dim="x", keep_attrs=True)
print("a attrs (True):", dict(r_true["a"].attrs))
print("b attrs (True):", dict(r_true["b"].attrs))
print("ds attrs (True):", dict(r_true.attrs))
if dict(r_true["a"].attrs) != {"units": "K"}:
    print("FAIL: var a attrs not kept")
    sys.exit(1)
if dict(r_true["b"].attrs) != {"long_name": "bee"}:
    print("FAIL: var b attrs not kept")
    sys.exit(1)
# R2.4: dataset-level attrs kept when True
if dict(r_true.attrs) != {"title": "t"}:
    print("FAIL: dataset attrs not kept")
    sys.exit(1)

# keep_attrs=False -> variables carry no attrs, dataset attrs dropped
r_false = ds.quantile(0.5, dim="x", keep_attrs=False)
print("a attrs (False):", dict(r_false["a"].attrs))
print("ds attrs (False):", dict(r_false.attrs))
if dict(r_false["a"].attrs) != {}:
    print("FAIL: var a attrs not dropped")
    sys.exit(1)
if dict(r_false.attrs) != {}:
    print("FAIL: dataset attrs not dropped")
    sys.exit(1)

print("PASS")
sys.exit(0)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""R1.5/R3.3/R4.1/R4.2: attribute-keeping choice does NOT change quantile values,
dims, or the leading-quantile-dimension behavior."""
import sys
import numpy as np
import xarray as xr

data = np.array([[0.0, 1, 2, 3], [4, 5, 6, 7], [8, 9, 10, 11]])
da = xr.DataArray(data, dims=("x", "y"), attrs={"units": "K"})

# single scalar quantile -> no quantile dim, values match nanpercentile
r1 = da.quantile(0.9, dim="x", interpolation="linear", keep_attrs=True)
r1b = da.quantile(0.9, dim="x", interpolation="linear", keep_attrs=False)
expected1 = np.nanpercentile(data, 90.0, axis=0, interpolation="linear")
print("r1 dims:", r1.dims, "values:", r1.values)
if "quantile" in r1.dims:
    print("FAIL: scalar q added quantile dim")
    sys.exit(1)
if not np.allclose(r1.values, expected1):
    print("FAIL: r1 values mismatch")
    sys.exit(1)
# values identical regardless of keep_attrs
if not np.allclose(r1.values, r1b.values) or r1.dims != r1b.dims:
    print("FAIL: keep_attrs changed values/dims")
    sys.exit(1)

# multiple quantiles -> leading quantile dim
r2 = da.quantile([0.25, 0.75], dim="x", keep_attrs=True)
expected2 = np.nanpercentile(data, [25.0, 75.0], axis=0, interpolation="linear")
print("r2 dims:", r2.dims, "shape:", r2.shape)
if r2.dims[0] != "quantile":
    print("FAIL: multi q did not add leading quantile dim")
    sys.exit(1)
if not np.allclose(r2.values, expected2):
    print("FAIL: r2 values mismatch")
    sys.exit(1)

print("PASS")
sys.exit(0)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""R3.1 (positive control): DataArray.quantile(keep_attrs=True) preserves attrs.
Holds on patched, fails at base."""
import sys
import numpy as np
import xarray as xr

da = xr.DataArray(np.arange(12.0).reshape(3, 4), dims=("x", "y"),
                  attrs={"units": "K", "foo": "bar"})
res = da.quantile(0.9, dim="x", keep_attrs=True)
print("result attrs:", dict(res.attrs))
if dict(res.attrs) != {"units": "K", "foo": "bar"}:
    print("FAIL: attrs not preserved")
    sys.exit(1)
print("PASS")
sys.exit(0)
```

Prepatch bug re-encoded as an attack: `True`.

Requirements: honor keep_attrs in Variable/Dataset/DataArray.quantile. Gold patch touches variable.py (adds keep_attrs param + _get_keep_attrs(default=False) resolution) and dataset.py (forwards keep_attrs). DataArray.quantile already forwarded keep_attrs at base.

Probes (all HOLD on patched tree; exit 0):
- probe_1 [R3.1, POSITIVE CONTROL]: DataArray.quantile(0.9, dim='x', keep_attrs=True) preserves attrs. Patched: attrs={'units','foo'} PASS. Base: attrs={} FAIL -> prepatch reproduced, discriminates.
- probe_2 [R1.1/R1.2/R1.3]: Variable.quantile accepts keep_attrs; True->source attrs, False->no attrs. Patched PASS.
- probe_3 [R1.4/R4.4]: unspecified defaults to drop; set_options(keep_attrs=True) makes unspecified keep. Patched PASS.
- probe_4 [R2.1/R2.2/R2.3/R2.4]: Dataset.quantile forwards keep_attrs per-variable; True keeps var+dataset attrs, False drops both. Patched PASS.
- probe_5 [R1.5/R3.3/R4.1/R4.2]: attr choice does not change values/dims; scalar q adds no quantile dim, multi-q adds leading 'quantile' dim; values match np.nanpercentile. Patched PASS.

Candidate patch exercised: weak.diff (naive always-keep). REJECTED by probes 2,3,4; passed 1,5. Suite discriminates a wrong implementation -> not too weak.

Verdict: SOUND. 5 distinct probes all hold on patched; positive control fails at base and holds patched; a probe-conforming-only wrong reading is rejected.

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
Naive candidate (weak.diff) makes Variable.quantile ALWAYS copy self._attrs (ignoring the keep_attrs request). Rejected by probe_2 (keep_attrs=False still carried {'units':'K'}), probe_3 (default/unspecified did not drop attrs; global-option resolution bypassed), and probe_4 (Dataset var 'a' attrs not dropped when keep_attrs=False). Demonstrates the probe suite discriminates the too-weak reading that satisfies only the keep=True criteria.
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
"""R3.1 (positive control): DataArray.quantile(keep_attrs=True) preserves attrs.
Holds on patched, fails at base."""
import sys
import numpy as np
import xarray as xr

da = xr.DataArray(np.arange(12.0).reshape(3, 4), dims=("x", "y"),
                  attrs={"units": "K", "foo": "bar"})
res = da.quantile(0.9, dim="x", keep_attrs=True)
print("result attrs:", dict(res.attrs))
if dict(res.attrs) != {"units": "K", "foo": "bar"}:
    print("FAIL: attrs not preserved")
    sys.exit(1)
print("PASS")
sys.exit(0)
```

Prepatch bug re-encoded as an attack: `True`.

Requirements: honor keep_attrs in Variable/Dataset/DataArray.quantile. Gold patch touches variable.py (adds keep_attrs param + _get_keep_attrs(default=False) resolution) and dataset.py (forwards keep_attrs). DataArray.quantile already forwarded keep_attrs at base.

Probes (all HOLD on patched tree; exit 0):
- probe_1 [R3.1, POSITIVE CONTROL]: DataArray.quantile(0.9, dim='x', keep_attrs=True) preserves attrs. Patched: attrs={'units','foo'} PASS. Base: attrs={} FAIL -> prepatch reproduced, discriminates.
- probe_2 [R1.1/R1.2/R1.3]: Variable.quantile accepts keep_attrs; True->source attrs, False->no attrs. Patched PASS.
- probe_3 [R1.4/R4.4]: unspecified defaults to drop; set_options(keep_attrs=True) makes unspecified keep. Patched PASS.
- probe_4 [R2.1/R2.2/R2.3/R2.4]: Dataset.quantile forwards keep_attrs per-variable; True keeps var+dataset attrs, False drops both. Patched PASS.
- probe_5 [R1.5/R3.3/R4.1/R4.2]: attr choice does not change values/dims; scalar q adds no quantile dim, multi-q adds leading 'quantile' dim; values match np.nanpercentile. Patched PASS.

Candidate patch exercised: weak.diff (naive always-keep). REJECTED by probes 2,3,4; passed 1,5. Suite discriminates a wrong implementation -> not too weak.

Verdict: SOUND. 5 distinct probes all hold on patched; positive control fails at base and holds patched; a probe-conforming-only wrong reading is rejected.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Probe probe.py returned ALL_OK on patched tree; base.py confirmed pre-patch bug. Modeling boundary is correct: requirements cover the full observable behavior change across all three layers (Variable/Dataset/DataArray) plus the None->global-option resolution, matching the patch's threading of keep_attrs down to Variable.quantile with _get_keep_attrs(default=False).


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The requirements describe behavior and localize the change to Variable.quantile (variable.py), Dataset.quantile (dataset.py), DataArray.quantile (dataarray.py) — all of which is legitimate localization (naming modules/functions is explicitly permitted). The gold patch touches variable.py and dataset.py; naming those is fine. No test names/paths/ids are transmitted: the doc never mentions test_dataarray.py, TestDataArray, or test_quantile. No verbatim gold lines are quoted; the `_get_keep_attrs(default=False)` resolution rule is paraphrased in prose ('fall back to the library's global keep_attrs option, whose effective default is to drop attributes') rather than quoted as an identifier. The keep_attrs parameter name is public (it appears in the problem_statement's MCVE). Req 4.2's single-vs-multiple-quantile dimension rule is genuine documented xarray behavior (also in the gold's own docstring), not a mirror of the test's q parametrization ([0.25,[0.50],[0.25,0.75]]) — the doc gives no specific q values, interpolation ids, or axis/dim enumerations. Translating what the FAIL_TO_PASS test checks (keep_attrs=True preserves attrs; values unchanged) into behavioral requirements is exactly the intended purpose. No reconstruction of the hidden tests.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
