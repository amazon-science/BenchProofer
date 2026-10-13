# P2 adversarial audit — sympy__sympy-20428

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
Weak candidate `__bool__` = `f.ex.is_zero == False` maps undetermined coefficients (is_zero is None) to False, so `bool(EX(a))` returns False and a not-provably-zero coefficient gets discarded — violates Req1.4. probe_3 REJECTS it (a.is_zero=None -> bool False, want True) while probe_1/2/4/5/6 still pass, demonstrating the suite discriminates.
```

**Attacks re-run (6):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
# Positive control + Req2.1/2.2 + Req3.3: the reported complicated constant that
# cancels to zero builds a Poly that equals Poly(0,x,EX) and has is_zero True.
import sys
from sympy import Poly, sympify, symbols
x = symbols("x")
BIG = ("-117968192370600*18**(1/3)/(217603955769048*(24201 + "
"253*sqrt(9165))**(1/3) + 2273005839412*sqrt(9165)*(24201 + "
"253*sqrt(9165))**(1/3)) - 15720318185*2**(2/3)*3**(1/3)*(24201 "
"+ 253*sqrt(9165))**(2/3)/(217603955769048*(24201 + 253*sqrt(9165))**"
"(1/3) + 2273005839412*sqrt(9165)*(24201 + 253*sqrt(9165))**(1/3)) "
"+ 15720318185*12**(1/3)*(24201 + 253*sqrt(9165))**(2/3)/("
"217603955769048*(24201 + 253*sqrt(9165))**(1/3) + 2273005839412*"
"sqrt(9165)*(24201 + 253*sqrt(9165))**(1/3)) + 117968192370600*2**("
"1/3)*3**(2/3)/(217603955769048*(24201 + 253*sqrt(9165))**(1/3)"
"+ 2273005839412*sqrt(9165)*(24201 + 253*sqrt(9165))**(1/3))")
f = Poly(sympify(BIG), x)
z = Poly(0, x, domain='EX')
eq = (f == z)
isz = f.is_zero
print("f =", f)
print("f == Poly(0,x,EX):", eq)
print("f.is_zero:", isz)
print("f.rep.rep (dense list):", f.rep.rep)
ok = bool(eq) and isz is True and f.rep.rep == []
print("OK" if ok else "FAIL")
sys.exit(0 if ok else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
# Req1.1/1.2/1.5: __bool__ of an EX element reflects mathematical zero.
# - literal 0 -> False; literal 1 -> True; nested-radical cancel-to-zero -> False.
import sys
from sympy import sqrt, sympify
from sympy.polys.domains import EX
zero_lit = EX.from_sympy(sympify(0))
one_lit = EX.from_sympy(sympify(1))
# simple cancelling expression that is not literal 0: sqrt(2)*sqrt(3) - sqrt(6)
cancel = EX.from_sympy(sqrt(2)*sqrt(3) - sqrt(6))
b_zero = bool(zero_lit)
b_one = bool(one_lit)
b_cancel = bool(cancel)
print("bool(EX(0)) =", b_zero, "(want False)")
print("bool(EX(1)) =", b_one, "(want True)")
print("cancel ex =", cancel.ex, "is_zero=", cancel.ex.is_zero)
print("bool(EX(cancel)) =", b_cancel, "(want False)")
ok = (b_zero is False) and (b_one is True) and (b_cancel is False)
print("OK" if ok else "FAIL")
sys.exit(0 if ok else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
# Req1.3/1.4/4.1: genuinely non-zero element -> True; undetermined -> True.
import sys
from sympy import symbols, sqrt
from sympy.polys.domains import EX
a = symbols("a")
nonzero = EX.from_sympy(sqrt(2))          # provably non-zero
symb = EX.from_sympy(a)                    # undetermined zero-status
b_nonzero = bool(nonzero)
b_symb = bool(symb)
print("sqrt(2).is_zero =", sqrt(2).is_zero, "bool ->", b_nonzero, "(want True)")
print("a.is_zero =", a.is_zero, "bool ->", b_symb, "(want True: not discarded)")
ok = (b_nonzero is True) and (b_symb is True)
print("OK" if ok else "FAIL")
sys.exit(0 if ok else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
# Req3.1/3.2: terms_gcd() and primitive() on the cancel-to-zero constant poly
# behave like the zero polynomial and do not raise.
import sys
from sympy import Poly, sympify, symbols
x = symbols("x")
BIG = ("-117968192370600*18**(1/3)/(217603955769048*(24201 + "
"253*sqrt(9165))**(1/3) + 2273005839412*sqrt(9165)*(24201 + "
"253*sqrt(9165))**(1/3)) - 15720318185*2**(2/3)*3**(1/3)*(24201 "
"+ 253*sqrt(9165))**(2/3)/(217603955769048*(24201 + 253*sqrt(9165))**"
"(1/3) + 2273005839412*sqrt(9165)*(24201 + 253*sqrt(9165))**(1/3)) "
"+ 15720318185*12**(1/3)*(24201 + 253*sqrt(9165))**(2/3)/("
"217603955769048*(24201 + 253*sqrt(9165))**(1/3) + 2273005839412*"
"sqrt(9165)*(24201 + 253*sqrt(9165))**(1/3)) + 117968192370600*2**("
"1/3)*3**(2/3)/(217603955769048*(24201 + 253*sqrt(9165))**(1/3)"
"+ 2273005839412*sqrt(9165)*(24201 + 253*sqrt(9165))**(1/3))")
f = Poly(sympify(BIG), x)
try:
    tg = f.terms_gcd()
    pr = f.primitive()
except Exception as e:
    print("RAISED:", type(e).__name__, e)
    print("FAIL")
    sys.exit(1)
print("terms_gcd() =", tg)
print("primitive() =", pr)
print("OK")
sys.exit(0)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
# Req4.1/4.2: preserve existing behavior for genuinely non-zero polys.
import sys
from sympy import Poly, symbols, sqrt
x = symbols("x")
# non-zero poly over EX with symbolic coeff
p = Poly(sqrt(2)*x**2 + 3*x + 1, x, domain='EX')
checks = {}
checks["is_zero_false"] = (p.is_zero is False)
checks["degree"] = (p.degree() == 2)
checks["coeff_extract"] = (p.all_coeffs()[0].as_expr() == sqrt(2))
checks["ne_zero"] = (p != Poly(0, x, domain='EX'))
checks["arith"] = ((p - p) == Poly(0, x, domain='EX'))
# a non-cancelling EX constant retained
c = Poly(sqrt(2), x, domain='EX')
checks["const_nonzero"] = (c.is_zero is False and c.rep.rep != [])
for k, v in checks.items():
    print(k, "=", v)
ok = all(checks.values())
print("OK" if ok else "FAIL")
sys.exit(0 if ok else 1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
# Req2.4 + Req4.3: clear_denoms() still returns (multiplier, poly) and the
# cleared constant poly that turns out zero is canonical zero.
import sys
from sympy import Poly, sympify, symbols
x = symbols("x")
BIG = ("-117968192370600*18**(1/3)/(217603955769048*(24201 + "
"253*sqrt(9165))**(1/3) + 2273005839412*sqrt(9165)*(24201 + "
"253*sqrt(9165))**(1/3)) - 15720318185*2**(2/3)*3**(1/3)*(24201 "
"+ 253*sqrt(9165))**(2/3)/(217603955769048*(24201 + 253*sqrt(9165))**"
"(1/3) + 2273005839412*sqrt(9165)*(24201 + 253*sqrt(9165))**(1/3)) "
"+ 15720318185*12**(1/3)*(24201 + 253*sqrt(9165))**(2/3)/("
"217603955769048*(24201 + 253*sqrt(9165))**(1/3) + 2273005839412*"
"sqrt(9165)*(24201 + 253*sqrt(9165))**(1/3)) + 117968192370600*2**("
"1/3)*3**(2/3)/(217603955769048*(24201 + 253*sqrt(9165))**(1/3)"
"+ 2273005839412*sqrt(9165)*(24201 + 253*sqrt(9165))**(1/3))")
f = Poly(sympify(BIG), x)
res = f.clear_denoms()
print("clear_denoms returned tuple len", len(res))
coeff, bad_poly = res
print("multiplier:", coeff)
print("cleared poly:", bad_poly, "is_zero=", bad_poly.is_zero)
ok = (len(res) == 2) and (bad_poly == Poly(0, x, domain='EX')) and (bad_poly.is_zero is True)
# also non-zero case: clear_denoms still returns 2-tuple with retained poly
g = Poly(x/2 + sympify("1/3"), x)
gc = g.clear_denoms()
print("nonzero clear_denoms:", gc)
ok = ok and (len(gc) == 2) and (gc[1].is_zero is False)
print("OK" if ok else "FAIL")
sys.exit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
# Positive control + Req2.1/2.2 + Req3.3: the reported complicated constant that
# cancels to zero builds a Poly that equals Poly(0,x,EX) and has is_zero True.
import sys
from sympy import Poly, sympify, symbols
x = symbols("x")
BIG = ("-117968192370600*18**(1/3)/(217603955769048*(24201 + "
"253*sqrt(9165))**(1/3) + 2273005839412*sqrt(9165)*(24201 + "
"253*sqrt(9165))**(1/3)) - 15720318185*2**(2/3)*3**(1/3)*(24201 "
"+ 253*sqrt(9165))**(2/3)/(217603955769048*(24201 + 253*sqrt(9165))**"
"(1/3) + 2273005839412*sqrt(9165)*(24201 + 253*sqrt(9165))**(1/3)) "
"+ 15720318185*12**(1/3)*(24201 + 253*sqrt(9165))**(2/3)/("
"217603955769048*(24201 + 253*sqrt(9165))**(1/3) + 2273005839412*"
"sqrt(9165)*(24201 + 253*sqrt(9165))**(1/3)) + 117968192370600*2**("
"1/3)*3**(2/3)/(217603955769048*(24201 + 253*sqrt(9165))**(1/3)"
"+ 2273005839412*sqrt(9165)*(24201 + 253*sqrt(9165))**(1/3))")
f = Poly(sympify(BIG), x)
z = Poly(0, x, domain='EX')
eq = (f == z)
isz = f.is_zero
print("f =", f)
print("f == Poly(0,x,EX):", eq)
print("f.is_zero:", isz)
print("f.rep.rep (dense list):", f.rep.rep)
ok = bool(eq) and isz is True and f.rep.rep == []
print("OK" if ok else "FAIL")
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Fix: `__bool__` changed from `f.ex != 0` (structural) to `not f.ex.is_zero` (mathematical). 6 probes cover Req1.1/1.2/1.5 (probe_2), Req1.3/1.4/4.1 (probe_3), Req2.1/2.2/3.3 (probe_1), Req3.1/3.2 (probe_4), Req4.1/4.2 (probe_5), Req2.4/4.3 (probe_6). All HOLD on gold-patched tree. Positive control probe_1 (reported nested-radical constant -> Poly(0,x,EX), is_zero True, empty dense rep) FAILS at base (VIOLATED: base is_zero False, unstripped rep) and HOLDS patched. One requirements-conforming-but-too-weak reading rejected. VIOLATION direction: no probe fails on patched tree -> requirements not too strong. TOO-WEAK direction: constructed the lazy `==False` fix; suite rejects it via Req1.4, so at least one wrong impl is discriminated; no probe-conforming alternative found that would pass every probe. Verdict SOUND.

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
Weak candidate `__bool__` = `f.ex.is_zero == False` maps undetermined coefficients (is_zero is None) to False, so `bool(EX(a))` returns False and a not-provably-zero coefficient gets discarded — violates Req1.4. probe_3 REJECTS it (a.is_zero=None -> bool False, want True) while probe_1/2/4/5/6 still pass, demonstrating the suite discriminates.
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
# Positive control + Req2.1/2.2 + Req3.3: the reported complicated constant that
# cancels to zero builds a Poly that equals Poly(0,x,EX) and has is_zero True.
import sys
from sympy import Poly, sympify, symbols
x = symbols("x")
BIG = ("-117968192370600*18**(1/3)/(217603955769048*(24201 + "
"253*sqrt(9165))**(1/3) + 2273005839412*sqrt(9165)*(24201 + "
"253*sqrt(9165))**(1/3)) - 15720318185*2**(2/3)*3**(1/3)*(24201 "
"+ 253*sqrt(9165))**(2/3)/(217603955769048*(24201 + 253*sqrt(9165))**"
"(1/3) + 2273005839412*sqrt(9165)*(24201 + 253*sqrt(9165))**(1/3)) "
"+ 15720318185*12**(1/3)*(24201 + 253*sqrt(9165))**(2/3)/("
"217603955769048*(24201 + 253*sqrt(9165))**(1/3) + 2273005839412*"
"sqrt(9165)*(24201 + 253*sqrt(9165))**(1/3)) + 117968192370600*2**("
"1/3)*3**(2/3)/(217603955769048*(24201 + 253*sqrt(9165))**(1/3)"
"+ 2273005839412*sqrt(9165)*(24201 + 253*sqrt(9165))**(1/3))")
f = Poly(sympify(BIG), x)
z = Poly(0, x, domain='EX')
eq = (f == z)
isz = f.is_zero
print("f =", f)
print("f == Poly(0,x,EX):", eq)
print("f.is_zero:", isz)
print("f.rep.rep (dense list):", f.rep.rep)
ok = bool(eq) and isz is True and f.rep.rep == []
print("OK" if ok else "FAIL")
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Fix: `__bool__` changed from `f.ex != 0` (structural) to `not f.ex.is_zero` (mathematical). 6 probes cover Req1.1/1.2/1.5 (probe_2), Req1.3/1.4/4.1 (probe_3), Req2.1/2.2/3.3 (probe_1), Req3.1/3.2 (probe_4), Req4.1/4.2 (probe_5), Req2.4/4.3 (probe_6). All HOLD on gold-patched tree. Positive control probe_1 (reported nested-radical constant -> Poly(0,x,EX), is_zero True, empty dense rep) FAILS at base (VIOLATED: base is_zero False, unstripped rep) and HOLDS patched. One requirements-conforming-but-too-weak reading rejected. VIOLATION direction: no probe fails on patched tree -> requirements not too strong. TOO-WEAK direction: constructed the lazy `==False` fix; suite rejects it via Req1.4, so at least one wrong impl is discriminated; no probe-conforming alternative found that would pass every probe. Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Gold patch is a one-liner in expressiondomain.py __bool__: `f.ex != 0` → `not f.ex.is_zero`. The requirements model the full observable chain (element truthiness → dense stripping → is_zero/equality/terms_gcd/primitive/clear_denoms), i.e. the changed behavior, not a narrow internal slice — correct modeling boundary. Base-commit probe confirms every requirement's target case flips (complicated coeff bool=True, f!=Poly(0), is_zero=False), so the requirements distinguish patched from unpatched. Requirement 1.4's treatment of undetermined (is_zero=None → truthy) faithfully captures the `not None` semantics. FAITHFUL.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The public problem_statement is exhaustive: it contains the exact nested-radical clear_denoms() example, the is_zero vs as_expr() disagreement, the terms_gcd() IndexError, the primitive() ZeroDivisionError, and the DMP unstripped-leading-zero observation (DMP([EX(0)]) vs DMP([])). requirements.md translates these into behavioral EARS criteria. The only hidden test, test_issue_20427 (F2P), constructs that same poly (already verbatim in the problem statement) and asserts f == Poly(0, x, domain='EX') — the doc never names it or its file/id. The gold edit `return not f.ex.is_zero` is described behaviorally ('assumptions system determines the wrapped expression to be mathematically zero'); is_zero is a standard SymPy attribute, not a fix-invented identifier. Module/class names (expressiondomain.py, ExpressionDomain.Expression, densebasic.py) are legitimate localization already implied by the problem-statement traceback. Requirement 1's undetermined->true and literal 0/1 cases are behavioral generalizations of is_zero semantics, not mirrors of any parametrized test cases (none exist). No test names/paths/ids, no quoted test/gold code, no test-shaped enumerations.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
