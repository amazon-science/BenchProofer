# P2 adversarial audit — pydata__xarray-4687

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
"""R2.1/R2.2 + R1.1: keep_attrs=True -> result carries exactly x's attrs, not cond/y.
Positive control: at base, where() has no keep_attrs kwarg -> TypeError -> fails."""
import sys
import numpy as np
import xarray as xr

cond = xr.DataArray([True, False, True], dims="x", attrs={"src": "cond"})
x = xr.DataArray([1, 2, 3], dims="x", attrs={"src": "x", "units": "m"})
y = xr.DataArray([10, 20, 30], dims="x", attrs={"src": "y"})

res = xr.where(cond, x, y, keep_attrs=True)
print("result attrs:", res.attrs)
if res.attrs != x.attrs:
    print("FAIL: attrs != x.attrs")
    sys.exit(1)
if res.attrs == cond.attrs or res.attrs == y.attrs:
    print("FAIL: attrs match cond/y")
    sys.exit(1)
print("PASS")
sys.exit(0)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""R1.2/R1.3/R3.3: default (no keep_attrs) -> empty attrs (global default keep_attrs=False).
Existing 3-arg calls remain valid."""
import sys
import xarray as xr

cond = xr.DataArray([True, False, True], dims="x", attrs={"src": "cond"})
x = xr.DataArray([1, 2, 3], dims="x", attrs={"src": "x"})
y = xr.DataArray([10, 20, 30], dims="x", attrs={"src": "y"})

res = xr.where(cond, x, y)  # 3-arg call must still work
print("default result attrs:", res.attrs)
if res.attrs != {}:
    print("FAIL: default should drop attrs")
    sys.exit(1)
print("PASS")
sys.exit(0)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""R2.3 + R3.1: values/dims/coords identical with and without keep_attrs; only attrs change.
Element-wise selection: x where cond truthy, y where falsy."""
import sys
import numpy as np
import xarray as xr

cond = xr.DataArray([True, False, True, False], dims="x",
                    coords={"x": [0, 1, 2, 3]}, attrs={"a": 1})
x = xr.DataArray([1, 2, 3, 4], dims="x", coords={"x": [0, 1, 2, 3]}, attrs={"b": 2})
y = xr.DataArray([10, 20, 30, 40], dims="x", coords={"x": [0, 1, 2, 3]}, attrs={"c": 3})

r_no = xr.where(cond, x, y)
r_keep = xr.where(cond, x, y, keep_attrs=True)

expected = np.array([1, 20, 3, 40])
print("no-keep values:", r_no.values, "keep values:", r_keep.values)
if not np.array_equal(r_no.values, expected):
    print("FAIL: selection values wrong")
    sys.exit(1)
if not np.array_equal(r_no.values, r_keep.values):
    print("FAIL: values differ between keep/no-keep")
    sys.exit(1)
if list(r_no.dims) != list(r_keep.dims):
    print("FAIL: dims differ")
    sys.exit(1)
if not r_no.coords["x"].equals(r_keep.coords["x"]):
    print("FAIL: coords differ")
    sys.exit(1)
print("PASS")
sys.exit(0)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""R1.3: default resolves from global keep_attrs option. set_options(keep_attrs=True) -> keeps x's attrs."""
import sys
import xarray as xr

cond = xr.DataArray([True, False], dims="x", attrs={"src": "cond"})
x = xr.DataArray([1, 2], dims="x", attrs={"src": "x"})
y = xr.DataArray([10, 20], dims="x", attrs={"src": "y"})

with xr.set_options(keep_attrs=True):
    res = xr.where(cond, x, y)  # unspecified -> resolves from global
print("global-keep result attrs:", res.attrs)
if res.attrs != x.attrs:
    print("FAIL: did not resolve global keep_attrs to keep x's attrs")
    sys.exit(1)
print("PASS")
sys.exit(0)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""R1.4: honor callable form of keep_attrs. A callable selecting attrs[1] (x) must be honored."""
import sys
import xarray as xr

cond = xr.DataArray([True, False], dims="x", attrs={"src": "cond"})
x = xr.DataArray([1, 2], dims="x", attrs={"src": "x", "u": "m"})
y = xr.DataArray([10, 20], dims="x", attrs={"src": "y"})

# callable form: keep attrs of x (index 1 in [cond, x, y])
res = xr.where(cond, x, y, keep_attrs=lambda attrs, context: attrs[1])
print("callable result attrs:", res.attrs)
if res.attrs != x.attrs:
    print("FAIL: callable keep_attrs not honored")
    sys.exit(1)

# keep_attrs=False explicitly -> empty
res2 = xr.where(cond, x, y, keep_attrs=False)
print("False result attrs:", res2.attrs)
if res2.attrs != {}:
    print("FAIL: keep_attrs=False should drop attrs")
    sys.exit(1)
print("PASS")
sys.exit(0)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
"""R3.4: return type priority preserved. Dataset input -> Dataset output; keep_attrs doesn't change type.
Also R3.2 broadcasting sanity."""
import sys
import numpy as np
import xarray as xr

# Dataset input
ds = xr.Dataset({"v": ("x", [1, 2, 3])}, attrs={"src": "x"})
cond = xr.DataArray([True, False, True], dims="x")
y = xr.Dataset({"v": ("x", [10, 20, 30])})
r = xr.where(cond, ds, y, keep_attrs=True)
print("type:", type(r).__name__)
if not isinstance(r, xr.Dataset):
    print("FAIL: Dataset not returned")
    sys.exit(1)

# broadcasting: cond scalar-ish over 2d
x2 = xr.DataArray(np.arange(6).reshape(2, 3), dims=("a", "b"))
y2 = xr.DataArray(-np.arange(6).reshape(2, 3), dims=("a", "b"))
c2 = xr.DataArray([True, False], dims="a")
rb = xr.where(c2, x2, y2)
print("broadcast values:\n", rb.values)
expected = np.where(np.array([[True], [False]]), x2.values, y2.values)
if not np.array_equal(rb.values, expected):
    print("FAIL: broadcasting selection wrong")
    sys.exit(1)
print("PASS")
sys.exit(0)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""R2.1/R2.2 + R1.1: keep_attrs=True -> result carries exactly x's attrs, not cond/y.
Positive control: at base, where() has no keep_attrs kwarg -> TypeError -> fails."""
import sys
import numpy as np
import xarray as xr

cond = xr.DataArray([True, False, True], dims="x", attrs={"src": "cond"})
x = xr.DataArray([1, 2, 3], dims="x", attrs={"src": "x", "units": "m"})
y = xr.DataArray([10, 20, 30], dims="x", attrs={"src": "y"})

res = xr.where(cond, x, y, keep_attrs=True)
print("result attrs:", res.attrs)
if res.attrs != x.attrs:
    print("FAIL: attrs != x.attrs")
    sys.exit(1)
if res.attrs == cond.attrs or res.attrs == y.attrs:
    print("FAIL: attrs match cond/y")
    sys.exit(1)
print("PASS")
sys.exit(0)
```

Prepatch bug re-encoded as an attack: `True`.

6 probes cover all 3 requirements. R2.1/R2.2/R1.1 (probe_1): keep_attrs=True -> result carries exactly x's attrs {'src':'x','units':'m'}, not cond/y. R1.2/R1.3/R3.3 (probe_2): 3-arg call still valid, default drops attrs ({}). R2.3/R3.1 (probe_3): element-wise selection [1,20,3,40] and dims/coords identical with vs without keep_attrs. R1.3 (probe_4): set_options(keep_attrs=True) + unspecified arg resolves global -> keeps x's attrs. R1.4 (probe_5): callable form honored (attrs[1]) and keep_attrs=False drops attrs. R3.4/R3.2 (probe_6): Dataset input -> Dataset output; 2D broadcasting selection correct.

All 6 HOLD on gold-patched tree.

Positive control = probe_1: HOLDS patched, FAILS at base (base where() has no keep_attrs kwarg -> TypeError). prepatch reproduced. probe_4 also VIOLATED at base (global keep_attrs ignored, took cond's attrs).

Wrong-fix candidate (weak.diff): keeps attrs[0] (cond) instead of attrs[1] (x) on keep_attrs=True — a plausible off-by-index misreading of R2.1. Applies cleanly at base_commit. Probes 1 and 4 REJECT it (result attrs = {'src':'cond'} instead of x's), proving the suite discriminates the correct branch's attrs. No requirements-conforming candidate found that would fail the harness — the suite pins x's attrs biconditionally.

Verdict SOUND: >=5 distinct probes all hold on patched, positive control discriminates base->patched, and a wrong-fix alternative is rejected.

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
"""R2.1/R2.2 + R1.1: keep_attrs=True -> result carries exactly x's attrs, not cond/y.
Positive control: at base, where() has no keep_attrs kwarg -> TypeError -> fails."""
import sys
import numpy as np
import xarray as xr

cond = xr.DataArray([True, False, True], dims="x", attrs={"src": "cond"})
x = xr.DataArray([1, 2, 3], dims="x", attrs={"src": "x", "units": "m"})
y = xr.DataArray([10, 20, 30], dims="x", attrs={"src": "y"})

res = xr.where(cond, x, y, keep_attrs=True)
print("result attrs:", res.attrs)
if res.attrs != x.attrs:
    print("FAIL: attrs != x.attrs")
    sys.exit(1)
if res.attrs == cond.attrs or res.attrs == y.attrs:
    print("FAIL: attrs match cond/y")
    sys.exit(1)
print("PASS")
sys.exit(0)
```

Prepatch bug re-encoded as an attack: `True`.

6 probes cover all 3 requirements. R2.1/R2.2/R1.1 (probe_1): keep_attrs=True -> result carries exactly x's attrs {'src':'x','units':'m'}, not cond/y. R1.2/R1.3/R3.3 (probe_2): 3-arg call still valid, default drops attrs ({}). R2.3/R3.1 (probe_3): element-wise selection [1,20,3,40] and dims/coords identical with vs without keep_attrs. R1.3 (probe_4): set_options(keep_attrs=True) + unspecified arg resolves global -> keeps x's attrs. R1.4 (probe_5): callable form honored (attrs[1]) and keep_attrs=False drops attrs. R3.4/R3.2 (probe_6): Dataset input -> Dataset output; 2D broadcasting selection correct.

All 6 HOLD on gold-patched tree.

Positive control = probe_1: HOLDS patched, FAILS at base (base where() has no keep_attrs kwarg -> TypeError). prepatch reproduced. probe_4 also VIOLATED at base (global keep_attrs ignored, took cond's attrs).

Wrong-fix candidate (weak.diff): keeps attrs[0] (cond) instead of attrs[1] (x) on keep_attrs=True — a plausible off-by-index misreading of R2.1. Applies cleanly at base_commit. Probes 1 and 4 REJECT it (result attrs = {'src':'cond'} instead of x's), proving the suite discriminates the correct branch's attrs. No requirements-conforming candidate found that would fail the harness — the suite pins x's attrs biconditionally.

Verdict SOUND: >=5 distinct probes all hold on patched, positive control discriminates base->patched, and a wrong-fix alternative is rejected.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Patch adds keep_attrs=None param to where(); None->_get_keep_attrs(default=False); True->lambda attrs,context: attrs[1] (keep x's attrs); passed to apply_ufunc. Requirements 1-3 correctly pin the changed observable behavior (attr preservation control) rather than a narrow branch/helper, and preserve value-selection/broadcasting/join/dask semantics. Modeling boundary is correct. The '.attrs[1]'->x mapping in code corresponds to x being element 1 of the (cond,x,y) objects list. Minor prose slip ('third positional') is non-behavioral; recommend FAITHFUL.

Counterexample / evidence:

```
Probed on gold-patched /testbed: cond=[T,F] attrs{c}, x=[1,2] attrs{attr_x}, y=[10,20] attrs{attr_y}. where(cond,x,y)->attrs={} (Req3.3); where(cond,x,y,keep_attrs=True)->attrs={'attr_x':'xval'} only (Req2.1/2.2), values [1,20] identical to default (Req2.3); set_options(keep_attrs=True) then where(...) -> {'attr_x':'xval'} (Req1.3); callable keep_attrs=lambda attrs,context: attrs[2] -> {'attr_y':'yval'} and string 'override' -> {'c':'cond'} (Req1.4); signature is (cond,x,y,keep_attrs=None) (Req1.1/1.2).
```


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** requirements.md describes the where(cond,x,y,keep_attrs) behavior at a public/behavioral level. The problem_statement already establishes the whole issue (xr.where drops attrs; desire to preserve or choose via keep_attrs to apply_ufunc). All specifics in the doc trace to (a) the public problem_statement or (b) the gold docstring's behavioral description ('keep_attrs : bool or str or callable, optional; If True, keep the attrs of x'), which is legitimate to translate into requirements. No test names/paths (test_where_attrs, test_computation.py), no parametrization ids, no verbatim gold code (the `_get_keep_attrs(default=False)` internal and `lambda attrs, context: attrs[1]` sentinel are NOT reproduced), and no fix-invented identifiers — keep_attrs, get_options/set_options, and the global keep_attrs option are all pre-existing public xarray API used to localize the change. Req 2's 'attrs of x, and no attrs of cond or y' states a general observable rule needed to specify the branch semantics, not the test's concrete attr values ('cond'/'x'/'y', [True,False] etc.), so it is not a test reconstruction. No enumeration mirrors the FAIL_TO_PASS/PASS_TO_PASS lists.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
