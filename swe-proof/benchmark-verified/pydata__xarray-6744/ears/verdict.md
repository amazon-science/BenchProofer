# P2 adversarial audit — pydata__xarray-6744

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
"""Positive control: centered manual iteration mean == vectorized centered mean.
Encodes Requirement 1.2 / 6.1 (center=True). Must HOLD patched, FAIL at base."""
import numpy as np
import xarray as xr

fail = False
for n, w in [(10, 3), (10, 4), (8, 5), (7, 2)]:
    da = xr.DataArray(np.arange(n, dtype=float), dims="x", coords={"x": np.arange(n)})
    roll = da.rolling(x=w, center=True)
    vec = roll.mean()
    manual = []
    for label, window in roll:
        manual.append(float(window.mean()))
    manual = np.array(manual)
    ref = vec.values
    ok = np.allclose(manual, ref, equal_nan=True)
    print(f"n={n} w={w} center=True match={ok}")
    print("  manual:", manual)
    print("  vec   :", ref)
    if not ok:
        fail = True

if fail:
    print("MISMATCH: centered manual iteration != vectorized")
    raise SystemExit(1)
print("OK: centered manual == vectorized")
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""Requirement 1.1/1.3: exact centered window index bounds.
For center=True window w: end = i + (w+1)//2, begin = end - w clamped to 0,
end clamped to n. Check yielded window equals that exact slice of the source."""
import numpy as np
import xarray as xr

fail = False
for n, w in [(10, 3), (10, 4), (9, 5), (6, 2), (7, 6)]:
    da = xr.DataArray(np.arange(n, dtype=float), dims="x", coords={"x": np.arange(n)})
    roll = da.rolling(x=w, center=True, min_periods=1)  # min_periods=1 => no masking, isolate bounds
    for i, (label, window) in enumerate(roll):
        end = i + (w + 1) // 2
        begin = end - w
        if begin < 0:
            begin = 0
        end_c = min(end, n)
        expected = da.isel(x=slice(begin, end_c)).values
        got = window.values
        if not (len(got) == len(expected) and np.array_equal(got, expected)):
            print(f"n={n} w={w} i={i}: expected slice[{begin}:{end_c}]={expected} got={got}")
            fail = True
    print(f"n={n} w={w}: checked bounds")

if fail:
    print("BOUNDS MISMATCH")
    raise SystemExit(1)
print("OK: centered window bounds exact")
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""Requirement 2: non-centered iteration preserves right-anchored windows and
matches vectorized non-centered reduction. Window i = slice(max(0,i+1-w), i+1)."""
import numpy as np
import xarray as xr

fail = False
for n, w in [(10, 3), (8, 1), (7, 4), (6, 6)]:
    da = xr.DataArray(np.arange(n, dtype=float) + 0.5, dims="x", coords={"x": np.arange(n)})
    roll = da.rolling(x=w, center=False, min_periods=1)  # isolate bounds from masking
    vec = roll.mean().values
    manual = []
    for i, (label, window) in enumerate(roll):
        begin = max(0, i + 1 - w)
        end = i + 1
        expected = da.isel(x=slice(begin, end)).values
        if not np.array_equal(window.values, expected):
            print(f"n={n} w={w} i={i}: expected slice[{begin}:{end}]={expected} got={window.values}")
            fail = True
        manual.append(float(window.mean()))
    manual = np.array(manual)
    if not np.allclose(manual, vec, equal_nan=True):
        print(f"n={n} w={w}: manual mean {manual} != vec {vec}")
        fail = True
    print(f"n={n} w={w}: non-centered checked")

if fail:
    print("NON-CENTERED MISMATCH")
    raise SystemExit(1)
print("OK: non-centered right-anchored preserved")
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""Requirement 3: exactly n (label, window) pairs, labels = coord values in order,
each window contiguous along rolling dim, other dims unchanged."""
import numpy as np
import xarray as xr

fail = False
# 2-D data, roll over one dim; check other dim preserved.
n, w = 9, 4
coords_x = np.arange(100, 100 + n)
da = xr.DataArray(np.arange(n * 3, dtype=float).reshape(n, 3),
                  dims=("x", "y"), coords={"x": coords_x, "y": [0, 1, 2]})
for center in (True, False):
    roll = da.rolling(x=w, center=center)
    pairs = list(roll)
    if len(pairs) != n:
        print(f"center={center}: expected {n} pairs got {len(pairs)}")
        fail = True
    labels = [float(l) for (l, _) in pairs]
    if labels != [float(c) for c in coords_x]:
        print(f"center={center}: labels {labels} != coords {list(coords_x)}")
        fail = True
    for i, (l, window) in enumerate(pairs):
        if window.dims != ("x", "y") or window.sizes["y"] != 3:
            print(f"center={center} i={i}: other dim changed dims={window.dims} sizes={window.sizes}")
            fail = True
    print(f"center={center}: {len(pairs)} pairs, labels ok")

if fail:
    print("STRUCTURE MISMATCH")
    raise SystemExit(1)
print("OK: n pairs, labels, contiguous windows")
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""Requirement 4: min_periods mask applied per window, consistent with vectorized.
Requirement 5: multi-dim rolling iteration raises ValueError."""
import numpy as np
import xarray as xr

fail = False

# Req 4: min_periods
n, w, mp = 10, 3, 2
da = xr.DataArray(np.arange(n, dtype=float), dims="x", coords={"x": np.arange(n)})
for center in (True, False):
    roll = da.rolling(x=w, center=center, min_periods=mp)
    vec = roll.mean().values
    manual = []
    for label, window in roll:
        manual.append(float(window.mean()))
    manual = np.array(manual)
    if not np.allclose(manual, vec, equal_nan=True):
        print(f"min_periods center={center}: manual {manual} != vec {vec}")
        fail = True
    else:
        print(f"min_periods center={center}: manual matches vec (nan boundaries)")

# Req 5: multi-dim rolling must raise ValueError on iteration
da2 = xr.DataArray(np.arange(20, dtype=float).reshape(4, 5), dims=("a", "b"),
                   coords={"a": np.arange(4), "b": np.arange(5)})
roll2 = da2.rolling(a=2, b=2)
try:
    for _ in roll2:
        pass
    print("multi-dim rolling did NOT raise")
    fail = True
except ValueError as e:
    print(f"multi-dim raised ValueError: {e}")

if fail:
    print("MIN_PERIODS/MULTIDIM MISMATCH")
    raise SystemExit(1)
print("OK: min_periods mask + multi-dim ValueError")
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
"""Requirement 1.4: centered iteration holds for w=1 (each window single element
aligned with its position) and for window sizes larger than n."""
import numpy as np
import xarray as xr

fail = False

# w = 1, center=True: each window is single element at position i.
n, w = 6, 1
da = xr.DataArray(np.arange(n, dtype=float) * 10, dims="x", coords={"x": np.arange(n)})
roll = da.rolling(x=w, center=True)
for i, (label, window) in enumerate(roll):
    exp = da.isel(x=slice(i, i + 1)).values
    if not np.array_equal(window.values, exp):
        print(f"w=1 i={i}: got {window.values} exp {exp}")
        fail = True
vec = roll.mean().values
manual = np.array([float(win.mean()) for _, win in da.rolling(x=w, center=True)])
if not np.allclose(manual, vec, equal_nan=True):
    print(f"w=1: manual {manual} != vec {vec}")
    fail = True
print(f"w=1 checked")

# w > n, center=True
n, w = 4, 7
da = xr.DataArray(np.arange(n, dtype=float), dims="x", coords={"x": np.arange(n)})
roll = da.rolling(x=w, center=True)
vec = roll.mean().values
manual = np.array([float(win.mean()) for _, win in da.rolling(x=w, center=True)])
if not np.allclose(manual, vec, equal_nan=True):
    print(f"w>n: manual {manual} != vec {vec}")
    fail = True
print(f"w>n (w={w} n={n}) checked: manual {manual} vec {vec}")

if fail:
    print("W1/WGTN MISMATCH")
    raise SystemExit(1)
print("OK: w=1 and w>n centered behave")
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Positive control: centered manual iteration mean == vectorized centered mean.
Encodes Requirement 1.2 / 6.1 (center=True). Must HOLD patched, FAIL at base."""
import numpy as np
import xarray as xr

fail = False
for n, w in [(10, 3), (10, 4), (8, 5), (7, 2)]:
    da = xr.DataArray(np.arange(n, dtype=float), dims="x", coords={"x": np.arange(n)})
    roll = da.rolling(x=w, center=True)
    vec = roll.mean()
    manual = []
    for label, window in roll:
        manual.append(float(window.mean()))
    manual = np.array(manual)
    ref = vec.values
    ok = np.allclose(manual, ref, equal_nan=True)
    print(f"n={n} w={w} center=True match={ok}")
    print("  manual:", manual)
    print("  vec   :", ref)
    if not ok:
        fail = True

if fail:
    print("MISMATCH: centered manual iteration != vectorized")
    raise SystemExit(1)
print("OK: centered manual == vectorized")
```

Prepatch bug re-encoded as an attack: `True`.

Requirements: DataArrayRolling.__iter__ must honor `center` so manual iteration windows match the vectorized reduction, for centered/non-centered, all window sizes, with min_periods masking, dimension labels, and a ValueError for multi-dim rolling.

Probes (all HOLD on gold-patched tree):
- probe_1 (POSITIVE CONTROL, Req 1.2/6.1 center=True): manual-iteration mean == vectorized centered mean over n/w combos. HOLDS patched, FAILS at base (base yields right-anchored windows shifted off-center). prepatch_reproduced=true.
- probe_2 (Req 1.1/1.3): exact centered window index bounds end=i+(w+1)//2, begin clamped>=0, end clamped<=n; run with min_periods=1 to isolate bounds from masking. HOLDS patched.
- probe_3 (Req 2.1/2.2): non-centered right-anchored slice(max(0,i+1-w),i+1) preserved and mean matches vectorized (min_periods=1). HOLDS patched.
- probe_4 (Req 3.1/3.2/3.3): exactly n pairs, labels==coord values in order, contiguous windows with other dims unchanged (2-D data). HOLDS patched.
- probe_5 (Req 4 + Req 5): min_periods masking matches vectorized nan boundaries (center=True/False); multi-dim rolling iteration raises ValueError. HOLDS patched.
- probe_6 (Req 1.4): w=1 (single element aligned with position) and w>n centered behave, matching vectorized. HOLDS patched.

Initial probe_2/probe_3 versions falsely flagged because they compared raw windows against unmasked slices while the default min_periods=w masks short windows (Req 4) — corrected to min_periods=1; the patch was never at fault.

CANDIDATE PATCH (weak.diff): offset = w//2 (instead of gold's (w+1)//2) for the centered case — a plausible misreading of 'centered'. REJECTED by probe_1 (mean mismatch at even/odd windows), probe_2 (bounds off by one), and probe_6 (w=1 offset=0 collapses to empty/left-shifted windows). This demonstrates the suite discriminates wrong implementations.

Conclusion: >=5 distinct probes all hold on the patched tree, positive control discriminates (fails at base), and a probe-conforming-looking wrong fix is rejected. Verdict SOUND.

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
"""Positive control: centered manual iteration mean == vectorized centered mean.
Encodes Requirement 1.2 / 6.1 (center=True). Must HOLD patched, FAIL at base."""
import numpy as np
import xarray as xr

fail = False
for n, w in [(10, 3), (10, 4), (8, 5), (7, 2)]:
    da = xr.DataArray(np.arange(n, dtype=float), dims="x", coords={"x": np.arange(n)})
    roll = da.rolling(x=w, center=True)
    vec = roll.mean()
    manual = []
    for label, window in roll:
        manual.append(float(window.mean()))
    manual = np.array(manual)
    ref = vec.values
    ok = np.allclose(manual, ref, equal_nan=True)
    print(f"n={n} w={w} center=True match={ok}")
    print("  manual:", manual)
    print("  vec   :", ref)
    if not ok:
        fail = True

if fail:
    print("MISMATCH: centered manual iteration != vectorized")
    raise SystemExit(1)
print("OK: centered manual == vectorized")
```

Prepatch bug re-encoded as an attack: `True`.

Requirements: DataArrayRolling.__iter__ must honor `center` so manual iteration windows match the vectorized reduction, for centered/non-centered, all window sizes, with min_periods masking, dimension labels, and a ValueError for multi-dim rolling.

Probes (all HOLD on gold-patched tree):
- probe_1 (POSITIVE CONTROL, Req 1.2/6.1 center=True): manual-iteration mean == vectorized centered mean over n/w combos. HOLDS patched, FAILS at base (base yields right-anchored windows shifted off-center). prepatch_reproduced=true.
- probe_2 (Req 1.1/1.3): exact centered window index bounds end=i+(w+1)//2, begin clamped>=0, end clamped<=n; run with min_periods=1 to isolate bounds from masking. HOLDS patched.
- probe_3 (Req 2.1/2.2): non-centered right-anchored slice(max(0,i+1-w),i+1) preserved and mean matches vectorized (min_periods=1). HOLDS patched.
- probe_4 (Req 3.1/3.2/3.3): exactly n pairs, labels==coord values in order, contiguous windows with other dims unchanged (2-D data). HOLDS patched.
- probe_5 (Req 4 + Req 5): min_periods masking matches vectorized nan boundaries (center=True/False); multi-dim rolling iteration raises ValueError. HOLDS patched.
- probe_6 (Req 1.4): w=1 (single element aligned with position) and w>n centered behave, matching vectorized. HOLDS patched.

Initial probe_2/probe_3 versions falsely flagged because they compared raw windows against unmasked slices while the default min_periods=w masks short windows (Req 4) — corrected to min_periods=1; the patch was never at fault.

CANDIDATE PATCH (weak.diff): offset = w//2 (instead of gold's (w+1)//2) for the centered case — a plausible misreading of 'centered'. REJECTED by probe_1 (mean mismatch at even/odd windows), probe_2 (bounds off by one), and probe_6 (w=1 offset=0 collapses to empty/left-shifted windows). This demonstrates the suite discriminates wrong implementations.

Conclusion: >=5 distinct probes all hold on the patched tree, positive control discriminates (fails at base), and a probe-conforming-looking wrong fix is rejected. Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Verified on the instance image via nl_attack probe (gold-patched tree). Req1/2 index arithmetic: exact match for all tested (n,w,center) incl. w=1 and w>n. Req3: exactly n (label,window) pairs in ascending order; labels are the rolling-dim coordinate values. Req4: patch retains counts=window.count(dim); window=window.where(counts>=min_periods) — masking preserved (confirmed a leading centered window yielded NaN under min_periods). Req5: multi-dim rolling iteration raises ValueError('__iter__ is only supported for 1d-rolling'). Req6: manual-vs-vectorized reduction element-equal for all in-range cases; note vectorized reduction itself errors for w>n (bottleneck constraint), so Req6 is only meaningfully testable for w<=n, which the requirement's own scope ('through the vectorized rolling API') respects. Modeling boundary is the changed observable behavior (the full iterator window computation), not a narrow slice — faithful.

Counterexample / evidence:

```
N/A — no requirement disagrees with patched code.
```


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The requirements describe observable behavior, not hidden-test internals. Naming xarray/core/rolling.py, DataArrayRolling, __iter__, center, and min_periods is legitimate localization; the center/mean equivalence scenario is verbatim in the public problem_statement (Option 1 vs Option 2 example returning array([nan,2,...,nan]) vs [nan,nan,2,...]). Requirement 1.1's window geometry (ends ⌈w/2⌉ past i, i.e. (w+1)//2) matches the gold's `offset = (window0 + 1) // 2` but is the BEHAVIORAL definition of center-justification — the required observable slice at each position — not a transmission of test code. No test file path (xarray/tests/test_rolling.py), no test function/class name (TestDataArrayRolling::test_rolling_iter), and no parametrization ids (numpy-3-True-1, dask-*) appear. Req 1.4 cites w=1 and sizes>n as behavioral edge cases and does NOT enumerate the test's exact size set [1,2,3,7], so it is not mirroring the parametrization. Req 5 paraphrases the ValueError ('supported only for 1-D rolling') rather than quoting the code string. No fix-invented identifiers (offset/window0/stops/starts) leak. Req 6 restates the public issue scenario. No semantic reconstruction of the hidden tests.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
