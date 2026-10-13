# P2 adversarial audit — django__django-13568

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 requirement probes hold on the patched tree; 2/2 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 7 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 7 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py`, `probe_7.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 2 alternative candidate patches, claimed to satisfy every cited requirement, and ran the same suite against them. The suite rejected all 2: a probe encoding a cited requirement fails under each of those, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (7):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
import sys
sys.path.insert(0, "/testbed/tests")
import django
from django.conf import settings
settings.configure(
    SECRET_KEY="x",
    INSTALLED_APPS=["django.contrib.auth","django.contrib.contenttypes","auth_tests"],
    DATABASES={"default":{"ENGINE":"django.db.backends.sqlite3","NAME":":memory:"}},
    AUTHENTICATION_BACKENDS=["django.contrib.auth.backends.ModelBackend"],
)
django.setup()
from django.test.utils import isolate_apps, override_settings
from django.contrib.auth.models import AbstractBaseUser
from django.db import models
from django.db.models import UniqueConstraint, Q
from django.contrib.auth.checks import check_user_model

@isolate_apps("auth_tests", kwarg_name="apps")
def run(apps):
    class CustomUserUC(AbstractBaseUser):
        username = models.CharField(max_length=30)
        USERNAME_FIELD = "username"
        class Meta:
            app_label = "auth_tests"
            constraints = [UniqueConstraint(fields=["username"], name="u1")]
    with override_settings(AUTH_USER_MODEL="auth_tests.CustomUserUC"):
        default = check_user_model(app_configs=apps.get_app_configs())
        with override_settings(AUTHENTICATION_BACKENDS=["my.custom.backend"]):
            custom = check_user_model(app_configs=apps.get_app_configs())
    return default, custom
d, c = run()
print("default-backend errors:", [e.id for e in d])
print("custom-backend errors:", [e.id for e in c])
ok = (d == []) and (c == [])
print("PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
import sys
sys.path.insert(0, "/testbed/tests")
import django
from django.conf import settings
settings.configure(
    SECRET_KEY="x",
    INSTALLED_APPS=["django.contrib.auth","django.contrib.contenttypes","auth_tests"],
    DATABASES={"default":{"ENGINE":"django.db.backends.sqlite3","NAME":":memory:"}},
    AUTHENTICATION_BACKENDS=["django.contrib.auth.backends.ModelBackend"],
)
django.setup()
from django.test.utils import isolate_apps, override_settings
from django.contrib.auth.models import AbstractBaseUser
from django.db import models
from django.db.models import UniqueConstraint, Q
from django.contrib.auth.checks import check_user_model

@isolate_apps("auth_tests", kwarg_name="apps")
def run(apps):
    class CustomUserPartial(AbstractBaseUser):
        username = models.CharField(max_length=30)
        USERNAME_FIELD = "username"
        class Meta:
            app_label = "auth_tests"
            constraints = [UniqueConstraint(fields=["username"], name="pu", condition=Q(password__isnull=False))]
    with override_settings(AUTH_USER_MODEL="auth_tests.CustomUserPartial"):
        d = check_user_model(app_configs=apps.get_app_configs())
        with override_settings(AUTHENTICATION_BACKENDS=["my.custom.backend"]):
            c = check_user_model(app_configs=apps.get_app_configs())
    return d, c
d, c = run()
print("default:", [e.id for e in d])
print("custom:", [e.id for e in c])
ok = ([e.id for e in d] == ["auth.E003"]) and ([e.id for e in c] == ["auth.W004"])
print("PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
import sys
sys.path.insert(0, "/testbed/tests")
import django
from django.conf import settings
settings.configure(
    SECRET_KEY="x",
    INSTALLED_APPS=["django.contrib.auth","django.contrib.contenttypes","auth_tests"],
    DATABASES={"default":{"ENGINE":"django.db.backends.sqlite3","NAME":":memory:"}},
    AUTHENTICATION_BACKENDS=["django.contrib.auth.backends.ModelBackend"],
)
django.setup()
from django.test.utils import isolate_apps, override_settings
from django.contrib.auth.models import AbstractBaseUser
from django.db import models
from django.db.models import UniqueConstraint, Q
from django.contrib.auth.checks import check_user_model

@isolate_apps("auth_tests", kwarg_name="apps")
def run(apps):
    class CustomUserNonUnique(AbstractBaseUser):
        username = models.CharField(max_length=30)
        USERNAME_FIELD = "username"
        class Meta:
            app_label = "auth_tests"
    with override_settings(AUTH_USER_MODEL="auth_tests.CustomUserNonUnique"):
        return check_user_model(app_configs=apps.get_app_configs())
d = run()
print("errors:", [(e.id, e.__class__.__name__) for e in d])
ok = ([e.id for e in d] == ["auth.E003"]) and (d[0].__class__.__name__ == "Error")
print("PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
import sys
sys.path.insert(0, "/testbed/tests")
import django
from django.conf import settings
settings.configure(
    SECRET_KEY="x",
    INSTALLED_APPS=["django.contrib.auth","django.contrib.contenttypes","auth_tests"],
    DATABASES={"default":{"ENGINE":"django.db.backends.sqlite3","NAME":":memory:"}},
    AUTHENTICATION_BACKENDS=["django.contrib.auth.backends.ModelBackend"],
)
django.setup()
from django.test.utils import isolate_apps, override_settings
from django.contrib.auth.models import AbstractBaseUser
from django.db import models
from django.db.models import UniqueConstraint, Q
from django.contrib.auth.checks import check_user_model

@isolate_apps("auth_tests", kwarg_name="apps")
def run(apps):
    class CustomUserNonUnique(AbstractBaseUser):
        username = models.CharField(max_length=30)
        USERNAME_FIELD = "username"
        class Meta:
            app_label = "auth_tests"
    with override_settings(AUTH_USER_MODEL="auth_tests.CustomUserNonUnique", AUTHENTICATION_BACKENDS=["my.custom.backend"]):
        return check_user_model(app_configs=apps.get_app_configs())
d = run()
print("errors:", [(e.id, e.__class__.__name__) for e in d])
ok = ([e.id for e in d] == ["auth.W004"]) and (d[0].__class__.__name__ == "Warning")
print("PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
import sys
sys.path.insert(0, "/testbed/tests")
import django
from django.conf import settings
settings.configure(
    SECRET_KEY="x",
    INSTALLED_APPS=["django.contrib.auth","django.contrib.contenttypes","auth_tests"],
    DATABASES={"default":{"ENGINE":"django.db.backends.sqlite3","NAME":":memory:"}},
    AUTHENTICATION_BACKENDS=["django.contrib.auth.backends.ModelBackend"],
)
django.setup()
from django.test.utils import isolate_apps, override_settings
from django.contrib.auth.models import AbstractBaseUser
from django.db import models
from django.db.models import UniqueConstraint, Q
from django.contrib.auth.checks import check_user_model

@isolate_apps("auth_tests", kwarg_name="apps")
def run(apps):
    class CustomUserMulti(AbstractBaseUser):
        username = models.CharField(max_length=30)
        other = models.CharField(max_length=30)
        USERNAME_FIELD = "username"
        class Meta:
            app_label = "auth_tests"
            constraints = [UniqueConstraint(fields=["username", "other"], name="mu")]
    with override_settings(AUTH_USER_MODEL="auth_tests.CustomUserMulti"):
        return check_user_model(app_configs=apps.get_app_configs())
d = run()
print("errors:", [e.id for e in d])
ok = ([e.id for e in d] == ["auth.E003"])
print("PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
import sys
sys.path.insert(0, "/testbed/tests")
import django
from django.conf import settings
settings.configure(
    SECRET_KEY="x",
    INSTALLED_APPS=["django.contrib.auth","django.contrib.contenttypes","auth_tests"],
    DATABASES={"default":{"ENGINE":"django.db.backends.sqlite3","NAME":":memory:"}},
    AUTHENTICATION_BACKENDS=["django.contrib.auth.backends.ModelBackend"],
)
django.setup()
from django.test.utils import isolate_apps, override_settings
from django.contrib.auth.models import AbstractBaseUser
from django.db import models
from django.db.models import UniqueConstraint, Q
from django.contrib.auth.checks import check_user_model

@isolate_apps("auth_tests", kwarg_name="apps")
def run(apps):
    class CustomUserOther(AbstractBaseUser):
        username = models.CharField(max_length=30)
        other = models.CharField(max_length=30)
        USERNAME_FIELD = "username"
        class Meta:
            app_label = "auth_tests"
            constraints = [UniqueConstraint(fields=["other"], name="ou")]
    with override_settings(AUTH_USER_MODEL="auth_tests.CustomUserOther"):
        return check_user_model(app_configs=apps.get_app_configs())
d = run()
print("errors:", [e.id for e in d])
ok = ([e.id for e in d] == ["auth.E003"])
print("PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)
```

Attack 7 — `probe_7.py` → holds on the patched tree (good)

```python
import sys
sys.path.insert(0, "/testbed/tests")
import django
from django.conf import settings
settings.configure(
    SECRET_KEY="x",
    INSTALLED_APPS=["django.contrib.auth","django.contrib.contenttypes","auth_tests"],
    DATABASES={"default":{"ENGINE":"django.db.backends.sqlite3","NAME":":memory:"}},
    AUTHENTICATION_BACKENDS=["django.contrib.auth.backends.ModelBackend"],
)
django.setup()
from django.test.utils import isolate_apps, override_settings
from django.contrib.auth.models import AbstractBaseUser
from django.db import models
from django.db.models import UniqueConstraint, Q
from django.contrib.auth.checks import check_user_model

@isolate_apps("auth_tests", kwarg_name="apps")
def run(apps):
    class CustomUserUniqueField(AbstractBaseUser):
        username = models.CharField(max_length=30, unique=True)
        USERNAME_FIELD = "username"
        class Meta:
            app_label = "auth_tests"
    with override_settings(AUTH_USER_MODEL="auth_tests.CustomUserUniqueField"):
        return check_user_model(app_configs=apps.get_app_configs())
d = run()
print("errors:", [e.id for e in d])
ok = (d == [])
print("PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
import sys
sys.path.insert(0, "/testbed/tests")
import django
from django.conf import settings
settings.configure(
    SECRET_KEY="x",
    INSTALLED_APPS=["django.contrib.auth","django.contrib.contenttypes","auth_tests"],
    DATABASES={"default":{"ENGINE":"django.db.backends.sqlite3","NAME":":memory:"}},
    AUTHENTICATION_BACKENDS=["django.contrib.auth.backends.ModelBackend"],
)
django.setup()
from django.test.utils import isolate_apps, override_settings
from django.contrib.auth.models import AbstractBaseUser
from django.db import models
from django.db.models import UniqueConstraint, Q
from django.contrib.auth.checks import check_user_model

@isolate_apps("auth_tests", kwarg_name="apps")
def run(apps):
    class CustomUserUC(AbstractBaseUser):
        username = models.CharField(max_length=30)
        USERNAME_FIELD = "username"
        class Meta:
            app_label = "auth_tests"
            constraints = [UniqueConstraint(fields=["username"], name="u1")]
    with override_settings(AUTH_USER_MODEL="auth_tests.CustomUserUC"):
        default = check_user_model(app_configs=apps.get_app_configs())
        with override_settings(AUTHENTICATION_BACKENDS=["my.custom.backend"]):
            custom = check_user_model(app_configs=apps.get_app_configs())
    return default, custom
d, c = run()
print("default-backend errors:", [e.id for e in d])
print("custom-backend errors:", [e.id for e in c])
ok = (d == []) and (c == [])
print("PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance django__django-13568: extend auth.check_user_model to suppress the USERNAME_FIELD uniqueness diagnostic (auth.E003/auth.W004) when a TOTAL (unconditional) UniqueConstraint covers exactly the single USERNAME_FIELD. Gold patch adds `and not any(constraint.fields == (cls.USERNAME_FIELD,) for constraint in cls._meta.total_unique_constraints)`.

All probes use an in-container scaffold: sys.path adds /testbed/tests to import the real auth_tests app, settings.configure with SECRET_KEY + sqlite, isolate_apps('auth_tests'), define a model, override AUTH_USER_MODEL, call check_user_model directly and inspect returned check ids/severities.

Probe results — PATCHED tree (all HOLD):
- probe_1 (POSITIVE CONTROL, Req 1.1/1.2): total unique constraint over [username] => [] under BOTH default and custom backends. PATCHED: HOLDS (default=[], custom=[]). BASE: VIOLATED (default=['auth.E003']) => discriminates.
- probe_2 (Req 2.3): PARTIAL constraint (condition=Q(password__isnull=False)) => still auth.E003 (default) and auth.W004 (custom). PATCHED: HOLDS.
- probe_3 (Req 2.1): non-unique, no constraint, default backend => exactly ['auth.E003'] Error. PATCHED: HOLDS.
- probe_4 (Req 2.2): non-unique, no constraint, custom backend => exactly ['auth.W004'] Warning. PATCHED: HOLDS.
- probe_5 (Req 1.3): constraint over TWO fields [username, other] => NOT suppressed => ['auth.E003']. PATCHED: HOLDS.
- probe_6 (Req 1.3): constraint over a DIFFERENT single field [other] => NOT suppressed => ['auth.E003']. PATCHED: HOLDS.
- probe_7 (Req 2.4): unique=True field => no diagnostic (pre-existing behavior). PATCHED: HOLDS.

### CANDIDATE PATCHES (both requirements-plausible wrong fixes, both REJECTED by the suite => discriminating power confirmed):
- weak_A.diff: matches any UniqueConstraint over (USERNAME_FIELD,) in cls._meta.constraints, IGNORING condition (uses .constraints not total_unique_constraints). REJECTED by probe_2 (partial constraint wrongly suppresses => default=[] VIOLATED). probe_1 and probe_5 still hold under it.
- weak_B.diff: uses `USERNAME_FIELD in constraint.fields` (membership) over total_unique_constraints instead of exact tuple equality. REJECTED by probe_5 (multi-field constraint wrongly suppresses => [] VIOLATED). probe_1 and probe_2 still hold under it.

Every needed run completed. >=5 distinct probes all hold on patched; positive control fails at base and holds patched; >=1 candidate exercised and >=2 candidates REJECTED by the probe suite. Requirements are faithful (not too strong: gold satisfies all probes) and discriminating (not too weak: both naive/partial fixes rejected). Verdict SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 requirement probes hold on the patched tree; 2/2 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 7 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 7 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py`, `probe_7.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 2 alternative candidate patches, claimed to satisfy every cited requirement, and ran the same suite against them. The suite rejected all 2: a probe encoding a cited requirement fails under each of those, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

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
import sys
sys.path.insert(0, "/testbed/tests")
import django
from django.conf import settings
settings.configure(
    SECRET_KEY="x",
    INSTALLED_APPS=["django.contrib.auth","django.contrib.contenttypes","auth_tests"],
    DATABASES={"default":{"ENGINE":"django.db.backends.sqlite3","NAME":":memory:"}},
    AUTHENTICATION_BACKENDS=["django.contrib.auth.backends.ModelBackend"],
)
django.setup()
from django.test.utils import isolate_apps, override_settings
from django.contrib.auth.models import AbstractBaseUser
from django.db import models
from django.db.models import UniqueConstraint, Q
from django.contrib.auth.checks import check_user_model

@isolate_apps("auth_tests", kwarg_name="apps")
def run(apps):
    class CustomUserUC(AbstractBaseUser):
        username = models.CharField(max_length=30)
        USERNAME_FIELD = "username"
        class Meta:
            app_label = "auth_tests"
            constraints = [UniqueConstraint(fields=["username"], name="u1")]
    with override_settings(AUTH_USER_MODEL="auth_tests.CustomUserUC"):
        default = check_user_model(app_configs=apps.get_app_configs())
        with override_settings(AUTHENTICATION_BACKENDS=["my.custom.backend"]):
            custom = check_user_model(app_configs=apps.get_app_configs())
    return default, custom
d, c = run()
print("default-backend errors:", [e.id for e in d])
print("custom-backend errors:", [e.id for e in c])
ok = (d == []) and (c == [])
print("PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance django__django-13568: extend auth.check_user_model to suppress the USERNAME_FIELD uniqueness diagnostic (auth.E003/auth.W004) when a TOTAL (unconditional) UniqueConstraint covers exactly the single USERNAME_FIELD. Gold patch adds `and not any(constraint.fields == (cls.USERNAME_FIELD,) for constraint in cls._meta.total_unique_constraints)`.

All probes use an in-container scaffold: sys.path adds /testbed/tests to import the real auth_tests app, settings.configure with SECRET_KEY + sqlite, isolate_apps('auth_tests'), define a model, override AUTH_USER_MODEL, call check_user_model directly and inspect returned check ids/severities.

Probe results — PATCHED tree (all HOLD):
- probe_1 (POSITIVE CONTROL, Req 1.1/1.2): total unique constraint over [username] => [] under BOTH default and custom backends. PATCHED: HOLDS (default=[], custom=[]). BASE: VIOLATED (default=['auth.E003']) => discriminates.
- probe_2 (Req 2.3): PARTIAL constraint (condition=Q(password__isnull=False)) => still auth.E003 (default) and auth.W004 (custom). PATCHED: HOLDS.
- probe_3 (Req 2.1): non-unique, no constraint, default backend => exactly ['auth.E003'] Error. PATCHED: HOLDS.
- probe_4 (Req 2.2): non-unique, no constraint, custom backend => exactly ['auth.W004'] Warning. PATCHED: HOLDS.
- probe_5 (Req 1.3): constraint over TWO fields [username, other] => NOT suppressed => ['auth.E003']. PATCHED: HOLDS.
- probe_6 (Req 1.3): constraint over a DIFFERENT single field [other] => NOT suppressed => ['auth.E003']. PATCHED: HOLDS.
- probe_7 (Req 2.4): unique=True field => no diagnostic (pre-existing behavior). PATCHED: HOLDS.

### CANDIDATE PATCHES (both requirements-plausible wrong fixes, both REJECTED by the suite => discriminating power confirmed):
- weak_A.diff: matches any UniqueConstraint over (USERNAME_FIELD,) in cls._meta.constraints, IGNORING condition (uses .constraints not total_unique_constraints). REJECTED by probe_2 (partial constraint wrongly suppresses => default=[] VIOLATED). probe_1 and probe_5 still hold under it.
- weak_B.diff: uses `USERNAME_FIELD in constraint.fields` (membership) over total_unique_constraints instead of exact tuple equality. REJECTED by probe_5 (multi-field constraint wrongly suppresses => [] VIOLATED). probe_1 and probe_2 still hold under it.

Every needed run completed. >=5 distinct probes all hold on patched; positive control fails at base and holds patched; >=1 candidate exercised and >=2 candidates REJECTED by the probe suite. Requirements are faithful (not too strong: gold satisfies all probes) and discriminating (not too weak: both naive/partial fixes rejected). Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Source confirmed on patched tree: `if not cls._meta.get_field(cls.USERNAME_FIELD).unique and not any(constraint.fields == (cls.USERNAME_FIELD,) for constraint in cls._meta.total_unique_constraints):`. total_unique_constraints returns UniqueConstraints with condition is None, so the partial-vs-total distinction in Req 2.3 is faithful. Requirements correctly model the changed observable behavior (whether the diagnostic fires) rather than a narrow slice. Probes run inside the instance image via nl_attack; models built with isolate_apps and the gold predicate evaluated directly (calling check_user_model resolves cls from AUTH_USER_MODEL, so per-field evaluation of the exact patched expression was used).


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The document names only public/legitimate surfaces: check_user_model (django/contrib/auth/checks.py), Model._meta.total_unique_constraints (django/db/models/options.py), and the auth.E003/W004 check — all present in the public problem_statement or as pre-existing real Django API (not fix-invented). The problem_statement itself already discloses auth.E003, USERNAME_FIELD, UniqueConstraint over ['username'], Model._meta.constraints, and the *_like-index rationale. The doc's partial/conditional-constraint requirement (Req 2.3) is NOT in the problem_statement but is a direct behavioral consequence of the fix relying on total_unique_constraints (condition is None); it is described as behavior without reproducing the test's condition=Q(password__isnull=False), the invented model names (CustomUserPartiallyUnique / CustomUserUniqueConstraint), test function/file names, or any quoted test/gold code. The fields-tuple equality (Req 1.3) is described behaviorally, not as the gold's literal `constraint.fields == (cls.USERNAME_FIELD,)`. auth.E001/E002/C009/C010 in Req 3 are pre-existing module checks describing preserved behavior, not test-derived. No test paths, ids, parametrization, or verbatim gold lines are transmitted.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
