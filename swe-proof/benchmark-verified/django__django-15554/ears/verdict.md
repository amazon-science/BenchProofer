# P2 adversarial audit — django__django-15554

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 7 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 7 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py`, `probe_7.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_2.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (7):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
"""Positive control / Req1.1-1.3, Req1.2: two FilteredRelation on the SAME
relation with DIFFERENT conditions must emit a SEPARATE join each (distinct
aliases). Count JOIN clauses in the compiled SQL. HOLDS iff >= 2 joins.
Base tree collapses to 1 join -> fails."""
import django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True,
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
        INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
        USE_TZ=False)
django.setup()
from django.db import models
from django.db.models import FilteredRelation, Q

class Author(models.Model):
    name = models.CharField(max_length=50, unique=True)
    class Meta: app_label = "auth"
class Book(models.Model):
    title = models.CharField(max_length=255)
    author = models.ForeignKey(Author, models.CASCADE, related_name="books", related_query_name="book")
    class Meta: app_label = "auth"

qs = (Author.objects.annotate(
        book_title_alice=FilteredRelation("book", condition=Q(book__title__contains="Alice")),
        book_title_jane=FilteredRelation("book", condition=Q(book__title__icontains="Jane")),
      ).filter(name="Jane")
       .values("book_title_alice__title", "book_title_jane__title"))
sql = str(qs.query)
njoin = sql.upper().count(" JOIN ")
print("SQL:", sql)
print("join_count:", njoin)
# The two FilteredRelation must each get their own join.
import sys
sys.exit(0 if njoin >= 2 else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""Req1.4 + Req2.1/2.2/2.3: correct per-row values. Reproduces the hidden
test scenario (Author 'Jane' with two books, both matching Jane, neither
matching Alice). Selecting through each FilteredRelation must reflect that
FR's own condition; unmatched -> None. HOLDS iff results match expected."""
import django, sys
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True,
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
        INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
        USE_TZ=False)
django.setup()
from django.db import models, connection
from django.db.models import FilteredRelation, Q

class Author(models.Model):
    name = models.CharField(max_length=50, unique=True)
    class Meta: app_label = "auth"
class Book(models.Model):
    title = models.CharField(max_length=255)
    author = models.ForeignKey(Author, models.CASCADE, related_name="books", related_query_name="book")
    class Meta: app_label = "auth"

with connection.schema_editor() as se:
    se.create_model(Author); se.create_model(Book)
jane = Author.objects.create(name="Jane")
Book.objects.create(title="The book by Jane A", author=jane)
Book.objects.create(title="The book by Jane B", author=jane)

qs = (Author.objects.annotate(
        book_title_alice=FilteredRelation("book", condition=Q(book__title__contains="Alice")),
        book_title_jane=FilteredRelation("book", condition=Q(book__title__icontains="Jane")),
      ).filter(name="Jane")
       .values("book_title_alice__title", "book_title_jane__title"))
rows = list(qs)
print("rows:", rows)
empty = "" if connection.features.interprets_empty_strings_as_nulls else None
expected = [
    {"book_title_alice__title": empty, "book_title_jane__title": "The book by Jane A"},
    {"book_title_alice__title": empty, "book_title_jane__title": "The book by Jane B"},
]
def norm(l): return sorted((r["book_title_alice__title"], r["book_title_jane__title"]) for r in l)
ok = norm(rows) == norm(expected)
print("expected:", expected, "match:", ok)
sys.exit(0 if ok else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""Req2.2 + Req2.3: a FilteredRelation whose condition matches NO row for an
author yields None (not a borrowed value from a sibling FR). Author 'John'
has an 'Alice' book but a Jane-matching book too; use disjoint conditions so
one side is unmatched. HOLDS iff unmatched side is None and matched side is
correct, i.e. the two FRs are independent."""
import django, sys
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True,
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
        INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
        USE_TZ=False)
django.setup()
from django.db import models, connection
from django.db.models import FilteredRelation, Q

class Author(models.Model):
    name = models.CharField(max_length=50, unique=True)
    class Meta: app_label = "auth"
class Book(models.Model):
    title = models.CharField(max_length=255)
    author = models.ForeignKey(Author, models.CASCADE, related_name="books", related_query_name="book")
    class Meta: app_label = "auth"

with connection.schema_editor() as se:
    se.create_model(Author); se.create_model(Book)
# Solo has exactly ONE book that matches 'Bee' but not 'Zed'.
solo = Author.objects.create(name="Solo")
Book.objects.create(title="Bee story", author=solo)

qs = (Author.objects.annotate(
        fr_zed=FilteredRelation("book", condition=Q(book__title__contains="Zed")),
        fr_bee=FilteredRelation("book", condition=Q(book__title__contains="Bee")),
      ).filter(name="Solo")
       .values("fr_zed__title", "fr_bee__title"))
rows = list(qs)
print("rows:", rows)
empty = "" if connection.features.interprets_empty_strings_as_nulls else None
ok = (len(rows) == 1
      and rows[0]["fr_zed__title"] == empty     # no match -> "no value" marker
      and rows[0]["fr_bee__title"] == "Bee story")  # own condition matched
print("unmatched side (fr_zed) == no-value:", rows and rows[0]["fr_zed__title"] == empty)
print("matched side (fr_bee) correct:", rows and rows[0]["fr_bee__title"] == "Bee story")
sys.exit(0 if ok else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""Req4.1 (regression): a SINGLE FilteredRelation with an extra .filter()
still works. HOLDS iff the single-FR query returns correct rows and emits
exactly one join for the FR relation."""
import django, sys
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True,
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
        INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
        USE_TZ=False)
django.setup()
from django.db import models, connection
from django.db.models import FilteredRelation, Q

class Author(models.Model):
    name = models.CharField(max_length=50, unique=True)
    class Meta: app_label = "auth"
class Book(models.Model):
    title = models.CharField(max_length=255)
    author = models.ForeignKey(Author, models.CASCADE, related_name="books", related_query_name="book")
    class Meta: app_label = "auth"

with connection.schema_editor() as se:
    se.create_model(Author); se.create_model(Book)
jane = Author.objects.create(name="Jane")
john = Author.objects.create(name="John")
Book.objects.create(title="Poem by Jane", author=jane)
Book.objects.create(title="Poem by John", author=john)

qs = (Author.objects.annotate(
        my_book=FilteredRelation("book", condition=Q(book__title__contains="Jane")),
      ).filter(my_book__title__contains="Poem"))
names = sorted(a.name for a in qs)
print("names:", names)
sql = str(qs.query)
njoin = sql.upper().count(" JOIN ")
print("join_count:", njoin)
# single FR -> exactly one join; only Jane matches
ok = names == ["Jane"] and njoin == 1
sys.exit(0 if ok else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""Req4.3 + Req4.8 (regression): referencing the SAME FR alias multiple times
resolves to a SINGLE join (not duplicated); and a query with at-most-one FR
per distinct relation keeps its single-join SQL shape. HOLDS iff the FR alias
referenced twice yields exactly one join for that relation."""
import django, sys
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True,
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
        INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
        USE_TZ=False)
django.setup()
from django.db import models, connection
from django.db.models import FilteredRelation, Q

class Author(models.Model):
    name = models.CharField(max_length=50, unique=True)
    class Meta: app_label = "auth"
class Book(models.Model):
    title = models.CharField(max_length=255)
    author = models.ForeignKey(Author, models.CASCADE, related_name="books", related_query_name="book")
    class Meta: app_label = "auth"

with connection.schema_editor() as se:
    se.create_model(Author); se.create_model(Book)

# One FR alias referenced twice (filter + values). Should be a single join.
qs = (Author.objects.annotate(
        my_book=FilteredRelation("book", condition=Q(book__title__contains="Alice")),
      ).filter(my_book__title__contains="Alice")
       .values("my_book__title", "name"))
sql = str(qs.query)
njoin = sql.upper().count(" JOIN ")
print("SQL:", sql)
print("join_count:", njoin)
sys.exit(0 if njoin == 1 else 1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
"""Req4.5 (regression): invalid FilteredRelation args still raise. A bare
expression as condition (not a Q) must raise ValueError; an empty relation
name must raise ValueError. HOLDS iff both still raise."""
import django, sys
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True,
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
        INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
        USE_TZ=False)
django.setup()
from django.db.models import FilteredRelation, F

ok = True
try:
    FilteredRelation("book", condition=F("book__title"))  # bare expr, not Q
    print("bare-expr condition did NOT raise"); ok = False
except ValueError as e:
    print("bare-expr raised ValueError:", e)
except Exception as e:
    print("bare-expr raised unexpected:", type(e).__name__, e); ok = False

try:
    FilteredRelation("", condition=None)  # empty relation name
    print("empty relation_name did NOT raise"); ok = False
except ValueError as e:
    print("empty relation_name raised ValueError:", e)
except Exception as e:
    print("empty relation_name raised unexpected:", type(e).__name__, e); ok = False

sys.exit(0 if ok else 1)
```

Attack 7 — `probe_7.py` → holds on the patched tree (good)

```python
"""Req4.7 (regression): a FilteredRelation declared but NOT selected through
produces NO join in the compiled SQL. HOLDS iff a query that annotates an FR
but never references it emits zero joins."""
import django, sys
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True,
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
        INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
        USE_TZ=False)
django.setup()
from django.db import models
from django.db.models import FilteredRelation, Q

class Author(models.Model):
    name = models.CharField(max_length=50, unique=True)
    class Meta: app_label = "auth"
class Book(models.Model):
    title = models.CharField(max_length=255)
    author = models.ForeignKey(Author, models.CASCADE, related_name="books", related_query_name="book")
    class Meta: app_label = "auth"

qs = (Author.objects.annotate(
        my_book=FilteredRelation("book", condition=Q(book__title__contains="Alice")),
      ).values("name"))  # never reference my_book
sql = str(qs.query)
njoin = sql.upper().count(" JOIN ")
print("SQL:", sql)
print("join_count:", njoin)
sys.exit(0 if njoin == 0 else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_2.py`

```python
"""Req1.4 + Req2.1/2.2/2.3: correct per-row values. Reproduces the hidden
test scenario (Author 'Jane' with two books, both matching Jane, neither
matching Alice). Selecting through each FilteredRelation must reflect that
FR's own condition; unmatched -> None. HOLDS iff results match expected."""
import django, sys
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True,
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
        INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
        USE_TZ=False)
django.setup()
from django.db import models, connection
from django.db.models import FilteredRelation, Q

class Author(models.Model):
    name = models.CharField(max_length=50, unique=True)
    class Meta: app_label = "auth"
class Book(models.Model):
    title = models.CharField(max_length=255)
    author = models.ForeignKey(Author, models.CASCADE, related_name="books", related_query_name="book")
    class Meta: app_label = "auth"

with connection.schema_editor() as se:
    se.create_model(Author); se.create_model(Book)
jane = Author.objects.create(name="Jane")
Book.objects.create(title="The book by Jane A", author=jane)
Book.objects.create(title="The book by Jane B", author=jane)

qs = (Author.objects.annotate(
        book_title_alice=FilteredRelation("book", condition=Q(book__title__contains="Alice")),
        book_title_jane=FilteredRelation("book", condition=Q(book__title__icontains="Jane")),
      ).filter(name="Jane")
       .values("book_title_alice__title", "book_title_jane__title"))
rows = list(qs)
print("rows:", rows)
empty = "" if connection.features.interprets_empty_strings_as_nulls else None
expected = [
    {"book_title_alice__title": empty, "book_title_jane__title": "The book by Jane A"},
    {"book_title_alice__title": empty, "book_title_jane__title": "The book by Jane B"},
]
def norm(l): return sorted((r["book_title_alice__title"], r["book_title_jane__title"]) for r in l)
ok = norm(rows) == norm(expected)
print("expected:", expected, "match:", ok)
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Bundle django__django-15554: multiple FilteredRelation on same relation with different conditions. 7 probes, all HOLD on gold-patched tree; positive controls (probe_1 join-count>=2, probe_2 correct per-row values, probe_3 unmatched->None + independence) each VIOLATED at base and HOLD patched -> discriminating power confirmed (G-DIFF analog).

Probe->requirement map:
- probe_1: Req1.1-1.3/1.2 — two FR on same relation emit >=2 distinct joins (base=1 join).
- probe_2 (positive control): Req1.4/Req2.1-2.3 — hidden-test scenario, correct per-row values; base returns both None (bug).
- probe_3: Req2.2/2.3 — FR with no matching row yields the 'no value' marker (None/'' by backend), not a borrowed sibling value; base collapses both to None.
- probe_4: Req4.1 regression — single FR + extra .filter() correct + exactly 1 join.
- probe_5: Req4.3/4.8 regression — one FR alias referenced twice = single join.
- probe_6: Req4.5 regression — invalid args (bare-expr condition, empty relation_name) still raise ValueError.
- probe_7: Req4.7 regression — declared-but-unused FR omits the join (0 joins).

WEAK CANDIDATE (weak.diff): naive fix flipping join()'s reuse test from j.equals(join) to j==join WITHOUT the patch's reuse_with_filtered_relation scoping plumbing through build_filter/setup_joins/build_filtered_relation_q. REJECTED by the probe suite: probes 2, 3, 4 fail under it with 'no such column: T3/T4.title' OperationalError (broken join resolution) — proves the suite discriminates plausibly-wrong implementations. Probes 1/5/6/7 pass under it (expected). All runs completed cleanly in the official image; no infra/timeouts.

Note: meta.json records G-PANEL-3=fail (LEAKAGE — worked example mirrors hidden test book/Alice/Jane specifics). That is a leakage concern, outside G-EQ (spec-fidelity) scope; G-EQ itself is SOUND: no requirement mandates behavior the gold code lacks, and the suite rejects a requirements-underspecified wrong fix.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 7 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 7 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py`, `probe_7.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_2.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (7):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts, and on this backend both roles put it through the same derivation: every block below is a requirement probe run on the gold-patched tree, and the `machine verdict:` line each role publishes above reports BOTH that its probes hold there and how many candidate patches the probe suite rejected — so the two roles re-ran ONE probe suite and each recorded its own outcome for every probe in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `probe_1.py` → holds on the patched tree (good)

Attack 2 — `probe_2.py` → holds on the patched tree (good)

Attack 3 — `probe_3.py` → holds on the patched tree (good)

Attack 4 — `probe_4.py` → holds on the patched tree (good)

Attack 5 — `probe_5.py` → holds on the patched tree (good)

Attack 6 — `probe_6.py` → holds on the patched tree (good)

Attack 7 — `probe_7.py` → holds on the patched tree (good)

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_2.py`

```python
"""Req1.4 + Req2.1/2.2/2.3: correct per-row values. Reproduces the hidden
test scenario (Author 'Jane' with two books, both matching Jane, neither
matching Alice). Selecting through each FilteredRelation must reflect that
FR's own condition; unmatched -> None. HOLDS iff results match expected."""
import django, sys
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True,
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
        INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
        USE_TZ=False)
django.setup()
from django.db import models, connection
from django.db.models import FilteredRelation, Q

class Author(models.Model):
    name = models.CharField(max_length=50, unique=True)
    class Meta: app_label = "auth"
class Book(models.Model):
    title = models.CharField(max_length=255)
    author = models.ForeignKey(Author, models.CASCADE, related_name="books", related_query_name="book")
    class Meta: app_label = "auth"

with connection.schema_editor() as se:
    se.create_model(Author); se.create_model(Book)
jane = Author.objects.create(name="Jane")
Book.objects.create(title="The book by Jane A", author=jane)
Book.objects.create(title="The book by Jane B", author=jane)

qs = (Author.objects.annotate(
        book_title_alice=FilteredRelation("book", condition=Q(book__title__contains="Alice")),
        book_title_jane=FilteredRelation("book", condition=Q(book__title__icontains="Jane")),
      ).filter(name="Jane")
       .values("book_title_alice__title", "book_title_jane__title"))
rows = list(qs)
print("rows:", rows)
empty = "" if connection.features.interprets_empty_strings_as_nulls else None
expected = [
    {"book_title_alice__title": empty, "book_title_jane__title": "The book by Jane A"},
    {"book_title_alice__title": empty, "book_title_jane__title": "The book by Jane B"},
]
def norm(l): return sorted((r["book_title_alice__title"], r["book_title_jane__title"]) for r in l)
ok = norm(rows) == norm(expected)
print("expected:", expected, "match:", ok)
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Bundle django__django-15554: multiple FilteredRelation on same relation with different conditions. 7 probes, all HOLD on gold-patched tree; positive controls (probe_1 join-count>=2, probe_2 correct per-row values, probe_3 unmatched->None + independence) each VIOLATED at base and HOLD patched -> discriminating power confirmed (G-DIFF analog).

Probe->requirement map:
- probe_1: Req1.1-1.3/1.2 — two FR on same relation emit >=2 distinct joins (base=1 join).
- probe_2 (positive control): Req1.4/Req2.1-2.3 — hidden-test scenario, correct per-row values; base returns both None (bug).
- probe_3: Req2.2/2.3 — FR with no matching row yields the 'no value' marker (None/'' by backend), not a borrowed sibling value; base collapses both to None.
- probe_4: Req4.1 regression — single FR + extra .filter() correct + exactly 1 join.
- probe_5: Req4.3/4.8 regression — one FR alias referenced twice = single join.
- probe_6: Req4.5 regression — invalid args (bare-expr condition, empty relation_name) still raise ValueError.
- probe_7: Req4.7 regression — declared-but-unused FR omits the join (0 joins).

WEAK CANDIDATE (weak.diff): naive fix flipping join()'s reuse test from j.equals(join) to j==join WITHOUT the patch's reuse_with_filtered_relation scoping plumbing through build_filter/setup_joins/build_filtered_relation_q. REJECTED by the probe suite: probes 2, 3, 4 fail under it with 'no such column: T3/T4.title' OperationalError (broken join resolution) — proves the suite discriminates plausibly-wrong implementations. Probes 1/5/6/7 pass under it (expected). All runs completed cleanly in the official image; no infra/timeouts.

Note: meta.json records G-PANEL-3=fail (LEAKAGE — worked example mirrors hidden test book/Alice/Jane specifics). That is a leakage concern, outside G-EQ (spec-fidelity) scope; G-EQ itself is SOUND: no requirement mandates behavior the gold code lacks, and the suite rejects a requirements-underspecified wrong fix.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Modeling boundary is correct: requirements pin the observable changed behavior (each distinct FilteredRelation on the same relation gets its own join/alias, values reflect own condition, NULL when unmatched) rather than a single branch or helper. Introduction's mechanism description (Join.equals structural vs Join.__eq__ full match; reuse_with_filtered_relation) matches patch.diff to query.py join/build_filter/setup_joins/build_filtered_relation_q. Probed live in instance image: patched HOLDS (exit0), base VIOLATED. Separately, meta records G-PANEL-3=fail (leakage of hidden-test specifics book/Alice/Jane), but that is the leakage role, not faithfulness; it does not make the requirements unfaithful to the change.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** requirements.md describes the FilteredRelation same-relation join-collapse bug and fix entirely in behavioral terms drawn from the PUBLIC problem_statement (zone/is_all/relation_zone/relation_all vocabulary). The hidden FAIL_TO_PASS test (test_multiple) leaks nothing: no Author/book/book_title_alice/book_title_jane identifiers, no Q(book__title__contains='Alice')/icontains='Jane') conditions, no filter(name='Jane'), and no expected values ('The book by Jane A/B', None/empty). The fix-invented parameter `reuse_with_filtered_relation` is never quoted. `Join.equals`/`Join.__eq__` are pre-existing datastructures.py methods (legitimate localization), and the equals->__eq__ swap is described behaviorally, not as code. Req 2.2's 'no value marker for an unmatched outer join' is genuine outer-join semantics, not a copy of the test's interprets_empty_strings_as_nulls mechanic. The Req 4 regression enumeration is the strongest leak candidate but only partially overlaps PASS_TO_PASS and IMPERFECTLY: it omits several existing tests (select_for_update, extra, relation_name_lookup, condition_*_relation_name) and adds paraphrased categories, indicating feature-surface scoping from domain knowledge rather than reconstruction of the hidden test id list. No test names, paths, ids, or assertions are transmitted.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
