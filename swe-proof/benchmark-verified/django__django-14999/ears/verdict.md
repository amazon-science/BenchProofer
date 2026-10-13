# P2 adversarial audit — django__django-14999

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
"""Probe R1.1 + positive control: RenameModel.database_forwards for a model
whose db_table is pinned (unchanged) SHALL execute ZERO queries.
Exit 0 iff zero queries emitted on database_forwards."""
import sys
import django
from django.conf import settings
if not settings.configured:
    settings.configure(
        DEBUG=True,
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
        INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
        USE_TZ=False,
    )
django.setup()
from django.db import connection, models, migrations
from django.db.migrations.state import ProjectState
from django.test.utils import CaptureQueriesContext

app_label = 'test_rmwdbtn'
def apply_ops(state, ops):
    for op in ops:
        ns = state.clone()
        op.state_forwards(app_label, ns)
        with connection.schema_editor(atomic=False) as ed:
            op.database_forwards(app_label, ed, state, ns)
        state = ns
    return state

project_state = apply_ops(ProjectState(), [
    migrations.CreateModel('Rider', fields=[('id', models.AutoField(primary_key=True))],
                           options={'db_table': 'rider'}),
    migrations.CreateModel('Pony', fields=[('id', models.AutoField(primary_key=True)),
                           ('rider', models.ForeignKey('%s.Rider' % app_label, models.CASCADE))]),
])
new_state = project_state.clone()
operation = migrations.RenameModel('Rider', 'Runner')
operation.state_forwards(app_label, new_state)

with connection.schema_editor(atomic=False) as ed:
    with CaptureQueriesContext(connection) as ctx:
        operation.database_forwards(app_label, ed, project_state, new_state)
qs = [q['sql'] for q in ctx.captured_queries]
print("database_forwards queries:", len(qs))
for q in qs:
    print("  ", q)
if len(qs) == 0:
    print("HOLD: no-op forwards emitted zero queries")
    sys.exit(0)
print("VIOLATION: expected 0 queries, got", len(qs))
sys.exit(1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""Probe R1.2: RenameModel.database_backwards for a pinned-db_table (unchanged)
model SHALL execute ZERO queries. Exit 0 iff zero queries on backwards."""
import sys
import django
from django.conf import settings
if not settings.configured:
    settings.configure(
        DEBUG=True,
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
        INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
        USE_TZ=False,
    )
django.setup()
from django.db import connection, models, migrations
from django.db.migrations.state import ProjectState
from django.test.utils import CaptureQueriesContext

app_label = 'test_rmwdbtn'
def apply_ops(state, ops):
    for op in ops:
        ns = state.clone()
        op.state_forwards(app_label, ns)
        with connection.schema_editor(atomic=False) as ed:
            op.database_forwards(app_label, ed, state, ns)
        state = ns
    return state

project_state = apply_ops(ProjectState(), [
    migrations.CreateModel('Rider', fields=[('id', models.AutoField(primary_key=True))],
                           options={'db_table': 'rider'}),
    migrations.CreateModel('Pony', fields=[('id', models.AutoField(primary_key=True)),
                           ('rider', models.ForeignKey('%s.Rider' % app_label, models.CASCADE))]),
])
new_state = project_state.clone()
operation = migrations.RenameModel('Rider', 'Runner')
operation.state_forwards(app_label, new_state)

with connection.schema_editor(atomic=False) as ed:
    with CaptureQueriesContext(connection) as ctx:
        operation.database_backwards(app_label, ed, new_state, project_state)
qs = [q['sql'] for q in ctx.captured_queries]
print("database_backwards queries:", len(qs))
for q in qs:
    print("  ", q)
if len(qs) == 0:
    print("HOLD: no-op backwards emitted zero queries")
    sys.exit(0)
print("VIOLATION: expected 0 queries, got", len(qs))
sys.exit(1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""Probe R2.1: RenameModel where the table name DOES change SHALL rename the
main table. We create a model with the default (class-derived) table name,
rename it, and confirm the underlying table was physically renamed.
Exit 0 iff the new table exists and the old one is gone."""
import sys
import django
from django.conf import settings
if not settings.configured:
    settings.configure(
        DEBUG=True,
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
        INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
        USE_TZ=False,
    )
django.setup()
from django.db import connection, models, migrations
from django.db.migrations.state import ProjectState

app_label = 'test_rmchg'
def apply_ops(state, ops):
    for op in ops:
        ns = state.clone()
        op.state_forwards(app_label, ns)
        with connection.schema_editor(atomic=False) as ed:
            op.database_forwards(app_label, ed, state, ns)
        state = ns
    return state

# default db_table -> test_rmchg_rider
project_state = apply_ops(ProjectState(), [
    migrations.CreateModel('Rider', fields=[('id', models.AutoField(primary_key=True))]),
])
old_table = project_state.apps.get_model(app_label, 'Rider')._meta.db_table
new_state = project_state.clone()
operation = migrations.RenameModel('Rider', 'Runner')
operation.state_forwards(app_label, new_state)
new_table = new_state.apps.get_model(app_label, 'Runner')._meta.db_table
print("old_table:", old_table, "new_table:", new_table)
assert old_table != new_table, "test setup: tables should differ"

with connection.schema_editor(atomic=False) as ed:
    operation.database_forwards(app_label, ed, project_state, new_state)

def tables():
    with connection.cursor() as c:
        c.execute("SELECT name FROM sqlite_master WHERE type='table'")
        return {r[0] for r in c.fetchall()}
t = tables()
print("tables now:", sorted(x for x in t if 'rmchg' in x))
ok = (new_table in t) and (old_table not in t)
if ok:
    print("HOLD: main table renamed from %s to %s" % (old_table, new_table))
    sys.exit(0)
print("VIOLATION: table rename did not happen as required")
sys.exit(1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""Probe R2.2: when the main table is renamed, dependent FK references SHALL be
updated to target the new table. Create Rider (default table) + Pony(FK->Rider),
rename Rider->Runner, and confirm Pony's FK now points at the new table name.
Exit 0 iff Pony's FK references the new (renamed) table."""
import sys
import django
from django.conf import settings
if not settings.configured:
    settings.configure(
        DEBUG=True,
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
        INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
        USE_TZ=False,
    )
django.setup()
from django.db import connection, models, migrations
from django.db.migrations.state import ProjectState

app_label = 'test_rmfk'
def apply_ops(state, ops):
    for op in ops:
        ns = state.clone()
        op.state_forwards(app_label, ns)
        with connection.schema_editor(atomic=False) as ed:
            op.database_forwards(app_label, ed, state, ns)
        state = ns
    return state

project_state = apply_ops(ProjectState(), [
    migrations.CreateModel('Rider', fields=[('id', models.AutoField(primary_key=True))]),
    migrations.CreateModel('Pony', fields=[('id', models.AutoField(primary_key=True)),
                           ('rider', models.ForeignKey('%s.Rider' % app_label, models.CASCADE))]),
])
old_table = project_state.apps.get_model(app_label, 'Rider')._meta.db_table
pony_table = project_state.apps.get_model(app_label, 'Pony')._meta.db_table
new_state = project_state.clone()
operation = migrations.RenameModel('Rider', 'Runner')
operation.state_forwards(app_label, new_state)
new_table = new_state.apps.get_model(app_label, 'Runner')._meta.db_table
print("old_table:", old_table, "new_table:", new_table, "pony:", pony_table)

with connection.schema_editor(atomic=False) as ed:
    operation.database_forwards(app_label, ed, project_state, new_state)

with connection.cursor() as c:
    c.execute("PRAGMA foreign_key_list(%s)" % pony_table)
    fks = c.fetchall()
targets = {row[2] for row in fks}  # 'table' column
print("Pony FK targets:", targets)
if new_table in targets and old_table not in targets:
    print("HOLD: FK now targets renamed table")
    sys.exit(0)
print("VIOLATION: FK target not updated to new table")
sys.exit(1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""Probe R2.3: renaming a model that owns an auto-created M2M table SHALL rename
that through table and its model-derived column. Rider + Pony(riders M2M Rider);
rename Pony->Horse. The auto through table and its pony_id column must be renamed.
Exit 0 iff new through table exists with the renamed column."""
import sys
import django
from django.conf import settings
if not settings.configured:
    settings.configure(
        DEBUG=True,
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
        INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
        USE_TZ=False,
    )
django.setup()
from django.db import connection, models, migrations
from django.db.migrations.state import ProjectState

app_label = 'test_rmm2m'
def apply_ops(state, ops):
    for op in ops:
        ns = state.clone()
        op.state_forwards(app_label, ns)
        with connection.schema_editor(atomic=False) as ed:
            op.database_forwards(app_label, ed, state, ns)
        state = ns
    return state

project_state = apply_ops(ProjectState(), [
    migrations.CreateModel('Rider', fields=[('id', models.AutoField(primary_key=True))]),
    migrations.CreateModel('Pony', fields=[('id', models.AutoField(primary_key=True)),
                           ('riders', models.ManyToManyField('%s.Rider' % app_label))]),
])
old_through = project_state.apps.get_model(app_label, 'Pony')._meta.get_field('riders').remote_field.through._meta.db_table
new_state = project_state.clone()
operation = migrations.RenameModel('Pony', 'Horse')
operation.state_forwards(app_label, new_state)
new_through = new_state.apps.get_model(app_label, 'Horse')._meta.get_field('riders').remote_field.through._meta.db_table
print("old_through:", old_through, "new_through:", new_through)

with connection.schema_editor(atomic=False) as ed:
    operation.database_forwards(app_label, ed, project_state, new_state)

def tables():
    with connection.cursor() as c:
        c.execute("SELECT name FROM sqlite_master WHERE type='table'")
        return {r[0] for r in c.fetchall()}
def cols(t):
    with connection.cursor() as c:
        c.execute("PRAGMA table_info(%s)" % t)
        return {r[1] for r in c.fetchall()}
t = tables()
print("through tables present:", sorted(x for x in t if 'rmm2m' in x))
if new_through not in t:
    print("VIOLATION: new through table missing")
    sys.exit(1)
c = cols(new_through)
print("new through columns:", sorted(c))
# column derived from model name renamed pony_id -> horse_id
if 'horse_id' in c and 'pony_id' not in c and old_through not in t:
    print("HOLD: m2m through table + column renamed")
    sys.exit(0)
print("VIOLATION: m2m through table/column not renamed as required")
sys.exit(1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
"""Probe R3.2: after database_backwards completes, the operation's stored
old_name/new_name attributes SHALL be unchanged (backwards swaps names only
transiently). Exit 0 iff old_name/new_name are the original values afterward."""
import sys
import django
from django.conf import settings
if not settings.configured:
    settings.configure(
        DEBUG=True,
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
        INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
        USE_TZ=False,
    )
django.setup()
from django.db import connection, models, migrations
from django.db.migrations.state import ProjectState

app_label = 'test_rmnames'
def apply_ops(state, ops):
    for op in ops:
        ns = state.clone()
        op.state_forwards(app_label, ns)
        with connection.schema_editor(atomic=False) as ed:
            op.database_forwards(app_label, ed, state, ns)
        state = ns
    return state

# Pinned db_table => no DB work, but the name-swap path still runs in backwards.
project_state = apply_ops(ProjectState(), [
    migrations.CreateModel('Rider', fields=[('id', models.AutoField(primary_key=True))],
                           options={'db_table': 'rider'}),
])
new_state = project_state.clone()
operation = migrations.RenameModel('Rider', 'Runner')
operation.state_forwards(app_label, new_state)
before = (operation.old_name, operation.new_name)
with connection.schema_editor(atomic=False) as ed:
    operation.database_backwards(app_label, ed, new_state, project_state)
after = (operation.old_name, operation.new_name)
print("before:", before, "after:", after)
if before == after == ('Rider', 'Runner'):
    print("HOLD: name attributes preserved after backwards")
    sys.exit(0)
print("VIOLATION: name attributes mutated by backwards")
sys.exit(1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Probe R1.1 + positive control: RenameModel.database_forwards for a model
whose db_table is pinned (unchanged) SHALL execute ZERO queries.
Exit 0 iff zero queries emitted on database_forwards."""
import sys
import django
from django.conf import settings
if not settings.configured:
    settings.configure(
        DEBUG=True,
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
        INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
        USE_TZ=False,
    )
django.setup()
from django.db import connection, models, migrations
from django.db.migrations.state import ProjectState
from django.test.utils import CaptureQueriesContext

app_label = 'test_rmwdbtn'
def apply_ops(state, ops):
    for op in ops:
        ns = state.clone()
        op.state_forwards(app_label, ns)
        with connection.schema_editor(atomic=False) as ed:
            op.database_forwards(app_label, ed, state, ns)
        state = ns
    return state

project_state = apply_ops(ProjectState(), [
    migrations.CreateModel('Rider', fields=[('id', models.AutoField(primary_key=True))],
                           options={'db_table': 'rider'}),
    migrations.CreateModel('Pony', fields=[('id', models.AutoField(primary_key=True)),
                           ('rider', models.ForeignKey('%s.Rider' % app_label, models.CASCADE))]),
])
new_state = project_state.clone()
operation = migrations.RenameModel('Rider', 'Runner')
operation.state_forwards(app_label, new_state)

with connection.schema_editor(atomic=False) as ed:
    with CaptureQueriesContext(connection) as ctx:
        operation.database_forwards(app_label, ed, project_state, new_state)
qs = [q['sql'] for q in ctx.captured_queries]
print("database_forwards queries:", len(qs))
for q in qs:
    print("  ", q)
if len(qs) == 0:
    print("HOLD: no-op forwards emitted zero queries")
    sys.exit(0)
print("VIOLATION: expected 0 queries, got", len(qs))
sys.exit(1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance django__django-14999: RenameModel with unchanged db_table must be a no-op. 6 probes cover the requirements:
- probe_1 (R1.1, positive control): database_forwards with pinned Meta.db_table='rider' emits 0 queries. HOLDS patched, FAILS at base (5 queries: SQLite table rebuild). Discriminates.
- probe_2 (R1.2): database_backwards likewise 0 queries. HOLDS patched, FAILS at base (5 queries).
- probe_3 (R2.1): rename with a changing (class-derived) table name physically renames the main table (old gone, new present). HOLDS patched.
- probe_4 (R2.2): dependent FK on Pony is updated to target the renamed table. HOLDS patched.
- probe_5 (R2.3): auto-created M2M through table + model-derived column (pony_id -> horse_id) renamed. HOLDS patched.
- probe_6 (R3.2): after database_backwards the operation's old_name/new_name attributes are unchanged. HOLDS patched.

All 6 hold on the gold-patched tree; positive controls probe_1 and probe_2 fail at base, confirming discriminating power (prepatch_reproduced=true).

Wrong-fix candidate (weak.diff): the naive reading permitted by a weak spec — guard on `self.old_name == self.new_name` (class-name comparison) instead of comparing resolved db_table (R1.3 explicitly forbids this). Under this candidate probe_1 and probe_2 are REJECTED (queries still fire because class names differ on a rename), i.e. it does NOT resolve the hidden test test_rename_model_with_db_table_noop. This demonstrates the suite discriminates the lazy fix. Probes 3-6 correctly still HOLD under it (that path is unaffected). Verdict SOUND: requirements are faithful and the probe suite rejects the requirements-non-conforming wrong fix.

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
"""Probe R1.1 + positive control: RenameModel.database_forwards for a model
whose db_table is pinned (unchanged) SHALL execute ZERO queries.
Exit 0 iff zero queries emitted on database_forwards."""
import sys
import django
from django.conf import settings
if not settings.configured:
    settings.configure(
        DEBUG=True,
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
        INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
        USE_TZ=False,
    )
django.setup()
from django.db import connection, models, migrations
from django.db.migrations.state import ProjectState
from django.test.utils import CaptureQueriesContext

app_label = 'test_rmwdbtn'
def apply_ops(state, ops):
    for op in ops:
        ns = state.clone()
        op.state_forwards(app_label, ns)
        with connection.schema_editor(atomic=False) as ed:
            op.database_forwards(app_label, ed, state, ns)
        state = ns
    return state

project_state = apply_ops(ProjectState(), [
    migrations.CreateModel('Rider', fields=[('id', models.AutoField(primary_key=True))],
                           options={'db_table': 'rider'}),
    migrations.CreateModel('Pony', fields=[('id', models.AutoField(primary_key=True)),
                           ('rider', models.ForeignKey('%s.Rider' % app_label, models.CASCADE))]),
])
new_state = project_state.clone()
operation = migrations.RenameModel('Rider', 'Runner')
operation.state_forwards(app_label, new_state)

with connection.schema_editor(atomic=False) as ed:
    with CaptureQueriesContext(connection) as ctx:
        operation.database_forwards(app_label, ed, project_state, new_state)
qs = [q['sql'] for q in ctx.captured_queries]
print("database_forwards queries:", len(qs))
for q in qs:
    print("  ", q)
if len(qs) == 0:
    print("HOLD: no-op forwards emitted zero queries")
    sys.exit(0)
print("VIOLATION: expected 0 queries, got", len(qs))
sys.exit(1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance django__django-14999: RenameModel with unchanged db_table must be a no-op. 6 probes cover the requirements:
- probe_1 (R1.1, positive control): database_forwards with pinned Meta.db_table='rider' emits 0 queries. HOLDS patched, FAILS at base (5 queries: SQLite table rebuild). Discriminates.
- probe_2 (R1.2): database_backwards likewise 0 queries. HOLDS patched, FAILS at base (5 queries).
- probe_3 (R2.1): rename with a changing (class-derived) table name physically renames the main table (old gone, new present). HOLDS patched.
- probe_4 (R2.2): dependent FK on Pony is updated to target the renamed table. HOLDS patched.
- probe_5 (R2.3): auto-created M2M through table + model-derived column (pony_id -> horse_id) renamed. HOLDS patched.
- probe_6 (R3.2): after database_backwards the operation's old_name/new_name attributes are unchanged. HOLDS patched.

All 6 hold on the gold-patched tree; positive controls probe_1 and probe_2 fail at base, confirming discriminating power (prepatch_reproduced=true).

Wrong-fix candidate (weak.diff): the naive reading permitted by a weak spec — guard on `self.old_name == self.new_name` (class-name comparison) instead of comparing resolved db_table (R1.3 explicitly forbids this). Under this candidate probe_1 and probe_2 are REJECTED (queries still fire because class names differ on a rename), i.e. it does NOT resolve the hidden test test_rename_model_with_db_table_noop. This demonstrates the suite discriminates the lazy fix. Probes 3-6 correctly still HOLD under it (that path is unaffected). Verdict SOUND: requirements are faithful and the probe suite rejects the requirements-non-conforming wrong fix.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Reconstructed the full patched database_forwards and database_backwards from RenameModel via the instance-image probe (nl_attack probe, exit 0 = no-op guard present AND backwards delegates to forwards). The requirements pin the actual changed observable behavior (no-op iff resolved db_table unchanged, in both directions) rather than a narrow slice (e.g. one DB backend, only the main table, or only forwards). No mandated-but-absent, forbidden-but-present, wrong-boundary, or invented behavior. FAITHFUL.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The document describes only behavior that is public via the problem_statement ('RenameModel with db_table should be a noop; on Postgres it drops/recreates FK constraints, on sqlite it recreates the table'). It legitimately localizes the change to RenameModel.database_forwards/database_backwards in django/db/migrations/operations/models.py and to the Meta.db_table option and the model metadata db_table value — all public API, not fix-invented identifiers (the gold's locals old_db_table/new_db_table are NOT named). No leak of: the hidden test name (test_rename_model_with_db_table_noop), the test path (tests/migrations/test_operations.py), the test's model/table fixtures (Rider/Runner/Pony/'rider'), or the FK setup. The 'zero database queries' phrasing is a natural behavioral characterization of a no-op, not a reconstruction of the test's assertNumQueries(0) structure; Requirement 2's full-rename behavior (main table rename, dependent FK update, auto-created M2M table/column rename, skip self-referential M2M, allow_migrate applicability, ordering) is a faithful behavioral description derivable from the operation's public semantics rather than an enumeration mirroring the parametrized PASS_TO_PASS cases. Translating test-checked behavior into requirements is the intended function; nothing transmits the hidden tests themselves.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
