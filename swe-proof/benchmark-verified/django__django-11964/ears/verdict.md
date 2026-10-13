# P2 adversarial audit — django__django-11964

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
# R1.1/R1.2/R1.4/R1.6 positive control:
# str(TextChoices member) == underlying string value exactly (incl empty),
# and NOT "<ClassName>.<MEMBER>". Holds patched, fails at base.
from django.db.models import TextChoices

class Vehicle(TextChoices):
    CAR = 'C', 'Carriage'
    TRUCK = 'T'
    JET_SKI = 'J', 'Jet Ski'

class WithEmpty(TextChoices):
    __empty__ = 'empty label'
    A = '', 'AnEmpty'   # empty-string value member
    B = 'b', 'Bee'

ok = True
for m, expected in [(Vehicle.CAR, 'C'), (Vehicle.TRUCK, 'T'), (Vehicle.JET_SKI, 'J'),
                    (WithEmpty.A, ''), (WithEmpty.B, 'b')]:
    s = str(m)
    print(f"str({m!r}) = {s!r} ; expected {expected!r}")
    if s != expected:
        ok = False
    if '.' in s and s.startswith(type(m).__name__ + '.'):
        print("  -> leaked ClassName.MEMBER form")
        ok = False

import sys
sys.exit(0 if ok else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
# R1.3: str(IntegerChoices member) == decimal textual form of underlying int,
# including negatives. Not "<ClassName>.<MEMBER>".
from django.db.models import IntegerChoices

class Suit(IntegerChoices):
    DIAMOND = 1, 'Diamond'
    SPADE = 2, 'Spade'
    NEG = -5, 'Negative'
    ZERO = 0, 'Zero'

ok = True
for m, expected in [(Suit.DIAMOND, '1'), (Suit.SPADE, '2'), (Suit.NEG, '-5'), (Suit.ZERO, '0')]:
    s = str(m)
    print(f"str({m!r}) = {s!r} ; expected {expected!r}")
    if s != expected:
        ok = False

import sys
sys.exit(0 if ok else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
# R1.5 + R1.7: str result invariant to label and to presence of __empty__,
# and defined on the shared base (applies uniformly). Compare two enums:
# one with labels+__empty__, one without, same underlying values -> same str.
from django.db.models import TextChoices, IntegerChoices, Choices

class TA(TextChoices):
    X = 'x', 'Ex Label'
class TB(TextChoices):
    __empty__ = 'nothing'
    X = 'x'   # auto label
ok = True
print("TA.X", repr(str(TA.X)), "TB.X", repr(str(TB.X)))
if str(TA.X) != 'x' or str(TB.X) != 'x':
    ok = False

class IA(IntegerChoices):
    N = 7, 'Seven'
class IB(IntegerChoices):
    __empty__ = 'none'
    N = 7
print("IA.N", repr(str(IA.N)), "IB.N", repr(str(IB.N)))
if str(IA.N) != '7' or str(IB.N) != '7':
    ok = False

# R1.7: __str__ defined on the shared Choices base
if '__str__' not in Choices.__dict__:
    print("__str__ not defined on Choices base")
    ok = False
else:
    print("__str__ defined on Choices base:", Choices.__dict__['__str__'])

import sys
sys.exit(0 if ok else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
# R2 regression: value type preserved, label preserved/auto-derived, repr unchanged.
from django.db.models import TextChoices, IntegerChoices

class Suit(IntegerChoices):
    DIAMOND = 1, 'Diamond'
    JACK_OF_SPADES = 11   # auto label
class Vehicle(TextChoices):
    CAR = 'C', 'Carriage'
    JET_SKI = 'J'   # auto label

ok = True
# R2.1 value + type
print("Suit.DIAMOND.value", repr(Suit.DIAMOND.value), type(Suit.DIAMOND.value).__name__)
if Suit.DIAMOND.value != 1 or not isinstance(Suit.DIAMOND.value, int):
    ok = False
if Vehicle.CAR.value != 'C' or not isinstance(Vehicle.CAR.value, str):
    ok = False
# R2.2/R2.4 labels
print("labels", Suit.DIAMOND.label, repr(Suit.JACK_OF_SPADES.label), repr(Vehicle.JET_SKI.label))
if Suit.DIAMOND.label != 'Diamond': ok = False
if Suit.JACK_OF_SPADES.label != 'Jack Of Spades': ok = False
if Vehicle.JET_SKI.label != 'Jet Ski': ok = False
# R2.3 repr unchanged: <ClassName.MEMBER: value>
r = repr(Suit.DIAMOND)
print("repr(Suit.DIAMOND)", r)
if r != '<Suit.DIAMOND: 1>': ok = False
rv = repr(Vehicle.CAR)
print("repr(Vehicle.CAR)", rv)
if rv != "<Vehicle.CAR: 'C'>": ok = False

import sys
sys.exit(0 if ok else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
# R3 regression: class-level metadata unchanged (choices, values, labels, names,
# __empty__ leading entry, membership testing, lookup).
from django.db.models import TextChoices, IntegerChoices

class Suit(IntegerChoices):
    __empty__ = '(Unknown)'
    DIAMOND = 1, 'Diamond'
    SPADE = 2, 'Spade'

ok = True
print("choices", Suit.choices)
print("values", Suit.values)
print("labels", Suit.labels)
print("names", Suit.names)
# R3.3 leading empty entry
if Suit.choices[0] != (None, '(Unknown)'): ok = False
if Suit.values[0] is not None: ok = False
if Suit.labels[0] != '(Unknown)': ok = False
if Suit.names[0] != '__empty__': ok = False
# R3.1/3.2 alignment
if Suit.choices != [(None,'(Unknown)'),(1,'Diamond'),(2,'Spade')]: ok = False
if Suit.values != [None,1,2]: ok = False
if Suit.labels != ['(Unknown)','Diamond','Spade']: ok = False
if Suit.names != ['__empty__','DIAMOND','SPADE']: ok = False
# R3.4 membership
print("1 in Suit", 1 in Suit, "; 99 in Suit", 99 in Suit)
if not (1 in Suit): ok = False
if 99 in Suit: ok = False
# R3.5 lookup by name and value
if Suit['DIAMOND'] is not Suit.DIAMOND: ok = False
if Suit(1) is not Suit.DIAMOND: ok = False
print("lookup ok")

import sys
sys.exit(0 if ok else 1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
# R4 regression: functional construction, TypeError for non-int, ValueError for dup,
# and custom (non-int/str) base types still get non-None labels.
from django.db.models import TextChoices, IntegerChoices
import datetime, decimal

ok = True
# R4.1 functional form
Vehicle = TextChoices('Vehicle', 'CAR TRUCK JET_SKI')
print("text functional", Vehicle.choices)
if Vehicle.CAR.value != 'CAR' or Vehicle.JET_SKI.label != 'Jet Ski': ok = False
Nums = IntegerChoices('Nums', 'A B C')
print("int functional", Nums.choices)
if [n.value for n in Nums] != [1,2,3]: ok = False
if Nums.A.label != 'A': ok = False

# R4.2 TypeError: non-integer second positional argument to int()
try:
    class Bad(IntegerChoices):
        ONE = 1, 'X', 'Invalid'   # (1,'X') -> int(1,'X'); 'X' not interpretable as int
    print("no TypeError raised!"); ok = False
except TypeError as e:
    print("TypeError:", e)
    if 'cannot be interpreted as an integer' not in str(e):
        ok = False

# R4.3 ValueError dup value
try:
    class Dup(IntegerChoices):
        A = 1, 'a'
        B = 1, 'b'
    print("no ValueError raised!"); ok = False
except ValueError as e:
    print("ValueError:", e)

# R4.5 custom base type -> non-None labels
from django.db.models.enums import Choices
class Number(decimal.Decimal, Choices):
    E = decimal.Decimal('2.718'), 'Euler'
    PI = decimal.Decimal('3.14')
print("Number labels", Number.labels)
if None in Number.labels: ok = False

import sys
sys.exit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
# R1.1/R1.2/R1.4/R1.6 positive control:
# str(TextChoices member) == underlying string value exactly (incl empty),
# and NOT "<ClassName>.<MEMBER>". Holds patched, fails at base.
from django.db.models import TextChoices

class Vehicle(TextChoices):
    CAR = 'C', 'Carriage'
    TRUCK = 'T'
    JET_SKI = 'J', 'Jet Ski'

class WithEmpty(TextChoices):
    __empty__ = 'empty label'
    A = '', 'AnEmpty'   # empty-string value member
    B = 'b', 'Bee'

ok = True
for m, expected in [(Vehicle.CAR, 'C'), (Vehicle.TRUCK, 'T'), (Vehicle.JET_SKI, 'J'),
                    (WithEmpty.A, ''), (WithEmpty.B, 'b')]:
    s = str(m)
    print(f"str({m!r}) = {s!r} ; expected {expected!r}")
    if s != expected:
        ok = False
    if '.' in s and s.startswith(type(m).__name__ + '.'):
        print("  -> leaked ClassName.MEMBER form")
        ok = False

import sys
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance django__django-11964: gold patch adds Choices.__str__ returning str(self.value) on the shared base.

Probes (all HOLD on patched tree; runner re-derives):
- probe_1 (R1.1/1.2/1.4/1.6 + POSITIVE CONTROL): str(TextChoices member) == underlying string exactly incl empty '', and not '<Class>.<MEMBER>'. HOLDS patched, FAILS at base (base yields 'Vehicle.TRUCK' etc.) => discriminates.
- probe_2 (R1.3): str(IntegerChoices member) == decimal form incl negative/zero ('1','2','-5','0'). HOLDS patched.
- probe_3 (R1.5/R1.7): str invariant to label and to __empty__ presence; __str__ defined on shared Choices base. HOLDS patched.
- probe_4 (R2.1-2.4): value & type preserved, labels declared/auto-derived, repr unchanged '<Suit.DIAMOND: 1>'. HOLDS.
- probe_5 (R3.1-3.5): choices/values/labels/names aligned, leading (None,label) for __empty__, membership by raw value, lookup by name/value. HOLDS.
- probe_6 (R4.1-4.3,4.5): functional construction (int sequential / text name values, title-case labels); TypeError "'str' object cannot be interpreted as an integer" for ONE=1,'X','Invalid'; ValueError duplicate; custom decimal.Decimal base yields non-None labels. HOLDS.

Wrong-fix candidate (weak.diff): puts __str__ only on TextChoices (a weak reading of the spec that ignores R1.7's 'shared base' and R1.3's integer requirement). The suite REJECTS it: probe_2 fails (IntegerChoices still renders 'Suit.DIAMOND') and probe_3 fails (__str__ not on Choices base, IntegerChoices leaks name). Demonstrates discriminating power.

6/6 probes hold patched; positive control discriminates base vs patched; 1/1 weak candidate rejected. Verdict SOUND. (Note: meta.json G-PANEL-3 flags R4.4/R4.5 as test-derived leakage — that is a separate leakage gate, orthogonal to G-EQ spec-strength which is sound.)

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
# R1.1/R1.2/R1.4/R1.6 positive control:
# str(TextChoices member) == underlying string value exactly (incl empty),
# and NOT "<ClassName>.<MEMBER>". Holds patched, fails at base.
from django.db.models import TextChoices

class Vehicle(TextChoices):
    CAR = 'C', 'Carriage'
    TRUCK = 'T'
    JET_SKI = 'J', 'Jet Ski'

class WithEmpty(TextChoices):
    __empty__ = 'empty label'
    A = '', 'AnEmpty'   # empty-string value member
    B = 'b', 'Bee'

ok = True
for m, expected in [(Vehicle.CAR, 'C'), (Vehicle.TRUCK, 'T'), (Vehicle.JET_SKI, 'J'),
                    (WithEmpty.A, ''), (WithEmpty.B, 'b')]:
    s = str(m)
    print(f"str({m!r}) = {s!r} ; expected {expected!r}")
    if s != expected:
        ok = False
    if '.' in s and s.startswith(type(m).__name__ + '.'):
        print("  -> leaked ClassName.MEMBER form")
        ok = False

import sys
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance django__django-11964: gold patch adds Choices.__str__ returning str(self.value) on the shared base.

Probes (all HOLD on patched tree; runner re-derives):
- probe_1 (R1.1/1.2/1.4/1.6 + POSITIVE CONTROL): str(TextChoices member) == underlying string exactly incl empty '', and not '<Class>.<MEMBER>'. HOLDS patched, FAILS at base (base yields 'Vehicle.TRUCK' etc.) => discriminates.
- probe_2 (R1.3): str(IntegerChoices member) == decimal form incl negative/zero ('1','2','-5','0'). HOLDS patched.
- probe_3 (R1.5/R1.7): str invariant to label and to __empty__ presence; __str__ defined on shared Choices base. HOLDS patched.
- probe_4 (R2.1-2.4): value & type preserved, labels declared/auto-derived, repr unchanged '<Suit.DIAMOND: 1>'. HOLDS.
- probe_5 (R3.1-3.5): choices/values/labels/names aligned, leading (None,label) for __empty__, membership by raw value, lookup by name/value. HOLDS.
- probe_6 (R4.1-4.3,4.5): functional construction (int sequential / text name values, title-case labels); TypeError "'str' object cannot be interpreted as an integer" for ONE=1,'X','Invalid'; ValueError duplicate; custom decimal.Decimal base yields non-None labels. HOLDS.

Wrong-fix candidate (weak.diff): puts __str__ only on TextChoices (a weak reading of the spec that ignores R1.7's 'shared base' and R1.3's integer requirement). The suite REJECTS it: probe_2 fails (IntegerChoices still renders 'Suit.DIAMOND') and probe_3 fails (__str__ not on Choices base, IntegerChoices leaks name). Demonstrates discriminating power.

6/6 probes hold patched; positive control discriminates base vs patched; 1/1 weak candidate rejected. Verdict SOUND. (Note: meta.json G-PANEL-3 flags R4.4/R4.5 as test-derived leakage — that is a separate leakage gate, orthogonal to G-EQ spec-strength which is sound.)

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Patch adds only Choices.__str__ -> str(self.value). Probe on gold-patched tree: all assertions HOLD (exit 0), incl. bytes-backed Separator.FS -> "b'\\x1c'" consistent with str(value). Probe --base: str(Gender.MALE)=='Gender.MALE', confirming divergence. Requirements neither mandate absent behavior, forbid present behavior, nor pin the wrong boundary.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The requirements describe behavior only. The hidden test (test_str, iterating Gender/Suit/YearInSchool/Vehicle and asserting str(member)==str(member.value)) is translated into a behavioral requirement (Req 1) without naming any of the test enums, test function/class names (test_str, ChoicesTests), file path (tests/model_enums/tests.py), or parametrization. The gold edit is a one-line __str__ returning str(self.value); __str__ is a standard Python dunder, not a fix-invented identifier, and Req 1.7 legitimately localizes it to the shared Choices base (the changed module/class is public knowledge / legitimate localization). Requirements 2-4 restate PASS_TO_PASS invariants (repr form <Class.MEMBER: value>, choices/values/labels/names ordering, __empty__ leading (None,...) entry, functional API, duplicate-value ValueError, non-int TypeError, unsupported base type TypeError, non-int/str custom value types) — all these correspond to pre-existing documented/public Choices behavior, not to hidden-test-only content. The problem_statement already exposes the ClassName.MEMBER vs value discrepancy, TextChoices/IntegerChoices, str backing, and the 'first'/value semantics; nothing in the doc exceeds public + behavioral description. Enumerations like the empty-member and custom-type cases are described by behavior class, not mirrored as a parametrized case list of the specific test enums.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
