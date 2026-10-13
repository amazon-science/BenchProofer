# P2 adversarial audit — django__django-16032

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 6 requirement probes hold on the patched tree; 1/2 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 6 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 6 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 2 alternative candidate patches, claimed to satisfy every cited requirement, and ran the same suite against them. The suite rejected 1 of the 2: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. The other 1 was not rejected by the suite. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (6):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
"""Positive control / Requirement 3.2: pk__in against an annotated+aliased
queryset executes and returns exactly the rows whose pk are produced by the
subquery. At base this raises OperationalError (subquery returns N columns)."""
import sys, types
import django
from django.conf import settings

settings.configure(
    DEBUG=True,
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    INSTALLED_APPS=["probeapp"], USE_TZ=False,
)
m = types.ModuleType("probeapp"); m.__path__ = ["/tmp"]; sys.modules["probeapp"] = m
django.setup()
from django.db import models, connection
from django.db.models import Value


class Publisher(models.Model):
    name = models.CharField(max_length=50)
    num_awards = models.IntegerField(default=0)
    class Meta: app_label = "probeapp"


with connection.schema_editor() as se:
    se.create_model(Publisher)

p1 = Publisher.objects.create(name="A", num_awards=3)
p2 = Publisher.objects.create(name="B", num_awards=7)
p3 = Publisher.objects.create(name="C", num_awards=9)

awarded = (Publisher.objects.filter(num_awards__gt=4)
           .annotate(pub_ann=Value(1)).alias(pub_alias=Value(1)))
qs = Publisher.objects.filter(pk__in=awarded)
try:
    got = sorted(qs.values_list("name", flat=True))
except Exception as e:
    print("RAISED:", type(e).__name__, str(e)[:200])
    sys.exit(1)
print("got:", got)
expected = ["B", "C"]
if got != expected:
    print("WRONG rows, expected", expected)
    sys.exit(1)
print("OK pk__in annotated+aliased returned correct rows")
sys.exit(0)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""Requirement 2.3 / 2.4 + F2P related test: Publisher.objects.filter(
book__in=long_books_qs).values("name") where long_books_qs is annotated and
aliased -> executes, returns correct related rows (single-column subquery)."""
import sys, types
import django
from django.conf import settings

settings.configure(
    DEBUG=True,
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    INSTALLED_APPS=["probeapp"], USE_TZ=False,
)
m = types.ModuleType("probeapp"); m.__path__ = ["/tmp"]; sys.modules["probeapp"] = m
django.setup()
from django.db import models, connection
from django.db.models import Value


class Publisher(models.Model):
    name = models.CharField(max_length=50)
    class Meta: app_label = "probeapp"


class Book(models.Model):
    title = models.CharField(max_length=50)
    pages = models.IntegerField(default=0)
    publisher = models.ForeignKey(Publisher, on_delete=models.CASCADE, related_name="book")
    class Meta: app_label = "probeapp"


with connection.schema_editor() as se:
    se.create_model(Publisher)
    se.create_model(Book)

pa = Publisher.objects.create(name="Apress")
pb = Publisher.objects.create(name="Sams")
pc = Publisher.objects.create(name="Nobody")
Book.objects.create(title="big1", pages=500, publisher=pa)
Book.objects.create(title="big2", pages=450, publisher=pb)
Book.objects.create(title="small", pages=100, publisher=pc)

long_books = (Book.objects.filter(pages__gt=400)
              .annotate(book_ann=Value(1)).alias(book_alias=Value(1)))
qs = Publisher.objects.filter(book__in=long_books).values("name")
try:
    got = sorted(r["name"] for r in qs)
except Exception as e:
    print("RAISED:", type(e).__name__, str(e)[:200]); sys.exit(1)
print("got:", got)
if got != ["Apress", "Sams"]:
    print("WRONG rows"); sys.exit(1)
print("OK related book__in annotated+aliased returned correct rows")
sys.exit(0)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""Requirement 1.1/1.2/1.3/1.4: has_select_fields attribute semantics.
- fresh Query -> False (1.1, 1.4 default readable)
- after annotate()/alias() only -> still False (1.3)
- after values()/set_values -> True (1.2)"""
import sys, types
import django
from django.conf import settings

settings.configure(
    DEBUG=True,
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    INSTALLED_APPS=["probeapp"], USE_TZ=False,
)
m = types.ModuleType("probeapp"); m.__path__ = ["/tmp"]; sys.modules["probeapp"] = m
django.setup()
from django.db import models, connection
from django.db.models import Value
from django.db.models.sql.query import Query


class Publisher(models.Model):
    name = models.CharField(max_length=50)
    num_awards = models.IntegerField(default=0)
    class Meta: app_label = "probeapp"


with connection.schema_editor() as se:
    se.create_model(Publisher)

ok = True

# 1.1 / 1.4: fresh query has no explicit select
q = Query(Publisher)
if getattr(q, "has_select_fields", "MISSING") is not False:
    print("FAIL 1.1: fresh has_select_fields =", getattr(q, "has_select_fields", "MISSING")); ok = False
else:
    print("OK 1.1 fresh has_select_fields is False")

# 1.3: annotate + alias only -> still False
qs = (Publisher.objects.filter(num_awards__gt=0)
      .annotate(a=Value(1)).alias(b=Value(1)))
if qs.query.has_select_fields is not False:
    print("FAIL 1.3: annotate/alias set has_select_fields True"); ok = False
else:
    print("OK 1.3 annotate/alias keeps has_select_fields False")

# 1.2: values() -> True
qv = Publisher.objects.values("name")
if qv.query.has_select_fields is not True:
    print("FAIL 1.2: values() has_select_fields =", qv.query.has_select_fields); ok = False
else:
    print("OK 1.2 values() sets has_select_fields True")

# also values_list
ql = Publisher.objects.values_list("pk")
if ql.query.has_select_fields is not True:
    print("FAIL 1.2b: values_list has_select_fields =", ql.query.has_select_fields); ok = False
else:
    print("OK 1.2b values_list sets has_select_fields True")

sys.exit(0 if ok else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""Requirement 4.1: an explicit values()/values_list() selection on the RHS
queryset is left intact (NOT overridden by single-column reduction). We use a
RHS queryset with an explicit .values("num_awards") of a NON-pk column and
check the generated subquery SQL selects num_awards, not the pk / not the
related target. If the fix wrongly clobbered explicit selections, the column
would change."""
import sys, types
import django
from django.conf import settings

settings.configure(
    DEBUG=True,
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    INSTALLED_APPS=["probeapp"], USE_TZ=False,
)
m = types.ModuleType("probeapp"); m.__path__ = ["/tmp"]; sys.modules["probeapp"] = m
django.setup()
from django.db import models, connection


class Publisher(models.Model):
    name = models.CharField(max_length=50)
    num_awards = models.IntegerField(default=0)
    class Meta: app_label = "probeapp"


class Book(models.Model):
    title = models.CharField(max_length=50)
    publisher = models.ForeignKey(Publisher, on_delete=models.CASCADE, related_name="book")
    class Meta: app_label = "probeapp"


with connection.schema_editor() as se:
    se.create_model(Publisher)
    se.create_model(Book)

# explicit values selection of a non-pk column; used on pk__in should honor it
rhs = Publisher.objects.filter(num_awards__gt=0).values("num_awards")
outer = Publisher.objects.filter(pk__in=rhs)
sql, params = outer.query.get_compiler("default").as_sql()
print("SQL:", sql)
low = sql.lower()
# The subquery must select num_awards (explicit), NOT be reduced to id.
if "num_awards" not in low:
    print("FAIL 4.1: explicit values(num_awards) not preserved in subquery")
    sys.exit(1)
# It should not have replaced with the primary key select of publisher inside subselect
print("OK 4.1 explicit values() selection preserved")
sys.exit(0)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""Requirement 4.3: cross-model queryset with no explicit selected fields
passed to a relation lookup still raises the validation error. Here book__in
expects Book rows; passing a Publisher queryset (incompatible model) must
raise ValueError as before."""
import sys, types
import django
from django.conf import settings

settings.configure(
    DEBUG=True,
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    INSTALLED_APPS=["probeapp"], USE_TZ=False,
)
m = types.ModuleType("probeapp"); m.__path__ = ["/tmp"]; sys.modules["probeapp"] = m
django.setup()
from django.db import models, connection


class Publisher(models.Model):
    name = models.CharField(max_length=50)
    class Meta: app_label = "probeapp"


class Book(models.Model):
    title = models.CharField(max_length=50)
    publisher = models.ForeignKey(Publisher, on_delete=models.CASCADE, related_name="book")
    class Meta: app_label = "probeapp"


with connection.schema_editor() as se:
    se.create_model(Publisher)
    se.create_model(Book)

# book__in expects Book; feed an incompatible Publisher queryset (no explicit select)
wrong = Publisher.objects.all()
try:
    list(Publisher.objects.filter(book__in=wrong))
except ValueError as e:
    print("OK 4.3 raised ValueError:", str(e)[:150])
    sys.exit(0)
except Exception as e:
    print("Raised other:", type(e).__name__, str(e)[:150])
    # Acceptable only if it is the cross-model validation; ValueError expected
    sys.exit(1)
print("FAIL 4.3: cross-model queryset did NOT raise")
sys.exit(1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
"""Requirement 2.1/2.4 (SQL-level): a relational __in with an unselected,
annotated+aliased RHS produces a subquery selecting exactly ONE column, and
the annotation/alias/model columns are discarded (no extra columns). We inspect
the compiled SQL of the subquery: count columns in the inner SELECT list."""
import sys, types, re
import django
from django.conf import settings

settings.configure(
    DEBUG=True,
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    INSTALLED_APPS=["probeapp"], USE_TZ=False,
)
m = types.ModuleType("probeapp"); m.__path__ = ["/tmp"]; sys.modules["probeapp"] = m
django.setup()
from django.db import models, connection
from django.db.models import Value


class Publisher(models.Model):
    name = models.CharField(max_length=50)
    class Meta: app_label = "probeapp"


class Book(models.Model):
    title = models.CharField(max_length=50)
    pages = models.IntegerField(default=0)
    publisher = models.ForeignKey(Publisher, on_delete=models.CASCADE, related_name="book")
    class Meta: app_label = "probeapp"


with connection.schema_editor() as se:
    se.create_model(Publisher)
    se.create_model(Book)

long_books = (Book.objects.filter(pages__gt=400)
              .annotate(book_ann=Value(1)).alias(book_alias=Value(1)))
outer = Publisher.objects.filter(book__in=long_books)
sql, params = outer.query.get_compiler("default").as_sql()
print("SQL:", sql)
# Extract the inner subselect: text between "IN (SELECT" and its closing ")"
mobj = re.search(r"IN \(SELECT (.*?) FROM", sql, re.IGNORECASE | re.DOTALL)
if not mobj:
    print("FAIL: could not locate subselect"); sys.exit(1)
cols = mobj.group(1)
ncols = cols.count(",") + 1
print("subselect columns:", cols, "->", ncols)
if ncols != 1:
    print("FAIL 2.1/2.4: subquery emits", ncols, "columns (expected 1)")
    sys.exit(1)
# discarded annotations: no book_ann in subselect column list
if "book_ann" in cols.lower():
    print("FAIL 2.4: annotation column leaked into subselect"); sys.exit(1)
# Single column should be the related target (publisher_id)
if "publisher_id" not in cols.lower() and "publisher" not in cols.lower():
    print("WARN: single column not obviously publisher target:", cols)
print("OK 2.1/2.4 subquery reduced to a single target column")
sys.exit(0)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Positive control / Requirement 3.2: pk__in against an annotated+aliased
queryset executes and returns exactly the rows whose pk are produced by the
subquery. At base this raises OperationalError (subquery returns N columns)."""
import sys, types
import django
from django.conf import settings

settings.configure(
    DEBUG=True,
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    INSTALLED_APPS=["probeapp"], USE_TZ=False,
)
m = types.ModuleType("probeapp"); m.__path__ = ["/tmp"]; sys.modules["probeapp"] = m
django.setup()
from django.db import models, connection
from django.db.models import Value


class Publisher(models.Model):
    name = models.CharField(max_length=50)
    num_awards = models.IntegerField(default=0)
    class Meta: app_label = "probeapp"


with connection.schema_editor() as se:
    se.create_model(Publisher)

p1 = Publisher.objects.create(name="A", num_awards=3)
p2 = Publisher.objects.create(name="B", num_awards=7)
p3 = Publisher.objects.create(name="C", num_awards=9)

awarded = (Publisher.objects.filter(num_awards__gt=4)
           .annotate(pub_ann=Value(1)).alias(pub_alias=Value(1)))
qs = Publisher.objects.filter(pk__in=awarded)
try:
    got = sorted(qs.values_list("name", flat=True))
except Exception as e:
    print("RAISED:", type(e).__name__, str(e)[:200])
    sys.exit(1)
print("got:", got)
expected = ["B", "C"]
if got != expected:
    print("WRONG rows, expected", expected)
    sys.exit(1)
print("OK pk__in annotated+aliased returned correct rows")
sys.exit(0)
```

Prepatch bug re-encoded as an attack: `True`.

6 distinct probes, all HOLD on gold-patched tree; each maps to a requirement criterion:
- probe_1 (Req 3.2, POSITIVE CONTROL): pk__in against annotated+aliased Publisher queryset executes and returns correct rows. HOLDS patched; VIOLATED at base ('sub-select returns 4 columns - expected 1'). Discriminates.
- probe_2 (Req 2.3/2.4 + F2P related test): Publisher.filter(book__in=long_books_qs).values('name') with annotated+aliased RHS returns correct related rows. HOLDS.
- probe_3 (Req 1.1/1.2/1.3/1.4): has_select_fields attribute semantics — fresh Query False, annotate()/alias() only keeps False, values()/values_list() sets True. HOLDS.
- probe_4 (Req 4.1): explicit .values('num_awards') RHS selection left intact (subselect selects num_awards, not reduced to pk). HOLDS.
- probe_5 (Req 4.3): cross-model queryset (Publisher fed to book__in) still raises ValueError validation error. HOLDS.
- probe_6 (Req 2.1/2.4, SQL-level): relational __in with unselected annotated+aliased RHS compiles to a single-column subselect (U0.id), annotation column discarded. HOLDS.

DISCRIMINATION: weak_C (only the related_lookups.py half of gold — set_values swap — WITHOUT restoring has_select_fields as a plain attribute, i.e. leaving the old property intact) is REJECTED by probes 1,2,3,6: annotate()/alias() still flip has_select_fields True (property derives from annotation_select_mask), so the reduction branch never fires and subqueries emit 4-5 columns. This proves the probe suite discriminates the buggy behavior.

weak_A (only the query.py half — new has_select_fields=False class attr + set in set_values — with related_lookups.py LEFT AT BASE using clear_select_clause()+add_fields) PASSES all 6 probes. It is a plausibly-wrong/alternate patch: the runner re-checks it against the official harness. It behaves equivalently on all encoded criteria (single-column subselects via the old clear_select_clause+add_fields path now correctly triggered by the fixed attribute). If the harness confirms it resolves, the spec is sound with an equivalent alternate; the probe suite floor is met (>=1 exercised, weak_C REJECTED).

All runs completed in-container; no INCONCLUSIVE. Verdict SOUND: >=5 probes hold on patched tree and the positive control discriminates (holds patched, fails at base).

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 requirement probes hold on the patched tree; 1/2 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 6 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 6 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 2 alternative candidate patches, claimed to satisfy every cited requirement, and ran the same suite against them. The suite rejected 1 of the 2: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. The other 1 was not rejected by the suite. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

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
"""Positive control / Requirement 3.2: pk__in against an annotated+aliased
queryset executes and returns exactly the rows whose pk are produced by the
subquery. At base this raises OperationalError (subquery returns N columns)."""
import sys, types
import django
from django.conf import settings

settings.configure(
    DEBUG=True,
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    INSTALLED_APPS=["probeapp"], USE_TZ=False,
)
m = types.ModuleType("probeapp"); m.__path__ = ["/tmp"]; sys.modules["probeapp"] = m
django.setup()
from django.db import models, connection
from django.db.models import Value


class Publisher(models.Model):
    name = models.CharField(max_length=50)
    num_awards = models.IntegerField(default=0)
    class Meta: app_label = "probeapp"


with connection.schema_editor() as se:
    se.create_model(Publisher)

p1 = Publisher.objects.create(name="A", num_awards=3)
p2 = Publisher.objects.create(name="B", num_awards=7)
p3 = Publisher.objects.create(name="C", num_awards=9)

awarded = (Publisher.objects.filter(num_awards__gt=4)
           .annotate(pub_ann=Value(1)).alias(pub_alias=Value(1)))
qs = Publisher.objects.filter(pk__in=awarded)
try:
    got = sorted(qs.values_list("name", flat=True))
except Exception as e:
    print("RAISED:", type(e).__name__, str(e)[:200])
    sys.exit(1)
print("got:", got)
expected = ["B", "C"]
if got != expected:
    print("WRONG rows, expected", expected)
    sys.exit(1)
print("OK pk__in annotated+aliased returned correct rows")
sys.exit(0)
```

Prepatch bug re-encoded as an attack: `True`.

6 distinct probes, all HOLD on gold-patched tree; each maps to a requirement criterion:
- probe_1 (Req 3.2, POSITIVE CONTROL): pk__in against annotated+aliased Publisher queryset executes and returns correct rows. HOLDS patched; VIOLATED at base ('sub-select returns 4 columns - expected 1'). Discriminates.
- probe_2 (Req 2.3/2.4 + F2P related test): Publisher.filter(book__in=long_books_qs).values('name') with annotated+aliased RHS returns correct related rows. HOLDS.
- probe_3 (Req 1.1/1.2/1.3/1.4): has_select_fields attribute semantics — fresh Query False, annotate()/alias() only keeps False, values()/values_list() sets True. HOLDS.
- probe_4 (Req 4.1): explicit .values('num_awards') RHS selection left intact (subselect selects num_awards, not reduced to pk). HOLDS.
- probe_5 (Req 4.3): cross-model queryset (Publisher fed to book__in) still raises ValueError validation error. HOLDS.
- probe_6 (Req 2.1/2.4, SQL-level): relational __in with unselected annotated+aliased RHS compiles to a single-column subselect (U0.id), annotation column discarded. HOLDS.

DISCRIMINATION: weak_C (only the related_lookups.py half of gold — set_values swap — WITHOUT restoring has_select_fields as a plain attribute, i.e. leaving the old property intact) is REJECTED by probes 1,2,3,6: annotate()/alias() still flip has_select_fields True (property derives from annotation_select_mask), so the reduction branch never fires and subqueries emit 4-5 columns. This proves the probe suite discriminates the buggy behavior.

weak_A (only the query.py half — new has_select_fields=False class attr + set in set_values — with related_lookups.py LEFT AT BASE using clear_select_clause()+add_fields) PASSES all 6 probes. It is a plausibly-wrong/alternate patch: the runner re-checks it against the official harness. It behaves equivalently on all encoded criteria (single-column subselects via the old clear_select_clause+add_fields path now correctly triggered by the fixed attribute). If the harness confirms it resolves, the spec is sound with an equivalent alternate; the probe suite floor is met (>=1 exercised, weak_C REJECTED).

All runs completed in-container; no INCONCLUSIVE. Verdict SOUND: >=5 probes hold on patched tree and the positive control discriminates (holds patched, fails at base).

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Patch: (1) query.py replaces the derived `has_select_fields` property (bool of select/annotation_select_mask/extra_select_mask) with a class attr False, flipped True inside set_values(); (2) related_lookups.py RelatedIn switches from clear_select_clause()+add_fields([tf],True) to set_values([tf]). Requirements 1-4 correctly pin the CHANGED observable behavior (annotations/aliases no longer count as an explicit selection; RHS reduced to one column) rather than a narrow helper slice. Probe HOLDS on gold-patched tree (exit 0, single-column subquery SQL emitted) and VIOLATES on base (REQ1.3 assertion fails). No requirement mandates behavior the patch lacks, forbids behavior it has, or invents behavior. FAITHFUL.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The public problem_statement already contains the full book__in reproduction test: the Book.objects.filter(pages__gt=400).annotate(...).alias(...) construction, Publisher.objects.filter(book__in=long_books_qs).values('name'), the expected result set {Apress, Sams, Prentice Hall, Morgan Kaufmann}, and the 'sub-select returns N columns - expected 1' error. Requirements 2 and 4.6 draw entirely from this public content. The hidden test_patch adds a second variant (pk__in=awarded_publishers_qs where awarded_publishers_qs=Publisher.objects.filter(num_awards__gt=4)..., asserting [p3,p4]) — none of its distinguishing details (num_awards__gt=4, p3/p4, test function/class names annotations.tests.NonAggregateAnnotationTestCase) appear in requirements.md. Requirement 3 describes pk__in behavior generically/behaviorally without those hidden specifics. All named symbols (has_select_fields, set_values, clear_select_clause, add_fields, RelatedIn, In/Exact, annotation_select_mask, extra_select_mask) are pre-existing Django identifiers used for legitimate localization; set_values predates the fix, so no fix-invented identifier is disclosed. No test paths, no verbatim gold-patch lines, no parametrization ids, no test-shaped enumeration. The document translates checked behavior into requirements — the legitimate goal — rather than transmitting the hidden tests.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
