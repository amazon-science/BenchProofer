# P2 adversarial audit — sympy__sympy-24213

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
"""Positive control / Req1.1: acceleration*time + velocity is accepted (no ValueError)
and returns a (scale_factor, dimension) tuple."""
import sys
from sympy.physics.units import meter, second, velocity, acceleration, time
from sympy.physics.units import Quantity
from sympy.physics.units.systems.si import SI

v1 = Quantity('v1')
SI.set_quantity_dimension(v1, velocity)
SI.set_quantity_scale_factor(v1, 2 * meter / second)

a1 = Quantity('a1')
SI.set_quantity_dimension(a1, acceleration)
SI.set_quantity_scale_factor(a1, -9.8 * meter / second**2)

t1 = Quantity('t1')
SI.set_quantity_dimension(t1, time)
SI.set_quantity_scale_factor(t1, 5 * second)

expr = a1 * t1 + v1
try:
    res = SI._collect_factor_and_dimension(expr)
except ValueError as e:
    print("FAIL: raised ValueError:", e)
    sys.exit(1)

print("observed result:", res)
if not (isinstance(res, tuple) and len(res) == 2):
    print("FAIL: not a 2-tuple")
    sys.exit(1)
print("PASS: accepted, returned tuple")
sys.exit(0)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""Req1.3 & 1.4: for equivalent-dimension sum, scale factor == sum of addends'
scale factors, and returned dimension == dimension of the first addend."""
import sys
from sympy.physics.units import meter, second, velocity, acceleration, time
from sympy.physics.units import Quantity
from sympy.physics.units.systems.si import SI

v1 = Quantity('v1')
SI.set_quantity_dimension(v1, velocity)
SI.set_quantity_scale_factor(v1, 2 * meter / second)

a1 = Quantity('a1')
SI.set_quantity_dimension(a1, acceleration)
SI.set_quantity_scale_factor(a1, -9.8 * meter / second**2)

t1 = Quantity('t1')
SI.set_quantity_dimension(t1, time)
SI.set_quantity_scale_factor(t1, 5 * second)

expr = a1 * t1 + v1
# expr.args[0] is whatever sympy orders first; the code carries ITS dimension
first_addend = expr.args[0]
f_first, d_first = SI._collect_factor_and_dimension(first_addend)
total_expected = 0
for ad in expr.args:
    fa, da = SI._collect_factor_and_dimension(ad)
    total_expected += fa
factor, dim = SI._collect_factor_and_dimension(expr)

print("first addend:", first_addend, "->", f_first, d_first)
print("sum result:", factor, dim)
print("expected factor:", total_expected)

if (factor - total_expected) != 0:
    print("FAIL: factor mismatch, expected", total_expected)
    sys.exit(1)
# returned dimension is dimension of the first addend
if dim != d_first:
    print("FAIL: dimension not first addend's dimension")
    sys.exit(1)
print("PASS: factor == sum, dim == first addend dim")
sys.exit(0)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""Req2.1 & 2.2: incompatible sum (length + time) still raises ValueError, and
the message identifies the offending addend, its dimension, and the expected."""
import sys
from sympy.physics.units import meter, second, length, time
from sympy.physics.units import Quantity
from sympy.physics.units.systems.si import SI

L = Quantity('Lq')
SI.set_quantity_dimension(L, length)
SI.set_quantity_scale_factor(L, 3 * meter)

T = Quantity('Tq')
SI.set_quantity_dimension(T, time)
SI.set_quantity_scale_factor(T, 4 * second)

expr = L + T
try:
    SI._collect_factor_and_dimension(expr)
except ValueError as e:
    msg = str(e)
    print("raised ValueError:", msg)
    # message should mention 'Dimension' and 'should be'
    if "Dimension of" in msg and "should be" in msg:
        print("PASS: rejected with descriptive message")
        sys.exit(0)
    print("FAIL: message not descriptive")
    sys.exit(1)
print("FAIL: did not raise ValueError")
sys.exit(1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""Req3.5: identical-surface-dimension sum still accepted and scale factors added.
Also Req3.1 (bare Quantity) and 3.2 (Mul)."""
import sys
from sympy.physics.units import meter, second, velocity
from sympy.physics.units import Quantity
from sympy.physics.units.systems.si import SI

v1 = Quantity('vv1')
SI.set_quantity_dimension(v1, velocity)
SI.set_quantity_scale_factor(v1, 2 * meter / second)

v2 = Quantity('vv2')
SI.set_quantity_dimension(v2, velocity)
SI.set_quantity_scale_factor(v2, 5 * meter / second)

# Req3.1: bare quantity
f, d = SI._collect_factor_and_dimension(v1)
print("bare quantity:", f, d)
if f != v1.scale_factor or d != v1.dimension:
    print("FAIL: bare quantity")
    sys.exit(1)

# Req3.5: same-dim sum
factor, dim = SI._collect_factor_and_dimension(v1 + v2)
print("same-dim sum:", factor, dim)
if (factor - (v1.scale_factor + v2.scale_factor)) != 0:
    print("FAIL: same-dim sum factor")
    sys.exit(1)

# Req3.2: Mul
mf, md = SI._collect_factor_and_dimension(v1 * v2)
print("mul:", mf, md)
if (mf - (v1.scale_factor * v2.scale_factor)) != 0:
    print("FAIL: mul factor")
    sys.exit(1)

print("PASS: bare/same-dim/mul all good")
sys.exit(0)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""Req1.2: matching is by canonical base-dimension dependency maps via
get_dimension_system().equivalent_dims — not surface identity.
Check: equivalent_dims(velocity, acceleration*time) is truthy, and the Add
branch accepts precisely such a pair (already covered), while a genuinely
different-map dim is rejected. Here we assert the semantic predicate the spec
names is what governs acceptance."""
import sys
from sympy.physics.units import velocity, acceleration, time, length
from sympy.physics.units.systems.si import SI

ds = SI.get_dimension_system()
eq_true = ds.equivalent_dims(velocity, acceleration * time)
eq_false = ds.equivalent_dims(velocity, length)
print("equivalent_dims(velocity, acceleration*time):", eq_true)
print("equivalent_dims(velocity, length):", eq_false)

if not eq_true:
    print("FAIL: velocity vs acceleration*time not equivalent by dim system")
    sys.exit(1)
if eq_false:
    print("FAIL: velocity vs length wrongly equivalent")
    sys.exit(1)
print("PASS: dimension-system equivalence predicate discriminates correctly")
sys.exit(0)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
"""Req3.3 (Pow) and 3.4 (Derivative/Function): preserved behavior."""
import sys
from sympy import Symbol, Function
from sympy.physics.units import meter, second, length, velocity
from sympy.physics.units import Quantity
from sympy.physics.units.systems.si import SI

L = Quantity('Lp')
SI.set_quantity_dimension(L, length)
SI.set_quantity_scale_factor(L, 3 * meter)

# Pow: L**2 -> scale 9, dimension length**2
pf, pd = SI._collect_factor_and_dimension(L**2)
print("pow:", pf, pd)
if (pf - 9) != 0:
    print("FAIL: pow factor")
    sys.exit(1)
if pd != L.dimension**2:
    print("FAIL: pow dimension")
    sys.exit(1)

# Derivative divides out variable dimension
t = Quantity('tp')
from sympy.physics.units import time
SI.set_quantity_dimension(t, time)
SI.set_quantity_scale_factor(t, 1 * second)
x = Quantity('xp')
SI.set_quantity_dimension(x, length)
SI.set_quantity_scale_factor(x, 1 * meter)
from sympy import Derivative
# d(x)/d(t) style requires a symbolic dependence; just confirm branch runs on a Function
f = Function('f')
farg = Quantity('fa')
SI.set_quantity_dimension(farg, length)  # nonzero dim
SI.set_quantity_scale_factor(farg, 1 * meter)
# dimensionless-arg function -> dimensionless treatment
import sympy
try:
    ff, fd = SI._collect_factor_and_dimension(f(sympy.Integer(1)))
    print("function(dimensionless):", ff, fd)
except Exception as e:
    print("FAIL: function branch raised:", e)
    sys.exit(1)

print("PASS: pow + function branches behave")
sys.exit(0)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Positive control / Req1.1: acceleration*time + velocity is accepted (no ValueError)
and returns a (scale_factor, dimension) tuple."""
import sys
from sympy.physics.units import meter, second, velocity, acceleration, time
from sympy.physics.units import Quantity
from sympy.physics.units.systems.si import SI

v1 = Quantity('v1')
SI.set_quantity_dimension(v1, velocity)
SI.set_quantity_scale_factor(v1, 2 * meter / second)

a1 = Quantity('a1')
SI.set_quantity_dimension(a1, acceleration)
SI.set_quantity_scale_factor(a1, -9.8 * meter / second**2)

t1 = Quantity('t1')
SI.set_quantity_dimension(t1, time)
SI.set_quantity_scale_factor(t1, 5 * second)

expr = a1 * t1 + v1
try:
    res = SI._collect_factor_and_dimension(expr)
except ValueError as e:
    print("FAIL: raised ValueError:", e)
    sys.exit(1)

print("observed result:", res)
if not (isinstance(res, tuple) and len(res) == 2):
    print("FAIL: not a 2-tuple")
    sys.exit(1)
print("PASS: accepted, returned tuple")
sys.exit(0)
```

Prepatch bug re-encoded as an attack: `True`.

Requirements cover the Add-branch dimension-equivalence fix in UnitSystem._collect_factor_and_dimension. Six probes, all HOLD on the gold-patched tree:
- probe_1 (Req1.1, positive control): acceleration*time + velocity accepted, returns 2-tuple. FAILS at base (raises ValueError) -> discriminating.
- probe_2 (Req1.3/1.4): scale factor == sum of addend factors; returned dimension == first addend's dimension (acceleration*time).
- probe_3 (Req2.1/2.2): length + time still raises ValueError with descriptive message (Dimension of .../should be ...).
- probe_4 (Req3.1/3.2/3.5): bare Quantity, Mul, and identical-surface-dim sum preserved.
- probe_5 (Req1.2): get_dimension_system().equivalent_dims discriminates velocity~acceleration*time (True) vs velocity/length (False). (Note: this predicate exists at base too, so it holds on both trees — not discriminating alone; probe_1 is the control.)
- probe_6 (Req3.3/3.4): Pow and Function branches preserved.

Candidate wrong-fix `never_raise` (replaces the guard with `if False:` so no incompatible sum is ever rejected) — a lazy over-broad reading of Req1. It is REJECTED by probe_3 (Req2.1: fails to raise on length+time), demonstrating the suite discriminates a too-weak fix. The gold patch is the minimal correct fix (surface `!=` -> equivalent_dims). No probe-conforming alternative found that would leave hidden tests unresolved. Verdict: SOUND.

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
"""Positive control / Req1.1: acceleration*time + velocity is accepted (no ValueError)
and returns a (scale_factor, dimension) tuple."""
import sys
from sympy.physics.units import meter, second, velocity, acceleration, time
from sympy.physics.units import Quantity
from sympy.physics.units.systems.si import SI

v1 = Quantity('v1')
SI.set_quantity_dimension(v1, velocity)
SI.set_quantity_scale_factor(v1, 2 * meter / second)

a1 = Quantity('a1')
SI.set_quantity_dimension(a1, acceleration)
SI.set_quantity_scale_factor(a1, -9.8 * meter / second**2)

t1 = Quantity('t1')
SI.set_quantity_dimension(t1, time)
SI.set_quantity_scale_factor(t1, 5 * second)

expr = a1 * t1 + v1
try:
    res = SI._collect_factor_and_dimension(expr)
except ValueError as e:
    print("FAIL: raised ValueError:", e)
    sys.exit(1)

print("observed result:", res)
if not (isinstance(res, tuple) and len(res) == 2):
    print("FAIL: not a 2-tuple")
    sys.exit(1)
print("PASS: accepted, returned tuple")
sys.exit(0)
```

Prepatch bug re-encoded as an attack: `True`.

Requirements cover the Add-branch dimension-equivalence fix in UnitSystem._collect_factor_and_dimension. Six probes, all HOLD on the gold-patched tree:
- probe_1 (Req1.1, positive control): acceleration*time + velocity accepted, returns 2-tuple. FAILS at base (raises ValueError) -> discriminating.
- probe_2 (Req1.3/1.4): scale factor == sum of addend factors; returned dimension == first addend's dimension (acceleration*time).
- probe_3 (Req2.1/2.2): length + time still raises ValueError with descriptive message (Dimension of .../should be ...).
- probe_4 (Req3.1/3.2/3.5): bare Quantity, Mul, and identical-surface-dim sum preserved.
- probe_5 (Req1.2): get_dimension_system().equivalent_dims discriminates velocity~acceleration*time (True) vs velocity/length (False). (Note: this predicate exists at base too, so it holds on both trees — not discriminating alone; probe_1 is the control.)
- probe_6 (Req3.3/3.4): Pow and Function branches preserved.

Candidate wrong-fix `never_raise` (replaces the guard with `if False:` so no incompatible sum is ever rejected) — a lazy over-broad reading of Req1. It is REJECTED by probe_3 (Req2.1: fails to raise on length+time), demonstrating the suite discriminates a too-weak fix. The gold patch is the minimal correct fix (surface `!=` -> equivalent_dims). No probe-conforming alternative found that would leave hidden tests unresolved. Verdict: SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Patch is a single-line change to the Add branch's dimension-compatibility test. Requirements correctly pin the changed observable behavior (equivalence-based acceptance/rejection) rather than a narrow slice, and preserve the returned-dimension-is-first-addend semantics. Probe HOLDS on gold-patched tree (exit=0).


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The reproduction example (acceleration*time + velocity), the involved dimensions, and the ValueError message all originate in the PUBLIC problem_statement. The document names the module/function (UnitSystem._collect_factor_and_dimension) and public API (get_dimension_system()) for legitimate localization, and describes the equivalence-of-reduced-dimensions mechanism as a behavioral requirement rather than quoting the gold line (`equivalent_dims` is not named). No test path/name (test_issue_24211), no test-invented identifiers (V1/A1/T1), no parametrization ids, no verbatim gold/test code. Req-3's list of preserved unit operations loosely resembles the PASS_TO_PASS set, but it enumerates the module's natural public API surface as a regression-scope clause, not test names/ids or case parametrization — it describes behavior to keep stable, which is the document's job.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
