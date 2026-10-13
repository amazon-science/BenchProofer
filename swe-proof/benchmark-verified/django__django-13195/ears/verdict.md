# P2 adversarial audit — django__django-13195

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
"""Positive control (Req 1.2): delete_cookie(samesite='lax') -> cookie samesite == 'lax'.
At base, delete_cookie has no samesite param -> TypeError -> fails."""
import django
from django.conf import settings
if not settings.configured:
    settings.configure(DEFAULT_CHARSET='utf-8')
django.setup()
from django.http import HttpResponse

r = HttpResponse()
r.delete_cookie('mykey', samesite='lax')
c = r.cookies['mykey']
print("samesite=", repr(c['samesite']), "max-age=", repr(c['max-age']))
assert c['samesite'] == 'lax', "samesite not lax"
print("OK")
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""Req 2.1 & 2.2: delete_cookie(samesite='None') -> secure True (case-insensitive)."""
import django
from django.conf import settings
if not settings.configured:
    settings.configure(DEFAULT_CHARSET='utf-8')
django.setup()
from django.http import HttpResponse

r = HttpResponse()
r.delete_cookie('mykey', samesite='None')  # capital N -> case-insensitive
c = r.cookies['mykey']
print("samesite=", repr(c['samesite']), "secure=", repr(c['secure']))
assert c['samesite'] == 'None'
assert c['secure'] is True or c['secure'] == True, "secure not True for none"
print("OK")
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""Req 3.1 & 2.3 & 3.3 & 3.4: default delete_cookie -> empty samesite, not secure,
max-age 0, epoch expires, path honored."""
import django
from django.conf import settings
if not settings.configured:
    settings.configure(DEFAULT_CHARSET='utf-8')
django.setup()
from django.http import HttpResponse

r = HttpResponse()
r.delete_cookie('plainkey', path='/sub', domain='example.com')
c = r.cookies['plainkey']
print("samesite=", repr(c['samesite']), "secure=", repr(c['secure']),
      "max-age=", repr(c['max-age']), "expires=", repr(c['expires']),
      "path=", repr(c['path']), "domain=", repr(c['domain']))
assert c['samesite'] == '', "samesite should be empty"
assert c['secure'] == '', "secure should be empty/unset"
assert c['max-age'] == 0, "max-age must be 0"
assert c['expires'] == 'Thu, 01 Jan 1970 00:00:00 GMT', "epoch expires"
assert c['path'] == '/sub'
assert c['domain'] == 'example.com'
print("OK")
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""Req 3.2: __Secure-/__Host- keys -> secure True even with no samesite.
Req 3.5: set_cookie rejects bad samesite; accepts lax/none/strict."""
import django
from django.conf import settings
if not settings.configured:
    settings.configure(DEFAULT_CHARSET='utf-8')
django.setup()
from django.http import HttpResponse

r = HttpResponse()
r.delete_cookie('__Secure-x')
r.delete_cookie('__Host-y')
assert r.cookies['__Secure-x']['secure'] is True
assert r.cookies['__Host-y']['secure'] is True
print("prefix secure OK")

# set_cookie rejects invalid samesite
try:
    HttpResponse().set_cookie('k', 'v', samesite='bad')
    raise SystemExit("no ValueError raised for bad samesite")
except ValueError:
    print("rejected bad samesite OK")

for v in ('lax', 'none', 'strict'):
    rr = HttpResponse()
    rr.set_cookie('k', 'v', samesite=v)  # must not raise
print("accepts lax/none/strict OK")
print("OK")
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""Req 4: SessionMiddleware deletes empty session cookie with SESSION_COOKIE_SAMESITE,
honoring path/domain."""
import django
from django.conf import settings
if not settings.configured:
    settings.configure(
        DEBUG=True,
        SECRET_KEY='x',
        SESSION_COOKIE_SAMESITE='Strict',
        SESSION_COOKIE_PATH='/spath',
        SESSION_COOKIE_DOMAIN='sess.example.com',
        SESSION_ENGINE='django.contrib.sessions.backends.db',
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
        INSTALLED_APPS=['django.contrib.sessions', 'django.contrib.contenttypes', 'django.contrib.auth'],
    )
django.setup()
from django.contrib.sessions.middleware import SessionMiddleware
from django.http import HttpResponse, HttpRequest

def get_response(req):
    return HttpResponse()

mw = SessionMiddleware(get_response)
req = HttpRequest()
# Pretend the client sent a session cookie; deletion path requires it in COOKIES.
req.COOKIES[settings.SESSION_COOKIE_NAME] = 'abc'
# Fresh empty store with no session_key -> is_empty() True (mirrors Django's own test)
from importlib import import_module
engine = import_module(settings.SESSION_ENGINE)
req.session = engine.SessionStore()
req.session.accessed = True
resp = HttpResponse()
out = mw.process_response(req, resp)
name = settings.SESSION_COOKIE_NAME
print("cookies:", list(out.cookies.keys()))
if name in out.cookies:
    c = out.cookies[name]
    print("samesite=", repr(c['samesite']), "path=", repr(c['path']), "domain=", repr(c['domain']),
          "expires=", repr(c['expires']))
    assert c['samesite'] == 'Strict', "session samesite not propagated"
    assert c['path'] == '/spath'
    assert c['domain'] == 'sess.example.com'
    print("OK")
else:
    raise SystemExit("session cookie not deleted")
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
"""Req 5: CookieStorage deletes messages cookie with SESSION_COOKIE_SAMESITE,
with epoch expires."""
import django
from django.conf import settings
if not settings.configured:
    settings.configure(
        DEBUG=True,
        SECRET_KEY='x',
        SESSION_COOKIE_SAMESITE='Lax',
        SESSION_COOKIE_DOMAIN='msg.example.com',
        INSTALLED_APPS=['django.contrib.messages', 'django.contrib.contenttypes', 'django.contrib.auth'],
        MESSAGE_STORAGE='django.contrib.messages.storage.cookie.CookieStorage',
    )
django.setup()
from django.contrib.messages.storage.cookie import CookieStorage
from django.http import HttpResponse, HttpRequest

req = HttpRequest()
req.COOKIES[CookieStorage.cookie_name] = 'stale'  # pretend an existing cookie exists
storage = CookieStorage(req)
resp = HttpResponse()
# No messages -> _store should delete the cookie
storage._store([], resp)
name = CookieStorage.cookie_name
print("cookies:", list(resp.cookies.keys()))
c = resp.cookies[name]
print("samesite=", repr(c['samesite']), "domain=", repr(c['domain']), "expires=", repr(c['expires']))
assert c['samesite'] == 'Lax', "messages samesite not propagated"
assert c['expires'] == 'Thu, 01 Jan 1970 00:00:00 GMT'
print("OK")
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Positive control (Req 1.2): delete_cookie(samesite='lax') -> cookie samesite == 'lax'.
At base, delete_cookie has no samesite param -> TypeError -> fails."""
import django
from django.conf import settings
if not settings.configured:
    settings.configure(DEFAULT_CHARSET='utf-8')
django.setup()
from django.http import HttpResponse

r = HttpResponse()
r.delete_cookie('mykey', samesite='lax')
c = r.cookies['mykey']
print("samesite=", repr(c['samesite']), "max-age=", repr(c['max-age']))
assert c['samesite'] == 'lax', "samesite not lax"
print("OK")
```

Prepatch bug re-encoded as an attack: `True`.

Probes and criteria (all HOLD on gold-patched tree):
- probe_1 (Req 1.2, POSITIVE CONTROL): delete_cookie(samesite='lax') -> cookie samesite=='lax'. HOLDS patched; FAILS at base (TypeError: delete_cookie() got no kwarg 'samesite'). Discriminates.
- probe_2 (Req 2.1/2.2): delete_cookie(samesite='None') -> secure is True, case-insensitive. HOLDS patched.
- probe_3 (Req 3.1/2.3/3.3/3.4): default delete_cookie -> empty samesite, empty secure, max-age 0, epoch expires, path+domain honored. HOLDS patched.
- probe_4 (Req 3.2/3.5): __Secure-/__Host- keys secure True with no samesite; set_cookie rejects invalid samesite and accepts lax/none/strict. HOLDS patched.
- probe_5 (Req 4.1/4.2/4.3): SessionMiddleware deletes empty session cookie with SESSION_COOKIE_SAMESITE, honoring SESSION_COOKIE_PATH/DOMAIN. HOLDS patched.
- probe_6 (Req 5.1/5.2/5.3): CookieStorage deletes messages cookie with SESSION_COOKIE_SAMESITE and epoch expires. HOLDS patched.

CANDIDATE PATCH (weak_no_secure_no_propagate): adds samesite kwarg to delete_cookie and threads it into set_cookie but (a) omits the Secure-on-'none' rule and (b) leaves session middleware and messages storage delete calls unchanged. Under this candidate: probe_1,3,4 HOLD but probe_2 REJECTS (secure not set for none), probe_5 REJECTS (session samesite not propagated), probe_6 REJECTS (messages samesite not propagated). => suite discriminates a plausible weak fix; no requirements-conforming alternative found.

All 6 probes HOLD on patched; positive control fails at base. No violation found; suite rejects the weak candidate on 3 distinct legs (Req 2, Req 4, Req 5). Verdict SOUND.

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
"""Positive control (Req 1.2): delete_cookie(samesite='lax') -> cookie samesite == 'lax'.
At base, delete_cookie has no samesite param -> TypeError -> fails."""
import django
from django.conf import settings
if not settings.configured:
    settings.configure(DEFAULT_CHARSET='utf-8')
django.setup()
from django.http import HttpResponse

r = HttpResponse()
r.delete_cookie('mykey', samesite='lax')
c = r.cookies['mykey']
print("samesite=", repr(c['samesite']), "max-age=", repr(c['max-age']))
assert c['samesite'] == 'lax', "samesite not lax"
print("OK")
```

Prepatch bug re-encoded as an attack: `True`.

Probes and criteria (all HOLD on gold-patched tree):
- probe_1 (Req 1.2, POSITIVE CONTROL): delete_cookie(samesite='lax') -> cookie samesite=='lax'. HOLDS patched; FAILS at base (TypeError: delete_cookie() got no kwarg 'samesite'). Discriminates.
- probe_2 (Req 2.1/2.2): delete_cookie(samesite='None') -> secure is True, case-insensitive. HOLDS patched.
- probe_3 (Req 3.1/2.3/3.3/3.4): default delete_cookie -> empty samesite, empty secure, max-age 0, epoch expires, path+domain honored. HOLDS patched.
- probe_4 (Req 3.2/3.5): __Secure-/__Host- keys secure True with no samesite; set_cookie rejects invalid samesite and accepts lax/none/strict. HOLDS patched.
- probe_5 (Req 4.1/4.2/4.3): SessionMiddleware deletes empty session cookie with SESSION_COOKIE_SAMESITE, honoring SESSION_COOKIE_PATH/DOMAIN. HOLDS patched.
- probe_6 (Req 5.1/5.2/5.3): CookieStorage deletes messages cookie with SESSION_COOKIE_SAMESITE and epoch expires. HOLDS patched.

CANDIDATE PATCH (weak_no_secure_no_propagate): adds samesite kwarg to delete_cookie and threads it into set_cookie but (a) omits the Secure-on-'none' rule and (b) leaves session middleware and messages storage delete calls unchanged. Under this candidate: probe_1,3,4 HOLD but probe_2 REJECTS (secure not set for none), probe_5 REJECTS (session samesite not propagated), probe_6 REJECTS (messages samesite not propagated). => suite discriminates a plausible weak fix; no requirements-conforming alternative found.

All 6 probes HOLD on patched; positive control fails at base. No violation found; suite rejects the weak candidate on 3 distinct legs (Req 2, Req 4, Req 5). Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Requirements pin the actual changed observable behavior (SameSite carried onto deletion header + Secure when samesite=='none' case-insensitive) across all three touched sites, matching the gold patch exactly. No wrong-boundary narrowing: the diff changes precisely these three functions and the requirements cover each with biconditional-style pins including regression protection. Probes ran green (HOLDS exit=0) on the patched image; behavior matches diff. Note SESSION_COOKIE_SAMESITE default is 'Lax', so R4/R5 propagate that value — requirements correctly phrase them relative to the configured value rather than a fixed literal.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Requirements describe behavior via legitimate localization (module/function names delete_cookie, set_cookie, SESSION_COOKIE_SAMESITE, SESSION_COOKIE_PATH/DOMAIN, __Secure-/__Host- prefixes, epoch expires string) — all of these plus the delete_cookie signature and the Secure/SameSite fix idea are already in the public problem_statement. No test file paths, test/class/function names (test_delete_cookie_samesite, DeleteCookieTests, etc.), parametrization ids, or verbatim gold lines appear. The lax/none/strict enumeration in Req 1 is the valid SameSite value set (general API behavior; 'strict' is not even tested), not a mirror of the test cases (which only cover lax and none). Req 3.5 restates pre-existing set_cookie ValueError behavior. Translating test expectations into behavioral requirements is the intended function of the document.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
