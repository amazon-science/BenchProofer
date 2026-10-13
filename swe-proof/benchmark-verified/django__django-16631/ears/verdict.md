# P2 adversarial audit — django__django-16631

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 5 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 5 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 5 | `probe_1_e2e_fallback.py`, `probe_2_fallback_enum.py`, `probe_3_explicit_secret.py`, `probe_4_current_secret_untouched.py`, `probe_5_no_match_flush.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1_e2e_fallback.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

Counterexample / evidence:

```
weak_noupgrade: identical to gold except it drops `request.session[HASH_SESSION_KEY] = session_auth_hash` after cycle_key() on a fallback match. It satisfies Req1/Req2/Req3.1-3.3/Req3.5/Req3.6/Req5 (probes 2-5 all HOLD under it) but violates Req3.4/Req4.1 — the stored hash is never upgraded to the current secret, so once the fallback is removed the user is logged out. probe_1 REJECTS it (exit=1: 'stored hash not upgraded'; 'user not authenticated after fallback removed'), matching the hidden F2P test test_get_user_fallback_secret which asserts authentication survives after the fallback secret is removed.
```

**Attacks re-run (5):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1_e2e_fallback.py` → holds on the patched tree (good)

```python
"""
Positive control + Req 3.2/3.3/3.4/4.1: end-to-end get_user with rotated secret.

A session signed under the OLD secret (now listed in SECRET_KEY_FALLBACKS) must:
 - stay authenticated (return the real user, not anonymous)  [Req 3.2]
 - have its session key rotated (differs from before)        [Req 3.3]
 - have its stored auth hash upgraded to the current secret   [Req 3.4]
 - keep working after the fallback is removed                 [Req 4.1]

HOLDS on patched, FAILS at base (base logs the user out => flush => anonymous).
"""
import django
from django.conf import settings

settings.configure(
    DEBUG=True,
    SECRET_KEY="oldsecret",
    SECRET_KEY_FALLBACKS=[],
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    INSTALLED_APPS=[
        "django.contrib.contenttypes",
        "django.contrib.auth",
        "django.contrib.sessions",
    ],
    AUTHENTICATION_BACKENDS=["django.contrib.auth.backends.ModelBackend"],
    SESSION_ENGINE="django.contrib.sessions.backends.db",
    PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"],
    USE_TZ=True,
)
django.setup()

from django.core.management import call_command
call_command("migrate", run_syncdb=True, verbosity=0)

from django.contrib.auth import get_user, SESSION_KEY, BACKEND_SESSION_KEY, HASH_SESSION_KEY
from django.contrib.auth.models import User, AnonymousUser
from django.contrib.sessions.backends.db import SessionStore
from django.test import override_settings

u = User.objects.create_user("testuser", "t@example.com", "testpw")

# Build a session as if logged in under the OLD secret.
session = SessionStore()
session[SESSION_KEY] = str(u.pk)
session[BACKEND_SESSION_KEY] = "django.contrib.auth.backends.ModelBackend"
session[HASH_SESSION_KEY] = u.get_session_auth_hash()  # under oldsecret
session.save()
prev_key = session.session_key

class Req:
    pass

req = Req()
req.session = session

ok = True
# Rotate secret: oldsecret -> newsecret, oldsecret now a fallback.
with override_settings(SECRET_KEY="newsecret", SECRET_KEY_FALLBACKS=["oldsecret"]):
    user = get_user(req)
    print("after-rotation user:", type(user).__name__, getattr(user, "username", None))
    if not isinstance(user, User) or user.username != "testuser":
        print("FAIL: user not authenticated on fallback")
        import sys; sys.exit(1)
    if req.session.session_key == prev_key:
        print("FAIL: session key NOT rotated", prev_key, req.session.session_key)
        ok = False
    else:
        print("session key rotated OK:", prev_key, "->", req.session.session_key)
    # stored hash should now be the newsecret hash
    new_hash = user.get_session_auth_hash()  # under newsecret
    if req.session.get(HASH_SESSION_KEY) != new_hash:
        print("FAIL: stored hash not upgraded to current secret")
        ok = False
    else:
        print("stored hash upgraded to current secret OK")

# Remove the fallback; current secret is the upgrade secret. Must still work.
with override_settings(SECRET_KEY="newsecret", SECRET_KEY_FALLBACKS=[]):
    user2 = get_user(req)
    print("after-fallback-removal user:", type(user2).__name__, getattr(user2, "username", None))
    if not isinstance(user2, User) or user2.username != "testuser":
        print("FAIL: user not authenticated after fallback removed")
        ok = False

import sys
sys.exit(0 if ok else 1)
```

Attack 2 — `probe_2_fallback_enum.py` → holds on the patched tree (good)

```python
"""
Req 2.1-2.4 (+ Req 1.4): get_session_auth_fallback_hash enumerates one hash per
fallback secret, IN ORDER; empty when no fallbacks; each equals the hash the user
would produce when that secret is the active SECRET_KEY.
"""
import django
from django.conf import settings

settings.configure(
    DEBUG=True,
    SECRET_KEY="cur",
    SECRET_KEY_FALLBACKS=["fb0", "fb1", "fb2"],
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
    PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"],
    USE_TZ=True,
)
django.setup()
from django.core.management import call_command
call_command("migrate", run_syncdb=True, verbosity=0)

from django.contrib.auth.models import User
from django.test import override_settings

u = User.objects.create_user("testuser", "t@example.com", "testpw")

ok = True

# 2.2: one per fallback, in order.
hashes = list(u.get_session_auth_fallback_hash())
print("n fallback hashes:", len(hashes))
if len(hashes) != 3:
    print("FAIL: expected 3 fallback hashes"); ok = False

# 1.4 / 2.4: each fallback hash == active-secret hash for that secret, in order.
for i, secret in enumerate(["fb0", "fb1", "fb2"]):
    with override_settings(SECRET_KEY=secret, SECRET_KEY_FALLBACKS=[]):
        active = u.get_session_auth_hash()
    match = (hashes[i] == active)
    print(f"fallback[{i}] ({secret}) matches active-secret hash: {match}")
    if not match:
        print("FAIL: ordering/derivation mismatch at index", i); ok = False

# 2.3: empty fallbacks -> no hashes.
with override_settings(SECRET_KEY="cur", SECRET_KEY_FALLBACKS=[]):
    empty = list(u.get_session_auth_fallback_hash())
print("empty-fallbacks yielded:", len(empty))
if empty:
    print("FAIL: expected no fallback hashes when empty"); ok = False

import sys
sys.exit(0 if ok else 1)
```

Attack 3 — `probe_3_explicit_secret.py` → holds on the patched tree (good)

```python
"""
Req 1.1-1.4 & Req 5.1/5.4: session-auth-hash computation under an explicit secret.

- get_session_auth_hash() with no explicit secret == current SECRET_KEY HMAC (1.2/5.1)
- derivation is SHA-256 salted_hmac of password under the fixed key_salt (1.3)
- computing under a supplied secret == the hash the user would produce with that
  secret active as SECRET_KEY (1.4)
- salted_hmac defaults to SECRET_KEY when no secret supplied (5.4)
"""
import django
from django.conf import settings

settings.configure(
    DEBUG=True,
    SECRET_KEY="cur",
    SECRET_KEY_FALLBACKS=[],
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
    PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"],
    USE_TZ=True,
)
django.setup()
from django.core.management import call_command
call_command("migrate", run_syncdb=True, verbosity=0)

from django.contrib.auth.models import User
from django.utils.crypto import salted_hmac
from django.test import override_settings

u = User.objects.create_user("testuser", "t@example.com", "testpw")
KEY_SALT = "django.contrib.auth.models.AbstractBaseUser.get_session_auth_hash"

ok = True

# 1.3 + 1.2: default hash == explicit salted_hmac sha256 under current secret.
expected_default = salted_hmac(KEY_SALT, u.password, algorithm="sha256").hexdigest()
got_default = u.get_session_auth_hash()
print("default==explicit sha256 salted_hmac:", got_default == expected_default)
if got_default != expected_default:
    print("FAIL: default derivation mismatch"); ok = False

# 1.1 + 1.4: private helper under an explicit secret == hash w/ that secret active.
explicit = u._get_session_auth_hash(secret="othersecret")
expected_explicit = salted_hmac(KEY_SALT, u.password, secret="othersecret",
                                algorithm="sha256").hexdigest()
print("explicit-secret helper matches salted_hmac(secret=...):",
      explicit == expected_explicit)
if explicit != expected_explicit:
    print("FAIL: explicit-secret derivation mismatch"); ok = False

with override_settings(SECRET_KEY="othersecret"):
    active_other = u.get_session_auth_hash()
print("explicit-secret hash == that-secret-active hash:", explicit == active_other)
if explicit != active_other:
    print("FAIL: explicit secret != active secret hash"); ok = False

# explicit under current secret must equal default.
print("explicit(cur)==default:", u._get_session_auth_hash(secret="cur") == got_default)
if u._get_session_auth_hash(secret="cur") != got_default:
    print("FAIL: explicit(cur) != default"); ok = False

# 5.4: salted_hmac with no secret defaults to SECRET_KEY.
a = salted_hmac(KEY_SALT, u.password, algorithm="sha256").hexdigest()
b = salted_hmac(KEY_SALT, u.password, secret="cur", algorithm="sha256").hexdigest()
print("salted_hmac no-secret == secret=SECRET_KEY:", a == b)
if a != b:
    print("FAIL: salted_hmac default-secret regression"); ok = False

import sys
sys.exit(0 if ok else 1)
```

Attack 4 — `probe_4_current_secret_untouched.py` → holds on the patched tree (good)

```python
"""
Req 3.1 & 5.5: when the stored hash matches the CURRENT secret, get_user returns
the user AND leaves the session unchanged — no rotate, no flush, no hash rewrite.
"""
import django
from django.conf import settings

settings.configure(
    DEBUG=True,
    SECRET_KEY="cur",
    SECRET_KEY_FALLBACKS=["oldfb"],
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth",
                    "django.contrib.sessions"],
    AUTHENTICATION_BACKENDS=["django.contrib.auth.backends.ModelBackend"],
    SESSION_ENGINE="django.contrib.sessions.backends.db",
    PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"],
    USE_TZ=True,
)
django.setup()
from django.core.management import call_command
call_command("migrate", run_syncdb=True, verbosity=0)

from django.contrib.auth import get_user, SESSION_KEY, BACKEND_SESSION_KEY, HASH_SESSION_KEY
from django.contrib.auth.models import User

u = User.objects.create_user("testuser", "t@example.com", "testpw")

from django.contrib.sessions.backends.db import SessionStore
session = SessionStore()
session[SESSION_KEY] = str(u.pk)
session[BACKEND_SESSION_KEY] = "django.contrib.auth.backends.ModelBackend"
cur_hash = u.get_session_auth_hash()  # under current secret
session[HASH_SESSION_KEY] = cur_hash
session.save()
prev_key = session.session_key

class Req: pass
req = Req(); req.session = session

user = get_user(req)
ok = True
print("user:", type(user).__name__, getattr(user, "username", None))
if not isinstance(user, User) or user.username != "testuser":
    print("FAIL: not authenticated on current secret"); ok = False
if req.session.session_key != prev_key:
    print("FAIL: session key rotated on current-secret match", prev_key,
          req.session.session_key); ok = False
else:
    print("session key unchanged OK")
if req.session.get(HASH_SESSION_KEY) != cur_hash:
    print("FAIL: stored hash altered on current-secret match"); ok = False
else:
    print("stored hash unchanged OK")

import sys
sys.exit(0 if ok else 1)
```

Attack 5 — `probe_5_no_match_flush.py` → holds on the patched tree (good)

```python
"""
Req 3.5 & 3.6:
 - stored hash matches neither current nor any fallback -> flush + anonymous.
 - no stored session auth hash at all -> flush + anonymous.
"""
import django
from django.conf import settings

settings.configure(
    DEBUG=True,
    SECRET_KEY="cur",
    SECRET_KEY_FALLBACKS=["fb0", "fb1"],
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth",
                    "django.contrib.sessions"],
    AUTHENTICATION_BACKENDS=["django.contrib.auth.backends.ModelBackend"],
    SESSION_ENGINE="django.contrib.sessions.backends.db",
    PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"],
    USE_TZ=True,
)
django.setup()
from django.core.management import call_command
call_command("migrate", run_syncdb=True, verbosity=0)

from django.contrib.auth import get_user, SESSION_KEY, BACKEND_SESSION_KEY, HASH_SESSION_KEY
from django.contrib.auth.models import User, AnonymousUser
from django.contrib.sessions.backends.db import SessionStore

u = User.objects.create_user("testuser", "t@example.com", "testpw")

def make_session(hashval):
    s = SessionStore()
    s[SESSION_KEY] = str(u.pk)
    s[BACKEND_SESSION_KEY] = "django.contrib.auth.backends.ModelBackend"
    if hashval is not None:
        s[HASH_SESSION_KEY] = hashval
    s.save()
    return s

class Req: pass

ok = True

# 3.5: bogus hash, not current nor any fallback.
s1 = make_session("deadbeef" * 8)
r1 = Req(); r1.session = s1
key1 = s1.session_key
u1 = get_user(r1)
print("bogus-hash user:", type(u1).__name__)
if not isinstance(u1, AnonymousUser):
    print("FAIL 3.5: expected anonymous"); ok = False
if r1.session.get(HASH_SESSION_KEY) is not None or r1.session.get(SESSION_KEY) is not None:
    print("FAIL 3.5: session not flushed"); ok = False
else:
    print("session flushed OK (3.5)")

# 3.6: no stored session auth hash.
s2 = make_session(None)
r2 = Req(); r2.session = s2
u2 = get_user(r2)
print("no-hash user:", type(u2).__name__)
if not isinstance(u2, AnonymousUser):
    print("FAIL 3.6: expected anonymous"); ok = False
if r2.session.get(SESSION_KEY) is not None:
    print("FAIL 3.6: session not flushed"); ok = False
else:
    print("session flushed OK (3.6)")

import sys
sys.exit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1_e2e_fallback.py`

```python
"""
Positive control + Req 3.2/3.3/3.4/4.1: end-to-end get_user with rotated secret.

A session signed under the OLD secret (now listed in SECRET_KEY_FALLBACKS) must:
 - stay authenticated (return the real user, not anonymous)  [Req 3.2]
 - have its session key rotated (differs from before)        [Req 3.3]
 - have its stored auth hash upgraded to the current secret   [Req 3.4]
 - keep working after the fallback is removed                 [Req 4.1]

HOLDS on patched, FAILS at base (base logs the user out => flush => anonymous).
"""
import django
from django.conf import settings

settings.configure(
    DEBUG=True,
    SECRET_KEY="oldsecret",
    SECRET_KEY_FALLBACKS=[],
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    INSTALLED_APPS=[
        "django.contrib.contenttypes",
        "django.contrib.auth",
        "django.contrib.sessions",
    ],
    AUTHENTICATION_BACKENDS=["django.contrib.auth.backends.ModelBackend"],
    SESSION_ENGINE="django.contrib.sessions.backends.db",
    PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"],
    USE_TZ=True,
)
django.setup()

from django.core.management import call_command
call_command("migrate", run_syncdb=True, verbosity=0)

from django.contrib.auth import get_user, SESSION_KEY, BACKEND_SESSION_KEY, HASH_SESSION_KEY
from django.contrib.auth.models import User, AnonymousUser
from django.contrib.sessions.backends.db import SessionStore
from django.test import override_settings

u = User.objects.create_user("testuser", "t@example.com", "testpw")

# Build a session as if logged in under the OLD secret.
session = SessionStore()
session[SESSION_KEY] = str(u.pk)
session[BACKEND_SESSION_KEY] = "django.contrib.auth.backends.ModelBackend"
session[HASH_SESSION_KEY] = u.get_session_auth_hash()  # under oldsecret
session.save()
prev_key = session.session_key

class Req:
    pass

req = Req()
req.session = session

ok = True
# Rotate secret: oldsecret -> newsecret, oldsecret now a fallback.
with override_settings(SECRET_KEY="newsecret", SECRET_KEY_FALLBACKS=["oldsecret"]):
    user = get_user(req)
    print("after-rotation user:", type(user).__name__, getattr(user, "username", None))
    if not isinstance(user, User) or user.username != "testuser":
        print("FAIL: user not authenticated on fallback")
        import sys; sys.exit(1)
    if req.session.session_key == prev_key:
        print("FAIL: session key NOT rotated", prev_key, req.session.session_key)
        ok = False
    else:
        print("session key rotated OK:", prev_key, "->", req.session.session_key)
    # stored hash should now be the newsecret hash
    new_hash = user.get_session_auth_hash()  # under newsecret
    if req.session.get(HASH_SESSION_KEY) != new_hash:
        print("FAIL: stored hash not upgraded to current secret")
        ok = False
    else:
        print("stored hash upgraded to current secret OK")

# Remove the fallback; current secret is the upgrade secret. Must still work.
with override_settings(SECRET_KEY="newsecret", SECRET_KEY_FALLBACKS=[]):
    user2 = get_user(req)
    print("after-fallback-removal user:", type(user2).__name__, getattr(user2, "username", None))
    if not isinstance(user2, User) or user2.username != "testuser":
        print("FAIL: user not authenticated after fallback removed")
        ok = False

import sys
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Runner env: /testbed, django 5.0.dev, py3.11. All 5 probes HOLD on gold-patched tree. Positive control (probe_1) FAILS at base (base get_user only compares current-secret hash => flush => AnonymousUser). Probe coverage by requirement: probe_1 -> Req3.2/3.3/3.4/4.1 (+ Req5.5 rotation only on fallback); probe_2 -> Req2.1-2.4 & Req1.4 (one hash per fallback, in order, empty when none, each == active-secret hash); probe_3 -> Req1.1-1.4, Req5.1, Req5.4 (explicit-secret computation, sha256 salted_hmac under fixed key_salt, default==current-secret, salted_hmac defaults to SECRET_KEY); probe_4 -> Req3.1 & Req5.5 (current-secret match: authenticated, session key unchanged, stored hash unchanged); probe_5 -> Req3.5 & Req3.6 (bogus hash and missing hash both flush + anonymous). Discrimination demonstrated: candidate weak_noupgrade applies cleanly at base_commit and is REJECTED by probe_1 while probes 2-5 still HOLD, proving the suite distinguishes the requirements-satisfying-but-wrong fixes from the gold behavior on exactly the upgrade/persistence criterion the hidden test exercises.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 5 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 5 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 5 | `probe_1_e2e_fallback.py`, `probe_2_fallback_enum.py`, `probe_3_explicit_secret.py`, `probe_4_current_secret_untouched.py`, `probe_5_no_match_flush.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1_e2e_fallback.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

Counterexample / evidence:

```
weak_noupgrade: identical to gold except it drops `request.session[HASH_SESSION_KEY] = session_auth_hash` after cycle_key() on a fallback match. It satisfies Req1/Req2/Req3.1-3.3/Req3.5/Req3.6/Req5 (probes 2-5 all HOLD under it) but violates Req3.4/Req4.1 — the stored hash is never upgraded to the current secret, so once the fallback is removed the user is logged out. probe_1 REJECTS it (exit=1: 'stored hash not upgraded'; 'user not authenticated after fallback removed'), matching the hidden F2P test test_get_user_fallback_secret which asserts authentication survives after the fallback secret is removed.
```

**Attacks re-run (5):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

_The 5 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts, and on this backend both roles put it through the same derivation: every block below is a requirement probe run on the gold-patched tree, and the `machine verdict:` line each role publishes above reports BOTH that its probes hold there and how many candidate patches the probe suite rejected — so the two roles re-ran ONE probe suite and each recorded its own outcome for every probe in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `probe_1_e2e_fallback.py` → holds on the patched tree (good)

Attack 2 — `probe_2_fallback_enum.py` → holds on the patched tree (good)

Attack 3 — `probe_3_explicit_secret.py` → holds on the patched tree (good)

Attack 4 — `probe_4_current_secret_untouched.py` → holds on the patched tree (good)

Attack 5 — `probe_5_no_match_flush.py` → holds on the patched tree (good)

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1_e2e_fallback.py`

```python
"""
Positive control + Req 3.2/3.3/3.4/4.1: end-to-end get_user with rotated secret.

A session signed under the OLD secret (now listed in SECRET_KEY_FALLBACKS) must:
 - stay authenticated (return the real user, not anonymous)  [Req 3.2]
 - have its session key rotated (differs from before)        [Req 3.3]
 - have its stored auth hash upgraded to the current secret   [Req 3.4]
 - keep working after the fallback is removed                 [Req 4.1]

HOLDS on patched, FAILS at base (base logs the user out => flush => anonymous).
"""
import django
from django.conf import settings

settings.configure(
    DEBUG=True,
    SECRET_KEY="oldsecret",
    SECRET_KEY_FALLBACKS=[],
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    INSTALLED_APPS=[
        "django.contrib.contenttypes",
        "django.contrib.auth",
        "django.contrib.sessions",
    ],
    AUTHENTICATION_BACKENDS=["django.contrib.auth.backends.ModelBackend"],
    SESSION_ENGINE="django.contrib.sessions.backends.db",
    PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"],
    USE_TZ=True,
)
django.setup()

from django.core.management import call_command
call_command("migrate", run_syncdb=True, verbosity=0)

from django.contrib.auth import get_user, SESSION_KEY, BACKEND_SESSION_KEY, HASH_SESSION_KEY
from django.contrib.auth.models import User, AnonymousUser
from django.contrib.sessions.backends.db import SessionStore
from django.test import override_settings

u = User.objects.create_user("testuser", "t@example.com", "testpw")

# Build a session as if logged in under the OLD secret.
session = SessionStore()
session[SESSION_KEY] = str(u.pk)
session[BACKEND_SESSION_KEY] = "django.contrib.auth.backends.ModelBackend"
session[HASH_SESSION_KEY] = u.get_session_auth_hash()  # under oldsecret
session.save()
prev_key = session.session_key

class Req:
    pass

req = Req()
req.session = session

ok = True
# Rotate secret: oldsecret -> newsecret, oldsecret now a fallback.
with override_settings(SECRET_KEY="newsecret", SECRET_KEY_FALLBACKS=["oldsecret"]):
    user = get_user(req)
    print("after-rotation user:", type(user).__name__, getattr(user, "username", None))
    if not isinstance(user, User) or user.username != "testuser":
        print("FAIL: user not authenticated on fallback")
        import sys; sys.exit(1)
    if req.session.session_key == prev_key:
        print("FAIL: session key NOT rotated", prev_key, req.session.session_key)
        ok = False
    else:
        print("session key rotated OK:", prev_key, "->", req.session.session_key)
    # stored hash should now be the newsecret hash
    new_hash = user.get_session_auth_hash()  # under newsecret
    if req.session.get(HASH_SESSION_KEY) != new_hash:
        print("FAIL: stored hash not upgraded to current secret")
        ok = False
    else:
        print("stored hash upgraded to current secret OK")

# Remove the fallback; current secret is the upgrade secret. Must still work.
with override_settings(SECRET_KEY="newsecret", SECRET_KEY_FALLBACKS=[]):
    user2 = get_user(req)
    print("after-fallback-removal user:", type(user2).__name__, getattr(user2, "username", None))
    if not isinstance(user2, User) or user2.username != "testuser":
        print("FAIL: user not authenticated after fallback removed")
        ok = False

import sys
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Runner env: /testbed, django 5.0.dev, py3.11. All 5 probes HOLD on gold-patched tree. Positive control (probe_1) FAILS at base (base get_user only compares current-secret hash => flush => AnonymousUser). Probe coverage by requirement: probe_1 -> Req3.2/3.3/3.4/4.1 (+ Req5.5 rotation only on fallback); probe_2 -> Req2.1-2.4 & Req1.4 (one hash per fallback, in order, empty when none, each == active-secret hash); probe_3 -> Req1.1-1.4, Req5.1, Req5.4 (explicit-secret computation, sha256 salted_hmac under fixed key_salt, default==current-secret, salted_hmac defaults to SECRET_KEY); probe_4 -> Req3.1 & Req5.5 (current-secret match: authenticated, session key unchanged, stored hash unchanged); probe_5 -> Req3.5 & Req3.6 (bogus hash and missing hash both flush + anonymous). Discrimination demonstrated: candidate weak_noupgrade applies cleanly at base_commit and is REJECTED by probe_1 while probes 2-5 still HOLD, proving the suite distinguishes the requirements-satisfying-but-wrong fixes from the gold behavior on exactly the upgrade/persistence criterion the hidden test exercises.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Requirements pin the actual changed observable behavior across both modified files, not a narrow slice. R1 = _get_session_auth_hash(secret=None) + unchanged default get_session_auth_hash; R2 = get_session_auth_fallback_hash generator yielding one hash per SECRET_KEY_FALLBACKS entry in order (empty=none); R3 = full get_user verification branch (current match leaves session unchanged, fallback match cycle_key+rewrite HASH_SESSION_KEY to current-secret hash, no-match flush->anon, missing hash flush->anon, stop-at-first-match via any()); R4 = upgrade survival; R5 = regression protections (salted_hmac default, missing get_session_auth_hash short-circuit, backend/anon guards, current-match no-mutation). The code's `session.cycle_key()` matches R3.3 'cycle to new key without discarding data'; `request.session[HASH_SESSION_KEY]=session_auth_hash` (current-secret hash) matches R3.4/R4. R3.7 stop-at-first is faithful to Python `any()` short-circuit over the generator. All grounded in patch.diff and live probe.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The document localizes the change by naming public/pre-existing symbols (get_user, get_session_auth_hash, salted_hmac, AbstractBaseUser, SECRET_KEY, SECRET_KEY_FALLBACKS, AUTHENTICATION_BACKENDS) — all present in or directly implied by the public problem_statement and standard Django API; legitimate. Checked all real leak vectors: (1) Fix-invented identifiers get_session_auth_fallback_hash and _get_session_auth_hash are NOT transmitted — the new capability is described only in prose ('a new capability ... to compute the session auth hash under the fallback secrets'). (2) No test names/paths/ids appear (test_basic.py, TestGetUser, test_get_user_fallback_secret absent). (3) No quoted test code or literals (no 'testuser'/'newsecret', no override_settings, no HttpRequest/client.session mechanics). (4) The key_salt string in Req 1.3 and cycle_key are pre-existing codebase content/public API, not hidden-test-derived. (5) Requirements 3.3 (session key differs) and 4 (upgrade survives fallback removal) mirror the test's two assertions but are rendered as intended-fix BEHAVIOR — precisely the upgrade-on-fallback design the public hints_text proposes — not as test parametrization or mechanics. This is legitimate behavior-to-requirement translation, not test reconstruction. The single F2P test is non-parametrized, so no case-enumeration mirroring is possible.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
