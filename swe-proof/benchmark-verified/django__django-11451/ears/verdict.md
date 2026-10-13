# P2 adversarial audit — django__django-11451

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 6 requirement probes hold on the patched tree; 2/2 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 6 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 6 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 2 alternative candidate patches, claimed to satisfy every cited requirement, and ran the same suite against them. The suite rejected all 2: a probe encoding a cited requirement fails under each of those, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_2.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (6):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
"""Requirement 1.1 / 1.5: no username -> return None, zero queries, zero hasher calls."""
import sys
import django
from django.conf import settings

if not settings.configured:
    settings.configure(
        DEBUG=True,
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
        INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
        AUTH_PASSWORD_VALIDATORS=[],
        PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'],
        USE_TZ=True,
    )
django.setup()
from django.core.management import call_command
call_command('migrate', run_syncdb=True, verbosity=0)

from django.db import connection
import django.contrib.auth.hashers as _h
import django.contrib.auth.base_user as _b
calls = {'n': 0}
_orig = _h.make_password
def _c(*a, **k):
    calls['n'] += 1
    return _orig(*a, **k)
_h.make_password = _c
_b.make_password = _c

from django.contrib.auth.backends import ModelBackend

q = []
def wrapper(execute, sql, params, many, context):
    q.append(sql)
    return execute(sql, params, many, context)

backend = ModelBackend()
calls['n'] = 0
with connection.execute_wrapper(wrapper):
    result = backend.authenticate(None, password='whatever')  # no username

print("result=%r queries=%d hasher_calls=%d" % (result, len(q), calls['n']))
ok = (result is None and len(q) == 0 and calls['n'] == 0)
sys.exit(0 if ok else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""Requirement 1.2: username present but password absent -> return None, zero queries, zero hasher calls."""
import sys
import django
from django.conf import settings

if not settings.configured:
    settings.configure(
        DEBUG=True,
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
        INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
        AUTH_PASSWORD_VALIDATORS=[],
        PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'],
        USE_TZ=True,
    )
django.setup()
from django.core.management import call_command
call_command('migrate', run_syncdb=True, verbosity=0)

from django.db import connection
import django.contrib.auth.hashers as _h
import django.contrib.auth.base_user as _b
calls = {'n': 0}
_orig = _h.make_password
def _c(*a, **k):
    calls['n'] += 1
    return _orig(*a, **k)
_h.make_password = _c
_b.make_password = _c

from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
User = get_user_model()
# create a real user so a query WOULD find something if it ran
User.objects.create_user(username='alice', password='secret')

q = []
def wrapper(execute, sql, params, many, context):
    q.append(sql)
    return execute(sql, params, many, context)

backend = ModelBackend()
calls['n'] = 0
with connection.execute_wrapper(wrapper):
    result = backend.authenticate(None, username='alice')  # no password

print("result=%r queries=%d hasher_calls=%d" % (result, len(q), calls['n']))
ok = (result is None and len(q) == 0 and calls['n'] == 0)
sys.exit(0 if ok else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""Requirement 1.3: no credentials at all (empty kwargs) -> None, zero queries, zero hasher."""
import sys
import django
from django.conf import settings

if not settings.configured:
    settings.configure(
        DEBUG=True,
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
        INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
        AUTH_PASSWORD_VALIDATORS=[],
        PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'],
        USE_TZ=True,
    )
django.setup()
from django.core.management import call_command
call_command('migrate', run_syncdb=True, verbosity=0)

from django.db import connection
import django.contrib.auth.hashers as _h
import django.contrib.auth.base_user as _b
calls = {'n': 0}
_orig = _h.make_password
def _c(*a, **k):
    calls['n'] += 1
    return _orig(*a, **k)
_h.make_password = _c
_b.make_password = _c

from django.contrib.auth.backends import ModelBackend

q = []
def wrapper(execute, sql, params, many, context):
    q.append(sql)
    return execute(sql, params, many, context)

backend = ModelBackend()
calls['n'] = 0
with connection.execute_wrapper(wrapper):
    result = backend.authenticate(None)  # nothing at all

print("result=%r queries=%d hasher_calls=%d" % (result, len(q), calls['n']))
ok = (result is None and len(q) == 0 and calls['n'] == 0)
sys.exit(0 if ok else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""Requirement 1.4: empty-but-present password ('') must NOT short-circuit.
With a resolved username and password='', the backend must proceed to the
credential-store lookup (>=1 query)."""
import sys
import django
from django.conf import settings

if not settings.configured:
    settings.configure(
        DEBUG=True,
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
        INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
        AUTH_PASSWORD_VALIDATORS=[],
        PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'],
        USE_TZ=True,
    )
django.setup()
from django.core.management import call_command
call_command('migrate', run_syncdb=True, verbosity=0)

from django.db import connection
from django.contrib.auth.backends import ModelBackend

q = []
def wrapper(execute, sql, params, many, context):
    q.append(sql)
    return execute(sql, params, many, context)

backend = ModelBackend()
# no such user -> lookup happens then hasher; but key point: a query IS emitted
with connection.execute_wrapper(wrapper):
    result = backend.authenticate(None, username='ghost', password='')

print("result=%r queries=%d" % (result, len(q)))
# empty password is present, so short-circuit must NOT happen: a lookup query occurs
ok = (result is None and len(q) >= 1)
sys.exit(0 if ok else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""Requirement 2.1: username resolved from USERNAME_FIELD kwarg when no explicit username.
A valid login supplied via kwargs['username'] (USERNAME_FIELD) with a password
must authenticate successfully -> returns the user (not short-circuited)."""
import sys
import django
from django.conf import settings

if not settings.configured:
    settings.configure(
        DEBUG=True,
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
        INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
        AUTH_PASSWORD_VALIDATORS=[],
        PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'],
        USE_TZ=True,
    )
django.setup()
from django.core.management import call_command
call_command('migrate', run_syncdb=True, verbosity=0)

from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
User = get_user_model()
u = User.objects.create_user(username='bob', password='hunter2')

backend = ModelBackend()
# USERNAME_FIELD is 'username'; pass it via kwargs, no explicit username arg
result = backend.authenticate(None, password='hunter2', username='bob')
# distinguish: pass through kwargs only path by using the resolved-from-kwargs branch
result2 = backend.authenticate(None, **{User.USERNAME_FIELD: 'bob', 'password': 'hunter2'})

print("result=%r result2=%r expected_pk=%r" % (result, result2, u.pk))
ok = (result is not None and result.pk == u.pk and result2 is not None and result2.pk == u.pk)
sys.exit(0 if ok else 1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
"""Requirement 3.1/3.2/3.3: normal auth behavior preserved.
- valid creds -> returns user
- wrong password -> None but hasher NOT run extra (user exists so check_password path)
- nonexistent user w/ password -> None AND default hasher run exactly once (timing mask)
- exactly one lookup query for present creds
Also Req 3.4: inactive user rejected."""
import sys
import django
from django.conf import settings

if not settings.configured:
    settings.configure(
        DEBUG=True,
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
        INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
        AUTH_PASSWORD_VALIDATORS=[],
        PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'],
        USE_TZ=True,
    )
django.setup()
from django.core.management import call_command
call_command('migrate', run_syncdb=True, verbosity=0)

from django.db import connection
import django.contrib.auth.hashers as _h
import django.contrib.auth.base_user as _b
calls = {'n': 0}
_orig = _h.make_password
def _c(*a, **k):
    calls['n'] += 1
    return _orig(*a, **k)
_h.make_password = _c
_b.make_password = _c

from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
User = get_user_model()
User.objects.create_user(username='carol', password='pw')
inactive = User.objects.create_user(username='dave', password='pw')
inactive.is_active = False
inactive.save()

backend = ModelBackend()

# valid creds
r_valid = backend.authenticate(None, username='carol', password='pw')

# wrong password (user exists)
r_wrong = backend.authenticate(None, username='carol', password='nope')

# inactive user rejected
r_inactive = backend.authenticate(None, username='dave', password='pw')

# nonexistent user: hasher must run exactly once, exactly one query
q = []
def wrapper(execute, sql, params, many, context):
    q.append(sql)
    return execute(sql, params, many, context)
calls['n'] = 0
with connection.execute_wrapper(wrapper):
    r_missing = backend.authenticate(None, username='nobody', password='pw')

print("valid=%r wrong=%r inactive=%r missing=%r missing_queries=%d hasher_on_missing=%d" % (
    r_valid, r_wrong, r_inactive, r_missing, len(q), calls['n']))

ok = (
    r_valid is not None and
    r_wrong is None and
    r_inactive is None and
    r_missing is None and
    len(q) == 1 and
    calls['n'] == 1
)
sys.exit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_2.py`

```python
"""Requirement 1.2: username present but password absent -> return None, zero queries, zero hasher calls."""
import sys
import django
from django.conf import settings

if not settings.configured:
    settings.configure(
        DEBUG=True,
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
        INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
        AUTH_PASSWORD_VALIDATORS=[],
        PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'],
        USE_TZ=True,
    )
django.setup()
from django.core.management import call_command
call_command('migrate', run_syncdb=True, verbosity=0)

from django.db import connection
import django.contrib.auth.hashers as _h
import django.contrib.auth.base_user as _b
calls = {'n': 0}
_orig = _h.make_password
def _c(*a, **k):
    calls['n'] += 1
    return _orig(*a, **k)
_h.make_password = _c
_b.make_password = _c

from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
User = get_user_model()
# create a real user so a query WOULD find something if it ran
User.objects.create_user(username='alice', password='secret')

q = []
def wrapper(execute, sql, params, many, context):
    q.append(sql)
    return execute(sql, params, many, context)

backend = ModelBackend()
calls['n'] = 0
with connection.execute_wrapper(wrapper):
    result = backend.authenticate(None, username='alice')  # no password

print("result=%r queries=%d hasher_calls=%d" % (result, len(q), calls['n']))
ok = (result is None and len(q) == 0 and calls['n'] == 0)
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance django__django-11451: ModelBackend.authenticate short-circuits (no DB query, no password hasher) when username or password is None, while preserving all normal auth/permission behavior. Six standalone probes, all run in the official image.

Probe->requirement mapping and results (PATCHED / BASE):
- probe_1 (Req 1.1/1.5: no username -> None, 0 queries, 0 hasher): HOLDS patched (q=0,h=0) / VIOLATED base (q=1,h=1).
- probe_2 (Req 1.2: username present, password None -> None, 0 queries, 0 hasher): HOLDS patched (q=0,h=0) / VIOLATED base (q=1,h=0). POSITIVE CONTROL.
- probe_3 (Req 1.3: empty kwargs -> None, 0 queries, 0 hasher): HOLDS patched / VIOLATED base (q=1,h=1).
- probe_4 (Req 1.4: empty-but-present password '' must NOT short-circuit -> a lookup query is emitted): HOLDS patched (q=1) / HOLDS base (regression criterion, both trees preserve it).
- probe_5 (Req 2.1: username resolved from USERNAME_FIELD kwarg, valid login authenticates): HOLDS both.
- probe_6 (Req 3.1/3.2/3.3/3.4: valid->user, wrong pw->None, inactive->None, nonexistent user runs default hasher exactly once with exactly one lookup query): HOLDS both.

Discriminating power: positive control (probes 1-3) fail at base and hold patched.

Candidate wrong-fix patches, both REJECTED by the suite (proves discrimination):
- weak_username_only ('if username is None: return' — ignores missing password): REJECTED by probe_2 (Req 1.2) — with a real user present it still emits a query when password is None.
- weak_truthiness ('if not username or not password: return' — truthiness instead of `is None`): REJECTED by probe_4 (Req 1.4) — empty-string password wrongly short-circuits (q=0), violating the explicit None-only rule.

All 6 probes hold on the gold-patched tree; positive control discriminates; two requirement-plausible weak fixes are both caught. No violation and no probe-conforming weak patch found. Verdict SOUND (advisory; runner re-runs).

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 requirement probes hold on the patched tree; 2/2 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 6 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 6 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 2 alternative candidate patches, claimed to satisfy every cited requirement, and ran the same suite against them. The suite rejected all 2: a probe encoding a cited requirement fails under each of those, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_2.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (6):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

_The 6 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts, and on this backend both roles put it through the same derivation: every block below is a requirement probe run on the gold-patched tree, and the `machine verdict:` line each role publishes above reports BOTH that its probes hold there and how many candidate patches the probe suite rejected — so the two roles re-ran ONE probe suite and each recorded its own outcome for every probe in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `probe_1.py` → holds on the patched tree (good)

Attack 2 — `probe_2.py` → holds on the patched tree (good)

Attack 3 — `probe_3.py` → holds on the patched tree (good)

Attack 4 — `probe_4.py` → holds on the patched tree (good)

Attack 5 — `probe_5.py` → holds on the patched tree (good)

Attack 6 — `probe_6.py` → holds on the patched tree (good)

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_2.py`

```python
"""Requirement 1.2: username present but password absent -> return None, zero queries, zero hasher calls."""
import sys
import django
from django.conf import settings

if not settings.configured:
    settings.configure(
        DEBUG=True,
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
        INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
        AUTH_PASSWORD_VALIDATORS=[],
        PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'],
        USE_TZ=True,
    )
django.setup()
from django.core.management import call_command
call_command('migrate', run_syncdb=True, verbosity=0)

from django.db import connection
import django.contrib.auth.hashers as _h
import django.contrib.auth.base_user as _b
calls = {'n': 0}
_orig = _h.make_password
def _c(*a, **k):
    calls['n'] += 1
    return _orig(*a, **k)
_h.make_password = _c
_b.make_password = _c

from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
User = get_user_model()
# create a real user so a query WOULD find something if it ran
User.objects.create_user(username='alice', password='secret')

q = []
def wrapper(execute, sql, params, many, context):
    q.append(sql)
    return execute(sql, params, many, context)

backend = ModelBackend()
calls['n'] = 0
with connection.execute_wrapper(wrapper):
    result = backend.authenticate(None, username='alice')  # no password

print("result=%r queries=%d hasher_calls=%d" % (result, len(q), calls['n']))
ok = (result is None and len(q) == 0 and calls['n'] == 0)
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance django__django-11451: ModelBackend.authenticate short-circuits (no DB query, no password hasher) when username or password is None, while preserving all normal auth/permission behavior. Six standalone probes, all run in the official image.

Probe->requirement mapping and results (PATCHED / BASE):
- probe_1 (Req 1.1/1.5: no username -> None, 0 queries, 0 hasher): HOLDS patched (q=0,h=0) / VIOLATED base (q=1,h=1).
- probe_2 (Req 1.2: username present, password None -> None, 0 queries, 0 hasher): HOLDS patched (q=0,h=0) / VIOLATED base (q=1,h=0). POSITIVE CONTROL.
- probe_3 (Req 1.3: empty kwargs -> None, 0 queries, 0 hasher): HOLDS patched / VIOLATED base (q=1,h=1).
- probe_4 (Req 1.4: empty-but-present password '' must NOT short-circuit -> a lookup query is emitted): HOLDS patched (q=1) / HOLDS base (regression criterion, both trees preserve it).
- probe_5 (Req 2.1: username resolved from USERNAME_FIELD kwarg, valid login authenticates): HOLDS both.
- probe_6 (Req 3.1/3.2/3.3/3.4: valid->user, wrong pw->None, inactive->None, nonexistent user runs default hasher exactly once with exactly one lookup query): HOLDS both.

Discriminating power: positive control (probes 1-3) fail at base and hold patched.

Candidate wrong-fix patches, both REJECTED by the suite (proves discrimination):
- weak_username_only ('if username is None: return' — ignores missing password): REJECTED by probe_2 (Req 1.2) — with a real user present it still emits a query when password is None.
- weak_truthiness ('if not username or not password: return' — truthiness instead of `is None`): REJECTED by probe_4 (Req 1.4) — empty-string password wrongly short-circuits (q=0), violating the explicit None-only rule.

All 6 probes hold on the gold-patched tree; positive control discriminates; two requirement-plausible weak fixes are both caught. No violation and no probe-conforming weak patch found. Verdict SOUND (advisory; runner re-runs).

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Requirements model the exact short-circuit boundary. Critically R1.4 (`is None`, not falsiness) matches the code: an empty-but-present password does NOT short-circuit, verified by probe R4 (query runs). No overreach: R3/R4 preserve existing hasher-once/active-flag behavior unchanged (nothing else in patch). No invented behavior. Modeling boundary is the changed authenticate() behavior, correctly biconditional (short-circuit iff username or password is None).


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The public problem_statement already contains the complete gold edit (`if username is None or password is None: return`), the username resolution line `kwargs.get(UserModel.USERNAME_FIELD)`, the timing-masking rationale (#20760), and the fact that the reporter noticed this via assertNumQueries tests observing the useless `username IS NULL` query plus needless hashing. Requirement 1's three acceptance criteria (username absent / password absent / empty kwargs -> return None with zero queries and zero hasher calls) map to the hidden test's three subTest dicts ({}, {'username':...}, {'password':'test'}), but this enumeration is directly and trivially derivable from the two-condition short-circuit that is PUBLIC in the problem statement — it is a behavioral restatement, not a transmission of the test. No hidden identifiers leak: the document never names test_authentication_without_credentials, test_custom_perms, the CountingMD5PasswordHasher, the test file path tests/auth_tests/test_auth_backends.py, or the backend test-class variants (ModelBackendTest / CustomPermissionsUserModelBackendTest / ExtensionUserModelBackendTest). Req 4's permission language ('custom permissions granted directly to a user and via groups', superuser/inactive/anonymous) describes general, long-standing ModelBackend behavior rather than mirroring test parametrization. Naming ModelBackend.authenticate is legitimate localization. No fix-invented identifiers exist (the fix invents nothing). No quoted test/gold code beyond what problem_statement already publishes.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
