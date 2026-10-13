# P2 adversarial audit — astropy__astropy-14539

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 6 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 6 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 6 | `probe_pc.py`, `probe_diff.py`, `probe_pq_parity.py`, `probe_report.py`, `probe_mixed.py`, `probe_regression_P.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_pc.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (6):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_pc.py` → holds on the patched tree (good)

```python
# Positive control: a FITS table with a Q-format (64-bit) VLA column compared
# to itself must report NO data differences. Encodes Req 2.1/2.2.
import numpy as np
from astropy.io import fits
from astropy.io.fits.diff import TableDataDiff, FITSDiff

# Build a Q-format VLA column (QJ = 64-bit descriptor, integer VLA)
c = fits.Column(name='qvla', format='QJ()', array=np.array(
    [np.array([1,2,3]), np.array([4,5]), np.array([6,7,8,9])], dtype=object))
hdu = fits.BinTableHDU.from_columns([c])
data = hdu.data

print("column format:", hdu.columns[0].format)
assert 'Q' in hdu.columns[0].format, "not a Q-format column"

diff = TableDataDiff(data, data)
print("identical:", diff.identical, "diff_total:", diff.diff_total, "diff_ratio:", diff.diff_ratio)
ok = (diff.identical is True) and (diff.diff_total == 0) and (diff.diff_ratio == 0)

# also via FITSDiff on the whole HDU
h1 = fits.HDUList([fits.PrimaryHDU(), hdu])
fd = FITSDiff(h1, h1)
print("FITSDiff identical:", fd.identical)
ok = ok and fd.identical

print("RESULT_OK" if ok else "RESULT_FAIL")
import sys; sys.exit(0 if ok else 1)
```

Attack 2 — `probe_diff.py` → holds on the patched tree (good)

```python
# Req 3.1/3.2/3.3/3.4: genuine per-row Q-VLA differences reported correctly.
import numpy as np
from astropy.io.fits import Column, BinTableHDU
from astropy.io.fits.diff import TableDataDiff

def mk(rows):
    c = Column(name='qvla', format='QJ()', array=np.array(rows, dtype=object))
    return BinTableHDU.from_columns([c]).data

a = mk([np.array([1,2,3]), np.array([4,5,5]), np.array([6,7,8,9])])
b = mk([np.array([1,2,3]), np.array([9,9,9]), np.array([6,7,0,9])])  # rows 1 and 2 differ

d = TableDataDiff(a, b)
print("diff_values:", d.diff_values)
print("diff_total:", d.diff_total, "diff_ratio:", d.diff_ratio)
recorded_idxs = [k[1] for (k, v) in d.diff_values]
recorded_names = [k[0] for (k, v) in d.diff_values]
ok = (d.diff_total == 2)                       # two differing rows counted once each (3.3)
ok = ok and recorded_idxs == [1, 2]            # increasing row idx ordering (3.2)
ok = ok and all(n == 'qvla' for n in recorded_names)  # identified by column name (3.1)
ok = ok and abs(d.diff_ratio - (2.0/3.0)) < 1e-12     # ratio = total/(nrows*ncols) (3.4)
ok = ok and (d.identical is False)
print("RESULT_OK" if ok else "RESULT_FAIL")
import sys; sys.exit(0 if ok else 1)
```

Attack 3 — `probe_pq_parity.py` → holds on the patched tree (good)

```python
# Req 1.3 / 3.2: Q descriptor treated exactly like P under same conditions.
import numpy as np
from astropy.io.fits import Column, BinTableHDU
from astropy.io.fits.diff import TableDataDiff

def mk(fmt, rows):
    c = Column(name='v', format=fmt, array=np.array(rows, dtype=object))
    return BinTableHDU.from_columns([c]).data

rowsa = [np.array([1,2,3]), np.array([4,5,5]), np.array([6,7,8,9])]
rowsb = [np.array([1,2,3]), np.array([9,9,9]), np.array([6,7,8,9])]  # row 1 differs

dp = TableDataDiff(mk('PJ()', rowsa), mk('PJ()', rowsb))
dq = TableDataDiff(mk('QJ()', rowsa), mk('QJ()', rowsb))
print("P:", dp.diff_total, dp.diff_ratio, [k for k,_ in dp.diff_values])
print("Q:", dq.diff_total, dq.diff_ratio, [k for k,_ in dq.diff_values])
ok = (dp.diff_total == dq.diff_total == 1)
ok = ok and (dp.diff_ratio == dq.diff_ratio)
ok = ok and ([k[1] for k,_ in dp.diff_values] == [k[1] for k,_ in dq.diff_values] == [1])
ok = ok and (dp.identical == dq.identical == False)
print("RESULT_OK" if ok else "RESULT_FAIL")
import sys; sys.exit(0 if ok else 1)
```

Attack 4 — `probe_report.py` → holds on the patched tree (good)

```python
# Req 3.5: report states # differing elements and percentage consistent w/ ratio.
import numpy as np, re, sys
from astropy.io.fits import Column, BinTableHDU
from astropy.io.fits.diff import TableDataDiff
def mk(qrows):
    c = Column(name='q', format='QJ()', array=np.array(qrows, dtype=object))
    return BinTableHDU.from_columns([c]).data
a = mk([np.array([1,2]), np.array([3,4,5]), np.array([6]), np.array([7,8])])
b = mk([np.array([1,2]), np.array([9,9,9]), np.array([6]), np.array([7,8])])  # row1 diff
d = TableDataDiff(a, b)
report = d.report()
pct = 100.0 * d.diff_ratio
print("total:", d.diff_total, "ratio:", d.diff_ratio, "expected pct:", pct)
m = re.search(r'(\d+)\s+different table data element', report)
found_count = int(m.group(1)) if m else None
mp = re.search(r'\(([\d.]+)%\s+different\)', report)
found_pct = float(mp.group(1)) if mp else None
print("report count=", found_count, "pct=", found_pct)
ok = (found_count == d.diff_total == 1)
ok = ok and (found_pct is not None) and abs(found_pct - pct) < 0.05
print("RESULT_OK" if ok else "RESULT_FAIL")
sys.exit(0 if ok else 1)
```

Attack 5 — `probe_mixed.py` → holds on the patched tree (good)

```python
# Req 4.2/4.3 + 2.3: mix ordinary columns (int, real, complex, 32-bit VLA) with
# a 64-bit VLA column; verdict/total/ratio/recorded diffs correct together.
import numpy as np
from astropy.io.fits import Column, BinTableHDU
from astropy.io.fits.diff import TableDataDiff

def mk(qrows, ints, reals):
    cols = [
        Column(name='i', format='J', array=np.array(ints, dtype=np.int32)),
        Column(name='x', format='E', array=np.array(reals, dtype=np.float32)),
        Column(name='q', format='QJ()', array=np.array(qrows, dtype=object)),
    ]
    return BinTableHDU.from_columns(cols).data

qa = [np.array([1,2]), np.array([3,4,5]), np.array([6])]
qb = [np.array([1,2]), np.array([3,4,5]), np.array([9])]   # q row 2 differs
a = mk(qa, [10,20,30], [1.0, 2.0, 3.0])
b = mk(qb, [10,99,30], [1.0, 2.0, 3.0])                     # i row 1 differs

d = TableDataDiff(a, b)
print("diff_values:", d.diff_values)
print("total:", d.diff_total, "ratio:", d.diff_ratio, "identical:", d.identical)
keys = [k for k,_ in d.diff_values]
# two diffs total: (i,1) and (q,2). column-major ordering: i before q.
ok = (d.diff_total == 2) and (d.identical is False)
ok = ok and keys == [('i', 1), ('q', 2)]
# ratio = 2 / (3 rows * 3 cols) = 2/9
ok = ok and abs(d.diff_ratio - (2.0/9.0)) < 1e-12
# float column with tolerance still not flagged (identical reals)
print("RESULT_OK" if ok else "RESULT_FAIL")
import sys; sys.exit(0 if ok else 1)
```

Attack 6 — `probe_regression_P.py` → holds on the patched tree (good)

```python
# Req 4.1: 32-bit P VLA identical inputs still report identical (row-wise).
import numpy as np
from astropy.io.fits import Column, BinTableHDU
from astropy.io.fits.diff import TableDataDiff
c = Column(name='p', format='PJ()', array=np.array(
    [np.array([1,2]), np.array([3,4,5]), np.array([6])], dtype=object))
data = BinTableHDU.from_columns([c]).data
d = TableDataDiff(data, data)
print("P identical:", d.identical, d.diff_total, d.diff_ratio)
ok = (d.identical is True) and d.diff_total == 0 and d.diff_ratio == 0
print("RESULT_OK" if ok else "RESULT_FAIL")
import sys; sys.exit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_pc.py`

```python
# Positive control: a FITS table with a Q-format (64-bit) VLA column compared
# to itself must report NO data differences. Encodes Req 2.1/2.2.
import numpy as np
from astropy.io import fits
from astropy.io.fits.diff import TableDataDiff, FITSDiff

# Build a Q-format VLA column (QJ = 64-bit descriptor, integer VLA)
c = fits.Column(name='qvla', format='QJ()', array=np.array(
    [np.array([1,2,3]), np.array([4,5]), np.array([6,7,8,9])], dtype=object))
hdu = fits.BinTableHDU.from_columns([c])
data = hdu.data

print("column format:", hdu.columns[0].format)
assert 'Q' in hdu.columns[0].format, "not a Q-format column"

diff = TableDataDiff(data, data)
print("identical:", diff.identical, "diff_total:", diff.diff_total, "diff_ratio:", diff.diff_ratio)
ok = (diff.identical is True) and (diff.diff_total == 0) and (diff.diff_ratio == 0)

# also via FITSDiff on the whole HDU
h1 = fits.HDUList([fits.PrimaryHDU(), hdu])
fd = FITSDiff(h1, h1)
print("FITSDiff identical:", fd.identical)
ok = ok and fd.identical

print("RESULT_OK" if ok else "RESULT_FAIL")
import sys; sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance fixes TableDataDiff._diff to treat 64-bit VLA descriptor kind (Q format) row-wise like the 32-bit (P) kind (gold: `elif "P" in col.format or "Q" in col.format:`).

Probes (all HOLD on gold-patched tree):
- probe_pc.py (POSITIVE CONTROL; Req 2.1/2.2): a QJ() VLA column compared to itself -> TableDataDiff.identical=True, diff_total=0, diff_ratio=0, and FITSDiff self-compare identical. HOLDS patched, FAILS at base (base raises ValueError 'truth value of an array with more than one element is ambiguous' from `np.where(arra != arrb)`, since Q falls through to the flat comparison). prepatch_reproduced=true.
- probe_diff.py (Req 3.1/3.2/3.3/3.4): Q-VLA with rows 1 and 2 differing (equal-length rows to avoid the pre-existing ragged allclose limitation shared by base+gold) -> diff_values keyed ('qvla',1),('qvla',2) in increasing-row order, diff_total=2, diff_ratio=2/3, identical=False.
- probe_pq_parity.py (Req 1.3/3.2): identical inputs to P and Q columns produce identical diff_total, diff_ratio, recorded keys, and verdict.
- probe_report.py (Req 3.5): report() text states '1 different table data element(s)' and '(25.00% different)', consistent with diff_ratio=0.25.
- probe_mixed.py (Req 4.2/4.3/2.3): int + float(E) + QJ() columns together; only (i,1) and (q,2) recorded in column-major then row order, diff_total=2, diff_ratio=2/9, float column with equal reals not flagged.
- probe_regression_P.py (Req 4.1): 32-bit PJ() VLA self-compare still identical (unchanged).

Candidate wrong patch (weak_A.diff, applies at base_commit): the lazy fix that only wraps the flat-comparison `np.where(arra != arrb)` fallback in try/except ValueError -> empty diffs. This satisfies the identical-inputs requirement (no crash, reports identical) and the P-regression, so it PASSES the positive control and probe_regression_P. But it never applies the row-wise strategy to Q columns, so genuine differences are silently dropped. The suite REJECTS it on 4 probes: probe_diff (0 diffs vs 2), probe_pq_parity (Q=0 vs P=1), probe_report (no diff text), probe_mixed (misses the q-column diff -> total 1 not 2, wrong ratio). This demonstrates the probe suite discriminates a requirements-plausible wrong fix from the gold behavior.

All 6 probes HOLD on the patched tree; positive control discriminates base->fail, patched->hold; >=1 candidate exercised and REJECTED. SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 6 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 6 | `probe_pc.py`, `probe_diff.py`, `probe_pq_parity.py`, `probe_report.py`, `probe_mixed.py`, `probe_regression_P.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_pc.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (6):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

_The 6 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts, and on this backend both roles put it through the same derivation: every block below is a requirement probe run on the gold-patched tree, and the `machine verdict:` line each role publishes above reports BOTH that its probes hold there and how many candidate patches the probe suite rejected — so the two roles re-ran ONE probe suite and each recorded its own outcome for every probe in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `probe_pc.py` → holds on the patched tree (good)

Attack 2 — `probe_diff.py` → holds on the patched tree (good)

Attack 3 — `probe_pq_parity.py` → holds on the patched tree (good)

Attack 4 — `probe_report.py` → holds on the patched tree (good)

Attack 5 — `probe_mixed.py` → holds on the patched tree (good)

Attack 6 — `probe_regression_P.py` → holds on the patched tree (good)

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_pc.py`

```python
# Positive control: a FITS table with a Q-format (64-bit) VLA column compared
# to itself must report NO data differences. Encodes Req 2.1/2.2.
import numpy as np
from astropy.io import fits
from astropy.io.fits.diff import TableDataDiff, FITSDiff

# Build a Q-format VLA column (QJ = 64-bit descriptor, integer VLA)
c = fits.Column(name='qvla', format='QJ()', array=np.array(
    [np.array([1,2,3]), np.array([4,5]), np.array([6,7,8,9])], dtype=object))
hdu = fits.BinTableHDU.from_columns([c])
data = hdu.data

print("column format:", hdu.columns[0].format)
assert 'Q' in hdu.columns[0].format, "not a Q-format column"

diff = TableDataDiff(data, data)
print("identical:", diff.identical, "diff_total:", diff.diff_total, "diff_ratio:", diff.diff_ratio)
ok = (diff.identical is True) and (diff.diff_total == 0) and (diff.diff_ratio == 0)

# also via FITSDiff on the whole HDU
h1 = fits.HDUList([fits.PrimaryHDU(), hdu])
fd = FITSDiff(h1, h1)
print("FITSDiff identical:", fd.identical)
ok = ok and fd.identical

print("RESULT_OK" if ok else "RESULT_FAIL")
import sys; sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance fixes TableDataDiff._diff to treat 64-bit VLA descriptor kind (Q format) row-wise like the 32-bit (P) kind (gold: `elif "P" in col.format or "Q" in col.format:`).

Probes (all HOLD on gold-patched tree):
- probe_pc.py (POSITIVE CONTROL; Req 2.1/2.2): a QJ() VLA column compared to itself -> TableDataDiff.identical=True, diff_total=0, diff_ratio=0, and FITSDiff self-compare identical. HOLDS patched, FAILS at base (base raises ValueError 'truth value of an array with more than one element is ambiguous' from `np.where(arra != arrb)`, since Q falls through to the flat comparison). prepatch_reproduced=true.
- probe_diff.py (Req 3.1/3.2/3.3/3.4): Q-VLA with rows 1 and 2 differing (equal-length rows to avoid the pre-existing ragged allclose limitation shared by base+gold) -> diff_values keyed ('qvla',1),('qvla',2) in increasing-row order, diff_total=2, diff_ratio=2/3, identical=False.
- probe_pq_parity.py (Req 1.3/3.2): identical inputs to P and Q columns produce identical diff_total, diff_ratio, recorded keys, and verdict.
- probe_report.py (Req 3.5): report() text states '1 different table data element(s)' and '(25.00% different)', consistent with diff_ratio=0.25.
- probe_mixed.py (Req 4.2/4.3/2.3): int + float(E) + QJ() columns together; only (i,1) and (q,2) recorded in column-major then row order, diff_total=2, diff_ratio=2/9, float column with equal reals not flagged.
- probe_regression_P.py (Req 4.1): 32-bit PJ() VLA self-compare still identical (unchanged).

Candidate wrong patch (weak_A.diff, applies at base_commit): the lazy fix that only wraps the flat-comparison `np.where(arra != arrb)` fallback in try/except ValueError -> empty diffs. This satisfies the identical-inputs requirement (no crash, reports identical) and the P-regression, so it PASSES the positive control and probe_regression_P. But it never applies the row-wise strategy to Q columns, so genuine differences are silently dropped. The suite REJECTS it on 4 probes: probe_diff (0 diffs vs 2), probe_pq_parity (Q=0 vs P=1), probe_report (no diff text), probe_mixed (misses the q-column diff -> total 1 not 2, wrong ratio). This demonstrates the probe suite discriminates a requirements-plausible wrong fix from the gold behavior.

All 6 probes HOLD on the patched tree; positive control discriminates base->fail, patched->hold; >=1 candidate exercised and REJECTED. SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Patch is a single-token change adding 'Q' to the existing 'P' VLA branch. Requirement 1's qualifier 'not floating-point-typed' correctly reflects the preceding float-dtype elif; because a VLA column's numpy dtype is object (not np.floating), the float branch never captures VLAs and the P/Q branch handles them — verified with QD (double element) VLA reaching the row-wise branch. R3.2 ordering (column-major then row-index) and R3.5 report text follow from the unchanged surrounding loop, which the patch does not alter. Base-commit probe confirms the pre-patch defect (Q VLA falls through to np.where(arra!=arrb) and raises/misreports). No requirement mandates behavior absent from the patched code, forbids behavior present, or pins a wrong/narrow boundary.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The requirements describe the P/Q VLA-descriptor fix behaviorally. The core defect (Q-format VLA falsely reported as different, e.g. comparing a QD-column file to itself) is already public in problem_statement, which includes the QD reproduction script. Naming TableDataDiff._diff / diff.py / diff_values / diff_total / diff_ratio is legitimate localization (matches the gold edit site but doesn't quote it — gold is just adding 'or "Q" in col.format'). No leaked test artifacts: no test names (test_identical_tables/test_different_table_data), no column ids (A-K, QJ(2)/PI(2)), no parametrized magic numbers (13/15, 0.65/0.682, 65.00%/68.18%). Req 3.4/3.5 state the ratio formula and report format generically (behavior, not the specific values). Req 4.3's column-kind list (logical/bit/byte/integer/real/complex/32-bit VLA) reflects the FITS format universe in the existing source, not a test-only enumeration. No fix-invented identifiers. Requirements translate test-checked behavior into behavioral obligations, which is the intended purpose.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
