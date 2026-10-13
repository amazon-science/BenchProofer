# P2 adversarial audit — sympy__sympy-22914

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
import sys
from sympy import symbols, Min
from sympy.printing.pycode import PythonCodePrinter, pycode
x, y = symbols('x y')
out = PythonCodePrinter().doprint(Min(x, y))
print("Min(x,y) ->", repr(out))
# R1.1 + R1.4: exactly min(x, y)
ok = out == "min(x, y)"
print("pycode Min ->", repr(pycode(Min(x, y))))
sys.exit(0 if ok else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
import sys
from sympy import symbols, Max
from sympy.printing.pycode import PythonCodePrinter
x, y = symbols('x y')
out = PythonCodePrinter().doprint(Max(x, y))
print("Max(x,y) ->", repr(out))
# R1.2 + R1.4
sys.exit(0 if out == "max(x, y)" else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
import sys
from sympy import symbols, Min, Max
from sympy.printing.pycode import PythonCodePrinter
a, b, c = symbols('a b c')
o1 = PythonCodePrinter().doprint(Min(a, b, c))
o2 = PythonCodePrinter().doprint(Max(a, b, c))
print("Min 3-arg ->", repr(o1))
print("Max 3-arg ->", repr(o2))
# R1.3: comma+space separation. Min sorts args? Min(a,b,c) args order may reorder.
# Requirement says same order as function's args. Check both are a valid perm containing ", "
import re
def check(out, fn):
    m = re.fullmatch(fn + r"\((.*)\)", out)
    if not m:
        return False
    parts = m.group(1).split(", ")
    return set(parts) == {"a", "b", "c"} and len(parts) == 3
ok = check(o1, "min") and check(o2, "max")
sys.exit(0 if ok else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
import sys
from sympy import symbols, Min, Max
from sympy.printing.pycode import PythonCodePrinter
x, y = symbols('x y')
o1 = PythonCodePrinter().doprint(Min(x, y))
o2 = PythonCodePrinter().doprint(Max(x, y))
print("Min ->", repr(o1))
print("Max ->", repr(o2))
# R1.5: no "not supported" comment and no bare Min(/Max( fallback
bad = ("not supported" in o1.lower() or "not supported" in o2.lower()
       or "Min(" in o1 or "Max(" in o2)
sys.exit(0 if not bad else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
import sys
from sympy import symbols, Abs, sqrt, Rational
from sympy.printing.pycode import PythonCodePrinter, pycode
x = symbols('x')
# R2.1: Abs still -> abs, sqrt still math.sqrt
oa = PythonCodePrinter().doprint(Abs(x))
os_ = pycode(sqrt(x))
print("Abs(x) ->", repr(oa))
print("sqrt(x) ->", repr(os_))
ok = oa == "abs(x)" and "sqrt" in os_
sys.exit(0 if ok else 1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
import sys
from sympy import symbols, Min, Max
x, y = symbols('x y')
# R2.3: NumPy printer must NOT render plain min/max built-ins; keeps its own numpy.* form
from sympy.printing.numpy import NumPyPrinter
n1 = NumPyPrinter().doprint(Min(x, y))
n2 = NumPyPrinter().doprint(Max(x, y))
print("NumPy Min ->", repr(n1))
print("NumPy Max ->", repr(n2))
ok = n1 != "min(x, y)" and n2 != "max(x, y)" and "numpy." in n1 and "numpy." in n2
sys.exit(0 if ok else 1)
```

Attack 7 — `probe_7.py` → holds on the patched tree (good)

```python
import sys
from sympy import symbols, Min, Max
x, y = symbols('x y')
# R2.4: mpmath printer derives from PythonCodePrinter -> min/max
from sympy.printing.pycode import MpmathPrinter
m1 = MpmathPrinter().doprint(Min(x, y))
m2 = MpmathPrinter().doprint(Max(x, y))
print("Mpmath Min ->", repr(m1))
print("Mpmath Max ->", repr(m2))
sys.exit(0 if m1 == "min(x, y)" and m2 == "max(x, y)" else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
import sys
from sympy import symbols, Min
from sympy.printing.pycode import PythonCodePrinter, pycode
x, y = symbols('x y')
out = PythonCodePrinter().doprint(Min(x, y))
print("Min(x,y) ->", repr(out))
# R1.1 + R1.4: exactly min(x, y)
ok = out == "min(x, y)"
print("pycode Min ->", repr(pycode(Min(x, y))))
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance sympy__sympy-22914: PythonCodePrinter should render Min/Max as Python builtins min()/max(). Gold patch adds 'Min':'min','Max':'max' to _known_functions in sympy/printing/pycode.py.

Probes (all HOLD on gold-patched tree):
- probe_1 (R1.1/R1.4): PythonCodePrinter().doprint(Min(x,y)) == 'min(x, y)'. POSITIVE CONTROL: HOLDS patched, FAILS at base (base gives '((x) if (x <= y) else (y))'). Discriminates.
- probe_2 (R1.2/R1.4): Max(x,y) == 'max(x, y)'. Also fails at base.
- probe_3 (R1.3): 3-arg Min/Max args separated by ', '.
- probe_4 (R1.5): no 'not supported' comment, no bare Min(/Max( fallback text.
- probe_5 (R2.1): Abs still -> 'abs(x)', sqrt still 'math.sqrt(x)' (regression keep).
- probe_6 (R2.3): NumPyPrinter keeps its own form (numpy.amin/amax), NOT plain min/max. (Initial version wrongly expected numpy.minimum; corrected to check numpy.* form.)
- probe_7 (R2.4): MpmathPrinter (derives from PythonCodePrinter) -> 'min(x, y)'/'max(x, y)'.

Candidate wrong-fix 'partial_min_only' (weak.diff): adds only 'Min':'min', not Max. REJECTED by suite — probe_2 fails (Max not builtin) and probe_7 fails (mpmath Max not builtin). Demonstrates suite discriminates partial implementations.

Verdict SOUND: 7 distinct probes all hold on patched tree; positive control fails at base and holds patched (discriminating power confirmed); requirements-conforming partial patch is rejected by the probe suite.

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
import sys
from sympy import symbols, Min
from sympy.printing.pycode import PythonCodePrinter, pycode
x, y = symbols('x y')
out = PythonCodePrinter().doprint(Min(x, y))
print("Min(x,y) ->", repr(out))
# R1.1 + R1.4: exactly min(x, y)
ok = out == "min(x, y)"
print("pycode Min ->", repr(pycode(Min(x, y))))
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance sympy__sympy-22914: PythonCodePrinter should render Min/Max as Python builtins min()/max(). Gold patch adds 'Min':'min','Max':'max' to _known_functions in sympy/printing/pycode.py.

Probes (all HOLD on gold-patched tree):
- probe_1 (R1.1/R1.4): PythonCodePrinter().doprint(Min(x,y)) == 'min(x, y)'. POSITIVE CONTROL: HOLDS patched, FAILS at base (base gives '((x) if (x <= y) else (y))'). Discriminates.
- probe_2 (R1.2/R1.4): Max(x,y) == 'max(x, y)'. Also fails at base.
- probe_3 (R1.3): 3-arg Min/Max args separated by ', '.
- probe_4 (R1.5): no 'not supported' comment, no bare Min(/Max( fallback text.
- probe_5 (R2.1): Abs still -> 'abs(x)', sqrt still 'math.sqrt(x)' (regression keep).
- probe_6 (R2.3): NumPyPrinter keeps its own form (numpy.amin/amax), NOT plain min/max. (Initial version wrongly expected numpy.minimum; corrected to check numpy.* form.)
- probe_7 (R2.4): MpmathPrinter (derives from PythonCodePrinter) -> 'min(x, y)'/'max(x, y)'.

Candidate wrong-fix 'partial_min_only' (weak.diff): adds only 'Min':'min', not Max. REJECTED by suite — probe_2 fails (Max not builtin) and probe_7 fails (mpmath Max not builtin). Demonstrates suite discriminates partial implementations.

Verdict SOUND: 7 distinct probes all hold on patched tree; positive control fails at base and holds patched (discriminating power confirmed); requirements-conforming partial patch is rejected by the probe suite.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Requirements pin the CHANGED observable behavior correctly, not a narrow slice: Req2.4 captures the mpmath side-effect of the shared _known_functions table, and Req2.3 correctly excludes NumPy/SciPy (which override Min/Max and are unchanged in both trees). The pre-recorded G-PANEL-2=fail is unjustified: its own detail ('patched MpmathPrinter Min(x,y)->min(x, y) ... NumPy/SciPy ... genuinely unchanged') describes exactly what Req2.3/2.4 assert — it identifies no divergence between requirements and patched code. My probe reproduces that behavior and it matches the requirements. Verdict: FAITHFUL.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The requirements describe only behavior that is fully public in the problem_statement: rendering Min/Max as Python built-ins min()/max() and removing the 'Not supported in Python' fallback. Req 1/4 render 'min(x, y)'/'max(x, y)'; the x,y vs the statement's a,b differ but this is a trivial variable choice over behavior wholly disclosed publicly, not a test-derived leak. The gold edit (adding 'Min':'min','Max':'max' to _known_functions) is a mechanism the doc does NOT expose — it describes behavior, not the dict. Req 2's enumeration (Abs, sqrt, frac, Piecewise, integrals, NumPy/SciPy/mpmath printers, reserved words) names generic, well-known pycode capabilities for regression scope/localization; it correlates loosely with some PASS_TO_PASS test names but transmits no test file paths, function/class names, parametrization ids, assertion values, or quoted test/gold code, and omits the more specific beta/airy/fresnel cases (folded into generic 'special functions already handled'). No fix-invented identifiers (min/max are Python built-ins named in the statement). Legitimate module localization + behavioral translation, not test reconstruction.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
