# P2 adversarial audit — django__django-12708

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

Counterexample / evidence:

```
Naive fix (change guard `if len(constraint_names) != 1` -> `< 1`, then delete constraint_names[0]) is REJECTED by the suite: probe_1 fails (it deletes the unique constraint instead of the ordinary index when both match — constraint_names[0] is arbitrary; here the index stays and something else is dropped), probe_5 fails (0-match guard no longer raises the required ValueError), probe_6 fails (does not select the exact-column non-unique index). This demonstrates discriminating power against a requirements-under-reading fix.
```

**Attacks re-run (6):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
"""POSITIVE CONTROL + Req1.3/1.4: Removing an index_together over columns that
also have a unique_together must NOT raise, must drop the ordinary index, and
must leave the unique constraint in place.

HOLDS iff: alter_index_together([(pink,weight)] -> []) completes without error,
the non-unique index over (pink,weight) is gone, and the unique constraint over
(pink,weight) still exists.

At base (unpatched) this raises ValueError("Found wrong number (2) ...") because
the filter {'index': True} matches both the index and the unique constraint.
"""
import os
import sys
# Create a real on-disk app package so Django's app loading works cleanly.
_d = '$SCRATCH'
os.makedirs(_d, exist_ok=True)
open(os.path.join(_d, '__init__.py'), 'w').close()
open(os.path.join(_d, 'models.py'), 'w').close()
sys.path.insert(0, '/tmp')
import django
from django.conf import settings

settings.configure(
    INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth', 'probeapp'],
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
    DEFAULT_AUTO_FIELD='django.db.models.AutoField',
)
django.setup()
from django.db import connection, models


def make_model():
    Meta = type('Meta', (), {'app_label': 'probeapp', 'unique_together': {('pink', 'weight')}})
    return type('Pony', (models.Model,), {
        '__module__': 'probeapp.models',
        'pink': models.IntegerField(),
        'weight': models.FloatField(),
        'Meta': Meta,
    })


def cons(table):
    with connection.cursor() as c:
        return connection.introspection.get_constraints(c, table)


def has_index(table, cols):
    return any(list(i['columns']) == cols and i['index'] and not i['unique']
               for i in cons(table).values())


def has_unique(table, cols):
    return any(list(i['columns']) == cols and i['unique'] for i in cons(table).values())


Pony = make_model()
table = Pony._meta.db_table
cols = ['pink', 'weight']

with connection.schema_editor() as editor:
    editor.create_model(Pony)
    # Add the index_together (ordinary composite index) over the same columns.
    editor.alter_index_together(Pony, set(), {('pink', 'weight')})

assert has_unique(table, cols), "setup: unique constraint should exist"
assert has_index(table, cols), "setup: ordinary index should exist"
print("SETUP: unique + index both present over", cols)

try:
    with connection.schema_editor() as editor:
        editor.alter_index_together(Pony, {('pink', 'weight')}, set())
except Exception as e:
    print("VIOLATED: removing index_together raised:", type(e).__name__, e)
    sys.exit(1)

idx = has_index(table, cols)
uniq = has_unique(table, cols)
print(f"AFTER REMOVE: ordinary_index_present={idx} unique_present={uniq}")
if idx:
    print("VIOLATED: ordinary index still present after removal")
    sys.exit(1)
if not uniq:
    print("VIOLATED: unique constraint was dropped")
    sys.exit(1)
print("HOLDS: index dropped, unique preserved, no error")
sys.exit(0)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
import os
import sys
_d = '$SCRATCH'
os.makedirs(_d, exist_ok=True)
open(os.path.join(_d, '__init__.py'), 'w').close()
open(os.path.join(_d, 'models.py'), 'w').close()
sys.path.insert(0, '/tmp')
import django
from django.conf import settings
settings.configure(
    INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth', 'probeapp'],
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
    DEFAULT_AUTO_FIELD='django.db.models.AutoField',
)
django.setup()
from django.db import connection, models


def cons(table):
    with connection.cursor() as c:
        return connection.introspection.get_constraints(c, table)


def has_index(table, cols):
    return any(list(i['columns']) == cols and i['index'] and not i['unique']
               for i in cons(table).values())


def has_unique(table, cols):
    return any(list(i['columns']) == cols and i['unique'] for i in cons(table).values())


def mk(unique=False, name='Pony', it=None):
    a = {'__module__': 'probeapp.models',
         'pink': models.IntegerField(), 'weight': models.FloatField()}
    m = {'app_label': 'probeapp'}
    if unique:
        m['unique_together'] = {('pink', 'weight')}
    if it is not None:
        m['index_together'] = it
    a['Meta'] = type('Meta', (), m)
    return type(name, (models.Model,), a)

# Model with NO unique_together. Add an index_together, then remove it.
Pony = mk(unique=False, name='PonyR2')
table = Pony._meta.db_table
cols = ['pink', 'weight']
with connection.schema_editor() as e:
    e.create_model(Pony)
    e.alter_index_together(Pony, set(), {('pink', 'weight')})
assert not has_unique(table, cols), "setup: no unique expected"
assert has_index(table, cols), "setup: index expected"
print("SETUP: index only (no unique)")
try:
    with connection.schema_editor() as e:
        e.alter_index_together(Pony, {('pink', 'weight')}, set())
except Exception as ex:
    print("VIOLATED: removal raised:", type(ex).__name__, ex); sys.exit(1)
print("AFTER: index_present=%s" % has_index(table, cols))
if has_index(table, cols):
    print("VIOLATED: index not dropped"); sys.exit(1)
print("HOLDS: non-overlapping index dropped as before"); sys.exit(0)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
import os
import sys
_d = '$SCRATCH'
os.makedirs(_d, exist_ok=True)
open(os.path.join(_d, '__init__.py'), 'w').close()
open(os.path.join(_d, 'models.py'), 'w').close()
sys.path.insert(0, '/tmp')
import django
from django.conf import settings
settings.configure(
    INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth', 'probeapp'],
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
    DEFAULT_AUTO_FIELD='django.db.models.AutoField',
)
django.setup()
from django.db import connection, models


def cons(table):
    with connection.cursor() as c:
        return connection.introspection.get_constraints(c, table)


def has_index(table, cols):
    return any(list(i['columns']) == cols and i['index'] and not i['unique']
               for i in cons(table).values())


def has_unique(table, cols):
    return any(list(i['columns']) == cols and i['unique'] for i in cons(table).values())


def mk(unique=False, name='Pony', it=None):
    a = {'__module__': 'probeapp.models',
         'pink': models.IntegerField(), 'weight': models.FloatField()}
    m = {'app_label': 'probeapp'}
    if unique:
        m['unique_together'] = {('pink', 'weight')}
    if it is not None:
        m['index_together'] = it
    a['Meta'] = type('Meta', (), m)
    return type(name, (models.Model,), a)

Pony = mk(unique=True, name='PonyR3')
table = Pony._meta.db_table
cols = ['pink', 'weight']
with connection.schema_editor() as e:
    e.create_model(Pony)
assert has_unique(table, cols), "setup: unique expected"
print("SETUP: unique present")
try:
    with connection.schema_editor() as e:
        e.alter_unique_together(Pony, {('pink', 'weight')}, set())
except Exception as ex:
    print("VIOLATED: alter_unique_together removal raised:", type(ex).__name__, ex); sys.exit(1)
u = has_unique(table, cols)
print("AFTER: unique_present=%s" % u)
if u:
    print("VIOLATED: unique constraint not dropped"); sys.exit(1)
print("HOLDS: unique_together removal drops unique via unique-only filter"); sys.exit(0)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
import os
import sys
_d = '$SCRATCH'
os.makedirs(_d, exist_ok=True)
open(os.path.join(_d, '__init__.py'), 'w').close()
open(os.path.join(_d, 'models.py'), 'w').close()
sys.path.insert(0, '/tmp')
import django
from django.conf import settings
settings.configure(
    INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth', 'probeapp'],
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
    DEFAULT_AUTO_FIELD='django.db.models.AutoField',
)
django.setup()
from django.db import connection, models


def cons(table):
    with connection.cursor() as c:
        return connection.introspection.get_constraints(c, table)


def has_index(table, cols):
    return any(list(i['columns']) == cols and i['index'] and not i['unique']
               for i in cons(table).values())


def has_unique(table, cols):
    return any(list(i['columns']) == cols and i['unique'] for i in cons(table).values())


def mk(unique=False, name='Pony', it=None):
    a = {'__module__': 'probeapp.models',
         'pink': models.IntegerField(), 'weight': models.FloatField()}
    m = {'app_label': 'probeapp'}
    if unique:
        m['unique_together'] = {('pink', 'weight')}
    if it is not None:
        m['index_together'] = it
    a['Meta'] = type('Meta', (), m)
    return type(name, (models.Model,), a)

Pony = mk(unique=False, name='PonyR4')
table = Pony._meta.db_table
cols = ['pink', 'weight']
with connection.schema_editor() as e:
    e.create_model(Pony)
assert not has_index(table, cols)
print("SETUP: no index yet")
with connection.schema_editor() as e:
    e.alter_index_together(Pony, set(), {('pink', 'weight')})
i = has_index(table, cols)
print("AFTER ADD: index_present=%s" % i)
if not i:
    print("VIOLATED: index not created"); sys.exit(1)
print("HOLDS: composed index created for new index_together"); sys.exit(0)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
import os
import sys
_d = '$SCRATCH'
os.makedirs(_d, exist_ok=True)
open(os.path.join(_d, '__init__.py'), 'w').close()
open(os.path.join(_d, 'models.py'), 'w').close()
sys.path.insert(0, '/tmp')
import django
from django.conf import settings
settings.configure(
    INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth', 'probeapp'],
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
    DEFAULT_AUTO_FIELD='django.db.models.AutoField',
)
django.setup()
from django.db import connection, models


def cons(table):
    with connection.cursor() as c:
        return connection.introspection.get_constraints(c, table)


def has_index(table, cols):
    return any(list(i['columns']) == cols and i['index'] and not i['unique']
               for i in cons(table).values())


def has_unique(table, cols):
    return any(list(i['columns']) == cols and i['unique'] for i in cons(table).values())


def mk(unique=False, name='Pony', it=None):
    a = {'__module__': 'probeapp.models',
         'pink': models.IntegerField(), 'weight': models.FloatField()}
    m = {'app_label': 'probeapp'}
    if unique:
        m['unique_together'] = {('pink', 'weight')}
    if it is not None:
        m['index_together'] = it
    a['Meta'] = type('Meta', (), m)
    return type(name, (models.Model,), a)

Pony = mk(unique=True, name='PonyR5')
table = Pony._meta.db_table
cols = ['pink', 'weight']
with connection.schema_editor() as e:
    e.create_model(Pony)
assert has_unique(table, cols) and not has_index(table, cols)
print("SETUP: unique present, no ordinary index")
raised = False
msg = ""
try:
    with connection.schema_editor() as e:
        # Pretend the old index_together had these cols though no index exists.
        e.alter_index_together(Pony, {('pink', 'weight')}, set())
except ValueError as ex:
    raised = True; msg = str(ex)
except Exception as ex:
    print("VIOLATED: wrong exception type:", type(ex).__name__, ex); sys.exit(1)
print("RAISED=%s msg=%r" % (raised, msg))
if not raised:
    print("VIOLATED: guard did not raise ValueError on 0 matches"); sys.exit(1)
if "Found wrong number (0)" not in msg or table not in msg:
    print("VIOLATED: ValueError message/format changed"); sys.exit(1)
# and the unique must remain untouched
if not has_unique(table, cols):
    print("VIOLATED: unique constraint disturbed"); sys.exit(1)
print("HOLDS: exactly-one guard preserved with original message/format"); sys.exit(0)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
import os
import sys
_d = '$SCRATCH'
os.makedirs(_d, exist_ok=True)
open(os.path.join(_d, '__init__.py'), 'w').close()
open(os.path.join(_d, 'models.py'), 'w').close()
sys.path.insert(0, '/tmp')
import django
from django.conf import settings
settings.configure(
    INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth', 'probeapp'],
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
    DEFAULT_AUTO_FIELD='django.db.models.AutoField',
)
django.setup()
from django.db import connection, models


def cons(table):
    with connection.cursor() as c:
        return connection.introspection.get_constraints(c, table)


def has_index(table, cols):
    return any(list(i['columns']) == cols and i['index'] and not i['unique']
               for i in cons(table).values())


def has_unique(table, cols):
    return any(list(i['columns']) == cols and i['unique'] for i in cons(table).values())


def mk(unique=False, name='Pony', it=None):
    a = {'__module__': 'probeapp.models',
         'pink': models.IntegerField(), 'weight': models.FloatField()}
    m = {'app_label': 'probeapp'}
    if unique:
        m['unique_together'] = {('pink', 'weight')}
    if it is not None:
        m['index_together'] = it
    a['Meta'] = type('Meta', (), m)
    return type(name, (models.Model,), a)

Pony = mk(unique=True, name='PonyR6')
table = Pony._meta.db_table
cols = ['pink', 'weight']
with connection.schema_editor() as e:
    e.create_model(Pony)
    # ordinary composite index over (pink,weight)
    e.alter_index_together(Pony, set(), {('pink', 'weight')})
    # a separate single-column ordinary index over (weight,)
    e.alter_index_together(Pony, {('pink', 'weight')}, {('pink', 'weight'), ('weight',)})
assert has_unique(table, cols)
assert has_index(table, cols)
assert has_index(table, ['weight'])
print("SETUP: unique(pink,weight)+index(pink,weight)+index(weight)")
try:
    with connection.schema_editor() as e:
        e.alter_index_together(Pony, {('pink', 'weight'), ('weight',)}, {('weight',)})
except Exception as ex:
    print("VIOLATED: removal raised:", type(ex).__name__, ex); sys.exit(1)
i_pw = has_index(table, cols)
i_w = has_index(table, ['weight'])
u = has_unique(table, cols)
print("AFTER: index(pink,weight)=%s index(weight)=%s unique(pink,weight)=%s" % (i_pw, i_w, u))
if i_pw:
    print("VIOLATED: exact-column index not dropped"); sys.exit(1)
if not i_w:
    print("VIOLATED: different-column index wrongly dropped"); sys.exit(1)
if not u:
    print("VIOLATED: unique wrongly dropped"); sys.exit(1)
print("HOLDS: only exact-column non-unique index dropped"); sys.exit(0)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""POSITIVE CONTROL + Req1.3/1.4: Removing an index_together over columns that
also have a unique_together must NOT raise, must drop the ordinary index, and
must leave the unique constraint in place.

HOLDS iff: alter_index_together([(pink,weight)] -> []) completes without error,
the non-unique index over (pink,weight) is gone, and the unique constraint over
(pink,weight) still exists.

At base (unpatched) this raises ValueError("Found wrong number (2) ...") because
the filter {'index': True} matches both the index and the unique constraint.
"""
import os
import sys
# Create a real on-disk app package so Django's app loading works cleanly.
_d = '$SCRATCH'
os.makedirs(_d, exist_ok=True)
open(os.path.join(_d, '__init__.py'), 'w').close()
open(os.path.join(_d, 'models.py'), 'w').close()
sys.path.insert(0, '/tmp')
import django
from django.conf import settings

settings.configure(
    INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth', 'probeapp'],
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
    DEFAULT_AUTO_FIELD='django.db.models.AutoField',
)
django.setup()
from django.db import connection, models


def make_model():
    Meta = type('Meta', (), {'app_label': 'probeapp', 'unique_together': {('pink', 'weight')}})
    return type('Pony', (models.Model,), {
        '__module__': 'probeapp.models',
        'pink': models.IntegerField(),
        'weight': models.FloatField(),
        'Meta': Meta,
    })


def cons(table):
    with connection.cursor() as c:
        return connection.introspection.get_constraints(c, table)


def has_index(table, cols):
    return any(list(i['columns']) == cols and i['index'] and not i['unique']
               for i in cons(table).values())


def has_unique(table, cols):
    return any(list(i['columns']) == cols and i['unique'] for i in cons(table).values())


Pony = make_model()
table = Pony._meta.db_table
cols = ['pink', 'weight']

with connection.schema_editor() as editor:
    editor.create_model(Pony)
    # Add the index_together (ordinary composite index) over the same columns.
    editor.alter_index_together(Pony, set(), {('pink', 'weight')})

assert has_unique(table, cols), "setup: unique constraint should exist"
assert has_index(table, cols), "setup: ordinary index should exist"
print("SETUP: unique + index both present over", cols)

try:
    with connection.schema_editor() as editor:
        editor.alter_index_together(Pony, {('pink', 'weight')}, set())
except Exception as e:
    print("VIOLATED: removing index_together raised:", type(e).__name__, e)
    sys.exit(1)

idx = has_index(table, cols)
uniq = has_unique(table, cols)
print(f"AFTER REMOVE: ordinary_index_present={idx} unique_present={uniq}")
if idx:
    print("VIOLATED: ordinary index still present after removal")
    sys.exit(1)
if not uniq:
    print("VIOLATED: unique constraint was dropped")
    sys.exit(1)
print("HOLDS: index dropped, unique preserved, no error")
sys.exit(0)
```

Prepatch bug re-encoded as an attack: `True`.

Instance django__django-12708: fix restricts _delete_composed_index search for a removed index_together to constraints that are index-backed AND NOT unique, via filter {'index': True, 'unique': False}, so removing an index_together over columns also covered by unique_together no longer crashes with ValueError('Found wrong number (2) ...').

Probes run in the official docker image (python3.6/testbed) using an in-memory sqlite backend (allows_multiple_constraints_on_same_fields=True, matching the F2P test's skip guard). Each probe registers a real on-disk package so Django app-loading works.

Results (gold-patched / base / weak-candidate):
- probe_1 (POS CONTROL; Req1.3,1.4): remove overlapping index_together -> no error, ordinary index dropped, unique preserved. HOLDS patched / VIOLATED base...') / REJECTED by weak.
- probe_2 (Req2.5): remove non-overlapping index_together still drops the single index. HOLDS patched / (accepts weak, as expected — not a discriminator).
- probe_3 (Req2.4): alter_unique_together removal still drops the unique via unique-only filter. HOLDS patched.
- probe_4 (Req2.3): adding a new index_together creates the composed index. HOLDS patched.
- probe_5 (Req2.1): exactly-one guard preserved — 0 non-unique-index matches still raises ValueError with the original 'Found wrong number (0)...' message/table. HOLDS patched / REJECTED by weak.
- probe_6 (Req2.6,1.2): column-exactness + unique-not-counted — with unique(pink,weight)+index(pink,weight)+index(weight), removing index_together(pink,weight) drops only the exact-column non-unique index; leaves index(weight) and the unique. HOLDS patched / REJECTED by weak.

Positive control discriminates (holds patched, fails at base with the exact ValueError). Candidate weak patch (guard != 1 -> < 1) is rejected by 3 of 6 probes. Verdict: SOUND — no probe fails on the patched tree, and the probe-conforming space is exercised by a wrong candidate that the suite rejects.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 6 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 6 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

Counterexample / evidence:

```
Naive fix (change guard `if len(constraint_names) != 1` -> `< 1`, then delete constraint_names[0]) is REJECTED by the suite: probe_1 fails (it deletes the unique constraint instead of the ordinary index when both match — constraint_names[0] is arbitrary; here the index stays and something else is dropped), probe_5 fails (0-match guard no longer raises the required ValueError), probe_6 fails (does not select the exact-column non-unique index). This demonstrates discriminating power against a requirements-under-reading fix.
```

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
"""POSITIVE CONTROL + Req1.3/1.4: Removing an index_together over columns that
also have a unique_together must NOT raise, must drop the ordinary index, and
must leave the unique constraint in place.

HOLDS iff: alter_index_together([(pink,weight)] -> []) completes without error,
the non-unique index over (pink,weight) is gone, and the unique constraint over
(pink,weight) still exists.

At base (unpatched) this raises ValueError("Found wrong number (2) ...") because
the filter {'index': True} matches both the index and the unique constraint.
"""
import os
import sys
# Create a real on-disk app package so Django's app loading works cleanly.
_d = '$SCRATCH'
os.makedirs(_d, exist_ok=True)
open(os.path.join(_d, '__init__.py'), 'w').close()
open(os.path.join(_d, 'models.py'), 'w').close()
sys.path.insert(0, '/tmp')
import django
from django.conf import settings

settings.configure(
    INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth', 'probeapp'],
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
    DEFAULT_AUTO_FIELD='django.db.models.AutoField',
)
django.setup()
from django.db import connection, models


def make_model():
    Meta = type('Meta', (), {'app_label': 'probeapp', 'unique_together': {('pink', 'weight')}})
    return type('Pony', (models.Model,), {
        '__module__': 'probeapp.models',
        'pink': models.IntegerField(),
        'weight': models.FloatField(),
        'Meta': Meta,
    })


def cons(table):
    with connection.cursor() as c:
        return connection.introspection.get_constraints(c, table)


def has_index(table, cols):
    return any(list(i['columns']) == cols and i['index'] and not i['unique']
               for i in cons(table).values())


def has_unique(table, cols):
    return any(list(i['columns']) == cols and i['unique'] for i in cons(table).values())


Pony = make_model()
table = Pony._meta.db_table
cols = ['pink', 'weight']

with connection.schema_editor() as editor:
    editor.create_model(Pony)
    # Add the index_together (ordinary composite index) over the same columns.
    editor.alter_index_together(Pony, set(), {('pink', 'weight')})

assert has_unique(table, cols), "setup: unique constraint should exist"
assert has_index(table, cols), "setup: ordinary index should exist"
print("SETUP: unique + index both present over", cols)

try:
    with connection.schema_editor() as editor:
        editor.alter_index_together(Pony, {('pink', 'weight')}, set())
except Exception as e:
    print("VIOLATED: removing index_together raised:", type(e).__name__, e)
    sys.exit(1)

idx = has_index(table, cols)
uniq = has_unique(table, cols)
print(f"AFTER REMOVE: ordinary_index_present={idx} unique_present={uniq}")
if idx:
    print("VIOLATED: ordinary index still present after removal")
    sys.exit(1)
if not uniq:
    print("VIOLATED: unique constraint was dropped")
    sys.exit(1)
print("HOLDS: index dropped, unique preserved, no error")
sys.exit(0)
```

Prepatch bug re-encoded as an attack: `True`.

Instance django__django-12708: fix restricts _delete_composed_index search for a removed index_together to constraints that are index-backed AND NOT unique, via filter {'index': True, 'unique': False}, so removing an index_together over columns also covered by unique_together no longer crashes with ValueError('Found wrong number (2) ...').

Probes run in the official docker image (python3.6/testbed) using an in-memory sqlite backend (allows_multiple_constraints_on_same_fields=True, matching the F2P test's skip guard). Each probe registers a real on-disk package so Django app-loading works.

Results (gold-patched / base / weak-candidate):
- probe_1 (POS CONTROL; Req1.3,1.4): remove overlapping index_together -> no error, ordinary index dropped, unique preserved. HOLDS patched / VIOLATED base...') / REJECTED by weak.
- probe_2 (Req2.5): remove non-overlapping index_together still drops the single index. HOLDS patched / (accepts weak, as expected — not a discriminator).
- probe_3 (Req2.4): alter_unique_together removal still drops the unique via unique-only filter. HOLDS patched.
- probe_4 (Req2.3): adding a new index_together creates the composed index. HOLDS patched.
- probe_5 (Req2.1): exactly-one guard preserved — 0 non-unique-index matches still raises ValueError with the original 'Found wrong number (0)...' message/table. HOLDS patched / REJECTED by weak.
- probe_6 (Req2.6,1.2): column-exactness + unique-not-counted — with unique(pink,weight)+index(pink,weight)+index(weight), removing index_together(pink,weight) drops only the exact-column non-unique index; leaves index(weight) and the unique. HOLDS patched / REJECTED by weak.

Positive control discriminates (holds patched, fails at base with the exact ValueError). Candidate weak patch (guard != 1 -> < 1) is rejected by 3 of 6 probes. Verdict: SOUND — no probe fails on the patched tree, and the probe-conforming space is exercised by a wrong candidate that the suite rejects.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Verified patched source in the instance image via nl_attack probe: _delete_composed_index builds meta_constraint_names/meta_index_names, calls _constraint_names(model, columns, exclude=..., **constraint_kwargs), raises the exact ValueError on len!=1, else deletes constraint_names[0]. alter_index_together deleted branch now passes {'index': True, 'unique': False}; alter_unique_together still passes {'unique': True}. _constraint_names filters unique/columns exactly. FAIL_TO_PASS test test_alter_index_together_remove_with_unique_together confirms the modeled scenario (unique+index over same fields, remove index_together, assert index gone and unique remains). Requirements align with all of these.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The requirements describe the fix as behavioral acceptance criteria (restrict the deleted-index search to constraints that are index-backed AND non-unique, leaving the unique_together intact). Everything referenced publicly derives from the problem_statement: file path django/db/backends/base/schema.py, functions alter_index_together / _delete_composed_index, the ValueError 'Found wrong number (%s) of constraints', and the unique_together/index_together overlap scenario. No hidden-test content is transmitted: no test function/class names (test_alter_index_together_remove_with_unique_together, OperationTests), no invented test helper (assertUniqueConstraintExists), no skip feature flag (allows_multiple_constraints_on_same_fields), no fixture identifiers (columns ['pink','weight'], table/app_label names), and no verbatim gold-patch code. The gold's dict filter {'index': True, 'unique': False} is expressed only as prose ('index-backed AND NOT unique'), a legitimate behavioral translation rather than a quoted identifier. Requirement 2 states preserved/unrelated behaviors (exactly-one guard, Meta.constraints/Meta.indexes exclusion, unique_together's unique-only filter, non-overlapping cases) as general behavior descriptions, not a mirror of the test parametrization.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
