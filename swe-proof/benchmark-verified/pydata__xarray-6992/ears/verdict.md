# P2 adversarial audit — pydata__xarray-6992

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
"""Positive control — Req 1.4 / 1.2 / 1.3: reproducing sequence completes,
invariant holds, ndata>=0, repr succeeds. Must FAIL at base (ValueError)."""
import sys
import xarray as xr

ds = xr.Dataset(coords={"a": ("x", [1, 2, 3]), "b": ("x", ["a", "b", "c"])})
res = ds.set_index(z=["a", "b"]).reset_index("z", drop=True)

cn = set(res._coord_names)
vn = set(res._variables)
print("coord_names:", cn)
print("variables:", vn)
assert cn <= vn, "invariant violated: coord_names not subset of variables"

# ndata computed as len(vars)-len(coords) must be >= 0
ndata = len(res._variables) - len(res._coord_names)
print("ndata:", ndata)
assert ndata >= 0, "negative data variable count"

# repr must not raise
r = repr(res)
print("repr length:", len(r))
n = len(res.data_vars)
print("len(data_vars):", n)
assert n >= 0
print("OK")
sys.exit(0)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""Req 3.1/3.2/3.3/3.4/3.5: reset_index(drop=False) on a plain dim index
converts the index coordinate to a base variable coordinate, preserving values
and attributes, removes the index, keeps the invariant."""
import sys
import numpy as np
import xarray as xr
from xarray.core.variable import IndexVariable

ds = xr.Dataset(coords={"x": ("x", [1, 2, 3])})
ds["x"].attrs["units"] = "m"
assert "x" in ds.xindexes, "setup: x should be indexed"

res = ds.reset_index("x")

print("indexes:", list(res.xindexes))
assert "x" not in res.xindexes, "3.4: index not removed"

# still a coordinate, present in variables
assert "x" in res._coord_names, "x should remain a coordinate"
assert "x" in res._variables, "3.5: x missing from variables"

# no longer an index variable
var = res._variables["x"]
print("var type:", type(var).__name__)
assert not isinstance(var, IndexVariable), "3.2: still an IndexVariable"

# same values
assert list(np.asarray(var)) == [1, 2, 3], "values changed"

# attributes preserved
print("attrs:", dict(var.attrs))
assert var.attrs.get("units") == "m", "3.3: attrs not preserved"

# equal to base variable form of original
assert var.equals(ds._variables["x"].to_base_variable()), "3.2: not equal to base var"

# invariant
assert set(res._coord_names) <= set(res._variables)
print("OK")
sys.exit(0)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""Req 4.1/4.2/4.3: reset_index(drop=True) on a plain dim index removes both
the index and the coordinate name from coord_names AND variables, and the
now-unused dimension disappears."""
import sys
import xarray as xr

ds = xr.Dataset(coords={"x": ("x", [1, 2, 3])})
assert "x" in ds.xindexes

res = ds.reset_index("x", drop=True)

print("coord_names:", set(res._coord_names))
print("variables:", set(res._variables))
print("dims:", dict(res.dims))

assert "x" not in res.xindexes, "index not removed"
assert "x" not in res._coord_names, "4.1: coord name not removed"
assert "x" not in res._variables, "4.1: variable not removed"
# dimension unused by any remaining variable -> gone
assert "x" not in res.dims, "4.2: orphaned dimension lingers"
assert set(res._coord_names) <= set(res._variables)
print("OK")
sys.exit(0)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""Req 2.4/2.2/2.3: set_index(x=[subset]) on a dim x currently carrying a
multi-index over levels (a,b): result's x is the new (single) index over the
requested level, and the previously-indexed level no longer part of any index
appears as an ordinary (base variable) coordinate on x."""
import sys
import numpy as np
import xarray as xr
from xarray.core.indexes import PandasIndex, PandasMultiIndex
from xarray.core.variable import IndexVariable

ds = xr.Dataset(coords={"a": ("x", [1, 2, 3]), "b": ("x", ["p", "q", "r"])})
mi = ds.set_index(x=["a", "b"])
assert isinstance(mi.xindexes["x"], PandasMultiIndex)

# rebuild index over just 'a' -> 'b' becomes de-indexed
res = mi.set_index(x=["a"])

print("coord_names:", set(res._coord_names))
print("variables:", set(res._variables))
print("indexes:", {k: type(v).__name__ for k, v in res.xindexes.items()})

# new index over 'a' installed
assert "x" in res.xindexes, "2.1: new index not installed"
# 'b' de-indexed but retained as base variable coordinate
assert "b" in res._coord_names, "2.2: de-indexed coord 'b' dropped from coords"
assert "b" in res._variables, "2.3: 'b' missing from variables"
assert not isinstance(res._variables["b"], IndexVariable), "2.2: b still index var"
assert list(np.asarray(res._variables["b"])) == ["p", "q", "r"], "b data changed"

# invariant
assert set(res._coord_names) <= set(res._variables), "invariant broken"
print("OK")
sys.exit(0)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""Req 5.1/5.2/5.3: reset_index of a strict subset of multi-index levels, with
one level remaining -> reduce to a plain single index over the dim, surviving
level coordinate renamed to the dimension name; reset level (drop=False)
retained as base variable coordinate."""
import sys
import numpy as np
import xarray as xr
from xarray.core.indexes import PandasIndex, PandasMultiIndex

ds = xr.Dataset(coords={"a": ("x", [1, 2, 3]), "b": ("x", ["p", "q", "r"])})
mi = ds.set_index(x=["a", "b"])
assert isinstance(mi.xindexes["x"], PandasMultiIndex)

# reset level 'a' only, keep 'b'
res = mi.reset_index("a")

print("coord_names:", set(res._coord_names))
print("variables:", set(res._variables))
print("indexes:", {k: type(v).__name__ for k, v in res.xindexes.items()})

# one level remains -> plain single index over dim x, renamed to dim name 'x'
assert "x" in res.xindexes, "5.2: no index over dim x"
assert isinstance(res.xindexes["x"], PandasIndex) and not isinstance(res.xindexes["x"], PandasMultiIndex), "5.2: not reduced to plain PandasIndex"
assert "x" in res._coord_names and "x" in res._variables, "5.2: dim-named coord absent"
# surviving level 'b' renamed to dim -> 'b' no longer an indexed level coordinate
# reset level 'a' retained as base variable coordinate (drop=False)
assert "a" in res._coord_names and "a" in res._variables, "5.3: reset level 'a' not retained"
assert "a" not in res.xindexes, "5.3: 'a' should no longer be indexed"
assert list(np.asarray(res._variables["a"])) == [1, 2, 3], "a data changed"

assert set(res._coord_names) <= set(res._variables)
print("OK")
sys.exit(0)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
"""Req 5.4/5.6: reset_index on the multi-index dimension itself with drop=False:
removes the multi-index dimension variable, retains every level coordinate as a
base variable coordinate, does NOT re-introduce a dim-named packed coordinate,
result has no index."""
import sys
import numpy as np
import xarray as xr
from xarray.core.variable import IndexVariable

ds = xr.Dataset(coords={"a": ("x", [1, 2, 3]), "b": ("x", ["p", "q", "r"])})
mi = ds.set_index(x=["a", "b"])

res = mi.reset_index("x")  # drop=False, target the dim itself

print("coord_names:", set(res._coord_names))
print("variables:", set(res._variables))
print("indexes:", list(res.xindexes))

# no index left
assert len(res.xindexes) == 0, "5.6: result should have no index"
# level coords retained as base variables
for lvl in ("a", "b"):
    assert lvl in res._coord_names and lvl in res._variables, f"5.4: level {lvl} not retained"
    assert not isinstance(res._variables[lvl], IndexVariable), f"5.4: {lvl} still index var"
# do NOT re-introduce a dim-named packed coordinate 'x' (unless it's just a plain dim, not a coord holding MI values)
# The multi-index dimension variable must be removed from coords
assert "x" not in res._coord_names, "5.6/5.4: dim-named coordinate re-introduced"
assert set(res._coord_names) <= set(res._variables)
print("OK")
sys.exit(0)
```

Attack 7 — `probe_7.py` → holds on the patched tree (good)

```python
"""Req 6.3 (regression) & 5.5: reset_index raises ValueError for a name that is
not a coordinate with an index; multiple names referring to the same index are
processed once (same result as naming once)."""
import sys
import xarray as xr

# 6.3: reset a non-indexed name
ds = xr.Dataset({"v": ("x", [1, 2, 3])})
raised = False
try:
    ds.reset_index("v")
except ValueError as e:
    raised = True
    print("raised ValueError:", e)
assert raised, "6.3: expected ValueError for non-indexed name"

# 5.5: multiple names of same multi-index -> same as once
ds2 = xr.Dataset(coords={"a": ("x", [1, 2, 3]), "b": ("x", ["p", "q", "r"])})
mi = ds2.set_index(x=["a", "b"])
r_multi = mi.reset_index(["a", "b"])
r_dim = mi.reset_index("x")
print("multi coords:", set(r_multi._coord_names), "dim coords:", set(r_dim._coord_names))
assert r_multi.identical(r_dim), "5.5: naming both levels != naming dim once"
assert set(r_multi._coord_names) <= set(r_multi._variables)
print("OK")
sys.exit(0)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Positive control — Req 1.4 / 1.2 / 1.3: reproducing sequence completes,
invariant holds, ndata>=0, repr succeeds. Must FAIL at base (ValueError)."""
import sys
import xarray as xr

ds = xr.Dataset(coords={"a": ("x", [1, 2, 3]), "b": ("x", ["a", "b", "c"])})
res = ds.set_index(z=["a", "b"]).reset_index("z", drop=True)

cn = set(res._coord_names)
vn = set(res._variables)
print("coord_names:", cn)
print("variables:", vn)
assert cn <= vn, "invariant violated: coord_names not subset of variables"

# ndata computed as len(vars)-len(coords) must be >= 0
ndata = len(res._variables) - len(res._coord_names)
print("ndata:", ndata)
assert ndata >= 0, "negative data variable count"

# repr must not raise
r = repr(res)
print("repr length:", len(r))
n = len(res.data_vars)
print("len(data_vars):", n)
assert n >= 0
print("OK")
sys.exit(0)
```

Prepatch bug re-encoded as an attack: `True`.

Bundle pydata__xarray-6992. 7 probes written & re-run on the gold-patched tree; all HOLD (exit 0). Coverage: probe_1 = positive control (Req 1.2/1.3/1.4 — reproducing sequence completes, coord_names⊆variables, ndata>=0, repr succeeds); it FAILS at base with 'invariant violated: coord_names not subset of variables' (prepatch reproduced). probe_2 = Req 3.1/3.2/3.3/3.4/3.5 (reset_index drop=False converts index coord to base variable, keeps values+attrs, removes index). probe_3 = Req 4.1/4.2 (drop=True removes coord from both coord_names and variables, orphaned dim disappears). probe_4 = Req 2.2/2.3/2.4 (set_index rebuilding index over a subset of a multi-index's levels keeps the de-indexed level as a base-variable coordinate). probe_5 = Req 5.1/5.2/5.3 (reset a subset of MI levels, single level remains -> plain PandasIndex renamed to dim; reset level retained as base var). probe_6 = Req 5.4/5.6 (reset the MI dim itself, drop=False: no index left, level coords retained as base vars, no dim-named packed coord re-introduced). probe_7 = Req 6.3 + 5.5. CANDIDATE PATCH weak.diff: the lazy Req-1 reading — patch only DataVariables.__len__ to sum(1 for _ in self) so repr stops raising, leaving the set_index/reset_index bookkeeping untouched.

It applies cleanly at base and is REJECTED by 6/7 probes (probe_1 invariant still violated; probe_2/3/4/5/6 all fail because coordinates are not converted/removed correctly). Only probe_7 (the pure regression checks) passes it. Suite demonstrably discriminates a wrong implementation; positive control discriminates base vs patched. Note: python binary is only at python, not bare 'python'.

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
"""Positive control — Req 1.4 / 1.2 / 1.3: reproducing sequence completes,
invariant holds, ndata>=0, repr succeeds. Must FAIL at base (ValueError)."""
import sys
import xarray as xr

ds = xr.Dataset(coords={"a": ("x", [1, 2, 3]), "b": ("x", ["a", "b", "c"])})
res = ds.set_index(z=["a", "b"]).reset_index("z", drop=True)

cn = set(res._coord_names)
vn = set(res._variables)
print("coord_names:", cn)
print("variables:", vn)
assert cn <= vn, "invariant violated: coord_names not subset of variables"

# ndata computed as len(vars)-len(coords) must be >= 0
ndata = len(res._variables) - len(res._coord_names)
print("ndata:", ndata)
assert ndata >= 0, "negative data variable count"

# repr must not raise
r = repr(res)
print("repr length:", len(r))
n = len(res.data_vars)
print("len(data_vars):", n)
assert n >= 0
print("OK")
sys.exit(0)
```

Prepatch bug re-encoded as an attack: `True`.

Bundle pydata__xarray-6992. 7 probes written & re-run on the gold-patched tree; all HOLD (exit 0). Coverage: probe_1 = positive control (Req 1.2/1.3/1.4 — reproducing sequence completes, coord_names⊆variables, ndata>=0, repr succeeds); it FAILS at base with 'invariant violated: coord_names not subset of variables' (prepatch reproduced). probe_2 = Req 3.1/3.2/3.3/3.4/3.5 (reset_index drop=False converts index coord to base variable, keeps values+attrs, removes index). probe_3 = Req 4.1/4.2 (drop=True removes coord from both coord_names and variables, orphaned dim disappears). probe_4 = Req 2.2/2.3/2.4 (set_index rebuilding index over a subset of a multi-index's levels keeps the de-indexed level as a base-variable coordinate). probe_5 = Req 5.1/5.2/5.3 (reset a subset of MI levels, single level remains -> plain PandasIndex renamed to dim; reset level retained as base var). probe_6 = Req 5.4/5.6 (reset the MI dim itself, drop=False: no index left, level coords retained as base vars, no dim-named packed coord re-introduced). probe_7 = Req 6.3 + 5.5. CANDIDATE PATCH weak.diff: the lazy Req-1 reading — patch only DataVariables.__len__ to sum(1 for _ in self) so repr stops raising, leaving the set_index/reset_index bookkeeping untouched.

It applies cleanly at base and is REJECTED by 6/7 probes (probe_1 invariant still violated; probe_2/3/4/5/6 all fail because coordinates are not converted/removed correctly). Only probe_7 (the pure regression checks) passes it. Suite demonstrably discriminates a wrong implementation; positive control discriminates base vs patched. Note: python binary is only at python, not bare 'python'.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Probes on gold-patched image confirm: (Req1.4/4.1-4.2) xr.Dataset(coords={a:(x,..),b:(x,..)}).set_index(z=[a,b]).reset_index('z',drop=True) yields empty Dataset, dim x removed, repr succeeds. (Req3) reset_index('x',drop=False) on plain index -> x becomes base Variable (not IndexVariable), index removed, attrs units='m' preserved, coord_names subset of variables. (Req5.2) resetting one level 'a' of multi-index over [a,b] on dim x with drop=False -> surviving level renamed to dim name 'x' as plain PandasIndex, reset level 'a' kept as base variable. (Req5.4/5.6) reset_index('x',drop=False) on full multi-index -> no 'x' variable re-introduced, levels a,b retained as base var coords, no index. (Req5.5) reset_index(['a','b']) identical to reset_index('x'). (Req2.2/2.4) set_index(x=['a']) over prior multi-index [a,b] retains de-indexed 'b' as base Variable coord. (Req6.3) reset_index of non-indexed name raises ValueError. The requirements correctly pin the changed observable behavior (the coord/var invariant and set_index/reset_index/keep_levels bookkeeping) rather than a narrow internal branch.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The requirements doc names only pre-existing/public API (dataset.py, indexes.py, set_index, reset_index, PandasMultiIndex.keep_levels, to_base_variable, PandasIndex, DataVariables, _coord_names, _variables) — legitimate localization; keep_levels is edited by the gold but pre-exists, not a fix-invented identifier. The MVCE, the ValueError, and the repr breakage are all in the public problem_statement. Requirements 2.4 and 5 track the scenarios behind test_set_index_deindexed_coords and the 8-way test_reset_index_drop_convert parametrization, but they are stated as behavioral obligations (subset-of-levels rebuild, single-remaining-level reduces to a PandasIndex renamed to the dim, drop-vs-convert of level coords, same underlying index processed once, full-reset drops the packed dim variable), not as test code, parametrize ids (e.g. foo-False-dropped0), test file paths, function/class names, issue numbers (#6969/#6946/#6989), or verbatim gold lines. No fix-invented private identifiers (drop_or_convert, seen, all_var_names) appear. Translating what the tests check into requirements is the intended function; the tests themselves are not transmitted.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
