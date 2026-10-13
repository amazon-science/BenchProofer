# P2 adversarial audit — django__django-11734

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 6 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 6 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 6 | `probe_1_posctl.py`, `probe_2_notq.py`, `probe_3_fref.py`, `probe_4_concrete.py`, `probe_5_invalid.py`, `probe_6_complement.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1_posctl.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (6):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1_posctl.py` → holds on the patched tree (good)

```python
# R1.1/R1.3 POSITIVE CONTROL: exclude(<m2m>=OuterRef(...)) inside Exists() used
# as a correlated subquery must build+execute WITHOUT raising the "reference to
# an outer query" ValueError, and must give the intended result set.
import django
from django.conf import settings
if not settings.configured:
    settings.configure(
        INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
    )
django.setup()

from django.db import models, connection
from django.db.models import Exists, OuterRef

class Job(models.Model):
    name = models.CharField(max_length=20, unique=True)
    class Meta: app_label = 'contenttypes'

class Responsibility(models.Model):
    description = models.CharField(max_length=20, unique=True)
    jobs = models.ManyToManyField(Job, through='JobResponsibilities', related_name='responsibilities')
    class Meta: app_label = 'contenttypes'

class JobResponsibilities(models.Model):
    job = models.ForeignKey(Job, models.CASCADE, to_field='name')
    responsibility = models.ForeignKey('Responsibility', models.CASCADE, to_field='description')
    class Meta: app_label = 'contenttypes'

with connection.schema_editor() as se:
    for m in (Job, Responsibility, JobResponsibilities):
        se.create_model(m)

j1 = Job.objects.create(name='Manager')
r1 = Responsibility.objects.create(description='Playing golf')
j2 = Job.objects.create(name='Programmer')
r2 = Responsibility.objects.create(description='Programming')
JobResponsibilities.objects.create(job=j1, responsibility=r1)
JobResponsibilities.objects.create(job=j2, responsibility=r2)

qs = JobResponsibilities.objects.filter(
    Exists(Responsibility.objects.exclude(jobs=OuterRef('job'))),
)
try:
    got1 = qs.exists()
    print("qs.exists() first =", got1)
    r1.delete()
    got2 = qs.exists()
    print("qs.exists() after r1.delete() =", got2)
except ValueError as e:
    print("RAISED ValueError:", e)
    raise SystemExit(1)

ok = (got1 is True and got2 is False)
print("R1 exclude OuterRef correlated subquery correct:", ok)
raise SystemExit(0 if ok else 1)
```

Attack 2 — `probe_2_notq.py` → holds on the patched tree (good)

```python
# R1.2: filter(~Q(<m2m>=OuterRef(...))) inside Exists() correlated subquery must
# build+execute without the "reference to an outer query" ValueError, and give
# the same result as the exclude() form.
import django
from django.conf import settings
if not settings.configured:
    settings.configure(
        INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
    )
django.setup()

from django.db import models, connection
from django.db.models import Exists, OuterRef, Q

class Job(models.Model):
    name = models.CharField(max_length=20, unique=True)
    class Meta: app_label = 'contenttypes'

class Responsibility(models.Model):
    description = models.CharField(max_length=20, unique=True)
    jobs = models.ManyToManyField(Job, through='JobResponsibilities', related_name='responsibilities')
    class Meta: app_label = 'contenttypes'

class JobResponsibilities(models.Model):
    job = models.ForeignKey(Job, models.CASCADE, to_field='name')
    responsibility = models.ForeignKey('Responsibility', models.CASCADE, to_field='description')
    class Meta: app_label = 'contenttypes'

with connection.schema_editor() as se:
    for m in (Job, Responsibility, JobResponsibilities):
        se.create_model(m)

j1 = Job.objects.create(name='Manager')
r1 = Responsibility.objects.create(description='Playing golf')
j2 = Job.objects.create(name='Programmer')
r2 = Responsibility.objects.create(description='Programming')
JobResponsibilities.objects.create(job=j1, responsibility=r1)
JobResponsibilities.objects.create(job=j2, responsibility=r2)

qs = JobResponsibilities.objects.filter(
    Exists(Responsibility.objects.filter(~Q(jobs=OuterRef('job')))),
)
try:
    got1 = qs.exists()
    print("~Q qs.exists() first =", got1)
    r1.delete()
    got2 = qs.exists()
    print("~Q qs.exists() after r1.delete() =", got2)
except ValueError as e:
    print("RAISED ValueError:", e)
    raise SystemExit(1)

ok = (got1 is True and got2 is False)
print("R1.2 ~Q OuterRef correlated subquery correct:", ok)
raise SystemExit(0 if ok else 1)
```

Attack 3 — `probe_3_fref.py` → holds on the patched tree (good)

```python
# R2.1 / R4.1(F case): exclude over a to-many relation whose rhs is a plain
# same-query column reference F(...) must still work (relocated column becomes
# an OuterRef reaching out one boundary). Mirrors test_exclude_reverse_fk_field_ref.
import django
from django.conf import settings
if not settings.configured:
    settings.configure(
        INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
    )
django.setup()

from django.db import models, connection
from django.db.models import F

class Tag(models.Model):
    name = models.CharField(max_length=10)
    class Meta: app_label = 'contenttypes'

class Note(models.Model):
    note = models.CharField(max_length=100)
    tag = models.ForeignKey(Tag, models.SET_NULL, blank=True, null=True)
    class Meta: app_label = 'contenttypes'

class Annotation(models.Model):
    name = models.CharField(max_length=10)
    tag = models.ForeignKey(Tag, models.CASCADE)
    class Meta: app_label = 'contenttypes'

with connection.schema_editor() as se:
    for m in (Tag, Note, Annotation):
        se.create_model(m)

tag = Tag.objects.create(name='t')
Note.objects.create(tag=tag, note='note')
annotation = Annotation.objects.create(name='annotation', tag=tag)

try:
    got = Annotation.objects.exclude(tag__note__note=F('name')).get()
except Exception as e:
    print("RAISED:", type(e).__name__, e)
    raise SystemExit(1)

ok = (got == annotation)
print("R2.1/R4.1 exclude(...=F(...)) over to-many still works, got:", got.pk, "expected:", annotation.pk, "ok:", ok)
raise SystemExit(0 if ok else 1)
```

Attack 4 — `probe_4_concrete.py` → holds on the patched tree (good)

```python
# R4.1 / R2.3: exclude over a to-many relation with a CONCRETE value rhs must
# keep its prior result set (regression). Mirrors ExcludeTests.test_to_field.
import django
from django.conf import settings
if not settings.configured:
    settings.configure(
        INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
    )
django.setup()

from django.db import models, connection

class Job(models.Model):
    name = models.CharField(max_length=20, unique=True)
    class Meta: app_label = 'contenttypes'

class Responsibility(models.Model):
    description = models.CharField(max_length=20, unique=True)
    jobs = models.ManyToManyField(Job, through='JobResponsibilities', related_name='responsibilities')
    class Meta: app_label = 'contenttypes'

class JobResponsibilities(models.Model):
    job = models.ForeignKey(Job, models.CASCADE, to_field='name')
    responsibility = models.ForeignKey('Responsibility', models.CASCADE, to_field='description')
    class Meta: app_label = 'contenttypes'

with connection.schema_editor() as se:
    for m in (Job, Responsibility, JobResponsibilities):
        se.create_model(m)

j1 = Job.objects.create(name='Manager')
r1 = Responsibility.objects.create(description='Playing golf')
j2 = Job.objects.create(name='Programmer')
r2 = Responsibility.objects.create(description='Programming')
JobResponsibilities.objects.create(job=j1, responsibility=r1)
JobResponsibilities.objects.create(job=j2, responsibility=r2)

# Job excluding a m2m through relation by concrete value
got = list(Job.objects.exclude(responsibilities__description='Playing golf').values_list('name', flat=True))
print("exclude by concrete value ->", got)
# Responsibility excluding jobs by concrete value
got2 = list(Responsibility.objects.exclude(jobs__name='Manager').values_list('description', flat=True))
print("exclude jobs__name=Manager ->", got2)

ok = (got == ['Programmer'] and got2 == ['Programming'])
print("R4.1 concrete-value exclude over to-many unchanged:", ok)
raise SystemExit(0 if ok else 1)
```

Attack 5 — `probe_5_invalid.py` → holds on the patched tree (good)

```python
# R3.2/R3.3/R4.4: a concrete, invalid value for a single-column relation lookup
# must STILL raise a validation error (get_prep_lookup normalizes concrete
# values as before). A non-integer for an integer PK FK must raise ValueError.
import django
from django.conf import settings
if not settings.configured:
    settings.configure(
        INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
    )
django.setup()

from django.db import models, connection

class Author(models.Model):
    name = models.CharField(max_length=20)
    class Meta: app_label = 'contenttypes'

class Book(models.Model):
    author = models.ForeignKey(Author, models.CASCADE)  # rel to integer pk
    class Meta: app_label = 'contenttypes'

with connection.schema_editor() as se:
    for m in (Author, Book):
        se.create_model(m)

raised = False
try:
    # non-integer concrete value for an integer-pk FK lookup must still be rejected
    list(Book.objects.filter(author='not-an-integer'))
except ValueError as e:
    raised = True
    print("filter(author='not-an-integer') raised ValueError:", e)

print("R4.4 invalid concrete relation value still raises ValueError:", raised)
raise SystemExit(0 if raised else 1)
```

Attack 6 — `probe_6_complement.py` → holds on the patched tree (good)

```python
# R1.4 / R4.3: the non-negated filter(...) OuterRef form over a to-many relation
# and the exclude(...) form must remain COMPLEMENTARY (filter selects the rows
# exclude drops). Also confirms the working filter(...) correlated-subquery form
# still works (R4.3).
import django
from django.conf import settings
if not settings.configured:
    settings.configure(
        INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
    )
django.setup()

from django.db import models, connection
from django.db.models import Exists, OuterRef

class Job(models.Model):
    name = models.CharField(max_length=20, unique=True)
    class Meta: app_label = 'contenttypes'

class Responsibility(models.Model):
    description = models.CharField(max_length=20, unique=True)
    jobs = models.ManyToManyField(Job, through='JobResponsibilities', related_name='responsibilities')
    class Meta: app_label = 'contenttypes'

class JobResponsibilities(models.Model):
    job = models.ForeignKey(Job, models.CASCADE, to_field='name')
    responsibility = models.ForeignKey('Responsibility', models.CASCADE, to_field='description')
    class Meta: app_label = 'contenttypes'

with connection.schema_editor() as se:
    for m in (Job, Responsibility, JobResponsibilities):
        se.create_model(m)

j1 = Job.objects.create(name='Manager')
r1 = Responsibility.objects.create(description='Playing golf')
j2 = Job.objects.create(name='Programmer')
r2 = Responsibility.objects.create(description='Programming')
JobResponsibilities.objects.create(job=j1, responsibility=r1)
JobResponsibilities.objects.create(job=j2, responsibility=r2)

# rows of JobResponsibilities for which SOME responsibility IS related to job (filter form)
qs_filter = JobResponsibilities.objects.filter(
    Exists(Responsibility.objects.filter(jobs=OuterRef('job'))),
)
# rows for which SOME responsibility is NOT related to job (exclude form)
qs_exclude = JobResponsibilities.objects.filter(
    Exists(Responsibility.objects.exclude(jobs=OuterRef('job'))),
)
all_ids = set(JobResponsibilities.objects.values_list('id', flat=True))
try:
    f_ids = set(qs_filter.values_list('id', flat=True))
    e_ids = set(qs_exclude.values_list('id', flat=True))
except ValueError as e:
    print("RAISED ValueError:", e)
    raise SystemExit(1)

print("all:", all_ids, "filter:", f_ids, "exclude:", e_ids)
# Both filter and exclude must be non-crashing and consistent (complementary in
# the sense: with >=2 distinct responsibilities each row has a matching AND a
# non-matching responsibility, so both forms select all rows here). The key
# requirement: both produce valid, consistent result sets rather than crashing.
ok = (f_ids == all_ids and e_ids == all_ids and len(all_ids) == 2)
print("R1.4/R4.3 filter & exclude OuterRef forms consistent:", ok)
raise SystemExit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1_posctl.py`

```python
# R1.1/R1.3 POSITIVE CONTROL: exclude(<m2m>=OuterRef(...)) inside Exists() used
# as a correlated subquery must build+execute WITHOUT raising the "reference to
# an outer query" ValueError, and must give the intended result set.
import django
from django.conf import settings
if not settings.configured:
    settings.configure(
        INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
    )
django.setup()

from django.db import models, connection
from django.db.models import Exists, OuterRef

class Job(models.Model):
    name = models.CharField(max_length=20, unique=True)
    class Meta: app_label = 'contenttypes'

class Responsibility(models.Model):
    description = models.CharField(max_length=20, unique=True)
    jobs = models.ManyToManyField(Job, through='JobResponsibilities', related_name='responsibilities')
    class Meta: app_label = 'contenttypes'

class JobResponsibilities(models.Model):
    job = models.ForeignKey(Job, models.CASCADE, to_field='name')
    responsibility = models.ForeignKey('Responsibility', models.CASCADE, to_field='description')
    class Meta: app_label = 'contenttypes'

with connection.schema_editor() as se:
    for m in (Job, Responsibility, JobResponsibilities):
        se.create_model(m)

j1 = Job.objects.create(name='Manager')
r1 = Responsibility.objects.create(description='Playing golf')
j2 = Job.objects.create(name='Programmer')
r2 = Responsibility.objects.create(description='Programming')
JobResponsibilities.objects.create(job=j1, responsibility=r1)
JobResponsibilities.objects.create(job=j2, responsibility=r2)

qs = JobResponsibilities.objects.filter(
    Exists(Responsibility.objects.exclude(jobs=OuterRef('job'))),
)
try:
    got1 = qs.exists()
    print("qs.exists() first =", got1)
    r1.delete()
    got2 = qs.exists()
    print("qs.exists() after r1.delete() =", got2)
except ValueError as e:
    print("RAISED ValueError:", e)
    raise SystemExit(1)

ok = (got1 is True and got2 is False)
print("R1 exclude OuterRef correlated subquery correct:", ok)
raise SystemExit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance django__django-11734: preserve OuterRef through split_exclude over a to-many relation. Requirements + gold patch (query.split_exclude wraps OuterRef in an additional OuterRef; RelatedLookupMixin.get_prep_lookup skips value-normalization for resolvable expressions; AutoField.get_prep_value removed).

Probes (all HOLD on gold-patched tree; run in the official py3.6 testbed image, standalone with in-memory sqlite and the queries-app M2M-through models):
- probe_1_posctl.py (R1.1/R1.3, POSITIVE CONTROL): JobResponsibilities.filter(Exists(Responsibility.exclude(jobs=OuterRef('job')))) builds+executes without the outer-query ValueError and returns the intended result set (True, then False after deleting r1). HOLDS patched; FAILS at base (base raises FieldError 'Cannot resolve keyword job' — reference resolved against wrong query). prepatch_reproduced=true. Discriminates.
- probe_2_notq.py (R1.2): filter(~Q(jobs=OuterRef('job'))) form works identically. HOLDS.
- probe_3_fref.py (R2.1/R4.1): exclude(tag__note__note=F('name')) over to-many still works (F relocated to one-boundary OuterRef). HOLDS.
- probe_4_concrete.py (R4.1/R2.3): concrete-value exclude over m2m-through relations unchanged (Job/Responsibility result sets). HOLDS.
- probe_5_invalid.py (R3.2/R3.3/R4.4): non-integer concrete value for an integer-pk FK lookup still raises ValueError (concrete-value normalization preserved). HOLDS.
- probe_6_complement.py (R1.4/R4.3): non-negated filter(...) OuterRef form and exclude(...) form both build and produce consistent result sets. HOLDS.

Candidate wrong patch (REQUIRED floor): weak_partial.diff — the lazy/partial fix that applies ONLY the split_exclude change in query.py and OMITS the related_lookups.py get_prep_lookup change. This is the reading of the requirements that fixes the boundary re-anchoring but forgets to stop value-normalization from mangling the OuterRef in a single-column relation lookup. Result under --patch: probe_1_posctl and probe_2_notq are REJECTED (exit 1 — the OuterRef gets normalized to a concrete value and the correlated subquery misbehaves/crashes), while probe_6 (which uses filter, not the negated path with concrete normalization) still holds. So the suite discriminates the incomplete fix. 1/1 candidate rejected.

Verdict: 6 distinct probes all hold on the patched tree; positive control discriminates base (fail) vs patched (hold); the requirements-partial candidate patch is rejected by the probe suite. SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 6 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 6 | `probe_1_posctl.py`, `probe_2_notq.py`, `probe_3_fref.py`, `probe_4_concrete.py`, `probe_5_invalid.py`, `probe_6_complement.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1_posctl.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (6):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

_The 6 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts, and on this backend both roles put it through the same derivation: every block below is a requirement probe run on the gold-patched tree, and the `machine verdict:` line each role publishes above reports BOTH that its probes hold there and how many candidate patches the probe suite rejected — so the two roles re-ran ONE probe suite and each recorded its own outcome for every probe in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `probe_1_posctl.py` → holds on the patched tree (good)

Attack 2 — `probe_2_notq.py` → holds on the patched tree (good)

Attack 3 — `probe_3_fref.py` → holds on the patched tree (good)

Attack 4 — `probe_4_concrete.py` → holds on the patched tree (good)

Attack 5 — `probe_5_invalid.py` → holds on the patched tree (good)

Attack 6 — `probe_6_complement.py` → holds on the patched tree (good)

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1_posctl.py`

```python
# R1.1/R1.3 POSITIVE CONTROL: exclude(<m2m>=OuterRef(...)) inside Exists() used
# as a correlated subquery must build+execute WITHOUT raising the "reference to
# an outer query" ValueError, and must give the intended result set.
import django
from django.conf import settings
if not settings.configured:
    settings.configure(
        INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
    )
django.setup()

from django.db import models, connection
from django.db.models import Exists, OuterRef

class Job(models.Model):
    name = models.CharField(max_length=20, unique=True)
    class Meta: app_label = 'contenttypes'

class Responsibility(models.Model):
    description = models.CharField(max_length=20, unique=True)
    jobs = models.ManyToManyField(Job, through='JobResponsibilities', related_name='responsibilities')
    class Meta: app_label = 'contenttypes'

class JobResponsibilities(models.Model):
    job = models.ForeignKey(Job, models.CASCADE, to_field='name')
    responsibility = models.ForeignKey('Responsibility', models.CASCADE, to_field='description')
    class Meta: app_label = 'contenttypes'

with connection.schema_editor() as se:
    for m in (Job, Responsibility, JobResponsibilities):
        se.create_model(m)

j1 = Job.objects.create(name='Manager')
r1 = Responsibility.objects.create(description='Playing golf')
j2 = Job.objects.create(name='Programmer')
r2 = Responsibility.objects.create(description='Programming')
JobResponsibilities.objects.create(job=j1, responsibility=r1)
JobResponsibilities.objects.create(job=j2, responsibility=r2)

qs = JobResponsibilities.objects.filter(
    Exists(Responsibility.objects.exclude(jobs=OuterRef('job'))),
)
try:
    got1 = qs.exists()
    print("qs.exists() first =", got1)
    r1.delete()
    got2 = qs.exists()
    print("qs.exists() after r1.delete() =", got2)
except ValueError as e:
    print("RAISED ValueError:", e)
    raise SystemExit(1)

ok = (got1 is True and got2 is False)
print("R1 exclude OuterRef correlated subquery correct:", ok)
raise SystemExit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance django__django-11734: preserve OuterRef through split_exclude over a to-many relation. Requirements + gold patch (query.split_exclude wraps OuterRef in an additional OuterRef; RelatedLookupMixin.get_prep_lookup skips value-normalization for resolvable expressions; AutoField.get_prep_value removed).

Probes (all HOLD on gold-patched tree; run in the official py3.6 testbed image, standalone with in-memory sqlite and the queries-app M2M-through models):
- probe_1_posctl.py (R1.1/R1.3, POSITIVE CONTROL): JobResponsibilities.filter(Exists(Responsibility.exclude(jobs=OuterRef('job')))) builds+executes without the outer-query ValueError and returns the intended result set (True, then False after deleting r1). HOLDS patched; FAILS at base (base raises FieldError 'Cannot resolve keyword job' — reference resolved against wrong query). prepatch_reproduced=true. Discriminates.
- probe_2_notq.py (R1.2): filter(~Q(jobs=OuterRef('job'))) form works identically. HOLDS.
- probe_3_fref.py (R2.1/R4.1): exclude(tag__note__note=F('name')) over to-many still works (F relocated to one-boundary OuterRef). HOLDS.
- probe_4_concrete.py (R4.1/R2.3): concrete-value exclude over m2m-through relations unchanged (Job/Responsibility result sets). HOLDS.
- probe_5_invalid.py (R3.2/R3.3/R4.4): non-integer concrete value for an integer-pk FK lookup still raises ValueError (concrete-value normalization preserved). HOLDS.
- probe_6_complement.py (R1.4/R4.3): non-negated filter(...) OuterRef form and exclude(...) form both build and produce consistent result sets. HOLDS.

Candidate wrong patch (REQUIRED floor): weak_partial.diff — the lazy/partial fix that applies ONLY the split_exclude change in query.py and OMITS the related_lookups.py get_prep_lookup change. This is the reading of the requirements that fixes the boundary re-anchoring but forgets to stop value-normalization from mangling the OuterRef in a single-column relation lookup. Result under --patch: probe_1_posctl and probe_2_notq are REJECTED (exit 1 — the OuterRef gets normalized to a concrete value and the correlated subquery misbehaves/crashes), while probe_6 (which uses filter, not the negated path with concrete normalization) still holds. So the suite discriminates the incomplete fix. 1/1 candidate rejected.

Verdict: 6 distinct probes all hold on the patched tree; positive control discriminates base (fail) vs patched (hold); the requirements-partial candidate patch is rejected by the probe suite. SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** The recorded meta.json G-PANEL-2=fail is a misread of confirming evidence as divergence — a classic wrong-boundary FALSE alarm: the auditor expected the generic resolve_expression predicate to live in split_exclude, but the gold patch deliberately keeps split_exclude narrow (OuterRef/F only) and puts the generic predicate in get_prep_lookup, which Req 2.4 and Req 3 correctly and separately pin. Requirements 1-4 are all faithful. Probes: probe.py (branch classification), probe2.py (structure, discriminates base), probe3.py (end-to-end Req1, base raises), probe4.py (Req 3.2/3.3).

Counterexample / evidence:

```
Probed in image: split_exclude branches are OuterRef->OuterRef(filter_rhs) (Req 2.2), F->OuterRef(filter_rhs.name) (Req 2.1), else->passthrough incl. CombinedExpression/literal/Value (Req 2.3/2.4). get_prep_lookup uses `not hasattr(self.rhs,'resolve_expression')` (Req 3.1/3.2). Functional: Item.objects.exclude(tags__category_id=OuterRef('num')).filter(number=OuterRef('pk')) inside Exists() builds and returns rows on patched (rows=1) but raises FieldError/reference error on base — Req 1.1; ~Q form same (Req 1.2); non-negated filter form also works (Req 1.4). Req 3.3: Item.objects.filter(number='notanint') still raises ValueError; valid pk value works. All discriminate base vs patched.
```


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** requirements.md describes the fix behaviorally and localizes it to the three gold-touched modules (Query.split_exclude, RelatedLookupMixin.get_prep_lookup, and implicitly the AutoField get_prep_value removal). All illustrative code (Item.objects.exclude(tags__category_id=OuterRef('pk')), Exists(), Number.objects, the ValueError text, filter/exclude/~Q forms) is already present verbatim in the PUBLIC problem_statement. None of the hidden test's distinguishing content leaks: no mention of the FAIL_TO_PASS test name test_subquery_exclude_outerref, its class queries.tests.ExcludeTests, the fixture models JobResponsibilities/Responsibility, OuterRef('job'), or the create-assert-then-delete-and-reassert pattern (self.r1.delete()). The four RHS cases in Requirement 2 (OuterRef/F/literal/other) track the source-code branch structure of split_exclude, not a test parametrization; the resolve_expression distinction in Requirement 3 restates the gold's hasattr(self.rhs,'resolve_expression') change as a behavioral requirement, which is the intended translation, not transmission of tests. Naming modules/functions is legitimate localization.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
