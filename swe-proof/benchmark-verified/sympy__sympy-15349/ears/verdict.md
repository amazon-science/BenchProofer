# P2 adversarial audit — sympy__sympy-15349

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 7 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 7 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py`, `probe_7.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_4.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (7):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
import sys
from sympy import symbols, simplify
from sympy.algebras.quaternion import Quaternion

a, b, c, d = symbols('a b c d', real=True)
q = Quaternion(a, b, c, d)
s = q.norm()**-2
M = q.to_rotation_matrix()
m12 = M[1, 2]
expected = 2*s*(c*d - b*a)
diff = simplify(m12 - expected)
print("m12 =", m12)
print("expected 2*s*(c*d - b*a) =", expected)
print("simplified diff =", diff)
sys.exit(0 if diff == 0 else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
import sys
from sympy import symbols, simplify
from sympy.algebras.quaternion import Quaternion

a, b, c, d = symbols('a b c d', real=True)
q = Quaternion(a, b, c, d)
s = q.norm()**-2
M = q.to_rotation_matrix()
m21 = M[2, 1]
expected = 2*s*(c*d + b*a)
diff = simplify(m21 - expected)
print("m21 =", m21)
print("expected 2*s*(c*d + b*a) =", expected)
print("simplified diff =", diff)
sys.exit(0 if diff == 0 else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
import sys
from sympy import symbols, simplify
from sympy.algebras.quaternion import Quaternion

# Req 1.3: m12 and m21 carry OPPOSITE signs on the b*a cross term.
# Then m12 + m21 has no b*a term (== 4*s*c*d), and m12 - m21 == -4*s*b*a (nonzero).
a, b, c, d = symbols('a b c d', real=True)
q = Quaternion(a, b, c, d)
s = q.norm()**-2
M = q.to_rotation_matrix()
m12, m21 = M[1, 2], M[2, 1]
sum_ = simplify(m12 + m21 - 4*s*c*d)
dif_ = simplify(m12 - m21 - (-4*s*b*a))
print("m12 =", m12)
print("m21 =", m21)
print("(m12+m21) - 4*s*c*d simplified =", sum_)
print("(m12-m21) - (-4*s*b*a) simplified =", dif_)
ok = (sum_ == 0) and (dif_ == 0)
sys.exit(0 if ok else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
import sys
from sympy import symbols, cos, sin, sqrt, trigsimp, Matrix, Rational
from sympy.algebras.quaternion import Quaternion

# Req 2: rotation about first axis. This is the positive control.
x = symbols('x', real=True)
q = Quaternion(cos(x/2), sin(x/2), 0, 0)
M = trigsimp(q.to_rotation_matrix())
print("M =", M)
expected = Matrix([
    [1, 0, 0],
    [0, cos(x), -sin(x)],
    [0, sin(x), cos(x)],
])
diff = trigsimp(M - expected)
print("diff =", diff)
ok = diff == Matrix.zeros(3, 3)
sys.exit(0 if ok else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
import sys
from sympy import symbols, simplify
from sympy.algebras.quaternion import Quaternion

# Req 3: 4x4 affine form. Upper-left 3x3 == 3x3 form (incl m12);
# fourth column rows 0-2 == p_i - (x*m_i0 + y*m_i1 + z*m_i2); fourth row (0,0,0,1).
a, b, c, d = symbols('a b c d', real=True)
x, y, z = symbols('x y z', real=True)
q = Quaternion(a, b, c, d)
M3 = q.to_rotation_matrix()
M4 = q.to_rotation_matrix((x, y, z))
print("M4 shape:", M4.shape)
ok = M4.shape == (4, 4)

# upper-left block equal
for i in range(3):
    for j in range(3):
        if simplify(M4[i, j] - M3[i, j]) != 0:
            print("block mismatch at", i, j)
            ok = False

# translation column
p = (x, y, z)
for i in range(3):
    exp = p[i] - (x*M3[i, 0] + y*M3[i, 1] + z*M3[i, 2])
    if simplify(M4[i, 3] - exp) != 0:
        print("trans mismatch at row", i, "got", M4[i, 3], "exp", exp)
        ok = False

# fourth row
if list(M4[3, :]) != [0, 0, 0, 1]:
    print("fourth row wrong:", list(M4[3, :]))
    ok = False

# specifically m12 corrected
if simplify(M4[1, 2] - 2*(q.norm()**-2)*(c*d - b*a)) != 0:
    print("M4[1,2] wrong:", M4[1, 2])
    ok = False

print("ok =", ok)
sys.exit(0 if ok else 1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
import sys
from sympy import symbols, simplify, Matrix
from sympy.algebras.quaternion import Quaternion

# Req 4: preserve all other entries (diagonals + other off-diagonals) and 3x3 shape.
a, b, c, d = symbols('a b c d', real=True)
q = Quaternion(a, b, c, d)
s = q.norm()**-2
M = q.to_rotation_matrix()
ok = M.shape == (3, 3)
exp = {
    (0, 0): 1 - 2*s*(c**2 + d**2),
    (1, 1): 1 - 2*s*(b**2 + d**2),
    (2, 2): 1 - 2*s*(b**2 + c**2),
    (0, 1): 2*s*(b*c - d*a),
    (0, 2): 2*s*(b*d + c*a),
    (1, 0): 2*s*(b*c + d*a),
    (2, 0): 2*s*(b*d - c*a),
}
for (i, j), e in exp.items():
    diff = simplify(M[i, j] - e)
    if diff != 0:
        print("entry", i, j, "wrong: got", M[i, j], "exp", e, "diff", diff)
        ok = False
    else:
        print("entry", i, j, "ok")
print("shape", M.shape, "ok =", ok)
sys.exit(0 if ok else 1)
```

Attack 7 — `probe_7.py` → holds on the patched tree (good)

```python
import sys
from sympy import Rational, sqrt, simplify, nsimplify, Matrix
from sympy.algebras.quaternion import Quaternion

# Req 4.4: to_axis_angle unchanged by the fix. The fix touches only m12 in
# to_rotation_matrix, never to_axis_angle. Verify to_axis_angle still yields the
# canonical result for a concrete quaternion (documented example: (1,1,1,1)).
q = Quaternion(1, 1, 1, 1)
axis, angle = q.to_axis_angle()
print("axis =", axis, "angle =", angle)
# Known: axis = (1/sqrt3, 1/sqrt3, 1/sqrt3), angle = 2*pi/3
from sympy import pi
exp_axis = (1/sqrt(3), 1/sqrt(3), 1/sqrt(3))
ok = all(simplify(axis[i] - exp_axis[i]) == 0 for i in range(3))
ok = ok and simplify(angle - 2*pi/3) == 0
print("ok =", ok)
sys.exit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_4.py`

```python
import sys
from sympy import symbols, cos, sin, sqrt, trigsimp, Matrix, Rational
from sympy.algebras.quaternion import Quaternion

# Req 2: rotation about first axis. This is the positive control.
x = symbols('x', real=True)
q = Quaternion(cos(x/2), sin(x/2), 0, 0)
M = trigsimp(q.to_rotation_matrix())
print("M =", M)
expected = Matrix([
    [1, 0, 0],
    [0, cos(x), -sin(x)],
    [0, sin(x), cos(x)],
])
diff = trigsimp(M - expected)
print("diff =", diff)
ok = diff == Matrix.zeros(3, 3)
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Requirements: correct sign of m12 (2nd row/3rd col) in Quaternion.to_rotation_matrix from 2*s*(c*d + b*a) to 2*s*(c*d - b*a). Gold patch flips m12 only.

Probes (all HOLD on gold-patched tree):
- probe_1 (Req1.1): symbolic M[1,2] == 2*s*(c*d - b*a). Patched HOLDS; base VIOLATED (diff 4*a*b/norm^2).
- probe_2 (Req1.2): symbolic M[2,1] == 2*s*(c*d + b*a). Patched HOLDS; base HOLDS (m21 unchanged by fix — correct).
- probe_3 (Req1.3): m12 and m21 carry OPPOSITE signs on b*a (m12+m21==4*s*c*d and m12-m21==-4*s*b*a). Patched HOLDS; base VIOLATED.
- probe_4 (Req2, POSITIVE CONTROL): Quaternion(cos(x/2),sin(x/2),0,0) -> trigsimp == [[1,0,0],[0,cos,-sin],[0,sin,cos]]. Patched HOLDS; base VIOLATED (base gives +sin above diagonal, matrix not a proper rotation). Discriminates.
- probe_5 (Req3): 4x4 affine — upper-left 3x3 equals 3x3 form incl corrected M4[1,2], translation column == p_i-(x*mi0+y*mi1+z*mi2), fourth row (0,0,0,1). Patched HOLDS.
- probe_6 (Req4.1/4.2/4.3): three diagonals and the four other off-diagonals unchanged; 3x3 shape. Patched HOLDS.
- probe_7 (Req4.4): to_axis_angle unchanged — Quaternion(1,1,1,1) -> axis (1/sqrt3,...), angle 2*pi/3. Patched HOLDS.

Candidate wrong-fix (weak.diff): the lazy misreading that flips m21 (3rd row/2nd col) instead of m12. Applies cleanly at base. Under it probes 1,2,3,4,5 all VIOLATED (probe_2 now fails because m21 is wrongly negated; probes 1/3/4/5 fail because m12 still wrong). Probes 6,7 HOLD (unrelated). Suite REJECTS the wrong fix -> discriminating power confirmed; no requirements-conforming wrong patch found.

All 7 probes hold on gold-patched tree; positive control fails at base. Verdict SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 7 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 7 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py`, `probe_7.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_4.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (7):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts, and on this backend both roles put it through the same derivation: every block below is a requirement probe run on the gold-patched tree, and the `machine verdict:` line each role publishes above reports BOTH that its probes hold there and how many candidate patches the probe suite rejected — so the two roles re-ran ONE probe suite and each recorded its own outcome for every probe in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `probe_1.py` → holds on the patched tree (good)

Attack 2 — `probe_2.py` → holds on the patched tree (good)

Attack 3 — `probe_3.py` → holds on the patched tree (good)

Attack 4 — `probe_4.py` → holds on the patched tree (good)

Attack 5 — `probe_5.py` → holds on the patched tree (good)

Attack 6 — `probe_6.py` → holds on the patched tree (good)

Attack 7 — `probe_7.py` → holds on the patched tree (good)

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_4.py`

```python
import sys
from sympy import symbols, cos, sin, sqrt, trigsimp, Matrix, Rational
from sympy.algebras.quaternion import Quaternion

# Req 2: rotation about first axis. This is the positive control.
x = symbols('x', real=True)
q = Quaternion(cos(x/2), sin(x/2), 0, 0)
M = trigsimp(q.to_rotation_matrix())
print("M =", M)
expected = Matrix([
    [1, 0, 0],
    [0, cos(x), -sin(x)],
    [0, sin(x), cos(x)],
])
diff = trigsimp(M - expected)
print("diff =", diff)
ok = diff == Matrix.zeros(3, 3)
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Requirements: correct sign of m12 (2nd row/3rd col) in Quaternion.to_rotation_matrix from 2*s*(c*d + b*a) to 2*s*(c*d - b*a). Gold patch flips m12 only.

Probes (all HOLD on gold-patched tree):
- probe_1 (Req1.1): symbolic M[1,2] == 2*s*(c*d - b*a). Patched HOLDS; base VIOLATED (diff 4*a*b/norm^2).
- probe_2 (Req1.2): symbolic M[2,1] == 2*s*(c*d + b*a). Patched HOLDS; base HOLDS (m21 unchanged by fix — correct).
- probe_3 (Req1.3): m12 and m21 carry OPPOSITE signs on b*a (m12+m21==4*s*c*d and m12-m21==-4*s*b*a). Patched HOLDS; base VIOLATED.
- probe_4 (Req2, POSITIVE CONTROL): Quaternion(cos(x/2),sin(x/2),0,0) -> trigsimp == [[1,0,0],[0,cos,-sin],[0,sin,cos]]. Patched HOLDS; base VIOLATED (base gives +sin above diagonal, matrix not a proper rotation). Discriminates.
- probe_5 (Req3): 4x4 affine — upper-left 3x3 equals 3x3 form incl corrected M4[1,2], translation column == p_i-(x*mi0+y*mi1+z*mi2), fourth row (0,0,0,1). Patched HOLDS.
- probe_6 (Req4.1/4.2/4.3): three diagonals and the four other off-diagonals unchanged; 3x3 shape. Patched HOLDS.
- probe_7 (Req4.4): to_axis_angle unchanged — Quaternion(1,1,1,1) -> axis (1/sqrt3,...), angle 2*pi/3. Patched HOLDS.

Candidate wrong-fix (weak.diff): the lazy misreading that flips m21 (3rd row/2nd col) instead of m12. Applies cleanly at base. Under it probes 1,2,3,4,5 all VIOLATED (probe_2 now fails because m21 is wrongly negated; probes 1/3/4/5 fail because m12 still wrong). Probes 6,7 HOLD (unrelated). Suite REJECTS the wrong fix -> discriminating power confirmed; no requirements-conforming wrong patch found.

All 7 probes hold on gold-patched tree; positive control fails at base. Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Probed gold-patched code: Req1.1 M[1,2]==2*s*(c*d-b*a) (diff simplifies to 0); Req1.2 M[2,1]==2*s*(c*d+b*a) (0); Req1.3 opposite signs confirmed. Req2: trigsimp of Quaternion(cos(x/2),sin(x/2),0,0).to_rotation_matrix() gives R00=1, R11=R22=cos(x), R12=-sin(x), R21=sin(x) — exactly as required. Req3.1 3x3 block matches; Req3.2 col-3 translation entries equal p_i-(x*m_i0+y*m_i1+z*m_i2) (diffs 0); Req3.3 last row (0,0,0,1). Req4: all diagonals and remaining off-diagonals (m00,m11,m22,m01,m02,m10,m20) match stated formulas (diffs 0); shapes 3x3/4x4 confirmed. The requirements do not overreach (Req4.4/4.5 assert unchanged behavior, consistent with a one-entry patch) nor invent behavior; the modeling boundary is the changed m12 entry itself, correctly biconditional against the reference formula. FAITHFUL.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The one fully-worked symbolic case in the requirements (Quaternion(cos(x/2), sin(x/2), 0, 0) → standard rotation matrix with -sin(x) above and +sin(x) below the diagonal) is verbatim from the PUBLIC problem_statement, which shows this exact quaternion and its buggy output and states 'One of the sin(x) functions should be negative.' The corrected target is the textbook result. The exact entry formulas (m12 = 2*s*(c*d - b*a), diagonal 1-2*s*(...), other off-diagonals) derive from the PUBLIC source file quaternion.py, which is directly linked in the problem_statement — they describe the method's own behavior, legitimate localization. The hidden test's distinctive numeric parametrized case (q1.to_rotation_matrix() == Matrix with entries -S(2)/3, S(2)/15, S(11)/15, S(14)/15, etc., and the 4×4 variant with S(4)/5, -S(2)/5) is NOT reproduced or enumerated anywhere in requirements.md. No test names (test_quaternion_conversions, test_quaternion_rotation_iss1593), no test file path, no 'issue 1593' marker, no quoted test/gold code, no fix-invented identifiers. Requirement 3's affine translation-column formula describes the method's public behavior, not a test id. Nothing beyond the public problem statement is transmitted.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
