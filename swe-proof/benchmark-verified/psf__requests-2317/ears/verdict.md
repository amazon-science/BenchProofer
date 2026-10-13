# P2 adversarial audit — psf__requests-2317

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
"""Req1 (positive control): byte token method coerced to textual 'GET'.

Session.request(b'GET', ...) must yield a prepared request whose method is the
three chars 'GET', NOT "b'GET'"/"B'GET'". We intercept Session.send to capture
the prepared request without any network I/O.
"""
import requests
from requests.sessions import Session


class Captured(Exception):
    pass


captured = {}


def fake_send(self, prep, **kwargs):
    captured['method'] = prep.method
    raise Captured()


Session.send = fake_send
s = Session()
try:
    s.request(b'GET', 'http://example.invalid/get')
except Captured:
    pass

m = captured.get('method')
print("prepared method =", repr(m))
ok = (m == 'GET')
print("PASS" if ok else "FAIL")
raise SystemExit(0 if ok else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""Req1.2/1.3: byte token method equals the text-token result; no quoting/prefix.

Compare prepared method for b'GET' vs 'GET' — must be identical, and must not
contain any 'b'/quote characters from repr of the byte object.
"""
from requests.sessions import Session


class Captured(Exception):
    pass


results = {}


def make_send(key):
    def fake_send(self, prep, **kwargs):
        results[key] = prep.method
        raise Captured()
    return fake_send


for key, meth in (('bytes', b'GET'), ('text', 'GET')):
    Session.send = make_send(key)
    s = Session()
    try:
        s.request(meth, 'http://example.invalid/get')
    except Captured:
        pass

print("bytes ->", repr(results.get('bytes')))
print("text  ->", repr(results.get('text')))
mb = results.get('bytes')
ok = (mb == results.get('text') == 'GET'
      and "b'" not in (mb or '') and 'b"' not in (mb or '')
      and "'" not in (mb or ''))
print("PASS" if ok else "FAIL")
raise SystemExit(0 if ok else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""Req2.1/2.2: normalized method is upper-cased, including a byte token that
spells a lower-case name.

b'get' and 'post' (text lower) must both end up upper-cased on the prepared req.
"""
from requests.sessions import Session


class Captured(Exception):
    pass


results = {}


def make_send(key):
    def fake_send(self, prep, **kwargs):
        results[key] = prep.method
        raise Captured()
    return fake_send


cases = {'bytes_lower': b'get', 'text_lower': 'post', 'bytes_mixed': b'PuT'}
for key, meth in cases.items():
    Session.send = make_send(key)
    s = Session()
    try:
        s.request(meth, 'http://example.invalid/x')
    except Captured:
        pass

for k, v in results.items():
    print(k, "->", repr(v))
ok = (results.get('bytes_lower') == 'GET'
      and results.get('text_lower') == 'POST'
      and results.get('bytes_mixed') == 'PUT')
print("PASS" if ok else "FAIL")
raise SystemExit(0 if ok else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""Req2.3: absent method (None) -> prepared method stays None (not coerced/upcased).

PreparedRequest.prepare_method(None) must leave .method None and not raise.
"""
from requests.models import PreparedRequest

p = PreparedRequest()
p.prepare_method(None)
print("method after None =", repr(p.method))
ok = p.method is None
print("PASS" if ok else "FAIL")
raise SystemExit(0 if ok else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""Req3.1/3.4: text methods (native str and unicode) retain chars, stored as
native str, unchanged aside from upper-casing.
"""
from requests.sessions import Session


class Captured(Exception):
    pass


results = {}


def make_send(key):
    def fake_send(self, prep, **kwargs):
        results[key] = prep.method
        raise Captured()
    return fake_send


cases = {'get': 'GET', 'unicode': u'HEAD', 'put': 'PUT'}
for key, meth in cases.items():
    Session.send = make_send(key)
    s = Session()
    try:
        s.request(meth, 'http://example.invalid/x')
    except Captured:
        pass

for k, v in results.items():
    print(k, "->", repr(v), type(v).__name__)
ok = (results.get('get') == 'GET' and isinstance(results.get('get'), str)
      and results.get('unicode') == 'HEAD' and isinstance(results.get('unicode'), str)
      and results.get('put') == 'PUT')
print("PASS" if ok else "FAIL")
raise SystemExit(0 if ok else 1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
"""Req3.2/3.3: redirect-following flow carries correctly normalized method.

Drive Session.resolve_redirects on a fake 302 response and confirm the next
request's method is a clean 'GET' (proves the coercion is native str, not b'GET',
and that redirect flows work). We avoid network by building objects directly.
"""
from requests.models import PreparedRequest, Response
from requests.sessions import Session
from requests.structures import CaseInsensitiveDict

# Build a prepared GET request as request() would (via byte token to stress it).
class Captured(Exception):
    pass

cap = {}
def fake_send(self, prep, **kwargs):
    cap['prep'] = prep
    raise Captured()

Session.send = fake_send
s = Session()
try:
    s.request(b'GET', 'http://example.invalid/start')
except Captured:
    pass
prep = cap['prep']

# Fake a 302 redirect response pointing elsewhere.
class StubRaw(object):
    def release_conn(self):
        pass
    def read(self, *a, **k):
        return b''
    def stream(self, *a, **k):
        return iter(())
    closed = True

resp = Response()
resp.status_code = 302
resp.headers = CaseInsensitiveDict({'location': 'http://example.invalid/next'})
resp.raw = StubRaw()
resp.request = prep
resp._content = b''
resp._content_consumed = True

# Patch send so resolve_redirects doesn't hit the network; capture next req.
nexts = []
def fake_send2(self, request, **kwargs):
    nexts.append(request.method)
    r = Response()
    r.status_code = 200
    r.headers = CaseInsensitiveDict()
    r.request = request
    r._content = b''
    r._content_consumed = True
    r.raw = None
    return r

Session.send = fake_send2
s2 = Session()
gen = s2.resolve_redirects(resp, prep)
try:
    for _ in gen:
        pass
except Exception as e:
    print("resolve_redirects raised:", repr(e))

print("methods of redirected requests:", nexts)
ok = bool(nexts) and all(m == 'GET' for m in nexts)
print("PASS" if ok else "FAIL")
raise SystemExit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Req1 (positive control): byte token method coerced to textual 'GET'.

Session.request(b'GET', ...) must yield a prepared request whose method is the
three chars 'GET', NOT "b'GET'"/"B'GET'". We intercept Session.send to capture
the prepared request without any network I/O.
"""
import requests
from requests.sessions import Session


class Captured(Exception):
    pass


captured = {}


def fake_send(self, prep, **kwargs):
    captured['method'] = prep.method
    raise Captured()


Session.send = fake_send
s = Session()
try:
    s.request(b'GET', 'http://example.invalid/get')
except Captured:
    pass

m = captured.get('method')
print("prepared method =", repr(m))
ok = (m == 'GET')
print("PASS" if ok else "FAIL")
raise SystemExit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance fixes Python-3 byte-method corruption: sessions.py changes builtin_str(method) -> to_native_string(method); prepare_method upper-cases. 

Probes (all exit 0 iff criterion holds), results PATCHED / BASE:
- probe_1 (Req1.1-1.3, POSITIVE CONTROL): Session.request(b'GET') -> prepared .method must == 'GET'. PATCHED=PASS('GET'), BASE=FAIL("B'GET'") => prepatch reproduced.
- probe_2 (Req1.2/1.3): b'GET' method == 'GET' text-token result, no b'/quote chars. PATCHED=PASS.
- probe_3 (Req2.1/2.2): b'get'->'GET', 'post'->'POST', b'PuT'->'PUT'. PATCHED=PASS.
- probe_4 (Req2.3): prepare_method(None) leaves .method None, no error. PATCHED=PASS.
- probe_5 (Req3.1/3.4): text 'GET'/u'HEAD'/'PUT' retained, native str. PATCHED=PASS.
- probe_6 (Req3.2/3.3): resolve_redirects on a fake 302 (from a b'GET' request) yields next request method 'GET'. PATCHED=PASS.

Candidate wrong patch 'no_coercion' (replace builtin_str(method) with method, i.e. no coercion at all — a lazy reading that 'text already works'): REJECTED by probes 1/2/3 (byte token stays b'GET'), while probes 5/6 (text-only) still pass. This demonstrates the suite discriminates a wrong impl on the exact fixed behavior. Note the harness upper-cases via method.upper() so b'GET'.upper()==b'GET' does not raise, yet .method is the bytes object, failing the textual-content criterion.

All 6 probes HOLD on gold-patched tree; positive control discriminates (holds patched, fails base). Verdict SOUND.

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
"""Req1 (positive control): byte token method coerced to textual 'GET'.

Session.request(b'GET', ...) must yield a prepared request whose method is the
three chars 'GET', NOT "b'GET'"/"B'GET'". We intercept Session.send to capture
the prepared request without any network I/O.
"""
import requests
from requests.sessions import Session


class Captured(Exception):
    pass


captured = {}


def fake_send(self, prep, **kwargs):
    captured['method'] = prep.method
    raise Captured()


Session.send = fake_send
s = Session()
try:
    s.request(b'GET', 'http://example.invalid/get')
except Captured:
    pass

m = captured.get('method')
print("prepared method =", repr(m))
ok = (m == 'GET')
print("PASS" if ok else "FAIL")
raise SystemExit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance fixes Python-3 byte-method corruption: sessions.py changes builtin_str(method) -> to_native_string(method); prepare_method upper-cases. 

Probes (all exit 0 iff criterion holds), results PATCHED / BASE:
- probe_1 (Req1.1-1.3, POSITIVE CONTROL): Session.request(b'GET') -> prepared .method must == 'GET'. PATCHED=PASS('GET'), BASE=FAIL("B'GET'") => prepatch reproduced.
- probe_2 (Req1.2/1.3): b'GET' method == 'GET' text-token result, no b'/quote chars. PATCHED=PASS.
- probe_3 (Req2.1/2.2): b'get'->'GET', 'post'->'POST', b'PuT'->'PUT'. PATCHED=PASS.
- probe_4 (Req2.3): prepare_method(None) leaves .method None, no error. PATCHED=PASS.
- probe_5 (Req3.1/3.4): text 'GET'/u'HEAD'/'PUT' retained, native str. PATCHED=PASS.
- probe_6 (Req3.2/3.3): resolve_redirects on a fake 302 (from a b'GET' request) yields next request method 'GET'. PATCHED=PASS.

Candidate wrong patch 'no_coercion' (replace builtin_str(method) with method, i.e. no coercion at all — a lazy reading that 'text already works'): REJECTED by probes 1/2/3 (byte token stays b'GET'), while probes 5/6 (text-only) still pass. This demonstrates the suite discriminates a wrong impl on the exact fixed behavior. Note the harness upper-cases via method.upper() so b'GET'.upper()==b'GET' does not raise, yet .method is the bytes object, failing the textual-content criterion.

All 6 probes HOLD on gold-patched tree; positive control discriminates (holds patched, fails base). Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Patch changes exactly one line: builtin_str(method)->to_native_string(method) in Session.request. Requirements correctly attribute coercion to Session.request and the (unchanged, pre-existing) upper-casing to PreparedRequest.prepare_method, and describe them as jointly producing the observable behavior — this is accurate, not an invented or misplaced boundary. Probes: to_native_string(b'GET')=='GET'; full prepare flow b'get'->'GET'; prepare_method(None)->None. R2.2's example (byte token spelling lower-case name -> upper-cased stored method) holds end-to-end because Session.request coerces to native str before prepare_method upper-cases it.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** requirements.md describes the defect and fix at a behavioral level, all of which is either public in problem_statement (builtin_str, requests/sessions.py, b'GET'->"b'GET'", 404, Python-3-specific) or legitimate localization. The gold-patch identifier `to_native_string` is NOT named; the doc instead describes 'decode the token's bytes to their corresponding text characters' (behavior, not the invented call). Session.request / PreparedRequest.prepare_method / requests/models.py are pre-existing symbols used to localize the change, not fix-invented. The hidden test test_encoded_methods (name/path/id, `requests.request(b'GET', httpbin('get')); assert r.ok`) is not quoted or referenced. Req 3.2/3.3's mention of GET/POST/HEAD/PUT and redirect/retry/history maps loosely onto the FAIL_TO_PASS set, but these are generic HTTP methods and standard flows expressed as behavioral requirements (normalized method must survive redirects/retries/history) rather than test ids or a parametrization mirror. No verbatim gold lines, no test-shaped enumeration reconstructing the tests.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
