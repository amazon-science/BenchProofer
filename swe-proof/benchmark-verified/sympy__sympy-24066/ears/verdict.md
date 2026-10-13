# P2 adversarial audit — sympy__sympy-24066

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 5 requirement probes hold on the patched tree; 2/2 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 5 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 5 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 2 alternative candidate patches, claimed to satisfy every cited requirement, and ran the same suite against them. The suite rejected all 2: a probe encoding a cited requirement fails under each of those, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (5):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
"""Positive control (R1.4, R2.3): exp of a dimensionless compound argument
(second/(ohm*farad)) is reported as Dimension(1). FAILS at base (reports raw
compound dim, not equal to Dimension(1))."""
import sys
from sympy import exp
from sympy.physics.units import second, ohm, farad
from sympy.physics.units.systems.si import SI
from sympy.physics.units.dimensions import Dimension

expr = exp(second / (ohm * farad))
factor, dim = SI._collect_factor_and_dimension(expr)
ds = SI.get_dimension_system()
print("dim =", dim)
print("is_dimensionless =", ds.is_dimensionless(dim))
print("== Dimension(1):", dim == Dimension(1))
ok = ds.is_dimensionless(dim) and dim == Dimension(1)
sys.exit(0 if ok else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""R2.1/R2.2: sum of a pure number and a function of a dimensionless argument
must NOT raise ValueError; dimension dimensionless; scale factor = number +
func(arg scale factor)."""
import sys
from sympy import exp
from sympy.physics.units import second, ohm, farad
from sympy.physics.units.systems.si import SI
from sympy.physics.units.dimensions import Dimension

expr = 100 + exp(second / (ohm * farad))
try:
    factor, dim = SI._collect_factor_and_dimension(expr)
except ValueError as e:
    print("RAISED ValueError:", e)
    sys.exit(1)
ds = SI.get_dimension_system()
# scale factor: exp arg reduces to scale factor 1 (second/(ohm*farad) all base SI => 1)
af, ad = SI._collect_factor_and_dimension(second / (ohm * farad))
expected = 100 + exp(af)
print("factor =", factor, "expected =", expected)
print("dim =", dim, "is_dimensionless =", ds.is_dimensionless(dim))
ok = ds.is_dimensionless(dim) and dim == Dimension(1) and factor == expected
sys.exit(0 if ok else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""R1.3 / R3.x: a function of a NON-dimensionless argument reports its
dimension UNCHANGED (not canonicalized to Dimension(1)). sin(meter) should
report dimension = length (canonical form). We check it is NOT dimensionless
and equals the length dimension."""
import sys
from sympy import sin
from sympy.physics.units import meter
from sympy.physics.units.systems.si import SI
from sympy.physics.units.dimensions import Dimension

expr = sin(meter)
factor, dim = SI._collect_factor_and_dimension(expr)
ds = SI.get_dimension_system()
_, length_dim = SI._collect_factor_and_dimension(meter)
print("dim =", dim, "length_dim =", length_dim)
print("is_dimensionless =", ds.is_dimensionless(dim))
# argument dimension is length; must be reported unchanged and NOT dimensionless
ok = (not ds.is_dimensionless(dim)) and dim == length_dim
sys.exit(0 if ok else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""R1.5: scale-factor component of a function application is the function
reapplied to the collected scale factors of its arguments. exp(2*second/second)
-> arg scale factor = 2, so factor == exp(2)."""
import sys
from sympy import exp
from sympy.physics.units import second
from sympy.physics.units.systems.si import SI

expr = exp(2 * second / second)
factor, dim = SI._collect_factor_and_dimension(expr)
print("factor =", factor)
ok = factor == exp(2)
print("expected exp(2):", exp(2), "ok:", ok)
sys.exit(0 if ok else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""R3 regression: other expression kinds unchanged.
- Quantity: speed_of_light returns its stored scale factor & dimension.
- Mul: meter*second dimension = length*time, factor = product.
- Pow: (meter)**2 dimension = length**2.
- Add mismatch: meter + second SHALL raise ValueError.
- R3.7: already-dimensionless function (exp of pure number) stays dimensionless.
"""
import sys
from sympy import exp
from sympy.physics.units import meter, second
from sympy.physics.units.systems.si import SI
from sympy.physics.units.dimensions import Dimension

ds = SI.get_dimension_system()
ok = True

# Mul
f, d = SI._collect_factor_and_dimension(meter * second)
_, dm = SI._collect_factor_and_dimension(meter)
_, dsc = SI._collect_factor_and_dimension(second)
print("Mul dim:", d, "expected:", dm*dsc)
ok = ok and d == dm*dsc

# Pow
f2, d2 = SI._collect_factor_and_dimension(meter**2)
print("Pow dim:", d2, "expected:", dm**2)
ok = ok and d2 == dm**2

# Add mismatch raises
raised = False
try:
    SI._collect_factor_and_dimension(meter + second)
except ValueError:
    raised = True
print("Add mismatch raised ValueError:", raised)
ok = ok and raised

# R3.7 already-dimensionless function stays dimensionless
f3, d3 = SI._collect_factor_and_dimension(exp(3))
print("exp(3) dim:", d3, "is_dimensionless:", ds.is_dimensionless(d3))
ok = ok and ds.is_dimensionless(d3) and d3 == Dimension(1)

sys.exit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Positive control (R1.4, R2.3): exp of a dimensionless compound argument
(second/(ohm*farad)) is reported as Dimension(1). FAILS at base (reports raw
compound dim, not equal to Dimension(1))."""
import sys
from sympy import exp
from sympy.physics.units import second, ohm, farad
from sympy.physics.units.systems.si import SI
from sympy.physics.units.dimensions import Dimension

expr = exp(second / (ohm * farad))
factor, dim = SI._collect_factor_and_dimension(expr)
ds = SI.get_dimension_system()
print("dim =", dim)
print("is_dimensionless =", ds.is_dimensionless(dim))
print("== Dimension(1):", dim == Dimension(1))
ok = ds.is_dimensionless(dim) and dim == Dimension(1)
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Requirements faithfully capture gold patch for sympy-24066 (_collect_factor_and_dimension Function branch: canonicalize dimensionless arg dims to Dimension(1) via get_dimension_system().is_dimensionless).

Probe results (patched / base):
- probe_1 (R1.4,R2.3 positive control): exp(second/(ohm*farad)) dim==Dimension(1) & is_dimensionless. HOLDS patched / VIOLATED base (base reports Dimension(time/(capacitance*impedance))). Discriminates.
- probe_2 (R2.1,R2.2): 100+exp(second/(ohm*farad)) no ValueError, dim==Dimension(1), factor==E+100. HOLDS patched / raises ValueError at base.
- probe_3 (R1.3): sin(meter) dim==length and NOT dimensionless (unchanged). HOLDS both trees (regression criterion).
- probe_4 (R1.5): exp(2*second/second) factor==exp(2). HOLDS both.
- probe_5 (R3.2/3.3/3.4/3.7): Mul,Pow dims correct; meter+second raises ValueError; exp(3) stays Dimension(1). HOLDS both.

Candidate wrong patches, both REJECTED by suite:
- candA (unconditionally set every arg dim to Dimension(1)): rejected by probe_3 — breaks R1.3, sin(meter) wrongly dimensionless.
- candB (only canonicalize when literally == Dimension(1)): rejected by probe_1 & probe_2 — fails the real compound-dimensionless bug (behaviorally equals base).

Suite has >=5 distinct probes, all hold on patched tree; positive control discriminates (holds patched, fails base); >=1 candidate exercised and >=2 rejected in both directions (over-strong and too-weak). Verdict SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 5 requirement probes hold on the patched tree; 2/2 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 5 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 5 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 2 alternative candidate patches, claimed to satisfy every cited requirement, and ran the same suite against them. The suite rejected all 2: a probe encoding a cited requirement fails under each of those, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (5):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

_The 5 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts, and on this backend both roles put it through the same derivation: every block below is a requirement probe run on the gold-patched tree, and the `machine verdict:` line each role publishes above reports BOTH that its probes hold there and how many candidate patches the probe suite rejected — so the two roles re-ran ONE probe suite and each recorded its own outcome for every probe in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `probe_1.py` → holds on the patched tree (good)

Attack 2 — `probe_2.py` → holds on the patched tree (good)

Attack 3 — `probe_3.py` → holds on the patched tree (good)

Attack 4 — `probe_4.py` → holds on the patched tree (good)

Attack 5 — `probe_5.py` → holds on the patched tree (good)

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Positive control (R1.4, R2.3): exp of a dimensionless compound argument
(second/(ohm*farad)) is reported as Dimension(1). FAILS at base (reports raw
compound dim, not equal to Dimension(1))."""
import sys
from sympy import exp
from sympy.physics.units import second, ohm, farad
from sympy.physics.units.systems.si import SI
from sympy.physics.units.dimensions import Dimension

expr = exp(second / (ohm * farad))
factor, dim = SI._collect_factor_and_dimension(expr)
ds = SI.get_dimension_system()
print("dim =", dim)
print("is_dimensionless =", ds.is_dimensionless(dim))
print("== Dimension(1):", dim == Dimension(1))
ok = ds.is_dimensionless(dim) and dim == Dimension(1)
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Requirements faithfully capture gold patch for sympy-24066 (_collect_factor_and_dimension Function branch: canonicalize dimensionless arg dims to Dimension(1) via get_dimension_system().is_dimensionless).

Probe results (patched / base):
- probe_1 (R1.4,R2.3 positive control): exp(second/(ohm*farad)) dim==Dimension(1) & is_dimensionless. HOLDS patched / VIOLATED base (base reports Dimension(time/(capacitance*impedance))). Discriminates.
- probe_2 (R2.1,R2.2): 100+exp(second/(ohm*farad)) no ValueError, dim==Dimension(1), factor==E+100. HOLDS patched / raises ValueError at base.
- probe_3 (R1.3): sin(meter) dim==length and NOT dimensionless (unchanged). HOLDS both trees (regression criterion).
- probe_4 (R1.5): exp(2*second/second) factor==exp(2). HOLDS both.
- probe_5 (R3.2/3.3/3.4/3.7): Mul,Pow dims correct; meter+second raises ValueError; exp(3) stays Dimension(1). HOLDS both.

Candidate wrong patches, both REJECTED by suite:
- candA (unconditionally set every arg dim to Dimension(1)): rejected by probe_3 — breaks R1.3, sin(meter) wrongly dimensionless.
- candB (only canonicalize when literally == Dimension(1)): rejected by probe_1 & probe_2 — fails the real compound-dimensionless bug (behaviorally equals base).

Suite has >=5 distinct probes, all hold on patched tree; positive control discriminates (holds patched, fails base); >=1 candidate exercised and >=2 rejected in both directions (over-strong and too-weak). Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Patch only edits the Function branch of _collect_factor_and_dimension, wrapping each arg dimension with `Dimension(1) if is_dimensionless(d[1]) else d[1]`. Requirements pin exactly this observable boundary (per-argument canonicalization keyed on get_dimension_system().is_dimensionless), not a narrow slice. Probe on gold-patched image passed all assertions; base issue reproduced by problem_statement.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** requirements.md describes the fix behaviorally: canonicalize a function application's dimensionless argument dimension to Dimension(1) so exp(dimensionless) combines additively. Every concrete detail it uses is already public in problem_statement: the 'time divided by product of impedance and capacitance' (= second/(ohm*farad)) example and its Dimension(time/(capacitance*impedance)) form appear verbatim in the ValueError of the repro; the exp-of-ratio, the numeric-plus-function sum, Dimension(1), and get_dimension_system().is_dimensionless are all in the problem_statement. The named identifiers (_collect_factor_and_dimension, unitsystem.py, is_dimensionless, Function/Mul/Pow/Add/Derivative/Dimension branches) are legitimate localization, not test content. No leak of test name (test_issue_24062), test path (test_quantities.py), parametrization ids, quoted test/gold code, or fix-invented identifiers. The Add-branch ValueError wording and the (1+E, Dimension(1)) semantics are behavioral descriptions, not reconstructions of the hidden test (which uses R/C/T quantities and 1+exp(expr), not enumerated in the doc).


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
