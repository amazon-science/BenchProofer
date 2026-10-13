# P2 adversarial audit — django__django-16256

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
"""Probe 1 (POSITIVE CONTROL) — Req1.1/1.3 + Req4.2:
acreate on a reverse many-to-one related manager creates the object AND binds
the FK to the owning instance, and the object is retrievable through that same
manager. On base, acreate is inherited from the queryset -> unscoped ->
NOT retrievable through the scoped manager (or errors). Exit 0 iff it holds.
"""
import os, sys, tempfile, asyncio

def boot():
    d = tempfile.mkdtemp()
    os.makedirs(d + "/probeapp")
    open(d + "/probeapp/__init__.py", "w").write("")
    open(d + "/probeapp/models.py", "w").write('''
from django.db import models
class SimpleModel(models.Model):
    field = models.IntegerField(default=0)
class RelatedModel(models.Model):
    simple = models.ForeignKey(SimpleModel, models.CASCADE, null=True)
''')
    sys.path.insert(0, d)
    from django.conf import settings
    settings.configure(
        DEBUG=True,
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": d + "/db.sqlite3"}},
        INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth", "probeapp"],
        USE_TZ=True, DEFAULT_AUTO_FIELD="django.db.models.AutoField",
    )
    import django
    django.setup()
    from django.db import connection
    import probeapp.models as m
    with connection.schema_editor() as se:
        se.create_model(m.SimpleModel)
        se.create_model(m.RelatedModel)
    return m

m = boot()

async def run():
    from asgiref.sync import sync_to_async
    s1 = await sync_to_async(m.SimpleModel.objects.create)(field=0)
    # acreate on reverse FK manager
    obj = await s1.relatedmodel_set.acreate()
    # Req1.2: returns the created object
    assert obj is not None and obj.pk is not None, "acreate did not return persisted object"
    # Req1.3: FK bound to owning instance
    fetched = await s1.relatedmodel_set.aget()
    ok_bind = (fetched.pk == obj.pk)
    ok_fk = (obj.simple_id == s1.pk)
    print(f"created pk={obj.pk} simple_id={obj.simple_id} owner={s1.pk} retrievable={ok_bind}")
    return ok_bind and ok_fk

try:
    ok = asyncio.run(run())
except Exception as e:
    import traceback; traceback.print_exc()
    print("EXCEPTION:", repr(e))
    sys.exit(1)
sys.exit(0 if ok else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""Probe 2 — Req1.1/1.5: acreate on the many-to-many related manager creates
the association (object appears in the relation) AND an optional
through_defaults mapping is accepted and applied to the intermediate row.
Uses an explicit through model with an extra field so 'applied' is observable.
Exit 0 iff created object is in the relation and through row got the default.
"""
import os, sys, tempfile, asyncio

def boot():
    d = tempfile.mkdtemp()
    os.makedirs(d + "/probeapp")
    open(d + "/probeapp/__init__.py", "w").write("")
    open(d + "/probeapp/models.py", "w").write('''
from django.db import models
class SimpleModel(models.Model):
    field = models.IntegerField(default=0)
class ManyToManyModel(models.Model):
    simples = models.ManyToManyField(SimpleModel, through="Membership")
class Membership(models.Model):
    mtm = models.ForeignKey(ManyToManyModel, models.CASCADE)
    simple = models.ForeignKey(SimpleModel, models.CASCADE)
    note = models.CharField(max_length=50, default="")
''')
    sys.path.insert(0, d)
    from django.conf import settings
    settings.configure(
        DEBUG=True,
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": d + "/db.sqlite3"}},
        INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth", "probeapp"],
        USE_TZ=True, DEFAULT_AUTO_FIELD="django.db.models.AutoField",
    )
    import django
    django.setup()
    from django.db import connection
    import probeapp.models as m
    with connection.schema_editor() as se:
        se.create_model(m.SimpleModel)
        se.create_model(m.ManyToManyModel)
        se.create_model(m.Membership)
    return m

m = boot()

async def run():
    from asgiref.sync import sync_to_async
    mtm = await sync_to_async(m.ManyToManyModel.objects.create)()
    obj = await mtm.simples.acreate(field=2, through_defaults={"note": "hi"})
    assert obj is not None and obj.pk is not None, "acreate returned no object"
    # appears in the relation
    ids = await sync_to_async(lambda: list(mtm.simples.values_list("pk", flat=True)))()
    in_rel = obj.pk in ids
    # through_defaults applied to intermediate row
    note = await sync_to_async(lambda: m.Membership.objects.get(mtm=mtm, simple=obj).note)()
    print(f"created pk={obj.pk} in_relation={in_rel} through_note={note!r}")
    return in_rel and note == "hi" and obj.field == 2

try:
    ok = asyncio.run(run())
except Exception as e:
    import traceback; traceback.print_exc(); print("EXCEPTION:", repr(e)); sys.exit(1)
sys.exit(0 if ok else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""Probe 3 — Req1.1/1.4: acreate on the GENERIC related manager sets
content-type + object-id to the owning instance, and the object is retrievable
through that same manager. Exit 0 iff bound + retrievable.
"""
import os, sys, tempfile, asyncio

def boot():
    d = tempfile.mkdtemp()
    os.makedirs(d + "/probeapp")
    open(d + "/probeapp/__init__.py", "w").write("")
    open(d + "/probeapp/models.py", "w").write('''
from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
class Bookmark(models.Model):
    url = models.CharField(max_length=200, default="")
    tags = GenericRelation("TaggedItem")
class TaggedItem(models.Model):
    tag = models.SlugField()
    content_type = models.ForeignKey(ContentType, models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey()
''')
    sys.path.insert(0, d)
    from django.conf import settings
    settings.configure(
        DEBUG=True,
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": d + "/db.sqlite3"}},
        INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth", "probeapp"],
        USE_TZ=True, DEFAULT_AUTO_FIELD="django.db.models.AutoField",
    )
    import django
    django.setup()
    from django.core.management import call_command
    call_command("migrate", "contenttypes", verbosity=0)
    from django.db import connection
    import probeapp.models as m
    with connection.schema_editor() as se:
        se.create_model(m.Bookmark)
        se.create_model(m.TaggedItem)
    return m

m = boot()

async def run():
    from asgiref.sync import sync_to_async
    bm = await sync_to_async(m.Bookmark.objects.create)(url="http://x")
    mgr = await sync_to_async(lambda: bm.tags)()
    obj = await mgr.acreate(tag="django")
    assert obj is not None and obj.pk is not None, "generic acreate returned no object"

    def inspect():
        from django.contrib.contenttypes.models import ContentType
        ct = ContentType.objects.get_for_model(m.Bookmark)
        ok_ct = (obj.content_type_id == ct.id)
        ok_oid = (obj.object_id == bm.pk)
        ok_ret = (bm.tags.get().pk == obj.pk)
        return ok_ct, ok_oid, ok_ret
    ok_ct, ok_oid, ok_ret = await sync_to_async(inspect)()
    print(f"tag pk={obj.pk} ct_ok={ok_ct} oid={obj.object_id} owner={bm.pk} retrievable={ok_ret}")
    return ok_ct and ok_oid and ok_ret

try:
    ok = asyncio.run(run())
except Exception as e:
    import traceback
    tb = traceback.extract_tb(sys.exc_info()[2])
    uf = [f for f in tb if "probe_impl" in f.filename]
    print("EXC:", type(e).__name__, str(e)[:120], "| userframe:", uf[-1].line if uf else "?")
    sys.exit(1)
sys.exit(0 if ok else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""Probe 4 — Req2 (aget_or_create) + Req3 (aupdate_or_create) on a reverse
many-to-one manager, scope-bound.
- aget_or_create first call -> created True, FK bound.
- aget_or_create second identical call -> created False, no duplicate.
- aupdate_or_create on existing -> updates defaults, created False.
Exit 0 iff all hold.
"""
import os, sys, tempfile, asyncio

def boot():
    d = tempfile.mkdtemp()
    os.makedirs(d + "/probeapp")
    open(d + "/probeapp/__init__.py", "w").write("")
    open(d + "/probeapp/models.py", "w").write('''
from django.db import models
class SimpleModel(models.Model):
    field = models.IntegerField(default=0)
class RelatedModel(models.Model):
    simple = models.ForeignKey(SimpleModel, models.CASCADE, null=True)
    field = models.IntegerField(default=0)
    name = models.CharField(max_length=50, default="")
''')
    sys.path.insert(0, d)
    from django.conf import settings
    settings.configure(
        DEBUG=True,
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": d + "/db.sqlite3"}},
        INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth", "probeapp"],
        USE_TZ=True, DEFAULT_AUTO_FIELD="django.db.models.AutoField",
    )
    import django
    django.setup()
    from django.db import connection
    import probeapp.models as m
    with connection.schema_editor() as se:
        se.create_model(m.SimpleModel)
        se.create_model(m.RelatedModel)
    return m

m = boot()

async def run():
    from asgiref.sync import sync_to_async
    s1 = await sync_to_async(m.SimpleModel.objects.create)(field=0)
    # get_or_create: creates
    obj, created = await s1.relatedmodel_set.aget_or_create(name="a")
    c1 = created is True and obj.simple_id == s1.pk
    # second identical: not created, no dup
    obj2, created2 = await s1.relatedmodel_set.aget_or_create(name="a")
    n = await s1.relatedmodel_set.acount()
    c2 = created2 is False and obj2.pk == obj.pk and n == 1
    # update_or_create existing: updates defaults, created False
    obj3, created3 = await s1.relatedmodel_set.aupdate_or_create(
        name="a", defaults={"field": 99})
    obj3_ref = await sync_to_async(lambda: m.RelatedModel.objects.get(pk=obj.pk))()
    c3 = created3 is False and obj3_ref.field == 99 and obj3.simple_id == s1.pk
    # update_or_create new: creates
    obj4, created4 = await s1.relatedmodel_set.aupdate_or_create(
        name="b", defaults={"field": 7})
    c4 = created4 is True and obj4.simple_id == s1.pk and obj4.field == 7
    print(f"goc_create={c1} goc_existing={c2} uoc_update={c3} uoc_create={c4} count={n}")
    return c1 and c2 and c3 and c4

try:
    ok = asyncio.run(run())
except Exception as e:
    import traceback; traceback.print_exc(); print("EXCEPTION:", repr(e)); sys.exit(1)
sys.exit(0 if ok else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""Probe 5 — Req1.7/2.7/3.7 + Req4.1: the async helpers are defined DIRECTLY on
each affected related manager (not inherited from the queryset), and each is
marked alters_data=True. We assert the function objects live on the manager
INSTANCE's own class (bound method whose __func__ is defined in the manager
class dict, not merely inherited from QuerySet) and carry alters_data.
Exit 0 iff acreate/aget_or_create/aupdate_or_create on the reverse-FK, m2m, and
generic managers are all own-attributes with alters_data True.
"""
import os, sys, tempfile

def boot():
    d = tempfile.mkdtemp()
    os.makedirs(d + "/probeapp")
    open(d + "/probeapp/__init__.py", "w").write("")
    open(d + "/probeapp/models.py", "w").write('''
from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
class SimpleModel(models.Model):
    field = models.IntegerField(default=0)
class RelatedModel(models.Model):
    simple = models.ForeignKey(SimpleModel, models.CASCADE, null=True)
class ManyToManyModel(models.Model):
    simples = models.ManyToManyField(SimpleModel)
class Bookmark(models.Model):
    url = models.CharField(max_length=200, default="")
    tags = GenericRelation("TaggedItem")
class TaggedItem(models.Model):
    tag = models.SlugField()
    content_type = models.ForeignKey(ContentType, models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey()
''')
    sys.path.insert(0, d)
    from django.conf import settings
    settings.configure(
        DEBUG=True,
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": d + "/db.sqlite3"}},
        INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth", "probeapp"],
        USE_TZ=True, DEFAULT_AUTO_FIELD="django.db.models.AutoField",
    )
    import django
    django.setup()
    from django.core.management import call_command
    call_command("migrate", "contenttypes", verbosity=0)
    from django.db import connection
    import probeapp.models as m
    with connection.schema_editor() as se:
        se.create_model(m.SimpleModel); se.create_model(m.RelatedModel)
        se.create_model(m.ManyToManyModel)
        se.create_model(m.Bookmark); se.create_model(m.TaggedItem)
    return m

m = boot()

from django.contrib.contenttypes.models import ContentType
from django.db.models.query import QuerySet

NAMES = ["acreate", "aget_or_create", "aupdate_or_create"]

def check(mgr, label):
    cls = type(mgr)
    ok = True
    for n in NAMES:
        # must exist
        if not hasattr(mgr, n):
            print(f"{label}: MISSING {n}"); ok = False; continue
        fn = getattr(mgr, n)
        func = getattr(fn, "__func__", fn)
        # must NOT be the QuerySet's own inherited implementation:
        qs_fn = getattr(QuerySet, n, None)
        qs_func = getattr(qs_fn, "__func__", qs_fn)
        own = func is not qs_func
        alters = getattr(func, "alters_data", False)
        print(f"{label}.{n}: own={own} alters_data={alters}")
        if not (own and alters):
            ok = False
    return ok

s1 = m.SimpleModel.objects.create(field=0)
rev = s1.relatedmodel_set
mtm = m.ManyToManyModel.objects.create()
m2m = mtm.simples
bm = m.Bookmark.objects.create(url="u")
gen = bm.tags

ok = check(rev, "reverse-fk") & check(m2m, "m2m") & check(gen, "generic")
sys.exit(0 if ok else 1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
"""Probe 6 — Req5 (SHALL keep): existing SYNCHRONOUS helpers and other
related-manager operations remain unchanged.
- sync create on reverse FK binds owner (Req5.1).
- sync m2m create with through_defaults applies to intermediate (Req5.3).
- add/remove/clear still work (Req5.2).
- create.alters_data still True (Req5.1).
Exit 0 iff all hold. (These behaviors exist at base too; this is a regression
guard against a fix that damages sync paths.)
"""
import os, sys, tempfile

def boot():
    d = tempfile.mkdtemp()
    os.makedirs(d + "/probeapp")
    open(d + "/probeapp/__init__.py", "w").write("")
    open(d + "/probeapp/models.py", "w").write('''
from django.db import models
class SimpleModel(models.Model):
    field = models.IntegerField(default=0)
class RelatedModel(models.Model):
    simple = models.ForeignKey(SimpleModel, models.CASCADE, null=True)
class ManyToManyModel(models.Model):
    simples = models.ManyToManyField(SimpleModel, through="Membership")
class Membership(models.Model):
    mtm = models.ForeignKey(ManyToManyModel, models.CASCADE)
    simple = models.ForeignKey(SimpleModel, models.CASCADE)
    note = models.CharField(max_length=50, default="")
''')
    sys.path.insert(0, d)
    from django.conf import settings
    settings.configure(
        DEBUG=True,
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": d + "/db.sqlite3"}},
        INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth", "probeapp"],
        USE_TZ=True, DEFAULT_AUTO_FIELD="django.db.models.AutoField",
    )
    import django
    django.setup()
    from django.db import connection
    import probeapp.models as m
    with connection.schema_editor() as se:
        se.create_model(m.SimpleModel); se.create_model(m.RelatedModel)
        se.create_model(m.ManyToManyModel); se.create_model(m.Membership)
    return m

m = boot()

s1 = m.SimpleModel.objects.create(field=0)
# sync reverse create binds owner
r = s1.relatedmodel_set.create()
c_bind = r.simple_id == s1.pk and s1.relatedmodel_set.get().pk == r.pk
# create.alters_data
c_alters = getattr(type(s1.relatedmodel_set).create, "alters_data", False) or \
           getattr(s1.relatedmodel_set.create, "alters_data", False)
# sync m2m create with through_defaults
mtm = m.ManyToManyModel.objects.create()
obj = mtm.simples.create(field=5, through_defaults={"note": "z"})
c_m2m = obj.pk in list(mtm.simples.values_list("pk", flat=True))
c_note = m.Membership.objects.get(mtm=mtm, simple=obj).note == "z"
# add/remove/clear
s2 = m.SimpleModel.objects.create(field=1)
mtm.simples.add(s2)
c_add = s2.pk in list(mtm.simples.values_list("pk", flat=True))
mtm.simples.remove(s2)
c_rm = s2.pk not in list(mtm.simples.values_list("pk", flat=True))
mtm.simples.clear()
c_clear = mtm.simples.count() == 0
print(f"bind={c_bind} alters={c_alters} m2m={c_m2m} note={c_note} add={c_add} rm={c_rm} clear={c_clear}")
sys.exit(0 if all([c_bind, c_alters, c_m2m, c_note, c_add, c_rm, c_clear]) else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Probe 1 (POSITIVE CONTROL) — Req1.1/1.3 + Req4.2:
acreate on a reverse many-to-one related manager creates the object AND binds
the FK to the owning instance, and the object is retrievable through that same
manager. On base, acreate is inherited from the queryset -> unscoped ->
NOT retrievable through the scoped manager (or errors). Exit 0 iff it holds.
"""
import os, sys, tempfile, asyncio

def boot():
    d = tempfile.mkdtemp()
    os.makedirs(d + "/probeapp")
    open(d + "/probeapp/__init__.py", "w").write("")
    open(d + "/probeapp/models.py", "w").write('''
from django.db import models
class SimpleModel(models.Model):
    field = models.IntegerField(default=0)
class RelatedModel(models.Model):
    simple = models.ForeignKey(SimpleModel, models.CASCADE, null=True)
''')
    sys.path.insert(0, d)
    from django.conf import settings
    settings.configure(
        DEBUG=True,
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": d + "/db.sqlite3"}},
        INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth", "probeapp"],
        USE_TZ=True, DEFAULT_AUTO_FIELD="django.db.models.AutoField",
    )
    import django
    django.setup()
    from django.db import connection
    import probeapp.models as m
    with connection.schema_editor() as se:
        se.create_model(m.SimpleModel)
        se.create_model(m.RelatedModel)
    return m

m = boot()

async def run():
    from asgiref.sync import sync_to_async
    s1 = await sync_to_async(m.SimpleModel.objects.create)(field=0)
    # acreate on reverse FK manager
    obj = await s1.relatedmodel_set.acreate()
    # Req1.2: returns the created object
    assert obj is not None and obj.pk is not None, "acreate did not return persisted object"
    # Req1.3: FK bound to owning instance
    fetched = await s1.relatedmodel_set.aget()
    ok_bind = (fetched.pk == obj.pk)
    ok_fk = (obj.simple_id == s1.pk)
    print(f"created pk={obj.pk} simple_id={obj.simple_id} owner={s1.pk} retrievable={ok_bind}")
    return ok_bind and ok_fk

try:
    ok = asyncio.run(run())
except Exception as e:
    import traceback; traceback.print_exc()
    print("EXCEPTION:", repr(e))
    sys.exit(1)
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

6 probes cover the requirements' behavioral SHALLs, boundaries, and SHALL-keep regressions.

Results (base / gold-patched / weak_unscoped candidate):
- probe_1 POSITIVE CONTROL (R1.1/1.3/4.2 — acreate on reverse many-to-one manager creates object, binds FK to owner, retrievable via same manager): VIOLATED(base) / HOLDS(patched) / VIOLATED(weak). Discriminates.
- probe_2 (R1.1/1.5 — m2m acreate establishes through association; through_defaults applied to intermediate row): VIOLATED(base) / HOLDS / VIOLATED(weak).
- probe_3 (R1.1/1.4 — generic acreate sets content_type+object_id to owner, retrievable): VIOLATED(base) / HOLDS / VIOLATED(weak).
- probe_4 (R2 aget_or_create + R3 aupdate_or_create on reverse-FK: created flags, no duplicate, defaults update, scope binding): VIOLATED(base) / HOLDS / VIOLATED(weak).
- probe_5 (R1.7/2.7/3.7/4.1 — a{create,get_or_create,update_or_create} defined DIRECTLY on each of reverse-FK/m2m/generic managers, not inherited from QuerySet, and alters_data=True): VIOLATED(base, alters_data False because inherited) / HOLDS / HOLDS(weak — structural check, weak fix also defines own alters_data methods).
- probe_6 (R5 SHALL-keep — sync create scoping, m2m through_defaults, add/remove/clear, create.alters_data): HOLDS(base) / HOLDS / HOLDS. Regression guard.

Positive control fails at base and holds patched (prepatch reproduced). All 6 hold on the gold tree.

Candidate wrong-fix `weak_unscoped.diff`: async helpers that route through the plain/base manager (unscoped) instead of the scoped related-manager create — exactly the fix a weak reading of Req4 permits. It is REJECTED by probes 1-4 (unbound/unretrievable objects; generic raises IntegrityError on missing content_type). This demonstrates the suite discriminates a requirements-nonconforming implementation; no TOO-WEAK candidate found that passes every probe.

Infra notes: probes are standalone (build a tiny app via schema_editor / contenttypes migrate, file-backed sqlite so sync_to_async threads share the DB). Generic manager attribute access itself hits the DB, so the manager is materialized inside a sync_to_async block before awaiting acreate.

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
"""Probe 1 (POSITIVE CONTROL) — Req1.1/1.3 + Req4.2:
acreate on a reverse many-to-one related manager creates the object AND binds
the FK to the owning instance, and the object is retrievable through that same
manager. On base, acreate is inherited from the queryset -> unscoped ->
NOT retrievable through the scoped manager (or errors). Exit 0 iff it holds.
"""
import os, sys, tempfile, asyncio

def boot():
    d = tempfile.mkdtemp()
    os.makedirs(d + "/probeapp")
    open(d + "/probeapp/__init__.py", "w").write("")
    open(d + "/probeapp/models.py", "w").write('''
from django.db import models
class SimpleModel(models.Model):
    field = models.IntegerField(default=0)
class RelatedModel(models.Model):
    simple = models.ForeignKey(SimpleModel, models.CASCADE, null=True)
''')
    sys.path.insert(0, d)
    from django.conf import settings
    settings.configure(
        DEBUG=True,
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": d + "/db.sqlite3"}},
        INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth", "probeapp"],
        USE_TZ=True, DEFAULT_AUTO_FIELD="django.db.models.AutoField",
    )
    import django
    django.setup()
    from django.db import connection
    import probeapp.models as m
    with connection.schema_editor() as se:
        se.create_model(m.SimpleModel)
        se.create_model(m.RelatedModel)
    return m

m = boot()

async def run():
    from asgiref.sync import sync_to_async
    s1 = await sync_to_async(m.SimpleModel.objects.create)(field=0)
    # acreate on reverse FK manager
    obj = await s1.relatedmodel_set.acreate()
    # Req1.2: returns the created object
    assert obj is not None and obj.pk is not None, "acreate did not return persisted object"
    # Req1.3: FK bound to owning instance
    fetched = await s1.relatedmodel_set.aget()
    ok_bind = (fetched.pk == obj.pk)
    ok_fk = (obj.simple_id == s1.pk)
    print(f"created pk={obj.pk} simple_id={obj.simple_id} owner={s1.pk} retrievable={ok_bind}")
    return ok_bind and ok_fk

try:
    ok = asyncio.run(run())
except Exception as e:
    import traceback; traceback.print_exc()
    print("EXCEPTION:", repr(e))
    sys.exit(1)
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

6 probes cover the requirements' behavioral SHALLs, boundaries, and SHALL-keep regressions.

Results (base / gold-patched / weak_unscoped candidate):
- probe_1 POSITIVE CONTROL (R1.1/1.3/4.2 — acreate on reverse many-to-one manager creates object, binds FK to owner, retrievable via same manager): VIOLATED(base) / HOLDS(patched) / VIOLATED(weak). Discriminates.
- probe_2 (R1.1/1.5 — m2m acreate establishes through association; through_defaults applied to intermediate row): VIOLATED(base) / HOLDS / VIOLATED(weak).
- probe_3 (R1.1/1.4 — generic acreate sets content_type+object_id to owner, retrievable): VIOLATED(base) / HOLDS / VIOLATED(weak).
- probe_4 (R2 aget_or_create + R3 aupdate_or_create on reverse-FK: created flags, no duplicate, defaults update, scope binding): VIOLATED(base) / HOLDS / VIOLATED(weak).
- probe_5 (R1.7/2.7/3.7/4.1 — a{create,get_or_create,update_or_create} defined DIRECTLY on each of reverse-FK/m2m/generic managers, not inherited from QuerySet, and alters_data=True): VIOLATED(base, alters_data False because inherited) / HOLDS / HOLDS(weak — structural check, weak fix also defines own alters_data methods).
- probe_6 (R5 SHALL-keep — sync create scoping, m2m through_defaults, add/remove/clear, create.alters_data): HOLDS(base) / HOLDS / HOLDS. Regression guard.

Positive control fails at base and holds patched (prepatch reproduced). All 6 hold on the gold tree.

Candidate wrong-fix `weak_unscoped.diff`: async helpers that route through the plain/base manager (unscoped) instead of the scoped related-manager create — exactly the fix a weak reading of Req4 permits. It is REJECTED by probes 1-4 (unbound/unretrievable objects; generic raises IntegrityError on missing content_type). This demonstrates the suite discriminates a requirements-nonconforming implementation; no TOO-WEAK candidate found that passes every probe.

Infra notes: probes are standalone (build a tiny app via schema_editor / contenttypes migrate, file-backed sqlite so sync_to_async threads share the DB). Generic manager attribute access itself hits the DB, so the manager is materialized inside a sync_to_async block before awaiting acreate.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Patch adds 9 async methods (3 per manager). The requirements correctly describe: (a) presence on all three managers, (b) m2m manager serving both forward and reverse directions (single create_forward_many_to_many_manager serves both), (c) alters_data marking (Req 1.7/2.7/3.7), (d) scope binding equivalence to sync helpers (Req 6 in each), (e) through_defaults for m2m (Req 1.5/2.5/3.5), (f) queryset interface unchanged (Req 5.4). Modeling boundary is the changed observable behavior (new async scoped helpers), not a narrow slice. Probe confirmed HOLDS on patched, VIOLATED on base.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The requirements describe behavior for the three async related-manager helpers (acreate/aget_or_create/aupdate_or_create) across the reverse many-to-one, many-to-many, and generic related managers. All method names, the alters_data marking, sync_to_async delegation, related_descriptors.py, the manager-builder functions, and the through_defaults=None signature are already public in the problem_statement (which quotes the target diff). Naming contrib/contenttypes/fields.py and create_generic_related_manager is legitimate change localization (gold-patch file), transmitting no test content. None of the hidden-test identifiers appear: no test names/paths (test_acreate, test_async_related_managers, generic_relations.tests), no test model names (ManyToManyModel, SimpleModel, RelatedModel, relatedmodel_set), no fixture names (bacon/fatty/tags), no concrete case values (field=2, tag='orange', defaults={'field':3}), and no acount/aget usage. The three-block structure mirrors the manager TYPES (the patch's scope) not the 9 parametrized test cases; it describes behavior rather than reproducing test assertions. No fix-invented identifiers (the fix invents no new names). No leakage beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
