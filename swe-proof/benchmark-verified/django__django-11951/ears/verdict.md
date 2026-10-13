# P2 adversarial audit — django__django-11951

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

Counterexample / evidence:

```
Under the weak patch (comment-only; keeps `batch_size = (batch_size or max(...))` verbatim), probe_1 is REJECTED: with backend max=3 and explicit batch_size=7 over 10 objects, the weak/base code issues ceil(10/7)=2 INSERT statements instead of the required ceil(10/3)=4. This is exactly the Req1 crit2/crit5 violation the gold patch fixes.
```

**Attacks re-run (5):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
# POSITIVE CONTROL / Req1 crit 2&5: explicit batch_size > backend max -> cap at max.
# n=10 objs, backend max M=3, explicit batch_size=7.
# effective chunk = min(7,3)=3 -> ceil(10/3)=4 INSERT statements.
# At base (verbatim 7): ceil(10/7)=2 -> discriminates.
import math
import django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True,
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
        INSTALLED_APPS=['django.contrib.contenttypes'], USE_TZ=False)
django.setup()
from django.db import connections, models
from django.db.models.query import QuerySet

class Thing(models.Model):
    name = models.CharField(max_length=50)
    class Meta:
        app_label = 'contenttypes'

conn = connections['default']
with conn.schema_editor() as se:
    se.create_model(Thing)
conn.ops.bulk_batch_size = lambda fields, objs: 3

calls = []
orig = QuerySet._insert
def wrap(self, objs, *a, **k):
    calls.append(list(objs))
    return orig(self, objs, *a, **k)
QuerySet._insert = wrap

objs = [Thing(name='x%d' % i) for i in range(10)]
Thing.objects.bulk_create(objs, batch_size=7)
n_stmts = len(calls)
expected = math.ceil(10 / 3)
print("insert statements=%d expected=%d chunk sizes=%s" % (n_stmts, expected, [len(c) for c in calls]))
assert n_stmts == expected, "batch size not capped at backend max"
# each chunk (except maybe last) size 3
for c in calls[:-1]:
    assert len(c) == 3, "chunk not capped to 3"
print("OK: explicit batch_size capped at backend max")
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
# Req1 crit3: explicit batch_size <= backend max -> use requested batch_size.
# n=10, backend max M=8, batch_size=4 -> effective=min(4,8)=4 -> ceil(10/4)=3 stmts.
import math, django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True,
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
        INSTALLED_APPS=['django.contrib.contenttypes'], USE_TZ=False)
django.setup()
from django.db import connections, models
from django.db.models.query import QuerySet
class Thing(models.Model):
    name = models.CharField(max_length=50)
    class Meta: app_label = 'contenttypes'
conn = connections['default']
with conn.schema_editor() as se: se.create_model(Thing)
conn.ops.bulk_batch_size = lambda fields, objs: 8
calls = []
orig = QuerySet._insert
QuerySet._insert = lambda self, objs, *a, **k: (calls.append(list(objs)), orig(self, objs, *a, **k))[1]
Thing.objects.bulk_create([Thing(name='x%d'%i) for i in range(10)], batch_size=4)
print("stmts=%d sizes=%s" % (len(calls), [len(c) for c in calls]))
assert len(calls) == math.ceil(10/4), "did not use requested batch_size"
assert all(len(c) <= 4 for c in calls)
assert [len(c) for c in calls] == [4,4,2]
print("OK: requested batch_size used when <= backend max")
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
# Req2 crit1&2: falsy batch_size (None and 0) -> _batched_insert uses backend max.
# Tests _batched_insert directly (bulk_create asserts >0 so 0 can't pass through it).
# n=10, backend max=4 -> ceil(10/4)=3 stmts for both None and 0.
# Req2 crit3 + Req1: objs<=chunk -> single INSERT (n=3,max=10,bs=None).
import math, django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True,
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
        INSTALLED_APPS=['django.contrib.contenttypes'], USE_TZ=False)
django.setup()
from django.db import connections, models
from django.db.models.query import QuerySet
class Thing(models.Model):
    name = models.CharField(max_length=50)
    class Meta: app_label = 'contenttypes'
conn = connections['default']
with conn.schema_editor() as se: se.create_model(Thing)
orig = QuerySet._insert
fields = [f for f in Thing._meta.concrete_fields if not f.primary_key]

def run_batched(batch_size, maxv, n):
    conn.ops.bulk_batch_size = lambda f, o: maxv
    calls = []
    QuerySet._insert = lambda self, objs, *a, **k: (calls.append(list(objs)), orig(self, objs, *a, **k))[1]
    qs = Thing.objects.get_queryset()
    objs = [Thing(name='x%d'%i) for i in range(n)]
    list(qs._batched_insert(objs, fields, batch_size))
    QuerySet._insert = orig
    return len(calls)

s_none = run_batched(None, 4, 10)
s_zero = run_batched(0, 4, 10)
s_single = run_batched(None, 10, 3)
print("None:%d 0:%d single:%d" % (s_none, s_zero, s_single))
assert s_none == math.ceil(10/4), "None did not use backend max"
assert s_zero == math.ceil(10/4), "0 (falsy) did not use backend max"
assert s_single == 1, "objs<=chunk not single insert"
print("OK: falsy batch_size (None,0) uses backend max; single insert when objs<=chunk")
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
# Req3 crit1&2: every object inserted exactly once, order preserved, consecutive chunks.
# Also verifies data actually persisted correctly. n=10, max=3, batch_size=100 (huge).
import django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True,
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
        INSTALLED_APPS=['django.contrib.contenttypes'], USE_TZ=False)
django.setup()
from django.db import connections, models
from django.db.models.query import QuerySet
class Thing(models.Model):
    name = models.CharField(max_length=50)
    class Meta: app_label = 'contenttypes'
conn = connections['default']
with conn.schema_editor() as se: se.create_model(Thing)
conn.ops.bulk_batch_size = lambda fields, objs: 3
calls = []
orig = QuerySet._insert
QuerySet._insert = lambda self, objs, *a, **k: (calls.append(list(objs)), orig(self, objs, *a, **k))[1]
names = ['x%02d' % i for i in range(10)]
Thing.objects.bulk_create([Thing(name=nm) for nm in names], batch_size=100)
# reconstruct chunk membership by name
chunk_names = [[o.name for o in c] for c in calls]
flat = [nm for c in chunk_names for nm in c]
print("chunks=%s" % chunk_names)
assert flat == names, "objects not consecutive/ordered/exactly-once: %s" % flat
# consecutive: concatenation equals ordered original -> already checked
# persisted rows
db_names = sorted(Thing.objects.values_list('name', flat=True))
assert db_names == sorted(names), "not all persisted exactly once: %s" % db_names
print("OK: each obj inserted once, order preserved, chunks consecutive")
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
# Req3 crit5: non-positive explicit batch_size still rejected (as before -> AssertionError).
# Req3 crit6: empty objs -> no INSERT statements.
import django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True,
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
        INSTALLED_APPS=['django.contrib.contenttypes'], USE_TZ=False)
django.setup()
from django.db import connections, models
from django.db.models.query import QuerySet
class Thing(models.Model):
    name = models.CharField(max_length=50)
    class Meta: app_label = 'contenttypes'
conn = connections['default']
with conn.schema_editor() as se: se.create_model(Thing)
conn.ops.bulk_batch_size = lambda fields, objs: 5

# negative / zero batch_size rejected (same as before: bulk_create asserts >0)
for bad in (-1, -5, 0):
    try:
        Thing.objects.bulk_create([Thing(name='a')], batch_size=bad)
        print("ERROR: no error for batch_size=%d" % bad); raise SystemExit(1)
    except (ValueError, AssertionError) as e:
        print("rejected batch_size=%d: %r" % (bad, type(e).__name__))

# empty -> no INSERT
calls = []
orig = QuerySet._insert
QuerySet._insert = lambda self, objs, *a, **k: (calls.append(list(objs)), orig(self, objs, *a, **k))[1]
res = Thing.objects.bulk_create([], batch_size=10)
QuerySet._insert = orig
print("empty insert stmts=%d result=%r" % (len(calls), res))
assert len(calls) == 0, "empty objs issued INSERT"
print("OK: non-positive batch_size rejected; empty objs -> no INSERT")
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
# POSITIVE CONTROL / Req1 crit 2&5: explicit batch_size > backend max -> cap at max.
# n=10 objs, backend max M=3, explicit batch_size=7.
# effective chunk = min(7,3)=3 -> ceil(10/3)=4 INSERT statements.
# At base (verbatim 7): ceil(10/7)=2 -> discriminates.
import math
import django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True,
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
        INSTALLED_APPS=['django.contrib.contenttypes'], USE_TZ=False)
django.setup()
from django.db import connections, models
from django.db.models.query import QuerySet

class Thing(models.Model):
    name = models.CharField(max_length=50)
    class Meta:
        app_label = 'contenttypes'

conn = connections['default']
with conn.schema_editor() as se:
    se.create_model(Thing)
conn.ops.bulk_batch_size = lambda fields, objs: 3

calls = []
orig = QuerySet._insert
def wrap(self, objs, *a, **k):
    calls.append(list(objs))
    return orig(self, objs, *a, **k)
QuerySet._insert = wrap

objs = [Thing(name='x%d' % i) for i in range(10)]
Thing.objects.bulk_create(objs, batch_size=7)
n_stmts = len(calls)
expected = math.ceil(10 / 3)
print("insert statements=%d expected=%d chunk sizes=%s" % (n_stmts, expected, [len(c) for c in calls]))
assert n_stmts == expected, "batch size not capped at backend max"
# each chunk (except maybe last) size 3
for c in calls[:-1]:
    assert len(c) == 3, "chunk not capped to 3"
print("OK: explicit batch_size capped at backend max")
```

Prepatch bug re-encoded as an attack: `True`.

Probes exercise the requirement criteria by monkey-patching connections['default'].ops.bulk_batch_size to force a known backend max and wrapping QuerySet._insert to count INSERT statements / chunk membership on an in-memory sqlite model.

Results (each RE-RUN by runner):
- probe_1 (Req1 crit2&5, POSITIVE CONTROL): explicit batch_size=7 > max=3, n=10 -> expect 4 stmts, chunks [3,3,3,1]. HOLDS patched; VIOLATED at base (2 stmts) and VIOLATED under weak patch. Discriminates.
- probe_2 (Req1 crit3): batch_size=4 <= max=8, n=10 -> uses requested 4 -> [4,4,2], 3 stmts. HOLDS patched; HOLDS under weak patch (weak patch only breaks the >max case) — correctly does not over-discriminate.
- probe_3 (Req2 crit1,2,3): tests _batched_insert directly (bulk_create asserts >0 so 0 cannot reach it via bulk_create). None and 0 (falsy) both -> backend max=4 -> 3 stmts; n=3<=max=10 -> 1 stmt. HOLDS patched.
- probe_4 (Req3 crit1&2): n=10, max=3, batch_size=100 -> chunks [x00-02][x03-05][x06-08][x09]; every object inserted exactly once, order preserved, consecutive; DB rows match. HOLDS patched.
- probe_5 (Req3 crit5&6): batch_size in {-1,-5,0} rejected (AssertionError, 'as before'); empty objs -> 0 INSERT statements. HOLDS patched.

All 5 probes hold on the gold-patched tree; positive control fails at base; the requirements-permissive weak candidate (verbatim batch_size) is rejected by probe_1. Suite has discriminating power and the requirements faithfully constrain the gold behavior. No VIOLATION or TOO-WEAK finding.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 5 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 5 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 5 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

Counterexample / evidence:

```
Under the weak patch (comment-only; keeps `batch_size = (batch_size or max(...))` verbatim), probe_1 is REJECTED: with backend max=3 and explicit batch_size=7 over 10 objects, the weak/base code issues ceil(10/7)=2 INSERT statements instead of the required ceil(10/3)=4. This is exactly the Req1 crit2/crit5 violation the gold patch fixes.
```

**Attacks re-run (5):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

_The 5 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts, and on this backend both roles put it through the same derivation: every block below is a requirement probe run on the gold-patched tree, and the `machine verdict:` line each role publishes above reports BOTH that its probes hold there and how many candidate patches the probe suite rejected — so the two roles re-ran ONE probe suite and each recorded its own outcome for every probe in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `probe_1.py` → holds on the patched tree (good)

Attack 2 — `probe_2.py` → holds on the patched tree (good)

Attack 3 — `probe_3.py` → holds on the patched tree (good)

Attack 4 — `probe_4.py` → holds on the patched tree (good)

Attack 5 — `probe_5.py` → holds on the patched tree (good)

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
# POSITIVE CONTROL / Req1 crit 2&5: explicit batch_size > backend max -> cap at max.
# n=10 objs, backend max M=3, explicit batch_size=7.
# effective chunk = min(7,3)=3 -> ceil(10/3)=4 INSERT statements.
# At base (verbatim 7): ceil(10/7)=2 -> discriminates.
import math
import django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True,
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
        INSTALLED_APPS=['django.contrib.contenttypes'], USE_TZ=False)
django.setup()
from django.db import connections, models
from django.db.models.query import QuerySet

class Thing(models.Model):
    name = models.CharField(max_length=50)
    class Meta:
        app_label = 'contenttypes'

conn = connections['default']
with conn.schema_editor() as se:
    se.create_model(Thing)
conn.ops.bulk_batch_size = lambda fields, objs: 3

calls = []
orig = QuerySet._insert
def wrap(self, objs, *a, **k):
    calls.append(list(objs))
    return orig(self, objs, *a, **k)
QuerySet._insert = wrap

objs = [Thing(name='x%d' % i) for i in range(10)]
Thing.objects.bulk_create(objs, batch_size=7)
n_stmts = len(calls)
expected = math.ceil(10 / 3)
print("insert statements=%d expected=%d chunk sizes=%s" % (n_stmts, expected, [len(c) for c in calls]))
assert n_stmts == expected, "batch size not capped at backend max"
# each chunk (except maybe last) size 3
for c in calls[:-1]:
    assert len(c) == 3, "chunk not capped to 3"
print("OK: explicit batch_size capped at backend max")
```

Prepatch bug re-encoded as an attack: `True`.

Probes exercise the requirement criteria by monkey-patching connections['default'].ops.bulk_batch_size to force a known backend max and wrapping QuerySet._insert to count INSERT statements / chunk membership on an in-memory sqlite model.

Results (each RE-RUN by runner):
- probe_1 (Req1 crit2&5, POSITIVE CONTROL): explicit batch_size=7 > max=3, n=10 -> expect 4 stmts, chunks [3,3,3,1]. HOLDS patched; VIOLATED at base (2 stmts) and VIOLATED under weak patch. Discriminates.
- probe_2 (Req1 crit3): batch_size=4 <= max=8, n=10 -> uses requested 4 -> [4,4,2], 3 stmts. HOLDS patched; HOLDS under weak patch (weak patch only breaks the >max case) — correctly does not over-discriminate.
- probe_3 (Req2 crit1,2,3): tests _batched_insert directly (bulk_create asserts >0 so 0 cannot reach it via bulk_create). None and 0 (falsy) both -> backend max=4 -> 3 stmts; n=3<=max=10 -> 1 stmt. HOLDS patched.
- probe_4 (Req3 crit1&2): n=10, max=3, batch_size=100 -> chunks [x00-02][x03-05][x06-08][x09]; every object inserted exactly once, order preserved, consecutive; DB rows match. HOLDS patched.
- probe_5 (Req3 crit5&6): batch_size in {-1,-5,0} rejected (AssertionError, 'as before'); empty objs -> 0 INSERT statements. HOLDS patched.

All 5 probes hold on the gold-patched tree; positive control fails at base; the requirements-permissive weak candidate (verbatim batch_size) is rejected by probe_1. Suite has discriminating power and the requirements faithfully constrain the gold behavior. No VIOLATION or TOO-WEAK finding.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Probe HOLDS on gold-patched (exit 0, 4 stmts sizes [3,3,3,1]) and VIOLATED on base (1 stmt). Modeling boundary is correct: requirements pin the changed observable (effective chunk size = min(requested, backend max) and resulting statement count), not a narrow helper slice. bulk_batch_size formula, falsy-default preservation, and unchanged-semantics fences all faithful.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The problem_statement already publishes the gold fix logic verbatim (`batch_size = min(batch_size, max_batch_size) if batch_size else max_batch_size`) and names query.py/bulk_create/bulk_update, so almost nothing here is hidden-only. requirements.md translates this into behavioral acceptance criteria. Nearest-to-test lines: Req 1.1 restates `max(connections[db].ops.bulk_batch_size(fields, objs), 1)` (bulk_batch_size is a public API signature; the `,1` floor is a behavioral description of the published fix) and Req 1.5 describes the ceil() query count and the 'batch_size one greater than the backend maximum' boundary. These are behavioral consequences of capping, stated generically. No hidden-test artifacts appear: no test name/path (test_explicit_batch_size_respects_max_batch_size), no Country model, no 1000-object count, no fields list ['name','iso_two_letter','description'], no assertNumQueries/skipUnlessDBFeature. No fix-invented identifiers (only max_batch_size, which is already in the problem_statement). Judgment: legitimate behavior translation, not test/gold transmission.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
