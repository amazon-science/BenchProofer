# P2 adversarial audit — pydata__xarray-7233

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 6 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 6 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 6 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_2.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (6):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
# Req1 AC2/AC4 + core fix: non-dimensional coordinate preserved as coordinate (POSITIVE CONTROL)
import numpy as np
import xarray as xr

da = xr.DataArray(
    np.arange(24).reshape(4, 6),
    dims=("x", "y"),
    coords={"x": np.arange(4), "y": np.arange(6)},
)
# add a non-dimensional coordinate on x
da = da.assign_coords(labels=("x", ["a", "b", "c", "d"]))
assert "labels" in da.coords, "setup failed"

res = da.coarsen(x=2).construct(x=("x_outer", "x_inner"))
coords = set(res.coords)
print("result coords:", sorted(coords))
ok = "labels" in coords
print("labels is coord:", ok)
raise SystemExit(0 if ok else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
# Req1 AC3: coordinate name set of result equals that of input (no drops, no promotions)
import numpy as np
import xarray as xr

ds = xr.Dataset(
    {"a": (("x", "y"), np.arange(24).reshape(4, 6)),
     "b": (("x", "y"), np.arange(24, 48).reshape(4, 6))},
    coords={"x": np.arange(4), "y": np.arange(6),
            "labels": ("x", ["p", "q", "r", "s"])},
)
in_coords = set(ds.coords)
res = ds.coarsen(x=2).construct(x=("xo", "xi"))
out_coords = set(res.coords)
print("input coords:", sorted(in_coords))
print("output coords:", sorted(out_coords))
# data var b must NOT be promoted, all input coords must remain
ok = (in_coords == out_coords) and ("b" not in out_coords) and ("a" not in out_coords)
print("equal & no promotion:", ok)
raise SystemExit(0 if ok else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
# Req1 AC4 / Req2: coordinate unrelated to reshaped dim stays a coordinate; DataArray vs Dataset consistency
import numpy as np
import xarray as xr

ds = xr.Dataset(
    {"a": (("x", "y"), np.arange(24).reshape(4, 6))},
    coords={"x": np.arange(4), "y": np.arange(6),
            "ycoord": ("y", np.arange(6) * 10)},  # coord on y, unrelated to reshaped x
)
# reshape only x
res_ds = ds.coarsen(x=2).construct(x=("xo", "xi"))
da = ds["a"]
res_da = da.coarsen(x=2).construct(x=("xo", "xi"))
print("ds out coords:", sorted(res_ds.coords))
print("da out coords:", sorted(res_da.coords))
ok = ("ycoord" in res_ds.coords) and ("ycoord" in res_da.coords)
# consistency: each result's coord set equals its input's coord set
ok = ok and (set(res_ds.coords) == set(ds.coords)) and (set(res_da.coords) == set(da.coords))
print("unrelated coord preserved & consistent:", ok)
raise SystemExit(0 if ok else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
# Req3 AC1/AC2/AC5: reshaping correctness + dim coord reshaped stays coord + unaffected var unchanged
import numpy as np
import xarray as xr

ds = xr.Dataset(
    {"a": (("x", "y"), np.arange(24).reshape(4, 6)),
     "z": (("y",), np.arange(6))},  # does not depend on x
    coords={"x": np.arange(4), "y": np.arange(6)},
)
res = ds.coarsen(x=2).construct(x=("xo", "xi"))
print("a dims:", res["a"].dims)
# reshaped: x replaced by xo,xi
ok = res["a"].dims == ("xo", "xi", "y")
# data values preserved in reshaped layout
expected = np.arange(24).reshape(4, 6).reshape(2, 2, 6)
ok = ok and np.array_equal(res["a"].values, expected)
# unaffected var carried through unchanged
ok = ok and res["z"].dims == ("y",) and np.array_equal(res["z"].values, np.arange(6))
# dim coord x reshaped remains coord
ok = ok and ("x" in res.coords)
print("reshape ok, x coord:", ok, "x in coords:", "x" in res.coords)
raise SystemExit(0 if ok else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
# Req3 AC3/AC4: keep_attrs semantics
import numpy as np
import xarray as xr

ds = xr.Dataset(
    {"a": (("x", "y"), np.arange(24).reshape(4, 6))},
    coords={"x": np.arange(4), "y": np.arange(6), "labels": ("x", list("abcd"))},
    attrs={"title": "hi"},
)
ds["a"].attrs["units"] = "m"

# default keep_attrs -> retain
r1 = ds.coarsen(x=2).construct(x=("xo", "xi"))
keep_ok = (r1.attrs.get("title") == "hi") and (r1["a"].attrs.get("units") == "m")

# keep_attrs=False -> empty
r2 = ds.coarsen(x=2).construct(x=("xo", "xi"), keep_attrs=False)
drop_ok = (r2.attrs == {}) and (r2["a"].attrs == {})
print("keep_ok:", keep_ok, "drop_ok:", drop_ok)
print("r2 obj attrs:", r2.attrs, "r2 a attrs:", r2["a"].attrs)
raise SystemExit(0 if (keep_ok and drop_ok) else 1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
# Req3 AC6 + Req4: mapping==kwargs equivalence and input validation errors
import numpy as np
import xarray as xr

ds = xr.Dataset(
    {"a": (("x", "y"), np.arange(24).reshape(4, 6))},
    coords={"x": np.arange(4), "y": np.arange(6), "labels": ("x", list("abcd"))},
)

# mapping vs kwargs equivalence
rm = ds.coarsen(x=2).construct({"x": ("xo", "xi")})
rk = ds.coarsen(x=2).construct(x=("xo", "xi"))
equiv = rm.identical(rk) and set(rm.coords) == set(rk.coords)

def raises(fn):
    try:
        fn()
        return False
    except ValueError:
        return True

# 1 no spec
v1 = raises(lambda: ds.coarsen(x=2).construct())
# 2 names a dim not being coarsened
v2 = raises(lambda: ds.coarsen(x=2).construct(y=("yo", "yi")))
# 3 coarsened dim not covered
v3 = raises(lambda: ds.coarsen(x=2, y=3).construct(x=("xo", "xi")))
# 4 not exactly two names
v4 = raises(lambda: ds.coarsen(x=2).construct(x="single"))
print("equiv:", equiv, "v1..4:", v1, v2, v3, v4)
raise SystemExit(0 if (equiv and v1 and v2 and v3 and v4) else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_2.py`

```python
# Req1 AC3: coordinate name set of result equals that of input (no drops, no promotions)
import numpy as np
import xarray as xr

ds = xr.Dataset(
    {"a": (("x", "y"), np.arange(24).reshape(4, 6)),
     "b": (("x", "y"), np.arange(24, 48).reshape(4, 6))},
    coords={"x": np.arange(4), "y": np.arange(6),
            "labels": ("x", ["p", "q", "r", "s"])},
)
in_coords = set(ds.coords)
res = ds.coarsen(x=2).construct(x=("xo", "xi"))
out_coords = set(res.coords)
print("input coords:", sorted(in_coords))
print("output coords:", sorted(out_coords))
# data var b must NOT be promoted, all input coords must remain
ok = (in_coords == out_coords) and ("b" not in out_coords) and ("a" not in out_coords)
print("equal & no promotion:", ok)
raise SystemExit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance pydata__xarray-7233: Coarsen.construct must preserve non-dimensional coordinates as coordinates. Gold fix unions ALL self.obj.coords into should_be_coords.

Probes (all HOLD on patched):
- probe_1 (Req1 AC2/AC4): DataArray non-dim coord 'labels' stays coord. NOTE: holds at base too (DataArray._from_temp_dataset re-coordinates on a DataArray), so NOT used as positive control.
- probe_2 (Req1 AC3, POSITIVE CONTROL): Dataset input/output coord-name sets equal, no data var promoted. PATCHED exit0; BASE exit1 (output coords lose 'labels'). Discriminates.
- probe_3 (Req1 AC4 / Req2): coord on a NON-reshaped dim ('ycoord' on y) preserved for both Dataset and DataArray, coord sets consistent. PATCHED exit0; BASE exit1.
- probe_4 (Req3 AC1/AC2/AC5): reshape correctness (x->xo,xi), values preserved, unaffected var 'z' unchanged, dim coord x kept.
- probe_5 (Req3 AC3/AC4): keep_attrs default retains obj+var attrs; keep_attrs=False empties both.
- probe_6 (Req3 AC6 + Req4 all): mapping==kwargs equivalence; ValueErrors for no-spec, non-coarsened dim, uncovered dim, non-two-name spec.

Candidate wrong-fix (weak.diff): unions only coords whose dims intersect window_dim (a partial reading of the requirements). REJECTED by probe_3 (demotes 'ycoord' on the non-reshaped y dim), confirming the suite discriminates wrong implementations. Req1 AC4 explicitly mandates coords unrelated to reshaped dims stay coords. No requirements-conforming alternative that fails the harness was found.

Verdict SOUND: 6 distinct probes cover all 4 requirements; positive control (probe_2) HOLDS patched and FAILS at base; wrong-fix candidate rejected.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 6 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 6 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_2.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (6):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

_The 6 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts, and on this backend both roles put it through the same derivation: every block below is a requirement probe run on the gold-patched tree, and the `machine verdict:` line each role publishes above reports BOTH that its probes hold there and how many candidate patches the probe suite rejected — so the two roles re-ran ONE probe suite and each recorded its own outcome for every probe in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `probe_1.py` → holds on the patched tree (good)

Attack 2 — `probe_2.py` → holds on the patched tree (good)

Attack 3 — `probe_3.py` → holds on the patched tree (good)

Attack 4 — `probe_4.py` → holds on the patched tree (good)

Attack 5 — `probe_5.py` → holds on the patched tree (good)

Attack 6 — `probe_6.py` → holds on the patched tree (good)

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_2.py`

```python
# Req1 AC3: coordinate name set of result equals that of input (no drops, no promotions)
import numpy as np
import xarray as xr

ds = xr.Dataset(
    {"a": (("x", "y"), np.arange(24).reshape(4, 6)),
     "b": (("x", "y"), np.arange(24, 48).reshape(4, 6))},
    coords={"x": np.arange(4), "y": np.arange(6),
            "labels": ("x", ["p", "q", "r", "s"])},
)
in_coords = set(ds.coords)
res = ds.coarsen(x=2).construct(x=("xo", "xi"))
out_coords = set(res.coords)
print("input coords:", sorted(in_coords))
print("output coords:", sorted(out_coords))
# data var b must NOT be promoted, all input coords must remain
ok = (in_coords == out_coords) and ("b" not in out_coords) and ("a" not in out_coords)
print("equal & no promotion:", ok)
raise SystemExit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance pydata__xarray-7233: Coarsen.construct must preserve non-dimensional coordinates as coordinates. Gold fix unions ALL self.obj.coords into should_be_coords.

Probes (all HOLD on patched):
- probe_1 (Req1 AC2/AC4): DataArray non-dim coord 'labels' stays coord. NOTE: holds at base too (DataArray._from_temp_dataset re-coordinates on a DataArray), so NOT used as positive control.
- probe_2 (Req1 AC3, POSITIVE CONTROL): Dataset input/output coord-name sets equal, no data var promoted. PATCHED exit0; BASE exit1 (output coords lose 'labels'). Discriminates.
- probe_3 (Req1 AC4 / Req2): coord on a NON-reshaped dim ('ycoord' on y) preserved for both Dataset and DataArray, coord sets consistent. PATCHED exit0; BASE exit1.
- probe_4 (Req3 AC1/AC2/AC5): reshape correctness (x->xo,xi), values preserved, unaffected var 'z' unchanged, dim coord x kept.
- probe_5 (Req3 AC3/AC4): keep_attrs default retains obj+var attrs; keep_attrs=False empties both.
- probe_6 (Req3 AC6 + Req4 all): mapping==kwargs equivalence; ValueErrors for no-spec, non-coarsened dim, uncovered dim, non-two-name spec.

Candidate wrong-fix (weak.diff): unions only coords whose dims intersect window_dim (a partial reading of the requirements). REJECTED by probe_3 (demotes 'ycoord' on the non-reshaped y dim), confirming the suite discriminates wrong implementations. Req1 AC4 explicitly mandates coords unrelated to reshaped dims stay coords. No requirements-conforming alternative that fails the harness was found.

Verdict SOUND: 6 distinct probes cover all 4 requirements; positive control (probe_2) HOLDS patched and FAILS at base; wrong-fix candidate rejected.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Base-vs-patched probe confirms the exact behavioral discriminator: base result coords=[] (day/other/scal demoted to data_vars) vs patched coords=['day','other','scal'] preserved. Requirement boundary is the full coordinate set, matching the patch's `| set(self.obj.coords)`. No requirement mandates behavior the code lacks, forbids behavior it has, or invents behavior. Requirement 3 regression clauses (reshaping layout, non-reshaped var passthrough, keep_attrs, mapping-vs-kwargs) are all behavior the patch leaves intact and were not disturbed by the one-line change.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The core coordinate-preservation behavior (F2P test) is fully public via the problem_statement MVCE, including the identifiers year/month/time/day, the to_dataset/DataArray-vs-Dataset framing, and coarsen(time=12).construct(time=("year","month")). No fix-invented identifiers are surfaced (gold's should_be_coords is not named). No test file paths, test class/function names (TestCoarsenConstruct, test_coarsen_construct_keeps_all_coords), parametrization ids, or quoted test/gold code appear. Requirement 3 (keep_attrs, mapping-vs-kwargs) and Requirement 4 describe the function's pre-existing, source-derivable input-validation and attribute contract — legitimate behavioral requirements the gold patch does not even touch. Requirement 4's 'single string or single-element sequence' phrasing echoes the regression test's pytest.raises cases but documents genuine documented behavior rather than transmitting the hidden tests. Naming the module/method Coarsen.construct is legitimate localization.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
