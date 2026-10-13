# P2 adversarial audit — django__django-16263

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
"""Req 1.1 + 2.1 (POSITIVE CONTROL): annotate a non-aggregate expression
(Lower) then count() -> emitted SQL must be a single flat SELECT and the
annotation alias must be absent. Fails at base (old code wraps + emits it)."""
import sys
import django
from django.conf import settings

settings.configure(
    DEBUG=True,
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
    USE_TZ=False,
)
django.setup()

from django.db import models, connection
from django.db.models import Count
from django.db.models.functions import Lower
from django.test.utils import CaptureQueriesContext


class Book(models.Model):
    name = models.CharField(max_length=100)
    class Meta:
        app_label = "contenttypes"


with connection.schema_editor() as se:
    se.create_model(Book)

with CaptureQueriesContext(connection) as ctx:
    Book.objects.annotate(name_lower=Lower("name")).count()
sql = ctx.captured_queries[0]["sql"].lower()
print("SQL:", sql)
n_select = sql.count("select")
has_alias = "name_lower" in sql
print("select_count=%d name_lower_present=%s" % (n_select, has_alias))
ok = (n_select == 1) and (not has_alias)
sys.exit(0 if ok else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""Req 1.2 + 2.1: an UNSELECTED alias(...) that is an aggregate over a
multi-valued relation, then count() -> no subquery (single SELECT) and alias
absent. (Book.alias(authors_count=Count('authors')).count())"""
import sys
import django
from django.conf import settings

settings.configure(
    DEBUG=True,
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
    USE_TZ=False,
)
django.setup()

from django.db import models, connection
from django.db.models import Count
from django.test.utils import CaptureQueriesContext


class Author(models.Model):
    name = models.CharField(max_length=100)
    class Meta:
        app_label = "contenttypes"


class Book(models.Model):
    name = models.CharField(max_length=100)
    authors = models.ManyToManyField(Author)
    class Meta:
        app_label = "contenttypes"


with connection.schema_editor() as se:
    se.create_model(Author)
    se.create_model(Book)

with CaptureQueriesContext(connection) as ctx:
    Book.objects.alias(authors_count=Count("authors")).count()
sql = ctx.captured_queries[0]["sql"].lower()
print("SQL:", sql)
n_select = sql.count("select")
has_alias = "authors_count" in sql
print("select_count=%d authors_count_present=%s" % (n_select, has_alias))
ok = (n_select == 1) and (not has_alias)
sys.exit(0 if ok else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""Req 2.2 + 2.3: a SELECTED existing aggregate that no requested aggregate
references -> a subquery IS used (2 SELECTs) but the unreferenced aggregate
alias is OMITTED from the emitted SQL.
(Book.annotate(authors_count=Count('authors')).count())"""
import sys
import django
from django.conf import settings

settings.configure(
    DEBUG=True,
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
    USE_TZ=False,
)
django.setup()

from django.db import models, connection
from django.db.models import Count
from django.test.utils import CaptureQueriesContext


class Author(models.Model):
    name = models.CharField(max_length=100)
    class Meta:
        app_label = "contenttypes"


class Book(models.Model):
    name = models.CharField(max_length=100)
    authors = models.ManyToManyField(Author)
    class Meta:
        app_label = "contenttypes"


with connection.schema_editor() as se:
    se.create_model(Author)
    se.create_model(Book)

with CaptureQueriesContext(connection) as ctx:
    Book.objects.annotate(authors_count=Count("authors")).count()
sql = ctx.captured_queries[0]["sql"].lower()
print("SQL:", sql)
n_select = sql.count("select")
has_alias = "authors_count" in sql
print("select_count=%d authors_count_present=%s" % (n_select, has_alias))
ok = (n_select == 2) and (not has_alias)
sys.exit(0 if ok else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""Req 3.1 + 3.2: a requested aggregate that REFERENCES an existing annotation
-> subquery used (2 SELECTs) AND the referenced alias appears twice (defined in
inner query + referred to by outer aggregate).
(Book.annotate(authors_count=Count('authors')).aggregate(Avg('authors_count')))"""
import sys
import django
from django.conf import settings

settings.configure(
    DEBUG=True,
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
    USE_TZ=False,
)
django.setup()

from django.db import models, connection
from django.db.models import Count, Avg
from django.test.utils import CaptureQueriesContext


class Author(models.Model):
    name = models.CharField(max_length=100)
    class Meta:
        app_label = "contenttypes"


class Book(models.Model):
    name = models.CharField(max_length=100)
    authors = models.ManyToManyField(Author)
    class Meta:
        app_label = "contenttypes"


with connection.schema_editor() as se:
    se.create_model(Author)
    se.create_model(Book)

with CaptureQueriesContext(connection) as ctx:
    Book.objects.annotate(authors_count=Count("authors")).aggregate(Avg("authors_count"))
sql = ctx.captured_queries[0]["sql"].lower()
print("SQL:", sql)
n_select = sql.count("select")
n_alias = sql.count("authors_count")
print("select_count=%d authors_count_count=%d" % (n_select, n_alias))
ok = (n_select == 2) and (n_alias == 2)
sys.exit(0 if ok else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""Req 4.1: numeric correctness — pruning a selected non-aggregate expression
must not change the count value: Book.annotate(name_lower=Lower('name')).count()
equals Book.objects.count(). Also the referenced-aggregate case (Req 4.1) must
compute the correct Avg."""
import sys
import django
from django.conf import settings

settings.configure(
    DEBUG=True,
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
    USE_TZ=False,
)
django.setup()

from django.db import models, connection
from django.db.models import Count, Avg
from django.db.models.functions import Lower


class Author(models.Model):
    name = models.CharField(max_length=100)
    class Meta:
        app_label = "contenttypes"


class Book(models.Model):
    name = models.CharField(max_length=100)
    authors = models.ManyToManyField(Author)
    class Meta:
        app_label = "contenttypes"


with connection.schema_editor() as se:
    se.create_model(Author)
    se.create_model(Book)

a1 = Author.objects.create(name="a1")
a2 = Author.objects.create(name="a2")
b1 = Book.objects.create(name="b1")
b2 = Book.objects.create(name="b2")
b3 = Book.objects.create(name="b3")
b1.authors.add(a1, a2)
b2.authors.add(a1)
# b3 has no authors

plain = Book.objects.count()
with_lower = Book.objects.annotate(name_lower=Lower("name")).count()
print("plain=%d with_lower=%d" % (plain, with_lower))

# referenced-aggregate numeric correctness: avg of per-book author counts
# counts among books (Count('authors') per book): b1=2, b2=1, b3=0 -> avg=1.0
avg = Book.objects.annotate(authors_count=Count("authors")).aggregate(a=Avg("authors_count"))["a"]
print("avg_authors_count=%r" % (avg,))

ok = (plain == 3) and (with_lower == 3) and (abs(avg - 1.0) < 1e-9)
sys.exit(0 if ok else 1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
"""Req 4.2: dropping an UNSELECTED aliased aggregate over a multi-valued
relation collapses to a flat query over the retained join, so count() reflects
joined-row cardinality (> base-table count). With b1 having 2 authors, b2 1,
b3 0, the joined count = 2+1 = 3 (rows with a matching author), which differs
from base count 3... use a setup that makes them differ.
b1:2 authors, b2:2 authors -> joined=4, base=2."""
import sys
import django
from django.conf import settings

settings.configure(
    DEBUG=True,
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
    USE_TZ=False,
)
django.setup()

from django.db import models, connection
from django.db.models import Count


class Author(models.Model):
    name = models.CharField(max_length=100)
    class Meta:
        app_label = "contenttypes"


class Book(models.Model):
    name = models.CharField(max_length=100)
    authors = models.ManyToManyField(Author)
    class Meta:
        app_label = "contenttypes"


with connection.schema_editor() as se:
    se.create_model(Author)
    se.create_model(Book)

a1 = Author.objects.create(name="a1")
a2 = Author.objects.create(name="a2")
b1 = Book.objects.create(name="b1")
b2 = Book.objects.create(name="b2")
b1.authors.add(a1, a2)
b2.authors.add(a1, a2)

base = Book.objects.count()  # 2
joined = Book.objects.alias(authors_count=Count("authors")).count()
print("base=%d aliased_count=%d" % (base, joined))
# Per Req 4.2, the flat query counts joined rows = 4, exceeding base 2.
ok = (base == 2) and (joined == 4)
sys.exit(0 if ok else 1)
```

Attack 7 — `probe_7.py` → holds on the patched tree (good)

```python
"""Req 3.3 + 4.3: distinct forces a subquery AND retains every selected clause
(no pruning). Book.annotate(name_lower=Lower('name')).distinct().count()
-> subquery used (2 SELECTs) and name_lower alias PRESENT (not pruned)."""
import sys
import django
from django.conf import settings

settings.configure(
    DEBUG=True,
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
    USE_TZ=False,
)
django.setup()

from django.db import models, connection
from django.db.models.functions import Lower
from django.test.utils import CaptureQueriesContext


class Book(models.Model):
    name = models.CharField(max_length=100)
    class Meta:
        app_label = "contenttypes"


with connection.schema_editor() as se:
    se.create_model(Book)

with CaptureQueriesContext(connection) as ctx:
    Book.objects.annotate(name_lower=Lower("name")).distinct().count()
sql = ctx.captured_queries[0]["sql"].lower()
print("SQL:", sql)
n_select = sql.count("select")
has_alias = "name_lower" in sql
print("select_count=%d name_lower_present=%s" % (n_select, has_alias))
ok = (n_select == 2) and has_alias
sys.exit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Req 1.1 + 2.1 (POSITIVE CONTROL): annotate a non-aggregate expression
(Lower) then count() -> emitted SQL must be a single flat SELECT and the
annotation alias must be absent. Fails at base (old code wraps + emits it)."""
import sys
import django
from django.conf import settings

settings.configure(
    DEBUG=True,
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
    USE_TZ=False,
)
django.setup()

from django.db import models, connection
from django.db.models import Count
from django.db.models.functions import Lower
from django.test.utils import CaptureQueriesContext


class Book(models.Model):
    name = models.CharField(max_length=100)
    class Meta:
        app_label = "contenttypes"


with connection.schema_editor() as se:
    se.create_model(Book)

with CaptureQueriesContext(connection) as ctx:
    Book.objects.annotate(name_lower=Lower("name")).count()
sql = ctx.captured_queries[0]["sql"].lower()
print("SQL:", sql)
n_select = sql.count("select")
has_alias = "name_lower" in sql
print("select_count=%d name_lower_present=%s" % (n_select, has_alias))
ok = (n_select == 1) and (not has_alias)
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Bundle django__django-16263: get_aggregation prunes unused annotations/aliases from count()/aggregate() SQL.

Probes (all HOLD on gold-patched tree):
- probe_1 (Req1.1/2.1, POSITIVE CONTROL): annotate(name_lower=Lower('name')).count() -> single SELECT, alias absent. HOLDS patched, VIOLATED at base (base wraps in subquery emitting name_lower). Discriminates.
- probe_2 (Req1.2/2.1): alias(authors_count=Count('authors')).count() -> single SELECT, alias absent. HOLDS patched, VIOLATED at base.
- probe_3 (Req2.2/2.3): annotate(authors_count=Count('authors')).count() -> subquery used (2 SELECT) but unreferenced aggregate alias omitted. HOLDS patched, VIOLATED at base (base emits authors_count).
- probe_4 (Req3.1/3.2): annotate(authors_count=Count('authors')).aggregate(Avg('authors_count')) -> subquery + alias appears twice (defined+referenced). HOLDS patched (also holds at base, not discriminating for wrapping but pins the retain-referenced criterion).
- probe_5 (Req4.1): numeric correctness — count with pruned Lower == plain count (3==3); Avg of per-book author counts == 1.0. HOLDS.
- probe_6 (Req4.2): alias(Count('authors')).count() over multi-valued relation collapses to flat join, counting joined rows (base=2, aliased=4). HOLDS patched, VIOLATED at base (base=2 -> subquery gives 2). Encodes the deliberate no-dedup cardinality change.
- probe_7 (Req3.3/4.3): distinct forces subquery AND retains all selected clauses (name_lower present, 2 SELECT). HOLDS patched (also holds at base — distinct regression preserved).

Candidate wrong-fix (weak.diff): weakens ONLY the subquery-wrapping trigger to has_existing_aggregation but omits the annotation masking/inlining (set_annotation_mask + Ref replacement). REJECTED by probes 1,2,3,6: probe_1 becomes flat but STILL emits name_lower (fails alias-absent); probe_3 still emits authors_count inside subquery; probe_6 gives aliased_count=2 not 4 (still wrapped for the alias-aggregate). This proves the suite discriminates a partial fix that would not resolve the hidden tests (test_non_aggregate_annotation_pruned asserts assertNotIn('name_lower'), test_unreferenced_aggregate_annotation_pruned asserts assertNotIn('authors_count')).

All 7 probes HOLD on patched tree; positive control discriminates (fail@base, hold@patched); >=1 candidate exercised and rejected. Verdict SOUND.

Note on prior meta.json G-EQ=fail: the earlier audit's probe_5 (a different scratch dir) recorded a VIOLATION, but I could not reproduce any patched-tree probe failure across a comprehensive suite covering all four requirements. My independent suite finds the requirements faithful and discriminating.

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
"""Req 1.1 + 2.1 (POSITIVE CONTROL): annotate a non-aggregate expression
(Lower) then count() -> emitted SQL must be a single flat SELECT and the
annotation alias must be absent. Fails at base (old code wraps + emits it)."""
import sys
import django
from django.conf import settings

settings.configure(
    DEBUG=True,
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
    USE_TZ=False,
)
django.setup()

from django.db import models, connection
from django.db.models import Count
from django.db.models.functions import Lower
from django.test.utils import CaptureQueriesContext


class Book(models.Model):
    name = models.CharField(max_length=100)
    class Meta:
        app_label = "contenttypes"


with connection.schema_editor() as se:
    se.create_model(Book)

with CaptureQueriesContext(connection) as ctx:
    Book.objects.annotate(name_lower=Lower("name")).count()
sql = ctx.captured_queries[0]["sql"].lower()
print("SQL:", sql)
n_select = sql.count("select")
has_alias = "name_lower" in sql
print("select_count=%d name_lower_present=%s" % (n_select, has_alias))
ok = (n_select == 1) and (not has_alias)
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Bundle django__django-16263: get_aggregation prunes unused annotations/aliases from count()/aggregate() SQL.

Probes (all HOLD on gold-patched tree):
- probe_1 (Req1.1/2.1, POSITIVE CONTROL): annotate(name_lower=Lower('name')).count() -> single SELECT, alias absent. HOLDS patched, VIOLATED at base (base wraps in subquery emitting name_lower). Discriminates.
- probe_2 (Req1.2/2.1): alias(authors_count=Count('authors')).count() -> single SELECT, alias absent. HOLDS patched, VIOLATED at base.
- probe_3 (Req2.2/2.3): annotate(authors_count=Count('authors')).count() -> subquery used (2 SELECT) but unreferenced aggregate alias omitted. HOLDS patched, VIOLATED at base (base emits authors_count).
- probe_4 (Req3.1/3.2): annotate(authors_count=Count('authors')).aggregate(Avg('authors_count')) -> subquery + alias appears twice (defined+referenced). HOLDS patched (also holds at base, not discriminating for wrapping but pins the retain-referenced criterion).
- probe_5 (Req4.1): numeric correctness — count with pruned Lower == plain count (3==3); Avg of per-book author counts == 1.0. HOLDS.
- probe_6 (Req4.2): alias(Count('authors')).count() over multi-valued relation collapses to flat join, counting joined rows (base=2, aliased=4). HOLDS patched, VIOLATED at base (base=2 -> subquery gives 2). Encodes the deliberate no-dedup cardinality change.
- probe_7 (Req3.3/4.3): distinct forces subquery AND retains all selected clauses (name_lower present, 2 SELECT). HOLDS patched (also holds at base — distinct regression preserved).

Candidate wrong-fix (weak.diff): weakens ONLY the subquery-wrapping trigger to has_existing_aggregation but omits the annotation masking/inlining (set_annotation_mask + Ref replacement). REJECTED by probes 1,2,3,6: probe_1 becomes flat but STILL emits name_lower (fails alias-absent); probe_3 still emits authors_count inside subquery; probe_6 gives aliased_count=2 not 4 (still wrapped for the alias-aggregate). This proves the suite discriminates a partial fix that would not resolve the hidden tests (test_non_aggregate_annotation_pruned asserts assertNotIn('name_lower'), test_unreferenced_aggregate_annotation_pruned asserts assertNotIn('authors_count')).

All 7 probes HOLD on patched tree; positive control discriminates (fail@base, hold@patched); >=1 candidate exercised and rejected. Verdict SOUND.

Note on prior meta.json G-EQ=fail: the earlier audit's probe_5 (a different scratch dir) recorded a VIOLATION, but I could not reproduce any patched-tree probe failure across a comprehensive suite covering all four requirements. My independent suite finds the requirements faithful and discriminating.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Verified against the actual gold-patched tree in the instance image (all assertions exit 0; same assertions exit 1 at base, confirming the requirements pin the CHANGED behavior, not a narrow slice). Checks: R1.1/R2.1 annotate(Lower('name')).count() -> single SELECT, 'name_lower' absent; R1.2/R4.2 alias(Count('authors')).count() -> single flat SELECT, alias absent, AND returns joined-row cardinality 3 vs base-table 2 (the subtle non-compensated-dedup consequence is exactly right); R2.2 annotate(Count('authors')).count() -> 2 SELECTs (subquery), alias omitted; R3.1/R3.2 aggregate(Avg('authors_count')) -> 2 SELECTs, alias appears twice (inner def + outer ref); R3.3 annotate(Lower).distinct().count() -> 2 SELECTs, selected clause retained. The modeling boundary is the changed observable behavior (subquery-trigger decision keyed on has_existing_aggregation incl. HAVING/QUALIFY, emitted-clause pruning via get_refs/annotation_mask, and the numeric-result consequences), matching the patch to query.py/expressions.py/query_utils.py/where.py. Conservative-default (R4.7, getattr(...,True)) and filter-ref-resolution (R4.6, summarize threading) are directly reflected in the diff. No fabricated or forbidden behavior found.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Compared requirements.md against hidden test_patch (AggregateAnnotationPruningTests in tests/aggregation/tests.py), FAIL_TO_PASS/PASS_TO_PASS ids, and the gold patch, versus the public problem_statement.

No test-derived content transmitted:
- No test file path, class name (AggregateAnnotationPruningTests), or the four test method names (test_unused_aliased_aggregate_pruned, test_non_aggregate_annotation_pruned, test_unreferenced_aggregate_annotation_pruned, test_referenced_aggregate_annotation_kept).
- No test-invented identifiers: authors_count, name_lower, Lower, Avg, alias(Count("authors")) — none appear.
- No gold/fix-invented identifiers: get_refs, has_existing_aggregation, annotation_mask, set_annotation_mask, summarize, Ref, replace_expressions — none appear.
- The only concrete example (Book.objects.annotate(Count("chapters")).count() vs Book.objects.count()) is verbatim from the PUBLIC problem_statement.
- Naming Query.get_aggregation and django/db/models/sql/query.py is legitimate change localization.

Case-mirroring check: the four Requirements do correspond to the four test scenarios, but they describe the genuine feature decision tree (selected vs unselected alias; aggregate/window vs non-aggregate; referenced vs unreferenced -> subquery-or-not, emit-or-prune). This is behavior translation, which is the intended purpose. Moreover R4.2 specifies join-cardinality/numeric consequences the tests never assert (tests only check SELECT count and alias-name presence), so the prose describes semantics beyond the tests rather than reconstructing them. No SELECT-count assertions or 'assertNotIn' style enumerations leak through as test-shaped prose.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
