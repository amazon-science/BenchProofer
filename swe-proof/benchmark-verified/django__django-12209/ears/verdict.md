# P2 adversarial audit — django__django-12209

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
"""Positive control (Req 1.2/1.3, Req 3.2):
A verbatim/replay (raw) save of an instance that is being ADDED, carries a pk
value, whose pk field has a default -> must attempt UPDATE first and NOT force a
second INSERT. So re-saving an existing row via the raw path must NOT raise a
duplicate-key error; it must update in place.

PATCHED: holds (no IntegrityError, row count stays 1).
BASE:   fails (raw save forced INSERT -> IntegrityError duplicate pk).
"""
import uuid, sys
import django
from django.conf import settings

settings.configure(
    DEBUG=True,
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
    INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth', 'testapp'],
    DEFAULT_AUTO_FIELD='django.db.models.AutoField',
)
import types, tempfile
testapp = types.ModuleType('testapp')
testapp.__path__ = [tempfile.mkdtemp()]
sys.modules['testapp'] = testapp
django.setup()

from django.db import models, connection, IntegrityError

class UUIDDefaultData(models.Model):
    data = models.UUIDField(primary_key=True, default=uuid.uuid4)
    class Meta:
        app_label = 'testapp'

with connection.schema_editor() as se:
    se.create_model(UUIDDefaultData)

pk = uuid.uuid4()

# First raw save (object not yet existing) -> must create it.
o1 = UUIDDefaultData(data=pk)
o1._state.adding = True
o1.save_base(raw=True)

cnt = UUIDDefaultData.objects.count()
print("after first raw save, count =", cnt)
assert cnt == 1, "first raw save did not create exactly one row"

# Second raw save of SAME pk, still marked as being added -> must UPDATE, not
# INSERT again. On base this forces an INSERT and raises IntegrityError.
o2 = UUIDDefaultData(data=pk)
o2._state.adding = True
try:
    o2.save_base(raw=True)
except IntegrityError as e:
    print("IntegrityError on re-save (VIOLATION):", e)
    sys.exit(1)

cnt2 = UUIDDefaultData.objects.count()
print("after second raw save, count =", cnt2)
assert cnt2 == 1, "re-save created a duplicate row"
print("OK: verbatim re-save updated in place, no duplicate")
sys.exit(0)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""Req 1.4: A verbatim/replay save of a not-yet-existing object (pk has default,
being added) SHALL fall back to INSERT and create it.
Holds on both base and patched (the fresh-insert fallback), so this checks the
UPDATE-then-fallback path actually persists a brand-new row via the raw path.
"""
import uuid, sys, types, tempfile
import django
from django.conf import settings
settings.configure(
    DEBUG=True,
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
    INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth', 'testapp'],
    DEFAULT_AUTO_FIELD='django.db.models.AutoField',
)
testapp = types.ModuleType('testapp'); testapp.__path__ = [tempfile.mkdtemp()]
sys.modules['testapp'] = testapp
django.setup()
from django.db import models, connection

class UUIDDefaultData(models.Model):
    data = models.UUIDField(primary_key=True, default=uuid.uuid4)
    class Meta: app_label = 'testapp'

with connection.schema_editor() as se:
    se.create_model(UUIDDefaultData)

pk = uuid.uuid4()
o = UUIDDefaultData(data=pk)
o._state.adding = True
o.save_base(raw=True)
got = list(UUIDDefaultData.objects.values_list('data', flat=True))
print("rows:", got)
assert got == [pk], "raw save of new object did not persist with its pk"
print("OK: verbatim save of new object created it with the given pk")
sys.exit(0)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""Req 2.1: A NON-verbatim save that adds a brand-new instance whose pk field has
a default (caller did not request force_insert) SHALL force a fresh insert and
NOT attempt a speculative UPDATE first.

We detect this by counting how many UPDATE statements hit the DB during the
ordinary save of a brand-new object. Optimization intact => 0 UPDATEs, exactly
one INSERT. Holds on both base and patched (Req 2 regression preservation).
"""
import uuid, sys, types, tempfile
import django
from django.conf import settings
settings.configure(
    DEBUG=True,
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
    INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth', 'testapp'],
    DEFAULT_AUTO_FIELD='django.db.models.AutoField',
)
testapp = types.ModuleType('testapp'); testapp.__path__ = [tempfile.mkdtemp()]
sys.modules['testapp'] = testapp
django.setup()
from django.db import models, connection
from django.test.utils import CaptureQueriesContext

class UUIDDefaultRich(models.Model):
    # pk field has a default AND there is a non-pk column, so a speculative
    # UPDATE (if the optimization were removed) shows up as a real UPDATE / an
    # existence probe rather than being elided.
    data = models.UUIDField(primary_key=True, default=uuid.uuid4)
    val = models.IntegerField(default=7)
    class Meta: app_label = 'testapp'

with connection.schema_editor() as se:
    se.create_model(UUIDDefaultRich)

o = UUIDDefaultRich()  # default generates a pk; _state.adding True by construction
assert o._state.adding
with CaptureQueriesContext(connection) as ctx:
    o.save()  # ordinary (non-raw) save
sqls = [q['sql'].strip().upper() for q in ctx.captured_queries]
updates = [s for s in sqls if s.startswith('UPDATE')]
# An existence/SELECT probe before the insert is also part of the speculative
# UPDATE attempt the optimization is supposed to skip.
selects = [s for s in sqls if s.startswith('SELECT')]
inserts = [s for s in sqls if s.startswith('INSERT')]
print("queries:", sqls)
assert len(updates) == 0, "ordinary new-instance save issued a speculative UPDATE"
assert len(selects) == 0, "ordinary new-instance save issued a speculative existence SELECT (optimization removed)"
assert len(inserts) == 1, "expected exactly one INSERT"
print("OK: ordinary save = single INSERT, no speculative UPDATE")
sys.exit(0)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""Req 2.3: If a save requests a forced update or specifies update_fields while
the instance has NO pk value, _save_table SHALL raise an error rather than
silently inserting. Regression criterion; holds on base and patched.
"""
import uuid, sys, types, tempfile
import django
from django.conf import settings
settings.configure(
    DEBUG=True,
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
    INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth', 'testapp'],
    DEFAULT_AUTO_FIELD='django.db.models.AutoField',
)
testapp = types.ModuleType('testapp'); testapp.__path__ = [tempfile.mkdtemp()]
sys.modules['testapp'] = testapp
django.setup()
from django.db import models, connection

class PlainData(models.Model):
    val = models.IntegerField(default=0)
    class Meta: app_label = 'testapp'

with connection.schema_editor() as se:
    se.create_model(PlainData)

# force_update with no pk -> must raise
o = PlainData()
assert o.pk is None
raised = False
try:
    o.save_base(force_update=True)
except (ValueError, Exception) as e:
    raised = True
    print("force_update no-pk raised:", type(e).__name__, e)
assert raised, "force_update with no pk did not raise"

# update_fields with no pk -> must raise (checked in save(); use save_base path
# via save with update_fields)
o2 = PlainData()
raised2 = False
try:
    o2.save(update_fields=['val'])
except (ValueError, Exception) as e:
    raised2 = True
    print("update_fields no-pk raised:", type(e).__name__, e)
assert raised2, "update_fields with no pk did not raise"
print("OK: forced-update / update_fields without pk both raise")
sys.exit(0)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""Req 2.2: force_insert forces a fresh insert independent of the verbatim/replay
distinction. So a RAW save with force_insert=True of an already-existing pk must
still attempt an INSERT (and thus raise a duplicate-key error) -- it must NOT be
diverted to an UPDATE. Regression criterion; holds base and patched.
"""
import uuid, sys, types, tempfile
import django
from django.conf import settings
settings.configure(
    DEBUG=True,
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
    INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth', 'testapp'],
    DEFAULT_AUTO_FIELD='django.db.models.AutoField',
)
testapp = types.ModuleType('testapp'); testapp.__path__ = [tempfile.mkdtemp()]
sys.modules['testapp'] = testapp
django.setup()
from django.db import models, connection, IntegrityError

class UUIDDefaultData(models.Model):
    data = models.UUIDField(primary_key=True, default=uuid.uuid4)
    class Meta: app_label = 'testapp'

with connection.schema_editor() as se:
    se.create_model(UUIDDefaultData)

pk = uuid.uuid4()
o1 = UUIDDefaultData(data=pk); o1._state.adding = True
o1.save_base(raw=True)
assert UUIDDefaultData.objects.count() == 1

# raw + force_insert of same pk -> must try INSERT -> duplicate error
o2 = UUIDDefaultData(data=pk); o2._state.adding = True
raised = False
try:
    o2.save_base(raw=True, force_insert=True)
except IntegrityError as e:
    raised = True
    print("raw+force_insert on existing pk raised (expected):", e)
assert raised, "force_insert on raw path was diverted to UPDATE (VIOLATION of Req 2.2)"
print("OK: force_insert forces INSERT regardless of raw")
sys.exit(0)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
"""Req 3.3 (no regression for pk WITHOUT default): For a model whose pk field has
NO default, an ordinary new-instance save with an explicit pk must still attempt
an UPDATE first then fall back to INSERT (the pre-existing behavior), and a raw
re-save of an existing explicit pk must update in place (idempotent), exactly as
before. This exercises the 'else' path that the optimization never touched.
Holds base and patched.
"""
import uuid, sys, types, tempfile
import django
from django.conf import settings
settings.configure(
    DEBUG=True,
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
    INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth', 'testapp'],
    DEFAULT_AUTO_FIELD='django.db.models.AutoField',
)
testapp = types.ModuleType('testapp'); testapp.__path__ = [tempfile.mkdtemp()]
sys.modules['testapp'] = testapp
django.setup()
from django.db import models, connection, IntegrityError

class UUIDPlainData(models.Model):
    data = models.UUIDField(primary_key=True)  # NO default
    class Meta: app_label = 'testapp'

with connection.schema_editor() as se:
    se.create_model(UUIDPlainData)

pk = uuid.uuid4()
o1 = UUIDPlainData(data=pk); o1._state.adding = True
o1.save_base(raw=True)
assert UUIDPlainData.objects.count() == 1, "first raw save failed"

# second raw save of same pk (still adding) -> must update in place, not dup
o2 = UUIDPlainData(data=pk); o2._state.adding = True
try:
    o2.save_base(raw=True)
except IntegrityError as e:
    print("VIOLATION: pk-without-default regressed:", e)
    sys.exit(1)
assert UUIDPlainData.objects.count() == 1
print("OK: pk-without-default raw re-save still idempotent (no regression)")
sys.exit(0)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Positive control (Req 1.2/1.3, Req 3.2):
A verbatim/replay (raw) save of an instance that is being ADDED, carries a pk
value, whose pk field has a default -> must attempt UPDATE first and NOT force a
second INSERT. So re-saving an existing row via the raw path must NOT raise a
duplicate-key error; it must update in place.

PATCHED: holds (no IntegrityError, row count stays 1).
BASE:   fails (raw save forced INSERT -> IntegrityError duplicate pk).
"""
import uuid, sys
import django
from django.conf import settings

settings.configure(
    DEBUG=True,
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
    INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth', 'testapp'],
    DEFAULT_AUTO_FIELD='django.db.models.AutoField',
)
import types, tempfile
testapp = types.ModuleType('testapp')
testapp.__path__ = [tempfile.mkdtemp()]
sys.modules['testapp'] = testapp
django.setup()

from django.db import models, connection, IntegrityError

class UUIDDefaultData(models.Model):
    data = models.UUIDField(primary_key=True, default=uuid.uuid4)
    class Meta:
        app_label = 'testapp'

with connection.schema_editor() as se:
    se.create_model(UUIDDefaultData)

pk = uuid.uuid4()

# First raw save (object not yet existing) -> must create it.
o1 = UUIDDefaultData(data=pk)
o1._state.adding = True
o1.save_base(raw=True)

cnt = UUIDDefaultData.objects.count()
print("after first raw save, count =", cnt)
assert cnt == 1, "first raw save did not create exactly one row"

# Second raw save of SAME pk, still marked as being added -> must UPDATE, not
# INSERT again. On base this forces an INSERT and raises IntegrityError.
o2 = UUIDDefaultData(data=pk)
o2._state.adding = True
try:
    o2.save_base(raw=True)
except IntegrityError as e:
    print("IntegrityError on re-save (VIOLATION):", e)
    sys.exit(1)

cnt2 = UUIDDefaultData.objects.count()
print("after second raw save, count =", cnt2)
assert cnt2 == 1, "re-save created a duplicate row"
print("OK: verbatim re-save updated in place, no duplicate")
sys.exit(0)
```

Prepatch bug re-encoded as an attack: `True`.

Instance django__django-12209: gold patch adds `not raw and` to the 'Skip an UPDATE when adding an instance and primary key has a default' guard in Model._save_table.

Probes (all standalone, stdlib+django only; run via nl_attack probe):
- probe_1 POSITIVE CONTROL (Req 1.2/1.3, Req 3.2): raw save of an existing UUIDDefaultData pk (state.adding=True, pk has default) must attempt UPDATE first and NOT force a duplicate INSERT. HOLDS patched (count stays 1), FAILS base (IntegrityError: UNIQUE constraint failed) => discriminates.
- probe_2 (Req 1.4): raw save of a not-yet-existing object with default pk falls back to INSERT and persists it. HOLDS patched.
- probe_3 (Req 2.1): ordinary (non-raw) new-instance save of a model whose pk has a default AND a non-pk column issues exactly one INSERT and NO speculative UPDATE/SELECT. HOLDS patched AND base; REJECTED under the weak candidate (AssertionError: speculative UPDATE reappears). This is the discriminating regression leg.
- probe_4 (Req 2.3): force_update / update_fields with no pk raise ValueError. HOLDS.
- probe_5 (Req 2.2): raw + force_insert on an existing pk still forces INSERT (duplicate error), not diverted to UPDATE. HOLDS.
- probe_6 (Req 3.3): pk WITHOUT default raw re-save still idempotent (no regression on the untouched else path). HOLDS.

CANDIDATE PATCH (weak.diff): deletes the entire 'skip UPDATE' optimization block. It satisfies Req 1 (verbatim saves attempt UPDATE) and Req 3, and passes probes 1,2,4,5,6 — but probe_3 REJECTS it because ordinary new-instance creates now perform a speculative UPDATE, violating Req 2.1's 'keep the fresh-insert optimization'. This demonstrates the probe suite discriminates a requirements-plausible wrong fix.

All 6 probes HOLD on the gold-patched tree; positive control discriminates (holds patched / fails base, prepatch_reproduced=true); the wrong-fix candidate is rejected by the suite. Verdict: SOUND.

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
"""Positive control (Req 1.2/1.3, Req 3.2):
A verbatim/replay (raw) save of an instance that is being ADDED, carries a pk
value, whose pk field has a default -> must attempt UPDATE first and NOT force a
second INSERT. So re-saving an existing row via the raw path must NOT raise a
duplicate-key error; it must update in place.

PATCHED: holds (no IntegrityError, row count stays 1).
BASE:   fails (raw save forced INSERT -> IntegrityError duplicate pk).
"""
import uuid, sys
import django
from django.conf import settings

settings.configure(
    DEBUG=True,
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
    INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth', 'testapp'],
    DEFAULT_AUTO_FIELD='django.db.models.AutoField',
)
import types, tempfile
testapp = types.ModuleType('testapp')
testapp.__path__ = [tempfile.mkdtemp()]
sys.modules['testapp'] = testapp
django.setup()

from django.db import models, connection, IntegrityError

class UUIDDefaultData(models.Model):
    data = models.UUIDField(primary_key=True, default=uuid.uuid4)
    class Meta:
        app_label = 'testapp'

with connection.schema_editor() as se:
    se.create_model(UUIDDefaultData)

pk = uuid.uuid4()

# First raw save (object not yet existing) -> must create it.
o1 = UUIDDefaultData(data=pk)
o1._state.adding = True
o1.save_base(raw=True)

cnt = UUIDDefaultData.objects.count()
print("after first raw save, count =", cnt)
assert cnt == 1, "first raw save did not create exactly one row"

# Second raw save of SAME pk, still marked as being added -> must UPDATE, not
# INSERT again. On base this forces an INSERT and raises IntegrityError.
o2 = UUIDDefaultData(data=pk)
o2._state.adding = True
try:
    o2.save_base(raw=True)
except IntegrityError as e:
    print("IntegrityError on re-save (VIOLATION):", e)
    sys.exit(1)

cnt2 = UUIDDefaultData.objects.count()
print("after second raw save, count =", cnt2)
assert cnt2 == 1, "re-save created a duplicate row"
print("OK: verbatim re-save updated in place, no duplicate")
sys.exit(0)
```

Prepatch bug re-encoded as an attack: `True`.

Instance django__django-12209: gold patch adds `not raw and` to the 'Skip an UPDATE when adding an instance and primary key has a default' guard in Model._save_table.

Probes (all standalone, stdlib+django only; run via nl_attack probe):
- probe_1 POSITIVE CONTROL (Req 1.2/1.3, Req 3.2): raw save of an existing UUIDDefaultData pk (state.adding=True, pk has default) must attempt UPDATE first and NOT force a duplicate INSERT. HOLDS patched (count stays 1), FAILS base (IntegrityError: UNIQUE constraint failed) => discriminates.
- probe_2 (Req 1.4): raw save of a not-yet-existing object with default pk falls back to INSERT and persists it. HOLDS patched.
- probe_3 (Req 2.1): ordinary (non-raw) new-instance save of a model whose pk has a default AND a non-pk column issues exactly one INSERT and NO speculative UPDATE/SELECT. HOLDS patched AND base; REJECTED under the weak candidate (AssertionError: speculative UPDATE reappears). This is the discriminating regression leg.
- probe_4 (Req 2.3): force_update / update_fields with no pk raise ValueError. HOLDS.
- probe_5 (Req 2.2): raw + force_insert on an existing pk still forces INSERT (duplicate error), not diverted to UPDATE. HOLDS.
- probe_6 (Req 3.3): pk WITHOUT default raw re-save still idempotent (no regression on the untouched else path). HOLDS.

CANDIDATE PATCH (weak.diff): deletes the entire 'skip UPDATE' optimization block. It satisfies Req 1 (verbatim saves attempt UPDATE) and Req 3, and passes probes 1,2,4,5,6 — but probe_3 REJECTS it because ordinary new-instance creates now perform a speculative UPDATE, violating Req 2.1's 'keep the fresh-insert optimization'. This demonstrates the probe suite discriminates a requirements-plausible wrong fix.

All 6 probes HOLD on the gold-patched tree; positive control discriminates (holds patched / fails base, prepatch_reproduced=true); the wrong-fix candidate is rejected by the suite. Verdict: SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Verified on the instance image via nl_attack probe: patched HOLDS (raw update succeeds, non-raw optimization preserved), base VIOLATED (UNIQUE constraint failed on raw re-save). Requirements accurately describe: the boundary condition (raw vs non-raw), the retained force_insert behavior (Req 2.2), and the preexisting force_update/no-pk error (Req 2.3, untouched by patch). No mandated behavior the code lacks, no forbidden behavior it has, no invented behavior.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** requirements.md describes behavior in terms of the pre-existing Model._save_table API surface only: raw (a pre-existing parameter in the _save_table signature, not fix-invented), force_insert, force_update, update-fields, _state.adding, pk.default. The gold edit merely adds 'not raw and' to an existing condition; naming raw is legitimate localization, not a leaked identifier. None of the hidden-test artifacts appear: the invented model name UUIDDefaultData, the UUIDField(primary_key=True, default=uuid.uuid4) definition, pk id 793, test file paths (tests/serializers/models/data.py, tests/serializers/test_data.py), or the register_tests machinery. The doc stays generic ('primary-key field whose default is set') and never mentions UUID specifically. Requirement 3's serialize/deserialize round-trip and double-load idempotency mirror the test's concern, but that concern is explicitly public in the problem_statement (loaddata, fixtures, 'loading the fixture multiple times', the UUIDField default=uuid4 model). No quoted test/gold code, no test names/ids, no case enumerations mirroring parametrization. This is behavioral translation, which is the intended purpose.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
