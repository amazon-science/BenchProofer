# P2 adversarial audit — pydata__xarray-4075

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
"""Positive control. Req 1.2 & 2.2: boolean weights -> numeric count & correct mean.
MCVE: dta=[1,1,1], wgt(bool)=[1,1,0]. sum_of_weights==2 (not True), mean==1.
HOLDS on patched, FAILS at base."""
import numpy as np
import xarray as xr

dta = xr.DataArray([1.0, 1.0, 1.0])
wgt = xr.DataArray(np.array([1, 1, 0], dtype=bool))

sow = dta.weighted(wgt).sum_of_weights().values
mean = dta.weighted(wgt).mean().values
print("sum_of_weights =", repr(sow), "dtype", np.asarray(sow).dtype)
print("mean =", repr(mean))

ok = True
# must be numeric 2, not boolean True
if not (np.asarray(sow).dtype != np.bool_ and float(sow) == 2.0):
    print("FAIL: sum_of_weights not numeric 2")
    ok = False
if not np.isclose(float(mean), 1.0):
    print("FAIL: mean != 1.0")
    ok = False
print("RESULT", "PASS" if ok else "FAIL")
raise SystemExit(0 if ok else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""Req 1.4 / 6.3: reduce over a proper subset of dims with boolean weights ->
numeric count per remaining position."""
import numpy as np
import xarray as xr

data = xr.DataArray(np.ones((3, 4)), dims=("x", "y"))
wgt = xr.DataArray(np.array([[True, True, False, True],
                             [False, True, True, True],
                             [True, True, True, False]]), dims=("x", "y"))
sow = data.weighted(wgt).sum_of_weights(dim="y")
print("sum_of_weights over y =", sow.values, "dtype", sow.values.dtype)
expected = np.array([3.0, 3.0, 3.0])  # count of True per row
ok = sow.values.dtype != np.bool_ and np.allclose(sow.values, expected)
print("expected", expected)
print("RESULT", "PASS" if ok else "FAIL")
raise SystemExit(0 if ok else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""Req 2.3 / 4.4: boolean weights select no entries -> mean is NaN.
Also Req 4.2: sum_of_weights reports NaN (not 0) for zero total weight."""
import numpy as np
import xarray as xr

dta = xr.DataArray([1.0, 2.0, 3.0])
wgt = xr.DataArray(np.array([0, 0, 0], dtype=bool))
sow = dta.weighted(wgt).sum_of_weights().values
mean = dta.weighted(wgt).mean().values
print("sum_of_weights =", repr(sow))
print("mean =", repr(mean))
ok = np.isnan(float(sow)) and np.isnan(float(mean))
print("RESULT", "PASS" if ok else "FAIL")
raise SystemExit(0 if ok else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""Req 3: numeric-weight behavior preserved. Req 3.4: constant factor mean == unweighted mean.
Req 3.2: sum == sum(data*weights), mean == sum/sumweights."""
import numpy as np
import xarray as xr

dta = xr.DataArray([1.0, 2.0, 3.0, 4.0])
ok = True
for factor in (1, 3, 3.14):
    wgt = xr.DataArray(np.array([factor, factor, factor, factor], dtype=float))
    mean = float(dta.weighted(wgt).mean().values)
    if not np.isclose(mean, 2.5):
        print(f"FAIL: factor {factor} mean {mean} != 2.5")
        ok = False

# numeric int weights: sum_of_weights == sum weights over non-null
wgt = xr.DataArray(np.array([2, 3, 0, 1]))
sow = float(dta.weighted(wgt).sum_of_weights().values)
wsum = float(dta.weighted(wgt).sum().values)
mean = float(dta.weighted(wgt).mean().values)
exp_wsum = 1*2 + 2*3 + 3*0 + 4*1  # 16
exp_sow = 2+3+0+1  # 6
print("sow", sow, "wsum", wsum, "mean", mean)
if not (np.isclose(sow, exp_sow) and np.isclose(wsum, exp_wsum) and np.isclose(mean, exp_wsum/exp_sow)):
    print("FAIL numeric weights")
    ok = False
print("RESULT", "PASS" if ok else "FAIL")
raise SystemExit(0 if ok else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""Req 4.1 & 4.3: missing-value handling preserved with boolean weights.
NaN data entries excluded from sum_of_weights count; mean ignores them."""
import numpy as np
import xarray as xr

# data has a NaN at position where weight is True -> should not be counted
dta = xr.DataArray([1.0, np.nan, 3.0, 5.0])
wgt = xr.DataArray(np.array([True, True, True, False]))
sow = float(dta.weighted(wgt).sum_of_weights().values)
mean = float(dta.weighted(wgt).mean().values)
print("sum_of_weights =", sow, "(expect 2: pos0 and pos2 true+nonnull)")
print("mean =", mean, "(expect (1+3)/2 = 2.0)")
ok = np.isclose(sow, 2.0) and np.isclose(mean, 2.0)
print("RESULT", "PASS" if ok else "FAIL")
raise SystemExit(0 if ok else 1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
"""Req 5: input validation preserved. Non-DataArray weights -> ValueError.
NaN in weights -> ValueError."""
import numpy as np
import xarray as xr

dta = xr.DataArray([1.0, 2.0, 3.0])
ok = True

try:
    dta.weighted(np.array([1, 1, 1]))  # not a DataArray
    print("FAIL: non-DataArray weights did not raise")
    ok = False
except ValueError as e:
    print("OK non-DataArray -> ValueError:", e)

try:
    dta.weighted(xr.DataArray([1.0, np.nan, 1.0]))  # NaN in weights
    print("FAIL: NaN weights did not raise")
    ok = False
except ValueError as e:
    print("OK NaN weights -> ValueError:", e)

print("RESULT", "PASS" if ok else "FAIL")
raise SystemExit(0 if ok else 1)
```

Attack 7 — `probe_7.py` → holds on the patched tree (good)

```python
"""Req 6.1: boolean weights spanning a subset of data dims -> broadcast then contract.
data (x,y), weights only over x. sum_of_weights over x should count True over x per y."""
import numpy as np
import xarray as xr

data = xr.DataArray(np.ones((3, 2)), dims=("x", "y"))
wgt = xr.DataArray(np.array([True, False, True]), dims=("x",))
sow = data.weighted(wgt).sum_of_weights(dim="x")
mean = data.weighted(wgt).mean(dim="x")
print("sum_of_weights over x =", sow.values, "dtype", sow.values.dtype)
print("mean over x =", mean.values)
# 2 True along x, broadcast over y -> [2,2]; mean of ones -> [1,1]
ok = (sow.values.dtype != np.bool_ and np.allclose(sow.values, [2.0, 2.0])
      and np.allclose(mean.values, [1.0, 1.0]))
print("RESULT", "PASS" if ok else "FAIL")
raise SystemExit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Positive control. Req 1.2 & 2.2: boolean weights -> numeric count & correct mean.
MCVE: dta=[1,1,1], wgt(bool)=[1,1,0]. sum_of_weights==2 (not True), mean==1.
HOLDS on patched, FAILS at base."""
import numpy as np
import xarray as xr

dta = xr.DataArray([1.0, 1.0, 1.0])
wgt = xr.DataArray(np.array([1, 1, 0], dtype=bool))

sow = dta.weighted(wgt).sum_of_weights().values
mean = dta.weighted(wgt).mean().values
print("sum_of_weights =", repr(sow), "dtype", np.asarray(sow).dtype)
print("mean =", repr(mean))

ok = True
# must be numeric 2, not boolean True
if not (np.asarray(sow).dtype != np.bool_ and float(sow) == 2.0):
    print("FAIL: sum_of_weights not numeric 2")
    ok = False
if not np.isclose(float(mean), 1.0):
    print("FAIL: mean != 1.0")
    ok = False
print("RESULT", "PASS" if ok else "FAIL")
raise SystemExit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

7 probes cover Reqs 1-6. All HOLD on the gold-patched tree. Positive control (probe_1, the MCVE: bool weights [1,1,0] on data [1,1,1]) yields sum_of_weights=2.0 and mean=1.0 patched, but sum_of_weights=1.0(True) and mean=2.0 at base -> discriminates (prepatch reproduced). Probe coverage: probe_1 Req1.2/2.2 (numeric count & correct mean), probe_2 Req1.4/6.3 (subset-dim reduction counts), probe_3 Req2.3/4.2/4.4 (zero-weight -> NaN for both sum_of_weights and mean), probe_4 Req3.2/3.4 (numeric weights preserved; constant-factor mean == unweighted; sum==sum(data*weights)), probe_5 Req4.1/4.3 (NaN data excluded from bool count), probe_6 Req5.1/5.2 (validation: non-DataArray and NaN weights raise ValueError), probe_7 Req6.1 (bool weights spanning subset of dims broadcast then contract).

Candidate patch 'weak_astype_bool_noop' mirrors the gold patch structure but casts self.weights.astype(bool) instead of astype(int) -- a no-op keeping boolean arithmetic. It applies cleanly at base and is REJECTED by probes 1,2,5,7 (sum_of_weights stays boolean-collapsed=1, mean wrong), demonstrating the suite discriminates the lazy/wrong fix. Note on the recorded G-PANEL-2 fail: it claims Req1.3 mandates value==count==0 for the all-False case and that gold's NaN violates it, but Req1.3 explicitly states the zero-total case is governed by Req4.2 which mandates NaN, not 0. Gold's nan is therefore FAITHFUL to the requirements (confirmed by probe_3). The G-EQ (spec-too-weak) leg is sound: >=5 probes hold, positive control discriminates, and >=1 requirements-conforming-looking candidate is rejected.

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
"""Positive control. Req 1.2 & 2.2: boolean weights -> numeric count & correct mean.
MCVE: dta=[1,1,1], wgt(bool)=[1,1,0]. sum_of_weights==2 (not True), mean==1.
HOLDS on patched, FAILS at base."""
import numpy as np
import xarray as xr

dta = xr.DataArray([1.0, 1.0, 1.0])
wgt = xr.DataArray(np.array([1, 1, 0], dtype=bool))

sow = dta.weighted(wgt).sum_of_weights().values
mean = dta.weighted(wgt).mean().values
print("sum_of_weights =", repr(sow), "dtype", np.asarray(sow).dtype)
print("mean =", repr(mean))

ok = True
# must be numeric 2, not boolean True
if not (np.asarray(sow).dtype != np.bool_ and float(sow) == 2.0):
    print("FAIL: sum_of_weights not numeric 2")
    ok = False
if not np.isclose(float(mean), 1.0):
    print("FAIL: mean != 1.0")
    ok = False
print("RESULT", "PASS" if ok else "FAIL")
raise SystemExit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

7 probes cover Reqs 1-6. All HOLD on the gold-patched tree. Positive control (probe_1, the MCVE: bool weights [1,1,0] on data [1,1,1]) yields sum_of_weights=2.0 and mean=1.0 patched, but sum_of_weights=1.0(True) and mean=2.0 at base -> discriminates (prepatch reproduced). Probe coverage: probe_1 Req1.2/2.2 (numeric count & correct mean), probe_2 Req1.4/6.3 (subset-dim reduction counts), probe_3 Req2.3/4.2/4.4 (zero-weight -> NaN for both sum_of_weights and mean), probe_4 Req3.2/3.4 (numeric weights preserved; constant-factor mean == unweighted; sum==sum(data*weights)), probe_5 Req4.1/4.3 (NaN data excluded from bool count), probe_6 Req5.1/5.2 (validation: non-DataArray and NaN weights raise ValueError), probe_7 Req6.1 (bool weights spanning subset of dims broadcast then contract).

Candidate patch 'weak_astype_bool_noop' mirrors the gold patch structure but casts self.weights.astype(bool) instead of astype(int) -- a no-op keeping boolean arithmetic. It applies cleanly at base and is REJECTED by probes 1,2,5,7 (sum_of_weights stays boolean-collapsed=1, mean wrong), demonstrating the suite discriminates the lazy/wrong fix. Note on the recorded G-PANEL-2 fail: it claims Req1.3 mandates value==count==0 for the all-False case and that gold's NaN violates it, but Req1.3 explicitly states the zero-total case is governed by Req4.2 which mandates NaN, not 0. Gold's nan is therefore FAITHFUL to the requirements (confirmed by probe_3). The G-EQ (spec-too-weak) leg is sound: >=5 probes hold, positive control discriminates, and >=1 requirements-conforming-looking candidate is rejected.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Probe on gold-patched tree: sow bool two True=2.0 float64; mean bool=1.0; issue mean=1.0; sow all False=nan; sum bool=5.0; sow numeric=3.0. Requirements 1-6 (boolean count, correct mean normalization, numeric preservation, missing/zero-weight NaN, validation, multi-dim/shape) all describe behavior the patched code exhibits. Validation reqs (5.x) and alignment reqs (6.x) are pre-existing untouched behavior and correctly stated as 'preserved'. No divergence found.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The gold edit adds `.astype(int)` for boolean weights in `_sum_of_weights` (xarray/core/weighted.py); F2P tests are test_weighted_sum_of_weights_bool (da=[1,2], weights=[True,True]->2) and test_weighted_mean_bool (da=[1,1], weights=[True,True]->1), plus a large numeric/nan/3D/shape PASS_TO_PASS suite. The requirements.md names only legitimate localization targets (weighted.py, Weighted/DataArrayWeighted/DatasetWeighted, _reduce, sum_of_weights/sum/mean) — all fair. The concrete example values it cites ('two True weights SHALL yield 2, not True' and 'all equal 1 SHALL yield 1') are already public: the problem_statement's MCVE shows the boolean-dot-product returning True vs the corrected `xr.dot(dta.notnull(), wgt*1)` returning 2, and the mean example returning 1 vs 2. No fix-invented identifier (`.astype(int)`, `mask`, `valid_weights`) is surfaced. No test names, file paths, parametrization ids (factors 0/1/3.14, shape_weights/shape_data tuples, True/False skipna axes), or quoted test/gold code appear. Reqs 3-6 translate the PASS_TO_PASS preservation surface into general behavioral requirements (numeric weights unchanged, skipna, zero-weight->NaN, multi-dim/nonequal-coords/broadcast) without enumerating the specific parametrized cases, so they describe behavior rather than reconstruct the tests. No semantic leakage beyond the public problem statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
