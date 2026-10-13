# P2 adversarial audit — django__django-11400

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 9 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 9 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 9 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py`, `probe_7.py`, `probe_8.py`, `probe_9.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (9):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
"""Requirement 1.1 (POSITIVE CONTROL): Field.get_choices with EMPTY ordering
preserves the related model's Meta.ordering.
Holds iff choices come back in Meta.ordering order (by 'd')."""
import django
from django.conf import settings
settings.configure(
    DEBUG=True,
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
    INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
    USE_TZ=True,
)
django.setup()
from django.db import connection, models

class Foo(models.Model):
    a = models.CharField(max_length=10)
    d = models.CharField(max_length=10)
    class Meta:
        app_label = 'probeapp'
        ordering = ('d',)
    def __str__(self):
        return self.a

class Bar(models.Model):
    a = models.ForeignKey(Foo, models.CASCADE)
    b = models.CharField(max_length=10)
    class Meta:
        app_label = 'probeapp'
    def __str__(self):
        return self.b

with connection.schema_editor() as se:
    se.create_model(Foo)
    se.create_model(Bar)

# foo1 inserted first (lower pk) but has larger 'd'; foo2 has smaller 'd'.
foo1 = Foo.objects.create(a='a', d='12.35')
foo2 = Foo.objects.create(a='b', d='12.34')
field = Bar._meta.get_field('a')

choices = field.get_choices(include_blank=False, ordering=())
values = [c[0] for c in choices]
print("choices values:", values, "expected (Meta.ordering by d):", [foo2.pk, foo1.pk])
import sys
sys.exit(0 if values == [foo2.pk, foo1.pk] else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""Requirement 1.2 & 5.1: Field.get_choices with a NON-EMPTY ordering directive
re-sequences the queryset by that directive (overriding Meta.ordering).
Meta.ordering=('d',) would give [foo2,foo1]; ordering=('a',) must give [foo1,foo2]."""
import django, sys
from django.conf import settings
settings.configure(DEBUG=True,
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
    INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'], USE_TZ=True)
django.setup()
from django.db import connection, models

class Foo(models.Model):
    a = models.CharField(max_length=10); d = models.CharField(max_length=10)
    class Meta: app_label='probeapp'; ordering=('d',)
    def __str__(self): return self.a
class Bar(models.Model):
    a = models.ForeignKey(Foo, models.CASCADE); b = models.CharField(max_length=10)
    class Meta: app_label='probeapp'
    def __str__(self): return self.b
with connection.schema_editor() as se:
    se.create_model(Foo); se.create_model(Bar)

foo1 = Foo.objects.create(a='a', d='12.35')  # 'a' small, 'd' large
foo2 = Foo.objects.create(a='b', d='12.34')  # 'a' large, 'd' small
field = Bar._meta.get_field('a')

asc = [c[0] for c in field.get_choices(include_blank=False, ordering=('a',))]
desc = [c[0] for c in field.get_choices(include_blank=False, ordering=('-a',))]
print("ordering=('a',):", asc, "expected", [foo1.pk, foo2.pk])
print("ordering=('-a',):", desc, "expected", [foo2.pk, foo1.pk])
sys.exit(0 if asc == [foo1.pk, foo2.pk] and desc == [foo2.pk, foo1.pk] else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""Requirement 2.1: ForeignObjectRel.get_choices with EMPTY ordering preserves
the related model's Meta.ordering (reverse relation).
Bar Meta.ordering=('b',). bar1 has b='b' (inserted first), bar2 has b='a'.
Empty ordering must yield bar2 (b='a') before bar1 (b='b')."""
import django, sys
from django.conf import settings
settings.configure(DEBUG=True,
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
    INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'], USE_TZ=True)
django.setup()
from django.db import connection, models

class Foo(models.Model):
    a = models.CharField(max_length=10); d = models.CharField(max_length=10)
    class Meta: app_label='probeapp'
    def __str__(self): return self.a
class Bar(models.Model):
    a = models.ForeignKey(Foo, models.CASCADE); b = models.CharField(max_length=10)
    class Meta: app_label='probeapp'; ordering=('b',)
    def __str__(self): return self.b
with connection.schema_editor() as se:
    se.create_model(Foo); se.create_model(Bar)

foo1 = Foo.objects.create(a='a', d='12.35')
foo2 = Foo.objects.create(a='b', d='12.34')
bar1 = Bar.objects.create(a=foo1, b='b')
bar2 = Bar.objects.create(a=foo2, b='a')
field = Bar._meta.get_field('a')

choices = field.remote_field.get_choices(include_blank=False, ordering=())
values = [c[0] for c in choices]
print("reverse choices:", values, "expected (Meta.ordering by b):", [bar2.pk, bar1.pk])
sys.exit(0 if values == [bar2.pk, bar1.pk] else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""Requirement 2.2 & 2.3: ForeignObjectRel.get_choices with NON-EMPTY ordering
re-sequences by directive; and structure (pk, str(x)) per record + blank prepend.
Also checks blank-choice prepend (Req 2.3)."""
import django, sys
from django.conf import settings
settings.configure(DEBUG=True,
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
    INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'], USE_TZ=True)
django.setup()
from django.db import connection, models

class Foo(models.Model):
    a = models.CharField(max_length=10); d = models.CharField(max_length=10)
    class Meta: app_label='probeapp'
    def __str__(self): return self.a
class Bar(models.Model):
    a = models.ForeignKey(Foo, models.CASCADE); b = models.CharField(max_length=10)
    class Meta: app_label='probeapp'
    def __str__(self): return self.b
with connection.schema_editor() as se:
    se.create_model(Foo); se.create_model(Bar)

foo1 = Foo.objects.create(a='a', d='12.35')
foo2 = Foo.objects.create(a='b', d='12.34')
bar1 = Bar.objects.create(a=foo1, b='b')
bar2 = Bar.objects.create(a=foo2, b='a')
field = Bar._meta.get_field('a')

asc = field.remote_field.get_choices(include_blank=False, ordering=('a',))
desc = field.remote_field.get_choices(include_blank=False, ordering=('-a',))
# a='a'(foo1) vs a='b'(foo2); bar1->foo1, bar2->foo2
asc_v = [c[0] for c in asc]; desc_v = [c[0] for c in desc]
print("asc ('a'):", asc_v, "expected", [bar1.pk, bar2.pk])
print("desc ('-a'):", desc_v, "expected", [bar2.pk, bar1.pk])
# structure: (pk, str) pairs and label is str repr
struct_ok = all(len(c) == 2 and c[1] == str(bobj) for c, bobj in
                [(c, Bar.objects.get(pk=c[0])) for c in asc])
# blank prepend
blank = field.remote_field.get_choices(include_blank=True, ordering=('a',))
blank_ok = blank[0] == ('', '---------') and [c[0] for c in blank[1:]] == asc_v
print("struct_ok:", struct_ok, "blank_ok:", blank_ok, "blank[0]:", blank[0])
sys.exit(0 if asc_v == [bar1.pk, bar2.pk] and desc_v == [bar2.pk, bar1.pk]
         and struct_ok and blank_ok else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""Requirement 3.2: RelatedFieldListFilter falls back to related model's
Meta.ordering when no ModelAdmin ordering is registered.
Employee has no registered admin here; Meta.ordering=('name',) must order the
filter's lookup_choices by name."""
import django, sys
from django.conf import settings
settings.configure(DEBUG=True,
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
    INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth',
                    'django.contrib.admin', 'django.contrib.sessions',
                    'django.contrib.messages'],
    ROOT_URLCONF=None, USE_TZ=True,
    TEMPLATES=[{'BACKEND': 'django.template.backends.django.DjangoTemplates',
                'DIRS': [], 'APP_DIRS': True,
                'OPTIONS': {'context_processors': []}}],
    MIDDLEWARE=[])
django.setup()
from django.db import connection, models

class Employee(models.Model):
    name = models.CharField(max_length=50)
    class Meta: app_label='probeapp'
    def __str__(self): return self.name
class Book(models.Model):
    title = models.CharField(max_length=50)
    employee = models.ForeignKey(Employee, models.SET_NULL, null=True)
    class Meta: app_label='probeapp'
    def __str__(self): return self.title

for m in (Employee, Book):
    with connection.schema_editor() as se:
        se.create_model(m)

from django.contrib.admin import ModelAdmin, site
from django.contrib.auth.models import User
from django.test import RequestFactory
from django.contrib.auth.models import AnonymousUser

# john (name 'John') inserted first, jack second; Meta.ordering by name -> Jack, John
john = Employee.objects.create(name='John Blue')
jack = Employee.objects.create(name='Jack Red')
Book.objects.create(title='b1', employee=john)
Book.objects.create(title='b2', employee=jack)

Employee._meta.ordering = ('name',)

class BookAdmin(ModelAdmin):
    list_filter = ('employee',)

modeladmin = BookAdmin(Book, site)
rf = RequestFactory()
request = rf.get('/')
su = User(username='alfred', is_superuser=True, is_staff=True)
request.user = su
changelist = modeladmin.get_changelist_instance(request)
filterspec = changelist.get_filters(request)[0][0]
got = filterspec.lookup_choices
expected = [(jack.pk, 'Jack Red'), (john.pk, 'John Blue')]
print("lookup_choices:", got, "expected:", expected)
sys.exit(0 if got == expected else 1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
"""Requirement 3.1 & 5.2: RelatedFieldListFilter orders by the related
ModelAdmin's ordering when one is registered (and this must remain intact).
Register EmployeeAdmin ordering=('name',); filter must order by name."""
import django, sys
from django.conf import settings
settings.configure(DEBUG=True,
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
    INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth',
                    'django.contrib.admin', 'django.contrib.sessions',
                    'django.contrib.messages'],
    USE_TZ=True,
    TEMPLATES=[{'BACKEND': 'django.template.backends.django.DjangoTemplates',
                'DIRS': [], 'APP_DIRS': True, 'OPTIONS': {'context_processors': []}}],
    MIDDLEWARE=[])
django.setup()
from django.db import connection, models

class Employee(models.Model):
    name = models.CharField(max_length=50)
    class Meta: app_label='probeapp'  # NO Meta.ordering
    def __str__(self): return self.name
class Book(models.Model):
    title = models.CharField(max_length=50)
    employee = models.ForeignKey(Employee, models.SET_NULL, null=True)
    class Meta: app_label='probeapp'
    def __str__(self): return self.title
for m in (Employee, Book):
    with connection.schema_editor() as se:
        se.create_model(m)

from django.contrib.admin import ModelAdmin, site
from django.contrib.auth.models import User
from django.test import RequestFactory

john = Employee.objects.create(name='John Blue')
jack = Employee.objects.create(name='Jack Red')
Book.objects.create(title='b1', employee=john)
Book.objects.create(title='b2', employee=jack)

class EmployeeAdmin(ModelAdmin):
    ordering = ('name',)
site.register(Employee, EmployeeAdmin)

class BookAdmin(ModelAdmin):
    list_filter = ('employee',)
modeladmin = BookAdmin(Book, site)
rf = RequestFactory(); request = rf.get('/')
request.user = User(username='a', is_superuser=True, is_staff=True)
changelist = modeladmin.get_changelist_instance(request)
filterspec = changelist.get_filters(request)[0][0]
got = filterspec.lookup_choices
expected = [(jack.pk, 'Jack Red'), (john.pk, 'John Blue')]
print("lookup_choices:", got, "expected (by ModelAdmin ordering name):", expected)
site.unregister(Employee)
sys.exit(0 if got == expected else 1)
```

Attack 7 — `probe_7.py` → holds on the patched tree (good)

```python
"""Requirement 4.2 & 4.3: RelatedOnlyFieldListFilter orders its NARROWED choices
by related Meta.ordering (no ModelAdmin ordering), while still restricting to
only referenced records.
Employees: albert, jack referenced by books; a third 'zed' NOT referenced ->
must be excluded. Ordering by name -> Albert, Jack."""
import django, sys
from django.conf import settings
settings.configure(DEBUG=True,
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
    INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth',
                    'django.contrib.admin', 'django.contrib.sessions',
                    'django.contrib.messages'],
    USE_TZ=True,
    TEMPLATES=[{'BACKEND': 'django.template.backends.django.DjangoTemplates',
                'DIRS': [], 'APP_DIRS': True, 'OPTIONS': {'context_processors': []}}],
    MIDDLEWARE=[])
django.setup()
from django.db import connection, models

class Employee(models.Model):
    name = models.CharField(max_length=50)
    class Meta: app_label='probeapp'
    def __str__(self): return self.name
class Book(models.Model):
    title = models.CharField(max_length=50)
    employee = models.ForeignKey(Employee, models.SET_NULL, null=True)
    class Meta: app_label='probeapp'
    def __str__(self): return self.title
for m in (Employee, Book):
    with connection.schema_editor() as se:
        se.create_model(m)

from django.contrib.admin import ModelAdmin, site, RelatedOnlyFieldListFilter
from django.contrib.auth.models import User
from django.test import RequestFactory

# zed inserted first (unreferenced), then jack, albert referenced
zed = Employee.objects.create(name='Zed Unref')
jack = Employee.objects.create(name='Jack Red')
albert = Employee.objects.create(name='Albert Green')
Book.objects.create(title='b1', employee=albert)
Book.objects.create(title='b2', employee=jack)

Employee._meta.ordering = ('name',)

class BookAdmin(ModelAdmin):
    list_filter = (('employee', RelatedOnlyFieldListFilter),)
modeladmin = BookAdmin(Book, site)
rf = RequestFactory(); request = rf.get('/')
request.user = User(username='a', is_superuser=True, is_staff=True)
changelist = modeladmin.get_changelist_instance(request)
filterspec = changelist.get_filters(request)[0][0]
got = filterspec.lookup_choices
expected = [(albert.pk, 'Albert Green'), (jack.pk, 'Jack Red')]
print("lookup_choices:", got, "expected (narrowed + name order):", expected)
# zed must not appear
zed_absent = zed.pk not in [c[0] for c in got]
print("zed excluded:", zed_absent)
sys.exit(0 if got == expected and zed_absent else 1)
```

Attack 8 — `probe_8.py` → holds on the patched tree (good)

```python
"""Requirement 5.3: fields with explicit static choices keep returning those
choices unchanged; the ordering directive only affects related-model querysets.
A CharField with choices must return exactly its declared choices with blank."""
import django, sys
from django.conf import settings
settings.configure(DEBUG=True,
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
    INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'], USE_TZ=True)
django.setup()
from django.db import models

CHOICES = [('c', 'C label'), ('a', 'A label'), ('b', 'B label')]
class Widget(models.Model):
    kind = models.CharField(max_length=1, choices=CHOICES)
    class Meta: app_label='probeapp'

field = Widget._meta.get_field('kind')
no_blank = field.get_choices(include_blank=False)
with_blank = field.get_choices(include_blank=True)
print("no_blank:", no_blank)
print("with_blank:", with_blank)
ok = (no_blank == CHOICES and with_blank == [('', '---------')] + CHOICES)
sys.exit(0 if ok else 1)
```

Attack 9 — `probe_9.py` → holds on the patched tree (good)

```python
"""Requirement 4.1: RelatedOnlyFieldListFilter orders its narrowed choices by
the related ModelAdmin's ordering when one is registered.
Employee has NO Meta.ordering; EmployeeAdmin ordering=('name',) is registered.
Narrowed set {albert, jack} must be ordered by name -> Albert, Jack.
(This discriminates a fix that only relies on get_choices' empty-ordering
default, which would leave RelatedOnly unordered / pk-ordered here.)"""
import django, sys
from django.conf import settings
settings.configure(DEBUG=True,
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
    INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth',
                    'django.contrib.admin', 'django.contrib.sessions',
                    'django.contrib.messages'],
    USE_TZ=True,
    TEMPLATES=[{'BACKEND': 'django.template.backends.django.DjangoTemplates',
                'DIRS': [], 'APP_DIRS': True, 'OPTIONS': {'context_processors': []}}],
    MIDDLEWARE=[])
django.setup()
from django.db import connection, models

class Employee(models.Model):
    name = models.CharField(max_length=50)
    class Meta: app_label='probeapp'   # NO Meta.ordering -> pk order by default
    def __str__(self): return self.name
class Book(models.Model):
    title = models.CharField(max_length=50)
    employee = models.ForeignKey(Employee, models.SET_NULL, null=True)
    class Meta: app_label='probeapp'
    def __str__(self): return self.title
for m in (Employee, Book):
    with connection.schema_editor() as se:
        se.create_model(m)

from django.contrib.admin import ModelAdmin, site, RelatedOnlyFieldListFilter
from django.contrib.auth.models import User
from django.test import RequestFactory

# jack inserted (lower pk) before albert; ordering by name flips them
jack = Employee.objects.create(name='Jack Red')
albert = Employee.objects.create(name='Albert Green')
Book.objects.create(title='b1', employee=jack)
Book.objects.create(title='b2', employee=albert)

class EmployeeAdmin(ModelAdmin):
    ordering = ('name',)
site.register(Employee, EmployeeAdmin)

class BookAdmin(ModelAdmin):
    list_filter = (('employee', RelatedOnlyFieldListFilter),)
modeladmin = BookAdmin(Book, site)
rf = RequestFactory(); request = rf.get('/')
request.user = User(username='a', is_superuser=True, is_staff=True)
changelist = modeladmin.get_changelist_instance(request)
filterspec = changelist.get_filters(request)[0][0]
got = filterspec.lookup_choices
expected = [(albert.pk, 'Albert Green'), (jack.pk, 'Jack Red')]
print("lookup_choices:", got, "expected (ModelAdmin name order):", expected)
site.unregister(Employee)
sys.exit(0 if got == expected else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Requirement 1.1 (POSITIVE CONTROL): Field.get_choices with EMPTY ordering
preserves the related model's Meta.ordering.
Holds iff choices come back in Meta.ordering order (by 'd')."""
import django
from django.conf import settings
settings.configure(
    DEBUG=True,
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
    INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
    USE_TZ=True,
)
django.setup()
from django.db import connection, models

class Foo(models.Model):
    a = models.CharField(max_length=10)
    d = models.CharField(max_length=10)
    class Meta:
        app_label = 'probeapp'
        ordering = ('d',)
    def __str__(self):
        return self.a

class Bar(models.Model):
    a = models.ForeignKey(Foo, models.CASCADE)
    b = models.CharField(max_length=10)
    class Meta:
        app_label = 'probeapp'
    def __str__(self):
        return self.b

with connection.schema_editor() as se:
    se.create_model(Foo)
    se.create_model(Bar)

# foo1 inserted first (lower pk) but has larger 'd'; foo2 has smaller 'd'.
foo1 = Foo.objects.create(a='a', d='12.35')
foo2 = Foo.objects.create(a='b', d='12.34')
field = Bar._meta.get_field('a')

choices = field.get_choices(include_blank=False, ordering=())
values = [c[0] for c in choices]
print("choices values:", values, "expected (Meta.ordering by d):", [foo2.pk, foo1.pk])
import sys
sys.exit(0 if values == [foo2.pk, foo1.pk] else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Probe coverage vs requirements (all HOLD on gold-patched tree):
- probe_1 (Req 1.1, POSITIVE CONTROL): Field.get_choices with empty ordering preserves related Meta.ordering. HOLDS patched=[2,1], VIOLATED at base=[1,2] -> discriminates.
- probe_2 (Req 1.2 & 5.1): non-empty ordering re-sequences (asc/desc), overriding Meta.ordering. HOLDS.
- probe_3 (Req 2.1): ForeignObjectRel.get_choices empty ordering preserves reverse Meta.ordering. HOLDS.
- probe_4 (Req 2.2/2.3): reverse non-empty ordering re-sequences; (pk,str) structure + blank prepend. HOLDS.
- probe_5 (Req 3.2): RelatedFieldListFilter falls back to Meta.ordering when no ModelAdmin registered. HOLDS.
- probe_6 (Req 3.1 & 5.2): RelatedFieldListFilter orders by registered ModelAdmin ordering. HOLDS.
- probe_7 (Req 4.2/4.3): RelatedOnlyFieldListFilter orders narrowed set by Meta.ordering AND excludes unreferenced records. HOLDS.
- probe_8 (Req 5.3): fields with static choices return declared choices unchanged (with/without blank). HOLDS.
- probe_9 (Req 4.1): RelatedOnlyFieldListFilter orders narrowed choices by registered ModelAdmin ordering. HOLDS patched.

CANDIDATE weak1_getchoices_only: patches only get_choices in fields/__init__.py + reverse_related.py (the empty-ordering-preserves-default behavior) but leaves admin/filters.py untouched, so RelatedOnlyFieldListFilter never forwards the ModelAdmin ordering. Applies at base_commit. Probes 1,5,6,7 still HOLD under it, but probe_9 (Req 4.1) is VIOLATED (got [Jack,Albert] pk-order vs expected [Albert,Jack] name-order). This is exactly the hidden test test_relatedonlyfieldlistfilter_foreignkey_ordering, so the suite discriminates a requirements-incomplete partial fix -> not a too-weak finding.

Verdict SOUND: >=5 distinct probes covering behavioral SHALLs, boundary (empty vs non-empty ordering), and regression 'SHALL keep' criteria (5.2, 5.3, narrowing in 4.3); positive control fails at base and holds patched; >=1 wrong-fix candidate exercised and REJECTED.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 9 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 9 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 9 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py`, `probe_7.py`, `probe_8.py`, `probe_9.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (9):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

_The 9 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts, and on this backend both roles put it through the same derivation: every block below is a requirement probe run on the gold-patched tree, and the `machine verdict:` line each role publishes above reports BOTH that its probes hold there and how many candidate patches the probe suite rejected — so the two roles re-ran ONE probe suite and each recorded its own outcome for every probe in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `probe_1.py` → holds on the patched tree (good)

Attack 2 — `probe_2.py` → holds on the patched tree (good)

Attack 3 — `probe_3.py` → holds on the patched tree (good)

Attack 4 — `probe_4.py` → holds on the patched tree (good)

Attack 5 — `probe_5.py` → holds on the patched tree (good)

Attack 6 — `probe_6.py` → holds on the patched tree (good)

Attack 7 — `probe_7.py` → holds on the patched tree (good)

Attack 8 — `probe_8.py` → holds on the patched tree (good)

Attack 9 — `probe_9.py` → holds on the patched tree (good)

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Requirement 1.1 (POSITIVE CONTROL): Field.get_choices with EMPTY ordering
preserves the related model's Meta.ordering.
Holds iff choices come back in Meta.ordering order (by 'd')."""
import django
from django.conf import settings
settings.configure(
    DEBUG=True,
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
    INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
    USE_TZ=True,
)
django.setup()
from django.db import connection, models

class Foo(models.Model):
    a = models.CharField(max_length=10)
    d = models.CharField(max_length=10)
    class Meta:
        app_label = 'probeapp'
        ordering = ('d',)
    def __str__(self):
        return self.a

class Bar(models.Model):
    a = models.ForeignKey(Foo, models.CASCADE)
    b = models.CharField(max_length=10)
    class Meta:
        app_label = 'probeapp'
    def __str__(self):
        return self.b

with connection.schema_editor() as se:
    se.create_model(Foo)
    se.create_model(Bar)

# foo1 inserted first (lower pk) but has larger 'd'; foo2 has smaller 'd'.
foo1 = Foo.objects.create(a='a', d='12.35')
foo2 = Foo.objects.create(a='b', d='12.34')
field = Bar._meta.get_field('a')

choices = field.get_choices(include_blank=False, ordering=())
values = [c[0] for c in choices]
print("choices values:", values, "expected (Meta.ordering by d):", [foo2.pk, foo1.pk])
import sys
sys.exit(0 if values == [foo2.pk, foo1.pk] else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Probe coverage vs requirements (all HOLD on gold-patched tree):
- probe_1 (Req 1.1, POSITIVE CONTROL): Field.get_choices with empty ordering preserves related Meta.ordering. HOLDS patched=[2,1], VIOLATED at base=[1,2] -> discriminates.
- probe_2 (Req 1.2 & 5.1): non-empty ordering re-sequences (asc/desc), overriding Meta.ordering. HOLDS.
- probe_3 (Req 2.1): ForeignObjectRel.get_choices empty ordering preserves reverse Meta.ordering. HOLDS.
- probe_4 (Req 2.2/2.3): reverse non-empty ordering re-sequences; (pk,str) structure + blank prepend. HOLDS.
- probe_5 (Req 3.2): RelatedFieldListFilter falls back to Meta.ordering when no ModelAdmin registered. HOLDS.
- probe_6 (Req 3.1 & 5.2): RelatedFieldListFilter orders by registered ModelAdmin ordering. HOLDS.
- probe_7 (Req 4.2/4.3): RelatedOnlyFieldListFilter orders narrowed set by Meta.ordering AND excludes unreferenced records. HOLDS.
- probe_8 (Req 5.3): fields with static choices return declared choices unchanged (with/without blank). HOLDS.
- probe_9 (Req 4.1): RelatedOnlyFieldListFilter orders narrowed choices by registered ModelAdmin ordering. HOLDS patched.

CANDIDATE weak1_getchoices_only: patches only get_choices in fields/__init__.py + reverse_related.py (the empty-ordering-preserves-default behavior) but leaves admin/filters.py untouched, so RelatedOnlyFieldListFilter never forwards the ModelAdmin ordering. Applies at base_commit. Probes 1,5,6,7 still HOLD under it, but probe_9 (Req 4.1) is VIOLATED (got [Jack,Albert] pk-order vs expected [Albert,Jack] name-order). This is exactly the hidden test test_relatedonlyfieldlistfilter_foreignkey_ordering, so the suite discriminates a requirements-incomplete partial fix -> not a too-weak finding.

Verdict SOUND: >=5 distinct probes covering behavioral SHALLs, boundary (empty vs non-empty ordering), and regression 'SHALL keep' criteria (5.2, 5.3, narrowing in 4.3); positive control fails at base and holds patched; >=1 wrong-fix candidate exercised and REJECTED.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Patch spans 3 files: (a) Field.get_choices and (b) ForeignObjectRel.get_choices now only call order_by when ordering is truthy, otherwise leaving _default_manager's default (Meta.ordering) intact — Reqs 1.1/1.2/2.1/2.2/5.1. (c) filters.py extracts field_admin_ordering (returns registered ModelAdmin.get_ordering or () ) — Req 3.4; RelatedFieldListFilter uses it (Reqs 3.1-3.3), RelatedOnlyFieldListFilter now passes ordering while keeping limit_choices_to={'pk__in': pk_qs} narrowing (Reqs 4.1-4.3). Requirements 1.3/1.4/1.5/2.3/5.3/5.4/5.5 are regression-protection of unchanged behavior (blank prepend, limit_choices_to, str(x) coercion, static choices, other filters) — all consistent with code the patch leaves untouched. Modeling boundary is correct: pinned to the changed observable = choice ORDER as a function of ordering-directive emptiness, not a single branch/helper in isolation. FAITHFUL.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The requirements localize the change by naming the two filter classes (RelatedFieldListFilter, RelatedOnlyFieldListFilter, filters.py) and the choice-building helpers Field.get_choices (fields/__init__.py) and ForeignObjectRel.get_choices (reverse_related.py). All of the filter/filters.py content is already in the public problem_statement; naming the get_choices helpers is legitimate localization of the gold edit's files, not a leak. The document translates what the hidden tests check into behavioral requirements (empty ordering directive preserves the related model's Meta.ordering; both filters fall back to ModelAdmin ordering then Meta.ordering) without transmitting the tests themselves: no test function names/paths (tests/admin_filters/tests.py, tests/model_fields/tests.py), no FAIL_TO_PASS ids, no fixture identifiers (Employee, Foo, Bar, Book, 'Jack Red'/'John Blue', book titles, the d='12.35' data tweak), and no expected-list enumerations mirroring the parametrized cases. Req 3 AC4 describes the gold's invented helper field_admin_ordering purely behaviorally ('a single shared step that returns the related ModelAdmin's ordering ... and an empty ordering otherwise') without naming the invented identifier. limit_choices_to is public Django API. This is behavior description, not test reconstruction.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
