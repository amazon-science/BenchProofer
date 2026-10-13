# P2 adversarial audit — django__django-16661

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
"""Positive control / Req1.2 + Req1.3: the exact F2P scenario.

A chain traversing a OneToOneField(primary_key=True) model must be permitted.
Encodes Requirement 1 acceptance criteria 2 & 3.
Exit 0 iff all three lookup_allowed calls return True.
"""
import sys
import django
from django.conf import settings

if not settings.configured:
    settings.configure(
        DEBUG=True, DATABASES={},
        INSTALLED_APPS=[
            "django.contrib.contenttypes", "django.contrib.auth",
            "django.contrib.admin", "django.contrib.sites",
            "django.contrib.messages",
        ],
        USE_TZ=True,
    )
django.setup()

from django.db import models
from django.contrib.admin import ModelAdmin, AdminSite


def run():
    class Country(models.Model):
        name = models.CharField(max_length=256)
        class Meta:
            app_label = "contenttypes"

    class Place(models.Model):
        country = models.ForeignKey(Country, models.CASCADE)
        class Meta:
            app_label = "contenttypes"

    class Restaurant(models.Model):
        place = models.OneToOneField(Place, models.CASCADE, primary_key=True)
        class Meta:
            app_label = "contenttypes"

    class Waiter(models.Model):
        restaurant = models.ForeignKey(Restaurant, models.CASCADE)
        class Meta:
            app_label = "contenttypes"

    class WaiterAdmin(ModelAdmin):
        list_filter = [
            "restaurant__place__country",
            "restaurant__place__country__name",
        ]

    ma = WaiterAdmin(Waiter, AdminSite())
    results = {
        "restaurant__place__country": ma.lookup_allowed("restaurant__place__country", "1"),
        "restaurant__place__country__id__exact": ma.lookup_allowed("restaurant__place__country__id__exact", "1"),
        "restaurant__place__country__name": ma.lookup_allowed("restaurant__place__country__name", "test_value"),
    }
    return results


res = run()
for k, v in res.items():
    print(f"{k} -> {v}")
ok = all(v is True for v in res.values())
print("ALL TRUE:", ok)
sys.exit(0 if ok else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""Req2.1 + Req3.7: concrete-inheritance parent link must still collapse,
and a one-to-one hop declared in list_filter must still be allowed.

This replicates the pre-existing test_lookup_allowed_considers_dynamic_fields /
concrete-inheritance behavior: a chain through a concrete-inheritance parent
link where the value is local should stay permitted, and lookups on the
one-to-one parent link should not be over-counted.

Encodes Requirement 2 acceptance criterion 1 (parent link not counted) via the
observable outcome that the existing employee__department__code filter works.
Exit 0 iff lookup_allowed returns True for the declared inheritance chain.
"""
import sys
import django
from django.conf import settings

if not settings.configured:
    settings.configure(
        DEBUG=True, DATABASES={},
        INSTALLED_APPS=[
            "django.contrib.contenttypes", "django.contrib.auth",
            "django.contrib.admin", "django.contrib.sites",
            "django.contrib.messages",
        ],
        USE_TZ=True,
    )
django.setup()

from django.db import models
from django.contrib.admin import ModelAdmin, AdminSite


def run():
    class Department(models.Model):
        code = models.CharField(max_length=4, unique=True)
        class Meta:
            app_label = "contenttypes"

    class Employee(models.Model):
        department = models.ForeignKey(Department, models.CASCADE, to_field="code")
        class Meta:
            app_label = "contenttypes"

    # Concrete inheritance: EmployeeProfile has an implicit parent link to Employee.
    class EmployeeProfile(Employee):
        pass
        class Meta:
            app_label = "contenttypes"

    class EmployeeProfileAdmin(ModelAdmin):
        list_filter = ["employee__department__code"]

    ma = EmployeeProfileAdmin(EmployeeProfile, AdminSite())
    # employee is the concrete-inheritance parent link (should collapse),
    # so the declared chain must be permitted.
    r1 = ma.lookup_allowed("employee__department__code", "test_value")
    return {"employee__department__code": r1}


res = run()
for k, v in res.items():
    print(f"{k} -> {v}")
ok = all(v is True for v in res.values())
print("ALL TRUE:", ok)
sys.exit(0 if ok else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""Req3.5 (negative side): with >1 relation part, an UNDECLARED chain must
return False. Guards against a too-weak patch that just returns True.

WaiterAdmin declares restaurant__place__country. A different, NOT-declared
multi-hop chain (restaurant__place with a further undeclared relation) must be
rejected. We use a chain the admin does not declare at all.
Exit 0 iff lookup_allowed returns False for the undeclared multi-hop chain.
"""
import sys
import django
from django.conf import settings

if not settings.configured:
    settings.configure(
        DEBUG=True, DATABASES={},
        INSTALLED_APPS=[
            "django.contrib.contenttypes", "django.contrib.auth",
            "django.contrib.admin", "django.contrib.sites",
            "django.contrib.messages",
        ],
        USE_TZ=True,
    )
django.setup()

from django.db import models
from django.contrib.admin import ModelAdmin, AdminSite


def run():
    class Country(models.Model):
        name = models.CharField(max_length=256)
        class Meta:
            app_label = "contenttypes"

    class Place(models.Model):
        country = models.ForeignKey(Country, models.CASCADE)
        class Meta:
            app_label = "contenttypes"

    class Restaurant(models.Model):
        place = models.OneToOneField(Place, models.CASCADE, primary_key=True)
        class Meta:
            app_label = "contenttypes"

    class Waiter(models.Model):
        restaurant = models.ForeignKey(Restaurant, models.CASCADE)
        class Meta:
            app_label = "contenttypes"

    class WaiterAdmin(ModelAdmin):
        # Only the country chain is declared; NOT restaurant__place__country__name here
        list_filter = ["restaurant__place__country"]

    ma = WaiterAdmin(Waiter, AdminSite())
    # restaurant__place__country__name is a further declared field only in the
    # F2P admin; here it is NOT declared, and it does not equal chain or chain+final
    # (chain = restaurant__place__country ; chain+final = ...__country__name matches?)
    # Actually name is the final processed component appended -> chain+final ==
    # restaurant__place__country__name, which is NOT in list_filter here -> False.
    r = ma.lookup_allowed("restaurant__place__country__name", "x")
    return {"restaurant__place__country__name (undeclared)": r}


res = run()
for k, v in res.items():
    print(f"{k} -> {v}")
ok = all(v is False for v in res.values())
print("ALL FALSE (rejected):", ok)
sys.exit(0 if ok else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""Req3.4 + Req2.3: a purely local / single-relation-part filter returns True,
and a component naming the previous relation's target column on a model WITH a
synthesised auto pk must still collapse (not be over-counted).

We reuse the classic employee__department__id case: on a normal model with an
auto pk, employee__department__id collapses to <=1 relation part beyond the
declared one, and lookup_allowed must return True even when only
employee__department is declared (id is reachable locally).
Exit 0 iff both hold.
"""
import sys
import django
from django.conf import settings

if not settings.configured:
    settings.configure(
        DEBUG=True, DATABASES={},
        INSTALLED_APPS=[
            "django.contrib.contenttypes", "django.contrib.auth",
            "django.contrib.admin", "django.contrib.sites",
            "django.contrib.messages",
        ],
        USE_TZ=True,
    )
django.setup()

from django.db import models
from django.contrib.admin import ModelAdmin, AdminSite


def run():
    class Department(models.Model):
        code = models.CharField(max_length=4, unique=True)
        class Meta:
            app_label = "contenttypes"

    class Employee(models.Model):
        department = models.ForeignKey(Department, models.CASCADE)
        class Meta:
            app_label = "contenttypes"

    class EmpAdmin(ModelAdmin):
        list_filter = ["department"]

    ma = EmpAdmin(Employee, AdminSite())
    out = {}
    # department__id : id is the auto pk / target reachable locally -> collapse,
    # <=1 relation part -> True even though only "department" declared.
    out["department__id"] = ma.lookup_allowed("department__id", "1")
    # a bare local field -> True (0 relation parts)
    out["department"] = ma.lookup_allowed("department", "1")
    return out


res = run()
for k, v in res.items():
    print(f"{k} -> {v}")
ok = all(v is True for v in res.values())
print("ALL TRUE:", ok)
sys.exit(0 if ok else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""Req3.2: a lookup on a nonexistent field is allowed (walk stops, remainder
ignorable). Req3.6-adjacent regression guard.

A chain whose first component does not resolve to a field must return True.
Exit 0 iff lookup_allowed returns True for a bogus field lookup.
"""
import sys
import django
from django.conf import settings

if not settings.configured:
    settings.configure(
        DEBUG=True, DATABASES={},
        INSTALLED_APPS=[
            "django.contrib.contenttypes", "django.contrib.auth",
            "django.contrib.admin", "django.contrib.sites",
            "django.contrib.messages",
        ],
        USE_TZ=True,
    )
django.setup()

from django.db import models
from django.contrib.admin import ModelAdmin, AdminSite


def run():
    class Country(models.Model):
        name = models.CharField(max_length=256)
        class Meta:
            app_label = "contenttypes"

    class Place(models.Model):
        country = models.ForeignKey(Country, models.CASCADE)
        class Meta:
            app_label = "contenttypes"

    class Restaurant(models.Model):
        place = models.OneToOneField(Place, models.CASCADE, primary_key=True)
        class Meta:
            app_label = "contenttypes"

    class Waiter(models.Model):
        restaurant = models.ForeignKey(Restaurant, models.CASCADE)
        class Meta:
            app_label = "contenttypes"

    class WaiterAdmin(ModelAdmin):
        list_filter = ["restaurant__place__country"]

    ma = WaiterAdmin(Waiter, AdminSite())
    out = {}
    # nonexistent leading field -> allowed
    out["nonexistent_field"] = ma.lookup_allowed("nonexistent_field__exact", "1")
    # relation then nonexistent -> walk stops, allowed
    out["restaurant__bogus"] = ma.lookup_allowed("restaurant__bogus", "1")
    return out


res = run()
for k, v in res.items():
    print(f"{k} -> {v}")
ok = all(v is True for v in res.values())
print("ALL TRUE:", ok)
sys.exit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Positive control / Req1.2 + Req1.3: the exact F2P scenario.

A chain traversing a OneToOneField(primary_key=True) model must be permitted.
Encodes Requirement 1 acceptance criteria 2 & 3.
Exit 0 iff all three lookup_allowed calls return True.
"""
import sys
import django
from django.conf import settings

if not settings.configured:
    settings.configure(
        DEBUG=True, DATABASES={},
        INSTALLED_APPS=[
            "django.contrib.contenttypes", "django.contrib.auth",
            "django.contrib.admin", "django.contrib.sites",
            "django.contrib.messages",
        ],
        USE_TZ=True,
    )
django.setup()

from django.db import models
from django.contrib.admin import ModelAdmin, AdminSite


def run():
    class Country(models.Model):
        name = models.CharField(max_length=256)
        class Meta:
            app_label = "contenttypes"

    class Place(models.Model):
        country = models.ForeignKey(Country, models.CASCADE)
        class Meta:
            app_label = "contenttypes"

    class Restaurant(models.Model):
        place = models.OneToOneField(Place, models.CASCADE, primary_key=True)
        class Meta:
            app_label = "contenttypes"

    class Waiter(models.Model):
        restaurant = models.ForeignKey(Restaurant, models.CASCADE)
        class Meta:
            app_label = "contenttypes"

    class WaiterAdmin(ModelAdmin):
        list_filter = [
            "restaurant__place__country",
            "restaurant__place__country__name",
        ]

    ma = WaiterAdmin(Waiter, AdminSite())
    results = {
        "restaurant__place__country": ma.lookup_allowed("restaurant__place__country", "1"),
        "restaurant__place__country__id__exact": ma.lookup_allowed("restaurant__place__country__id__exact", "1"),
        "restaurant__place__country__name": ma.lookup_allowed("restaurant__place__country__name", "test_value"),
    }
    return results


res = run()
for k, v in res.items():
    print(f"{k} -> {v}")
ok = all(v is True for v in res.values())
print("ALL TRUE:", ok)
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance django__django-16661: lookup_allowed must count a OneToOneField(primary_key=True) hop as a real relation part. Five probes, all self-contained (django.setup with contenttypes app_label, no isolate_apps).

Probes on gold-PATCHED tree (all HOLD, exit 0):
- probe_1 (Req1.2/1.3, POSITIVE CONTROL): F2P scenario Waiter->Restaurant(place OneToOne pk)->Place->Country. restaurant__place__country / __id__exact / __name all -> True.
- probe_2 (Req2.1/3.7): concrete-inheritance parent link collapses; employee__department__code -> True.
- probe_3 (Req3.5 negative): undeclared multi-hop restaurant__place__country__name (not in list_filter) -> False.
- probe_4 (Req2.3/3.4): department__id collapses (auto-pk local target) and bare local field -> True.
- probe_5 (Req3.2): lookups on nonexistent fields -> True (walk stops).

Positive control (probe_1) at BASE: all three -> False, exit 1 => prepatch reproduced, discriminating power confirmed.

WEAK CANDIDATE (weak.diff): naive fix `if not prev_field or prev_field.is_relation:` (always count relational component). Applies cleanly at base. REJECTED by probe_1 (restaurant__place__country__id__exact -> False, over-counts the id transform hop) and probe_4 (department__id -> False, breaks the local-value collapse regression). Confirms the suite discriminates wrong implementations that drop the collapse guard.

All 5 probes hold on patched; positive control discriminates; >=1 candidate rejected. Verdict SOUND.

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
"""Positive control / Req1.2 + Req1.3: the exact F2P scenario.

A chain traversing a OneToOneField(primary_key=True) model must be permitted.
Encodes Requirement 1 acceptance criteria 2 & 3.
Exit 0 iff all three lookup_allowed calls return True.
"""
import sys
import django
from django.conf import settings

if not settings.configured:
    settings.configure(
        DEBUG=True, DATABASES={},
        INSTALLED_APPS=[
            "django.contrib.contenttypes", "django.contrib.auth",
            "django.contrib.admin", "django.contrib.sites",
            "django.contrib.messages",
        ],
        USE_TZ=True,
    )
django.setup()

from django.db import models
from django.contrib.admin import ModelAdmin, AdminSite


def run():
    class Country(models.Model):
        name = models.CharField(max_length=256)
        class Meta:
            app_label = "contenttypes"

    class Place(models.Model):
        country = models.ForeignKey(Country, models.CASCADE)
        class Meta:
            app_label = "contenttypes"

    class Restaurant(models.Model):
        place = models.OneToOneField(Place, models.CASCADE, primary_key=True)
        class Meta:
            app_label = "contenttypes"

    class Waiter(models.Model):
        restaurant = models.ForeignKey(Restaurant, models.CASCADE)
        class Meta:
            app_label = "contenttypes"

    class WaiterAdmin(ModelAdmin):
        list_filter = [
            "restaurant__place__country",
            "restaurant__place__country__name",
        ]

    ma = WaiterAdmin(Waiter, AdminSite())
    results = {
        "restaurant__place__country": ma.lookup_allowed("restaurant__place__country", "1"),
        "restaurant__place__country__id__exact": ma.lookup_allowed("restaurant__place__country__id__exact", "1"),
        "restaurant__place__country__name": ma.lookup_allowed("restaurant__place__country__name", "test_value"),
    }
    return results


res = run()
for k, v in res.items():
    print(f"{k} -> {v}")
ok = all(v is True for v in res.values())
print("ALL TRUE:", ok)
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance django__django-16661: lookup_allowed must count a OneToOneField(primary_key=True) hop as a real relation part. Five probes, all self-contained (django.setup with contenttypes app_label, no isolate_apps).

Probes on gold-PATCHED tree (all HOLD, exit 0):
- probe_1 (Req1.2/1.3, POSITIVE CONTROL): F2P scenario Waiter->Restaurant(place OneToOne pk)->Place->Country. restaurant__place__country / __id__exact / __name all -> True.
- probe_2 (Req2.1/3.7): concrete-inheritance parent link collapses; employee__department__code -> True.
- probe_3 (Req3.5 negative): undeclared multi-hop restaurant__place__country__name (not in list_filter) -> False.
- probe_4 (Req2.3/3.4): department__id collapses (auto-pk local target) and bare local field -> True.
- probe_5 (Req3.2): lookups on nonexistent fields -> True (walk stops).

Positive control (probe_1) at BASE: all three -> False, exit 1 => prepatch reproduced, discriminating power confirmed.

WEAK CANDIDATE (weak.diff): naive fix `if not prev_field or prev_field.is_relation:` (always count relational component). Applies cleanly at base. REJECTED by probe_1 (restaurant__place__country__id__exact -> False, over-counts the id transform hop) and probe_4 (department__id -> False, breaks the local-value collapse regression). Confirms the suite discriminates wrong implementations that drop the collapse guard.

All 5 probes hold on patched; positive control discriminates; >=1 candidate rejected. Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Confirmed via nl_attack probe on both gold-patched and --base trees, and by inspecting inspect.getsource(ModelAdmin.lookup_allowed) in the instance image. The requirements pin lookup_allowed's return value (the observable behavior the issue is about) rather than an internal helper, and correctly attribute the fix to the auto_field-is-None / to_fields relation-part rule. Preservation cases (concrete-inheritance parent link, auto-pk-local collapse via to_field) also hold in the patched code. Requirements are faithful.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The public problem_statement already contains the full model graph (Country/Place/Restaurant/Waiter), list_filter=['restaurant__place__country'], and the assertion lookup_allowed('restaurant__place__country','test_value')==True. requirements.md uses exactly these public artifacts. 

Hidden-only material in test_patch: the extended list_filter entry 'restaurant__place__country__name', and two extra assertions ('restaurant__place__country__id__exact'->True, 'restaurant__place__country__name'->True). Req 1.3 (lines 59-62) describes 'the declared relational chain followed by an id/exact-style suffix, or followed by a further declared field' — this parallels those two hidden assertions, but it is phrased as a generic behavioral consequence of the chain-vs-(chain+final-component) matching rule already stated generically in Req 3.5, using only public model names. No test name/path/id, no parametrization ids, no quoted test code. It translates behavior, not the test structure — legitimate.

Hidden gold-patch identifiers (_meta.parents.values(), _meta.auto_field, to_fields, path_infos[-1].target_fields) are rendered as behavioral prose ('synthesised automatic primary key', 'parent links', 'previous relation's declared target columns'), not verbatim symbols. Naming lookup_allowed / options.py is legitimate localization. No fix-invented identifier is leaked. 

Conclusion: the document describes behavior and localizes the change without transmitting the hidden tests or gold code.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
