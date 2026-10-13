# P2 adversarial audit — pydata__xarray-3151

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 5 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 5 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 5 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (5):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
# Req1.1 (POSITIVE CONTROL): bystander non-monotonic coord must not raise.
import numpy as np
from xarray import Dataset
from xarray.core.combine import combine_by_coords

ycoord = ['a', 'c', 'b']  # non-monotonic
data = np.random.rand(7, 3)
ds1 = Dataset(data_vars=dict(data=(['x', 'y'], data[:3, :])),
              coords=dict(x=[1, 2, 3], y=ycoord))
ds2 = Dataset(data_vars=dict(data=(['x', 'y'], data[3:, :])),
              coords=dict(x=[4, 5, 6, 7], y=ycoord))
try:
    actual = combine_by_coords((ds1, ds2))
except ValueError as e:
    print("FAIL: raised ValueError:", e)
    raise SystemExit(1)
print("OK: combine succeeded, result dims:", dict(actual.dims))
raise SystemExit(0)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
# Req1.3 & 1.4: shared non-varying coord retained same values/order; data correctly
# concatenated along x with no loss/reordering.
import numpy as np
from xarray import Dataset
from xarray.core.combine import combine_by_coords

ycoord = ['a', 'c', 'b']
data = np.arange(21).reshape(7, 3).astype(float)
ds1 = Dataset(data_vars=dict(data=(['x', 'y'], data[:3, :])),
              coords=dict(x=[1, 2, 3], y=ycoord))
ds2 = Dataset(data_vars=dict(data=(['x', 'y'], data[3:, :])),
              coords=dict(x=[4, 5, 6, 7], y=ycoord))
actual = combine_by_coords((ds1, ds2))

y_out = list(actual['y'].values)
x_out = list(actual['x'].values)
print("y:", y_out, "x:", x_out)
if y_out != ycoord:
    print("FAIL: y coord changed:", y_out)
    raise SystemExit(1)
if x_out != [1, 2, 3, 4, 5, 6, 7]:
    print("FAIL: x coord wrong:", x_out)
    raise SystemExit(1)
if not np.array_equal(actual['data'].transpose('x', 'y').values, data):
    print("FAIL: data reordered/lost")
    raise SystemExit(1)
print("OK: coord order retained, data intact")
raise SystemExit(0)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
# Req2.1 & 2.3: concatenated dimension whose GLOBAL index is non-monotonic must
# still raise ValueError naming the dimension. Each input is individually
# monotonic-increasing, but concatenation order (by first coord) yields a
# non-monotonic global index [5,15,10,20] -> exercises the post-concat check.
import numpy as np
from xarray import Dataset
from xarray.core.combine import combine_by_coords

ds1 = Dataset(data_vars=dict(v=('x', [10., 20.])), coords=dict(x=[10, 20]))
ds2 = Dataset(data_vars=dict(v=('x', [5., 15.])), coords=dict(x=[5, 15]))
try:
    actual = combine_by_coords([ds1, ds2])
    print("FAIL: did not raise; result x:", list(actual['x'].values))
    raise SystemExit(1)
except ValueError as e:
    msg = str(e)
    print("OK raised ValueError:", msg)
    if "monotonic" not in msg or "x" not in msg:
        print("FAIL: error does not identify dim x / monotonic")
        raise SystemExit(1)
raise SystemExit(0)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
# Req3.1 & 3.2: monotonically increasing concat ordered by coord regardless of input
# order; monotonically decreasing accepted and order preserved.
import numpy as np
from xarray import Dataset
from xarray.core.combine import combine_by_coords

# increasing, given out of order
ds_a = Dataset(data_vars=dict(v=('x', [3.])), coords=dict(x=[3]))
ds_b = Dataset(data_vars=dict(v=('x', [1.])), coords=dict(x=[1]))
ds_c = Dataset(data_vars=dict(v=('x', [2.])), coords=dict(x=[2]))
inc = combine_by_coords([ds_a, ds_b, ds_c])
print("inc x:", list(inc['x'].values), "v:", list(inc['v'].values))
if list(inc['x'].values) != [1, 2, 3] or list(inc['v'].values) != [1., 2., 3.]:
    print("FAIL: not sorted by coord")
    raise SystemExit(1)

# decreasing
dd1 = Dataset(data_vars=dict(v=('x', [3., 2.])), coords=dict(x=[3, 2]))
dd2 = Dataset(data_vars=dict(v=('x', [1., 0.])), coords=dict(x=[1, 0]))
dec = combine_by_coords([dd1, dd2])
print("dec x:", list(dec['x'].values))
if list(dec['x'].values) != [3, 2, 1, 0]:
    print("FAIL: decreasing order not preserved")
    raise SystemExit(1)
print("OK: increasing sorted & decreasing preserved")
raise SystemExit(0)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
# Req3.3: datasets that need no concatenation (share all coords, differ only in
# data variables) SHALL merge without raising.
import numpy as np
from xarray import Dataset
from xarray.core.combine import combine_by_coords

x = [0, 1]
ds1 = Dataset(data_vars=dict(a=('x', [1., 2.])), coords=dict(x=x))
ds2 = Dataset(data_vars=dict(b=('x', [3., 4.])), coords=dict(x=x))
try:
    merged = combine_by_coords([ds1, ds2])
except ValueError as e:
    print("FAIL: raised:", e)
    raise SystemExit(1)
print("vars:", sorted(merged.data_vars), "x:", list(merged['x'].values))
if set(merged.data_vars) != {"a", "b"}:
    print("FAIL: variables not merged")
    raise SystemExit(1)
if list(merged['x'].values) != x:
    print("FAIL: x changed")
    raise SystemExit(1)
print("OK: merged without concatenation")
raise SystemExit(0)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
# Req1.1 (POSITIVE CONTROL): bystander non-monotonic coord must not raise.
import numpy as np
from xarray import Dataset
from xarray.core.combine import combine_by_coords

ycoord = ['a', 'c', 'b']  # non-monotonic
data = np.random.rand(7, 3)
ds1 = Dataset(data_vars=dict(data=(['x', 'y'], data[:3, :])),
              coords=dict(x=[1, 2, 3], y=ycoord))
ds2 = Dataset(data_vars=dict(data=(['x', 'y'], data[3:, :])),
              coords=dict(x=[4, 5, 6, 7], y=ycoord))
try:
    actual = combine_by_coords((ds1, ds2))
except ValueError as e:
    print("FAIL: raised ValueError:", e)
    raise SystemExit(1)
print("OK: combine succeeded, result dims:", dict(actual.dims))
raise SystemExit(0)
```

Prepatch bug re-encoded as an attack: `True`.

Instance pydata__xarray-3151: combine_by_coords must restrict post-concat monotonicity validation to actually-concatenated dims (concat_dims) instead of all result dims.

Probes (all HOLD on gold-patched tree):
- probe_1 (Req1.1, POSITIVE CONTROL): bystander non-monotonic coord y=['a','c','b'] shared across inputs; combine must not raise. HOLDS patched, VIOLATED at base (base raises 'Resulting object does not have monotonic global indexes along dimension y'). prepatch_reproduced=true => discriminating power confirmed.
- probe_2 (Req1.3/1.4): shared non-varying y coord retains same values/order; data correctly concatenated along x with no loss/reorder. HOLDS patched.
- probe_3 (Req2.1/2.3): concatenated dim whose GLOBAL index is non-monotonic must still raise ValueError naming the dim. Inputs x=[10,20] and x=[5,15] are each individually monotonic but the concat-ordered global index [5,15,10,20] is non-monotonic -> exercises the retained post-concat check specifically (not the earlier per-dataset check). HOLDS patched.
- probe_4 (Req3.1/3.2): increasing coords sorted by value regardless of input order; decreasing accepted and order preserved. HOLDS patched.
- probe_5 (Req3.3): datasets differing only in data variables merge without raising. HOLDS patched.

Candidate wrong-fix (weak.diff): the lazy reading of Req1 that simply DELETES the post-concat monotonicity loop entirely. It satisfies Req1 (bystander ok) but violates Req2: probe_3 REJECTS it (returns mis-ordered x=[5,15,10,20] instead of raising). This demonstrates the suite discriminates a plausibly-wrong implementation the requirements would otherwise seem to permit if Req2 were ignored. First draft of probe_3 accidentally triggered the earlier per-dataset monotonicity check (which the weak patch keeps), so it was rewritten to hit the specific removed global check; confirmed it now passes patched, fails weak, and (incidentally) also holds at base since base still has the check.

All 5 probes hold on the patched tree; positive control discriminates base vs patched; >=1 candidate exercised and REJECTED. Verdict SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 5 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 5 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 5 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (5):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

_The 5 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts, and on this backend both roles put it through the same derivation: every block below is a requirement probe run on the gold-patched tree, and the `machine verdict:` line each role publishes above reports BOTH that its probes hold there and how many candidate patches the probe suite rejected — so the two roles re-ran ONE probe suite and each recorded its own outcome for every probe in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `probe_1.py` → holds on the patched tree (good)

Attack 2 — `probe_2.py` → holds on the patched tree (good)

Attack 3 — `probe_3.py` → holds on the patched tree (good)

Attack 4 — `probe_4.py` → holds on the patched tree (good)

Attack 5 — `probe_5.py` → holds on the patched tree (good)

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
# Req1.1 (POSITIVE CONTROL): bystander non-monotonic coord must not raise.
import numpy as np
from xarray import Dataset
from xarray.core.combine import combine_by_coords

ycoord = ['a', 'c', 'b']  # non-monotonic
data = np.random.rand(7, 3)
ds1 = Dataset(data_vars=dict(data=(['x', 'y'], data[:3, :])),
              coords=dict(x=[1, 2, 3], y=ycoord))
ds2 = Dataset(data_vars=dict(data=(['x', 'y'], data[3:, :])),
              coords=dict(x=[4, 5, 6, 7], y=ycoord))
try:
    actual = combine_by_coords((ds1, ds2))
except ValueError as e:
    print("FAIL: raised ValueError:", e)
    raise SystemExit(1)
print("OK: combine succeeded, result dims:", dict(actual.dims))
raise SystemExit(0)
```

Prepatch bug re-encoded as an attack: `True`.

Instance pydata__xarray-3151: combine_by_coords must restrict post-concat monotonicity validation to actually-concatenated dims (concat_dims) instead of all result dims.

Probes (all HOLD on gold-patched tree):
- probe_1 (Req1.1, POSITIVE CONTROL): bystander non-monotonic coord y=['a','c','b'] shared across inputs; combine must not raise. HOLDS patched, VIOLATED at base (base raises 'Resulting object does not have monotonic global indexes along dimension y'). prepatch_reproduced=true => discriminating power confirmed.
- probe_2 (Req1.3/1.4): shared non-varying y coord retains same values/order; data correctly concatenated along x with no loss/reorder. HOLDS patched.
- probe_3 (Req2.1/2.3): concatenated dim whose GLOBAL index is non-monotonic must still raise ValueError naming the dim. Inputs x=[10,20] and x=[5,15] are each individually monotonic but the concat-ordered global index [5,15,10,20] is non-monotonic -> exercises the retained post-concat check specifically (not the earlier per-dataset check). HOLDS patched.
- probe_4 (Req3.1/3.2): increasing coords sorted by value regardless of input order; decreasing accepted and order preserved. HOLDS patched.
- probe_5 (Req3.3): datasets differing only in data variables merge without raising. HOLDS patched.

Candidate wrong-fix (weak.diff): the lazy reading of Req1 that simply DELETES the post-concat monotonicity loop entirely. It satisfies Req1 (bystander ok) but violates Req2: probe_3 REJECTS it (returns mis-ordered x=[5,15,10,20] instead of raising). This demonstrates the suite discriminates a plausibly-wrong implementation the requirements would otherwise seem to permit if Req2 were ignored. First draft of probe_3 accidentally triggered the earlier per-dataset monotonicity check (which the weak patch keeps), so it was rewritten to hit the specific removed global check; confirmed it now passes patched, fails weak, and (incidentally) also holds at base since base still has the check.

All 5 probes hold on the patched tree; positive control discriminates base vs patched; >=1 candidate exercised and REJECTED. Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Patch changes the monotonicity check loop from `for dim in concatenated.dims: if dim in concatenated` to `for dim in concat_dims`, i.e. only dimensions actually concatenated are validated. Requirements 1-2 pin precisely this observable boundary (bystander dims skipped, concatenated dims still validated) rather than an internal narrow slice. Req3 regression clauses are consistent with unchanged surrounding behavior. Probed on gold-patched instance image: all assertions hold, exit 0.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The requirements describe behavior in EARS form and correctly localize the change to combine_by_coords in xarray/core/combine.py (legitimate). Every concrete detail beyond generic behavior is already public in problem_statement: the non-monotonic example ['a','c','b'] (line 24) matches yCoord = ['a', 'c', 'b'] in the MCVE; the ValueError wording 'monotonic global indexes along dimension' is quoted verbatim in the problem_statement; the 'bystander' / non-varying identical-coordinate contract is quoted from the problem_statement's documentation reference. No hidden-test content is transmitted: no test function name (test_combine_leaving_bystander_dimensions), no test file path (xarray/tests/test_combine.py), no parametrization ids, no gold-invented identifier (the fix's concat_dims / concatenated.dims variables never appear). Req 3.6's mention of string/datetime/numeric coordinates loosely parallels PASS_TO_PASS helper tests but is a generic type-coverage regression clause with no values, ids, or structure reconstructing any test — a behavioral translation, not test transmission. Reqs 2 and 3 translate the monotonicity-still-enforced and regression cases into behavior without mirroring the parametrized case list.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
