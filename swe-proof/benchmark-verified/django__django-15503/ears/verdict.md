# P2 adversarial audit — django__django-15503

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
"""Probe 1 (POSITIVE CONTROL) — Requirement 1.1/1.2:
has_key with an all-digit top-level key ("1111") must MATCH a row whose JSON
object contains that member on SQLite. HOLDS on patched, FAILS at base.
Exit 0 iff the numeric-key row is matched (and a row without it is not)."""
import django
from django.conf import settings

settings.configure(
    DEBUG=True,
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3",
                           "NAME": ":memory:"}},
    INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth", "probeapp"],
    USE_TZ=False,
)
import sys, types, tempfile, os
_appdir = tempfile.mkdtemp()
open(os.path.join(_appdir, "__init__.py"), "w").close()
app = types.ModuleType("probeapp")
app.__path__ = [_appdir]
app.__file__ = os.path.join(_appdir, "__init__.py")
sys.modules["probeapp"] = app
django.setup()

from django.db import models, connection

class M(models.Model):
    value = models.JSONField()
    class Meta:
        app_label = "probeapp"

with connection.schema_editor() as se:
    se.create_model(M)

a = M.objects.create(value={"1111": "x", "foo": 1})
b = M.objects.create(value={"foo": 1})
c = M.objects.create(value={"2222": "y"})

matched = set(M.objects.filter(value__has_key="1111").values_list("id", flat=True))
print("has_key('1111') matched ids:", sorted(matched), "expected:", [a.id])
ok = matched == {a.id}
print("OK" if ok else "FAIL")
sys.exit(0 if ok else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""Probe 2 — Requirement 1.3: leading-zero all-digit key '007' must match the
object member of that exact name, not be reinterpreted as index 7."""
import django, sys, types, tempfile, os
from django.conf import settings
settings.configure(
    DEBUG=True,
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth", "probeapp"],
    USE_TZ=False,
)
_appdir = tempfile.mkdtemp()
open(os.path.join(_appdir, "__init__.py"), "w").close()
app = types.ModuleType("probeapp")
app.__path__ = [_appdir]; app.__file__ = os.path.join(_appdir, "__init__.py")
sys.modules["probeapp"] = app
django.setup()
from django.db import models, connection
from django.db.models.fields.json import KeyTransform
from django.db.models import Q
class M(models.Model):
    value = models.JSONField()
    class Meta:
        app_label = "probeapp"
with connection.schema_editor() as se:
    se.create_model(M)
def done(ok, msg):
    print(msg); print("OK" if ok else "FAIL"); sys.exit(0 if ok else 1)
a = M.objects.create(value={"007": "x"})
b = M.objects.create(value={"7": "y"})
m = set(M.objects.filter(value__has_key="007").values_list("id", flat=True))
print("has_key('007') matched:", sorted(m), "expected:", [a.id])
done(m == {a.id}, "leading-zero numeric key addressed as member name")
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""Probe 3 — Requirement 2.1: nested numeric key reached through intermediate
object member must match. value__baz__has_key='1111'."""
import django, sys, types, tempfile, os
from django.conf import settings
settings.configure(
    DEBUG=True,
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth", "probeapp"],
    USE_TZ=False,
)
_appdir = tempfile.mkdtemp()
open(os.path.join(_appdir, "__init__.py"), "w").close()
app = types.ModuleType("probeapp")
app.__path__ = [_appdir]; app.__file__ = os.path.join(_appdir, "__init__.py")
sys.modules["probeapp"] = app
django.setup()
from django.db import models, connection
from django.db.models.fields.json import KeyTransform
from django.db.models import Q
class M(models.Model):
    value = models.JSONField()
    class Meta:
        app_label = "probeapp"
with connection.schema_editor() as se:
    se.create_model(M)
def done(ok, msg):
    print(msg); print("OK" if ok else "FAIL"); sys.exit(0 if ok else 1)
a = M.objects.create(value={"baz": {"1111": 1, "a": 2}})
b = M.objects.create(value={"baz": {"a": 2}})
m = set(M.objects.filter(value__baz__has_key="1111").values_list("id", flat=True))
print("value__baz__has_key('1111') matched:", sorted(m), "expected:", [a.id])
done(m == {a.id}, "nested numeric key found as member")
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""Probe 4 — Requirement 2.2/2.3: numeric key beneath an array element. The
intermediate positional transform [1] addresses the array element by index,
the final all-digit key '1111' is addressed as an object member name."""
import django, sys, types, tempfile, os
from django.conf import settings
settings.configure(
    DEBUG=True,
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth", "probeapp"],
    USE_TZ=False,
)
_appdir = tempfile.mkdtemp()
open(os.path.join(_appdir, "__init__.py"), "w").close()
app = types.ModuleType("probeapp")
app.__path__ = [_appdir]; app.__file__ = os.path.join(_appdir, "__init__.py")
sys.modules["probeapp"] = app
django.setup()
from django.db import models, connection
from django.db.models.fields.json import KeyTransform
from django.db.models import Q
class M(models.Model):
    value = models.JSONField()
    class Meta:
        app_label = "probeapp"
with connection.schema_editor() as se:
    se.create_model(M)
def done(ok, msg):
    print(msg); print("OK" if ok else "FAIL"); sys.exit(0 if ok else 1)
a = M.objects.create(value=[{"a": 1}, {"1111": "z"}])
b = M.objects.create(value=[{"1111": "z"}, {"a": 1}])  # 1111 under index 0, not 1
m = set(M.objects.filter(value__1__has_key="1111").values_list("id", flat=True))
print("value__1__has_key('1111') matched:", sorted(m), "expected:", [a.id])
done(m == {a.id}, "intermediate index preserved; final numeric key as member")
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""Probe 5 — Requirement 3.1/3.2: has_keys AND has_any_keys honor numeric keys."""
import django, sys, types, tempfile, os
from django.conf import settings
settings.configure(
    DEBUG=True,
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth", "probeapp"],
    USE_TZ=False,
)
_appdir = tempfile.mkdtemp()
open(os.path.join(_appdir, "__init__.py"), "w").close()
app = types.ModuleType("probeapp")
app.__path__ = [_appdir]; app.__file__ = os.path.join(_appdir, "__init__.py")
sys.modules["probeapp"] = app
django.setup()
from django.db import models, connection
from django.db.models.fields.json import KeyTransform
from django.db.models import Q
class M(models.Model):
    value = models.JSONField()
    class Meta:
        app_label = "probeapp"
with connection.schema_editor() as se:
    se.create_model(M)
def done(ok, msg):
    print(msg); print("OK" if ok else "FAIL"); sys.exit(0 if ok else 1)
a = M.objects.create(value={"1111": 1, "2222": 2})   # has both
b = M.objects.create(value={"1111": 1})              # has one
c = M.objects.create(value={"foo": 1})               # neither
hk = set(M.objects.filter(value__has_keys=["1111", "2222"]).values_list("id", flat=True))
ha = set(M.objects.filter(value__has_any_keys=["1111", "2222"]).values_list("id", flat=True))
print("has_keys([1111,2222]):", sorted(hk), "expected:", [a.id])
print("has_any_keys([1111,2222]):", sorted(ha), "expected:", sorted([a.id, b.id]))
done(hk == {a.id} and ha == {a.id, b.id}, "multi-key numeric lookups honored")
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
"""Probe 6 — Requirement 4 (regression): non-numeric has_key/has_any_keys/deep/
null-value presence all still behave as before."""
import django, sys, types, tempfile, os
from django.conf import settings
settings.configure(
    DEBUG=True,
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth", "probeapp"],
    USE_TZ=False,
)
_appdir = tempfile.mkdtemp()
open(os.path.join(_appdir, "__init__.py"), "w").close()
app = types.ModuleType("probeapp")
app.__path__ = [_appdir]; app.__file__ = os.path.join(_appdir, "__init__.py")
sys.modules["probeapp"] = app
django.setup()
from django.db import models, connection
from django.db.models.fields.json import KeyTransform
from django.db.models import Q
class M(models.Model):
    value = models.JSONField()
    class Meta:
        app_label = "probeapp"
with connection.schema_editor() as se:
    se.create_model(M)
def done(ok, msg):
    print(msg); print("OK" if ok else "FAIL"); sys.exit(0 if ok else 1)
o3 = M.objects.create(value={"a": 1, "c": 2})
o4 = M.objects.create(value={"a": 1, "c": 2, "h": 3, "j": None})
o6 = M.objects.create(value={"l": 1})
o7 = M.objects.create(value={"baz": {"a": "b", "c": "d"}})
r_hk = set(M.objects.filter(value__has_key="a").values_list("id", flat=True))
r_any = set(M.objects.filter(value__has_any_keys=["c", "l"]).values_list("id", flat=True))
r_deep = set(M.objects.filter(value__baz__has_key="a").values_list("id", flat=True))
r_null = set(M.objects.filter(value__has_key="j").values_list("id", flat=True))
print("has_key(a):", sorted(r_hk), "exp", sorted([o3.id, o4.id]))
print("has_any_keys(c,l):", sorted(r_any), "exp", sorted([o3.id, o4.id, o6.id]))
print("baz__has_key(a):", sorted(r_deep), "exp", [o7.id])
print("has_key(j) null value present:", sorted(r_null), "exp", [o4.id])
ok = (r_hk == {o3.id, o4.id} and r_any == {o3.id, o4.id, o6.id}
      and r_deep == {o7.id} and r_null == {o4.id})
done(ok, "non-numeric regression behaviors preserved")
```

Attack 7 — `probe_7.py` → holds on the patched tree (good)

```python
"""Probe 7 — Requirement 5.2: key__isnull=False remains equivalent to key
present using the array-index-capable rendering variant. For an array element
selected by a positional key transform, isnull=False matches when present."""
import django, sys, types, tempfile, os
from django.conf import settings
settings.configure(
    DEBUG=True,
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth", "probeapp"],
    USE_TZ=False,
)
_appdir = tempfile.mkdtemp()
open(os.path.join(_appdir, "__init__.py"), "w").close()
app = types.ModuleType("probeapp")
app.__path__ = [_appdir]; app.__file__ = os.path.join(_appdir, "__init__.py")
sys.modules["probeapp"] = app
django.setup()
from django.db import models, connection
from django.db.models.fields.json import KeyTransform
from django.db.models import Q
class M(models.Model):
    value = models.JSONField()
    class Meta:
        app_label = "probeapp"
with connection.schema_editor() as se:
    se.create_model(M)
def done(ok, msg):
    print(msg); print("OK" if ok else "FAIL"); sys.exit(0 if ok else 1)
a = M.objects.create(value=[{"a": 1}, {"b": 2}])  # index 1 present
b = M.objects.create(value=[{"a": 1}])            # index 1 absent
m = set(M.objects.filter(value__1__isnull=False).values_list("id", flat=True))
print("value__1__isnull=False matched:", sorted(m), "expected:", [a.id])
done(m == {a.id}, "isnull array-index-capable rendering preserved")
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Probe 1 (POSITIVE CONTROL) — Requirement 1.1/1.2:
has_key with an all-digit top-level key ("1111") must MATCH a row whose JSON
object contains that member on SQLite. HOLDS on patched, FAILS at base.
Exit 0 iff the numeric-key row is matched (and a row without it is not)."""
import django
from django.conf import settings

settings.configure(
    DEBUG=True,
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3",
                           "NAME": ":memory:"}},
    INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth", "probeapp"],
    USE_TZ=False,
)
import sys, types, tempfile, os
_appdir = tempfile.mkdtemp()
open(os.path.join(_appdir, "__init__.py"), "w").close()
app = types.ModuleType("probeapp")
app.__path__ = [_appdir]
app.__file__ = os.path.join(_appdir, "__init__.py")
sys.modules["probeapp"] = app
django.setup()

from django.db import models, connection

class M(models.Model):
    value = models.JSONField()
    class Meta:
        app_label = "probeapp"

with connection.schema_editor() as se:
    se.create_model(M)

a = M.objects.create(value={"1111": "x", "foo": 1})
b = M.objects.create(value={"foo": 1})
c = M.objects.create(value={"2222": "y"})

matched = set(M.objects.filter(value__has_key="1111").values_list("id", flat=True))
print("has_key('1111') matched ids:", sorted(matched), "expected:", [a.id])
ok = matched == {a.id}
print("OK" if ok else "FAIL")
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Django JSONField has_key/has_keys/has_any_keys numeric-key fix (django-15503). All probes run in the instance's official Docker image via nl_attack; each is standalone (stdlib + django only), configures in-memory SQLite, and exits 0 iff the criterion holds.

Probes (path -> requirement -> observed):
- probe_1.py (POSITIVE CONTROL) -> Req 1.1/1.2: has_key('1111') matches the row containing that member. PATCHED: HOLDS (matched [1]). BASE: FAILS (matched []). Discriminates.
- probe_2.py -> Req 1.3: leading-zero key '007' matches member '007', not normalized to index 7. PATCHED HOLDS.
- probe_3.py -> Req 2.1: nested numeric key value__baz__has_key('1111') matches. PATCHED HOLDS.
- probe_4.py -> Req 2.2/2.3: value__1__has_key('1111') — intermediate positional [1] addressed by index, final numeric key as member; matches only the row with 1111 under index 1. PATCHED HOLDS.
- probe_5.py -> Req 3.1/3.2: has_keys/has_any_keys honor numeric keys (AND vs OR semantics). PATCHED HOLDS.
- probe_6.py -> Req 4.1-4.4: regression — non-numeric has_key, has_any_keys, deep baz__has_key, and null-value presence (has_key('j')) all preserved. PATCHED HOLDS.
- probe_7.py -> Req 5.2: value__1__isnull=False remains present-test via the array-index-capable rendering variant. PATCHED HOLDS.

All 7 hold on the gold-patched tree.

Weak candidate (naive_always_member, weak.diff): makes compile_json_path ALWAYS render every segment as a quoted member (drops the int/array-index branch entirely) — the lazy over-broad reading of Requirement 1. It satisfies the top-level numeric case (probe_1 HOLDS) but is REJECTED by probe_4 (matched [] expected [1] — intermediate array index broken) and probe_7 (matched [] expected [1] — isnull array-index rendering broken). This demonstrates the suite discriminates a wrong implementation: it enforces the gold design's split between intermediate (index-capable) and final-key (member) rendering, which the naive fix violates. No requirement-conforming alternative patch found that fails the harness.

Verdict SOUND: 7 distinct probes all hold on patched; positive control fails at base and holds patched (discriminating power confirmed); >=1 wrong-fix candidate exercised and rejected by the probe suite.

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
"""Probe 1 (POSITIVE CONTROL) — Requirement 1.1/1.2:
has_key with an all-digit top-level key ("1111") must MATCH a row whose JSON
object contains that member on SQLite. HOLDS on patched, FAILS at base.
Exit 0 iff the numeric-key row is matched (and a row without it is not)."""
import django
from django.conf import settings

settings.configure(
    DEBUG=True,
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3",
                           "NAME": ":memory:"}},
    INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth", "probeapp"],
    USE_TZ=False,
)
import sys, types, tempfile, os
_appdir = tempfile.mkdtemp()
open(os.path.join(_appdir, "__init__.py"), "w").close()
app = types.ModuleType("probeapp")
app.__path__ = [_appdir]
app.__file__ = os.path.join(_appdir, "__init__.py")
sys.modules["probeapp"] = app
django.setup()

from django.db import models, connection

class M(models.Model):
    value = models.JSONField()
    class Meta:
        app_label = "probeapp"

with connection.schema_editor() as se:
    se.create_model(M)

a = M.objects.create(value={"1111": "x", "foo": 1})
b = M.objects.create(value={"foo": 1})
c = M.objects.create(value={"2222": "y"})

matched = set(M.objects.filter(value__has_key="1111").values_list("id", flat=True))
print("has_key('1111') matched ids:", sorted(matched), "expected:", [a.id])
ok = matched == {a.id}
print("OK" if ok else "FAIL")
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Django JSONField has_key/has_keys/has_any_keys numeric-key fix (django-15503). All probes run in the instance's official Docker image via nl_attack; each is standalone (stdlib + django only), configures in-memory SQLite, and exits 0 iff the criterion holds.

Probes (path -> requirement -> observed):
- probe_1.py (POSITIVE CONTROL) -> Req 1.1/1.2: has_key('1111') matches the row containing that member. PATCHED: HOLDS (matched [1]). BASE: FAILS (matched []). Discriminates.
- probe_2.py -> Req 1.3: leading-zero key '007' matches member '007', not normalized to index 7. PATCHED HOLDS.
- probe_3.py -> Req 2.1: nested numeric key value__baz__has_key('1111') matches. PATCHED HOLDS.
- probe_4.py -> Req 2.2/2.3: value__1__has_key('1111') — intermediate positional [1] addressed by index, final numeric key as member; matches only the row with 1111 under index 1. PATCHED HOLDS.
- probe_5.py -> Req 3.1/3.2: has_keys/has_any_keys honor numeric keys (AND vs OR semantics). PATCHED HOLDS.
- probe_6.py -> Req 4.1-4.4: regression — non-numeric has_key, has_any_keys, deep baz__has_key, and null-value presence (has_key('j')) all preserved. PATCHED HOLDS.
- probe_7.py -> Req 5.2: value__1__isnull=False remains present-test via the array-index-capable rendering variant. PATCHED HOLDS.

All 7 hold on the gold-patched tree.

Weak candidate (naive_always_member, weak.diff): makes compile_json_path ALWAYS render every segment as a quoted member (drops the int/array-index branch entirely) — the lazy over-broad reading of Requirement 1. It satisfies the top-level numeric case (probe_1 HOLDS) but is REJECTED by probe_4 (matched [] expected [1] — intermediate array index broken) and probe_7 (matched [] expected [1] — isnull array-index rendering broken). This demonstrates the suite discriminates a wrong implementation: it enforces the gold design's split between intermediate (index-capable) and final-key (member) rendering, which the naive fix violates. No requirement-conforming alternative patch found that fails the harness.

Verdict SOUND: 7 distinct probes all hold on patched; positive control fails at base and holds patched (discriminating power confirmed); >=1 wrong-fix candidate exercised and rejected by the probe suite.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Probed on gold-patched instance image. The requirements model the changed boundary biconditionally: existence lookups (has_key/has_keys/has_any_keys) render the FINAL tested key as a named member on all backends via HasKeyLookup.compile_json_path_final_key = '.%s' % json.dumps(key), while intermediate descent transforms remain positional via compile_json_path, and the isnull/none-value key lookups retain the array-index-capable variant HasKeyOrArrayIndex. This matches the full gold diff (4 hunks) rather than a narrow slice — e.g. Req5 correctly captures all three isnull/none-value call sites, not just one. Leading-zero preservation (Req 1.3) is guaranteed by json.dumps, verified. No invented behavior; no omitted changed behavior.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Requirements describe behavior and localize to pre-existing public symbols (compile_json_path, HasKeyLookup/HasKey/HasKeys/HasAnyKeys, json.py, backend predicates JSON_TYPE/JSON_CONTAINS_PATH/JSON_EXISTS). The gold's fix-invented identifiers (compile_json_path_final_key, HasKeyOrArrayIndex) are described behaviorally in Req 2/5 but never named. No test names/paths/parametrization ids or quoted test/gold code appear. The {has_key,has_keys,has_any_keys}×{top,nested,array} coverage in Req 2/3 is the genuine behavioral surface, not a 1:1 transcription of the 9 hidden Q(...) cases. Closest concern is Req 1.3's leading-zero '000' case (present only in the hidden test, not problem_statement), but it is stated as a behavioral rule about digit-runs vs array indices — legitimate domain reasoning, not test reconstruction.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
