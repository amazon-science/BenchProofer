# P2 adversarial audit — pydata__xarray-4695

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 6 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 6 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 6 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_5.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (6):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
import sys
import numpy as np
import xarray as xr

# R1.2/R1.3: dimension named "method" must be selected as a dimension, not consumed
# as the sel() matching parameter; must NOT raise "Invalid fill method".
da = xr.DataArray(
    np.arange(6).reshape(2, 3),
    dims=["dim1", "method"],
    coords={"dim1": ["x", "y"], "method": ["a", "b", "c"]},
)
try:
    res = da.loc[dict(dim1="x", method="b")]
except Exception as e:
    print("FAIL: raised", type(e).__name__, e)
    sys.exit(1)
val = int(res.values)
print("selected value:", val, "coords:", res.coords.get("dim1").item(), res.coords.get("method").item())
# da[dim1=x row=0], method=b -> col1 -> value 1
if val != 1:
    print("FAIL: wrong value")
    sys.exit(1)
print("PASS R1.2/R1.3: dimension named 'method' selected correctly, no fill-method error")
sys.exit(0)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
import sys
import numpy as np
import xarray as xr

# R1.5: list of labels along a dim retains the dim with EXACTLY the requested
# labels, ORDERED AS REQUESTED (not reordered to match the coordinate).
da = xr.DataArray(
    np.arange(3),
    dims=["dim1"],
    coords={"dim1": ["a", "b", "c"]},
)
res = da.loc[dict(dim1=["c", "a"])]
order = [str(x) for x in res.coords["dim1"].values]
print("requested [c, a]; result dim1 order:", order)
print("values:", res.values.tolist())
if order != ["c", "a"]:
    print("FAIL: R1.5 mandates requested order [c, a], got", order)
    sys.exit(1)
if res.values.tolist() != [2, 0]:
    print("FAIL: values should be [2, 0]")
    sys.exit(1)
print("PASS R1.5: list-of-labels retains dim in requested order")
sys.exit(0)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
import sys
import numpy as np
import xarray as xr

# R1.1/R1.6: dict-based .loc selects along named dims using labels; omitted dims
# are returned in full.
da = xr.DataArray(
    np.arange(12).reshape(3, 4),
    dims=["dim1", "dim2"],
    coords={"dim1": ["x", "y", "z"], "dim2": ["a", "b", "c", "d"]},
)
res = da.loc[dict(dim1="y")]  # dim2 omitted -> full
print("shape:", res.shape, "dims:", res.dims)
if res.dims != ("dim2",) or res.shape != (4,):
    print("FAIL: omitted dim not returned in full")
    sys.exit(1)
if res.values.tolist() != [4, 5, 6, 7]:
    print("FAIL: wrong row selected")
    sys.exit(1)
print("PASS R1.1/R1.6: selects named dim, leaves omitted dim full")
sys.exit(0)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
import sys
import numpy as np
import xarray as xr

# R1.4: optional matching params (method/tolerance/drop) stay at defaults when
# a dim is named like one of them. If "method" were consumed as the sel method,
# a valid nearest-style value would behave differently. Here we confirm that a
# dim named "tolerance" is selected as a dim and no tolerance-based matching
# occurs (exact selection only). A non-existent label must raise KeyError, not
# silently nearest-match.
da = xr.DataArray(
    np.arange(3),
    dims=["tolerance"],
    coords={"tolerance": [0.0, 1.0, 2.0]},
)
res = da.loc[dict(tolerance=1.0)]
print("selected:", int(res.values))
if int(res.values) != 1:
    print("FAIL: exact selection wrong")
    sys.exit(1)
# label not present -> must be exact-match failure (KeyError), not tolerance match
raised = False
try:
    da.loc[dict(tolerance=0.6)]
except KeyError:
    raised = True
except Exception as e:
    print("FAIL: unexpected error", type(e).__name__, e)
    sys.exit(1)
print("missing-label raised KeyError:", raised)
if not raised:
    print("FAIL: R1.4 - tolerance dim label was inexact-matched (param leaked)")
    sys.exit(1)
print("PASS R1.4: matching params stay at defaults; exact selection only")
sys.exit(0)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
import sys
import numpy as np
import xarray as xr

# POSITIVE CONTROL + R1.3: the core fixed behavior. A dim literally named
# "method" mapped to a label must select, NOT raise "Invalid fill method".
# On base (sel(**key)) this raises ValueError about an invalid fill method.
da = xr.DataArray(
    np.arange(4),
    dims=["method"],
    coords={"method": ["a", "b", "c", "d"]},
)
try:
    res = da.loc[dict(method="c")]
except Exception as e:
    print("observed exception:", type(e).__name__, str(e))
    print("FAIL: .loc with dim named 'method' raised instead of selecting")
    sys.exit(1)
val = int(res.values)
print("selected value:", val)
if val != 2:
    print("FAIL: wrong element (expected 2 for label 'c')")
    sys.exit(1)
print("PASS: dim named 'method' selected correctly (label 'c' -> 2)")
sys.exit(0)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
import sys
import numpy as np
import xarray as xr

# R2.2/R2.3/R2.5: preserve non-dict .loc (positional label selection, incl.
# scalar on 1-D, coord preservation), and R2.4 equivalence with sel.
da = xr.DataArray(
    np.arange(6).reshape(2, 3),
    dims=["dim1", "dim2"],
    coords={"dim1": ["x", "y"], "dim2": ["a", "b", "c"]},
)
# non-dict positional key (tuple)
r1 = da.loc["x", "b"]
if int(r1.values) != 1:
    print("FAIL R2.2: positional tuple key", int(r1.values)); sys.exit(1)
# scalar-label reduces its dim, keeps the other; coords preserved
r2 = da.loc["y"]
if r2.dims != ("dim2",) or "dim1" not in r2.coords:
    print("FAIL R2.5: coords/dims not preserved", r2.dims); sys.exit(1)
# equivalence with sel (R2.4)
r3 = da.loc[dict(dim1="x", dim2="c")]
r4 = da.sel(dict(dim1="x", dim2="c"))
if int(r3.values) != int(r4.values):
    print("FAIL R2.4: loc != sel"); sys.exit(1)
# 1-D scalar incl boolean-labeled coord (R2.3)
b = xr.DataArray([10, 20], dims=["d"], coords={"d": [False, True]})
if int(b.loc[True].values) != 20:
    print("FAIL R2.3: boolean-label scalar"); sys.exit(1)
print("PASS R2.2/2.3/2.4/2.5: positional, scalar, equivalence, coord-preserve")
sys.exit(0)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_5.py`

```python
import sys
import numpy as np
import xarray as xr

# POSITIVE CONTROL + R1.3: the core fixed behavior. A dim literally named
# "method" mapped to a label must select, NOT raise "Invalid fill method".
# On base (sel(**key)) this raises ValueError about an invalid fill method.
da = xr.DataArray(
    np.arange(4),
    dims=["method"],
    coords={"method": ["a", "b", "c", "d"]},
)
try:
    res = da.loc[dict(method="c")]
except Exception as e:
    print("observed exception:", type(e).__name__, str(e))
    print("FAIL: .loc with dim named 'method' raised instead of selecting")
    sys.exit(1)
val = int(res.values)
print("selected value:", val)
if val != 2:
    print("FAIL: wrong element (expected 2 for label 'c')")
    sys.exit(1)
print("PASS: dim named 'method' selected correctly (label 'c' -> 2)")
sys.exit(0)
```

Prepatch bug re-encoded as an attack: `True`.

Gold patch: _LocIndexer.__getitem__ changes self.data_array.sel(**key) -> self.data_array.sel(key), so a dict key is forwarded positionally as the `indexers` mapping instead of being unpacked into keyword args, preventing dimension names from colliding with sel's method/tolerance/drop params.

6 probes, ALL HOLD on the gold-patched tree:
- probe_1 (R1.2/R1.3): dim named 'method' selected as a dimension, no 'Invalid fill method' error -> value 1. Base: raises ValueError Invalid fill method.
- probe_2 (R1.5): dict(dim1=['c','a']) retains dim1 in the REQUESTED order ['c','a'] with values [2,0]. Holds patched.
- probe_3 (R1.1/R1.6): dict(dim1='y') selects that dim, leaves omitted dim2 full (shape (4,)).
- probe_4 (R1.4): dim named 'tolerance' -> exact selection only; a missing label raises KeyError (no inexact/tolerance matching leaked from the dict).
- probe_5 (POSITIVE CONTROL, R1.3): dim named 'method' mapped to label 'c' selects element 2. HOLDS patched, FAILS at base (Invalid fill method / multi-element error) -> discriminates.
- probe_6 (R2.2/2.3/2.4/2.5): non-dict positional key, scalar-label reduction, loc==sel equivalence, boolean-labeled 1-D scalar, coord preservation.

CANDIDATE PATCH (weak.diff): a partial fix that only special-cases the reported 'method' collision (pop 'method' and sel it separately) but still unpacks the rest via sel(**key). It PASSES probe_1/2/3/5/6 but is REJECTED by probe_4 (a dim named 'tolerance' is still consumed as sel(tolerance=...), so exact selection breaks -> multi-element/ TypeError). This proves the probe suite discriminates a plausibly-wrong fix. No requirements-conforming alternative that fails the hidden tests was found.

IMPORTANT: the prior recorded G-EQ/G-PANEL-1 FAIL (probe_6 in a previous audit dir) is itself an ARTIFACT: that probe encoded R1.5 BACKWARDS, demanding underlying-coordinate order [a,c]. R1.5 explicitly states labels are 'ordered as they appear in the requested list (not reordered to match the underlying coordinate)'. My probe_2 confirms the patched tree returns the requested order [c,a] -- exactly what the requirement mandates. So that prior VIOLATION was a mis-encoded probe, not a real spec-too-weak/violation. Requirements are faithful and adequately strong.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 6 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 6 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_5.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (6):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

_The 6 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts, and on this backend both roles put it through the same derivation: every block below is a requirement probe run on the gold-patched tree, and the `machine verdict:` line each role publishes above reports BOTH that its probes hold there and how many candidate patches the probe suite rejected — so the two roles re-ran ONE probe suite and each recorded its own outcome for every probe in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `probe_1.py` → holds on the patched tree (good)

Attack 2 — `probe_2.py` → holds on the patched tree (good)

Attack 3 — `probe_3.py` → holds on the patched tree (good)

Attack 4 — `probe_4.py` → holds on the patched tree (good)

Attack 5 — `probe_5.py` → holds on the patched tree (good)

Attack 6 — `probe_6.py` → holds on the patched tree (good)

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_5.py`

```python
import sys
import numpy as np
import xarray as xr

# POSITIVE CONTROL + R1.3: the core fixed behavior. A dim literally named
# "method" mapped to a label must select, NOT raise "Invalid fill method".
# On base (sel(**key)) this raises ValueError about an invalid fill method.
da = xr.DataArray(
    np.arange(4),
    dims=["method"],
    coords={"method": ["a", "b", "c", "d"]},
)
try:
    res = da.loc[dict(method="c")]
except Exception as e:
    print("observed exception:", type(e).__name__, str(e))
    print("FAIL: .loc with dim named 'method' raised instead of selecting")
    sys.exit(1)
val = int(res.values)
print("selected value:", val)
if val != 2:
    print("FAIL: wrong element (expected 2 for label 'c')")
    sys.exit(1)
print("PASS: dim named 'method' selected correctly (label 'c' -> 2)")
sys.exit(0)
```

Prepatch bug re-encoded as an attack: `True`.

Gold patch: _LocIndexer.__getitem__ changes self.data_array.sel(**key) -> self.data_array.sel(key), so a dict key is forwarded positionally as the `indexers` mapping instead of being unpacked into keyword args, preventing dimension names from colliding with sel's method/tolerance/drop params.

6 probes, ALL HOLD on the gold-patched tree:
- probe_1 (R1.2/R1.3): dim named 'method' selected as a dimension, no 'Invalid fill method' error -> value 1. Base: raises ValueError Invalid fill method.
- probe_2 (R1.5): dict(dim1=['c','a']) retains dim1 in the REQUESTED order ['c','a'] with values [2,0]. Holds patched.
- probe_3 (R1.1/R1.6): dict(dim1='y') selects that dim, leaves omitted dim2 full (shape (4,)).
- probe_4 (R1.4): dim named 'tolerance' -> exact selection only; a missing label raises KeyError (no inexact/tolerance matching leaked from the dict).
- probe_5 (POSITIVE CONTROL, R1.3): dim named 'method' mapped to label 'c' selects element 2. HOLDS patched, FAILS at base (Invalid fill method / multi-element error) -> discriminates.
- probe_6 (R2.2/2.3/2.4/2.5): non-dict positional key, scalar-label reduction, loc==sel equivalence, boolean-labeled 1-D scalar, coord preservation.

CANDIDATE PATCH (weak.diff): a partial fix that only special-cases the reported 'method' collision (pop 'method' and sel it separately) but still unpacks the rest via sel(**key). It PASSES probe_1/2/3/5/6 but is REJECTED by probe_4 (a dim named 'tolerance' is still consumed as sel(tolerance=...), so exact selection breaks -> multi-element/ TypeError). This proves the probe suite discriminates a plausibly-wrong fix. No requirements-conforming alternative that fails the hidden tests was found.

IMPORTANT: the prior recorded G-EQ/G-PANEL-1 FAIL (probe_6 in a previous audit dir) is itself an ARTIFACT: that probe encoded R1.5 BACKWARDS, demanding underlying-coordinate order [a,c]. R1.5 explicitly states labels are 'ordered as they appear in the requested list (not reordered to match the underlying coordinate)'. My probe_2 confirms the patched tree returns the requested order [c,a] -- exactly what the requirement mandates. So that prior VIOLATION was a mis-encoded probe, not a real spec-too-weak/violation. Requirements are faithful and adequately strong.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Change is one line: _LocIndexer.__getitem__ forwards self.data_array.sel(**key) -> sel(key), so a dimension named 'method'/'tolerance'/'drop' is no longer consumed as a sel keyword. Requirements pin exactly this observable behavior at the correct boundary (_LocIndexer.__getitem__).

Probed on gold-patched tree (all exit 0):
- R1.3/R1.2/R1.4: DataArray dims=['dim1','method'], D.loc[dict(dim1='x', method='a')] selects (0.0), no 'Invalid fill method' error; matching params stay default.
- R1.5: D.loc[dict(dim2=['c','a'])] -> dim2 order ['c','a'] (requested-list order, matches R1.5). Also method-dim list [b,a] -> ['b','a'].
- R1.6: omitting dim2 returns it in full ['a','b','c'].
- R2.2: positional D.loc['x','b']=1.0. R2.3: boolean-labeled 1D D.loc[True]=10.0. R2.4: loc[mapping]==sel(mapping). R2.5: coords/dims preserved.

No mandated-but-absent behavior, none forbidden that the patch has, no wrong boundary, no invented behavior. The prior G-PANEL-1/G-EQ VIOLATION stamp rests on an incorrect reading of R1.5 and should not be treated as a faithfulness defect.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The requirements describe behavior localized to _LocIndexer.__getitem__ in xarray/core/dataarray.py (legitimate localization, and the file is named in the public hints/traceback anyway). Everything test-adjacent is derivable from the PUBLIC problem_statement: the dimension name 'method', dims dim1/dim2, coord labels ['x','y']/['a','b'], and the 'ValueError: Invalid fill method' error are all quoted in the problem_statement code sample and error text. The sel() optional params method/tolerance/drop are documented public API. The gold fix (sel(**key) -> sel(key)) invents NO new identifiers, so no fix-invented names could leak. No test names/paths (test_loc_dim_name_collision_with_sel_params), no test class (TestDataArray), no parametrization ids, and no verbatim test/gold code appear. Req 1.5 (list-of-labels retains dimension in requested order) generalizes standard .sel list-selection semantics rather than reconstructing the hidden test's specific inputs/outputs (da.loc[dict(dim1=['x','y'], method=['a'])] == [[0],[1]]); the doc never enumerates those concrete labels or expected values. Prose translates tested behavior into requirements — the intended purpose — without transmitting the tests themselves.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
