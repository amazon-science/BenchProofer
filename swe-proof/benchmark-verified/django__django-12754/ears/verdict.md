# P2 adversarial audit — django__django-12754

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
"""Probe for Requirement 1 (core fix) — POSITIVE CONTROL.

Criterion: R1.2 / R1.3 — for a field moved from a base onto a new inheriting
model in one change, the single migration's operations must begin with
RemoveField(base, field) followed by CreateModel(newmodel).

Exits 0 iff ops == [RemoveField(readable.title), CreateModel(book)].
HOLDS on patched tree; FAILS at base (base emits CreateModel before RemoveField).
"""
import django
from django.conf import settings
if not settings.configured:
    settings.configure(INSTALLED_APPS=[], DATABASES={}, USE_TZ=False)
django.setup()

from django.db import models
from django.db.migrations.autodetector import MigrationAutodetector
from django.db.migrations.state import ModelState, ProjectState


def make_state(model_states):
    ps = ProjectState()
    for ms in model_states:
        ps.add_model(ms.clone())
    return ps


def get_changes(before, after):
    return MigrationAutodetector(make_state(before), make_state(after))._detect_changes()


before = [
    ModelState('app', 'readable', [
        ('id', models.AutoField(primary_key=True)),
        ('title', models.CharField(max_length=200)),
    ]),
]
after = [
    ModelState('app', 'readable', [
        ('id', models.AutoField(primary_key=True)),
    ]),
    ModelState('app', 'book', [
        ('title', models.CharField(max_length=200)),
    ], bases=('app.readable',)),
]

changes = get_changes(before, after)
migs = changes.get('app', [])
print("num migrations for app:", len(migs))
if len(migs) != 1:
    print("FAIL: expected exactly 1 migration")
    raise SystemExit(1)
ops = migs[0].operations
op_types = [type(o).__name__ for o in ops]
print("operation types:", op_types)
if op_types != ['RemoveField', 'CreateModel']:
    print("FAIL: expected ['RemoveField','CreateModel']")
    raise SystemExit(1)
# Check attributes
rm, cr = ops[0], ops[1]
print("RemoveField name=", rm.name, "model_name=", rm.model_name)
print("CreateModel name=", cr.name)
if rm.name != 'title' or rm.model_name != 'readable':
    print("FAIL: RemoveField targets wrong model/field")
    raise SystemExit(1)
if cr.name != 'book':
    print("FAIL: CreateModel targets wrong model")
    raise SystemExit(1)
print("PASS: removal of base field ordered before creation of subclass")
raise SystemExit(0)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""Probe for Requirement 3 — coalesce a shared moved field across multiple
new subclasses.

R3.1: a field removed from a base and re-declared by 2+ new subclasses ->
a SINGLE RemoveField, not one per subclass.
R3.2: that single removal ordered before creation of every subclass.

Exits 0 iff exactly one RemoveField(readable.title) appears and it precedes
every CreateModel that re-declares title.
"""
import django
from django.conf import settings
if not settings.configured:
    settings.configure(INSTALLED_APPS=[], DATABASES={}, USE_TZ=False)
django.setup()

from django.db import models
from django.db.migrations.autodetector import MigrationAutodetector
from django.db.migrations.state import ModelState, ProjectState


def make_state(model_states):
    ps = ProjectState()
    for ms in model_states:
        ps.add_model(ms.clone())
    return ps


def get_changes(before, after):
    return MigrationAutodetector(make_state(before), make_state(after))._detect_changes()


before = [
    ModelState('app', 'readable', [
        ('id', models.AutoField(primary_key=True)),
        ('title', models.CharField(max_length=200)),
    ]),
]
after = [
    ModelState('app', 'readable', [
        ('id', models.AutoField(primary_key=True)),
    ]),
    ModelState('app', 'book', [
        ('title', models.CharField(max_length=200)),
    ], bases=('app.readable',)),
    ModelState('app', 'magazine', [
        ('title', models.CharField(max_length=200)),
    ], bases=('app.readable',)),
]

changes = get_changes(before, after)
migs = changes.get('app', [])
print("num migrations:", len(migs))
if len(migs) != 1:
    print("FAIL: expected 1 migration")
    raise SystemExit(1)
ops = migs[0].operations
op_types = [type(o).__name__ for o in ops]
print("operation types:", op_types)

# count RemoveField ops targeting readable.title
rm_idx = [i for i, o in enumerate(ops)
          if type(o).__name__ == 'RemoveField' and o.name == 'title'
          and o.model_name == 'readable']
print("RemoveField(readable.title) indices:", rm_idx)
if len(rm_idx) != 1:
    print("FAIL: expected exactly one removal of the shared base field")
    raise SystemExit(1)

# creations of the two subclasses that re-declare title
cr_idx = [i for i, o in enumerate(ops)
          if type(o).__name__ == 'CreateModel' and o.name in ('book', 'magazine')]
print("CreateModel(book/magazine) indices:", cr_idx)
if len(cr_idx) != 2:
    print("FAIL: expected creation of both subclasses")
    raise SystemExit(1)
if not all(rm_idx[0] < ci for ci in cr_idx):
    print("FAIL: removal not ordered before every subclass creation")
    raise SystemExit(1)
print("PASS: single coalesced removal precedes both subclass creations")
raise SystemExit(0)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""Probe for Requirement 2.1 — restrict the new dependency to genuinely moved
fields: IF a field is still declared by the referenced base in the current
state, the autodetector SHALL NOT record a base-field-removal dependency (and
must not invent a RemoveField for a field that was not removed).

Scenario: base 'readable' keeps 'title' in BOTH states (pre-existing). A new
subclass 'book' also declares 'title'. Since title is not removed from base,
no RemoveField(readable.title) may appear; only CreateModel(book).

Exits 0 iff there is no RemoveField for readable.title and book is created.
This behavior is the SAME on base and patched trees (a restriction/regression
criterion) — it guards against an over-eager fix.
"""
import django
from django.conf import settings
if not settings.configured:
    settings.configure(INSTALLED_APPS=[], DATABASES={}, USE_TZ=False)
django.setup()

from django.db import models
from django.db.migrations.autodetector import MigrationAutodetector
from django.db.migrations.state import ModelState, ProjectState


def make_state(model_states):
    ps = ProjectState()
    for ms in model_states:
        ps.add_model(ms.clone())
    return ps


def get_changes(before, after):
    return MigrationAutodetector(make_state(before), make_state(after))._detect_changes()


before = [
    ModelState('app', 'readable', [
        ('id', models.AutoField(primary_key=True)),
        ('title', models.CharField(max_length=200)),
    ]),
]
after = [
    ModelState('app', 'readable', [
        ('id', models.AutoField(primary_key=True)),
        ('title', models.CharField(max_length=200)),
    ]),
    ModelState('app', 'book', [
        ('name', models.CharField(max_length=200)),
    ], bases=('app.readable',)),
]

changes = get_changes(before, after)
migs = changes.get('app', [])
ops = [o for m in migs for o in m.operations]
op_types = [type(o).__name__ for o in ops]
print("operation types:", op_types)
removes_title = [o for o in ops
                 if type(o).__name__ == 'RemoveField'
                 and getattr(o, 'name', None) == 'title'
                 and getattr(o, 'model_name', None) == 'readable']
creates_book = [o for o in ops if type(o).__name__ == 'CreateModel' and o.name == 'book']
print("RemoveField(readable.title) count:", len(removes_title))
print("CreateModel(book) count:", len(creates_book))
if removes_title:
    print("FAIL: invented a removal of a field still present on the base")
    raise SystemExit(1)
if not creates_book:
    print("FAIL: subclass creation missing")
    raise SystemExit(1)
print("PASS: no spurious removal when the base field is retained")
raise SystemExit(0)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""Probe for Requirement 2.3 — IF a field is removed from the referenced base
but is NOT declared by the new subclass, THEN no base-field-removal dependency
that reorders removal before creation.

Scenario: base 'readable' loses 'title'. New subclass 'book' does NOT declare
'title' (declares an unrelated field 'name'). Because there is no field CLASH,
the fix must NOT force RemoveField(title) before CreateModel(book) — the
existing (pre-fix) behavior applies: CreateModel(book) precedes
RemoveField(readable.title) (both depend on readable, created models first).

Exits 0 iff the CreateModel(book) is ordered BEFORE RemoveField(readable.title)
— i.e. the moved-field reorder did NOT trigger. HOLDS on both base and patched.
"""
import django
from django.conf import settings
if not settings.configured:
    settings.configure(INSTALLED_APPS=[], DATABASES={}, USE_TZ=False)
django.setup()

from django.db import models
from django.db.migrations.autodetector import MigrationAutodetector
from django.db.migrations.state import ModelState, ProjectState


def make_state(model_states):
    ps = ProjectState()
    for ms in model_states:
        ps.add_model(ms.clone())
    return ps


def get_changes(before, after):
    return MigrationAutodetector(make_state(before), make_state(after))._detect_changes()


before = [
    ModelState('app', 'readable', [
        ('id', models.AutoField(primary_key=True)),
        ('title', models.CharField(max_length=200)),
    ]),
]
after = [
    ModelState('app', 'readable', [
        ('id', models.AutoField(primary_key=True)),
    ]),
    ModelState('app', 'book', [
        ('name', models.CharField(max_length=200)),
    ], bases=('app.readable',)),
]

changes = get_changes(before, after)
migs = changes.get('app', [])
ops = [o for m in migs for o in m.operations]
op_types = [type(o).__name__ for o in ops]
print("operation types:", op_types)

rm_idx = [i for i, o in enumerate(ops)
          if type(o).__name__ == 'RemoveField' and getattr(o, 'name', None) == 'title'
          and getattr(o, 'model_name', None) == 'readable']
cr_idx = [i for i, o in enumerate(ops)
          if type(o).__name__ == 'CreateModel' and o.name == 'book']
print("RemoveField(readable.title) idx:", rm_idx, "CreateModel(book) idx:", cr_idx)
if not rm_idx or not cr_idx:
    print("FAIL: expected both a removal and a creation")
    raise SystemExit(1)
# No clash -> reorder must NOT trigger -> create precedes remove (pre-fix order)
if not (cr_idx[0] < rm_idx[0]):
    print("FAIL: removal was reordered before creation despite no field clash")
    raise SystemExit(1)
print("PASS: no reorder for a removed base field not re-declared by the subclass")
raise SystemExit(0)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""Probe for Requirement 4.5 — MTI model removal with no moved field keeps its
existing operation set unchanged.

Scenario (mirrors test_mti_inheritance_model_removal): before has Animal and
Dog(bases=app.Animal); after has only Animal. No field is moved onto a new
subclass. Expect exactly one migration: [DeleteModel] targeting Dog.

Exits 0 iff ops == [DeleteModel(Dog)]. HOLDS on base and patched.
"""
import django
from django.conf import settings
if not settings.configured:
    settings.configure(INSTALLED_APPS=[], DATABASES={}, USE_TZ=False)
django.setup()

from django.db import models
from django.db.migrations.autodetector import MigrationAutodetector
from django.db.migrations.state import ModelState, ProjectState


def make_state(model_states):
    ps = ProjectState()
    for ms in model_states:
        ps.add_model(ms.clone())
    return ps


def get_changes(before, after):
    return MigrationAutodetector(make_state(before), make_state(after))._detect_changes()


Animal = ModelState('app', 'Animal', [("id", models.AutoField(primary_key=True))])
Dog = ModelState('app', 'Dog', [], bases=('app.Animal',))

changes = get_changes([Animal, Dog], [Animal])
migs = changes.get('app', [])
print("num migrations:", len(migs))
if len(migs) != 1:
    print("FAIL: expected 1 migration")
    raise SystemExit(1)
ops = migs[0].operations
op_types = [type(o).__name__ for o in ops]
print("operation types:", op_types)
if op_types != ['DeleteModel']:
    print("FAIL: expected ['DeleteModel']")
    raise SystemExit(1)
if ops[0].name != 'Dog':
    print("FAIL: expected DeleteModel(Dog), got", ops[0].name)
    raise SystemExit(1)
print("PASS: MTI removal unchanged")
raise SystemExit(0)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
"""Probe for Requirement 4.2 — a new model inheriting a dotted base still
depends on the CREATION of that base, so bases are created before subclasses.

Scenario: both base 'readable' and subclass 'book' are brand new (not in
before state). Expect CreateModel(readable) ordered before CreateModel(book).
No field is moved (nothing removed), so this is the preserved base-creation
dependency. HOLDS on base and patched.
"""
import django
from django.conf import settings
if not settings.configured:
    settings.configure(INSTALLED_APPS=[], DATABASES={}, USE_TZ=False)
django.setup()

from django.db import models
from django.db.migrations.autodetector import MigrationAutodetector
from django.db.migrations.state import ModelState, ProjectState


def make_state(model_states):
    ps = ProjectState()
    for ms in model_states:
        ps.add_model(ms.clone())
    return ps


def get_changes(before, after):
    return MigrationAutodetector(make_state(before), make_state(after))._detect_changes()


before = []
after = [
    ModelState('app', 'readable', [
        ('id', models.AutoField(primary_key=True)),
    ]),
    ModelState('app', 'book', [
        ('title', models.CharField(max_length=200)),
    ], bases=('app.readable',)),
]

changes = get_changes(before, after)
migs = changes.get('app', [])
ops = [o for m in migs for o in m.operations]
op_types = [(type(o).__name__, getattr(o, 'name', None)) for o in ops]
print("operations:", op_types)
cr = {o.name: i for i, o in enumerate(ops) if type(o).__name__ == 'CreateModel'}
print("CreateModel positions:", cr)
if 'readable' not in cr or 'book' not in cr:
    print("FAIL: expected both models created")
    raise SystemExit(1)
if not (cr['readable'] < cr['book']):
    print("FAIL: base not created before inheriting model")
    raise SystemExit(1)
print("PASS: base created before subclass (base-creation dependency preserved)")
raise SystemExit(0)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Probe for Requirement 1 (core fix) — POSITIVE CONTROL.

Criterion: R1.2 / R1.3 — for a field moved from a base onto a new inheriting
model in one change, the single migration's operations must begin with
RemoveField(base, field) followed by CreateModel(newmodel).

Exits 0 iff ops == [RemoveField(readable.title), CreateModel(book)].
HOLDS on patched tree; FAILS at base (base emits CreateModel before RemoveField).
"""
import django
from django.conf import settings
if not settings.configured:
    settings.configure(INSTALLED_APPS=[], DATABASES={}, USE_TZ=False)
django.setup()

from django.db import models
from django.db.migrations.autodetector import MigrationAutodetector
from django.db.migrations.state import ModelState, ProjectState


def make_state(model_states):
    ps = ProjectState()
    for ms in model_states:
        ps.add_model(ms.clone())
    return ps


def get_changes(before, after):
    return MigrationAutodetector(make_state(before), make_state(after))._detect_changes()


before = [
    ModelState('app', 'readable', [
        ('id', models.AutoField(primary_key=True)),
        ('title', models.CharField(max_length=200)),
    ]),
]
after = [
    ModelState('app', 'readable', [
        ('id', models.AutoField(primary_key=True)),
    ]),
    ModelState('app', 'book', [
        ('title', models.CharField(max_length=200)),
    ], bases=('app.readable',)),
]

changes = get_changes(before, after)
migs = changes.get('app', [])
print("num migrations for app:", len(migs))
if len(migs) != 1:
    print("FAIL: expected exactly 1 migration")
    raise SystemExit(1)
ops = migs[0].operations
op_types = [type(o).__name__ for o in ops]
print("operation types:", op_types)
if op_types != ['RemoveField', 'CreateModel']:
    print("FAIL: expected ['RemoveField','CreateModel']")
    raise SystemExit(1)
# Check attributes
rm, cr = ops[0], ops[1]
print("RemoveField name=", rm.name, "model_name=", rm.model_name)
print("CreateModel name=", cr.name)
if rm.name != 'title' or rm.model_name != 'readable':
    print("FAIL: RemoveField targets wrong model/field")
    raise SystemExit(1)
if cr.name != 'book':
    print("FAIL: CreateModel targets wrong model")
    raise SystemExit(1)
print("PASS: removal of base field ordered before creation of subclass")
raise SystemExit(0)
```

Prepatch bug re-encoded as an attack: `True`.

6 distinct probes, all HOLD on the gold-patched tree; positive control (probe_1) FAILS at base (base emits ['CreateModel','RemoveField']; patched emits ['RemoveField','CreateModel']), confirming discriminating power.

Wrong-fix candidate (weak.diff): the naive fix that drops the '.intersection(model_state.fields)' restriction and depends on removal of ALL fields disappeared from the base regardless of whether the subclass re-declares them. This candidate is REJECTED by probe_4 (exit 1: 'removal was reordered before creation despite no field clash'), while passing probes 1,2,3,5,6 — demonstrating the suite discriminates a plausible over-eager fix. No requirements-conforming-yet-nonresolving candidate was found; the intersection restriction (R2.3) is exactly what the suite pins. Runs used the swebench-lean conda python inside the instance's official Docker image.

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
"""Probe for Requirement 1 (core fix) — POSITIVE CONTROL.

Criterion: R1.2 / R1.3 — for a field moved from a base onto a new inheriting
model in one change, the single migration's operations must begin with
RemoveField(base, field) followed by CreateModel(newmodel).

Exits 0 iff ops == [RemoveField(readable.title), CreateModel(book)].
HOLDS on patched tree; FAILS at base (base emits CreateModel before RemoveField).
"""
import django
from django.conf import settings
if not settings.configured:
    settings.configure(INSTALLED_APPS=[], DATABASES={}, USE_TZ=False)
django.setup()

from django.db import models
from django.db.migrations.autodetector import MigrationAutodetector
from django.db.migrations.state import ModelState, ProjectState


def make_state(model_states):
    ps = ProjectState()
    for ms in model_states:
        ps.add_model(ms.clone())
    return ps


def get_changes(before, after):
    return MigrationAutodetector(make_state(before), make_state(after))._detect_changes()


before = [
    ModelState('app', 'readable', [
        ('id', models.AutoField(primary_key=True)),
        ('title', models.CharField(max_length=200)),
    ]),
]
after = [
    ModelState('app', 'readable', [
        ('id', models.AutoField(primary_key=True)),
    ]),
    ModelState('app', 'book', [
        ('title', models.CharField(max_length=200)),
    ], bases=('app.readable',)),
]

changes = get_changes(before, after)
migs = changes.get('app', [])
print("num migrations for app:", len(migs))
if len(migs) != 1:
    print("FAIL: expected exactly 1 migration")
    raise SystemExit(1)
ops = migs[0].operations
op_types = [type(o).__name__ for o in ops]
print("operation types:", op_types)
if op_types != ['RemoveField', 'CreateModel']:
    print("FAIL: expected ['RemoveField','CreateModel']")
    raise SystemExit(1)
# Check attributes
rm, cr = ops[0], ops[1]
print("RemoveField name=", rm.name, "model_name=", rm.model_name)
print("CreateModel name=", cr.name)
if rm.name != 'title' or rm.model_name != 'readable':
    print("FAIL: RemoveField targets wrong model/field")
    raise SystemExit(1)
if cr.name != 'book':
    print("FAIL: CreateModel targets wrong model")
    raise SystemExit(1)
print("PASS: removal of base field ordered before creation of subclass")
raise SystemExit(0)
```

Prepatch bug re-encoded as an attack: `True`.

6 distinct probes, all HOLD on the gold-patched tree; positive control (probe_1) FAILS at base (base emits ['CreateModel','RemoveField']; patched emits ['RemoveField','CreateModel']), confirming discriminating power.

Wrong-fix candidate (weak.diff): the naive fix that drops the '.intersection(model_state.fields)' restriction and depends on removal of ALL fields disappeared from the base regardless of whether the subclass re-declares them. This candidate is REJECTED by probe_4 (exit 1: 'removal was reordered before creation despite no field clash'), while passing probes 1,2,3,5,6 — demonstrating the suite discriminates a plausible over-eager fix. No requirements-conforming-yet-nonresolving candidate was found; the intersection restriction (R2.3) is exactly what the suite pins. Runs used the swebench-lean conda python inside the instance's official Docker image.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Patch adds dependency (base_app_label, base_name, removed_base_field, False) guarded by: base is dotted str, both old_base_model_state and new_base_model_state present, removed_base_fields = (old_base.fields - new_base.fields) & model_state.fields. This exactly realizes Req 1 (add dep), Req 2.1-2.5 (all restriction guards: still-in-base excluded by set-difference, never-in-base excluded, not-in-subclass excluded by intersection, missing old/new state excluded by 'if old and new', non-dotted base excluded by the isinstance/'.' guard), Req 3 (set dedup + single shared RemoveField op), and Req 4 (pre-existing (.,.,None,True) base-create dep, proxy dep, and PK-relation dep are all left intact above/around the added block). Requirements 1.3/1.4 attribute assertions (name='title', model_name='readable', new model 'book') match the added upstream test test_add_model_with_field_removed_from_base_model and my scenario A. Verified via swebench_unified.nl_attack probe on both patched (HOLDS) and --base.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The requirements describe the fix behaviorally in fully generic terms and never transmit hidden-test/gold artifacts. No leak of: the test name (test_add_model_with_field_removed_from_base_model), the test file path (tests/migrations/test_autodetector.py), the concrete example identifiers (app/readable/book/title, or the Magazine variant), or the literal gold dependency tuple (base_app_label, base_name, removed_base_field, False). Naming the modules/functions (autodetector.py, generate_created_models, check_dependency) is legitimate localization and largely public in problem_statement/hints. The RemoveField-before-CreateModel ordering, the field-clash rationale, and the single-removal-for-multiple-subclasses coalescing (Req 3) all derive from the PUBLIC problem_statement and hints_text discussion, and are phrased as behavioral requirements rather than mirroring test assertions/parametrization. Req 2's negative conditions are the natural set-difference/intersection logic of the change, described behaviorally, not an enumeration of parametrized test cases.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
