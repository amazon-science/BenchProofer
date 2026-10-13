# P2 adversarial audit — django__django-14351

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
"""Probe for Req1.1/1.2 (POSITIVE CONTROL): when an __in subquery (no explicit
selected columns) becomes a GROUP BY grouping key, it SHALL be normalized to a
single primary-key column -> the group-by subquery returns exactly ONE column.
HOLDS iff the parenthesised subquery in GROUP BY has exactly 1 select column.
Discriminates: at base it has all default columns (>1)."""
import os, sys, tempfile, django

def setup():
    d = tempfile.mkdtemp()
    os.makedirs(os.path.join(d, 'app'))
    open(os.path.join(d, 'app', '__init__.py'), 'w').close()
    with open(os.path.join(d, 'app', 'models.py'), 'w') as f:
        f.write(
            "from django.db import models\n"
            "class Author(models.Model):\n"
            "    name = models.CharField(max_length=50)\n"
            "class Book(models.Model):\n"
            "    title = models.CharField(max_length=50)\n"
            "    authors = models.ManyToManyField(Author, related_name='books')\n"
        )
    sys.path.insert(0, d)
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth', 'app'],
            DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
            DEFAULT_AUTO_FIELD='django.db.models.AutoField',
        )
        django.setup()

def groupby_clause(sql):
    up = sql.upper()
    i = up.find('GROUP BY')
    assert i != -1, "no GROUP BY in SQL:\n" + sql
    tail = sql[i + len('GROUP BY'):]
    utail = tail.upper()
    ends = [utail.find(k) for k in (' HAVING', ' ORDER BY', ' LIMIT') if utail.find(k) != -1]
    j = min(ends) if ends else len(tail)
    return tail[:j]

def subquery_columns(clause):
    up = clause.upper()
    start = None; depth = 0
    for idx, ch in enumerate(clause):
        if ch == '(':
            if depth == 0 and up[idx:idx + 7] == '(SELECT':
                start = idx; depth = 1; continue
            if start is not None: depth += 1
        elif ch == ')' and start is not None:
            depth -= 1
            if depth == 0:
                sub = clause[start + 1:idx]; break
    else:
        return None
    usub = sub.upper(); sel = usub.find('SELECT')
    d = 0; fpos = None; k = sel + 6
    while k < len(sub):
        if sub[k] == '(': d += 1
        elif sub[k] == ')': d -= 1
        elif d == 0 and usub[k:k+4] == 'FROM' and sub[k-1] in ' \t\n' and sub[k+4] in ' \t\n':
            fpos = k; break
        k += 1
    assert fpos is not None
    sl = sub[sel+6:fpos]; d = 0; cols = 1
    for ch in sl:
        if ch == '(': d += 1
        elif ch == ')': d -= 1
        elif ch == ',' and d == 0: cols += 1
    return cols, sl.strip()

setup()
from django.db.models import Count, Q
from app.models import Author, Book
qs = Book.objects.annotate(Count('authors')).filter(
    Q(authors__in=Author.objects.filter(pk=1)) | Q(authors__count__gt=2)
)
sql = str(qs.query)
clause = groupby_clause(sql)
res = subquery_columns(clause)
print("GROUP BY clause:", clause.strip())
assert res is not None, "expected an __in subquery in GROUP BY but found none"
ncols, sl = res
print("subquery select list:", sl, "=> ncols:", ncols)
assert ncols == 1, "GROUP BY subquery returns %d columns (expected exactly 1): %s" % (ncols, sl)
print("PASS: group-by __in subquery contributes exactly one column")
sys.exit(0)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""Probe for Req2.1/2.2: the OR-of-__in-subquery-with-aggregate query SHALL
execute (no DB error) AND return exactly the objects satisfying membership OR
aggregate. We use a real data scenario mirroring the gold test:
b1 authored by a1 (matches __in a1); b4 authored by 3 authors (count>2).
HOLDS iff query executes and result == {b1, b4}."""
import os, sys, tempfile, django

def setup():
    d = tempfile.mkdtemp()
    os.makedirs(os.path.join(d, 'app'))
    open(os.path.join(d, 'app', '__init__.py'), 'w').close()
    with open(os.path.join(d, 'app', 'models.py'), 'w') as f:
        f.write(
            "from django.db import models\n"
            "class Author(models.Model):\n"
            "    name = models.CharField(max_length=50)\n"
            "class Book(models.Model):\n"
            "    title = models.CharField(max_length=50)\n"
            "    authors = models.ManyToManyField(Author, related_name='books')\n"
        )
    sys.path.insert(0, d)
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth', 'app'],
            DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
            DEFAULT_AUTO_FIELD='django.db.models.AutoField',
        )
        django.setup()

setup()
from django.db import connection
from django.db.models import Count, Q
from app.models import Author, Book
with connection.schema_editor() as se:
    se.create_model(Author)
    se.create_model(Book)  # creates the m2m through table too

a1 = Author.objects.create(name='a1')
a2 = Author.objects.create(name='a2')
a3 = Author.objects.create(name='a3')
b1 = Book.objects.create(title='b1'); b1.authors.add(a1)          # matches __in a1
b2 = Book.objects.create(title='b2'); b2.authors.add(a2)          # no match
b3 = Book.objects.create(title='b3'); b3.authors.add(a2, a3)      # count=2, no match
b4 = Book.objects.create(title='b4'); b4.authors.add(a1, a2, a3)  # count=3>2 AND has a1

authors = Author.objects.filter(pk=a1.pk)
qs = Book.objects.annotate(Count('authors')).filter(
    Q(authors__in=authors) | Q(authors__count__gt=2)
)
try:
    got = set(qs)
except Exception as e:
    print("QUERY RAISED:", type(e).__name__, e)
    sys.exit(1)
expected = {b1, b4}
print("expected:", sorted(b.title for b in expected))
print("got     :", sorted(b.title for b in got))
assert got == expected, "result mismatch: got %s expected %s" % (
    sorted(b.title for b in got), sorted(b.title for b in expected))
print("PASS: OR query executes and returns exactly the disjunction rows")
sys.exit(0)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""Probe for Req1.3: IF the rhs subquery ALREADY has explicitly selected
columns, the lookup SHALL leave that subquery's selected columns unchanged when
contributing group-by columns (i.e. it must NOT clobber them to pk).
We select an explicit non-pk column (.values('name')). HOLDS iff the group-by
subquery select list is the explicitly-chosen 'name' column (not rewritten to id)."""
import os, sys, tempfile, django

def setup():
    d = tempfile.mkdtemp()
    os.makedirs(os.path.join(d, 'app'))
    open(os.path.join(d, 'app', '__init__.py'), 'w').close()
    with open(os.path.join(d, 'app', 'models.py'), 'w') as f:
        f.write(
            "from django.db import models\n"
            "class Author(models.Model):\n"
            "    name = models.CharField(max_length=50)\n"
            "class Book(models.Model):\n"
            "    title = models.CharField(max_length=50)\n"
            "    authors = models.ManyToManyField(Author, related_name='books')\n"
        )
    sys.path.insert(0, d)
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth', 'app'],
            DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
            DEFAULT_AUTO_FIELD='django.db.models.AutoField',
        )
        django.setup()

def groupby_clause(sql):
    up = sql.upper(); i = up.find('GROUP BY')
    assert i != -1
    tail = sql[i + 8:]; utail = tail.upper()
    ends = [utail.find(k) for k in (' HAVING', ' ORDER BY', ' LIMIT') if utail.find(k) != -1]
    return tail[:min(ends)] if ends else tail

def subquery_select_list(clause):
    up = clause.upper(); start = None; depth = 0
    for idx, ch in enumerate(clause):
        if ch == '(':
            if depth == 0 and up[idx:idx+7] == '(SELECT':
                start = idx; depth = 1; continue
            if start is not None: depth += 1
        elif ch == ')' and start is not None:
            depth -= 1
            if depth == 0:
                sub = clause[start+1:idx]; break
    else:
        return None
    usub = sub.upper(); sel = usub.find('SELECT')
    d = 0; fpos = None; k = sel + 6
    while k < len(sub):
        if sub[k] == '(': d += 1
        elif sub[k] == ')': d -= 1
        elif d == 0 and usub[k:k+4] == 'FROM' and sub[k-1] in ' \t\n' and sub[k+4] in ' \t\n':
            fpos = k; break
        k += 1
    return sub[sel+6:fpos].strip()

setup()
from django.db.models import Count, Q
from app.models import Author, Book
# rhs explicitly selects the 'name' column
authors = Author.objects.filter(pk=1).values('name')
qs = Book.objects.annotate(Count('authors')).filter(
    Q(authors__in=authors) | Q(authors__count__gt=2)
)
sql = str(qs.query)
clause = groupby_clause(sql)
sl = subquery_select_list(clause)
print("GROUP BY clause:", clause.strip())
assert sl is not None, "expected an __in subquery in GROUP BY"
print("subquery select list:", sl)
low = sl.lower()
assert 'name' in low, "explicit 'name' column was dropped from group-by subquery: %s" % sl
assert '"id"' not in low and '.id' not in low, "subquery was clobbered to pk despite explicit fields: %s" % sl
print("PASS: explicitly-selected rhs columns preserved unchanged in group-by")
sys.exit(0)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""Probe for Req1.4 / Req3.1: IF the rhs of the __in lookup is NOT a subquery
(a plain collection of values), the lookup SHALL contribute only the lhs's
group-by columns and SHALL NOT attempt subquery normalization.
We build an In lookup directly with a plain list rhs, call get_group_by_cols(),
and assert it returns exactly the lhs group-by cols (no crash, no extra cols)."""
import os, sys, tempfile, django

def setup():
    d = tempfile.mkdtemp()
    os.makedirs(os.path.join(d, 'app'))
    open(os.path.join(d, 'app', '__init__.py'), 'w').close()
    with open(os.path.join(d, 'app', 'models.py'), 'w') as f:
        f.write(
            "from django.db import models\n"
            "class Author(models.Model):\n"
            "    name = models.CharField(max_length=50)\n"
            "class Book(models.Model):\n"
            "    title = models.CharField(max_length=50)\n"
            "    authors = models.ManyToManyField(Author, related_name='books')\n"
        )
    sys.path.insert(0, d)
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth', 'app'],
            DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
            DEFAULT_AUTO_FIELD='django.db.models.AutoField',
        )
        django.setup()

setup()
from django.db.models.lookups import In
from app.models import Author

# lhs: a column expression (the pk field of Author)
lhs = Author._meta.pk.get_col('app_author')
rhs = [1, 2, 3]  # plain, non-subquery values
lookup = In(lhs, rhs)
assert not hasattr(rhs, 'get_group_by_cols'), "test setup: rhs must not be a query"

lhs_cols = lhs.get_group_by_cols()
got = lookup.get_group_by_cols()
print("lhs group_by cols:", lhs_cols)
print("In(plain list) group_by cols:", got)
assert got == lhs_cols, "non-subquery __in contributed extra/altered group-by cols: %s vs lhs %s" % (got, lhs_cols)
print("PASS: non-subquery rhs contributes only lhs group-by cols, no normalization")
sys.exit(0)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""Probe for Req3.4: the previously-working single-column form -- a membership
test whose rhs EXPLICITLY selects only the primary key -- SHALL keep producing
a single-column subquery AND correct results, both before and after the change.
Uses .values('pk')/values_list('pk'). HOLDS iff query executes, group-by
subquery has exactly 1 column, and result == {b1, b4}."""
import os, sys, tempfile, django

def setup():
    d = tempfile.mkdtemp()
    os.makedirs(os.path.join(d, 'app'))
    open(os.path.join(d, 'app', '__init__.py'), 'w').close()
    with open(os.path.join(d, 'app', 'models.py'), 'w') as f:
        f.write(
            "from django.db import models\n"
            "class Author(models.Model):\n"
            "    name = models.CharField(max_length=50)\n"
            "class Book(models.Model):\n"
            "    title = models.CharField(max_length=50)\n"
            "    authors = models.ManyToManyField(Author, related_name='books')\n"
        )
    sys.path.insert(0, d)
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth', 'app'],
            DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
            DEFAULT_AUTO_FIELD='django.db.models.AutoField',
        )
        django.setup()

def groupby_clause(sql):
    up = sql.upper(); i = up.find('GROUP BY'); assert i != -1
    tail = sql[i+8:]; utail = tail.upper()
    ends = [utail.find(k) for k in (' HAVING', ' ORDER BY', ' LIMIT') if utail.find(k) != -1]
    return tail[:min(ends)] if ends else tail

def subq_ncols(clause):
    up = clause.upper(); start = None; depth = 0
    for idx, ch in enumerate(clause):
        if ch == '(':
            if depth == 0 and up[idx:idx+7] == '(SELECT':
                start = idx; depth = 1; continue
            if start is not None: depth += 1
        elif ch == ')' and start is not None:
            depth -= 1
            if depth == 0:
                sub = clause[start+1:idx]; break
    else:
        return None
    usub = sub.upper(); sel = usub.find('SELECT')
    d = 0; fpos = None; k = sel + 6
    while k < len(sub):
        if sub[k] == '(': d += 1
        elif sub[k] == ')': d -= 1
        elif d == 0 and usub[k:k+4] == 'FROM' and sub[k-1] in ' \t\n' and sub[k+4] in ' \t\n':
            fpos = k; break
        k += 1
    sl = sub[sel+6:fpos]; d = 0; cols = 1
    for ch in sl:
        if ch == '(': d += 1
        elif ch == ')': d -= 1
        elif ch == ',' and d == 0: cols += 1
    return cols, sl.strip()

setup()
from django.db import connection
from django.db.models import Count, Q
from app.models import Author, Book
with connection.schema_editor() as se:
    se.create_model(Author)
    se.create_model(Book)

a1 = Author.objects.create(name='a1'); a2 = Author.objects.create(name='a2'); a3 = Author.objects.create(name='a3')
b1 = Book.objects.create(title='b1'); b1.authors.add(a1)
b2 = Book.objects.create(title='b2'); b2.authors.add(a2)
b3 = Book.objects.create(title='b3'); b3.authors.add(a2, a3)
b4 = Book.objects.create(title='b4'); b4.authors.add(a1, a2, a3)

# explicit single-column pk form (the "already working" branch)
authors_pk = Author.objects.filter(pk=a1.pk).values_list('pk', flat=True)
qs = Book.objects.annotate(Count('authors')).filter(
    Q(authors__in=authors_pk) | Q(authors__count__gt=2)
)
sql = str(qs.query)
clause = groupby_clause(sql)
res = subq_ncols(clause)
print("GROUP BY clause:", clause.strip())
assert res is not None, "expected an __in subquery in GROUP BY"
ncols, sl = res
print("subquery select list:", sl, "ncols:", ncols)
assert ncols == 1, "explicit-pk form produced %d-column subquery: %s" % (ncols, sl)
got = set(qs)
print("result:", sorted(b.title for b in got))
assert got == {b1, b4}, "explicit-pk form wrong result: %s" % sorted(b.title for b in got)
print("PASS: explicit single-column pk form keeps 1-column subquery and correct rows")
sys.exit(0)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Probe for Req1.1/1.2 (POSITIVE CONTROL): when an __in subquery (no explicit
selected columns) becomes a GROUP BY grouping key, it SHALL be normalized to a
single primary-key column -> the group-by subquery returns exactly ONE column.
HOLDS iff the parenthesised subquery in GROUP BY has exactly 1 select column.
Discriminates: at base it has all default columns (>1)."""
import os, sys, tempfile, django

def setup():
    d = tempfile.mkdtemp()
    os.makedirs(os.path.join(d, 'app'))
    open(os.path.join(d, 'app', '__init__.py'), 'w').close()
    with open(os.path.join(d, 'app', 'models.py'), 'w') as f:
        f.write(
            "from django.db import models\n"
            "class Author(models.Model):\n"
            "    name = models.CharField(max_length=50)\n"
            "class Book(models.Model):\n"
            "    title = models.CharField(max_length=50)\n"
            "    authors = models.ManyToManyField(Author, related_name='books')\n"
        )
    sys.path.insert(0, d)
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth', 'app'],
            DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
            DEFAULT_AUTO_FIELD='django.db.models.AutoField',
        )
        django.setup()

def groupby_clause(sql):
    up = sql.upper()
    i = up.find('GROUP BY')
    assert i != -1, "no GROUP BY in SQL:\n" + sql
    tail = sql[i + len('GROUP BY'):]
    utail = tail.upper()
    ends = [utail.find(k) for k in (' HAVING', ' ORDER BY', ' LIMIT') if utail.find(k) != -1]
    j = min(ends) if ends else len(tail)
    return tail[:j]

def subquery_columns(clause):
    up = clause.upper()
    start = None; depth = 0
    for idx, ch in enumerate(clause):
        if ch == '(':
            if depth == 0 and up[idx:idx + 7] == '(SELECT':
                start = idx; depth = 1; continue
            if start is not None: depth += 1
        elif ch == ')' and start is not None:
            depth -= 1
            if depth == 0:
                sub = clause[start + 1:idx]; break
    else:
        return None
    usub = sub.upper(); sel = usub.find('SELECT')
    d = 0; fpos = None; k = sel + 6
    while k < len(sub):
        if sub[k] == '(': d += 1
        elif sub[k] == ')': d -= 1
        elif d == 0 and usub[k:k+4] == 'FROM' and sub[k-1] in ' \t\n' and sub[k+4] in ' \t\n':
            fpos = k; break
        k += 1
    assert fpos is not None
    sl = sub[sel+6:fpos]; d = 0; cols = 1
    for ch in sl:
        if ch == '(': d += 1
        elif ch == ')': d -= 1
        elif ch == ',' and d == 0: cols += 1
    return cols, sl.strip()

setup()
from django.db.models import Count, Q
from app.models import Author, Book
qs = Book.objects.annotate(Count('authors')).filter(
    Q(authors__in=Author.objects.filter(pk=1)) | Q(authors__count__gt=2)
)
sql = str(qs.query)
clause = groupby_clause(sql)
res = subquery_columns(clause)
print("GROUP BY clause:", clause.strip())
assert res is not None, "expected an __in subquery in GROUP BY but found none"
ncols, sl = res
print("subquery select list:", sl, "=> ncols:", ncols)
assert ncols == 1, "GROUP BY subquery returns %d columns (expected exactly 1): %s" % (ncols, sl)
print("PASS: group-by __in subquery contributes exactly one column")
sys.exit(0)
```

Prepatch bug re-encoded as an attack: `True`.

Instance django__django-14351: In.get_group_by_cols must normalize a no-explicit-select __in subquery to its single pk column when it becomes a GROUP BY grouping key.

Probe suite (all standalone, sqlite in-memory + m2m Author/Book models; runner re-runs):
- probe_1 (POSITIVE CONTROL, Req1.1/1.2): parses the GROUP BY clause and counts columns in the parenthesised __in subquery. HOLDS patched (1 col: U0."id"), FAILS at base (2 cols: U0."id", U0."name") -> discriminates. prepatch_reproduced=true.
- probe_2 (Req2.1/2.2): real data (b1 by a1; b4 by a1,a2,a3), executes Q(authors__in=Author.filter(pk=a1))|Q(authors__count__gt=2). HOLDS patched (returns {b1,b4}); at base raises OperationalError 'sub-select returns 2 columns - expected 1'.
- probe_3 (Req1.3): rhs = .values('name') (explicit non-pk column). HOLDS patched (subquery keeps U0."name", not clobbered to id).
- probe_4 (Req1.4/3.1): direct In(lhs, [1,2,3]) with plain-list rhs; get_group_by_cols() returns exactly lhs cols, no normalization/crash. HOLDS.
- probe_5 (Req3.4): explicit .values_list('pk') form keeps 1-column subquery AND returns {b1,b4}. HOLDS.

Discriminating power on wrong fixes:
- weak.diff (always clear_select_clause+add pk, ignoring has_select_fields): REJECTED by probe_3 (clobbers explicit 'name' -> id).
- weak2.diff (return only lhs cols; drop rhs from group-by entirely): REJECTED by probe_1, probe_3, probe_5 (no __in subquery appears in GROUP BY). Note weak2 still passes probe_2/probe_4, but the suite as a whole rejects it.

Note: signal is the SQL column count in the group-by subquery, since sqlite (test DB) tolerates multi-column subqueries and would not raise at base for probe_1; probe_2 does surface the runtime error at base on sqlite. No requirements-conforming alternative patch found that would fail the hidden tests; both plausible wrong fixes are caught. Verdict SOUND: >=5 distinct probes hold on the patched tree, positive control discriminates base vs patched, and >=1 wrong candidate exercised and rejected (two, in fact).

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
"""Probe for Req1.1/1.2 (POSITIVE CONTROL): when an __in subquery (no explicit
selected columns) becomes a GROUP BY grouping key, it SHALL be normalized to a
single primary-key column -> the group-by subquery returns exactly ONE column.
HOLDS iff the parenthesised subquery in GROUP BY has exactly 1 select column.
Discriminates: at base it has all default columns (>1)."""
import os, sys, tempfile, django

def setup():
    d = tempfile.mkdtemp()
    os.makedirs(os.path.join(d, 'app'))
    open(os.path.join(d, 'app', '__init__.py'), 'w').close()
    with open(os.path.join(d, 'app', 'models.py'), 'w') as f:
        f.write(
            "from django.db import models\n"
            "class Author(models.Model):\n"
            "    name = models.CharField(max_length=50)\n"
            "class Book(models.Model):\n"
            "    title = models.CharField(max_length=50)\n"
            "    authors = models.ManyToManyField(Author, related_name='books')\n"
        )
    sys.path.insert(0, d)
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth', 'app'],
            DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
            DEFAULT_AUTO_FIELD='django.db.models.AutoField',
        )
        django.setup()

def groupby_clause(sql):
    up = sql.upper()
    i = up.find('GROUP BY')
    assert i != -1, "no GROUP BY in SQL:\n" + sql
    tail = sql[i + len('GROUP BY'):]
    utail = tail.upper()
    ends = [utail.find(k) for k in (' HAVING', ' ORDER BY', ' LIMIT') if utail.find(k) != -1]
    j = min(ends) if ends else len(tail)
    return tail[:j]

def subquery_columns(clause):
    up = clause.upper()
    start = None; depth = 0
    for idx, ch in enumerate(clause):
        if ch == '(':
            if depth == 0 and up[idx:idx + 7] == '(SELECT':
                start = idx; depth = 1; continue
            if start is not None: depth += 1
        elif ch == ')' and start is not None:
            depth -= 1
            if depth == 0:
                sub = clause[start + 1:idx]; break
    else:
        return None
    usub = sub.upper(); sel = usub.find('SELECT')
    d = 0; fpos = None; k = sel + 6
    while k < len(sub):
        if sub[k] == '(': d += 1
        elif sub[k] == ')': d -= 1
        elif d == 0 and usub[k:k+4] == 'FROM' and sub[k-1] in ' \t\n' and sub[k+4] in ' \t\n':
            fpos = k; break
        k += 1
    assert fpos is not None
    sl = sub[sel+6:fpos]; d = 0; cols = 1
    for ch in sl:
        if ch == '(': d += 1
        elif ch == ')': d -= 1
        elif ch == ',' and d == 0: cols += 1
    return cols, sl.strip()

setup()
from django.db.models import Count, Q
from app.models import Author, Book
qs = Book.objects.annotate(Count('authors')).filter(
    Q(authors__in=Author.objects.filter(pk=1)) | Q(authors__count__gt=2)
)
sql = str(qs.query)
clause = groupby_clause(sql)
res = subquery_columns(clause)
print("GROUP BY clause:", clause.strip())
assert res is not None, "expected an __in subquery in GROUP BY but found none"
ncols, sl = res
print("subquery select list:", sl, "=> ncols:", ncols)
assert ncols == 1, "GROUP BY subquery returns %d columns (expected exactly 1): %s" % (ncols, sl)
print("PASS: group-by __in subquery contributes exactly one column")
sys.exit(0)
```

Prepatch bug re-encoded as an attack: `True`.

Instance django__django-14351: In.get_group_by_cols must normalize a no-explicit-select __in subquery to its single pk column when it becomes a GROUP BY grouping key.

Probe suite (all standalone, sqlite in-memory + m2m Author/Book models; runner re-runs):
- probe_1 (POSITIVE CONTROL, Req1.1/1.2): parses the GROUP BY clause and counts columns in the parenthesised __in subquery. HOLDS patched (1 col: U0."id"), FAILS at base (2 cols: U0."id", U0."name") -> discriminates. prepatch_reproduced=true.
- probe_2 (Req2.1/2.2): real data (b1 by a1; b4 by a1,a2,a3), executes Q(authors__in=Author.filter(pk=a1))|Q(authors__count__gt=2). HOLDS patched (returns {b1,b4}); at base raises OperationalError 'sub-select returns 2 columns - expected 1'.
- probe_3 (Req1.3): rhs = .values('name') (explicit non-pk column). HOLDS patched (subquery keeps U0."name", not clobbered to id).
- probe_4 (Req1.4/3.1): direct In(lhs, [1,2,3]) with plain-list rhs; get_group_by_cols() returns exactly lhs cols, no normalization/crash. HOLDS.
- probe_5 (Req3.4): explicit .values_list('pk') form keeps 1-column subquery AND returns {b1,b4}. HOLDS.

Discriminating power on wrong fixes:
- weak.diff (always clear_select_clause+add pk, ignoring has_select_fields): REJECTED by probe_3 (clobbers explicit 'name' -> id).
- weak2.diff (return only lhs cols; drop rhs from group-by entirely): REJECTED by probe_1, probe_3, probe_5 (no __in subquery appears in GROUP BY). Note weak2 still passes probe_2/probe_4, but the suite as a whole rejects it.

Note: signal is the SQL column count in the group-by subquery, since sqlite (test DB) tolerates multi-column subqueries and would not raise at base for probe_1; probe_2 does surface the runtime error at base on sqlite. No requirements-conforming alternative patch found that would fail the hidden tests; both plausible wrong fixes are caught. Verdict SOUND: >=5 distinct probes hold on the patched tree, positive control discriminates base vs patched, and >=1 wrong candidate exercised and rejected (two, in fact).

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Verified with probes in the instance image. Patched tree: In.get_group_by_cols exists and contains clear_select_clause + add_fields(['pk']) gated on 'not has_select_fields' and on hasattr(rhs,'get_group_by_cols'). Base tree (--base): method/normalization absent (AssertionError), confirming the patch is exactly what introduces the behavior. Modeling boundary is pinned at the changed observable behavior (the added method), not a narrow slice; Req2's observable (OR of __in subquery filter with aggregate filter executing without ProgrammingError, returning correct rows) matches the F2P test_having_subquery_select and the issue's report.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Requirements localize the fix to django/db/models/lookups.py / the In lookup / process_rhs and describe the single-pk-column GROUP BY normalization — all derivable from the public problem_statement (which already shows the failing SQL, the 'subquery must return only one column' error, the OR of an __in subquery with an aggregate count condition, and the pk-only vs all-columns difference). No hidden-test/gold content transmitted: the gold-invented identifiers (get_group_by_cols, has_select_fields, clear_select_clause, add_fields(['pk'])) are NOT named — behavior is described instead ('a separate, inherited code path', 'normalize ... single primary-key column'). None of the hidden test specifics appear: no test name/path (test_having_subquery_select), no Author/Book models, no Count('authors'), no __count__gt=2 threshold, no expected {b1,b4} result set, no skipUnlessDBFeature feature id. Acceptance criteria are generic behavioral translations, not case enumerations mirroring the test.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
