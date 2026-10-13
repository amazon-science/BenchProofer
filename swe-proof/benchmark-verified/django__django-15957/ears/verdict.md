# P2 adversarial audit — django__django-15957

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
"""Probe 1 (POSITIVE CONTROL) — Requirement 1 (crit 1,2,4).
Sliced reverse-FK prefetch must (a) NOT raise "Cannot filter ... slice",
and (b) give each parent the per-parent window authors[1:] (offset 1, no
upper bound => drop the first related object of each parent's group, in the
queryset's ordering). HOLDS on patched, must FAIL at base (base raises).
"""
import django
from django.conf import settings

settings.configure(
    DEBUG=True,
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth", "probeapp"],
    DEFAULT_AUTO_FIELD="django.db.models.AutoField",
)
import sys, types
app = types.ModuleType("probeapp")
app.__file__ = "/work/probeapp.py"
app.__path__ = ["/work"]
sys.modules["probeapp"] = app
django.setup()

from django.db import models, connection

class Author(models.Model):
    name = models.CharField(max_length=100)
    fav_book = models.ForeignKey("Book", null=True, related_name="fans",
                                 on_delete=models.CASCADE)
    class Meta:
        app_label = "probeapp"
        ordering = ["name"]

class Book(models.Model):
    title = models.CharField(max_length=100)
    authors = models.ManyToManyField(Author, related_name="books")
    class Meta:
        app_label = "probeapp"
        ordering = ["title"]

with connection.schema_editor() as se:
    se.create_model(Author)
    se.create_model(Book)

from django.db.models import Prefetch

b1 = Book.objects.create(title="B1")
b2 = Book.objects.create(title="B2")
# authors whose fav_book is b1: names deliberately unsorted at insert time
for nm in ["c_auth", "a_auth", "b_auth"]:
    Author.objects.create(name=nm, fav_book=b1)
for nm in ["z_auth", "y_auth"]:
    Author.objects.create(name=nm, fav_book=b2)

authors = Author.objects.order_by("-name")  # explicit ordering
try:
    books = list(
        Book.objects.prefetch_related(
            Prefetch("fans", authors),
            Prefetch("fans", authors[1:], to_attr="fans_sliced"),
        )
    )
except Exception as e:
    print("FAIL: prefetch raised:", type(e).__name__, e)
    sys.exit(1)

ok = True
for book in books:
    full = list(book.fans.all())
    expected = full[1:]
    got = book.fans_sliced
    print(f"book={book.title} full={[a.name for a in full]} "
          f"expected={[a.name for a in expected]} got={[a.name for a in got]}")
    if got != expected:
        ok = False

sys.exit(0 if ok else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""Probe 2 — Requirement 2 crit 1 (M2M FORWARD sliced prefetch).
Book.prefetch_related(Prefetch("authors", authors[1:], to_attr=...)) must
complete without error and give each book its authors[1:] window (offset 1,
no upper bound) in the queryset ordering.
"""
import django
from django.conf import settings
settings.configure(
    DEBUG=True,
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth", "probeapp"],
    DEFAULT_AUTO_FIELD="django.db.models.AutoField",
)
import sys, types
app = types.ModuleType("probeapp")
app.__file__ = "/work/probeapp.py"; app.__path__ = ["/work"]
sys.modules["probeapp"] = app
django.setup()
from django.db import models, connection

class Author(models.Model):
    name = models.CharField(max_length=100)
    class Meta:
        app_label = "probeapp"; ordering = ["name"]

class Book(models.Model):
    title = models.CharField(max_length=100)
    authors = models.ManyToManyField(Author, related_name="books")
    class Meta:
        app_label = "probeapp"; ordering = ["title"]

with connection.schema_editor() as se:
    se.create_model(Author); se.create_model(Book)

from django.db.models import Prefetch
a = {n: Author.objects.create(name=n) for n in ["a1","a2","a3","a4"]}
b1 = Book.objects.create(title="B1"); b1.authors.add(a["a1"], a["a2"], a["a3"])
b2 = Book.objects.create(title="B2"); b2.authors.add(a["a4"], a["a2"])

authors = Author.objects.all()  # Meta.ordering by name
try:
    books = list(Book.objects.prefetch_related(
        Prefetch("authors", authors),
        Prefetch("authors", authors[1:], to_attr="authors_sliced"),
    ))
except Exception as e:
    print("FAIL: prefetch raised:", type(e).__name__, e); sys.exit(1)

ok = True
for book in books:
    full = list(book.authors.all()); expected = full[1:]; got = book.authors_sliced
    print(f"book={book.title} full={[x.name for x in full]} "
          f"expected={[x.name for x in expected]} got={[x.name for x in got]}")
    if got != expected: ok = False
sys.exit(0 if ok else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""Probe 3 — Requirement 2 crit 2/3 (M2M REVERSE sliced prefetch) with an
UPPER BOUND slice books[1:2]. Author.prefetch_related over reverse m2m
"books" with slice [1:2] must complete without error and give each author
exactly its books[1:2] window (offset lower bound 1, upper bound 2 as
absolute within-group positions). Exercises Requirement 1 crit 5 + Req 4
crit 2 (upper bound applied in addition to membership).
"""
import django
from django.conf import settings
settings.configure(
    DEBUG=True,
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth", "probeapp"],
    DEFAULT_AUTO_FIELD="django.db.models.AutoField",
)
import sys, types
app = types.ModuleType("probeapp")
app.__file__ = "/work/probeapp.py"; app.__path__ = ["/work"]
sys.modules["probeapp"] = app
django.setup()
from django.db import models, connection

class Author(models.Model):
    name = models.CharField(max_length=100)
    class Meta:
        app_label = "probeapp"; ordering = ["name"]

class Book(models.Model):
    title = models.CharField(max_length=100)
    authors = models.ManyToManyField(Author, related_name="books")
    class Meta:
        app_label = "probeapp"; ordering = ["title"]

with connection.schema_editor() as se:
    se.create_model(Author); se.create_model(Book)

from django.db.models import Prefetch
au = {n: Author.objects.create(name=n) for n in ["a1","a2"]}
# a1 has 4 books, a2 has 3 books
for t in ["t1","t2","t3","t4"]:
    Book.objects.create(title=t).authors.add(au["a1"])
for t in ["u1","u2","u3"]:
    Book.objects.create(title=t).authors.add(au["a2"])

books = Book.objects.order_by("title")
try:
    authors = list(Author.objects.prefetch_related(
        Prefetch("books", books),
        Prefetch("books", books[1:2], to_attr="books_sliced"),
    ))
except Exception as e:
    print("FAIL: prefetch raised:", type(e).__name__, e); sys.exit(1)

ok = True
for author in authors:
    full = list(author.books.all()); expected = full[1:2]; got = author.books_sliced
    print(f"author={author.name} full={[x.title for x in full]} "
          f"expected={[x.title for x in expected]} got={[x.title for x in got]}")
    if got != expected: ok = False
sys.exit(0 if ok else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""Probe 4 — Requirement 3 (per-parent slice respects ordering; reversed
ordering takes the window from the opposite end). Same slice [1:] applied
under normal ordering vs reversed ordering must produce DIFFERENT kept sets,
each equal to the corresponding full[1:]. This pins that position is by the
queryset ordering, not insertion order.
"""
import django
from django.conf import settings
settings.configure(
    DEBUG=True,
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth", "probeapp"],
    DEFAULT_AUTO_FIELD="django.db.models.AutoField",
)
import sys, types
app = types.ModuleType("probeapp")
app.__file__ = "/work/probeapp.py"; app.__path__ = ["/work"]
sys.modules["probeapp"] = app
django.setup()
from django.db import models, connection

class Author(models.Model):
    name = models.CharField(max_length=100)
    class Meta:
        app_label = "probeapp"; ordering = ["name"]

class Book(models.Model):
    title = models.CharField(max_length=100)
    authors = models.ManyToManyField(Author, related_name="books")
    class Meta:
        app_label = "probeapp"; ordering = ["title"]

with connection.schema_editor() as se:
    se.create_model(Author); se.create_model(Book)

from django.db.models import Prefetch
a = {n: Author.objects.create(name=n) for n in ["a1","a2","a3"]}
b1 = Book.objects.create(title="B1"); b1.authors.add(a["a1"], a["a2"], a["a3"])

def sliced_names(qs):
    book = list(Book.objects.prefetch_related(
        Prefetch("authors", qs[1:], to_attr="s")))[0]
    return [x.name for x in book.s]

fwd = sliced_names(Author.objects.order_by("name"))   # full=a1,a2,a3 -> [a2,a3]
rev = sliced_names(Author.objects.order_by("-name"))  # full=a3,a2,a1 -> [a2,a1]
print("forward slice[1:] =", fwd)
print("reverse slice[1:] =", rev)
ok = (fwd == ["a2","a3"] and rev == ["a2","a1"] and fwd != rev)
if not ok:
    print("FAIL: ordering not respected")
sys.exit(0 if ok else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""Probe 5 — Requirement 4 (membership always applied; per-parent conditions
in ADDITION to membership). With a slice present, every related object kept
for a parent must actually belong to that parent (never leak objects from
other parents), AND the kept set must be exactly the parent's own full[1:]
(a subset of that parent's group). Uses reverse-FK with several parents each
owning disjoint groups.
"""
import django
from django.conf import settings
settings.configure(
    DEBUG=True,
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth", "probeapp"],
    DEFAULT_AUTO_FIELD="django.db.models.AutoField",
)
import sys, types
app = types.ModuleType("probeapp")
app.__file__ = "/work/probeapp.py"; app.__path__ = ["/work"]
sys.modules["probeapp"] = app
django.setup()
from django.db import models, connection

class Book(models.Model):
    title = models.CharField(max_length=100)
    class Meta:
        app_label = "probeapp"; ordering = ["title"]

class Author(models.Model):
    name = models.CharField(max_length=100)
    fav_book = models.ForeignKey(Book, null=True, related_name="fans",
                                 on_delete=models.CASCADE)
    class Meta:
        app_label = "probeapp"; ordering = ["name"]

with connection.schema_editor() as se:
    se.create_model(Book); se.create_model(Author)

from django.db.models import Prefetch
books = {}
# 3 parents, each with 3 fans; names globally overlap-free so leakage is visible
for i in range(3):
    bk = Book.objects.create(title=f"B{i}")
    books[bk.id] = set()
    for j in range(3):
        au = Author.objects.create(name=f"b{i}_a{j}", fav_book=bk)
        books[bk.id].add(au.name)

authors = Author.objects.order_by("name")
result = list(Book.objects.prefetch_related(
    Prefetch("fans", authors[1:], to_attr="fans_sliced")))

ok = True
for bk in result:
    got = set(x.name for x in bk.fans_sliced)
    own = books[bk.id]
    # membership: sliced set must be subset of this parent's own group
    leaked = got - own
    # correctness: exactly own full[1:]
    own_sorted = sorted(own)
    expected = set(own_sorted[1:])
    print(f"book={bk.title} own={own_sorted} got={sorted(got)} "
          f"expected={sorted(expected)} leaked={sorted(leaked)}")
    if leaked or got != expected:
        ok = False
sys.exit(0 if ok else 1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
"""Probe 6 — Requirement 5 (UNSLICED prefetch preserved / regression).
An unsliced caller queryset must prefetch ALL related objects per parent
(reverse-FK and m2m forward+reverse), with correct parent association, and
in a single prefetch query per relation (no per-parent window added). Also
checks that unsliced prefetch still works and returns full groups.
"""
import django
from django.conf import settings
settings.configure(
    DEBUG=True,
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth", "probeapp"],
    DEFAULT_AUTO_FIELD="django.db.models.AutoField",
)
import sys, types
app = types.ModuleType("probeapp")
app.__file__ = "/work/probeapp.py"; app.__path__ = ["/work"]
sys.modules["probeapp"] = app
django.setup()
from django.db import models, connection, reset_queries
from django.test.utils import CaptureQueriesContext

class Author(models.Model):
    name = models.CharField(max_length=100)
    fav_book = models.ForeignKey("Book", null=True, related_name="fans",
                                 on_delete=models.CASCADE)
    class Meta:
        app_label = "probeapp"; ordering = ["name"]

class Book(models.Model):
    title = models.CharField(max_length=100)
    authors = models.ManyToManyField(Author, related_name="books")
    class Meta:
        app_label = "probeapp"; ordering = ["title"]

with connection.schema_editor() as se:
    se.create_model(Author); se.create_model(Book)

from django.db.models import Prefetch
b1 = Book.objects.create(title="B1"); b2 = Book.objects.create(title="B2")
a1 = Author.objects.create(name="a1", fav_book=b1)
a2 = Author.objects.create(name="a2", fav_book=b1)
a3 = Author.objects.create(name="a3", fav_book=b2)
b1.authors.add(a1, a2); b2.authors.add(a3, a1)

ok = True

# reverse-FK unsliced -> all fans
books = list(Book.objects.prefetch_related("fans"))
by = {b.title: [x.name for x in b.fans.all()] for b in books}
print("reverse-FK unsliced:", by)
if by != {"B1": ["a1","a2"], "B2": ["a3"]}: ok = False

# m2m forward unsliced -> all authors
books = list(Book.objects.prefetch_related("authors"))
by = {b.title: [x.name for x in b.authors.all()] for b in books}
print("m2m forward unsliced:", by)
if by != {"B1": ["a1","a2"], "B2": ["a1","a3"]}: ok = False

# m2m reverse unsliced -> all books
authors = list(Author.objects.prefetch_related("books"))
by = {a.name: [x.title for x in a.books.all()] for a in authors}
print("m2m reverse unsliced:", by)
if by != {"a1": ["B1","B2"], "a2": ["B1"], "a3": ["B2"]}: ok = False

# no per-parent window added: unsliced m2m forward prefetch is exactly 2 queries
with CaptureQueriesContext(connection) as ctx:
    list(Book.objects.prefetch_related("authors"))
nq = len(ctx.captured_queries)
print("unsliced m2m forward query count:", nq)
if nq != 2: ok = False

sys.exit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Probe 1 (POSITIVE CONTROL) — Requirement 1 (crit 1,2,4).
Sliced reverse-FK prefetch must (a) NOT raise "Cannot filter ... slice",
and (b) give each parent the per-parent window authors[1:] (offset 1, no
upper bound => drop the first related object of each parent's group, in the
queryset's ordering). HOLDS on patched, must FAIL at base (base raises).
"""
import django
from django.conf import settings

settings.configure(
    DEBUG=True,
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth", "probeapp"],
    DEFAULT_AUTO_FIELD="django.db.models.AutoField",
)
import sys, types
app = types.ModuleType("probeapp")
app.__file__ = "/work/probeapp.py"
app.__path__ = ["/work"]
sys.modules["probeapp"] = app
django.setup()

from django.db import models, connection

class Author(models.Model):
    name = models.CharField(max_length=100)
    fav_book = models.ForeignKey("Book", null=True, related_name="fans",
                                 on_delete=models.CASCADE)
    class Meta:
        app_label = "probeapp"
        ordering = ["name"]

class Book(models.Model):
    title = models.CharField(max_length=100)
    authors = models.ManyToManyField(Author, related_name="books")
    class Meta:
        app_label = "probeapp"
        ordering = ["title"]

with connection.schema_editor() as se:
    se.create_model(Author)
    se.create_model(Book)

from django.db.models import Prefetch

b1 = Book.objects.create(title="B1")
b2 = Book.objects.create(title="B2")
# authors whose fav_book is b1: names deliberately unsorted at insert time
for nm in ["c_auth", "a_auth", "b_auth"]:
    Author.objects.create(name=nm, fav_book=b1)
for nm in ["z_auth", "y_auth"]:
    Author.objects.create(name=nm, fav_book=b2)

authors = Author.objects.order_by("-name")  # explicit ordering
try:
    books = list(
        Book.objects.prefetch_related(
            Prefetch("fans", authors),
            Prefetch("fans", authors[1:], to_attr="fans_sliced"),
        )
    )
except Exception as e:
    print("FAIL: prefetch raised:", type(e).__name__, e)
    sys.exit(1)

ok = True
for book in books:
    full = list(book.fans.all())
    expected = full[1:]
    got = book.fans_sliced
    print(f"book={book.title} full={[a.name for a in full]} "
          f"expected={[a.name for a in expected]} got={[a.name for a in got]}")
    if got != expected:
        ok = False

sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance django__django-15957: support sliced querysets in prefetch_related. Gold patch adds _filter_prefetch_queryset which, when the caller queryset is sliced, replaces the plain slice with a per-parent RowNumber() Window (partition_by=grouping field, order_by=queryset ordering) bounded by GreaterThan(low_mark) and LessThanOrEqual(high_mark), clears limits, and always ANDs the membership Q(field__in=instances). Applied to reverse-FK manager and the m2m manager (forward+reverse).

Probes (all run in the official image via nl_attack; all HOLD on the gold-patched tree):
- probe_1 (POSITIVE CONTROL, Req1 crit 1/2/4): sliced reverse-FK prefetch authors[1:] with order_by('-name'). HOLDS patched (window == full[1:] per parent, no error); FAILS at base with TypeError 'Cannot filter a query once a slice has been taken.' => prepatch_reproduced=true, discriminating.
- probe_2 (Req2 crit1): m2m FORWARD sliced [1:] -> each book gets authors[1:]. HOLDS.
- probe_3 (Req2 crit2/3 + Req1 crit5 upper bound): m2m REVERSE slice [1:2] -> each author gets exactly books[1:2] (both bounds absolute per group). HOLDS.
- probe_4 (Req3 ordering): slice [1:] under order_by('name') vs order_by('-name') yields different, correctly-ordered windows ([a2,a3] vs [a2,a1]). HOLDS.
- probe_5 (Req4 membership always applied): 3 reverse-FK parents each with disjoint fan groups; sliced set is a subset of the parent's own group (no leakage) AND equals own full[1:]. HOLDS.
- probe_6 (Req5 regression, unsliced preserved): reverse-FK + m2m fwd + m2m rev unsliced prefetch returns ALL related objects with correct parent association; unsliced m2m forward = exactly 2 queries (no per-parent window added). HOLDS.

Candidate wrong patch (REQUIRED floor met):
- weak_dropslice.diff: the lazy fix a weak reading permits — on a sliced queryset it merely calls queryset.query.clear_limits() and applies the membership filter, dropping the requested window so ALL related objects are kept. Applies cleanly at base_commit. My suite REJECTS it: probe_1 VIOLATED (got full group instead of [1:]), probe_2 VIOLATED, probe_3 VIOLATED, probe_4 VIOLATED (ordering irrelevant since nothing sliced), probe_5 VIOLATED (got own full group not full[1:]). probe_6 correctly still HOLDS (unsliced behavior unchanged). This demonstrates the suite discriminates a requirements-plausible wrong implementation, so it is NOT reported as too-weak. It would also fail the hidden F2P tests (test_m2m_forward/reverse, test_foreignkey_reverse, test_reverse_ordering all assert the [1:]/[1:2] windows).

Verdict SOUND: >=5 distinct probes all hold on the patched tree; positive control discriminates (holds patched, fails base); >=1 candidate exercised and REJECTED. No probe fails on the patched tree and no probe-conforming alternative patch was found.

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
"""Probe 1 (POSITIVE CONTROL) — Requirement 1 (crit 1,2,4).
Sliced reverse-FK prefetch must (a) NOT raise "Cannot filter ... slice",
and (b) give each parent the per-parent window authors[1:] (offset 1, no
upper bound => drop the first related object of each parent's group, in the
queryset's ordering). HOLDS on patched, must FAIL at base (base raises).
"""
import django
from django.conf import settings

settings.configure(
    DEBUG=True,
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth", "probeapp"],
    DEFAULT_AUTO_FIELD="django.db.models.AutoField",
)
import sys, types
app = types.ModuleType("probeapp")
app.__file__ = "/work/probeapp.py"
app.__path__ = ["/work"]
sys.modules["probeapp"] = app
django.setup()

from django.db import models, connection

class Author(models.Model):
    name = models.CharField(max_length=100)
    fav_book = models.ForeignKey("Book", null=True, related_name="fans",
                                 on_delete=models.CASCADE)
    class Meta:
        app_label = "probeapp"
        ordering = ["name"]

class Book(models.Model):
    title = models.CharField(max_length=100)
    authors = models.ManyToManyField(Author, related_name="books")
    class Meta:
        app_label = "probeapp"
        ordering = ["title"]

with connection.schema_editor() as se:
    se.create_model(Author)
    se.create_model(Book)

from django.db.models import Prefetch

b1 = Book.objects.create(title="B1")
b2 = Book.objects.create(title="B2")
# authors whose fav_book is b1: names deliberately unsorted at insert time
for nm in ["c_auth", "a_auth", "b_auth"]:
    Author.objects.create(name=nm, fav_book=b1)
for nm in ["z_auth", "y_auth"]:
    Author.objects.create(name=nm, fav_book=b2)

authors = Author.objects.order_by("-name")  # explicit ordering
try:
    books = list(
        Book.objects.prefetch_related(
            Prefetch("fans", authors),
            Prefetch("fans", authors[1:], to_attr="fans_sliced"),
        )
    )
except Exception as e:
    print("FAIL: prefetch raised:", type(e).__name__, e)
    sys.exit(1)

ok = True
for book in books:
    full = list(book.fans.all())
    expected = full[1:]
    got = book.fans_sliced
    print(f"book={book.title} full={[a.name for a in full]} "
          f"expected={[a.name for a in expected]} got={[a.name for a in got]}")
    if got != expected:
        ok = False

sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance django__django-15957: support sliced querysets in prefetch_related. Gold patch adds _filter_prefetch_queryset which, when the caller queryset is sliced, replaces the plain slice with a per-parent RowNumber() Window (partition_by=grouping field, order_by=queryset ordering) bounded by GreaterThan(low_mark) and LessThanOrEqual(high_mark), clears limits, and always ANDs the membership Q(field__in=instances). Applied to reverse-FK manager and the m2m manager (forward+reverse).

Probes (all run in the official image via nl_attack; all HOLD on the gold-patched tree):
- probe_1 (POSITIVE CONTROL, Req1 crit 1/2/4): sliced reverse-FK prefetch authors[1:] with order_by('-name'). HOLDS patched (window == full[1:] per parent, no error); FAILS at base with TypeError 'Cannot filter a query once a slice has been taken.' => prepatch_reproduced=true, discriminating.
- probe_2 (Req2 crit1): m2m FORWARD sliced [1:] -> each book gets authors[1:]. HOLDS.
- probe_3 (Req2 crit2/3 + Req1 crit5 upper bound): m2m REVERSE slice [1:2] -> each author gets exactly books[1:2] (both bounds absolute per group). HOLDS.
- probe_4 (Req3 ordering): slice [1:] under order_by('name') vs order_by('-name') yields different, correctly-ordered windows ([a2,a3] vs [a2,a1]). HOLDS.
- probe_5 (Req4 membership always applied): 3 reverse-FK parents each with disjoint fan groups; sliced set is a subset of the parent's own group (no leakage) AND equals own full[1:]. HOLDS.
- probe_6 (Req5 regression, unsliced preserved): reverse-FK + m2m fwd + m2m rev unsliced prefetch returns ALL related objects with correct parent association; unsliced m2m forward = exactly 2 queries (no per-parent window added). HOLDS.

Candidate wrong patch (REQUIRED floor met):
- weak_dropslice.diff: the lazy fix a weak reading permits — on a sliced queryset it merely calls queryset.query.clear_limits() and applies the membership filter, dropping the requested window so ALL related objects are kept. Applies cleanly at base_commit. My suite REJECTS it: probe_1 VIOLATED (got full group instead of [1:]), probe_2 VIOLATED, probe_3 VIOLATED, probe_4 VIOLATED (ordering irrelevant since nothing sliced), probe_5 VIOLATED (got own full group not full[1:]). probe_6 correctly still HOLDS (unsliced behavior unchanged). This demonstrates the suite discriminates a requirements-plausible wrong implementation, so it is NOT reported as too-weak. It would also fail the hidden F2P tests (test_m2m_forward/reverse, test_foreignkey_reverse, test_reverse_ordering all assert the [1:]/[1:2] windows).

Verdict SOUND: >=5 distinct probes all hold on the patched tree; positive control discriminates (holds patched, fails base); >=1 candidate exercised and REJECTED. No probe fails on the patched tree and no probe-conforming alternative patch was found.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Gold patch adds _filter_prefetch_queryset: predicate = Q(field__in=instances); if is_sliced, builds Window(RowNumber(), partition_by=field, order_by=get_order_by()), adds GreaterThan(window, low_mark) and (if high_mark) LessThanOrEqual(window, high_mark), then clear_limits(); returns queryset.filter(predicate). Requirements pin the CHANGED observable behavior (per-parent window via RowNumber, membership always applied, limits cleared, unsliced unchanged) rather than a narrow slice. Modeling boundary is correct — covers reverse-FK and both M2M directions (the two edited get_prefetch_queryset call sites). Req1.3 wording 'both as absolute positions' correctly reflects window compared to low_mark/high_mark. Requirements do not over-mandate implementation details (e.g. don't forbid other refactors), don't forbid behavior the code has, and don't invent behavior. Probes: FK slices, M2M fwd/rev, ordering-reversal, unsliced, and base-fails all confirmed via nl_attack probe / --base.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** requirements.md describes the sliced-prefetch feature behaviorally and localizes only to real, pre-existing symbols (module related_descriptors.py; the reverse-FK and m2m related managers' get_prefetch_queryset methods) — legitimate localization required by the spec. No hidden-test content is transmitted: none of the test class/function names (PrefetchLimitTests, test_m2m_forward/reverse, test_foreignkey_reverse, test_reverse_ordering), the to_attr identifiers, assertNumQueries(3), or the concrete slice inputs ([1:], [1:2]) appear. No gold/fix-invented identifiers leak either (Window, RowNumber, partition_by, RowNumber, GreaterThan/LessThanOrEqual, low_mark/high_mark, clear_limits, _filter_prefetch_queryset) — the prose ("per-parent window", "within-group position", "remove plain slice bounds") states behavior, not implementation names. The Req 1/2/3 breakdown (reverse FK, m2m forward, m2m reverse, reversed ordering) tracks genuine behavioral axes: reverse FK is public in problem_statement (post_set example), and m2m directions + ordering-sensitivity are natural consequences of the feature, not a mirror of parametrized test inputs. This is exactly the intended translation of test-checked behavior into requirements, not transmission of the tests.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
