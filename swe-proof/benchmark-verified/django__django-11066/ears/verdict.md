# P2 adversarial audit — django__django-11066

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
# Requirement 1.2/1.3 (POSITIVE CONTROL): with a router whose write target is
# 'default', renaming forward against 'other' persists renamedfoo to 'other'
# and NOT to 'default'. Holds on gold-patched, fails at base.
import os, tempfile
d = tempfile.mkdtemp()
import django
from django.conf import settings
settings.configure(
    DEBUG=True,
    DATABASES={
        'default': {'ENGINE':'django.db.backends.sqlite3','NAME': os.path.join(d,'default.sqlite3')},
        'other':   {'ENGINE':'django.db.backends.sqlite3','NAME': os.path.join(d,'other.sqlite3')},
    },
    INSTALLED_APPS=['django.contrib.contenttypes','django.contrib.auth'],
    DATABASE_ROUTERS=[],
)
django.setup()
from django.apps import apps
from django.db import connections
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.management import RenameContentType

for alias in ('default','other'):
    with connections[alias].schema_editor() as se:
        se.create_model(ContentType)

# Router that ALWAYS writes to default (the bug trigger)
class Router:
    def db_for_write(self, model, **hints):
        return 'default'
    def db_for_read(self, model, **hints):
        return 'default'
settings.DATABASE_ROUTERS = [Router()]

APP='contenttypes_tests'
# seed the row on 'other'
ContentType.objects.using('other').create(app_label=APP, model='foo')

class FakeSE:
    connection = connections['other']

op = RenameContentType(APP, 'foo', 'renamedfoo')
op._rename(apps, FakeSE, 'foo', 'renamedfoo')

other = ContentType.objects.using('other').filter(app_label=APP)
default = ContentType.objects.using('default').filter(app_label=APP)
has_renamed_other = other.filter(model='renamedfoo').exists()
has_foo_other = other.filter(model='foo').exists()
default_count = default.count()
print("other has renamedfoo:", has_renamed_other)
print("other still has foo:", has_foo_other)
print("default row count:", default_count)

ok = has_renamed_other and (not has_foo_other) and default_count == 0
print("CRITERION HOLDS" if ok else "CRITERION FAILS")
import sys; sys.exit(0 if ok else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
# Requirement 1.4: reversing the rename (backward) against 'other' restores
# 'foo' and removes 'renamedfoo' on that same db, under a write->default router.
import os, tempfile, sys
d = tempfile.mkdtemp()
import django
from django.conf import settings
settings.configure(
    DEBUG=True,
    DATABASES={
        'default': {'ENGINE':'django.db.backends.sqlite3','NAME': os.path.join(d,'default.sqlite3')},
        'other':   {'ENGINE':'django.db.backends.sqlite3','NAME': os.path.join(d,'other.sqlite3')},
    },
    INSTALLED_APPS=['django.contrib.contenttypes','django.contrib.auth'],
    DATABASE_ROUTERS=[],
)
django.setup()
from django.apps import apps
from django.db import connections
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.management import RenameContentType
for alias in ('default','other'):
    with connections[alias].schema_editor() as se:
        se.create_model(ContentType)
class WriteDefaultRouter:
    def db_for_write(self, model, **hints):
        return 'default'
    def db_for_read(self, model, **hints):
        return 'default'
class FakeSE:
    connection = connections['other']
APP='contenttypes_tests'
settings.DATABASE_ROUTERS = [WriteDefaultRouter()]
# start in the "renamed" state on other
ContentType.objects.using('other').create(app_label=APP, model='renamedfoo')
op = RenameContentType(APP, 'foo', 'renamedfoo')
op._rename(apps, FakeSE, 'renamedfoo', 'foo')  # backward
other = ContentType.objects.using('other').filter(app_label=APP)
default = ContentType.objects.using('default').filter(app_label=APP)
has_foo = other.filter(model='foo').exists()
has_renamed = other.filter(model='renamedfoo').exists()
dcount = default.count()
print("other has foo:", has_foo, "| other has renamedfoo:", has_renamed, "| default count:", dcount)
ok = has_foo and (not has_renamed) and dcount==0
print("HOLDS" if ok else "FAILS")
sys.exit(0 if ok else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
# Requirement 2.2: if no row for (app_label, old_model) exists on the migration db,
# _rename returns without error and makes no change to any database.
import os, tempfile, sys
d = tempfile.mkdtemp()
import django
from django.conf import settings
settings.configure(
    DEBUG=True,
    DATABASES={
        'default': {'ENGINE':'django.db.backends.sqlite3','NAME': os.path.join(d,'default.sqlite3')},
        'other':   {'ENGINE':'django.db.backends.sqlite3','NAME': os.path.join(d,'other.sqlite3')},
    },
    INSTALLED_APPS=['django.contrib.contenttypes','django.contrib.auth'],
    DATABASE_ROUTERS=[],
)
django.setup()
from django.apps import apps
from django.db import connections
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.management import RenameContentType
for alias in ('default','other'):
    with connections[alias].schema_editor() as se:
        se.create_model(ContentType)
class WriteDefaultRouter:
    def db_for_write(self, model, **hints):
        return 'default'
    def db_for_read(self, model, **hints):
        return 'default'
class FakeSE:
    connection = connections['other']
APP='contenttypes_tests'
settings.DATABASE_ROUTERS = [WriteDefaultRouter()]
# NO seed row anywhere
op = RenameContentType(APP, 'foo', 'renamedfoo')
try:
    op._rename(apps, FakeSE, 'foo', 'renamedfoo')
except Exception as e:
    print("RAISED:", type(e).__name__, e)
    sys.exit(1)
other_c = ContentType.objects.using('other').filter(app_label=APP).count()
default_c = ContentType.objects.using('default').filter(app_label=APP).count()
print("other count:", other_c, "| default count:", default_c)
ok = other_c==0 and default_c==0
print("HOLDS" if ok else "FAILS")
sys.exit(0 if ok else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
# Requirement 3.1/3.2: when the destination natural key already exists on the
# target db, the IntegrityError is caught, the write rolled back (no new row),
# and the in-memory content_type.model is restored to old_model.
import os, tempfile, sys
d = tempfile.mkdtemp()
import django
from django.conf import settings
settings.configure(
    DEBUG=True,
    DATABASES={
        'default': {'ENGINE':'django.db.backends.sqlite3','NAME': os.path.join(d,'default.sqlite3')},
        'other':   {'ENGINE':'django.db.backends.sqlite3','NAME': os.path.join(d,'other.sqlite3')},
    },
    INSTALLED_APPS=['django.contrib.contenttypes','django.contrib.auth'],
    DATABASE_ROUTERS=[],
)
django.setup()
from django.apps import apps
from django.db import connections
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.management import RenameContentType
for alias in ('default','other'):
    with connections[alias].schema_editor() as se:
        se.create_model(ContentType)
class WriteDefaultRouter:
    def db_for_write(self, model, **hints):
        return 'default'
    def db_for_read(self, model, **hints):
        return 'default'
class FakeSE:
    connection = connections['other']
APP='contenttypes_tests'
settings.DATABASE_ROUTERS = [WriteDefaultRouter()]
# seed both foo and renamedfoo on 'other' -> renaming foo->renamedfoo collides
ContentType.objects.using('other').create(app_label=APP, model='foo')
ContentType.objects.using('other').create(app_label=APP, model='renamedfoo')
op = RenameContentType(APP, 'foo', 'renamedfoo')
try:
    op._rename(apps, FakeSE, 'foo', 'renamedfoo')
except Exception as e:
    print("UNEXPECTED RAISE:", type(e).__name__, e)
    sys.exit(1)
other = ContentType.objects.using('other').filter(app_label=APP)
# foo row must still exist (rolled back), still exactly one renamedfoo
foo_still = other.filter(model='foo').exists()
renamed_count = other.filter(model='renamedfoo').count()
print("foo still present:", foo_still, "| renamedfoo count:", renamed_count)
ok = foo_still and renamed_count==1
print("HOLDS" if ok else "FAILS")
sys.exit(0 if ok else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
# Requirement 2.3: if the router disallows migrating ContentType on that db,
# _rename makes no change and returns without error.
import os, tempfile, sys
d = tempfile.mkdtemp()
import django
from django.conf import settings
settings.configure(
    DEBUG=True,
    DATABASES={
        'default': {'ENGINE':'django.db.backends.sqlite3','NAME': os.path.join(d,'default.sqlite3')},
        'other':   {'ENGINE':'django.db.backends.sqlite3','NAME': os.path.join(d,'other.sqlite3')},
    },
    INSTALLED_APPS=['django.contrib.contenttypes','django.contrib.auth'],
    DATABASE_ROUTERS=[],
)
django.setup()
from django.apps import apps
from django.db import connections
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.management import RenameContentType
for alias in ('default','other'):
    with connections[alias].schema_editor() as se:
        se.create_model(ContentType)
class WriteDefaultRouter:
    def db_for_write(self, model, **hints):
        return 'default'
    def db_for_read(self, model, **hints):
        return 'default'
class FakeSE:
    connection = connections['other']
APP='contenttypes_tests'
class DenyRouter:
    def allow_migrate(self, db, app_label, model_name=None, **hints):
        return False
    def db_for_write(self, model, **hints):
        return 'default'
settings.DATABASE_ROUTERS = [DenyRouter()]
ContentType.objects.using('other').create(app_label=APP, model='foo')
op = RenameContentType(APP, 'foo', 'renamedfoo')
try:
    op._rename(apps, FakeSE, 'foo', 'renamedfoo')
except Exception as e:
    print("RAISED:", type(e).__name__, e)
    sys.exit(1)
other = ContentType.objects.using('other').filter(app_label=APP)
foo_intact = other.filter(model='foo').exists()
renamed = other.filter(model='renamedfoo').exists()
print("foo intact:", foo_intact, "| renamedfoo present:", renamed)
ok = foo_intact and (not renamed)
print("HOLDS" if ok else "FAILS")
sys.exit(0 if ok else 1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
# Requirement 1.5: the update is limited to the target row's model field; other
# content-type rows and other databases are left unchanged.
import os, tempfile, sys
d = tempfile.mkdtemp()
import django
from django.conf import settings
settings.configure(
    DEBUG=True,
    DATABASES={
        'default': {'ENGINE':'django.db.backends.sqlite3','NAME': os.path.join(d,'default.sqlite3')},
        'other':   {'ENGINE':'django.db.backends.sqlite3','NAME': os.path.join(d,'other.sqlite3')},
    },
    INSTALLED_APPS=['django.contrib.contenttypes','django.contrib.auth'],
    DATABASE_ROUTERS=[],
)
django.setup()
from django.apps import apps
from django.db import connections
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.management import RenameContentType
for alias in ('default','other'):
    with connections[alias].schema_editor() as se:
        se.create_model(ContentType)
class WriteDefaultRouter:
    def db_for_write(self, model, **hints):
        return 'default'
    def db_for_read(self, model, **hints):
        return 'default'
class FakeSE:
    connection = connections['other']
APP='contenttypes_tests'
settings.DATABASE_ROUTERS = [WriteDefaultRouter()]
ContentType.objects.using('other').create(app_label=APP, model='foo')
# an unrelated row on 'other' and a row on 'default'
ContentType.objects.using('other').create(app_label=APP, model='bar')
ContentType.objects.using('default').create(app_label=APP, model='foo')
op = RenameContentType(APP, 'foo', 'renamedfoo')
op._rename(apps, FakeSE, 'foo', 'renamedfoo')
other = ContentType.objects.using('other').filter(app_label=APP)
default = ContentType.objects.using('default').filter(app_label=APP)
bar_intact = other.filter(model='bar').exists()
renamed = other.filter(model='renamedfoo').exists()
# default 'foo' must be untouched, no renamedfoo on default
default_foo = default.filter(model='foo').exists()
default_renamed = default.filter(model='renamedfoo').exists()
print("other bar intact:", bar_intact, "| other renamedfoo:", renamed)
print("default foo intact:", default_foo, "| default renamedfoo:", default_renamed)
ok = bar_intact and renamed and default_foo and (not default_renamed)
print("HOLDS" if ok else "FAILS")
sys.exit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
# Requirement 1.2/1.3 (POSITIVE CONTROL): with a router whose write target is
# 'default', renaming forward against 'other' persists renamedfoo to 'other'
# and NOT to 'default'. Holds on gold-patched, fails at base.
import os, tempfile
d = tempfile.mkdtemp()
import django
from django.conf import settings
settings.configure(
    DEBUG=True,
    DATABASES={
        'default': {'ENGINE':'django.db.backends.sqlite3','NAME': os.path.join(d,'default.sqlite3')},
        'other':   {'ENGINE':'django.db.backends.sqlite3','NAME': os.path.join(d,'other.sqlite3')},
    },
    INSTALLED_APPS=['django.contrib.contenttypes','django.contrib.auth'],
    DATABASE_ROUTERS=[],
)
django.setup()
from django.apps import apps
from django.db import connections
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.management import RenameContentType

for alias in ('default','other'):
    with connections[alias].schema_editor() as se:
        se.create_model(ContentType)

# Router that ALWAYS writes to default (the bug trigger)
class Router:
    def db_for_write(self, model, **hints):
        return 'default'
    def db_for_read(self, model, **hints):
        return 'default'
settings.DATABASE_ROUTERS = [Router()]

APP='contenttypes_tests'
# seed the row on 'other'
ContentType.objects.using('other').create(app_label=APP, model='foo')

class FakeSE:
    connection = connections['other']

op = RenameContentType(APP, 'foo', 'renamedfoo')
op._rename(apps, FakeSE, 'foo', 'renamedfoo')

other = ContentType.objects.using('other').filter(app_label=APP)
default = ContentType.objects.using('default').filter(app_label=APP)
has_renamed_other = other.filter(model='renamedfoo').exists()
has_foo_other = other.filter(model='foo').exists()
default_count = default.count()
print("other has renamedfoo:", has_renamed_other)
print("other still has foo:", has_foo_other)
print("default row count:", default_count)

ok = has_renamed_other and (not has_foo_other) and default_count == 0
print("CRITERION HOLDS" if ok else "CRITERION FAILS")
import sys; sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

django__django-11066: gold fix is content_type.save(using=db, update_fields={'model'}) in RenameContentType._rename. Probes drive _rename directly with a two-sqlite-db config (default/other), a router that writes to 'default', and schema_editor.connection.alias='other'.

Probe results (all HOLD on gold-patched tree):
- probe_1 (Req 1.2/1.3, POSITIVE CONTROL): forward rename against 'other' under write->default router persists renamedfoo to 'other', not to 'default'. HOLDS patched; FAILS at base with 'Save with update_fields did not affect any rows.' (DatabaseError) — discriminates.
- probe_2 (Req 1.4): backward rename restores 'foo' on 'other', removes 'renamedfoo', default untouched. HOLDS.
- probe_3 (Req 2.2): missing (app_label, old_model) on migration db -> no change, no error. HOLDS.
- probe_4 (Req 3.1/3.2): destination natural key already present -> IntegrityError caught, rolled back, foo row preserved, single renamedfoo. HOLDS.
- probe_5 (Req 2.3): router allow_migrate=False -> no change, no error. HOLDS.
- probe_6 (Req 1.5): update limited to target row; unrelated 'other' row and 'default' rows untouched. HOLDS.

Candidate wrong-fix (weak_router.diff): save(using=router.db_for_write(ContentType), ...) instead of using=db. REJECTED by probe_1 (positive control) — same base-style DatabaseError because the write is directed at the router's 'default' db where the row does not exist. Demonstrates the suite discriminates a plausibly-wrong reading (direct at router target) from the correct fix (direct at schema_editor.connection.alias).

>=5 distinct probes all hold on patched; positive control fails at base and under the wrong candidate. No violation or too-weak finding. SOUND.

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
# Requirement 1.2/1.3 (POSITIVE CONTROL): with a router whose write target is
# 'default', renaming forward against 'other' persists renamedfoo to 'other'
# and NOT to 'default'. Holds on gold-patched, fails at base.
import os, tempfile
d = tempfile.mkdtemp()
import django
from django.conf import settings
settings.configure(
    DEBUG=True,
    DATABASES={
        'default': {'ENGINE':'django.db.backends.sqlite3','NAME': os.path.join(d,'default.sqlite3')},
        'other':   {'ENGINE':'django.db.backends.sqlite3','NAME': os.path.join(d,'other.sqlite3')},
    },
    INSTALLED_APPS=['django.contrib.contenttypes','django.contrib.auth'],
    DATABASE_ROUTERS=[],
)
django.setup()
from django.apps import apps
from django.db import connections
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.management import RenameContentType

for alias in ('default','other'):
    with connections[alias].schema_editor() as se:
        se.create_model(ContentType)

# Router that ALWAYS writes to default (the bug trigger)
class Router:
    def db_for_write(self, model, **hints):
        return 'default'
    def db_for_read(self, model, **hints):
        return 'default'
settings.DATABASE_ROUTERS = [Router()]

APP='contenttypes_tests'
# seed the row on 'other'
ContentType.objects.using('other').create(app_label=APP, model='foo')

class FakeSE:
    connection = connections['other']

op = RenameContentType(APP, 'foo', 'renamedfoo')
op._rename(apps, FakeSE, 'foo', 'renamedfoo')

other = ContentType.objects.using('other').filter(app_label=APP)
default = ContentType.objects.using('default').filter(app_label=APP)
has_renamed_other = other.filter(model='renamedfoo').exists()
has_foo_other = other.filter(model='foo').exists()
default_count = default.count()
print("other has renamedfoo:", has_renamed_other)
print("other still has foo:", has_foo_other)
print("default row count:", default_count)

ok = has_renamed_other and (not has_foo_other) and default_count == 0
print("CRITERION HOLDS" if ok else "CRITERION FAILS")
import sys; sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

django__django-11066: gold fix is content_type.save(using=db, update_fields={'model'}) in RenameContentType._rename. Probes drive _rename directly with a two-sqlite-db config (default/other), a router that writes to 'default', and schema_editor.connection.alias='other'.

Probe results (all HOLD on gold-patched tree):
- probe_1 (Req 1.2/1.3, POSITIVE CONTROL): forward rename against 'other' under write->default router persists renamedfoo to 'other', not to 'default'. HOLDS patched; FAILS at base with 'Save with update_fields did not affect any rows.' (DatabaseError) — discriminates.
- probe_2 (Req 1.4): backward rename restores 'foo' on 'other', removes 'renamedfoo', default untouched. HOLDS.
- probe_3 (Req 2.2): missing (app_label, old_model) on migration db -> no change, no error. HOLDS.
- probe_4 (Req 3.1/3.2): destination natural key already present -> IntegrityError caught, rolled back, foo row preserved, single renamedfoo. HOLDS.
- probe_5 (Req 2.3): router allow_migrate=False -> no change, no error. HOLDS.
- probe_6 (Req 1.5): update limited to target row; unrelated 'other' row and 'default' rows untouched. HOLDS.

Candidate wrong-fix (weak_router.diff): save(using=router.db_for_write(ContentType), ...) instead of using=db. REJECTED by probe_1 (positive control) — same base-style DatabaseError because the write is directed at the router's 'default' db where the row does not exist. Demonstrates the suite discriminates a plausibly-wrong reading (direct at router target) from the correct fix (direct at schema_editor.connection.alias).

>=5 distinct probes all hold on patched; positive control fails at base and under the wrong candidate. No violation or too-weak finding. SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Modeling boundary is correctly on the changed observable behavior (writes routed to schema_editor.connection.alias independent of the router), which is exactly what the one-line save(using=db) fix accomplishes and what the added F2P test asserts. Requirements 2 and 3 describe surrounding unchanged logic (lookup, allow_migrate, IntegrityError fallback, cache clear) accurately and as preserved context, not as the change. Verified _rename source live in the gold-patched instance image.

Counterexample / evidence:

```
N/A — no input distinguishes the requirements from the patched code's behavior.
```


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The public problem_statement is highly detailed: it already discloses the target method (RenameContentType._rename), the file path (django/contrib/contenttypes/management/__init__.py), schema_editor.connection.alias, transaction.atomic(using=db), the exact defective line content_type.save(update_fields={'model'}) and the proposed fix content_type.save(using=db, update_fields={'model'}), OperationalError, and the router-writes-to-wrong-database scenario. Every identifier/behavior in requirements.md is either public or a legitimate behavioral description. The hidden test (test_existing_content_type_rename_other_database; TestRouter.db_for_write->'default'; databases {'default','other'}; model 'foo'->'renamedfoo'; forward + migrate-to-zero reverse) is NOT transmitted: no test function name, no test file path, no 'other'/'default' alias literals, no 'foo'/'renamedfoo' literals, no TestRouter identifier, no parametrization ids. Req 1.3/1.4's forward+reverse persistence maps to the test's structure but is stated generically (old_model/new_model) and reflects standard migration reversibility — behavior translation, which is the intended purpose. Conflict-fallback/cache-invalidation criteria describe existing surrounding code being preserved. No leakage beyond the problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
