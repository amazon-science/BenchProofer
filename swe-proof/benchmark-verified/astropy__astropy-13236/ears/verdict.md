# P2 adversarial audit — astropy__astropy-13236

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

Counterexample / evidence:

```
Under weak.diff (changes `len(data.dtype) > 1` to `> 2`, i.e. only auto-converts structured arrays with >2 fields), a 3-field structured plain ndarray dtype=[('a','i4'),('b','f8'),('c','i2')] is still viewed as NdarrayMixin instead of Column. probe_2 REJECTS this candidate (observed class NdarrayMixin, requires Column per R1.1/R1.2). This partial fix would not resolve the hidden tests, and the probe suite catches it.
```

**Attacks re-run (6):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
"""R1.1 (positive control): a structured plain ndarray added to a Table
becomes an ordinary Column, NOT an NdarrayMixin.
At base this fails (auto-conversion to NdarrayMixin)."""
import sys
import numpy as np
from astropy.table import Table, Column, NdarrayMixin

arr = np.array([(1, 2.0), (3, 4.0)], dtype=[('a', 'i4'), ('b', 'f8')])

ok = True
# construction
t = Table([arr], names=['s'])
c = t['s']
print("construction class:", type(c).__name__)
if not isinstance(c, Column) or isinstance(c, NdarrayMixin):
    ok = False

# item assignment
t2 = Table()
t2['s'] = arr
c2 = t2['s']
print("assignment class:", type(c2).__name__)
if not isinstance(c2, Column) or isinstance(c2, NdarrayMixin):
    ok = False

# add_column
t3 = Table()
t3.add_column(arr, name='s')
c3 = t3['s']
print("add_column class:", type(c3).__name__)
if not isinstance(c3, Column) or isinstance(c3, NdarrayMixin):
    ok = False

sys.exit(0 if ok else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""R1.2 & R1.3: stored Column preserves the structured dtype (field names,
dtypes, order) and element/field access equals the original."""
import sys
import numpy as np
from astropy.table import Table, Column, NdarrayMixin

arr = np.array([(1, 2.0, 3), (4, 5.0, 6)],
               dtype=[('a', 'i4'), ('b', 'f8'), ('c', 'i2')])
t = Table()
t['s'] = arr
c = t['s']
print("class:", type(c).__name__)
print("dtype:", c.dtype)
ok = isinstance(c, Column) and not isinstance(c, NdarrayMixin)

# dtype identical (names, formats, order)
if c.dtype != arr.dtype:
    print("dtype mismatch"); ok = False
if c.dtype.names != arr.dtype.names:
    print("names mismatch"); ok = False

# field access
for f in arr.dtype.names:
    if not np.array_equal(np.asarray(c[f]), arr[f]):
        print("field access mismatch", f); ok = False

# row + combined access
if not (c[0]['a'] == arr[0]['a'] and c[1]['b'] == arr[1]['b']):
    print("combined access mismatch"); ok = False

sys.exit(0 if ok else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""R2: masked structured array -> MaskedColumn with per-field masks preserved
and unmasked values equal to input."""
import sys
import numpy as np
from astropy.table import Table, MaskedColumn

data = np.array([(1, 2.0), (3, 4.0)], dtype=[('a', 'i4'), ('b', 'f8')])
mask = np.array([(True, False), (False, True)],
                dtype=[('a', '?'), ('b', '?')])
marr = np.ma.MaskedArray(data, mask=mask)

t = Table()
t['s'] = marr
c = t['s']
print("class:", type(c).__name__)
ok = isinstance(c, MaskedColumn)

# per-field mask preserved
for f in ['a', 'b']:
    got = np.asarray(c.mask[f])
    want = mask[f]
    print("field", f, "mask got", got, "want", want)
    if not np.array_equal(got, want):
        print("mask mismatch", f); ok = False

# unmasked values equal
for f in ['a', 'b']:
    if not np.array_equal(np.asarray(c[f].data), data[f]):
        print("value mismatch", f); ok = False

sys.exit(0 if ok else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""R3: a value already viewed as NdarrayMixin stays an NdarrayMixin, and
its element/field values equal the original."""
import sys
import numpy as np
from astropy.table import Table, NdarrayMixin

arr = np.array([(1, 2.0), (3, 4.0)], dtype=[('a', 'i4'), ('b', 'f8')])
mix = arr.view(NdarrayMixin)

t = Table()
t['s'] = mix
c = t['s']
print("class:", type(c).__name__)
ok = isinstance(c, NdarrayMixin)

for f in ['a', 'b']:
    if not np.array_equal(np.asarray(c[f]), arr[f]):
        print("field mismatch", f); ok = False
if not (c[0]['a'] == arr[0]['a']):
    print("elem mismatch"); ok = False

sys.exit(0 if ok else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""R4.4 & R4.5 (regression SHALL-keep): non-structured masked array -> MaskedColumn;
plain single/unstructured dtype array -> ordinary Column; Quantity mixin preserved."""
import sys
import numpy as np
from astropy.table import Table, QTable, Column, MaskedColumn, NdarrayMixin
import astropy.units as u

ok = True

# R4.5 plain unstructured array -> Column
t = Table()
t['x'] = np.array([1, 2, 3])
print("plain class:", type(t['x']).__name__)
if not isinstance(t['x'], Column) or isinstance(t['x'], (MaskedColumn, NdarrayMixin)):
    print("plain not Column"); ok = False

# R4.4 non-structured masked -> MaskedColumn
t2 = Table()
t2['m'] = np.ma.MaskedArray([1, 2, 3], mask=[True, False, False])
print("masked class:", type(t2['m']).__name__)
if not isinstance(t2['m'], MaskedColumn):
    print("masked not MaskedColumn"); ok = False

# R4.2 Quantity mixin preserved (QTable route keeps Quantity as mixin)
t3 = QTable()
t3['q'] = np.array([1.0, 2.0]) * u.m
print("quantity class:", type(t3['q']).__name__)
if not isinstance(t3['q'], u.Quantity):
    print("quantity not preserved"); ok = False

sys.exit(0 if ok else 1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
"""R4.6 (SHALL-keep): structured Column supports I/O round trip (ECSV) and
copy/insertion, preserving dtype and values."""
import sys, os, tempfile
import numpy as np
from astropy.table import Table, Column, NdarrayMixin

arr = np.array([(1, 2.0), (3, 4.0)], dtype=[('a', 'i4'), ('b', 'f8')])
t = Table()
t['s'] = arr
ok = isinstance(t['s'], Column) and not isinstance(t['s'], NdarrayMixin)

# ECSV serialization round-trip via temp file
fn = os.path.join(tempfile.mkdtemp(), 'tbl.ecsv')
t.write(fn, format='ascii.ecsv')
t2 = Table.read(fn, format='ascii.ecsv')
print("roundtrip class:", type(t2['s']).__name__)
print("roundtrip dtype:", t2['s'].dtype)
if t2['s'].dtype.names != arr.dtype.names:
    print("roundtrip names mismatch"); ok = False
for f in arr.dtype.names:
    if not np.array_equal(np.asarray(t2['s'][f]), arr[f]):
        print("roundtrip value mismatch", f); ok = False

# copy preserves
tc = t.copy()
if not np.array_equal(np.asarray(tc['s']['a']), arr['a']):
    print("copy mismatch"); ok = False

sys.exit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""R1.1 (positive control): a structured plain ndarray added to a Table
becomes an ordinary Column, NOT an NdarrayMixin.
At base this fails (auto-conversion to NdarrayMixin)."""
import sys
import numpy as np
from astropy.table import Table, Column, NdarrayMixin

arr = np.array([(1, 2.0), (3, 4.0)], dtype=[('a', 'i4'), ('b', 'f8')])

ok = True
# construction
t = Table([arr], names=['s'])
c = t['s']
print("construction class:", type(c).__name__)
if not isinstance(c, Column) or isinstance(c, NdarrayMixin):
    ok = False

# item assignment
t2 = Table()
t2['s'] = arr
c2 = t2['s']
print("assignment class:", type(c2).__name__)
if not isinstance(c2, Column) or isinstance(c2, NdarrayMixin):
    ok = False

# add_column
t3 = Table()
t3.add_column(arr, name='s')
c3 = t3['s']
print("add_column class:", type(c3).__name__)
if not isinstance(c3, Column) or isinstance(c3, NdarrayMixin):
    ok = False

sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Gold patch removes the structured-ndarray->NdarrayMixin special-case in Table._convert_data_to_col. Probe results — PATCHED: all 6 HOLD. BASE: probe_1/2/6 FAIL (class=NdarrayMixin), confirming discriminating power. WEAK (weak.diff, >2 fields): probe_2 REJECTS (NdarrayMixin), probes 1/3/4/5/6 hold — suite discriminates the partial fix. Probe coverage: probe_1=R1.1 (Column via construction/assignment/add_column; positive control); probe_2=R1.2/R1.3 (dtype+field/row access preserved); probe_3=R2 (masked structured -> MaskedColumn, per-field masks); probe_4=R3 (explicit NdarrayMixin retained); probe_5=R4.2/R4.4/R4.5 (Quantity mixin via QTable, non-structured masked -> MaskedColumn, plain array -> Column); probe_6=R4.6 (ECSV I/O roundtrip + copy for structured Column). Two probes initially had test-harness bugs (StringIO write, plain-Table Quantity route), fixed to use temp file and QTable respectively; not requirement violations. No violation found; no probe-conforming alternative patch that resolves was found.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 6 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 6 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

Counterexample / evidence:

```
Under weak.diff (changes `len(data.dtype) > 1` to `> 2`, i.e. only auto-converts structured arrays with >2 fields), a 3-field structured plain ndarray dtype=[('a','i4'),('b','f8'),('c','i2')] is still viewed as NdarrayMixin instead of Column. probe_2 REJECTS this candidate (observed class NdarrayMixin, requires Column per R1.1/R1.2). This partial fix would not resolve the hidden tests, and the probe suite catches it.
```

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
"""R1.1 (positive control): a structured plain ndarray added to a Table
becomes an ordinary Column, NOT an NdarrayMixin.
At base this fails (auto-conversion to NdarrayMixin)."""
import sys
import numpy as np
from astropy.table import Table, Column, NdarrayMixin

arr = np.array([(1, 2.0), (3, 4.0)], dtype=[('a', 'i4'), ('b', 'f8')])

ok = True
# construction
t = Table([arr], names=['s'])
c = t['s']
print("construction class:", type(c).__name__)
if not isinstance(c, Column) or isinstance(c, NdarrayMixin):
    ok = False

# item assignment
t2 = Table()
t2['s'] = arr
c2 = t2['s']
print("assignment class:", type(c2).__name__)
if not isinstance(c2, Column) or isinstance(c2, NdarrayMixin):
    ok = False

# add_column
t3 = Table()
t3.add_column(arr, name='s')
c3 = t3['s']
print("add_column class:", type(c3).__name__)
if not isinstance(c3, Column) or isinstance(c3, NdarrayMixin):
    ok = False

sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Gold patch removes the structured-ndarray->NdarrayMixin special-case in Table._convert_data_to_col. Probe results — PATCHED: all 6 HOLD. BASE: probe_1/2/6 FAIL (class=NdarrayMixin), confirming discriminating power. WEAK (weak.diff, >2 fields): probe_2 REJECTS (NdarrayMixin), probes 1/3/4/5/6 hold — suite discriminates the partial fix. Probe coverage: probe_1=R1.1 (Column via construction/assignment/add_column; positive control); probe_2=R1.2/R1.3 (dtype+field/row access preserved); probe_3=R2 (masked structured -> MaskedColumn, per-field masks); probe_4=R3 (explicit NdarrayMixin retained); probe_5=R4.2/R4.4/R4.5 (Quantity mixin via QTable, non-structured masked -> MaskedColumn, plain array -> Column); probe_6=R4.6 (ECSV I/O roundtrip + copy for structured Column). Two probes initially had test-harness bugs (StringIO write, plain-Table Quantity route), fixed to use temp file and QTable respectively; not requirement violations. No violation found; no probe-conforming alternative patch that resolves was found.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Patch removes the single special-case clause in Table._convert_data_to_col that re-viewed structured ndarrays as NdarrayMixin. Requirement 4 correctly frames all other column-class decisions as unchanged (Column/MaskedColumn upgrade rule, recognized mixins, mixin-scalar sequences, non-structured masked arrays, single/unstructured dtype -> Column, I/O/join/pickle preserved, registered mixin handlers). These are pre-existing behaviors untouched by the one-line deletion, so pinning them as invariants is faithful. G-DIFF-equivalent base probe confirms divergence occurs precisely at R1's structured-plain-array case.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The requirements describe behavior, not the hidden tests. Public problem_statement already discloses: the structured-ndarray→NdarrayMixin auto-transform, the exact code clause, its location in Table._convert_data_to_col (astropy/table/table.py), the Column/NdarrayMixin classes, the serialization rationale, and 'unless already a valid mixin class'. So Req 1 (structured plain→Column) and Req 3 (already-a-mixin stays) are derivable from the public statement.

Req 2 (masked structured → MaskedColumn with per-field masks) corresponds to hidden FAIL_TO_PASS test_structured_masked_column, but it is stated as a general behavioral requirement — it does NOT reproduce the test's specific field names (z/x/y), the specific mask matrix, the function name, or any test id. That is legitimate test→behavior translation, which is the point of the doc.

No leak of: test names/paths (test_ndarray_mixin, test_structured_masked_column, test_mixin.py, test_table.py), parametrization ids ([True]/[False], as_ndarray_mixin), quoted test/gold code, or fix-invented identifiers (the gold patch is a pure deletion and invents none). Req 1.3/1.4 loosely echo access-by-index/field and 'added as init data + assigned column' but these are intrinsic properties of structured columns, not test transcription; no enumeration mirrors the parametrization. Naming the module/function is legitimate localization.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
