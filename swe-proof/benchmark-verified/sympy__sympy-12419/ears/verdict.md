# P2 adversarial audit — sympy__sympy-12419

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
# Positive control: Req 1.3 - undetermined symbolic positions must NOT be a definite 0
from sympy import Identity, symbols, S
n, i, j = symbols('n i j', integer=True)
e = Identity(n)[i, j]
print("Identity(n)[i,j] =", repr(e))
# base returns S.Zero; patched returns a symbolic indicator (KroneckerDelta)
ok = (e != S.Zero) and (e is not S.Zero)
print("is definite zero?", e is S.Zero)
import sys
sys.exit(0 if ok else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
# Req 1.4: the symbolic indicator evaluates to 1 when positions made equal, 0 when unequal
from sympy import Identity, symbols, S
n, i, j = symbols('n i j', integer=True)
e = Identity(n)[i, j]
eq = e.subs(j, i)
neq = e.subs(j, i + 1)
print("subs j->i :", repr(eq))
print("subs j->i+1:", repr(neq))
ok = (eq == S.One) and (neq == S.Zero)
import sys
sys.exit(0 if ok else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
# Req 2.1/2.2: double Sum over identity elements retains diagonal, evaluates to order
from sympy import Identity, Sum, symbols
n = symbols('n', integer=True, positive=True)
i, j = symbols('i j', integer=True)
expr = Sum(Sum(Identity(n)[i, j], (i, 0, n - 1)), (j, 0, n - 1)).doit()
print("double sum =", repr(expr))
val = expr.subs(n, 5)
print("at n=5:", repr(val))
ok = (int(val) == 5)
import sys
sys.exit(0 if ok else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
# Req 3.7: concrete positions still 1 (equal) and 0 (distinct); Req 1.1/1.2
from sympy import Identity, symbols, S
n = symbols('n', integer=True)
I = Identity(n)
a = I[2, 2]
b = I[1, 2]
print("[2,2]=", repr(a), " [1,2]=", repr(b))
ok = (a == S.One) and (b == S.Zero)
import sys
sys.exit(0 if ok else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
# Req 1.5: element for undetermined positions is not equal to 0 (Ne does not reduce to false)
from sympy import Identity, symbols, S, Ne
n, i, j = symbols('n i j', integer=True)
e = Identity(n)[i, j]
rel = Ne(e, 0)
print("Ne(e,0) =", repr(rel))
ok = rel is not S.false
import sys
sys.exit(0 if ok else 1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
# Req 3.1-3.6: algebraic regressions of Identity
from sympy import Identity, MatrixSymbol, symbols, S, transpose, conjugate
n = symbols('n', integer=True)
I = Identity(n)
A = MatrixSymbol('A', n, n)
checks = {}
checks['I*A'] = (I * A).doit() == A
checks['A*I'] = (A * I).doit() == A
checks['transpose'] = transpose(I).doit() == I
checks['inverse'] = I.inverse() == I
checks['conjugate'] = I.conjugate() == I
checks['det'] = I._eval_determinant() == S.One
from sympy import Trace
checks['trace'] = Trace(I).doit() == n
for k, v in checks.items():
    print(k, v)
ok = all(checks.values())
import sys
sys.exit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
# Positive control: Req 1.3 - undetermined symbolic positions must NOT be a definite 0
from sympy import Identity, symbols, S
n, i, j = symbols('n i j', integer=True)
e = Identity(n)[i, j]
print("Identity(n)[i,j] =", repr(e))
# base returns S.Zero; patched returns a symbolic indicator (KroneckerDelta)
ok = (e != S.Zero) and (e is not S.Zero)
print("is definite zero?", e is S.Zero)
import sys
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Bundle: sympy__sympy-12419. Gold fix makes Identity._entry three-valued: returns S.One when Eq(i,j) is S.true, S.Zero when S.false, else KroneckerDelta(i,j).

Probes (all HOLD on gold-patched tree):
- probe_1 (POSITIVE CONTROL, Req 1.3): Identity(n)[i,j] for two distinct free symbols is NOT a definite S.Zero. HOLDS patched, FAILS at base (base returns S.Zero). Discriminates. prepatch_reproduced=true.
- probe_2 (Req 1.4): the symbolic indicator subs(j->i)==1 and subs(j->i+1)==0.
- probe_3 (Req 2.1/2.2): double Sum of Identity(n)[i,j] over 0..n-1 x 0..n-1, .doit() then subs(n,5)==5 (diagonal retained).
- probe_4 (Req 1.1/1.2/3.7): concrete [2,2]==1, [1,2]==0.
- probe_5 (Req 1.5): Ne(element,0) does not reduce to S.false.
- probe_6 (Req 3.1-3.6): I*A==A, A*I==A, transpose(I).doit()==I, I.inverse()==I, I.conjugate()==I, det==1, Trace(I).doit()==n. (Used I.conjugate() — the method Req 3.4 refers to — since this old sympy's conjugate(I).doit() returns Adjoint(I); a probe bug I corrected before submission.)

CANDIDATE WRONG PATCH (weak_eq.diff, applies at base): replaces _entry body with `return Eq(i, j)` — a naive 'symbolic indicator' reading. REJECTED by the suite: probe_2 fails (Eq(i,i) is S.true not 1, Eq(i,i+1) is S.false not 0), probe_3 fails (Sum of Booleans -> BooleanTrue, int() raises TypeError; diagonal not aggregated to order), probe_4 fails (concrete access returns Boolean, not 1/0). This demonstrates the suite discriminates a wrong-but-plausible fix.

All 6 probes hold on gold-patched; positive control discriminates base vs patched; candidate rejected. SOUND.

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
# Positive control: Req 1.3 - undetermined symbolic positions must NOT be a definite 0
from sympy import Identity, symbols, S
n, i, j = symbols('n i j', integer=True)
e = Identity(n)[i, j]
print("Identity(n)[i,j] =", repr(e))
# base returns S.Zero; patched returns a symbolic indicator (KroneckerDelta)
ok = (e != S.Zero) and (e is not S.Zero)
print("is definite zero?", e is S.Zero)
import sys
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Bundle: sympy__sympy-12419. Gold fix makes Identity._entry three-valued: returns S.One when Eq(i,j) is S.true, S.Zero when S.false, else KroneckerDelta(i,j).

Probes (all HOLD on gold-patched tree):
- probe_1 (POSITIVE CONTROL, Req 1.3): Identity(n)[i,j] for two distinct free symbols is NOT a definite S.Zero. HOLDS patched, FAILS at base (base returns S.Zero). Discriminates. prepatch_reproduced=true.
- probe_2 (Req 1.4): the symbolic indicator subs(j->i)==1 and subs(j->i+1)==0.
- probe_3 (Req 2.1/2.2): double Sum of Identity(n)[i,j] over 0..n-1 x 0..n-1, .doit() then subs(n,5)==5 (diagonal retained).
- probe_4 (Req 1.1/1.2/3.7): concrete [2,2]==1, [1,2]==0.
- probe_5 (Req 1.5): Ne(element,0) does not reduce to S.false.
- probe_6 (Req 3.1-3.6): I*A==A, A*I==A, transpose(I).doit()==I, I.inverse()==I, I.conjugate()==I, det==1, Trace(I).doit()==n. (Used I.conjugate() — the method Req 3.4 refers to — since this old sympy's conjugate(I).doit() returns Adjoint(I); a probe bug I corrected before submission.)

CANDIDATE WRONG PATCH (weak_eq.diff, applies at base): replaces _entry body with `return Eq(i, j)` — a naive 'symbolic indicator' reading. REJECTED by the suite: probe_2 fails (Eq(i,i) is S.true not 1, Eq(i,i+1) is S.false not 0), probe_3 fails (Sum of Booleans -> BooleanTrue, int() raises TypeError; diagonal not aggregated to order), probe_4 fails (concrete access returns Boolean, not 1/0). This demonstrates the suite discriminates a wrong-but-plausible fix.

All 6 probes hold on gold-patched; positive control discriminates base vs patched; candidate rejected. SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Patch: Identity._entry becomes three-valued via eq=Eq(i,j): S.One if eq is S.true, S.Zero if eq is S.false, else KroneckerDelta(i,j). Requirements pin exactly this changed observable behavior (the KroneckerDelta indicator) plus the downstream summation fix, matching the gold test_patch (In[i,j]!=0; Sum(...).subs(n,3).doit()==3 for both combined and nested groupings). Modeling boundary is correct — R1 targets the changed _entry behavior itself, not a narrow branch. Caveat, non-diverging: R2.2 is stated as 'after the symbolic order is replaced by a concrete positive integer', i.e. subs-first-then-doit — which is exactly what the gold test does and what works; the pure doit-first symbolic path leaves an unevaluated Piecewise Sum, but no requirement asserts that path resolves, so requirements and code agree. Base (unpatched) probe confirms twin fails: _entry(i,j)==0 and double sum subs(5) collapses to 0.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The requirements describe the fix behaviorally without transmitting hidden-test/gold content. Legitimate localization: naming sympy/matrices/expressions/matexpr.py and Identity._entry(i,j) is required to localize the change and is not a leak. The gold's fix-invented mechanism (KroneckerDelta / Eq(i,j) three-way branch) is NOT named — the doc uses the abstracted phrase 'symbolic indicator of the equality of the two positions', which is a behavioral description, not the invented identifier. No test names/paths/parametrization ids appear (test_Identity, test file path, FAIL_TO_PASS all absent). The double-Sum example is already public in the problem_statement. Reviewed borderline items: (a) Req 1.5 ('inequality comparison against zero SHALL NOT reduce to false') translates the test assertion `In[i,j] != 0` into a behavioral requirement — this is legitimate behavior-translation, not test code. (b) Req 2.2 uses the generic 'concrete positive integer' rather than the test's specific value 3 — no parametrization value leaked. (c) Req 2.3 (grouping/ordering invariance) is the closest to mirroring the test's two summation forms (combined-range vs nested Sum), but it states a genuine mathematical invariance property rather than reconstructing the test; the nested form itself is public in the problem_statement. (d) Req 3's enumeration of identity properties (mult, transpose, inverse, conjugate, determinant, trace) are standard identity-matrix properties/regression descriptions, not verbatim gold or test-only content. No verbatim gold-patch lines are quoted.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
