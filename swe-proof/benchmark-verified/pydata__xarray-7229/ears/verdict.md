# P2 adversarial audit — pydata__xarray-7229

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
"""Req 1 (positive control): per-coordinate attribute retention.
Coordinate attrs on the result must equal x's identically-named coordinate's
own attrs, NOT x's global/variable attrs. This is the core bug.
Exit 0 iff the coord attrs are preserved (empty dict at base = FAIL/overwrite)."""
import sys
import numpy as np
import xarray as xr

# all three share the same time coord (three-arg where uses join='exact')
tc = ("time", np.arange(3), {"long_name": "time coord"})
x = xr.DataArray(np.arange(3.0), dims="time", coords={"time": tc},
                 attrs={"var_attr": "global-of-x"})
y = xr.DataArray(np.zeros(3), dims="time",
                 coords={"time": ("time", np.arange(3))})
cond = xr.DataArray([True, False, True], dims="time",
                    coords={"time": ("time", np.arange(3))})

res = xr.where(cond, x, y, keep_attrs=True)
coord_attrs = dict(res.time.attrs)
print("result time coord attrs:", coord_attrs)
print("x global attrs:", dict(x.attrs))

# The coord attrs must be x's coord attrs, not x's global attrs and not empty.
ok = coord_attrs == {"long_name": "time coord"}
print("PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""Req 1.2: coordinate on result with NO identically-named coord on x =>
empty attr dict. x has no coords; result coord comes from y; must be empty."""
import sys
import numpy as np
import xarray as xr

x = xr.DataArray(np.arange(3.0), dims="time", attrs={"g": "gx"})
y = xr.DataArray(np.zeros(3), dims="time",
                 coords={"time": ("time", np.arange(3), {"long_name": "from y"})})
cond = xr.DataArray([True, False, True], dims="time")

res = xr.where(cond, x, y, keep_attrs=True)
coord_attrs = dict(res.time.attrs)
print("result time coord attrs (x has no such coord):", coord_attrs)
ok = coord_attrs == {}
print("PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""Req 2.1 & 2.3 & 5.1: DataArray result top-level attrs come from x's global
attrs; values preserved element-wise."""
import sys
import numpy as np
import xarray as xr

tc = ("time", np.arange(3), {"long_name": "tc"})
x = xr.DataArray(np.arange(3.0), dims="time", coords={"time": tc},
                 attrs={"var_attr": "global-of-x"})
y = xr.DataArray(np.zeros(3), dims="time",
                 coords={"time": ("time", np.arange(3))})
cond = xr.DataArray([True, False, True], dims="time",
                    coords={"time": ("time", np.arange(3))})

res = xr.where(cond, x, y, keep_attrs=True)
print("result top-level attrs:", dict(res.attrs))
print("result values:", res.values)

expected = np.where([True, False, True], np.arange(3.0), np.zeros(3))
ok_attrs = dict(res.attrs) == {"var_attr": "global-of-x"}
ok_vals = np.array_equal(res.values, expected)
print("attrs ok:", ok_attrs, "vals ok:", ok_vals)
ok = ok_attrs and ok_vals
print("PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""Req 3: x non-Dataset promoted against Dataset y. Result Dataset top-level
attrs empty; matching data var gets x's attrs; coord attrs from x (Req 3.3)."""
import sys
import numpy as np
import xarray as xr

tc_x = ("time", np.arange(3), {"long_name": "tc-of-x"})
x = xr.DataArray(np.arange(3.0), dims="time", coords={"time": tc_x},
                 attrs={"xa": "x-array-attr"}, name="foo")
y = xr.Dataset({"foo": ("time", np.zeros(3))},
               coords={"time": ("time", np.arange(3), {"long_name": "tc-of-y"})},
               attrs={"ya": "y-global"})
cond = xr.DataArray([True, False, True], dims="time",
                    coords={"time": ("time", np.arange(3))})

res = xr.where(cond, x, y, keep_attrs=True)
print("type:", type(res).__name__)
print("global attrs:", dict(res.attrs))
print("data var foo attrs:", dict(res["foo"].attrs))
print("coord time attrs:", dict(res.time.attrs))

ok = (isinstance(res, xr.Dataset)
      and dict(res.attrs) == {}
      and dict(res["foo"].attrs) == {"xa": "x-array-attr"}
      and dict(res.time.attrs) == {"long_name": "tc-of-x"})
print("PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""Req 4.2: keep_attrs=False/default => NO attrs copied; global and coord attrs
on result empty even though x carries attrs."""
import sys
import numpy as np
import xarray as xr

tc = ("time", np.arange(3), {"long_name": "tc"})
x = xr.DataArray(np.arange(3.0), dims="time", coords={"time": tc}, attrs={"g": "gx"})
y = xr.DataArray(np.zeros(3), dims="time", coords={"time": ("time", np.arange(3))})
cond = xr.DataArray([True, False, True], dims="time",
                    coords={"time": ("time", np.arange(3))})

res_default = xr.where(cond, x, y)
res_false = xr.where(cond, x, y, keep_attrs=False)

print("default global:", dict(res_default.attrs), "coord:", dict(res_default.time.attrs))
print("False global:", dict(res_false.attrs), "coord:", dict(res_false.time.attrs))

ok = (dict(res_default.attrs) == {}
      and dict(res_default.time.attrs) == {}
      and dict(res_false.attrs) == {}
      and dict(res_false.time.attrs) == {})
print("PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
"""Req 5.4 & 2.2 & 5.3: keep_attrs=True with scalar x and y (array cond, as in
the hidden test) => empty top-level attrs and correct element-wise selection."""
import sys
import numpy as np
import xarray as xr

cond = xr.DataArray([True, False], dims="d", attrs={"attr": "cond"})
res = xr.where(cond, 1, 0, keep_attrs=True)
print("result:", res.values, "attrs:", dict(res.attrs))
ok = dict(res.attrs) == {} and list(res.values) == [1, 0]
print("PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Req 1 (positive control): per-coordinate attribute retention.
Coordinate attrs on the result must equal x's identically-named coordinate's
own attrs, NOT x's global/variable attrs. This is the core bug.
Exit 0 iff the coord attrs are preserved (empty dict at base = FAIL/overwrite)."""
import sys
import numpy as np
import xarray as xr

# all three share the same time coord (three-arg where uses join='exact')
tc = ("time", np.arange(3), {"long_name": "time coord"})
x = xr.DataArray(np.arange(3.0), dims="time", coords={"time": tc},
                 attrs={"var_attr": "global-of-x"})
y = xr.DataArray(np.zeros(3), dims="time",
                 coords={"time": ("time", np.arange(3))})
cond = xr.DataArray([True, False, True], dims="time",
                    coords={"time": ("time", np.arange(3))})

res = xr.where(cond, x, y, keep_attrs=True)
coord_attrs = dict(res.time.attrs)
print("result time coord attrs:", coord_attrs)
print("x global attrs:", dict(x.attrs))

# The coord attrs must be x's coord attrs, not x's global attrs and not empty.
ok = coord_attrs == {"long_name": "time coord"}
print("PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance pydata__xarray-7229: xr.where(...,keep_attrs=True) must rebuild attrs from x per-component/per-level and NOT clobber coordinate attrs with x's global attrs.

Probes (all HOLD on gold-patched tree):
- probe_1 (Req1.1, POSITIVE CONTROL): result coord attrs == x's identically-named coord attrs, not x's global attrs. PATCHED: PASS (coord attrs={'long_name':'time coord'}). BASE: FAIL (coord attrs overwritten with x's global {'var_attr':...}) -> prepatch_reproduced=true, discriminates.
- probe_2 (Req1.2): coord present on result but absent on x -> empty attr dict. PATCHED PASS.
- probe_3 (Req2.1/2.3/5.1): DataArray result top-level attrs from x's global attrs; element-wise values preserved. PATCHED PASS.
- probe_4 (Req3.1/3.2/3.3): non-Dataset x promoted vs Dataset y -> empty global attrs, matching data var gets x's attrs, coord attrs from x. PATCHED PASS.
- probe_5 (Req4.1/4.2): default/False keep_attrs -> no attrs copied (global+coord empty). PATCHED PASS.
- probe_6 (Req5.4/2.2/5.3): scalar x,y with array cond -> empty top-level attrs, correct selection [1,0] (mirrors hidden test). PATCHED PASS.

Candidate wrong-fix (weak_coord.diff, applies at base_commit): identical to gold EXCEPT the per-coordinate line uses `result[c].attrs = getattr(x,'attrs',{})` (x's global attrs) instead of the per-coord `getattr(getattr(x,c,None),'attrs',{})` — i.e. the naive/lazy fix that reintroduces the original #6461 regression. Suite REJECTS it: probe_1 VIOLATED (coord attrs = x global attrs), probe_2 VIOLATED (coord attrs = x global {'g':'gx'} instead of empty), probe_4 VIOLATED (coord attrs wrong). Probes 3/5/6 still HOLD (they don't target coords), confirming the rejection is precisely the coord-fidelity criteria. This demonstrates the suite discriminates a plausible weak reading of the requirements.

>=5 distinct probes all hold on patched, positive control discriminates patched-vs-base, and >=1 candidate patch is rejected. Verdict SOUND.

Env note: use python; three-arg where uses join='exact' so all inputs share coords in probes.

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
"""Req 1 (positive control): per-coordinate attribute retention.
Coordinate attrs on the result must equal x's identically-named coordinate's
own attrs, NOT x's global/variable attrs. This is the core bug.
Exit 0 iff the coord attrs are preserved (empty dict at base = FAIL/overwrite)."""
import sys
import numpy as np
import xarray as xr

# all three share the same time coord (three-arg where uses join='exact')
tc = ("time", np.arange(3), {"long_name": "time coord"})
x = xr.DataArray(np.arange(3.0), dims="time", coords={"time": tc},
                 attrs={"var_attr": "global-of-x"})
y = xr.DataArray(np.zeros(3), dims="time",
                 coords={"time": ("time", np.arange(3))})
cond = xr.DataArray([True, False, True], dims="time",
                    coords={"time": ("time", np.arange(3))})

res = xr.where(cond, x, y, keep_attrs=True)
coord_attrs = dict(res.time.attrs)
print("result time coord attrs:", coord_attrs)
print("x global attrs:", dict(x.attrs))

# The coord attrs must be x's coord attrs, not x's global attrs and not empty.
ok = coord_attrs == {"long_name": "time coord"}
print("PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance pydata__xarray-7229: xr.where(...,keep_attrs=True) must rebuild attrs from x per-component/per-level and NOT clobber coordinate attrs with x's global attrs.

Probes (all HOLD on gold-patched tree):
- probe_1 (Req1.1, POSITIVE CONTROL): result coord attrs == x's identically-named coord attrs, not x's global attrs. PATCHED: PASS (coord attrs={'long_name':'time coord'}). BASE: FAIL (coord attrs overwritten with x's global {'var_attr':...}) -> prepatch_reproduced=true, discriminates.
- probe_2 (Req1.2): coord present on result but absent on x -> empty attr dict. PATCHED PASS.
- probe_3 (Req2.1/2.3/5.1): DataArray result top-level attrs from x's global attrs; element-wise values preserved. PATCHED PASS.
- probe_4 (Req3.1/3.2/3.3): non-Dataset x promoted vs Dataset y -> empty global attrs, matching data var gets x's attrs, coord attrs from x. PATCHED PASS.
- probe_5 (Req4.1/4.2): default/False keep_attrs -> no attrs copied (global+coord empty). PATCHED PASS.
- probe_6 (Req5.4/2.2/5.3): scalar x,y with array cond -> empty top-level attrs, correct selection [1,0] (mirrors hidden test). PATCHED PASS.

Candidate wrong-fix (weak_coord.diff, applies at base_commit): identical to gold EXCEPT the per-coordinate line uses `result[c].attrs = getattr(x,'attrs',{})` (x's global attrs) instead of the per-coord `getattr(getattr(x,c,None),'attrs',{})` — i.e. the naive/lazy fix that reintroduces the original #6461 regression. Suite REJECTS it: probe_1 VIOLATED (coord attrs = x global attrs), probe_2 VIOLATED (coord attrs = x global {'g':'gx'} instead of empty), probe_4 VIOLATED (coord attrs wrong). Probes 3/5/6 still HOLD (they don't target coords), confirming the rejection is precisely the coord-fidelity criteria. This demonstrates the suite discriminates a plausible weak reading of the requirements.

>=5 distinct probes all hold on patched, positive control discriminates patched-vs-base, and >=1 candidate patch is rejected. Verdict SOUND.

Env note: use python; three-arg where uses join='exact' so all inputs share coords in probes.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** The gold patch has exactly two branches: the Dataset-promotion special case (result.attrs={}, matching data var = x.attrs) and the general case (result.attrs=x.attrs, each data var attrs from x), plus an unconditional coord loop pulling coord attrs from x. Requirements 1-3 pin this per-component/per-level reconstruction as the changed observable behavior (not a narrow single-branch slice), matching the issue (coord attrs were being clobbered by variable attrs). R5 regression protection and R4 default/callable behavior also verified. Probes run on /testbed patched tree; all assertions passed (cond aligned on 't').


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** requirements.md describes the behavior of xr.where(keep_attrs=True) at the level of the gold edit's branches (per-coordinate, global, data-variable retention; x-promoted-to-Dataset special case; scalar-source handling). All identifiers named (xarray.where, computation.py, x/y/cond, coords, data_vars, x.name) are pre-existing public API used for legitimate localization; the fix invents no new symbols. No test file path, test function name, parametrization id, or verbatim test/gold code appears. No attribute-value literals from the hidden test (x_da/x_coord/cond_coord/y_ds etc.). The scalar and Dataset-promotion scenarios trace to code branches in the gold patch (getattr(x,'attrs',{}); isinstance(y,Dataset) and not isinstance(x,Dataset)), i.e. behavioral translation of the fix, not a transcription of the single non-parametrized test_where_attrs sub-assertions. The 'time coordinate' example derives from the public problem_statement MVCE. This is behavioral spec, not test reconstruction.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
