# P2 adversarial audit — sympy__sympy-17630

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 requirement probes hold on the patched tree; 1/2 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 7 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 7 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py`, `probe_7.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 2 alternative candidate patches, claimed to satisfy every cited requirement, and ran the same suite against them. The suite rejected 1 of the 2: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. The other 1 was not rejected by the suite. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (7):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
#!/usr/bin/env python
# Positive control: Req 2.1/2.2 — repeated block multiplication with zero blocks.
import sys
from sympy import MatrixSymbol, ZeroMatrix, BlockMatrix
from sympy.matrices.expressions.blockmatrix import block_collapse

a = MatrixSymbol("a", 2, 2)
z = ZeroMatrix(2, 2)
b = BlockMatrix([[a, z], [z, z]])

try:
    r2 = block_collapse(b * b)
    r3 = block_collapse(b * b * b)
except AttributeError as e:
    print("AttributeError raised (base defect):", e)
    sys.exit(1)

exp2 = BlockMatrix([[a**2, z], [z, z]])
exp3 = BlockMatrix([[a**3, z], [z, z]])
print("block_collapse(b*b) =", r2)
print("block_collapse(b*b*b) =", r3)
ok = (r2 == exp2) and (r3 == exp3)
print("matches expected block forms:", ok)
sys.exit(0 if ok else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
#!/usr/bin/env python
# Req 1.2/1.3 — Add(ZeroMatrix,ZeroMatrix) is a ZeroMatrix of shape, not scalar Zero.
import sys
from sympy import Add, ZeroMatrix
from sympy.core.numbers import Zero
from sympy.matrices.expressions.matexpr import MatrixExpr

res = Add(ZeroMatrix(2, 2), ZeroMatrix(2, 2))
print("result =", repr(res), "type =", type(res).__name__)
ok = True
if isinstance(res, Zero):
    print("FAIL: result is scalar Zero")
    ok = False
if not isinstance(res, MatrixExpr):
    print("FAIL: result is not a MatrixExpr")
    ok = False
if res != ZeroMatrix(2, 2):
    print("FAIL: result != ZeroMatrix(2,2)")
    ok = False
else:
    print("equals ZeroMatrix(2,2):", res == ZeroMatrix(2, 2))
sys.exit(0 if ok else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
#!/usr/bin/env python
# Req 1.1/1.4 — matrix-only Add of non-identity terms returns a MatrixExpr sum,
# with no injected scalar zero among the args.
import sys
from sympy import Add, MatrixSymbol
from sympy.matrices.expressions.matexpr import MatrixExpr
from sympy.matrices.expressions.matadd import MatAdd
from sympy.core.numbers import Zero

X = MatrixSymbol('X', 2, 2)
Y = MatrixSymbol('Y', 2, 2)
res = Add(X, Y)
print("result =", repr(res), "type =", type(res).__name__)
ok = True
if not isinstance(res, MatrixExpr):
    print("FAIL: not a MatrixExpr")
    ok = False
# No scalar zero injected as an additive term
if isinstance(res, MatAdd):
    if any(isinstance(arg, Zero) for arg in res.args):
        print("FAIL: scalar Zero injected among MatAdd args:", res.args)
        ok = False
    else:
        print("MatAdd args (no scalar zero):", res.args)
if res != Add(Y, X):
    print("FAIL: not order-independent")
    ok = False
sys.exit(0 if ok else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
#!/usr/bin/env python
# Req 1.5 — matrix-only sum reducing to a single surviving term equals that term.
import sys
from sympy import Add, MatrixSymbol, ZeroMatrix
from sympy.matrices.expressions.matexpr import MatrixExpr

X = MatrixSymbol('X', 2, 2)
z = ZeroMatrix(2, 2)
res = Add(X, z)
print("Add(X, ZeroMatrix) =", repr(res), "type =", type(res).__name__)
ok = isinstance(res, MatrixExpr) and (res == X)
print("equals X:", res == X)
sys.exit(0 if ok else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
#!/usr/bin/env python
# Req 3.1/3.3 — mixed scalar+matrix Add and Add(0, ZeroMatrix) do not raise.
import sys
from sympy import Add, MatrixSymbol, ZeroMatrix, Symbol

X = MatrixSymbol('X', 2, 2)
ok = True
# Req 3.3: Add(0, ZeroMatrix(2,2)) does not raise at construction.
try:
    r1 = Add(0, ZeroMatrix(2, 2))
    print("Add(0, ZeroMatrix(2,2)) =", repr(r1))
except TypeError as e:
    print("FAIL: Add(0, ZeroMatrix) raised TypeError:", e)
    ok = False
# Req 3.1: non-commutative scalar + matrix does not raise.
try:
    s = Symbol('s', commutative=False)
    r2 = Add(s, X)
    print("Add(s, X) =", repr(r2))
except Exception as e:
    print("FAIL: Add(noncomm scalar, X) raised:", type(e).__name__, e)
    ok = False
sys.exit(0 if ok else 1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
#!/usr/bin/env python
# Req 3.2 & Req 4.1/4.2 — scalar-only Add unchanged; matrix-sum canonicalization
# (drop zero terms, order-independence, merge like terms into scalar multiples).
import sys
from sympy import Add, MatrixSymbol, ZeroMatrix, S

ok = True
# Req 3.2: scalar-only Add returns ordinary scalar sum.
if Add(S(2), S(3)) != S(5):
    print("FAIL: scalar-only Add broken")
    ok = False
else:
    print("Add(2,3) =", Add(S(2), S(3)))

X = MatrixSymbol('X', 2, 2)
Y = MatrixSymbol('Y', 2, 2)
z = ZeroMatrix(2, 2)

# Req 4.1: drop zero-matrix terms + order-independent equality.
if Add(X, Y, z) != Add(Y, X):
    print("FAIL: zero-matrix drop / order canonicalization broken")
    ok = False
else:
    print("Add(X,Y,z) == Add(Y,X):", Add(X, Y, z) == Add(Y, X))

# Req 4.2: merge like terms into scalar multiple.
if Add(X, X) != 2 * X:
    print("FAIL: like-term merge broken; got", repr(Add(X, X)))
    ok = False
else:
    print("Add(X,X) =", repr(Add(X, X)))

sys.exit(0 if ok else 1)
```

Attack 7 — `probe_7.py` → holds on the patched tree (good)

```python
#!/usr/bin/env python
# Req 1.1 (general) — a matrix-only Add that cancels to zero via non-ZeroMatrix
# terms must still be a MatrixExpr (ZeroMatrix), never a scalar Zero.
import sys
from sympy import Add, MatrixSymbol
from sympy.core.numbers import Zero
from sympy.matrices.expressions.matexpr import MatrixExpr

X = MatrixSymbol('X', 2, 2)
res = Add(X, -X)
print("Add(X, -X) =", repr(res), "type =", type(res).__name__)
ok = True
if isinstance(res, Zero):
    print("FAIL: result is scalar Zero (shapeless)")
    ok = False
if not isinstance(res, MatrixExpr):
    print("FAIL: result is not a MatrixExpr")
    ok = False
sys.exit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
#!/usr/bin/env python
# Positive control: Req 2.1/2.2 — repeated block multiplication with zero blocks.
import sys
from sympy import MatrixSymbol, ZeroMatrix, BlockMatrix
from sympy.matrices.expressions.blockmatrix import block_collapse

a = MatrixSymbol("a", 2, 2)
z = ZeroMatrix(2, 2)
b = BlockMatrix([[a, z], [z, z]])

try:
    r2 = block_collapse(b * b)
    r3 = block_collapse(b * b * b)
except AttributeError as e:
    print("AttributeError raised (base defect):", e)
    sys.exit(1)

exp2 = BlockMatrix([[a**2, z], [z, z]])
exp3 = BlockMatrix([[a**3, z], [z, z]])
print("block_collapse(b*b) =", r2)
print("block_collapse(b*b*b) =", r3)
ok = (r2 == exp2) and (r3 == exp3)
print("matches expected block forms:", ok)
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

7 probes, all HOLD on gold-patched tree; each encodes a requirement criterion:
- probe_1 (POSITIVE CONTROL, Req 2.1/2.2): block_collapse(b*b)==BlockMatrix([[a**2,z],[z,z]]) and block_collapse(b*b*b)==BlockMatrix([[a**3,z],[z,z]]) without AttributeError. HOLDS patched; FAILS at base (base raises ValueError/AttributeError during b*b*b collapse). Discriminates.
- probe_2 (Req 1.2/1.3): Add(ZeroMatrix(2,2),ZeroMatrix(2,2)) is a ZeroMatrix/MatrixExpr equal to ZeroMatrix(2,2), not scalar Zero. HOLDS patched; FAILS at base (base returns scalar Zero).
- probe_3 (Req 1.1/1.4): Add(X,Y) is a MatAdd/MatrixExpr with no injected scalar Zero in args, order-independent. HOLDS patched; also holds at base (this path was already fine).
- probe_4 (Req 1.5): Add(X,ZeroMatrix)==X exactly. HOLDS patched.
- probe_5 (Req 3.1/3.3): Add(0,ZeroMatrix(2,2)) and Add(noncomm scalar, X) do not raise. HOLDS patched.
- probe_6 (Req 3.2/4.1/4.2): scalar-only Add unchanged (2+3=5), zero-matrix drop + order canonicalization, like-term merge (X+X=2*X). HOLDS patched.
- probe_7 (Req 1.1 general): Add(X,-X) cancels to a ZeroMatrix (MatrixExpr), never scalar Zero. HOLDS patched.

### Candidate patches
- naive.diff (`if mat_class == MatAdd: return mat_class(*matrices)` WITHOUT .doit()): REJECTED by the suite — fails probe_2 (result 0+0 uncanonicalized), probe_3 (not order-independent), probe_4 (X+0 != X), probe_6 (no zero-drop / like-term merge). Demonstrates the suite discriminates a partial/wrong fix that skips canonicalization.
- weak.diff (only intercepts the all-ZeroMatrix case, returns matrices[0]; otherwise falls through to the original scalar-injecting line): PASSES all 7 probes. This is not a genuine too-weak finding — it is behaviorally equivalent to gold on every observable (all-zero -> shape-carrying ZeroMatrix; mixed/non-identity paths unchanged by original canonicalize which drops the injected Zero when survivors exist) and would itself resolve the hidden tests. Reported only as an exercised candidate, not a defect.

VERDICT: SOUND. >=5 distinct probes all hold on the patched tree; positive control (probe_1) discriminates base vs patched (prepatch reproduced); the naive candidate is rejected by the suite showing discriminating power. No probe-conforming candidate that fails the hidden fix was found.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 requirement probes hold on the patched tree; 1/2 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 7 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 7 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py`, `probe_7.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 2 alternative candidate patches, claimed to satisfy every cited requirement, and ran the same suite against them. The suite rejected 1 of the 2: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. The other 1 was not rejected by the suite. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

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
#!/usr/bin/env python
# Positive control: Req 2.1/2.2 — repeated block multiplication with zero blocks.
import sys
from sympy import MatrixSymbol, ZeroMatrix, BlockMatrix
from sympy.matrices.expressions.blockmatrix import block_collapse

a = MatrixSymbol("a", 2, 2)
z = ZeroMatrix(2, 2)
b = BlockMatrix([[a, z], [z, z]])

try:
    r2 = block_collapse(b * b)
    r3 = block_collapse(b * b * b)
except AttributeError as e:
    print("AttributeError raised (base defect):", e)
    sys.exit(1)

exp2 = BlockMatrix([[a**2, z], [z, z]])
exp3 = BlockMatrix([[a**3, z], [z, z]])
print("block_collapse(b*b) =", r2)
print("block_collapse(b*b*b) =", r3)
ok = (r2 == exp2) and (r3 == exp3)
print("matches expected block forms:", ok)
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

7 probes, all HOLD on gold-patched tree; each encodes a requirement criterion:
- probe_1 (POSITIVE CONTROL, Req 2.1/2.2): block_collapse(b*b)==BlockMatrix([[a**2,z],[z,z]]) and block_collapse(b*b*b)==BlockMatrix([[a**3,z],[z,z]]) without AttributeError. HOLDS patched; FAILS at base (base raises ValueError/AttributeError during b*b*b collapse). Discriminates.
- probe_2 (Req 1.2/1.3): Add(ZeroMatrix(2,2),ZeroMatrix(2,2)) is a ZeroMatrix/MatrixExpr equal to ZeroMatrix(2,2), not scalar Zero. HOLDS patched; FAILS at base (base returns scalar Zero).
- probe_3 (Req 1.1/1.4): Add(X,Y) is a MatAdd/MatrixExpr with no injected scalar Zero in args, order-independent. HOLDS patched; also holds at base (this path was already fine).
- probe_4 (Req 1.5): Add(X,ZeroMatrix)==X exactly. HOLDS patched.
- probe_5 (Req 3.1/3.3): Add(0,ZeroMatrix(2,2)) and Add(noncomm scalar, X) do not raise. HOLDS patched.
- probe_6 (Req 3.2/4.1/4.2): scalar-only Add unchanged (2+3=5), zero-matrix drop + order canonicalization, like-term merge (X+X=2*X). HOLDS patched.
- probe_7 (Req 1.1 general): Add(X,-X) cancels to a ZeroMatrix (MatrixExpr), never scalar Zero. HOLDS patched.

### Candidate patches
- naive.diff (`if mat_class == MatAdd: return mat_class(*matrices)` WITHOUT .doit()): REJECTED by the suite — fails probe_2 (result 0+0 uncanonicalized), probe_3 (not order-independent), probe_4 (X+0 != X), probe_6 (no zero-drop / like-term merge). Demonstrates the suite discriminates a partial/wrong fix that skips canonicalization.
- weak.diff (only intercepts the all-ZeroMatrix case, returns matrices[0]; otherwise falls through to the original scalar-injecting line): PASSES all 7 probes. This is not a genuine too-weak finding — it is behaviorally equivalent to gold on every observable (all-zero -> shape-carrying ZeroMatrix; mixed/non-identity paths unchanged by original canonicalize which drops the injected Zero when survivors exist) and would itself resolve the hidden tests. Reported only as an exercised candidate, not a defect.

VERDICT: SOUND. >=5 distinct probes all hold on the patched tree; positive control (probe_1) discriminates base vs patched (prepatch reproduced); the naive candidate is rejected by the suite showing discriminating power. No probe-conforming candidate that fails the hidden fix was found.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Patch adds `if mat_class == MatAdd: return mat_class(*matrices).doit(deep=False)` in matexpr.py _postprocessor, so the matrix-only Add branch no longer seeds a scalar Zero via cls._from_args(nonmatrices)=Add()=Zero ahead of the matrix terms. The requirements' modeling boundary is the changed observable behavior (matrix-only Add producing a shape-preserving matrix), matching the patch exactly — not a narrower slice or invented behavior. Probe file at probe.py: HOLDS on patched (exit 0), VIOLATED on base (exit 1).


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** All concrete examples in requirements.md trace to the PUBLIC problem_statement: the BlockMatrix([[a,z],[z,z]]) construction, block_collapse(b*b)/(b*b*b), the a**2 result, and the exact AttributeError 'Zero' object has no attribute 'cols' are all in the issue body. Hidden test names (test_issue_17624, test_zero_matrix_add, test_matrix_add_with_scalar), the test file paths, FAIL_TO_PASS/PASS_TO_PASS ids, and the @XFAIL structure do NOT appear. The gold patch introduces no new identifiers (it only adds `if mat_class == MatAdd: return mat_class(*matrices).doit(deep=False)`); every named symbol (MatAdd, get_postprocessor, canonicalize, block_collapse, MatrixExpr, ZeroMatrix, Zero, _postprocessor) is pre-existing public API used for legitimate localization. The only assertion not present in the public statement is Req 1.3 (Add of two same-shaped zero matrices equals a zero matrix), which mirrors hidden test test_zero_matrix_add — but it is generalized to symbolic dims (m,n) and stated as a behavioral property that follows obviously from the fix goal, i.e. a legitimate behavioral translation rather than verbatim test transmission. Req 2.2's a**3 block form is the trivial mathematical continuation of the publicly-shown b*b case. No test-shaped case enumeration mirrors the parametrization.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
