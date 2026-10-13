# P2 adversarial audit — django__django-11265

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

Counterexample / evidence:

```
weak_partial candidate (split_exclude fix only, omitting the trim_start fix) is REJECTED by probes 1,2,3: the leading INNER join carrying the filtered-relation condition is collapsed, so the emitted subquery becomes 'NOT (id IN (SELECT author_id FROM book WHERE id IS NOT NULL))' — the 'title LIKE' condition is dropped and exclude(book_alice__isnull=False) returns [] instead of [Jane]. This demonstrates the suite discriminates the partial wrong fix; no probe-conforming candidate resolving incorrectly was found.
```

**Attacks re-run (6):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
"""POSITIVE CONTROL. Req1.4 + Req2.5: exclude(book_alice__isnull=False) on an
annotated FilteredRelation over a to-many relation executes without raising AND
returns exactly the rows that do NOT satisfy the condition (author2 only).
HOLDS on patched tree; FAILS at base (FieldError / wrong rows)."""
import sys
import django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True,
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
        INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth', 'probeapp'],
        USE_TZ=False)
import types
m = types.ModuleType('probeapp'); m.__path__ = ['/testbed']; sys.modules['probeapp'] = m
django.setup()
from django.db import models, connection
from django.db.models import Q, FilteredRelation

class Author(models.Model):
    name = models.CharField(max_length=50, unique=True)
    class Meta: app_label = 'probeapp'
class Editor(models.Model):
    name = models.CharField(max_length=255)
    class Meta: app_label = 'probeapp'
class Book(models.Model):
    title = models.CharField(max_length=255)
    author = models.ForeignKey(Author, models.CASCADE, related_name='books', related_query_name='book')
    editor = models.ForeignKey(Editor, models.CASCADE)
    class Meta: app_label = 'probeapp'

with connection.schema_editor() as se:
    se.create_model(Author); se.create_model(Editor); se.create_model(Book)
ed = Editor.objects.create(name='Ed')
a1 = Author.objects.create(name='Alice')
a2 = Author.objects.create(name='Jane')
Book.objects.create(title='Poem by Alice', author=a1, editor=ed)
Book.objects.create(title='The book by Jane A', author=a2, editor=ed)

try:
    qs = Author.objects.annotate(
        book_alice=FilteredRelation('book', condition=Q(book__title__iexact='poem by alice')),
    ).exclude(book_alice__isnull=False)
    result = list(qs)
except Exception as e:
    print("VIOLATED: exclude raised %r: %s" % (type(e).__name__, e))
    sys.exit(1)

names = sorted(a.name for a in result)
print("exclude(book_alice__isnull=False) ->", names)
if names == ['Jane']:
    print("OK: returns only author2 (Jane), the row not satisfying the condition")
    sys.exit(0)
print("VIOLATED: expected ['Jane'], got", names)
sys.exit(1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""Req 2.5 / superset guard (also a strong discriminator for the trim_start
fix). Use a condition matching author2's book. exclude(book_alice__isnull=False)
must return exactly author1 (the row NOT satisfying the condition). If the
filtered relation's condition were dropped when the leading join is trimmed, the
subquery would become 'authors with ANY book' and exclude would return [] —
a wrong (super-restrictive) result. HOLDS patched, FAILS at base."""
import sys, types
import django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True,
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
        INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth', 'probeapp'],
        USE_TZ=False)
m = types.ModuleType('probeapp'); m.__path__ = ['/testbed']; sys.modules['probeapp'] = m
django.setup()
from django.db import models, connection
from django.db.models import Q, FilteredRelation

class Author(models.Model):
    name = models.CharField(max_length=50, unique=True)
    class Meta: app_label = 'probeapp'
class Editor(models.Model):
    name = models.CharField(max_length=255)
    class Meta: app_label = 'probeapp'
class Book(models.Model):
    title = models.CharField(max_length=255)
    author = models.ForeignKey(Author, models.CASCADE, related_name='books', related_query_name='book')
    editor = models.ForeignKey(Editor, models.CASCADE)
    class Meta: app_label = 'probeapp'

with connection.schema_editor() as se:
    se.create_model(Author); se.create_model(Editor); se.create_model(Book)
ed = Editor.objects.create(name='Ed')
a1 = Author.objects.create(name='Alice')
a2 = Author.objects.create(name='Jane')
Book.objects.create(title='Poem by Alice', author=a1, editor=ed)
Book.objects.create(title='The book by Jane A', author=a2, editor=ed)

try:
    qs = Author.objects.annotate(
        book_jane=FilteredRelation('book', condition=Q(book__title__iexact='the book by jane a')),
    ).exclude(book_jane__isnull=False)
    names = sorted(a.name for a in qs)
except Exception as e:
    print("VIOLATED: raised %r: %s" % (type(e).__name__, e))
    sys.exit(1)
print("exclude(book_jane__isnull=False) ->", names)
if names == ['Alice']:
    print("OK: condition retained; only author1 returned")
    sys.exit(0)
print("VIOLATED: expected ['Alice'] (condition retained); got", names)
sys.exit(1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""Req 1.1/1.2/1.3 (mechanism-level): split_exclude must install the
originating query's named filtered-relation definitions onto the inner query so
the alias resolves. We introspect the generated SQL: excluding on the alias must
compile to a negated membership subquery (NOT (... IN (SELECT ...))) and must
NOT raise FieldError. Encodes that the definitions are carried (else FieldError)
and the subquery form is a negated membership subquery. HOLDS patched, FAILS base."""
import sys, types
import django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True,
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
        INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth', 'probeapp'],
        USE_TZ=False)
m = types.ModuleType('probeapp'); m.__path__ = ['/testbed']; sys.modules['probeapp'] = m
django.setup()
from django.db import models, connection
from django.db.models import Q, FilteredRelation

class Author(models.Model):
    name = models.CharField(max_length=50, unique=True)
    class Meta: app_label = 'probeapp'
class Editor(models.Model):
    name = models.CharField(max_length=255)
    class Meta: app_label = 'probeapp'
class Book(models.Model):
    title = models.CharField(max_length=255)
    author = models.ForeignKey(Author, models.CASCADE, related_name='books', related_query_name='book')
    editor = models.ForeignKey(Editor, models.CASCADE)
    class Meta: app_label = 'probeapp'

with connection.schema_editor() as se:
    se.create_model(Author); se.create_model(Editor); se.create_model(Book)

try:
    qs = Author.objects.annotate(
        book_alice=FilteredRelation('book', condition=Q(book__title__iexact='poem by alice')),
    ).exclude(book_alice__isnull=False)
    sql, params = qs.query.sql_with_params()
except Exception as e:
    print("VIOLATED: building/compiling raised %r: %s" % (type(e).__name__, e))
    sys.exit(1)
low = sql.lower()
print("SQL:", sql)
if 'not (' not in low or 'in (select' not in low:
    print("VIOLATED: expected a negated membership subquery (NOT (... IN (SELECT ...)))")
    sys.exit(1)
# the filtered relation's condition text must survive into the subquery
if 'poem by alice' not in ' '.join(str(p).lower() for p in params) and 'iexact' not in low and 'like' not in low and 'upper' not in low:
    print("VIOLATED: filtered relation condition not present in emitted SQL")
    sys.exit(1)
print("OK: negated membership subquery emitted with condition present")
sys.exit(0)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""Req 3.1: filter(...) on an annotated FilteredRelation (incl. __isnull and a
join-crossing condition) keeps returning the same rows as before. This is a
"SHALL keep" regression criterion — it must HOLD on BOTH base and patched trees.
filter(book_alice__isnull=False) -> author1; filter with join condition too."""
import sys, types
import django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True,
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
        INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth', 'probeapp'],
        USE_TZ=False)
m = types.ModuleType('probeapp'); m.__path__ = ['/testbed']; sys.modules['probeapp'] = m
django.setup()
from django.db import models, connection
from django.db.models import Q, FilteredRelation

class Author(models.Model):
    name = models.CharField(max_length=50, unique=True)
    class Meta: app_label = 'probeapp'
class Editor(models.Model):
    name = models.CharField(max_length=255)
    class Meta: app_label = 'probeapp'
class Book(models.Model):
    title = models.CharField(max_length=255)
    author = models.ForeignKey(Author, models.CASCADE, related_name='books', related_query_name='book')
    editor = models.ForeignKey(Editor, models.CASCADE)
    class Meta: app_label = 'probeapp'

with connection.schema_editor() as se:
    se.create_model(Author); se.create_model(Editor); se.create_model(Book)
ed = Editor.objects.create(name='Ed')
a1 = Author.objects.create(name='Alice')
a2 = Author.objects.create(name='Jane')
Book.objects.create(title='Poem by Alice', author=a1, editor=ed)
Book.objects.create(title='The book by Jane A', author=a2, editor=ed)

try:
    q1 = Author.objects.annotate(
        book_alice=FilteredRelation('book', condition=Q(book__title__iexact='poem by alice')),
    ).filter(book_alice__isnull=False)
    n1 = sorted(a.name for a in q1)
    q2 = Author.objects.annotate(
        book_alice=FilteredRelation('book', condition=Q(book__title__iexact='poem by alice')),
    ).filter(book_alice__title__iexact='poem by alice')
    n2 = sorted(a.name for a in q2)
except Exception as e:
    print("VIOLATED: filter raised %r: %s" % (type(e).__name__, e))
    sys.exit(1)
print("filter(isnull=False) ->", n1, "; filter(join cond) ->", n2)
if n1 == ['Alice'] and n2 == ['Alice']:
    print("OK: filter on FilteredRelation unchanged")
    sys.exit(0)
print("VIOLATED: expected ['Alice']/['Alice']")
sys.exit(1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""Req 3.3: misuse of a FilteredRelation (empty relation name) SHALL keep raising
the same validation error. FilteredRelation('', condition=...) must raise
ValueError both before and after the change. A "SHALL keep" regression: HOLDS on
BOTH trees."""
import sys, types
import django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True,
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
        INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth', 'probeapp'],
        USE_TZ=False)
m = types.ModuleType('probeapp'); m.__path__ = ['/testbed']; sys.modules['probeapp'] = m
django.setup()
from django.db.models import Q, FilteredRelation

try:
    FilteredRelation('', condition=Q(book__title='x'))
    print("VIOLATED: empty relation_name did not raise")
    sys.exit(1)
except ValueError as e:
    print("OK: empty relation_name raised ValueError:", e)
    sys.exit(0)
except Exception as e:
    print("VIOLATED: raised %r not ValueError: %s" % (type(e).__name__, e))
    sys.exit(1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
"""Req 3.4: exclude(...) crossing a to-many relation that does NOT involve a
FilteredRelation SHALL keep building the negated subquery and returning the same
rows. exclude(book__title__iexact='poem by alice') -> author2 (Jane). A "SHALL
keep" regression: HOLDS on BOTH trees (the fix must not disturb this path)."""
import sys, types
import django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True,
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
        INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth', 'probeapp'],
        USE_TZ=False)
m = types.ModuleType('probeapp'); m.__path__ = ['/testbed']; sys.modules['probeapp'] = m
django.setup()
from django.db import models, connection
from django.db.models import Q

class Author(models.Model):
    name = models.CharField(max_length=50, unique=True)
    class Meta: app_label = 'probeapp'
class Editor(models.Model):
    name = models.CharField(max_length=255)
    class Meta: app_label = 'probeapp'
class Book(models.Model):
    title = models.CharField(max_length=255)
    author = models.ForeignKey(Author, models.CASCADE, related_name='books', related_query_name='book')
    editor = models.ForeignKey(Editor, models.CASCADE)
    class Meta: app_label = 'probeapp'

with connection.schema_editor() as se:
    se.create_model(Author); se.create_model(Editor); se.create_model(Book)
ed = Editor.objects.create(name='Ed')
a1 = Author.objects.create(name='Alice')
a2 = Author.objects.create(name='Jane')
Book.objects.create(title='Poem by Alice', author=a1, editor=ed)
Book.objects.create(title='The book by Jane A', author=a2, editor=ed)

try:
    qs = Author.objects.exclude(book__title__iexact='poem by alice')
    names = sorted(a.name for a in qs)
except Exception as e:
    print("VIOLATED: raised %r: %s" % (type(e).__name__, e))
    sys.exit(1)
print("exclude(book__title=...) ->", names)
if names == ['Jane']:
    print("OK: non-FilteredRelation exclude over to-many unchanged")
    sys.exit(0)
print("VIOLATED: expected ['Jane']; got", names)
sys.exit(1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""POSITIVE CONTROL. Req1.4 + Req2.5: exclude(book_alice__isnull=False) on an
annotated FilteredRelation over a to-many relation executes without raising AND
returns exactly the rows that do NOT satisfy the condition (author2 only).
HOLDS on patched tree; FAILS at base (FieldError / wrong rows)."""
import sys
import django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True,
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
        INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth', 'probeapp'],
        USE_TZ=False)
import types
m = types.ModuleType('probeapp'); m.__path__ = ['/testbed']; sys.modules['probeapp'] = m
django.setup()
from django.db import models, connection
from django.db.models import Q, FilteredRelation

class Author(models.Model):
    name = models.CharField(max_length=50, unique=True)
    class Meta: app_label = 'probeapp'
class Editor(models.Model):
    name = models.CharField(max_length=255)
    class Meta: app_label = 'probeapp'
class Book(models.Model):
    title = models.CharField(max_length=255)
    author = models.ForeignKey(Author, models.CASCADE, related_name='books', related_query_name='book')
    editor = models.ForeignKey(Editor, models.CASCADE)
    class Meta: app_label = 'probeapp'

with connection.schema_editor() as se:
    se.create_model(Author); se.create_model(Editor); se.create_model(Book)
ed = Editor.objects.create(name='Ed')
a1 = Author.objects.create(name='Alice')
a2 = Author.objects.create(name='Jane')
Book.objects.create(title='Poem by Alice', author=a1, editor=ed)
Book.objects.create(title='The book by Jane A', author=a2, editor=ed)

try:
    qs = Author.objects.annotate(
        book_alice=FilteredRelation('book', condition=Q(book__title__iexact='poem by alice')),
    ).exclude(book_alice__isnull=False)
    result = list(qs)
except Exception as e:
    print("VIOLATED: exclude raised %r: %s" % (type(e).__name__, e))
    sys.exit(1)

names = sorted(a.name for a in result)
print("exclude(book_alice__isnull=False) ->", names)
if names == ['Jane']:
    print("OK: returns only author2 (Jane), the row not satisfying the condition")
    sys.exit(0)
print("VIOLATED: expected ['Jane'], got", names)
sys.exit(1)
```

Prepatch bug re-encoded as an attack: `True`.

Requirements bundle for django__django-11265 (exclude over annotated FilteredRelation). 6 standalone probes, all run in the instance Docker image (probeapp given __path__=['/testbed']).

Results (criterion -> base / patched / weak_partial):
- probe_1 POSITIVE CONTROL, Req1.4+2.5 exclude(book_alice__isnull=False)->['Jane']: base VIOLATED (FieldError) / patched HOLDS / partial VIOLATED ([]). Discriminates.
- probe_2 Req2.5 superset guard, condition matches author2, exclude->['Alice']: base VIOLATED (FieldError) / patched HOLDS / partial VIOLATED ([]).
- probe_3 Req1.1-1.3 mechanism: split_exclude carries _filtered_relations; SQL must be negated membership subquery retaining the LIKE condition: base VIOLATED (FieldError) / patched HOLDS / partial VIOLATED (condition collapsed out of subquery).
- probe_4 Req3.1 SHALL-keep: filter(isnull=False) and join-crossing filter ->['Alice']: HOLDS base+patched+partial.
- probe_5 Req3.3 SHALL-keep: FilteredRelation('') raises ValueError: HOLDS base+patched+partial.
- probe_6 Req3.4 SHALL-keep: exclude over non-FilteredRelation to-many ->['Jane']: HOLDS base+patched+partial.

Positive control fails at base (FieldError) and holds patched -> discriminating power confirmed. All 6 probes hold on the gold-patched tree. The partial-fix candidate (the lazy reading that only carries _filtered_relations without the trim_start non-collapse) is rejected by 3 probes, so the requirements as encoded are not too-weak on that axis. No probe fails on the patched tree; no probe-conforming candidate resolves incorrectly. Verdict SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 6 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 6 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

Counterexample / evidence:

```
weak_partial candidate (split_exclude fix only, omitting the trim_start fix) is REJECTED by probes 1,2,3: the leading INNER join carrying the filtered-relation condition is collapsed, so the emitted subquery becomes 'NOT (id IN (SELECT author_id FROM book WHERE id IS NOT NULL))' — the 'title LIKE' condition is dropped and exclude(book_alice__isnull=False) returns [] instead of [Jane]. This demonstrates the suite discriminates the partial wrong fix; no probe-conforming candidate resolving incorrectly was found.
```

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
"""POSITIVE CONTROL. Req1.4 + Req2.5: exclude(book_alice__isnull=False) on an
annotated FilteredRelation over a to-many relation executes without raising AND
returns exactly the rows that do NOT satisfy the condition (author2 only).
HOLDS on patched tree; FAILS at base (FieldError / wrong rows)."""
import sys
import django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True,
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
        INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth', 'probeapp'],
        USE_TZ=False)
import types
m = types.ModuleType('probeapp'); m.__path__ = ['/testbed']; sys.modules['probeapp'] = m
django.setup()
from django.db import models, connection
from django.db.models import Q, FilteredRelation

class Author(models.Model):
    name = models.CharField(max_length=50, unique=True)
    class Meta: app_label = 'probeapp'
class Editor(models.Model):
    name = models.CharField(max_length=255)
    class Meta: app_label = 'probeapp'
class Book(models.Model):
    title = models.CharField(max_length=255)
    author = models.ForeignKey(Author, models.CASCADE, related_name='books', related_query_name='book')
    editor = models.ForeignKey(Editor, models.CASCADE)
    class Meta: app_label = 'probeapp'

with connection.schema_editor() as se:
    se.create_model(Author); se.create_model(Editor); se.create_model(Book)
ed = Editor.objects.create(name='Ed')
a1 = Author.objects.create(name='Alice')
a2 = Author.objects.create(name='Jane')
Book.objects.create(title='Poem by Alice', author=a1, editor=ed)
Book.objects.create(title='The book by Jane A', author=a2, editor=ed)

try:
    qs = Author.objects.annotate(
        book_alice=FilteredRelation('book', condition=Q(book__title__iexact='poem by alice')),
    ).exclude(book_alice__isnull=False)
    result = list(qs)
except Exception as e:
    print("VIOLATED: exclude raised %r: %s" % (type(e).__name__, e))
    sys.exit(1)

names = sorted(a.name for a in result)
print("exclude(book_alice__isnull=False) ->", names)
if names == ['Jane']:
    print("OK: returns only author2 (Jane), the row not satisfying the condition")
    sys.exit(0)
print("VIOLATED: expected ['Jane'], got", names)
sys.exit(1)
```

Prepatch bug re-encoded as an attack: `True`.

Requirements bundle for django__django-11265 (exclude over annotated FilteredRelation). 6 standalone probes, all run in the instance Docker image (probeapp given __path__=['/testbed']).

Results (criterion -> base / patched / weak_partial):
- probe_1 POSITIVE CONTROL, Req1.4+2.5 exclude(book_alice__isnull=False)->['Jane']: base VIOLATED (FieldError) / patched HOLDS / partial VIOLATED ([]). Discriminates.
- probe_2 Req2.5 superset guard, condition matches author2, exclude->['Alice']: base VIOLATED (FieldError) / patched HOLDS / partial VIOLATED ([]).
- probe_3 Req1.1-1.3 mechanism: split_exclude carries _filtered_relations; SQL must be negated membership subquery retaining the LIKE condition: base VIOLATED (FieldError) / patched HOLDS / partial VIOLATED (condition collapsed out of subquery).
- probe_4 Req3.1 SHALL-keep: filter(isnull=False) and join-crossing filter ->['Alice']: HOLDS base+patched+partial.
- probe_5 Req3.3 SHALL-keep: FilteredRelation('') raises ValueError: HOLDS base+patched+partial.
- probe_6 Req3.4 SHALL-keep: exclude over non-FilteredRelation to-many ->['Jane']: HOLDS base+patched+partial.

Positive control fails at base (FieldError) and holds patched -> discriminating power confirmed. All 6 probes hold on the gold-patched tree. The partial-fix candidate (the lazy reading that only carries _filtered_relations without the trim_start non-collapse) is rejected by 3 probes, so the requirements as encoded are not too-weak on that axis. No probe fails on the patched tree; no probe-conforming candidate resolves incorrectly. Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** The gold patch has exactly two hunks in django/db/models/sql/query.py, and the requirements track them precisely. Hunk 1 (split_exclude): `query._filtered_relations = self._filtered_relations` inserted before `query.add_filter(filter_expr)`; the pre-existing `query.clear_ordering(True)` on the next line backs Req 1.5's 'drop ordering' clause. This maps to Req 1.1-1.5 — install the originating query's filtered-relation defs onto the inner query before applying the filter, making the sets equal (Req 1.2), enabling alias resolution (Req 1.3/1.4). Hunk 2 (trim_start): the collapse guard changes from `if self.alias_map[...].join_type != LOUTER:` to `first_join = ...; if first_join.join_type != LOUTER and not first_join.filtered_relation:`. This maps to Req 2.1-2.4 — a filtered-relation INNER join is now non-collapsible (Req 2.1/2.4), LOUTER remains non-collapsible (Req 2.2), and only joins that are neither collapse (Req 2.3). Req 2's modeling boundary is correct: it pins the full changed observable (exclude retains the condition → returns correct rows, verified by exclude=['Jane'] not superset), not merely one branch. Req 3 preservation confirmed: filter path still returns ['Alice']. No unfaithful mandate, no forbidden behavior, no invented behavior, correct (behavior-level, not narrow-slice) boundary.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The requirements describe behavior and localize the change to django/db/models/sql/query.py's Query.split_exclude and Query.trim_start — legitimate localization, not a leak. The concrete example prose uses (book_alice=FilteredRelation('book', condition=Q(book__title__iexact='poem by alice')) + exclude(book_alice__isnull=False)), which is ALREADY present verbatim in the PUBLIC problem_statement, so it transmits nothing beyond it. No hidden-test content leaks: the test path/module (tests/filtered_relation/tests.py, filtered_relation.tests.FilteredRelationTests), the test function name (test_with_exclude), and the expected result ([self.author2]) do not appear. The gold-invented identifiers (query._filtered_relations, first_join.filtered_relation, LOUTER) are not quoted; Requirement 2 paraphrases the two-condition non-collapse rule (left-outer OR filtered-relation join) as behavior rather than reproducing the diff lines. Requirement 3's regression items are generic FilteredRelation behaviors implied by the public problem framing, not a mirror of the PASS_TO_PASS parametrization. No case enumeration reconstructs the hidden tests.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
