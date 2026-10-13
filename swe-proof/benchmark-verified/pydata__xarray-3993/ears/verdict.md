# P2 adversarial audit — pydata__xarray-3993

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
"""Positive control: Req1.1/1.3 — DataArray.integrate accepts `coord` keyword
and returns the correct trapezoidal integral. Must FAIL at base (no `coord`
param there)."""
import sys
import numpy as np
import xarray as xr

da = xr.DataArray(
    np.array([[0.0, 1.0, 2.0, 3.0], [10.0, 11.0, 12.0, 13.0]]),
    dims=["y", "x"],
    coords={"x": [0.0, 0.1, 1.1, 1.2]},
)
try:
    out = da.integrate(coord="x")
except TypeError as e:
    print("FAIL: coord keyword not accepted:", e)
    sys.exit(1)

expected = np.trapz(da.values, da["x"].values, axis=1)
got = out.values
print("coord=x integrate ->", got, "expected", expected)
if not np.allclose(got, expected):
    print("FAIL: wrong integral")
    sys.exit(1)
if "x" in out.dims:
    print("FAIL: x dim not reduced")
    sys.exit(1)
print("PASS")
sys.exit(0)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""Req1.2/1.4 — positional coord works AND no deprecation warning when using
the consistent name (positional or keyword) with no deprecated selector."""
import sys, warnings
import numpy as np
import xarray as xr

da = xr.DataArray(
    np.array([1.0, 2.0, 4.0, 8.0]),
    dims=["x"],
    coords={"x": [0.0, 1.0, 2.0, 3.0]},
)
expected = np.trapz(da.values, da["x"].values)

# positional
with warnings.catch_warnings(record=True) as w:
    warnings.simplefilter("always")
    out_pos = da.integrate("x")
    warns_pos = [x for x in w if issubclass(x.category, (FutureWarning, DeprecationWarning))]
print("positional ->", float(out_pos.values), "warns:", [str(x.message) for x in warns_pos])
if not np.allclose(float(out_pos.values), expected):
    print("FAIL: positional wrong result"); sys.exit(1)
if warns_pos:
    print("FAIL: unexpected deprecation warning for positional coord"); sys.exit(1)

# keyword
with warnings.catch_warnings(record=True) as w:
    warnings.simplefilter("always")
    out_kw = da.integrate(coord="x")
    warns_kw = [x for x in w if issubclass(x.category, (FutureWarning, DeprecationWarning))]
if warns_kw:
    print("FAIL: unexpected deprecation warning for coord kwarg"); sys.exit(1)
print("PASS")
sys.exit(0)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""Req2 — deprecated `dim` keyword still honored, gives same result as `coord`,
and emits a FutureWarning."""
import sys, warnings
import numpy as np
import xarray as xr

da = xr.DataArray(
    np.array([1.0, 2.0, 4.0, 8.0]),
    dims=["x"],
    coords={"x": [0.0, 1.0, 2.0, 3.0]},
)
expected = float(da.integrate(coord="x").values)

with warnings.catch_warnings(record=True) as w:
    warnings.simplefilter("always")
    out = da.integrate(dim="x")
    fw = [x for x in w if issubclass(x.category, FutureWarning)]
got = float(out.values)
print("dim=x ->", got, "expected", expected, "FutureWarnings:", [str(x.message) for x in fw])
if not np.allclose(got, expected):
    print("FAIL: dim result differs from coord result"); sys.exit(1)
if not fw:
    print("FAIL: no FutureWarning emitted for deprecated dim"); sys.exit(1)
print("PASS")
sys.exit(0)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""Req3 — supplying BOTH coord and dim raises ValueError and does NOT emit the
FutureWarning in place of raising (error takes precedence)."""
import sys, warnings
import numpy as np
import xarray as xr

da = xr.DataArray(
    np.array([1.0, 2.0, 4.0, 8.0]),
    dims=["x"],
    coords={"x": [0.0, 1.0, 2.0, 3.0]},
)
with warnings.catch_warnings(record=True) as w:
    warnings.simplefilter("always")
    try:
        da.integrate(coord="x", dim="x")
    except ValueError as e:
        print("raised ValueError:", e)
        fw = [x for x in w if issubclass(x.category, FutureWarning)]
        if fw:
            print("FAIL: FutureWarning emitted despite error"); sys.exit(1)
        print("PASS"); sys.exit(0)
    except Exception as e:
        print("FAIL: wrong exception type:", type(e).__name__, e); sys.exit(1)
print("FAIL: no error raised for contradictory selectors"); sys.exit(1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""Req4.3 — multi-dimensional coordinate (not valid 1-D) raises ValueError.
Preserves existing validation."""
import sys
import numpy as np
import xarray as xr

# 2-D coordinate 'xy'
da = xr.DataArray(
    np.arange(6.0).reshape(2, 3),
    dims=["a", "b"],
    coords={"xy": (("a", "b"), np.arange(6.0).reshape(2, 3))},
)
try:
    da.integrate(coord="xy")
except ValueError as e:
    print("PASS: ValueError for multidim coord:", e); sys.exit(0)
except Exception as e:
    print("FAIL: wrong exception:", type(e).__name__, e); sys.exit(1)
print("FAIL: no error for multidim coord"); sys.exit(1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
"""Req4.4/4.5 — Dataset.integrate unchanged: still accepts coord, returns
correct integrated Dataset, no deprecation warning."""
import sys, warnings
import numpy as np
import xarray as xr

ds = xr.Dataset(
    {"v": (("x",), np.array([1.0, 2.0, 4.0, 8.0]))},
    coords={"x": [0.0, 1.0, 2.0, 3.0]},
)
expected = np.trapz(ds["v"].values, ds["x"].values)
with warnings.catch_warnings(record=True) as w:
    warnings.simplefilter("always")
    out = ds.integrate("x")
    dw = [x for x in w if issubclass(x.category, (FutureWarning, DeprecationWarning))]
got = float(out["v"].values)
print("Dataset.integrate('x') v ->", got, "expected", expected)
if not isinstance(out, xr.Dataset):
    print("FAIL: not a Dataset"); sys.exit(1)
if not np.allclose(got, expected):
    print("FAIL: wrong Dataset integral"); sys.exit(1)
if dw:
    print("FAIL: Dataset.integrate emitted deprecation warning:", [str(x.message) for x in dw]); sys.exit(1)
# also keyword coord still works
out2 = ds.integrate(coord="x")
if not np.allclose(float(out2["v"].values), expected):
    print("FAIL: Dataset coord kwarg wrong"); sys.exit(1)
print("PASS")
sys.exit(0)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Positive control: Req1.1/1.3 — DataArray.integrate accepts `coord` keyword
and returns the correct trapezoidal integral. Must FAIL at base (no `coord`
param there)."""
import sys
import numpy as np
import xarray as xr

da = xr.DataArray(
    np.array([[0.0, 1.0, 2.0, 3.0], [10.0, 11.0, 12.0, 13.0]]),
    dims=["y", "x"],
    coords={"x": [0.0, 0.1, 1.1, 1.2]},
)
try:
    out = da.integrate(coord="x")
except TypeError as e:
    print("FAIL: coord keyword not accepted:", e)
    sys.exit(1)

expected = np.trapz(da.values, da["x"].values, axis=1)
got = out.values
print("coord=x integrate ->", got, "expected", expected)
if not np.allclose(got, expected):
    print("FAIL: wrong integral")
    sys.exit(1)
if "x" in out.dims:
    print("FAIL: x dim not reduced")
    sys.exit(1)
print("PASS")
sys.exit(0)
```

Prepatch bug re-encoded as an attack: `True`.

6 probes, all HOLD on gold-patched tree. Coverage: probe_1 (Req1.1/1.3 coord kwarg + correct trapezoid, POSITIVE CONTROL: fails at base with TypeError 'coord'); probe_2 (Req1.2/1.4 positional coord + no dep warning); probe_3 (Req2.1-2.4 deprecated dim honored, same result, FutureWarning); probe_4 (Req3.1-3.2 both selectors -> ValueError, no FutureWarning); probe_5 (Req4.3 multidim coord -> ValueError); probe_6 (Req4.4/4.5 Dataset.integrate unchanged, no warning). Positive control probe_1 FAILS at base ('coord' kwarg unknown) -> prepatch reproduced. Probes 2 and 3 also fail at base. Wrong-fix candidate weak.diff (naive rename dim->coord, dropping deprecation + contradiction handling) is REJECTED by probe_3 (dim kwarg no longer accepted -> violates Req2) and probe_4 (contradiction case -> TypeError not ValueError, violates Req3), while probes 1,2,5,6 still hold. Suite discriminates a plausibly-wrong implementation; no probe-conforming weak patch found. Requirements are faithful to the gold patch.

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
"""Positive control: Req1.1/1.3 — DataArray.integrate accepts `coord` keyword
and returns the correct trapezoidal integral. Must FAIL at base (no `coord`
param there)."""
import sys
import numpy as np
import xarray as xr

da = xr.DataArray(
    np.array([[0.0, 1.0, 2.0, 3.0], [10.0, 11.0, 12.0, 13.0]]),
    dims=["y", "x"],
    coords={"x": [0.0, 0.1, 1.1, 1.2]},
)
try:
    out = da.integrate(coord="x")
except TypeError as e:
    print("FAIL: coord keyword not accepted:", e)
    sys.exit(1)

expected = np.trapz(da.values, da["x"].values, axis=1)
got = out.values
print("coord=x integrate ->", got, "expected", expected)
if not np.allclose(got, expected):
    print("FAIL: wrong integral")
    sys.exit(1)
if "x" in out.dims:
    print("FAIL: x dim not reduced")
    sys.exit(1)
print("PASS")
sys.exit(0)
```

Prepatch bug re-encoded as an attack: `True`.

6 probes, all HOLD on gold-patched tree. Coverage: probe_1 (Req1.1/1.3 coord kwarg + correct trapezoid, POSITIVE CONTROL: fails at base with TypeError 'coord'); probe_2 (Req1.2/1.4 positional coord + no dep warning); probe_3 (Req2.1-2.4 deprecated dim honored, same result, FutureWarning); probe_4 (Req3.1-3.2 both selectors -> ValueError, no FutureWarning); probe_5 (Req4.3 multidim coord -> ValueError); probe_6 (Req4.4/4.5 Dataset.integrate unchanged, no warning). Positive control probe_1 FAILS at base ('coord' kwarg unknown) -> prepatch reproduced. Probes 2 and 3 also fail at base. Wrong-fix candidate weak.diff (naive rename dim->coord, dropping deprecation + contradiction handling) is REJECTED by probe_3 (dim kwarg no longer accepted -> violates Req2) and probe_4 (contradiction case -> TypeError not ValueError, violates Req3), while probes 1,2,5,6 still hold. Suite discriminates a plausibly-wrong implementation; no probe-conforming weak patch found. Requirements are faithful to the gold patch.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** The patch renames the primary selector of DataArray.integrate from 'dim' to 'coord' with a keyword-only 'dim' deprecation alias: raises ValueError if both non-None, else if dim given aliases to coord and warns FutureWarning, then delegates unchanged to Dataset.integrate. Requirements pin exactly this observable behavior (accept coord positional/keyword, no warning for coord, deprecation warning + correct result for dim, error on both, unchanged trapezoidal computation and multi-dim validation, Dataset.integrate unchanged). The modeling boundary is the changed DataArray.integrate signature/dispatch behavior — correct, not a narrow slice or invented behavior. Probe HOLDS on patched tree (exit 0, ALL OK).


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The dim→coord rename, the sibling differentiate(coord=), and the deprecation-cycle question are all explicit in the public problem_statement, so naming coord/dim and localizing to DataArray.integrate/Dataset.integrate is legitimate. No hidden-test artifacts leak: no test paths/function names (test_dataset.py::test_integrate, test_units.py), no parametrization ids ([True]/[False], dask), no quoted test or gold code, and the gold-invented literal version '0.19.0' is deliberately abstracted to 'a future release'. The one matching identifier, `FutureWarning` (Req 2.3), plus the ValueError-on-both requirement (Req 3, which isn't even in the visible test_patch), are observable-behavior descriptions — a warning class and an exception type are standard behavioral specifications, exactly the kind of test-intent-to-requirement translation the task permits, not transmission of the tests themselves. The exact gold warning message string is NOT reproduced (spec paraphrases via 'consistent name'/'deprecated selector name').


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
