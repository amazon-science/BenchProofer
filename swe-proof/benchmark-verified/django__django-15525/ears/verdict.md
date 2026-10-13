# P2 adversarial audit — django__django-15525

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

Counterexample / evidence:

```
weak_late candidate (assign obj._state.db = db AFTER calling obj.natural_key() instead of before) is rejected by probes 1, 2, 6: the FK-following natural_key() still queries the default database, raising DoesNotExist when the related Author exists only in the target 'other' db.
```

**Attacks re-run (7):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
import django
from django.conf import settings
settings.configure(
    DEBUG=True,
    DATABASES={
        "default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"},
        "other":   {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"},
    },
    INSTALLED_APPS=["probeapp"],
    USE_TZ=False,
)
import sys, types, os, tempfile
_d = tempfile.mkdtemp()
m = types.ModuleType("probeapp"); m.__path__=[_d]; m.__file__=os.path.join(_d,"__init__.py"); sys.modules["probeapp"]=m
django.setup()
from django.db import models, connections
class AuthorManager(models.Manager):
    def get_by_natural_key(self, name): return self.get(name=name)
class Author(models.Model):
    name = models.CharField(max_length=100, unique=True)
    objects = AuthorManager()
    class Meta: app_label="probeapp"
    def natural_key(self): return (self.name,)
class BookManager(models.Manager):
    def get_by_natural_key(self, title, author_name):
        return self.get(title=title, author__name=author_name)
class Book(models.Model):
    title = models.CharField(max_length=100)
    author = models.ForeignKey(Author, on_delete=models.CASCADE)
    objects = BookManager()
    class Meta: app_label="probeapp"
    def natural_key(self): return (self.title,) + self.author.natural_key()
    natural_key.dependencies=["probeapp.author"]
class Plain(models.Model):
    label = models.CharField(max_length=50)
    class Meta: app_label="probeapp"
def make_tables():
    for alias in ("default","other"):
        with connections[alias].schema_editor() as se:
            for mm in (Author, Book, Plain): se.create_model(mm)
# Req 1.2/1.3 + POSITIVE CONTROL: FK-natural-key resolves against target db 'other'.
from django.core.serializers.base import build_instance
make_tables()
a = Author.objects.using("other").create(name="AuthOther")
bk = Book.objects.using("other").create(title="BookOther", author=a)
data = {"title": "BookOther", "author_id": a.pk}
try:
    inst = build_instance(Book, dict(data), "other")
except Exception as e:
    print("build_instance RAISED:", type(e).__name__, e); sys.exit(1)
got = getattr(inst, "id", None)
print("resolved pk:", got, "expected:", bk.pk)
sys.exit(0 if got == bk.pk else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
import django
from django.conf import settings
settings.configure(
    DEBUG=True,
    DATABASES={
        "default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"},
        "other":   {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"},
    },
    INSTALLED_APPS=["probeapp"],
    USE_TZ=False,
)
import sys, types, os, tempfile
_d = tempfile.mkdtemp()
m = types.ModuleType("probeapp"); m.__path__=[_d]; m.__file__=os.path.join(_d,"__init__.py"); sys.modules["probeapp"]=m
django.setup()
from django.db import models, connections
class AuthorManager(models.Manager):
    def get_by_natural_key(self, name): return self.get(name=name)
class Author(models.Model):
    name = models.CharField(max_length=100, unique=True)
    objects = AuthorManager()
    class Meta: app_label="probeapp"
    def natural_key(self): return (self.name,)
class BookManager(models.Manager):
    def get_by_natural_key(self, title, author_name):
        return self.get(title=title, author__name=author_name)
class Book(models.Model):
    title = models.CharField(max_length=100)
    author = models.ForeignKey(Author, on_delete=models.CASCADE)
    objects = BookManager()
    class Meta: app_label="probeapp"
    def natural_key(self): return (self.title,) + self.author.natural_key()
    natural_key.dependencies=["probeapp.author"]
class Plain(models.Model):
    label = models.CharField(max_length=50)
    class Meta: app_label="probeapp"
def make_tables():
    for alias in ("default","other"):
        with connections[alias].schema_editor() as se:
            for mm in (Author, Book, Plain): se.create_model(mm)
from django.core.serializers.base import build_instance
make_tables()
seen = {}
class SpyManager(models.Manager):
    def get_by_natural_key(self, name): return self.get(name=name)
class Spy(models.Model):
    name = models.CharField(max_length=100, unique=True)
    objects = SpyManager()
    class Meta: app_label="probeapp"
    def natural_key(self):
        seen["db"] = self._state.db
        return (self.name,)
with connections["other"].schema_editor() as se: se.create_model(Spy)
Spy.objects.using("other").create(name="X")
build_instance(Spy, {"name": "X"}, "other")
print("state.db observed at natural_key():", seen.get("db"))
sys.exit(0 if seen.get("db") == "other" else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
import django
from django.conf import settings
settings.configure(
    DEBUG=True,
    DATABASES={
        "default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"},
        "other":   {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"},
    },
    INSTALLED_APPS=["probeapp"],
    USE_TZ=False,
)
import sys, types, os, tempfile
_d = tempfile.mkdtemp()
m = types.ModuleType("probeapp"); m.__path__=[_d]; m.__file__=os.path.join(_d,"__init__.py"); sys.modules["probeapp"]=m
django.setup()
from django.db import models, connections
class AuthorManager(models.Manager):
    def get_by_natural_key(self, name): return self.get(name=name)
class Author(models.Model):
    name = models.CharField(max_length=100, unique=True)
    objects = AuthorManager()
    class Meta: app_label="probeapp"
    def natural_key(self): return (self.name,)
class BookManager(models.Manager):
    def get_by_natural_key(self, title, author_name):
        return self.get(title=title, author__name=author_name)
class Book(models.Model):
    title = models.CharField(max_length=100)
    author = models.ForeignKey(Author, on_delete=models.CASCADE)
    objects = BookManager()
    class Meta: app_label="probeapp"
    def natural_key(self): return (self.title,) + self.author.natural_key()
    natural_key.dependencies=["probeapp.author"]
class Plain(models.Model):
    label = models.CharField(max_length=50)
    class Meta: app_label="probeapp"
def make_tables():
    for alias in ("default","other"):
        with connections[alias].schema_editor() as se:
            for mm in (Author, Book, Plain): se.create_model(mm)
from django.core.serializers.base import build_instance
make_tables()
# no Author/Book rows exist anywhere; if a nat-key lookup were attempted it'd query FK
data = {"id": 999, "title": "T", "author_id": 5}
inst = build_instance(Book, dict(data), "other")
print("pk kept:", inst.id, "title:", inst.title)
sys.exit(0 if inst.id == 999 and inst.title == "T" else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
import django
from django.conf import settings
settings.configure(
    DEBUG=True,
    DATABASES={
        "default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"},
        "other":   {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"},
    },
    INSTALLED_APPS=["probeapp"],
    USE_TZ=False,
)
import sys, types, os, tempfile
_d = tempfile.mkdtemp()
m = types.ModuleType("probeapp"); m.__path__=[_d]; m.__file__=os.path.join(_d,"__init__.py"); sys.modules["probeapp"]=m
django.setup()
from django.db import models, connections
class AuthorManager(models.Manager):
    def get_by_natural_key(self, name): return self.get(name=name)
class Author(models.Model):
    name = models.CharField(max_length=100, unique=True)
    objects = AuthorManager()
    class Meta: app_label="probeapp"
    def natural_key(self): return (self.name,)
class BookManager(models.Manager):
    def get_by_natural_key(self, title, author_name):
        return self.get(title=title, author__name=author_name)
class Book(models.Model):
    title = models.CharField(max_length=100)
    author = models.ForeignKey(Author, on_delete=models.CASCADE)
    objects = BookManager()
    class Meta: app_label="probeapp"
    def natural_key(self): return (self.title,) + self.author.natural_key()
    natural_key.dependencies=["probeapp.author"]
class Plain(models.Model):
    label = models.CharField(max_length=50)
    class Meta: app_label="probeapp"
def make_tables():
    for alias in ("default","other"):
        with connections[alias].schema_editor() as se:
            for mm in (Author, Book, Plain): se.create_model(mm)
from django.core.serializers.base import build_instance
make_tables()
data = {"label": "hello"}  # Plain has no natural_key/get_by_natural_key
inst = build_instance(Plain, dict(data), "other")
print("label:", inst.label, "pk:", inst.pk)
sys.exit(0 if inst.label == "hello" and inst.pk is None else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
import django
from django.conf import settings
settings.configure(
    DEBUG=True,
    DATABASES={
        "default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"},
        "other":   {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"},
    },
    INSTALLED_APPS=["probeapp"],
    USE_TZ=False,
)
import sys, types, os, tempfile
_d = tempfile.mkdtemp()
m = types.ModuleType("probeapp"); m.__path__=[_d]; m.__file__=os.path.join(_d,"__init__.py"); sys.modules["probeapp"]=m
django.setup()
from django.db import models, connections
class AuthorManager(models.Manager):
    def get_by_natural_key(self, name): return self.get(name=name)
class Author(models.Model):
    name = models.CharField(max_length=100, unique=True)
    objects = AuthorManager()
    class Meta: app_label="probeapp"
    def natural_key(self): return (self.name,)
class BookManager(models.Manager):
    def get_by_natural_key(self, title, author_name):
        return self.get(title=title, author__name=author_name)
class Book(models.Model):
    title = models.CharField(max_length=100)
    author = models.ForeignKey(Author, on_delete=models.CASCADE)
    objects = BookManager()
    class Meta: app_label="probeapp"
    def natural_key(self): return (self.title,) + self.author.natural_key()
    natural_key.dependencies=["probeapp.author"]
class Plain(models.Model):
    label = models.CharField(max_length=50)
    class Meta: app_label="probeapp"
def make_tables():
    for alias in ("default","other"):
        with connections[alias].schema_editor() as se:
            for mm in (Author, Book, Plain): se.create_model(mm)
from django.core.serializers.base import build_instance
make_tables()
# Author simple natural key, no matching row
inst = build_instance(Author, {"name": "Ghost"}, "other")
print("pk after miss:", inst.pk, "name:", inst.name)
sys.exit(0 if inst.pk is None and inst.name == "Ghost" else 1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
import django
from django.conf import settings
settings.configure(
    DEBUG=True,
    DATABASES={
        "default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"},
        "other":   {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"},
    },
    INSTALLED_APPS=["probeapp"],
    USE_TZ=False,
)
import sys, types, os, tempfile
_d = tempfile.mkdtemp()
m = types.ModuleType("probeapp"); m.__path__=[_d]; m.__file__=os.path.join(_d,"__init__.py"); sys.modules["probeapp"]=m
django.setup()
from django.db import models, connections
class AuthorManager(models.Manager):
    def get_by_natural_key(self, name): return self.get(name=name)
class Author(models.Model):
    name = models.CharField(max_length=100, unique=True)
    objects = AuthorManager()
    class Meta: app_label="probeapp"
    def natural_key(self): return (self.name,)
class BookManager(models.Manager):
    def get_by_natural_key(self, title, author_name):
        return self.get(title=title, author__name=author_name)
class Book(models.Model):
    title = models.CharField(max_length=100)
    author = models.ForeignKey(Author, on_delete=models.CASCADE)
    objects = BookManager()
    class Meta: app_label="probeapp"
    def natural_key(self): return (self.title,) + self.author.natural_key()
    natural_key.dependencies=["probeapp.author"]
class Plain(models.Model):
    label = models.CharField(max_length=50)
    class Meta: app_label="probeapp"
def make_tables():
    for alias in ("default","other"):
        with connections[alias].schema_editor() as se:
            for mm in (Author, Book, Plain): se.create_model(mm)
from django.core.serializers.base import build_instance
make_tables()
a = Author.objects.using("other").create(name="Same")
bk = Book.objects.using("other").create(title="TT", author=a)
data = {"title": "TT", "author_id": a.pk}
inst = build_instance(Book, dict(data), "other")
ok = (inst.title == "TT" and inst.author_id == a.pk and inst.id == bk.pk)
print("title:", inst.title, "author_id:", inst.author_id, "pk:", inst.id, "exp:", bk.pk)
sys.exit(0 if ok else 1)
```

Attack 7 — `probe_7.py` → holds on the patched tree (good)

```python
import django
from django.conf import settings
settings.configure(
    DEBUG=True,
    DATABASES={
        "default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"},
        "other":   {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"},
    },
    INSTALLED_APPS=["probeapp"],
    USE_TZ=False,
)
import sys, types, os, tempfile
_d = tempfile.mkdtemp()
m = types.ModuleType("probeapp"); m.__path__=[_d]; m.__file__=os.path.join(_d,"__init__.py"); sys.modules["probeapp"]=m
django.setup()
from django.db import models, connections
class AuthorManager(models.Manager):
    def get_by_natural_key(self, name): return self.get(name=name)
class Author(models.Model):
    name = models.CharField(max_length=100, unique=True)
    objects = AuthorManager()
    class Meta: app_label="probeapp"
    def natural_key(self): return (self.name,)
class BookManager(models.Manager):
    def get_by_natural_key(self, title, author_name):
        return self.get(title=title, author__name=author_name)
class Book(models.Model):
    title = models.CharField(max_length=100)
    author = models.ForeignKey(Author, on_delete=models.CASCADE)
    objects = BookManager()
    class Meta: app_label="probeapp"
    def natural_key(self): return (self.title,) + self.author.natural_key()
    natural_key.dependencies=["probeapp.author"]
class Plain(models.Model):
    label = models.CharField(max_length=50)
    class Meta: app_label="probeapp"
def make_tables():
    for alias in ("default","other"):
        with connections[alias].schema_editor() as se:
            for mm in (Author, Book, Plain): se.create_model(mm)
from django.core.serializers.base import build_instance
make_tables()
a = Author.objects.using("default").create(name="DefAuth")
bk = Book.objects.using("default").create(title="DefBook", author=a)
data = {"title": "DefBook", "author_id": a.pk}
inst = build_instance(Book, dict(data), "default")
print("resolved pk:", inst.id, "expected:", bk.pk)
sys.exit(0 if inst.id == bk.pk else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
import django
from django.conf import settings
settings.configure(
    DEBUG=True,
    DATABASES={
        "default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"},
        "other":   {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"},
    },
    INSTALLED_APPS=["probeapp"],
    USE_TZ=False,
)
import sys, types, os, tempfile
_d = tempfile.mkdtemp()
m = types.ModuleType("probeapp"); m.__path__=[_d]; m.__file__=os.path.join(_d,"__init__.py"); sys.modules["probeapp"]=m
django.setup()
from django.db import models, connections
class AuthorManager(models.Manager):
    def get_by_natural_key(self, name): return self.get(name=name)
class Author(models.Model):
    name = models.CharField(max_length=100, unique=True)
    objects = AuthorManager()
    class Meta: app_label="probeapp"
    def natural_key(self): return (self.name,)
class BookManager(models.Manager):
    def get_by_natural_key(self, title, author_name):
        return self.get(title=title, author__name=author_name)
class Book(models.Model):
    title = models.CharField(max_length=100)
    author = models.ForeignKey(Author, on_delete=models.CASCADE)
    objects = BookManager()
    class Meta: app_label="probeapp"
    def natural_key(self): return (self.title,) + self.author.natural_key()
    natural_key.dependencies=["probeapp.author"]
class Plain(models.Model):
    label = models.CharField(max_length=50)
    class Meta: app_label="probeapp"
def make_tables():
    for alias in ("default","other"):
        with connections[alias].schema_editor() as se:
            for mm in (Author, Book, Plain): se.create_model(mm)
# Req 1.2/1.3 + POSITIVE CONTROL: FK-natural-key resolves against target db 'other'.
from django.core.serializers.base import build_instance
make_tables()
a = Author.objects.using("other").create(name="AuthOther")
bk = Book.objects.using("other").create(title="BookOther", author=a)
data = {"title": "BookOther", "author_id": a.pk}
try:
    inst = build_instance(Book, dict(data), "other")
except Exception as e:
    print("build_instance RAISED:", type(e).__name__, e); sys.exit(1)
got = getattr(inst, "id", None)
print("resolved pk:", got, "expected:", bk.pk)
sys.exit(0 if got == bk.pk else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance: django__django-15525. Fix under audit: build_instance() sets obj._state.db = db before invoking obj.natural_key() so FK-traversing natural keys query the target database. Environment: Django 4.1.dev, py3.9, sqlite in-memory default+other DBs; probeapp given a real filesystem path via tempfile so app registry accepts it.

Probe coverage (all HOLD on gold-patched tree):
- probe_1 (Req 1.2/1.3 + POSITIVE CONTROL): Book.natural_key follows FK to Author present only in 'other'; build_instance resolves pk without DoesNotExist. Patched: HOLDS (pk=1). Base: VIOLATED (DoesNotExist) — prepatch reproduced, discriminating power confirmed.
- probe_2 (Req 1.1): spy natural_key() observes self._state.db == 'other' at invocation time. Patched HOLDS; base and weak_late give None.
- probe_3 (Req 2.1): data already has pk -> no natural-key lookup, pk kept (999), no FK query attempted.
- probe_4 (Req 2.2): model without natural key -> built directly, pk None.
- probe_5 (Req 2.3): natural-key miss -> DoesNotExist swallowed, pk absent, no raise.
- probe_6 (Req 2.4): descriptive fields (title, author_id) unchanged; only pk populated on match. Rejects weak_late.
- probe_7 (Req 2.5): FK-natural-key fixture still loads into DEFAULT db.

Candidate patch weak_late (requirements-informed wrong fix): sets _state.db after natural_key(). REJECTED by probes 1,2,6 -> suite discriminates wrong implementations. No probe-conforming alternative found; verdict SOUND.

(Req 2.6 dependency-ordering is a serializer/loaddata orchestration concern outside build_instance's unit scope and not separately probed; build_instance behavior itself is fully covered.)

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 7 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 7 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py`, `probe_7.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

Counterexample / evidence:

```
weak_late candidate (assign obj._state.db = db AFTER calling obj.natural_key() instead of before) is rejected by probes 1, 2, 6: the FK-following natural_key() still queries the default database, raising DoesNotExist when the related Author exists only in the target 'other' db.
```

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
import django
from django.conf import settings
settings.configure(
    DEBUG=True,
    DATABASES={
        "default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"},
        "other":   {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"},
    },
    INSTALLED_APPS=["probeapp"],
    USE_TZ=False,
)
import sys, types, os, tempfile
_d = tempfile.mkdtemp()
m = types.ModuleType("probeapp"); m.__path__=[_d]; m.__file__=os.path.join(_d,"__init__.py"); sys.modules["probeapp"]=m
django.setup()
from django.db import models, connections
class AuthorManager(models.Manager):
    def get_by_natural_key(self, name): return self.get(name=name)
class Author(models.Model):
    name = models.CharField(max_length=100, unique=True)
    objects = AuthorManager()
    class Meta: app_label="probeapp"
    def natural_key(self): return (self.name,)
class BookManager(models.Manager):
    def get_by_natural_key(self, title, author_name):
        return self.get(title=title, author__name=author_name)
class Book(models.Model):
    title = models.CharField(max_length=100)
    author = models.ForeignKey(Author, on_delete=models.CASCADE)
    objects = BookManager()
    class Meta: app_label="probeapp"
    def natural_key(self): return (self.title,) + self.author.natural_key()
    natural_key.dependencies=["probeapp.author"]
class Plain(models.Model):
    label = models.CharField(max_length=50)
    class Meta: app_label="probeapp"
def make_tables():
    for alias in ("default","other"):
        with connections[alias].schema_editor() as se:
            for mm in (Author, Book, Plain): se.create_model(mm)
# Req 1.2/1.3 + POSITIVE CONTROL: FK-natural-key resolves against target db 'other'.
from django.core.serializers.base import build_instance
make_tables()
a = Author.objects.using("other").create(name="AuthOther")
bk = Book.objects.using("other").create(title="BookOther", author=a)
data = {"title": "BookOther", "author_id": a.pk}
try:
    inst = build_instance(Book, dict(data), "other")
except Exception as e:
    print("build_instance RAISED:", type(e).__name__, e); sys.exit(1)
got = getattr(inst, "id", None)
print("resolved pk:", got, "expected:", bk.pk)
sys.exit(0 if got == bk.pk else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance: django__django-15525. Fix under audit: build_instance() sets obj._state.db = db before invoking obj.natural_key() so FK-traversing natural keys query the target database. Environment: Django 4.1.dev, py3.9, sqlite in-memory default+other DBs; probeapp given a real filesystem path via tempfile so app registry accepts it.

Probe coverage (all HOLD on gold-patched tree):
- probe_1 (Req 1.2/1.3 + POSITIVE CONTROL): Book.natural_key follows FK to Author present only in 'other'; build_instance resolves pk without DoesNotExist. Patched: HOLDS (pk=1). Base: VIOLATED (DoesNotExist) — prepatch reproduced, discriminating power confirmed.
- probe_2 (Req 1.1): spy natural_key() observes self._state.db == 'other' at invocation time. Patched HOLDS; base and weak_late give None.
- probe_3 (Req 2.1): data already has pk -> no natural-key lookup, pk kept (999), no FK query attempted.
- probe_4 (Req 2.2): model without natural key -> built directly, pk None.
- probe_5 (Req 2.3): natural-key miss -> DoesNotExist swallowed, pk absent, no raise.
- probe_6 (Req 2.4): descriptive fields (title, author_id) unchanged; only pk populated on match. Rejects weak_late.
- probe_7 (Req 2.5): FK-natural-key fixture still loads into DEFAULT db.

Candidate patch weak_late (requirements-informed wrong fix): sets _state.db after natural_key(). REJECTED by probes 1,2,6 -> suite discriminates wrong implementations. No probe-conforming alternative found; verdict SOUND.

(Req 2.6 dependency-ordering is a serializer/loaddata orchestration concern outside build_instance's unit scope and not separately probed; build_instance behavior itself is fully covered.)

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Modeling boundary is correct: Req 1 targets the changed observable (target-db natural-key resolution incl. related lookups) rather than a narrow slice like only the _state.db assignment; Req 2 correctly fences off the unchanged paths. FAIL_TO_PASS and the model fixture (NaturalKeyWithFKDependency.natural_key = (name,) + author.natural_key()) directly exercise the FK-traversal scenario the requirements describe.

Counterexample / evidence:

```
N/A — probed the gold-patched instance image (swebench_unified.nl_attack probe): build_instance source at runtime contains `obj = Model(**data)`, `obj._state.db = db`, `natural_key = obj.natural_key()`, and the to_python/db_manager(db).get_by_natural_key lookup, matching requirements 1.1/1.4 exactly; the pk guard `pk = data.get(...)` / `pk is None` backs 2.1/2.2, and `except Model.DoesNotExist: pass` backs 2.3.
```


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The document localizes the change to build_instance in django/core/serializers/base.py (legitimate) and describes behavior in EARS prose. Every concrete example it uses — Book/Author models, natural_key() returning (self.title,) + self.author.natural_key(), the DoesNotExist on --database other, and the default_manager.db_manager(db).get_by_natural_key(...) / to_python lines — is drawn from the PUBLIC problem_statement or is pre-existing (base-commit) code of build_instance, not gold-invented. None of the hidden-test artifacts appear: no test class name (NaturalKeyFixtureOnOtherDatabaseTests), no fixture path/name (fixtures/nk_with_foreign_key.json), no test-only model/identifiers (NaturalKeyWithFKDependency, NaturalKeyWithFKDependencyManager, Person), no data literals ('The Lord of the Rings', 'J.R.R. Tolkien'), no FAIL_TO_PASS/PASS_TO_PASS ids, and no unrelated PASS_TO_PASS artifact (the sqlite mock.patch.object cursor change). The fix-invented mechanism (obj._state.db = db) is described purely behaviorally ('associated with the target database db before natural_key() is invoked') without transmitting the private attribute or code. Requirement 2's regression clauses translate general invariants, not enumerated parametrized cases. No reconstruction of the hidden tests beyond the public spec.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
