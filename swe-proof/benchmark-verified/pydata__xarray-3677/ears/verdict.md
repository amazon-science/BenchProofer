# P2 adversarial audit — pydata__xarray-3677

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
import sys
import xarray as xr

# Req 1.1 / 1.3 (POSITIVE CONTROL): ds.merge(da) with a named scalar DataArray
# completes without AttributeError and yields both the pre-existing var and a
# new data var named after the DataArray carrying its value.
ds = xr.Dataset({"a": 0})
da = xr.DataArray(1, name="b")
try:
    out = ds.merge(da)
except AttributeError as e:
    print("FAIL: AttributeError raised:", e)
    sys.exit(1)
except Exception as e:
    print("FAIL: unexpected exception:", type(e).__name__, e)
    sys.exit(1)

print("result data_vars:", list(out.data_vars))
if "a" not in out.data_vars:
    print("FAIL: pre-existing var 'a' missing")
    sys.exit(1)
if "b" not in out.data_vars:
    print("FAIL: new var 'b' missing")
    sys.exit(1)
if int(out["a"].values) != 0:
    print("FAIL: a value wrong", out["a"].values)
    sys.exit(1)
if int(out["b"].values) != 1:
    print("FAIL: b value wrong", out["b"].values)
    sys.exit(1)
print("PASS: ds.merge(da) produced both vars a=0, b=1 without AttributeError")
sys.exit(0)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
import sys
import xarray as xr

# Req 1.2: merged data content of ds.merge(da) equals the content of
# xr.merge([ds, da]) for data_vars, coords, dims, values, dtypes; AND the
# returned dataset additionally retains the calling dataset's own attributes.
ds = xr.Dataset({"a": ("x", [1, 2, 3])}, coords={"x": [10, 20, 30]})
ds.attrs["foo"] = "bar"
da = xr.DataArray([4, 5, 6], dims="x", coords={"x": [10, 20, 30]}, name="b")

method = ds.merge(da)
func = xr.merge([ds, da])

# data content equality: compare with attrs dropped so we compare content only
m = method.copy(deep=True)
f = func.copy(deep=True)
m.attrs = {}
f.attrs = {}
# also drop per-variable attrs mismatch not relevant; compare identical content
try:
    xr.testing.assert_identical(m, f)
except AssertionError as e:
    print("FAIL: content differs from top-level merge:", e)
    sys.exit(1)

# retains caller attrs
if method.attrs.get("foo") != "bar":
    print("FAIL: caller attribute 'foo' not retained; attrs=", method.attrs)
    sys.exit(1)

print("PASS: content equals xr.merge([ds,da]) and caller attrs retained")
sys.exit(0)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
import sys
import xarray as xr

# Req 1.4: unnamed DataArray merged via Dataset.merge SHALL raise the same error
# that converting an unnamed DataArray to a dataset raises (ValueError from
# to_dataset), rather than silently producing an unnamed variable.
ds = xr.Dataset({"a": 0})
da = xr.DataArray(1)  # no name

# Determine reference error from to_dataset
ref_exc = None
try:
    da.to_dataset()
except Exception as e:
    ref_exc = type(e)
print("to_dataset() raises:", ref_exc.__name__ if ref_exc else None)
if ref_exc is None:
    print("FAIL: to_dataset() unexpectedly did not raise")
    sys.exit(1)

try:
    out = ds.merge(da)
except Exception as e:
    if isinstance(e, ref_exc):
        print("PASS: ds.merge(unnamed da) raised", type(e).__name__, "matching to_dataset")
        sys.exit(0)
    print("FAIL: raised different error", type(e).__name__, e)
    sys.exit(1)
print("FAIL: ds.merge(unnamed da) did not raise; produced", list(out.data_vars))
sys.exit(1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
import sys
import xarray as xr
import numpy as np

# Req 2.1 & 2.2: merging another Dataset works as before; merging a mapping
# (dict) of names to values works, including entries whose values are DataArrays.
ds = xr.Dataset({"a": ("x", [1, 2])}, coords={"x": [0, 1]})

# 2.1 Dataset merge
other_ds = xr.Dataset({"b": ("x", [3, 4])}, coords={"x": [0, 1]})
m1 = ds.merge(other_ds)
if "a" not in m1.data_vars or "b" not in m1.data_vars:
    print("FAIL: dataset merge missing vars", list(m1.data_vars))
    sys.exit(1)

# 2.2 mapping with a DataArray value inside
da = xr.DataArray([5, 6], dims="x", coords={"x": [0, 1]})
m2 = ds.merge({"c": da, "d": ("x", [7, 8])})
if not {"a", "c", "d"}.issubset(set(m2.data_vars)):
    print("FAIL: mapping merge missing vars", list(m2.data_vars))
    sys.exit(1)
if list(m2["c"].values) != [5, 6] or list(m2["d"].values) != [7, 8]:
    print("FAIL: mapping merge wrong values", m2["c"].values, m2["d"].values)
    sys.exit(1)

print("PASS: Dataset merge and dict(mapping-with-DataArray) merge both work")
sys.exit(0)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
import sys
import xarray as xr

# Req 2.4: conflicting values for a shared variable under effective compat
# SHALL raise a MergeError.  Also Req 2.3: compat/fill_value etc honored.
from xarray import MergeError

ds1 = xr.Dataset({"a": ("x", [1, 2])}, coords={"x": [0, 1]})
da_conflict = xr.DataArray([9, 9], dims="x", coords={"x": [0, 1]}, name="a")

# default compat='no_conflicts' with a conflicting 'a' should raise MergeError
try:
    out = ds1.merge(da_conflict)
except MergeError:
    print("PASS: conflicting merge raised MergeError")
    sys.exit(0)
except Exception as e:
    print("FAIL: raised non-MergeError", type(e).__name__, e)
    sys.exit(1)
print("FAIL: conflicting merge did not raise; got", out["a"].values)
sys.exit(1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
import sys
import xarray as xr

# Req 2.6: an object that is neither Dataset, mapping, nor DataArray SHALL raise
# an error rather than silently producing a result (no new validation message
# introduced; whatever the internal machinery raised).
ds = xr.Dataset({"a": 0})
raised = False
try:
    ds.merge(42)
except Exception as e:
    raised = True
    print("merge(42) raised", type(e).__name__, ":", e)
if not raised:
    print("FAIL: merge(42) did not raise")
    sys.exit(1)
print("PASS: unsupported operand raises an error")
sys.exit(0)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
import sys
import xarray as xr

# Req 1.1 / 1.3 (POSITIVE CONTROL): ds.merge(da) with a named scalar DataArray
# completes without AttributeError and yields both the pre-existing var and a
# new data var named after the DataArray carrying its value.
ds = xr.Dataset({"a": 0})
da = xr.DataArray(1, name="b")
try:
    out = ds.merge(da)
except AttributeError as e:
    print("FAIL: AttributeError raised:", e)
    sys.exit(1)
except Exception as e:
    print("FAIL: unexpected exception:", type(e).__name__, e)
    sys.exit(1)

print("result data_vars:", list(out.data_vars))
if "a" not in out.data_vars:
    print("FAIL: pre-existing var 'a' missing")
    sys.exit(1)
if "b" not in out.data_vars:
    print("FAIL: new var 'b' missing")
    sys.exit(1)
if int(out["a"].values) != 0:
    print("FAIL: a value wrong", out["a"].values)
    sys.exit(1)
if int(out["b"].values) != 1:
    print("FAIL: b value wrong", out["b"].values)
    sys.exit(1)
print("PASS: ds.merge(da) produced both vars a=0, b=1 without AttributeError")
sys.exit(0)
```

Prepatch bug re-encoded as an attack: `True`.

6 distinct probes covering all EARS criteria, all HOLD on the gold-patched tree; positive control (probe_1, Req 1.1/1.3) FAILS at base (AttributeError: 'DataArray' object has no attribute 'items') and PASSES patched — discriminating power confirmed. probe_2 also fails at base.

Probe coverage:
- probe_1 (Req 1.1/1.3, POSITIVE CONTROL): ds.merge(named scalar da) completes without AttributeError and yields both pre-existing var a=0 and new var b=1. base=FAIL, patched=PASS, weak=PASS.
- probe_2 (Req 1.2): merged content equals xr.merge([ds,da]) (attrs dropped for content compare) AND caller attrs retained. base=FAIL, patched=PASS.
- probe_3 (Req 1.4): unnamed DataArray raises the same ValueError that to_dataset() raises, not a silent unnamed var. patched=PASS, weak=REJECT (weak produces ['a', None]).
- probe_4 (Req 2.1/2.2): Dataset merge and dict-mapping merge (incl. DataArray value) work. patched=PASS.
- probe_5 (Req 2.4): conflicting shared var raises MergeError. patched=PASS.
- probe_6 (Req 2.6): unsupported operand (int) raises an error (AttributeError from internal machinery, no new validation message). patched=PASS.

Candidate patch weak.diff coerces a named DataArray via {other.name: other} instead of to_dataset(). It satisfies probes 1,2,4,5,6 but is REJECTED by probe_3: an unnamed DataArray (name=None) is silently folded in as a None-named variable, violating Req 1.4. This demonstrates the suite discriminates a plausibly-wrong (partial) fix; no requirements-conforming alternative was found that fails the hidden tests.

IMPORTANT re: prior meta.json G-EQ=fail: the previously recorded VIOLATION (probe_2 in run hq3o5l99) demanded strict assert_identical between ds.merge(da) and xr.merge([ds,da]) INCLUDING attrs. That probe was buggy: Req 1.2 explicitly states the method 'additionally retain[s] the calling dataset's own attributes ... rather than building a fresh attribute-less dataset', which by design differs from the top-level merge result on the attrs=... foo:bar note. My probe_2 compares content (attrs stripped) for equality and separately asserts caller-attr retention — matching what the requirement actually mandates — and it HOLDS on the patched tree. The gold patch faithfully satisfies every EARS criterion.

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
import sys
import xarray as xr

# Req 1.1 / 1.3 (POSITIVE CONTROL): ds.merge(da) with a named scalar DataArray
# completes without AttributeError and yields both the pre-existing var and a
# new data var named after the DataArray carrying its value.
ds = xr.Dataset({"a": 0})
da = xr.DataArray(1, name="b")
try:
    out = ds.merge(da)
except AttributeError as e:
    print("FAIL: AttributeError raised:", e)
    sys.exit(1)
except Exception as e:
    print("FAIL: unexpected exception:", type(e).__name__, e)
    sys.exit(1)

print("result data_vars:", list(out.data_vars))
if "a" not in out.data_vars:
    print("FAIL: pre-existing var 'a' missing")
    sys.exit(1)
if "b" not in out.data_vars:
    print("FAIL: new var 'b' missing")
    sys.exit(1)
if int(out["a"].values) != 0:
    print("FAIL: a value wrong", out["a"].values)
    sys.exit(1)
if int(out["b"].values) != 1:
    print("FAIL: b value wrong", out["b"].values)
    sys.exit(1)
print("PASS: ds.merge(da) produced both vars a=0, b=1 without AttributeError")
sys.exit(0)
```

Prepatch bug re-encoded as an attack: `True`.

6 distinct probes covering all EARS criteria, all HOLD on the gold-patched tree; positive control (probe_1, Req 1.1/1.3) FAILS at base (AttributeError: 'DataArray' object has no attribute 'items') and PASSES patched — discriminating power confirmed. probe_2 also fails at base.

Probe coverage:
- probe_1 (Req 1.1/1.3, POSITIVE CONTROL): ds.merge(named scalar da) completes without AttributeError and yields both pre-existing var a=0 and new var b=1. base=FAIL, patched=PASS, weak=PASS.
- probe_2 (Req 1.2): merged content equals xr.merge([ds,da]) (attrs dropped for content compare) AND caller attrs retained. base=FAIL, patched=PASS.
- probe_3 (Req 1.4): unnamed DataArray raises the same ValueError that to_dataset() raises, not a silent unnamed var. patched=PASS, weak=REJECT (weak produces ['a', None]).
- probe_4 (Req 2.1/2.2): Dataset merge and dict-mapping merge (incl. DataArray value) work. patched=PASS.
- probe_5 (Req 2.4): conflicting shared var raises MergeError. patched=PASS.
- probe_6 (Req 2.6): unsupported operand (int) raises an error (AttributeError from internal machinery, no new validation message). patched=PASS.

Candidate patch weak.diff coerces a named DataArray via {other.name: other} instead of to_dataset(). It satisfies probes 1,2,4,5,6 but is REJECTED by probe_3: an unnamed DataArray (name=None) is silently folded in as a None-named variable, violating Req 1.4. This demonstrates the suite discriminates a plausibly-wrong (partial) fix; no requirements-conforming alternative was found that fails the hidden tests.

IMPORTANT re: prior meta.json G-EQ=fail: the previously recorded VIOLATION (probe_2 in run hq3o5l99) demanded strict assert_identical between ds.merge(da) and xr.merge([ds,da]) INCLUDING attrs. That probe was buggy: Req 1.2 explicitly states the method 'additionally retain[s] the calling dataset's own attributes ... rather than building a fresh attribute-less dataset', which by design differs from the top-level merge result on the attrs=... foo:bar note. My probe_2 compares content (attrs stripped) for equality and separately asserts caller-attr retention — matching what the requirement actually mandates — and it HOLDS on the patched tree. The gold patch faithfully satisfies every EARS criterion.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Gold patch is a single line: `other = other.to_dataset() if isinstance(other, xr.DataArray) else other` prepended to Dataset.merge. Requirements correctly model the changed observable behavior (DataArray coercion in the method) and its boundary: they explicitly note only DataArray coercion is added, params unchanged, and the caller-attrs difference vs the top-level function (which the top-level does not preserve). All claims machine-verified via nl_attack probe on the instance image.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** requirements.md describes Dataset.merge accepting a DataArray purely as behavior. All potentially test-derived content is actually present in the PUBLIC problem_statement: the exact example (ds={'a':0}, da named 'b'=1), the full call chain dataset_merge_method→merge_core→coerce_pandas_values, and the AttributeError 'DataArray' object has no attribute 'items'. Req 1.2 translates the hidden test's assertion (assert_identical(ds.merge(da), xr.merge([ds,da]))) into behavioral terms — legitimate. Req 1.3's scalar-scenario mirrors the public MWE, not the parametrization. Req 1.4 (unnamed DataArray) is general coercion behavior; no test name (test_merge_dataarray/_unnamed), no file path (xarray/tests/test_merge.py), no class name (TestMergeMethod), no parametrization ids, and no gold identifiers are transmitted. The gold fix's to_dataset() is public API described conceptually, not a fix-invented symbol. Naming dataset.py/merge.py modules is legitimate localization and appears in the public traceback.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
