# P2 adversarial audit — django__django-12304

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
"""Req 1.1 (POSITIVE CONTROL): a class created via ChoicesMeta carries the
standard Django marker do_not_call_in_templates == True. HOLDS patched,
FAILS at base."""
import sys
from django.db.models import Choices, IntegerChoices, TextChoices

ok = True
for cls in (Choices, IntegerChoices, TextChoices):
    marker = getattr(cls, "do_not_call_in_templates", None)
    print(f"{cls.__name__}.do_not_call_in_templates = {marker!r}")
    if marker is not True:
        ok = False

# also on a user subclass
class Suit(IntegerChoices):
    DIAMOND = 1, "Diamond"
    SPADE = 2, "Spade"

m = getattr(Suit, "do_not_call_in_templates", None)
print(f"Suit.do_not_call_in_templates = {m!r}")
if m is not True:
    ok = False

sys.exit(0 if ok else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""Req 1.2/1.5: the template engine's Variable resolution leaves the enum
class intact (does NOT call it) and rendering succeeds without the
missing-'value'-argument TypeError. Simulates the exact template resolve path."""
import sys
import django
from django.conf import settings

if not settings.configured:
    settings.configure(
        DEBUG=True,
        TEMPLATES=[{"BACKEND": "django.template.backends.django.DjangoTemplates",
                    "DIRS": [], "APP_DIRS": False, "OPTIONS": {}}],
        USE_TZ=True,
    )
django.setup()

from django.db.models import IntegerChoices
from django.template import Context, Template

class Suit(IntegerChoices):
    DIAMOND = 1, "Diamond"
    SPADE = 2, "Spade"

# Reference the class by name; if the engine called it (no-arg) it would raise
# TypeError: __call__() missing 'value'. do_not_call_in_templates prevents that.
try:
    t = Template("{{ Suit.DIAMOND.label }}|{{ Suit.SPADE.value }}")
    out = t.render(Context({"Suit": Suit}))
except Exception as e:
    print(f"render raised: {type(e).__name__}: {e}")
    sys.exit(1)

print(f"rendered output = {out!r}")
sys.exit(0 if out == "Diamond|2" else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""Req 1.2 (mechanism-level): Variable('Suit')._resolve_lookup returns the
class OBJECT itself, not a no-arg call result. At base the resolver would try
to call the class and raise TypeError."""
import sys
import django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True, TEMPLATES=[], USE_TZ=True)
django.setup()

from django.db.models import TextChoices
from django.template.base import Variable
from django.template import Context

class Vehicle(TextChoices):
    CAR = "C", "Car"
    BIKE = "B", "Bike"

try:
    resolved = Variable("V").resolve(Context({"V": Vehicle}))
except Exception as e:
    print(f"resolve raised: {type(e).__name__}: {e}")
    sys.exit(1)

print(f"resolved is the class itself? {resolved is Vehicle}")
sys.exit(0 if resolved is Vehicle else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""Req 2.1/2.2/2.4: existing enum behavior preserved — label mapping,
class-level choices/labels/values/names properties incl. leading empty entry
for __empty__, and str(member) == str(value)."""
import sys
from django.db.models import IntegerChoices, TextChoices

ok = True

class Suit(IntegerChoices):
    DIAMOND = 1, "Diamond"
    SPADE = 2, "Spade"
    HEART = 3  # no label -> auto title-case "Heart"

# label mapping (2.1)
print("DIAMOND.label =", Suit.DIAMOND.label)
print("HEART.label =", Suit.HEART.label)
if Suit.DIAMOND.label != "Diamond" or Suit.HEART.label != "Heart":
    ok = False

# class props (2.2)
print("choices =", Suit.choices)
print("labels =", Suit.labels)
print("values =", Suit.values)
print("names =", Suit.names)
if Suit.values != [1, 2, 3] or Suit.labels != ["Diamond", "Spade", "Heart"]:
    ok = False
if Suit.names != ["DIAMOND", "SPADE", "HEART"]:
    ok = False
if Suit.choices != [(1, "Diamond"), (2, "Spade"), (3, "Heart")]:
    ok = False

# str(member) == str(value)  (2.4)
print("str(Suit.DIAMOND) =", str(Suit.DIAMOND))
if str(Suit.DIAMOND) != "1":
    ok = False

# __empty__ leading empty entry (2.2)
class Answer(IntegerChoices):
    NO = 0, "No"
    YES = 1, "Yes"
    __empty__ = "(Unknown)"

print("Answer.choices =", Answer.choices)
if Answer.choices[0] != (None, "(Unknown)"):
    ok = False

sys.exit(0 if ok else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""Req 2.3/2.5/2.6: __contains__ semantics (non-enum operand matches by value,
enum operand by containment), functional API + text value from name, and
duplicate-value error retained."""
import sys
from django.db.models import IntegerChoices, TextChoices

ok = True

class Suit(IntegerChoices):
    DIAMOND = 1, "Diamond"
    SPADE = 2, "Spade"

# 2.3 membership
print("1 in Suit:", 1 in Suit)
print("9 in Suit:", 9 in Suit)
print("Suit.DIAMOND in Suit:", Suit.DIAMOND in Suit)
if not (1 in Suit) or (9 in Suit) or not (Suit.DIAMOND in Suit):
    ok = False

# 2.5 functional API + text value from name
Vehicle = TextChoices("Vehicle", "CAR BIKE")
print("Vehicle.CAR.value =", Vehicle.CAR.value, "label =", Vehicle.CAR.label)
if Vehicle.CAR.value != "CAR" or Vehicle.CAR.label != "Car":
    ok = False
Suit2 = IntegerChoices("Suit2", "DIAMOND SPADE")
print("Suit2.DIAMOND.value =", Suit2.DIAMOND.value)
if Suit2.DIAMOND.value != 1:
    ok = False

# 2.6 duplicate value -> error
try:
    class Bad(IntegerChoices):
        A = 1, "A"
        B = 1, "B"
    print("duplicate NOT rejected")
    ok = False
except ValueError as e:
    print("duplicate rejected:", e)

sys.exit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Req 1.1 (POSITIVE CONTROL): a class created via ChoicesMeta carries the
standard Django marker do_not_call_in_templates == True. HOLDS patched,
FAILS at base."""
import sys
from django.db.models import Choices, IntegerChoices, TextChoices

ok = True
for cls in (Choices, IntegerChoices, TextChoices):
    marker = getattr(cls, "do_not_call_in_templates", None)
    print(f"{cls.__name__}.do_not_call_in_templates = {marker!r}")
    if marker is not True:
        ok = False

# also on a user subclass
class Suit(IntegerChoices):
    DIAMOND = 1, "Diamond"
    SPADE = 2, "Spade"

m = getattr(Suit, "do_not_call_in_templates", None)
print(f"Suit.do_not_call_in_templates = {m!r}")
if m is not True:
    ok = False

sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

5 probes covering all criteria. Probe1 (Req1.1, POSITIVE CONTROL): do_not_call_in_templates is True on Choices/IntegerChoices/TextChoices + user subclass — HOLDS patched, FAILS at base (=None). Probe2 (Req1.2/1.5): full template render of {{Suit.DIAMOND.label}}|{{Suit.SPADE.value}} == 'Diamond|2', no missing-'value'-arg TypeError. Probe3 (Req1.2 mechanism): Variable resolve returns the class object itself. Probe4 (Req2.1/2.2/2.4): label mapping incl auto title-case, choices/labels/values/names props, leading __empty__ entry, str(member)==str(value). Probe5 (Req2.3/2.5/2.6): __contains__ value/enum semantics, functional API + text-value-from-name, duplicate-value ValueError. All 5 HOLD on patched tree. Candidate naive.diff sets do_not_call_in_templates=False (a weak reading permits any assignment): probes 1,2,3 REJECT it (marker False -> template engine still calls the class; render='|', Variable.resolve raises) — suite discriminates the wrong fix. Positive control discriminates base(fail)->patched(hold).

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
"""Req 1.1 (POSITIVE CONTROL): a class created via ChoicesMeta carries the
standard Django marker do_not_call_in_templates == True. HOLDS patched,
FAILS at base."""
import sys
from django.db.models import Choices, IntegerChoices, TextChoices

ok = True
for cls in (Choices, IntegerChoices, TextChoices):
    marker = getattr(cls, "do_not_call_in_templates", None)
    print(f"{cls.__name__}.do_not_call_in_templates = {marker!r}")
    if marker is not True:
        ok = False

# also on a user subclass
class Suit(IntegerChoices):
    DIAMOND = 1, "Diamond"
    SPADE = 2, "Spade"

m = getattr(Suit, "do_not_call_in_templates", None)
print(f"Suit.do_not_call_in_templates = {m!r}")
if m is not True:
    ok = False

sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

5 probes covering all criteria. Probe1 (Req1.1, POSITIVE CONTROL): do_not_call_in_templates is True on Choices/IntegerChoices/TextChoices + user subclass — HOLDS patched, FAILS at base (=None). Probe2 (Req1.2/1.5): full template render of {{Suit.DIAMOND.label}}|{{Suit.SPADE.value}} == 'Diamond|2', no missing-'value'-arg TypeError. Probe3 (Req1.2 mechanism): Variable resolve returns the class object itself. Probe4 (Req2.1/2.2/2.4): label mapping incl auto title-case, choices/labels/values/names props, leading __empty__ entry, str(member)==str(value). Probe5 (Req2.3/2.5/2.6): __contains__ value/enum semantics, functional API + text-value-from-name, duplicate-value ValueError. All 5 HOLD on patched tree. Candidate naive.diff sets do_not_call_in_templates=False (a weak reading permits any assignment): probes 1,2,3 REJECT it (marker False -> template engine still calls the class; render='|', Variable.resolve raises) — suite discriminates the wrong fix. Positive control discriminates base(fail)->patched(hold).

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Requirements correctly pin the changed observable behavior (do_not_call_in_templates marker enabling template use) rather than a narrow slice. Requirement 2's preservation clauses correctly reflect that the patch adds nothing that alters enum semantics. Probed live in instance image: gold HOLDS, base VIOLATED.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The gold edit (cls.do_not_call_in_templates = True) and the callable-class template mechanism are already fully disclosed in the public problem_statement, which even names the exact marker; the requirements are actually more discreet, referring to 'the standard Django marker' rather than quoting the identifier. The hidden test (test_templates: Suit.DIAMOND.label/.value -> 'Diamond|1') is nowhere reconstructed — no test name/path, no 'Suit'/'DIAMOND', no 'Diamond|1' literal, no Context/Template import. Requirement 1 translates behavior generically. Requirement 2's preservation list does parallel the PASS_TO_PASS set (integerchoices/textchoices, containment, str, functional API, empty-label, duplicate-value, bool/UUID/timezone-unsupported), but these are genuine documented Django enum behaviors a regression-preservation requirement must localize; no test ids, quoted code, or fix-invented identifiers are transmitted. Behavioral translation, not test transmission.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
