# P2 adversarial audit — django__django-16612

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 6 requirement probes hold on the patched tree; 2/2 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 6 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 6 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 2 alternative candidate patches, claimed to satisfy every cited requirement, and ran the same suite against them. The suite rejected all 2: a probe encoding a cited requirement fails under each of those, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (6):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
"""Positive control / Req 1.1,1.2,1.5: APPEND_SLASH=True, staff-less direct
call to catch_all_view for a known URL missing its slash WITH a query string
-> HTTP 301 whose Location is the slash-terminated path + '?' + same query.
HOLDS on patched (query preserved); FAILS at base (query dropped)."""
import sys, types
import django
from django.conf import settings

if not settings.configured:
    settings.configure(
        DEBUG=True, ALLOWED_HOSTS=["*"], APPEND_SLASH=True,
        ROOT_URLCONF="probe_urlconf",
        DATABASES={}, INSTALLED_APPS=[], SECRET_KEY="x",
    )
django.setup()

from django.http import HttpResponsePermanentRedirect
from django.test import RequestFactory
from django.contrib.admin.sites import AdminSite

# urlconf where the slash-appended path resolves to a normal view
mod = types.ModuleType("probe_urlconf")
from django.urls import path
def target(request):  # normal view -> should_append_slash defaults True
    from django.http import HttpResponse
    return HttpResponse("ok")
mod.urlpatterns = [path("target/", target)]
sys.modules["probe_urlconf"] = mod

rf = RequestFactory()
req = rf.get("/target", data={"id": "123"})   # no trailing slash, query id=123
print("path=%r path_info=%r QS=%r" % (req.path, req.path_info, req.META.get("QUERY_STRING")))

site = AdminSite()
resp = site.catch_all_view(req, "target")
loc = resp.get("Location") if hasattr(resp, "get") else None
code = getattr(resp, "status_code", None)
is301 = isinstance(resp, HttpResponsePermanentRedirect) and code == 301
print("status=%s location=%r is301=%s" % (code, loc, is301))

ok = is301 and loc == "/target/?id=123"
print("CRITERION query-preserved-301:", ok)
sys.exit(0 if ok else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""Req 1.3 & 3.5: known URL missing slash, NO query string -> 301 to the
slash-terminated path with NO '?' and no query component. (Unchanged legacy
behavior.) HOLDS patched AND base."""
import sys, types
import django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True, ALLOWED_HOSTS=["*"], APPEND_SLASH=True,
        ROOT_URLCONF="probe_urlconf", DATABASES={}, INSTALLED_APPS=[], SECRET_KEY="x")
django.setup()
from django.http import HttpResponsePermanentRedirect, HttpResponse
from django.test import RequestFactory
from django.contrib.admin.sites import AdminSite
from django.urls import path
mod = types.ModuleType("probe_urlconf")
def target(request): return HttpResponse("ok")
mod.urlpatterns = [path("target/", target)]
sys.modules["probe_urlconf"] = mod

req = RequestFactory().get("/target")   # no query string
site = AdminSite()
resp = site.catch_all_view(req, "target")
loc = resp.get("Location"); code = resp.status_code
print("status=%s location=%r" % (code, loc))
ok = isinstance(resp, HttpResponsePermanentRedirect) and code == 301 and loc == "/target/"
print("CRITERION no-query-301-plain-slash:", ok)
sys.exit(0 if ok else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""Req 2 (script-name/prefix): request served under SCRIPT_NAME prefix with a
query string -> 301 whose Location includes the prefix in the path AND the
query string after a single '?'. Derived from full path, not prefix-stripped.
HOLDS patched; FAILS at base (query dropped)."""
import sys, types
import django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True, ALLOWED_HOSTS=["*"], APPEND_SLASH=True,
        ROOT_URLCONF="probe_urlconf", DATABASES={}, INSTALLED_APPS=[], SECRET_KEY="x")
django.setup()
from django.http import HttpResponsePermanentRedirect, HttpResponse
from django.test import RequestFactory
from django.contrib.admin.sites import AdminSite
from django.urls import path
mod = types.ModuleType("probe_urlconf")
def target(request): return HttpResponse("ok")
mod.urlpatterns = [path("target/", target)]
sys.modules["probe_urlconf"] = mod

# SCRIPT_NAME prefix -> request.path includes /prefix, path_info does not
req = RequestFactory().get("/target", data={"id": "1"}, SCRIPT_NAME="/prefix")
print("path=%r path_info=%r QS=%r" % (req.path, req.path_info, req.META.get("QUERY_STRING")))
site = AdminSite()
resp = site.catch_all_view(req, "target")
loc = resp.get("Location"); code = resp.status_code
print("status=%s location=%r" % (code, loc))
ok = (isinstance(resp, HttpResponsePermanentRedirect) and code == 301
      and loc == "/prefix/target/?id=1")
print("CRITERION prefix+query preserved:", ok)
sys.exit(0 if ok else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""Req 3.1 (regression): APPEND_SLASH=True but the resolved target view opts
OUT of slash-appending (should_append_slash=False) -> catch_all_view SHALL NOT
redirect and SHALL raise Http404. HOLDS patched AND base."""
import sys, types
import django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True, ALLOWED_HOSTS=["*"], APPEND_SLASH=True,
        ROOT_URLCONF="probe_urlconf", DATABASES={}, INSTALLED_APPS=[], SECRET_KEY="x")
django.setup()
from django.http import Http404, HttpResponse
from django.test import RequestFactory
from django.contrib.admin.sites import AdminSite
from django.urls import path
from django.views.decorators.common import no_append_slash
mod = types.ModuleType("probe_urlconf")
@no_append_slash
def target(request): return HttpResponse("ok")
mod.urlpatterns = [path("target/", target)]
sys.modules["probe_urlconf"] = mod

req = RequestFactory().get("/target", data={"id": "1"})
site = AdminSite()
raised = False; resp = None
try:
    resp = site.catch_all_view(req, "target")
except Http404:
    raised = True
print("raised_404=%s resp=%r" % (raised, resp))
ok = raised and resp is None
print("CRITERION opt-out->404:", ok)
sys.exit(0 if ok else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""Req 3.2 & 3.3 (regression): (a) APPEND_SLASH=False with a query string ->
Http404, no redirect; (b) appending a slash does NOT resolve to any view ->
Http404. HOLDS patched AND base."""
import sys, types
import django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True, ALLOWED_HOSTS=["*"], APPEND_SLASH=True,
        ROOT_URLCONF="probe_urlconf", DATABASES={}, INSTALLED_APPS=[], SECRET_KEY="x")
django.setup()
from django.http import Http404, HttpResponse
from django.test import RequestFactory
from django.contrib.admin.sites import AdminSite
from django.urls import path
from django.conf import settings as S
mod = types.ModuleType("probe_urlconf")
def target(request): return HttpResponse("ok")
mod.urlpatterns = [path("target/", target)]
sys.modules["probe_urlconf"] = mod
site = AdminSite()

# (a) APPEND_SLASH=False, known url + query -> 404 regardless of query
S.APPEND_SLASH = False
r1 = RequestFactory().get("/target", data={"id": "1"})
a_ok = False
try:
    site.catch_all_view(r1, "target")
except Http404:
    a_ok = True
print("append_slash_false -> 404:", a_ok)

# (b) APPEND_SLASH=True but slash-appended path does not resolve -> 404
S.APPEND_SLASH = True
r2 = RequestFactory().get("/nonexistent", data={"id": "1"})
b_ok = False
try:
    site.catch_all_view(r2, "nonexistent")
except Http404:
    b_ok = True
print("unresolved-slash -> 404:", b_ok)

ok = a_ok and b_ok
print("CRITERION false/unresolved->404:", ok)
sys.exit(0 if ok else 1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
"""Req 1.4 & 1.5: exactly one trailing slash (never doubled) AND the query
string preserves parameter order + is URI-encoded as get_full_path encodes it.
Use a multi-param, order-sensitive, space-containing query.
HOLDS patched; FAILS at base (query dropped)."""
import sys, types
import django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True, ALLOWED_HOSTS=["*"], APPEND_SLASH=True,
        ROOT_URLCONF="probe_urlconf", DATABASES={}, INSTALLED_APPS=[], SECRET_KEY="x")
django.setup()
from django.http import HttpResponsePermanentRedirect, HttpResponse
from django.test import RequestFactory
from django.contrib.admin.sites import AdminSite
from django.urls import path
mod = types.ModuleType("probe_urlconf")
def target(request): return HttpResponse("ok")
mod.urlpatterns = [path("target/", target)]
sys.modules["probe_urlconf"] = mod

# order-sensitive: b before a; a space to exercise encoding
qs = "b=2&a=1&q=x y"
req = RequestFactory().get("/target?" + qs)
print("QS=%r" % req.META.get("QUERY_STRING"))
site = AdminSite()
resp = site.catch_all_view(req, "target")
loc = resp.get("Location"); code = resp.status_code
print("location=%r" % loc)

# exactly one trailing slash on path component (before '?')
pathpart = loc.split("?", 1)[0]
single_slash = pathpart == "/target/" and not pathpart.endswith("//")
# query preserved w/ order and encoding matching get_full_path
expected = req.get_full_path(force_append_slash=True)
print("expected(get_full_path)=%r single_slash=%s" % (expected, single_slash))
ok = (isinstance(resp, HttpResponsePermanentRedirect) and code == 301
      and single_slash and loc == expected and loc.startswith("/target/?b=2&a=1&q="))
print("CRITERION order+encoding+single-slash:", ok)
sys.exit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Positive control / Req 1.1,1.2,1.5: APPEND_SLASH=True, staff-less direct
call to catch_all_view for a known URL missing its slash WITH a query string
-> HTTP 301 whose Location is the slash-terminated path + '?' + same query.
HOLDS on patched (query preserved); FAILS at base (query dropped)."""
import sys, types
import django
from django.conf import settings

if not settings.configured:
    settings.configure(
        DEBUG=True, ALLOWED_HOSTS=["*"], APPEND_SLASH=True,
        ROOT_URLCONF="probe_urlconf",
        DATABASES={}, INSTALLED_APPS=[], SECRET_KEY="x",
    )
django.setup()

from django.http import HttpResponsePermanentRedirect
from django.test import RequestFactory
from django.contrib.admin.sites import AdminSite

# urlconf where the slash-appended path resolves to a normal view
mod = types.ModuleType("probe_urlconf")
from django.urls import path
def target(request):  # normal view -> should_append_slash defaults True
    from django.http import HttpResponse
    return HttpResponse("ok")
mod.urlpatterns = [path("target/", target)]
sys.modules["probe_urlconf"] = mod

rf = RequestFactory()
req = rf.get("/target", data={"id": "123"})   # no trailing slash, query id=123
print("path=%r path_info=%r QS=%r" % (req.path, req.path_info, req.META.get("QUERY_STRING")))

site = AdminSite()
resp = site.catch_all_view(req, "target")
loc = resp.get("Location") if hasattr(resp, "get") else None
code = getattr(resp, "status_code", None)
is301 = isinstance(resp, HttpResponsePermanentRedirect) and code == 301
print("status=%s location=%r is301=%s" % (code, loc, is301))

ok = is301 and loc == "/target/?id=123"
print("CRITERION query-preserved-301:", ok)
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance django__django-16612: catch_all_view must preserve query string when appending trailing slash. Gold fix: return HttpResponsePermanentRedirect(request.get_full_path(force_append_slash=True)).

Probes drive AdminSite().catch_all_view directly with RequestFactory + a dynamic urlconf whose slash-appended path resolves. Requirement coverage:
- probe_1 (Req 1.1/1.2/1.5, POSITIVE CONTROL): known URL missing slash + query id=123 -> 301 Location '/target/?id=123'. HOLDS patched, VIOLATED at base (base gives '/target/'). Discriminates.
- probe_2 (Req 1.3/3.5): no query string -> 301 to '/target/' with no '?'. HOLDS patched AND base (unchanged legacy behavior).
- probe_3 (Req 2): SCRIPT_NAME=/prefix + query -> 301 '/prefix/target/?id=1'. HOLDS patched, VIOLATED at base.
- probe_4 (Req 3.1): should_append_slash=False (no_append_slash view) -> Http404, no redirect. HOLDS patched AND base.
- probe_5 (Req 3.2/3.3): APPEND_SLASH=False+query -> 404; slash-appended path unresolved -> 404. HOLDS patched AND base.
- probe_6 (Req 1.4/1.5): multi-param order-sensitive space-containing query 'b=2&a=1&q=x y' -> exactly one trailing slash, order preserved, URI-encoded exactly as get_full_path (=> '/target/?b=2&a=1&q=x%20y'). HOLDS patched, VIOLATED at base.

### CANDIDATE WRONG PATCHES (both apply at base, both REJECTED by the suite):
- weak_A ('%s/?%s' % (request.path, QUERY_STRING)): naive always-append. REJECTED by probe_2 (empty-query case yields dangling '/target/?'). Passes 1,3,4,5,6 but the suite discriminates it.
- weak_B (request.get_full_path() WITHOUT force_append_slash=True): the lazy get_full_path reading. REJECTED by probes 1,2,3,6 (trailing slash missing -> Location '/target' etc). This is the plausible weak reading of Req that omits the slash; suite catches it.

All 6 probes HOLD on the gold-patched tree; positive control (probe_1) FAILS at base and HOLDS patched (prepatch reproduced). No requirements VIOLATION found; no probe-conforming alternative patch found (both candidates rejected). Verdict SOUND. Runs executed in the official instance Docker image via nl_attack probe runner.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 requirement probes hold on the patched tree; 2/2 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 6 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 6 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 2 alternative candidate patches, claimed to satisfy every cited requirement, and ran the same suite against them. The suite rejected all 2: a probe encoding a cited requirement fails under each of those, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

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
"""Positive control / Req 1.1,1.2,1.5: APPEND_SLASH=True, staff-less direct
call to catch_all_view for a known URL missing its slash WITH a query string
-> HTTP 301 whose Location is the slash-terminated path + '?' + same query.
HOLDS on patched (query preserved); FAILS at base (query dropped)."""
import sys, types
import django
from django.conf import settings

if not settings.configured:
    settings.configure(
        DEBUG=True, ALLOWED_HOSTS=["*"], APPEND_SLASH=True,
        ROOT_URLCONF="probe_urlconf",
        DATABASES={}, INSTALLED_APPS=[], SECRET_KEY="x",
    )
django.setup()

from django.http import HttpResponsePermanentRedirect
from django.test import RequestFactory
from django.contrib.admin.sites import AdminSite

# urlconf where the slash-appended path resolves to a normal view
mod = types.ModuleType("probe_urlconf")
from django.urls import path
def target(request):  # normal view -> should_append_slash defaults True
    from django.http import HttpResponse
    return HttpResponse("ok")
mod.urlpatterns = [path("target/", target)]
sys.modules["probe_urlconf"] = mod

rf = RequestFactory()
req = rf.get("/target", data={"id": "123"})   # no trailing slash, query id=123
print("path=%r path_info=%r QS=%r" % (req.path, req.path_info, req.META.get("QUERY_STRING")))

site = AdminSite()
resp = site.catch_all_view(req, "target")
loc = resp.get("Location") if hasattr(resp, "get") else None
code = getattr(resp, "status_code", None)
is301 = isinstance(resp, HttpResponsePermanentRedirect) and code == 301
print("status=%s location=%r is301=%s" % (code, loc, is301))

ok = is301 and loc == "/target/?id=123"
print("CRITERION query-preserved-301:", ok)
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance django__django-16612: catch_all_view must preserve query string when appending trailing slash. Gold fix: return HttpResponsePermanentRedirect(request.get_full_path(force_append_slash=True)).

Probes drive AdminSite().catch_all_view directly with RequestFactory + a dynamic urlconf whose slash-appended path resolves. Requirement coverage:
- probe_1 (Req 1.1/1.2/1.5, POSITIVE CONTROL): known URL missing slash + query id=123 -> 301 Location '/target/?id=123'. HOLDS patched, VIOLATED at base (base gives '/target/'). Discriminates.
- probe_2 (Req 1.3/3.5): no query string -> 301 to '/target/' with no '?'. HOLDS patched AND base (unchanged legacy behavior).
- probe_3 (Req 2): SCRIPT_NAME=/prefix + query -> 301 '/prefix/target/?id=1'. HOLDS patched, VIOLATED at base.
- probe_4 (Req 3.1): should_append_slash=False (no_append_slash view) -> Http404, no redirect. HOLDS patched AND base.
- probe_5 (Req 3.2/3.3): APPEND_SLASH=False+query -> 404; slash-appended path unresolved -> 404. HOLDS patched AND base.
- probe_6 (Req 1.4/1.5): multi-param order-sensitive space-containing query 'b=2&a=1&q=x y' -> exactly one trailing slash, order preserved, URI-encoded exactly as get_full_path (=> '/target/?b=2&a=1&q=x%20y'). HOLDS patched, VIOLATED at base.

### CANDIDATE WRONG PATCHES (both apply at base, both REJECTED by the suite):
- weak_A ('%s/?%s' % (request.path, QUERY_STRING)): naive always-append. REJECTED by probe_2 (empty-query case yields dangling '/target/?'). Passes 1,3,4,5,6 but the suite discriminates it.
- weak_B (request.get_full_path() WITHOUT force_append_slash=True): the lazy get_full_path reading. REJECTED by probes 1,2,3,6 (trailing slash missing -> Location '/target' etc). This is the plausible weak reading of Req that omits the slash; suite catches it.

All 6 probes HOLD on the gold-patched tree; positive control (probe_1) FAILS at base and HOLDS patched (prepatch reproduced). No requirements VIOLATION found; no probe-conforming alternative patch found (both candidates rejected). Verdict SOUND. Runs executed in the official instance Docker image via nl_attack probe runner.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Probed on gold-patched tree (settings.configure + AdminSite().catch_all_view): '/admin/foo?id=123' -> ('REDIRECT',301,'/admin/foo/?id=123') [Req 1.1,1.2,1.4,1.5]; '/admin/foo' -> ('REDIRECT',301,'/admin/foo/') [Req 1.3,3.5]; '/admin/foo/' (already slash) -> 404 [Req 3.3]; APPEND_SLASH=False -> 404 [Req 3.2]; SCRIPT_NAME='/prefix/' -> ('REDIRECT',301,'/prefix/admin/foo/?id=123') [Req 2.1,2.2,2.3]; unknown '/admin/bar' -> 404 [Req 3.3]. get_full_path implementation in image confirmed to build path+('/' if force_append_slash and not endswith('/'))+('?'+iri_to_uri(QUERY_STRING) if QUERY_STRING) — matches Req 1.4/1.5 encoding claims and single-slash guarantee. Req 3.4 (login redirect with url-encoded ?id in next) is pre-existing unchanged behavior corroborated by the passing gold test test_missing_slash_append_slash_true_non_staff_user_query_string (G-RESOLVE=pass). Req 3.1 (should_append_slash False -> 404) matches the unchanged getattr guard. No mandated-but-absent, forbidden-but-present, wrong-boundary, or invented behavior found.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The requirements localize the change to legitimate targets (AdminSite.catch_all_view in django/contrib/admin/sites.py; HttpRequest.get_full_path in django/http/request.py) and translate test intent into behavioral acceptance criteria. get_full_path appears only in hints_text/gold, but naming the fix's function for localization is permitted; force_append_slash is never quoted in prose and is a pre-existing Django parameter (not fix-invented). Req-3 enumerations (opt-out->404, APPEND_SLASH=False->404, already-slashed, non-staff login redirect with URL-encoded `next`, no-query-string unchanged, without-final-catch-all-view) map onto the FAIL_TO_PASS/PASS_TO_PASS/added tests but are stated as behavior (status codes + redirect targets), not test code. No test file path, no test method names, no parametrization ids, no verbatim test/gold literals (e.g. `?id=1`, `%3Fid%3D1`, SCRIPT_NAME="/prefix/", admin10:) are transmitted. The `?id=123`/`.../foo` example comes from the PUBLIC problem_statement. No semantic gold-reconstruction beyond the public problem statement.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
