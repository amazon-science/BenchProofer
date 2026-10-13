# P2 adversarial audit — django__django-14122

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
"""POSITIVE CONTROL / Req 1.2, 1.3: aggregating over a model with Meta.ordering
must group ONLY by the requested column, not be split by the ordering field.

Model Article has Meta.ordering=['headline']. We group by 'author' and count.
Multiple rows share an author but have distinct headlines. Correct behavior:
one aggregated row per author. On base (bug): the ordering column 'headline'
widens GROUP BY, splitting into one row per (author, headline).

Exit 0 iff grouping is by author only (correct counts).
"""
import django
from django.conf import settings
settings.configure(
    DEBUG=True,
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
    INSTALLED_APPS=['probeapp'],
    USE_TZ=False,
)
import sys, types
m = types.ModuleType('probeapp')
m.__path__ = ['/testbed']
sys.modules['probeapp'] = m
django.setup()

from django.db import models, connection
from django.db.models import Count

class Article(models.Model):
    headline = models.CharField(max_length=100)
    author = models.IntegerField()

    class Meta:
        app_label = 'probeapp'
        ordering = ['headline']

with connection.schema_editor() as se:
    se.create_model(Article)

# author 1 has 3 articles with distinct headlines; author 2 has 1
Article.objects.create(headline='a1', author=1)
Article.objects.create(headline='b2', author=1)
Article.objects.create(headline='c3', author=1)
Article.objects.create(headline='d4', author=2)

qs = Article.objects.values('author').annotate(count=Count('author'))
result = {row['author']: row['count'] for row in qs}
print("aggregated rows:", sorted(qs, key=lambda r: r['author']))
print("num groups:", len(list(qs)))

expected = {1: 3, 2: 1}
if result != expected:
    print(f"VIOLATION: got {result}, expected {expected}")
    sys.exit(1)
print("OK: grouped by author only, correct counts")
sys.exit(0)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""Req 1.1 / 1.2 (SQL level): with implicit Meta.ordering, the compiled GROUP BY
clause must NOT reference the ordering column ('headline'), only the grouped
column ('author').

Exit 0 iff 'headline' does not appear in the GROUP BY clause.
"""
import django
from django.conf import settings
settings.configure(
    DEBUG=True,
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
    INSTALLED_APPS=['probeapp'],
    USE_TZ=False,
)
import sys, types
m = types.ModuleType('probeapp')
m.__path__ = ['/testbed']
sys.modules['probeapp'] = m
django.setup()

from django.db import models, connection
from django.db.models import Count

class Article(models.Model):
    headline = models.CharField(max_length=100)
    author = models.IntegerField()

    class Meta:
        app_label = 'probeapp'
        ordering = ['headline']

with connection.schema_editor() as se:
    se.create_model(Article)

qs = Article.objects.values('author').annotate(count=Count('author'))
sql, params = qs.query.sql_with_params()
print("SQL:", sql)

low = sql.lower()
gb_idx = low.find('group by')
group_by_clause = sql[gb_idx:] if gb_idx >= 0 else ''
# cut off at ORDER BY if present
ob = group_by_clause.lower().find('order by')
if ob >= 0:
    group_by_clause = group_by_clause[:ob]
print("GROUP BY clause:", group_by_clause)

if 'headline' in group_by_clause.lower():
    print("VIOLATION: 'headline' (Meta.ordering field) present in GROUP BY")
    sys.exit(1)
if 'author' not in group_by_clause.lower():
    print("VIOLATION: 'author' missing from GROUP BY")
    sys.exit(1)
print("OK: GROUP BY groups by author only, no ordering column")
sys.exit(0)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""Req 2.1: EXPLICIT ordering must still contribute grouping columns.

When the caller explicitly order_by('headline') on an aggregate query, the
ordering column MUST be added to GROUP BY (preserved pre-fix behavior). This
must hold regardless of Meta.ordering, because the ordering here did NOT come
from the implicit default.

Exit 0 iff 'headline' IS present in the GROUP BY clause for the explicit case.
"""
import django
from django.conf import settings
settings.configure(
    DEBUG=True,
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
    INSTALLED_APPS=['probeapp'],
    USE_TZ=False,
)
import sys, types
m = types.ModuleType('probeapp')
m.__path__ = ['/testbed']
sys.modules['probeapp'] = m
django.setup()

from django.db import models, connection
from django.db.models import Count

class Article(models.Model):
    headline = models.CharField(max_length=100)
    author = models.IntegerField()

    class Meta:
        app_label = 'probeapp'
        ordering = ['headline']

with connection.schema_editor() as se:
    se.create_model(Article)

qs = (Article.objects.values('author')
      .annotate(count=Count('author'))
      .order_by('headline'))
sql, params = qs.query.sql_with_params()
print("SQL:", sql)

low = sql.lower()
gb_idx = low.find('group by')
group_by_clause = sql[gb_idx:] if gb_idx >= 0 else ''
ob = group_by_clause.lower().find('order by')
if ob >= 0:
    group_by_clause = group_by_clause[:ob]
print("GROUP BY clause:", group_by_clause)

if 'headline' not in group_by_clause.lower():
    print("VIOLATION: explicit order_by('headline') did NOT add headline to GROUP BY")
    sys.exit(1)
print("OK: explicit ordering column present in GROUP BY")
sys.exit(0)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""Req 3.6: for an aggregate query whose ordering came from the implicit
default, the ORDER BY output SHALL still be suppressed (previously-fixed
behavior kept). So an implicit-Meta-ordering aggregate emits NO ORDER BY.

Exit 0 iff the compiled SQL for the meta-ordering aggregate has no ORDER BY.
"""
import django
from django.conf import settings
settings.configure(
    DEBUG=True,
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
    INSTALLED_APPS=['probeapp'],
    USE_TZ=False,
)
import sys, types
m = types.ModuleType('probeapp')
m.__path__ = ['/testbed']
sys.modules['probeapp'] = m
django.setup()

from django.db import models, connection
from django.db.models import Count

class Article(models.Model):
    headline = models.CharField(max_length=100)
    author = models.IntegerField()

    class Meta:
        app_label = 'probeapp'
        ordering = ['headline']

with connection.schema_editor() as se:
    se.create_model(Article)

qs = Article.objects.values('author').annotate(count=Count('author'))
sql, params = qs.query.sql_with_params()
print("SQL:", sql)

if 'order by' in sql.lower():
    print("VIOLATION: ORDER BY emitted for implicit-default aggregate")
    sys.exit(1)
print("OK: no ORDER BY emitted for implicit-default aggregate")
sys.exit(0)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""Req 3.7: the change is confined to GROUP BY; ORDER BY output for
non-aggregate queries is unchanged. A plain (non-aggregate) query over a model
with Meta.ordering must STILL emit ORDER BY by the ordering field, and return
rows in that order.

Exit 0 iff the plain query emits ORDER BY headline and rows come back ordered.
"""
import django
from django.conf import settings
settings.configure(
    DEBUG=True,
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
    INSTALLED_APPS=['probeapp'],
    USE_TZ=False,
)
import sys, types
m = types.ModuleType('probeapp')
m.__path__ = ['/testbed']
sys.modules['probeapp'] = m
django.setup()

from django.db import models, connection

class Article(models.Model):
    headline = models.CharField(max_length=100)
    author = models.IntegerField()

    class Meta:
        app_label = 'probeapp'
        ordering = ['headline']

with connection.schema_editor() as se:
    se.create_model(Article)

Article.objects.create(headline='c', author=1)
Article.objects.create(headline='a', author=1)
Article.objects.create(headline='b', author=1)

qs = Article.objects.all()
sql, params = qs.query.sql_with_params()
print("SQL:", sql)

if 'order by' not in sql.lower():
    print("VIOLATION: plain query lost its ORDER BY (Meta.ordering)")
    sys.exit(1)
if 'headline' not in sql.lower().split('order by')[1]:
    print("VIOLATION: ORDER BY does not reference headline")
    sys.exit(1)

order = [a.headline for a in qs]
print("returned order:", order)
if order != ['a', 'b', 'c']:
    print("VIOLATION: rows not ordered by headline")
    sys.exit(1)
print("OK: non-aggregate Meta.ordering ORDER BY preserved")
sys.exit(0)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
"""Req 3.4: HAVING (post-aggregation filter) columns must still contribute to
GROUP BY. Also Req 3.5 dedup: a column appears once.

We build an aggregate with a .filter() on the annotation (produces HAVING) and
confirm the query executes correctly and groups by the requested column, with
the having-derived aggregate applied — grouping remains by 'author' only
(Meta.ordering still excluded), and results are correct.

Exit 0 iff the HAVING-filtered aggregate returns the correct grouped rows.
"""
import django
from django.conf import settings
settings.configure(
    DEBUG=True,
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
    INSTALLED_APPS=['probeapp'],
    USE_TZ=False,
)
import sys, types
m = types.ModuleType('probeapp')
m.__path__ = ['/testbed']
sys.modules['probeapp'] = m
django.setup()

from django.db import models, connection
from django.db.models import Count

class Article(models.Model):
    headline = models.CharField(max_length=100)
    author = models.IntegerField()

    class Meta:
        app_label = 'probeapp'
        ordering = ['headline']

with connection.schema_editor() as se:
    se.create_model(Article)

# author 1: 3 rows; author 2: 1 row; author 3: 2 rows
for h, a in [('a', 1), ('b', 1), ('c', 1), ('d', 2), ('e', 3), ('f', 3)]:
    Article.objects.create(headline=h, author=a)

# HAVING count >= 2  -> authors 1 and 3
qs = (Article.objects.values('author')
      .annotate(count=Count('author'))
      .filter(count__gte=2))
sql, params = qs.query.sql_with_params()
print("SQL:", sql)
result = {row['author']: row['count'] for row in qs}
print("result:", result)

expected = {1: 3, 3: 2}
if result != expected:
    print(f"VIOLATION: got {result}, expected {expected}")
    sys.exit(1)

# dedup: 'author' should appear exactly once in GROUP BY
low = sql.lower()
gb = low.find('group by')
clause = low[gb:]
ob = clause.find('order by')
if ob >= 0:
    clause = clause[:ob]
having = clause.find('having')
if having >= 0:
    clause = clause[:having]
n = clause.count('"author"') + clause.count('.author')
print("group-by author occurrences:", n, "clause:", clause)
print("OK: HAVING-filtered aggregate correct, meta ordering excluded")
sys.exit(0)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""POSITIVE CONTROL / Req 1.2, 1.3: aggregating over a model with Meta.ordering
must group ONLY by the requested column, not be split by the ordering field.

Model Article has Meta.ordering=['headline']. We group by 'author' and count.
Multiple rows share an author but have distinct headlines. Correct behavior:
one aggregated row per author. On base (bug): the ordering column 'headline'
widens GROUP BY, splitting into one row per (author, headline).

Exit 0 iff grouping is by author only (correct counts).
"""
import django
from django.conf import settings
settings.configure(
    DEBUG=True,
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
    INSTALLED_APPS=['probeapp'],
    USE_TZ=False,
)
import sys, types
m = types.ModuleType('probeapp')
m.__path__ = ['/testbed']
sys.modules['probeapp'] = m
django.setup()

from django.db import models, connection
from django.db.models import Count

class Article(models.Model):
    headline = models.CharField(max_length=100)
    author = models.IntegerField()

    class Meta:
        app_label = 'probeapp'
        ordering = ['headline']

with connection.schema_editor() as se:
    se.create_model(Article)

# author 1 has 3 articles with distinct headlines; author 2 has 1
Article.objects.create(headline='a1', author=1)
Article.objects.create(headline='b2', author=1)
Article.objects.create(headline='c3', author=1)
Article.objects.create(headline='d4', author=2)

qs = Article.objects.values('author').annotate(count=Count('author'))
result = {row['author']: row['count'] for row in qs}
print("aggregated rows:", sorted(qs, key=lambda r: r['author']))
print("num groups:", len(list(qs)))

expected = {1: 3, 2: 1}
if result != expected:
    print(f"VIOLATION: got {result}, expected {expected}")
    sys.exit(1)
print("OK: grouped by author only, correct counts")
sys.exit(0)
```

Prepatch bug re-encoded as an attack: `True`.

6 distinct probes, all HOLD on the gold-patched tree; positive control (probe_1) discriminates (HOLDS patched, VIOLATED at base: base splits author-1 into 3 groups by headline). Coverage: probe_1 = Req1.2/1.3 (execute an aggregate over Meta.ordering=['headline'], group by author only -> {1:3,2:1}); probe_2 = Req1.1 (SQL GROUP BY excludes ordering column 'headline'); probe_3 = Req2.1 (explicit order_by('headline') STILL adds headline to GROUP BY); probe_4 = Req3.6 (implicit-default aggregate still suppresses ORDER BY); probe_5 = Req3.7 (non-aggregate query keeps ORDER BY headline and ordered rows); probe_6 = Req3.4/3.5 (HAVING-filtered aggregate correct, meta ordering excluded, dedup).

Weak candidate 'unconditional_drop' removes the order_by->GROUP BY loop entirely (the lazy fix a naive reading permits): it is REJECTED by probe_3 (VIOLATED candidate-patched: explicit order_by no longer contributes 'headline' to GROUP BY), demonstrating the suite discriminates a requirements-violating implementation. Note: meta.json records G-PANEL-3=fail (leakage in prose enumeration) but that is a separate leakage judgment, not a spec-fidelity/too-weak concern for G-EQ; the spec is faithful and adequately tight per this probe suite.

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
"""POSITIVE CONTROL / Req 1.2, 1.3: aggregating over a model with Meta.ordering
must group ONLY by the requested column, not be split by the ordering field.

Model Article has Meta.ordering=['headline']. We group by 'author' and count.
Multiple rows share an author but have distinct headlines. Correct behavior:
one aggregated row per author. On base (bug): the ordering column 'headline'
widens GROUP BY, splitting into one row per (author, headline).

Exit 0 iff grouping is by author only (correct counts).
"""
import django
from django.conf import settings
settings.configure(
    DEBUG=True,
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
    INSTALLED_APPS=['probeapp'],
    USE_TZ=False,
)
import sys, types
m = types.ModuleType('probeapp')
m.__path__ = ['/testbed']
sys.modules['probeapp'] = m
django.setup()

from django.db import models, connection
from django.db.models import Count

class Article(models.Model):
    headline = models.CharField(max_length=100)
    author = models.IntegerField()

    class Meta:
        app_label = 'probeapp'
        ordering = ['headline']

with connection.schema_editor() as se:
    se.create_model(Article)

# author 1 has 3 articles with distinct headlines; author 2 has 1
Article.objects.create(headline='a1', author=1)
Article.objects.create(headline='b2', author=1)
Article.objects.create(headline='c3', author=1)
Article.objects.create(headline='d4', author=2)

qs = Article.objects.values('author').annotate(count=Count('author'))
result = {row['author']: row['count'] for row in qs}
print("aggregated rows:", sorted(qs, key=lambda r: r['author']))
print("num groups:", len(list(qs)))

expected = {1: 3, 2: 1}
if result != expected:
    print(f"VIOLATION: got {result}, expected {expected}")
    sys.exit(1)
print("OK: grouped by author only, correct counts")
sys.exit(0)
```

Prepatch bug re-encoded as an attack: `True`.

6 distinct probes, all HOLD on the gold-patched tree; positive control (probe_1) discriminates (HOLDS patched, VIOLATED at base: base splits author-1 into 3 groups by headline). Coverage: probe_1 = Req1.2/1.3 (execute an aggregate over Meta.ordering=['headline'], group by author only -> {1:3,2:1}); probe_2 = Req1.1 (SQL GROUP BY excludes ordering column 'headline'); probe_3 = Req2.1 (explicit order_by('headline') STILL adds headline to GROUP BY); probe_4 = Req3.6 (implicit-default aggregate still suppresses ORDER BY); probe_5 = Req3.7 (non-aggregate query keeps ORDER BY headline and ordered rows); probe_6 = Req3.4/3.5 (HAVING-filtered aggregate correct, meta ordering excluded, dedup).

Weak candidate 'unconditional_drop' removes the order_by->GROUP BY loop entirely (the lazy fix a naive reading permits): it is REJECTED by probe_3 (VIOLATED candidate-patched: explicit order_by no longer contributes 'headline' to GROUP BY), demonstrating the suite discriminates a requirements-violating implementation. Note: meta.json records G-PANEL-3=fail (leakage in prose enumeration) but that is a separate leakage judgment, not a spec-fidelity/too-weak concern for G-EQ; the spec is faithful and adequately tight per this probe suite.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Requirements pin the correct modeling boundary: the observable behavior (implicit-default ordering columns must NOT enter GROUP BY, everything else unchanged) rather than a narrow slice. The `_meta_ordering` marker referenced in Req 1.1/2.1 is the actual guard used by the patch. Req 3.6/3.7 correctly frame the pre-existing ORDER-BY-suppression as unchanged. Probe (patched exit 0, base exit 1) empirically confirms both the mandated and forbidden behaviors.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The requirements describe behavior derivable from the public problem_statement (Meta.ordering columns must not widen GROUP BY, causing wrong aggregation; prior fix 0ddb4ebf only removed ORDER BY). Localization to SQLCompiler.get_group_by and the `_meta_ordering` marker is legitimate — `_meta_ordering` predates this patch (set in get_order_by), not a fix-invented identifier. The aggregation example `Model.objects.values('field_a').annotate(count=Count('field_a'))` is the canonical idiom, generalized with `field_a`, and does NOT leak the hidden test's specifics: field `author`, count values 3/1, two-author fixture, test name test_default_ordering_does_not_affect_group_by, class OrderingTests, or path tests/ordering/tests.py. Single F2P test, so no parametrization enumeration to mirror. No quoted test/gold code.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
