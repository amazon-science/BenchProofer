# P2 adversarial audit — sympy__sympy-14976

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
# Req 1.1/1.3: MpmathPrinter prints Rational(232,3) as mpmath.mpf(232)/mpmath.mpf(3)
import sys
from sympy import Rational
from sympy.printing.pycode import MpmathPrinter
p = MpmathPrinter()
out = p.doprint(Rational(232, 3))
print("output:", repr(out))
expected = "mpmath.mpf(232)/mpmath.mpf(3)"
if out == expected:
    sys.exit(0)
print("expected:", expected)
sys.exit(1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
# Req 1.1/1.2/1.6: general rational -> two separate mpf(...) wraps joined by single '/'
import sys, re
from sympy import Rational
from sympy.printing.pycode import MpmathPrinter
p = MpmathPrinter()
ok = True
for num, den in [(1, 7), (22, 7), (5, 13)]:
    out = p.doprint(Rational(num, den))
    print("Rational(%d,%d) ->" % (num, den), repr(out))
    exp = "mpmath.mpf(%d)/mpmath.mpf(%d)" % (num, den)
    if out != exp:
        print("  MISMATCH expected", exp); ok = False
    # must not be the bare quotient
    if out == "%d/%d" % (num, den):
        print("  bare quotient!"); ok = False
    # exactly two mpf( constructor calls, one slash
    if out.count("mpmath.mpf(") != 2 or out.count("/") != 1:
        print("  structure wrong"); ok = False
sys.exit(0 if ok else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
# Req 1.4: negative numerator carries leading minus exactly like str(int)
import sys
from sympy import Rational
from sympy.printing.pycode import MpmathPrinter
p = MpmathPrinter()
out = p.doprint(Rational(-232, 3))
print("Rational(-232,3) ->", repr(out))
exp = "mpmath.mpf(-232)/mpmath.mpf(3)"
ok = (out == exp)
if not ok:
    print("expected", exp)
sys.exit(0 if ok else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
# Req 4.1/4.2: nsolve on equation with a rational constant returns full precision.
# The reported issue: nsolve(x**2 - Rational(232,3)? ) -- use the canonical issue form.
import sys
import mpmath
from sympy import symbols, nsolve, Rational, sqrt
x = symbols('x')
prec = 64
# linear eq: x + 232/3 = 0 -> x = -232/3, non-terminating rational
root = nsolve(x + Rational(232, 3), x, 0, prec=prec)
print("root:", root)
mpmath.mp.dps = prec + 5
expected = mpmath.mpf(-232) / mpmath.mpf(3)
diff = abs(mpmath.mpf(str(root)) - expected)
print("expected:", expected)
print("diff:", diff)
# accurate well beyond native double (~1e-16). require < 1e-30
if diff < mpmath.mpf(10) ** (-30):
    sys.exit(0)
print("NOT full precision")
sys.exit(1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
# Req 2 & 3: additive change. Float still wrapped as mpf; special-cases intact;
# and PythonCodePrinter / NumPy printer render rationals unchanged (no mpmath leak).
import sys
from sympy import Rational, Float, symbols
from sympy.printing.pycode import MpmathPrinter, PythonCodePrinter, NumPyPrinter
x = symbols('x')
ok = True

# Float via mpmath still wrapped in mpmath.mpf(...)
mp = MpmathPrinter()
f_out = mp.doprint(Float(1.0))
print("mpmath Float(1.0) ->", repr(f_out))
if "mpmath.mpf(" not in f_out:
    print("  Float no longer mpf-wrapped"); ok = False

# plain python printer: rational stays plain division, no mpmath leak
pp = PythonCodePrinter()
pr = pp.doprint(Rational(232, 3))
print("PythonCodePrinter Rational(232,3) ->", repr(pr))
if "mpmath" in pr:
    print("  mpmath leaked into python printer"); ok = False
if pr != "232/3":
    print("  python rational changed from 232/3"); ok = False

# numpy printer: no mpmath leak
npp = NumPyPrinter()
nr = npp.doprint(Rational(232, 3))
print("NumPyPrinter Rational(232,3) ->", repr(nr))
if "mpmath" in nr:
    print("  mpmath leaked into numpy printer"); ok = False

sys.exit(0 if ok else 1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
# Req 1.5 & 2.3: mpf name via module resolution; special-cases (uppergamma etc) intact.
import sys
from sympy import Rational, symbols, uppergamma, log
from sympy.printing.pycode import MpmathPrinter
x = symbols('x')
ok = True
mp = MpmathPrinter()

# module-qualified name (fully_qualified default) -> "mpmath.mpf" not bare "mpf"
out = mp.doprint(Rational(5, 2))
print("Rational(5,2) ->", repr(out))
if "mpmath.mpf(" not in out:
    print("  not module-qualified"); ok = False

# uppergamma special case still uses gammainc
ug = mp.doprint(uppergamma(x, x))
print("uppergamma ->", repr(ug))
if "gammainc" not in ug:
    print("  uppergamma special-case broken"); ok = False

sys.exit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
# Req 1.1/1.3: MpmathPrinter prints Rational(232,3) as mpmath.mpf(232)/mpmath.mpf(3)
import sys
from sympy import Rational
from sympy.printing.pycode import MpmathPrinter
p = MpmathPrinter()
out = p.doprint(Rational(232, 3))
print("output:", repr(out))
expected = "mpmath.mpf(232)/mpmath.mpf(3)"
if out == expected:
    sys.exit(0)
print("expected:", expected)
sys.exit(1)
```

Prepatch bug re-encoded as an attack: `True`.

6 probes cover Req1 (1.1/1.3 exact string mpmath.mpf(232)/mpmath.mpf(3) [probe_1]; 1.1/1.2/1.6 two mpf wraps + single slash, not bare quotient [probe_2]; 1.4 negative numerator leading minus [probe_3]; 1.5 module-qualified name [probe_6]), Req4 (nsolve full precision to 64 digits on x+232/3 [probe_4], diff 3e-63 patched vs 4.7e-15 base), Req2/3 regression-keep (Float still mpf-wrapped, PythonCodePrinter/NumPyPrinter rationals stay '232/3' with no mpmath leak [probe_5], uppergamma gammainc special-case intact [probe_6]). All 6 HOLD on gold-patched tree. Positive controls probe_1 and probe_4 both FAIL at base (232/3 unwrapped; nsolve only ~15 digits) -> discriminating power confirmed. Wrong-fix candidate weak.diff renders mpmath.mpf(p/q) (division in native Python BEFORE wrapping): REJECTED by probes 1,2,3 (wrong string) and 4 (still loses precision, diff 4.7e-15) -> suite discriminates the lazy fix a weak reading permits. No requirement-conforming alternative found.

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
# Req 1.1/1.3: MpmathPrinter prints Rational(232,3) as mpmath.mpf(232)/mpmath.mpf(3)
import sys
from sympy import Rational
from sympy.printing.pycode import MpmathPrinter
p = MpmathPrinter()
out = p.doprint(Rational(232, 3))
print("output:", repr(out))
expected = "mpmath.mpf(232)/mpmath.mpf(3)"
if out == expected:
    sys.exit(0)
print("expected:", expected)
sys.exit(1)
```

Prepatch bug re-encoded as an attack: `True`.

6 probes cover Req1 (1.1/1.3 exact string mpmath.mpf(232)/mpmath.mpf(3) [probe_1]; 1.1/1.2/1.6 two mpf wraps + single slash, not bare quotient [probe_2]; 1.4 negative numerator leading minus [probe_3]; 1.5 module-qualified name [probe_6]), Req4 (nsolve full precision to 64 digits on x+232/3 [probe_4], diff 3e-63 patched vs 4.7e-15 base), Req2/3 regression-keep (Float still mpf-wrapped, PythonCodePrinter/NumPyPrinter rationals stay '232/3' with no mpmath leak [probe_5], uppergamma gammainc special-case intact [probe_6]). All 6 HOLD on gold-patched tree. Positive controls probe_1 and probe_4 both FAIL at base (232/3 unwrapped; nsolve only ~15 digits) -> discriminating power confirmed. Wrong-fix candidate weak.diff renders mpmath.mpf(p/q) (division in native Python BEFORE wrapping): REJECTED by probes 1,2,3 (wrong string) and 4 (still loses precision, diff 4.7e-15) -> suite discriminates the lazy fix a weak reading permits. No requirement-conforming alternative found.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Requirements pin the actual changed observable behavior (MpmathPrinter's Rational rendering) biconditionally with a correct boundary. No mandated-but-absent, forbidden-but-present, or invented behavior. The G-PANEL-3 leakage stamp about singling out sign(x) is a provenance/leakage concern, not a faithfulness break: the assertion R2.1 makes about sign(x)->'mpmath.sign(x)' is true of the patched code (verified by probe).


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The requirements describe behavior derivable from the public problem_statement and legitimate localization. (1) The `232/3` rational and the output form `mpmath.mpf(232)/mpmath.mpf(3)` (Req 1.3) come directly from the public problem_statement — describing required output IS the behavioral spec. (2) The hidden unit test's specific values (`Rational(1,2) -> mpmath.mpf(1)/mpmath.mpf(2)`) are NOT reproduced. (3) The gold's fix-invented `_print_Rational` is never named; behavior is described instead. Listed methods (`_print_Float`, `_print_uppergamma`, `_print_lowergamma`, `_print_log2`, `_print_log1p`) are pre-existing public members of pycode.py — legitimate localization. (4) The hidden nsolve test's `Rational(1,3)`/`prec=100` are not leaked; Req 4.2 speaks generically of a non-terminating rational and precision beyond double. (5) Req 3's enumeration (reserved words, print-method dispatch, codegen AST nodes, NumPy/SciPy printers) maps to real public features of pycode.py that an additive/no-regress spec would naturally cite, not to test names/paths/ids. No test code, paths, function names, or parametrization ids are transmitted.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
