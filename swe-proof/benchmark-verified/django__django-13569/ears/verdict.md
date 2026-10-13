# P2 adversarial audit — django__django-13569

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 6 requirement probes hold on the patched tree; 2/2 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 6 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 6 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 2 alternative candidate patches, claimed to satisfy every cited requirement, and ran the same suite against them. The suite rejected all 2: a probe encoding a cited requirement fails under each of those, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (6):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
# Requirement 1.1 & 1.2 (positive control): Random.get_group_by_cols returns empty, with or without alias
import django
from django.conf import settings
if not settings.configured:
    settings.configure(DATABASES={'default': {'ENGINE':'django.db.backends.sqlite3','NAME':':memory:'}}, INSTALLED_APPS=[])
django.setup()
from django.db.models.functions import Random
r = Random()
c1 = r.get_group_by_cols()
c2 = r.get_group_by_cols(alias='foo')
print("no-alias:", repr(c1))
print("with-alias:", repr(c2))
ok = (list(c1) == []) and (list(c2) == [])
print("OK" if ok else "FAIL")
raise SystemExit(0 if ok else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
import django, sys, types, tempfile
from django.conf import settings
if not settings.configured:
    settings.configure(
        DATABASES={'default': {'ENGINE':'django.db.backends.sqlite3','NAME':':memory:'}},
        INSTALLED_APPS=['testapp'],
        DEFAULT_AUTO_FIELD='django.db.models.AutoField',
    )
app = types.ModuleType('testapp'); app.__path__ = [tempfile.mkdtemp()]
sys.modules['testapp'] = app
django.setup()
from django.db import models, connection

class Author(models.Model):
    name = models.CharField(max_length=50)
    class Meta: app_label = 'testapp'

class Book(models.Model):
    author = models.ForeignKey(Author, on_delete=models.CASCADE, related_name='books')
    title = models.CharField(max_length=50)
    class Meta: app_label = 'testapp'

def setup_db():
    with connection.schema_editor() as se:
        se.create_model(Author); se.create_model(Book)
    a1 = Author.objects.create(name='a1')
    a2 = Author.objects.create(name='a2')
    Book.objects.create(author=a1, title='b1')
    Book.objects.create(author=a1, title='b2')
    Book.objects.create(author=a1, title='b3')
    Book.objects.create(author=a2, title='b4')
    return a1, a2
from django.db.models import Count
setup_db()
qs = Author.objects.annotate(rc=Count('books')).order_by('?')
sql, params = qs.query.sql_with_params()
print("SQL:", sql)
up=sql.upper()
gb = up.split("GROUP BY",1)[1] if "GROUP BY" in up else ""
# strip trailing ORDER BY so the RAND() in ORDER BY doesn't count
gb_only = gb.split("ORDER BY",1)[0]
print("GROUP BY (only):", gb_only)
ok = "RAND" not in gb_only
print("OK" if ok else "FAIL: random term present in GROUP BY")
raise SystemExit(0 if ok else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
import django, sys, types, tempfile
from django.conf import settings
if not settings.configured:
    settings.configure(
        DATABASES={'default': {'ENGINE':'django.db.backends.sqlite3','NAME':':memory:'}},
        INSTALLED_APPS=['testapp'],
        DEFAULT_AUTO_FIELD='django.db.models.AutoField',
    )
app = types.ModuleType('testapp'); app.__path__ = [tempfile.mkdtemp()]
sys.modules['testapp'] = app
django.setup()
from django.db import models, connection

class Author(models.Model):
    name = models.CharField(max_length=50)
    class Meta: app_label = 'testapp'

class Book(models.Model):
    author = models.ForeignKey(Author, on_delete=models.CASCADE, related_name='books')
    title = models.CharField(max_length=50)
    class Meta: app_label = 'testapp'

def setup_db():
    with connection.schema_editor() as se:
        se.create_model(Author); se.create_model(Book)
    a1 = Author.objects.create(name='a1')
    a2 = Author.objects.create(name='a2')
    Book.objects.create(author=a1, title='b1')
    Book.objects.create(author=a1, title='b2')
    Book.objects.create(author=a1, title='b3')
    Book.objects.create(author=a2, title='b4')
    return a1, a2
from django.db.models import Count
a1,a2=setup_db()
base = dict(Author.objects.annotate(rc=Count('books')).values_list('id','rc'))
rand = dict(Author.objects.annotate(rc=Count('books')).order_by('?').values_list('id','rc'))
print("unordered:", base)
print("random   :", rand)
ok = (base == rand) and (len(rand)==2) and base.get(a1.id)==3 and base.get(a2.id)==1
print("OK" if ok else "FAIL")
raise SystemExit(0 if ok else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
import django, sys, types, tempfile
from django.conf import settings
if not settings.configured:
    settings.configure(
        DATABASES={'default': {'ENGINE':'django.db.backends.sqlite3','NAME':':memory:'}},
        INSTALLED_APPS=['testapp'],
        DEFAULT_AUTO_FIELD='django.db.models.AutoField',
    )
app = types.ModuleType('testapp'); app.__path__ = [tempfile.mkdtemp()]
sys.modules['testapp'] = app
django.setup()
from django.db import models, connection

class Author(models.Model):
    name = models.CharField(max_length=50)
    class Meta: app_label = 'testapp'

class Book(models.Model):
    author = models.ForeignKey(Author, on_delete=models.CASCADE, related_name='books')
    title = models.CharField(max_length=50)
    class Meta: app_label = 'testapp'

def setup_db():
    with connection.schema_editor() as se:
        se.create_model(Author); se.create_model(Book)
    a1 = Author.objects.create(name='a1')
    a2 = Author.objects.create(name='a2')
    Book.objects.create(author=a1, title='b1')
    Book.objects.create(author=a1, title='b2')
    Book.objects.create(author=a1, title='b3')
    Book.objects.create(author=a2, title='b4')
    return a1, a2
from django.db.models import Count
setup_db()
qs = Author.objects.annotate(rc=Count('books')).order_by('books__title')
sql, params = qs.query.sql_with_params()
print("SQL:", sql)
up = sql.upper()
gb = up.split("GROUP BY",1)[1] if "GROUP BY" in up else ""
print("GROUP BY tail:", gb)
ok = "TITLE" in gb
print("OK" if ok else "FAIL: real ordering column not in GROUP BY")
raise SystemExit(0 if ok else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
import django, sys, types, tempfile
from django.conf import settings
if not settings.configured:
    settings.configure(
        DATABASES={'default': {'ENGINE':'django.db.backends.sqlite3','NAME':':memory:'}},
        INSTALLED_APPS=['testapp'],
        DEFAULT_AUTO_FIELD='django.db.models.AutoField',
    )
app = types.ModuleType('testapp'); app.__path__ = [tempfile.mkdtemp()]
sys.modules['testapp'] = app
django.setup()
from django.db import models, connection

class Author(models.Model):
    name = models.CharField(max_length=50)
    class Meta: app_label = 'testapp'

class Book(models.Model):
    author = models.ForeignKey(Author, on_delete=models.CASCADE, related_name='books')
    title = models.CharField(max_length=50)
    class Meta: app_label = 'testapp'

def setup_db():
    with connection.schema_editor() as se:
        se.create_model(Author); se.create_model(Book)
    a1 = Author.objects.create(name='a1')
    a2 = Author.objects.create(name='a2')
    Book.objects.create(author=a1, title='b1')
    Book.objects.create(author=a1, title='b2')
    Book.objects.create(author=a1, title='b3')
    Book.objects.create(author=a2, title='b4')
    return a1, a2
from django.db.models.functions import Random
setup_db()
qs = Author.objects.annotate(r=Random()).values('id','r')
sql, params = qs.query.sql_with_params()
print("SQL:", sql)
up=sql.upper()
compiles = ("RANDOM()" in up) or ("RAND()" in up)
qs2 = Author.objects.order_by('?')
rows = list(qs2)
usable = len(rows) == 2
print("compiles random fn:", compiles, "orderby('?') rows:", len(rows))
ok = compiles and usable
print("OK" if ok else "FAIL")
raise SystemExit(0 if ok else 1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
import django, sys, types, tempfile
from django.conf import settings
if not settings.configured:
    settings.configure(
        DATABASES={'default': {'ENGINE':'django.db.backends.sqlite3','NAME':':memory:'}},
        INSTALLED_APPS=['testapp'],
        DEFAULT_AUTO_FIELD='django.db.models.AutoField',
    )
app = types.ModuleType('testapp'); app.__path__ = [tempfile.mkdtemp()]
sys.modules['testapp'] = app
django.setup()
from django.db import models, connection

class Author(models.Model):
    name = models.CharField(max_length=50)
    class Meta: app_label = 'testapp'

class Book(models.Model):
    author = models.ForeignKey(Author, on_delete=models.CASCADE, related_name='books')
    title = models.CharField(max_length=50)
    class Meta: app_label = 'testapp'

def setup_db():
    with connection.schema_editor() as se:
        se.create_model(Author); se.create_model(Book)
    a1 = Author.objects.create(name='a1')
    a2 = Author.objects.create(name='a2')
    Book.objects.create(author=a1, title='b1')
    Book.objects.create(author=a1, title='b2')
    Book.objects.create(author=a1, title='b3')
    Book.objects.create(author=a2, title='b4')
    return a1, a2
from django.db.models import Count
from django.db.models.functions import Lower
setup_db()
qs = Author.objects.annotate(rc=Count('books')).order_by(Lower('name'))
sql, params = qs.query.sql_with_params()
up = sql.upper()
gb = up.split("GROUP BY",1)[1] if "GROUP BY" in up else ""
print("GROUP BY tail:", gb)
ok = "NAME" in gb
print("OK" if ok else "FAIL: non-random function ordering not folded into GROUP BY")
raise SystemExit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
# Requirement 1.1 & 1.2 (positive control): Random.get_group_by_cols returns empty, with or without alias
import django
from django.conf import settings
if not settings.configured:
    settings.configure(DATABASES={'default': {'ENGINE':'django.db.backends.sqlite3','NAME':':memory:'}}, INSTALLED_APPS=[])
django.setup()
from django.db.models.functions import Random
r = Random()
c1 = r.get_group_by_cols()
c2 = r.get_group_by_cols(alias='foo')
print("no-alias:", repr(c1))
print("with-alias:", repr(c2))
ok = (list(c1) == []) and (list(c2) == [])
print("OK" if ok else "FAIL")
raise SystemExit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Gold patch adds Random.get_group_by_cols(alias=None) -> [] in django/db/models/functions/math.py, so the random ordering term contributes no grouping columns.

Probes (all HOLD on gold-patched tree; note this image's sqlite backend emits RAND() for Random, so probes match RAND/RANDOM):
- probe_1 (Req 1.1/1.2, POSITIVE CONTROL): Random().get_group_by_cols() and get_group_by_cols(alias='foo') both return []. HOLDS patched ([], []); at BASE returns [Random()], [Random()] -> FAIL. Discriminates.
- probe_2 (Req 1.3): GROUP BY of Author.annotate(Count('books')).order_by('?') contains no random term (RAND stripped-of-ORDER-BY check). HOLDS patched; at BASE GROUP BY includes RAND() -> FAIL. Discriminates.
- probe_3 (Req 2.1/2.2/2.3): random-ordered aggregate values equal unordered ({1:3,2:1}). HOLDS patched; at BASE random ordering fragments groups giving {1:1,2:1} -> FAIL. Discriminates.
- probe_4 (Req 3.1): ordering by real related column books__title still folds TITLE into GROUP BY. HOLDS patched.
- probe_5 (Req 4.1): Random still compiles to backend random fn (RAND()) as an annotation expression and order_by('?') executes. HOLDS patched.
- probe_6 (Req 3.4/4.2): non-random function ordering Lower('name') still folds NAME into GROUP BY. HOLDS patched.

Candidate wrong-fixes (both REJECTED by suite):
- weak_noop (comment only, == base): rejected by probe_1, probe_2, probe_3.
- weak_alias (returns [] only when alias is None, else [self]): rejected by probe_1 (alias='foo' case returns [Random()]). This targets the Req-1.2 'regardless of optional alias' criterion — a plausible weak reading that the suite catches.

>=5 probes all hold on patched, positive control discriminates (holds patched, fails base), and >=1 candidate exercised and rejected. Verdict SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 requirement probes hold on the patched tree; 2/2 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 6 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 6 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 2 alternative candidate patches, claimed to satisfy every cited requirement, and ran the same suite against them. The suite rejected all 2: a probe encoding a cited requirement fails under each of those, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

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
# Requirement 1.1 & 1.2 (positive control): Random.get_group_by_cols returns empty, with or without alias
import django
from django.conf import settings
if not settings.configured:
    settings.configure(DATABASES={'default': {'ENGINE':'django.db.backends.sqlite3','NAME':':memory:'}}, INSTALLED_APPS=[])
django.setup()
from django.db.models.functions import Random
r = Random()
c1 = r.get_group_by_cols()
c2 = r.get_group_by_cols(alias='foo')
print("no-alias:", repr(c1))
print("with-alias:", repr(c2))
ok = (list(c1) == []) and (list(c2) == [])
print("OK" if ok else "FAIL")
raise SystemExit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Gold patch adds Random.get_group_by_cols(alias=None) -> [] in django/db/models/functions/math.py, so the random ordering term contributes no grouping columns.

Probes (all HOLD on gold-patched tree; note this image's sqlite backend emits RAND() for Random, so probes match RAND/RANDOM):
- probe_1 (Req 1.1/1.2, POSITIVE CONTROL): Random().get_group_by_cols() and get_group_by_cols(alias='foo') both return []. HOLDS patched ([], []); at BASE returns [Random()], [Random()] -> FAIL. Discriminates.
- probe_2 (Req 1.3): GROUP BY of Author.annotate(Count('books')).order_by('?') contains no random term (RAND stripped-of-ORDER-BY check). HOLDS patched; at BASE GROUP BY includes RAND() -> FAIL. Discriminates.
- probe_3 (Req 2.1/2.2/2.3): random-ordered aggregate values equal unordered ({1:3,2:1}). HOLDS patched; at BASE random ordering fragments groups giving {1:1,2:1} -> FAIL. Discriminates.
- probe_4 (Req 3.1): ordering by real related column books__title still folds TITLE into GROUP BY. HOLDS patched.
- probe_5 (Req 4.1): Random still compiles to backend random fn (RAND()) as an annotation expression and order_by('?') executes. HOLDS patched.
- probe_6 (Req 3.4/4.2): non-random function ordering Lower('name') still folds NAME into GROUP BY. HOLDS patched.

Candidate wrong-fixes (both REJECTED by suite):
- weak_noop (comment only, == base): rejected by probe_1, probe_2, probe_3.
- weak_alias (returns [] only when alias is None, else [self]): rejected by probe_1 (alias='foo' case returns [Random()]). This targets the Req-1.2 'regardless of optional alias' criterion — a plausible weak reading that the suite catches.

>=5 probes all hold on patched, positive control discriminates (holds patched, fails base), and >=1 candidate exercised and rejected. Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Modeling boundary is correct: requirements pin the changed observable behavior (Random contributes no grouping columns -> correct aggregate results) rather than a narrow slice. Req 1 targets the exact patched method incl. the alias arg; Req 2 targets the observable aggregate correctness the issue reports; Req 3 protects the unchanged non-random path (regression scope); Req 4 covers 'otherwise unchanged'. No overreach: the patch is a single 2-line method on Random, and no requirement mandates behavior the code lacks nor forbids behavior it has. Verified base vs patched via nl_attack probes.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The gold edit adds Random.get_group_by_cols(self, alias=None) -> [] in functions/math.py. The requirements describe this as behavior ('return an empty collection of grouping columns', 'regardless of any optional alias argument'). This is legitimate: (1) get_group_by_cols(alias=None) is the pre-existing public Django expression API signature, not a fix-invented identifier; (2) naming Random/math.py and get_group_by/compiler.py is localization, and both are already in the PUBLIC problem_statement (which itself quotes the get_group_by loop and names django.db.models.sql.compiler.get_group_by). The hidden test's distinctive content — the AggregateTestCase.test_aggregation_random_ordering name, the Author/Count('book') fixture, the nine enumerated (name, count) rows (e.g. Peter Norvig -> 2), and the ordered=False assertion — is NOT reproduced. Requirement 2 translates ordered=False into behavioral prose ('same set of pairs, differing at most in order') rather than transmitting the test. Requirements 3-4 are regression/behavior descriptions consistent with PASS_TO_PASS coverage without enumerating test ids. No test paths, no quoted test/gold code beyond what problem_statement already exposes, no test-shaped enumeration.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
