# P2 adversarial audit — django__django-16100

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 5 requirement probes hold on the patched tree; 2/2 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 5 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 5 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 2 alternative candidate patches, claimed to satisfy every cited requirement, and ran the same suite against them. The suite rejected all 2: a probe encoding a cited requirement fails under each of those, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (5):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
"""Probe for Requirement 1.5 + 1.3 (positive control):
When one row is saved successfully and then a later row's save sequence raises
(log_change on the 2nd row), ALL rows must roll back to their pre-submission
values. Exit 0 iff both rows retain original values after a DatabaseError.

This is the discriminating leg: HOLDS on patched (atomic), VIOLATED at base
(first row committed independently).
"""
import os, sys
sys.path.insert(0, "/testbed/tests")

import django
from django.conf import settings

if not settings.configured:
    settings.configure(
        DEBUG=False,
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3",
                               "NAME": ":memory:"}},
        INSTALLED_APPS=[
            "django.contrib.admin",
            "django.contrib.auth",
            "django.contrib.contenttypes",
            "django.contrib.sessions",
            "django.contrib.messages",
            "django.contrib.staticfiles",
            "admin_changelist",
        ],
        MIDDLEWARE=[
            "django.contrib.sessions.middleware.SessionMiddleware",
            "django.contrib.auth.middleware.AuthenticationMiddleware",
            "django.contrib.messages.middleware.MessageMiddleware",
        ],
        ROOT_URLCONF="admin_changelist.urls",
        TEMPLATES=[{
            "BACKEND": "django.template.backends.django.DjangoTemplates",
            "DIRS": [],
            "APP_DIRS": True,
            "OPTIONS": {"context_processors": [
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "django.template.context_processors.request",
            ]},
        }],
        STATIC_URL="/static/",
        SECRET_KEY="x",
        USE_TZ=True,
        PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"],
    )
django.setup()

from django.db import connection, DatabaseError
from unittest import mock

# Skip if backend cannot support transactions (criterion is gated on it).
if not connection.features.supports_transactions:
    print("SKIP: backend has no transaction support")
    sys.exit(0)

old_name = connection.creation.create_test_db(verbosity=0, serialize=False)

try:
    from django.contrib.auth.models import User
    from django.urls import reverse
    from django.test import Client
    from admin_changelist.models import Swallow

    superuser = User.objects.create_superuser("super", "s@e.com", "secret")
    a = Swallow.objects.create(origin="Swallow A", load=4, speed=1)
    b = Swallow.objects.create(origin="Swallow B", load=2, speed=2)

    client = Client()
    client.force_login(superuser)
    url = reverse("admin:admin_changelist_swallow_changelist")
    data = {
        "form-TOTAL_FORMS": "2", "form-INITIAL_FORMS": "2",
        "form-MIN_NUM_FORMS": "0", "form-MAX_NUM_FORMS": "1000",
        "form-0-uuid": str(a.pk), "form-1-uuid": str(b.pk),
        "form-0-load": "9.0", "form-0-speed": "3.0",
        "form-1-load": "5.0", "form-1-speed": "1.0",
        "_save": "Save",
    }
    # first call succeeds, second (later row) raises -> must roll back BOTH.
    raised = False
    with mock.patch("django.contrib.admin.ModelAdmin.log_change",
                    side_effect=[None, DatabaseError]):
        try:
            client.post(url, data)
        except DatabaseError:
            raised = True
    a.refresh_from_db(); b.refresh_from_db()
    print(f"raised={raised} a=({a.load},{a.speed}) b=({b.load},{b.speed})")
    ok = raised and a.load == 4 and a.speed == 1 and b.load == 2 and b.speed == 2
    if not ok:
        print("VIOLATION: rows not rolled back / error not raised")
        sys.exit(1)
    print("OK: later-row failure rolled back all earlier rows")
    sys.exit(0)
finally:
    connection.creation.destroy_test_db(old_name, verbosity=0)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
import os, sys
sys.path.insert(0, "/testbed/tests")
import django
from django.conf import settings
if not settings.configured:
    settings.configure(
        DEBUG=False,
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
        INSTALLED_APPS=[
            "django.contrib.admin", "django.contrib.auth",
            "django.contrib.contenttypes", "django.contrib.sessions",
            "django.contrib.messages", "django.contrib.staticfiles",
            "admin_changelist",
        ],
        MIDDLEWARE=[
            "django.contrib.sessions.middleware.SessionMiddleware",
            "django.contrib.auth.middleware.AuthenticationMiddleware",
            "django.contrib.messages.middleware.MessageMiddleware",
        ],
        ROOT_URLCONF="admin_changelist.urls",
        TEMPLATES=[{
            "BACKEND": "django.template.backends.django.DjangoTemplates",
            "DIRS": [], "APP_DIRS": True,
            "OPTIONS": {"context_processors": [
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "django.template.context_processors.request",
            ]},
        }],
        STATIC_URL="/static/", SECRET_KEY="x", USE_TZ=True,
        PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"],
    )
django.setup()
from django.db import connection, DatabaseError
from unittest import mock
if not connection.features.supports_transactions:
    print("SKIP: backend has no transaction support"); sys.exit(0)
old_name = connection.creation.create_test_db(verbosity=0, serialize=False)
from django.contrib.auth.models import User
from django.urls import reverse
from django.test import Client
from admin_changelist.models import Swallow
URL = reverse("admin:admin_changelist_swallow_changelist")
def mkclient():
    su = User.objects.create_superuser("super", "s@e.com", "secret")
    c = Client(); c.force_login(su); return c
def two_swallows():
    a = Swallow.objects.create(origin="Swallow A", load=4, speed=1)
    b = Swallow.objects.create(origin="Swallow B", load=2, speed=2)
    return a, b
def data_for(a, b, l0="9.0", s0="3.0", l1="5.0", s1="1.0"):
    return {
        "form-TOTAL_FORMS": "2", "form-INITIAL_FORMS": "2",
        "form-MIN_NUM_FORMS": "0", "form-MAX_NUM_FORMS": "1000",
        "form-0-uuid": str(a.pk), "form-1-uuid": str(b.pk),
        "form-0-load": l0, "form-0-speed": s0,
        "form-1-load": l1, "form-1-speed": s1,
        "_save": "Save",
    }
try:
    c = mkclient(); a, b = two_swallows()
    raised = False
    with mock.patch("django.contrib.admin.ModelAdmin.log_change", side_effect=DatabaseError):
        try:
            c.post(URL, data_for(a, b))
        except DatabaseError:
            raised = True
    a.refresh_from_db(); b.refresh_from_db()
    print(f"raised={raised} a=({a.load},{a.speed}) b=({b.load},{b.speed})")
    ok = raised and a.load==4 and a.speed==1 and b.load==2 and b.speed==2
    if not ok:
        print("VIOLATION: first-row error did not leave all rows unchanged"); sys.exit(1)
    print("OK: first-row failure left all rows at pre-submission values"); sys.exit(0)
finally:
    connection.creation.destroy_test_db(old_name, verbosity=0)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
import os, sys
sys.path.insert(0, "/testbed/tests")
import django
from django.conf import settings
if not settings.configured:
    settings.configure(
        DEBUG=False,
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
        INSTALLED_APPS=[
            "django.contrib.admin", "django.contrib.auth",
            "django.contrib.contenttypes", "django.contrib.sessions",
            "django.contrib.messages", "django.contrib.staticfiles",
            "admin_changelist",
        ],
        MIDDLEWARE=[
            "django.contrib.sessions.middleware.SessionMiddleware",
            "django.contrib.auth.middleware.AuthenticationMiddleware",
            "django.contrib.messages.middleware.MessageMiddleware",
        ],
        ROOT_URLCONF="admin_changelist.urls",
        TEMPLATES=[{
            "BACKEND": "django.template.backends.django.DjangoTemplates",
            "DIRS": [], "APP_DIRS": True,
            "OPTIONS": {"context_processors": [
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "django.template.context_processors.request",
            ]},
        }],
        STATIC_URL="/static/", SECRET_KEY="x", USE_TZ=True,
        PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"],
    )
django.setup()
from django.db import connection, DatabaseError
from unittest import mock
if not connection.features.supports_transactions:
    print("SKIP: backend has no transaction support"); sys.exit(0)
old_name = connection.creation.create_test_db(verbosity=0, serialize=False)
from django.contrib.auth.models import User
from django.urls import reverse
from django.test import Client
from admin_changelist.models import Swallow
URL = reverse("admin:admin_changelist_swallow_changelist")
def mkclient():
    su = User.objects.create_superuser("super", "s@e.com", "secret")
    c = Client(); c.force_login(su); return c
def two_swallows():
    a = Swallow.objects.create(origin="Swallow A", load=4, speed=1)
    b = Swallow.objects.create(origin="Swallow B", load=2, speed=2)
    return a, b
def data_for(a, b, l0="9.0", s0="3.0", l1="5.0", s1="1.0"):
    return {
        "form-TOTAL_FORMS": "2", "form-INITIAL_FORMS": "2",
        "form-MIN_NUM_FORMS": "0", "form-MAX_NUM_FORMS": "1000",
        "form-0-uuid": str(a.pk), "form-1-uuid": str(b.pk),
        "form-0-load": l0, "form-0-speed": s0,
        "form-1-load": l1, "form-1-speed": s1,
        "_save": "Save",
    }
try:
    c = mkclient(); a, b = two_swallows()
    raised = False; resp = None
    with mock.patch("django.contrib.admin.ModelAdmin.log_change", side_effect=[None, DatabaseError]):
        try:
            resp = c.post(URL, data_for(a, b))
        except DatabaseError:
            raised = True
    # Requirement 2.1: error must propagate (not swallowed / no 200-success page).
    # Requirement 2.2: must NOT report "changed successfully".
    reported_success = False
    if resp is not None:
        body = resp.content.decode("utf-8", "replace").lower() if hasattr(resp, "content") else ""
        reported_success = "changed successfully" in body
    print(f"raised={raised} resp={resp!r} reported_success={reported_success}")
    if not raised:
        print("VIOLATION: DatabaseError was swallowed, not propagated"); sys.exit(1)
    if reported_success:
        print("VIOLATION: reported changed-successfully despite failure"); sys.exit(1)
    print("OK: error propagated and no success reported"); sys.exit(0)
finally:
    connection.creation.destroy_test_db(old_name, verbosity=0)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
import os, sys
sys.path.insert(0, "/testbed/tests")
import django
from django.conf import settings
if not settings.configured:
    settings.configure(
        DEBUG=False,
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
        INSTALLED_APPS=[
            "django.contrib.admin", "django.contrib.auth",
            "django.contrib.contenttypes", "django.contrib.sessions",
            "django.contrib.messages", "django.contrib.staticfiles",
            "admin_changelist",
        ],
        MIDDLEWARE=[
            "django.contrib.sessions.middleware.SessionMiddleware",
            "django.contrib.auth.middleware.AuthenticationMiddleware",
            "django.contrib.messages.middleware.MessageMiddleware",
        ],
        ROOT_URLCONF="admin_changelist.urls",
        TEMPLATES=[{
            "BACKEND": "django.template.backends.django.DjangoTemplates",
            "DIRS": [], "APP_DIRS": True,
            "OPTIONS": {"context_processors": [
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "django.template.context_processors.request",
            ]},
        }],
        STATIC_URL="/static/", SECRET_KEY="x", USE_TZ=True,
        PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"],
    )
django.setup()
from django.db import connection, DatabaseError
from unittest import mock
if not connection.features.supports_transactions:
    print("SKIP: backend has no transaction support"); sys.exit(0)
old_name = connection.creation.create_test_db(verbosity=0, serialize=False)
from django.contrib.auth.models import User
from django.urls import reverse
from django.test import Client
from admin_changelist.models import Swallow
URL = reverse("admin:admin_changelist_swallow_changelist")
def mkclient():
    su = User.objects.create_superuser("super", "s@e.com", "secret")
    c = Client(); c.force_login(su); return c
def two_swallows():
    a = Swallow.objects.create(origin="Swallow A", load=4, speed=1)
    b = Swallow.objects.create(origin="Swallow B", load=2, speed=2)
    return a, b
def data_for(a, b, l0="9.0", s0="3.0", l1="5.0", s1="1.0"):
    return {
        "form-TOTAL_FORMS": "2", "form-INITIAL_FORMS": "2",
        "form-MIN_NUM_FORMS": "0", "form-MAX_NUM_FORMS": "1000",
        "form-0-uuid": str(a.pk), "form-1-uuid": str(b.pk),
        "form-0-load": l0, "form-0-speed": s0,
        "form-1-load": l1, "form-1-speed": s1,
        "_save": "Save",
    }
from django.contrib.admin.models import LogEntry
try:
    c = mkclient(); a, b = two_swallows()
    n0 = LogEntry.objects.count()
    resp = c.post(URL, data_for(a, b))
    a.refresh_from_db(); b.refresh_from_db()
    n1 = LogEntry.objects.count()
    status = getattr(resp, "status_code", None)
    print(f"status={status} a=({a.load},{a.speed}) b=({b.load},{b.speed}) logentries_added={n1-n0}")
    ok = (status == 302 and a.load==9 and a.speed==3 and b.load==5 and b.speed==1
          and (n1-n0) == 2)
    if not ok:
        print("VIOLATION: normal bulk edit did not save/log/redirect as before"); sys.exit(1)
    print("OK: both rows saved, 2 log entries recorded, redirected (302)"); sys.exit(0)
finally:
    connection.creation.destroy_test_db(old_name, verbosity=0)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
import os, sys
sys.path.insert(0, "/testbed/tests")
import django
from django.conf import settings
if not settings.configured:
    settings.configure(
        DEBUG=False,
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
        INSTALLED_APPS=[
            "django.contrib.admin", "django.contrib.auth",
            "django.contrib.contenttypes", "django.contrib.sessions",
            "django.contrib.messages", "django.contrib.staticfiles",
            "admin_changelist",
        ],
        MIDDLEWARE=[
            "django.contrib.sessions.middleware.SessionMiddleware",
            "django.contrib.auth.middleware.AuthenticationMiddleware",
            "django.contrib.messages.middleware.MessageMiddleware",
        ],
        ROOT_URLCONF="admin_changelist.urls",
        TEMPLATES=[{
            "BACKEND": "django.template.backends.django.DjangoTemplates",
            "DIRS": [], "APP_DIRS": True,
            "OPTIONS": {"context_processors": [
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "django.template.context_processors.request",
            ]},
        }],
        STATIC_URL="/static/", SECRET_KEY="x", USE_TZ=True,
        PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"],
    )
django.setup()
from django.db import connection, DatabaseError
from unittest import mock
if not connection.features.supports_transactions:
    print("SKIP: backend has no transaction support"); sys.exit(0)
old_name = connection.creation.create_test_db(verbosity=0, serialize=False)
from django.contrib.auth.models import User
from django.urls import reverse
from django.test import Client
from admin_changelist.models import Swallow
URL = reverse("admin:admin_changelist_swallow_changelist")
def mkclient():
    su = User.objects.create_superuser("super", "s@e.com", "secret")
    c = Client(); c.force_login(su); return c
def two_swallows():
    a = Swallow.objects.create(origin="Swallow A", load=4, speed=1)
    b = Swallow.objects.create(origin="Swallow B", load=2, speed=2)
    return a, b
def data_for(a, b, l0="9.0", s0="3.0", l1="5.0", s1="1.0"):
    return {
        "form-TOTAL_FORMS": "2", "form-INITIAL_FORMS": "2",
        "form-MIN_NUM_FORMS": "0", "form-MAX_NUM_FORMS": "1000",
        "form-0-uuid": str(a.pk), "form-1-uuid": str(b.pk),
        "form-0-load": l0, "form-0-speed": s0,
        "form-1-load": l1, "form-1-speed": s1,
        "_save": "Save",
    }
from django.contrib.admin.models import LogEntry
try:
    c = mkclient(); a, b = two_swallows()
    n0 = LogEntry.objects.count()
    # b submitted with its ORIGINAL values -> unchanged; only a changes.
    resp = c.post(URL, data_for(a, b, l0="9.0", s0="3.0", l1="2.0", s1="2.0"))
    a.refresh_from_db(); b.refresh_from_db()
    n1 = LogEntry.objects.count()
    status = getattr(resp, "status_code", None)
    added = n1 - n0
    print(f"status={status} a=({a.load},{a.speed}) b=({b.load},{b.speed}) logentries_added={added}")
    # a changed and saved; b unchanged -> exactly one row processed.
    ok = (status == 302 and a.load==9 and a.speed==3 and b.load==2 and b.speed==2 and added == 1)
    if not ok:
        print("VIOLATION: unchanged row was processed/counted, or changed row not saved"); sys.exit(1)
    print("OK: only the changed row was saved+logged; unchanged row untouched"); sys.exit(0)
finally:
    connection.creation.destroy_test_db(old_name, verbosity=0)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Probe for Requirement 1.5 + 1.3 (positive control):
When one row is saved successfully and then a later row's save sequence raises
(log_change on the 2nd row), ALL rows must roll back to their pre-submission
values. Exit 0 iff both rows retain original values after a DatabaseError.

This is the discriminating leg: HOLDS on patched (atomic), VIOLATED at base
(first row committed independently).
"""
import os, sys
sys.path.insert(0, "/testbed/tests")

import django
from django.conf import settings

if not settings.configured:
    settings.configure(
        DEBUG=False,
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3",
                               "NAME": ":memory:"}},
        INSTALLED_APPS=[
            "django.contrib.admin",
            "django.contrib.auth",
            "django.contrib.contenttypes",
            "django.contrib.sessions",
            "django.contrib.messages",
            "django.contrib.staticfiles",
            "admin_changelist",
        ],
        MIDDLEWARE=[
            "django.contrib.sessions.middleware.SessionMiddleware",
            "django.contrib.auth.middleware.AuthenticationMiddleware",
            "django.contrib.messages.middleware.MessageMiddleware",
        ],
        ROOT_URLCONF="admin_changelist.urls",
        TEMPLATES=[{
            "BACKEND": "django.template.backends.django.DjangoTemplates",
            "DIRS": [],
            "APP_DIRS": True,
            "OPTIONS": {"context_processors": [
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "django.template.context_processors.request",
            ]},
        }],
        STATIC_URL="/static/",
        SECRET_KEY="x",
        USE_TZ=True,
        PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"],
    )
django.setup()

from django.db import connection, DatabaseError
from unittest import mock

# Skip if backend cannot support transactions (criterion is gated on it).
if not connection.features.supports_transactions:
    print("SKIP: backend has no transaction support")
    sys.exit(0)

old_name = connection.creation.create_test_db(verbosity=0, serialize=False)

try:
    from django.contrib.auth.models import User
    from django.urls import reverse
    from django.test import Client
    from admin_changelist.models import Swallow

    superuser = User.objects.create_superuser("super", "s@e.com", "secret")
    a = Swallow.objects.create(origin="Swallow A", load=4, speed=1)
    b = Swallow.objects.create(origin="Swallow B", load=2, speed=2)

    client = Client()
    client.force_login(superuser)
    url = reverse("admin:admin_changelist_swallow_changelist")
    data = {
        "form-TOTAL_FORMS": "2", "form-INITIAL_FORMS": "2",
        "form-MIN_NUM_FORMS": "0", "form-MAX_NUM_FORMS": "1000",
        "form-0-uuid": str(a.pk), "form-1-uuid": str(b.pk),
        "form-0-load": "9.0", "form-0-speed": "3.0",
        "form-1-load": "5.0", "form-1-speed": "1.0",
        "_save": "Save",
    }
    # first call succeeds, second (later row) raises -> must roll back BOTH.
    raised = False
    with mock.patch("django.contrib.admin.ModelAdmin.log_change",
                    side_effect=[None, DatabaseError]):
        try:
            client.post(url, data)
        except DatabaseError:
            raised = True
    a.refresh_from_db(); b.refresh_from_db()
    print(f"raised={raised} a=({a.load},{a.speed}) b=({b.load},{b.speed})")
    ok = raised and a.load == 4 and a.speed == 1 and b.load == 2 and b.speed == 2
    if not ok:
        print("VIOLATION: rows not rolled back / error not raised")
        sys.exit(1)
    print("OK: later-row failure rolled back all earlier rows")
    sys.exit(0)
finally:
    connection.creation.destroy_test_db(old_name, verbosity=0)
```

Prepatch bug re-encoded as an attack: `True`.

Instance: transaction handling for admin changelist list_editable bulk save. Gold wraps the per-row save loop in a single transaction.atomic(using=router.db_for_write(self.model)).

Probes (all run in the official image; grepped out git-apply noise):
- probe_1 = POSITIVE CONTROL (Req 1.5 + 1.3): two rows changed; log_change side_effect=[None, DatabaseError] fails the SECOND row. Requires BOTH rows to roll back to pre-submission (a=4,1 / b=2,2). HOLDS patched (a=(4,1) b=(2,2)); VIOLATED at base (a=(9,3) b=(5,1) — first row committed independently). Discriminates.
- probe_2 (Req 1.4): first-row error (log_change=DatabaseError) leaves all rows unchanged. HOLDS patched.
- probe_3 (Req 2.1 + 2.2): later-row error must PROPAGATE (DatabaseError raised out of POST) and NOT report changed-successfully. HOLDS patched (raised, no response).
- probe_4 (Req 3.1 + 3.2 regression): normal error-free bulk edit saves both rows, records exactly 2 LogEntry rows, redirects 302. HOLDS patched.
- probe_5 (Req 3.4 regression): row submitted with unchanged values is NOT saved/logged/counted; only the changed row processed (1 LogEntry, 302). HOLDS patched.

All 5 probes HOLD on the gold-patched tree.

Candidate wrong patches (both apply at base_commit):
- perrow.diff: naive per-row atomic (transaction.atomic INSIDE the loop, per row). A weak reading of Req1 ('within a database transaction') permits this. REJECTED by probe_1 (later-row failure leaves the first row committed: a=(9,3)) while still passing probe_4 — proving the suite discriminates the cross-row-rollback requirement (Req 1.5), not just 'some transaction'.
- swallow.diff: whole-loop atomic but wrapped in try/except Exception that resets changecount. Atomic rollback happens, but REJECTED by probe_3 (error swallowed, returns 302 instead of propagating) — enforces Req 2.1/2.2.

No requirements-conforming candidate found that fails the hidden test; both wrong candidates are caught by the probe suite. Verdict SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 5 requirement probes hold on the patched tree; 2/2 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 5 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 5 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 2 alternative candidate patches, claimed to satisfy every cited requirement, and ran the same suite against them. The suite rejected all 2: a probe encoding a cited requirement fails under each of those, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (5):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

_The 5 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts, and on this backend both roles put it through the same derivation: every block below is a requirement probe run on the gold-patched tree, and the `machine verdict:` line each role publishes above reports BOTH that its probes hold there and how many candidate patches the probe suite rejected — so the two roles re-ran ONE probe suite and each recorded its own outcome for every probe in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `probe_1.py` → holds on the patched tree (good)

Attack 2 — `probe_2.py` → holds on the patched tree (good)

Attack 3 — `probe_3.py` → holds on the patched tree (good)

Attack 4 — `probe_4.py` → holds on the patched tree (good)

Attack 5 — `probe_5.py` → holds on the patched tree (good)

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Probe for Requirement 1.5 + 1.3 (positive control):
When one row is saved successfully and then a later row's save sequence raises
(log_change on the 2nd row), ALL rows must roll back to their pre-submission
values. Exit 0 iff both rows retain original values after a DatabaseError.

This is the discriminating leg: HOLDS on patched (atomic), VIOLATED at base
(first row committed independently).
"""
import os, sys
sys.path.insert(0, "/testbed/tests")

import django
from django.conf import settings

if not settings.configured:
    settings.configure(
        DEBUG=False,
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3",
                               "NAME": ":memory:"}},
        INSTALLED_APPS=[
            "django.contrib.admin",
            "django.contrib.auth",
            "django.contrib.contenttypes",
            "django.contrib.sessions",
            "django.contrib.messages",
            "django.contrib.staticfiles",
            "admin_changelist",
        ],
        MIDDLEWARE=[
            "django.contrib.sessions.middleware.SessionMiddleware",
            "django.contrib.auth.middleware.AuthenticationMiddleware",
            "django.contrib.messages.middleware.MessageMiddleware",
        ],
        ROOT_URLCONF="admin_changelist.urls",
        TEMPLATES=[{
            "BACKEND": "django.template.backends.django.DjangoTemplates",
            "DIRS": [],
            "APP_DIRS": True,
            "OPTIONS": {"context_processors": [
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "django.template.context_processors.request",
            ]},
        }],
        STATIC_URL="/static/",
        SECRET_KEY="x",
        USE_TZ=True,
        PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"],
    )
django.setup()

from django.db import connection, DatabaseError
from unittest import mock

# Skip if backend cannot support transactions (criterion is gated on it).
if not connection.features.supports_transactions:
    print("SKIP: backend has no transaction support")
    sys.exit(0)

old_name = connection.creation.create_test_db(verbosity=0, serialize=False)

try:
    from django.contrib.auth.models import User
    from django.urls import reverse
    from django.test import Client
    from admin_changelist.models import Swallow

    superuser = User.objects.create_superuser("super", "s@e.com", "secret")
    a = Swallow.objects.create(origin="Swallow A", load=4, speed=1)
    b = Swallow.objects.create(origin="Swallow B", load=2, speed=2)

    client = Client()
    client.force_login(superuser)
    url = reverse("admin:admin_changelist_swallow_changelist")
    data = {
        "form-TOTAL_FORMS": "2", "form-INITIAL_FORMS": "2",
        "form-MIN_NUM_FORMS": "0", "form-MAX_NUM_FORMS": "1000",
        "form-0-uuid": str(a.pk), "form-1-uuid": str(b.pk),
        "form-0-load": "9.0", "form-0-speed": "3.0",
        "form-1-load": "5.0", "form-1-speed": "1.0",
        "_save": "Save",
    }
    # first call succeeds, second (later row) raises -> must roll back BOTH.
    raised = False
    with mock.patch("django.contrib.admin.ModelAdmin.log_change",
                    side_effect=[None, DatabaseError]):
        try:
            client.post(url, data)
        except DatabaseError:
            raised = True
    a.refresh_from_db(); b.refresh_from_db()
    print(f"raised={raised} a=({a.load},{a.speed}) b=({b.load},{b.speed})")
    ok = raised and a.load == 4 and a.speed == 1 and b.load == 2 and b.speed == 2
    if not ok:
        print("VIOLATION: rows not rolled back / error not raised")
        sys.exit(1)
    print("OK: later-row failure rolled back all earlier rows")
    sys.exit(0)
finally:
    connection.creation.destroy_test_db(old_name, verbosity=0)
```

Prepatch bug re-encoded as an attack: `True`.

Instance: transaction handling for admin changelist list_editable bulk save. Gold wraps the per-row save loop in a single transaction.atomic(using=router.db_for_write(self.model)).

Probes (all run in the official image; grepped out git-apply noise):
- probe_1 = POSITIVE CONTROL (Req 1.5 + 1.3): two rows changed; log_change side_effect=[None, DatabaseError] fails the SECOND row. Requires BOTH rows to roll back to pre-submission (a=4,1 / b=2,2). HOLDS patched (a=(4,1) b=(2,2)); VIOLATED at base (a=(9,3) b=(5,1) — first row committed independently). Discriminates.
- probe_2 (Req 1.4): first-row error (log_change=DatabaseError) leaves all rows unchanged. HOLDS patched.
- probe_3 (Req 2.1 + 2.2): later-row error must PROPAGATE (DatabaseError raised out of POST) and NOT report changed-successfully. HOLDS patched (raised, no response).
- probe_4 (Req 3.1 + 3.2 regression): normal error-free bulk edit saves both rows, records exactly 2 LogEntry rows, redirects 302. HOLDS patched.
- probe_5 (Req 3.4 regression): row submitted with unchanged values is NOT saved/logged/counted; only the changed row processed (1 LogEntry, 302). HOLDS patched.

All 5 probes HOLD on the gold-patched tree.

Candidate wrong patches (both apply at base_commit):
- perrow.diff: naive per-row atomic (transaction.atomic INSIDE the loop, per row). A weak reading of Req1 ('within a database transaction') permits this. REJECTED by probe_1 (later-row failure leaves the first row committed: a=(9,3)) while still passing probe_4 — proving the suite discriminates the cross-row-rollback requirement (Req 1.5), not just 'some transaction'.
- swallow.diff: whole-loop atomic but wrapped in try/except Exception that resets changecount. Atomic rollback happens, but REJECTED by probe_3 (error swallowed, returns 302 instead of propagating) — enforces Req 2.1/2.2.

No requirements-conforming candidate found that fails the hidden test; both wrong candidates are caught by the probe suite. Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Probe confirmed: patched ModelAdmin.changelist_view source contains `transaction.atomic(using=router.db_for_write(self.model))` before the `for form in formset.forms` loop, with all per-row ops (save_form, save_model, save_related, construct_change_message, log_change, changecount += 1) still inside; base_commit lacks the atomic scoping (probe exit != 0 at --base). Clean discriminator; modeling boundary = the changed observable (transactional bulk save), not a narrow branch or helper.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The requirements describe wrapping the list_editable bulk-save loop in a single database transaction (transaction.atomic scoped to router.db_for_write) so the per-row writes are all-or-nothing. This is fully derivable from the PUBLIC problem_statement ('Add transaction handling to Changelist list_editable processing... wrapped in a transaction to prevent unexpected states in case of errors'). Naming changelist_view / options.py and the per-row save sequence (save object, save related, log_change) is legitimate localization matching the gold patch scope. No hidden-test content is transmitted: no test name (test_list_editable_atomicity), no path (tests/admin_changelist/tests.py), no Swallow model, no skipUnlessDBFeature('supports_transactions'), no DatabaseError/mock.patch failure mechanism, no form field values (load/speed/uuid), and log_change is never singled out as the injected failure point. Criteria 4 & 5 (fail on first row vs. fail on a later row after successes) are the natural logical decomposition of atomicity stated as behavior, not a mirror of the test's two side_effect parametrizations. Standard Django APIs are described behaviorally, not quoted as gold code.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
