# P2 adversarial audit — django__django-11555

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
"""POSITIVE CONTROL / Req1.4 & Req1.1: ordering a child model by its
parent-link pointer, where the parent's Meta.ordering contains an OrderBy
expression, must NOT crash and must return rows in the dictated order.
Holds on patched; at base raises 'OrderBy' object is not subscriptable."""
import sys
import django
from django.conf import settings

settings.configure(
    DEBUG=True,
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
    INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
    USE_TZ=False,
)
django.setup()
from django.db import models, connection


class Author(models.Model):
    name = models.CharField(max_length=64)
    class Meta:
        app_label = 'ordprobe'


class Article(models.Model):
    headline = models.CharField(max_length=64)
    author = models.ForeignKey(Author, models.SET_NULL, null=True)
    class Meta:
        app_label = 'ordprobe'
        ordering = (models.F('author').asc(nulls_first=True), 'id')


class ChildArticle(Article):
    class Meta:
        app_label = 'ordprobe'


with connection.schema_editor() as se:
    se.create_model(Author)
    se.create_model(Article)
    se.create_model(ChildArticle)

a1 = Author.objects.create(name='a1')   # pk 1
a2 = Author.objects.create(name='a2')   # pk 2
# author ascending with nulls first -> None, then a1(1), then a2(2); tie-break id
ca1 = ChildArticle.objects.create(headline='h', author=a2)   # id 1
ca2 = ChildArticle.objects.create(headline='h', author=a1)   # id 2
ca3 = ChildArticle.objects.create(headline='h', author=a1)   # id 3
ca4 = ChildArticle.objects.create(headline='h', author=None)  # id 4

try:
    got = list(ChildArticle.objects.order_by('article_ptr'))
except Exception as e:
    print("VIOLATED: raised", type(e).__name__, e)
    sys.exit(1)

expected = [ca4, ca2, ca3, ca1]   # nulls_first(author) then id
print("expected pks:", [o.pk for o in expected])
print("got pks:     ", [o.pk for o in got])
sys.exit(0 if got == expected else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""Req1.1 & 1.2: when find_ordering_name expands a related model's default
ordering and hits an OrderBy item, it emits that exact OrderBy object paired
with the boolean flag False. Inspect the (expr, is_ref) tuples directly."""
import sys
import django
from django.conf import settings

settings.configure(
    DEBUG=True,
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
    INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
    USE_TZ=False,
)
django.setup()
from django.db import models, connection
from django.db.models.expressions import OrderBy


class Author(models.Model):
    name = models.CharField(max_length=64)
    class Meta:
        app_label = 'ordprobe'


class Article(models.Model):
    headline = models.CharField(max_length=64)
    author = models.ForeignKey(Author, models.SET_NULL, null=True)
    class Meta:
        app_label = 'ordprobe'
        ordering = (models.F('author').asc(nulls_first=True), 'id')


class ChildArticle(Article):
    class Meta:
        app_label = 'ordprobe'


with connection.schema_editor() as se:
    se.create_model(Author)
    se.create_model(Article)
    se.create_model(ChildArticle)

qs = ChildArticle.objects.order_by('article_ptr')
compiler = qs.query.get_compiler(using='default')
# reach the related-model expansion path directly:
opts = Article._meta
try:
    results = compiler.find_ordering_name('article_ptr', ChildArticle._meta)
except Exception as e:
    print("VIOLATED: find_ordering_name raised", type(e).__name__, e)
    sys.exit(1)

print("results:", results)
orderby_tuples = [(e, f) for (e, f) in results if isinstance(e, OrderBy)]
print("orderby tuples:", orderby_tuples)
if not orderby_tuples:
    print("VIOLATED: no OrderBy emitted from parent default ordering")
    sys.exit(1)
# every emitted OrderBy must be paired with flag exactly False
bad = [(e, f) for (e, f) in orderby_tuples if f is not False]
if bad:
    print("VIOLATED: OrderBy not paired with False:", bad)
    sys.exit(1)
# the emitted OrderBy must be the F('author').asc(nulls_first=True) from Meta
src = Article._meta.ordering[0]
if not any(e is src for (e, f) in orderby_tuples):
    print("VIOLATED: emitted OrderBy is not the identical Meta.ordering object")
    sys.exit(1)
print("HOLDS: OrderBy emitted directly, paired with False, identical object")
sys.exit(0)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""Req1.5: expanding a related model's default ordering that MIXES OrderBy
items and textual field-name items preserves the original order — the result
is the in-order concatenation of each item's expansion. Use ordering
(F('author').asc, 'id', F('headline').desc) and check relative positions."""
import sys
import django
from django.conf import settings

settings.configure(
    DEBUG=True,
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
    INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
    USE_TZ=False,
)
django.setup()
from django.db import models, connection
from django.db.models.expressions import OrderBy


class Author(models.Model):
    name = models.CharField(max_length=64)
    class Meta:
        app_label = 'ordprobe'


class Article(models.Model):
    headline = models.CharField(max_length=64)
    author = models.ForeignKey(Author, models.SET_NULL, null=True)
    class Meta:
        app_label = 'ordprobe'
        ordering = (models.F('author').asc(nulls_first=True), 'id',
                    models.F('headline').desc())


class ChildArticle(Article):
    class Meta:
        app_label = 'ordprobe'


with connection.schema_editor() as se:
    se.create_model(Author)
    se.create_model(Article)
    se.create_model(ChildArticle)

compiler = ChildArticle.objects.all().query.get_compiler(using='default')
try:
    results = compiler.find_ordering_name('article_ptr', ChildArticle._meta)
except Exception as e:
    print("VIOLATED: raised", type(e).__name__, e)
    sys.exit(1)

print("results:", results)
exprs = [e for (e, f) in results]
# The two Meta OrderBy source objects are emitted directly (identity); string
# 'id' resolves into its own column directive that is NOT one of those objects.
src0 = Article._meta.ordering[0]   # F('author').asc(...)
src2 = Article._meta.ordering[2]   # F('headline').desc()
try:
    p0 = next(i for i, e in enumerate(exprs) if e is src0)
    p2 = next(i for i, e in enumerate(exprs) if e is src2)
except StopIteration:
    print("VIOLATED: a Meta.ordering OrderBy source object was not emitted directly")
    sys.exit(1)
print("pos(author-OrderBy)=%d pos(headline-OrderBy)=%d" % (p0, p2))
# original order: author(0) before headline(2)
if not p0 < p2:
    print("VIOLATED: OrderBy directives not in original spec order")
    sys.exit(1)
# the 'id' expansion must land strictly between them (in-order concatenation)
mid = exprs[p0 + 1:p2]
if not mid:
    print("VIOLATED: 'id' expansion did not land between the two OrderBy items")
    sys.exit(1)
# and none of the mid entries may be a Meta source OrderBy object
if any(e is src0 or e is src2 for e in mid):
    print("VIOLATED: unexpected source object between the two OrderBy items")
    sys.exit(1)
print("HOLDS: mixed ordering preserved in-order (author, id, headline)")
sys.exit(0)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""Req2.1 & 2.3: textual field references in a related model's Meta.ordering
still resolve by name to concrete column ordering directives (no OrderBy
objects leak out for a pure-string ordering). Parent orders by ('headline',
'-id'); expanding via the child's ptr must produce plain column directives in
that order, direction respected."""
import sys
import django
from django.conf import settings

settings.configure(
    DEBUG=True,
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
    INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
    USE_TZ=False,
)
django.setup()
from django.db import models, connection
from django.db.models.expressions import OrderBy


class P(models.Model):
    headline = models.CharField(max_length=64)
    class Meta:
        app_label = 'ordprobe'
        ordering = ('headline', '-id')


class C(P):
    class Meta:
        app_label = 'ordprobe'


with connection.schema_editor() as se:
    se.create_model(P)
    se.create_model(C)

compiler = C.objects.all().query.get_compiler(using='default')
try:
    results = compiler.find_ordering_name('p_ptr', C._meta)
except Exception as e:
    print("VIOLATED: raised", type(e).__name__, e)
    sys.exit(1)

print("results:", results)
if not results:
    print("VIOLATED: string ordering produced no directives")
    sys.exit(1)
# String field refs resolve by NAME into concrete column directives: each
# emitted OrderBy wraps a Col (a resolved column), never the raw string / the
# unresolved F. If resolution were bypassed we'd see a bare string or an
# unresolved F expression here.
from django.db.models.expressions import Col, F
for (e, f) in results:
    inner = getattr(e, 'expression', e)
    if isinstance(inner, F) or isinstance(e, (str, F)):
        print("VIOLATED: string ordering was not resolved by name:", e)
        sys.exit(1)
# functional check: rows come back ordered by headline asc, id desc
c1 = C.objects.create(headline='b')  # id1
c2 = C.objects.create(headline='a')  # id2
c3 = C.objects.create(headline='a')  # id3
got = [o.pk for o in C.objects.order_by('p_ptr')]
expected = [c3.pk, c2.pk, c1.pk]  # headline a (id desc: 3,2) then b (1)
print("got", got, "expected", expected)
sys.exit(0 if got == expected else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""Req2.2: infinite ordering loops (a relation whose default ordering cycles
back on itself) must still be rejected with a FieldError when expanding a
related model's default ordering."""
import sys
import django
from django.conf import settings

settings.configure(
    DEBUG=True,
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
    INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
    USE_TZ=False,
)
django.setup()
from django.db import models, connection
from django.core.exceptions import FieldError


class Node(models.Model):
    self_rel = models.ForeignKey('self', models.SET_NULL, null=True)
    class Meta:
        app_label = 'ordprobe'
        ordering = ('self_rel',)   # cycles back on itself


with connection.schema_editor() as se:
    se.create_model(Node)

compiler = Node.objects.all().query.get_compiler(using='default')
try:
    compiler.find_ordering_name('self_rel', Node._meta)
except FieldError as e:
    print("HOLDS: FieldError raised for ordering loop:", e)
    sys.exit(0)
except Exception as e:
    print("VIOLATED: wrong exception", type(e).__name__, e)
    sys.exit(1)
print("VIOLATED: no error raised for self-referential ordering loop")
sys.exit(1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
"""Req3.2 & 3.3: query expressions used directly in order_by(...) (with
nulls_first/nulls_last) and used in a model's OWN (non-relational) Meta.ordering
still produce the requested ordering. This is a regression guard that must hold
on both trees."""
import sys
import django
from django.conf import settings

settings.configure(
    DEBUG=True,
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
    INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
    USE_TZ=False,
)
django.setup()
from django.db import models, connection


class Thing(models.Model):
    rank = models.IntegerField(null=True)
    class Meta:
        app_label = 'ordprobe'
        ordering = (models.F('rank').asc(nulls_last=True), 'id')


with connection.schema_editor() as se:
    se.create_model(Thing)

t_none = Thing.objects.create(rank=None)  # id1
t5 = Thing.objects.create(rank=5)         # id2
t1 = Thing.objects.create(rank=1)         # id3

# 3.3: own Meta.ordering by F expr (rank asc nulls_last, then id)
default_order = [o.pk for o in Thing.objects.all()]
expected_default = [t1.pk, t5.pk, t_none.pk]
print("default", default_order, "expected", expected_default)
if default_order != expected_default:
    print("VIOLATED: own F-expr Meta.ordering wrong")
    sys.exit(1)

# 3.2: explicit order_by with F expr and nulls_first
explicit = [o.pk for o in Thing.objects.order_by(models.F('rank').desc(nulls_first=True))]
expected_explicit = [t_none.pk, t5.pk, t1.pk]
print("explicit", explicit, "expected", expected_explicit)
if explicit != expected_explicit:
    print("VIOLATED: explicit F-expr order_by wrong")
    sys.exit(1)

print("HOLDS: direct/own F-expr ordering intact")
sys.exit(0)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""POSITIVE CONTROL / Req1.4 & Req1.1: ordering a child model by its
parent-link pointer, where the parent's Meta.ordering contains an OrderBy
expression, must NOT crash and must return rows in the dictated order.
Holds on patched; at base raises 'OrderBy' object is not subscriptable."""
import sys
import django
from django.conf import settings

settings.configure(
    DEBUG=True,
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
    INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
    USE_TZ=False,
)
django.setup()
from django.db import models, connection


class Author(models.Model):
    name = models.CharField(max_length=64)
    class Meta:
        app_label = 'ordprobe'


class Article(models.Model):
    headline = models.CharField(max_length=64)
    author = models.ForeignKey(Author, models.SET_NULL, null=True)
    class Meta:
        app_label = 'ordprobe'
        ordering = (models.F('author').asc(nulls_first=True), 'id')


class ChildArticle(Article):
    class Meta:
        app_label = 'ordprobe'


with connection.schema_editor() as se:
    se.create_model(Author)
    se.create_model(Article)
    se.create_model(ChildArticle)

a1 = Author.objects.create(name='a1')   # pk 1
a2 = Author.objects.create(name='a2')   # pk 2
# author ascending with nulls first -> None, then a1(1), then a2(2); tie-break id
ca1 = ChildArticle.objects.create(headline='h', author=a2)   # id 1
ca2 = ChildArticle.objects.create(headline='h', author=a1)   # id 2
ca3 = ChildArticle.objects.create(headline='h', author=a1)   # id 3
ca4 = ChildArticle.objects.create(headline='h', author=None)  # id 4

try:
    got = list(ChildArticle.objects.order_by('article_ptr'))
except Exception as e:
    print("VIOLATED: raised", type(e).__name__, e)
    sys.exit(1)

expected = [ca4, ca2, ca3, ca1]   # nulls_first(author) then id
print("expected pks:", [o.pk for o in expected])
print("got pks:     ", [o.pk for o in got])
sys.exit(0 if got == expected else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Fix under review: in SQLCompiler.find_ordering_name, when expanding a related model's default ordering, dispatch on isinstance(item, OrderBy) -> results.append((item, False)); continue. Instance django__django-11555, F2P test_order_by_ptr_field_with_default_ordering_by_expression.

Six probes, all HOLD on the gold-patched tree:
- probe_1 (POSITIVE CONTROL, Req1.1/1.4): order a ChildArticle by its parent-link ptr where parent Meta.ordering=(F('author').asc(nulls_first=True),'id'). VIOLATED at base ('OrderBy' object does not support indexing / TypeError), HOLDS patched with correct row order [4,2,3,1]. Discriminates.
- probe_2 (Req1.1/1.2): inspects find_ordering_name output tuples directly; asserts the Meta OrderBy object is emitted by identity and paired with flag exactly False.
- probe_3 (Req1.5): mixed OrderBy+string ordering (author, id, headline-desc) preserves original in-order concatenation; source OrderBy objects emitted by identity at correct relative positions with the string 'id' expansion strictly between.
- probe_4 (Req2.1/2.3): string-only parent ordering ('headline','-id') resolves by name into concrete Col directives (not raw string / unresolved F) and returns correct row order.
- probe_5 (Req2.2): self-referential ordering loop still raises FieldError ('Infinite loop caused by ordering').
- probe_6 (Req3.2/3.3): direct order_by F-expr with nulls_first, and own non-relational Meta.ordering F-expr, both produce requested order (regression guard; holds both trees).

CANDIDATE WRONG PATCH (weak.diff): identical structure but pairs the OrderBy with True instead of False (a weak reading of Req1 that emits the expression but mishandles the is-reference flag). Applies at base_commit. Probe suite REJECTS it: probe_2 VIOLATED ('OrderBy not paired with False: [(OrderBy(F(author)...), True)]'). This demonstrates the suite discriminates a plausibly-wrong implementation on the Req1.2 flag criterion. (Note: probes 1,3,4,5,6 still HOLD under the weak patch since sqlite ORDER BY output happens to coincide; probe_2 is the discriminator on the flag semantics.)

Verdict SOUND: >=5 distinct probes all hold on patched, positive control fails at base and holds patched (discriminating power confirmed), and >=1 candidate patch is rejected by the suite. No requirements VIOLATION found (no mandated behavior missing from gold), and no probe-conforming TOO-WEAK patch found.

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
"""POSITIVE CONTROL / Req1.4 & Req1.1: ordering a child model by its
parent-link pointer, where the parent's Meta.ordering contains an OrderBy
expression, must NOT crash and must return rows in the dictated order.
Holds on patched; at base raises 'OrderBy' object is not subscriptable."""
import sys
import django
from django.conf import settings

settings.configure(
    DEBUG=True,
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
    INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
    USE_TZ=False,
)
django.setup()
from django.db import models, connection


class Author(models.Model):
    name = models.CharField(max_length=64)
    class Meta:
        app_label = 'ordprobe'


class Article(models.Model):
    headline = models.CharField(max_length=64)
    author = models.ForeignKey(Author, models.SET_NULL, null=True)
    class Meta:
        app_label = 'ordprobe'
        ordering = (models.F('author').asc(nulls_first=True), 'id')


class ChildArticle(Article):
    class Meta:
        app_label = 'ordprobe'


with connection.schema_editor() as se:
    se.create_model(Author)
    se.create_model(Article)
    se.create_model(ChildArticle)

a1 = Author.objects.create(name='a1')   # pk 1
a2 = Author.objects.create(name='a2')   # pk 2
# author ascending with nulls first -> None, then a1(1), then a2(2); tie-break id
ca1 = ChildArticle.objects.create(headline='h', author=a2)   # id 1
ca2 = ChildArticle.objects.create(headline='h', author=a1)   # id 2
ca3 = ChildArticle.objects.create(headline='h', author=a1)   # id 3
ca4 = ChildArticle.objects.create(headline='h', author=None)  # id 4

try:
    got = list(ChildArticle.objects.order_by('article_ptr'))
except Exception as e:
    print("VIOLATED: raised", type(e).__name__, e)
    sys.exit(1)

expected = [ca4, ca2, ca3, ca1]   # nulls_first(author) then id
print("expected pks:", [o.pk for o in expected])
print("got pks:     ", [o.pk for o in got])
sys.exit(0 if got == expected else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Fix under review: in SQLCompiler.find_ordering_name, when expanding a related model's default ordering, dispatch on isinstance(item, OrderBy) -> results.append((item, False)); continue. Instance django__django-11555, F2P test_order_by_ptr_field_with_default_ordering_by_expression.

Six probes, all HOLD on the gold-patched tree:
- probe_1 (POSITIVE CONTROL, Req1.1/1.4): order a ChildArticle by its parent-link ptr where parent Meta.ordering=(F('author').asc(nulls_first=True),'id'). VIOLATED at base ('OrderBy' object does not support indexing / TypeError), HOLDS patched with correct row order [4,2,3,1]. Discriminates.
- probe_2 (Req1.1/1.2): inspects find_ordering_name output tuples directly; asserts the Meta OrderBy object is emitted by identity and paired with flag exactly False.
- probe_3 (Req1.5): mixed OrderBy+string ordering (author, id, headline-desc) preserves original in-order concatenation; source OrderBy objects emitted by identity at correct relative positions with the string 'id' expansion strictly between.
- probe_4 (Req2.1/2.3): string-only parent ordering ('headline','-id') resolves by name into concrete Col directives (not raw string / unresolved F) and returns correct row order.
- probe_5 (Req2.2): self-referential ordering loop still raises FieldError ('Infinite loop caused by ordering').
- probe_6 (Req3.2/3.3): direct order_by F-expr with nulls_first, and own non-relational Meta.ordering F-expr, both produce requested order (regression guard; holds both trees).

CANDIDATE WRONG PATCH (weak.diff): identical structure but pairs the OrderBy with True instead of False (a weak reading of Req1 that emits the expression but mishandles the is-reference flag). Applies at base_commit. Probe suite REJECTS it: probe_2 VIOLATED ('OrderBy not paired with False: [(OrderBy(F(author)...), True)]'). This demonstrates the suite discriminates a plausibly-wrong implementation on the Req1.2 flag criterion. (Note: probes 1,3,4,5,6 still HOLD under the weak patch since sqlite ORDER BY output happens to coincide; probe_2 is the discriminator on the flag semantics.)

Verdict SOUND: >=5 distinct probes all hold on patched, positive control fails at base and holds patched (discriminating power confirmed), and >=1 candidate patch is rejected by the suite. No requirements VIOLATION found (no mandated behavior missing from gold), and no probe-conforming TOO-WEAK patch found.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Gold patch: in find_ordering_name's Meta.ordering expansion loop, `if isinstance(item, OrderBy): results.append((item, False)); continue`. R1.1-1.3 (emit OrderBy directly, pair with False, skip get_order_dir) mirror the three effects of the patch exactly — confirmed via probe: the pair is (OrderBy, False) and no indexing error. R1.4/1.5 (no crash, in-order concatenation) hold since the loop order is untouched. R2.x (strings still recurse; loop detection kept) and R3.x (regression protection) describe unchanged code paths. Modeling boundary is CORRECT and appropriately narrow: the patch only special-cases OrderBy via isinstance, and the requirements explicitly scope to OrderBy items, noting other expression types are out of scope. This matches the patch even though the issue's hints mention Lower('name') also failing — the gold patch does NOT handle Lower, and the requirements correctly do not claim it does (no over-claim). FAITHFUL.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The document localizes the change to SQLCompiler.find_ordering_name / get_order_dir and the OrderBy-vs-string dispatch — all of which are public in the problem_statement (which names OrderBy, get_order_dir, 'not subscriptable', MTI, and expressions in Meta.ordering). Borderline items examined and cleared: (1) Req 1.2 pins pairing the OrderBy item with boolean False ('is-reference' flag) — this mirrors the gold's (item, False) tuple, but it describes find_ordering_name's pre-existing return contract (directive, is_ref pairs), which is legitimate localization, not test-derived content. (2) Req 1.4's 'child model by its parent-link pointer field' echoes the test scenario (ChildArticle.order_by('article_ptr')) but is directly inferable from the public MTI 'order_by a parent model' description; the fix-/test-invented identifiers ChildArticle and article_ptr are NOT disclosed. (3) Req 3's regression enumeration overlaps the PASS_TO_PASS set (nulls_first/last, pk, fk attname, constant value, extra ordering quoted/table-qualified, random, values()/annotate() deprecation, duplicate-table reference, no-reorder-after-slicing) and is somewhat test-shaped, but it names no test functions/ids, quotes no test or gold code, and lists only general well-known Django ordering features as a regression envelope — translating behaviors, not transmitting tests. No test names/paths/ids, no quoted test/gold lines, no fix-invented identifiers leak.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
