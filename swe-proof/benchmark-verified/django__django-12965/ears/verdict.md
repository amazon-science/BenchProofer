# P2 adversarial audit — django__django-12965

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
"""Requirement 1.1 / 2.5 (also the positive control):
Full-table delete `Model.objects.all().delete()` SHALL compile to a direct
DELETE FROM with NO 'SELECT' keyword / no subquery.
Exit 0 iff compiled SQL contains no 'SELECT'.
"""
import sys, os
import django
from django.conf import settings

os.makedirs('$SCRATCH', exist_ok=True)
open('$SCRATCH/__init__.py', 'w').close()
open('$SCRATCH/models.py', 'w').close()
sys.path.insert(0, '$SCRATCH')

settings.configure(
    DEBUG=True,
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
    INSTALLED_APPS=['probeapp'],
    USE_TZ=False,
)
django.setup()

from django.db import models, connection

class Author(models.Model):
    name = models.CharField(max_length=50)
    class Meta: app_label = 'probeapp'

with connection.schema_editor() as se:
    se.create_model(Author)

qs = Author.objects.all()
q = qs.query.clone()
q.__class__ = __import__('django.db.models.sql.subqueries', fromlist=['DeleteQuery']).DeleteQuery
compiler = q.get_compiler(using='default')
sql, params = compiler.as_sql()
print("SQL:", sql)
print("single_alias:", compiler.single_alias)
if 'SELECT' in sql.upper():
    print("FAIL: subquery/SELECT present in full-table delete")
    sys.exit(1)
if not sql.upper().startswith('DELETE FROM'):
    print("FAIL: not a direct DELETE FROM")
    sys.exit(1)
print("OK: direct DELETE FROM with no SELECT")
sys.exit(0)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""Requirement 1.2 / 1.3: full-table delete executes as exactly ONE query and
removes every row (rows-affected preserved).
Exit 0 iff exactly 1 query issued AND all rows deleted AND count returned == n.
"""
import sys, os
import django
from django.conf import settings
from django.test.utils import CaptureQueriesContext

os.makedirs('$SCRATCH', exist_ok=True)
open('$SCRATCH/__init__.py', 'w').close()
open('$SCRATCH/models.py', 'w').close()
sys.path.insert(0, '$SCRATCH')
settings.configure(DEBUG=True,
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
    INSTALLED_APPS=['probeapp'], USE_TZ=False)
django.setup()

from django.db import models, connection

class Author(models.Model):
    name = models.CharField(max_length=50)
    class Meta: app_label = 'probeapp'

with connection.schema_editor() as se:
    se.create_model(Author)

Author.objects.create(name='a')
Author.objects.create(name='b')
Author.objects.create(name='c')

with CaptureQueriesContext(connection) as ctx:
    deleted, per = Author.objects.all().delete()

def _is_dml(sql):
    s = sql.strip().upper()
    return not (s in ('BEGIN', 'COMMIT', 'ROLLBACK') or s.startswith('SAVEPOINT')
                or s.startswith('RELEASE SAVEPOINT') or s.startswith('ROLLBACK TO'))

dml = [q['sql'] for q in ctx.captured_queries if _is_dml(q['sql'])]
nqueries = len(dml)
print("queries (dml):", nqueries, "  total captured:", len(ctx.captured_queries))
for q in ctx.captured_queries:
    print("  ", q['sql'])
print("deleted count:", deleted, per)
print("remaining:", Author.objects.count())

if nqueries != 1:
    print("FAIL: expected exactly 1 query, got", nqueries); sys.exit(1)
if deleted != 3 or per.get('probeapp.Author') != 3:
    print("FAIL: rows-affected wrong"); sys.exit(1)
if Author.objects.count() != 0:
    print("FAIL: not all rows deleted"); sys.exit(1)
print("OK: 1 query, all rows removed, count preserved")
sys.exit(0)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""Requirement 3.2: single-table delete WITH a filter emits direct
DELETE FROM t WHERE ... (no subquery) and deletes exactly the matching rows.
Exit 0 iff SQL is direct DELETE...WHERE with no SELECT AND only matching rows gone.
"""
import sys, os
import django
from django.conf import settings
from django.test.utils import CaptureQueriesContext

os.makedirs('$SCRATCH', exist_ok=True)
open('$SCRATCH/__init__.py', 'w').close()
open('$SCRATCH/models.py', 'w').close()
sys.path.insert(0, '$SCRATCH')
settings.configure(DEBUG=True,
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
    INSTALLED_APPS=['probeapp'], USE_TZ=False)
django.setup()

from django.db import models, connection

class Author(models.Model):
    name = models.CharField(max_length=50)
    class Meta: app_label = 'probeapp'

with connection.schema_editor() as se:
    se.create_model(Author)

Author.objects.create(name='keep')
Author.objects.create(name='drop')
Author.objects.create(name='drop')

with CaptureQueriesContext(connection) as ctx:
    deleted, per = Author.objects.filter(name='drop').delete()

sql = ctx.captured_queries[-1]['sql']
print("SQL:", sql)
print("deleted:", deleted, per, "remaining:", Author.objects.count())

if 'SELECT' in sql.upper():
    print("FAIL: filtered single-table delete used a subquery"); sys.exit(1)
if 'WHERE' not in sql.upper():
    print("FAIL: no WHERE clause"); sys.exit(1)
if deleted != 2:
    print("FAIL: wrong rows-affected"); sys.exit(1)
if Author.objects.filter(name='drop').exists() or not Author.objects.filter(name='keep').exists():
    print("FAIL: wrong rows removed"); sys.exit(1)
print("OK: direct filtered DELETE, exactly matching rows removed")
sys.exit(0)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""Requirement 3.1: a delete that references MORE THAN ONE table (filter via a
relation/join) SHALL have single_alias False and emit the subquery-guarded form
(IN (SELECT ...)). Exit 0 iff single_alias is False AND SQL contains a subquery.
"""
import sys, os
import django
from django.conf import settings
from django.test.utils import CaptureQueriesContext

os.makedirs('$SCRATCH', exist_ok=True)
open('$SCRATCH/__init__.py', 'w').close()
open('$SCRATCH/models.py', 'w').close()
sys.path.insert(0, '$SCRATCH')
settings.configure(DEBUG=True,
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
    INSTALLED_APPS=['probeapp'], USE_TZ=False)
django.setup()

from django.db import models, connection

class Author(models.Model):
    name = models.CharField(max_length=50)
    class Meta: app_label = 'probeapp'

class Book(models.Model):
    title = models.CharField(max_length=50)
    author = models.ForeignKey(Author, on_delete=models.CASCADE)
    class Meta: app_label = 'probeapp'

with connection.schema_editor() as se:
    se.create_model(Author)
    se.create_model(Book)

a = Author.objects.create(name='a')
Book.objects.create(title='t', author=a)

# delete Books restricted through the related Author table (join -> 2 tables)
qs = Book.objects.filter(author__name='a')
with CaptureQueriesContext(connection) as ctx:
    qs.delete()

# find the DELETE statement
delsql = [q['sql'] for q in ctx.captured_queries if q['sql'].strip().upper().startswith('DELETE')]
print("DELETE stmts:")
for s in delsql:
    print("  ", s)

joined = [s for s in delsql if 'SELECT' in s.upper()]
if not joined:
    print("FAIL: multi-table delete did not use a subquery-guarded form"); sys.exit(1)
print("OK: relation-restricted delete used IN (SELECT ...) subquery")
sys.exit(0)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""Requirement 2.1/2.2/2.4: evaluating single_alias on a fresh full-table delete
query SHALL first register the base table (alias_map gains the base table with a
positive refcount) and report True (exactly one active reference).
Exit 0 iff base table absent before, present+active after, and single_alias True.
"""
import sys, os
import django
from django.conf import settings

os.makedirs('$SCRATCH', exist_ok=True)
open('$SCRATCH/__init__.py', 'w').close()
open('$SCRATCH/models.py', 'w').close()
sys.path.insert(0, '$SCRATCH')
settings.configure(DEBUG=True,
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
    INSTALLED_APPS=['probeapp'], USE_TZ=False)
django.setup()

from django.db import models, connection
from django.db.models.sql.subqueries import DeleteQuery

class Author(models.Model):
    name = models.CharField(max_length=50)
    class Meta: app_label = 'probeapp'

with connection.schema_editor() as se:
    se.create_model(Author)

qs = Author.objects.all()
q = qs.query.clone()
q.__class__ = DeleteQuery
base = q.get_meta().db_table
compiler = q.get_compiler(using='default')

active_before = [t for t in q.alias_map if q.alias_refcount[t] > 0]
print("active refs before single_alias:", active_before)

val = compiler.single_alias  # evaluation should register base table

active_after = [t for t in q.alias_map if q.alias_refcount[t] > 0]
print("active refs after:", active_after)
print("single_alias:", val)

if active_before:
    print("FAIL: base table was already active before (setup assumption wrong)"); sys.exit(1)
if base not in active_after:
    print("FAIL: base table not registered as active after evaluating single_alias"); sys.exit(1)
if len(active_after) != 1:
    print("FAIL: expected exactly one active reference"); sys.exit(1)
if val is not True:
    print("FAIL: single_alias should be True for full-table delete"); sys.exit(1)
print("OK: base table ensured present, single_alias True")
sys.exit(0)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
"""Requirement 3.3/3.4: cascade/fast-delete behavior for related objects is
preserved. Deleting all Authors cascades to their Books.
Exit 0 iff after Author.objects.all().delete() both tables are empty and the
returned per-model counts include both models.
"""
import sys, os
import django
from django.conf import settings

os.makedirs('$SCRATCH', exist_ok=True)
open('$SCRATCH/__init__.py', 'w').close()
open('$SCRATCH/models.py', 'w').close()
sys.path.insert(0, '$SCRATCH')
settings.configure(DEBUG=True,
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
    INSTALLED_APPS=['probeapp'], USE_TZ=False)
django.setup()

from django.db import models, connection

class Author(models.Model):
    name = models.CharField(max_length=50)
    class Meta: app_label = 'probeapp'

class Book(models.Model):
    title = models.CharField(max_length=50)
    author = models.ForeignKey(Author, on_delete=models.CASCADE)
    class Meta: app_label = 'probeapp'

with connection.schema_editor() as se:
    se.create_model(Author)
    se.create_model(Book)

a1 = Author.objects.create(name='a1')
a2 = Author.objects.create(name='a2')
Book.objects.create(title='b1', author=a1)
Book.objects.create(title='b2', author=a1)
Book.objects.create(title='b3', author=a2)

deleted, per = Author.objects.all().delete()
print("deleted:", deleted, per)
print("authors:", Author.objects.count(), "books:", Book.objects.count())

if Author.objects.count() != 0 or Book.objects.count() != 0:
    print("FAIL: cascade did not remove all rows"); sys.exit(1)
if per.get('probeapp.Author') != 2 or per.get('probeapp.Book') != 3:
    print("FAIL: per-model cascade counts wrong:", per); sys.exit(1)
print("OK: cascade delete preserved (all rows removed, counts correct)")
sys.exit(0)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Requirement 1.1 / 2.5 (also the positive control):
Full-table delete `Model.objects.all().delete()` SHALL compile to a direct
DELETE FROM with NO 'SELECT' keyword / no subquery.
Exit 0 iff compiled SQL contains no 'SELECT'.
"""
import sys, os
import django
from django.conf import settings

os.makedirs('$SCRATCH', exist_ok=True)
open('$SCRATCH/__init__.py', 'w').close()
open('$SCRATCH/models.py', 'w').close()
sys.path.insert(0, '$SCRATCH')

settings.configure(
    DEBUG=True,
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
    INSTALLED_APPS=['probeapp'],
    USE_TZ=False,
)
django.setup()

from django.db import models, connection

class Author(models.Model):
    name = models.CharField(max_length=50)
    class Meta: app_label = 'probeapp'

with connection.schema_editor() as se:
    se.create_model(Author)

qs = Author.objects.all()
q = qs.query.clone()
q.__class__ = __import__('django.db.models.sql.subqueries', fromlist=['DeleteQuery']).DeleteQuery
compiler = q.get_compiler(using='default')
sql, params = compiler.as_sql()
print("SQL:", sql)
print("single_alias:", compiler.single_alias)
if 'SELECT' in sql.upper():
    print("FAIL: subquery/SELECT present in full-table delete")
    sys.exit(1)
if not sql.upper().startswith('DELETE FROM'):
    print("FAIL: not a direct DELETE FROM")
    sys.exit(1)
print("OK: direct DELETE FROM with no SELECT")
sys.exit(0)
```

Prepatch bug re-encoded as an attack: `True`.

Instance django__django-12965: make full-table delete emit direct DELETE FROM (no self-referential subquery) by having SQLDeleteCompiler.single_alias call query.get_initial_alias() to register the base table before counting active references.

Probes (all standalone python, run in the official image via nl_attack; each bootstraps a dynamic 'probeapp' Django app on in-memory sqlite):
- probe_1 (Req 1.1 / 2.5; POSITIVE CONTROL): compiles Model.objects.all().delete() and asserts no 'SELECT' in SQL, starts with DELETE FROM. PATCHED: HOLDS (DELETE FROM "probeapp_author", single_alias True). BASE: FAILS (DELETE ... WHERE id IN (SELECT id FROM ...), single_alias False). Discriminates.
- probe_2 (Req 1.2 / 1.3): executes all().delete(), counts DML queries (filtering BEGIN/COMMIT/SAVEPOINT as assertNumQueries does), asserts exactly 1 query, deleted==3, count preserved, all rows gone. PATCHED: HOLDS. (Holds at base too — this is a preservation criterion, not the discriminator.)
- probe_3 (Req 3.2): filtered single-table delete emits direct DELETE...WHERE, no SELECT, exactly matching rows removed. PATCHED: HOLDS.
- probe_4 (Req 3.1): relation-join-restricted delete (Book.objects.filter(author__name=...).delete()) keeps the IN (SELECT ...) subquery-guarded form. PATCHED: HOLDS.
- probe_5 (Req 2.1/2.2/2.4): evaluating single_alias on a fresh DeleteQuery registers the base table as a new active reference (absent before, present+active after) and reports True (exactly one active ref). PATCHED: HOLDS.
- probe_6 (Req 3.3/3.4): cascade delete via all().delete() removes Authors and their Books; per-model counts correct. PATCHED: HOLDS.

CANDIDATE PATCH (weak_where_shortcut, applies at base_commit): the lazy fix that leaves single_alias unchanged and instead special-cases as_sql with `if self.single_alias or not self.query.where`. This conforms to a weak reading (full-table deletes have no WHERE, so they take the direct branch) but does NOT fix single_alias itself. Result under the suite: REJECTED. probe_5 fails (single_alias still False, base table never registered — Req 2.1/2.2/2.4 violated); probe_1 and probe_2 CRASH (self.query.base_table is None because get_initial_alias() was never called, so quote_name(None) raises AttributeError) — Req 1.1/1.2 violated. This demonstrates the suite discriminates a requirements-non-conforming wrong fix.

All 6 probes HOLD on the gold-patched tree; the positive control (probe_1) fails at base and holds when patched; at least one candidate patch is REJECTED by the suite. Verdict SOUND.

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
"""Requirement 1.1 / 2.5 (also the positive control):
Full-table delete `Model.objects.all().delete()` SHALL compile to a direct
DELETE FROM with NO 'SELECT' keyword / no subquery.
Exit 0 iff compiled SQL contains no 'SELECT'.
"""
import sys, os
import django
from django.conf import settings

os.makedirs('$SCRATCH', exist_ok=True)
open('$SCRATCH/__init__.py', 'w').close()
open('$SCRATCH/models.py', 'w').close()
sys.path.insert(0, '$SCRATCH')

settings.configure(
    DEBUG=True,
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
    INSTALLED_APPS=['probeapp'],
    USE_TZ=False,
)
django.setup()

from django.db import models, connection

class Author(models.Model):
    name = models.CharField(max_length=50)
    class Meta: app_label = 'probeapp'

with connection.schema_editor() as se:
    se.create_model(Author)

qs = Author.objects.all()
q = qs.query.clone()
q.__class__ = __import__('django.db.models.sql.subqueries', fromlist=['DeleteQuery']).DeleteQuery
compiler = q.get_compiler(using='default')
sql, params = compiler.as_sql()
print("SQL:", sql)
print("single_alias:", compiler.single_alias)
if 'SELECT' in sql.upper():
    print("FAIL: subquery/SELECT present in full-table delete")
    sys.exit(1)
if not sql.upper().startswith('DELETE FROM'):
    print("FAIL: not a direct DELETE FROM")
    sys.exit(1)
print("OK: direct DELETE FROM with no SELECT")
sys.exit(0)
```

Prepatch bug re-encoded as an attack: `True`.

Instance django__django-12965: make full-table delete emit direct DELETE FROM (no self-referential subquery) by having SQLDeleteCompiler.single_alias call query.get_initial_alias() to register the base table before counting active references.

Probes (all standalone python, run in the official image via nl_attack; each bootstraps a dynamic 'probeapp' Django app on in-memory sqlite):
- probe_1 (Req 1.1 / 2.5; POSITIVE CONTROL): compiles Model.objects.all().delete() and asserts no 'SELECT' in SQL, starts with DELETE FROM. PATCHED: HOLDS (DELETE FROM "probeapp_author", single_alias True). BASE: FAILS (DELETE ... WHERE id IN (SELECT id FROM ...), single_alias False). Discriminates.
- probe_2 (Req 1.2 / 1.3): executes all().delete(), counts DML queries (filtering BEGIN/COMMIT/SAVEPOINT as assertNumQueries does), asserts exactly 1 query, deleted==3, count preserved, all rows gone. PATCHED: HOLDS. (Holds at base too — this is a preservation criterion, not the discriminator.)
- probe_3 (Req 3.2): filtered single-table delete emits direct DELETE...WHERE, no SELECT, exactly matching rows removed. PATCHED: HOLDS.
- probe_4 (Req 3.1): relation-join-restricted delete (Book.objects.filter(author__name=...).delete()) keeps the IN (SELECT ...) subquery-guarded form. PATCHED: HOLDS.
- probe_5 (Req 2.1/2.2/2.4): evaluating single_alias on a fresh DeleteQuery registers the base table as a new active reference (absent before, present+active after) and reports True (exactly one active ref). PATCHED: HOLDS.
- probe_6 (Req 3.3/3.4): cascade delete via all().delete() removes Authors and their Books; per-model counts correct. PATCHED: HOLDS.

CANDIDATE PATCH (weak_where_shortcut, applies at base_commit): the lazy fix that leaves single_alias unchanged and instead special-cases as_sql with `if self.single_alias or not self.query.where`. This conforms to a weak reading (full-table deletes have no WHERE, so they take the direct branch) but does NOT fix single_alias itself. Result under the suite: REJECTED. probe_5 fails (single_alias still False, base table never registered — Req 2.1/2.2/2.4 violated); probe_1 and probe_2 CRASH (self.query.base_table is None because get_initial_alias() was never called, so quote_name(None) raises AttributeError) — Req 1.1/1.2 violated. This demonstrates the suite discriminates a requirements-non-conforming wrong fix.

All 6 probes HOLD on the gold-patched tree; the positive control (probe_1) fails at base and holds when patched; at least one candidate patch is REJECTED by the suite. Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Patch adds `self.query.get_initial_alias()` before the refcount==1 test in SQLDeleteCompiler.single_alias. The EARS bundle models the changed OBSERVABLE behavior (SQL statement shape: subquery vs direct DELETE) and the single_alias predicate, not a narrow helper slice. Boundary is correct: full-table single-table -> direct (Req1/2.5), single-table filtered -> direct WHERE (Req3.2), multi-table -> subquery preserved (Req3.1). Base-vs-patched probes confirm the discriminator (base fails Req1's no-SELECT assertion; patched passes). FAIL_TO_PASS test_fast_delete_all is consistent with Req1.2 (single query). Req2.2/2.3 (get_initial_alias adds/keeps base table active) are true implementation-level descriptions of get_initial_alias and are not contradicted by behavior.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** All identifiers named in requirements.md (SQLDeleteCompiler, single_alias, alias_map, alias_refcount, _as_sql, as_sql) pre-exist in the target module compiler.py — legitimate change localization, not leaked from tests. The gold's fix-invented call get_initial_alias() is NOT named; it is described only behaviorally ('ensure the deletion's own base table is registered'). The Req 1 criteria ('no SELECT keyword', 'exactly one database query') translate behavior that the PUBLIC problem_statement already exposes (direct DELETE vs subquery, single-query performance) — no hidden-test leakage: they do not reveal the test name test_fast_delete_all, its path tests/delete/tests.py, the FastDeleteTests class, the User model, assertNumQueries/captured_queries API, or any parametrization ids. Req 3.4's scenario list (unconditional/filtered/cascading/multi-table deletes) is a generic deletion taxonomy, not a mirror of the specific PASS_TO_PASS test set. No quoted/near-quoted test or gold code.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
