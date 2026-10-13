# P2 adversarial audit — django__django-12325

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
"""Positive control (R2.1, R3.2/R3.3): a subclass with an extra OneToOneField
to the parent, relying on auto-created parent link, SHALL construct without
ImproperlyConfigured and check() SHALL report no errors."""
import django
from django.conf import settings
if not settings.configured:
    settings.configure(INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
                        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}})
django.setup()
from django.db import models

class Place(models.Model):
    class Meta:
        app_label = 'auth'

class ParkingLot(Place):
    other_place = models.OneToOneField(Place, models.CASCADE, related_name='other_parking')
    class Meta:
        app_label = 'auth'

errs = ParkingLot.check()
print("check() =", errs)
assert errs == [], "expected no errors, got %r" % errs
print("OK: model constructed and check() empty")
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""R2.2 / R1.3: explicit parent_link=True field plus an ordinary extra
OneToOneField to the same parent -> constructs and check() empty; parent link
is the explicitly designated field."""
import django
from django.conf import settings
if not settings.configured:
    settings.configure(INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
                        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}})
django.setup()
from django.db import models

class Place(models.Model):
    class Meta:
        app_label = 'auth'

class ParkingLot(Place):
    place = models.OneToOneField(Place, models.CASCADE, parent_link=True, primary_key=True)
    other_place = models.OneToOneField(Place, models.CASCADE, related_name='other_parking')
    class Meta:
        app_label = 'auth'

errs = ParkingLot.check()
print("check() =", errs)
assert errs == [], "expected no errors, got %r" % errs
pk = ParkingLot._meta.pk
print("pk field =", pk.name)
assert pk.name == 'place', "parent link should be 'place', got %r" % pk.name
print("OK")
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""R1.2/R1.3/R3: order-independence. Extra ordinary OneToOneField declared
BEFORE the explicit parent_link field must NOT displace the parent link.
The parent link (place) must still be selected as pk, and no error raised."""
import django
from django.conf import settings
if not settings.configured:
    settings.configure(INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
                        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}})
django.setup()
from django.db import models

class Place(models.Model):
    class Meta:
        app_label = 'auth'

class ParkingLot(Place):
    other_place = models.OneToOneField(Place, models.CASCADE, related_name='other_parking')
    place = models.OneToOneField(Place, models.CASCADE, parent_link=True, primary_key=True)
    class Meta:
        app_label = 'auth'

errs = ParkingLot.check()
print("check() =", errs)
pk = ParkingLot._meta.pk
print("pk field =", pk.name)
assert errs == [], "expected no errors, got %r" % errs
assert pk.name == 'place', "parent link should be 'place', got %r" % pk.name
print("OK")
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""R4.1/R4.2: a genuine reverse-name clash between an extra OneToOneField and
the auto-created parent link must be reported via model checks (E304 accessor
clash + E305 query-name clash for each direction), NOT abort construction."""
import django
from django.conf import settings
if not settings.configured:
    settings.configure(INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
                        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}})
django.setup()
from django.db import models

class Parent(models.Model):
    class Meta:
        app_label = 'auth'

class Child(Parent):
    other_parent = models.OneToOneField(Parent, models.CASCADE)
    class Meta:
        app_label = 'auth'

errs = Child.check()
ids = sorted(e.id for e in errs)
print("error ids =", ids)
assert ids == ['fields.E304', 'fields.E304', 'fields.E305', 'fields.E305'], "got %r" % ids
for e in errs:
    assert e.hint and 'related_name' in e.hint, "missing related_name hint: %r" % e
print("OK: 4 clash errors with related_name hints")
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""R5.1/R5.2: an auto-created parent link SHALL be marked parent_link=True,
and its deconstruct() representation SHALL reflect parent_link alongside
primary_key."""
import django
from django.conf import settings
if not settings.configured:
    settings.configure(INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
                        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}})
django.setup()
from django.db import models

class Place(models.Model):
    class Meta:
        app_label = 'auth'

class Restaurant(Place):
    class Meta:
        app_label = 'auth'

link = Restaurant._meta.parents[Place]
print("parent link field =", link.name, "auto_created=", link.auto_created)
assert link.remote_field.parent_link is True, "parent link not marked parent_link"
name, path, args, kwargs = link.deconstruct()
print("deconstruct kwargs =", kwargs)
assert kwargs.get('parent_link') is True, "parent_link not in deconstruct kwargs: %r" % kwargs
assert kwargs.get('primary_key') is True, "primary_key not in deconstruct kwargs: %r" % kwargs
print("OK: auto-created parent link marked and serialized")
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
"""R5.3 (regression): a plain model with no parent link still receives an
auto-created integer primary key named 'id'."""
import django
from django.conf import settings
if not settings.configured:
    settings.configure(INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
                        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}})
django.setup()
from django.db import models

class Plain(models.Model):
    class Meta:
        app_label = 'auth'

pk = Plain._meta.pk
print("pk =", pk.name, type(pk).__name__, "auto_created=", pk.auto_created)
assert pk.name == 'id', "expected auto id pk, got %r" % pk.name
assert isinstance(pk, models.AutoField), "expected AutoField"
assert pk.auto_created is True
print("OK: auto-created integer pk preserved")
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Positive control (R2.1, R3.2/R3.3): a subclass with an extra OneToOneField
to the parent, relying on auto-created parent link, SHALL construct without
ImproperlyConfigured and check() SHALL report no errors."""
import django
from django.conf import settings
if not settings.configured:
    settings.configure(INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
                        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}})
django.setup()
from django.db import models

class Place(models.Model):
    class Meta:
        app_label = 'auth'

class ParkingLot(Place):
    other_place = models.OneToOneField(Place, models.CASCADE, related_name='other_parking')
    class Meta:
        app_label = 'auth'

errs = ParkingLot.check()
print("check() =", errs)
assert errs == [], "expected no errors, got %r" % errs
print("OK: model constructed and check() empty")
```

Prepatch bug re-encoded as an attack: `True`.

6 probes, all HOLD on gold-patched tree.

Probe->requirement mapping (all HOLD patched):
- probe_1 (R2.1/R3.2/R3.3, POSITIVE CONTROL): subclass with extra OneToOneField relying on auto parent link -> constructs, check()==[]. FAILS at base with ImproperlyConfigured 'Add parent_link=True to auth.ParkingLot.other_place.' HOLDS patched. Discriminates.
- probe_2 (R2.2/R1.3): explicit parent_link=True + extra one-to-one, check()==[] and pk=='place'. (Note: holds at base too since explicit parent_link declared first — not a discriminator alone, but pins correct selection.)
- probe_3 (R1.2/R1.3/R3): order-independence — extra ordinary O2O declared BEFORE the parent_link field; pk still 'place', check()==[].
- probe_4 (R4.1/R4.2): genuine reverse-name clash reported as exactly E304,E304,E305,E305 with related_name hints, not aborting. FAILS at base (ImproperlyConfigured).
- probe_5 (R5.1/R5.2): auto-created parent link marked parent_link=True and deconstruct() reflects parent_link+primary_key.
- probe_6 (R5.3 regression): plain model still gets auto-created AutoField 'id' pk.

Candidate wrong-fix REJECTED: guard_removal_only (weak.diff) removes only the ImproperlyConfigured guard in options.py but keeps the buggy last-write-wins collection in base.py. Under it probe_1/2/3/5/6 pass, but probe_4 is REJECTED (got [] instead of the 4 clash errors): because the non-parent-link field still overwrites the genuine parent link and is promoted to pk, the reverse-name clash between the auto parent link and other_parent is never detected. This shows the suite discriminates a plausible partial fix that satisfies R2/R3 but violates R4 — confirming the base.py change is genuinely required. This candidate is NOT too-weak (it fails the probe suite).

Environment note: the instance image has no 'invalid_models_tests' app on the path, so probes use app_label='auth' with in-process model classes instead of isolate_apps; behavior is equivalent for these checks.

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
"""Positive control (R2.1, R3.2/R3.3): a subclass with an extra OneToOneField
to the parent, relying on auto-created parent link, SHALL construct without
ImproperlyConfigured and check() SHALL report no errors."""
import django
from django.conf import settings
if not settings.configured:
    settings.configure(INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
                        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}})
django.setup()
from django.db import models

class Place(models.Model):
    class Meta:
        app_label = 'auth'

class ParkingLot(Place):
    other_place = models.OneToOneField(Place, models.CASCADE, related_name='other_parking')
    class Meta:
        app_label = 'auth'

errs = ParkingLot.check()
print("check() =", errs)
assert errs == [], "expected no errors, got %r" % errs
print("OK: model constructed and check() empty")
```

Prepatch bug re-encoded as an attack: `True`.

6 probes, all HOLD on gold-patched tree.

Probe->requirement mapping (all HOLD patched):
- probe_1 (R2.1/R3.2/R3.3, POSITIVE CONTROL): subclass with extra OneToOneField relying on auto parent link -> constructs, check()==[]. FAILS at base with ImproperlyConfigured 'Add parent_link=True to auth.ParkingLot.other_place.' HOLDS patched. Discriminates.
- probe_2 (R2.2/R1.3): explicit parent_link=True + extra one-to-one, check()==[] and pk=='place'. (Note: holds at base too since explicit parent_link declared first — not a discriminator alone, but pins correct selection.)
- probe_3 (R1.2/R1.3/R3): order-independence — extra ordinary O2O declared BEFORE the parent_link field; pk still 'place', check()==[].
- probe_4 (R4.1/R4.2): genuine reverse-name clash reported as exactly E304,E304,E305,E305 with related_name hints, not aborting. FAILS at base (ImproperlyConfigured).
- probe_5 (R5.1/R5.2): auto-created parent link marked parent_link=True and deconstruct() reflects parent_link+primary_key.
- probe_6 (R5.3 regression): plain model still gets auto-created AutoField 'id' pk.

Candidate wrong-fix REJECTED: guard_removal_only (weak.diff) removes only the ImproperlyConfigured guard in options.py but keeps the buggy last-write-wins collection in base.py. Under it probe_1/2/3/5/6 pass, but probe_4 is REJECTED (got [] instead of the 4 clash errors): because the non-parent-link field still overwrites the genuine parent link and is promoted to pk, the reverse-name clash between the auto parent link and other_parent is never detected. This shows the suite discriminates a plausible partial fix that satisfies R2/R3 but violates R4 — confirming the base.py change is genuinely required. This candidate is NOT too-weak (it fails the probe suite).

Environment note: the instance image has no 'invalid_models_tests' app on the path, so probes use app_label='auth' with in-process model classes instead of isolate_apps; behavior is equivalent for these checks.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** The modeling boundary is correct: requirements pin the changed OBSERVABLE behavior (order-independent parent-link selection, no ImproperlyConfigured on valid MTI, clashes routed to model checks) rather than a narrow slice. Both code sites of the gold patch (base.py __new__ collection filter, options.py _prepare guard removal) are covered by R1 and R3 respectively. Minor note: R5.2 (state render reflects parent_link) is technically pre-existing behavior (base_commit already deconstructs parent_link=True — it corresponds to the test_state.py render assertion added in the test_patch which passes on both trees), but the patched code still satisfies it, so it is not unfaithful — it does not mandate absent behavior or forbid present behavior. No invented behavior; no forbidden behavior; no wrong boundary.

Counterexample / evidence:

```
None found. Ran probes on both gold-patched and base_commit trees; requirements match patched behavior on every scenario including the two declaration orders from the issue, the auto-created-parent-link case, and the reverse-name-clash case.
```


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The requirements localize the change to django/db/models/base.py (ModelBase.__new__) and Options._prepare in options.py — legitimate localization, and base.py/ModelBase.__new__ even appear in the public hints_text PR sketch. All cited symbols (ImproperlyConfigured, the 'Add parent_link=True to ...' message, the order-dependence bug, Document/Picking-style multiple OneToOne scenario) come straight from the public problem_statement. No hidden-test artifacts are transmitted: no test function names (test_onetoone_with_parent_model, test_onetoone_with_explicit_parent_link_parent_model, test_clash_parent_link), no test file paths, no model names from the tests (Place/ParkingLot/Parent/Child), no error-code identifiers (fields.E304/E305), no field names (parent_ptr/other_parent), and no quoted test or gold code. Borderline items — Req 4's reverse-accessor/reverse-query-name clash enumeration (maps to test_clash_parent_link) and Req 5.2's auto-created-parent-link state representation (maps to the migrations/test_state.py gold change adding parent_link=True) — are behavioral translations of standard Django check/state behavior, with error kinds and hint text paraphrased rather than quoted. This is describing what the fix must do, not reconstructing the tests. Verdict: NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
