# P2 adversarial audit — django__django-11179

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
"""Requirement 1.1/1.2: deleting a dependency-free instance via model.delete()
leaves instance.pk == None (fast path clears the PK)."""
import django
from django.conf import settings

settings.configure(
    DEBUG=True,
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth", "probeapp"],
    DEFAULT_AUTO_FIELD="django.db.models.AutoField",
)
import sys, types
import os, tempfile
_appdir = tempfile.mkdtemp()
open(os.path.join(_appdir, "__init__.py"), "w").close()
mod = types.ModuleType("probeapp")
mod.__path__ = [_appdir]
mod.__file__ = os.path.join(_appdir, "__init__.py")
sys.modules["probeapp"] = mod
django.setup()

from django.db import models, connection


class Simple(models.Model):
    name = models.CharField(max_length=20)

    class Meta:
        app_label = "probeapp"


with connection.schema_editor() as se:
    se.create_model(Simple)

obj = Simple.objects.create(name="x")
pk_before = obj.pk
assert pk_before is not None, "sanity: created object should have a pk"
obj.delete()
print("pk_before=%r pk_after=%r" % (pk_before, obj.pk))
if obj.pk is None:
    print("HOLD: pk cleared to None after fast delete")
    sys.exit(0)
print("VIOLATION: pk not cleared")
sys.exit(1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""Requirement 1.3: PK cleared using the model's actual pk attname, even when
the primary key is a custom/renamed field not named 'id'."""
import django
from django.conf import settings

settings.configure(
    DEBUG=True,
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth", "probeapp"],
    DEFAULT_AUTO_FIELD="django.db.models.AutoField",
)
import sys, types
import os, tempfile
_appdir = tempfile.mkdtemp()
open(os.path.join(_appdir, "__init__.py"), "w").close()
mod = types.ModuleType("probeapp")
mod.__path__ = [_appdir]
mod.__file__ = os.path.join(_appdir, "__init__.py")
sys.modules["probeapp"] = mod
django.setup()

from django.db import models, connection


class CustomPK(models.Model):
    code = models.AutoField(primary_key=True)
    name = models.CharField(max_length=20)

    class Meta:
        app_label = "probeapp"


with connection.schema_editor() as se:
    se.create_model(CustomPK)

obj = CustomPK.objects.create(name="y")
assert obj._meta.pk.attname == "code", "sanity: pk attname should be 'code'"
before = obj.code
obj.delete()
print("attname=%r code_before=%r code_after=%r pk=%r"
      % (obj._meta.pk.attname, before, obj.code, obj.pk))
if obj.code is None and obj.pk is None:
    print("HOLD: custom pk attribute 'code' cleared to None")
    sys.exit(0)
print("VIOLATION: custom pk not cleared")
sys.exit(1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""Requirement 2.1: fast-path delete() returns (total, {label: count}) exactly
as before — the return value semantics are preserved."""
import django
from django.conf import settings

settings.configure(
    DEBUG=True,
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth", "probeapp"],
    DEFAULT_AUTO_FIELD="django.db.models.AutoField",
)
import sys, types
import os, tempfile
_appdir = tempfile.mkdtemp()
open(os.path.join(_appdir, "__init__.py"), "w").close()
mod = types.ModuleType("probeapp")
mod.__path__ = [_appdir]
mod.__file__ = os.path.join(_appdir, "__init__.py")
sys.modules["probeapp"] = mod
django.setup()

from django.db import models, connection


class Simple(models.Model):
    name = models.CharField(max_length=20)

    class Meta:
        app_label = "probeapp"


with connection.schema_editor() as se:
    se.create_model(Simple)

obj = Simple.objects.create(name="x")
label = Simple._meta.label
ret = obj.delete()
print("return=%r" % (ret,))
total, per_model = ret
if total == 1 and per_model == {label: 1}:
    print("HOLD: fast-path return semantics preserved")
    sys.exit(0)
print("VIOLATION: unexpected return value")
sys.exit(1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""Requirement 2.2: clearing the pk is an in-memory assignment issuing NO extra
query. The fast path performs exactly ONE db operation (a single DELETE)."""
import django
from django.conf import settings

settings.configure(
    DEBUG=True,
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth", "probeapp"],
    DEFAULT_AUTO_FIELD="django.db.models.AutoField",
)
import sys, types
import os, tempfile
_appdir = tempfile.mkdtemp()
open(os.path.join(_appdir, "__init__.py"), "w").close()
mod = types.ModuleType("probeapp")
mod.__path__ = [_appdir]
mod.__file__ = os.path.join(_appdir, "__init__.py")
sys.modules["probeapp"] = mod
django.setup()

from django.db import models, connection
from django.test.utils import CaptureQueriesContext


class Simple(models.Model):
    name = models.CharField(max_length=20)

    class Meta:
        app_label = "probeapp"


with connection.schema_editor() as se:
    se.create_model(Simple)

obj = Simple.objects.create(name="x")
with CaptureQueriesContext(connection) as ctx:
    obj.delete()
queries = [q["sql"] for q in ctx.captured_queries]
deletes = [q for q in queries if "DELETE" in q.upper()]
print("n_queries=%d queries=%r" % (len(queries), queries))
# Fast path should issue exactly one DELETE and no more than one query total.
if len(queries) == 1 and len(deletes) == 1:
    print("HOLD: exactly one DELETE query, no extra query for pk reset")
    sys.exit(0)
print("VIOLATION: unexpected query count")
sys.exit(1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""Requirement 3.1 + 2.3 + 3.6: an instance WITH dependents does NOT take the
fast path (goes general path), yet its pk is still cleared to None, and the
cascade count mapping is correct. Guards against a fix that only handles the
fast path while regressing the general path."""
import django
from django.conf import settings

settings.configure(
    DEBUG=True,
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth", "probeapp"],
    DEFAULT_AUTO_FIELD="django.db.models.AutoField",
)
import sys, types
import os, tempfile
_appdir = tempfile.mkdtemp()
open(os.path.join(_appdir, "__init__.py"), "w").close()
mod = types.ModuleType("probeapp")
mod.__path__ = [_appdir]
mod.__file__ = os.path.join(_appdir, "__init__.py")
sys.modules["probeapp"] = mod
django.setup()

from django.db import models, connection
from django.db.models.deletion import Collector


class Parent(models.Model):
    name = models.CharField(max_length=20)

    class Meta:
        app_label = "probeapp"


class Child(models.Model):
    parent = models.ForeignKey(Parent, on_delete=models.CASCADE)

    class Meta:
        app_label = "probeapp"


with connection.schema_editor() as se:
    se.create_model(Parent)
    se.create_model(Child)

p = Parent.objects.create(name="p")
Child.objects.create(parent=p)
Child.objects.create(parent=p)

# Confirm this instance is NOT fast-deletable (has dependents => general path).
coll = Collector(using="default")
fast = coll.can_fast_delete(p)
print("can_fast_delete(parent)=%r" % (fast,))
if fast:
    print("VIOLATION: parent with children wrongly deemed fast-deletable")
    sys.exit(1)

pk_before = p.pk
ret = p.delete()
print("return=%r pk_after=%r remaining_children=%d"
      % (ret, p.pk, Child.objects.count()))
total, per_model = ret
ok = (p.pk is None
      and total == 3
      and per_model.get(Parent._meta.label) == 1
      and per_model.get(Child._meta.label) == 2
      and Child.objects.count() == 0)
if ok:
    print("HOLD: general path clears pk, cascades, correct counts")
    sys.exit(0)
print("VIOLATION: general path regression")
sys.exit(1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
"""Requirement 3.2 + 3.5: on-delete SET_NULL honored and queued field updates
applied to in-memory related instances after deletion. Deleting the referenced
object nulls the FK both in DB and on the in-memory related object."""
import django
from django.conf import settings

settings.configure(
    DEBUG=True,
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth", "probeapp"],
    DEFAULT_AUTO_FIELD="django.db.models.AutoField",
)
import sys, types
import os, tempfile
_appdir = tempfile.mkdtemp()
open(os.path.join(_appdir, "__init__.py"), "w").close()
mod = types.ModuleType("probeapp")
mod.__path__ = [_appdir]
mod.__file__ = os.path.join(_appdir, "__init__.py")
sys.modules["probeapp"] = mod
django.setup()

from django.db import models, connection


class Target(models.Model):
    name = models.CharField(max_length=20)

    class Meta:
        app_label = "probeapp"


class Ref(models.Model):
    target = models.ForeignKey(Target, null=True, on_delete=models.SET_NULL)

    class Meta:
        app_label = "probeapp"


with connection.schema_editor() as se:
    se.create_model(Target)
    se.create_model(Ref)

t = Target.objects.create(name="t")
r = Ref.objects.create(target=t)
# Load a fresh in-memory ref that participates in the collection.
r_live = Ref.objects.get(pk=r.pk)
t.delete()
db_val = Ref.objects.get(pk=r.pk).target_id
print("db_target_id=%r t.pk=%r" % (db_val, t.pk))
if db_val is None and t.pk is None:
    print("HOLD: SET_NULL applied and deleted target pk cleared")
    sys.exit(0)
print("VIOLATION: SET_NULL / pk clearing regression")
sys.exit(1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Requirement 1.1/1.2: deleting a dependency-free instance via model.delete()
leaves instance.pk == None (fast path clears the PK)."""
import django
from django.conf import settings

settings.configure(
    DEBUG=True,
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth", "probeapp"],
    DEFAULT_AUTO_FIELD="django.db.models.AutoField",
)
import sys, types
import os, tempfile
_appdir = tempfile.mkdtemp()
open(os.path.join(_appdir, "__init__.py"), "w").close()
mod = types.ModuleType("probeapp")
mod.__path__ = [_appdir]
mod.__file__ = os.path.join(_appdir, "__init__.py")
sys.modules["probeapp"] = mod
django.setup()

from django.db import models, connection


class Simple(models.Model):
    name = models.CharField(max_length=20)

    class Meta:
        app_label = "probeapp"


with connection.schema_editor() as se:
    se.create_model(Simple)

obj = Simple.objects.create(name="x")
pk_before = obj.pk
assert pk_before is not None, "sanity: created object should have a pk"
obj.delete()
print("pk_before=%r pk_after=%r" % (pk_before, obj.pk))
if obj.pk is None:
    print("HOLD: pk cleared to None after fast delete")
    sys.exit(0)
print("VIOLATION: pk not cleared")
sys.exit(1)
```

Prepatch bug re-encoded as an attack: `True`.

Requirements cover the deletion.py fast-path pk-clearing fix (django-11179). 6 probes, all HOLD on gold-patched tree:
- probe_1 (Req 1.1/1.2): dependency-free instance.delete() leaves instance.pk == None. Patched HOLDS, BASE VIOLATED (pk stays 1) => positive control, discriminates.
- probe_2 (Req 1.3): model with custom pk attname 'code' has that attribute cleared to None. Patched HOLDS, BASE VIOLATED.
- probe_3 (Req 2.1): fast-path delete() returns (1, {label:1}). HOLDS patched & base (semantics preserved).
- probe_4 (Req 2.2): fast path issues exactly one DELETE query, no extra query for pk reset. HOLDS.
- probe_5 (Req 3.1/2.3/3.6): instance with cascade children is NOT fast-deletable, general path still clears pk and returns correct total/per-model counts. HOLDS.
- probe_6 (Req 3.2/3.5): SET_NULL honored and deleted target pk cleared. HOLDS.

Positive control (probe_1): FAILS at base (pk_after=1), HOLDS patched => prepatch reproduced.

Wrong-fix candidate weak.diff: naive fix that clears literal 'id' attr instead of model._meta.pk.attname. Applies at base cleanly. Probe suite REJECTS it via probe_2 (custom-pk model 'code' NOT cleared) — demonstrates the suite discriminates a plausible weak reading of Req 1.3. Probes 1,3,4,5,6 pass under it (they use default 'id' pk), so the suite is not over-broad. This candidate would also fail the hidden test focus on general pk attname behavior. No requirements-conforming candidate found that resolves incorrectly; the gold patch (setattr(instance, model._meta.pk.attname, None) after the delete) is the minimal faithful implementation.

All runs completed in the official docker image (python3.6/testbed). Requirements are faithful and adequately constraining.

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
"""Requirement 1.1/1.2: deleting a dependency-free instance via model.delete()
leaves instance.pk == None (fast path clears the PK)."""
import django
from django.conf import settings

settings.configure(
    DEBUG=True,
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth", "probeapp"],
    DEFAULT_AUTO_FIELD="django.db.models.AutoField",
)
import sys, types
import os, tempfile
_appdir = tempfile.mkdtemp()
open(os.path.join(_appdir, "__init__.py"), "w").close()
mod = types.ModuleType("probeapp")
mod.__path__ = [_appdir]
mod.__file__ = os.path.join(_appdir, "__init__.py")
sys.modules["probeapp"] = mod
django.setup()

from django.db import models, connection


class Simple(models.Model):
    name = models.CharField(max_length=20)

    class Meta:
        app_label = "probeapp"


with connection.schema_editor() as se:
    se.create_model(Simple)

obj = Simple.objects.create(name="x")
pk_before = obj.pk
assert pk_before is not None, "sanity: created object should have a pk"
obj.delete()
print("pk_before=%r pk_after=%r" % (pk_before, obj.pk))
if obj.pk is None:
    print("HOLD: pk cleared to None after fast delete")
    sys.exit(0)
print("VIOLATION: pk not cleared")
sys.exit(1)
```

Prepatch bug re-encoded as an attack: `True`.

Requirements cover the deletion.py fast-path pk-clearing fix (django-11179). 6 probes, all HOLD on gold-patched tree:
- probe_1 (Req 1.1/1.2): dependency-free instance.delete() leaves instance.pk == None. Patched HOLDS, BASE VIOLATED (pk stays 1) => positive control, discriminates.
- probe_2 (Req 1.3): model with custom pk attname 'code' has that attribute cleared to None. Patched HOLDS, BASE VIOLATED.
- probe_3 (Req 2.1): fast-path delete() returns (1, {label:1}). HOLDS patched & base (semantics preserved).
- probe_4 (Req 2.2): fast path issues exactly one DELETE query, no extra query for pk reset. HOLDS.
- probe_5 (Req 3.1/2.3/3.6): instance with cascade children is NOT fast-deletable, general path still clears pk and returns correct total/per-model counts. HOLDS.
- probe_6 (Req 3.2/3.5): SET_NULL honored and deleted target pk cleared. HOLDS.

Positive control (probe_1): FAILS at base (pk_after=1), HOLDS patched => prepatch reproduced.

Wrong-fix candidate weak.diff: naive fix that clears literal 'id' attr instead of model._meta.pk.attname. Applies at base cleanly. Probe suite REJECTS it via probe_2 (custom-pk model 'code' NOT cleared) — demonstrates the suite discriminates a plausible weak reading of Req 1.3. Probes 1,3,4,5,6 pass under it (they use default 'id' pk), so the suite is not over-broad. This candidate would also fail the hidden test focus on general pk attname behavior. No requirements-conforming candidate found that resolves incorrectly; the gold patch (setattr(instance, model._meta.pk.attname, None) after the delete) is the minimal faithful implementation.

All runs completed in the official docker image (python3.6/testbed). Requirements are faithful and adequately constraining.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Probed both gold-patched (HOLDS: pk cleared, custom-pk attname cleared, count/return preserved) and base (VIOLATED: pk not cleared) in the instance image. Requirements pin exactly the changed observable behavior; the custom-PK criterion (R1.3) faithfully captures the pk.attname detail of the patch rather than a hardcoded 'id'. No over-claiming or invented behavior found.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The single hidden test (test_fast_delete_instance_set_pk_none) checks that after u.delete() on a fast-deletable User, u.pk is None, and constructs a Collector to assert can_fast_delete(u). The gold patch adds `setattr(instance, model._meta.pk.attname, None)` after the fast-delete batch. requirements.md describes only behavior: fast-delete path must clear the pk to None after the DB delete, using the model's actual pk attribute name (custom/renamed pks), while preserving count/return semantics and all other deletion behaviors. It names Collector.delete / Collector.can_fast_delete and django.db.models.deletion — legitimate localization already public in the problem_statement (which cites deletion.py:276-281 and can_fast_delete's fast path). No test file paths, no test function/class names, no parametrization ids, no quoted test or gold code, no fix-invented identifiers (`_meta.pk.attname` is Django API, and the requirement phrases it as 'actual primary-key attribute name', not the literal), and no test-shaped case enumeration (only one FAIL_TO_PASS test exists). Req 1.3's mention of renamed/custom pks is a behavioral generalization of using attname, not something the test exercises, so it is spec-side reasoning rather than test reconstruction. Req 1.4 (reset after DB delete) describes semantics, not the patch's literal placement in a way a reader couldn't infer from the stated goal. No semantic leakage.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
