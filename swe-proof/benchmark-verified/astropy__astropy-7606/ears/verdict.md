# P2 adversarial audit — astropy__astropy-7606

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 5 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 5 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 5 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (5):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
"""Req 1.1 (positive control): UnrecognizedUnit == None must not raise and is falsey."""
import sys
import astropy.units as u

unit = u.Unit('asdf', parse_strict='silent')
print("type(unit)=", type(unit).__name__)
try:
    r = (unit == None)
except Exception as e:
    print("RAISED:", type(e).__name__, e)
    sys.exit(1)
print("unit == None ->", r)
if r:
    print("FAIL: expected falsey")
    sys.exit(1)
print("OK")
sys.exit(0)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""Req 1.2 & 1.3: UnrecognizedUnit != None is True; membership 'unit not in (None, u.m)'."""
import sys
import astropy.units as u

unit = u.Unit('asdf', parse_strict='silent')
try:
    ne = (unit != None)
    member = unit in (None, u.m)
except Exception as e:
    print("RAISED:", type(e).__name__, e)
    sys.exit(1)
print("unit != None ->", ne)
print("unit in (None, u.m) ->", member)
if ne is not True:
    print("FAIL: != None should be True")
    sys.exit(1)
if member:
    print("FAIL: should not be a member")
    sys.exit(1)
print("OK")
sys.exit(0)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""Req 2: UnrecognizedUnit equality semantics with interpretable operands.
== string name True; == same-name unrec True; != diff-name; == genuine unit False, != True;
is_equivalent agrees."""
import sys
import astropy.units as u

unit = u.Unit('asdf', parse_strict='silent')
same = u.Unit('asdf', parse_strict='silent')
other = u.Unit('qwer', parse_strict='silent')

checks = []
checks.append(("== 'asdf'", (unit == 'asdf'), True))
checks.append(("== same-name unrec", (unit == same), True))
checks.append(("== diff-name unrec", (unit == other), False))
checks.append(("== u.m", (unit == u.m), False))
checks.append(("!= u.m", (unit != u.m), True))
checks.append(("is_equivalent same", bool(unit.is_equivalent(same)), True))
checks.append(("is_equivalent diff", bool(unit.is_equivalent(other)), False))

ok = True
for name, got, exp in checks:
    print(f"{name}: got={got!r} expect={exp!r}")
    if bool(got) != bool(exp):
        ok = False
if not ok:
    print("FAIL")
    sys.exit(1)
print("OK")
sys.exit(0)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""Req 3: recognized UnitBase == None falsey, != None True, no raise; also arbitrary object."""
import sys
import astropy.units as u

try:
    eq = (u.m == None)
    ne = (u.m != None)
    eq_obj = (u.m == object())
except Exception as e:
    print("RAISED:", type(e).__name__, e)
    sys.exit(1)
print("u.m == None ->", eq)
print("u.m != None ->", ne)
print("u.m == object() ->", eq_obj)
if eq:
    print("FAIL: == None should be falsey")
    sys.exit(1)
if ne is not True:
    print("FAIL: != None should be True")
    sys.exit(1)
if eq_obj:
    print("FAIL: == object() should be falsey")
    sys.exit(1)
print("OK")
sys.exit(0)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""Req 4: preserved semantics for genuine units.
- same physical quantity == True; non-convertible == False
- ordering reflects scale; non-convertible ordering raises UnitsError
- == equivalent string True"""
import sys
import astropy.units as u
from astropy.units import UnitsError

ok = True
def chk(name, got, exp):
    global ok
    print(f"{name}: got={got!r} expect={exp!r}")
    if bool(got) != bool(exp):
        ok = False

chk("m == m", (u.m == u.m), True)
chk("m == s", (u.m == u.s), False)
chk("km > m", (u.km > u.m), True)
chk("m < km", (u.m < u.km), True)
chk("m == 'm'", (u.m == 'm'), True)

# non-convertible ordering raises
raised = False
try:
    _ = (u.m < u.s)
except UnitsError:
    raised = True
except Exception as e:
    print("ordering raised unexpected type:", type(e).__name__)
print("m < s raised UnitsError ->", raised)
if not raised:
    ok = False

if not ok:
    print("FAIL")
    sys.exit(1)
print("OK")
sys.exit(0)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Req 1.1 (positive control): UnrecognizedUnit == None must not raise and is falsey."""
import sys
import astropy.units as u

unit = u.Unit('asdf', parse_strict='silent')
print("type(unit)=", type(unit).__name__)
try:
    r = (unit == None)
except Exception as e:
    print("RAISED:", type(e).__name__, e)
    sys.exit(1)
print("unit == None ->", r)
if r:
    print("FAIL: expected falsey")
    sys.exit(1)
print("OK")
sys.exit(0)
```

Prepatch bug re-encoded as an attack: `True`.

Requirements cover the total-comparison contract for both UnitBase and UnrecognizedUnit __eq__/__ne__. 5 distinct probes, all HOLD on the gold-patched tree:
- probe_1 (Req 1.1, POSITIVE CONTROL): UnrecognizedUnit('asdf') == None does not raise and is falsey. HOLDS patched; at base raises TypeError('None is not a valid Unit') -> exit 1. Discriminates.
- probe_2 (Req 1.2/1.3): unit != None is True; `unit in (None, u.m)` is False, no raise. HOLDS patched; VIOLATED at base (TypeError).
- probe_3 (Req 2.1-2.4): == name-string True, == same-name unrec True, == diff-name unrec False, == u.m False, != u.m True, is_equivalent agrees. HOLDS.
- probe_4 (Req 3.1-3.3): u.m == None falsey, != None True, == object() falsey, no raise. HOLDS.
- probe_5 (Req 4.1-4.4): m==m True, m==s False, km>m/m<km ordering, m=='m' True, non-convertible ordering (m<s) raises UnitsError. HOLDS.

CANDIDATE PATCH (weak_only_unitbase): applies ONLY the UnitBase.__eq__ change (return NotImplemented) but leaves UnrecognizedUnit.__eq__ unguarded (the lazy partial fix a weak reading permits). Probe suite REJECTS it: probe_1 and probe_2 VIOLATED (candidate-patched) — UnrecognizedUnit == None still raises TypeError. This alternative would NOT resolve the hidden tests (which assert `unit == 'FOO'`, `unit != None`, `unit not in (None, u.m)` on an UnrecognizedUnit). Suite discriminates the wrong implementation.

Verdict SOUND: >=5 probes hold on patched, positive control discriminates base vs patched, and >=1 candidate rejected.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 5 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 5 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 5 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

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
"""Req 1.1 (positive control): UnrecognizedUnit == None must not raise and is falsey."""
import sys
import astropy.units as u

unit = u.Unit('asdf', parse_strict='silent')
print("type(unit)=", type(unit).__name__)
try:
    r = (unit == None)
except Exception as e:
    print("RAISED:", type(e).__name__, e)
    sys.exit(1)
print("unit == None ->", r)
if r:
    print("FAIL: expected falsey")
    sys.exit(1)
print("OK")
sys.exit(0)
```

Prepatch bug re-encoded as an attack: `True`.

Requirements cover the total-comparison contract for both UnitBase and UnrecognizedUnit __eq__/__ne__. 5 distinct probes, all HOLD on the gold-patched tree:
- probe_1 (Req 1.1, POSITIVE CONTROL): UnrecognizedUnit('asdf') == None does not raise and is falsey. HOLDS patched; at base raises TypeError('None is not a valid Unit') -> exit 1. Discriminates.
- probe_2 (Req 1.2/1.3): unit != None is True; `unit in (None, u.m)` is False, no raise. HOLDS patched; VIOLATED at base (TypeError).
- probe_3 (Req 2.1-2.4): == name-string True, == same-name unrec True, == diff-name unrec False, == u.m False, != u.m True, is_equivalent agrees. HOLDS.
- probe_4 (Req 3.1-3.3): u.m == None falsey, != None True, == object() falsey, no raise. HOLDS.
- probe_5 (Req 4.1-4.4): m==m True, m==s False, km>m/m<km ordering, m=='m' True, non-convertible ordering (m<s) raises UnitsError. HOLDS.

CANDIDATE PATCH (weak_only_unitbase): applies ONLY the UnitBase.__eq__ change (return NotImplemented) but leaves UnrecognizedUnit.__eq__ unguarded (the lazy partial fix a weak reading permits). Probe suite REJECTS it: probe_1 and probe_2 VIOLATED (candidate-patched) — UnrecognizedUnit == None still raises TypeError. This alternative would NOT resolve the hidden tests (which assert `unit == 'FOO'`, `unit != None`, `unit not in (None, u.m)` on an UnrecognizedUnit). Suite discriminates the wrong implementation.

Verdict SOUND: >=5 probes hold on patched, positive control discriminates base vs patched, and >=1 candidate rejected.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Probe HOLDS on gold-patched tree (exit 0, all 13 observations as required) and VIOLATED on base (TypeError: None is not a valid Unit), confirming the modeling boundary sits on the actual change. Requirement 3 correctly describes observable 'falsey' / 'True' outcomes; note the patch returns NotImplemented (not False) so Python falls back to identity comparison, which yields the same user-visible booleans the requirements state — no divergence. No behavior mandated that the code lacks; no present behavior forbidden; no invented behavior.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** requirements.md describes behavior derivable from the public problem_statement (UnrecognizedUnit == None raising TypeError) generalized to robust total equality/inequality. It names only public API surfaces (UnitBase, UnrecognizedUnit, astropy/units/core.py, Unit(other, parse_strict='silent')) — legitimate localization; core.py and the __eq__ snippet already appear in the public traceback. No test function names/paths (test_unknown_unit3), no parametrization ids, no quoted test/gold code, and no fix-invented identifiers (NotImplemented, type(self)) are transmitted. The four acceptance criteria loosely correspond to the four added asserts (== 'FOO', != u.m, != None, not in (None, u.m)) but are phrased as general behavioral requirements without quoting the literals ('FOO', (None, u.m)) or mirroring a parametrization — a behavioral translation, which is the intended purpose. Req 1.4/3.3's 'defer to Python's default object comparison' describes the NotImplemented mechanism behaviorally, not as leaked code. Membership Req 1.3 is a reasonable generalization of 'comparison must never raise against arbitrary operands', within the problem statement's scope.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
