# P2 adversarial audit — sympy__sympy-21612

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
# Positive control - Req1: reciprocal of a reciprocal (compound Pow base)
from sympy import symbols, Mul, Pow
x, y = symbols('x y')
expr = Mul(x, Pow(1/y, -1, evaluate=False), evaluate=False)
s = str(expr)
print("got:", repr(s))
assert s == 'x/(1/y)', s
print("OK")
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
# Req2.1 - reciprocal of a product base keeps parens
from sympy import symbols, Mul, Pow
x, y = symbols('x y')
expr = Mul(-2, x, Pow(Mul(y, y, evaluate=False), -1, evaluate=False), evaluate=False)
s = str(expr)
print("got:", repr(s))
assert s == '-2*x/(y*y)', s
print("OK")
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
# Req3.2 - simple x/y no added parens
from sympy import symbols
x, y = symbols('x y')
s = str(x/y)
print("got:", repr(s))
assert s == 'x/y', s
print("OK")
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
# Req4.5 - negative exponent not -1 renders as power in denominator
from sympy import symbols
x, y = symbols('x y')
s = str(x*y**-2)
print("got:", repr(s))
assert s == 'x/y**2', s
print("OK")
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
# Req4.3 - multiple denominator factors joined by * inside one pair of parens
from sympy import symbols
x, y, z = symbols('x y z')
s = str(x/(y*z))
print("got:", repr(s))
assert s == 'x/(y*z)', s
print("OK")
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
# Req3.1/3.3 - single-component reciprocal base (lone symbol) NOT wrapped
# and evaluated reciprocal 1/x prints 1/x with no extra parens
from sympy import symbols, Mul, Pow
x, y = symbols('x y')
s1 = str(1/x)
print("1/x ->", repr(s1))
assert s1 == '1/x', s1
# a Mul with reciprocal of a lone symbol
s2 = str(Mul(x, Pow(y, -1, evaluate=False), evaluate=False))
print("x*y**-1 ->", repr(s2))
assert s2 == 'x/y', s2
print("OK")
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
# Positive control - Req1: reciprocal of a reciprocal (compound Pow base)
from sympy import symbols, Mul, Pow
x, y = symbols('x y')
expr = Mul(x, Pow(1/y, -1, evaluate=False), evaluate=False)
s = str(expr)
print("got:", repr(s))
assert s == 'x/(1/y)', s
print("OK")
```

Prepatch bug re-encoded as an attack: `True`.

6 probes, all HOLD on gold-patched tree. Coverage: probe_1 (Req1.1/1.2 reciprocal-of-reciprocal compound Pow base -> 'x/(1/y)', also positive control), probe_2 (Req2.1/2.2 reciprocal of product Mul base with coeff/sign -> '-2*x/(y*y)'), probe_3 (Req3.2 simple x/y no parens), probe_4 (Req4.5 exponent != -1 renders as denominator power 'x/y**2'), probe_5 (Req4.3 multi denom factors '(y*z)'), probe_6 (Req3.1/3.3 lone-symbol reciprocal base unwrapped + evaluated 1/x). Positive control probe_1 FAILS at base (base prints 'x/1/y', chained division) and HOLDS patched -> discriminating. Wrong-fix candidate weak.diff swaps isinstance(item.base,(Mul,Pow)) for isinstance(item.base,Pow) alone (drops the pre-existing Mul case): REJECTED by probe_2 (prints '-2*x/y*y', exit 1), while probe_1/probe_5 still pass. This demonstrates the suite discriminates a requirements-violating partial fix (regresses Req2). No too-weak finding: every constructed alternative fails at least one probe. Gold patch changes exactly one isinstance check from Mul to (Mul, Pow).

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
# Positive control - Req1: reciprocal of a reciprocal (compound Pow base)
from sympy import symbols, Mul, Pow
x, y = symbols('x y')
expr = Mul(x, Pow(1/y, -1, evaluate=False), evaluate=False)
s = str(expr)
print("got:", repr(s))
assert s == 'x/(1/y)', s
print("OK")
```

Prepatch bug re-encoded as an attack: `True`.

6 probes, all HOLD on gold-patched tree. Coverage: probe_1 (Req1.1/1.2 reciprocal-of-reciprocal compound Pow base -> 'x/(1/y)', also positive control), probe_2 (Req2.1/2.2 reciprocal of product Mul base with coeff/sign -> '-2*x/(y*y)'), probe_3 (Req3.2 simple x/y no parens), probe_4 (Req4.5 exponent != -1 renders as denominator power 'x/y**2'), probe_5 (Req4.3 multi denom factors '(y*z)'), probe_6 (Req3.1/3.3 lone-symbol reciprocal base unwrapped + evaluated 1/x). Positive control probe_1 FAILS at base (base prints 'x/1/y', chained division) and HOLDS patched -> discriminating. Wrong-fix candidate weak.diff swaps isinstance(item.base,(Mul,Pow)) for isinstance(item.base,Pow) alone (drops the pre-existing Mul case): REJECTED by probe_2 (prints '-2*x/y*y', exit 1), while probe_1/probe_5 still pass. This demonstrates the suite discriminates a requirements-violating partial fix (regresses Req2). No too-weak finding: every constructed alternative fails at least one probe. Gold patch changes exactly one isinstance check from Mul to (Mul, Pow).

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Gold patch is a one-line widening in StrPrinter._print_Mul: isinstance(item.base, Mul) -> isinstance(item.base, (Mul, Pow)), still guarded by len(item.args[0].args)!=1. Requirements model the changed OBSERVABLE str output (correct modeling boundary), not a narrow internal slice: R1 = the actual fix (compound-power reciprocal base now bracketed), R2 = preserved compound-product case, R3 = single-component no-parens boundary, R4 = unchanged Mul invariants incl. negative-non-(-1) exponent. Only nit is R3.1's parenthetical 'argument count is one, e.g. a lone symbol' — a lone Symbol actually has 0 args and the guard is !=1 — but the described no-parens output is exactly what the code produces, so no requirement/code disagreement on any concrete input. Faithful. (G-PANEL-3 leakage is a separate stamp and does not bear on faithfulness.)


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The requirements localize the change to StrPrinter._print_Mul in sympy/printing/str.py (legitimate) and describe the gold edit (isinstance(item.base, Mul) -> (Mul, Pow)) as a behavioral requirement: bracket a reciprocal denominator factor whose base is a compound power as well as a compound product. This is the intended translation of test behavior into requirements. No hidden-test content is transmitted: the test name 'test_Mul' and file path test_str.py are absent; the exact hidden assertion string 'x/(1/y)' does not appear (only the generic contrast example 'x/y' does); the gold comment/issue numbers (#14160, #21537) are absent; and the gold condition len(item.args[0].args)!=1 is expressed behaviorally as 'argument count is one / more than one argument' rather than quoted. The document describes behavior, not the tests themselves.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
