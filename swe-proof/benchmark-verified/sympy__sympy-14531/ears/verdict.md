# P2 adversarial audit — sympy__sympy-14531

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 7 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 7 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py`, `probe_7.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_2.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

Counterexample / evidence:

```
Weak patch (fixes only _print_Relational, leaves _print_Limit using bare %s) is REJECTED by probe_2: sstr(Limit(x, x, S(1)/2), sympy_integers=True) yields 'Limit(x, x, 1/2)' instead of required 'Limit(x, x, S(1)/2)'.
```

**Attacks re-run (7):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
import sys
from sympy import symbols, S, Eq
from sympy.printing.str import sstr

x = symbols('x')
got = sstr(Eq(x, S(1)/2), sympy_integers=True)
print("got:", repr(got))
sys.exit(0 if got == 'Eq(x, S(1)/2)' else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
import sys
from sympy import symbols, S, Limit
from sympy.printing.str import sstr

x = symbols('x')
got = sstr(Limit(x, x, S(1)/2), sympy_integers=True)
print("got:", repr(got))
sys.exit(0 if got == 'Limit(x, x, S(1)/2)' else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
import sys
from sympy import symbols, Eq
from sympy.printing.python import python

x, y = symbols('x y')
got = python(Eq(x, y))
print("got:", repr(got))
expected = "x = Symbol('x')\ny = Symbol('y')\ne = Eq(x, y)"
sys.exit(0 if got == expected else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
import sys
from sympy import symbols, Ge, Le, Gt, Lt, Eq, Ne
from sympy.printing.str import sstr
from sympy.printing.python import python

x, y = symbols('x y')
# Regression: default relational rendering unchanged
checks = {
    'Eq': (sstr(Eq(x, y)), 'Eq(x, y)'),
    'Ne': (sstr(Ne(x, y)), 'Ne(x, y)'),
    'Ge': (sstr(Ge(x, y)), 'x >= y'),
    'Le': (sstr(Le(x, y)), 'x <= y'),
    'Gt': (sstr(Gt(x, y)), 'x > y'),
    'Lt': (sstr(Lt(x, y)), 'x < y'),
}
ok = True
for k, (g, e) in checks.items():
    print(k, repr(g), "expected", repr(e))
    if g != e:
        ok = False

# python() ordering-relation regression
py_checks = {
    'Ge': (python(Ge(x, y)), "x = Symbol('x')\ny = Symbol('y')\ne = x >= y"),
    'Le': (python(Le(x, y)), "x = Symbol('x')\ny = Symbol('y')\ne = x <= y"),
    'Gt': (python(Gt(x, y)), "x = Symbol('x')\ny = Symbol('y')\ne = x > y"),
    'Lt': (python(Lt(x, y)), "x = Symbol('x')\ny = Symbol('y')\ne = x < y"),
}
for k, (g, e) in py_checks.items():
    print("python", k, repr(g))
    if g != e:
        ok = False

sys.exit(0 if ok else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
import sys
from sympy import symbols, S, Limit, Eq, Ne
from sympy.printing.str import sstr

x, y = symbols('x y')
ok = True
# Limit default layout unchanged
g = sstr(Limit(x, x, 0))
print("Limit default:", repr(g))
if g != 'Limit(x, x, 0)':
    ok = False
g2 = sstr(Limit(x, x, 0, dir='-'))
print("Limit dir:", repr(g2))
if g2 != "Limit(x, x, 0, dir='-')":
    ok = False
# bare sum already correct, unchanged
g3 = sstr(x + S(1)/2, sympy_integers=True)
print("sum:", repr(g3))
if g3 != 'x + S(1)/2':
    ok = False
# default settings sum unchanged
g4 = sstr(x + S(1)/2)
print("sum default:", repr(g4))
if g4 != 'x + 1/2':
    ok = False
sys.exit(0 if ok else 1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
import sys
from sympy import symbols, S, Ne
from sympy.printing.str import sstr

x = symbols('x')
# Ne container should also honor sympy_integers on its rational side
got = sstr(Ne(x, S(1)/2), sympy_integers=True)
print("got:", repr(got))
sys.exit(0 if got == 'Ne(x, S(1)/2)' else 1)
```

Attack 7 — `probe_7.py` → holds on the patched tree (good)

```python
import sys
from sympy import symbols, Eq
from sympy.printing.python import python

x, y, z = symbols('x y z')
# Requirement 4.3: nested free symbols in compound relational sides declared
got = python(Eq(x + y, z))
print("got:", repr(got))
# every free symbol declared
ok = all(("%s = Symbol('%s')" % (n, n)) in got for n in ('x', 'y', 'z'))
ok = ok and got.strip().splitlines()[-1].startswith('e = Eq(')
print("all symbols declared:", ok)
sys.exit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_2.py`

```python
import sys
from sympy import symbols, S, Limit
from sympy.printing.str import sstr

x = symbols('x')
got = sstr(Limit(x, x, S(1)/2), sympy_integers=True)
print("got:", repr(got))
sys.exit(0 if got == 'Limit(x, x, S(1)/2)' else 1)
```

Prepatch bug re-encoded as an attack: `True`.

7 probes cover Req1 (probe_1 Eq(x,S(1)/2)->Eq(x,S(1)/2); probe_6 Ne), Req2 (probe_2 Limit S(1)/2 form; probe_5 Limit default+dir layout), Req4 (probe_3 python(Eq(x,y)) exact; probe_7 nested compound-side free-symbol declarations), Req1.4/Req4.4/Req5 regressions (probe_4 default Eq/Ne/Ge/Le/Gt/Lt and python ordering-relations; probe_5 bare sum sympy_integers + default sum). ALL 7 HOLD on gold-patched tree. Positive controls (probes 1,2,3,6,7) FAIL at base — prepatch reproduced. Regression probes 4,5 also hold at base (as expected; they encode unchanged behavior). The requirements-conforming-but-partial candidate weak.diff is REJECTED by probe_2, demonstrating the suite discriminates an incomplete fix (Limit not routed through printer). Suite is sound and discriminating.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 7 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 7 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py`, `probe_7.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_2.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

Counterexample / evidence:

```
Weak patch (fixes only _print_Relational, leaves _print_Limit using bare %s) is REJECTED by probe_2: sstr(Limit(x, x, S(1)/2), sympy_integers=True) yields 'Limit(x, x, 1/2)' instead of required 'Limit(x, x, S(1)/2)'.
```

**Attacks re-run (7):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts, and on this backend both roles put it through the same derivation: every block below is a requirement probe run on the gold-patched tree, and the `machine verdict:` line each role publishes above reports BOTH that its probes hold there and how many candidate patches the probe suite rejected — so the two roles re-ran ONE probe suite and each recorded its own outcome for every probe in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `probe_1.py` → holds on the patched tree (good)

Attack 2 — `probe_2.py` → holds on the patched tree (good)

Attack 3 — `probe_3.py` → holds on the patched tree (good)

Attack 4 — `probe_4.py` → holds on the patched tree (good)

Attack 5 — `probe_5.py` → holds on the patched tree (good)

Attack 6 — `probe_6.py` → holds on the patched tree (good)

Attack 7 — `probe_7.py` → holds on the patched tree (good)

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_2.py`

```python
import sys
from sympy import symbols, S, Limit
from sympy.printing.str import sstr

x = symbols('x')
got = sstr(Limit(x, x, S(1)/2), sympy_integers=True)
print("got:", repr(got))
sys.exit(0 if got == 'Limit(x, x, S(1)/2)' else 1)
```

Prepatch bug re-encoded as an attack: `True`.

7 probes cover Req1 (probe_1 Eq(x,S(1)/2)->Eq(x,S(1)/2); probe_6 Ne), Req2 (probe_2 Limit S(1)/2 form; probe_5 Limit default+dir layout), Req4 (probe_3 python(Eq(x,y)) exact; probe_7 nested compound-side free-symbol declarations), Req1.4/Req4.4/Req5 regressions (probe_4 default Eq/Ne/Ge/Le/Gt/Lt and python ordering-relations; probe_5 bare sum sympy_integers + default sum). ALL 7 HOLD on gold-patched tree. Positive controls (probes 1,2,3,6,7) FAIL at base — prepatch reproduced. Regression probes 4,5 also hold at base (as expected; they encode unchanged behavior). The requirements-conforming-but-partial candidate weak.diff is REJECTED by probe_2, demonstrating the suite discriminates an incomplete fix (Limit not routed through printer). Suite is sound and discriminating.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** The gold patch replaces bare %s/str() interpolation with self._print(...) across exactly the methods the requirements enumerate: _print_Relational (charmap/function-call branch only, ordering relations kept infix per Req 1.4/4.4), _print_Limit, _print_AppliedPredicate, _print_ExprCondPair, _print_Lambda, _print_MatrixElement, _print_Normal, _print_Uniform, _print_Permutation, _print_PermutationGroup, _print_PolyRing, _print_FracField. Requirements pin the changed OBSERVABLE behavior (settings propagation + PythonPrinter symbol registration side-effect) biconditionally, not a narrow slice/helper. Probe confirms all patched outputs and preserved defaults. No mandated behavior the code lacks, no forbidden behavior it has, no invented behavior.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Requirements localize the change by naming the affected StrPrinter methods (AppliedPredicate, ExprCondPair, Lambda, Limit, MatrixElement, Normal, Uniform, Permutation, PermutationGroup, PolyRing, FracField, Relational) — which matches the gold patch's edited-method set, but naming modules/functions to localize is explicitly legitimate. No test file paths, test function names (test_Rational, test_python_relational), or parametrization ids are transmitted. The concrete examples used in requirements (Eq(x, S(1)/2), Limit(x, x, S(1)/2), python(Eq(x,y)) -> "x = Symbol('x')\ny = Symbol('y')\ne = Eq(x, y)") all come verbatim from the PUBLIC problem_statement, not from the hidden tests. Crucially, the requirements do NOT use the hidden test's distinctive values (Rational(2,3) -> S(2)/3, Rational(7,2) -> S(7)/2); they use the problem-statement's S(1)/2. Req 4.4 enumerates Ge/Le/Gt/Lt regression outputs (e = x >= y, etc.), which mirrors the test's regression block, but these are pre-existing behaviors preserved, and the Symbol-declaration output format is already public via the problem_statement. The fix invents no identifiers (mechanical str()->self._print swap), so no fix-invented identifier can leak. This is behavioral translation of what the tests check, not transmission of the tests themselves.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
