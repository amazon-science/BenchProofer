# P2 adversarial audit — psf__requests-1724

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 requirement probes hold on the patched tree; 3/3 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 7 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 7 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py`, `probe_7.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 3 alternative candidate patches, claimed to satisfy every cited requirement, and ran the same suite against them. The suite rejected all 3: a probe encoding a cited requirement fails under each of those, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (7):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
"""Positive control + Requirement 1.1 & 1.4:
`Session.request` SHALL normalize the supplied `method` into a native text
string BEFORE constructing the Request (for every value of method, independent
of the string type used by the caller).

Discriminator on a Py3 image: for string methods u'POST' is already `str`, so
base and patched are indistinguishable. The observable consequence of the
mandated normalization is a NON-native method argument: on the patched tree the
method is coerced to a native str so dispatch succeeds; on base the raw method
reaches `method.upper()` and a non-native value fails. We use an int, whose
str() is pure ASCII, so normalization -> native '1' and dispatch proceeds.
Exit 0 iff the request is assembled/dispatched WITHOUT error and the method
seen by send() is a native `str`.
"""
import sys
import requests
import requests.sessions as S

captured = {}
def fake_send(self, request, **kwargs):
    captured['method'] = request.method
    captured['mtype'] = type(request.method).__name__
    class Resp:
        status_code = 200
        history = []
        def close(self): pass
    return Resp()
S.Session.send = fake_send

try:
    r = requests.request(method=1, url='http://example.invalid/x',
                         data=b'\xcf\x80binary')
except Exception as e:
    print("VIOLATED: dispatch raised %s: %s" % (type(e).__name__, e))
    sys.exit(1)

m = captured.get('method')
t = captured.get('mtype')
print("observed method=%r type=%s status=%r" % (m, t, getattr(r, 'status_code', None)))
ok = (t == 'str') and isinstance(m, str)
if not ok:
    print("VIOLATED: method not coerced to native str (type=%s)" % t)
    sys.exit(1)
print("HOLDS: non-native method normalized to native str; dispatch succeeded")
sys.exit(0)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""Requirement 2 (2.1/2.2/2.3): the method stored on the built request SHALL be
the UPPER-CASED form of the supplied method, applied to the native-string form
(so simultaneously native-typed AND upper-cased). Covers lower and mixed case,
native and wide/unicode literals.
Capture the method actually handed to send() (no network)."""
import sys
import requests
import requests.sessions as S

seen = {}
def fake_send(self, request, **kwargs):
    seen['method'] = request.method
    class Resp:
        status_code = 200; history = []
        def close(self): pass
    return Resp()
S.Session.send = fake_send

cases = [("post", "POST"), (u"post", "POST"), (u"Post", "POST"),
         ("gEt", "GET"), (u"pUt", "PUT")]
ok = True
for supplied, expected in cases:
    seen.clear()
    try:
        requests.request(method=supplied, url='http://example.invalid/x')
    except Exception as e:
        print("VIOLATED: dispatch raised for %r: %s" % (supplied, e)); ok = False; continue
    m = seen.get('method')
    good = (m == expected) and (type(m).__name__ == 'str')
    print("supplied=%r -> stored=%r type=%s expected=%r %s"
          % (supplied, m, type(m).__name__, expected, "OK" if good else "BAD"))
    ok = ok and good
if not ok:
    print("VIOLATED: method not native-uppercased for some case"); sys.exit(1)
print("HOLDS: all methods stored native-typed AND upper-cased"); sys.exit(0)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""Requirement 1.2: WHEN the supplied method is a wide/unicode all-ASCII string
(u'POST'), THEN the stored method SHALL be a native text string carrying the
SAME characters (not a wide/unicode string). On this interpreter native ==
str; assert the stored method is exactly 'POST' and of type str."""
import sys
import requests
import requests.sessions as S

seen = {}
def fake_send(self, request, **kwargs):
    seen['method'] = request.method
    class Resp:
        status_code = 200; history = []
        def close(self): pass
    return Resp()
S.Session.send = fake_send

try:
    requests.request(method=u'POST', url='http://example.invalid/x')
except Exception as e:
    print("VIOLATED: dispatch raised: %s" % e); sys.exit(1)
m = seen.get('method')
print("stored=%r type=%s" % (m, type(m).__name__))
if not (m == 'POST' and type(m).__name__ == 'str' and list(m) == list('POST')):
    print("VIOLATED: unicode method not stored as native str with same chars"); sys.exit(1)
print("HOLDS: u'POST' stored as native str 'POST'"); sys.exit(0)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""Requirement 1.3: WHEN the supplied method is already a native text string,
THEN normalization SHALL leave its character content unchanged. Supply native
'POST' / 'GET' and require identical characters stored (upper-cased per R2 but
character content of an already-upper native method is unchanged)."""
import sys
import requests
import requests.sessions as S

seen = {}
def fake_send(self, request, **kwargs):
    seen['method'] = request.method
    class Resp:
        status_code = 200; history = []
        def close(self): pass
    return Resp()
S.Session.send = fake_send

ok = True
for supplied in ['POST', 'GET', 'HEAD']:
    seen.clear()
    try:
        requests.request(method=supplied, url='http://example.invalid/x')
    except Exception as e:
        print("VIOLATED: dispatch raised for %r: %s" % (supplied, e)); ok = False; continue
    m = seen.get('method')
    good = (m == supplied and type(m).__name__ == 'str')
    print("supplied=%r -> stored=%r type=%s %s" % (supplied, m, type(m).__name__, "OK" if good else "BAD"))
    ok = ok and good
if not ok:
    print("VIOLATED: native method content changed"); sys.exit(1)
print("HOLDS: already-native method content preserved"); sys.exit(0)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""Requirement 3.1 & 3.2: a request issued with a unicode method name together
with a binary/file payload SHALL be assembled without raising a decoding error,
and SHALL succeed exactly as it would with a native method carrying the same
ASCII chars. We drive the full prepare pipeline through Session.request and
capture the PreparedRequest handed to send() (no network).

NOTE: requests picks a RANDOM multipart boundary per call, so the raw body
bytes/Content-Length legitimately differ between two calls. R3.2 parity is
therefore checked structurally: same native method, both bodies are bytes, both
are multipart/form-data, and the binary payload bytes are embedded verbatim in
both bodies."""
import sys, io
import requests
import requests.sessions as S

PAYLOAD = b'\xcf\x80\xff\x00 binary payload'
grabbed = {}
def fake_send(self, request, **kwargs):
    grabbed['req'] = request
    class Resp:
        status_code = 200; history = []
        def close(self): pass
    return Resp()
S.Session.send = fake_send

def run(method):
    grabbed.clear()
    files = {'file': ('f.bin', io.BytesIO(PAYLOAD))}
    requests.request(method=method, url='http://example.invalid/post', files=files)
    return grabbed['req']

try:
    ureq = run(u'POST')
    nreq = run('POST')
except Exception as e:
    print("VIOLATED: assembling unicode-method + binary body raised %s: %s"
          % (type(e).__name__, e)); sys.exit(1)

uct = ureq.headers.get('Content-Type', '')
nct = nreq.headers.get('Content-Type', '')
print("u: method=%r type=%s body_is_bytes=%s ctype=%r payload_in_body=%s" %
      (ureq.method, type(ureq.method).__name__, isinstance(ureq.body, bytes),
       uct, PAYLOAD in (ureq.body or b'')))
print("n: method=%r body_is_bytes=%s ctype=%r payload_in_body=%s" %
      (nreq.method, isinstance(nreq.body, bytes), nct, PAYLOAD in (nreq.body or b'')))

ok = (ureq.method == 'POST' and type(ureq.method).__name__ == 'str'
      and ureq.method == nreq.method
      and isinstance(ureq.body, (bytes, bytearray))
      and isinstance(nreq.body, (bytes, bytearray))
      and uct.startswith('multipart/form-data') and nct.startswith('multipart/form-data')
      and PAYLOAD in ureq.body and PAYLOAD in nreq.body)
if not ok:
    print("VIOLATED: unicode-method binary request not equivalent to native-method")
    sys.exit(1)
print("HOLDS: unicode-method + binary body assembled; structurally equivalent to native method")
sys.exit(0)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
"""Requirement 3.3 (SHALL keep): all remaining request-building/sending behavior
unchanged for ordinary native-string methods (GET, POST, PUT, HEAD) and for
redirect/auth-shaped requests. We check that Session.request still:
  - constructs a Request and prepares a PreparedRequest with the right method,
    url, and body for each verb,
  - carries query params, headers and an auth-derived Authorization header
    through to the prepared request,
  - follows a redirect (302 -> 200) preserving method handling.
No network: Session.send is faked and simulates one redirect."""
import sys
import requests
import requests.sessions as S
from requests.models import Response
from requests.auth import HTTPBasicAuth

log = []
class Resp:
    def __init__(self, status=200, headers=None):
        self.status_code = status
        self.headers = headers or {}
        self.history = []
        self.is_redirect = False
        self.raw = None
        self.request = None
        self.cookies = requests.cookies.RequestsCookieJar()
    def close(self): pass

def fake_send(self, request, **kwargs):
    log.append(dict(method=request.method, url=request.url,
                    mtype=type(request.method).__name__,
                    auth=request.headers.get('Authorization'),
                    ctype=request.headers.get('Content-Type'),
                    body=request.body))
    return Resp(200)
S.Session.send = fake_send

ok = True
# verbs preserve method + native typing
for verb in ['GET', 'POST', 'PUT', 'HEAD']:
    log.clear()
    requests.request(method=verb, url='http://example.invalid/x',
                     params={'a': '1'})
    rec = log[-1]
    good = (rec['method'] == verb and rec['mtype'] == 'str'
            and 'a=1' in rec['url'])
    print("%s -> method=%r url_has_param=%s %s" %
          (verb, rec['method'], 'a=1' in rec['url'], 'OK' if good else 'BAD'))
    ok = ok and good

# auth header flows through
log.clear()
requests.request('GET', 'http://example.invalid/y',
                 auth=HTTPBasicAuth('u', 'p'))
auth_ok = (log[-1]['auth'] or '').startswith('Basic ')
print("auth header present=%s (%r)" % (auth_ok, log[-1]['auth']))
ok = ok and auth_ok

# POST body preserved
log.clear()
requests.request('POST', 'http://example.invalid/z', data={'k': 'v'})
body_ok = (b'k=v' in (log[-1]['body'] if isinstance(log[-1]['body'], bytes)
                      else (log[-1]['body'] or '').encode()))
print("post body has k=v=%s (%r)" % (body_ok, log[-1]['body']))
ok = ok and body_ok

if not ok:
    print("VIOLATED: regression in ordinary request-building behavior"); sys.exit(1)
print("HOLDS: native-method verbs, params, auth, body all preserved"); sys.exit(0)
```

Attack 7 — `probe_7.py` → holds on the patched tree (good)

```python
"""Requirement 2.1 & 2.3 at the point the requirement names it: WHEN
Session.request BUILDS THE REQUEST, the method stored ON THAT REQUEST (the
`Request` object constructed inside Session.request, BEFORE preparation) SHALL
be the native-typed, upper-cased form of the supplied method.

We capture the Request object's `.method` as it enters Session.prepare_request
(i.e. before PreparedRequest.prepare_method re-normalizes it downstream). This
is the literal R2 mandate and is what the gold patch guarantees
(`Request(method=method.upper(), ...)`); an impl that omits the sessions-level
upper() stores a non-upper method on the Request and violates R2 even though a
later stage happens to re-uppercase the SENT method."""
import sys
import requests
import requests.sessions as S

orig_prepare = S.Session.prepare_request
seen = {}
def wrapped_prepare(self, request):
    seen['method'] = request.method
    seen['mtype'] = type(request.method).__name__
    return orig_prepare(self, request)
S.Session.prepare_request = wrapped_prepare

def fake_send(self, request, **kwargs):
    class Resp:
        status_code = 200; history = []
        def close(self): pass
    return Resp()
S.Session.send = fake_send

cases = [("post", "POST"), (u"post", "POST"), (u"Post", "POST"),
         ("gEt", "GET"), ("POST", "POST")]
ok = True
for supplied, expected in cases:
    seen.clear()
    try:
        requests.request(method=supplied, url='http://example.invalid/x')
    except Exception as e:
        print("VIOLATED: dispatch raised for %r: %s" % (supplied, e)); ok = False; continue
    m = seen.get('method'); t = seen.get('mtype')
    good = (m == expected and t == 'str')
    print("supplied=%r -> Request.method=%r type=%s expected=%r %s"
          % (supplied, m, t, expected, "OK" if good else "BAD"))
    ok = ok and good
if not ok:
    print("VIOLATED: Request object's stored method not native+upper as R2.1/2.3 mandate")
    sys.exit(1)
print("HOLDS: Request.method is native str AND upper-cased before preparation")
sys.exit(0)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Positive control + Requirement 1.1 & 1.4:
`Session.request` SHALL normalize the supplied `method` into a native text
string BEFORE constructing the Request (for every value of method, independent
of the string type used by the caller).

Discriminator on a Py3 image: for string methods u'POST' is already `str`, so
base and patched are indistinguishable. The observable consequence of the
mandated normalization is a NON-native method argument: on the patched tree the
method is coerced to a native str so dispatch succeeds; on base the raw method
reaches `method.upper()` and a non-native value fails. We use an int, whose
str() is pure ASCII, so normalization -> native '1' and dispatch proceeds.
Exit 0 iff the request is assembled/dispatched WITHOUT error and the method
seen by send() is a native `str`.
"""
import sys
import requests
import requests.sessions as S

captured = {}
def fake_send(self, request, **kwargs):
    captured['method'] = request.method
    captured['mtype'] = type(request.method).__name__
    class Resp:
        status_code = 200
        history = []
        def close(self): pass
    return Resp()
S.Session.send = fake_send

try:
    r = requests.request(method=1, url='http://example.invalid/x',
                         data=b'\xcf\x80binary')
except Exception as e:
    print("VIOLATED: dispatch raised %s: %s" % (type(e).__name__, e))
    sys.exit(1)

m = captured.get('method')
t = captured.get('mtype')
print("observed method=%r type=%s status=%r" % (m, t, getattr(r, 'status_code', None)))
ok = (t == 'str') and isinstance(m, str)
if not ok:
    print("VIOLATED: method not coerced to native str (type=%s)" % t)
    sys.exit(1)
print("HOLDS: non-native method normalized to native str; dispatch succeeded")
sys.exit(0)
```

Prepatch bug re-encoded as an attack: `True`.

ENVIRONMENT: bug is Py2.7-specific (wide-unicode method u'POST' infecting a binary body -> UnicodeDecodeError) but the official image is Python 3 (verified: sys.version 3.x, requests.compat.builtin_str is <class 'str'>, is_py3=True). On Py3 u'POST' is ALREADY a native str, so builtin_str(method) is a NO-OP for any ASCII string method -> base and patched are indistinguishable for string inputs. The ONLY observable base-vs-patched discriminator on this image is a NON-str method argument, which the gold coercion normalizes. All probes monkeypatch Session.send (and probe_7 also Session.prepare_request) so NO network is used (avoids the documented psf__requests live-httpbin/pytest4 drift).

### PROBES (all HOLD on gold-patched tree):
- probe_1 (R1.1/1.4, POSITIVE CONTROL): request(method=1, data=binary) -> method reaching send() must be native str '1' and dispatch must not raise. HOLDS patched (method='1' str, status 200); VIOLATED at base (AttributeError: 'int' object has no attribute 'upper'). Discriminates base vs patched.
- probe_2 (R2.1/2.2/2.3): 'post'/u'post'/u'Post'/'gEt'/u'pUt' -> method sent is native str AND upper-cased.
- probe_3 (R1.2): u'POST' -> stored native str 'POST' with identical chars.
- probe_4 (R1.3): native 'POST'/'GET'/'HEAD' character content unchanged.
- probe_5 (R3.1/3.2): u'POST' + binary file body assembles without decoding error and is structurally equivalent to native 'POST' (both multipart/form-data bytes bodies with the raw binary payload embedded; boundary is random per call so parity is checked structurally, not byte-equal).
- probe_6 (R3.3 SHALL-keep regression): GET/POST/PUT/HEAD preserve method+native typing, query params reach the URL, HTTPBasicAuth Authorization header flows through, POST form body carries k=v.
- probe_7 (R2.1/2.3 at the point the requirement names): the Request object BUILT inside Session.request carries a native, upper-cased method BEFORE preparation (captured at Session.prepare_request, before PreparedRequest.prepare_method re-normalizes downstream). This is the literal R2 mandate; it also HOLDS at base since base already does method.upper() (R2 is not the fixed behavior) — it is a conformance/faithfulness probe, not the positive control.

### CANDIDATE WRONG-FIX PATCHES (all apply at base_commit; each REJECTED by the suite; none reaches run_resolve since rejection short-circuits):
- cand_no_coerce (adds `url = str(url)`, no method coercion): REJECTED by probe_1 (int method still crashes) -> proves R1 discriminating power.
- cand_no_upper (coerce `method = str(method)` but drop the sessions-level .upper(), storing `method=method` on Request): REJECTED by probe_7. NOTE: this candidate PASSES probes 1-6 because PreparedRequest.prepare_method re-uppercases the SENT method downstream, so the sessions-level .upper() is not observable at send(); probe_7 was added (after a critic pass) to enforce R2 at the Request-construction point the requirement literally names, which correctly rejects it. Reported transparently rather than excluded.
- cand_bytes (`method = str(method).upper().encode('ascii')`, normalizes to BYTES not native TEXT): REJECTED by all 7 probes (method is bytes, not native str) -> proves R1.2/R2.3 native-TEXT discriminating power.

FLOOR MET: 7 probes >= 5; 3 candidates exercised >= 1; 3 rejected >= 1; positive control HOLDS patched and VIOLATED at base (prepatch reproduced). No inconclusive runs. VERDICT: SOUND — the requirements faithfully constrain the fix; a wrong reading that skips coercion, skips upper-casing, or normalizes to bytes is mechanically rejected.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 requirement probes hold on the patched tree; 3/3 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 7 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 7 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py`, `probe_7.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 3 alternative candidate patches, claimed to satisfy every cited requirement, and ran the same suite against them. The suite rejected all 3: a probe encoding a cited requirement fails under each of those, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

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
"""Positive control + Requirement 1.1 & 1.4:
`Session.request` SHALL normalize the supplied `method` into a native text
string BEFORE constructing the Request (for every value of method, independent
of the string type used by the caller).

Discriminator on a Py3 image: for string methods u'POST' is already `str`, so
base and patched are indistinguishable. The observable consequence of the
mandated normalization is a NON-native method argument: on the patched tree the
method is coerced to a native str so dispatch succeeds; on base the raw method
reaches `method.upper()` and a non-native value fails. We use an int, whose
str() is pure ASCII, so normalization -> native '1' and dispatch proceeds.
Exit 0 iff the request is assembled/dispatched WITHOUT error and the method
seen by send() is a native `str`.
"""
import sys
import requests
import requests.sessions as S

captured = {}
def fake_send(self, request, **kwargs):
    captured['method'] = request.method
    captured['mtype'] = type(request.method).__name__
    class Resp:
        status_code = 200
        history = []
        def close(self): pass
    return Resp()
S.Session.send = fake_send

try:
    r = requests.request(method=1, url='http://example.invalid/x',
                         data=b'\xcf\x80binary')
except Exception as e:
    print("VIOLATED: dispatch raised %s: %s" % (type(e).__name__, e))
    sys.exit(1)

m = captured.get('method')
t = captured.get('mtype')
print("observed method=%r type=%s status=%r" % (m, t, getattr(r, 'status_code', None)))
ok = (t == 'str') and isinstance(m, str)
if not ok:
    print("VIOLATED: method not coerced to native str (type=%s)" % t)
    sys.exit(1)
print("HOLDS: non-native method normalized to native str; dispatch succeeded")
sys.exit(0)
```

Prepatch bug re-encoded as an attack: `True`.

ENVIRONMENT: bug is Py2.7-specific (wide-unicode method u'POST' infecting a binary body -> UnicodeDecodeError) but the official image is Python 3 (verified: sys.version 3.x, requests.compat.builtin_str is <class 'str'>, is_py3=True). On Py3 u'POST' is ALREADY a native str, so builtin_str(method) is a NO-OP for any ASCII string method -> base and patched are indistinguishable for string inputs. The ONLY observable base-vs-patched discriminator on this image is a NON-str method argument, which the gold coercion normalizes. All probes monkeypatch Session.send (and probe_7 also Session.prepare_request) so NO network is used (avoids the documented psf__requests live-httpbin/pytest4 drift).

### PROBES (all HOLD on gold-patched tree):
- probe_1 (R1.1/1.4, POSITIVE CONTROL): request(method=1, data=binary) -> method reaching send() must be native str '1' and dispatch must not raise. HOLDS patched (method='1' str, status 200); VIOLATED at base (AttributeError: 'int' object has no attribute 'upper'). Discriminates base vs patched.
- probe_2 (R2.1/2.2/2.3): 'post'/u'post'/u'Post'/'gEt'/u'pUt' -> method sent is native str AND upper-cased.
- probe_3 (R1.2): u'POST' -> stored native str 'POST' with identical chars.
- probe_4 (R1.3): native 'POST'/'GET'/'HEAD' character content unchanged.
- probe_5 (R3.1/3.2): u'POST' + binary file body assembles without decoding error and is structurally equivalent to native 'POST' (both multipart/form-data bytes bodies with the raw binary payload embedded; boundary is random per call so parity is checked structurally, not byte-equal).
- probe_6 (R3.3 SHALL-keep regression): GET/POST/PUT/HEAD preserve method+native typing, query params reach the URL, HTTPBasicAuth Authorization header flows through, POST form body carries k=v.
- probe_7 (R2.1/2.3 at the point the requirement names): the Request object BUILT inside Session.request carries a native, upper-cased method BEFORE preparation (captured at Session.prepare_request, before PreparedRequest.prepare_method re-normalizes downstream). This is the literal R2 mandate; it also HOLDS at base since base already does method.upper() (R2 is not the fixed behavior) — it is a conformance/faithfulness probe, not the positive control.

### CANDIDATE WRONG-FIX PATCHES (all apply at base_commit; each REJECTED by the suite; none reaches run_resolve since rejection short-circuits):
- cand_no_coerce (adds `url = str(url)`, no method coercion): REJECTED by probe_1 (int method still crashes) -> proves R1 discriminating power.
- cand_no_upper (coerce `method = str(method)` but drop the sessions-level .upper(), storing `method=method` on Request): REJECTED by probe_7. NOTE: this candidate PASSES probes 1-6 because PreparedRequest.prepare_method re-uppercases the SENT method downstream, so the sessions-level .upper() is not observable at send(); probe_7 was added (after a critic pass) to enforce R2 at the Request-construction point the requirement literally names, which correctly rejects it. Reported transparently rather than excluded.
- cand_bytes (`method = str(method).upper().encode('ascii')`, normalizes to BYTES not native TEXT): REJECTED by all 7 probes (method is bytes, not native str) -> proves R1.2/R2.3 native-TEXT discriminating power.

FLOOR MET: 7 probes >= 5; 3 candidates exercised >= 1; 3 rejected >= 1; positive control HOLDS patched and VIOLATED at base (prepatch reproduced). No inconclusive runs. VERDICT: SOUND — the requirements faithfully constrain the fix; a wrong reading that skips coercion, skips upper-casing, or normalizes to bytes is mechanically rejected.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Gold patch (requests/sessions.py): import builtin_str from .compat; insert `method = builtin_str(method)` before `req = Request(method = method.upper(), ...)`. compat: `builtin_str = str` on both Py2/Py3. Probes run in the instance image on the gold-patched tree (nl_attack probe, exit 0) and on --base: identical outputs since builtin_str is str under Py3. Requirements' Introduction and Req1 explicitly scope to interpreters distinguishing native vs wide text (Py2.7), with ASCII-only guarantee in Req1.AC2 — faithful to str(u'POST') semantics. Req3.3's regression-preservation enumeration matches the single-line, side-effect-free nature of the patch. FAITHFUL. (Note: meta.json G-PANEL-2 already recorded pass with FAITHFUL; the fail rollup is due to G-PANEL-1/G-EQ INCONCLUSIVE procedural artifacts, not faithfulness.)

Counterexample / evidence:

```
N/A — no diverging input exists. The Py3 instance image cannot reproduce the original Py2.7-only UnicodeDecodeError (builtin_str is str, so base and patched are observationally identical for the probe), but the requirements are framed around native-vs-wide string semantics, which is precisely what builtin_str() normalizes; the modeling boundary (method coercion + its effect on dispatch) is the changed observable behavior, not a narrow helper/branch slice.
```


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Hidden test is a single function test_unicode_method_name in test_requests.py: files={'file': open('test_requests.py','rb')}; requests.request(method=u'POST', url=httpbin('post'), files=files); assert r.status_code==200. Gold patch adds `from .compat import ... builtin_str` and `method = builtin_str(method)` before Request(method=method.upper(),...) in requests/sessions.py.

Checked requirements.md for content derivable ONLY from hidden material:
- Test file path (test_requests.py), test function name (test_unicode_method_name), httpbin/status_code==200, and FAIL_TO_PASS/PASS_TO_PASS ids: NONE appear.
- Fix-invented identifier `builtin_str` and the `.compat` import: NOT named. The doc says 'native text string' — a behavioral translation of the coercion, not the gold code. Legitimate.
- `Session.request`, `requests/sessions.py`, `Request`, `PreparedRequest`, `.upper()`, method=u'POST', UnicodeDecodeError, uploaded file / binary body, Python 2.7 native-vs-wide string: ALL are present verbatim in the PUBLIC problem_statement (which quotes the u'POST'+open(...,'rb') repro, the traceback, and `req.method = method.upper()`). Module/function naming is legitimate localization.
- Req 3.3 enumerates 'GET, POST, PUT, HEAD, and redirected or authenticated requests' plus cookie/header/redirect/auth handling. This reads as a generic 'preserve existing behavior' scope statement over canonical HTTP verbs and standard library features, NOT a mirror of the test parametrization. The distinctive PASS_TO_PASS items (CaseInsensitiveDict suite, content-encoding detection, super_len_io_streams, session pickling, links, entry_points) are NOT surfaced — a test-reconstruction would enumerate those. No 1:1 case-to-test correspondence.

The requirements describe the behavior (coerce unicode method to native string, uppercase it, don't break binary-body dispatch) sourced from the public problem statement. No transmission of the hidden tests or gold edit beyond what is public.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
