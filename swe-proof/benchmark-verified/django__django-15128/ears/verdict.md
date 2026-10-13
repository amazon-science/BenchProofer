# P2 adversarial audit — django__django-15128

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 9 requirement probes hold on the patched tree; 2/2 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 9 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 9 | `probe_1_or_no_crash.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py`, `probe_7.py`, `probe_8.py`, `probe_9.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 2 alternative candidate patches, claimed to satisfy every cited requirement, and ran the same suite against them. The suite rejected all 2: a probe encoding a cited requirement fails under each of those, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1_or_no_crash.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (9):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1_or_no_crash.py` → holds on the patched tree (good)

```python
import django, sys, types
from django.conf import settings
if not settings.configured:
    settings.configure(
        INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth", "probe_app"],
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
        DEFAULT_AUTO_FIELD="django.db.models.AutoField",
    )
_app = types.ModuleType("probe_app"); _app.__path__ = ["/work"]; _app.__file__ = "/work/probe_app_init.py"
sys.modules["probe_app"] = _app
import importlib.machinery
_app.__spec__ = importlib.machinery.ModuleSpec("probe_app", None, is_package=True)
_app.__spec__.submodule_search_locations = ["/work"]
_m = types.ModuleType("probe_app.models"); sys.modules["probe_app.models"] = _m
_m.__spec__ = importlib.machinery.ModuleSpec("probe_app.models", None)
_m.__file__ = "/work/probe_app_models.py"
django.setup()
from django.db import models

class Tag(models.Model):
    class Meta: app_label = "probe_app"
class Note(models.Model):
    tag = models.ForeignKey(Tag, models.CASCADE, null=True)
    class Meta: app_label = "probe_app"
class Annotation(models.Model):
    tag = models.ForeignKey(Tag, models.CASCADE)
    notes = models.ManyToManyField(Note)
    class Meta: app_label = "probe_app"
class BaseUser(models.Model):
    annotation = models.ForeignKey(Annotation, models.CASCADE, null=True, blank=True)
    class Meta: app_label = "probe_app"
class Task(models.Model):
    owner = models.ForeignKey(BaseUser, models.CASCADE, related_name="owner")
    creator = models.ForeignKey(BaseUser, models.CASCADE, related_name="creator")
    note = models.ForeignKey(Note, on_delete=models.CASCADE, null=True, blank=True)
    class Meta: app_label = "probe_app"
for _c in (Tag, Note, Annotation, BaseUser, Task):
    setattr(_m, _c.__name__, _c)

from django.db import connection
def create_schema():
    with connection.schema_editor() as se:
        for c in (Tag, Note, Annotation, BaseUser, Task):
            se.create_model(c)
        se.create_model(Annotation.notes.through)
def seed():
    tag = Tag.objects.create()
    a1 = Annotation.objects.create(tag=tag)
    a2 = Annotation.objects.create(tag=tag)
    note = a1.notes.create(tag=tag)
    bu1 = BaseUser.objects.create(annotation=a1)
    bu2 = BaseUser.objects.create(annotation=a2)
    Task.objects.create(owner=bu2, creator=bu2, note=note)
    return bu1, bu2, a1
# Requirement 1.1 / 2.1 + POSITIVE CONTROL: OR of two prefix-colliding querysets
# completes (both orders) without AssertionError.
from django.db.models import Q
a1 = Annotation(pk=1)
qs1 = a1.baseuser_set.all()
qs2 = BaseUser.objects.filter(
    Q(owner__note__in=Note.objects.filter(pk=1)) |
    Q(creator__note__in=Note.objects.filter(pk=1))
)
ok = True
try:
    str((qs2 | qs1).query)
    str((qs1 | qs2).query)
    print("both OR orders compiled without AssertionError")
except AssertionError as e:
    ok = False; print("AssertionError during OR combine:", repr(e))
sys.exit(0 if ok else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
import django, sys, types
from django.conf import settings
if not settings.configured:
    settings.configure(
        INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth", "probe_app"],
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
        DEFAULT_AUTO_FIELD="django.db.models.AutoField",
    )
_app = types.ModuleType("probe_app"); _app.__path__ = ["/work"]; _app.__file__ = "/work/probe_app_init.py"
sys.modules["probe_app"] = _app
import importlib.machinery
_app.__spec__ = importlib.machinery.ModuleSpec("probe_app", None, is_package=True)
_app.__spec__.submodule_search_locations = ["/work"]
_m = types.ModuleType("probe_app.models"); sys.modules["probe_app.models"] = _m
_m.__spec__ = importlib.machinery.ModuleSpec("probe_app.models", None)
_m.__file__ = "/work/probe_app_models.py"
django.setup()
from django.db import models

class Tag(models.Model):
    class Meta: app_label = "probe_app"
class Note(models.Model):
    tag = models.ForeignKey(Tag, models.CASCADE, null=True)
    class Meta: app_label = "probe_app"
class Annotation(models.Model):
    tag = models.ForeignKey(Tag, models.CASCADE)
    notes = models.ManyToManyField(Note)
    class Meta: app_label = "probe_app"
class BaseUser(models.Model):
    annotation = models.ForeignKey(Annotation, models.CASCADE, null=True, blank=True)
    class Meta: app_label = "probe_app"
class Task(models.Model):
    owner = models.ForeignKey(BaseUser, models.CASCADE, related_name="owner")
    creator = models.ForeignKey(BaseUser, models.CASCADE, related_name="creator")
    note = models.ForeignKey(Note, on_delete=models.CASCADE, null=True, blank=True)
    class Meta: app_label = "probe_app"
for _c in (Tag, Note, Annotation, BaseUser, Task):
    setattr(_m, _c.__name__, _c)

from django.db import connection
def create_schema():
    with connection.schema_editor() as se:
        for c in (Tag, Note, Annotation, BaseUser, Task):
            se.create_model(c)
def seed():
    tag = Tag.objects.create()
    a1 = Annotation.objects.create(tag=tag)
    a2 = Annotation.objects.create(tag=tag)
    note = a1.notes.create(tag=tag)
    bu1 = BaseUser.objects.create(annotation=a1)
    bu2 = BaseUser.objects.create(annotation=a2)
    Task.objects.create(owner=bu2, creator=bu2, note=note)
    return bu1, bu2, a1
# Requirement 2.2 / 2.3 / 1.3: with real data, (qs1|qs2) and (qs2|qs1) return
# the same rows, and that set is exactly {base_user_1, base_user_2}.
from django.db.models import Q
create_schema()
bu1, bu2, a1 = seed()
qs1 = a1.baseuser_set.all()
qs2 = BaseUser.objects.filter(
    Q(owner__note__in=a1.notes.all()) | Q(creator__note__in=a1.notes.all())
)
r_ab = sorted(x.pk for x in (qs1 | qs2))
r_ba = sorted(x.pk for x in (qs2 | qs1))
expected = sorted([bu1.pk, bu2.pk])
print("qs1|qs2:", r_ab, "qs2|qs1:", r_ba, "expected:", expected)
ok = (r_ab == r_ba == expected)
sys.exit(0 if ok else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
import django, sys, types
from django.conf import settings
if not settings.configured:
    settings.configure(
        INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth", "probe_app"],
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
        DEFAULT_AUTO_FIELD="django.db.models.AutoField",
    )
_app = types.ModuleType("probe_app"); _app.__path__ = ["/work"]; _app.__file__ = "/work/probe_app_init.py"
sys.modules["probe_app"] = _app
import importlib.machinery
_app.__spec__ = importlib.machinery.ModuleSpec("probe_app", None, is_package=True)
_app.__spec__.submodule_search_locations = ["/work"]
_m = types.ModuleType("probe_app.models"); sys.modules["probe_app.models"] = _m
_m.__spec__ = importlib.machinery.ModuleSpec("probe_app.models", None)
_m.__file__ = "/work/probe_app_models.py"
django.setup()
from django.db import models

class Tag(models.Model):
    class Meta: app_label = "probe_app"
class Note(models.Model):
    tag = models.ForeignKey(Tag, models.CASCADE, null=True)
    class Meta: app_label = "probe_app"
class Annotation(models.Model):
    tag = models.ForeignKey(Tag, models.CASCADE)
    notes = models.ManyToManyField(Note)
    class Meta: app_label = "probe_app"
class BaseUser(models.Model):
    annotation = models.ForeignKey(Annotation, models.CASCADE, null=True, blank=True)
    class Meta: app_label = "probe_app"
class Task(models.Model):
    owner = models.ForeignKey(BaseUser, models.CASCADE, related_name="owner")
    creator = models.ForeignKey(BaseUser, models.CASCADE, related_name="creator")
    note = models.ForeignKey(Note, on_delete=models.CASCADE, null=True, blank=True)
    class Meta: app_label = "probe_app"
for _c in (Tag, Note, Annotation, BaseUser, Task):
    setattr(_m, _c.__name__, _c)

from django.db import connection
def create_schema():
    with connection.schema_editor() as se:
        for c in (Tag, Note, Annotation, BaseUser, Task):
            se.create_model(c)
        se.create_model(Annotation.notes.through)
def seed():
    tag = Tag.objects.create()
    a1 = Annotation.objects.create(tag=tag)
    a2 = Annotation.objects.create(tag=tag)
    note = a1.notes.create(tag=tag)
    bu1 = BaseUser.objects.create(annotation=a1)
    bu2 = BaseUser.objects.create(annotation=a2)
    Task.objects.create(owner=bu2, creator=bu2, note=note)
    return bu1, bu2, a1
# Requirement 4.1: bump_prefix with no exclude renumbers every alias (behavior
# unchanged from before). We call it directly and assert every original alias
# got a new positional name, none preserved. Also 4.3/4.5 positional mapping.
q = BaseUser.objects.filter(
    owner__note__isnull=False, creator__note__isnull=False
).query
# ensure multiple aliases exist
orig_aliases = list(q.alias_map)
assert len(orig_aliases) >= 2, orig_aliases
captured = {}
real_change = q.change_aliases
def spy(cm):
    captured.clear(); captured.update(cm)
    return real_change(cm)
q.change_aliases = spy
class Dummy:
    alias_prefix = q.alias_prefix
    subq_aliases = set()
q.bump_prefix(Dummy())
# Every original alias must be a key in the rename map (none preserved).
missing = [a for a in orig_aliases if a not in captured]
print("orig:", orig_aliases, "renamemap:", captured)
# Also positional: value == prefix + str(index) in original order
newpref = None
posok = True
for pos, a in enumerate(orig_aliases):
    v = captured.get(a)
    if v is None:
        posok = False; continue
    if not v[-1].isdigit() or int(v[len(v)-len(str(pos)):]) != pos:
        # value should end with the positional number
        if not v.endswith(str(pos)):
            posok = False
ok = (not missing) and posok
print("missing:", missing, "positional_ok:", posok)
sys.exit(0 if ok else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
import django, sys, types
from django.conf import settings
if not settings.configured:
    settings.configure(
        INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth", "probe_app"],
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
        DEFAULT_AUTO_FIELD="django.db.models.AutoField",
    )
_app = types.ModuleType("probe_app"); _app.__path__ = ["/work"]; _app.__file__ = "/work/probe_app_init.py"
sys.modules["probe_app"] = _app
import importlib.machinery
_app.__spec__ = importlib.machinery.ModuleSpec("probe_app", None, is_package=True)
_app.__spec__.submodule_search_locations = ["/work"]
_m = types.ModuleType("probe_app.models"); sys.modules["probe_app.models"] = _m
_m.__spec__ = importlib.machinery.ModuleSpec("probe_app.models", None)
_m.__file__ = "/work/probe_app_models.py"
django.setup()
from django.db import models

class Tag(models.Model):
    class Meta: app_label = "probe_app"
class Note(models.Model):
    tag = models.ForeignKey(Tag, models.CASCADE, null=True)
    class Meta: app_label = "probe_app"
class Annotation(models.Model):
    tag = models.ForeignKey(Tag, models.CASCADE)
    notes = models.ManyToManyField(Note)
    class Meta: app_label = "probe_app"
class BaseUser(models.Model):
    annotation = models.ForeignKey(Annotation, models.CASCADE, null=True, blank=True)
    class Meta: app_label = "probe_app"
class Task(models.Model):
    owner = models.ForeignKey(BaseUser, models.CASCADE, related_name="owner")
    creator = models.ForeignKey(BaseUser, models.CASCADE, related_name="creator")
    note = models.ForeignKey(Note, on_delete=models.CASCADE, null=True, blank=True)
    class Meta: app_label = "probe_app"
for _c in (Tag, Note, Annotation, BaseUser, Task):
    setattr(_m, _c.__name__, _c)

from django.db import connection
def create_schema():
    with connection.schema_editor() as se:
        for c in (Tag, Note, Annotation, BaseUser, Task):
            se.create_model(c)
        se.create_model(Annotation.notes.through)
def seed():
    tag = Tag.objects.create()
    a1 = Annotation.objects.create(tag=tag)
    a2 = Annotation.objects.create(tag=tag)
    note = a1.notes.create(tag=tag)
    bu1 = BaseUser.objects.create(annotation=a1)
    bu2 = BaseUser.objects.create(annotation=a2)
    Task.objects.create(owner=bu2, creator=bu2, note=note)
    return bu1, bu2, a1
# Requirement 4.2 / 4.4 / 4.5: bump_prefix(exclude={base}) keeps the base alias
# out of the rename map (preserved), and a preserved alias still consumes its
# position so the followers keep their positional numbers (not shifted).
q = BaseUser.objects.filter(
    owner__note__isnull=False, creator__note__isnull=False
).query
orig = list(q.alias_map)
base = orig[0]  # initial/base table alias
captured = {}
real = q.change_aliases
def spy(cm):
    captured.clear(); captured.update(cm); return real(cm)
q.change_aliases = spy
class Dummy:
    alias_prefix = q.alias_prefix
    subq_aliases = set()
q.bump_prefix(Dummy(), exclude={base})
print("orig:", orig, "base(excluded):", base, "renamemap:", captured)
# 4.2: base not a key
if base in captured:
    print("FAIL: excluded alias appears as key"); sys.exit(1)
# 4.4/4.5: each non-preserved alias mapped to prefix+position(index in orig)
prefix = q.alias_prefix
bad = []
for pos, a in enumerate(orig):
    if a == base:
        if a in captured: bad.append((a,"present"))
        continue
    exp = "%s%d" % (prefix, pos)
    if captured.get(a) != exp:
        bad.append((a, captured.get(a), exp))
# each non-preserved appears exactly once
nonpreserved = [a for a in orig if a != base]
if sorted(captured) != sorted(nonpreserved):
    bad.append(("keyset", sorted(captured), sorted(nonpreserved)))
print("bad:", bad)
sys.exit(0 if not bad else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
import django, sys, types
from django.conf import settings
if not settings.configured:
    settings.configure(
        INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth", "probe_app"],
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
        DEFAULT_AUTO_FIELD="django.db.models.AutoField",
    )
_app = types.ModuleType("probe_app"); _app.__path__ = ["/work"]; _app.__file__ = "/work/probe_app_init.py"
sys.modules["probe_app"] = _app
import importlib.machinery
_app.__spec__ = importlib.machinery.ModuleSpec("probe_app", None, is_package=True)
_app.__spec__.submodule_search_locations = ["/work"]
_m = types.ModuleType("probe_app.models"); sys.modules["probe_app.models"] = _m
_m.__spec__ = importlib.machinery.ModuleSpec("probe_app.models", None)
_m.__file__ = "/work/probe_app_models.py"
django.setup()
from django.db import models

class Tag(models.Model):
    class Meta: app_label = "probe_app"
class Note(models.Model):
    tag = models.ForeignKey(Tag, models.CASCADE, null=True)
    class Meta: app_label = "probe_app"
class Annotation(models.Model):
    tag = models.ForeignKey(Tag, models.CASCADE)
    notes = models.ManyToManyField(Note)
    class Meta: app_label = "probe_app"
class BaseUser(models.Model):
    annotation = models.ForeignKey(Annotation, models.CASCADE, null=True, blank=True)
    class Meta: app_label = "probe_app"
class Task(models.Model):
    owner = models.ForeignKey(BaseUser, models.CASCADE, related_name="owner")
    creator = models.ForeignKey(BaseUser, models.CASCADE, related_name="creator")
    note = models.ForeignKey(Note, on_delete=models.CASCADE, null=True, blank=True)
    class Meta: app_label = "probe_app"
for _c in (Tag, Note, Annotation, BaseUser, Task):
    setattr(_m, _c.__name__, _c)

from django.db import connection
def create_schema():
    with connection.schema_editor() as se:
        for c in (Tag, Note, Annotation, BaseUser, Task):
            se.create_model(c)
        se.create_model(Annotation.notes.through)
def seed():
    tag = Tag.objects.create()
    a1 = Annotation.objects.create(tag=tag)
    a2 = Annotation.objects.create(tag=tag)
    note = a1.notes.create(tag=tag)
    bu1 = BaseUser.objects.create(annotation=a1)
    bu2 = BaseUser.objects.create(annotation=a2)
    Task.objects.create(owner=bu2, creator=bu2, note=note)
    return bu1, bu2, a1
# Requirement 3.1/3.2/3.3: after combine, the rhs base table alias equals the
# lhs initial alias (shared base alias, not duplicated). We combine and check
# the resulting query uses a single alias for the BaseUser base table.
from django.db.models import Q
a1 = Annotation(pk=1)
lhs = a1.baseuser_set.all().query.clone()
initial = lhs.get_initial_alias()
rhs = BaseUser.objects.filter(
    Q(owner__note__in=Note.objects.filter(pk=1)) |
    Q(creator__note__in=Note.objects.filter(pk=1))
).query.clone()
# combine (this triggers bump_prefix on rhs with exclude={initial})
lhs.combine(rhs, Q.OR)
# The base table for BaseUser must appear exactly once among alias_map tables.
tables = [lhs.alias_map[a].table_name for a in lhs.alias_map]
base_table = BaseUser._meta.db_table
count = tables.count(base_table)
print("initial alias:", initial, "aliases:", list(lhs.alias_map),
      "base_table_count:", count)
# base table appears once, and the initial alias survived as a key
ok = (count == 1) and (initial in lhs.alias_map)
sys.exit(0 if ok else 1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
import django, sys, types
from django.conf import settings
if not settings.configured:
    settings.configure(
        INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth", "probe_app"],
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
        DEFAULT_AUTO_FIELD="django.db.models.AutoField",
    )
_app = types.ModuleType("probe_app"); _app.__path__ = ["/work"]; _app.__file__ = "/work/probe_app_init.py"
sys.modules["probe_app"] = _app
import importlib.machinery
_app.__spec__ = importlib.machinery.ModuleSpec("probe_app", None, is_package=True)
_app.__spec__.submodule_search_locations = ["/work"]
_m = types.ModuleType("probe_app.models"); sys.modules["probe_app.models"] = _m
_m.__spec__ = importlib.machinery.ModuleSpec("probe_app.models", None)
_m.__file__ = "/work/probe_app_models.py"
django.setup()
from django.db import models

class Tag(models.Model):
    class Meta: app_label = "probe_app"
class Note(models.Model):
    tag = models.ForeignKey(Tag, models.CASCADE, null=True)
    class Meta: app_label = "probe_app"
class Annotation(models.Model):
    tag = models.ForeignKey(Tag, models.CASCADE)
    notes = models.ManyToManyField(Note)
    class Meta: app_label = "probe_app"
class BaseUser(models.Model):
    annotation = models.ForeignKey(Annotation, models.CASCADE, null=True, blank=True)
    class Meta: app_label = "probe_app"
class Task(models.Model):
    owner = models.ForeignKey(BaseUser, models.CASCADE, related_name="owner")
    creator = models.ForeignKey(BaseUser, models.CASCADE, related_name="creator")
    note = models.ForeignKey(Note, on_delete=models.CASCADE, null=True, blank=True)
    class Meta: app_label = "probe_app"
for _c in (Tag, Note, Annotation, BaseUser, Task):
    setattr(_m, _c.__name__, _c)

from django.db import connection
def create_schema():
    with connection.schema_editor() as se:
        for c in (Tag, Note, Annotation, BaseUser, Task):
            se.create_model(c)
        se.create_model(Annotation.notes.through)
def seed():
    tag = Tag.objects.create()
    a1 = Annotation.objects.create(tag=tag)
    a2 = Annotation.objects.create(tag=tag)
    note = a1.notes.create(tag=tag)
    bu1 = BaseUser.objects.create(annotation=a1)
    bu2 = BaseUser.objects.create(annotation=a2)
    Task.objects.create(owner=bu2, creator=bu2, note=note)
    return bu1, bu2, a1
# Requirement 3.4: if the two queries do NOT share an alias prefix, the
# renumbering (bump_prefix) makes NO change to the rhs aliases.
q = BaseUser.objects.filter(owner__note__isnull=False).query
before = list(q.alias_map)
class Dummy:
    alias_prefix = "ZZ"   # different from q.alias_prefix (default 'T')
    subq_aliases = set()
assert q.alias_prefix != "ZZ", q.alias_prefix
q.bump_prefix(Dummy(), exclude=set())
after = list(q.alias_map)
print("prefix:", q.alias_prefix, "before:", before, "after:", after)
sys.exit(0 if before == after else 1)
```

Attack 7 — `probe_7.py` → holds on the patched tree (good)

```python
import django, sys, types
from django.conf import settings
if not settings.configured:
    settings.configure(
        INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth", "probe_app"],
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
        DEFAULT_AUTO_FIELD="django.db.models.AutoField",
    )
_app = types.ModuleType("probe_app"); _app.__path__ = ["/work"]; _app.__file__ = "/work/probe_app_init.py"
sys.modules["probe_app"] = _app
import importlib.machinery
_app.__spec__ = importlib.machinery.ModuleSpec("probe_app", None, is_package=True)
_app.__spec__.submodule_search_locations = ["/work"]
_m = types.ModuleType("probe_app.models"); sys.modules["probe_app.models"] = _m
_m.__spec__ = importlib.machinery.ModuleSpec("probe_app.models", None)
_m.__file__ = "/work/probe_app_models.py"
django.setup()
from django.db import models

class Tag(models.Model):
    class Meta: app_label = "probe_app"
class Note(models.Model):
    tag = models.ForeignKey(Tag, models.CASCADE, null=True)
    class Meta: app_label = "probe_app"
class Annotation(models.Model):
    tag = models.ForeignKey(Tag, models.CASCADE)
    notes = models.ManyToManyField(Note)
    class Meta: app_label = "probe_app"
class BaseUser(models.Model):
    annotation = models.ForeignKey(Annotation, models.CASCADE, null=True, blank=True)
    class Meta: app_label = "probe_app"
class Task(models.Model):
    owner = models.ForeignKey(BaseUser, models.CASCADE, related_name="owner")
    creator = models.ForeignKey(BaseUser, models.CASCADE, related_name="creator")
    note = models.ForeignKey(Note, on_delete=models.CASCADE, null=True, blank=True)
    class Meta: app_label = "probe_app"
for _c in (Tag, Note, Annotation, BaseUser, Task):
    setattr(_m, _c.__name__, _c)

from django.db import connection
def create_schema():
    with connection.schema_editor() as se:
        for c in (Tag, Note, Annotation, BaseUser, Task):
            se.create_model(c)
def seed():
    tag = Tag.objects.create()
    a1 = Annotation.objects.create(tag=tag)
    a2 = Annotation.objects.create(tag=tag)
    note = a1.notes.create(tag=tag)
    bu1 = BaseUser.objects.create(annotation=a1)
    bu2 = BaseUser.objects.create(annotation=a2)
    Task.objects.create(owner=bu2, creator=bu2, note=note)
    return bu1, bu2, a1
# Requirement 5.2: incompatible combinations still raise TypeError at
# Query.combine: different base models, sliced query, distinct-vs-nondistinct,
# differing distinct fields. (Tested at the Query.combine level, where these
# guards live.)
from django.db.models import Q
fails = []
def expect_typeerror(label, fn):
    try:
        fn(); fails.append(label + ": no TypeError")
    except TypeError:
        pass
    except Exception as e:
        fails.append(label + ": wrong exc " + repr(e))
# different base models
expect_typeerror("different-models",
    lambda: BaseUser.objects.all().query.combine(Task.objects.all().query, Q.OR))
# sliced query (self is sliced)
def sliced():
    q = BaseUser.objects.all().query.clone()
    q.set_limits(0, 1)
    q.combine(BaseUser.objects.all().query, Q.OR)
expect_typeerror("sliced", sliced)
# distinct vs non-distinct
def distmix():
    q = BaseUser.objects.distinct().query
    q.combine(BaseUser.objects.all().query, Q.OR)
expect_typeerror("distinct-mix", distmix)
# differing distinct fields
def distfields():
    q = BaseUser.objects.distinct("annotation").query
    q.combine(BaseUser.objects.distinct("id").query, Q.OR)
expect_typeerror("distinct-fields", distfields)
print("fails:", fails)
sys.exit(0 if not fails else 1)
```

Attack 8 — `probe_8.py` → holds on the patched tree (good)

```python
import django, sys, types
from django.conf import settings
if not settings.configured:
    settings.configure(
        INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth", "probe_app"],
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
        DEFAULT_AUTO_FIELD="django.db.models.AutoField",
    )
_app = types.ModuleType("probe_app"); _app.__path__ = ["/work"]; _app.__file__ = "/work/probe_app_init.py"
sys.modules["probe_app"] = _app
import importlib.machinery
_app.__spec__ = importlib.machinery.ModuleSpec("probe_app", None, is_package=True)
_app.__spec__.submodule_search_locations = ["/work"]
_m = types.ModuleType("probe_app.models"); sys.modules["probe_app.models"] = _m
_m.__spec__ = importlib.machinery.ModuleSpec("probe_app.models", None)
_m.__file__ = "/work/probe_app_models.py"
django.setup()
from django.db import models

class Tag(models.Model):
    class Meta: app_label = "probe_app"
class Note(models.Model):
    tag = models.ForeignKey(Tag, models.CASCADE, null=True)
    class Meta: app_label = "probe_app"
class Annotation(models.Model):
    tag = models.ForeignKey(Tag, models.CASCADE)
    notes = models.ManyToManyField(Note)
    class Meta: app_label = "probe_app"
class BaseUser(models.Model):
    annotation = models.ForeignKey(Annotation, models.CASCADE, null=True, blank=True)
    class Meta: app_label = "probe_app"
class Task(models.Model):
    owner = models.ForeignKey(BaseUser, models.CASCADE, related_name="owner")
    creator = models.ForeignKey(BaseUser, models.CASCADE, related_name="creator")
    note = models.ForeignKey(Note, on_delete=models.CASCADE, null=True, blank=True)
    class Meta: app_label = "probe_app"
for _c in (Tag, Note, Annotation, BaseUser, Task):
    setattr(_m, _c.__name__, _c)

from django.db import connection
def create_schema():
    with connection.schema_editor() as se:
        for c in (Tag, Note, Annotation, BaseUser, Task):
            se.create_model(c)
        se.create_model(Annotation.notes.through)
def seed():
    tag = Tag.objects.create()
    a1 = Annotation.objects.create(tag=tag)
    a2 = Annotation.objects.create(tag=tag)
    note = a1.notes.create(tag=tag)
    bu1 = BaseUser.objects.create(annotation=a1)
    bu2 = BaseUser.objects.create(annotation=a2)
    Task.objects.create(owner=bu2, creator=bu2, note=note)
    return bu1, bu2, a1
# Requirement 5.5: change_aliases with a rename map whose keys and values
# intersect STILL raises AssertionError.
q = BaseUser.objects.all().query
try:
    q.change_aliases({"T4": "T5", "T5": "T6"})
    print("FAIL: no AssertionError"); sys.exit(1)
except AssertionError:
    print("AssertionError correctly raised on intersecting change_map")
    sys.exit(0)
```

Attack 9 — `probe_9.py` → holds on the patched tree (good)

```python
import django, sys, types
from django.conf import settings
if not settings.configured:
    settings.configure(
        INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth", "probe_app"],
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
        DEFAULT_AUTO_FIELD="django.db.models.AutoField",
    )
_app = types.ModuleType("probe_app"); _app.__path__ = ["/work"]; _app.__file__ = "/work/probe_app_init.py"
sys.modules["probe_app"] = _app
import importlib.machinery
_app.__spec__ = importlib.machinery.ModuleSpec("probe_app", None, is_package=True)
_app.__spec__.submodule_search_locations = ["/work"]
_m = types.ModuleType("probe_app.models"); sys.modules["probe_app.models"] = _m
_m.__spec__ = importlib.machinery.ModuleSpec("probe_app.models", None)
_m.__file__ = "/work/probe_app_models.py"
django.setup()
from django.db import models

class Tag(models.Model):
    class Meta: app_label = "probe_app"
class Note(models.Model):
    tag = models.ForeignKey(Tag, models.CASCADE, null=True)
    class Meta: app_label = "probe_app"
class Annotation(models.Model):
    tag = models.ForeignKey(Tag, models.CASCADE)
    notes = models.ManyToManyField(Note)
    class Meta: app_label = "probe_app"
class BaseUser(models.Model):
    annotation = models.ForeignKey(Annotation, models.CASCADE, null=True, blank=True)
    class Meta: app_label = "probe_app"
class Task(models.Model):
    owner = models.ForeignKey(BaseUser, models.CASCADE, related_name="owner")
    creator = models.ForeignKey(BaseUser, models.CASCADE, related_name="creator")
    note = models.ForeignKey(Note, on_delete=models.CASCADE, null=True, blank=True)
    class Meta: app_label = "probe_app"
for _c in (Tag, Note, Annotation, BaseUser, Task):
    setattr(_m, _c.__name__, _c)

from django.db import connection
def create_schema():
    with connection.schema_editor() as se:
        for c in (Tag, Note, Annotation, BaseUser, Task):
            se.create_model(c)
def seed():
    tag = Tag.objects.create()
    a1 = Annotation.objects.create(tag=tag)
    a2 = Annotation.objects.create(tag=tag)
    note = a1.notes.create(tag=tag)
    bu1 = BaseUser.objects.create(annotation=a1)
    bu2 = BaseUser.objects.create(annotation=a2)
    Task.objects.create(owner=bu2, creator=bu2, note=note)
    return bu1, bu2, a1
# Requirement 5.3: nest a combined queryset inside a further filter (filter by
# pks drawn from a combined queryset's values) and return correct rows.
from django.db.models import Q
create_schema()
bu1, bu2, a1 = seed()
qs1 = a1.baseuser_set.all()
qs2 = BaseUser.objects.filter(
    Q(owner__note__in=a1.notes.all()) | Q(creator__note__in=a1.notes.all())
)
combined = qs2 | qs1
nested = BaseUser.objects.filter(pk__in=combined.values('pk'))
got = sorted(x.pk for x in nested)
expected = sorted([bu1.pk, bu2.pk])
print("nested:", got, "expected:", expected)
sys.exit(0 if got == expected else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1_or_no_crash.py`

```python
import django, sys, types
from django.conf import settings
if not settings.configured:
    settings.configure(
        INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth", "probe_app"],
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
        DEFAULT_AUTO_FIELD="django.db.models.AutoField",
    )
_app = types.ModuleType("probe_app"); _app.__path__ = ["/work"]; _app.__file__ = "/work/probe_app_init.py"
sys.modules["probe_app"] = _app
import importlib.machinery
_app.__spec__ = importlib.machinery.ModuleSpec("probe_app", None, is_package=True)
_app.__spec__.submodule_search_locations = ["/work"]
_m = types.ModuleType("probe_app.models"); sys.modules["probe_app.models"] = _m
_m.__spec__ = importlib.machinery.ModuleSpec("probe_app.models", None)
_m.__file__ = "/work/probe_app_models.py"
django.setup()
from django.db import models

class Tag(models.Model):
    class Meta: app_label = "probe_app"
class Note(models.Model):
    tag = models.ForeignKey(Tag, models.CASCADE, null=True)
    class Meta: app_label = "probe_app"
class Annotation(models.Model):
    tag = models.ForeignKey(Tag, models.CASCADE)
    notes = models.ManyToManyField(Note)
    class Meta: app_label = "probe_app"
class BaseUser(models.Model):
    annotation = models.ForeignKey(Annotation, models.CASCADE, null=True, blank=True)
    class Meta: app_label = "probe_app"
class Task(models.Model):
    owner = models.ForeignKey(BaseUser, models.CASCADE, related_name="owner")
    creator = models.ForeignKey(BaseUser, models.CASCADE, related_name="creator")
    note = models.ForeignKey(Note, on_delete=models.CASCADE, null=True, blank=True)
    class Meta: app_label = "probe_app"
for _c in (Tag, Note, Annotation, BaseUser, Task):
    setattr(_m, _c.__name__, _c)

from django.db import connection
def create_schema():
    with connection.schema_editor() as se:
        for c in (Tag, Note, Annotation, BaseUser, Task):
            se.create_model(c)
        se.create_model(Annotation.notes.through)
def seed():
    tag = Tag.objects.create()
    a1 = Annotation.objects.create(tag=tag)
    a2 = Annotation.objects.create(tag=tag)
    note = a1.notes.create(tag=tag)
    bu1 = BaseUser.objects.create(annotation=a1)
    bu2 = BaseUser.objects.create(annotation=a2)
    Task.objects.create(owner=bu2, creator=bu2, note=note)
    return bu1, bu2, a1
# Requirement 1.1 / 2.1 + POSITIVE CONTROL: OR of two prefix-colliding querysets
# completes (both orders) without AssertionError.
from django.db.models import Q
a1 = Annotation(pk=1)
qs1 = a1.baseuser_set.all()
qs2 = BaseUser.objects.filter(
    Q(owner__note__in=Note.objects.filter(pk=1)) |
    Q(creator__note__in=Note.objects.filter(pk=1))
)
ok = True
try:
    str((qs2 | qs1).query)
    str((qs1 | qs2).query)
    print("both OR orders compiled without AssertionError")
except AssertionError as e:
    ok = False; print("AssertionError during OR combine:", repr(e))
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance: OR-combining querysets sharing an alias prefix crashes with AssertionError in Query.change_aliases (base). Gold fix: rhs.bump_prefix(self, exclude={initial_alias}) in Query.combine, plus optional exclude param on bump_prefix. All probes run in the official image via nl_attack; each prepends a self-contained Django harness (in-memory sqlite, synthetic probe_app mirroring the F2P models: BaseUser.annotation FK, Task.note FK).

Probes (path : requirement : base -> patched):
- probe_1_or_no_crash.py : Req 1.1/2.1 (+POSITIVE CONTROL) both OR orders compile w/o AssertionError : FAIL(base, AssertionError) -> HOLD(patched). Discriminates.
- probe_2.py : Req 2.2/2.3/1.3 qs1|qs2 == qs2|qs1 == expected rows [1,2] w/ real data : FAIL(base) -> HOLD.
- probe_3.py : Req 4.1/4.3/4.5 bump_prefix w/o exclude renumbers EVERY alias positionally : HOLD(base) -> HOLD (unchanged-behavior regression check).
- probe_4.py : Req 4.2/4.4/4.5 bump_prefix(exclude={base}) keeps base out of rename map, followers keep positional numbers : FAIL(base, no exclude param) -> HOLD.
- probe_5.py : Req 3.1/3.2/3.3 after combine base table alias appears exactly once, initial alias survives : FAIL(base) -> HOLD.
- probe_6.py : Req 3.4 differing prefix => bump_prefix makes no change : FAIL(base, no exclude param) -> HOLD.
- probe_7.py : Req 5.2 incompatible combos still raise TypeError (different models, sliced, distinct-mix, distinct-fields) at Query.combine : HOLD -> HOLD (regression).
- probe_8.py : Req 5.5 change_aliases still asserts on intersecting change_map : HOLD -> HOLD (regression).
- probe_9.py : Req 5.3 nesting combined qs in a further pk__in filter returns correct rows : HOLD -> HOLD.

Positive control (probe_1): HOLDS patched, FAILS base (AssertionError) — prepatch reproduced.

Candidate wrong-fix patches (both apply at base_commit, both REJECTED by the suite):
- weak_drop_assert.diff (lazy fix: delete the disjointness assert in change_aliases): REJECTED by probe_8 (Req 5.5 -> no AssertionError), probe_4, probe_6 (exclude param absent). Makes crash disappear without the real prefix renumbering; fails hidden test's biconditional/regression expectations.
- weak_no_exclude.diff (partial fix: rhs.bump_prefix(self) WITHOUT exclude={initial_alias}): REJECTED by probe_1 (still AssertionErrors — renumbering base alias breaks the shared-base merge), probe_2, probe_5, probe_9.

No candidate satisfied the full probe suite => no TOO-WEAK finding. 9 distinct probes all hold on patched; positive control discriminates; >=1 candidate exercised and rejected. Verdict SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 9 requirement probes hold on the patched tree; 2/2 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 9 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 9 | `probe_1_or_no_crash.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py`, `probe_7.py`, `probe_8.py`, `probe_9.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 2 alternative candidate patches, claimed to satisfy every cited requirement, and ran the same suite against them. The suite rejected all 2: a probe encoding a cited requirement fails under each of those, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1_or_no_crash.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (9):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

_The 9 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts, and on this backend both roles put it through the same derivation: every block below is a requirement probe run on the gold-patched tree, and the `machine verdict:` line each role publishes above reports BOTH that its probes hold there and how many candidate patches the probe suite rejected — so the two roles re-ran ONE probe suite and each recorded its own outcome for every probe in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `probe_1_or_no_crash.py` → holds on the patched tree (good)

Attack 2 — `probe_2.py` → holds on the patched tree (good)

Attack 3 — `probe_3.py` → holds on the patched tree (good)

Attack 4 — `probe_4.py` → holds on the patched tree (good)

Attack 5 — `probe_5.py` → holds on the patched tree (good)

Attack 6 — `probe_6.py` → holds on the patched tree (good)

Attack 7 — `probe_7.py` → holds on the patched tree (good)

Attack 8 — `probe_8.py` → holds on the patched tree (good)

Attack 9 — `probe_9.py` → holds on the patched tree (good)

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1_or_no_crash.py`

```python
import django, sys, types
from django.conf import settings
if not settings.configured:
    settings.configure(
        INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth", "probe_app"],
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
        DEFAULT_AUTO_FIELD="django.db.models.AutoField",
    )
_app = types.ModuleType("probe_app"); _app.__path__ = ["/work"]; _app.__file__ = "/work/probe_app_init.py"
sys.modules["probe_app"] = _app
import importlib.machinery
_app.__spec__ = importlib.machinery.ModuleSpec("probe_app", None, is_package=True)
_app.__spec__.submodule_search_locations = ["/work"]
_m = types.ModuleType("probe_app.models"); sys.modules["probe_app.models"] = _m
_m.__spec__ = importlib.machinery.ModuleSpec("probe_app.models", None)
_m.__file__ = "/work/probe_app_models.py"
django.setup()
from django.db import models

class Tag(models.Model):
    class Meta: app_label = "probe_app"
class Note(models.Model):
    tag = models.ForeignKey(Tag, models.CASCADE, null=True)
    class Meta: app_label = "probe_app"
class Annotation(models.Model):
    tag = models.ForeignKey(Tag, models.CASCADE)
    notes = models.ManyToManyField(Note)
    class Meta: app_label = "probe_app"
class BaseUser(models.Model):
    annotation = models.ForeignKey(Annotation, models.CASCADE, null=True, blank=True)
    class Meta: app_label = "probe_app"
class Task(models.Model):
    owner = models.ForeignKey(BaseUser, models.CASCADE, related_name="owner")
    creator = models.ForeignKey(BaseUser, models.CASCADE, related_name="creator")
    note = models.ForeignKey(Note, on_delete=models.CASCADE, null=True, blank=True)
    class Meta: app_label = "probe_app"
for _c in (Tag, Note, Annotation, BaseUser, Task):
    setattr(_m, _c.__name__, _c)

from django.db import connection
def create_schema():
    with connection.schema_editor() as se:
        for c in (Tag, Note, Annotation, BaseUser, Task):
            se.create_model(c)
        se.create_model(Annotation.notes.through)
def seed():
    tag = Tag.objects.create()
    a1 = Annotation.objects.create(tag=tag)
    a2 = Annotation.objects.create(tag=tag)
    note = a1.notes.create(tag=tag)
    bu1 = BaseUser.objects.create(annotation=a1)
    bu2 = BaseUser.objects.create(annotation=a2)
    Task.objects.create(owner=bu2, creator=bu2, note=note)
    return bu1, bu2, a1
# Requirement 1.1 / 2.1 + POSITIVE CONTROL: OR of two prefix-colliding querysets
# completes (both orders) without AssertionError.
from django.db.models import Q
a1 = Annotation(pk=1)
qs1 = a1.baseuser_set.all()
qs2 = BaseUser.objects.filter(
    Q(owner__note__in=Note.objects.filter(pk=1)) |
    Q(creator__note__in=Note.objects.filter(pk=1))
)
ok = True
try:
    str((qs2 | qs1).query)
    str((qs1 | qs2).query)
    print("both OR orders compiled without AssertionError")
except AssertionError as e:
    ok = False; print("AssertionError during OR combine:", repr(e))
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance: OR-combining querysets sharing an alias prefix crashes with AssertionError in Query.change_aliases (base). Gold fix: rhs.bump_prefix(self, exclude={initial_alias}) in Query.combine, plus optional exclude param on bump_prefix. All probes run in the official image via nl_attack; each prepends a self-contained Django harness (in-memory sqlite, synthetic probe_app mirroring the F2P models: BaseUser.annotation FK, Task.note FK).

Probes (path : requirement : base -> patched):
- probe_1_or_no_crash.py : Req 1.1/2.1 (+POSITIVE CONTROL) both OR orders compile w/o AssertionError : FAIL(base, AssertionError) -> HOLD(patched). Discriminates.
- probe_2.py : Req 2.2/2.3/1.3 qs1|qs2 == qs2|qs1 == expected rows [1,2] w/ real data : FAIL(base) -> HOLD.
- probe_3.py : Req 4.1/4.3/4.5 bump_prefix w/o exclude renumbers EVERY alias positionally : HOLD(base) -> HOLD (unchanged-behavior regression check).
- probe_4.py : Req 4.2/4.4/4.5 bump_prefix(exclude={base}) keeps base out of rename map, followers keep positional numbers : FAIL(base, no exclude param) -> HOLD.
- probe_5.py : Req 3.1/3.2/3.3 after combine base table alias appears exactly once, initial alias survives : FAIL(base) -> HOLD.
- probe_6.py : Req 3.4 differing prefix => bump_prefix makes no change : FAIL(base, no exclude param) -> HOLD.
- probe_7.py : Req 5.2 incompatible combos still raise TypeError (different models, sliced, distinct-mix, distinct-fields) at Query.combine : HOLD -> HOLD (regression).
- probe_8.py : Req 5.5 change_aliases still asserts on intersecting change_map : HOLD -> HOLD (regression).
- probe_9.py : Req 5.3 nesting combined qs in a further pk__in filter returns correct rows : HOLD -> HOLD.

Positive control (probe_1): HOLDS patched, FAILS base (AssertionError) — prepatch reproduced.

Candidate wrong-fix patches (both apply at base_commit, both REJECTED by the suite):
- weak_drop_assert.diff (lazy fix: delete the disjointness assert in change_aliases): REJECTED by probe_8 (Req 5.5 -> no AssertionError), probe_4, probe_6 (exclude param absent). Makes crash disappear without the real prefix renumbering; fails hidden test's biconditional/regression expectations.
- weak_no_exclude.diff (partial fix: rhs.bump_prefix(self) WITHOUT exclude={initial_alias}): REJECTED by probe_1 (still AssertionErrors — renumbering base alias breaks the shared-base merge), probe_2, probe_5, probe_9.

No candidate satisfied the full probe suite => no TOO-WEAK finding. 9 distinct probes all hold on patched; positive control discriminates; >=1 candidate exercised and rejected. Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Requirements pin the changed observable behavior (order-independent, crash-free OR-combination) AND the exact helper contracts the patch modifies (combine calls rhs.bump_prefix(self, exclude={initial_alias}) before building change_map; bump_prefix gains the exclude param with positional numbering over full alias ordering; the change_aliases disjointness assert is retained with its documenting comment). Modeling boundary is correct — not a narrow single-branch slice. Base-commit divergence (crash) and gold-patched behavior verified live in the instance image via nl_attack probe/--base.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The requirements localize the change to Query.combine/bump_prefix/change_aliases and describe the fix behaviorally, which is legitimate. Checked all leak vectors: (1) The `change_map` example `T4→T5, T5→T6` (lines 11-12) is verbatim in the PUBLIC problem_statement (`change_map = {'T4': 'T5', 'T5': 'T6'}`) — not derived from hidden material. (2) Function names combine/change_aliases/table_alias appear in problem_statement; bump_prefix is an existing Django method being modified — naming it to localize is legitimate. (3) The gold-invented parameter `exclude` is described semantically ("optional set of aliases to preserve") but never named — no identifier leak. (4) The hidden test `test_conflicting_aliases_during_combine (queries.tests.QuerySetBitwiseOperationTests)`, its model changes (BaseUser.annotation, Task.note), the specific relation lookups (owner__note__in / creator__note__in), fixture data, and assertions (assertCountEqual(qs2|qs1, qs1|qs2)) do NOT appear anywhere in the document. (5) Req 2 order-independence and Req 5 regression list describe behavior/existing guard clauses (the TypeErrors are in combine's own source), not test parametrization — and there is only one F2P test, so no parametrized case-list to mirror. Req 4's positional-numbering detail (lines 95-105) mirrors the gold algorithm `enumerate(self.alias_map) if alias not in exclude` in prose, but this is behavioral specification of the fix, not transmission of any test (no test exercises bump_prefix directly). No test paths/names/ids, quoted test or gold code, or fix-invented identifiers cross into the spec.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
