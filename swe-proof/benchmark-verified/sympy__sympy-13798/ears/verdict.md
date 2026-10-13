# P2 adversarial audit — sympy__sympy-13798

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

Counterexample / evidence:

```
Wrong-fix candidate weak.diff (naive: on KeyError, use the custom mul_symbol verbatim for BOTH general AND numeric separators, omitting Req 2.1's spacing-command detection) is REJECTED by probe_3 and probe_6: under mul_symbol=r'\,' it renders Float(2.5e20) as '2.5\,10^{20}' instead of the required '2.5 \cdot 10^{20}'. This demonstrates the probe suite discriminates a plausibly-wrong reading of the requirements.
```

**Attacks re-run (6):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
# R1.1 + R1.3 (POSITIVE CONTROL): custom mul_symbol constructs without error
# and places the custom string verbatim between symbolic factors.
# 3 * x**2 * y with mul_symbol=r"\," -> "3\,x^{2}\,y"
from sympy import symbols
from sympy.printing.latex import latex
x, y = symbols('x y')
try:
    out = latex(3*x**2*y, mul_symbol=r"\,")
except Exception as e:
    print("construction FAILED:", repr(e))
    raise SystemExit(1)
print("observed:", repr(out))
expected = r"3\,x^{2}\,y"
if out == expected:
    print("HOLDS: custom separator placed verbatim")
    raise SystemExit(0)
print("expected:", repr(expected))
raise SystemExit(1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
# R1.2 + R1.4: a non-spacing custom string is used verbatim between general
# factors, no substitution/escaping. mul_symbol="*" -> "x*y" and "3*x^{2}*y".
from sympy import symbols
from sympy.printing.latex import latex
x, y = symbols('x y')
out1 = latex(x*y, mul_symbol="*")
out2 = latex(3*x**2*y, mul_symbol="*")
print("observed:", repr(out1), repr(out2))
ok = (out1 == "x*y") and (out2 == "3*x^{2}*y")
if ok:
    print("HOLDS: custom string used verbatim, no escaping")
    raise SystemExit(0)
raise SystemExit(1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
# R2.1 + R2.3: for a spacing-command custom mul_symbol (thin space "\,"), the
# NUMERIC separator falls back to " \cdot " while general separator stays "\,".
# Float 2.5e20 -> "2.5 \cdot 10^{20}"; but general factors still use "\,".
from sympy import symbols, Float
from sympy.printing.latex import latex
x, y = symbols('x y')
fl = latex(Float("2.5e20"), mul_symbol=r"\,")
gen = latex(3*x**2*y, mul_symbol=r"\,")
print("float:", repr(fl), "general:", repr(gen))
ok = (fl == r"2.5 \cdot 10^{20}") and (gen == r"3\,x^{2}\,y")
if ok:
    print("HOLDS: numeric uses \\cdot, general uses custom for spacing command")
    raise SystemExit(0)
raise SystemExit(1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
# R2.2 + R2.3: for a non-spacing custom mul_symbol ("*"), the numeric separator
# is that same custom string verbatim. Float 2.5e20 -> "2.5*10^{20}".
from sympy import Float
from sympy.printing.latex import latex
fl = latex(Float("2.5e20"), mul_symbol="*")
print("float:", repr(fl))
if fl == "2.5*10^{20}":
    print("HOLDS: numeric separator is custom string verbatim")
    raise SystemExit(0)
raise SystemExit(1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
# R3.1-3.4: the four built-in selectors (and default) keep exact behavior for
# BOTH the general-factor separator and the numeric separator.
from sympy import symbols, Float
from sympy.printing.latex import latex
x, y = symbols('x y')
fl = Float("2.5e20")
cases = {
    "default_gen":  (latex(x*y),                    "x y"),
    "default_num":  (latex(fl),                     r"2.5 \cdot 10^{20}"),
    "none_gen":     (latex(x*y, mul_symbol=None),   "x y"),
    "none_num":     (latex(fl, mul_symbol=None),    r"2.5 \cdot 10^{20}"),
    "dot_gen":      (latex(x*y, mul_symbol="dot"),  r"x \cdot y"),
    "dot_num":      (latex(fl, mul_symbol="dot"),   r"2.5 \cdot 10^{20}"),
    "times_gen":    (latex(x*y, mul_symbol="times"),r"x \times y"),
    "times_num":    (latex(fl, mul_symbol="times"), r"2.5 \times 10^{20}"),
    "ldot_gen":     (latex(x*y, mul_symbol="ldot"), r"x \,.\, y"),
    "ldot_num":     (latex(fl, mul_symbol="ldot"),  r"2.5 \,.\, 10^{20}"),
}
bad = []
for k, (got, exp) in cases.items():
    print(k, "got", repr(got), "exp", repr(exp))
    if got != exp:
        bad.append(k)
if not bad:
    print("HOLDS: all four selectors + default unchanged")
    raise SystemExit(0)
print("MISMATCH:", bad)
raise SystemExit(1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
# R2.4 + R2.1: numeric-separator decision depends only on the STRIPPED form.
# A custom "  \,  " (thin space padded with whitespace) must still trigger the
# \cdot numeric fallback (stripped -> "\,"), and general separator is verbatim.
from sympy import symbols, Float
from sympy.printing.latex import latex
x, y = symbols('x y')
padded = r"  \,  "
fl = latex(Float("2.5e20"), mul_symbol=padded)
gen = latex(x*y, mul_symbol=padded)
print("float:", repr(fl), "general:", repr(gen))
ok = (fl == r"2.5 \cdot 10^{20}") and (gen == "x" + padded + "y")
if ok:
    print("HOLDS: numeric fallback keys off stripped form; general verbatim")
    raise SystemExit(0)
raise SystemExit(1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
# R1.1 + R1.3 (POSITIVE CONTROL): custom mul_symbol constructs without error
# and places the custom string verbatim between symbolic factors.
# 3 * x**2 * y with mul_symbol=r"\," -> "3\,x^{2}\,y"
from sympy import symbols
from sympy.printing.latex import latex
x, y = symbols('x y')
try:
    out = latex(3*x**2*y, mul_symbol=r"\,")
except Exception as e:
    print("construction FAILED:", repr(e))
    raise SystemExit(1)
print("observed:", repr(out))
expected = r"3\,x^{2}\,y"
if out == expected:
    print("HOLDS: custom separator placed verbatim")
    raise SystemExit(0)
print("expected:", repr(expected))
raise SystemExit(1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance: allow arbitrary mul_symbol in sympy LaTeX printer (LatexPrinter.__init__). 6 distinct probes cover all requirements.

Probes (criterion -> result on base / gold-patched / weak-candidate):
- probe_1 (R1.1+R1.3, POSITIVE CONTROL): custom mul_symbol=r'\,' constructs w/o error and yields '3\,x^{2}\,y'. base=FAIL / patched=HOLD / weak=HOLD. DISCRIMINATES (fails base, holds patched).
- probe_2 (R1.2+R1.4): non-spacing custom '*' used verbatim between general factors -> 'x*y','3*x^{2}*y'. base=FAIL / patched=HOLD / weak=HOLD.
- probe_3 (R2.1+R2.3): spacing command '\,' -> numeric separator falls back to ' \cdot ' while general stays custom -> Float='2.5 \cdot 10^{20}', general='3\,x^{2}\,y'. base=FAIL / patched=HOLD / weak=REJECT.
- probe_4 (R2.2+R2.3): non-spacing '*' -> numeric separator is custom verbatim -> Float='2.5*10^{20}'. base=FAIL / patched=HOLD / weak=HOLD.
- probe_5 (R3.1-3.4 regression 'SHALL keep'): default/None/dot/times/ldot exact general+numeric outputs unchanged. base=HOLD / patched=HOLD / weak=HOLD (regression correctly holds on all trees).
- probe_6 (R2.4+R2.1): numeric fallback keys off STRIPPED form -> '  \,  ' still triggers \cdot numeric while general keeps padded verbatim. base=FAIL / patched=HOLD / weak=REJECT.

All runs completed in the official Docker image via nl_attack. >=5 probes hold patched, positive control discriminates (prepatch_reproduced=true), and a requirements-plausible wrong fix is rejected by 2 probes. Verified against sympy printing/latex.py behavior directly (explore.py dump matched every expected string).

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 6 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 6 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

Counterexample / evidence:

```
Wrong-fix candidate weak.diff (naive: on KeyError, use the custom mul_symbol verbatim for BOTH general AND numeric separators, omitting Req 2.1's spacing-command detection) is REJECTED by probe_3 and probe_6: under mul_symbol=r'\,' it renders Float(2.5e20) as '2.5\,10^{20}' instead of the required '2.5 \cdot 10^{20}'. This demonstrates the probe suite discriminates a plausibly-wrong reading of the requirements.
```

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
# R1.1 + R1.3 (POSITIVE CONTROL): custom mul_symbol constructs without error
# and places the custom string verbatim between symbolic factors.
# 3 * x**2 * y with mul_symbol=r"\," -> "3\,x^{2}\,y"
from sympy import symbols
from sympy.printing.latex import latex
x, y = symbols('x y')
try:
    out = latex(3*x**2*y, mul_symbol=r"\,")
except Exception as e:
    print("construction FAILED:", repr(e))
    raise SystemExit(1)
print("observed:", repr(out))
expected = r"3\,x^{2}\,y"
if out == expected:
    print("HOLDS: custom separator placed verbatim")
    raise SystemExit(0)
print("expected:", repr(expected))
raise SystemExit(1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance: allow arbitrary mul_symbol in sympy LaTeX printer (LatexPrinter.__init__). 6 distinct probes cover all requirements.

Probes (criterion -> result on base / gold-patched / weak-candidate):
- probe_1 (R1.1+R1.3, POSITIVE CONTROL): custom mul_symbol=r'\,' constructs w/o error and yields '3\,x^{2}\,y'. base=FAIL / patched=HOLD / weak=HOLD. DISCRIMINATES (fails base, holds patched).
- probe_2 (R1.2+R1.4): non-spacing custom '*' used verbatim between general factors -> 'x*y','3*x^{2}*y'. base=FAIL / patched=HOLD / weak=HOLD.
- probe_3 (R2.1+R2.3): spacing command '\,' -> numeric separator falls back to ' \cdot ' while general stays custom -> Float='2.5 \cdot 10^{20}', general='3\,x^{2}\,y'. base=FAIL / patched=HOLD / weak=REJECT.
- probe_4 (R2.2+R2.3): non-spacing '*' -> numeric separator is custom verbatim -> Float='2.5*10^{20}'. base=FAIL / patched=HOLD / weak=HOLD.
- probe_5 (R3.1-3.4 regression 'SHALL keep'): default/None/dot/times/ldot exact general+numeric outputs unchanged. base=HOLD / patched=HOLD / weak=HOLD (regression correctly holds on all trees).
- probe_6 (R2.4+R2.1): numeric fallback keys off STRIPPED form -> '  \,  ' still triggers \cdot numeric while general keeps padded verbatim. base=FAIL / patched=HOLD / weak=REJECT.

All runs completed in the official Docker image via nl_attack. >=5 probes hold patched, positive control discriminates (prepatch_reproduced=true), and a requirements-plausible wrong fix is rejected by 2 probes. Verified against sympy printing/latex.py behavior directly (explore.py dump matched every expected string).

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** The patch adds try/except KeyError fallbacks in LatexPrinter.__init__ for both mul_symbol_latex (general) and mul_symbol_latex_numbers (numeric). Requirements pin the changed observable behavior at the correct boundary (init translation observed via _print_Mul/_print_Float), covering the custom-string case, the spacing-command numeric fallback, and full regression of the four selectors. The requirement's spacing-command enumeration matches the patch's literal list; the stripped-comparison detail (R2.4) matches `self._settings['mul_symbol'].strip() in [...]`.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The requirements localize the change (LatexPrinter.__init__, mul_symbol_latex / mul_symbol_latex_numbers, _print_Mul/_print_Float/_print_PolyElement) — legitimate localization, and these symbols appear in the public gold context anyway. The worked example `3\,x^{2}\,y` for input `mul_symbol=r'\,'` on `3*x**2*y` comes straight from the PUBLIC problem_statement, which already uses exactly `latex(3*x**2*y)` and the thin space `\,`; the no-extra-space output is the natural behavioral consequence, not test-derived content. Crucially, Requirement 2 (numeric separator) describes the rule BEHAVIORALLY ('a LaTeX horizontal-spacing command that inserts blank space without rendering a visible glyph') and does NOT enumerate the gold patch's fix-invented magic list ['', ' ', '\\', '\\,', '\\:', '\\;', '\\quad'] — no leak of that enumeration or its specific tokens beyond the public \, example. The second hidden test assertion (1.5*3**x -> '1.5 \cdot 3^{x}') is not quoted; the doc's numeric example (2.5 \cdot 10^{20}) differs. No test names/paths/ids (test_latex_basic, test_latex.py), no quoted test code, no parametrization mirroring. This is translation of behavior into EARS, which is the intended purpose.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
