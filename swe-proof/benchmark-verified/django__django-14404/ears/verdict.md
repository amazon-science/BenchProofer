# P2 adversarial audit — django__django-14404

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
"""Req 1.1/1.2 + positive control: per-request SCRIPT_NAME prefix.
The redirect target MUST be the outward-facing path '/prefix/foo/'
(begins with the prefix), NOT the internal '/foo/'."""
import sys, types
from django.conf import settings
settings.configure(DEBUG=True, APPEND_SLASH=True, FORCE_SCRIPT_NAME=None,
    ROOT_URLCONF='_u', ALLOWED_HOSTS=['*'], SECRET_KEY='x', DATABASES={},
    INSTALLED_APPS=[], USE_TZ=True)
import django; django.setup()
from django.urls import path
def v(r): return None
mod = types.ModuleType('_u'); mod.urlpatterns=[path('foo/', v, name='foo')]
sys.modules['_u']=mod
from django.test import RequestFactory
from django.contrib.admin.sites import AdminSite
req = RequestFactory().get('/foo', SCRIPT_NAME='/prefix/')
print("path_info=", req.path_info, "path=", req.path)
resp = AdminSite().catch_all_view(req, 'foo')
loc = resp['Location']
print("redirect Location=", loc, "status=", resp.status_code)
assert loc == '/prefix/foo/', f"expected /prefix/foo/ got {loc!r}"
assert loc.startswith('/prefix/'), "target must begin with script-name prefix"
print("OK")
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""Req 1.3: FORCE_SCRIPT_NAME global prefix. Even though the request env
carries no prefix, the redirect target MUST begin with the forced prefix."""
import sys, types
from django.conf import settings
settings.configure(DEBUG=True, APPEND_SLASH=True, FORCE_SCRIPT_NAME='/prefix/',
    ROOT_URLCONF='_u', ALLOWED_HOSTS=['*'], SECRET_KEY='x', DATABASES={},
    INSTALLED_APPS=[], USE_TZ=True)
import django; django.setup()
from django.urls import path
def v(r): return None
mod = types.ModuleType('_u'); mod.urlpatterns=[path('foo/', v, name='foo')]
sys.modules['_u']=mod
from django.test import RequestFactory
from django.contrib.admin.sites import AdminSite
req = RequestFactory().get('/foo')  # env has no prefix; FORCE_SCRIPT_NAME applies
print("path_info=", req.path_info, "path=", req.path)
resp = AdminSite().catch_all_view(req, 'foo')
loc = resp['Location']
print("redirect Location=", loc, "status=", resp.status_code)
assert loc == '/prefix/foo/', f"expected /prefix/foo/ got {loc!r}"
assert loc.startswith('/prefix/'), "target must begin with forced prefix"
print("OK")
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""Req 1.4 + 1.5 + 4.3: no prefix. Redirect target == locator + '/',
and it's an HTTP 301 permanent redirect."""
import sys, types
from django.conf import settings
settings.configure(DEBUG=True, APPEND_SLASH=True, FORCE_SCRIPT_NAME=None,
    ROOT_URLCONF='_u', ALLOWED_HOSTS=['*'], SECRET_KEY='x', DATABASES={},
    INSTALLED_APPS=[], USE_TZ=True)
import django; django.setup()
from django.urls import path
def v(r): return None
mod = types.ModuleType('_u'); mod.urlpatterns=[path('foo/', v, name='foo')]
sys.modules['_u']=mod
from django.test import RequestFactory
from django.contrib.admin.sites import AdminSite
from django.http import HttpResponsePermanentRedirect
req = RequestFactory().get('/foo')
resp = AdminSite().catch_all_view(req, 'foo')
loc = resp['Location']
print("Location=", loc, "status=", resp.status_code, "type=", type(resp).__name__)
assert loc == '/foo/', f"expected /foo/ got {loc!r}"
assert resp.status_code == 301, f"expected 301 got {resp.status_code}"
assert isinstance(resp, HttpResponsePermanentRedirect)
print("OK")
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""Req 3.1/3.2 + 4.1: preconditions & non-redirectable => Http404, no redirect.
- APPEND_SLASH disabled -> Http404
- url already ends with '/' -> Http404
- slash-appended locator not recognized -> Http404 (no redirect)"""
import sys, types
from django.conf import settings
settings.configure(DEBUG=True, APPEND_SLASH=True, FORCE_SCRIPT_NAME=None,
    ROOT_URLCONF='_u', ALLOWED_HOSTS=['*'], SECRET_KEY='x', DATABASES={},
    INSTALLED_APPS=[], USE_TZ=True)
import django; django.setup()
from django.urls import path
def v(r): return None
mod = types.ModuleType('_u'); mod.urlpatterns=[path('foo/', v, name='foo')]
sys.modules['_u']=mod
from django.test import RequestFactory
from django.contrib.admin.sites import AdminSite
from django.http import Http404
rf = RequestFactory()
site = AdminSite()

# 3.1 APPEND_SLASH disabled
settings.APPEND_SLASH = False
try:
    site.catch_all_view(rf.get('/foo'), 'foo')
    print("FAIL: expected Http404 with APPEND_SLASH off"); sys.exit(1)
except Http404:
    print("APPEND_SLASH off -> Http404 OK")
settings.APPEND_SLASH = True

# 3.2 url already ends with slash
try:
    site.catch_all_view(rf.get('/foo/'), 'foo/')
    print("FAIL: expected Http404 for trailing-slash url"); sys.exit(1)
except Http404:
    print("trailing-slash url -> Http404 OK")

# 4.1 slash-appended locator not recognized
try:
    site.catch_all_view(rf.get('/nope'), 'nope')
    print("FAIL: expected Http404 for unrecognized"); sys.exit(1)
except Http404:
    print("unrecognized -> Http404 OK")
print("OK")
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""Req 4.2: matched view with should_append_slash=False -> Http404, no redirect,
even under a script-name prefix (decision must be independent of prefix)."""
import sys, types
from django.conf import settings
settings.configure(DEBUG=True, APPEND_SLASH=True, FORCE_SCRIPT_NAME=None,
    ROOT_URLCONF='_u', ALLOWED_HOSTS=['*'], SECRET_KEY='x', DATABASES={},
    INSTALLED_APPS=[], USE_TZ=True)
import django; django.setup()
from django.urls import path
def v(r): return None
v.should_append_slash = False
mod = types.ModuleType('_u'); mod.urlpatterns=[path('noslash/', v, name='ns')]
sys.modules['_u']=mod
from django.test import RequestFactory
from django.contrib.admin.sites import AdminSite
from django.http import Http404
site = AdminSite()
for sn in (None, '/prefix/'):
    kw = {} if sn is None else {'SCRIPT_NAME': sn}
    req = RequestFactory().get('/noslash', **kw)
    try:
        site.catch_all_view(req, 'noslash')
        print(f"FAIL: expected Http404 with should_append_slash=False (sn={sn})"); sys.exit(1)
    except Http404:
        print(f"should_append_slash=False (sn={sn}) -> Http404 OK")
print("OK")
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
"""Req 2.1/2.3: resolution probe uses the INTERNAL routing path.
Under a script-name prefix, the request env path_info is '/foo' (prefix stripped).
resolve() must be attempted against '/foo/' (internal) -> recognized -> redirect.
If the view wrongly resolved the outward path '/prefix/foo/', resolution would
FAIL (no such pattern) and it would 404. So a successful redirect proves the
probe used the internal path. Also confirms decision independent of prefix."""
import sys, types
from django.conf import settings
settings.configure(DEBUG=True, APPEND_SLASH=True, FORCE_SCRIPT_NAME=None,
    ROOT_URLCONF='_u', ALLOWED_HOSTS=['*'], SECRET_KEY='x', DATABASES={},
    INSTALLED_APPS=[], USE_TZ=True)
import django; django.setup()
from django.urls import path
def v(r): return None
mod = types.ModuleType('_u'); mod.urlpatterns=[path('foo/', v, name='foo')]
sys.modules['_u']=mod
from django.test import RequestFactory
from django.contrib.admin.sites import AdminSite
from django.http import Http404
site = AdminSite()

# with prefix: internal path '/foo' resolves as '/foo/' -> redirect happens
req = RequestFactory().get('/foo', SCRIPT_NAME='/prefix/')
print("path_info=", req.path_info)
try:
    resp = site.catch_all_view(req, 'foo')
except Http404:
    print("FAIL: 404 -> probe did not use internal routing path"); sys.exit(1)
print("resolved via internal path -> Location=", resp['Location'])
assert resp['Location'] == '/prefix/foo/'

# decision independent of prefix: same recognition with and without prefix
req2 = RequestFactory().get('/foo')
resp2 = site.catch_all_view(req2, 'foo')
print("no-prefix Location=", resp2['Location'])
assert resp2['Location'] == '/foo/'
print("OK")
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Req 1.1/1.2 + positive control: per-request SCRIPT_NAME prefix.
The redirect target MUST be the outward-facing path '/prefix/foo/'
(begins with the prefix), NOT the internal '/foo/'."""
import sys, types
from django.conf import settings
settings.configure(DEBUG=True, APPEND_SLASH=True, FORCE_SCRIPT_NAME=None,
    ROOT_URLCONF='_u', ALLOWED_HOSTS=['*'], SECRET_KEY='x', DATABASES={},
    INSTALLED_APPS=[], USE_TZ=True)
import django; django.setup()
from django.urls import path
def v(r): return None
mod = types.ModuleType('_u'); mod.urlpatterns=[path('foo/', v, name='foo')]
sys.modules['_u']=mod
from django.test import RequestFactory
from django.contrib.admin.sites import AdminSite
req = RequestFactory().get('/foo', SCRIPT_NAME='/prefix/')
print("path_info=", req.path_info, "path=", req.path)
resp = AdminSite().catch_all_view(req, 'foo')
loc = resp['Location']
print("redirect Location=", loc, "status=", resp.status_code)
assert loc == '/prefix/foo/', f"expected /prefix/foo/ got {loc!r}"
assert loc.startswith('/prefix/'), "target must begin with script-name prefix"
print("OK")
```

Prepatch bug re-encoded as an attack: `True`.

django-14404: catch_all_view trailing-slash redirect must target the outward-facing request.path (incl. script-name prefix), while the resolution probe still uses internal request.path_info.

Probes (all HOLD on gold-patched):
- probe_1 (Req 1.1/1.2, POSITIVE CONTROL): per-request SCRIPT_NAME='/prefix/', locator '/foo' -> Location must == '/prefix/foo/'. HOLDS patched, VIOLATED at base (base gives '/foo/').
- probe_2 (Req 1.3): FORCE_SCRIPT_NAME='/prefix/' with no env prefix -> Location must == '/prefix/foo/'. HOLDS patched, VIOLATED at base.
- probe_3 (Req 1.4/1.5/4.3): no prefix -> Location == '/foo/', 301 HttpResponsePermanentRedirect. HOLDS.
- probe_4 (Req 3.1/3.2/4.1): APPEND_SLASH off -> Http404; url already '/'-terminated -> Http404; unrecognized locator -> Http404. HOLDS.
- probe_5 (Req 4.2): matched view with should_append_slash=False -> Http404 (with and without prefix). HOLDS.
- probe_6 (Req 2.1/2.3): under prefix, internal path_info '/foo' resolves as '/foo/' -> redirect succeeds (proves probe used internal path, not outward '/prefix/foo/' which wouldn't resolve); decision independent of prefix. HOLDS patched, VIOLATED at base.

Discriminating power: probe_1, probe_2, probe_6 all FAIL at base_commit (de32fe83), confirming the positive-control leg.

Candidate wrong-fix 'weak_keep_path_info': naive fix that leaves the redirect target as request.path_info (the base behavior for the target). REJECTED by probes 1, 2, and 6 (they observe '/foo/' instead of '/prefix/foo/'), while probes 3/4/5 still pass. This demonstrates the suite discriminates the lazy reading that a weak spec would permit. No probe-conforming alternative patch was found -> no TOO-WEAK finding.

Verdict SOUND: 6 distinct probes covering all 4 requirements (behavioral SHALLs, boundary/precondition cases, and the should_append_slash regression), all hold on the patched tree; positive control discriminates base vs patched; wrong-fix candidate is rejected.

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
"""Req 1.1/1.2 + positive control: per-request SCRIPT_NAME prefix.
The redirect target MUST be the outward-facing path '/prefix/foo/'
(begins with the prefix), NOT the internal '/foo/'."""
import sys, types
from django.conf import settings
settings.configure(DEBUG=True, APPEND_SLASH=True, FORCE_SCRIPT_NAME=None,
    ROOT_URLCONF='_u', ALLOWED_HOSTS=['*'], SECRET_KEY='x', DATABASES={},
    INSTALLED_APPS=[], USE_TZ=True)
import django; django.setup()
from django.urls import path
def v(r): return None
mod = types.ModuleType('_u'); mod.urlpatterns=[path('foo/', v, name='foo')]
sys.modules['_u']=mod
from django.test import RequestFactory
from django.contrib.admin.sites import AdminSite
req = RequestFactory().get('/foo', SCRIPT_NAME='/prefix/')
print("path_info=", req.path_info, "path=", req.path)
resp = AdminSite().catch_all_view(req, 'foo')
loc = resp['Location']
print("redirect Location=", loc, "status=", resp.status_code)
assert loc == '/prefix/foo/', f"expected /prefix/foo/ got {loc!r}"
assert loc.startswith('/prefix/'), "target must begin with script-name prefix"
print("OK")
```

Prepatch bug re-encoded as an attack: `True`.

django-14404: catch_all_view trailing-slash redirect must target the outward-facing request.path (incl. script-name prefix), while the resolution probe still uses internal request.path_info.

Probes (all HOLD on gold-patched):
- probe_1 (Req 1.1/1.2, POSITIVE CONTROL): per-request SCRIPT_NAME='/prefix/', locator '/foo' -> Location must == '/prefix/foo/'. HOLDS patched, VIOLATED at base (base gives '/foo/').
- probe_2 (Req 1.3): FORCE_SCRIPT_NAME='/prefix/' with no env prefix -> Location must == '/prefix/foo/'. HOLDS patched, VIOLATED at base.
- probe_3 (Req 1.4/1.5/4.3): no prefix -> Location == '/foo/', 301 HttpResponsePermanentRedirect. HOLDS.
- probe_4 (Req 3.1/3.2/4.1): APPEND_SLASH off -> Http404; url already '/'-terminated -> Http404; unrecognized locator -> Http404. HOLDS.
- probe_5 (Req 4.2): matched view with should_append_slash=False -> Http404 (with and without prefix). HOLDS.
- probe_6 (Req 2.1/2.3): under prefix, internal path_info '/foo' resolves as '/foo/' -> redirect succeeds (proves probe used internal path, not outward '/prefix/foo/' which wouldn't resolve); decision independent of prefix. HOLDS patched, VIOLATED at base.

Discriminating power: probe_1, probe_2, probe_6 all FAIL at base_commit (de32fe83), confirming the positive-control leg.

Candidate wrong-fix 'weak_keep_path_info': naive fix that leaves the redirect target as request.path_info (the base behavior for the target). REJECTED by probes 1, 2, and 6 (they observe '/foo/' instead of '/prefix/foo/'), while probes 3/4/5 still pass. This demonstrates the suite discriminates the lazy reading that a weak spec would permit. No probe-conforming alternative patch was found -> no TOO-WEAK finding.

Verdict SOUND: 6 distinct probes covering all 4 requirements (behavioral SHALLs, boundary/precondition cases, and the should_append_slash regression), all hold on the patched tree; positive control discriminates base vs patched; wrong-fix candidate is rejected.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Modeling boundary is correct: R1 pins the outward-facing request.path (the changed expression), R2 explicitly preserves request.path_info for the resolution probe (the unchanged expression), and R2.3/R1.4 correctly assert the redirect DECISION is prefix-independent while only the TARGET changes. No requirement mandates behavior the patch lacks, forbids behavior it has, or invents behavior. should_append_slash gating (R4.2/R4.3) and 301 (R1.5) match HttpResponsePermanentRedirect and the getattr(match.func,'should_append_slash',True) check verbatim.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The public problem_statement already discloses FORCE_SCRIPT_NAME, the request.path vs request.path_info distinction, and the trailing-slash redirect. Requirement 1's two sub-cases (per-request SCRIPT_NAME and global FORCE_SCRIPT_NAME) parallel the two FAIL_TO_PASS tests but are the two natural mechanisms of a script-name prefix — FORCE_SCRIPT_NAME is named publicly and per-request SCRIPT_NAME is standard WSGI/request.path behavior, so this is behavioral description, not test reconstruction. All identifiers used (should_append_slash, APPEND_SLASH, Http404, resolve, urlconf, catch_all_view) are pre-existing symbols in the shipped source, legitimate for localization; none are gold-invented. No test names/paths/ids, no quoted test/gold code (the '/prefix/' literal, reverse(...) target, 403 target_status_code, fetch_redirect_response=False never appear). The 301 and 404 outcomes are pre-existing view behavior. No semantic leak beyond the public statement.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
