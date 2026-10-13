# P2 adversarial audit — sympy__sympy-15345

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 7 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 7 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py`, `probe_7.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (7):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
#!/usr/bin/env python
# Req 1.1 (positive control): Max renders as Max[...] with square brackets, no round parens.
import sys
from sympy import symbols, Max
from sympy.printing.mathematica import mathematica_code as mcode

x = symbols('x')
out = mcode(Max(x, 2))
print("Max(x,2) ->", repr(out))
ok = out.startswith("Max[") and out.endswith("]") and "(" not in out and ")" not in out
sys.exit(0 if ok else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
#!/usr/bin/env python
# Req 1.2: Min renders as Min[...] with square brackets, no round parens.
import sys
from sympy import symbols, Min
from sympy.printing.mathematica import mathematica_code as mcode

x = symbols('x')
out = mcode(Min(x, 2))
print("Min(x,2) ->", repr(out))
ok = out.startswith("Min[") and out.endswith("]") and "(" not in out and ")" not in out
sys.exit(0 if ok else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
#!/usr/bin/env python
# Req 1.3 & 1.5: arguments joined by ", " (comma+single space) and in expr.args order.
import sys
from sympy import symbols, Max
from sympy.printing.mathematica import mathematica_code as mcode

x, y, z = symbols('x y z')
e = Max(x, y, z)
out = mcode(e)
print("expr.args =", e.args)
print("out =", repr(out))
inner = out[len("Max["):-1]  # strip Max[ ... ]
parts = inner.split(", ")
expected = [mcode(a) for a in e.args]
print("parts =", parts, "expected =", expected)
ok = out.startswith("Max[") and out.endswith("]") and parts == expected
# also verify separator is exactly ", " (comma then single space), reconstruct
ok = ok and inner == ", ".join(expected)
sys.exit(0 if ok else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
#!/usr/bin/env python
# Req 1.6 & 2.2: nested Max/Min uses brackets; product Max[...]*Min[...].
import sys
from sympy import symbols, Max, Min
from sympy.printing.mathematica import mathematica_code as mcode

x, y = symbols('x y')
# nested
nested = Max(x, Min(y, 2))
out_n = mcode(nested)
print("nested ->", repr(out_n))
# product of Max and Min
prod = Max(x, 2) * Min(y, 3)
out_p = mcode(prod)
print("product ->", repr(out_p))

ok_nested = "Max[" in out_n and "Min[" in out_n and "(" not in out_n and ")" not in out_n
ok_prod = ("Max[" in out_p and "Min[" in out_p and "*" in out_p
           and "(" not in out_p and ")" not in out_p)
print("ok_nested", ok_nested, "ok_prod", ok_prod)
sys.exit(0 if (ok_nested and ok_prod) else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
#!/usr/bin/env python
# Req 3.1/3.3/3.4/3.6/3.7/3.8: preserve existing behavior for recognized funcs,
# rationals, powers, constants, containers, integrals/derivatives.
import sys
from sympy import (symbols, sin, cos, exp, conjugate, Rational, oo, pi, Tuple,
                   Integral, Derivative, sqrt)
from sympy.printing.mathematica import mathematica_code as mcode

x, y = symbols('x y')
checks = {
    "sin": (mcode(sin(x)), "Sin[x]"),
    "cos": (mcode(cos(x)), "Cos[x]"),
    "exp": (mcode(exp(x)), "Exp[x]"),
    "conjugate": (mcode(conjugate(x)), "Conjugate[x]"),
    "rational": (mcode(Rational(-3, 4)), "-3/4"),
    "power": (mcode(x**3), "x^3"),
    "pi": (mcode(pi), "Pi"),
    "posinf": (mcode(oo), "Infinity"),
    "neginf": (mcode(-oo), "-Infinity"),
    "tuple": (mcode(Tuple(1, 2, 3)), "{1, 2, 3}"),
    "integral": (mcode(Integral(x, x)), "Hold[Integrate[x, x]]"),
    "derivative": (mcode(Derivative(x**2, x)), "Hold[D[x^2, x]]"),
}
ok = True
for name, (got, exp) in checks.items():
    good = got == exp
    ok = ok and good
    print(f"{name}: got={got!r} expected={exp!r} {'OK' if good else 'FAIL'}")
sys.exit(0 if ok else 1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
#!/usr/bin/env python
# Req 3.2: unrecognized function f rendered as f[x, y, z], args joined by ", ".
import sys
from sympy import symbols, Function
from sympy.printing.mathematica import mathematica_code as mcode

x, y, z = symbols('x y z')
f = Function('f')
out_f = mcode(f(x, y, z))
print("f(x,y,z) ->", repr(out_f))
ok_f = out_f == "f[x, y, z]"
sys.exit(0 if ok_f else 1)
```

Attack 7 — `probe_7.py` → holds on the patched tree (good)

```python
#!/usr/bin/env python
# Req 2.1: product with a Max factor uses square-bracket call joined by '*'.
# Req 3.9: expressions without Max/Min unchanged (regression on a product).
import sys
from sympy import symbols, Max
from sympy.printing.mathematica import mathematica_code as mcode

x, y = symbols('x y')
# product Req 2.1
p = 3 * Max(x, y)
out = mcode(p)
print("3*Max(x,y) ->", repr(out))
ok_p = "Max[" in out and "*" in out and out.count("(") == 0 and out.count(")") == 0
# Req 3.9: no Max/Min -> unchanged (a plain product)
out2 = mcode(2 * x * y)
print("2*x*y ->", repr(out2))
ok_plain = out2 == "2*x*y"
print("ok_p", ok_p, "ok_plain", ok_plain)
sys.exit(0 if (ok_p and ok_plain) else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
#!/usr/bin/env python
# Req 1.1 (positive control): Max renders as Max[...] with square brackets, no round parens.
import sys
from sympy import symbols, Max
from sympy.printing.mathematica import mathematica_code as mcode

x = symbols('x')
out = mcode(Max(x, 2))
print("Max(x,2) ->", repr(out))
ok = out.startswith("Max[") and out.endswith("]") and "(" not in out and ")" not in out
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance sympy-15345: Mathematica printer must render Max/Min as square-bracket Wolfram calls. Gold patch adds known_functions entries for Max/Min AND '_print_MinMaxBase = _print_Function' (the dispatch that actually routes MinMaxBase applications through _print_Function). 

7 probes cover the criteria:
- probe_1 (Req 1.1, POSITIVE CONTROL): Max(x,2) -> 'Max[2, x]', no round parens. HOLDS patched, FAILS at base ('Max(2, x)'). Discriminates.
- probe_2 (Req 1.2): Min -> 'Min[2, x]'. HOLDS patched, FAILS base.
- probe_3 (Req 1.3/1.5): args joined by exactly ', ' and in expr.args order. HOLDS patched, FAILS base.
- probe_4 (Req 1.6/2.2): nested Max/Min -> 'Max[x, Min[2, y]]'; product -> 'Max[2, x]*Min[3, y]'. HOLDS patched, FAILS base.
- probe_5 (Req 3.1/3.3/3.4/3.6/3.7/3.8): regression suite — sin/cos/exp/conjugate, -3/4, x^3, Pi, Infinity/-Infinity, Tuple {1,2,3}, Hold[Integrate], Hold[D]. All match expected. HOLDS patched.
- probe_6 (Req 3.2): unrecognized f(x,y,z) -> 'f[x, y, z]'. HOLDS patched.
- probe_7 (Req 2.1/3.9): 3*Max(x,y) -> '3*Max[x, y]'; 2*x*y -> '2*x*y' unchanged. HOLDS patched.

Note on Req 1.4 (single-arg): NOT reachable — SymPy's Max(x) auto-evaluates to x (0 args, not a MinMaxBase application), so no probe can exercise it against real code; excluded as a non-behavior, not a violation.

CANDIDATE WRONG PATCH (weak.diff): the lazy partial fix a weak reading permits — adds only the Max/Min known_functions entries but OMITS the '_print_MinMaxBase = _print_Function' dispatch. Without dispatch, MinMaxBase never reaches _print_Function, so known_functions is never consulted and output stays 'Max(2, x)'. Probes 1-4 REJECT it (exit 1, identical to base). This proves the suite discriminates the crucial dispatch line, which is the real fix. No requirements-conforming-yet-nonresolving patch found.

Verdict SOUND: all 7 probes hold on the gold-patched tree, positive control (probe_1) fails at base, and the plausible partial fix is caught by the suite.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 7 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 7 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py`, `probe_7.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

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
# Req 1.1 (positive control): Max renders as Max[...] with square brackets, no round parens.
import sys
from sympy import symbols, Max
from sympy.printing.mathematica import mathematica_code as mcode

x = symbols('x')
out = mcode(Max(x, 2))
print("Max(x,2) ->", repr(out))
ok = out.startswith("Max[") and out.endswith("]") and "(" not in out and ")" not in out
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance sympy-15345: Mathematica printer must render Max/Min as square-bracket Wolfram calls. Gold patch adds known_functions entries for Max/Min AND '_print_MinMaxBase = _print_Function' (the dispatch that actually routes MinMaxBase applications through _print_Function). 

7 probes cover the criteria:
- probe_1 (Req 1.1, POSITIVE CONTROL): Max(x,2) -> 'Max[2, x]', no round parens. HOLDS patched, FAILS at base ('Max(2, x)'). Discriminates.
- probe_2 (Req 1.2): Min -> 'Min[2, x]'. HOLDS patched, FAILS base.
- probe_3 (Req 1.3/1.5): args joined by exactly ', ' and in expr.args order. HOLDS patched, FAILS base.
- probe_4 (Req 1.6/2.2): nested Max/Min -> 'Max[x, Min[2, y]]'; product -> 'Max[2, x]*Min[3, y]'. HOLDS patched, FAILS base.
- probe_5 (Req 3.1/3.3/3.4/3.6/3.7/3.8): regression suite — sin/cos/exp/conjugate, -3/4, x^3, Pi, Infinity/-Infinity, Tuple {1,2,3}, Hold[Integrate], Hold[D]. All match expected. HOLDS patched.
- probe_6 (Req 3.2): unrecognized f(x,y,z) -> 'f[x, y, z]'. HOLDS patched.
- probe_7 (Req 2.1/3.9): 3*Max(x,y) -> '3*Max[x, y]'; 2*x*y -> '2*x*y' unchanged. HOLDS patched.

Note on Req 1.4 (single-arg): NOT reachable — SymPy's Max(x) auto-evaluates to x (0 args, not a MinMaxBase application), so no probe can exercise it against real code; excluded as a non-behavior, not a violation.

CANDIDATE WRONG PATCH (weak.diff): the lazy partial fix a weak reading permits — adds only the Max/Min known_functions entries but OMITS the '_print_MinMaxBase = _print_Function' dispatch. Without dispatch, MinMaxBase never reaches _print_Function, so known_functions is never consulted and output stays 'Max(2, x)'. Probes 1-4 REJECT it (exit 1, identical to base). This proves the suite discriminates the crucial dispatch line, which is the real fix. No requirements-conforming-yet-nonresolving patch found.

Verdict SOUND: all 7 probes hold on the gold-patched tree, positive control (probe_1) fails at base, and the plausible partial fix is caught by the suite.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Patch adds Max/Min to known_functions (lambda *x: True -> 'Max'/'Min') and aliases _print_MinMaxBase = _print_Function. Probed patched tree: Max(x,2)->'Max[2, x]', Min(x,2)->'Min[2, x]', Max(x)->'x' (single arg, no separator, Req1.4), Max(x,Min(y,2))->'Max[x, Min[2, y]]' (nested, Req1.6), 2*Max(x,y)->'2*Max[x, y]' (Req2.1), Max(x,y)*Min(x,y)->'Max[x, y]*Min[x, y]' (Req2.2). Base (unpatched) gives round-paren forms Max(2, x)/Min(2, x), confirming the discriminator. Preservation confirmed: sin->Sin[x], f(x,y,z)->f[x, y, z] (Req3.2), Integral->Hold[Integrate[x, x]] (Req3.8), Tuple->{1, 2, 3} (Req3.7), oo/-oo/pi->Infinity/-Infinity/Pi (Req3.6). Requirements pin the exact changed observable behavior (bracket call syntax) without inventing behavior or pinning a narrow slice.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The requirements describe printer behavior abstractly and localize the change to legitimately-public identifiers (mathematica_code, MCodePrinter, MinMaxBase in sympy.functions/printing.mathematica). No hidden-test content is transmitted: (1) The F2P test string is `mcode(Max(x,y,z)*Min(y,z)) == "Max[x, y, z]*Min[y, z]"`; the doc never quotes it — Req 2.2 states the product composition with generic placeholders `Max[...]*Min[...]`. Extending the public problem_statement (which mentions only Max) to Min and their product is a behavioral translation, since Min is the symmetric MinMaxBase partner and this is the stated purpose of the change, not test reconstruction. (2) Req 3's enumeration (Integer/Rational/Pow/Mul/constants/containers/Integral/Derivative) parallels the PASS_TO_PASS names, but describes source-observable public printer behavior (e.g. Hold[Integrate[...]], Hold[D[...]] are in public sympy source) and does NOT reconstruct the tests — the real test file additionally has test_matrices, test_NDArray, test_Sum, test_Relational, test_special_polynomials (none in doc) and the actual test_constants/test_Function check far more cases (Tribonacci, dozens of special functions) than the doc enumerates. It under-specifies relative to the hidden tests rather than mirroring them. (3) No test file paths, test function/class names, parametrization ids, verbatim gold-patch lines, or fix-invented identifiers (`_print_MinMaxBase` never appears). Generic examples like `f[x, y, z]` use conventional placeholder symbols describing the public generic-function fallback.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
