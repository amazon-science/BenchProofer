# P2 adversarial audit — pydata__xarray-6599

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
# Positive control: Req 1.4 / 1.1
# polyval with timedelta64 coord and identity coeffs [0,1] must reproduce
# the elapsed-time magnitudes as floats. HOLDS patched, FAILS at base.
import sys
import numpy as np
import xarray as xr

x = xr.DataArray(
    np.array([1000, 2000, 3000], dtype="timedelta64[ns]"),
    dims="x",
)
coeffs = xr.DataArray([0, 1], dims="degree", coords={"degree": [0, 1]})
res = xr.polyval(x, coeffs)
got = np.asarray(res.values, dtype=float)
expected = np.array([1000.0, 2000.0, 3000.0])
print("got:", got)
print("expected:", expected)
ok = np.allclose(got, expected)
print("HOLDS" if ok else "VIOLATED")
sys.exit(0 if ok else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
# Req 1.1/1.2/1.3: _ensure_numeric on a timedelta64 DataArray returns
# float values equal to the array's underlying elapsed-time integer counts
# (xarray stores durations as its native resolution), floating dtype, no
# epoch offset, and does not raise.
import sys
import numpy as np
import xarray as xr
from xarray.core.computation import _ensure_numeric

da = xr.DataArray(np.array([1000, 2000, 3000], dtype="timedelta64[ns]"), dims="x")
# underlying integer counts of the stored representation
underlying = da.data.astype("int64").astype(float)
out = _ensure_numeric(da)
print("dtype:", out.dtype)
print("values:", out.values, "underlying:", underlying)
ok = out.dtype.kind == "f" and np.array_equal(np.asarray(out.values), underlying)

# A duration must NOT be reduced relative to any calendar epoch: a datetime
# path would subtract ~1970 epoch and change the magnitude drastically.
# The identity here is that output equals the raw int view exactly (offset 0).
ok = ok and np.asarray(out.values)[0] == underlying[0]  # no offset added
print("HOLDS" if ok else "VIOLATED")
sys.exit(0 if ok else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
# Req 2.1/2.2: datetime64 coords keep epoch-relative (1970-01-01, ns) coercion.
import sys
import numpy as np
import xarray as xr
from xarray.core.computation import _ensure_numeric

dates = np.array(["1970-01-01", "1970-01-02", "2000-01-01"], dtype="datetime64[ns]")
da = xr.DataArray(dates, dims="t")
out = _ensure_numeric(da)
print("dtype:", out.dtype)
print("values:", out.values)
# epoch-relative ns counts
expected = (dates - np.datetime64("1970-01-01", "ns")) / np.timedelta64(1, "ns")
print("expected:", expected)
ok = out.dtype.kind == "f" and np.allclose(np.asarray(out.values), expected)
print("HOLDS" if ok else "VIOLATED")
sys.exit(0 if ok else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
# Req 3.1/3.2: already-numeric passed through unchanged; Dataset applies
# per-variable rules (numeric unchanged, timedelta->float, datetime->epoch float).
import sys
import numpy as np
import xarray as xr
from xarray.core.computation import _ensure_numeric

# numeric DataArray unchanged
num = xr.DataArray(np.array([1.5, 2.5, 3.5]), dims="x")
outn = _ensure_numeric(num)
ok = outn.dtype == num.dtype and np.array_equal(outn.values, num.values)
print("numeric unchanged:", ok)

# int unchanged (not m/M)
inti = xr.DataArray(np.array([1, 2, 3]), dims="x")
outi = _ensure_numeric(inti)
ok = ok and outi.dtype == inti.dtype and np.array_equal(outi.values, inti.values)
print("int unchanged:", outi.dtype, outi.values)

# Dataset with mixed variables
ds = xr.Dataset(
    {
        "a": ("x", np.array([1000, 2000], dtype="timedelta64[ns]")),
        "b": ("x", np.array([2.0, 4.0])),
        "c": ("x", np.array(["1970-01-01", "1970-01-02"], dtype="datetime64[ns]")),
    }
)
outds = _ensure_numeric(ds)
print("ds a:", outds["a"].values, outds["a"].dtype)
print("ds b:", outds["b"].values, outds["b"].dtype)
print("ds c:", outds["c"].values, outds["c"].dtype)
ok = ok and isinstance(outds, xr.Dataset)
ok = ok and outds["a"].dtype.kind == "f" and np.allclose(outds["a"].values, [1000.0, 2000.0])
ok = ok and outds["b"].dtype == np.dtype(float) and np.array_equal(outds["b"].values, [2.0, 4.0])
ok = ok and outds["c"].dtype.kind == "f"
epoch = (np.array(["1970-01-01", "1970-01-02"], dtype="datetime64[ns]") - np.datetime64("1970-01-01", "ns")) / np.timedelta64(1, "ns")
ok = ok and np.allclose(outds["c"].values, epoch)
print("HOLDS" if ok else "VIOLATED")
sys.exit(0 if ok else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
# Req 4.1/4.2/4.5: numeric polyval regression — Horner, sparse/reordered
# degrees, coord label preservation, no degree dim retained.
import sys
import numpy as np
import xarray as xr

ok = True

# basic ascending
x = xr.DataArray([1.0, 2.0, 3.0], dims="x", coords={"x": [10, 20, 30]})
c = xr.DataArray([1.0, 2.0, 3.0], dims="degree", coords={"degree": [0, 1, 2]})
res = xr.polyval(x, c)
exp = 1 + 2 * x.values + 3 * x.values ** 2
print("basic:", res.values, exp)
ok = ok and np.allclose(res.values, exp)
ok = ok and "degree" not in res.dims
ok = ok and np.array_equal(res["x"].values, [10, 20, 30])

# reordered degree labels
c2 = xr.DataArray([3.0, 1.0, 2.0], dims="degree", coords={"degree": [2, 0, 1]})
res2 = xr.polyval(x, c2)
print("reordered:", res2.values, exp)
ok = ok and np.allclose(res2.values, exp)

# sparse / non-contiguous degrees: missing degrees treated as zero
c3 = xr.DataArray([2.0, 5.0], dims="degree", coords={"degree": [0, 2]})
res3 = xr.polyval(x, c3)
exp3 = 2 + 0 * x.values + 5 * x.values ** 2
print("sparse:", res3.values, exp3)
ok = ok and np.allclose(res3.values, exp3)

print("HOLDS" if ok else "VIOLATED")
sys.exit(0 if ok else 1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
# Req 4.3/4.4: polyval error handling.
# - degree_dim not a coordinate variable with labels -> ValueError
# - degree coordinate not integer dtype -> ValueError
import sys
import numpy as np
import xarray as xr

ok = True

x = xr.DataArray([1.0, 2.0, 3.0], dims="x")

# no degree coordinate labels
c_nolabel = xr.DataArray([1.0, 2.0], dims="degree")
try:
    xr.polyval(x, c_nolabel)
    print("no-label: NO error raised")
    ok = False
except ValueError as e:
    print("no-label ValueError:", e)

# non-integer degree coordinate
c_float = xr.DataArray([1.0, 2.0], dims="degree", coords={"degree": [0.0, 1.0]})
try:
    xr.polyval(x, c_float)
    print("float-degree: NO error raised")
    ok = False
except ValueError as e:
    print("float-degree ValueError:", e)

print("HOLDS" if ok else "VIOLATED")
sys.exit(0 if ok else 1)
```

Attack 7 — `probe_7.py` → holds on the patched tree (good)

```python
# Req 1.4 sharper: polyval over a timedelta coord equals the polynomial
# evaluated on the durations' float magnitudes (the stored int counts as float),
# for a quadratic. This distinguishes the correct raw-magnitude coercion from
# any epoch-reduced or otherwise offset coercion.
import sys
import numpy as np
import xarray as xr

x = xr.DataArray(np.array([1, 2, 3], dtype="timedelta64[ns]"), dims="x")
mags = x.data.astype("int64").astype(float)  # [1,2,3]
c = xr.DataArray([1.0, 2.0, 3.0], dims="degree", coords={"degree": [0, 1, 2]})
res = xr.polyval(x, c)
exp = 1 + 2 * mags + 3 * mags ** 2
print("got:", res.values, "expected:", exp)
ok = np.allclose(res.values, exp)
print("HOLDS" if ok else "VIOLATED")
sys.exit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
# Positive control: Req 1.4 / 1.1
# polyval with timedelta64 coord and identity coeffs [0,1] must reproduce
# the elapsed-time magnitudes as floats. HOLDS patched, FAILS at base.
import sys
import numpy as np
import xarray as xr

x = xr.DataArray(
    np.array([1000, 2000, 3000], dtype="timedelta64[ns]"),
    dims="x",
)
coeffs = xr.DataArray([0, 1], dims="degree", coords={"degree": [0, 1]})
res = xr.polyval(x, coeffs)
got = np.asarray(res.values, dtype=float)
expected = np.array([1000.0, 2000.0, 3000.0])
print("got:", got)
print("expected:", expected)
ok = np.allclose(got, expected)
print("HOLDS" if ok else "VIOLATED")
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance pydata__xarray-6599: split _ensure_numeric.to_floatable so datetime64 ('M') keeps datetime_to_numeric epoch-relative ns coercion and timedelta64 ('m') returns x.astype(float) (raw stored ns magnitude).

Probes (all HOLD on gold-patched tree):
- probe_1 (Req 1.4/1.1, POSITIVE CONTROL): polyval([1000,2000,3000] timedelta64[ns], coeffs [0,1]) == [1000,2000,3000]. HOLDS patched; at BASE raises _UFuncBinaryResolutionError (subtract m8 vs M8 epoch) -> discriminates.
- probe_2 (Req 1.1/1.2/1.3): _ensure_numeric on timedelta64 returns float dtype equal to underlying int ns counts, no epoch offset, no raise. HOLDS.
- probe_3 (Req 2.1/2.2): datetime64 coerced to epoch-relative (1970-01-01, ns) floats. HOLDS.
- probe_4 (Req 3.1/3.2): numeric/int DataArray unchanged; Dataset applies per-variable rules (timedelta->float, datetime->epoch float, numeric unchanged). HOLDS.
- probe_5 (Req 4.1/4.2/4.5): numeric polyval Horner, reordered + sparse/non-contiguous degrees, coord label preserved, degree dim dropped. HOLDS.
- probe_6 (Req 4.3/4.4): ValueError for missing degree coord labels and for non-integer degree dtype. HOLDS.
- probe_7 (Req 1.4): quadratic polyval over timedelta coord equals evaluation on float magnitudes (raw ns counts), excludes epoch-reduced/offset coercions. HOLDS.

Note: xarray stores durations in native ns resolution, so 'underlying elapsed-time counts' = stored int view; probes verify equality to that (offset 0).

Weak candidate (weak.diff): timedelta -> astype('timedelta64[s]').astype(float) — a plausibly-wrong fix that satisfies the 'float dtype, no epoch offset' surface reading but rescales magnitude. REJECTED by probe_1 (got [0,0,0]), probe_2 (values [0,0,0] vs underlying [1000,2000,3000]), probe_7 (got [1,1,1] vs [6,17,34]). Suite discriminates wrong implementations.

Verdict: 7 probes hold patched, positive control discriminates base vs patched, >=1 wrong candidate rejected. SOUND. (Independent of the G-PANEL-3 leakage concern in meta.json, which is a separate axis from spec-fidelity/too-weak.)

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
# Positive control: Req 1.4 / 1.1
# polyval with timedelta64 coord and identity coeffs [0,1] must reproduce
# the elapsed-time magnitudes as floats. HOLDS patched, FAILS at base.
import sys
import numpy as np
import xarray as xr

x = xr.DataArray(
    np.array([1000, 2000, 3000], dtype="timedelta64[ns]"),
    dims="x",
)
coeffs = xr.DataArray([0, 1], dims="degree", coords={"degree": [0, 1]})
res = xr.polyval(x, coeffs)
got = np.asarray(res.values, dtype=float)
expected = np.array([1000.0, 2000.0, 3000.0])
print("got:", got)
print("expected:", expected)
ok = np.allclose(got, expected)
print("HOLDS" if ok else "VIOLATED")
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance pydata__xarray-6599: split _ensure_numeric.to_floatable so datetime64 ('M') keeps datetime_to_numeric epoch-relative ns coercion and timedelta64 ('m') returns x.astype(float) (raw stored ns magnitude).

Probes (all HOLD on gold-patched tree):
- probe_1 (Req 1.4/1.1, POSITIVE CONTROL): polyval([1000,2000,3000] timedelta64[ns], coeffs [0,1]) == [1000,2000,3000]. HOLDS patched; at BASE raises _UFuncBinaryResolutionError (subtract m8 vs M8 epoch) -> discriminates.
- probe_2 (Req 1.1/1.2/1.3): _ensure_numeric on timedelta64 returns float dtype equal to underlying int ns counts, no epoch offset, no raise. HOLDS.
- probe_3 (Req 2.1/2.2): datetime64 coerced to epoch-relative (1970-01-01, ns) floats. HOLDS.
- probe_4 (Req 3.1/3.2): numeric/int DataArray unchanged; Dataset applies per-variable rules (timedelta->float, datetime->epoch float, numeric unchanged). HOLDS.
- probe_5 (Req 4.1/4.2/4.5): numeric polyval Horner, reordered + sparse/non-contiguous degrees, coord label preserved, degree dim dropped. HOLDS.
- probe_6 (Req 4.3/4.4): ValueError for missing degree coord labels and for non-integer degree dtype. HOLDS.
- probe_7 (Req 1.4): quadratic polyval over timedelta coord equals evaluation on float magnitudes (raw ns counts), excludes epoch-reduced/offset coercions. HOLDS.

Note: xarray stores durations in native ns resolution, so 'underlying elapsed-time counts' = stored int view; probes verify equality to that (offset 0).

Weak candidate (weak.diff): timedelta -> astype('timedelta64[s]').astype(float) — a plausibly-wrong fix that satisfies the 'float dtype, no epoch offset' surface reading but rescales magnitude. REJECTED by probe_1 (got [0,0,0]), probe_2 (values [0,0,0] vs underlying [1000,2000,3000]), probe_7 (got [1,1,1] vs [6,17,34]). Suite discriminates wrong implementations.

Verdict: 7 probes hold patched, positive control discriminates base vs patched, >=1 wrong candidate rejected. SOUND. (Independent of the G-PANEL-3 leakage concern in meta.json, which is a separate axis from spec-fidelity/too-weak.)

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Gold patch is a 3-line split of to_floatable's `x.dtype.kind in 'mM'` into `== 'M'` (datetime_to_numeric, unchanged) and `elif == 'm'` (x.astype(float), new). The requirements pin exactly this changed observable boundary across all three dtype branches biconditionally — correct modeling boundary, not a narrow slice or a leaf helper. Verified at both patched (HOLDS) and base commits via nl_attack probe. Note: bundle meta records G-PANEL-3 (leakage) as fail for reconstructing F2P test literals, but that is a separate concern from faithfulness; on the faithfulness axis the requirements are faithful.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Requirements name only pre-existing identifiers (computation.py, polyval, _ensure_numeric, to_floatable, datetime_to_numeric) — legitimate localization; to_floatable is modified, not invented, by the gold patch. No test names, file paths, parametrization ids, or verbatim test/gold code appear. The hidden-test literals (timedelta [1000,2000,3000] → [1000.0,2000.0,3000.0]) are not quoted. dtype kinds 'm'/'M', the 1970-01-01/ns epoch, and arbitrary degree order all appear in the public problem_statement MVCE/traceback or are standard xarray/NumPy semantics. Req 1.4's 'identity polynomial reproduces magnitudes' is a behavioral consequence of the coercion, not a value dump. BORDERLINE: Req 4.1-4.4's enumeration (broadcast/shared-dim/reordered/sparse/DataArray-vs-Dataset, missing-coord & non-integer ValueErrors) tracks the pre-existing PASS_TO_PASS test_polyval[...] and test_polyval_degree_dim_checks parametrization fairly closely — this is the 'enumeration mirroring parametrized cases' shape — but it describes the general public polyval contract for regression protection rather than reconstructing the timedelta fix's hidden test, so it stays on the legitimate side of behavioral translation.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
