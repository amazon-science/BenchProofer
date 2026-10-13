# P2 adversarial audit — django__django-16938

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 requirement probes hold on the patched tree; 2/2 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 7 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 7 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py`, `probe_7.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 2 alternative candidate patches, claimed to satisfy every cited requirement, and ran the same suite against them. The suite rejected all 2: a probe encoding a cited requirement fails under each of those, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (7):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
import sys, types
import django
from django.conf import settings
if not settings.configured:
    settings.configure(
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
        INSTALLED_APPS=["django.contrib.contenttypes", "testapp"],
        DEFAULT_AUTO_FIELD="django.db.models.AutoField",
        USE_TZ=False, DEBUG=True,
    )
    _m = types.ModuleType("testapp"); _m.__path__ = ["/work"]
    sys.modules["testapp"] = _m
    django.setup()
from django.db import models, connection
from django.core import serializers

class Master(models.Model):
    name = models.CharField(max_length=120)
    class Meta: app_label = "testapp"

class TagManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().select_related("master")

class Tag(models.Model):
    name = models.CharField(max_length=120)
    master = models.ForeignKey(Master, on_delete=models.SET_NULL, null=True)
    objects = TagManager()
    class Meta: app_label = "testapp"

class NatManager(models.Manager):
    def get_by_natural_key(self, code):
        return self.get(code=code)

class Nat(models.Model):
    code = models.CharField(max_length=120, unique=True)
    extra = models.CharField(max_length=120, default="x")
    objects = NatManager()
    def natural_key(self):
        return (self.code,)
    class Meta: app_label = "testapp"

class Plain(models.Model):
    name = models.CharField(max_length=120)
    class Meta: app_label = "testapp"

class Test(models.Model):
    name = models.CharField(max_length=120)
    tags = models.ManyToManyField(Tag, blank=True)
    nats = models.ManyToManyField(Nat, blank=True)
    plains = models.ManyToManyField(Plain, blank=True)
    class Meta: app_label = "testapp"

def _build():
    with connection.schema_editor() as se:
        for m in (Master, Tag, Nat, Plain, Test):
            se.create_model(m)

_build()
master = Master.objects.create(name="m")
tag = Tag.objects.create(name="t", master=master)
t = Test.objects.create(name="test")
t.tags.add(tag)
try:
    out = serializers.serialize("json", [t])
except Exception as e:
    print("FieldError/exception raised:", type(e).__name__, e)
    sys.exit(1)
print("json serialized OK:", out)
import json
d = json.loads(out)
assert d[0]["fields"]["tags"] == [tag.pk], d
print("tags pk emitted:", d[0]["fields"]["tags"])
sys.exit(0)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
import sys, types
import django
from django.conf import settings
if not settings.configured:
    settings.configure(
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
        INSTALLED_APPS=["django.contrib.contenttypes", "testapp"],
        DEFAULT_AUTO_FIELD="django.db.models.AutoField",
        USE_TZ=False, DEBUG=True,
    )
    _m = types.ModuleType("testapp"); _m.__path__ = ["/work"]
    sys.modules["testapp"] = _m
    django.setup()
from django.db import models, connection
from django.core import serializers

class Master(models.Model):
    name = models.CharField(max_length=120)
    class Meta: app_label = "testapp"

class TagManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().select_related("master")

class Tag(models.Model):
    name = models.CharField(max_length=120)
    master = models.ForeignKey(Master, on_delete=models.SET_NULL, null=True)
    objects = TagManager()
    class Meta: app_label = "testapp"

class NatManager(models.Manager):
    def get_by_natural_key(self, code):
        return self.get(code=code)

class Nat(models.Model):
    code = models.CharField(max_length=120, unique=True)
    extra = models.CharField(max_length=120, default="x")
    objects = NatManager()
    def natural_key(self):
        return (self.code,)
    class Meta: app_label = "testapp"

class Plain(models.Model):
    name = models.CharField(max_length=120)
    class Meta: app_label = "testapp"

class Test(models.Model):
    name = models.CharField(max_length=120)
    tags = models.ManyToManyField(Tag, blank=True)
    nats = models.ManyToManyField(Nat, blank=True)
    plains = models.ManyToManyField(Plain, blank=True)
    class Meta: app_label = "testapp"

def _build():
    with connection.schema_editor() as se:
        for m in (Master, Tag, Nat, Plain, Test):
            se.create_model(m)

_build()
master = Master.objects.create(name="m")
tag = Tag.objects.create(name="t", master=master)
t = Test.objects.create(name="test")
t.tags.add(tag)
try:
    out = serializers.serialize("xml", [t])
except Exception as e:
    print("xml serialize raised:", type(e).__name__, e)
    sys.exit(1)
print("xml serialized OK")
assert ('<object pk="%d">' % tag.pk) in out, out
print("xml contains object pk element for tag")
sys.exit(0)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
import sys, types
import django
from django.conf import settings
if not settings.configured:
    settings.configure(
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
        INSTALLED_APPS=["django.contrib.contenttypes", "testapp"],
        DEFAULT_AUTO_FIELD="django.db.models.AutoField",
        USE_TZ=False, DEBUG=True,
    )
    _m = types.ModuleType("testapp"); _m.__path__ = ["/work"]
    sys.modules["testapp"] = _m
    django.setup()
from django.db import models, connection
from django.core import serializers

class Master(models.Model):
    name = models.CharField(max_length=120)
    class Meta: app_label = "testapp"

class TagManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().select_related("master")

class Tag(models.Model):
    name = models.CharField(max_length=120)
    master = models.ForeignKey(Master, on_delete=models.SET_NULL, null=True)
    objects = TagManager()
    class Meta: app_label = "testapp"

class NatManager(models.Manager):
    def get_by_natural_key(self, code):
        return self.get(code=code)

class Nat(models.Model):
    code = models.CharField(max_length=120, unique=True)
    extra = models.CharField(max_length=120, default="x")
    objects = NatManager()
    def natural_key(self):
        return (self.code,)
    class Meta: app_label = "testapp"

class Plain(models.Model):
    name = models.CharField(max_length=120)
    class Meta: app_label = "testapp"

class Test(models.Model):
    name = models.CharField(max_length=120)
    tags = models.ManyToManyField(Tag, blank=True)
    nats = models.ManyToManyField(Nat, blank=True)
    plains = models.ManyToManyField(Plain, blank=True)
    class Meta: app_label = "testapp"

def _build():
    with connection.schema_editor() as se:
        for m in (Master, Tag, Nat, Plain, Test):
            se.create_model(m)

_build()
master = Master.objects.create(name="m")
tag = Tag.objects.create(name="t", master=master)
t = Test.objects.create(name="test")
t.tags.add(tag)
from django.db import reset_queries
reset_queries()
out = serializers.serialize("json", [t])
qs = [q["sql"] for q in connection.queries]
# find the query that reads the Tag m2m relation (references the tag table)
tag_reads = [s for s in qs if "testapp_tag" in s and "select" in s.lower()]
print("tag-related SQL:")
for s in tag_reads:
    print("  ", s)
assert tag_reads, "no tag read query captured"
for s in tag_reads:
    if "master_id" in s:
        print("VIOLATION: FK column master_id selected in m2m query")
        sys.exit(1)
print("no m2m query selects master_id (pk-only preserved)")
sys.exit(0)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
import sys, types
import django
from django.conf import settings
if not settings.configured:
    settings.configure(
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
        INSTALLED_APPS=["django.contrib.contenttypes", "testapp"],
        DEFAULT_AUTO_FIELD="django.db.models.AutoField",
        USE_TZ=False, DEBUG=True,
    )
    _m = types.ModuleType("testapp"); _m.__path__ = ["/work"]
    sys.modules["testapp"] = _m
    django.setup()
from django.db import models, connection
from django.core import serializers

class Master(models.Model):
    name = models.CharField(max_length=120)
    class Meta: app_label = "testapp"

class TagManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().select_related("master")

class Tag(models.Model):
    name = models.CharField(max_length=120)
    master = models.ForeignKey(Master, on_delete=models.SET_NULL, null=True)
    objects = TagManager()
    class Meta: app_label = "testapp"

class NatManager(models.Manager):
    def get_by_natural_key(self, code):
        return self.get(code=code)

class Nat(models.Model):
    code = models.CharField(max_length=120, unique=True)
    extra = models.CharField(max_length=120, default="x")
    objects = NatManager()
    def natural_key(self):
        return (self.code,)
    class Meta: app_label = "testapp"

class Plain(models.Model):
    name = models.CharField(max_length=120)
    class Meta: app_label = "testapp"

class Test(models.Model):
    name = models.CharField(max_length=120)
    tags = models.ManyToManyField(Tag, blank=True)
    nats = models.ManyToManyField(Nat, blank=True)
    plains = models.ManyToManyField(Plain, blank=True)
    class Meta: app_label = "testapp"

def _build():
    with connection.schema_editor() as se:
        for m in (Master, Tag, Nat, Plain, Test):
            se.create_model(m)

_build()
p1 = Plain.objects.create(name="a")
p2 = Plain.objects.create(name="b")
t = Test.objects.create(name="test")
t.plains.add(p1, p2)
import json
out = serializers.serialize("json", [t])
d = json.loads(out)
got = d[0]["fields"]["plains"]
print("plains emitted:", got)
assert got == [p1.pk, p2.pk], got
sys.exit(0)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
import sys, types
import django
from django.conf import settings
if not settings.configured:
    settings.configure(
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
        INSTALLED_APPS=["django.contrib.contenttypes", "testapp"],
        DEFAULT_AUTO_FIELD="django.db.models.AutoField",
        USE_TZ=False, DEBUG=True,
    )
    _m = types.ModuleType("testapp"); _m.__path__ = ["/work"]
    sys.modules["testapp"] = _m
    django.setup()
from django.db import models, connection
from django.core import serializers

class Master(models.Model):
    name = models.CharField(max_length=120)
    class Meta: app_label = "testapp"

class TagManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().select_related("master")

class Tag(models.Model):
    name = models.CharField(max_length=120)
    master = models.ForeignKey(Master, on_delete=models.SET_NULL, null=True)
    objects = TagManager()
    class Meta: app_label = "testapp"

class NatManager(models.Manager):
    def get_by_natural_key(self, code):
        return self.get(code=code)

class Nat(models.Model):
    code = models.CharField(max_length=120, unique=True)
    extra = models.CharField(max_length=120, default="x")
    objects = NatManager()
    def natural_key(self):
        return (self.code,)
    class Meta: app_label = "testapp"

class Plain(models.Model):
    name = models.CharField(max_length=120)
    class Meta: app_label = "testapp"

class Test(models.Model):
    name = models.CharField(max_length=120)
    tags = models.ManyToManyField(Tag, blank=True)
    nats = models.ManyToManyField(Nat, blank=True)
    plains = models.ManyToManyField(Plain, blank=True)
    class Meta: app_label = "testapp"

def _build():
    with connection.schema_editor() as se:
        for m in (Master, Tag, Nat, Plain, Test):
            se.create_model(m)

_build()
n = Nat.objects.create(code="ncode", extra="stuff")
t = Test.objects.create(name="test")
t.nats.add(n)
import json
out = serializers.serialize("json", [t], use_natural_foreign_keys=True)
d = json.loads(out)
got = d[0]["fields"]["nats"]
print("nats emitted with natural keys:", got)
assert got == [["ncode"]], got
sys.exit(0)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
import sys, types
import django
from django.conf import settings
if not settings.configured:
    settings.configure(
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
        INSTALLED_APPS=["django.contrib.contenttypes", "testapp"],
        DEFAULT_AUTO_FIELD="django.db.models.AutoField",
        USE_TZ=False, DEBUG=True,
    )
    _m = types.ModuleType("testapp"); _m.__path__ = ["/work"]
    sys.modules["testapp"] = _m
    django.setup()
from django.db import models, connection
from django.core import serializers

class Master(models.Model):
    name = models.CharField(max_length=120)
    class Meta: app_label = "testapp"

class TagManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().select_related("master")

class Tag(models.Model):
    name = models.CharField(max_length=120)
    master = models.ForeignKey(Master, on_delete=models.SET_NULL, null=True)
    objects = TagManager()
    class Meta: app_label = "testapp"

class NatManager(models.Manager):
    def get_by_natural_key(self, code):
        return self.get(code=code)

class Nat(models.Model):
    code = models.CharField(max_length=120, unique=True)
    extra = models.CharField(max_length=120, default="x")
    objects = NatManager()
    def natural_key(self):
        return (self.code,)
    class Meta: app_label = "testapp"

class Plain(models.Model):
    name = models.CharField(max_length=120)
    class Meta: app_label = "testapp"

class Test(models.Model):
    name = models.CharField(max_length=120)
    tags = models.ManyToManyField(Tag, blank=True)
    nats = models.ManyToManyField(Nat, blank=True)
    plains = models.ManyToManyField(Plain, blank=True)
    class Meta: app_label = "testapp"

def _build():
    with connection.schema_editor() as se:
        for m in (Master, Tag, Nat, Plain, Test):
            se.create_model(m)

_build()
master = Master.objects.create(name="m")
tag = Tag.objects.create(name="t", master=master)
t = Test.objects.create(name="test")
t.tags.add(tag)
from django.db import reset_queries
# baseline without prefetch
reset_queries()
serializers.serialize("json", Test.objects.all())
n_plain = len(connection.queries)
reset_queries()
out = serializers.serialize("json", Test.objects.prefetch_related("tags", "nats", "plains"))
n_pref = len(connection.queries)
print("queries plain=%d prefetch=%d" % (n_plain, n_pref))
import json
d = json.loads(out)
assert d[0]["fields"]["tags"] == [tag.pk], d
# with prefetch, the m2m sets come from cache: total queries should be the
# prefetch queries (1 base + 3 prefetch = 4), NOT re-issuing per-object m2m reads.
assert n_pref <= 4, "prefetch cache not used, %d queries" % n_pref
print("prefetched cache used (%d queries)" % n_pref)
sys.exit(0)
```

Attack 7 — `probe_7.py` → holds on the patched tree (good)

```python
import sys, types
import django
from django.conf import settings
if not settings.configured:
    settings.configure(
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
        INSTALLED_APPS=["django.contrib.contenttypes", "testapp"],
        DEFAULT_AUTO_FIELD="django.db.models.AutoField",
        USE_TZ=False, DEBUG=True,
    )
    _m = types.ModuleType("testapp"); _m.__path__ = ["/work"]
    sys.modules["testapp"] = _m
    django.setup()
from django.db import models, connection
from django.core import serializers

class Master(models.Model):
    name = models.CharField(max_length=120)
    class Meta: app_label = "testapp"

class TagManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().select_related("master")

class Tag(models.Model):
    name = models.CharField(max_length=120)
    master = models.ForeignKey(Master, on_delete=models.SET_NULL, null=True)
    objects = TagManager()
    class Meta: app_label = "testapp"

class NatManager(models.Manager):
    def get_by_natural_key(self, code):
        return self.get(code=code)

class Nat(models.Model):
    code = models.CharField(max_length=120, unique=True)
    extra = models.CharField(max_length=120, default="x")
    objects = NatManager()
    def natural_key(self):
        return (self.code,)
    class Meta: app_label = "testapp"

class Plain(models.Model):
    name = models.CharField(max_length=120)
    class Meta: app_label = "testapp"

class Test(models.Model):
    name = models.CharField(max_length=120)
    tags = models.ManyToManyField(Tag, blank=True)
    nats = models.ManyToManyField(Nat, blank=True)
    plains = models.ManyToManyField(Plain, blank=True)
    class Meta: app_label = "testapp"

def _build():
    with connection.schema_editor() as se:
        for m in (Master, Tag, Nat, Plain, Test):
            se.create_model(m)

_build()
master = Master.objects.create(name="m")
tags = [Tag.objects.create(name="t%d"%i, master=master) for i in range(4)]
t = Test.objects.create(name="test")
for tg in tags:
    t.tags.add(tg)
import json
out = serializers.serialize("json", [t])
got = json.loads(out)[0]["fields"]["tags"]
print("tags emitted:", got)
assert sorted(got) == sorted(tg.pk for tg in tags), got
assert len(got) == 4
sys.exit(0)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
import sys, types
import django
from django.conf import settings
if not settings.configured:
    settings.configure(
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
        INSTALLED_APPS=["django.contrib.contenttypes", "testapp"],
        DEFAULT_AUTO_FIELD="django.db.models.AutoField",
        USE_TZ=False, DEBUG=True,
    )
    _m = types.ModuleType("testapp"); _m.__path__ = ["/work"]
    sys.modules["testapp"] = _m
    django.setup()
from django.db import models, connection
from django.core import serializers

class Master(models.Model):
    name = models.CharField(max_length=120)
    class Meta: app_label = "testapp"

class TagManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().select_related("master")

class Tag(models.Model):
    name = models.CharField(max_length=120)
    master = models.ForeignKey(Master, on_delete=models.SET_NULL, null=True)
    objects = TagManager()
    class Meta: app_label = "testapp"

class NatManager(models.Manager):
    def get_by_natural_key(self, code):
        return self.get(code=code)

class Nat(models.Model):
    code = models.CharField(max_length=120, unique=True)
    extra = models.CharField(max_length=120, default="x")
    objects = NatManager()
    def natural_key(self):
        return (self.code,)
    class Meta: app_label = "testapp"

class Plain(models.Model):
    name = models.CharField(max_length=120)
    class Meta: app_label = "testapp"

class Test(models.Model):
    name = models.CharField(max_length=120)
    tags = models.ManyToManyField(Tag, blank=True)
    nats = models.ManyToManyField(Nat, blank=True)
    plains = models.ManyToManyField(Plain, blank=True)
    class Meta: app_label = "testapp"

def _build():
    with connection.schema_editor() as se:
        for m in (Master, Tag, Nat, Plain, Test):
            se.create_model(m)

_build()
master = Master.objects.create(name="m")
tag = Tag.objects.create(name="t", master=master)
t = Test.objects.create(name="test")
t.tags.add(tag)
try:
    out = serializers.serialize("json", [t])
except Exception as e:
    print("FieldError/exception raised:", type(e).__name__, e)
    sys.exit(1)
print("json serialized OK:", out)
import json
d = json.loads(out)
assert d[0]["fields"]["tags"] == [tag.pk], d
print("tags pk emitted:", d[0]["fields"]["tags"])
sys.exit(0)
```

Prepatch bug re-encoded as an attack: `True`.

Bundle django__django-16938: m2m serialization fails FieldError when the related model's manager uses select_related; gold fix inserts .select_related() before .only('pk') in both python.py and xml_serializer.py.

Probe suite (all self-contained; each rebuilds an in-memory sqlite schema with a select_related-using TagManager, a natural-key Nat model, and a plain-manager Plain model):
- probe_1 (Req 1.1 / positive control): json serialize of an object whose m2m points at Tag (select_related('master') manager) completes without FieldError and emits tag pk. HOLDS patched; VIOLATED at base with exact 'Field Tag.master cannot be both deferred and traversed using select_related' FieldError => discriminates.
- probe_2 (Req 5.2): same for xml. HOLDS patched, fails base.
- probe_3 (Req 2.1): executed SQL for the m2m read does NOT select the FK column master_id (pk-only preserved). HOLDS patched.
- probe_4 (Req 1.3/2.2): plain m2m (no select_related) emits ordered pk list unchanged.
- probe_5 (Req 3.1): use_natural_foreign_keys emits natural key [['ncode']] not pk.
- probe_6 (Req 4.1): prefetch_related uses the prefetched cache (<=4 queries, no per-object m2m re-query).
- probe_7 (Req 2.3): all 4 related tags iterated/emitted.

All 7 HOLD on the gold-patched tree. Positive control fails at base (prepatch reproduced).

Candidate wrong-fixes both REJECTED by the suite:
- candA_partial: only python.py fixed, xml left broken. Rejected by probe_2 (xml still raises FieldError). Would fail the hidden xml tests.
- candB_droponly: clears select_related but drops the .only('pk') restriction (select_related(None) with no only). Resolves the FieldError but loads all columns incl master_id. Rejected by probe_3 (m2m query selects master_id => violates test_serialize_only_pk assertion that category_id/master_id not in SQL).

Suite discriminates base, the correct fix, and two plausible weak fixes. Verdict SOUND. (Note: meta.json records a separate G-PANEL-3 leakage fail re Requirement 6 enumerating hidden-test behaviors; that is a leakage concern, orthogonal to spec-fidelity/too-weak which is what G-EQ tests here.)

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 requirement probes hold on the patched tree; 2/2 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 7 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 7 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py`, `probe_7.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 2 alternative candidate patches, claimed to satisfy every cited requirement, and ran the same suite against them. The suite rejected all 2: a probe encoding a cited requirement fails under each of those, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

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
import sys, types
import django
from django.conf import settings
if not settings.configured:
    settings.configure(
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
        INSTALLED_APPS=["django.contrib.contenttypes", "testapp"],
        DEFAULT_AUTO_FIELD="django.db.models.AutoField",
        USE_TZ=False, DEBUG=True,
    )
    _m = types.ModuleType("testapp"); _m.__path__ = ["/work"]
    sys.modules["testapp"] = _m
    django.setup()
from django.db import models, connection
from django.core import serializers

class Master(models.Model):
    name = models.CharField(max_length=120)
    class Meta: app_label = "testapp"

class TagManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().select_related("master")

class Tag(models.Model):
    name = models.CharField(max_length=120)
    master = models.ForeignKey(Master, on_delete=models.SET_NULL, null=True)
    objects = TagManager()
    class Meta: app_label = "testapp"

class NatManager(models.Manager):
    def get_by_natural_key(self, code):
        return self.get(code=code)

class Nat(models.Model):
    code = models.CharField(max_length=120, unique=True)
    extra = models.CharField(max_length=120, default="x")
    objects = NatManager()
    def natural_key(self):
        return (self.code,)
    class Meta: app_label = "testapp"

class Plain(models.Model):
    name = models.CharField(max_length=120)
    class Meta: app_label = "testapp"

class Test(models.Model):
    name = models.CharField(max_length=120)
    tags = models.ManyToManyField(Tag, blank=True)
    nats = models.ManyToManyField(Nat, blank=True)
    plains = models.ManyToManyField(Plain, blank=True)
    class Meta: app_label = "testapp"

def _build():
    with connection.schema_editor() as se:
        for m in (Master, Tag, Nat, Plain, Test):
            se.create_model(m)

_build()
master = Master.objects.create(name="m")
tag = Tag.objects.create(name="t", master=master)
t = Test.objects.create(name="test")
t.tags.add(tag)
try:
    out = serializers.serialize("json", [t])
except Exception as e:
    print("FieldError/exception raised:", type(e).__name__, e)
    sys.exit(1)
print("json serialized OK:", out)
import json
d = json.loads(out)
assert d[0]["fields"]["tags"] == [tag.pk], d
print("tags pk emitted:", d[0]["fields"]["tags"])
sys.exit(0)
```

Prepatch bug re-encoded as an attack: `True`.

Bundle django__django-16938: m2m serialization fails FieldError when the related model's manager uses select_related; gold fix inserts .select_related() before .only('pk') in both python.py and xml_serializer.py.

Probe suite (all self-contained; each rebuilds an in-memory sqlite schema with a select_related-using TagManager, a natural-key Nat model, and a plain-manager Plain model):
- probe_1 (Req 1.1 / positive control): json serialize of an object whose m2m points at Tag (select_related('master') manager) completes without FieldError and emits tag pk. HOLDS patched; VIOLATED at base with exact 'Field Tag.master cannot be both deferred and traversed using select_related' FieldError => discriminates.
- probe_2 (Req 5.2): same for xml. HOLDS patched, fails base.
- probe_3 (Req 2.1): executed SQL for the m2m read does NOT select the FK column master_id (pk-only preserved). HOLDS patched.
- probe_4 (Req 1.3/2.2): plain m2m (no select_related) emits ordered pk list unchanged.
- probe_5 (Req 3.1): use_natural_foreign_keys emits natural key [['ncode']] not pk.
- probe_6 (Req 4.1): prefetch_related uses the prefetched cache (<=4 queries, no per-object m2m re-query).
- probe_7 (Req 2.3): all 4 related tags iterated/emitted.

All 7 HOLD on the gold-patched tree. Positive control fails at base (prepatch reproduced).

Candidate wrong-fixes both REJECTED by the suite:
- candA_partial: only python.py fixed, xml left broken. Rejected by probe_2 (xml still raises FieldError). Would fail the hidden xml tests.
- candB_droponly: clears select_related but drops the .only('pk') restriction (select_related(None) with no only). Resolves the FieldError but loads all columns incl master_id. Rejected by probe_3 (m2m query selects master_id => violates test_serialize_only_pk assertion that category_id/master_id not in SQL).

Suite discriminates base, the correct fix, and two plausible weak fixes. Verdict SOUND. (Note: meta.json records a separate G-PANEL-3 leakage fail re Requirement 6 enumerating hidden-test behaviors; that is a leakage concern, orthogonal to spec-fidelity/too-weak which is what G-EQ tests here.)

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Gold patch: getattr(obj, field.name).only('pk') -> getattr(obj, field.name).select_related().only('pk') in both python.py handle_m2m_field and xml_serializer.py handle_m2m. The argless .select_related() clears any inherited field-restricted select_related state before .only('pk'), exactly the 'neutralize inherited select_related' behavior R1.2 pins. Requirements pin the changed observable behavior (serialization succeeds regardless of manager select_related, still pk-only, both backends), not a narrow slice. Base fail / patched pass both verified live via nl_attack probe (--base and default).


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The requirements localize the change (handle_m2m_field in python.py, handle_m2m in xml_serializer.py) — legitimate — and translate the defect into behavioral requirements. The select_related('master') example and the FieldError message both originate in the PUBLIC problem_statement, not the hidden tests. The hidden tests introduce Topic/TopicManager/select_related('category'), a topics m2m field, and specific query-count assertions (3->4, 5->7); NONE of these test-specific identifiers, the test file paths/function names, or the parametrization appear in requirements.md. Requirements 3 (natural-key path) and 4 (prefetched _prefetched_objects_cache) describe pre-existing serializer behavior visible in gold-patch context, not fix-invented identifiers, and are behavioral rather than test-shaped. The 'neutralize inherited select_related' phrasing describes the fix's behavior (derivable from the public conflict between select_related and only) without quoting the gold's .select_related() code line. No semantic gold/test reconstruction beyond legitimate localization.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
