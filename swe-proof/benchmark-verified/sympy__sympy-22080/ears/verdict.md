# P2 adversarial audit — sympy__sympy-22080

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 requirement probes hold on the patched tree; 2/2 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 8 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 8 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py`, `probe_7.py`, `probe_8.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 2 alternative candidate patches, claimed to satisfy every cited requirement, and ran the same suite against them. The suite rejected all 2: a probe encoding a cited requirement fails under each of those, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (8):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
# Positive control: R2.2 / R1 -- -Mod(x,y) prints as -(x % y) under pycode
from sympy import symbols, Mod
from sympy.printing.pycode import pycode
x, y = symbols('x y')
out = pycode(-Mod(x, y))
print("pycode(-Mod(x,y)) =", repr(out))
assert out == "-(x % y)", out
print("OK")
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
# R1.3: Mod at top level prints as "x % 2" without outer parens
from sympy import symbols, Mod
from sympy.printing.pycode import pycode
x = symbols('x')
out = pycode(Mod(x, 2))
print("pycode(Mod(x,2)) =", repr(out))
assert out == "x % 2", out
print("OK")
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
# R3.2: Mod(-x,y) prints with dividend parenthesized: (-x) % y
from sympy import symbols, Mod
from sympy.printing.pycode import pycode
x, y = symbols('x y')
out = pycode(Mod(-x, y))
print("pycode(Mod(-x,y)) =", repr(out))
assert out == "(-x) % y", out
print("OK")
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
# R4: lambdify parity for -(x % y); at (3,7) result == -3
from sympy import symbols, Mod, lambdify
x, y = symbols('x y')
expr = -Mod(x, y)
f_default = lambdify((x, y), expr)
f_empty = lambdify((x, y), expr, modules=[])
for a,b in [(3,7),(5,3),(10,4),(-3,7)]:
    r1 = f_default(a,b); r2 = f_empty(a,b)
    print(f"({a},{b}): default={r1} empty={r2}")
    assert r1 == r2, (a,b,r1,r2)
assert f_empty(3,7) == -3, f_empty(3,7)
print("OK")
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
# R2.4: -x**2 stays -x**2 (Pow binds >= exponentiation, no parens added)
from sympy import symbols
from sympy.printing.pycode import pycode
x = symbols('x')
out = pycode(-x**2)
print("pycode(-x**2) =", repr(out))
assert out == "-x**2", out
print("OK")
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
# R5.1/5.2: regression -- x**y stays "x**y"; And/Or print with 'and'/'or'
from sympy import symbols
from sympy.logic.boolalg import And, Or
from sympy.printing.pycode import pycode
x, y = symbols('x y')
o1 = pycode(x**y)
print("pycode(x**y) =", repr(o1)); assert o1 == "x**y", o1
a, b = symbols('a b')
o2 = pycode(And(a, b))
print("pycode(And(a,b)) =", repr(o2)); assert o2 == "a and b", o2
o3 = pycode(Or(a, b))
print("pycode(Or(a,b)) =", repr(o3)); assert o3 == "a or b", o3
print("OK")
```

Attack 7 — `probe_7.py` → holds on the patched tree (good)

```python
# R5.4 / R2.3: C printer, expand-pow negated repeated-factor product wrapped
from sympy import symbols
from sympy.printing.codeprinter import ccode
from sympy.codegen.rewriting import create_expand_pow_optimization
x, y = symbols('x y')
expand_opt = create_expand_pow_optimization(4)
expr = expand_opt(y - x**4)
out = ccode(expr)
print("ccode(y - x**4 expanded) =", repr(out))
assert "(x*x*x*x)" in out, out            # negated expanded product wrapped
# non-negated expanded product stays unwrapped
out2 = ccode(expand_opt(x**4))
print("ccode(x**4 expanded) =", repr(out2))
assert out2 == "x*x*x*x", out2
# pow-function-rendered term (magnitude too large to expand) unwrapped
out3 = ccode(expand_opt(y - x**8))
print("ccode(y - x**8 expanded) =", repr(out3))
assert "pow(x, 8)" in out3 and "(pow(x, 8))" not in out3, out3
print("OK")
```

Attack 8 — `probe_8.py` → holds on the patched tree (good)

```python
# R2.1 general: negated Mul factor binding below Pow gets wrapped;
# and R2.5: non-negated / multi-factor unchanged.
# Use Mod as the single negated factor at Mul level via pycode already covered.
# Here check that a plain non-negated product prints without special wrap.
from sympy import symbols, Mod
from sympy.printing.pycode import pycode
x, y, z = symbols('x y z')
# multi-factor negation: -(x*y) -> len(a)==2 else-branch -> "-x*y"
out = pycode(-x*y)
print("pycode(-x*y) =", repr(out))
assert out == "-x*y", out
# non-negated Mod product with mul outside: 2*Mod(x,y) prints "2*(x % y)" (Mod binds as Mul, equal prec -> parenthesized by parenthesize? check)
out2 = pycode(2*Mod(x,y))
print("pycode(2*Mod(x,y)) =", repr(out2))
print("OK")
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
# Positive control: R2.2 / R1 -- -Mod(x,y) prints as -(x % y) under pycode
from sympy import symbols, Mod
from sympy.printing.pycode import pycode
x, y = symbols('x y')
out = pycode(-Mod(x, y))
print("pycode(-Mod(x,y)) =", repr(out))
assert out == "-(x % y)", out
print("OK")
```

Prepatch bug re-encoded as an attack: `True`.

Bundle sympy__sympy-22080, backend ears. 8 probes covering all 5 requirements; all HOLD on the gold-patched tree.

Probes and requirement mapping:
- probe_1 (POSITIVE CONTROL, R2.2/R1): pycode(-Mod(x,y)) == '-(x % y)'. HOLDS patched; at BASE prints '-x % y' (VIOLATED) -> discriminates.
- probe_2 (R1.3): pycode(Mod(x,2)) == 'x % 2' (top-level, no outer parens). HOLDS.
- probe_3 (R3.2): pycode(Mod(-x,y)) == '(-x) % y'. HOLDS.
- probe_4 (R4.1/R4.2): lambdify parity of -Mod(x,y) between default modules and modules=[] over several inputs; f_empty(3,7)==-3. HOLDS.
- probe_5 (R2.4): pycode(-x**2) == '-x**2' (Pow binds >= exponentiation, no added parens). HOLDS.
- probe_6 (R5.1/R5.2 regression): pycode(x**y)=='x**y', And(a,b)->'a and b', Or(a,b)->'a or b'. HOLDS.
- probe_7 (R5.4/R2.3): C printer with create_expand_pow_optimization(4): ccode(y - x**4) wraps the negated repeated-factor product as '(x*x*x*x)'; non-negated expand stays 'x*x*x*x'; the too-large power (x**8) renders through pow() unwrapped. HOLDS.
- probe_8 (R2.5): pycode(-x*y)=='-x*y' (multi-factor negation uses else-branch, unchanged); 2*Mod(x,y)->'2*(x % y)'. HOLDS.

### CANDIDATE PATCHES (both requirements-plausible partial fixes, both REJECTED by the suite):
- weak_A (precedence.py Mod entry only, no codeprinter change): probe_1 VIOLATED (-Mod prints '-x % y'... actually the single-negated wrap missing), probe_4 VIOLATED (lambdify value mismatch), probe_7 VIOLATED (C expand-pow negation not wrapped). Rejected.
- weak_B (codeprinter single-negated-factor branch only, no Mod precedence entry): probe_1 VIOLATED and probe_4 VIOLATED (Mod has no Mul precedence, so the midway-weight comparison still doesn't wrap it -> '-x % y', wrong lambdify value). Rejected.

Both halves of the gold patch are necessary: the probe suite discriminates each partial fix. Positive control failed at base and holds patched. Verdict SOUND.

Note (advisory, matches recorded G-PANEL-3=fail): the requirements prose reproduces the gold's internal 0.5*(Pow+Mul) midway-weight mechanism; that is a leakage concern for G-PANEL-3, not a spec-fidelity/too-weak concern for G-EQ. My probes encode only black-box observable outcomes, and they discriminate correctly.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 requirement probes hold on the patched tree; 2/2 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 8 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 8 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py`, `probe_7.py`, `probe_8.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 2 alternative candidate patches, claimed to satisfy every cited requirement, and ran the same suite against them. The suite rejected all 2: a probe encoding a cited requirement fails under each of those, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (8):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts, and on this backend both roles put it through the same derivation: every block below is a requirement probe run on the gold-patched tree, and the `machine verdict:` line each role publishes above reports BOTH that its probes hold there and how many candidate patches the probe suite rejected — so the two roles re-ran ONE probe suite and each recorded its own outcome for every probe in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `probe_1.py` → holds on the patched tree (good)

Attack 2 — `probe_2.py` → holds on the patched tree (good)

Attack 3 — `probe_3.py` → holds on the patched tree (good)

Attack 4 — `probe_4.py` → holds on the patched tree (good)

Attack 5 — `probe_5.py` → holds on the patched tree (good)

Attack 6 — `probe_6.py` → holds on the patched tree (good)

Attack 7 — `probe_7.py` → holds on the patched tree (good)

Attack 8 — `probe_8.py` → holds on the patched tree (good)

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
# Positive control: R2.2 / R1 -- -Mod(x,y) prints as -(x % y) under pycode
from sympy import symbols, Mod
from sympy.printing.pycode import pycode
x, y = symbols('x y')
out = pycode(-Mod(x, y))
print("pycode(-Mod(x,y)) =", repr(out))
assert out == "-(x % y)", out
print("OK")
```

Prepatch bug re-encoded as an attack: `True`.

Bundle sympy__sympy-22080, backend ears. 8 probes covering all 5 requirements; all HOLD on the gold-patched tree.

Probes and requirement mapping:
- probe_1 (POSITIVE CONTROL, R2.2/R1): pycode(-Mod(x,y)) == '-(x % y)'. HOLDS patched; at BASE prints '-x % y' (VIOLATED) -> discriminates.
- probe_2 (R1.3): pycode(Mod(x,2)) == 'x % 2' (top-level, no outer parens). HOLDS.
- probe_3 (R3.2): pycode(Mod(-x,y)) == '(-x) % y'. HOLDS.
- probe_4 (R4.1/R4.2): lambdify parity of -Mod(x,y) between default modules and modules=[] over several inputs; f_empty(3,7)==-3. HOLDS.
- probe_5 (R2.4): pycode(-x**2) == '-x**2' (Pow binds >= exponentiation, no added parens). HOLDS.
- probe_6 (R5.1/R5.2 regression): pycode(x**y)=='x**y', And(a,b)->'a and b', Or(a,b)->'a or b'. HOLDS.
- probe_7 (R5.4/R2.3): C printer with create_expand_pow_optimization(4): ccode(y - x**4) wraps the negated repeated-factor product as '(x*x*x*x)'; non-negated expand stays 'x*x*x*x'; the too-large power (x**8) renders through pow() unwrapped. HOLDS.
- probe_8 (R2.5): pycode(-x*y)=='-x*y' (multi-factor negation uses else-branch, unchanged); 2*Mod(x,y)->'2*(x % y)'. HOLDS.

### CANDIDATE PATCHES (both requirements-plausible partial fixes, both REJECTED by the suite):
- weak_A (precedence.py Mod entry only, no codeprinter change): probe_1 VIOLATED (-Mod prints '-x % y'... actually the single-negated wrap missing), probe_4 VIOLATED (lambdify value mismatch), probe_7 VIOLATED (C expand-pow negation not wrapped). Rejected.
- weak_B (codeprinter single-negated-factor branch only, no Mod precedence entry): probe_1 VIOLATED and probe_4 VIOLATED (Mod has no Mul precedence, so the midway-weight comparison still doesn't wrap it -> '-x % y', wrong lambdify value). Rejected.

Both halves of the gold patch are necessary: the probe suite discriminates each partial fix. Positive control failed at base and holds patched. Verdict SOUND.

Note (advisory, matches recorded G-PANEL-3=fail): the requirements prose reproduces the gold's internal 0.5*(Pow+Mul) midway-weight mechanism; that is a leakage concern for G-PANEL-3, not a spec-fidelity/too-weak concern for G-EQ. My probes encode only black-box observable outcomes, and they discriminate correctly.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Patch is two hunks: precedence.py adds "Mod": PRECEDENCE["Mul"]; codeprinter._print_Mul adds a len(a)==1 and sign=='-' branch parenthesizing against 0.5*(PRECEDENCE['Pow']+PRECEDENCE['Mul']). Requirements pin the CHANGED observable behavior (Mod parenthesization, negated single-factor wrapping, C-printer expand-pow negation, lambdify parity) rather than one branch/helper. Note: the requirements.md prose has been REVISED from the version G-PANEL-3 (leakage) flagged — R2.1/R2.4 no longer state the internal 'midway weight' rule but instead frame the boundary observably ('binds less tightly than an exponentiation'), which is exactly the observable modeling boundary. R2.3's -(x*x*x*x)/-(x*x) examples are only reachable via create_expand_pow_optimization in the C printer (naive pycode collapses x*x*x*x to Pow x**4 -> '-x**4'); this is restated in R5.4 and matches gold test_rewriting.py — faithful framing, not invented behavior. Verified: base probes show '-x % y' and lambdify 4, patched show '-(x % y)' and -3, confirming the requirements track the actual fix. Verdict FAITHFUL for the faithfulness dimension (G-PANEL-2); the separate G-PANEL-3 leakage stamp is a different dimension.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The requirements describe behavior and localize the change to public sympy modules/functions (precedence.py, codeprinter.py, _print_Mul, create_expand_pow_optimization, PRECEDENCE, pow) — all pre-existing public identifiers, not fix-invented. No test names, file paths, parametrization ids, or quoted test/gold code appear. The gold's magic weight 0.5*(PRECEDENCE['Pow']+PRECEDENCE['Mul']) is paraphrased behaviorally ('binds below exponentiation, at multiplicative level'), not transmitted verbatim. Example strings that coincide with hidden-test expectations: -(x % y), (-x) % y, -(x*x*x*x), -(x*x), pow(x,i)-(x*x); and Req5.4 enumerates the three expand-pow scenarios matching test_create_expand_pow_optimization. These are canonical illustrations of the described precedence/parenthesization behavior — legitimate translation of what tests check into acceptance criteria — rather than reconstruction of the tests themselves. The (3,7)->-3 numeric example is already public in the problem_statement. Borderline on Req5.4's test-shaped enumeration, but it states a genuine behavioral consequence of the universal _print_Mul change (C printer regression), framed as a rule not a case list keyed to test structure. No semantic gold/test reconstruction beyond the public spec.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
