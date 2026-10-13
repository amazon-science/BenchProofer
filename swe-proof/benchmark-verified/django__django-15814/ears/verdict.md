# P2 adversarial audit — django__django-15814

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 5 requirement probes hold on the patched tree; 2/2 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 5 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 5 | `probe_core.py`, `probe_key_concrete.py`, `probe_chain.py`, `probe_regress.py`, `probe_defer_eq.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 2 alternative candidate patches, claimed to satisfy every cited requirement, and ran the same suite against them. The suite rejected all 2: a probe encoding a cited requirement fails under each of those, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_core.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (5):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_core.py` → holds on the patched tree (good)

```python
# Positive control: Requirement 1.1/1.2 — select_related().only() over a
# relation to a proxy model must evaluate without ValueError and return the
# stored object.
import os, sys, django
from django.conf import settings

sys.path.insert(0, '/testbed/tests')
settings.configure(
    DEBUG=True,
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
    INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth', 'proxy_models'],
    USE_TZ=True,
)
django.setup()

from django.db import connection
from django.apps import apps
from proxy_models.models import ProxyTrackerUser, Issue

# create schema for all concrete models in the proxy_models app + deps
with connection.schema_editor() as se:
    created = set()
    for model in apps.get_models():
        if model._meta.proxy:
            continue
        if model in created:
            continue
        try:
            se.create_model(model)
            created.add(model)
        except Exception as e:
            pass

user = ProxyTrackerUser.objects.create(name="Joe Doe", status="test")
issue = Issue.objects.create(summary="New issue", assignee=user)
qs = Issue.objects.select_related("assignee").only("assignee__status")
try:
    got = qs.get()
except Exception as e:
    print("RAISED:", type(e).__name__, e)
    sys.exit(1)
print("got:", got, "eq:", got == issue)
if got != issue:
    print("MISMATCH")
    sys.exit(1)
# related object identity available without extra query
print("assignee.status:", got.assignee.status, "pk:", got.assignee.pk)
if got.assignee.pk != user.pk:
    sys.exit(1)
print("OK")
sys.exit(0)
```

Attack 2 — `probe_key_concrete.py` → holds on the patched tree (good)

```python
# Requirement 2.1: when deferred_to_data resolves a proxy target, it SHALL key
# the load plan under the CONCRETE model, never under the proxy model itself.
import os, sys, django
from django.conf import settings
sys.path.insert(0, '/testbed/tests')
settings.configure(DEBUG=True, DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}}, INSTALLED_APPS=['django.contrib.contenttypes','django.contrib.auth','proxy_models'], USE_TZ=True)
django.setup()
from proxy_models.models import Issue
qs = Issue.objects.select_related("assignee").only("assignee__status")
columns = {}
qs.query.clone().deferred_to_data(columns)
info = {m.__name__: {'proxy': m._meta.proxy, 'concrete': m._meta.concrete_model.__name__, 'vals': sorted(map(str, v))} for m, v in columns.items()}
print("PLAN:", info)
# No key may be a proxy model
proxy_keys = [m.__name__ for m in columns if m._meta.proxy]
print("proxy_keys:", proxy_keys)
if proxy_keys:
    print("FAIL: plan keyed under proxy model(s)")
    sys.exit(1)
# The assignee target is ProxyTrackerUser whose concrete is TrackerUser; that
# key must be present and include the pk requirement.
tu = [m for m in columns if m.__name__ == 'TrackerUser']
if not tu:
    print("FAIL: no TrackerUser (concrete) key present")
    sys.exit(1)
print("OK")
sys.exit(0)
```

Attack 3 — `probe_chain.py` → holds on the patched tree (good)

```python
import os, sys, django
from django.conf import settings
sys.path.insert(0, '/testbed/tests')
settings.configure(DEBUG=True, DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}}, INSTALLED_APPS=['django.contrib.contenttypes','django.contrib.auth','proxy_models'], USE_TZ=True)
django.setup()
from django.db import connection
from django.apps import apps
from proxy_models.models import Improvement, ProxyTrackerUser, ProxyProxyBug, BaseUser
with connection.schema_editor() as se:
    for model in apps.get_models():
        if model._meta.proxy: continue
        try: se.create_model(model)
        except Exception: pass
# Improvement has reporter->ProxyTrackerUser and associated_bug->ProxyProxyBug
rep = ProxyTrackerUser.objects.create(name="R", status="s")
# ProxyProxyBug is proxy of Bug (concrete). Bug has reporter FK to BaseUser.
bu = BaseUser.objects.create(name="bug-owner")
bug = ProxyProxyBug.objects.create(summary="b", assignee=rep, version="1", reporter=bu)
imp = Improvement.objects.create(summary="imp", assignee=rep, version="9", reporter=rep, associated_bug=bug)
qs = Improvement.objects.select_related("reporter", "associated_bug").only(
    "reporter__status", "associated_bug__version")
# plan keys: no proxy allowed
columns = {}
qs.query.clone().deferred_to_data(columns)
proxy_keys = [m.__name__ for m in columns if m._meta.proxy]
print("KEYS:", [m.__name__ for m in columns], "proxy_keys:", proxy_keys)
if proxy_keys:
    print("FAIL: proxy key in multi-step plan"); sys.exit(1)
# and evaluation works
try:
    got = qs.get()
except Exception as e:
    print("RAISED:", type(e).__name__, e); sys.exit(1)
print("got:", got, "eq:", got == imp, "rep.status:", got.reporter.status, "bug.version:", got.associated_bug.version)
if got != imp or got.reporter.pk != rep.pk or got.associated_bug.pk != bug.pk:
    print("FAIL mismatch"); sys.exit(1)
print("OK"); sys.exit(0)
```

Attack 4 — `probe_regress.py` → holds on the patched tree (good)

```python
import os, sys, django
from django.conf import settings
sys.path.insert(0, '/testbed/tests')
settings.configure(DEBUG=True, DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}}, INSTALLED_APPS=['django.contrib.contenttypes','django.contrib.auth','proxy_models'], USE_TZ=True)
django.setup()
from django.db import connection
from django.apps import apps
from proxy_models.models import Bug, Issue, ProxyTrackerUser, BaseUser
with connection.schema_editor() as se:
    for model in apps.get_models():
        if model._meta.proxy: continue
        try: se.create_model(model)
        except Exception: pass
# Bug.reporter -> BaseUser (a plain concrete model, NON-proxy target)
bu = BaseUser.objects.create(name="owner")
assignee = ProxyTrackerUser.objects.create(name="A", status="x")
bug = Bug.objects.create(summary="B", assignee=assignee, version="v1", reporter=bu)
# only() across non-proxy relation reporter->BaseUser
qs = Bug.objects.select_related("reporter").only("reporter__name")
columns = {}
qs.query.clone().deferred_to_data(columns)
# BaseUser is the concrete non-proxy target; key must be BaseUser itself.
names = sorted(m.__name__ for m in columns)
print("KEYS:", names)
if 'BaseUser' not in names:
    print("FAIL: BaseUser key missing"); sys.exit(1)
got = qs.get()
print("got.reporter.name:", got.reporter.name, "pk:", got.reporter.pk)
if got.reporter.name != "owner" or got.reporter.pk != bu.pk:
    print("FAIL reporter"); sys.exit(1)
# Req 3.2: select_related WITHOUT only() fully populates related object
qs2 = Issue.objects.select_related("assignee")
Issue.objects.create(summary="I", assignee=assignee)
got2 = qs2.filter(summary="I").get()
print("full assignee name:", got2.assignee.name, "status:", got2.assignee.status)
if got2.assignee.name != "A" or got2.assignee.status != "x":
    print("FAIL full populate"); sys.exit(1)
print("OK"); sys.exit(0)
```

Attack 5 — `probe_defer_eq.py` → holds on the patched tree (good)

```python
import os, sys, django
from django.conf import settings
sys.path.insert(0, '/testbed/tests')
settings.configure(DEBUG=True, DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}}, INSTALLED_APPS=['django.contrib.contenttypes','django.contrib.auth','proxy_models'], USE_TZ=True)
django.setup()
from django.db import connection
from django.apps import apps
from proxy_models.models import ProxyTrackerUser, TrackerUser, Issue
with connection.schema_editor() as se:
    for model in apps.get_models():
        if model._meta.proxy: continue
        try: se.create_model(model)
        except Exception: pass
user = ProxyTrackerUser.objects.create(name="Joe", status="test")
issue = Issue.objects.create(summary="I", assignee=user)
# defer() form should also traverse and not crash (Req 1.1: only()/defer())
qs = Issue.objects.select_related("assignee").defer("assignee__name")
try:
    got = qs.get()
except Exception as e:
    print("RAISED:", type(e).__name__, e); sys.exit(1)
print("defer got:", got, "eq:", got == issue, "status:", got.assignee.status)
if got != issue:
    print("FAIL defer"); sys.exit(1)
# Req 3.4: concrete_model of an already-concrete model is itself (no-op)
if TrackerUser._meta.concrete_model is not TrackerUser:
    print("FAIL: concrete of concrete not itself"); sys.exit(1)
# Req 3.5: proxy instance == concrete instance with same pk
pkfield = TrackerUser._meta.pk.attname
p = ProxyTrackerUser(**{pkfield: user.pk})
c = TrackerUser(**{pkfield: user.pk})
print("pkfield:", pkfield, "proxy==concrete:", p == c)
if not (p == c):
    print("FAIL equality"); sys.exit(1)
print("OK"); sys.exit(0)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_core.py`

```python
# Positive control: Requirement 1.1/1.2 — select_related().only() over a
# relation to a proxy model must evaluate without ValueError and return the
# stored object.
import os, sys, django
from django.conf import settings

sys.path.insert(0, '/testbed/tests')
settings.configure(
    DEBUG=True,
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
    INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth', 'proxy_models'],
    USE_TZ=True,
)
django.setup()

from django.db import connection
from django.apps import apps
from proxy_models.models import ProxyTrackerUser, Issue

# create schema for all concrete models in the proxy_models app + deps
with connection.schema_editor() as se:
    created = set()
    for model in apps.get_models():
        if model._meta.proxy:
            continue
        if model in created:
            continue
        try:
            se.create_model(model)
            created.add(model)
        except Exception as e:
            pass

user = ProxyTrackerUser.objects.create(name="Joe Doe", status="test")
issue = Issue.objects.create(summary="New issue", assignee=user)
qs = Issue.objects.select_related("assignee").only("assignee__status")
try:
    got = qs.get()
except Exception as e:
    print("RAISED:", type(e).__name__, e)
    sys.exit(1)
print("got:", got, "eq:", got == issue)
if got != issue:
    print("MISMATCH")
    sys.exit(1)
# related object identity available without extra query
print("assignee.status:", got.assignee.status, "pk:", got.assignee.pk)
if got.assignee.pk != user.pk:
    sys.exit(1)
print("OK")
sys.exit(0)
```

Prepatch bug re-encoded as an attack: `True`.

Instance django__django-15814: gold adds `cur_model = cur_model._meta.concrete_model` in Query.deferred_to_data so the column-load plan is keyed under the concrete model, not a proxy. Hidden F2P: test_select_related_only (Issue.assignee -> ProxyTrackerUser, a FORWARD FK; ProxyTrackerUser is proxy of MTI TrackerUser, pk attname baseuser_ptr_id).

### PROBES (all run in the official py3.9 testbed image; schema built in-memory via schema_editor over the proxy_models test app):
1. probe_core.py (POSITIVE CONTROL, Req 1.1/1.2/1.3): select_related('assignee').only('assignee__status').get() must not raise and must equal the stored Issue, with assignee.pk/status populated. BASE: VIOLATED. PATCHED: HOLDS. Discriminates.
2. probe_key_concrete.py (Req 2.1/2.3): inspect deferred_to_data(columns) output — NO plan key may be a proxy model, and the concrete TrackerUser key must exist. BASE: VIOLATED (key 'ProxyTrackerUser' present, its plan lacks status+pk split). PATCHED: HOLDS (keys collapse to TrackerUser/Issue).
3. probe_chain.py (Req 2.4): multi-relation path Improvement -> reporter(ProxyTrackerUser) & associated_bug(ProxyProxyBug, proxy-of-proxy); no proxy key allowed and .get() must succeed and equal stored. BASE: VIOLATED (proxy keys ProxyTrackerUser, ProxyProxyBug). PATCHED: HOLDS.
4. probe_regress.py (Req 3.1/3.2): only() over a NON-proxy target (Bug.reporter -> BaseUser) keeps BaseUser key + correct result; select_related without only() fully populates. HOLDS on BOTH base and patched (unchanged behavior, correct regression leg).
5. probe_defer_eq.py (Req 1.1 defer variant, 3.4, 3.5): defer('assignee__name') over proxy relation succeeds; concrete_model of a concrete model is itself; proxy instance == concrete instance with same pk. HOLDS on BOTH trees.

### Candidate patches
- weak_reverse_only.diff: applies concrete_model only inside the is_reverse_o2o branch (a weak reading). REJECTED by probe_core, probe_key_concrete, probe_chain (forward-FK proxy still crashes / keyed under proxy). Would fail hidden test (which is a forward FK).
- weak_opts_only.diff: sets opts = cur_model._meta.concrete_model._meta but leaves cur_model (the must_include KEY) as the proxy. Passes the FUNCTIONAL probes (core/regress/defer_eq HOLD) because opts.pk now yields the right pk field, BUT REJECTED by probe_key_concrete and probe_chain (Req 2: plan still keyed under ProxyTrackerUser/ProxyProxyBug). Demonstrates the Req-2 keying probes discriminate a partial fix that a weak spec reading would permit.

No probe fails on the patched tree; positive control discriminates (fails base, holds patched, prepatch_reproduced=true); every candidate that a weaker suite might miss is rejected by at least one probe. No requirements-conforming-yet-nonresolving alternative found.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 5 requirement probes hold on the patched tree; 2/2 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 5 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 5 | `probe_core.py`, `probe_key_concrete.py`, `probe_chain.py`, `probe_regress.py`, `probe_defer_eq.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 2 alternative candidate patches, claimed to satisfy every cited requirement, and ran the same suite against them. The suite rejected all 2: a probe encoding a cited requirement fails under each of those, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_core.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (5):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

_The 5 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts, and on this backend both roles put it through the same derivation: every block below is a requirement probe run on the gold-patched tree, and the `machine verdict:` line each role publishes above reports BOTH that its probes hold there and how many candidate patches the probe suite rejected — so the two roles re-ran ONE probe suite and each recorded its own outcome for every probe in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `probe_core.py` → holds on the patched tree (good)

Attack 2 — `probe_key_concrete.py` → holds on the patched tree (good)

Attack 3 — `probe_chain.py` → holds on the patched tree (good)

Attack 4 — `probe_regress.py` → holds on the patched tree (good)

Attack 5 — `probe_defer_eq.py` → holds on the patched tree (good)

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_core.py`

```python
# Positive control: Requirement 1.1/1.2 — select_related().only() over a
# relation to a proxy model must evaluate without ValueError and return the
# stored object.
import os, sys, django
from django.conf import settings

sys.path.insert(0, '/testbed/tests')
settings.configure(
    DEBUG=True,
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
    INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth', 'proxy_models'],
    USE_TZ=True,
)
django.setup()

from django.db import connection
from django.apps import apps
from proxy_models.models import ProxyTrackerUser, Issue

# create schema for all concrete models in the proxy_models app + deps
with connection.schema_editor() as se:
    created = set()
    for model in apps.get_models():
        if model._meta.proxy:
            continue
        if model in created:
            continue
        try:
            se.create_model(model)
            created.add(model)
        except Exception as e:
            pass

user = ProxyTrackerUser.objects.create(name="Joe Doe", status="test")
issue = Issue.objects.create(summary="New issue", assignee=user)
qs = Issue.objects.select_related("assignee").only("assignee__status")
try:
    got = qs.get()
except Exception as e:
    print("RAISED:", type(e).__name__, e)
    sys.exit(1)
print("got:", got, "eq:", got == issue)
if got != issue:
    print("MISMATCH")
    sys.exit(1)
# related object identity available without extra query
print("assignee.status:", got.assignee.status, "pk:", got.assignee.pk)
if got.assignee.pk != user.pk:
    sys.exit(1)
print("OK")
sys.exit(0)
```

Prepatch bug re-encoded as an attack: `True`.

Instance django__django-15814: gold adds `cur_model = cur_model._meta.concrete_model` in Query.deferred_to_data so the column-load plan is keyed under the concrete model, not a proxy. Hidden F2P: test_select_related_only (Issue.assignee -> ProxyTrackerUser, a FORWARD FK; ProxyTrackerUser is proxy of MTI TrackerUser, pk attname baseuser_ptr_id).

### PROBES (all run in the official py3.9 testbed image; schema built in-memory via schema_editor over the proxy_models test app):
1. probe_core.py (POSITIVE CONTROL, Req 1.1/1.2/1.3): select_related('assignee').only('assignee__status').get() must not raise and must equal the stored Issue, with assignee.pk/status populated. BASE: VIOLATED. PATCHED: HOLDS. Discriminates.
2. probe_key_concrete.py (Req 2.1/2.3): inspect deferred_to_data(columns) output — NO plan key may be a proxy model, and the concrete TrackerUser key must exist. BASE: VIOLATED (key 'ProxyTrackerUser' present, its plan lacks status+pk split). PATCHED: HOLDS (keys collapse to TrackerUser/Issue).
3. probe_chain.py (Req 2.4): multi-relation path Improvement -> reporter(ProxyTrackerUser) & associated_bug(ProxyProxyBug, proxy-of-proxy); no proxy key allowed and .get() must succeed and equal stored. BASE: VIOLATED (proxy keys ProxyTrackerUser, ProxyProxyBug). PATCHED: HOLDS.
4. probe_regress.py (Req 3.1/3.2): only() over a NON-proxy target (Bug.reporter -> BaseUser) keeps BaseUser key + correct result; select_related without only() fully populates. HOLDS on BOTH base and patched (unchanged behavior, correct regression leg).
5. probe_defer_eq.py (Req 1.1 defer variant, 3.4, 3.5): defer('assignee__name') over proxy relation succeeds; concrete_model of a concrete model is itself; proxy instance == concrete instance with same pk. HOLDS on BOTH trees.

### Candidate patches
- weak_reverse_only.diff: applies concrete_model only inside the is_reverse_o2o branch (a weak reading). REJECTED by probe_core, probe_key_concrete, probe_chain (forward-FK proxy still crashes / keyed under proxy). Would fail hidden test (which is a forward FK).
- weak_opts_only.diff: sets opts = cur_model._meta.concrete_model._meta but leaves cur_model (the must_include KEY) as the proxy. Passes the FUNCTIONAL probes (core/regress/defer_eq HOLD) because opts.pk now yields the right pk field, BUT REJECTED by probe_key_concrete and probe_chain (Req 2: plan still keyed under ProxyTrackerUser/ProxyProxyBug). Demonstrates the Req-2 keying probes discriminate a partial fix that a weak spec reading would permit.

No probe fails on the patched tree; positive control discriminates (fails base, holds patched, prepatch_reproduced=true); every candidate that a weaker suite might miss is rejected by at least one probe. No requirements-conforming-yet-nonresolving alternative found.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Probe on instance image: patched HOLDS (exit 0, custom.pk=1, name='test'); base VIOLATED with the exact issue traceback ValueError: 'id' is not in list at query.py get_related_populators -> RelatedPopulator.__init__ self.init_list.index(self.model_cls._meta.pk.attname). Confirmed the patched code inserts the concrete_model coercion inside the parts[:-1] loop. Requirements correctly identify RelatedPopulator's concrete-pk lookup as the downstream consumer and the proxy-vs-concrete keying mismatch as the root cause.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** requirements.md stays within the public problem_statement plus legitimate localization. The public problem_statement already contains: the crash, the traceback naming RelatedPopulator / deferred_to_data / self.pk_idx = self.init_list.index(self.model_cls._meta.pk.attname), the models (CustomModel/ProxyCustomModel/AnotherModel), AND the exact fix snippet (opts = cur_model._meta.concrete_model._meta). The doc introduces NO hidden-test content: it never mentions the test name (test_select_related_only), file path (tests/proxy_models/tests.py), or the test's specific identifiers (ProxyTrackerUser, Issue, assignee, status, name). It uses abstract placeholders (<rel>__<field>). The gold edit adds only `cur_model = cur_model._meta.concrete_model`, which invents no new identifier; the concrete-model keying is described behaviorally and was already publicly disclosed in the problem statement. `must_include` is pre-existing source, not fix-invented. Requirement 1.2's 'single matching row compares equal to the stored object' is a behavioral translation of assertEqual(qs.get(), issue), which is the intended purpose of the spec, not a test transmission; no case enumeration mirrors parametrization (the F2P is a single non-parametrized test).

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
