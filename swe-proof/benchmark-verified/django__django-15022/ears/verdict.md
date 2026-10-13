# P2 adversarial audit — django__django-15022

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
"""Positive control / Req 1.2 & 1.1:
When all search fields span the SAME multi-valued relation, and two words are
each individually matched through that relation but no single related row
matches BOTH words, get_search_results SHALL EXCLUDE the instance.
Base over-matches (retains) -> VIOLATED at base; patched excludes -> HOLDS.
"""
import django
from django.conf import settings

settings.configure(
    DEBUG=True,
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    INSTALLED_APPS=[
        "django.contrib.contenttypes", "django.contrib.auth",
        "django.contrib.admin", "django.contrib.sessions",
        "django.contrib.messages",
    ],
    DEFAULT_AUTO_FIELD="django.db.models.AutoField",
)
django.setup()

from django.db import models, connection
from django.contrib import admin
from django.contrib.admin.sites import AdminSite


class Parent(models.Model):
    name = models.CharField(max_length=100)
    class Meta:
        app_label = "admin"


class Child(models.Model):
    parent = models.ForeignKey(Parent, related_name="children", on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    class Meta:
        app_label = "admin"


with connection.schema_editor() as se:
    se.create_model(Parent)
    se.create_model(Child)


class ParentAdmin(admin.ModelAdmin):
    search_fields = ["children__name"]


p = Parent.objects.create(name="p1")
Child.objects.create(parent=p, name="foo")
Child.objects.create(parent=p, name="bar")

ma = ParentAdmin(Parent, AdminSite())

class Req:
    pass
req = Req()

qs, dup = ma.get_search_results(req, Parent.objects.all(), "foo bar")
ids = sorted(set(qs.values_list("id", flat=True)))
print("retained ids for 'foo bar':", ids)
# No single child has both 'foo' and 'bar' -> instance must be excluded.
if ids == []:
    print("OK: instance excluded (no single related row matches both words)")
    raise SystemExit(0)
else:
    print("FAIL: instance retained -> over-matching across different related rows")
    raise SystemExit(1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""Req 1.3: When a single related row matches EVERY word matched through the
relation, the instance SHALL be RETAINED."""
import django
from django.conf import settings
settings.configure(DEBUG=True,
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    INSTALLED_APPS=["django.contrib.contenttypes","django.contrib.auth",
        "django.contrib.admin","django.contrib.sessions","django.contrib.messages"],
    DEFAULT_AUTO_FIELD="django.db.models.AutoField")
django.setup()
from django.db import models, connection
from django.contrib import admin
from django.contrib.admin.sites import AdminSite

class Parent(models.Model):
    name = models.CharField(max_length=100)
    class Meta: app_label = "admin"
class Child(models.Model):
    parent = models.ForeignKey(Parent, related_name="children", on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    class Meta: app_label = "admin"
with connection.schema_editor() as se:
    se.create_model(Parent); se.create_model(Child)

class ParentAdmin(admin.ModelAdmin):
    search_fields = ["children__name"]

p = Parent.objects.create(name="p1")
Child.objects.create(parent=p, name="foo bar baz")  # one row matches both words
Child.objects.create(parent=p, name="unrelated")
ma = ParentAdmin(Parent, AdminSite())
qs, dup = ma.get_search_results(object(), Parent.objects.all(), "foo bar")
ids = sorted(set(qs.values_list("id", flat=True)))
print("retained ids:", ids)
if ids == [p.id]:
    print("OK: instance retained (one related row matches all words)")
    raise SystemExit(0)
print("FAIL: instance not retained though a single related row matches all words")
raise SystemExit(1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""Req 1.4 & 5.1: A word satisfiable by the instance's own single-valued field
should combine independently; same-related-row binds only words matched through
the same relation. Two search fields: own name + children__name. Word 'p1'
matches parent's own name, word 'foo' matches a child. Instance retained even
though the child matching 'foo' does not itself contain 'p1'."""
import django
from django.conf import settings
settings.configure(DEBUG=True,
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    INSTALLED_APPS=["django.contrib.contenttypes","django.contrib.auth",
        "django.contrib.admin","django.contrib.sessions","django.contrib.messages"],
    DEFAULT_AUTO_FIELD="django.db.models.AutoField")
django.setup()
from django.db import models, connection
from django.contrib import admin
from django.contrib.admin.sites import AdminSite

class Parent(models.Model):
    name = models.CharField(max_length=100)
    class Meta: app_label = "admin"
class Child(models.Model):
    parent = models.ForeignKey(Parent, related_name="children", on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    class Meta: app_label = "admin"
with connection.schema_editor() as se:
    se.create_model(Parent); se.create_model(Child)

class ParentAdmin(admin.ModelAdmin):
    search_fields = ["name", "children__name"]

p = Parent.objects.create(name="p1alpha")
Child.objects.create(parent=p, name="foo")
q = Parent.objects.create(name="other")
Child.objects.create(parent=q, name="foo")
ma = ParentAdmin(Parent, AdminSite())
# words: 'p1alpha' (own name) and 'foo' (child). p retained; q not (name mismatch).
qs, dup = ma.get_search_results(object(), Parent.objects.all(), "p1alpha foo")
ids = sorted(set(qs.values_list("id", flat=True)))
print("retained ids:", ids)
if ids == [p.id]:
    print("OK: own-field word combines independently with relation word")
    raise SystemExit(0)
print("FAIL: expected only parent p1alpha")
raise SystemExit(1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""Req 3.1: empty search term or no search fields -> queryset returned unchanged
(same object, unchanged dup flag). Req 4.1: returns (qs, bool)."""
import django
from django.conf import settings
settings.configure(DEBUG=True,
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    INSTALLED_APPS=["django.contrib.contenttypes","django.contrib.auth",
        "django.contrib.admin","django.contrib.sessions","django.contrib.messages"],
    DEFAULT_AUTO_FIELD="django.db.models.AutoField")
django.setup()
from django.db import models, connection
from django.contrib import admin
from django.contrib.admin.sites import AdminSite

class Parent(models.Model):
    name = models.CharField(max_length=100)
    class Meta: app_label = "admin"
with connection.schema_editor() as se:
    se.create_model(Parent)
Parent.objects.create(name="a"); Parent.objects.create(name="b")

class WithFields(admin.ModelAdmin):
    search_fields = ["name"]
class NoFields(admin.ModelAdmin):
    search_fields = []

ok = True
# empty term
ma = WithFields(Parent, AdminSite())
base_qs = Parent.objects.all()
qs, dup = ma.get_search_results(object(), base_qs, "")
if qs is not base_qs:
    print("FAIL: empty term did not return same queryset object"); ok = False
if dup is not False:
    print("FAIL: dup flag not False for empty term:", dup); ok = False
# no search fields
ma2 = NoFields(Parent, AdminSite())
qs2, dup2 = ma2.get_search_results(object(), base_qs, "anything")
if qs2 is not base_qs:
    print("FAIL: no-fields did not return same queryset object"); ok = False
if not isinstance(dup, bool) or not isinstance(dup2, bool):
    print("FAIL: dup indicator not boolean"); ok = False
if ok:
    print("OK: unchanged queryset + boolean dup flag for empty/no-fields")
    raise SystemExit(0)
raise SystemExit(1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""Req 3.2 (quoted literal) & 3.3 (prefix operators): quotes group multiple
tokens into one word; '^' = istartswith; '=' = iexact. And Req 5.2 exclusion."""
import django
from django.conf import settings
settings.configure(DEBUG=True,
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    INSTALLED_APPS=["django.contrib.contenttypes","django.contrib.auth",
        "django.contrib.admin","django.contrib.sessions","django.contrib.messages"],
    DEFAULT_AUTO_FIELD="django.db.models.AutoField")
django.setup()
from django.db import models, connection
from django.contrib import admin
from django.contrib.admin.sites import AdminSite

class Item(models.Model):
    name = models.CharField(max_length=100)
    class Meta: app_label = "admin"
with connection.schema_editor() as se:
    se.create_model(Item)
i1 = Item.objects.create(name="hello world")
i2 = Item.objects.create(name="hello there")
ma_start = type("A", (admin.ModelAdmin,), {"search_fields": ["^name"]})(Item, AdminSite())
ma_exact = type("B", (admin.ModelAdmin,), {"search_fields": ["=name"]})(Item, AdminSite())
ma_c = type("C", (admin.ModelAdmin,), {"search_fields": ["name"]})(Item, AdminSite())

ok = True
# quoted literal: "hello world" is one word -> only i1
qs, _ = ma_c.get_search_results(object(), Item.objects.all(), '"hello world"')
ids = sorted(set(qs.values_list("id", flat=True)))
if ids != [i1.id]:
    print("FAIL: quoted literal grouping wrong:", ids); ok = False
else:
    print("quoted literal OK:", ids)
# istartswith prefix: '^hello' matches both; '^world' matches none
qs, _ = ma_start.get_search_results(object(), Item.objects.all(), "world")
if sorted(set(qs.values_list("id", flat=True))) != []:
    print("FAIL: ^ istartswith should not match 'world' mid-string"); ok = False
else:
    print("istartswith prefix OK")
# iexact: '=name' matches full string only
qs, _ = ma_exact.get_search_results(object(), Item.objects.all(), '"hello world"')
if sorted(set(qs.values_list("id", flat=True))) != [i1.id]:
    print("FAIL: =name iexact wrong"); ok = False
else:
    print("iexact prefix OK")
# Req 5.2: multi-word not satisfiable by any single instance -> excluded
qs, _ = ma_c.get_search_results(object(), Item.objects.all(), "world there")
if sorted(set(qs.values_list("id", flat=True))) != []:
    print("FAIL: 5.2 exclusion"); ok = False
else:
    print("5.2 exclusion OK")
raise SystemExit(0 if ok else 1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
"""Req 4.2/4.3: duplicate indicator. A multi-valued search field spawns
duplicates -> dup True. A single-valued field -> dup False. The change must
not alter this indicator's meaning."""
import django
from django.conf import settings
settings.configure(DEBUG=True,
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    INSTALLED_APPS=["django.contrib.contenttypes","django.contrib.auth",
        "django.contrib.admin","django.contrib.sessions","django.contrib.messages"],
    DEFAULT_AUTO_FIELD="django.db.models.AutoField")
django.setup()
from django.db import models, connection
from django.contrib import admin
from django.contrib.admin.sites import AdminSite

class Parent(models.Model):
    name = models.CharField(max_length=100)
    class Meta: app_label = "admin"
class Child(models.Model):
    parent = models.ForeignKey(Parent, related_name="children", on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    class Meta: app_label = "admin"
with connection.schema_editor() as se:
    se.create_model(Parent); se.create_model(Child)
p = Parent.objects.create(name="p")
Child.objects.create(parent=p, name="foo")

ok = True
# multi-valued relation -> may have duplicates True
ma_mv = type("MV", (admin.ModelAdmin,), {"search_fields": ["children__name"]})(Parent, AdminSite())
_, dup = ma_mv.get_search_results(object(), Parent.objects.all(), "foo")
if dup is not True:
    print("FAIL: multi-valued relation should report may_have_duplicates True; got", dup); ok = False
else:
    print("multi-valued dup=True OK")
# single-valued field -> False
ma_sv = type("SV", (admin.ModelAdmin,), {"search_fields": ["name"]})(Parent, AdminSite())
_, dup2 = ma_sv.get_search_results(object(), Parent.objects.all(), "p")
if dup2 is not False:
    print("FAIL: single-valued should report False; got", dup2); ok = False
else:
    print("single-valued dup=False OK")
raise SystemExit(0 if ok else 1)
```

Attack 7 — `probe_7.py` → holds on the patched tree (good)

```python
"""Req 2.2/2.3 & 5.1: repeated word over one multi-valued field -> retain when
one related row matches; order independence & multi-word single-valued retain."""
import django
from django.conf import settings
settings.configure(DEBUG=True,
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    INSTALLED_APPS=["django.contrib.contenttypes","django.contrib.auth",
        "django.contrib.admin","django.contrib.sessions","django.contrib.messages"],
    DEFAULT_AUTO_FIELD="django.db.models.AutoField")
django.setup()
from django.db import models, connection
from django.contrib import admin
from django.contrib.admin.sites import AdminSite

class Parent(models.Model):
    name = models.CharField(max_length=100)
    class Meta: app_label = "admin"
class Child(models.Model):
    parent = models.ForeignKey(Parent, related_name="children", on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    class Meta: app_label = "admin"
with connection.schema_editor() as se:
    se.create_model(Parent); se.create_model(Child)
p = Parent.objects.create(name="p")
Child.objects.create(parent=p, name="foo")
ma = type("MV", (admin.ModelAdmin,), {"search_fields": ["children__name"]})(Parent, AdminSite())

ok = True
# repeated word: one related row matches -> retain
qs, _ = ma.get_search_results(object(), Parent.objects.all(), "foo foo foo")
if sorted(set(qs.values_list("id", flat=True))) != [p.id]:
    print("FAIL: repeated word should retain"); ok = False
else:
    print("repeated-word retain OK")

# single-valued multi-word retain iff satisfies every word; order-independent
class Item(models.Model):
    name = models.CharField(max_length=100)
    class Meta: app_label = "admin"
with connection.schema_editor() as se:
    se.create_model(Item)
it = Item.objects.create(name="alpha beta gamma")
Item.objects.create(name="alpha only")
ma2 = type("SV", (admin.ModelAdmin,), {"search_fields": ["name"]})(Item, AdminSite())
a, _ = ma2.get_search_results(object(), Item.objects.all(), "alpha gamma")
b, _ = ma2.get_search_results(object(), Item.objects.all(), "gamma alpha")
ida = sorted(set(a.values_list("id", flat=True)))
idb = sorted(set(b.values_list("id", flat=True)))
if ida != [it.id] or idb != [it.id]:
    print("FAIL: single-valued multi-word retain / order", ida, idb); ok = False
else:
    print("single-valued multi-word + order-independence OK")
raise SystemExit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Positive control / Req 1.2 & 1.1:
When all search fields span the SAME multi-valued relation, and two words are
each individually matched through that relation but no single related row
matches BOTH words, get_search_results SHALL EXCLUDE the instance.
Base over-matches (retains) -> VIOLATED at base; patched excludes -> HOLDS.
"""
import django
from django.conf import settings

settings.configure(
    DEBUG=True,
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    INSTALLED_APPS=[
        "django.contrib.contenttypes", "django.contrib.auth",
        "django.contrib.admin", "django.contrib.sessions",
        "django.contrib.messages",
    ],
    DEFAULT_AUTO_FIELD="django.db.models.AutoField",
)
django.setup()

from django.db import models, connection
from django.contrib import admin
from django.contrib.admin.sites import AdminSite


class Parent(models.Model):
    name = models.CharField(max_length=100)
    class Meta:
        app_label = "admin"


class Child(models.Model):
    parent = models.ForeignKey(Parent, related_name="children", on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    class Meta:
        app_label = "admin"


with connection.schema_editor() as se:
    se.create_model(Parent)
    se.create_model(Child)


class ParentAdmin(admin.ModelAdmin):
    search_fields = ["children__name"]


p = Parent.objects.create(name="p1")
Child.objects.create(parent=p, name="foo")
Child.objects.create(parent=p, name="bar")

ma = ParentAdmin(Parent, AdminSite())

class Req:
    pass
req = Req()

qs, dup = ma.get_search_results(req, Parent.objects.all(), "foo bar")
ids = sorted(set(qs.values_list("id", flat=True)))
print("retained ids for 'foo bar':", ids)
# No single child has both 'foo' and 'bar' -> instance must be excluded.
if ids == []:
    print("OK: instance excluded (no single related row matches both words)")
    raise SystemExit(0)
else:
    print("FAIL: instance retained -> over-matching across different related rows")
    raise SystemExit(1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance django__django-15022: ModelAdmin.get_search_results must narrow with a SINGLE combined filter so words matched through the same multi-valued relation share one related row.

Probes (all run in the official docker image):
- probe_1.py (Req 1.1/1.2, POSITIVE CONTROL): search_fields=['children__name'], parent p has children 'foo' and 'bar' (no single child has both). Search 'foo bar' -> instance MUST be excluded. VIOLATED at base (retained id [1]); HOLDS patched (retained []). Discriminates.
- probe_2.py (Req 1.3): one child 'foo bar baz' matches both words -> instance retained. HOLDS patched.
- probe_3.py (Req 1.4/5.1): search_fields=['name','children__name']; word matching parent's own field combines independently with a relation word; only the matching parent retained. HOLDS patched.
- probe_4.py (Req 3.1/4.1): empty term and no-search-fields return the SAME queryset object with boolean dup=False. HOLDS patched.
- probe_5.py (Req 3.2/3.3/5.2): quoted literal grouping ('"hello world"' = one word), '^' istartswith, '=' iexact prefixes, and multi-word non-satisfiable exclusion. HOLDS patched.
- probe_6.py (Req 4.2/4.3): multi-valued relation search field reports may_have_duplicates=True; single-valued reports False. HOLDS patched.
- probe_7.py (Req 2.2/2.3/5.1): repeated word over one multi-valued field retains when one row matches; single-valued multi-word retain is order-independent. HOLDS patched.

All 7 probes HOLD on the gold-patched tree.

Candidate wrong-fix (weak_partial.diff): collects per-word or_queries into a list but STILL applies them as separate chained .filter() calls (the semantic equivalent of the base bug — separate joins per word). It applies cleanly at base_commit and passes the regression probes (4,5,6) but is REJECTED by probe_1 (over-matches: retains id [1] for 'foo bar'), demonstrating the suite discriminates a plausible partial fix that would not resolve the hidden FAIL_TO_PASS tests (test_many_search_terms / multi-valued relationship search).

Protocol satisfied: >=5 distinct probes covering behavioral SHALLs, boundaries, and 'SHALL keep' regressions; positive control fails at base and holds patched; >=1 candidate exercised and REJECTED.

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
"""Positive control / Req 1.2 & 1.1:
When all search fields span the SAME multi-valued relation, and two words are
each individually matched through that relation but no single related row
matches BOTH words, get_search_results SHALL EXCLUDE the instance.
Base over-matches (retains) -> VIOLATED at base; patched excludes -> HOLDS.
"""
import django
from django.conf import settings

settings.configure(
    DEBUG=True,
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    INSTALLED_APPS=[
        "django.contrib.contenttypes", "django.contrib.auth",
        "django.contrib.admin", "django.contrib.sessions",
        "django.contrib.messages",
    ],
    DEFAULT_AUTO_FIELD="django.db.models.AutoField",
)
django.setup()

from django.db import models, connection
from django.contrib import admin
from django.contrib.admin.sites import AdminSite


class Parent(models.Model):
    name = models.CharField(max_length=100)
    class Meta:
        app_label = "admin"


class Child(models.Model):
    parent = models.ForeignKey(Parent, related_name="children", on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    class Meta:
        app_label = "admin"


with connection.schema_editor() as se:
    se.create_model(Parent)
    se.create_model(Child)


class ParentAdmin(admin.ModelAdmin):
    search_fields = ["children__name"]


p = Parent.objects.create(name="p1")
Child.objects.create(parent=p, name="foo")
Child.objects.create(parent=p, name="bar")

ma = ParentAdmin(Parent, AdminSite())

class Req:
    pass
req = Req()

qs, dup = ma.get_search_results(req, Parent.objects.all(), "foo bar")
ids = sorted(set(qs.values_list("id", flat=True)))
print("retained ids for 'foo bar':", ids)
# No single child has both 'foo' and 'bar' -> instance must be excluded.
if ids == []:
    print("OK: instance excluded (no single related row matches both words)")
    raise SystemExit(0)
else:
    print("FAIL: instance retained -> over-matching across different related rows")
    raise SystemExit(1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance django__django-15022: ModelAdmin.get_search_results must narrow with a SINGLE combined filter so words matched through the same multi-valued relation share one related row.

Probes (all run in the official docker image):
- probe_1.py (Req 1.1/1.2, POSITIVE CONTROL): search_fields=['children__name'], parent p has children 'foo' and 'bar' (no single child has both). Search 'foo bar' -> instance MUST be excluded. VIOLATED at base (retained id [1]); HOLDS patched (retained []). Discriminates.
- probe_2.py (Req 1.3): one child 'foo bar baz' matches both words -> instance retained. HOLDS patched.
- probe_3.py (Req 1.4/5.1): search_fields=['name','children__name']; word matching parent's own field combines independently with a relation word; only the matching parent retained. HOLDS patched.
- probe_4.py (Req 3.1/4.1): empty term and no-search-fields return the SAME queryset object with boolean dup=False. HOLDS patched.
- probe_5.py (Req 3.2/3.3/5.2): quoted literal grouping ('"hello world"' = one word), '^' istartswith, '=' iexact prefixes, and multi-word non-satisfiable exclusion. HOLDS patched.
- probe_6.py (Req 4.2/4.3): multi-valued relation search field reports may_have_duplicates=True; single-valued reports False. HOLDS patched.
- probe_7.py (Req 2.2/2.3/5.1): repeated word over one multi-valued field retains when one row matches; single-valued multi-word retain is order-independent. HOLDS patched.

All 7 probes HOLD on the gold-patched tree.

Candidate wrong-fix (weak_partial.diff): collects per-word or_queries into a list but STILL applies them as separate chained .filter() calls (the semantic equivalent of the base bug — separate joins per word). It applies cleanly at base_commit and passes the regression probes (4,5,6) but is REJECTED by probe_1 (over-matches: retains id [1] for 'foo bar'), demonstrating the suite discriminates a plausible partial fix that would not resolve the hidden FAIL_TO_PASS tests (test_many_search_terms / multi-valued relationship search).

Protocol satisfied: >=5 distinct probes covering behavioral SHALLs, boundaries, and 'SHALL keep' regressions; positive control fails at base and holds patched; >=1 candidate exercised and REJECTED.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** The gold patch collapses per-word queryset.filter() calls into a single queryset.filter(models.Q(*term_queries)) so words matched through one multi-valued relation must be satisfied by the same related row. The requirements model the changed OBSERVABLE behavior (combined AND-of-OR single filter) at the correct boundary, and Req 1.4 correctly carves out the mixed own-field/other-relation case. The earlier G-PANEL-2 UNFAITHFUL verdict was a misjudgment: it treated the Mary/Daniel retention as a violation, but Req 1.4 predicts it. Reqs 3 (preserved behaviors) and 4 (may_have_duplicates unchanged) also match the patch, which leaves the duplicate logic untouched. Verdict: FAITHFUL.

Counterexample / evidence:

```
None. Probes on gold-patched tree: A ['name','child__name'] 'Mary Daniel'=1 (Req1.4); B ['child__name','child__age'] 'danielle 19'=0 (Req1.2); C 'daniel 19'=1 (Req1.3); D two children 'daniel 99'=0 (over-match fixed, Req1.1/1.2); E empty term=unchanged 3/3 (Req3.1); F 'daniel '*80 count=1 with exactly 1 JOIN (Req2.2); G ['name'] 'Mary Daniel'=0 (Req5.2); H ['name'] 'Mary'=1 (Req5.1). All consistent with the requirements.
```


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The requirements describe the fix behaviorally without transmitting the hidden evaluation. Legitimate localization only: names ModelAdmin.get_search_results and django/contrib/admin/options.py (the changed symbol/file). No test names/paths (test_many_search_terms, test_related_field_multiple_search_terms), no parametrization values ('daniel '*80, JOIN==1, 'danielle 19'->0, 'daniel 19'->1, 'Mary Jonathan Duo'->0), no quoted test/gold code, and no fix-invented identifier (gold's `term_queries`/`models.Q(*term_queries)` never appears). Closest calls: (a) line 18 uses `child__name` as the illustrative multi-valued relation — this matches the test fixture rather than the problem_statement's `clientoffice__name` example, but it is used only as a generic Django relation-path idiom, not to reconstruct the test; (b) Req 2.2 ('many repetitions of the same word ... exactly one join') echoes test_many_search_terms, but the bounded-join-per-word property is already the public problem_statement's central complaint, so this is a behavioral translation, not test leakage. The same-related-row correctness semantics are derived from the described defect, not from enumerating the parametrized cases.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
