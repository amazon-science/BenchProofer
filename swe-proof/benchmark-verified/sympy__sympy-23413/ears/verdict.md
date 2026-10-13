# P2 adversarial audit — sympy__sympy-23413

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 6 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 6 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 6 | `probe_1_issue.py`, `probe_2_req4.py`, `probe_3_width.py`, `probe_4_regression.py`, `probe_5_domain_D.py`, `probe_6_transpose.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_2_req4.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (6):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1_issue.py` → holds on the patched tree (good)

```python
# Req1.1/1.2/1.3 + positive control: tall matrix, upper row carries independent pivot.
# The issue's transposed example [[5,8,12],[0,0,1]].T -> 3x2; upper rows must keep pivots.
import sys
from sympy import Matrix
from sympy.matrices.normalforms import hermite_normal_form as hnf

M = Matrix([[5, 0], [8, 0], [12, 1]])  # 3x2 tall, rank 2
H = hnf(M)
print("input 3x2:", M.tolist())
print("HNF shape:", H.shape, "->", H.tolist())
# Must keep both pivot columns (width 2), not drop to width 1.
expected = [[5, 0], [8, 0], [0, 1]]
ok = (H.shape == (3, 2)) and (H.tolist() == expected)
print("expected:", expected, "ok:", ok)
sys.exit(0 if ok else 1)
```

Attack 2 — `probe_2_req4.py` → holds on the patched tree (good)

```python
# Req1.4: tall matrix, exactly one nonzero row above the bottom band, rest zero.
# Result SHALL be a single-column matrix reflecting that row's normalized pivot,
# NOT an empty-width matrix.
import sys
from sympy import Matrix
from sympy.matrices.normalforms import hermite_normal_form as hnf

cases = [
    (Matrix([[2, 7], [0, 0], [0, 0]]), (3, 1), [[1], [0], [0]]),   # gcd(2,7)=1 pivot in top row
    (Matrix([[3, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0]]), (4, 1), [[3], [0], [0], [0]]),
]
allok = True
for M, sh, exp in cases:
    H = hnf(M)
    ok = (H.shape == sh) and (H.tolist() == exp)
    print("in", M.tolist(), "-> shape", H.shape, H.tolist(), "exp", exp, "ok", ok)
    if H.shape[1] == 0:
        print("  VIOLATION: empty-width result")
    allok = allok and ok
sys.exit(0 if allok else 1)
```

Attack 3 — `probe_3_width.py` → holds on the patched tree (good)

```python
# Req2.3 + Req2.2 break guard: tall matrix with pivots in ALL columns.
# Result width SHALL equal the number of input columns exactly (not exceed / not drop).
import sys
from sympy import Matrix
from sympy.matrices.normalforms import hermite_normal_form as hnf

# 3x2 full column rank -> width exactly 2
M1 = Matrix([[1, 0], [0, 0], [0, 3]])
H1 = hnf(M1)
print("M1", M1.tolist(), "-> shape", H1.shape, H1.tolist())
ok1 = H1.shape[1] == 2

# 4x2, all columns get pivots -> width 2, and no out-of-range column
M2 = Matrix([[2, 0], [0, 5], [0, 0], [0, 0]])
H2 = hnf(M2)
print("M2", M2.tolist(), "-> shape", H2.shape, H2.tolist())
ok2 = H2.shape == (4, 2)

# rows==cols square already-correct: width 2
M3 = Matrix([[2, 3], [4, 5]])
H3 = hnf(M3)
ok3 = H3.shape[1] == 2
print("M3 square shape", H3.shape)

ok = ok1 and ok2 and ok3
print("ok:", ok)
sys.exit(0 if ok else 1)
```

Attack 4 — `probe_4_regression.py` → holds on the patched tree (good)

```python
# Req3.1/3.2/3.4: preserve existing behavior for cols>=rows (wide/square),
# full-row-rank lower-triangular form, non-negative normalized pivots.
import sys
from sympy import Matrix
from sympy.matrices.normalforms import hermite_normal_form as hnf

checks = []
# wide full row rank: known HNF
H = hnf(Matrix([[2, 3, 4], [5, 6, 7]]))
print("wide", H.shape, H.tolist())
checks.append(H.tolist() == [[3, 1], [0, 1]])

# square full-rank: HNF is lower-triangular-style with pivots in rightmost cols,
# non-negative diagonal, and off-diagonal reduced modulo the pivot. Verify structure.
M = Matrix([[8, 28, 68], [98, 618, 442], [448, 990, 1288]])
H = hnf(M)
print("square3", H.tolist())
sq_ok = H.shape == (3, 3)
# diagonal pivots strictly positive (non-negative normalization)
sq_ok = sq_ok and all(H[i, i] > 0 for i in range(3))
# determinant preserved (up to sign) = full rank / lattice preserved
sq_ok = sq_ok and abs(M.det()) == abs(H.det())
checks.append(sq_ok)

# negative pivot -> normalized to non-negative
H = hnf(Matrix([[-2, 3], [0, -4]]))
print("neg", H.tolist())
diag_nonneg = all(H[i, i] >= 0 for i in range(min(H.shape)))
checks.append(diag_nonneg and H.tolist() == [[2, 1], [0, 4]])

ok = all(checks)
print("checks", checks, "ok", ok)
sys.exit(0 if ok else 1)
```

Attack 5 — `probe_5_domain_D.py` → holds on the patched tree (good)

```python
# Req3.6 (non-ZZ raises) + Req3.5 (D arg for full-row-rank matches ordinary result).
import sys
from sympy import Matrix
from sympy.matrices.normalforms import hermite_normal_form as hnf

ok = True
# non-ZZ domain -> DMDomainError
try:
    hnf(Matrix([[0.5, 1], [2, 3]]))
    print("non-ZZ: NO EXCEPTION - VIOLATION")
    ok = False
except Exception as e:
    print("non-ZZ raised:", type(e).__name__)
    ok = ok and (type(e).__name__ == "DMDomainError")

# D argument on full-row-rank square: same as ordinary
M = Matrix([[2, 3], [4, 5]])
plain = hnf(M)
withD = hnf(M, D=2)
print("plain", plain.tolist(), "D=2", withD.tolist())
ok = ok and (plain.tolist() == withD.tolist())

# with rank-check enabled
withDcheck = hnf(M, D=2, check_rank=True)
print("D check", withDcheck.tolist())
ok = ok and (withDcheck.tolist() == plain.tolist())

print("ok", ok)
sys.exit(0 if ok else 1)
```

Attack 6 — `probe_6_transpose.py` → holds on the patched tree (good)

```python
# Req3.3 + Req1.2: a wide full-rank matrix's HNF is preserved, AND its transpose
# (taller-than-wide) retains all genuine pivots (no row/pivot dropping).
import sys
from sympy import Matrix
from sympy.matrices.normalforms import hermite_normal_form as hnf

# wide matrix and its tall transpose
W = Matrix([[2, 3, 4], [5, 6, 7]])   # 2x3 wide
Hw = hnf(W)
print("wide HNF", Hw.shape, Hw.tolist())
okw = Hw.tolist() == [[3, 1], [0, 1]]

T = W.T  # 3x2 tall, rank 2 -> must keep 2 pivot columns
Ht = hnf(T)
print("tall(transpose) HNF", Ht.shape, Ht.tolist())
# tall with full column rank 2 must NOT be dropped to width < 2
okt = Ht.shape[1] == 2

# Another tall case with rank 2 to be robust
T2 = Matrix([[5, 8], [0, 0], [0, 1]])
Ht2 = hnf(T2)
print("T2", Ht2.shape, Ht2.tolist())
okt2 = Ht2.shape[1] == 2

ok = okw and okt and okt2
print("ok", ok)
sys.exit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_2_req4.py`

```python
# Req1.4: tall matrix, exactly one nonzero row above the bottom band, rest zero.
# Result SHALL be a single-column matrix reflecting that row's normalized pivot,
# NOT an empty-width matrix.
import sys
from sympy import Matrix
from sympy.matrices.normalforms import hermite_normal_form as hnf

cases = [
    (Matrix([[2, 7], [0, 0], [0, 0]]), (3, 1), [[1], [0], [0]]),   # gcd(2,7)=1 pivot in top row
    (Matrix([[3, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0]]), (4, 1), [[3], [0], [0], [0]]),
]
allok = True
for M, sh, exp in cases:
    H = hnf(M)
    ok = (H.shape == sh) and (H.tolist() == exp)
    print("in", M.tolist(), "-> shape", H.shape, H.tolist(), "exp", exp, "ok", ok)
    if H.shape[1] == 0:
        print("  VIOLATION: empty-width result")
    allok = allok and ok
sys.exit(0 if allok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Bundle: sympy__sympy-23413, gold patch makes _hermite_normal_form iterate all rows (range(m-1,-1,-1)) instead of only the bottom min(m,n), plus a k==0 early-break guard.

### PROBES (all HOLD on gold-patched tree):
- probe_1_issue (Req1.1/1.2/1.3): 3x2 tall [[5,0],[8,0],[12,1]] (transpose of the issue's [[5,8,12],[0,0,1]]) -> HNF keeps both pivot columns [[5,0],[8,0],[0,1]] width 2. PATCHED HOLDS; BASE also HOLDS (this particular input already width 2 at base since bottom rows carry both pivots) — not discriminating but a faithful Req1 encoding.
- probe_2_req4 (Req1.4) = POSITIVE CONTROL: tall matrix with one nonzero row above the bottom band, rest zero ([[2,7],[0,0],[0,0]] and 4x3 [[3,0,0],...]) -> single-column normalized-pivot result, NOT empty-width. PATCHED HOLDS (shape (3,1)=[[1],[0],[0]]); BASE FAILS (shape (3,0) empty). Prepatch reproduced.
- probe_3_width (Req2.2/2.3): tall matrices with pivots in all columns -> width == input columns. PATCHED HOLDS; BASE FAILS (M1 3x2 -> width 1 at base).
- probe_4_regression (Req3.1/3.2/3.4): wide full-rank [[3,1],[0,1]] preserved; square full-rank HNF is lower-triangular-style with strictly-positive diagonal and |det| preserved; negative pivot normalized non-negative. Holds on BOTH trees (regression protection — correctly non-discriminating).
- probe_5_domain_D (Req3.5/3.6): non-ZZ raises DMDomainError; D arg (with and without check_rank) matches ordinary result. Holds both trees.
- probe_6_transpose (Req3.3/1.2): wide HNF preserved and its tall transpose retains all genuine pivots (width 2). PATCHED HOLDS; BASE FAILS (tall transpose dropped to width < 2).

DISCRIMINATION: probes 2, 3, 6 all fail at base, so the suite has real discriminating power; positive control (probe_2) HOLDS patched and FAILS base.

CANDIDATE PATCH (required): weak_nobreak.diff = the plausible partial fix that iterates all rows (range(m-1,-1,-1)) but OMITS the k==0 early-break guard. Applies cleanly at base_commit. Under this candidate: probes 1,2,3,4,5 HOLD but probe_6 is REJECTED (tall transpose of [[2,3,4],[5,6,7]] returns shape (3,1)=[[0],[0],[0]] because without the break k underflows and the pivot columns are clobbered/mis-sliced). This confirms the probe suite REJECTS a requirements-plausible wrong fix — the k==0 guard (Req2.2) is genuinely load-bearing and the suite catches its omission.

All 6 probes hold on the patched tree; positive control discriminates; >=1 candidate patch exercised and REJECTED. Verdict SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 6 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 6 | `probe_1_issue.py`, `probe_2_req4.py`, `probe_3_width.py`, `probe_4_regression.py`, `probe_5_domain_D.py`, `probe_6_transpose.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_2_req4.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (6):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

_The 6 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts, and on this backend both roles put it through the same derivation: every block below is a requirement probe run on the gold-patched tree, and the `machine verdict:` line each role publishes above reports BOTH that its probes hold there and how many candidate patches the probe suite rejected — so the two roles re-ran ONE probe suite and each recorded its own outcome for every probe in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `probe_1_issue.py` → holds on the patched tree (good)

Attack 2 — `probe_2_req4.py` → holds on the patched tree (good)

Attack 3 — `probe_3_width.py` → holds on the patched tree (good)

Attack 4 — `probe_4_regression.py` → holds on the patched tree (good)

Attack 5 — `probe_5_domain_D.py` → holds on the patched tree (good)

Attack 6 — `probe_6_transpose.py` → holds on the patched tree (good)

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_2_req4.py`

```python
# Req1.4: tall matrix, exactly one nonzero row above the bottom band, rest zero.
# Result SHALL be a single-column matrix reflecting that row's normalized pivot,
# NOT an empty-width matrix.
import sys
from sympy import Matrix
from sympy.matrices.normalforms import hermite_normal_form as hnf

cases = [
    (Matrix([[2, 7], [0, 0], [0, 0]]), (3, 1), [[1], [0], [0]]),   # gcd(2,7)=1 pivot in top row
    (Matrix([[3, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0]]), (4, 1), [[3], [0], [0], [0]]),
]
allok = True
for M, sh, exp in cases:
    H = hnf(M)
    ok = (H.shape == sh) and (H.tolist() == exp)
    print("in", M.tolist(), "-> shape", H.shape, H.tolist(), "exp", exp, "ok", ok)
    if H.shape[1] == 0:
        print("  VIOLATION: empty-width result")
    allok = allok and ok
sys.exit(0 if allok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Bundle: sympy__sympy-23413, gold patch makes _hermite_normal_form iterate all rows (range(m-1,-1,-1)) instead of only the bottom min(m,n), plus a k==0 early-break guard.

### PROBES (all HOLD on gold-patched tree):
- probe_1_issue (Req1.1/1.2/1.3): 3x2 tall [[5,0],[8,0],[12,1]] (transpose of the issue's [[5,8,12],[0,0,1]]) -> HNF keeps both pivot columns [[5,0],[8,0],[0,1]] width 2. PATCHED HOLDS; BASE also HOLDS (this particular input already width 2 at base since bottom rows carry both pivots) — not discriminating but a faithful Req1 encoding.
- probe_2_req4 (Req1.4) = POSITIVE CONTROL: tall matrix with one nonzero row above the bottom band, rest zero ([[2,7],[0,0],[0,0]] and 4x3 [[3,0,0],...]) -> single-column normalized-pivot result, NOT empty-width. PATCHED HOLDS (shape (3,1)=[[1],[0],[0]]); BASE FAILS (shape (3,0) empty). Prepatch reproduced.
- probe_3_width (Req2.2/2.3): tall matrices with pivots in all columns -> width == input columns. PATCHED HOLDS; BASE FAILS (M1 3x2 -> width 1 at base).
- probe_4_regression (Req3.1/3.2/3.4): wide full-rank [[3,1],[0,1]] preserved; square full-rank HNF is lower-triangular-style with strictly-positive diagonal and |det| preserved; negative pivot normalized non-negative. Holds on BOTH trees (regression protection — correctly non-discriminating).
- probe_5_domain_D (Req3.5/3.6): non-ZZ raises DMDomainError; D arg (with and without check_rank) matches ordinary result. Holds both trees.
- probe_6_transpose (Req3.3/1.2): wide HNF preserved and its tall transpose retains all genuine pivots (width 2). PATCHED HOLDS; BASE FAILS (tall transpose dropped to width < 2).

DISCRIMINATION: probes 2, 3, 6 all fail at base, so the suite has real discriminating power; positive control (probe_2) HOLDS patched and FAILS base.

CANDIDATE PATCH (required): weak_nobreak.diff = the plausible partial fix that iterates all rows (range(m-1,-1,-1)) but OMITS the k==0 early-break guard. Applies cleanly at base_commit. Under this candidate: probes 1,2,3,4,5 HOLD but probe_6 is REJECTED (tall transpose of [[2,3,4],[5,6,7]] returns shape (3,1)=[[0],[0],[0]] because without the break k underflows and the pivot columns are clobbered/mis-sliced). This confirms the probe suite REJECTS a requirements-plausible wrong fix — the k==0 guard (Req2.2) is genuinely load-bearing and the suite catches its omission.

All 6 probes hold on the patched tree; positive control discriminates; >=1 candidate patch exercised and REJECTED. Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Gold patch replaces `rows=min(m,n)` / `for i in range(m-1, m-1-rows, -1)` with `for i in range(m-1,-1,-1)` plus an `if k==0: break` guard. Requirements pin exactly this changed observable behavior: all rows eligible to contribute a pivot (R1.1-1.3), the tall single-nonzero-row -> single-column result (R1.4, matches test_patch), the [:, k:] result slice (R2.1), the k==0 early stop (R2.2), and regression preservation for cols>=rows (R3.1-3.3). Base-vs-patched probes confirm the divergence is only where the requirements claim. Modeling boundary is correct (the changed loop + width), not a narrow helper slice, and no behavior beyond the fix is mandated. Domain error (R3.6) and negative-pivot normalization/reduction (R3.4) are unchanged by the patch and correctly described.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The requirements localize the change to the correct modules/functions (sympy/polys/matrices/normalforms.py, hermite_normal_form/_hermite_normal_form) and describe corrected behavior, which is legitimate. The public problem_statement already supplies the [[5,8,12],[0,0,1]] example and the dropped-row/false-rank-deficiency symptom, both reused fairly. No hidden-only content is transmitted: no test file paths, no test function names (test_issue_23410 never appears), no parametrization ids, no verbatim gold-patch lines (the loop-bound / k==0 break edit is described only as behavior — 'process rows from the bottom upward such that any row may contribute a pivot' and 'stop when every column already holds a pivot'), and no fix-invented identifiers (k/m/n are pre-existing algorithm variables used to localize). The closest call is Req 1.4 ('single nonzero row above the bottom band, remaining rows zero -> single-column matrix ... rather than an empty-width matrix'), which parallels the gold test case [[2,7],[0,0],[0,0]] -> [[1],[0],[0]] (was empty-width Matrix(3,0,[])). But it abstracts the behavioral class — it does not quote the matrix, the expected value, or enumerate the parametrized cases — and the empty-width/dropped-row contrast is a direct consequence of the symptom already public in the problem statement. This is behavioral translation, not test reconstruction.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
