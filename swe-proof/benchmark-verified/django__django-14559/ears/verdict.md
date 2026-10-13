# P2 adversarial audit — django__django-14559

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
import django
from django.conf import settings
settings.configure(
    DEBUG=True,
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
    INSTALLED_APPS=['django.contrib.contenttypes'],
    DEFAULT_AUTO_FIELD='django.db.models.AutoField',
    USE_TZ=False,
)
django.setup()
from django.db import models, connection

class Thing(models.Model):
    note = models.CharField(max_length=100)
    class Meta:
        app_label = 'contenttypes'

with connection.schema_editor() as se:
    se.create_model(Thing)

# Req 1.2 / 1.4: distinct existing rows, single batch -> return == number of objects (int, not None)
objs = [Thing.objects.create(note='a%d' % i) for i in range(5)]
r = Thing.objects.bulk_update(objs, ['note'])
print("bulk_update returned:", repr(r), "type", type(r).__name__)
ok = (r is not None) and isinstance(r, int) and not isinstance(r, bool) and r == 5
print("OK" if ok else "FAIL")
import sys; sys.exit(0 if ok else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
import django
from django.conf import settings
settings.configure(
    DEBUG=True,
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
    INSTALLED_APPS=['django.contrib.contenttypes'],
    DEFAULT_AUTO_FIELD='django.db.models.AutoField',
    USE_TZ=False,
)
django.setup()
from django.db import models, connection

class Thing(models.Model):
    note = models.CharField(max_length=100)
    class Meta:
        app_label = 'contenttypes'

with connection.schema_editor() as se:
    se.create_model(Thing)

# Req 2.1: empty collection -> return integer 0
r = Thing.objects.bulk_update([], ['note'])
print("empty bulk_update returned:", repr(r))
ok = isinstance(r, int) and not isinstance(r, bool) and r == 0
print("OK" if ok else "FAIL")
import sys; sys.exit(0 if ok else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
import django
from django.conf import settings
settings.configure(
    DEBUG=True,
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
    INSTALLED_APPS=['django.contrib.contenttypes'],
    DEFAULT_AUTO_FIELD='django.db.models.AutoField',
    USE_TZ=False,
)
django.setup()
from django.db import models, connection

class Thing(models.Model):
    note = models.CharField(max_length=100)
    class Meta:
        app_label = 'contenttypes'

with connection.schema_editor() as se:
    se.create_model(Thing)
from django.db import reset_queries
reset_queries()
r = Thing.objects.bulk_update([], ['note'])
n = len(connection.queries)
print("empty bulk_update returned:", repr(r), "queries executed:", n)
# Req 2.2: no db queries on empty input; Req 2.1 return 0
ok = (r == 0) and (n == 0)
print("OK" if ok else "FAIL")
import sys; sys.exit(0 if ok else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
import django
from django.conf import settings
settings.configure(
    DEBUG=True,
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
    INSTALLED_APPS=['django.contrib.contenttypes'],
    DEFAULT_AUTO_FIELD='django.db.models.AutoField',
    USE_TZ=False,
)
django.setup()
from django.db import models, connection

class Thing(models.Model):
    note = models.CharField(max_length=100)
    class Meta:
        app_label = 'contenttypes'

with connection.schema_editor() as se:
    se.create_model(Thing)

# Req 3.2: same object twice within one batch -> counted once -> return 1
note = Thing.objects.create(note='test')
r = Thing.objects.bulk_update([note, note], ['note'])
print("duplicates single batch returned:", repr(r))
ok = (r == 1)
print("OK" if ok else "FAIL")
import sys; sys.exit(0 if ok else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
import django
from django.conf import settings
settings.configure(
    DEBUG=True,
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
    INSTALLED_APPS=['django.contrib.contenttypes'],
    DEFAULT_AUTO_FIELD='django.db.models.AutoField',
    USE_TZ=False,
)
django.setup()
from django.db import models, connection

class Thing(models.Model):
    note = models.CharField(max_length=100)
    class Meta:
        app_label = 'contenttypes'

with connection.schema_editor() as se:
    se.create_model(Thing)

# Req 3.3: duplicates across separate batches (batch_size=1) -> once per batch -> return 2
note = Thing.objects.create(note='test')
r = Thing.objects.bulk_update([note, note], ['note'], batch_size=1)
print("duplicates across batches (batch_size=1) returned:", repr(r))
ok = (r == 2)
print("OK" if ok else "FAIL")
import sys; sys.exit(0 if ok else 1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
import django
from django.conf import settings
settings.configure(
    DEBUG=True,
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
    INSTALLED_APPS=['django.contrib.contenttypes'],
    DEFAULT_AUTO_FIELD='django.db.models.AutoField',
    USE_TZ=False,
)
django.setup()
from django.db import models, connection

class Thing(models.Model):
    note = models.CharField(max_length=100)
    class Meta:
        app_label = 'contenttypes'

with connection.schema_editor() as se:
    se.create_model(Thing)

# Req 1.1/1.3: multiple batches sum to total distinct objects
objs = [Thing.objects.create(note='n%d' % i) for i in range(10)]
r = Thing.objects.bulk_update(objs, ['note'], batch_size=3)
print("10 objs batch_size=3 returned:", repr(r))
# 10 distinct rows across batches of 3 -> 4 batches summing 3+3+3+1 = 10
ok = isinstance(r, int) and not isinstance(r, bool) and r == 10
print("OK" if ok else "FAIL")
import sys; sys.exit(0 if ok else 1)
```

Attack 7 — `probe_7.py` → holds on the patched tree (good)

```python
import django
from django.conf import settings
settings.configure(
    DEBUG=True,
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
    INSTALLED_APPS=['django.contrib.contenttypes'],
    DEFAULT_AUTO_FIELD='django.db.models.AutoField',
    USE_TZ=False,
)
django.setup()
from django.db import models, connection

class Thing(models.Model):
    note = models.CharField(max_length=100)
    class Meta:
        app_label = 'contenttypes'

with connection.schema_editor() as se:
    se.create_model(Thing)

# Req 4.1/4.2/4.5: validation preserved (negative batch_size, no fields, pk field)
res = {}
try:
    Thing.objects.bulk_update([Thing(note='x')], ['note'], batch_size=-1)
    res['neg'] = False
except ValueError:
    res['neg'] = True
try:
    Thing.objects.bulk_update([Thing.objects.create(note='y')], [])
    res['nofields'] = False
except ValueError:
    res['nofields'] = True
try:
    Thing.objects.bulk_update([Thing.objects.create(note='z')], ['id'])
    res['pk'] = False
except ValueError:
    res['pk'] = True
print("validation results:", res)
ok = all(res.values())
print("OK" if ok else "FAIL")
import sys; sys.exit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
import django
from django.conf import settings
settings.configure(
    DEBUG=True,
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
    INSTALLED_APPS=['django.contrib.contenttypes'],
    DEFAULT_AUTO_FIELD='django.db.models.AutoField',
    USE_TZ=False,
)
django.setup()
from django.db import models, connection

class Thing(models.Model):
    note = models.CharField(max_length=100)
    class Meta:
        app_label = 'contenttypes'

with connection.schema_editor() as se:
    se.create_model(Thing)

# Req 1.2 / 1.4: distinct existing rows, single batch -> return == number of objects (int, not None)
objs = [Thing.objects.create(note='a%d' % i) for i in range(5)]
r = Thing.objects.bulk_update(objs, ['note'])
print("bulk_update returned:", repr(r), "type", type(r).__name__)
ok = (r is not None) and isinstance(r, int) and not isinstance(r, bool) and r == 5
print("OK" if ok else "FAIL")
import sys; sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance django__django-14559: bulk_update() must return the total matched-row count instead of None. 7 standalone probes (in-memory sqlite, contenttypes app, a CharField model 'Thing'), all HOLD on the gold-patched tree:
- probe_1 (Req 1.2/1.4): 5 distinct rows single batch -> returns int 5 (not None). PATCHED HOLDS, BASE VIOLATED (returns None). POSITIVE CONTROL, discriminates.
- probe_2 (Req 2.1): empty input -> returns 0. HOLDS.
- probe_3 (Req 2.2 + 2.1): empty input -> returns 0 AND executes 0 queries (len(connection.queries)==0). HOLDS.
- probe_4 (Req 3.1/3.2): [note,note] single batch -> returns 1 (matched once). HOLDS.
- probe_5 (Req 3.3/3.4): [note,note] batch_size=1 -> returns 2 (once per batch). HOLDS.
- probe_6 (Req 1.1/1.3): 10 distinct objs batch_size=3 -> sum across batches == 10. HOLDS.
- probe_7 (Req 4.1/4.2/4.5): negative batch_size, empty fields, and pk field each raise ValueError. HOLDS.

CANDIDATE PATCH (weak.diff): naive fix returning len(objs) instead of summing per-batch update() counts. Applies cleanly at base. REJECTED by the suite: probe_4 VIOLATED (returns 2 for in-batch duplicates where the requirement mandates 1) — demonstrating discriminating power over the repeated-object semantics that are the crux of the fix. probe_1 and probe_5 happen to pass under it, but probe_4 catches it.

All needed runs completed in the official Docker image. >=5 distinct probes all hold on patched; positive control fails at base and holds patched; >=1 wrong candidate exercised and rejected. Verdict SOUND (advisory).

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
import django
from django.conf import settings
settings.configure(
    DEBUG=True,
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
    INSTALLED_APPS=['django.contrib.contenttypes'],
    DEFAULT_AUTO_FIELD='django.db.models.AutoField',
    USE_TZ=False,
)
django.setup()
from django.db import models, connection

class Thing(models.Model):
    note = models.CharField(max_length=100)
    class Meta:
        app_label = 'contenttypes'

with connection.schema_editor() as se:
    se.create_model(Thing)

# Req 1.2 / 1.4: distinct existing rows, single batch -> return == number of objects (int, not None)
objs = [Thing.objects.create(note='a%d' % i) for i in range(5)]
r = Thing.objects.bulk_update(objs, ['note'])
print("bulk_update returned:", repr(r), "type", type(r).__name__)
ok = (r is not None) and isinstance(r, int) and not isinstance(r, bool) and r == 5
print("OK" if ok else "FAIL")
import sys; sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance django__django-14559: bulk_update() must return the total matched-row count instead of None. 7 standalone probes (in-memory sqlite, contenttypes app, a CharField model 'Thing'), all HOLD on the gold-patched tree:
- probe_1 (Req 1.2/1.4): 5 distinct rows single batch -> returns int 5 (not None). PATCHED HOLDS, BASE VIOLATED (returns None). POSITIVE CONTROL, discriminates.
- probe_2 (Req 2.1): empty input -> returns 0. HOLDS.
- probe_3 (Req 2.2 + 2.1): empty input -> returns 0 AND executes 0 queries (len(connection.queries)==0). HOLDS.
- probe_4 (Req 3.1/3.2): [note,note] single batch -> returns 1 (matched once). HOLDS.
- probe_5 (Req 3.3/3.4): [note,note] batch_size=1 -> returns 2 (once per batch). HOLDS.
- probe_6 (Req 1.1/1.3): 10 distinct objs batch_size=3 -> sum across batches == 10. HOLDS.
- probe_7 (Req 4.1/4.2/4.5): negative batch_size, empty fields, and pk field each raise ValueError. HOLDS.

CANDIDATE PATCH (weak.diff): naive fix returning len(objs) instead of summing per-batch update() counts. Applies cleanly at base. REJECTED by the suite: probe_4 VIOLATED (returns 2 for in-batch duplicates where the requirement mandates 1) — demonstrating discriminating power over the repeated-object semantics that are the crux of the fix. probe_1 and probe_5 happen to pass under it, but probe_4 catches it.

All needed runs completed in the official Docker image. >=5 distinct probes all hold on patched; positive control fails at base and holds patched; >=1 wrong candidate exercised and rejected. Verdict SOUND (advisory).

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Gold patch (django/db/models/query.py bulk_update): changes `return` on empty to `return 0`, accumulates `rows_updated += self.filter(pk__in=pks).update(**update_kwargs)` per batch inside the transaction and returns the sum. Requirements model exactly this changed observable behavior. R1 (sum of per-UPDATE match counts, integer, never None) matches. R2 (empty->0, no queries) matches — probe: assertNumQueries(0) passed and r==0. R3 correctly captures the subtle per-batch match semantics (repeated pk within a batch matched once; across batches counted per batch) — probe confirmed [note,note]->1 and batch_size=1->2, exactly the semantics in the official test_patch (test_updated_rows_when_passing_duplicates). R4 preserves pre-existing validation/execution behavior (batch_size<0, no fields, missing pk, non-concrete/m2m/pk fields raise ValueError; atomic transaction; effective batch size) — these were unchanged by the patch and remain valid. Boundary is the changed behavior (the return value across all batches), not a narrow slice. No divergence found.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** requirements.md describes bulk_update()'s new return-value behavior — including the empty-input (0), single/multi-batch sum, and repeated-object counting cases — as behavioral requirements. It legitimately localizes the change (django/db/models/query.py, QuerySet.bulk_update). No hidden-test artifacts leak: no test function/class names, file paths, or parametrization ids; the fix-invented identifier `rows_updated` is never mentioned; the test's magic number 2000 is absent (Req 1.3 uses generic 'large collection'). The duplicate-counting Requirement 3 tracks test_updated_rows_when_passing_duplicates closely but is expressed as pk__in UPDATE semantics (this edge case is also discussed in the publicly-linked ticket #32388) rather than reproducing the test's [note,note]/batch_size=1 → 1/2 parametrization verbatim. This is behavior translation, which is the intended purpose, not test transmission.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
