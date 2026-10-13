# P2 adversarial audit — sympy__sympy-13757

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
"""Req1.2 / positive control: x * Poly(x) must return Poly(x**2, x) over ZZ."""
import sys
from sympy import symbols, Poly
x = symbols('x')
res = x * Poly(x, x)
print("x * Poly(x) =", repr(res))
expected = Poly(x**2, x)
ok = isinstance(res, Poly) and res == expected
print("is Poly:", isinstance(res, Poly), "equals Poly(x**2,x):", res == expected)
sys.exit(0 if ok else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""Req1.3: S(-2) * Poly(x) must evaluate to Poly(-2*x, x), never unevaluated Mul."""
import sys
from sympy import symbols, Poly, S, Mul
x = symbols('x')
res = S(-2) * Poly(x, x)
print("S(-2) * Poly(x) =", repr(res))
expected = Poly(-2*x, x)
ok = isinstance(res, Poly) and (not isinstance(res, Mul)) and res == expected
print("is Poly:", isinstance(res, Poly), "equals Poly(-2*x,x):", res == expected)
sys.exit(0 if ok else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""Req2.1: operand-order symmetry. Poly(x)*expr == expr*Poly(x) for convertible factors, both Poly."""
import sys
from sympy import symbols, Poly, sin, S
x, y = symbols('x y')
p = Poly(x, x)
cases = [x, 3, S(-2), y, sin(y)]
ok = True
for f in cases:
    left = p * f
    right = f * p
    same = left == right
    both_poly = isinstance(left, Poly) and isinstance(right, Poly)
    print("factor", repr(f), "-> left", repr(left), "right", repr(right), "equal:", same, "both Poly:", both_poly)
    if not (same and both_poly):
        ok = False
sys.exit(0 if ok else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""Req3.1/3.2: non-convertible factor (1/x) falls back to symbolic (non-Poly), same both orders."""
import sys
from sympy import symbols, Poly, Mul
x = symbols('x')
p = Poly(x, x)
f = 1/x  # negative power of generator -> not convertible
left = p * f
right = f * p
print("Poly(x)*(1/x) =", repr(left))
print("(1/x)*Poly(x) =", repr(right))
not_poly = (not isinstance(left, Poly)) and (not isinstance(right, Poly))
same = left == right
print("neither Poly:", not_poly, "equal:", same)
sys.exit(0 if (not_poly and same) else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""Req1.1/3.3: factor not involving generators (sin(y)) -> Poly, absorbed as ground coeff, right operand."""
import sys
from sympy import symbols, Poly, sin
x, y = symbols('x y')
p = Poly(x, x)
res = sin(y) * p
print("sin(y) * Poly(x) =", repr(res))
expected = Poly(sin(y)*x, x)
ok = isinstance(res, Poly) and res == expected
print("is Poly:", isinstance(res, Poly), "equals Poly(sin(y)*x, x):", res == expected)
sys.exit(0 if ok else 1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
"""Req5.1 regression + Req4.1 precedence: established cases keep working and _op_priority set."""
import sys
from sympy import symbols, Poly
x = symbols('x')
ok = True
# established already-working cases
a = Poly(x, x) * 2
b = 2 * Poly(x, x)
c = Poly(x, x) * Poly(x, x)
print("Poly(x)*2 =", repr(a))
print("2*Poly(x) =", repr(b))
print("Poly(x)*Poly(x) =", repr(c))
if not (isinstance(a, Poly) and a == Poly(2*x, x)): ok = False
if not (isinstance(b, Poly) and b == Poly(2*x, x)): ok = False
if not (isinstance(c, Poly) and c == Poly(x**2, x)): ok = False
# Req4.1: Poly advertises higher op priority than generic Expr
prio = getattr(Poly, '_op_priority', None)
print("_op_priority =", prio)
if prio is None or not (prio > 10.0): ok = False
sys.exit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Req1.2 / positive control: x * Poly(x) must return Poly(x**2, x) over ZZ."""
import sys
from sympy import symbols, Poly
x = symbols('x')
res = x * Poly(x, x)
print("x * Poly(x) =", repr(res))
expected = Poly(x**2, x)
ok = isinstance(res, Poly) and res == expected
print("is Poly:", isinstance(res, Poly), "equals Poly(x**2,x):", res == expected)
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

6 probes cover Req1.2 (x*Poly(x)==Poly(x**2,x); positive control), Req1.3 (S(-2)*Poly(x) evaluates, not Mul), Req2.1 order symmetry over 5 factors incl. sin(y)/other-symbol, Req3.1/3.2 non-convertible 1/x symbolic fallback both orders, Req1.1/3.3 sin(y)*Poly(x)->Poly ground-coeff absorption, Req5.1 regression (Poly*2, 2*Poly, Poly*Poly) + Req4.1 _op_priority>10. ALL 6 HOLD on gold-patched tree; ALL 6 VIOLATED at base (positive control probe_1 fails at base -> prepatch reproduced). Wrong-fix candidate weak.diff sets _op_priority=10.0 (equal to Expr, not strictly greater), so SymPy binary-op dispatch never routes mixed products to Poly.__rmul__: the suite REJECTS it on all 6 probes, demonstrating discriminating power against the lazy reading of Req4.1. Suite discriminates base, gold, and a plausible-wrong patch.

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
"""Req1.2 / positive control: x * Poly(x) must return Poly(x**2, x) over ZZ."""
import sys
from sympy import symbols, Poly
x = symbols('x')
res = x * Poly(x, x)
print("x * Poly(x) =", repr(res))
expected = Poly(x**2, x)
ok = isinstance(res, Poly) and res == expected
print("is Poly:", isinstance(res, Poly), "equals Poly(x**2,x):", res == expected)
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

6 probes cover Req1.2 (x*Poly(x)==Poly(x**2,x); positive control), Req1.3 (S(-2)*Poly(x) evaluates, not Mul), Req2.1 order symmetry over 5 factors incl. sin(y)/other-symbol, Req3.1/3.2 non-convertible 1/x symbolic fallback both orders, Req1.1/3.3 sin(y)*Poly(x)->Poly ground-coeff absorption, Req5.1 regression (Poly*2, 2*Poly, Poly*Poly) + Req4.1 _op_priority>10. ALL 6 HOLD on gold-patched tree; ALL 6 VIOLATED at base (positive control probe_1 fails at base -> prepatch reproduced). Wrong-fix candidate weak.diff sets _op_priority=10.0 (equal to Expr, not strictly greater), so SymPy binary-op dispatch never routes mixed products to Poly.__rmul__: the suite REJECTS it on all 6 probes, demonstrating discriminating power against the lazy reading of Req4.1. Suite discriminates base, gold, and a plausible-wrong patch.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** The one-line gold patch adds `_op_priority = 10.001` to class Poly, raising its arithmetic-dispatch precedence above generic Expr (default 10.0) so SymPy routes mixed products to Poly.__rmul__. The requirements correctly pin the CHANGED OBSERVABLE BEHAVIOR (right-operand mixed products now evaluate; operand-order symmetry) plus the mechanism (Req4). The modeling boundary is right, not a narrow slice: it covers convertible cases (bare generator, numbers via S(-2), foreign symbols/functions absorbed as ground coefficients), non-convertible fallback both orders (function of generator, negative/rational powers), and regression preservation of left-operand and Poly*Poly cases. Coercion/fallback logic in __mul__/__rmul__ (unchanged by patch) is explicitly stated as pre-existing and to-be-preserved (intro para + Req1 note), matching the diff which touches nothing there. Probes: gold-patched ALL_ASSERTS_PASS (exit 0); base confirmed asymmetry (exit 0).


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** All concrete examples in requirements.md (Poly(x)*x, x*Poly(x), -2*Poly(x), S(-2)*Poly(x), Poly(x)*S(-2) and their polynomial results incl. domain='ZZ') come verbatim from the PUBLIC problem_statement. The gold edit's only content is `_op_priority = 10.001` on class Poly; the document describes this purely behaviorally ('arithmetic-dispatch precedence strictly greater than a generic SymPy expression', routing to __rmul__) without transmitting the attribute name or the numeric value. Hidden-test artifacts are NOT leaked: FAIL_TO_PASS name test_issue_13079, the file paths (test_polytools.py, test_match.py), and the test_mul change (I*Poly(x,x) matching I*p == {p: x}) do not appear anywhere. Requirement 5.1's Poly(x,x)*2 / 2*Poly(x,x) regression cases echo test_Poly_mul, but they are generic already-working-case protection derivable from the public -2 example and standard polynomial semantics, not a reconstruction of the parametrization. Requirement 3's non-convertible illustrations (sin(y), fractional/negative powers, rational expressions) are behavioral generalizations absent from any hidden test. Naming polytools.py, Poly, __mul__/__rmul__ is legitimate localization.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
