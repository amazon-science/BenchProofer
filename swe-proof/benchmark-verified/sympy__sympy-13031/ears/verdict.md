# P2 adversarial audit — sympy__sympy-13031

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
Partial patch fixing only row_join (horizontal) leaves col_join/vstack broken: vstack(0x0,1x0,2x0,3x0) yields shape (3,0) instead of (6,0). Rejected by probe_2 (Req 3.3).
```

**Attacks re-run (6):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
# Req1.3 + positive control: hstack of zero-row matrices 0x0,0x1,0x2,0x3 -> (0,6)
import sys
from sympy import SparseMatrix
Ms = [SparseMatrix.zeros(0, c) for c in (0, 1, 2, 3)]
r = SparseMatrix.hstack(*Ms)
print("hstack shape:", r.shape)
ok = r.shape == (0, 6)
print("OK" if ok else "FAIL")
sys.exit(0 if ok else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
# Req3.3: vstack of zero-col matrices 0x0,1x0,2x0,3x0 -> (6,0)
import sys
from sympy import SparseMatrix
Ms = [SparseMatrix.zeros(r, 0) for r in (0, 1, 2, 3)]
r = SparseMatrix.vstack(*Ms)
print("vstack shape:", r.shape)
ok = r.shape == (6, 0)
print("OK" if ok else "FAIL")
sys.exit(0 if ok else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
# Req2.1: left operand zero cols, differing rows -> result equals right operand shape+entries
import sys
from sympy import SparseMatrix
L = SparseMatrix.zeros(2, 0)          # 2x0
R = SparseMatrix([[1, 2], [3, 4], [5, 6]])  # 3x2
res = L.row_join(R)
print("row_join shape:", res.shape, "expected", R.shape)
ok = (res.shape == R.shape) and (res == R)
# also hstack path
res2 = SparseMatrix.hstack(SparseMatrix.zeros(2, 0), R)
print("hstack shape:", res2.shape)
ok = ok and res2.shape == R.shape and res2 == R
print("OK" if ok else "FAIL")
sys.exit(0 if ok else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
# Req4.1: top operand zero rows, differing cols -> result equals bottom operand shape+entries
import sys
from sympy import SparseMatrix
T = SparseMatrix.zeros(0, 3)          # 0x3
B = SparseMatrix([[1, 2], [3, 4]])    # 2x2
res = T.col_join(B)
print("col_join shape:", res.shape, "expected", B.shape)
ok = (res.shape == B.shape) and (res == B)
res2 = SparseMatrix.vstack(SparseMatrix.zeros(0, 3), B)
print("vstack shape:", res2.shape)
ok = ok and res2.shape == B.shape and res2 == B
print("OK" if ok else "FAIL")
sys.exit(0 if ok else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
# Req1.1/1.4 + Req5: ordinary horizontal join sums cols, entries placed, class preserved
import sys
from sympy import SparseMatrix
A = SparseMatrix([[1, 2], [3, 4]])   # 2x2
B = SparseMatrix([[5], [6]])         # 2x1
res = A.row_join(B)
print("shape:", res.shape, "type:", type(res).__name__)
ok = res.shape == (2, 3)
ok = ok and res[0,0]==1 and res[0,1]==2 and res[0,2]==5 and res[1,2]==6
ok = ok and isinstance(res, SparseMatrix)
# Req5.2: shape mismatch when left has nonzero cols and rows differ
try:
    A.row_join(SparseMatrix([[9]]))  # 1x1 rows differ
    print("no error raised - FAIL")
    ok = False
except Exception as e:
    print("raised:", type(e).__name__)
print("OK" if ok else "FAIL")
sys.exit(0 if ok else 1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
# Req3.1/3.4 + Req5.3: ordinary vertical join sums rows, entries placed, class + mismatch
import sys
from sympy import SparseMatrix
A = SparseMatrix([[1, 2], [3, 4]])   # 2x2
B = SparseMatrix([[5, 6]])           # 1x2
res = A.col_join(B)
print("shape:", res.shape, "type:", type(res).__name__)
ok = res.shape == (3, 2)
ok = ok and res[0,0]==1 and res[2,0]==5 and res[2,1]==6
ok = ok and isinstance(res, SparseMatrix)
# Req5.3: mismatch when top has nonzero rows and cols differ
try:
    A.col_join(SparseMatrix([[9]]))  # 1x1
    print("no error - FAIL")
    ok = False
except Exception as e:
    print("raised:", type(e).__name__)
print("OK" if ok else "FAIL")
sys.exit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
# Req1.3 + positive control: hstack of zero-row matrices 0x0,0x1,0x2,0x3 -> (0,6)
import sys
from sympy import SparseMatrix
Ms = [SparseMatrix.zeros(0, c) for c in (0, 1, 2, 3)]
r = SparseMatrix.hstack(*Ms)
print("hstack shape:", r.shape)
ok = r.shape == (0, 6)
print("OK" if ok else "FAIL")
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

6 distinct probes cover Req1.3 (probe_1, positive control: hstack 0x0,0x1,0x2,0x3 -> (0,6)), Req3.3 (probe_2, vstack -> (6,0)), Req2.1 (probe_3, zero-col left operand w/ differing rows returns right operand), Req4.1 (probe_4, zero-row top operand w/ differing cols returns bottom operand), Req1.1/1.4/5.1/5.2 (probe_5: horizontal sum+entry placement+class+ShapeError), Req3.1/3.4/5.1/5.3 (probe_6: vertical sum+entry placement+class+ShapeError). All 6 HOLD on gold-patched tree. Positive controls probe_1 and probe_2 FAIL at base (base gives (0,3) and (3,0) respectively) — discriminating power confirmed. Candidate wrong patch (horizontal-only, weak.diff) applies at base_commit and is REJECTED by probe_2, demonstrating the suite discriminates partial fixes. No too-weak finding; requirements faithful to gold behavior.

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
Partial patch fixing only row_join (horizontal) leaves col_join/vstack broken: vstack(0x0,1x0,2x0,3x0) yields shape (3,0) instead of (6,0). Rejected by probe_2 (Req 3.3).
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
# Req1.3 + positive control: hstack of zero-row matrices 0x0,0x1,0x2,0x3 -> (0,6)
import sys
from sympy import SparseMatrix
Ms = [SparseMatrix.zeros(0, c) for c in (0, 1, 2, 3)]
r = SparseMatrix.hstack(*Ms)
print("hstack shape:", r.shape)
ok = r.shape == (0, 6)
print("OK" if ok else "FAIL")
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

6 distinct probes cover Req1.3 (probe_1, positive control: hstack 0x0,0x1,0x2,0x3 -> (0,6)), Req3.3 (probe_2, vstack -> (6,0)), Req2.1 (probe_3, zero-col left operand w/ differing rows returns right operand), Req4.1 (probe_4, zero-row top operand w/ differing cols returns bottom operand), Req1.1/1.4/5.1/5.2 (probe_5: horizontal sum+entry placement+class+ShapeError), Req3.1/3.4/5.1/5.3 (probe_6: vertical sum+entry placement+class+ShapeError). All 6 HOLD on gold-patched tree. Positive controls probe_1 and probe_2 FAIL at base (base gives (0,3) and (3,0) respectively) — discriminating power confirmed. Candidate wrong patch (horizontal-only, weak.diff) applies at base_commit and is REJECTED by probe_2, demonstrating the suite discriminates partial fixes. No too-weak finding; requirements faithful to gold behavior.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Patch changes SparseMatrix.row_join/col_join in sparse.py: replaces the over-broad `if not self: return type(self)(other)` shortcut with a narrower guard that only short-circuits when the empty dimension is degenerate AND the other dimension mismatches (self.cols==0 & rows differ -> reshape and re-join; symmetric for col_join). This exactly matches the requirements' modeling boundary: the changed observable behavior is that a degenerate operand contributes its non-degenerate dimension (widths/heights sum) instead of being dropped, while shape-mismatch errors on non-degenerate operands and left/top class preservation are preserved. Requirements pin the full observable behavior (accumulated shape, entry placement Req1.4/3.4, class Req5.1, error Req5.2/5.3), not a narrow slice. No mandated-but-absent, forbidden-but-present, or invented behavior found.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The requirements name only public API surfaces (SparseMatrix.row_join/col_join, hstack/vstack, sympy/matrices/sparse.py) — legitimate localization. The horizontal enumeration `0x0,0x1,0x2,0x3` -> (0,6) is quoted verbatim from the PUBLIC problem_statement. The vertical `0,1,2,3` -> six rows case (Req 3.3, Req 4) is the obvious symmetric mirror of the public defect, described as behavior; it does not reproduce the hidden test (no `test_sparse_matrix` name, no `test_sparse.py` path, no `Matrix(6,0,[])` / `SparseMatrix.vstack(*...)` quoted code). No fix-invented identifiers leak: the gold's `self._new(...)` / `type(self)(other)` internals and the `#10770` comment are absent. Acceptance criteria are behavioral translations (shapes, class preservation, ShapeError) — the legitimate purpose of the spec, not test transmission.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
