# P2 adversarial audit — sympy__sympy-19783

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

Counterexample / evidence:

```
Partial-fix candidate (weak.diff: only Dagger.__mul__, omitting IdentityOperator.__mul__ Dagger handling) is REJECTED by probe_3 which encodes Req 2.1 (I * Dagger(A) SHALL == Dagger(A)); under weak.diff it yields the unevaluated I*Dagger(A). This demonstrates the suite discriminates wrong implementations.
```

**Attacks re-run (7):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
"""Req1.1 (positive control): Dagger(A) * Identity SHALL return Dagger(A)."""
import sys
from sympy.physics.quantum.operator import Operator, IdentityOperator
from sympy.physics.quantum.dagger import Dagger

A = Operator('A')
I = IdentityOperator()
res = Dagger(A) * I
expected = Dagger(A)
print("Dagger(A)*I =", repr(res), " expected:", repr(expected))
sys.exit(0 if res == expected else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""Req1.2: Dagger(A) * Dagger(Identity) SHALL return Dagger(A)
(conjugate of identity is the identity)."""
import sys
from sympy.physics.quantum.operator import Operator, IdentityOperator
from sympy.physics.quantum.dagger import Dagger

A = Operator('A')
I = IdentityOperator()
dagI = Dagger(I)
print("Dagger(I) =", repr(dagI))
res = Dagger(A) * dagI
expected = Dagger(A)
print("Dagger(A)*Dagger(I) =", repr(res), " expected:", repr(expected))
sys.exit(0 if res == expected else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""Req2.1: Identity * Dagger(A) SHALL return Dagger(A)."""
import sys
from sympy.physics.quantum.operator import Operator, IdentityOperator
from sympy.physics.quantum.dagger import Dagger

A = Operator('A')
I = IdentityOperator()
res = I * Dagger(A)
expected = Dagger(A)
print("I*Dagger(A) =", repr(res), " expected:", repr(expected))
sys.exit(0 if res == expected else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""Req3.1 & 3.2: Non-identity products of a Dagger stay unevaluated.
Dagger(A)*B stays as Mul(Dagger(A),B); Dagger(A)*Dagger(A) == Dagger(A)**2."""
import sys
from sympy import Mul
from sympy.physics.quantum.operator import Operator, IdentityOperator
from sympy.physics.quantum.dagger import Dagger

A = Operator('A')
B = Operator('B')

# 3.1: Dagger(A) * B unevaluated product, not collapsed to a factor
res = Dagger(A) * B
expected = Mul(Dagger(A), B)
print("Dagger(A)*B =", repr(res), " expected:", repr(expected))
ok1 = (res == expected) and (res != Dagger(A)) and (res != B)

# 3.2: Dagger(A)*Dagger(A) == Dagger(A)**2
res2 = Dagger(A) * Dagger(A)
expected2 = Dagger(A)**2
print("Dagger(A)*Dagger(A) =", repr(res2), " expected:", repr(expected2))
ok2 = (res2 == expected2)

sys.exit(0 if (ok1 and ok2) else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""Req3.3: (Dagger(A)*B) * Identity SHALL preserve the inner product as operand.
The final product equals Mul(inner, I) with inner unchanged."""
import sys
from sympy import Mul
from sympy.physics.quantum.operator import Operator, IdentityOperator
from sympy.physics.quantum.dagger import Dagger

A = Operator('A')
B = Operator('B')
I = IdentityOperator()

inner = Dagger(A) * B          # unevaluated Mul(Dagger(A), B)
final = inner * I
expected = Mul(inner, I)
print("inner =", repr(inner))
print("(inner)*I =", repr(final), " expected:", repr(expected))
# The final product SHALL equal the unevaluated product multiplied by the
# identity operator, with the inner product unchanged (not collapsed to a factor
# and I not absorbed). Mul flattens the nesting, so check by equality.
ok = (final == expected) and (final != inner) and (I in final.args)
print("final==Mul(inner,I):", final == expected, " I in final.args:", I in final.args)
sys.exit(0 if ok else 1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
"""Req4.1-4.4: Pre-existing identity simplifications preserved.
4.1 I*A == A ; 4.2 A*I == A ; 4.3 I*I is IdentityOperator ; 4.4 I*scalar unevaluated Mul."""
import sys
from sympy import Mul, Symbol, Integer
from sympy.physics.quantum.operator import Operator, IdentityOperator
from sympy.physics.quantum.dagger import Dagger

A = Operator('A')
I = IdentityOperator()

r41 = I * A
ok41 = (r41 == A)
print("I*A =", repr(r41), "-> ok", ok41)

r42 = A * I
ok42 = (r42 == A)
print("A*I =", repr(r42), "-> ok", ok42)

r43 = I * I
ok43 = isinstance(r43, IdentityOperator)
print("I*I =", repr(r43), "isIdentity", ok43)

x = Symbol('x')
r44 = I * x
ok44 = isinstance(r44, Mul) and (r44 == Mul(I, x))
print("I*x =", repr(r44), "-> ok", ok44)

sys.exit(0 if (ok41 and ok42 and ok43 and ok44) else 1)
```

Attack 7 — `probe_7.py` → holds on the patched tree (good)

```python
"""Req4.5: Dagger construction rules preserved for supported args
(scalars, kets, bras, inner/outer products, sums, products, powers)."""
import sys
from sympy import Symbol, I as ImagUnit, sqrt, conjugate
from sympy.physics.quantum.dagger import Dagger
from sympy.physics.quantum.state import Ket, Bra
from sympy.physics.quantum.operator import Operator

checks = []

# scalar: Dagger(2+3i) == conjugate
z = 2 + 3*ImagUnit
checks.append(("scalar", Dagger(z), conjugate(z)))

# ket -> bra
k = Ket('k')
checks.append(("ket->bra", Dagger(k), Bra('k')))

# bra -> ket
b = Bra('b')
checks.append(("bra->ket", Dagger(b), Ket('b')))

# power: Dagger(A**2) == Dagger(A)**2
A = Operator('A')
checks.append(("power", Dagger(A**2), Dagger(A)**2))

# double dagger returns arg
checks.append(("double", Dagger(Dagger(A)), A))

ok = True
for name, got, exp in checks:
    good = (got == exp)
    ok = ok and good
    print(f"{name}: {got!r} == {exp!r} -> {good}")

sys.exit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Req1.1 (positive control): Dagger(A) * Identity SHALL return Dagger(A)."""
import sys
from sympy.physics.quantum.operator import Operator, IdentityOperator
from sympy.physics.quantum.dagger import Dagger

A = Operator('A')
I = IdentityOperator()
res = Dagger(A) * I
expected = Dagger(A)
print("Dagger(A)*I =", repr(res), " expected:", repr(expected))
sys.exit(0 if res == expected else 1)
```

Prepatch bug re-encoded as an attack: `True`.

7 probes cover all 4 requirements: probe_1 Req1.1 (Dagger(A)*I -> Dagger(A)) = positive control (FAILS at base, HOLDS patched); probe_2 Req1.2 (Dagger(A)*Dagger(I) -> Dagger(A)); probe_3 Req2.1 (I*Dagger(A) -> Dagger(A)); probe_4 Req3.1/3.2 (Dagger(A)*B unevaluated Mul, Dagger(A)*Dagger(A)==Dagger(A)**2); probe_5 Req3.3 ((Dagger(A)*B)*I == Mul(inner,I), inner preserved, I not absorbed); probe_6 Req4.1-4.4 (I*A, A*I, I*I, I*scalar regressions); probe_7 Req4.5 (Dagger construction rules for scalar/ket/bra/power/double). All 7 HOLD on gold-patched tree. Positive control probe_1 and probe_3 both VIOLATED at base, confirming discriminating power. The requirements-conforming partial patch (weak.diff) is rejected by probe_3. Probe_5 was initially over-strict (checked literal Mul.args membership which Mul flattens) and was corrected to match the requirement's actual biconditional (final == Mul(inner,I)); re-ran and it HOLDS.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 7 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 7 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py`, `probe_7.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

Counterexample / evidence:

```
Partial-fix candidate (weak.diff: only Dagger.__mul__, omitting IdentityOperator.__mul__ Dagger handling) is REJECTED by probe_3 which encodes Req 2.1 (I * Dagger(A) SHALL == Dagger(A)); under weak.diff it yields the unevaluated I*Dagger(A). This demonstrates the suite discriminates wrong implementations.
```

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
"""Req1.1 (positive control): Dagger(A) * Identity SHALL return Dagger(A)."""
import sys
from sympy.physics.quantum.operator import Operator, IdentityOperator
from sympy.physics.quantum.dagger import Dagger

A = Operator('A')
I = IdentityOperator()
res = Dagger(A) * I
expected = Dagger(A)
print("Dagger(A)*I =", repr(res), " expected:", repr(expected))
sys.exit(0 if res == expected else 1)
```

Prepatch bug re-encoded as an attack: `True`.

7 probes cover all 4 requirements: probe_1 Req1.1 (Dagger(A)*I -> Dagger(A)) = positive control (FAILS at base, HOLDS patched); probe_2 Req1.2 (Dagger(A)*Dagger(I) -> Dagger(A)); probe_3 Req2.1 (I*Dagger(A) -> Dagger(A)); probe_4 Req3.1/3.2 (Dagger(A)*B unevaluated Mul, Dagger(A)*Dagger(A)==Dagger(A)**2); probe_5 Req3.3 ((Dagger(A)*B)*I == Mul(inner,I), inner preserved, I not absorbed); probe_6 Req4.1-4.4 (I*A, A*I, I*I, I*scalar regressions); probe_7 Req4.5 (Dagger construction rules for scalar/ket/bra/power/double). All 7 HOLD on gold-patched tree. Positive control probe_1 and probe_3 both VIOLATED at base, confirming discriminating power. The requirements-conforming partial patch (weak.diff) is rejected by probe_3. Probe_5 was initially over-strict (checked literal Mul.args membership which Mul flattens) and was corrected to match the requirement's actual biconditional (final == Mul(inner,I)); re-ran and it HOLDS.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** The gold patch makes two changes that jointly implement the spec: (1) Dagger.__mul__ absorbs a right-hand IdentityOperator (covers R1.1; R1.2 works because Dagger(IdentityOperator) returns the IdentityOperator itself, so it hits the same isinstance check); (2) IdentityOperator.__mul__ extended to (Operator, Dagger) so I*Dagger(O) returns the Dagger (R2.1). R3.x negative/preservation cases and R4 pre-existing simplifications all hold. The requirements mirror the test_patch (test_dagger_mul, test_identity additions) exactly. Modeling boundary is correct: requirements target the changed multiplication behavior on both sides, not a narrow single-branch slice. R4.5 (dagger construction rules preserved) is an accurate no-regression claim consistent with the patch touching only __mul__.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** requirements.md describes the identity-absorption behavior for Dagger in behavioral EARS prose. All named identifiers (Dagger, IdentityOperator, Operator, dagger.py, operator.py) are public API and/or already present in the problem_statement, used for legitimate localization. No test function/class names (test_dagger_mul, test_identity), no file paths (tests/test_dagger.py), no parametrization ids, no verbatim test or gold-patch code, and no fix-invented identifiers appear. The gold introduces only a __mul__ override — nothing novel to leak. Closest call: R3.2 (Dagger*Dagger -> square) and R3.3 (Mul(Dagger,O)*I inner-product preservation) and R4's scalar/symbol cases go beyond the public problem_statement (which only shows Dagger(A)*Identity) and track the two hidden test functions assertion-by-assertion. However each is expressed as behavioral prose ('returns the square of the conjugate', 'preserve the already-formed product as the operand', 'leave the product unevaluated for a scalar or symbol') rather than quoted code, variable names, or enumerated test ids. Translating what tests verify into behavioral requirements is the sanctioned purpose of the spec; the defect would be transmitting the tests themselves, which does not happen here.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
