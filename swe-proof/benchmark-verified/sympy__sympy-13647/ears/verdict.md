# P2 adversarial audit — sympy__sympy-13647

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

Counterexample / evidence:

```
Weak candidate (return self[i, j - pos] instead of self[i, j - other.cols]) is rejected by probes 1/2/3: for eye(6).col_insert(3, 2*ones(6,2)) it either scrambles/IndexErrors the right-hand original columns. Probe_1 on patched gives correct block placement; at base the original col_insert (self[i, j-pos-other.cols]) also violates.
```

**Attacks re-run (5):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
# PROBE 1 (positive control): Req1.4 right-hand columns shifted correctly
import sys
from sympy import Matrix, eye, ones

M = eye(6)
V = 2 * ones(6, 2)
R = M.col_insert(3, V)

expected = Matrix([
    [1, 0, 0, 2, 2, 0, 0, 0],
    [0, 1, 0, 2, 2, 0, 0, 0],
    [0, 0, 1, 2, 2, 0, 0, 0],
    [0, 0, 0, 2, 2, 1, 0, 0],
    [0, 0, 0, 2, 2, 0, 1, 0],
    [0, 0, 0, 2, 2, 0, 0, 1],
])
print("result=")
print(R)
print("expected=")
print(expected)
if R == expected:
    print("HOLDS")
    sys.exit(0)
print("VIOLATED")
sys.exit(1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
# PROBE 2: Req1.1/1.2/1.3/1.4 - full entrywise spec on a generic symbolic matrix
import sys
from sympy import Matrix, Symbol

# Build 4x5 host with distinct symbols, 4x3 other with distinct symbols
def sym(name, r, c):
    return Matrix(r, c, lambda i, j: Symbol("%s_%d_%d" % (name, i, j)))

self_ = sym("s", 4, 5)
other = sym("o", 4, 3)
n = self_.cols
k = other.cols
pos = 2
R = self_.col_insert(pos, other)

ok = True
# Req1.1 shape
if R.rows != self_.rows or R.cols != n + k:
    print("shape wrong", R.shape); ok = False
for i in range(R.rows):
    for j in range(R.cols):
        if j < pos:
            exp = self_[i, j]
        elif pos <= j < pos + k:
            exp = other[i, j - pos]
        else:
            exp = self_[i, j - k]
        if R[i, j] != exp:
            print("MISMATCH i=%d j=%d got=%s exp=%s" % (i, j, R[i, j], exp))
            ok = False
print("checked all entries, ok=", ok)
sys.exit(0 if ok else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
# PROBE 3: Req2 - position argument handling (negative, too-large, 0, n)
import sys
from sympy import Matrix

self_ = Matrix(2, 3, lambda i, j: 10*i + j)   # entries known
other = Matrix(2, 2, lambda i, j: 100 + 10*i + j)
n = self_.cols  # 3
k = other.cols

def expect(pos):
    # normalize pos per Req2
    p = pos
    if p < 0:
        p += n
        if p < 0:
            p = 0
    if p > n:
        p = n
    cols = []
    for j in range(n + k):
        if j < p:
            cols.append(("s", j))
        elif p <= j < p + k:
            cols.append(("o", j - p))
        else:
            cols.append(("s", j - k))
    E = Matrix(self_.rows, n + k, lambda i, j: (self_[i, cols[j][1]] if cols[j][0]=="s" else other[i, cols[j][1]]))
    return E

ok = True
for pos in [-100, -1, 0, 1, 3, 5]:
    R = self_.col_insert(pos, other)
    E = expect(pos)
    if R != E:
        print("pos=%d FAIL" % pos); print("got", R); print("exp", E); ok = False
    else:
        print("pos=%d ok" % pos)
sys.exit(0 if ok else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
# PROBE 4: Req3 - shape validation, empty host, type preservation
import sys
from sympy import Matrix, zeros
from sympy.matrices.common import ShapeError

ok = True

# Req3.1 mismatched rows -> ShapeError
self_ = Matrix(3, 2, lambda i, j: i + j)
other = Matrix(2, 2, lambda i, j: i + j)
try:
    self_.col_insert(0, other)
    print("no error raised for mismatched rows"); ok = False
except ShapeError:
    print("ShapeError raised as required")
except Exception as e:
    print("wrong exception type", type(e)); ok = False

# Req3.2 empty host -> returns other
empty = Matrix(0, 0, [])
o2 = Matrix(0, 0, [])
# Use a genuine null host: rows 0. col_insert on empty should return other
# sympy: an empty matrix (0 rows) with other having 0 rows
o3 = Matrix(2, 2, lambda i, j: i*2+j)
emptyhost = zeros(2, 0)  # 2 rows, 0 cols -> non-null in rows
R = emptyhost.col_insert(0, o3)
if R == o3:
    print("empty(cols=0) host returns other")
else:
    print("empty host mismatch", R); ok = False

# Req3.3 type preservation
from sympy import ImmutableMatrix
im = ImmutableMatrix(Matrix(2,2,lambda i,j:i+j))
Ri = im.col_insert(1, ImmutableMatrix(Matrix(2,1,lambda i,j:9)))
if type(Ri) is type(im):
    print("type preserved:", type(Ri).__name__)
else:
    print("type NOT preserved got", type(Ri), "exp", type(im)); ok = False

sys.exit(0 if ok else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
# PROBE 5: Req4 regression - row_insert, row_join/col_join unchanged; symbolic example
import sys
from sympy import Matrix, Symbol, eye

ok = True

# Req4.1 row_insert: insert rows shift lower rows down
A = Matrix(3, 2, lambda i, j: 10*i + j)
Ins = Matrix(2, 2, lambda i, j: 100 + 10*i + j)
R = A.row_insert(1, Ins)
expected_rows = [A.row(0), Ins.row(0), Ins.row(1), A.row(1), A.row(2)]
E = Matrix.vstack(*expected_rows)
if R == E:
    print("row_insert ok")
else:
    print("row_insert FAIL", R); ok = False

# Req4.2 row_join / col_join append without altering
X = Matrix(2, 2, lambda i, j: i + j)
Y = Matrix(2, 3, lambda i, j: 5 + i + j)
RJ = X.row_join(Y)
if RJ.cols == 5 and all(RJ[i, j] == X[i, j] for i in range(2) for j in range(2)) \
        and all(RJ[i, 2 + j] == Y[i, j] for i in range(2) for j in range(3)):
    print("row_join ok")
else:
    print("row_join FAIL", RJ); ok = False

Z = Matrix(3, 2, lambda i, j: 7 + i + j)
CJ = X.col_join(Z)
if CJ.rows == 5 and all(CJ[i, j] == X[i, j] for i in range(2) for j in range(2)) \
        and all(CJ[2 + i, j] == Z[i, j] for i in range(3) for j in range(2)):
    print("col_join ok")
else:
    print("col_join FAIL", CJ); ok = False

# Req4.4 symbolic col_insert matches spec (append at end pos=n)
a, b = Symbol('a'), Symbol('b')
S = Matrix([[a, b]])
O = Matrix([[a + b]])
R2 = S.col_insert(2, O)
if R2 == Matrix([[a, b, a + b]]):
    print("symbolic col_insert ok")
else:
    print("symbolic FAIL", R2); ok = False

sys.exit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
# PROBE 1 (positive control): Req1.4 right-hand columns shifted correctly
import sys
from sympy import Matrix, eye, ones

M = eye(6)
V = 2 * ones(6, 2)
R = M.col_insert(3, V)

expected = Matrix([
    [1, 0, 0, 2, 2, 0, 0, 0],
    [0, 1, 0, 2, 2, 0, 0, 0],
    [0, 0, 1, 2, 2, 0, 0, 0],
    [0, 0, 0, 2, 2, 1, 0, 0],
    [0, 0, 0, 2, 2, 0, 1, 0],
    [0, 0, 0, 2, 2, 0, 0, 1],
])
print("result=")
print(R)
print("expected=")
print(expected)
if R == expected:
    print("HOLDS")
    sys.exit(0)
print("VIOLATED")
sys.exit(1)
```

Prepatch bug re-encoded as an attack: `True`.

Requirements faithfully match the gold one-line fix (self[i,j-pos-other.cols] -> self[i,j-other.cols]).

Probes (all HOLD patched):
- probe_1 (Req1.4 positive control): eye(6).col_insert(3, 2*ones(6,2)) equals documented expected matrix. HOLDS patched, FAILS base. Discriminates.
- probe_2 (Req1.1-1.4): full entrywise spec on 4x5 symbolic host + 4x3 other at pos=2 (shape n+k, j<pos->self[i,j], middle->other[i,j-pos], right->self[i,j-k]). HOLDS patched, FAILS base.
- probe_3 (Req2 position handling): pos in {-100,-1,0,1,3,5} normalized (negative+n clamp0, >n clamp n) all match reconstructed expectation. HOLDS patched, FAILS base.
- probe_4 (Req3): mismatched rows -> ShapeError; empty(cols=0) host returns other; ImmutableMatrix type preserved. HOLDS patched.
- probe_5 (Req4 regression): row_insert shift, row_join/col_join append, symbolic col_insert. HOLDS patched.

Positive controls (probe_1,2,3) all VIOLATED at base -> prepatch reproduced.

Wrong-fix candidate weak.diff (self[i, j-pos]): REJECTED by probes 1/2/3 (scramble/IndexError on right-hand cols); probes 4/5 correctly agnostic (validation/regression untouched). Suite discriminates wrong implementations.

All runs completed in the official image.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 5 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 5 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 5 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

Counterexample / evidence:

```
Weak candidate (return self[i, j - pos] instead of self[i, j - other.cols]) is rejected by probes 1/2/3: for eye(6).col_insert(3, 2*ones(6,2)) it either scrambles/IndexErrors the right-hand original columns. Probe_1 on patched gives correct block placement; at base the original col_insert (self[i, j-pos-other.cols]) also violates.
```

**Attacks re-run (5):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

_The 5 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts, and on this backend both roles put it through the same derivation: every block below is a requirement probe run on the gold-patched tree, and the `machine verdict:` line each role publishes above reports BOTH that its probes hold there and how many candidate patches the probe suite rejected — so the two roles re-ran ONE probe suite and each recorded its own outcome for every probe in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `probe_1.py` → holds on the patched tree (good)

Attack 2 — `probe_2.py` → holds on the patched tree (good)

Attack 3 — `probe_3.py` → holds on the patched tree (good)

Attack 4 — `probe_4.py` → holds on the patched tree (good)

Attack 5 — `probe_5.py` → holds on the patched tree (good)

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
# PROBE 1 (positive control): Req1.4 right-hand columns shifted correctly
import sys
from sympy import Matrix, eye, ones

M = eye(6)
V = 2 * ones(6, 2)
R = M.col_insert(3, V)

expected = Matrix([
    [1, 0, 0, 2, 2, 0, 0, 0],
    [0, 1, 0, 2, 2, 0, 0, 0],
    [0, 0, 1, 2, 2, 0, 0, 0],
    [0, 0, 0, 2, 2, 1, 0, 0],
    [0, 0, 0, 2, 2, 0, 1, 0],
    [0, 0, 0, 2, 2, 0, 0, 1],
])
print("result=")
print(R)
print("expected=")
print(expected)
if R == expected:
    print("HOLDS")
    sys.exit(0)
print("VIOLATED")
sys.exit(1)
```

Prepatch bug re-encoded as an attack: `True`.

Requirements faithfully match the gold one-line fix (self[i,j-pos-other.cols] -> self[i,j-other.cols]).

Probes (all HOLD patched):
- probe_1 (Req1.4 positive control): eye(6).col_insert(3, 2*ones(6,2)) equals documented expected matrix. HOLDS patched, FAILS base. Discriminates.
- probe_2 (Req1.1-1.4): full entrywise spec on 4x5 symbolic host + 4x3 other at pos=2 (shape n+k, j<pos->self[i,j], middle->other[i,j-pos], right->self[i,j-k]). HOLDS patched, FAILS base.
- probe_3 (Req2 position handling): pos in {-100,-1,0,1,3,5} normalized (negative+n clamp0, >n clamp n) all match reconstructed expectation. HOLDS patched, FAILS base.
- probe_4 (Req3): mismatched rows -> ShapeError; empty(cols=0) host returns other; ImmutableMatrix type preserved. HOLDS patched.
- probe_5 (Req4 regression): row_insert shift, row_join/col_join append, symbolic col_insert. HOLDS patched.

Positive controls (probe_1,2,3) all VIOLATED at base -> prepatch reproduced.

Wrong-fix candidate weak.diff (self[i, j-pos]): REJECTED by probes 1/2/3 (scramble/IndexError on right-hand cols); probes 4/5 correctly agnostic (validation/regression untouched). Suite discriminates wrong implementations.

All runs completed in the official image.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Boundary is correctly modeled: Req1 pins the full biconditional over all three column regions (j<pos original, pos<=j<pos+k inserted, j>=pos+k shifted-by-k) rather than only the changed branch, and Req1.4 states the exact corrected index self[i, j-k]. Argument handling (Req2) and shape/degenerate cases (Req3) match the actual col_insert wrapper unchanged by the patch. Regression clauses (Req4) match observed row_insert/join behavior. No requirement mandates absent behavior, forbids present behavior, or invents behavior. Verified live in the instance image via nl_attack probe on the gold-patched tree; all assertions passed.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The requirements only reference legitimately-localizable public artifacts: the module sympy/matrices/common.py, the public API Matrix.col_insert, and its real helper _eval_col_insert (all pre-existing, not fix-invented). The core scenario (identity/structured matrix, interior column-block insertion, right-hand columns misplaced/scrambled) comes directly from the PUBLIC problem_statement, which already shows eye(6).col_insert(3, 2*ones(6,2)) and the buggy shifted output. The hidden test uses exactly that example (eye_Shaping(6).col_insert(3, Matrix of 2s)); the document restates it as a general behavioral requirement rather than quoting the test. Req 1.4 (original column j maps to self column j-k, shifted by number of inserted columns) is the correct behavioral spec that the gold one-liner (j-pos-other.cols -> j-other.cols) realizes, but it is expressed as behavior, not as the patched expression or an invented symbol. Reqs 2-4 describe pre-existing argument-handling (negative pos, pos>cols, empty host, shape error, type preservation) and regression behaviors (row_insert/row_join/col_join) that are part of the source contract, not the hidden test parametrization. No test names/paths/ids, no quoted test or gold code, no fix-invented identifiers, and no case enumeration mirroring the single-assert test beyond what the public statement already reveals.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
