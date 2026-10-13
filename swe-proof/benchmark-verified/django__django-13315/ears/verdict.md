# P2 adversarial audit — django__django-13315

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

**Attacks re-run (7):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
"""Probe 1 (POSITIVE CONTROL) — Req 1.1: a candidate matching through >1
related row via a Q() constraint over a multi-valued relation appears EXACTLY
ONCE in the form field's queryset.
HOLDS on patched (dedup); FAILS at base (duplicate)."""
import django
from django.conf import settings
settings.configure(
    DEBUG=True,
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
    INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
    USE_TZ=False,
)
django.setup()

from django.db import models, connection
from django.db.models import Q
from django.forms.models import modelform_factory

APP = 'contenttypes'

class Tag(models.Model):
    name = models.CharField(max_length=50)
    class Meta:
        app_label = APP

class Person(models.Model):
    name = models.CharField(max_length=50)
    tags = models.ManyToManyField(Tag)
    class Meta:
        app_label = APP

class Report(models.Model):
    person = models.ForeignKey(
        Person, on_delete=models.CASCADE,
        limit_choices_to=Q(tags__name='x'))
    class Meta:
        app_label = APP

with connection.schema_editor() as se:
    se.create_model(Tag)
    se.create_model(Person)
    se.create_model(Report)

# p1 matches the constraint through TWO related rows (two tags named 'x')
p1 = Person.objects.create(name='p1')
t1 = Tag.objects.create(name='x')
t2 = Tag.objects.create(name='x')
p1.tags.add(t1, t2)
# p2 matches through zero rows (should be excluded)
Person.objects.create(name='p2')

Form = modelform_factory(Report, fields=['person'])
qs = Form().fields['person'].queryset
pks = list(qs.values_list('pk', flat=True))
print("person pks offered:", pks)

count_p1 = pks.count(p1.pk)
print("p1 appears", count_p1, "time(s)")
ok = (count_p1 == 1) and (p1.pk in pks)
print("PASS" if ok else "FAIL")
import sys
sys.exit(0 if ok else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""Probe 2 — Req 2.2 + 1.1: DICTIONARY constraint spanning a multi-valued
relation dedupes (candidate matching via 2 rows appears once, and only
matching candidates present)."""
import django
from django.conf import settings
settings.configure(DEBUG=True,
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
    INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'], USE_TZ=False)
django.setup()
from django.db import models, connection
from django.forms.models import modelform_factory
APP = 'contenttypes'
class Tag(models.Model):
    name = models.CharField(max_length=50)
    class Meta: app_label = APP
class Person(models.Model):
    name = models.CharField(max_length=50)
    tags = models.ManyToManyField(Tag)
    class Meta: app_label = APP
class Report(models.Model):
    person = models.ForeignKey(Person, on_delete=models.CASCADE,
        limit_choices_to={'tags__name': 'x'})   # DICT form
    class Meta: app_label = APP
with connection.schema_editor() as se:
    se.create_model(Tag); se.create_model(Person); se.create_model(Report)
p1 = Person.objects.create(name='p1')
p1.tags.add(Tag.objects.create(name='x'), Tag.objects.create(name='x'))
Person.objects.create(name='p2')  # no matching tag
qs = modelform_factory(Report, fields=['person'])().fields['person'].queryset
pks = list(qs.values_list('pk', flat=True))
print("offered:", pks)
ok = pks == [p1.pk]
print("PASS" if ok else "FAIL")
import sys; sys.exit(0 if ok else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""Probe 3 — Req 2.3 + 2.4: dict and equivalent Q constraint offer the SAME
set, AND for a ManyToManyField relation (2.4). Also multi-valued dedup on M2M."""
import django
from django.conf import settings
settings.configure(DEBUG=True,
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
    INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'], USE_TZ=False)
django.setup()
from django.db import models, connection
from django.db.models import Q
from django.forms.models import modelform_factory
APP = 'contenttypes'
class Tag(models.Model):
    name = models.CharField(max_length=50)
    class Meta: app_label = APP
class Person(models.Model):
    name = models.CharField(max_length=50)
    tags = models.ManyToManyField(Tag)
    class Meta: app_label = APP
# M2M field with dict-form limit_choices_to spanning Person.tags
class ReportDict(models.Model):
    people = models.ManyToManyField(Person, limit_choices_to={'tags__name': 'x'})
    class Meta: app_label = APP
class ReportQ(models.Model):
    people = models.ManyToManyField(Person, limit_choices_to=Q(tags__name='x'))
    class Meta: app_label = APP
with connection.schema_editor() as se:
    se.create_model(Tag); se.create_model(Person)
    se.create_model(ReportDict); se.create_model(ReportQ)
p1 = Person.objects.create(name='p1')
p1.tags.add(Tag.objects.create(name='x'), Tag.objects.create(name='x'))
Person.objects.create(name='p2')
qd = list(modelform_factory(ReportDict, fields=['people'])().fields['people'].queryset
          .values_list('pk', flat=True))
qq = list(modelform_factory(ReportQ, fields=['people'])().fields['people'].queryset
          .values_list('pk', flat=True))
print("dict M2M offered:", qd, "| Q M2M offered:", qq)
ok = qd == [p1.pk] and qq == [p1.pk] and qd == qq
print("PASS" if ok else "FAIL")
import sys; sys.exit(0 if ok else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""Probe 4 — Req 3.2/3.3 + 4.4: a field with NO limit_choices_to keeps its
FULL queryset with ORDER/identity preserved (no dedup side effects, all rows).
Also Req 3: empty constraint leaves queryset unchanged."""
import django
from django.conf import settings
settings.configure(DEBUG=True,
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
    INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'], USE_TZ=False)
django.setup()
from django.db import models, connection
from django.forms.models import modelform_factory
APP = 'contenttypes'
class Person(models.Model):
    name = models.CharField(max_length=50)
    class Meta:
        app_label = APP
        ordering = ['-name']
class Report(models.Model):
    person = models.ForeignKey(Person, on_delete=models.CASCADE)  # NO limit_choices_to
    class Meta: app_label = APP
with connection.schema_editor() as se:
    se.create_model(Person); se.create_model(Report)
for n in ['a', 'b', 'c']:
    Person.objects.create(name=n)
qs = modelform_factory(Report, fields=['person'])().fields['person'].queryset
got = list(qs.values_list('name', flat=True))
expected = list(Person.objects.all().values_list('name', flat=True))
print("offered:", got, "| expected full ordered:", expected)
ok = got == expected == ['c', 'b', 'a']
print("PASS" if ok else "FAIL")
import sys; sys.exit(0 if ok else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""Probe 5 — Req 4.1/4.2: a CALLABLE limit_choices_to is invoked (exactly once
per field construction) and its resolved constraint narrows the queryset."""
import django
from django.conf import settings
settings.configure(DEBUG=True,
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
    INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'], USE_TZ=False)
django.setup()
from django.db import models, connection
from django.db.models import Q
from django.forms.models import modelform_factory
APP = 'contenttypes'
calls = {'n': 0}
def limiter():
    calls['n'] += 1
    return Q(name='keep')
class Person(models.Model):
    name = models.CharField(max_length=50)
    class Meta: app_label = APP
class Report(models.Model):
    person = models.ForeignKey(Person, on_delete=models.CASCADE,
        limit_choices_to=limiter)
    class Meta: app_label = APP
with connection.schema_editor() as se:
    se.create_model(Person); se.create_model(Report)
keep = Person.objects.create(name='keep')
Person.objects.create(name='drop')
calls['n'] = 0
qs = modelform_factory(Report, fields=['person'])().fields['person'].queryset
pks = list(qs.values_list('pk', flat=True))
print("offered:", pks, "| callable invoked", calls['n'], "time(s)")
ok = pks == [keep.pk] and calls['n'] == 1
print("PASS" if ok else "FAIL")
import sys; sys.exit(0 if ok else 1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
"""Probe 6 — Req 1.2 / 3: presence is iff at least one related row satisfies,
independent of count. Tests candidate matching via exactly 1 row is present,
candidate matching via 3 rows present once, candidate via 0 rows absent."""
import django
from django.conf import settings
settings.configure(DEBUG=True,
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
    INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'], USE_TZ=False)
django.setup()
from django.db import models, connection
from django.db.models import Q
from django.forms.models import modelform_factory
APP = 'contenttypes'
class Tag(models.Model):
    name = models.CharField(max_length=50)
    class Meta: app_label = APP
class Person(models.Model):
    name = models.CharField(max_length=50)
    tags = models.ManyToManyField(Tag)
    class Meta:
        app_label = APP
        ordering = ['pk']
class Report(models.Model):
    person = models.ForeignKey(Person, on_delete=models.CASCADE,
        limit_choices_to=Q(tags__name='x'))
    class Meta: app_label = APP
with connection.schema_editor() as se:
    se.create_model(Tag); se.create_model(Person); se.create_model(Report)
one = Person.objects.create(name='one')      # 1 matching row
one.tags.add(Tag.objects.create(name='x'))
three = Person.objects.create(name='three')  # 3 matching rows
three.tags.add(Tag.objects.create(name='x'), Tag.objects.create(name='x'),
               Tag.objects.create(name='x'))
zero = Person.objects.create(name='zero')    # 0 matching rows
zero.tags.add(Tag.objects.create(name='y'))
qs = modelform_factory(Report, fields=['person'])().fields['person'].queryset
pks = list(qs.values_list('pk', flat=True))
print("offered:", pks)
ok = sorted(pks) == sorted([one.pk, three.pk]) and len(pks) == len(set(pks)) \
     and zero.pk not in pks
print("PASS" if ok else "FAIL")
import sys; sys.exit(0 if ok else 1)
```

Attack 7 — `probe_7.py` → holds on the patched tree (good)

```python
"""Probe 7 — Req 1/2 with the HIDDEN-TEST shape: constraint spans TWO
multi-valued relations at once (Q(a__f=True, b__f=True)). The candidate that
matches through several (row_a, row_b) combinations must appear exactly once,
and only candidates satisfying BOTH joins are offered."""
import django
from django.conf import settings
settings.configure(DEBUG=True,
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
    INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'], USE_TZ=False)
django.setup()
from django.db import models, connection
from django.db.models import Q
from django.forms.models import modelform_factory
APP = 'contenttypes'
class Character(models.Model):
    name = models.CharField(max_length=50)
    class Meta:
        app_label = APP
        ordering = ['pk']
class Joke(models.Model):
    funny = models.BooleanField(default=False)
    fk_char = models.ForeignKey(Character, models.CASCADE, related_name='jokes')
    m2m_char = models.ManyToManyField(Character, related_name='jokes_today')
    class Meta: app_label = APP
class Details(models.Model):
    character = models.ForeignKey(Character, models.CASCADE,
        limit_choices_to=Q(jokes__funny=True, jokes_today__funny=True))
    class Meta: app_label = APP
with connection.schema_editor() as se:
    se.create_model(Character); se.create_model(Joke); se.create_model(Details)
threepwood = Character.objects.create(name='threepwood')
marley = Character.objects.create(name='marley')
# marley: multiple qualifying (fk joke funny) x (m2m joke funny) combos
j1 = Joke.objects.create(funny=True, fk_char=threepwood)
j2 = Joke.objects.create(funny=True, fk_char=threepwood)
j3 = Joke.objects.create(funny=True, fk_char=marley)
Joke.objects.create(funny=False, fk_char=marley)
j1.m2m_char.add(marley, threepwood)
j2.m2m_char.add(marley)
j3.m2m_char.add(marley, threepwood)
qs = modelform_factory(Details, fields=['character'])().fields['character'].queryset
pks = list(qs.values_list('pk', flat=True))
print("offered:", pks)
ok = sorted(pks) == sorted([marley.pk, threepwood.pk]) and len(pks) == len(set(pks))
print("PASS" if ok else "FAIL")
import sys; sys.exit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Probe 1 (POSITIVE CONTROL) — Req 1.1: a candidate matching through >1
related row via a Q() constraint over a multi-valued relation appears EXACTLY
ONCE in the form field's queryset.
HOLDS on patched (dedup); FAILS at base (duplicate)."""
import django
from django.conf import settings
settings.configure(
    DEBUG=True,
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
    INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
    USE_TZ=False,
)
django.setup()

from django.db import models, connection
from django.db.models import Q
from django.forms.models import modelform_factory

APP = 'contenttypes'

class Tag(models.Model):
    name = models.CharField(max_length=50)
    class Meta:
        app_label = APP

class Person(models.Model):
    name = models.CharField(max_length=50)
    tags = models.ManyToManyField(Tag)
    class Meta:
        app_label = APP

class Report(models.Model):
    person = models.ForeignKey(
        Person, on_delete=models.CASCADE,
        limit_choices_to=Q(tags__name='x'))
    class Meta:
        app_label = APP

with connection.schema_editor() as se:
    se.create_model(Tag)
    se.create_model(Person)
    se.create_model(Report)

# p1 matches the constraint through TWO related rows (two tags named 'x')
p1 = Person.objects.create(name='p1')
t1 = Tag.objects.create(name='x')
t2 = Tag.objects.create(name='x')
p1.tags.add(t1, t2)
# p2 matches through zero rows (should be excluded)
Person.objects.create(name='p2')

Form = modelform_factory(Report, fields=['person'])
qs = Form().fields['person'].queryset
pks = list(qs.values_list('pk', flat=True))
print("person pks offered:", pks)

count_p1 = pks.count(p1.pk)
print("p1 appears", count_p1, "time(s)")
ok = (count_p1 == 1) and (p1.pk in pks)
print("PASS" if ok else "FAIL")
import sys
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance django__django-13315: apply_limit_choices_to_to_formfield must dedupe candidates matched via multi-valued joins. 7 probes cover Req1 (dedup across joins: probe_1,6,7), Req2 (dict vs Q equivalence + M2M relations: probe_2,3), Req3/4.4 (no/empty constraint leaves full ordered queryset unchanged: probe_4), Req4.1/4.2 (callable invoked exactly once + narrows: probe_5). ALL 7 HOLD on the gold-patched tree.

Positive control = probe_1 (Q constraint over M2M, candidate matched via 2 rows): HOLDS patched (offered [1]), FAILS at base (offered [1,1]) -> discriminating power confirmed. probe_7 also independently reproduces at base ([1,1,1,1,2,2,2] -> [1,2] patched), mirroring the hidden-test double-join shape Q(jokes__funny, jokes_today__funny).

CANDIDATE PATCH (naive_truthiness_no_dedup): the lazy fix a weak reading permits -- change only the guard `is not None` -> truthiness (satisfies Req3 empty->unchanged) but keep the original complex_filter with NO Exists()/dedup. REJECTED by probes 1,2,3,6,7 (duplicates reappear), only 4 and 5 pass. This demonstrates the suite discriminates duplicate-producing implementations, so it is NOT a too-weak finding.

Conclusion: requirements are faithful (no probe fails patched) and non-trivial (a probe-conforming naive fix is rejected). SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 7 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 7 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py`, `probe_7.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

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
"""Probe 1 (POSITIVE CONTROL) — Req 1.1: a candidate matching through >1
related row via a Q() constraint over a multi-valued relation appears EXACTLY
ONCE in the form field's queryset.
HOLDS on patched (dedup); FAILS at base (duplicate)."""
import django
from django.conf import settings
settings.configure(
    DEBUG=True,
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
    INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
    USE_TZ=False,
)
django.setup()

from django.db import models, connection
from django.db.models import Q
from django.forms.models import modelform_factory

APP = 'contenttypes'

class Tag(models.Model):
    name = models.CharField(max_length=50)
    class Meta:
        app_label = APP

class Person(models.Model):
    name = models.CharField(max_length=50)
    tags = models.ManyToManyField(Tag)
    class Meta:
        app_label = APP

class Report(models.Model):
    person = models.ForeignKey(
        Person, on_delete=models.CASCADE,
        limit_choices_to=Q(tags__name='x'))
    class Meta:
        app_label = APP

with connection.schema_editor() as se:
    se.create_model(Tag)
    se.create_model(Person)
    se.create_model(Report)

# p1 matches the constraint through TWO related rows (two tags named 'x')
p1 = Person.objects.create(name='p1')
t1 = Tag.objects.create(name='x')
t2 = Tag.objects.create(name='x')
p1.tags.add(t1, t2)
# p2 matches through zero rows (should be excluded)
Person.objects.create(name='p2')

Form = modelform_factory(Report, fields=['person'])
qs = Form().fields['person'].queryset
pks = list(qs.values_list('pk', flat=True))
print("person pks offered:", pks)

count_p1 = pks.count(p1.pk)
print("p1 appears", count_p1, "time(s)")
ok = (count_p1 == 1) and (p1.pk in pks)
print("PASS" if ok else "FAIL")
import sys
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance django__django-13315: apply_limit_choices_to_to_formfield must dedupe candidates matched via multi-valued joins. 7 probes cover Req1 (dedup across joins: probe_1,6,7), Req2 (dict vs Q equivalence + M2M relations: probe_2,3), Req3/4.4 (no/empty constraint leaves full ordered queryset unchanged: probe_4), Req4.1/4.2 (callable invoked exactly once + narrows: probe_5). ALL 7 HOLD on the gold-patched tree.

Positive control = probe_1 (Q constraint over M2M, candidate matched via 2 rows): HOLDS patched (offered [1]), FAILS at base (offered [1,1]) -> discriminating power confirmed. probe_7 also independently reproduces at base ([1,1,1,1,2,2,2] -> [1,2] patched), mirroring the hidden-test double-join shape Q(jokes__funny, jokes_today__funny).

CANDIDATE PATCH (naive_truthiness_no_dedup): the lazy fix a weak reading permits -- change only the guard `is not None` -> truthiness (satisfies Req3 empty->unchanged) but keep the original complex_filter with NO Exists()/dedup. REJECTED by probes 1,2,3,6,7 (duplicates reappear), only 4 and 5 pass. This demonstrates the suite discriminates duplicate-producing implementations, so it is NOT a too-weak finding.

Conclusion: requirements are faithful (no probe fails patched) and non-trivial (a probe-conforming naive fix is rejected). SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Boundary check passed: Req 3.2 correctly captures the guard change from `is not None` to truthy, which is the only subtle behavioral shift beyond dedup. Base probe VIOLATED (AttributeError on complex_filter for empty dict) vs gold HOLDS, confirming the discriminator. No mandated-but-absent, forbidden-but-present, or invented behavior found.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** requirements.md describes behavior and localizes the change to the public helper apply_limit_choices_to_to_formfield / get_limit_choices_to in django/forms/models.py (legitimate localization). It transmits none of the hidden material: no test function/class/module names (test_limit_choices_to_no_duplicates, LimitChoicesToTests, model_forms/tests.py), no fix-invented identifiers (Exists, OuterRef, _base_manager, complex_filter), no test fixture objects (marley/threepwood/StumpJoke/CharacterDetails), and no quoted test or gold code. The coverage beyond the terse problem_statement (dict vs Q equivalence, FK/O2O/M2M, callable-once, empty-constraint no-op, ordering preservation) is a behavioral generalization derivable from the gold edit's dict->Q branch and standard Django semantics, and is broader than the test's specific parametrization rather than a 1:1 mirror of it. This is translating tested behavior into requirements, which is the intended purpose, not transmitting the tests.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
