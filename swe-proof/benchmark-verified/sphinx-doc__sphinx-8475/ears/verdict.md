# P2 adversarial audit — sphinx-doc__sphinx-8475

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 7 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 7 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py`, `probe_7.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

Counterexample / evidence:

```
Weak candidate (catch TooManyRedirects then `return 'working', '', 0` WITHOUT retrying GET) passes probe_1 (Req 1.1/1.2) but is REJECTED by probe_7 (Req 1.3): with HEAD in a redirect loop and GET returning 404, the gold patch reports 'broken' (outcome from the GET), while the weak fix falsely reports 'working'. This proves the suite discriminates a plausibly-wrong reading of the requirements.
```

**Attacks re-run (7):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
"""Positive control -- Req 1.1 & 1.2: HEAD redirect loop -> GET fallback -> working, info "".
HOLDS on patched (fallback catches TooManyRedirects), FAILS at base (loop not caught -> broken).
"""
import http.server, json, os, socketserver, tempfile, threading, contextlib

class _Server(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True; allow_reuse_address = True

@contextlib.contextmanager
def http_server(handler, port=7777):
    srv = _Server(("localhost", port), handler)
    t = threading.Thread(target=srv.serve_forever, daemon=True); t.start()
    try: yield srv
    finally:
        srv.shutdown(); srv.server_close(); t.join(timeout=5)

def run_linkcheck(handler, link="http://localhost:7777/", confoverrides=None):
    from sphinx.application import Sphinx
    src = tempfile.mkdtemp(); out = tempfile.mkdtemp(); dt = tempfile.mkdtemp()
    open(os.path.join(src, "conf.py"), "w").write("exclude_patterns=['_build']\n")
    open(os.path.join(src, "index.rst"), "w").write("`local server <%s>`_\n" % link)
    with http_server(handler):
        app = Sphinx(src, src, out, dt, "linkcheck", confoverrides=confoverrides or {},
                     freshenv=True, status=None, warning=None)
        app.build()
    text = open(os.path.join(out, "output.json")).read().strip()
    rows = [json.loads(x) for x in text.splitlines() if x.strip()]
    return rows[0]

class InfiniteRedirectOnHeadHandler(http.server.BaseHTTPRequestHandler):
    def do_HEAD(self):
        self.send_response(302, "Found")
        self.send_header("Location", "http://localhost:7777/")
        self.end_headers()
    def do_GET(self):
        self.send_response(200, "OK"); self.end_headers(); self.wfile.write(b"ok\n")
    def log_message(self, *a): pass

row = run_linkcheck(InfiniteRedirectOnHeadHandler)
print("observed:", row)
ok = (row.get("status") == "working" and row.get("info") == ""
      and row.get("uri") == "http://localhost:7777/" and row.get("code") == 0)
print("PASS" if ok else "FAIL")
raise SystemExit(0 if ok else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""Req 2.1: HEAD HTTP status error -> GET fallback -> outcome from GET (working).
Server: HEAD returns 405, GET returns 200. Preserved pre-existing fallback.
HOLDS on patched (and base). Regression check for the HTTPError fallback.
"""
import http.server, json, os, socketserver, tempfile, threading, contextlib

class _Server(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True; allow_reuse_address = True

@contextlib.contextmanager
def http_server(handler, port=7777):
    srv = _Server(("localhost", port), handler)
    t = threading.Thread(target=srv.serve_forever, daemon=True); t.start()
    try: yield srv
    finally:
        srv.shutdown(); srv.server_close(); t.join(timeout=5)

def run_linkcheck(handler, link="http://localhost:7777/", confoverrides=None):
    from sphinx.application import Sphinx
    src = tempfile.mkdtemp(); out = tempfile.mkdtemp(); dt = tempfile.mkdtemp()
    open(os.path.join(src, "conf.py"), "w").write("exclude_patterns=['_build']\n")
    open(os.path.join(src, "index.rst"), "w").write("`local server <%s>`_\n" % link)
    with http_server(handler):
        app = Sphinx(src, src, out, dt, "linkcheck", confoverrides=confoverrides or {},
                     freshenv=True, status=None, warning=None)
        app.build()
    text = open(os.path.join(out, "output.json")).read().strip()
    rows = [json.loads(x) for x in text.splitlines() if x.strip()]
    return rows[0]

class HeadRejectHandler(http.server.BaseHTTPRequestHandler):
    def do_HEAD(self):
        self.send_response(405, "Method Not Allowed"); self.end_headers()
    def do_GET(self):
        self.send_response(200, "OK"); self.end_headers(); self.wfile.write(b"ok\n")
    def log_message(self, *a): pass

row = run_linkcheck(HeadRejectHandler)
print("observed:", row)
ok = (row.get("status") == "working" and row.get("info") == ""
      and row.get("uri") == "http://localhost:7777/")
print("PASS" if ok else "FAIL")
raise SystemExit(0 if ok else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""Req 3.1: determining request fails with 401 -> report 'working'.
Server answers 401 to both HEAD and GET. HEAD 401 -> HTTPError -> GET 401 ->
HTTPError -> classified as working ('Unauthorized' == working). Regression.
"""
import http.server, json, os, socketserver, tempfile, threading, contextlib

class _Server(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True; allow_reuse_address = True

@contextlib.contextmanager
def http_server(handler, port=7777):
    srv = _Server(("localhost", port), handler)
    t = threading.Thread(target=srv.serve_forever, daemon=True); t.start()
    try: yield srv
    finally:
        srv.shutdown(); srv.server_close(); t.join(timeout=5)

def run_linkcheck(handler, link="http://localhost:7777/"):
    from sphinx.application import Sphinx
    src = tempfile.mkdtemp(); out = tempfile.mkdtemp(); dt = tempfile.mkdtemp()
    open(os.path.join(src, "conf.py"), "w").write("exclude_patterns=['_build']\n")
    open(os.path.join(src, "index.rst"), "w").write("`local server <%s>`_\n" % link)
    with http_server(handler):
        app = Sphinx(src, src, out, dt, "linkcheck", freshenv=True, status=None, warning=None)
        app.build()
    text = open(os.path.join(out, "output.json")).read().strip()
    return [json.loads(x) for x in text.splitlines() if x.strip()][0]

class H(http.server.BaseHTTPRequestHandler):
    def do_HEAD(self):
        self.send_response(401, "Unauthorized"); self.end_headers()
    def do_GET(self):
        self.send_response(401, "Unauthorized"); self.end_headers()
    def log_message(self, *a): pass

row = run_linkcheck(H)
print("observed:", row)
ok = row.get("status") == "working"
print("PASS" if ok else "FAIL")
raise SystemExit(0 if ok else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""Req 3.2 & 3.3: 503 -> 'ignored'; other status (500) -> 'broken'.
Two servers on the same port sequentially. Both HEAD and GET return the status.
Regression checks for status classification.
"""
import http.server, json, os, socketserver, tempfile, threading, contextlib

class _Server(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True; allow_reuse_address = True

@contextlib.contextmanager
def http_server(handler, port=7777):
    srv = _Server(("localhost", port), handler)
    t = threading.Thread(target=srv.serve_forever, daemon=True); t.start()
    try: yield srv
    finally:
        srv.shutdown(); srv.server_close(); t.join(timeout=5)

def run_linkcheck(handler, link="http://localhost:7777/"):
    from sphinx.application import Sphinx
    src = tempfile.mkdtemp(); out = tempfile.mkdtemp(); dt = tempfile.mkdtemp()
    open(os.path.join(src, "conf.py"), "w").write("exclude_patterns=['_build']\n")
    open(os.path.join(src, "index.rst"), "w").write("`local server <%s>`_\n" % link)
    with http_server(handler):
        app = Sphinx(src, src, out, dt, "linkcheck", freshenv=True, status=None, warning=None)
        app.build()
    text = open(os.path.join(out, "output.json")).read().strip()
    return [json.loads(x) for x in text.splitlines() if x.strip()][0]

def make(status):
    class H(http.server.BaseHTTPRequestHandler):
        def do_HEAD(self):
            self.send_response(status); self.end_headers()
        def do_GET(self):
            self.send_response(status); self.end_headers()
        def log_message(self, *a): pass
    return H

r503 = run_linkcheck(make(503))
print("503 observed:", r503)
r500 = run_linkcheck(make(500))
print("500 observed:", r500)
ok = r503.get("status") == "ignored" and r500.get("status") == "broken"
print("PASS" if ok else "FAIL")
raise SystemExit(0 if ok else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""Req 4.2: determining response final URL differs -> 'redirected' with final URL
and the last redirect status code. Server: HEAD supports redirect once to
/?redirected=1 (204). Report 'redirected with Found' to ...?redirected=1, code 302.
Regression check for redirect reporting.
"""
import http.server, json, os, socketserver, tempfile, threading, contextlib

class _Server(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True; allow_reuse_address = True

@contextlib.contextmanager
def http_server(handler, port=7777):
    srv = _Server(("localhost", port), handler)
    t = threading.Thread(target=srv.serve_forever, daemon=True); t.start()
    try: yield srv
    finally:
        srv.shutdown(); srv.server_close(); t.join(timeout=5)

def run_linkcheck(handler, link="http://localhost:7777/"):
    from sphinx.application import Sphinx
    src = tempfile.mkdtemp(); out = tempfile.mkdtemp(); dt = tempfile.mkdtemp()
    open(os.path.join(src, "conf.py"), "w").write("exclude_patterns=['_build']\n")
    open(os.path.join(src, "index.rst"), "w").write("`local server <%s>`_\n" % link)
    with http_server(handler):
        app = Sphinx(src, src, out, dt, "linkcheck", freshenv=True, status=None, warning=None)
        app.build()
    text = open(os.path.join(out, "output.json")).read().strip()
    return [json.loads(x) for x in text.splitlines() if x.strip()][0]

class RedirectHandler(http.server.BaseHTTPRequestHandler):
    def _act(self):
        if self.path == "/?redirected=1":
            self.send_response(204, "No content"); self.end_headers()
        else:
            self.send_response(302, "Found")
            self.send_header("Location", "http://localhost:7777/?redirected=1")
            self.end_headers()
    def do_HEAD(self): self._act()
    def do_GET(self): self._act()
    def log_message(self, *a): pass

row = run_linkcheck(RedirectHandler)
print("observed:", row)
ok = (row.get("status") == "redirected"
      and row.get("info") == "http://localhost:7777/?redirected=1"
      and row.get("code") == 302)
print("PASS" if ok else "FAIL")
raise SystemExit(0 if ok else 1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
"""Req 5.1: with anchor checking enabled and URL has a fragment, GET the resource
and report 'broken' if the anchor is absent. Server returns HTML without the
anchor. Link points to #missing. Regression check for anchor behavior.
"""
import http.server, json, os, socketserver, tempfile, threading, contextlib

class _Server(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True; allow_reuse_address = True

@contextlib.contextmanager
def http_server(handler, port=7777):
    srv = _Server(("localhost", port), handler)
    t = threading.Thread(target=srv.serve_forever, daemon=True); t.start()
    try: yield srv
    finally:
        srv.shutdown(); srv.server_close(); t.join(timeout=5)

def run_linkcheck(handler, link):
    from sphinx.application import Sphinx
    src = tempfile.mkdtemp(); out = tempfile.mkdtemp(); dt = tempfile.mkdtemp()
    open(os.path.join(src, "conf.py"), "w").write("exclude_patterns=['_build']\n")
    open(os.path.join(src, "index.rst"), "w").write("`local server <%s>`_\n" % link)
    with http_server(handler):
        app = Sphinx(src, src, out, dt, "linkcheck", freshenv=True, status=None, warning=None)
        app.build()
    text = open(os.path.join(out, "output.json")).read().strip()
    return [json.loads(x) for x in text.splitlines() if x.strip()][0]

class HtmlHandler(http.server.BaseHTTPRequestHandler):
    body = b"<html><body><h1 id='present'>hi</h1></body></html>"
    def do_HEAD(self):
        self.send_response(200); self.send_header("Content-Type", "text/html")
        self.end_headers()
    def do_GET(self):
        self.do_HEAD(); self.wfile.write(self.body)
    def log_message(self, *a): pass

row = run_linkcheck(HtmlHandler, "http://localhost:7777/#missing")
print("observed:", row)
ok = row.get("status") == "broken" and "missing" in (row.get("info") or "").lower()
print("PASS" if ok else "FAIL")
raise SystemExit(0 if ok else 1)
```

Attack 7 — `probe_7.py` → holds on the patched tree (good)

```python
"""Req 1.3: HEAD redirect loop, then the fallback GET itself FAILS -> report the
outcome from that GET failure (here GET returns 404 -> 'broken'), NOT 'working',
and do NOT re-raise the redirect loop. Discriminates a naive "on redirect loop
just report working" fix. Server: HEAD 302->self (loop); GET 404.
"""
import http.server, json, os, socketserver, tempfile, threading, contextlib

class _Server(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True; allow_reuse_address = True

@contextlib.contextmanager
def http_server(handler, port=7777):
    srv = _Server(("localhost", port), handler)
    t = threading.Thread(target=srv.serve_forever, daemon=True); t.start()
    try: yield srv
    finally:
        srv.shutdown(); srv.server_close(); t.join(timeout=5)

def run_linkcheck(handler, link="http://localhost:7777/"):
    from sphinx.application import Sphinx
    src = tempfile.mkdtemp(); out = tempfile.mkdtemp(); dt = tempfile.mkdtemp()
    open(os.path.join(src, "conf.py"), "w").write("exclude_patterns=['_build']\n")
    open(os.path.join(src, "index.rst"), "w").write("`local server <%s>`_\n" % link)
    with http_server(handler):
        app = Sphinx(src, src, out, dt, "linkcheck", freshenv=True, status=None, warning=None)
        app.build()
    text = open(os.path.join(out, "output.json")).read().strip()
    return [json.loads(x) for x in text.splitlines() if x.strip()][0]

class H(http.server.BaseHTTPRequestHandler):
    def do_HEAD(self):
        self.send_response(302, "Found")
        self.send_header("Location", "http://localhost:7777/")
        self.end_headers()
    def do_GET(self):
        self.send_response(404, "Not Found"); self.end_headers()
    def log_message(self, *a): pass

row = run_linkcheck(H)
print("observed:", row)
# Outcome must come from the GET failure (404 -> broken), never 'working'.
ok = row.get("status") == "broken"
print("PASS" if ok else "FAIL")
raise SystemExit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Positive control -- Req 1.1 & 1.2: HEAD redirect loop -> GET fallback -> working, info "".
HOLDS on patched (fallback catches TooManyRedirects), FAILS at base (loop not caught -> broken).
"""
import http.server, json, os, socketserver, tempfile, threading, contextlib

class _Server(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True; allow_reuse_address = True

@contextlib.contextmanager
def http_server(handler, port=7777):
    srv = _Server(("localhost", port), handler)
    t = threading.Thread(target=srv.serve_forever, daemon=True); t.start()
    try: yield srv
    finally:
        srv.shutdown(); srv.server_close(); t.join(timeout=5)

def run_linkcheck(handler, link="http://localhost:7777/", confoverrides=None):
    from sphinx.application import Sphinx
    src = tempfile.mkdtemp(); out = tempfile.mkdtemp(); dt = tempfile.mkdtemp()
    open(os.path.join(src, "conf.py"), "w").write("exclude_patterns=['_build']\n")
    open(os.path.join(src, "index.rst"), "w").write("`local server <%s>`_\n" % link)
    with http_server(handler):
        app = Sphinx(src, src, out, dt, "linkcheck", confoverrides=confoverrides or {},
                     freshenv=True, status=None, warning=None)
        app.build()
    text = open(os.path.join(out, "output.json")).read().strip()
    rows = [json.loads(x) for x in text.splitlines() if x.strip()]
    return rows[0]

class InfiniteRedirectOnHeadHandler(http.server.BaseHTTPRequestHandler):
    def do_HEAD(self):
        self.send_response(302, "Found")
        self.send_header("Location", "http://localhost:7777/")
        self.end_headers()
    def do_GET(self):
        self.send_response(200, "OK"); self.end_headers(); self.wfile.write(b"ok\n")
    def log_message(self, *a): pass

row = run_linkcheck(InfiniteRedirectOnHeadHandler)
print("observed:", row)
ok = (row.get("status") == "working" and row.get("info") == ""
      and row.get("uri") == "http://localhost:7777/" and row.get("code") == 0)
print("PASS" if ok else "FAIL")
raise SystemExit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Real sphinx linkcheck builds run against local stdlib HTTP servers inside the instance image (harness inlined per-probe; sole external link in index.rst -> single output.json row).

Probe results (all on gold-patched tree unless noted):
- probe_1 (POSITIVE CONTROL, Req 1.1+1.2): HEAD 302->self loop (TooManyRedirects), GET 200. HOLDS patched (status=working, info=""); FAILS at base (status=broken, 'Exceeded 30 redirects.'). Discriminates.
- probe_2 (Req 2.1): HEAD 405 -> GET 200 -> working. HOLDS. Pre-existing HTTPError fallback preserved.
- probe_3 (Req 3.1): 401 on HEAD+GET -> working. HOLDS.
- probe_4 (Req 3.2+3.3): 503 -> ignored; 500 -> broken. HOLDS.
- probe_5 (Req 4.2): HEAD redirect 302 -> /?redirected=1 (204) -> redirected, info=final URL, code=302. HOLDS.
- probe_6 (Req 5.1): anchor #missing absent in GET body -> broken "Anchor 'missing' not found". HOLDS.
- probe_7 (Req 1.3): HEAD loop then GET 404 -> broken (outcome from GET, not re-raised loop). HOLDS on gold; VIOLATED under weak candidate.

Weak candidate diff applies cleanly at base_commit; probes re-run under it: probe_1 HOLDS, probe_7 VIOLATED. >=5 distinct probes all hold on the patched tree, positive control discriminates (holds patched / fails base), and a probe-conforming-but-wrong candidate is rejected by the suite. Verdict SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 7 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 7 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py`, `probe_7.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

Counterexample / evidence:

```
Weak candidate (catch TooManyRedirects then `return 'working', '', 0` WITHOUT retrying GET) passes probe_1 (Req 1.1/1.2) but is REJECTED by probe_7 (Req 1.3): with HEAD in a redirect loop and GET returning 404, the gold patch reports 'broken' (outcome from the GET), while the weak fix falsely reports 'working'. This proves the suite discriminates a plausibly-wrong reading of the requirements.
```

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
"""Positive control -- Req 1.1 & 1.2: HEAD redirect loop -> GET fallback -> working, info "".
HOLDS on patched (fallback catches TooManyRedirects), FAILS at base (loop not caught -> broken).
"""
import http.server, json, os, socketserver, tempfile, threading, contextlib

class _Server(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True; allow_reuse_address = True

@contextlib.contextmanager
def http_server(handler, port=7777):
    srv = _Server(("localhost", port), handler)
    t = threading.Thread(target=srv.serve_forever, daemon=True); t.start()
    try: yield srv
    finally:
        srv.shutdown(); srv.server_close(); t.join(timeout=5)

def run_linkcheck(handler, link="http://localhost:7777/", confoverrides=None):
    from sphinx.application import Sphinx
    src = tempfile.mkdtemp(); out = tempfile.mkdtemp(); dt = tempfile.mkdtemp()
    open(os.path.join(src, "conf.py"), "w").write("exclude_patterns=['_build']\n")
    open(os.path.join(src, "index.rst"), "w").write("`local server <%s>`_\n" % link)
    with http_server(handler):
        app = Sphinx(src, src, out, dt, "linkcheck", confoverrides=confoverrides or {},
                     freshenv=True, status=None, warning=None)
        app.build()
    text = open(os.path.join(out, "output.json")).read().strip()
    rows = [json.loads(x) for x in text.splitlines() if x.strip()]
    return rows[0]

class InfiniteRedirectOnHeadHandler(http.server.BaseHTTPRequestHandler):
    def do_HEAD(self):
        self.send_response(302, "Found")
        self.send_header("Location", "http://localhost:7777/")
        self.end_headers()
    def do_GET(self):
        self.send_response(200, "OK"); self.end_headers(); self.wfile.write(b"ok\n")
    def log_message(self, *a): pass

row = run_linkcheck(InfiniteRedirectOnHeadHandler)
print("observed:", row)
ok = (row.get("status") == "working" and row.get("info") == ""
      and row.get("uri") == "http://localhost:7777/" and row.get("code") == 0)
print("PASS" if ok else "FAIL")
raise SystemExit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Real sphinx linkcheck builds run against local stdlib HTTP servers inside the instance image (harness inlined per-probe; sole external link in index.rst -> single output.json row).

Probe results (all on gold-patched tree unless noted):
- probe_1 (POSITIVE CONTROL, Req 1.1+1.2): HEAD 302->self loop (TooManyRedirects), GET 200. HOLDS patched (status=working, info=""); FAILS at base (status=broken, 'Exceeded 30 redirects.'). Discriminates.
- probe_2 (Req 2.1): HEAD 405 -> GET 200 -> working. HOLDS. Pre-existing HTTPError fallback preserved.
- probe_3 (Req 3.1): 401 on HEAD+GET -> working. HOLDS.
- probe_4 (Req 3.2+3.3): 503 -> ignored; 500 -> broken. HOLDS.
- probe_5 (Req 4.2): HEAD redirect 302 -> /?redirected=1 (204) -> redirected, info=final URL, code=302. HOLDS.
- probe_6 (Req 5.1): anchor #missing absent in GET body -> broken "Anchor 'missing' not found". HOLDS.
- probe_7 (Req 1.3): HEAD loop then GET 404 -> broken (outcome from GET, not re-raised loop). HOLDS on gold; VIOLATED under weak candidate.

Weak candidate diff applies cleanly at base_commit; probes re-run under it: probe_1 HOLDS, probe_7 VIOLATED. >=5 distinct probes all hold on the patched tree, positive control discriminates (holds patched / fails base), and a probe-conforming-but-wrong candidate is rejected by the suite. Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Confirmed base-commit source of check_uri via the sphinx git repo; only diff is the widened except tuple plus the import. Requirements pin the changed observable boundary (redirect-loop HEAD -> GET fallback) biconditionally and preserve the rest accurately. FAIL_TO_PASS test test_TooManyRedirects_on_HEAD is consistent with Req1. Probe tool truncates stdout so source was read from the upstream repository at base_commit; patch.diff confirms the single-line change.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The requirements describe behavior only. The public problem_statement already names the HEAD->GET fallback, TooManyRedirects, and the redirect-loop scenario. The doc adds: (a) module/function localization (sphinx/builders/linkcheck.py, check_uri, check_thread, CheckExternalLinksBuilder) — legitimate real source identifiers, not fix-invented; the gold patch invents no new identifier (it merely widens `except HTTPError` to `except (HTTPError, TooManyRedirects)`). (b) status-classification rules (401->working, 503->ignored, else->broken; connection/TLS -> broken) and redirect/trailing-slash reporting — these describe PRE-EXISTING code behavior visible in the source, not content derived from the hidden test. The hidden test (test_TooManyRedirects_on_HEAD, its InfiniteRedirectOnHeadHandler, localhost:7777, output.json assertion) is nowhere quoted or near-quoted: no test name, path, handler class, port, or parametrization ids leak. Req 1.2's 'working + empty message on final URL == requested URL' is a behavioral restatement of existing redirect reporting, not a transcription of the single test's assertion. No test-shaped enumeration mirroring parametrized cases (F2P has exactly one test, no parametrization).

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
