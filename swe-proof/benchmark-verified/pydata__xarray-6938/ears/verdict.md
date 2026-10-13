# P2 adversarial audit — pydata__xarray-6938

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
"""Req 1.1: index-form conversion on an already-index variable returns a
DISTINCT instance (not the same object). Positive control."""
import sys
import numpy as np
from xarray.core.variable import IndexVariable

iv = IndexVariable(("x",), np.array([1, 2, 3]))
out = iv.to_index_variable()
print("receiver id:", id(iv), "returned id:", id(out))
print("is same object:", out is iv)
if out is iv:
    print("FAIL: to_index_variable returned the same object")
    sys.exit(1)
if not isinstance(out, IndexVariable):
    print("FAIL: returned object is not an IndexVariable")
    sys.exit(1)
print("PASS: distinct IndexVariable returned")
sys.exit(0)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""Req 1.2: returned object carries same dims, data/values, attrs, encoding."""
import sys
import numpy as np
from xarray.core.variable import IndexVariable

data = np.array([10, 20, 30])
iv = IndexVariable(("x",), data, attrs={"a": 1}, encoding={"e": 2})
out = iv.to_index_variable()
ok = True
if out.dims != iv.dims:
    print("FAIL dims", out.dims, iv.dims); ok = False
if not np.array_equal(out.values, iv.values):
    print("FAIL values", out.values, iv.values); ok = False
if dict(out.attrs) != dict(iv.attrs):
    print("FAIL attrs", out.attrs, iv.attrs); ok = False
if dict(out.encoding) != dict(iv.encoding):
    print("FAIL encoding", out.encoding, iv.encoding); ok = False
print("dims", out.dims, "values", out.values, "attrs", dict(out.attrs), "encoding", dict(out.encoding))
sys.exit(0 if ok else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""Req 1.3: mutating the returned object in place (reassign dims) must NOT
change the receiver's dims/data/attrs/encoding. Core defect probe."""
import sys
import numpy as np
from xarray.core.variable import IndexVariable

iv = IndexVariable(("x",), np.array([1, 2, 3]), attrs={"a": 1}, encoding={"e": 2})
orig_dims = iv.dims
out = iv.to_index_variable()
out.dims = ("y",)  # mutate the returned object
print("receiver dims after mutation:", iv.dims, "returned dims:", out.dims)
ok = True
if iv.dims != orig_dims:
    print("FAIL: receiver dims changed to", iv.dims); ok = False
if out.dims != ("y",):
    print("FAIL: returned dims not updated", out.dims); ok = False
if dict(iv.attrs) != {"a": 1} or dict(iv.encoding) != {"e": 2}:
    print("FAIL: receiver attrs/encoding changed"); ok = False
sys.exit(0 if ok else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""Req 1.5: to_base_variable returns a NEW base Variable carrying dims/data/
attrs/encoding and leaves the receiver unchanged; mutating result doesn't leak."""
import sys
import numpy as np
from xarray.core.variable import Variable, IndexVariable

iv = IndexVariable(("x",), np.array([1, 2, 3]), attrs={"a": 1}, encoding={"e": 2})
base = iv.to_base_variable()
ok = True
if base is iv:
    print("FAIL: same object"); ok = False
if type(base) is not Variable:
    print("FAIL: not a plain base Variable:", type(base)); ok = False
if base.dims != iv.dims or not np.array_equal(base.values, iv.values):
    print("FAIL: dims/values mismatch"); ok = False
if dict(base.attrs) != {"a": 1} or dict(base.encoding) != {"e": 2}:
    print("FAIL: attrs/encoding mismatch", base.attrs, base.encoding); ok = False
# mutate result, receiver must be unchanged
base.dims = ("y",)
if iv.dims != ("x",):
    print("FAIL: receiver dims leaked", iv.dims); ok = False
print("base type", type(base).__name__, "base dims now", base.dims, "iv dims", iv.dims)
sys.exit(0 if ok else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""Req 2.1/2.2/2.3: Dataset.swap_dims must not mutate the source dataset; the
source variable retains its original dims, and repeated calls are stable."""
import sys
import numpy as np
import xarray as xr

ds = xr.Dataset(
    {"a": ("x", np.array([1, 2, 3]))},
    coords={"y": ("x", np.array([10, 20, 30]))},
)
before_dims = ds["y"].dims
before_a_dims = ds["a"].dims

r1 = ds.swap_dims({"x": "y"})
after_dims = ds["y"].dims
after_a_dims = ds["a"].dims
print("y dims before:", before_dims, "after:", after_dims)
print("a dims before:", before_a_dims, "after:", after_a_dims)

ok = True
if after_dims != before_dims:
    print("FAIL: source y dims mutated ->", after_dims); ok = False
if after_a_dims != before_a_dims:
    print("FAIL: source a dims mutated ->", after_a_dims); ok = False

# repeated invocation stability
r2 = ds.swap_dims({"x": "y"})
if ds["y"].dims != before_dims:
    print("FAIL: source mutated after second call ->", ds["y"].dims); ok = False
if r1["a"].dims != r2["a"].dims:
    print("FAIL: results differ across calls"); ok = False
print("PASS-ish" if ok else "FAIL")
sys.exit(0 if ok else 1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
"""Req 3.1: converted index-form values compare equal & same pandas index.
Req 3.5: IndexVariable.name setter still rejects in-place modification."""
import sys
import numpy as np
from xarray.core.variable import IndexVariable

iv = IndexVariable(("x",), np.array([1, 2, 3]))
out = iv.to_index_variable()
ok = True
if not np.array_equal(out.values, iv.values):
    print("FAIL: values not equal"); ok = False
if not out.to_index().equals(iv.to_index()):
    print("FAIL: pandas index differs"); ok = False
# name setter must raise
try:
    iv.name = "z"
    print("FAIL: name setter did not raise"); ok = False
except AttributeError as e:
    print("name setter raised AttributeError:", e)
print("index:", list(out.to_index()))
sys.exit(0 if ok else 1)
```

Attack 7 — `probe_7.py` → holds on the patched tree (good)

```python
"""Req 2.4 + 3.2 + 3.3: swap_dims produces requested swap (replacement becomes
dim coordinate) and validation errors are preserved."""
import sys
import numpy as np
import xarray as xr

ds = xr.Dataset(
    {"a": ("x", np.array([1, 2, 3]))},
    coords={"y": ("x", np.array([10, 20, 30]))},
)
r = ds.swap_dims({"x": "y"})
ok = True
# Req 2.4: y is now a dimension coordinate; a's dim renamed to y
if "y" not in r.dims:
    print("FAIL: y not a dimension in result", r.dims); ok = False
if r["a"].dims != ("y",):
    print("FAIL: a dims not swapped", r["a"].dims); ok = False
if "y" not in r.coords:
    print("FAIL: y not a coordinate", list(r.coords)); ok = False

# Req 3.2: swapping from a non-existent dimension raises
try:
    ds.swap_dims({"nope": "y"})
    print("FAIL: no error for non-existent dim"); ok = False
except ValueError as e:
    print("non-existent dim raised:", str(e)[:60])

# Req 3.3: replacement not 1D along old dim raises
ds2 = xr.Dataset({"a": ("x", np.array([1, 2, 3])), "b": (("x", "z"), np.ones((3, 2)))})
try:
    ds2.swap_dims({"x": "b"})
    print("FAIL: no error for non-1D replacement"); ok = False
except ValueError as e:
    print("non-1D replacement raised:", str(e)[:60])

print("result dims:", dict(r.dims))
sys.exit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Req 1.1: index-form conversion on an already-index variable returns a
DISTINCT instance (not the same object). Positive control."""
import sys
import numpy as np
from xarray.core.variable import IndexVariable

iv = IndexVariable(("x",), np.array([1, 2, 3]))
out = iv.to_index_variable()
print("receiver id:", id(iv), "returned id:", id(out))
print("is same object:", out is iv)
if out is iv:
    print("FAIL: to_index_variable returned the same object")
    sys.exit(1)
if not isinstance(out, IndexVariable):
    print("FAIL: returned object is not an IndexVariable")
    sys.exit(1)
print("PASS: distinct IndexVariable returned")
sys.exit(0)
```

Prepatch bug re-encoded as an attack: `True`.

Requirements cover IndexVariable.to_index_variable returning an independent object (Req1), swap_dims non-destructiveness (Req2), and preserved conversion/validation behavior (Req3). The actual defect (base: `return self`) is observable at the Variable-method level, which is exactly what the hidden F2P test targets (test_to_index_variable_copy). 

Probe->requirement->result (BASE / PATCHED):
- probe_1 (Req1.1 distinct instance): VIOLATED base / HOLDS patched  [POSITIVE CONTROL — discriminates]
- probe_2 (Req1.2 same dims/data/attrs/encoding): HOLDS patched
- probe_3 (Req1.3 mutating result doesn't leak into receiver): VIOLATED base / HOLDS patched  [also discriminates]
- probe_4 (Req1.5 to_base_variable returns new base Variable, no leak): HOLDS patched
- probe_5 (Req2.1/2.2/2.3 swap_dims non-destructive+stable): HOLDS both (regression 'SHALL keep')
- probe_6 (Req3.1 values/pandas index equal + Req3.5 name setter rejects): HOLDS patched
- probe_7 (Req2.4 swap performed + Req3.2/3.3 validation errors): HOLDS patched

Note: at the Dataset.swap_dims level the source is NOT mutated even at base (swap_dims builds a fresh variables dict via _replace_with_new_dims), so probes 5/7/8 hold on both trees — they are legitimate regression probes, not discriminators. The discriminating leg is the Variable-method aliasing (probes 1 & 3), matching the gold F2P test.

CANDIDATE PATCH (weak_dataset_only.diff): the lazy dataset-only fix that adds `.copy()` inside swap_dims but leaves IndexVariable.to_index_variable returning `self`. Applies cleanly at base_commit. Under this patch: probe_1 VIOLATED, probe_3 VIOLATED (probes 5/7 still hold). => REJECTED by the suite, and it would NOT resolve the hidden test which calls a.to_index_variable() directly and asserts `a is not b`. This demonstrates the probe suite discriminates a requirement-plausible-but-wrong implementation. No requirement-conforming alternative that fails the harness was found; the spec pins the exact fixed behavior.

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
"""Req 1.1: index-form conversion on an already-index variable returns a
DISTINCT instance (not the same object). Positive control."""
import sys
import numpy as np
from xarray.core.variable import IndexVariable

iv = IndexVariable(("x",), np.array([1, 2, 3]))
out = iv.to_index_variable()
print("receiver id:", id(iv), "returned id:", id(out))
print("is same object:", out is iv)
if out is iv:
    print("FAIL: to_index_variable returned the same object")
    sys.exit(1)
if not isinstance(out, IndexVariable):
    print("FAIL: returned object is not an IndexVariable")
    sys.exit(1)
print("PASS: distinct IndexVariable returned")
sys.exit(0)
```

Prepatch bug re-encoded as an attack: `True`.

Requirements cover IndexVariable.to_index_variable returning an independent object (Req1), swap_dims non-destructiveness (Req2), and preserved conversion/validation behavior (Req3). The actual defect (base: `return self`) is observable at the Variable-method level, which is exactly what the hidden F2P test targets (test_to_index_variable_copy). 

Probe->requirement->result (BASE / PATCHED):
- probe_1 (Req1.1 distinct instance): VIOLATED base / HOLDS patched  [POSITIVE CONTROL — discriminates]
- probe_2 (Req1.2 same dims/data/attrs/encoding): HOLDS patched
- probe_3 (Req1.3 mutating result doesn't leak into receiver): VIOLATED base / HOLDS patched  [also discriminates]
- probe_4 (Req1.5 to_base_variable returns new base Variable, no leak): HOLDS patched
- probe_5 (Req2.1/2.2/2.3 swap_dims non-destructive+stable): HOLDS both (regression 'SHALL keep')
- probe_6 (Req3.1 values/pandas index equal + Req3.5 name setter rejects): HOLDS patched
- probe_7 (Req2.4 swap performed + Req3.2/3.3 validation errors): HOLDS patched

Note: at the Dataset.swap_dims level the source is NOT mutated even at base (swap_dims builds a fresh variables dict via _replace_with_new_dims), so probes 5/7/8 hold on both trees — they are legitimate regression probes, not discriminators. The discriminating leg is the Variable-method aliasing (probes 1 & 3), matching the gold F2P test.

CANDIDATE PATCH (weak_dataset_only.diff): the lazy dataset-only fix that adds `.copy()` inside swap_dims but leaves IndexVariable.to_index_variable returning `self`. Applies cleanly at base_commit. Under this patch: probe_1 VIOLATED, probe_3 VIOLATED (probes 5/7 still hold). => REJECTED by the suite, and it would NOT resolve the hidden test which calls a.to_index_variable() directly and asserts `a is not b`. This demonstrates the probe suite discriminates a requirement-plausible-but-wrong implementation. No requirement-conforming alternative that fails the harness was found; the spec pins the exact fixed behavior.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Gold patch changes exactly two files: variable.py (IndexVariable.to_index_variable now returns self.copy() instead of self; type annotations added; unchanged self.dims->self._dims are equivalent) and dataset.py (a type annotation, no behavior change). The requirements' modeling boundary is the changed observable behavior — index-form conversion independence and swap_dims non-destructiveness — not a narrow slice. Probe: HOLDS gold-patched (exit 0), VIOLATED base (fails at Req1.1 'should be distinct instance'). Faithful.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The requirements describe behavior (index-form conversion must return an independent object; mutating the returned object must not affect the source; swap_dims must be non-destructive) that faithfully translates the hidden F2P test (test_to_index_variable_copy: a is not b; b.dims=('y',) leaves a.dims unchanged) into acceptance criteria WITHOUT transmitting the tests themselves. No test file path, test/class/function names, parametrization ids, or quoted test code appear. The concrete dims literals from the test ('x'/'y') are not quoted. Named symbols (to_index_variable/to_base_variable/to_index, Variable/IndexVariable, swap_dims, variable.py/dataset.py) are legitimate change localization; swap_dims is already named in the public problem_statement. Gold-invented identifiers (NoReturn annotation, self._dims, .copy()) are NOT surfaced in prose. Requirement 3's swap_dims validation clauses are general preserved-contract descriptions, not an enumeration mirroring test parametrization (the F2P is a single unparametrized test).


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
