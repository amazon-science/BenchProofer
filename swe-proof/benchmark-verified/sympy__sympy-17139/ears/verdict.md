# P2 adversarial audit — sympy__sympy-17139

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 6 requirement probes hold on the patched tree; 1/2 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 6 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 6 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 2 alternative candidate patches, claimed to satisfy every cited requirement, and ran the same suite against them. The suite rejected 1 of the 2: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. The other 1 was not rejected by the suite. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (6):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
# Req 1.6 (positive control): simplify(cos(x)**I) completes and returns expr equal to input power.
from sympy import symbols, cos, I, simplify
x = symbols('x')
try:
    r = simplify(cos(x)**I)
except Exception as e:
    print("FAIL: simplify raised", type(e).__name__, e)
    raise SystemExit(1)
print("simplify(cos(x)**I) =", r)
ok = (r == cos(x)**I)
print("equal to input power:", ok)
raise SystemExit(0 if ok else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
# Req 1.3 / 1.5: TR6 and TR5 on purely imaginary exponent I return the power unchanged, no error.
from sympy import symbols, cos, sin, I
from sympy.simplify.fu import TR5, TR6
x = symbols('x')
r6 = TR6(cos(x)**I)
r5 = TR5(sin(x)**I)
print("TR6(cos(x)**I) =", r6)
print("TR5(sin(x)**I) =", r5)
ok = (r6 == cos(x)**I) and (r5 == sin(x)**I)
print("both unchanged:", ok)
raise SystemExit(0 if ok else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
# Req 1.4: complex exponent with nonzero imaginary part (and nonzero real part) returned unchanged.
from sympy import symbols, cos, sin, I
from sympy.simplify.fu import TR5, TR6
x = symbols('x')
e = 2 + 3*I
r6 = TR6(cos(x)**e)
r5 = TR5(sin(x)**e)
r6b = TR6(cos(x)**(4*I))
print("TR6(cos(x)**(2+3I)) =", r6)
print("TR5(sin(x)**(2+3I)) =", r5)
print("TR6(cos(x)**(4I)) =", r6b)
ok = (r6 == cos(x)**e) and (r5 == sin(x)**e) and (r6b == cos(x)**(4*I))
print("all unchanged:", ok)
raise SystemExit(0 if ok else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
# Req 1.1/1.2: _TR56 directly leaves matching power with non-real exponent unchanged, no order comparison / TypeError.
import importlib
from sympy import symbols, cos, I
fumod = importlib.import_module("sympy.simplify.fu")
x = symbols('x')
# Emulate TR6 call: f=cos, g=cos, h=lambda z:1-z, max=4, pow=False
out = fumod._TR56(cos(x)**I, cos, lambda a: cos(a), lambda z: 1 - z, 4, False)
print("_TR56(cos(x)**I) =", out)
ok = (out == cos(x)**I)
out2 = fumod._TR56(cos(x)**(1+I), cos, lambda a: cos(a), lambda z: 1 - z, 4, False)
print("_TR56(cos(x)**(1+I)) =", out2)
ok = ok and (out2 == cos(x)**(1+I))
print("unchanged & no error:", ok)
raise SystemExit(0 if ok else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
# Req 2.1: real exponent 2 triggers squared-form rewrite (unchanged behavior).
from sympy import symbols, cos, sin
from sympy.simplify.fu import TR5, TR6
x = symbols('x')
r6 = TR6(cos(x)**2)
r5 = TR5(sin(x)**2)
print("TR6(cos(x)**2) =", r6)
print("TR5(sin(x)**2) =", r5)
ok = (r6 == 1 - sin(x)**2) and (r5 == 1 - cos(x)**2)
print("rewrites correct:", ok)
raise SystemExit(0 if ok else 1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
# Req 2.2: higher real even power rewritten as before; Req 2.3: negative real exponent unchanged.
from sympy import symbols, cos, sin
from sympy.simplify.fu import TR6
x = symbols('x')
r4 = TR6(cos(x)**4)
rneg = TR6(cos(x)**-2)
rodd = TR6(cos(x)**3)   # odd, not pow -> unchanged
print("TR6(cos(x)**4) =", r4)
print("TR6(cos(x)**-2) =", rneg)
print("TR6(cos(x)**3) =", rodd)
ok = (r4 == (1 - sin(x)**2)**2) and (rneg == cos(x)**-2) and (rodd == cos(x)**3)
print("all correct:", ok)
raise SystemExit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
# Req 1.6 (positive control): simplify(cos(x)**I) completes and returns expr equal to input power.
from sympy import symbols, cos, I, simplify
x = symbols('x')
try:
    r = simplify(cos(x)**I)
except Exception as e:
    print("FAIL: simplify raised", type(e).__name__, e)
    raise SystemExit(1)
print("simplify(cos(x)**I) =", r)
ok = (r == cos(x)**I)
print("equal to input power:", ok)
raise SystemExit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Gold patch adds `if not rv.exp.is_real: return rv` before the order comparisons in _TR56 (sympy/simplify/fu.py). Confirmed exact patched source via dump probe.

Probes (each standalone python, stdlib+sympy only):
- probe_1 (Req 1.6, POSITIVE CONTROL): simplify(cos(x)**I) completes and returns cos(x)**I. PATCHED: HOLDS. BASE: FAILS with `TypeError: Invalid comparison of complex I`. Discriminates.
- probe_2 (Req 1.3/1.5): TR6(cos(x)**I)==cos(x)**I and TR5(sin(x)**I)==sin(x)**I. PATCHED HOLDS; BASE FAILS (TypeError in _TR56).
- probe_3 (Req 1.4): complex exp with nonzero imag+real part (2+3I) and pure-imag 4*I returned unchanged by TR5/TR6. PATCHED HOLDS; BASE FAILS.
- probe_4 (Req 1.1/1.2): direct _TR56(cos(x)**I,...) and _TR56(cos(x)**(1+I),...) return power unchanged with no order comparison / TypeError. PATCHED HOLDS; BASE FAILS.
- probe_5 (Req 2.1 regression): TR6(cos(x)**2)==1-sin(x)**2, TR5(sin(x)**2)==1-cos(x)**2. HOLDS.
- probe_6 (Req 2.2/2.3 regression): TR6(cos(x)**4)==(1-sin(x)**2)**2; TR6(cos(x)**-2) and TR6(cos(x)**3) unchanged. HOLDS.

All 6 HOLD on the gold-patched tree; positive controls (1-4) all FAIL at base with the mandated TypeError, so prepatch reproduced.

Candidate patches (both apply at base_commit):
- weak_imag.diff: guards only `rv.exp.is_imaginary` (a narrow reading of Req 1 that treats 'non-real' as 'purely imaginary'). This VIOLATES Req 1.4 for exponents like 2+3I / 1+I where is_imaginary is False. REJECTED by probe_3 and probe_4 (still crashes with TypeError). Demonstrates the suite discriminates a wrong/partial fix.
- weak_try.diff: wraps the order comparisons in try/except TypeError. Passes ALL probes -- this is a genuinely-correct alternative fix (same observable behavior, would also resolve the hidden tests), NOT a too-weak finding.

No requirements-conforming patch was found that fails the hidden tests; no probe fails on the patched tree; positive control discriminates. Verdict SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 requirement probes hold on the patched tree; 1/2 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 6 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 6 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 2 alternative candidate patches, claimed to satisfy every cited requirement, and ran the same suite against them. The suite rejected 1 of the 2: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. The other 1 was not rejected by the suite. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

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
# Req 1.6 (positive control): simplify(cos(x)**I) completes and returns expr equal to input power.
from sympy import symbols, cos, I, simplify
x = symbols('x')
try:
    r = simplify(cos(x)**I)
except Exception as e:
    print("FAIL: simplify raised", type(e).__name__, e)
    raise SystemExit(1)
print("simplify(cos(x)**I) =", r)
ok = (r == cos(x)**I)
print("equal to input power:", ok)
raise SystemExit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Gold patch adds `if not rv.exp.is_real: return rv` before the order comparisons in _TR56 (sympy/simplify/fu.py). Confirmed exact patched source via dump probe.

Probes (each standalone python, stdlib+sympy only):
- probe_1 (Req 1.6, POSITIVE CONTROL): simplify(cos(x)**I) completes and returns cos(x)**I. PATCHED: HOLDS. BASE: FAILS with `TypeError: Invalid comparison of complex I`. Discriminates.
- probe_2 (Req 1.3/1.5): TR6(cos(x)**I)==cos(x)**I and TR5(sin(x)**I)==sin(x)**I. PATCHED HOLDS; BASE FAILS (TypeError in _TR56).
- probe_3 (Req 1.4): complex exp with nonzero imag+real part (2+3I) and pure-imag 4*I returned unchanged by TR5/TR6. PATCHED HOLDS; BASE FAILS.
- probe_4 (Req 1.1/1.2): direct _TR56(cos(x)**I,...) and _TR56(cos(x)**(1+I),...) return power unchanged with no order comparison / TypeError. PATCHED HOLDS; BASE FAILS.
- probe_5 (Req 2.1 regression): TR6(cos(x)**2)==1-sin(x)**2, TR5(sin(x)**2)==1-cos(x)**2. HOLDS.
- probe_6 (Req 2.2/2.3 regression): TR6(cos(x)**4)==(1-sin(x)**2)**2; TR6(cos(x)**-2) and TR6(cos(x)**3) unchanged. HOLDS.

All 6 HOLD on the gold-patched tree; positive controls (1-4) all FAIL at base with the mandated TypeError, so prepatch reproduced.

Candidate patches (both apply at base_commit):
- weak_imag.diff: guards only `rv.exp.is_imaginary` (a narrow reading of Req 1 that treats 'non-real' as 'purely imaginary'). This VIOLATES Req 1.4 for exponents like 2+3I / 1+I where is_imaginary is False. REJECTED by probe_3 and probe_4 (still crashes with TypeError). Demonstrates the suite discriminates a wrong/partial fix.
- weak_try.diff: wraps the order comparisons in try/except TypeError. Passes ALL probes -- this is a genuinely-correct alternative fix (same observable behavior, would also resolve the hidden tests), NOT a too-weak finding.

No requirements-conforming patch was found that fails the hidden tests; no probe fails on the patched tree; positive control discriminates. Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Probed the gold-patched tree in the instance image: simplify(cos(x)**I) -> cos(x)**I (Req 1.6, returns equal, no crash); TR6(cos(x)**I) -> cos(x)**I and TR5(sin(x)**I) -> sin(x)**I (Reqs 1.1/1.3/1.5); TR6(cos(x)**(2+I)) -> cos(x)**(2+I) unchanged (Req 1.4, non-zero imaginary with real part); real exponents preserved: TR6(cos(x)**2) -> 1 - sin(x)**2, TR5(sin(x)**2) -> 1 - cos(x)**2 (Req 2.1), TR6(cos(x)**-2) -> cos(x)**(-2) (Req 2.3 negative). Base commit crashes with `TypeError: Invalid comparison of complex I` at `if (rv.exp < 0) == True`, confirming the guard's purpose (Req 1.2). The modeling boundary is correct: requirements pin the changed observable behavior (guard non-real exp in _TR56) and its propagation through TR5/TR6/simplify, matching the one-line real-exponent guard exactly.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The public problem_statement already contains the full traceback, which discloses all sensitive-looking names: sympy/simplify/fu.py, _TR56, TR5/TR6, the crashing comparison `if (rv.exp < 0) == True:`, the TR6 call signature (max=max, pow=pow), the example simplify(cos(x)**I), and the TypeError message. So module/function localization and the crash mechanism are all public.

Hidden material: gold fix is `if not rv.exp.is_real: return rv`; tests assert sin(x)**I, sin(x)**(2*I+1), cos(x)**I, cos(x)**(2+3*I) unchanged (test__TR56, test_issue_17137 in test_fu.py / test_simplify.py).

The requirements translate this into behavior without transmitting the tests: (a) no test file paths, test/function names (test__TR56, test_issue_17137), or the T(...) helper are named; (b) no verbatim test literals (2*I+1, 2+3*I, max=4) or gold code are quoted; (c) `is_real` is a stock sympy attribute, not a fix-invented identifier, and the doc never even names it — it says 'non-real (complex) exponent'. Req 1.3/1.4 split 'purely imaginary (e.g. I)' vs 'complex with non-zero imaginary part' — this is an exhaustive behavioral partition of the non-real domain, not a mirror of parametrized case ids; it is the legitimate behavior-translation the spec is meant to do. Requirement 2 describes pre-existing real-exponent _TR56 behavior for the preservation contract, again without quoting the P2P assertions. Nothing reconstructs the hidden tests beyond the public problem_statement.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
