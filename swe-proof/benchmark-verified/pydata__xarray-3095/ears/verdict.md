# P2 adversarial audit — pydata__xarray-3095

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
"""R1.1/R1.2: IndexVariable.copy(deep) preserves recorded <U dtype (not object)."""
import numpy as np
import xarray as xr
from xarray.core.variable import IndexVariable

v = IndexVariable('x', np.array(['a', 'bb', 'ccc']))
orig = v.dtype
print("original dtype:", orig)
assert orig.kind == 'U', "sanity: original should be fixed-width unicode, got %r" % orig
ok = True
for deep in (True, False):
    c = v.copy(deep=deep)
    print("deep=%s copy dtype: %s" % (deep, c.dtype))
    if c.dtype != orig:
        print("  MISMATCH: expected %r got %r" % (orig, c.dtype))
        ok = False
    if c.dtype == np.dtype('O'):
        print("  WIDENED to object!")
        ok = False
import sys
sys.exit(0 if ok else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""R1.3: copy dtype equals original for float/int/unicode (not re-derived from index)."""
import numpy as np
import xarray as xr
from xarray.core.variable import IndexVariable
import sys

cases = {
    'float': np.array([1.0, 2.0, 3.0]),
    'int': np.array([1, 2, 3]),
    'str': np.array(['a', 'bb', 'ccc']),
}
ok = True
for name, arr in cases.items():
    v = IndexVariable('x', arr)
    for deep in (True, False):
        c = v.copy(deep=deep)
        print("%s deep=%s: orig=%s copy=%s" % (name, deep, v.dtype, c.dtype))
        if c.dtype != v.dtype:
            print("  MISMATCH")
            ok = False
sys.exit(0 if ok else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""R2: PandasIndexAdapter.copy exists; deep copy duplicates backing, preserves dtype+values."""
import numpy as np
import sys
from xarray.core.indexing import PandasIndexAdapter

a = PandasIndexAdapter(np.array(['a', 'bb', 'ccc']))
print("adapter dtype:", a.dtype)
assert hasattr(a, 'copy'), "R2.1: PandasIndexAdapter has no copy method"
ok = True

# deep copy
d = a.copy(deep=True)
print("deep copy dtype:", d.dtype)
if d.dtype != a.dtype:
    print("  dtype mismatch"); ok = False
if not np.array_equal(np.asarray(d), np.asarray(a)):
    print("  values mismatch"); ok = False
# distinct backing storage (not the same underlying pandas.Index object)
if d.array is a.array:
    print("  R2.2: deep copy shares backing index object"); ok = False

# shallow copy
s = a.copy(deep=False)
print("shallow copy dtype:", s.dtype)
if s.dtype != a.dtype:
    print("  dtype mismatch"); ok = False
if not np.array_equal(np.asarray(s), np.asarray(a)):
    print("  values mismatch"); ok = False

sys.exit(0 if ok else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""R3: copy is identical (dims/attrs/values/dtype) incl copy.copy/deepcopy for str index."""
import copy as _copy
import numpy as np
import sys
from xarray.core.variable import IndexVariable

v = IndexVariable('x', np.array(['a', 'bb', 'ccc']), attrs={'foo': 'bar'})
ok = True

for label, c in [
    ('copy(deep=True)', v.copy(deep=True)),
    ('copy(deep=False)', v.copy(deep=False)),
    ('copy.copy', _copy.copy(v)),
    ('copy.deepcopy', _copy.deepcopy(v)),
]:
    identical = v.identical(c)
    print("%s: identical=%s dtype=%s dims=%s attrs=%s" % (label, identical, c.dtype, c.dims, c.attrs))
    if not identical:
        print("  NOT identical"); ok = False
    if c.dtype != v.dtype:
        print("  dtype mismatch"); ok = False

sys.exit(0 if ok else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""R4: regression protection for ordinary Variable deep/shallow sharing + replacement data."""
import numpy as np
import sys
from xarray.core.variable import Variable

ok = True
data = np.array([1.0, 2.0, 3.0])
v = Variable('x', data, attrs={'a': 1})

# R4.1 deep copy => distinct buffer
dc = v.copy(deep=True)
share_deep = np.shares_memory(dc.data, v.data)
print("deep: shares_memory=%s dtype=%s" % (share_deep, dc.dtype))
if share_deep:
    print("  R4.1 deep copy shares storage!"); ok = False
if dc.dtype != v.dtype or not np.array_equal(dc.values, v.values) or dc.dims != v.dims or dict(dc.attrs) != dict(v.attrs):
    print("  R4.1 metadata/values mismatch"); ok = False

# R4.2 shallow copy => shares buffer
sc = v.copy(deep=False)
share_shallow = np.shares_memory(sc.data, v.data)
print("shallow: shares_memory=%s dtype=%s" % (share_shallow, sc.dtype))
if not share_shallow:
    print("  R4.2 shallow copy does NOT share storage!"); ok = False

# R4.4 replacement data
rep = v.copy(data=np.array([9.0, 8.0, 7.0]))
print("replacement values:", rep.values, "dims:", rep.dims, "attrs:", dict(rep.attrs))
if not np.array_equal(rep.values, [9.0, 8.0, 7.0]) or rep.dims != v.dims or dict(rep.attrs) != dict(v.attrs):
    print("  R4.4 replacement mismatch"); ok = False
# R4.4 shape mismatch raises
raised = False
try:
    v.copy(data=np.array([1.0, 2.0]))
except ValueError:
    raised = True
print("shape-mismatch raised:", raised)
if not raised:
    print("  R4.4 no error on bad shape"); ok = False

# R4.5 default is deep
default_c = v.copy()
print("default copy shares_memory:", np.shares_memory(default_c.data, v.data))
if np.shares_memory(default_c.data, v.data):
    print("  R4.5 default not deep!"); ok = False

sys.exit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""R1.1/R1.2: IndexVariable.copy(deep) preserves recorded <U dtype (not object)."""
import numpy as np
import xarray as xr
from xarray.core.variable import IndexVariable

v = IndexVariable('x', np.array(['a', 'bb', 'ccc']))
orig = v.dtype
print("original dtype:", orig)
assert orig.kind == 'U', "sanity: original should be fixed-width unicode, got %r" % orig
ok = True
for deep in (True, False):
    c = v.copy(deep=deep)
    print("deep=%s copy dtype: %s" % (deep, c.dtype))
    if c.dtype != orig:
        print("  MISMATCH: expected %r got %r" % (orig, c.dtype))
        ok = False
    if c.dtype == np.dtype('O'):
        print("  WIDENED to object!")
        ok = False
import sys
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

5 distinct probes, all HOLD on gold-patched tree; all exercised.

Probe->requirement mapping and results (PATCHED / BASE):
- probe_1 (R1.1,R1.2): IndexVariable.copy(deep=True/False) keeps recorded <U3 dtype, not widened to object. PATCHED exit0 / BASE exit1 (deep=True copy widened to object). POSITIVE CONTROL — discriminates.
- probe_2 (R1.3,R1.4): copy dtype equals original for float/int/str x deep/shallow (not re-derived from index). PATCHED exit0.
- probe_3 (R2.1-2.4): PandasIndexAdapter.copy exists; deep copy has distinct backing index object, preserves dtype+values; shallow preserves dtype+values. PATCHED exit0 / BASE exit1 (no copy method).
- probe_4 (R3.1-3.3): copy(deep=T/F), copy.copy, copy.deepcopy all identical() to original with same dtype/dims/attrs. PATCHED exit0 / BASE exit1 (copy.deepcopy dtype=object).
- probe_5 (R4.1,4.2,4.4,4.5): ordinary Variable deep copy => distinct buffer, shallow => shared buffer; replacement data honored w/ dims/attrs preserved and shape-mismatch raises; default copy is deep. PATCHED exit0.

CANDIDATE PATCH (weak.diff): fixes IndexVariable.copy inline by forwarding self._data._dtype to a new PandasIndexAdapter (dtype preserved) BUT does NOT add PandasIndexAdapter.copy — a lazy reading that satisfies the observable dtype behavior of R1/R3 while violating R2's explicit mandate that the adapter provide its own copy method. Result under weak.diff: probes 1,2,4,5 HOLD (exit0) but probe_3 REJECTS it (exit1: 'PandasIndexAdapter has no copy method'). This demonstrates the suite discriminates a wrong/partial implementation, and specifically that R2 is load-bearing and enforced.

Positive control reproduced the prepatch bug at base (dtype widened to object). Verdict SOUND: >=5 probes hold on patched tree, positive control discriminates base vs patched, and >=1 candidate patch was constructed and REJECTED by the suite.

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
"""R1.1/R1.2: IndexVariable.copy(deep) preserves recorded <U dtype (not object)."""
import numpy as np
import xarray as xr
from xarray.core.variable import IndexVariable

v = IndexVariable('x', np.array(['a', 'bb', 'ccc']))
orig = v.dtype
print("original dtype:", orig)
assert orig.kind == 'U', "sanity: original should be fixed-width unicode, got %r" % orig
ok = True
for deep in (True, False):
    c = v.copy(deep=deep)
    print("deep=%s copy dtype: %s" % (deep, c.dtype))
    if c.dtype != orig:
        print("  MISMATCH: expected %r got %r" % (orig, c.dtype))
        ok = False
    if c.dtype == np.dtype('O'):
        print("  WIDENED to object!")
        ok = False
import sys
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

5 distinct probes, all HOLD on gold-patched tree; all exercised.

Probe->requirement mapping and results (PATCHED / BASE):
- probe_1 (R1.1,R1.2): IndexVariable.copy(deep=True/False) keeps recorded <U3 dtype, not widened to object. PATCHED exit0 / BASE exit1 (deep=True copy widened to object). POSITIVE CONTROL — discriminates.
- probe_2 (R1.3,R1.4): copy dtype equals original for float/int/str x deep/shallow (not re-derived from index). PATCHED exit0.
- probe_3 (R2.1-2.4): PandasIndexAdapter.copy exists; deep copy has distinct backing index object, preserves dtype+values; shallow preserves dtype+values. PATCHED exit0 / BASE exit1 (no copy method).
- probe_4 (R3.1-3.3): copy(deep=T/F), copy.copy, copy.deepcopy all identical() to original with same dtype/dims/attrs. PATCHED exit0 / BASE exit1 (copy.deepcopy dtype=object).
- probe_5 (R4.1,4.2,4.4,4.5): ordinary Variable deep copy => distinct buffer, shallow => shared buffer; replacement data honored w/ dims/attrs preserved and shape-mismatch raises; default copy is deep. PATCHED exit0.

CANDIDATE PATCH (weak.diff): fixes IndexVariable.copy inline by forwarding self._data._dtype to a new PandasIndexAdapter (dtype preserved) BUT does NOT add PandasIndexAdapter.copy — a lazy reading that satisfies the observable dtype behavior of R1/R3 while violating R2's explicit mandate that the adapter provide its own copy method. Result under weak.diff: probes 1,2,4,5 HOLD (exit0) but probe_3 REJECTS it (exit1: 'PandasIndexAdapter has no copy method'). This demonstrates the suite discriminates a wrong/partial implementation, and specifically that R2 is load-bearing and enforced.

Positive control reproduced the prepatch bug at base (dtype widened to object). Verdict SOUND: >=5 probes hold on patched tree, positive control discriminates base vs patched, and >=1 candidate patch was constructed and REJECTED by the suite.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Gold patch adds PandasIndexAdapter.copy(deep) which forwards self._dtype and duplicates the pandas.Index only when deep, and rewrites IndexVariable.copy to call self._data.copy(deep=deep). Requirements pin exactly the changed observable behavior (recorded dtype preservation across all copy paths) rather than a narrow slice. R2's adapter-copy modeling is the actual code change, not an over-narrow helper pin, since the changed behavior lives precisely in that helper. Probe on gold-patched tree: HOLDS (exit 0), base VIOLATED.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Requirements localize the change to PandasIndexAdapter (indexing.py) and IndexVariable.copy (variable.py) and describe adding a dtype-preserving copy method on the adapter — all legitimate module/function naming and behavior translation of the gold edit. No verbatim gold code (the pickle-size comment, np.dtype(dtype) coercion, DTypeLike import) is quoted, and no fix-invented identifiers leak beyond the obvious 'copy' method name (a natural API name). No test file paths, class/function names (TestIndexVariable, test_copy), or parametrization ids (str-True, etc.) appear. The one borderline item is the repeated enumeration 'floating-point, integer, or fixed-width unicode dtype' crossed with 'deep=True or deep=False' (Req 3.3, 4.3), which parallels the hidden test's parametrize(astype=[float,int,str]) x parametrize(deep=[True,False]). However this reads as a natural generalization of 'preserve the recorded dtype for any element type' (only the unicode case is in the public problem_statement; float/int are ordinary examples), and it transmits no test artifact — it describes behavior rather than reconstructing the tests. Verdict: NO-LEAKAGE.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
