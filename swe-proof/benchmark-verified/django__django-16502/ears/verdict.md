# P2 adversarial audit — django__django-16502

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
"""Positive control — Requirement 1.1 & 3.2 & 4.2:
HEAD response has NO entity body (last line is the bare CRLF that ends the
header block) AND no Content-Length header AND no 'Connection: close'.
Must HOLD on patched tree, FAIL at base (base writes the full body)."""
from io import BytesIO
from socketserver import ThreadingMixIn
from django.core.servers.basehttp import WSGIRequestHandler


class Stub(ThreadingMixIn):
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    def sendall(self, data):
        self.makefile("wb").write(data)


hello = b"<!DOCTYPE html><html><body>Hello World</body></html>"


def app(environ, start_response):
    start_response("200 OK", [])
    return [hello]


rfile = BytesIO(b"HEAD / HTTP/1.0\r\n")
rfile.seek(0)


class UnclosableBytesIO(BytesIO):
    def close(self):
        pass


wfile = UnclosableBytesIO()


def makefile(mode, *a, **kw):
    return rfile if mode == "rb" else wfile


request = Stub(makefile=makefile)
server = Stub(base_environ={}, get_app=lambda: app)
WSGIRequestHandler(request, "192.168.0.2", server)

wfile.seek(0)
lines = list(wfile.readlines())
print("HEAD response lines:", lines)
body = lines[-1]
ok_body = body == b"\r\n"
ok_no_cl = not any(l.startswith(b"Content-Length:") for l in lines)
ok_no_close = b"Connection: close\r\n" not in lines
ok_status = any(l.startswith(b"HTTP/") and b" 200" in l for l in lines)
print("last-line-empty:", ok_body, "no-content-length:", ok_no_cl,
      "no-connection-close:", ok_no_close, "status-present:", ok_status)
assert ok_body, "HEAD body must be empty (bare CRLF)"
assert ok_no_cl, "HEAD must have no Content-Length"
assert ok_no_close, "HEAD must not assert Connection: close"
assert ok_status, "HEAD must still emit status line"
print("PASS")
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""Requirement 1.2: On a HEAD request the handler SHALL fully consume the
iterable of body data returned by the WSGI app (so app-side generation/cleanup
runs), without writing it. We give the app a generator that records that it
ran to completion; the recorder must fire AND the body must not be written."""
from io import BytesIO
from socketserver import ThreadingMixIn
from django.core.servers.basehttp import WSGIRequestHandler

consumed = {"done": False}
hello = b"<!DOCTYPE html><html><body>Hello World</body></html>"


class Stub(ThreadingMixIn):
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    def sendall(self, data):
        self.makefile("wb").write(data)


def app(environ, start_response):
    start_response("200 OK", [])

    def gen():
        yield hello
        consumed["done"] = True  # cleanup / generation past the last chunk
    return gen()


rfile = BytesIO(b"HEAD / HTTP/1.0\r\n")
rfile.seek(0)


class UnclosableBytesIO(BytesIO):
    def close(self):
        pass


wfile = UnclosableBytesIO()


def makefile(mode, *a, **kw):
    return rfile if mode == "rb" else wfile


request = Stub(makefile=makefile)
server = Stub(base_environ={}, get_app=lambda: app)
WSGIRequestHandler(request, "192.168.0.2", server)

wfile.seek(0)
data = wfile.read()
print("generator fully consumed:", consumed["done"])
print("body-bytes-present:", hello in data)
assert consumed["done"], "HEAD must fully consume the app iterable"
assert hello not in data, "HEAD must not write the entity body"
print("PASS")
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""Requirement 2.1 & 2.2 & 3.3 & 4.1(non-HEAD w/ CL present): ordinary GET
request keeps its FULL body, its Content-Length header, and (since CL is
present on a threading server) no 'Connection: close'."""
from io import BytesIO
from socketserver import ThreadingMixIn
from django.core.servers.basehttp import WSGIRequestHandler


class Stub(ThreadingMixIn):
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    def sendall(self, data):
        self.makefile("wb").write(data)


hello = b"<!DOCTYPE html><html><body>Hello World</body></html>"
clen = len(hello)


def app(environ, start_response):
    start_response("200 OK", [])
    return [hello]


rfile = BytesIO(b"GET / HTTP/1.0\r\n")
rfile.seek(0)


class UnclosableBytesIO(BytesIO):
    def close(self):
        pass


wfile = UnclosableBytesIO()


def makefile(mode, *a, **kw):
    return rfile if mode == "rb" else wfile


request = Stub(makefile=makefile)
server = Stub(base_environ={}, get_app=lambda: app)
WSGIRequestHandler(request, "192.168.0.2", server)

wfile.seek(0)
lines = list(wfile.readlines())
print("GET response lines:", lines)
body = lines[-1]
ok_body = body == hello
ok_cl = (f"Content-Length: {clen}\r\n").encode() in lines
ok_no_close = b"Connection: close\r\n" not in lines
print("body-full:", ok_body, "content-length-present:", ok_cl,
      "no-connection-close:", ok_no_close)
assert ok_body, "GET must return full body"
assert ok_cl, "GET must keep Content-Length"
assert ok_no_close, "GET with CL on threading server must not close"
print("PASS")
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""Requirement 4.1: ordinary (non-HEAD) request whose response has NO
Content-Length (streaming app, unknown length) SHALL assert 'Connection:
close'. Contrast with 4.2 (HEAD with no CL must NOT close, probe_1)."""
from io import BytesIO
from socketserver import ThreadingMixIn
from django.core.servers.basehttp import WSGIRequestHandler


class Stub(ThreadingMixIn):
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    def sendall(self, data):
        self.makefile("wb").write(data)


def app(environ, start_response):
    start_response("200 OK", [])

    def gen():
        yield b"chunk-a"
        yield b"chunk-b"
    return gen()  # length unknown => no Content-Length


rfile = BytesIO(b"GET / HTTP/1.0\r\n")
rfile.seek(0)


class UnclosableBytesIO(BytesIO):
    def close(self):
        pass


wfile = UnclosableBytesIO()


def makefile(mode, *a, **kw):
    return rfile if mode == "rb" else wfile


request = Stub(makefile=makefile)
server = Stub(base_environ={}, get_app=lambda: app)
WSGIRequestHandler(request, "192.168.0.2", server)

wfile.seek(0)
lines = list(wfile.readlines())
print("GET(streaming) response lines:", lines)
has_cl = any(l.startswith(b"Content-Length:") for l in lines)
has_close = b"Connection: close\r\n" in lines
print("has-content-length:", has_cl, "has-connection-close:", has_close)
assert not has_cl, "streaming GET should have no Content-Length"
assert has_close, "GET without Content-Length must assert Connection: close"
print("PASS")
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""Requirement 5.1 (SHALL keep): request headers whose names contain
underscores are excluded from the WSGI environ passed to the app. This is the
pre-existing behaviour that must be preserved by the change."""
from io import BytesIO
from socketserver import ThreadingMixIn
from django.core.servers.basehttp import WSGIRequestHandler

seen = {}


class Stub(ThreadingMixIn):
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    def sendall(self, data):
        self.makefile("wb").write(data)


def app(environ, start_response):
    start_response("200 OK", [])
    seen["some"] = environ.get("HTTP_SOME_HEADER")
    seen["under"] = environ.get("HTTP_UNDER_SCORE")  # from 'Under_Score'
    return [b"ok"]


rfile = BytesIO(
    b"GET / HTTP/1.0\r\n"
    b"Some-Header: good\r\n"
    b"Under_Score: bad\r\n"
)
rfile.seek(0)


class UnclosableBytesIO(BytesIO):
    def close(self):
        pass


wfile = UnclosableBytesIO()


def makefile(mode, *a, **kw):
    return rfile if mode == "rb" else wfile


request = Stub(makefile=makefile)
server = Stub(base_environ={}, get_app=lambda: app)
WSGIRequestHandler(request, "192.168.0.2", server)

print("HTTP_SOME_HEADER:", seen.get("some"), "HTTP_UNDER_SCORE:", seen.get("under"))
assert seen.get("some") == "good", "normal header must reach app"
assert seen.get("under") is None, "underscore header must be filtered out"
print("PASS")
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
"""Requirement 4.3: when Content-Length is present AND served by a
non-threading server, the handler SHALL assert 'Connection: close'. Here the
server Stub is NOT a ThreadingMixIn, GET has a known length."""
from io import BytesIO
from django.core.servers.basehttp import WSGIRequestHandler


class Stub:  # NOT a ThreadingMixIn => single-request server
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    def sendall(self, data):
        self.makefile("wb").write(data)


hello = b"hello world body"


def app(environ, start_response):
    start_response("200 OK", [])
    return [hello]  # known length => Content-Length present


rfile = BytesIO(b"GET / HTTP/1.0\r\n")
rfile.seek(0)


class UnclosableBytesIO(BytesIO):
    def close(self):
        pass


wfile = UnclosableBytesIO()


def makefile(mode, *a, **kw):
    return rfile if mode == "rb" else wfile


request = Stub(makefile=makefile)
server = Stub(base_environ={}, get_app=lambda: app)
WSGIRequestHandler(request, "192.168.0.2", server)

wfile.seek(0)
lines = list(wfile.readlines())
print("GET(non-threading) response lines:", lines)
has_cl = any(l.startswith(b"Content-Length:") for l in lines)
has_close = b"Connection: close\r\n" in lines
print("has-content-length:", has_cl, "has-connection-close:", has_close)
assert has_cl, "known-length GET should have Content-Length"
assert has_close, "non-threading server with CL must assert Connection: close"
print("PASS")
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Positive control — Requirement 1.1 & 3.2 & 4.2:
HEAD response has NO entity body (last line is the bare CRLF that ends the
header block) AND no Content-Length header AND no 'Connection: close'.
Must HOLD on patched tree, FAIL at base (base writes the full body)."""
from io import BytesIO
from socketserver import ThreadingMixIn
from django.core.servers.basehttp import WSGIRequestHandler


class Stub(ThreadingMixIn):
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    def sendall(self, data):
        self.makefile("wb").write(data)


hello = b"<!DOCTYPE html><html><body>Hello World</body></html>"


def app(environ, start_response):
    start_response("200 OK", [])
    return [hello]


rfile = BytesIO(b"HEAD / HTTP/1.0\r\n")
rfile.seek(0)


class UnclosableBytesIO(BytesIO):
    def close(self):
        pass


wfile = UnclosableBytesIO()


def makefile(mode, *a, **kw):
    return rfile if mode == "rb" else wfile


request = Stub(makefile=makefile)
server = Stub(base_environ={}, get_app=lambda: app)
WSGIRequestHandler(request, "192.168.0.2", server)

wfile.seek(0)
lines = list(wfile.readlines())
print("HEAD response lines:", lines)
body = lines[-1]
ok_body = body == b"\r\n"
ok_no_cl = not any(l.startswith(b"Content-Length:") for l in lines)
ok_no_close = b"Connection: close\r\n" not in lines
ok_status = any(l.startswith(b"HTTP/") and b" 200" in l for l in lines)
print("last-line-empty:", ok_body, "no-content-length:", ok_no_cl,
      "no-connection-close:", ok_no_close, "status-present:", ok_status)
assert ok_body, "HEAD body must be empty (bare CRLF)"
assert ok_no_cl, "HEAD must have no Content-Length"
assert ok_no_close, "HEAD must not assert Connection: close"
assert ok_status, "HEAD must still emit status line"
print("PASS")
```

Prepatch bug re-encoded as an attack: `True`.

Instance django__django-16502: development server must omit the entity body from HEAD responses. All 6 probes run in the official docker image via nl_attack; the Stub server needs a sendall() method (wbufsize=0 -> _SocketWriter.write calls sendall) to drive WSGIRequestHandler end-to-end.

Probes and requirements covered:
- probe_1 (POSITIVE CONTROL) — Req 1.1 / 3.2 / 4.2: HEAD response's last line is the bare CRLF (empty body), NO Content-Length header, NO 'Connection: close', status line still emitted. HOLDS patched, VIOLATED at base (base writes the full body — prepatch reproduced).
- probe_2 — Req 1.2: HEAD fully consumes the WSGI app's generator (a recorder past the last chunk fires) yet writes no body bytes. HOLDS patched.
- probe_3 — Req 2.1 / 2.2 / 3.3 / 4.1(non-HEAD w/ CL, threading): ordinary GET keeps full body + Content-Length: 52 + no Connection: close. HOLDS patched.
- probe_4 — Req 4.1: streaming GET with unknown length has no Content-Length and DOES assert 'Connection: close'. HOLDS patched.
- probe_5 — Req 5.1 (SHALL keep): underscore request headers ('Under_Score') excluded from WSGI environ; normal 'Some-Header' passes through. HOLDS patched.
- probe_6 — Req 4.3: known-length GET on a NON-threading server asserts 'Connection: close' while keeping Content-Length. HOLDS patched.

Discriminating power confirmed: positive control probe_1 fails at base and holds patched.

Candidate wrong-fix (weak.diff): the gold patch minus the block that deletes Content-Length for HEAD in cleanup_headers — i.e. a partial reading that strips the HEAD body and fixes the Connection policy but leaves the Content-Length header in place. probe_1 REJECTS it ('HEAD must have no Content-Length'), matching the hidden test's assertNotIn Content-Length assertion. probes 2-6 hold under it. This demonstrates the suite discriminates a requirements-incomplete implementation; therefore no requirements-conforming-yet-nonresolving patch was found. SOUND.

All needed runs completed (patched, base, candidate). weak.diff applies cleanly at base_commit.

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
"""Positive control — Requirement 1.1 & 3.2 & 4.2:
HEAD response has NO entity body (last line is the bare CRLF that ends the
header block) AND no Content-Length header AND no 'Connection: close'.
Must HOLD on patched tree, FAIL at base (base writes the full body)."""
from io import BytesIO
from socketserver import ThreadingMixIn
from django.core.servers.basehttp import WSGIRequestHandler


class Stub(ThreadingMixIn):
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    def sendall(self, data):
        self.makefile("wb").write(data)


hello = b"<!DOCTYPE html><html><body>Hello World</body></html>"


def app(environ, start_response):
    start_response("200 OK", [])
    return [hello]


rfile = BytesIO(b"HEAD / HTTP/1.0\r\n")
rfile.seek(0)


class UnclosableBytesIO(BytesIO):
    def close(self):
        pass


wfile = UnclosableBytesIO()


def makefile(mode, *a, **kw):
    return rfile if mode == "rb" else wfile


request = Stub(makefile=makefile)
server = Stub(base_environ={}, get_app=lambda: app)
WSGIRequestHandler(request, "192.168.0.2", server)

wfile.seek(0)
lines = list(wfile.readlines())
print("HEAD response lines:", lines)
body = lines[-1]
ok_body = body == b"\r\n"
ok_no_cl = not any(l.startswith(b"Content-Length:") for l in lines)
ok_no_close = b"Connection: close\r\n" not in lines
ok_status = any(l.startswith(b"HTTP/") and b" 200" in l for l in lines)
print("last-line-empty:", ok_body, "no-content-length:", ok_no_cl,
      "no-connection-close:", ok_no_close, "status-present:", ok_status)
assert ok_body, "HEAD body must be empty (bare CRLF)"
assert ok_no_cl, "HEAD must have no Content-Length"
assert ok_no_close, "HEAD must not assert Connection: close"
assert ok_status, "HEAD must still emit status line"
print("PASS")
```

Prepatch bug re-encoded as an attack: `True`.

Instance django__django-16502: development server must omit the entity body from HEAD responses. All 6 probes run in the official docker image via nl_attack; the Stub server needs a sendall() method (wbufsize=0 -> _SocketWriter.write calls sendall) to drive WSGIRequestHandler end-to-end.

Probes and requirements covered:
- probe_1 (POSITIVE CONTROL) — Req 1.1 / 3.2 / 4.2: HEAD response's last line is the bare CRLF (empty body), NO Content-Length header, NO 'Connection: close', status line still emitted. HOLDS patched, VIOLATED at base (base writes the full body — prepatch reproduced).
- probe_2 — Req 1.2: HEAD fully consumes the WSGI app's generator (a recorder past the last chunk fires) yet writes no body bytes. HOLDS patched.
- probe_3 — Req 2.1 / 2.2 / 3.3 / 4.1(non-HEAD w/ CL, threading): ordinary GET keeps full body + Content-Length: 52 + no Connection: close. HOLDS patched.
- probe_4 — Req 4.1: streaming GET with unknown length has no Content-Length and DOES assert 'Connection: close'. HOLDS patched.
- probe_5 — Req 5.1 (SHALL keep): underscore request headers ('Under_Score') excluded from WSGI environ; normal 'Some-Header' passes through. HOLDS patched.
- probe_6 — Req 4.3: known-length GET on a NON-threading server asserts 'Connection: close' while keeping Content-Length. HOLDS patched.

Discriminating power confirmed: positive control probe_1 fails at base and holds patched.

Candidate wrong-fix (weak.diff): the gold patch minus the block that deletes Content-Length for HEAD in cleanup_headers — i.e. a partial reading that strips the HEAD body and fixes the Connection policy but leaves the Content-Length header in place. probe_1 REJECTS it ('HEAD must have no Content-Length'), matching the hidden test's assertNotIn Content-Length assertion. probes 2-6 hold under it. This demonstrates the suite discriminates a requirements-incomplete implementation; therefore no requirements-conforming-yet-nonresolving patch was found. SOUND.

All needed runs completed (patched, base, candidate). weak.diff applies cleanly at base_commit.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Probe on gold-patched tree (HOLDS exit=0) and base (VIOLATED: HEAD returns 'helloworld' body) confirms the modeling boundary is the changed observable behavior. Additional checks: HEAD non-threading with Content-Length -> Connection:close set via the non-threading elif branch (True), which is consistent with Req4.2's precise wording 'on the basis of the missing length alone' (the CL was removed for HEAD, then the elif fires on the threading-server condition, not on missing length). HEAD threading -> no close (True). Req4.1 verified: GET without Content-Length on non-threading server sets Connection:close. All matches the two-clause cleanup_headers edit and the new finish_response override in patch.diff.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Requirements translate the public problem_statement (HEAD body omission per RFC 2616 §4.3, broken-pipe symptom, Content-Length inconsistency) into behavioral acceptance criteria. All named identifiers (basehttp.py, ServerHandler, WSGIRequestHandler, cleanup_headers, finish_response) are pre-existing real/stdlib names being localized, not fix-invented. The threading/non-threading connection-persistence policy (Req 4) reflects the PRE-EXISTING cleanup_headers logic being edited, not gold-invented behavior. No test names/paths/ids, no parametrization enumeration, no quoted test or gold code, no test literals (hello_world_body, 192.168.0.2, b'\r\n'), no test helper class names (Stub, UnclosableBytesIO). Req 1.2/1.4 describe intended consume-and-cleanup behavior (behavioral), not the test — the test doesn't even exercise the error path. Clean behavioral spec.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
