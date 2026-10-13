# P2 adversarial audit — django__django-13820

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
"""Positive control + Req 1.1/1.2: an ordinary package whose __path__ is a
plain list but which lacks __file__ (frozen-env simulation) SHALL be treated as
a migrated app and ALL its migration modules discovered.
Exit 0 iff both migrations are discovered. HOLDS patched, FAILS at base."""
import os, sys, tempfile

work = tempfile.mkdtemp()
app = os.path.join(work, "frozenapp")
mig = os.path.join(app, "migrations")
os.makedirs(mig)
open(os.path.join(app, "__init__.py"), "w").close()
open(os.path.join(mig, "__init__.py"), "w").close()
for n in ("0001_initial", "0002_second"):
    with open(os.path.join(mig, n + ".py"), "w") as f:
        f.write("from django.db import migrations\n"
                "class Migration(migrations.Migration):\n"
                "    dependencies = []\n    operations = []\n")
sys.path.insert(0, work)

import django
from django.conf import settings
settings.configure(
    INSTALLED_APPS=["frozenapp"],
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
)
django.setup()

from importlib import import_module
m = import_module("frozenapp.migrations")
assert isinstance(m.__path__, list), "precondition: __path__ must be a plain list"
# Simulate a frozen environment: no __file__ on a regular package.
if hasattr(m, "__file__"):
    del m.__file__
try:
    m.__spec__.origin = None
    m.__spec__.has_location = False
except Exception:
    pass

from django.db.migrations.loader import MigrationLoader
loader = MigrationLoader(None, load=False)
loader.load_disk()
migs = sorted(n for a, n in loader.disk_migrations if a == "frozenapp")
migrated = "frozenapp" in loader.migrated_apps
print("has __file__:", hasattr(m, "__file__"), "| __path__ is list:", isinstance(m.__path__, list))
print("migrated_apps has frozenapp:", migrated, "| discovered:", migs)
ok = migrated and migs == ["0001_initial", "0002_second"]
print("RESULT", "HOLD" if ok else "VIOLATED")
sys.exit(0 if ok else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""Req 2.1/2.2/2.3: a genuine PEP 420 namespace package (no __init__.py, so no
__file__ and __path__ is a custom non-list iterable) SHALL be treated as an
UNMIGRATED app and NOT scanned, exactly as before. Even if it physically
contains migration-looking files, none may be discovered.
Exit 0 iff frozenapp is unmigrated and no migrations discovered."""
import os, sys, tempfile

work = tempfile.mkdtemp()
app = os.path.join(work, "nsapp")
mig = os.path.join(app, "migrations")
os.makedirs(mig)
open(os.path.join(app, "__init__.py"), "w").close()
# NO __init__.py in migrations -> implicit namespace package.
with open(os.path.join(mig, "0001_initial.py"), "w") as f:
    f.write("from django.db import migrations\n"
            "class Migration(migrations.Migration):\n"
            "    dependencies = []\n    operations = []\n")
sys.path.insert(0, work)

import django
from django.conf import settings
settings.configure(
    INSTALLED_APPS=["nsapp"],
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
)
django.setup()

from importlib import import_module
m = import_module("nsapp.migrations")
print("has __file__:", getattr(m, "__file__", None), "| __path__ is list:", isinstance(m.__path__, list))
assert not isinstance(m.__path__, list), "precondition: namespace __path__ must NOT be a plain list"

from django.db.migrations.loader import MigrationLoader
loader = MigrationLoader(None, load=False)
loader.load_disk()
migs = sorted(n for a, n in loader.disk_migrations if a == "nsapp")
unmigrated = "nsapp" in loader.unmigrated_apps
migrated = "nsapp" in loader.migrated_apps
print("unmigrated:", unmigrated, "| migrated:", migrated, "| discovered:", migs)
ok = unmigrated and not migrated and migs == []
print("RESULT", "HOLD" if ok else "VIOLATED")
sys.exit(0 if ok else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""Req 3.1/3.2: a migrations module that is NOT a package (a single-file
migrations.py, no __path__) SHALL be treated as unmigrated and NOT scanned.
Exit 0 iff the app is unmigrated and nothing discovered."""
import os, sys, tempfile

work = tempfile.mkdtemp()
app = os.path.join(work, "flatapp")
os.makedirs(app)
open(os.path.join(app, "__init__.py"), "w").close()
# migrations is a plain module file, not a package.
with open(os.path.join(app, "migrations.py"), "w") as f:
    f.write("# not a package\n")
sys.path.insert(0, work)

import django
from django.conf import settings
settings.configure(
    INSTALLED_APPS=["flatapp"],
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
)
django.setup()

from importlib import import_module
m = import_module("flatapp.migrations")
print("has __path__:", hasattr(m, "__path__"))
assert not hasattr(m, "__path__"), "precondition: module must not be a package"

from django.db.migrations.loader import MigrationLoader
loader = MigrationLoader(None, load=False)
loader.load_disk()
migs = [n for a, n in loader.disk_migrations if a == "flatapp"]
unmigrated = "flatapp" in loader.unmigrated_apps
print("unmigrated:", unmigrated, "| discovered:", migs)
ok = unmigrated and "flatapp" not in loader.migrated_apps and migs == []
print("RESULT", "HOLD" if ok else "VIOLATED")
sys.exit(0 if ok else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""Req 4.1/4.2: an ordinary package WITH __file__ is migrated and scanned; and
discovery excludes sub-packages and modules beginning with underscore/tilde/dot.
Exit 0 iff exactly the two real migrations are found (the _private module, the
~temp module, and the subpkg sub-package are all excluded)."""
import os, sys, tempfile

work = tempfile.mkdtemp()
app = os.path.join(work, "normalapp")
mig = os.path.join(app, "migrations")
os.makedirs(mig)
open(os.path.join(app, "__init__.py"), "w").close()
open(os.path.join(mig, "__init__.py"), "w").close()
for n in ("0001_initial", "0002_second"):
    with open(os.path.join(mig, n + ".py"), "w") as f:
        f.write("from django.db import migrations\n"
                "class Migration(migrations.Migration):\n"
                "    dependencies = []\n    operations = []\n")
# excluded: leading underscore, and a sub-package
open(os.path.join(mig, "_private.py"), "w").close()
sub = os.path.join(mig, "subpkg")
os.makedirs(sub)
open(os.path.join(sub, "__init__.py"), "w").close()
sys.path.insert(0, work)

import django
from django.conf import settings
settings.configure(
    INSTALLED_APPS=["normalapp"],
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
)
django.setup()

from importlib import import_module
m = import_module("normalapp.migrations")
print("has __file__:", hasattr(m, "__file__"), "| __path__ is list:", isinstance(m.__path__, list))

from django.db.migrations.loader import MigrationLoader
loader = MigrationLoader(None, load=False)
loader.load_disk()
migs = sorted(n for a, n in loader.disk_migrations if a == "normalapp")
migrated = "normalapp" in loader.migrated_apps
print("migrated:", migrated, "| discovered:", migs)
ok = migrated and migs == ["0001_initial", "0002_second"]
print("RESULT", "HOLD" if ok else "VIOLATED")
sys.exit(0 if ok else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""Req 4.3: a migrations directory that contains NO __init__ module (so import
yields a namespace package) and no migration files SHALL be treated as
unmigrated. Also exercises Req 1.3/3.3 default-to-None-not-error path.
Exit 0 iff the app is unmigrated and nothing discovered / no error raised."""
import os, sys, tempfile

work = tempfile.mkdtemp()
app = os.path.join(work, "emptyapp")
mig = os.path.join(app, "migrations")
os.makedirs(mig)
open(os.path.join(app, "__init__.py"), "w").close()
# no __init__.py, no migration files -> empty namespace dir
sys.path.insert(0, work)

import django
from django.conf import settings
settings.configure(
    INSTALLED_APPS=["emptyapp"],
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
)
django.setup()

from importlib import import_module
m = import_module("emptyapp.migrations")
print("has __file__:", getattr(m, "__file__", None), "| __path__ is list:", isinstance(m.__path__, list))

from django.db.migrations.loader import MigrationLoader
loader = MigrationLoader(None, load=False)
loader.load_disk()  # must not raise
migs = [n for a, n in loader.disk_migrations if a == "emptyapp"]
unmigrated = "emptyapp" in loader.unmigrated_apps
print("unmigrated:", unmigrated, "| discovered:", migs)
ok = unmigrated and "emptyapp" not in loader.migrated_apps and migs == []
print("RESULT", "HOLD" if ok else "VIOLATED")
sys.exit(0 if ok else 1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
"""Req 3.3: when an app has NO migrations submodule at all, load_disk SHALL
treat it as unmigrated rather than propagating the ModuleNotFoundError.
Exit 0 iff no exception is raised and the app is unmigrated."""
import os, sys, tempfile

work = tempfile.mkdtemp()
app = os.path.join(work, "nomigapp")
os.makedirs(app)
open(os.path.join(app, "__init__.py"), "w").close()
# no migrations module whatsoever
sys.path.insert(0, work)

import django
from django.conf import settings
settings.configure(
    INSTALLED_APPS=["nomigapp"],
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
)
django.setup()

from django.db.migrations.loader import MigrationLoader
loader = MigrationLoader(None, load=False)
try:
    loader.load_disk()
except Exception as e:
    print("UNEXPECTED EXCEPTION:", type(e).__name__, e)
    sys.exit(1)
unmigrated = "nomigapp" in loader.unmigrated_apps
migs = [n for a, n in loader.disk_migrations if a == "nomigapp"]
print("unmigrated:", unmigrated, "| discovered:", migs)
ok = unmigrated and "nomigapp" not in loader.migrated_apps and migs == []
print("RESULT", "HOLD" if ok else "VIOLATED")
sys.exit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Positive control + Req 1.1/1.2: an ordinary package whose __path__ is a
plain list but which lacks __file__ (frozen-env simulation) SHALL be treated as
a migrated app and ALL its migration modules discovered.
Exit 0 iff both migrations are discovered. HOLDS patched, FAILS at base."""
import os, sys, tempfile

work = tempfile.mkdtemp()
app = os.path.join(work, "frozenapp")
mig = os.path.join(app, "migrations")
os.makedirs(mig)
open(os.path.join(app, "__init__.py"), "w").close()
open(os.path.join(mig, "__init__.py"), "w").close()
for n in ("0001_initial", "0002_second"):
    with open(os.path.join(mig, n + ".py"), "w") as f:
        f.write("from django.db import migrations\n"
                "class Migration(migrations.Migration):\n"
                "    dependencies = []\n    operations = []\n")
sys.path.insert(0, work)

import django
from django.conf import settings
settings.configure(
    INSTALLED_APPS=["frozenapp"],
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
)
django.setup()

from importlib import import_module
m = import_module("frozenapp.migrations")
assert isinstance(m.__path__, list), "precondition: __path__ must be a plain list"
# Simulate a frozen environment: no __file__ on a regular package.
if hasattr(m, "__file__"):
    del m.__file__
try:
    m.__spec__.origin = None
    m.__spec__.has_location = False
except Exception:
    pass

from django.db.migrations.loader import MigrationLoader
loader = MigrationLoader(None, load=False)
loader.load_disk()
migs = sorted(n for a, n in loader.disk_migrations if a == "frozenapp")
migrated = "frozenapp" in loader.migrated_apps
print("has __file__:", hasattr(m, "__file__"), "| __path__ is list:", isinstance(m.__path__, list))
print("migrated_apps has frozenapp:", migrated, "| discovered:", migs)
ok = migrated and migs == ["0001_initial", "0002_second"]
print("RESULT", "HOLD" if ok else "VIOLATED")
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance: fix in django/db/migrations/loader.py MigrationLoader.load_disk. Old rule rejected any module with __file__ absent/None; new rule only rejects when BOTH __file__ is None AND __path__ is NOT a plain list (namespace test), and orders the not-a-package check first.

Probe results (all on the instance's official Docker image via nl_attack):
- probe_1 POSITIVE CONTROL (Req 1.1/1.2): ordinary package whose __path__ is a plain list but __file__ deleted (frozen-env sim). HOLDS gold-patched (migrated, both migrations discovered); VIOLATED at base (unmigrated, discovered []). Discriminating power confirmed.
- probe_2 (Req 2.1/2.2/2.3): genuine PEP 420 namespace pkg (no __init__, custom non-list __path__) containing a migration file. HOLDS gold-patched (unmigrated, none discovered).
- probe_3 (Req 3.1/3.2): single-file migrations.py (no __path__). HOLDS gold-patched (unmigrated).
- probe_4 (Req 4.1/4.2): ordinary pkg WITH __file__, plus a _underscore module and a sub-package present. HOLDS gold-patched (migrated; exactly 0001_initial+0002_second, exclusions honored).
- probe_5 (Req 4.3): empty migrations dir, no __init__/files -> namespace. HOLDS gold-patched (unmigrated).
- probe_6 (Req 3.3): app with NO migrations submodule at all. HOLDS gold-patched (unmigrated, no exception propagated).

Wrong-fix candidate weak.diff = the naive over-broad fix that DELETES the __file__/None check entirely (treats every package, incl. namespace packages, as migrated). It satisfies Req 1 (probe_1,4 HOLD) but is REJECTED by probe_2 (Req 2: namespace pkg wrongly scanned -> migrated, 0001_initial discovered) and probe_5 (Req 4.3: empty namespace dir wrongly marked migrated). Thus the probe suite discriminates the requirements-incomplete wrong reading; it does not admit a wrong fix.

Verdict SOUND: >=5 distinct probes all hold on the patched tree, positive control fails at base and holds patched, and the constructed plausible wrong fix is rejected by the suite (so no TOO-WEAK finding). No requirements VIOLATION found.

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
"""Positive control + Req 1.1/1.2: an ordinary package whose __path__ is a
plain list but which lacks __file__ (frozen-env simulation) SHALL be treated as
a migrated app and ALL its migration modules discovered.
Exit 0 iff both migrations are discovered. HOLDS patched, FAILS at base."""
import os, sys, tempfile

work = tempfile.mkdtemp()
app = os.path.join(work, "frozenapp")
mig = os.path.join(app, "migrations")
os.makedirs(mig)
open(os.path.join(app, "__init__.py"), "w").close()
open(os.path.join(mig, "__init__.py"), "w").close()
for n in ("0001_initial", "0002_second"):
    with open(os.path.join(mig, n + ".py"), "w") as f:
        f.write("from django.db import migrations\n"
                "class Migration(migrations.Migration):\n"
                "    dependencies = []\n    operations = []\n")
sys.path.insert(0, work)

import django
from django.conf import settings
settings.configure(
    INSTALLED_APPS=["frozenapp"],
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
)
django.setup()

from importlib import import_module
m = import_module("frozenapp.migrations")
assert isinstance(m.__path__, list), "precondition: __path__ must be a plain list"
# Simulate a frozen environment: no __file__ on a regular package.
if hasattr(m, "__file__"):
    del m.__file__
try:
    m.__spec__.origin = None
    m.__spec__.has_location = False
except Exception:
    pass

from django.db.migrations.loader import MigrationLoader
loader = MigrationLoader(None, load=False)
loader.load_disk()
migs = sorted(n for a, n in loader.disk_migrations if a == "frozenapp")
migrated = "frozenapp" in loader.migrated_apps
print("has __file__:", hasattr(m, "__file__"), "| __path__ is list:", isinstance(m.__path__, list))
print("migrated_apps has frozenapp:", migrated, "| discovered:", migs)
ok = migrated and migs == ["0001_initial", "0002_second"]
print("RESULT", "HOLD" if ok else "VIOLATED")
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance: fix in django/db/migrations/loader.py MigrationLoader.load_disk. Old rule rejected any module with __file__ absent/None; new rule only rejects when BOTH __file__ is None AND __path__ is NOT a plain list (namespace test), and orders the not-a-package check first.

Probe results (all on the instance's official Docker image via nl_attack):
- probe_1 POSITIVE CONTROL (Req 1.1/1.2): ordinary package whose __path__ is a plain list but __file__ deleted (frozen-env sim). HOLDS gold-patched (migrated, both migrations discovered); VIOLATED at base (unmigrated, discovered []). Discriminating power confirmed.
- probe_2 (Req 2.1/2.2/2.3): genuine PEP 420 namespace pkg (no __init__, custom non-list __path__) containing a migration file. HOLDS gold-patched (unmigrated, none discovered).
- probe_3 (Req 3.1/3.2): single-file migrations.py (no __path__). HOLDS gold-patched (unmigrated).
- probe_4 (Req 4.1/4.2): ordinary pkg WITH __file__, plus a _underscore module and a sub-package present. HOLDS gold-patched (migrated; exactly 0001_initial+0002_second, exclusions honored).
- probe_5 (Req 4.3): empty migrations dir, no __init__/files -> namespace. HOLDS gold-patched (unmigrated).
- probe_6 (Req 3.3): app with NO migrations submodule at all. HOLDS gold-patched (unmigrated, no exception propagated).

Wrong-fix candidate weak.diff = the naive over-broad fix that DELETES the __file__/None check entirely (treats every package, incl. namespace packages, as migrated). It satisfies Req 1 (probe_1,4 HOLD) but is REJECTED by probe_2 (Req 2: namespace pkg wrongly scanned -> migrated, 0001_initial discovered) and probe_5 (Req 4.3: empty namespace dir wrongly marked migrated). Thus the probe suite discriminates the requirements-incomplete wrong reading; it does not admit a wrong fix.

Verdict SOUND: >=5 distinct probes all hold on the patched tree, positive control fails at base and holds patched, and the constructed plausible wrong fix is rejected by the suite (so no TOO-WEAK finding). No requirements VIOLATION found.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Patch changes only the namespace test in load_disk from `getattr(module,'__file__',None) is None` to `getattr(module,'__file__',None) is None and not isinstance(module.__path__, list)`, and reorders so the not-a-package (`not hasattr(module,'__path__')`) check runs first. Requirements 1-4 pin exactly this changed observable behavior biconditionally, not a narrow slice. Only nit: Req1.3 says the determination is on a 'truthy' __file__ while the code uses `is None`; these diverge only for an empty-string __file__, which the import system never produces — no realistic diverging input, so not unfaithful. Verified via nl_attack probe on the instance image.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The entire fix mechanism (reject namespace packages via getattr(m,'__file__',None) combined with isinstance(m.__path__, list); the 'ordinary package's __path__ is a list, namespace __path__ is a custom iterable' rationale; frozen-environment motivation; the affected module django/db/migrations/loader.py and method MigrationLoader.load_disk) is all publicly disclosed in the problem_statement. None of the hidden-test-specific artifacts appear in requirements.md: the test function name test_loading_package_without__file__, the MIGRATION_MODULES={'migrations':'migrations.test_migrations'} setting, the __spec__.origin/has_location deletion trick, or the gold-expected migration ids ['0001_initial','0002_second']. Requirement 4.2's underscore/tilde/dot exclusion and sub-package exclusion describe pre-existing general loader behavior, not a mirror of the test parametrization. Module/method naming is legitimate localization. No test code, paths, ids, or fix-invented identifiers transmitted beyond the public statement.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
