# P2 adversarial audit — django__django-11141

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
# Positive control — Requirement 1.2 / 1.1 / 2.1:
# A namespace-package migrations dir (no __init__.py) containing a migration
# file SHALL be classified migrated and its migration recorded in disk_migrations.
import os, sys, tempfile, textwrap

work = tempfile.mkdtemp(prefix="nsprobe_")
sys.path.insert(0, work)

# App package (ordinary) so it can be an installed app / import target.
app = os.path.join(work, "nsapp")
os.makedirs(app)
open(os.path.join(app, "__init__.py"), "w").close()

# migrations dir WITHOUT __init__.py  => implicit namespace package
mig = os.path.join(app, "migrations")
os.makedirs(mig)
with open(os.path.join(mig, "0001_initial.py"), "w") as f:
    f.write(textwrap.dedent("""
        from django.db import migrations, models
        class Migration(migrations.Migration):
            initial = True
            dependencies = []
            operations = [migrations.CreateModel(
                name='Author',
                fields=[('id', models.AutoField(primary_key=True)),
                        ('name', models.CharField(max_length=100))])]
    """))

import django
from django.conf import settings
settings.configure(
    DEBUG=True,
    INSTALLED_APPS=['nsapp'],
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
)
django.setup()

from django.db.migrations.loader import MigrationLoader
loader = MigrationLoader(connection=None, load=False)
loader.load_disk()

print("migrated_apps:", loader.migrated_apps)
print("unmigrated_apps:", loader.unmigrated_apps)
recorded = sorted(k for k in loader.disk_migrations if k[0] == 'nsapp')
print("nsapp disk_migrations:", recorded)

ok = ('nsapp' in loader.migrated_apps
      and 'nsapp' not in loader.unmigrated_apps
      and ('nsapp', '0001_initial') in loader.disk_migrations)
print("RESULT", "PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
# Requirement 2.2 / 2.3: an imported migrations module that exposes a search
# path but has NO migration file, with ignore_no_migrations disabled, SHALL be
# classified unmigrated and SHALL record no migrations.
import os, sys, tempfile
work = tempfile.mkdtemp(prefix="nsprobe2_"); sys.path.insert(0, work)
app = os.path.join(work, "emptyns"); os.makedirs(app)
open(os.path.join(app, "__init__.py"), "w").close()
os.makedirs(os.path.join(app, "migrations"))   # namespace pkg, no migration files
import django
from django.conf import settings
settings.configure(DEBUG=True, INSTALLED_APPS=['emptyns'],
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}})
django.setup()
from django.db.migrations.loader import MigrationLoader
loader = MigrationLoader(connection=None, load=False)
loader.ignore_no_migrations = False
loader.load_disk()
print("migrated:", 'emptyns' in loader.migrated_apps,
      "unmigrated:", 'emptyns' in loader.unmigrated_apps)
recs = [k for k in loader.disk_migrations if k[0]=='emptyns']
print("records:", recs)
ok = ('emptyns' in loader.unmigrated_apps
      and 'emptyns' not in loader.migrated_apps
      and not recs)
print("RESULT", "PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
# Requirement 2.2: an imported migrations module with a search path but no
# migration file SHALL be classified MIGRATED when ignore_no_migrations is enabled.
import os, sys, tempfile
work = tempfile.mkdtemp(prefix="nsprobe3_"); sys.path.insert(0, work)
app = os.path.join(work, "emptyns2"); os.makedirs(app)
open(os.path.join(app, "__init__.py"), "w").close()
os.makedirs(os.path.join(app, "migrations"))   # namespace pkg, no files
import django
from django.conf import settings
settings.configure(DEBUG=True, INSTALLED_APPS=['emptyns2'],
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}})
django.setup()
from django.db.migrations.loader import MigrationLoader
loader = MigrationLoader(connection=None, load=False)
loader.ignore_no_migrations = True
loader.load_disk()
print("migrated:", 'emptyns2' in loader.migrated_apps,
      "unmigrated:", 'emptyns2' in loader.unmigrated_apps)
ok = ('emptyns2' in loader.migrated_apps and 'emptyns2' not in loader.unmigrated_apps)
print("RESULT", "PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
# Requirement 3.1: when the imported migrations object is NOT a package (no
# __path__, e.g. a single migrations.py module) the app SHALL be unmigrated and
# no migrations recorded. Regression: removing the __file__ check must not
# reclassify plain modules.
import os, sys, tempfile
work = tempfile.mkdtemp(prefix="nsprobe4_"); sys.path.insert(0, work)
app = os.path.join(work, "modapp"); os.makedirs(app)
open(os.path.join(app, "__init__.py"), "w").close()
# migrations is a MODULE file, not a package
with open(os.path.join(app, "migrations.py"), "w") as f:
    f.write("# a plain module, not a package\n")
import django
from django.conf import settings
settings.configure(DEBUG=True, INSTALLED_APPS=['modapp'],
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}})
django.setup()
from django.db.migrations.loader import MigrationLoader
loader = MigrationLoader(connection=None, load=False)
loader.load_disk()
print("migrated:", 'modapp' in loader.migrated_apps,
      "unmigrated:", 'modapp' in loader.unmigrated_apps)
recs = [k for k in loader.disk_migrations if k[0]=='modapp']
print("records:", recs)
ok = ('modapp' in loader.unmigrated_apps and 'modapp' not in loader.migrated_apps and not recs)
print("RESULT", "PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
# Requirement 2.4 / 3.4: discovered migrations = entries on the search path
# that are not subpackages and whose names don't start with _ ~ . ; the __file__
# marker is irrelevant. Use an ordinary (__init__.py) migrations pkg to isolate
# the filtering rule.
import os, sys, tempfile, textwrap
work = tempfile.mkdtemp(prefix="nsprobe5_"); sys.path.insert(0, work)
app = os.path.join(work, "filtapp"); os.makedirs(app)
open(os.path.join(app, "__init__.py"), "w").close()
mig = os.path.join(app, "migrations"); os.makedirs(mig)
open(os.path.join(mig, "__init__.py"), "w").close()
def m(name):
    with open(os.path.join(mig, name), "w") as f:
        f.write(textwrap.dedent("""
            from django.db import migrations
            class Migration(migrations.Migration):
                dependencies = []
                operations = []
        """))
m("0001_initial.py")     # should be discovered
m("_private.py")         # excluded: leading underscore
m("~backup.py")          # excluded: leading tilde
m(".hidden.py")          # excluded: leading dot
os.makedirs(os.path.join(mig, "subpkg"))                   # subpackage -> excluded
open(os.path.join(mig, "subpkg", "__init__.py"), "w").close()
import django
from django.conf import settings
settings.configure(DEBUG=True, INSTALLED_APPS=['filtapp'],
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}})
django.setup()
from django.db.migrations.loader import MigrationLoader
loader = MigrationLoader(connection=None, load=False)
loader.load_disk()
names = sorted(n for a,n in loader.disk_migrations if a=='filtapp')
print("discovered:", names)
ok = (names == ['0001_initial'])
print("RESULT", "PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
# Requirement 1.3: namespace-packaged migrations appear as graph nodes and their
# forward plan matches the same migrations in an ordinary package.
import os, sys, tempfile, textwrap
work = tempfile.mkdtemp(prefix="nsprobe6_"); sys.path.insert(0, work)
def build(appname, as_namespace):
    app = os.path.join(work, appname); os.makedirs(app)
    open(os.path.join(app, "__init__.py"), "w").close()
    mig = os.path.join(app, "migrations"); os.makedirs(mig)
    if not as_namespace:
        open(os.path.join(mig, "__init__.py"), "w").close()
    def w(name, deps):
        with open(os.path.join(mig, name+".py"), "w") as f:
            f.write("from django.db import migrations, models\n"
                    "class Migration(migrations.Migration):\n"
                    "    dependencies = %r\n"
                    "    operations = [migrations.CreateModel('M%s',[('id',models.AutoField(primary_key=True))])]\n"
                    % (deps, name[-1]))
    w("0001_initial", [])
    w("0002_more", [(appname, "0001_initial")])
build("nsg", True)     # namespace package
build("okg", False)    # ordinary package
import django
from django.conf import settings
settings.configure(DEBUG=True, INSTALLED_APPS=['nsg','okg'],
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}})
django.setup()
from django.db.migrations.loader import MigrationLoader
loader = MigrationLoader(connection=None, load=False)
loader.load_disk()
loader.build_graph()
ns_nodes = sorted(k for k in loader.graph.nodes if k[0]=='nsg')
ok_nodes = sorted(k for k in loader.graph.nodes if k[0]=='okg')
ns_plan = [n for n in loader.graph.forwards_plan(('nsg','0002_more'))]
ok_plan = [n for n in loader.graph.forwards_plan(('okg','0002_more'))]
print("ns_nodes:", ns_nodes)
print("ns_plan:", ns_plan)
print("ok_plan:", ok_plan)
ok = (ns_nodes == [('nsg','0001_initial'),('nsg','0002_more')]
      and [x[1] for x in ns_plan] == [x[1] for x in ok_plan]
      and [x[1] for x in ns_plan] == ['0001_initial','0002_more'])
print("RESULT", "PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)
```

Attack 7 — `probe_7.py` → holds on the patched tree (good)

```python
# Requirement 3.2: if the app has no migrations module configured (module name
# resolves to nothing, via MIGRATION_MODULES={app: None}) it SHALL be unmigrated.
import os, sys, tempfile, textwrap
work = tempfile.mkdtemp(prefix="nsprobe7_"); sys.path.insert(0, work)
app = os.path.join(work, "noneapp"); os.makedirs(app)
open(os.path.join(app, "__init__.py"), "w").close()
mig = os.path.join(app, "migrations"); os.makedirs(mig)
open(os.path.join(mig, "__init__.py"), "w").close()
with open(os.path.join(mig, "0001_initial.py"), "w") as f:
    f.write("from django.db import migrations\n"
            "class Migration(migrations.Migration):\n"
            "    dependencies = []\n    operations = []\n")
import django
from django.conf import settings
settings.configure(DEBUG=True, INSTALLED_APPS=['noneapp'],
    MIGRATION_MODULES={'noneapp': None},
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}})
django.setup()
from django.db.migrations.loader import MigrationLoader
loader = MigrationLoader(connection=None, load=False)
loader.load_disk()
print("migrated:", 'noneapp' in loader.migrated_apps,
      "unmigrated:", 'noneapp' in loader.unmigrated_apps)
recs = [k for k in loader.disk_migrations if k[0]=='noneapp']
print("records:", recs)
ok = ('noneapp' in loader.unmigrated_apps and 'noneapp' not in loader.migrated_apps and not recs)
print("RESULT", "PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
# Positive control — Requirement 1.2 / 1.1 / 2.1:
# A namespace-package migrations dir (no __init__.py) containing a migration
# file SHALL be classified migrated and its migration recorded in disk_migrations.
import os, sys, tempfile, textwrap

work = tempfile.mkdtemp(prefix="nsprobe_")
sys.path.insert(0, work)

# App package (ordinary) so it can be an installed app / import target.
app = os.path.join(work, "nsapp")
os.makedirs(app)
open(os.path.join(app, "__init__.py"), "w").close()

# migrations dir WITHOUT __init__.py  => implicit namespace package
mig = os.path.join(app, "migrations")
os.makedirs(mig)
with open(os.path.join(mig, "0001_initial.py"), "w") as f:
    f.write(textwrap.dedent("""
        from django.db import migrations, models
        class Migration(migrations.Migration):
            initial = True
            dependencies = []
            operations = [migrations.CreateModel(
                name='Author',
                fields=[('id', models.AutoField(primary_key=True)),
                        ('name', models.CharField(max_length=100))])]
    """))

import django
from django.conf import settings
settings.configure(
    DEBUG=True,
    INSTALLED_APPS=['nsapp'],
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
)
django.setup()

from django.db.migrations.loader import MigrationLoader
loader = MigrationLoader(connection=None, load=False)
loader.load_disk()

print("migrated_apps:", loader.migrated_apps)
print("unmigrated_apps:", loader.unmigrated_apps)
recorded = sorted(k for k in loader.disk_migrations if k[0] == 'nsapp')
print("nsapp disk_migrations:", recorded)

ok = ('nsapp' in loader.migrated_apps
      and 'nsapp' not in loader.unmigrated_apps
      and ('nsapp', '0001_initial') in loader.disk_migrations)
print("RESULT", "PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance loads migrations from packages without __init__.py (namespace packages). PY3.6.13/Django3.1, /testbed. Structural check: base HAS_FILE_CHECK=True/HAS_GATE=False; patched HAS_FILE_CHECK=False/HAS_GATE=True.

Probes (all run in the official image; all HOLD on the gold-patched tree):
- probe_1 (Req 1.1/1.2/2.1, POSITIVE CONTROL): namespace-pkg migrations dir with 0001_initial.py -> app classified migrated and ('nsapp','0001_initial') recorded in disk_migrations. PATCHED: PASS (migrated={'nsapp'}, records present). BASE: FAIL (unmigrated={'nsapp'}, no records) => discriminates, prepatch reproduced.
- probe_2 (Req 2.2/2.3): empty namespace migrations pkg, ignore_no_migrations=False -> unmigrated, no records. PATCHED PASS.
- probe_3 (Req 2.2): empty namespace migrations pkg, ignore_no_migrations=True -> migrated. PATCHED PASS.
- probe_4 (Req 3.1): migrations.py plain module (no __path__) -> unmigrated, no records. PATCHED PASS (regression: __file__ removal doesn't reclassify plain modules).
- probe_5 (Req 2.4/3.4): file filtering — only 0001_initial discovered; _private, ~backup, .hidden, and a subpackage all excluded. PATCHED PASS.
- probe_6 (Req 1.3): namespace-pkg migrations appear as graph nodes and forwards_plan identical to an ordinary-package equivalent. PATCHED PASS.
- probe_7 (Req 3.2): MIGRATION_MODULES={app: None} -> unmigrated, no records even though a real migration file exists. PATCHED PASS.

Candidate wrong-fix (weak.diff): removes ONLY the obsolete __file__ check but keeps the pre-patch unconditional `self.migrated_apps.add(label)` (i.e. omits the new `if migration_names or ignore_no_migrations` gate). This is the lazy reading of Req 1 that ignores Req 2.2/2.3. Under weak.diff: probe_1 still HOLDS (namespace migrations load) but probe_2 is REJECTED (empty namespace pkg wrongly classified migrated with ignore_no_migrations=False). This demonstrates the suite discriminates the plausible partial fix; it is NOT a too-weak finding.

Note on meta.json: recorded G-PANEL-2 fail asserts an empty ORDINARY package (has __file__) becomes unmigrated under the patch where pre-patch it was migrated — that is the same Req-2.2/2.3 behavior probe_2 encodes and is faithful to the gold diff (the new gate applies to all packages, ordinary or namespace). No spec-fidelity VIOLATION found and no probe-conforming alternative escapes the suite.

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
# Positive control — Requirement 1.2 / 1.1 / 2.1:
# A namespace-package migrations dir (no __init__.py) containing a migration
# file SHALL be classified migrated and its migration recorded in disk_migrations.
import os, sys, tempfile, textwrap

work = tempfile.mkdtemp(prefix="nsprobe_")
sys.path.insert(0, work)

# App package (ordinary) so it can be an installed app / import target.
app = os.path.join(work, "nsapp")
os.makedirs(app)
open(os.path.join(app, "__init__.py"), "w").close()

# migrations dir WITHOUT __init__.py  => implicit namespace package
mig = os.path.join(app, "migrations")
os.makedirs(mig)
with open(os.path.join(mig, "0001_initial.py"), "w") as f:
    f.write(textwrap.dedent("""
        from django.db import migrations, models
        class Migration(migrations.Migration):
            initial = True
            dependencies = []
            operations = [migrations.CreateModel(
                name='Author',
                fields=[('id', models.AutoField(primary_key=True)),
                        ('name', models.CharField(max_length=100))])]
    """))

import django
from django.conf import settings
settings.configure(
    DEBUG=True,
    INSTALLED_APPS=['nsapp'],
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
)
django.setup()

from django.db.migrations.loader import MigrationLoader
loader = MigrationLoader(connection=None, load=False)
loader.load_disk()

print("migrated_apps:", loader.migrated_apps)
print("unmigrated_apps:", loader.unmigrated_apps)
recorded = sorted(k for k in loader.disk_migrations if k[0] == 'nsapp')
print("nsapp disk_migrations:", recorded)

ok = ('nsapp' in loader.migrated_apps
      and 'nsapp' not in loader.unmigrated_apps
      and ('nsapp', '0001_initial') in loader.disk_migrations)
print("RESULT", "PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance loads migrations from packages without __init__.py (namespace packages). PY3.6.13/Django3.1, /testbed. Structural check: base HAS_FILE_CHECK=True/HAS_GATE=False; patched HAS_FILE_CHECK=False/HAS_GATE=True.

Probes (all run in the official image; all HOLD on the gold-patched tree):
- probe_1 (Req 1.1/1.2/2.1, POSITIVE CONTROL): namespace-pkg migrations dir with 0001_initial.py -> app classified migrated and ('nsapp','0001_initial') recorded in disk_migrations. PATCHED: PASS (migrated={'nsapp'}, records present). BASE: FAIL (unmigrated={'nsapp'}, no records) => discriminates, prepatch reproduced.
- probe_2 (Req 2.2/2.3): empty namespace migrations pkg, ignore_no_migrations=False -> unmigrated, no records. PATCHED PASS.
- probe_3 (Req 2.2): empty namespace migrations pkg, ignore_no_migrations=True -> migrated. PATCHED PASS.
- probe_4 (Req 3.1): migrations.py plain module (no __path__) -> unmigrated, no records. PATCHED PASS (regression: __file__ removal doesn't reclassify plain modules).
- probe_5 (Req 2.4/3.4): file filtering — only 0001_initial discovered; _private, ~backup, .hidden, and a subpackage all excluded. PATCHED PASS.
- probe_6 (Req 1.3): namespace-pkg migrations appear as graph nodes and forwards_plan identical to an ordinary-package equivalent. PATCHED PASS.
- probe_7 (Req 3.2): MIGRATION_MODULES={app: None} -> unmigrated, no records even though a real migration file exists. PATCHED PASS.

Candidate wrong-fix (weak.diff): removes ONLY the obsolete __file__ check but keeps the pre-patch unconditional `self.migrated_apps.add(label)` (i.e. omits the new `if migration_names or ignore_no_migrations` gate). This is the lazy reading of Req 1 that ignores Req 2.2/2.3. Under weak.diff: probe_1 still HOLDS (namespace migrations load) but probe_2 is REJECTED (empty namespace pkg wrongly classified migrated with ignore_no_migrations=False). This demonstrates the suite discriminates the plausible partial fix; it is NOT a too-weak finding.

Note on meta.json: recorded G-PANEL-2 fail asserts an empty ORDINARY package (has __file__) becomes unmigrated under the patch where pre-patch it was migrated — that is the same Req-2.2/2.3 behavior probe_2 encodes and is faithful to the gold diff (the new gate applies to all packages, ordinary or namespace). No spec-fidelity VIOLATION found and no probe-conforming alternative escapes the suite.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Requirements pin the changed OBSERVABLE behavior (count-based migrated/unmigrated classification), not merely the narrow `__file__`-removal slice — correct modeling boundary. Note the instance image's real upstream code keeps a refined `__file__ is None and not isinstance(__path__, list)` guard, but the bundle's patch.diff (what is being audited) removes the check entirely; requirements are faithful to the bundle patch. No mandated-absent, forbidden-present, or invented behavior.

Counterexample / evidence:

```
No divergence. Base-vs-patched probe confirms the `__file__` check exists only at base_commit; patched source contains no `__file__` and contains `if migration_names or self.ignore_no_migrations:`. iter_modules probe confirmed dotfile/underscore/tilde exclusion behavior.
```


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The requirements only translate the gold edit into behavioral prose. Everything load-bearing (implicit namespace packages have no __file__ but expose __path__; discovery uses pkgutil.iter_modules over __path__; the __file__ check is obsolete and blocks migrate) is already public in the problem_statement. Naming django/db/migrations/loader.py and MigrationLoader.load_disk is legitimate localization, not derived from hidden tests. The migrated/unmigrated-by-discovered-migrations reclassification and the ignore_no_migrations branch (Req 2) describe the gold patch's behavior — not the tests; ignore_no_migrations is a pre-existing identifier, not fix-invented. Req 1.3's 'forward plan'/'graph nodes' language is a general behavioral description, not the test's specific forwards_plan(('migrations','0001_initial'))==[...] assertion; the migration id, the test function name (test_loading_namespace_package), and the test dir (test_migrations_namespace_package) are nowhere quoted or reconstructed. The '_', '~', '.' filtering enumeration reflects the code branch/existing PASS_TO_PASS behavior, not a case parametrization. No test paths/names/ids, no quoted test or gold source lines, no fix-invented identifiers.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
