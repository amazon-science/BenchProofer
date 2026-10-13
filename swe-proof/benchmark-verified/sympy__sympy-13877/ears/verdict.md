# P2 adversarial audit — sympy__sympy-13877

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

**Attacks re-run (6):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
"""Positive control (Req 1.6, 1.1, 1.2): det() default Bareiss on the reported
family — entry in row j, column i equals i + a*j — at n=5 (a Bareiss size that
previously failed) returns a finite, mathematically-zero determinant, no nan,
no TypeError. At base this returns nan. Req 1.6 also demands (det == 0) is True."""
import sys
from sympy import Matrix, symbols, nan
from sympy.core.function import expand

a = symbols('a')
# entry row j, col i = i + a*j  ->  outer loop rows=j, inner cols=i
M = lambda n: Matrix([[i + a*j for i in range(n)] for j in range(n)])
n = 5
try:
    d = M(n).det()  # default method='bareiss'
except TypeError as e:
    print("FAIL: det() raised TypeError:", e)
    sys.exit(1)
print("det M(5) =", d)
if d is nan:
    print("FAIL: det returned nan")
    sys.exit(1)
if expand(d) != 0:
    print("FAIL: det not mathematically zero, expand =", expand(d))
    sys.exit(1)
if (d == 0) is not True:
    print("FAIL: (det == 0) not True, got", d == 0)
    sys.exit(1)
print("OK: det M(5) finite, mathematically zero, (det==0) is True")
sys.exit(0)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""Req 1.6 / 1.1 / 1.2: for the reported family (entry row j, col i = i + a*j) at
Bareiss sizes n=5,6,7 that previously returned nan / raised TypeError, det()
SHALL return an expression equal to zero (det==0 True), finite, no exception."""
import sys
from sympy import Matrix, symbols, nan
from sympy.core.function import expand

a = symbols('a')
M = lambda n: Matrix([[i + a*j for i in range(n)] for j in range(n)])
ok = True
for n in (5, 6, 7):
    try:
        d = M(n).det()
    except Exception as e:
        print("FAIL n=%d raised %r" % (n, e)); ok = False; continue
    cmp0 = (d == 0)
    print("n=%d det=%s  (det==0) -> %s" % (n, d, cmp0))
    if d is nan:
        print("FAIL n=%d det is nan" % n); ok = False
    if cmp0 is not True:
        print("FAIL n=%d det==0 not True" % n); ok = False
    if expand(d) != 0:
        print("FAIL n=%d not mathematically zero" % n); ok = False
sys.exit(0 if ok else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""Req 2.2 (regression): Bareiss agrees with berkowitz on symbolic matrices,
including ones with structurally-nonzero-but-mathematically-zero column entries.
Also Req 1.1 correctness: for a full-rank symbolic matrix the bareiss det is
correct (matches berkowitz)."""
import sys
from sympy import Matrix, Symbol
from sympy.core.function import expand

a, x, y = Symbol('a'), Symbol('x'), Symbol('y')
mats = [
    Matrix(4, 4, lambda i, j: i + a*j),          # rank-deficient family
    Matrix([[x, y, 1], [y, x, 2], [1, 2, x*y]]), # generic symbolic 3x3
    Matrix([[x**2 - x*x, 1, 2], [3, x, 4], [5, 6, x]]),  # leading entry cancels to 0
    Matrix([[1, 2, 3, 4], [x, x**2, x, 1], [0, 1, 0, 2], [x-x, 3, x, 1]]),
]
ok = True
for i, M in enumerate(mats):
    db = M.det(method='bareiss')
    dk = M.det(method='berkowitz')
    same = expand(db - dk) == 0
    print("mat %d: bareiss-berkowitz zero? %s  (b=%s)" % (i, same, db))
    if not same:
        print("FAIL mat %d disagreement: bareiss=%s berkowitz=%s" % (i, db, dk))
        ok = False
sys.exit(0 if ok else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""Req 2.1 & 2.4 (regression): integer-valued matrices and small (size 0/1/2/3)
matrices return the exact known determinants under Bareiss."""
import sys
from sympy import Matrix, eye, zeros, Symbol

ok = True
cases = [
    (Matrix([[1, 2], [3, 4]]), -2),
    (Matrix([[2, 3, 4], [5, 6, 7], [8, 9, 1]]), (2*(6*1-7*9) - 3*(5*1-7*8) + 4*(5*9-6*8))),
    (eye(4), 1),
    (Matrix([[3]]), 3),
    (zeros(0, 0), 1),   # empty det = 1
    (Matrix([[1,2,3,4],[5,6,7,8],[2,6,4,8],[3,1,1,2]]), None),  # compare bareiss vs berkowitz
]
for M, expected in cases:
    d = M.det(method='bareiss')
    if expected is None:
        dk = M.det(method='berkowitz')
        print("int mat det bareiss=%s berkowitz=%s" % (d, dk))
        if d != dk:
            print("FAIL disagreement"); ok = False
    else:
        print("det=%s expected=%s" % (d, expected))
        if d != expected:
            print("FAIL expected %s got %s" % (expected, d)); ok = False

# size 3 direct-formula: Req 1.7 / 2.4 — small member of family unchanged (nonzero form)
a = Symbol('a')
M3 = Matrix(3, 3, lambda i, j: i + a*j)
d3 = M3.det(method='bareiss')
print("family n=3 det =", d3)
from sympy.core.function import expand
if expand(d3) != 0:
    print("FAIL family n=3 not mathematically zero"); ok = False
sys.exit(0 if ok else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""Req 2.5 & 2.6 (regression): non-square raises the non-square error; unknown
method raises ValueError. Req 2.3: berkowitz and lu still work."""
import sys
from sympy import Matrix, Symbol
from sympy.matrices.matrices import NonSquareMatrixError

ok = True
# non-square
try:
    Matrix([[1, 2, 3], [4, 5, 6]]).det()
    print("FAIL: non-square did not raise"); ok = False
except NonSquareMatrixError:
    print("OK non-square raised NonSquareMatrixError")
except Exception as e:
    print("FAIL non-square raised wrong type %r" % e); ok = False

# unknown method
try:
    Matrix([[1, 2], [3, 4]]).det(method='bogus')
    print("FAIL: unknown method did not raise"); ok = False
except ValueError:
    print("OK unknown method raised ValueError")
except Exception as e:
    print("FAIL unknown method raised %r" % e); ok = False

# lu / berkowitz still compute
M = Matrix([[1, 2, 3], [4, 5, 6], [7, 8, 10]])
for m in ('lu', 'berkowitz'):
    d = M.det(method=m)
    print("method %s det=%s" % (m, d))
    if d != -3:
        print("FAIL method %s expected -3 got %s" % (m, d)); ok = False
sys.exit(0 if ok else 1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
"""Req 3: random_complex_number accepts optional tolerance defaulting to None;
rational=True honours tolerance; non-rational returns floats; default call
unchanged bounds."""
import sys
import inspect
from sympy.utilities.randtest import random_complex_number
from sympy import Rational, Float, nsimplify

ok = True
sig = inspect.signature(random_complex_number)
params = sig.parameters
if 'tolerance' not in params:
    print("FAIL: no tolerance parameter"); ok = False
else:
    if params['tolerance'].default is not None:
        print("FAIL tolerance default not None:", params['tolerance'].default); ok = False
    else:
        print("OK tolerance default None")

# rational=True returns rational parts
z = random_complex_number(rational=True)
re, im = z.as_real_imag()
if not (re.is_rational and im.is_rational):
    print("FAIL rational parts not rational:", re, im); ok = False
else:
    print("OK rational parts:", re, im)

# rational with tolerance honoured — must be a valid call and rational
z2 = random_complex_number(rational=True, tolerance=1e-2)
re2, im2 = z2.as_real_imag()
if not (re2.is_rational and im2.is_rational):
    print("FAIL rational+tolerance parts not rational:", re2, im2); ok = False
else:
    print("OK rational+tolerance:", re2, im2)

# non-rational returns floats (unchanged)
z3 = random_complex_number()
re3, im3 = z3.as_real_imag()
if not (re3.is_Float and im3.is_Float):
    print("FAIL default not float parts:", re3, im3); ok = False
else:
    print("OK default float parts")

# bounds honoured for default call: 2<=Re<=3, -1<=Im<=1
for _ in range(50):
    zz = random_complex_number()
    r, m = zz.as_real_imag()
    if not (2 <= float(r) <= 3 and -1 <= float(m) <= 1):
        print("FAIL bounds violated:", r, m); ok = False; break
else:
    print("OK bounds honoured over samples")
sys.exit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Positive control (Req 1.6, 1.1, 1.2): det() default Bareiss on the reported
family — entry in row j, column i equals i + a*j — at n=5 (a Bareiss size that
previously failed) returns a finite, mathematically-zero determinant, no nan,
no TypeError. At base this returns nan. Req 1.6 also demands (det == 0) is True."""
import sys
from sympy import Matrix, symbols, nan
from sympy.core.function import expand

a = symbols('a')
# entry row j, col i = i + a*j  ->  outer loop rows=j, inner cols=i
M = lambda n: Matrix([[i + a*j for i in range(n)] for j in range(n)])
n = 5
try:
    d = M(n).det()  # default method='bareiss'
except TypeError as e:
    print("FAIL: det() raised TypeError:", e)
    sys.exit(1)
print("det M(5) =", d)
if d is nan:
    print("FAIL: det returned nan")
    sys.exit(1)
if expand(d) != 0:
    print("FAIL: det not mathematically zero, expand =", expand(d))
    sys.exit(1)
if (d == 0) is not True:
    print("FAIL: (det == 0) not True, got", d == 0)
    sys.exit(1)
print("OK: det M(5) finite, mathematically zero, (det==0) is True")
sys.exit(0)
```

Prepatch bug re-encoded as an attack: `True`.

6 distinct probes, all HOLD on gold-patched tree; each re-runnable standalone (stdlib + sympy).

CRITICAL family-orientation note: Req 1.6 defines the matrix 'entry in row j, column i equals i + a*j', i.e. entry(row,col)=col+a*row. This matches the hidden test M = lambda n: Matrix([[i + a*j for i in range(n)] for j in range(n)]). The TRANSPOSE (Matrix(n,n,lambda i,j: i+a*j), entry=row+a*col) does NOT trigger the Bareiss nan bug on this image (returns 0 for n>=4 even at base) — an easy mis-encoding that would silently destroy discriminating power. Probes 1/2 use the requirement's exact orientation. Confirmed at base via diag2.py: family det n=3=nonzero, n=4=0, n=5=nan, n=6/n=7=TypeError('Invalid NaN comparison'); patched: n=5/6/7=0.

Probe coverage:
- probe_1 (POSITIVE CONTROL, Req 1.1/1.2/1.6): det() M(5) finite, mathematically zero, (det==0) is True, no nan/TypeError. HOLDS patched, VIOLATED base (prepatch reproduced).
- probe_2 (Req 1.6/1.1/1.2): family n=5,6,7 all det==0 True, finite, no exception. HOLDS patched, VIOLATED base.
- probe_3 (Req 2.2/1.1): bareiss agrees with berkowitz on 4 symbolic matrices incl. rank-deficient family and leading-entry-cancels-to-zero cases. HOLDS.
- probe_4 (Req 2.1/2.4/1.7): integer + size-0/1/2/3 direct-formula dets exact; family n=3 unchanged unsimplified nonzero form, mathematically zero. HOLDS.
- probe_5 (Req 2.3/2.5/2.6): non-square -> NonSquareMatrixError; unknown method -> ValueError; lu & berkowitz still compute correctly. HOLDS.
- probe_6 (Req 3.1-3.4): random_complex_number has tolerance param defaulting None; rational=True returns rational parts; rational+tolerance honoured; default returns floats; default bounds honoured over 50 samples. HOLDS.

CANDIDATE PATCH (weak.diff): applies ONLY the gold's randtest.py half (tolerance arg), leaving the _eval_det_bareiss pivot bug unfixed — the lazy 'fix half the diff' reading. Probes REJECT it: probe_1 VIOLATED, probe_2 VIOLATED (family n=5 still nan), while probe_6 (randtest) HOLDS. Demonstrates the suite discriminates a wrong impl on the core behavior. 1/1 weak candidate rejected.

Note on G-PANEL-2 fail in meta.json: that is a faithfulness/boundary observation about n=3 (direct 3x3 formula returns unsimplified nonzero form, unchanged) — but Req 1.7 explicitly acknowledges this (small members keep the pre-change unsimplified result). Req 1.6 correctly scopes the det==0 guarantee to Bareiss sizes only. So for the G-EQ (too-weak/too-strong) question the spec is SOUND: probes discriminate and no requirement-conforming weak patch survives.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 6 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 6 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

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
"""Positive control (Req 1.6, 1.1, 1.2): det() default Bareiss on the reported
family — entry in row j, column i equals i + a*j — at n=5 (a Bareiss size that
previously failed) returns a finite, mathematically-zero determinant, no nan,
no TypeError. At base this returns nan. Req 1.6 also demands (det == 0) is True."""
import sys
from sympy import Matrix, symbols, nan
from sympy.core.function import expand

a = symbols('a')
# entry row j, col i = i + a*j  ->  outer loop rows=j, inner cols=i
M = lambda n: Matrix([[i + a*j for i in range(n)] for j in range(n)])
n = 5
try:
    d = M(n).det()  # default method='bareiss'
except TypeError as e:
    print("FAIL: det() raised TypeError:", e)
    sys.exit(1)
print("det M(5) =", d)
if d is nan:
    print("FAIL: det returned nan")
    sys.exit(1)
if expand(d) != 0:
    print("FAIL: det not mathematically zero, expand =", expand(d))
    sys.exit(1)
if (d == 0) is not True:
    print("FAIL: (det == 0) not True, got", d == 0)
    sys.exit(1)
print("OK: det M(5) finite, mathematically zero, (det==0) is True")
sys.exit(0)
```

Prepatch bug re-encoded as an attack: `True`.

6 distinct probes, all HOLD on gold-patched tree; each re-runnable standalone (stdlib + sympy).

CRITICAL family-orientation note: Req 1.6 defines the matrix 'entry in row j, column i equals i + a*j', i.e. entry(row,col)=col+a*row. This matches the hidden test M = lambda n: Matrix([[i + a*j for i in range(n)] for j in range(n)]). The TRANSPOSE (Matrix(n,n,lambda i,j: i+a*j), entry=row+a*col) does NOT trigger the Bareiss nan bug on this image (returns 0 for n>=4 even at base) — an easy mis-encoding that would silently destroy discriminating power. Probes 1/2 use the requirement's exact orientation. Confirmed at base via diag2.py: family det n=3=nonzero, n=4=0, n=5=nan, n=6/n=7=TypeError('Invalid NaN comparison'); patched: n=5/6/7=0.

Probe coverage:
- probe_1 (POSITIVE CONTROL, Req 1.1/1.2/1.6): det() M(5) finite, mathematically zero, (det==0) is True, no nan/TypeError. HOLDS patched, VIOLATED base (prepatch reproduced).
- probe_2 (Req 1.6/1.1/1.2): family n=5,6,7 all det==0 True, finite, no exception. HOLDS patched, VIOLATED base.
- probe_3 (Req 2.2/1.1): bareiss agrees with berkowitz on 4 symbolic matrices incl. rank-deficient family and leading-entry-cancels-to-zero cases. HOLDS.
- probe_4 (Req 2.1/2.4/1.7): integer + size-0/1/2/3 direct-formula dets exact; family n=3 unchanged unsimplified nonzero form, mathematically zero. HOLDS.
- probe_5 (Req 2.3/2.5/2.6): non-square -> NonSquareMatrixError; unknown method -> ValueError; lu & berkowitz still compute correctly. HOLDS.
- probe_6 (Req 3.1-3.4): random_complex_number has tolerance param defaulting None; rational=True returns rational parts; rational+tolerance honoured; default returns floats; default bounds honoured over 50 samples. HOLDS.

CANDIDATE PATCH (weak.diff): applies ONLY the gold's randtest.py half (tolerance arg), leaving the _eval_det_bareiss pivot bug unfixed — the lazy 'fix half the diff' reading. Probes REJECT it: probe_1 VIOLATED, probe_2 VIOLATED (family n=5 still nan), while probe_6 (randtest) HOLDS. Demonstrates the suite discriminates a wrong impl on the core behavior. 1/1 weak candidate rejected.

Note on G-PANEL-2 fail in meta.json: that is a faithfulness/boundary observation about n=3 (direct 3x3 formula returns unsimplified nonzero form, unchanged) — but Req 1.7 explicitly acknowledges this (small members keep the pre-change unsimplified result). Req 1.6 correctly scopes the det==0 guarantee to Bareiss sizes only. So for the G-EQ (too-weak/too-strong) question the spec is SOUND: probes discriminate and no requirement-conforming weak patch survives.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Requirements correctly pin the CHANGED observable behavior (Bareiss det no longer returns nan/raises on the reported rank-deficient family; result is a genuine mathematical zero for n>=5) rather than a narrow slice, and correctly carve out the size-0..3 direct-formula path as unchanged (Req 1.7 explicitly preserves the unsimplified n=3 output). The modeling boundary is the pivot zero-test used inside fraction-free elimination, which is precisely the gold change (_is_zero_after_expand_mul via _find_reasonable_pivot). The randtest tolerance change (Req 3) is described faithfully. No mandated behavior the code lacks, no forbidden behavior it has, no invented behavior. Base-vs-patched divergence confirmed by nl_attack probe (base: n=5 -> nan; patched: n=5 -> 0).


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** requirements.md stays within behavioral translation. The matrix family [[i + a*j ...]], its zero-ness (f(1)=0,f(4)=0), the nan/TypeError failures, the Bareiss method / _eval_det_bareiss, and the pivot-selection root cause are all PUBLIC in problem_statement. The document does NOT: name the fix-invented helper _is_zero_after_expand_mul; quote gold code (expand_mul==0, _find_reasonable_pivot(iszerofunc=...)); name the test (test_determinant) or path; or enumerate the exact parametrized sizes 5/6/7 (it says 'sizes above the direct-formula cases', describing behavior not the test cases). Req 2.7's 'reasonable-pivot selection helpers / naive reasonable-pivot search' is generic naming of pre-existing public functions for localization, permitted. Req 3 (random_complex_number tolerance) is derived from the gold randtest.py edit but only names the real existing module/function and translates behavior — no test covers it (FAIL_TO_PASS is solely test_determinant) and no code/identifier is transmitted. No semantic gold/test reconstruction found.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
