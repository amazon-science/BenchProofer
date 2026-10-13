# P2 adversarial audit — django__django-7530

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
"""Requirement 1 (crit 1-5) + positive control:
Every (app_label, model_name) pair passed to router.allow_migrate() during the
makemigrations consistency check must be VALID: model_name must be the
object_name of a model that actually belongs to app_label.

Records all pairs by installing a router that returns False (falsy) so the
`any(...)` generator is fully consumed and every pair is observed. Then checks
each pair with apps.get_app_config(app_label).get_model(model_name), exactly as
the hidden test does.

HOLDS iff no invalid (app_label, model_name) pair is ever passed.
"""
import sys
sys.path.insert(0, '/testbed/tests')

import django
from django.conf import settings

CALLS = []


class RecRouter(object):
    def allow_migrate(self, db, app_label, model_name=None, **hints):
        CALLS.append((db, app_label, model_name))
        return False  # falsy so `any()` consumes the whole generator


settings.configure(
    DEBUG=True,
    DATABASES={
        'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'},
        'other': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'},
    },
    INSTALLED_APPS=['migrations', 'migrations2'],
    DATABASE_ROUTERS=[RecRouter()],
    MIDDLEWARE_CLASSES=[],
)
django.setup()

from django.apps import apps
from django.core.management import call_command

call_command('makemigrations', 'migrations', verbosity=0, dry_run=True)

print("total allow_migrate calls recorded:", len(CALLS))
if not CALLS:
    print("FAIL: no calls recorded (check did not run)")
    sys.exit(1)

bad = []
for alias, app_label, model_name in CALLS:
    try:
        apps.get_app_config(app_label).get_model(model_name)
    except Exception as e:
        bad.append((alias, app_label, model_name, type(e).__name__))

# sample of observed pairs
seen = sorted(set((a, m) for _, a, m in CALLS))
print("distinct (app_label, model_name) pairs:", len(seen))
for a, m in seen:
    print("   pair:", a, m)
print("invalid pairs:", bad)

if bad:
    print("FAIL: invalid (app_label, model_name) pairs passed to allow_migrate")
    sys.exit(1)
print("OK: every pair valid for its application")
sys.exit(0)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""Requirement 1 crit 1,4,5 + Requirement 2 crit 1:
Every installed application is enumerated, and each is paired with EXACTLY its
own models (resolved via its AppConfig) — never another app's models. With
several apps that each own models (contenttypes, auth, migrations), a
project-wide lookup would cross-pair; the correct fix must not.

Router returns False so the whole `any(...)` generator is consumed and every
pair is observed.

HOLDS iff, for every app that appears in the calls, the observed model-name set
equals that app's own models exactly; AND at least 3 distinct model-owning apps
are observed (so the check really covers every app, not just one).
"""
import sys
sys.path.insert(0, '/testbed/tests')

import django
from django.conf import settings

CALLS = []


class RecRouter(object):
    def allow_migrate(self, db, app_label, model_name=None, **hints):
        CALLS.append((db, app_label, model_name))
        return False


settings.configure(
    DEBUG=True,
    DATABASES={
        'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'},
        'other': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'},
    },
    INSTALLED_APPS=[
        'django.contrib.contenttypes',
        'django.contrib.auth',
        'migrations',
    ],
    DATABASE_ROUTERS=[RecRouter()],
    MIDDLEWARE_CLASSES=[],
)
django.setup()

from django.apps import apps
from django.core.management import call_command

call_command('makemigrations', 'migrations', verbosity=0, dry_run=True)

observed = {}
for _, app_label, model_name in CALLS:
    observed.setdefault(app_label, set()).add(model_name)

print("apps observed:", sorted(observed))

expected = {}
for cfg in apps.get_app_configs():
    expected[cfg.label] = set(m._meta.object_name for m in cfg.get_models())

ok = True
for app_label, names in sorted(observed.items()):
    exp = expected.get(app_label, set())
    print("app", app_label, "observed", sorted(names), "== expected", sorted(exp), ":", names == exp)
    if names != exp:
        ok = False

# ensure the check spans multiple model-owning apps (not collapsed to one)
if len(observed) < 3:
    print("FAIL: fewer than 3 apps enumerated:", sorted(observed))
    ok = False

# each of the model-owning installed apps must have been enumerated
for req in ('contenttypes', 'auth', 'migrations'):
    if req not in observed:
        print("FAIL: app not enumerated:", req)
        ok = False

if not ok:
    print("FAIL")
    sys.exit(1)
print("OK: every app paired with exactly its own models; all model-owning apps enumerated")
sys.exit(0)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""Requirement 2 crit 2 & 6: WHEN database routers are configured, the check
evaluates the relevant NON-default connections (not only 'default'), and each
allow_migrate() call receives the alias of the connection being evaluated,
unchanged (only 'default'/'other' ever appear).

Router returns False so all connections/pairs are consumed.

HOLDS iff both 'default' and 'other' aliases appear among the calls, and no
alias other than the configured connection aliases is ever passed.
"""
import sys
sys.path.insert(0, '/testbed/tests')

import django
from django.conf import settings

CALLS = []


class RecRouter(object):
    def allow_migrate(self, db, app_label, model_name=None, **hints):
        CALLS.append((db, app_label, model_name))
        return False


settings.configure(
    DEBUG=True,
    DATABASES={
        'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'},
        'other': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'},
    },
    INSTALLED_APPS=['migrations', 'migrations2'],
    DATABASE_ROUTERS=[RecRouter()],
    MIDDLEWARE_CLASSES=[],
)
django.setup()

from django.core.management import call_command

call_command('makemigrations', 'migrations', verbosity=0, dry_run=True)

aliases = set(alias for alias, _, _ in CALLS)
print("aliases evaluated:", sorted(aliases))

valid_aliases = {'default', 'other'}
ok = True
if 'default' not in aliases:
    print("FAIL: 'default' not evaluated"); ok = False
if 'other' not in aliases:
    print("FAIL: 'other' (non-default) not evaluated despite routers configured"); ok = False
stray = aliases - valid_aliases
if stray:
    print("FAIL: stray/altered aliases passed:", stray); ok = False

if not ok:
    print("FAIL")
    sys.exit(1)
print("OK: default and other both evaluated; aliases passed unchanged")
sys.exit(0)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""Requirement 2 crit 3: WHEN no database routers are configured, the system
SHALL evaluate only the default database connection.

With DATABASE_ROUTERS unset, ConnectionRouter.allow_migrate still runs (default
return True), so we record which aliases the consistency check evaluates.

HOLDS iff the only alias evaluated is 'default' (never 'other'), even though an
'other' connection is configured.
"""
import sys
sys.path.insert(0, '/testbed/tests')

import django
from django.conf import settings
from django.db.utils import ConnectionRouter

CALLS = []
_orig = ConnectionRouter.allow_migrate


def _rec(self, db, app_label, **hints):
    CALLS.append((db, app_label, hints.get('model_name')))
    return _orig(self, db, app_label, **hints)


ConnectionRouter.allow_migrate = _rec

settings.configure(
    DEBUG=True,
    DATABASES={
        'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'},
        'other': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'},
    },
    INSTALLED_APPS=['migrations', 'migrations2'],
    DATABASE_ROUTERS=[],  # no routers
    MIDDLEWARE_CLASSES=[],
)
django.setup()

from django.core.management import call_command

call_command('makemigrations', 'migrations', verbosity=0, dry_run=True)

aliases = set(a for a, _, _ in CALLS)
print("aliases evaluated with no routers:", sorted(aliases))

if aliases != {'default'}:
    print("FAIL: expected only {'default'}, got", sorted(aliases))
    sys.exit(1)
print("OK: only default connection evaluated when no routers configured")
sys.exit(0)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""Requirement 2 crit 5: WHILE evaluating a connection whose engine is the
dummy backend, the system SHALL NOT perform the history consistency check for
that connection.

We configure 'other' as the dummy backend and a router that would ALLOW
migrate on 'other' (returns True). If the dummy connection were checked, the
dummy backend would raise on any real DB access. We verify by patching
MigrationLoader.check_consistent_history to record which connection aliases it
is invoked for; the dummy connection must never be among them.

HOLDS iff check_consistent_history is invoked for 'default' but never for the
dummy 'other'.
"""
import sys
sys.path.insert(0, '/testbed/tests')

import django
from django.conf import settings

CHECKED = []


class AllowRouter(object):
    def allow_migrate(self, db, app_label, model_name=None, **hints):
        return True  # would trigger a check on every connection


settings.configure(
    DEBUG=True,
    DATABASES={
        'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'},
        'other': {'ENGINE': 'django.db.backends.dummy'},
    },
    INSTALLED_APPS=['migrations', 'migrations2'],
    DATABASE_ROUTERS=[AllowRouter()],
    MIDDLEWARE_CLASSES=[],
)
django.setup()

from django.db.migrations.loader import MigrationLoader

_orig = MigrationLoader.check_consistent_history


def _rec(self, connection):
    CHECKED.append(connection.alias)
    return _orig(self, connection)


MigrationLoader.check_consistent_history = _rec

from django.core.management import call_command

call_command('makemigrations', 'migrations', verbosity=0, dry_run=True)

print("connections consistency-checked:", CHECKED)

if 'other' in CHECKED:
    print("FAIL: dummy connection 'other' was consistency-checked")
    sys.exit(1)
if 'default' not in CHECKED:
    print("FAIL: 'default' was not consistency-checked (check weakened)")
    sys.exit(1)
print("OK: dummy backend skipped; default checked")
sys.exit(0)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
"""Requirement 2 crit 4 + Requirement 3 crit 3 (SHALL keep):
(a) WHEN at least one allow_migrate() call for a connection returns truthy, the
    consistency check IS performed for that connection.
(b) The "app could not be found" error behavior is preserved for a bad label.

Part (a): a router allowing migrate on 'default' only must cause
check_consistent_history to run for 'default'.
Part (b): call_command('makemigrations','no_such_app') must exit(2) (SystemExit)
and emit the "could not be found" message — preserved behavior.

HOLDS iff both hold.
"""
import sys, io
sys.path.insert(0, '/testbed/tests')

import django
from django.conf import settings

CHECKED = []


class DefaultOnlyRouter(object):
    def allow_migrate(self, db, app_label, model_name=None, **hints):
        return db == 'default'


settings.configure(
    DEBUG=True,
    DATABASES={
        'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'},
        'other': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'},
    },
    INSTALLED_APPS=['migrations', 'migrations2'],
    DATABASE_ROUTERS=[DefaultOnlyRouter()],
    MIDDLEWARE_CLASSES=[],
)
django.setup()

from django.db.migrations.loader import MigrationLoader
_orig = MigrationLoader.check_consistent_history


def _rec(self, connection):
    CHECKED.append(connection.alias)
    return _orig(self, connection)


MigrationLoader.check_consistent_history = _rec

from django.core.management import call_command, CommandError

# Part (a)
call_command('makemigrations', 'migrations', verbosity=0, dry_run=True)
print("checked:", CHECKED)
ok = True
if 'default' not in CHECKED:
    print("FAIL(a): 'default' not checked despite truthy allow_migrate"); ok = False
if 'other' in CHECKED:
    print("FAIL(a): 'other' checked despite router forbidding it"); ok = False

# Part (b): bad app label
err = io.StringIO()
raised = None
try:
    call_command('makemigrations', 'definitely_not_an_app', verbosity=0, stderr=err)
except SystemExit as e:
    raised = ('SystemExit', e.code)
except CommandError as e:
    raised = ('CommandError', str(e))
msg = err.getvalue()
print("bad-app outcome:", raised, "| stderr:", msg.strip()[:120])
if raised is None:
    print("FAIL(b): no error raised for invalid app label"); ok = False
elif raised[0] == 'SystemExit':
    if raised[1] not in (2,):
        print("FAIL(b): SystemExit code not 2:", raised[1]); ok = False
    if 'could not be found' not in msg:
        print("FAIL(b): expected 'could not be found' message"); ok = False
# CommandError variant also acceptable (later Django); message check
elif raised[0] == 'CommandError':
    pass

if not ok:
    print("FAIL")
    sys.exit(1)
print("OK: truthy triggers check; bad app label preserved error behavior")
sys.exit(0)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Requirement 1 (crit 1-5) + positive control:
Every (app_label, model_name) pair passed to router.allow_migrate() during the
makemigrations consistency check must be VALID: model_name must be the
object_name of a model that actually belongs to app_label.

Records all pairs by installing a router that returns False (falsy) so the
`any(...)` generator is fully consumed and every pair is observed. Then checks
each pair with apps.get_app_config(app_label).get_model(model_name), exactly as
the hidden test does.

HOLDS iff no invalid (app_label, model_name) pair is ever passed.
"""
import sys
sys.path.insert(0, '/testbed/tests')

import django
from django.conf import settings

CALLS = []


class RecRouter(object):
    def allow_migrate(self, db, app_label, model_name=None, **hints):
        CALLS.append((db, app_label, model_name))
        return False  # falsy so `any()` consumes the whole generator


settings.configure(
    DEBUG=True,
    DATABASES={
        'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'},
        'other': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'},
    },
    INSTALLED_APPS=['migrations', 'migrations2'],
    DATABASE_ROUTERS=[RecRouter()],
    MIDDLEWARE_CLASSES=[],
)
django.setup()

from django.apps import apps
from django.core.management import call_command

call_command('makemigrations', 'migrations', verbosity=0, dry_run=True)

print("total allow_migrate calls recorded:", len(CALLS))
if not CALLS:
    print("FAIL: no calls recorded (check did not run)")
    sys.exit(1)

bad = []
for alias, app_label, model_name in CALLS:
    try:
        apps.get_app_config(app_label).get_model(model_name)
    except Exception as e:
        bad.append((alias, app_label, model_name, type(e).__name__))

# sample of observed pairs
seen = sorted(set((a, m) for _, a, m in CALLS))
print("distinct (app_label, model_name) pairs:", len(seen))
for a, m in seen:
    print("   pair:", a, m)
print("invalid pairs:", bad)

if bad:
    print("FAIL: invalid (app_label, model_name) pairs passed to allow_migrate")
    sys.exit(1)
print("OK: every pair valid for its application")
sys.exit(0)
```

Prepatch bug re-encoded as an attack: `True`.

Instance django__django-7530: makemigrations consistency check must call router.allow_migrate() only with valid (app_label, model_name) pairs. Gold fix replaces `apps.get_models(app_label)` with `apps.get_app_config(app_label).get_models()`.

Probes (all standalone, stdlib+repo only, run in official image; results below):
- probe_1 (Req1 c1-5, POSITIVE CONTROL): installs a recording router returning False so the whole any() generator is consumed; every (alias,app_label,model_name) pair is checked via apps.get_app_config(app_label).get_model(model_name). HOLDS patched (exit0, 0 invalid pairs); VIOLATED at base (LookupError on 'migrations2'/ModelWithCustomBase etc. — cross-app pairs). Discriminates base vs patched.
- probe_2 (Req1 c1,4,5 + Req2 c1): with 3 model-owning apps (contenttypes, auth, migrations), observed model-name set per app must EQUAL that app's own AppConfig models, and >=3 apps enumerated. HOLDS patched; would fail at base (each app paired with all project models).
- probe_3 (Req2 c2,6): with routers configured, both 'default' and non-default 'other' aliases evaluated; only configured aliases passed unchanged. HOLDS.
- probe_4 (Req2 c3): with DATABASE_ROUTERS=[] only 'default' evaluated even though 'other' configured. HOLDS.
- probe_5 (Req2 c5): 'other' set to dummy backend + allow-all router; check_consistent_history must be invoked for 'default' but never the dummy 'other'. HOLDS.
- probe_6 (Req2 c4 + Req3 c3): truthy allow_migrate for 'default' only triggers check for 'default' not 'other'; invalid app label 'definitely_not_an_app' -> SystemExit(2) with "could not be found" message preserved. HOLDS.

Candidate wrong patch (weak.diff): replaces `apps.get_models(app_label)` with `apps.get_models()` (the lazy/naive fix that still pairs every app with all project models). Probes 1 and 2 REJECT it (VIOLATED: invalid cross-app pairs like ('migrations2','ModelWithCustomBase')), demonstrating the suite discriminates the wrong implementation. No requirement-conforming alternative found.

Verdict SOUND: 6 distinct probes all hold on the gold-patched tree; positive control fails at base and holds patched (prepatch reproduced); a plausible weak patch is rejected by the suite. All docker runs completed.

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
"""Requirement 1 (crit 1-5) + positive control:
Every (app_label, model_name) pair passed to router.allow_migrate() during the
makemigrations consistency check must be VALID: model_name must be the
object_name of a model that actually belongs to app_label.

Records all pairs by installing a router that returns False (falsy) so the
`any(...)` generator is fully consumed and every pair is observed. Then checks
each pair with apps.get_app_config(app_label).get_model(model_name), exactly as
the hidden test does.

HOLDS iff no invalid (app_label, model_name) pair is ever passed.
"""
import sys
sys.path.insert(0, '/testbed/tests')

import django
from django.conf import settings

CALLS = []


class RecRouter(object):
    def allow_migrate(self, db, app_label, model_name=None, **hints):
        CALLS.append((db, app_label, model_name))
        return False  # falsy so `any()` consumes the whole generator


settings.configure(
    DEBUG=True,
    DATABASES={
        'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'},
        'other': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'},
    },
    INSTALLED_APPS=['migrations', 'migrations2'],
    DATABASE_ROUTERS=[RecRouter()],
    MIDDLEWARE_CLASSES=[],
)
django.setup()

from django.apps import apps
from django.core.management import call_command

call_command('makemigrations', 'migrations', verbosity=0, dry_run=True)

print("total allow_migrate calls recorded:", len(CALLS))
if not CALLS:
    print("FAIL: no calls recorded (check did not run)")
    sys.exit(1)

bad = []
for alias, app_label, model_name in CALLS:
    try:
        apps.get_app_config(app_label).get_model(model_name)
    except Exception as e:
        bad.append((alias, app_label, model_name, type(e).__name__))

# sample of observed pairs
seen = sorted(set((a, m) for _, a, m in CALLS))
print("distinct (app_label, model_name) pairs:", len(seen))
for a, m in seen:
    print("   pair:", a, m)
print("invalid pairs:", bad)

if bad:
    print("FAIL: invalid (app_label, model_name) pairs passed to allow_migrate")
    sys.exit(1)
print("OK: every pair valid for its application")
sys.exit(0)
```

Prepatch bug re-encoded as an attack: `True`.

Instance django__django-7530: makemigrations consistency check must call router.allow_migrate() only with valid (app_label, model_name) pairs. Gold fix replaces `apps.get_models(app_label)` with `apps.get_app_config(app_label).get_models()`.

Probes (all standalone, stdlib+repo only, run in official image; results below):
- probe_1 (Req1 c1-5, POSITIVE CONTROL): installs a recording router returning False so the whole any() generator is consumed; every (alias,app_label,model_name) pair is checked via apps.get_app_config(app_label).get_model(model_name). HOLDS patched (exit0, 0 invalid pairs); VIOLATED at base (LookupError on 'migrations2'/ModelWithCustomBase etc. — cross-app pairs). Discriminates base vs patched.
- probe_2 (Req1 c1,4,5 + Req2 c1): with 3 model-owning apps (contenttypes, auth, migrations), observed model-name set per app must EQUAL that app's own AppConfig models, and >=3 apps enumerated. HOLDS patched; would fail at base (each app paired with all project models).
- probe_3 (Req2 c2,6): with routers configured, both 'default' and non-default 'other' aliases evaluated; only configured aliases passed unchanged. HOLDS.
- probe_4 (Req2 c3): with DATABASE_ROUTERS=[] only 'default' evaluated even though 'other' configured. HOLDS.
- probe_5 (Req2 c5): 'other' set to dummy backend + allow-all router; check_consistent_history must be invoked for 'default' but never the dummy 'other'. HOLDS.
- probe_6 (Req2 c4 + Req3 c3): truthy allow_migrate for 'default' only triggers check for 'default' not 'other'; invalid app label 'definitely_not_an_app' -> SystemExit(2) with "could not be found" message preserved. HOLDS.

Candidate wrong patch (weak.diff): replaces `apps.get_models(app_label)` with `apps.get_models()` (the lazy/naive fix that still pairs every app with all project models). Probes 1 and 2 REJECT it (VIOLATED: invalid cross-app pairs like ('migrations2','ModelWithCustomBase')), demonstrating the suite discriminates the wrong implementation. No requirement-conforming alternative found.

Verdict SOUND: 6 distinct probes all hold on the gold-patched tree; positive control fails at base and holds patched (prepatch reproduced); a plausible weak patch is rejected by the suite. All docker runs completed.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Verified against actual code (via nl_attack probe on the gold-patched tree, exit 0; --base fails since patched enumeration absent, confirming the boundary). Requirement-by-requirement: Req 1 (1-5) matches the diff line-for-line, including 1.5's AppConfig-vs-project-wide-lookup framing (the real root cause: get_models(app_label) silently ignores its positional arg). Req 2 pins the UNCHANGED surrounding context and every clause is present in the real code: 2.1 consistency_check_labels = set(config.label for config in apps.get_app_configs()); 2.2 aliases_to_check = connections if settings.DATABASE_ROUTERS; 2.3 else [DEFAULT_DB_ALIAS]; 2.4 any(...) truthy -> check_consistent_history; 2.5 ENGINE != 'django.db.backends.dummy' guard; 2.6 router.allow_migrate(connection.alias, ...) alias passed unchanged. Req 3 (minimal targeted change; all other makemigrations behavior untouched) holds — patch touches only the generator's inner `for model` clause. Modeling boundary is correct: the requirements target the set of (app_label, model_name) pairs fed to allow_migrate — exactly the changed line — not a narrower slice (e.g. a single branch or helper) nor invented behavior. No over- or under-constraint found.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Requirements describe the fix behaviorally: pair each app label only with its own registered models during the makemigrations consistency check (gold: apps.get_models(app_label) -> apps.get_app_config(app_label).get_models()). Naming AppConfig/get_models (Req 1.5) is legitimate localization of a public Django API, not a fix-invented identifier. No hidden-test content is transmitted: no test names/paths (test_makemigrations_consistency_checks_respect_routers), no INSTALLED_APPS=['migrations','migrations2'], no UnicodeModel, no 'default'/'other' alias literals, no mock_calls/assert_any_call/ensure_schema.call_count enumeration. Connection-iteration and dummy-backend clauses (Req 2.2/2.3/2.5) describe preserved surrounding source behavior (public), not the hidden tests. Problem_statement already covers the all-models-vs-app-models defect and sharding-router breakage.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
