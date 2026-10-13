# P2 adversarial audit — sympy__sympy-12096

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
"""R1.3 positive control: composition f(g(2)) with f=x**2, g=2*x -> Float(16).
Should FAIL at base (returns unevaluated), HOLD on patched tree."""
import sys
from sympy.utilities.lambdify import implemented_function
from sympy import Float, Symbol

x = Symbol('x')
f = implemented_function('f', lambda x: x**2)
g = implemented_function('g', lambda x: 2*x)
expr = f(g(2))
res = expr.evalf()
print("f(g(2)).evalf() =", repr(res))
ok = isinstance(res, Float) and abs(float(res) - 16.0) < 1e-9
print("is Float(16)?", ok)
sys.exit(0 if ok else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""R2.1: single-level squaring applied to 2 -> Float(4). Must hold on both."""
import sys
from sympy.utilities.lambdify import implemented_function
from sympy import Float, Symbol

f = implemented_function('f', lambda x: x**2)
res = f(2).evalf()
print("f(2).evalf() =", repr(res))
ok = isinstance(res, Float) and abs(float(res) - 4.0) < 1e-9
print("is Float(4)?", ok)
sys.exit(0 if ok else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""R1.4/R1.5: arguments evaluated at requested precision; result is a Float
carrying that precision. Use purely-numeric implementations that yield an
irrational-in-decimal value: g=1/x, f=x**2. f(g(3)) = (1/3)**2 = 1/9,
which needs many digits to distinguish precision."""
import sys
import mpmath
from sympy.utilities.lambdify import implemented_function
from sympy import Float

f = implemented_function('f', lambda x: x**2)
g = implemented_function('g', lambda x: 1/x)
res = f(g(3)).evalf(50)
print("f(g(3)).evalf(50) =", repr(res))
if not isinstance(res, Float):
    print("not a Float")
    sys.exit(1)
mpmath.mp.dps = 60
expected = mpmath.mpf(1)/9
got = mpmath.mpf(str(res))
rel = abs(got - expected)/abs(expected)
print("relative error =", rel)
print("Float _prec (binary) =", res._prec)
ok = rel < mpmath.mpf(10)**(-45) and res._prec >= 160  # 50 dps ~ 166 bits
print("precise enough & high prec?", ok)
sys.exit(0 if ok else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""R2.2: implementation raising TypeError/ValueError/AttributeError -> evalf
leaves expression unevaluated (returns the function application), not an error."""
import sys
from sympy.utilities.lambdify import implemented_function
from sympy import Float

def bad(x):
    raise ValueError("nope")

f = implemented_function('f', bad)
try:
    res = f(2).evalf()
except Exception as e:
    print("ERROR propagated:", type(e).__name__, e)
    sys.exit(1)
print("f(2).evalf() =", repr(res))
# should be left unevaluated: NOT a Float
ok = not isinstance(res, Float)
print("left unevaluated (not Float)?", ok)
sys.exit(0 if ok else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""R2.3: mpmath-backed path unaffected. sin(1).evalf() must still use mpmath
and give the correct value regardless of this change."""
import sys
import mpmath
from sympy import sin, Float

res = sin(1).evalf(30)
print("sin(1).evalf(30) =", repr(res))
mpmath.mp.dps = 40
expected = mpmath.sin(1)
got = mpmath.mpf(str(res))
rel = abs(got - expected)/abs(expected)
print("relative error =", rel)
ok = isinstance(res, Float) and rel < mpmath.mpf(10)**(-28)
print("mpmath path correct?", ok)
sys.exit(0 if ok else 1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
"""R1.2 (three-level composition): f(g(h(2))) reduces recursively.
f=x**2, g=x+1, h=2*x. h(2)=4, g(4)=5, f(5)=25. Should FAIL at base
(inner apps unreduced), HOLD patched. Extra discriminator vs single-level fix."""
import sys
from sympy.utilities.lambdify import implemented_function
from sympy import Float

f = implemented_function('f', lambda x: x**2)
g = implemented_function('g', lambda x: x+1)
h = implemented_function('h', lambda x: 2*x)
res = f(g(h(2))).evalf()
print("f(g(h(2))).evalf() =", repr(res))
ok = isinstance(res, Float) and abs(float(res) - 25.0) < 1e-9
print("is Float(25)?", ok)
sys.exit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""R1.3 positive control: composition f(g(2)) with f=x**2, g=2*x -> Float(16).
Should FAIL at base (returns unevaluated), HOLD on patched tree."""
import sys
from sympy.utilities.lambdify import implemented_function
from sympy import Float, Symbol

x = Symbol('x')
f = implemented_function('f', lambda x: x**2)
g = implemented_function('g', lambda x: 2*x)
expr = f(g(2))
res = expr.evalf()
print("f(g(2)).evalf() =", repr(res))
ok = isinstance(res, Float) and abs(float(res) - 16.0) < 1e-9
print("is Float(16)?", ok)
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Gold fix: Float(self._imp_(*[i.evalf(prec) for i in self.args]), prec) in Function._eval_evalf (sympy/core/function.py). 6 probes, all HOLD on patched tree.

Probes:
- probe_1 (R1.3 positive control): f(g(2)) with f=x**2,g=2*x -> Float(16). HOLDS patched, FAILS at base (returns unevaluated f(g(2))). DISCRIMINATES.
- probe_2 (R2.1 regression): single-level f(2)=Float(4). HOLDS on base and patched.
- probe_3 (R1.4/R1.5 precision): f(g(3))=(1/3)**2=1/9 at prec 50; checks relative error <1e-45 AND Float _prec>=160 bits. HOLDS patched, FAILS at base. Crucially REJECTS the weak candidate.
- probe_4 (R2.2 error fallback): implementation raising ValueError -> evalf leaves expression unevaluated, no propagation. HOLDS both.
- probe_5 (R2.3 mpmath path): sin(1).evalf(30) still mpmath-accurate. HOLDS both.
- probe_6 (R1.2 three-level composition): f(g(h(2)))=25. HOLDS patched, FAILS at base. Extra discriminator beyond single-level.

Positive controls (1,3,6) all FAIL at base and HOLD patched (prepatch_reproduced=true).

Candidate patch weak_no_prec: naive fix using i.evalf() with NO precision argument. It satisfies the composition SHALLs (probes 1,6 HOLD) and single-level/fallback/mpmath (2,4,5 HOLD) but VIOLATES R1.4 'evaluated at the precision requested' — probe_3 REJECTS it (arguments evaluated at default 15-digit precision, so f(g(3)) at prec 50 has insufficient accuracy). This demonstrates the suite discriminates a requirements-plausible-but-wrong implementation. The gold patch passes probe_3 precisely because it passes `prec` into the recursive evalf.

Note: an earlier probe_3 draft used a symbolic-valued implementation (pi*x) which legitimately cannot reduce to Float and is outside spec scope; replaced with purely-numeric implementations (1/x, x**2) that stress precision without leaving the numeric domain.

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
"""R1.3 positive control: composition f(g(2)) with f=x**2, g=2*x -> Float(16).
Should FAIL at base (returns unevaluated), HOLD on patched tree."""
import sys
from sympy.utilities.lambdify import implemented_function
from sympy import Float, Symbol

x = Symbol('x')
f = implemented_function('f', lambda x: x**2)
g = implemented_function('g', lambda x: 2*x)
expr = f(g(2))
res = expr.evalf()
print("f(g(2)).evalf() =", repr(res))
ok = isinstance(res, Float) and abs(float(res) - 16.0) < 1e-9
print("is Float(16)?", ok)
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Gold fix: Float(self._imp_(*[i.evalf(prec) for i in self.args]), prec) in Function._eval_evalf (sympy/core/function.py). 6 probes, all HOLD on patched tree.

Probes:
- probe_1 (R1.3 positive control): f(g(2)) with f=x**2,g=2*x -> Float(16). HOLDS patched, FAILS at base (returns unevaluated f(g(2))). DISCRIMINATES.
- probe_2 (R2.1 regression): single-level f(2)=Float(4). HOLDS on base and patched.
- probe_3 (R1.4/R1.5 precision): f(g(3))=(1/3)**2=1/9 at prec 50; checks relative error <1e-45 AND Float _prec>=160 bits. HOLDS patched, FAILS at base. Crucially REJECTS the weak candidate.
- probe_4 (R2.2 error fallback): implementation raising ValueError -> evalf leaves expression unevaluated, no propagation. HOLDS both.
- probe_5 (R2.3 mpmath path): sin(1).evalf(30) still mpmath-accurate. HOLDS both.
- probe_6 (R1.2 three-level composition): f(g(h(2)))=25. HOLDS patched, FAILS at base. Extra discriminator beyond single-level.

Positive controls (1,3,6) all FAIL at base and HOLD patched (prepatch_reproduced=true).

Candidate patch weak_no_prec: naive fix using i.evalf() with NO precision argument. It satisfies the composition SHALLs (probes 1,6 HOLD) and single-level/fallback/mpmath (2,4,5 HOLD) but VIOLATES R1.4 'evaluated at the precision requested' — probe_3 REJECTS it (arguments evaluated at default 15-digit precision, so f(g(3)) at prec 50 has insufficient accuracy). This demonstrates the suite discriminates a requirements-plausible-but-wrong implementation. The gold patch passes probe_3 precisely because it passes `prec` into the recursive evalf.

Note: an earlier probe_3 draft used a symbolic-valued implementation (pi*x) which legitimately cannot reduce to Float and is outside spec scope; replaced with purely-numeric implementations (1/x, x**2) that stress precision without leaving the numeric domain.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Gold patch changes exactly one line in Function._eval_evalf (sympy/core/function.py): the fallback that applies the attached _imp_ now evaluates each argument first via i.evalf(prec). Requirements checked against real behavior in the instance image:
- Req 1.1/1.2 (recursively evalf each argument before applying _imp_): matches the list-comprehension over self.args.
- Req 1.3 (f(g(2)) with f=x**2,g=2x -> Float(16)): PROBED. Patched tree gives Float(16); base returns unevaluated f(g(2)) (AssertionError got f(g(2))). Exact match.
- Req 1.4 (args evaluated at requested precision): matches i.evalf(prec).
- Req 1.5 (result is Float at requested prec): matches Float(..., prec) wrapper.
- Req 2.1 (single-level f(2) -> Float(4)): PROBED, holds.
- Req 2.2 (only AttributeError/TypeError/ValueError caught -> return None): matches the UNCHANGED except clause; probe confirmed a KeyError-raising impl propagates (not swallowed).
- Req 2.3 (mpmath path unchanged): the getattr(mpmath, fname) branch is untouched by the patch.
- Req 2.4 (implemented_function/_imp_ reachability): preserved.
No requirement over-specifies, forbids present behavior, invents behavior, or pins a wrong/narrow boundary — the modeled boundary (recursive arg evalf in the _imp_ fallback) IS the changed observable behavior. Preservation clauses (Req 2) correctly fence the unchanged mpmath/error paths.

- Req 1.1/1.2 (recursively evalf each argument before applying _imp_): matches the list-comprehension over self.args.
- Req 1.3 (f(g(2)) with f=x**2,g=2x -> Float(16)): PROBED. Patched tree gives Float(16); base returns unevaluated f(g(2)) (AssertionError got f(g(2))). Exact match.
- Req 1.4 (args evaluated at requested precision): matches i.evalf(prec).
- Req 1.5 (result is Float at requested prec): matches Float(..., prec) wrapper.
- Req 2.1 (single-level f(2) -> Float(4)): PROBED, holds.
- Req 2.2 (only AttributeError/TypeError/ValueError caught -> return None): matches the UNCHANGED except clause; probe confirmed a KeyError-raising impl propagates (not swallowed).
- Req 2.3 (mpmath path unchanged): the getattr(mpmath, fname) branch is untouched by the patch.
- Req 2.4 (implemented_function/_imp_ reachability): preserved.
No requirement over-specifies, forbids present behavior, invents behavior, or pins a wrong/narrow boundary — the modeled boundary (recursive arg evalf in the _imp_ fallback) IS the changed observable behavior. Preservation clauses (Req 2) correctly fence the unchanged mpmath/error paths.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** All module/function/attribute names cited (Function._eval_evalf, sympy/core/function.py, implemented_function, _imp_, evalf) appear verbatim in the public problem_statement, so naming them is legitimate localization. The numeric anchors are public or public-derivable: Float(4) is literally shown in the problem_statement (f(2).evalf() -> 4.00000000000000), and Float(16) is the mathematical result of the public composition example f(g(2)) (g(2)=4, f(4)=16). The hidden test asserts f(f(2)).evalf()==Float(16) — a different composition — but the requirement frames its example around the public f(g(2)) and describes 'squaring composed on the value 4', i.e. behavior, not the test's f(f(2)) structure. No test file path (test_lambdify.py), test name (test_issue_12092), parametrization ids, gold-patch code (the '[i.evalf(prec) for i in self.args]' comprehension), or fix-invented identifiers are transmitted. The precision requirements (1.4/1.5) and error-fallback (2.2: AttributeError/TypeError/ValueError) describe behavior; the exception triple also matches the pre-existing except clause visible via the change context but is stated as required behavior, not as quoted test content. No semantic reconstruction of the hidden tests.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
