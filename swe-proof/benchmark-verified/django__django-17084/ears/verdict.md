# P2 adversarial audit — django__django-17084

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 5 requirement probes hold on the patched tree; 2/2 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 5 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 5 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 2 alternative candidate patches, claimed to satisfy every cited requirement, and ran the same suite against them. The suite rejected all 2: a probe encoding a cited requirement fails under each of those, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (5):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
"""Positive control — Requirement 1 (criteria 1,2,3) + FAIL_TO_PASS core.

Aggregate (Sum) over a Window annotation must:
  - succeed and return the correct value (crit 3),
  - be evaluated inside a wrapping subquery: the generated SQL has TWO
    SELECTs (crit 1,2 — aggregate applied over inner window column, not
    nested around the OVER expression),
  - use exactly ONE query.
On the BASE tree this raises (window nested in aggregate) or produces a
single-level SELECT — so this FAILS at base and HOLDS when patched.
"""
import django
from django.conf import settings

settings.configure(
    DEBUG=True,
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3",
                           "NAME": ":memory:"}},
    INSTALLED_APPS=["django.contrib.contenttypes"],
    USE_TZ=False,
)
django.setup()

from django.db import connection, models
from django.db.models import Sum, Count, Avg, F, Window
from django.db.models.functions import Coalesce


class Publisher(models.Model):
    name = models.CharField(max_length=50)
    class Meta:
        app_label = "contenttypes"


class Book(models.Model):
    pages = models.IntegerField()
    publisher = models.ForeignKey(Publisher, on_delete=models.CASCADE)
    class Meta:
        app_label = "contenttypes"


if not connection.features.supports_over_clause:
    print("SKIP-ish: backend has no window support; treating as N/A -> hold")
    raise SystemExit(0)

with connection.schema_editor() as se:
    se.create_model(Publisher)
    se.create_model(Book)

p1 = Publisher.objects.create(name="A")
p2 = Publisher.objects.create(name="B")
Book.objects.create(pages=100, publisher=p1)
Book.objects.create(pages=300, publisher=p1)
Book.objects.create(pages=700, publisher=p2)

qs = Book.objects.annotate(
    avg_pub_pages=Coalesce(Window(Avg("pages"), partition_by=F("publisher")), 0.0)
)

from django.test.utils import CaptureQueriesContext
with CaptureQueriesContext(connection) as ctx:
    result = qs.aggregate(
        sum_avg=Sum("avg_pub_pages"),
        books_count=Count("id"),
    )

print("result =", result)
n_queries = len(ctx.captured_queries)
sql = ctx.captured_queries[0]["sql"].lower()
n_select = sql.count("select")
print("n_queries =", n_queries, "n_select =", n_select)
print("sql =", sql)

# Expected: p1 partition avg = 200 (two books), p2 = 700 (one book).
# Sum over rows = 200+200+700 = 1100.0 ; books_count = 3
ok = True
if n_queries != 1:
    print("FAIL: expected exactly 1 query, got", n_queries); ok = False
if n_select < 2:
    print("FAIL: expected wrapping subquery (>=2 SELECTs), got", n_select); ok = False
if result != {"sum_avg": 1100.0, "books_count": 3}:
    print("FAIL: wrong aggregate result", result); ok = False
print("POSITIVE CONTROL", "HOLD" if ok else "VIOLATED")
raise SystemExit(0 if ok else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
import django
from django.conf import settings
settings.configure(
    DEBUG=True,
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    INSTALLED_APPS=["django.contrib.contenttypes"],
    USE_TZ=False,
)
django.setup()
from django.db import connection, models
from django.db.models import Sum, Count, Avg, F, Window, OuterRef, Subquery
from django.db.models.functions import Coalesce
from django.test.utils import CaptureQueriesContext

class Publisher(models.Model):
    name = models.CharField(max_length=50)
    class Meta:
        app_label = "contenttypes"

class Book(models.Model):
    pages = models.IntegerField()
    publisher = models.ForeignKey(Publisher, on_delete=models.CASCADE)
    class Meta:
        app_label = "contenttypes"

with connection.schema_editor() as se:
    se.create_model(Publisher)
    se.create_model(Book)

p1 = Publisher.objects.create(name="A")
p2 = Publisher.objects.create(name="B")
Book.objects.create(pages=100, publisher=p1)
Book.objects.create(pages=300, publisher=p1)
Book.objects.create(pages=700, publisher=p2)

# Requirement 2 crit 2,3 & Requirement 3 crit 4:
# An aggregate referencing a NON-window annotation must NOT introduce a
# wrapping subquery -> single-level query (exactly one SELECT).
qs = Book.objects.annotate(dbl=F("pages") * 2)
with CaptureQueriesContext(connection) as ctx:
    result = qs.aggregate(total=Sum("dbl"))
sql = ctx.captured_queries[0]["sql"].lower()
n_select = sql.count("select")
print("result =", result, "n_select =", n_select)
print("sql =", sql)
# 100*2+300*2+700*2 = 2200
ok = True
if n_select != 1:
    print("FAIL: non-window aggregate should NOT wrap; got", n_select, "SELECTs"); ok = False
if result != {"total": 2200}:
    print("FAIL: wrong value", result); ok = False
print("REQ2-noregress", "HOLD" if ok else "VIOLATED")
raise SystemExit(0 if ok else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
import django
from django.conf import settings
settings.configure(
    DEBUG=True,
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    INSTALLED_APPS=["django.contrib.contenttypes"],
    USE_TZ=False,
)
django.setup()
from django.db import connection, models
from django.db.models import Sum, Count, Avg, F, Window, OuterRef, Subquery
from django.db.models.functions import Coalesce
from django.test.utils import CaptureQueriesContext

class Publisher(models.Model):
    name = models.CharField(max_length=50)
    class Meta:
        app_label = "contenttypes"

class Book(models.Model):
    pages = models.IntegerField()
    publisher = models.ForeignKey(Publisher, on_delete=models.CASCADE)
    class Meta:
        app_label = "contenttypes"

with connection.schema_editor() as se:
    se.create_model(Publisher)
    se.create_model(Book)

p1 = Publisher.objects.create(name="A")
p2 = Publisher.objects.create(name="B")
Book.objects.create(pages=100, publisher=p1)
Book.objects.create(pages=300, publisher=p1)
Book.objects.create(pages=700, publisher=p2)

# Requirement 3 crit 1: aggregate referencing a SUBQUERY annotation must
# continue to wrap (>=2 SELECT, exactly one query). Pre-existing behavior.
sub = Book.objects.filter(publisher=OuterRef("pk")).order_by().values("publisher").annotate(c=Count("*")).values("c")
qs = Publisher.objects.annotate(nbooks=Subquery(sub))
with CaptureQueriesContext(connection) as ctx:
    result = qs.aggregate(total=Sum("nbooks"))
sql = ctx.captured_queries[0]["sql"].lower()
n_select = sql.count("select")
print("result =", result, "n_select =", n_select)
print("sql =", sql)
# p1 has 2 books, p2 has 1 -> sum = 3
ok = True
if n_select < 2:
    print("FAIL: subquery-referenced aggregate must wrap; got", n_select); ok = False
if result != {"total": 3}:
    print("FAIL: wrong value", result); ok = False
print("REQ3-subquery-wrap", "HOLD" if ok else "VIOLATED")
raise SystemExit(0 if ok else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
import django
from django.conf import settings
settings.configure(
    DEBUG=True,
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    INSTALLED_APPS=["django.contrib.contenttypes"],
    USE_TZ=False,
)
django.setup()
from django.db import connection, models
from django.db.models import Sum, Count, Avg, F, Window, OuterRef, Subquery
from django.db.models.functions import Coalesce
from django.test.utils import CaptureQueriesContext

class Publisher(models.Model):
    name = models.CharField(max_length=50)
    class Meta:
        app_label = "contenttypes"

class Book(models.Model):
    pages = models.IntegerField()
    publisher = models.ForeignKey(Publisher, on_delete=models.CASCADE)
    class Meta:
        app_label = "contenttypes"

with connection.schema_editor() as se:
    se.create_model(Publisher)
    se.create_model(Book)

p1 = Publisher.objects.create(name="A")
p2 = Publisher.objects.create(name="B")
Book.objects.create(pages=100, publisher=p1)
Book.objects.create(pages=300, publisher=p1)
Book.objects.create(pages=700, publisher=p2)

# Requirement 3 crit 2 & 3: annotation pruning preserved.
# An UNREFERENCED annotation must NOT appear in emitted SQL; a REFERENCED
# annotation must appear. Use a window annotation that is NOT referenced by
# the aggregate -> it should be pruned (and thus no wrapping forced by it).
qs = Book.objects.annotate(
    win_unref=Coalesce(Window(Avg("pages"), partition_by=F("publisher")), 0.0),
    dbl=F("pages") * 2,
)
with CaptureQueriesContext(connection) as ctx:
    result = qs.aggregate(total=Sum("dbl"))
sql = ctx.captured_queries[0]["sql"].lower()
print("result =", result)
print("sql =", sql)
ok = True
# Unreferenced window annotation pruned -> no OVER clause, no partition, single SELECT.
if "over" in sql or "partition" in sql:
    print("FAIL: unreferenced window annotation not pruned"); ok = False
if sql.count("select") != 1:
    print("FAIL: pruned-away window should not force wrapping; SELECTs =", sql.count("select")); ok = False
# referenced 'dbl' must appear (pages*2)
if "* 2" not in sql and "*2" not in sql:
    print("FAIL: referenced annotation missing from SQL"); ok = False
if result != {"total": 2200}:
    print("FAIL: wrong value", result); ok = False
print("REQ3-pruning", "HOLD" if ok else "VIOLATED")
raise SystemExit(0 if ok else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
import django
from django.conf import settings
settings.configure(
    DEBUG=True,
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    INSTALLED_APPS=["django.contrib.contenttypes"],
    USE_TZ=False,
)
django.setup()
from django.db import connection, models
from django.db.models import Sum, Count, Avg, F, Window, OuterRef, Subquery
from django.db.models.functions import Coalesce
from django.test.utils import CaptureQueriesContext

class Publisher(models.Model):
    name = models.CharField(max_length=50)
    class Meta:
        app_label = "contenttypes"

class Book(models.Model):
    pages = models.IntegerField()
    publisher = models.ForeignKey(Publisher, on_delete=models.CASCADE)
    class Meta:
        app_label = "contenttypes"

with connection.schema_editor() as se:
    se.create_model(Publisher)
    se.create_model(Book)

p1 = Publisher.objects.create(name="A")
p2 = Publisher.objects.create(name="B")
Book.objects.create(pages=100, publisher=p1)
Book.objects.create(pages=300, publisher=p1)
Book.objects.create(pages=700, publisher=p2)

# Requirement 1 crit 4 & 5: a BARE (not Coalesce-wrapped) Window annotation
# still triggers wrapping (contains_over_clause via get_refs), and a plain
# Count requested alongside it is produced together in ONE result mapping via
# ONE query. Distinct from probe_1 (which wraps the window in Coalesce).
qs = Book.objects.annotate(w=Window(Avg("pages"), partition_by=F("publisher")))
with CaptureQueriesContext(connection) as ctx:
    result = qs.aggregate(sw=Sum("w"), n=Count("id"))
sql = ctx.captured_queries[0]["sql"].lower()
n_queries = len(ctx.captured_queries)
n_select = sql.count("select")
print("result =", result, "n_queries =", n_queries, "n_select =", n_select)
print("sql =", sql)
ok = True
if n_queries != 1:
    print("FAIL: expected 1 query, got", n_queries); ok = False
if n_select < 2:
    print("FAIL: bare-window aggregate must wrap; SELECTs =", n_select); ok = False
if set(result) != {"sw", "n"}:
    print("FAIL: both aggregates not in one mapping", result); ok = False
# p1 avg=200 (x2 rows), p2 avg=700 -> sum=1100.0 ; count=3
if result.get("sw") != 1100.0 or result.get("n") != 3:
    print("FAIL: wrong combined values", result); ok = False
# aggregate must NOT be nested directly around OVER: the outer sum wraps a
# column, not the window expression. Inner SELECT has the OVER; the string
# "sum(avg(" would indicate nesting.
if "sum(avg(" in sql.replace(" ", ""):
    print("FAIL: aggregate nested directly around window"); ok = False
print("REQ1-bare-window-combined", "HOLD" if ok else "VIOLATED")
raise SystemExit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Positive control — Requirement 1 (criteria 1,2,3) + FAIL_TO_PASS core.

Aggregate (Sum) over a Window annotation must:
  - succeed and return the correct value (crit 3),
  - be evaluated inside a wrapping subquery: the generated SQL has TWO
    SELECTs (crit 1,2 — aggregate applied over inner window column, not
    nested around the OVER expression),
  - use exactly ONE query.
On the BASE tree this raises (window nested in aggregate) or produces a
single-level SELECT — so this FAILS at base and HOLDS when patched.
"""
import django
from django.conf import settings

settings.configure(
    DEBUG=True,
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3",
                           "NAME": ":memory:"}},
    INSTALLED_APPS=["django.contrib.contenttypes"],
    USE_TZ=False,
)
django.setup()

from django.db import connection, models
from django.db.models import Sum, Count, Avg, F, Window
from django.db.models.functions import Coalesce


class Publisher(models.Model):
    name = models.CharField(max_length=50)
    class Meta:
        app_label = "contenttypes"


class Book(models.Model):
    pages = models.IntegerField()
    publisher = models.ForeignKey(Publisher, on_delete=models.CASCADE)
    class Meta:
        app_label = "contenttypes"


if not connection.features.supports_over_clause:
    print("SKIP-ish: backend has no window support; treating as N/A -> hold")
    raise SystemExit(0)

with connection.schema_editor() as se:
    se.create_model(Publisher)
    se.create_model(Book)

p1 = Publisher.objects.create(name="A")
p2 = Publisher.objects.create(name="B")
Book.objects.create(pages=100, publisher=p1)
Book.objects.create(pages=300, publisher=p1)
Book.objects.create(pages=700, publisher=p2)

qs = Book.objects.annotate(
    avg_pub_pages=Coalesce(Window(Avg("pages"), partition_by=F("publisher")), 0.0)
)

from django.test.utils import CaptureQueriesContext
with CaptureQueriesContext(connection) as ctx:
    result = qs.aggregate(
        sum_avg=Sum("avg_pub_pages"),
        books_count=Count("id"),
    )

print("result =", result)
n_queries = len(ctx.captured_queries)
sql = ctx.captured_queries[0]["sql"].lower()
n_select = sql.count("select")
print("n_queries =", n_queries, "n_select =", n_select)
print("sql =", sql)

# Expected: p1 partition avg = 200 (two books), p2 = 700 (one book).
# Sum over rows = 200+200+700 = 1100.0 ; books_count = 3
ok = True
if n_queries != 1:
    print("FAIL: expected exactly 1 query, got", n_queries); ok = False
if n_select < 2:
    print("FAIL: expected wrapping subquery (>=2 SELECTs), got", n_select); ok = False
if result != {"sum_avg": 1100.0, "books_count": 3}:
    print("FAIL: wrong aggregate result", result); ok = False
print("POSITIVE CONTROL", "HOLD" if ok else "VIOLATED")
raise SystemExit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Requirements faithfully describe the gold patch (add refs_window OR-term in Query.get_aggregation, detecting refs whose annotation contains_over_clause). 5 probes all HOLD on the gold-patched tree:
- probe_1 (POSITIVE CONTROL, Req1 c1/c2/c3): Sum over Coalesce(Window(...)) annotation -> exactly 1 query, 2 SELECTs (aggregate over inner window column, not nested), result {'sum_avg':1100.0,'books_count':3}. HOLDS patched; at --base raises OperationalError 'misuse of window function AVG()' -> VIOLATED at base (discriminates).
- probe_2 (Req2 c2/c3, Req3 c4): plain non-window aggregate stays single-level (1 SELECT), value 2200. HOLDS.
- probe_3 (Req3 c1): Subquery-referenced aggregate keeps wrapping (>=2 SELECT), value 3. HOLDS.
- probe_4 (Req3 c2/c3): unreferenced Window annotation pruned (no OVER/partition, 1 SELECT), referenced annotation retained. HOLDS.
- probe_5 (Req1 c4/c5): bare Window annotation triggers wrapping; Sum + Count returned together in ONE query/mapping (1100.0, 3); aggregate not nested around OVER. HOLDS.

Candidate wrong patches, both REJECTED by the suite (proves discrimination):
- weak_alwayswrap.diff (refs_window=True unconditionally, the lazy always-wrap fix): REJECTED by probe_2 and probe_4 (introduces a redundant subquery layer for non-window aggregates and defeats pruning -> violates Req2 c3 / Req3). probes 1,3,5 still pass.
- weak_isinstance.diff (detect only isinstance Window via __class__.__name__=='Window', ignoring Coalesce(Window) wrapper): REJECTED by probe_1 (the hidden test / Req1 c4 boundary: window wrapped in Coalesce is not detected, so aggregate stays nested and the DB errors). probes 2,3,4,5 pass.

No requirements-conforming alternative found that also fails the hidden tests. Verdict SOUND: >=5 distinct probes cover Req1 (c1-c5), Req2 (c2,c3), Req3 (c1-c4); positive control discriminates patched-vs-base; suite rejects >=1 wrong candidate (rejects 2).

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 5 requirement probes hold on the patched tree; 2/2 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 5 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 5 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 2 alternative candidate patches, claimed to satisfy every cited requirement, and ran the same suite against them. The suite rejected all 2: a probe encoding a cited requirement fails under each of those, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (5):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

_The 5 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts, and on this backend both roles put it through the same derivation: every block below is a requirement probe run on the gold-patched tree, and the `machine verdict:` line each role publishes above reports BOTH that its probes hold there and how many candidate patches the probe suite rejected — so the two roles re-ran ONE probe suite and each recorded its own outcome for every probe in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `probe_1.py` → holds on the patched tree (good)

Attack 2 — `probe_2.py` → holds on the patched tree (good)

Attack 3 — `probe_3.py` → holds on the patched tree (good)

Attack 4 — `probe_4.py` → holds on the patched tree (good)

Attack 5 — `probe_5.py` → holds on the patched tree (good)

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Positive control — Requirement 1 (criteria 1,2,3) + FAIL_TO_PASS core.

Aggregate (Sum) over a Window annotation must:
  - succeed and return the correct value (crit 3),
  - be evaluated inside a wrapping subquery: the generated SQL has TWO
    SELECTs (crit 1,2 — aggregate applied over inner window column, not
    nested around the OVER expression),
  - use exactly ONE query.
On the BASE tree this raises (window nested in aggregate) or produces a
single-level SELECT — so this FAILS at base and HOLDS when patched.
"""
import django
from django.conf import settings

settings.configure(
    DEBUG=True,
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3",
                           "NAME": ":memory:"}},
    INSTALLED_APPS=["django.contrib.contenttypes"],
    USE_TZ=False,
)
django.setup()

from django.db import connection, models
from django.db.models import Sum, Count, Avg, F, Window
from django.db.models.functions import Coalesce


class Publisher(models.Model):
    name = models.CharField(max_length=50)
    class Meta:
        app_label = "contenttypes"


class Book(models.Model):
    pages = models.IntegerField()
    publisher = models.ForeignKey(Publisher, on_delete=models.CASCADE)
    class Meta:
        app_label = "contenttypes"


if not connection.features.supports_over_clause:
    print("SKIP-ish: backend has no window support; treating as N/A -> hold")
    raise SystemExit(0)

with connection.schema_editor() as se:
    se.create_model(Publisher)
    se.create_model(Book)

p1 = Publisher.objects.create(name="A")
p2 = Publisher.objects.create(name="B")
Book.objects.create(pages=100, publisher=p1)
Book.objects.create(pages=300, publisher=p1)
Book.objects.create(pages=700, publisher=p2)

qs = Book.objects.annotate(
    avg_pub_pages=Coalesce(Window(Avg("pages"), partition_by=F("publisher")), 0.0)
)

from django.test.utils import CaptureQueriesContext
with CaptureQueriesContext(connection) as ctx:
    result = qs.aggregate(
        sum_avg=Sum("avg_pub_pages"),
        books_count=Count("id"),
    )

print("result =", result)
n_queries = len(ctx.captured_queries)
sql = ctx.captured_queries[0]["sql"].lower()
n_select = sql.count("select")
print("n_queries =", n_queries, "n_select =", n_select)
print("sql =", sql)

# Expected: p1 partition avg = 200 (two books), p2 = 700 (one book).
# Sum over rows = 200+200+700 = 1100.0 ; books_count = 3
ok = True
if n_queries != 1:
    print("FAIL: expected exactly 1 query, got", n_queries); ok = False
if n_select < 2:
    print("FAIL: expected wrapping subquery (>=2 SELECTs), got", n_select); ok = False
if result != {"sum_avg": 1100.0, "books_count": 3}:
    print("FAIL: wrong aggregate result", result); ok = False
print("POSITIVE CONTROL", "HOLD" if ok else "VIOLATED")
raise SystemExit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Requirements faithfully describe the gold patch (add refs_window OR-term in Query.get_aggregation, detecting refs whose annotation contains_over_clause). 5 probes all HOLD on the gold-patched tree:
- probe_1 (POSITIVE CONTROL, Req1 c1/c2/c3): Sum over Coalesce(Window(...)) annotation -> exactly 1 query, 2 SELECTs (aggregate over inner window column, not nested), result {'sum_avg':1100.0,'books_count':3}. HOLDS patched; at --base raises OperationalError 'misuse of window function AVG()' -> VIOLATED at base (discriminates).
- probe_2 (Req2 c2/c3, Req3 c4): plain non-window aggregate stays single-level (1 SELECT), value 2200. HOLDS.
- probe_3 (Req3 c1): Subquery-referenced aggregate keeps wrapping (>=2 SELECT), value 3. HOLDS.
- probe_4 (Req3 c2/c3): unreferenced Window annotation pruned (no OVER/partition, 1 SELECT), referenced annotation retained. HOLDS.
- probe_5 (Req1 c4/c5): bare Window annotation triggers wrapping; Sum + Count returned together in ONE query/mapping (1100.0, 3); aggregate not nested around OVER. HOLDS.

Candidate wrong patches, both REJECTED by the suite (proves discrimination):
- weak_alwayswrap.diff (refs_window=True unconditionally, the lazy always-wrap fix): REJECTED by probe_2 and probe_4 (introduces a redundant subquery layer for non-window aggregates and defeats pruning -> violates Req2 c3 / Req3). probes 1,3,5 still pass.
- weak_isinstance.diff (detect only isinstance Window via __class__.__name__=='Window', ignoring Coalesce(Window) wrapper): REJECTED by probe_1 (the hidden test / Req1 c4 boundary: window wrapped in Coalesce is not detected, so aggregate stays nested and the DB errors). probes 2,3,4,5 pass.

No requirements-conforming alternative found that also fails the hidden tests. Verdict SOUND: >=5 distinct probes cover Req1 (c1-c5), Req2 (c2,c3), Req3 (c1-c4); positive control discriminates patched-vs-base; suite rejects >=1 wrong candidate (rejects 2).

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Patch is a 2-line addition: `refs_window` flag set in the aggregate-resolution loop and OR'd into the inner_query_must_be_used condition alongside grouped/is_sliced/has_existing_aggregation/refs_subquery/qualify/distinct/combinator. Requirement 2.1 enumerates precisely this OR set including 'a referenced annotation is a window annotation'. Requirement 3 (pruning/subquery preservation) untouched by the patch and unchanged. Minor: the getattr default is True (not False) — an annotation lacking contains_over_clause would be treated as a window annotation; the requirements phrase it as 'reports that it contains an OVER clause', but all real Django expressions define contains_over_clause, so no observable divergence exists and this does not rise to unfaithfulness.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The gold patch adds a `refs_window` flag to Query.get_aggregation() that ORs `getattr(annotation, 'contains_over_clause', True)` into the existing wrapping decision (query.py). The hidden test (test_referenced_window_requires_wrapping) annotates Book with Coalesce(Window(Avg('pages'), partition_by=F('publisher')), 0.0), aggregates Sum + Count('id'), and asserts assertNumQueries(1)/sql.count('select')==2/result {'sum_avg_publisher_pages':1100.0,'books_count':2}.

Checked all leak categories: (1) No test names/paths/class names/ids present. (2) No test-specific literals leak: Book, 'pages', 'publisher', partition_by, 1100.0, books_count, the select-count '2', assertNumQueries — none appear. (3) The identifiers named in the doc (Query.get_aggregation, query.py, contains_over_clause, Coalesce(Window(...))) are all either legitimate localization of the changed method or already present in the PUBLIC problem_statement (which itself gives the Coalesce(Window(Sum('DJR'),...)) example and the PostgreSQL grouping error). contains_over_clause is a pre-existing Django API property, not a fix-invented identifier; the gold's local var name refs_window is NOT disclosed. (4) The OR-enumeration in Req 2.1 (grouped-by/sliced/existing-aggregation/subquery/qualify/distinct/combinator) reproduces the surrounding source-code condition being modified — legitimate localization of public code, not the hidden test.

Borderline: Req 1 criterion 5 describes a non-window aggregate (plain Count) requested alongside a window-referencing aggregate, mirroring the test's Sum+Count('id') dual-aggregate shape (the problem statement instead pairs two Sums). But this is a generic behavioral description (heterogeneous aggregates computed in one wrapping execution) — it does not reconstruct the test (no Book model, no partition_by, no gold values, no select-count assertion). This is translation of behavior into requirements, which is the intended function, not transmission of the tests. NO-LEAKAGE.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
