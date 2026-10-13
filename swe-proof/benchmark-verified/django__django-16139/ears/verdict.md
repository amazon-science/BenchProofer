# P2 adversarial audit — django__django-16139

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
"""Probe 1 (POSITIVE CONTROL) — Requirement 1, criteria 1/2/3.

The password help-text link, resolved against a change-form URL reached via a
to_field value that is NOT the pk, SHALL equal the admin password-change URL
keyed by the user's own primary key.

Holds on gold (href="../../<pk>/password/"), fails at base (href="../password/").
"""
import re
import urllib.parse
import django
from django.conf import settings

settings.configure(
    DEBUG=True,
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3",
                           "NAME": ":memory:"}},
    INSTALLED_APPS=[
        "django.contrib.contenttypes",
        "django.contrib.auth",
    ],
    USE_TZ=True,
    AUTH_USER_MODEL="auth.User",
)
django.setup()

from django.core.management import call_command
call_command("migrate", run_syncdb=True, verbosity=0)

from django.contrib.auth.forms import UserChangeForm
from django.contrib.auth.models import User

user = User.objects.create(username="testclient", password="x")
PK = user.pk
form = UserChangeForm(instance=user)
help_text = form.fields["password"].help_text
print("help_text:", help_text)

m = re.search(r'<a href="(.*?)">', help_text)
assert m, "no anchor href found in help text"
href = m.group(1)
print("href:", href)

# Change-form URL reached via to_field=uuid/username (NOT the pk):
change_url = "/admin/auth/user/testclient/change/"
resolved = urllib.parse.urljoin(change_url, href)
print("resolved:", resolved)

# The correct password-change URL is keyed by the primary key:
expected = "/admin/auth/user/%s/password/" % PK
print("expected:", expected)

if resolved != expected:
    print("VIOLATION: resolved link does not point at pk-keyed password URL")
    raise SystemExit(1)
print("OK: resolved link points at pk-keyed password URL")
raise SystemExit(0)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""Probe 2 — Requirement 1 criterion 4 (common case regression).

WHEN the change form is reached by pk in the ordinary way, the resolved
password link SHALL still point at the pk-keyed password-change form.
"""
import re, urllib.parse, django
from django.conf import settings
settings.configure(DEBUG=True,
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
    USE_TZ=True, AUTH_USER_MODEL="auth.User")
django.setup()
from django.core.management import call_command
call_command("migrate", run_syncdb=True, verbosity=0)
from django.contrib.auth.forms import UserChangeForm
from django.contrib.auth.models import User

user = User.objects.create(username="alice", password="x")
form = UserChangeForm(instance=user)
href = re.search(r'<a href="(.*?)">', form.fields["password"].help_text).group(1)
change_url = "/admin/auth/user/%s/change/" % user.pk   # reached BY PK
resolved = urllib.parse.urljoin(change_url, href)
expected = "/admin/auth/user/%s/password/" % user.pk
print("href:", href, "resolved:", resolved, "expected:", expected)
if resolved != expected:
    print("VIOLATION: common (pk) case broken")
    raise SystemExit(1)
print("OK: common (pk) case resolves correctly")
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""Probe 3 — Requirement 2 criterion 1 (help text structure preserved).

Help text SHALL render as human-readable guidance containing EXACTLY ONE
HTML anchor, with the surrounding template wording otherwise unchanged (only
the placeholder filled). Also checks the anchor text is 'this form'.
"""
import re, django
from django.conf import settings
settings.configure(DEBUG=True,
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
    USE_TZ=True, AUTH_USER_MODEL="auth.User")
django.setup()
from django.core.management import call_command
call_command("migrate", run_syncdb=True, verbosity=0)
from django.contrib.auth.forms import UserChangeForm
from django.contrib.auth.models import User

user = User.objects.create(username="bob", password="x")
help_text = form_ht = UserChangeForm(instance=user).fields["password"].help_text
print("help_text:", help_text)

anchors = re.findall(r'<a href="[^"]*">.*?</a>', help_text)
print("num anchors:", len(anchors))
ok = True
if len(anchors) != 1:
    print("VIOLATION: expected exactly one anchor"); ok = False
# surrounding wording preserved
if "Raw passwords are not stored" not in help_text:
    print("VIOLATION: leading wording changed"); ok = False
if "this form" not in help_text:
    print("VIOLATION: anchor text/wording changed"); ok = False
# no stray unfilled placeholder
if "{}" in help_text or "{0}" in help_text:
    print("VIOLATION: placeholder left unfilled"); ok = False
if not ok:
    raise SystemExit(1)
print("OK: help text has exactly one anchor, wording preserved")
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""Probe 4 — Requirement 2 criterion 2 (no password field => no error).

WHEN UserChangeForm is initialized and no password field is present (a subclass
excludes it), initialization SHALL complete without error and SHALL NOT attempt
to fill the help-text placeholder.
"""
import django
from django.conf import settings
settings.configure(DEBUG=True,
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
    USE_TZ=True, AUTH_USER_MODEL="auth.User")
django.setup()
from django.core.management import call_command
call_command("migrate", run_syncdb=True, verbosity=0)
from django.contrib.auth.forms import UserChangeForm
from django.contrib.auth.models import User

# Drop the declared password field AND restrict Meta.fields so it is truly
# absent from the form — a genuine "no password field" subclass.
class NoPwForm(UserChangeForm):
    password = None
    class Meta(UserChangeForm.Meta):
        fields = ("username",)

user = User.objects.create(username="carol", password="x")
try:
    form = NoPwForm(instance=user)
except Exception as e:
    print("VIOLATION: init raised when password field absent:", repr(e))
    raise SystemExit(1)
present = "password" in form.fields
print("password field present:", present)
if present:
    print("VIOLATION: password field not actually removed; guard untested")
    raise SystemExit(1)
print("OK: init completed without error when password field absent")
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""Probe 5 — Requirement 2 criteria 3 & 4 (read-only password + queryset opt).

- The password is a read-only value never returned as an editable password:
  clean_password() returns the INITIAL value regardless of submitted data.
- initial password value is available for correct rendering.
- user_permissions queryset is optimized with select_related(content_type).
- username field unchanged (present).
"""
import django
from django.conf import settings
settings.configure(DEBUG=True,
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
    USE_TZ=True, AUTH_USER_MODEL="auth.User")
django.setup()
from django.core.management import call_command
call_command("migrate", run_syncdb=True, verbosity=0)
from django.contrib.auth.forms import UserChangeForm
from django.contrib.auth.models import User

user = User.objects.create(username="dave")
user.set_password("s3cret")
user.save()
initial_hash = user.password

# read-only password: submitting a different value must NOT change it.
# ReadOnlyPasswordHashField is disabled and bound_data returns the initial,
# so the field never surfaces the attacker-submitted value.
form = UserChangeForm(data={"username": "dave", "password": "attacker-supplied"},
                      instance=user)
ok = True
pw_field = form.fields["password"]
if not getattr(pw_field, "disabled", False):
    print("VIOLATION: password field not disabled/read-only"); ok = False
bound = pw_field.bound_data("attacker-supplied", initial_hash)
print("bound_data ->", bound)
if bound != initial_hash:
    print("VIOLATION: password not read-only (bound_data ignored initial)"); ok = False

# initial value available for rendering
print("initial password:", form.initial.get("password"))
if form.initial.get("password") != initial_hash:
    print("VIOLATION: initial password not available"); ok = False

# username field present/unchanged
if "username" not in form.fields:
    print("VIOLATION: username field missing"); ok = False

# user_permissions queryset optimized via select_related(content_type)
qs = form.fields["user_permissions"].queryset
sr = qs.query.select_related
print("user_permissions select_related:", sr)
if not (sr and "content_type" in sr):
    print("VIOLATION: user_permissions queryset not select_related(content_type)"); ok = False

if not ok:
    raise SystemExit(1)
print("OK: read-only password, initial available, username present, qs optimized")
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
"""Probe 6 — Requirement 1 criterion 3 (climbs out AND re-descends by pk).

The relative URL SHALL NOT assume the current change-form segment already
identifies the user by pk: it must climb out of the current record segment and
re-descend through the pk record. Encoded structurally + behaviorally:

- The href must be a relative path that, applied to a change-form URL whose
  record segment is an ARBITRARY to_field value (uuid), yields the pk-keyed
  password URL — i.e. the record segment in the result is the pk, not the uuid.
- A link of the naive shape '../password/' (which merely swaps the trailing
  segment, keeping the record segment) must NOT satisfy this.
"""
import re, urllib.parse, django
from django.conf import settings
settings.configure(DEBUG=True,
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
    USE_TZ=True, AUTH_USER_MODEL="auth.User")
django.setup()
from django.core.management import call_command
call_command("migrate", run_syncdb=True, verbosity=0)
from django.contrib.auth.forms import UserChangeForm
from django.contrib.auth.models import User

user = User.objects.create(username="erin", password="x")
pk = user.pk
href = re.search(r'<a href="(.*?)">', UserChangeForm(instance=user).fields["password"].help_text).group(1)
print("href:", href, "pk:", pk)

uuid = "22222222-3333-4444-5555-666677778888"
change_url = "/admin/auth/user/%s/change/" % uuid
resolved = urllib.parse.urljoin(change_url, href)
print("resolved from uuid-url:", resolved)

expected = "/admin/auth/user/%s/password/" % pk
if resolved != expected:
    print("VIOLATION: link did not re-descend by pk (got", resolved, ")")
    raise SystemExit(1)
# and the uuid must not survive in the path
if uuid in resolved:
    print("VIOLATION: uuid segment survived in resolved URL")
    raise SystemExit(1)
print("OK: link climbs out and re-descends through pk record")
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Probe 1 (POSITIVE CONTROL) — Requirement 1, criteria 1/2/3.

The password help-text link, resolved against a change-form URL reached via a
to_field value that is NOT the pk, SHALL equal the admin password-change URL
keyed by the user's own primary key.

Holds on gold (href="../../<pk>/password/"), fails at base (href="../password/").
"""
import re
import urllib.parse
import django
from django.conf import settings

settings.configure(
    DEBUG=True,
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3",
                           "NAME": ":memory:"}},
    INSTALLED_APPS=[
        "django.contrib.contenttypes",
        "django.contrib.auth",
    ],
    USE_TZ=True,
    AUTH_USER_MODEL="auth.User",
)
django.setup()

from django.core.management import call_command
call_command("migrate", run_syncdb=True, verbosity=0)

from django.contrib.auth.forms import UserChangeForm
from django.contrib.auth.models import User

user = User.objects.create(username="testclient", password="x")
PK = user.pk
form = UserChangeForm(instance=user)
help_text = form.fields["password"].help_text
print("help_text:", help_text)

m = re.search(r'<a href="(.*?)">', help_text)
assert m, "no anchor href found in help text"
href = m.group(1)
print("href:", href)

# Change-form URL reached via to_field=uuid/username (NOT the pk):
change_url = "/admin/auth/user/testclient/change/"
resolved = urllib.parse.urljoin(change_url, href)
print("resolved:", resolved)

# The correct password-change URL is keyed by the primary key:
expected = "/admin/auth/user/%s/password/" % PK
print("expected:", expected)

if resolved != expected:
    print("VIOLATION: resolved link does not point at pk-keyed password URL")
    raise SystemExit(1)
print("OK: resolved link points at pk-keyed password URL")
raise SystemExit(0)
```

Prepatch bug re-encoded as an attack: `True`.

Instance django__django-16139: UserChangeForm password help-text link must resolve to the pk-keyed password-change URL even when the change form is reached via a to_field (non-pk) value. Gold fix: help_text.format(f'../../{self.instance.pk}/password/').

Probes (all HOLD on gold-patched tree; runner re-runs):
- probe_1 (POSITIVE CONTROL, Req1 c1/c2/c3): href resolved against a to_field(username)-keyed change URL == /admin/auth/user/<pk>/password/. HOLDS patched, VIOLATED at base (base gives ../password/ -> .../testclient/password/). Discriminates.
- probe_2 (Req1 c4): common pk-keyed change URL still resolves to pk-keyed password URL. HOLDS.
- probe_3 (Req2 c1): help text preserves surrounding wording, exactly one <a> anchor, no unfilled placeholder. HOLDS.
- probe_4 (Req2 c2): subclass with password=None + Meta.fields=('username',) — no password field — inits without error and doesn't touch placeholder. HOLDS both trees (guard is a regression invariant, not a fixed behavior).
- probe_5 (Req2 c3/c4): password field disabled/read-only (bound_data returns initial), initial password available, username present, user_permissions queryset select_related('content_type'). HOLDS.
- probe_6 (Req1 c3): link climbs out AND re-descends by pk — resolving against an arbitrary uuid change URL yields the pk password URL and the uuid does NOT survive. HOLDS patched.

Candidate wrong-fix candA (naive one-level climb f'../{pk}/password/'): REJECTED by probes 1, 2 and 6 (yields .../testclient/1/password/ or .../1/1/password/, keeping the record segment instead of replacing it). Demonstrates the suite discriminates a plausible weak fix. No requirements-conforming alternative patch was found that fails the hidden test — the biconditional pk-keyed resolution probes (1/2/6) pin the exact fixed behavior.

Environment note: probes bootstrap Django with an in-memory sqlite DB + migrate run_syncdb (needed because UserChangeForm.__init__ touches the user_permissions queryset and User creation). Ran on the official instance image via nl_attack.

Verdict SOUND: >=6 distinct probes covering Req1 c1-c4 and Req2 c1-c4 all hold on the patched tree; positive control fails at base and holds patched; >=1 candidate patch exercised and rejected.

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
"""Probe 1 (POSITIVE CONTROL) — Requirement 1, criteria 1/2/3.

The password help-text link, resolved against a change-form URL reached via a
to_field value that is NOT the pk, SHALL equal the admin password-change URL
keyed by the user's own primary key.

Holds on gold (href="../../<pk>/password/"), fails at base (href="../password/").
"""
import re
import urllib.parse
import django
from django.conf import settings

settings.configure(
    DEBUG=True,
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3",
                           "NAME": ":memory:"}},
    INSTALLED_APPS=[
        "django.contrib.contenttypes",
        "django.contrib.auth",
    ],
    USE_TZ=True,
    AUTH_USER_MODEL="auth.User",
)
django.setup()

from django.core.management import call_command
call_command("migrate", run_syncdb=True, verbosity=0)

from django.contrib.auth.forms import UserChangeForm
from django.contrib.auth.models import User

user = User.objects.create(username="testclient", password="x")
PK = user.pk
form = UserChangeForm(instance=user)
help_text = form.fields["password"].help_text
print("help_text:", help_text)

m = re.search(r'<a href="(.*?)">', help_text)
assert m, "no anchor href found in help text"
href = m.group(1)
print("href:", href)

# Change-form URL reached via to_field=uuid/username (NOT the pk):
change_url = "/admin/auth/user/testclient/change/"
resolved = urllib.parse.urljoin(change_url, href)
print("resolved:", resolved)

# The correct password-change URL is keyed by the primary key:
expected = "/admin/auth/user/%s/password/" % PK
print("expected:", expected)

if resolved != expected:
    print("VIOLATION: resolved link does not point at pk-keyed password URL")
    raise SystemExit(1)
print("OK: resolved link points at pk-keyed password URL")
raise SystemExit(0)
```

Prepatch bug re-encoded as an attack: `True`.

Instance django__django-16139: UserChangeForm password help-text link must resolve to the pk-keyed password-change URL even when the change form is reached via a to_field (non-pk) value. Gold fix: help_text.format(f'../../{self.instance.pk}/password/').

Probes (all HOLD on gold-patched tree; runner re-runs):
- probe_1 (POSITIVE CONTROL, Req1 c1/c2/c3): href resolved against a to_field(username)-keyed change URL == /admin/auth/user/<pk>/password/. HOLDS patched, VIOLATED at base (base gives ../password/ -> .../testclient/password/). Discriminates.
- probe_2 (Req1 c4): common pk-keyed change URL still resolves to pk-keyed password URL. HOLDS.
- probe_3 (Req2 c1): help text preserves surrounding wording, exactly one <a> anchor, no unfilled placeholder. HOLDS.
- probe_4 (Req2 c2): subclass with password=None + Meta.fields=('username',) — no password field — inits without error and doesn't touch placeholder. HOLDS both trees (guard is a regression invariant, not a fixed behavior).
- probe_5 (Req2 c3/c4): password field disabled/read-only (bound_data returns initial), initial password available, username present, user_permissions queryset select_related('content_type'). HOLDS.
- probe_6 (Req1 c3): link climbs out AND re-descends by pk — resolving against an arbitrary uuid change URL yields the pk password URL and the uuid does NOT survive. HOLDS patched.

Candidate wrong-fix candA (naive one-level climb f'../{pk}/password/'): REJECTED by probes 1, 2 and 6 (yields .../testclient/1/password/ or .../1/1/password/, keeping the record segment instead of replacing it). Demonstrates the suite discriminates a plausible weak fix. No requirements-conforming alternative patch was found that fails the hidden test — the biconditional pk-keyed resolution probes (1/2/6) pin the exact fixed behavior.

Environment note: probes bootstrap Django with an in-memory sqlite DB + migrate run_syncdb (needed because UserChangeForm.__init__ touches the user_permissions queryset and User creation). Ran on the official instance image via nl_attack.

Verdict SOUND: >=6 distinct probes covering Req1 c1-c4 and Req2 c1-c4 all hold on the patched tree; positive control fails at base and holds patched; >=1 candidate patch exercised and rejected.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Patch changes only the .format() argument from '../password/' to f'../../{self.instance.pk}/password/'. Every requirement clause maps to observed patched behavior or to code the patch provably leaves intact. No wrong-boundary defect: requirements pin the changed observable (the resolved relative URL keyed by pk), not a narrow helper. Probes: patched HOLDS ('../../7/password/'), base VIOLATED ('../password/').


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The public problem_statement is exceptionally complete: it contains the full UserChangeForm source (including the `if password:` guard and help-text template with `<a href="{}">`), the exact to_field="uuid" broken-URL scenario, and the verbatim gold fix `password.help_text.format(f"../../{self.instance.pk}/password/")`. Every requirement is a behavioral restatement of this public material. Req 1 (link keyed by pk, climb-out/re-descend) = the public fix; Req 2.2 (no password field / excluding subclass) is implied by the public `if password:` guard, not the hidden test `test_password_excluded`; Req 2.4 (user_permissions select_related) is visible in the surrounding public code context. None of the hidden test's distinctive artifacts leaked: no `auth_tests.urls_admin`, no `urllib.parse.urljoin`, no `reverse(...args=(user.username,))`, no `password_change` reverse, no test function/class names, no parametrization ids. Naming forms.py / UserChangeForm.__init__ is legitimate localization. The PASS_TO_PASS regression protections in Req 2.5 are generic 'don't disturb sibling forms' prose, not a mirror of the test list.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
