# P2 adversarial audit — sphinx-doc__sphinx-8269

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 8 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 8 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py`, `probe_7.py`, `probe_8.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (8):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
# Positive control + Req1.1/1.2/1.5: error status governs anchor path, reported as HTTP error (broken),
# NOT anchor-not-found -- even though the anchor IS present in the error body.
import http.server, threading, socket, tempfile, os, json, io, sys

BODY = b"<html><body><p id='anchor'>here is the anchor</p></body></html>"

class Handler(http.server.BaseHTTPRequestHandler):
    status = 500
    def log_message(self, *a): pass
    def do_HEAD(self):
        self.send_response(self.status); self.send_header("Content-Length","0"); self.end_headers()
    def do_GET(self):
        self.send_response(self.status)
        self.send_header("Content-Type","text/html")
        self.send_header("Content-Length",str(len(BODY)))
        self.end_headers()
        self.wfile.write(BODY)

def free_port():
    s=socket.socket(); s.bind(("localhost",0)); p=s.getsockname()[1]; s.close(); return p

def build(port):
    src=tempfile.mkdtemp()
    open(os.path.join(src,"conf.py"),"w").write("linkcheck_anchors=True\nexclude_patterns=['_build']\n")
    open(os.path.join(src,"index.rst"),"w").write("`local <http://localhost:%d/#anchor>`_\n"%port)
    out=tempfile.mkdtemp()
    from sphinx.application import Sphinx
    app=Sphinx(src,src,out,os.path.join(out,".doctrees"),"linkcheck",status=io.StringIO(),warning=io.StringIO(),freshenv=True)
    app.build()
    return json.loads(open(os.path.join(out,"output.json")).read().strip().splitlines()[0])

port=free_port()
srv=http.server.HTTPServer(("localhost",port),Handler)
t=threading.Thread(target=srv.serve_forever,kwargs={"poll_interval":0.01},daemon=True); t.start()
try:
    rec=build(port)
finally:
    srv.shutdown(); srv.server_close()

status=rec["status"]; info=rec["info"]
print("OBSERVED status=%r info=%r" % (status, info))
anchor_msg = "anchor" in info.lower() and "not found" in info.lower()
ok = (status=="broken") and ("500" in info) and ("Server Error" in info) and (not anchor_msg)
print("CRITERION (Req1.1/1.2/1.5) ok=%r" % ok)
sys.exit(0 if ok else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
import http.server, threading, socket, tempfile, os, json, io, sys
BODY=b"<html><body>no anchor here</body></html>"
class H(http.server.BaseHTTPRequestHandler):
    def log_message(self,*a): pass
    def do_HEAD(self): self.send_error(401,"Unauthorized")
    def do_GET(self):
        self.send_response(401); self.send_header("Content-Type","text/html")
        self.send_header("Content-Length",str(len(BODY))); self.end_headers()
        try: self.wfile.write(BODY)
        except Exception: pass
def fp():
    s=socket.socket(); s.bind(("localhost",0)); p=s.getsockname()[1]; s.close(); return p
def build(port):
    src=tempfile.mkdtemp()
    open(os.path.join(src,"conf.py"),"w").write("linkcheck_anchors=True\nexclude_patterns=['_build']\n")
    open(os.path.join(src,"index.rst"),"w").write("`local <http://localhost:%d/#anchor>`_\n"%port)
    out=tempfile.mkdtemp()
    from sphinx.application import Sphinx
    app=Sphinx(src,src,out,os.path.join(out,".doctrees"),"linkcheck",status=io.StringIO(),warning=io.StringIO(),freshenv=True)
    app.build()
    return json.loads(open(os.path.join(out,"output.json")).read().strip().splitlines()[0])
port=fp(); srv=http.server.HTTPServer(("localhost",port),H)
threading.Thread(target=srv.serve_forever,kwargs={"poll_interval":0.01},daemon=True).start()
try: rec=build(port)
finally: srv.shutdown(); srv.server_close()
print("OBSERVED status=%r info=%r"%(rec["status"],rec["info"]))
ok = rec["status"]=="working"
print("CRITERION Req1.3 (401 unauthorized -> working) ok=%r"%ok)
sys.exit(0 if ok else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
import http.server, threading, socket, tempfile, os, json, io, sys
BODY=b"<html><body>no anchor</body></html>"
class H(http.server.BaseHTTPRequestHandler):
    def log_message(self,*a): pass
    def do_HEAD(self): self.send_error(503,"Service Unavailable")
    def do_GET(self):
        self.send_response(503); self.send_header("Content-Type","text/html")
        self.send_header("Content-Length",str(len(BODY))); self.end_headers()
        try: self.wfile.write(BODY)
        except Exception: pass
def fp():
    s=socket.socket(); s.bind(("localhost",0)); p=s.getsockname()[1]; s.close(); return p
def build(port):
    src=tempfile.mkdtemp()
    open(os.path.join(src,"conf.py"),"w").write("linkcheck_anchors=True\nexclude_patterns=['_build']\n")
    open(os.path.join(src,"index.rst"),"w").write("`local <http://localhost:%d/#anchor>`_\n"%port)
    out=tempfile.mkdtemp()
    from sphinx.application import Sphinx
    app=Sphinx(src,src,out,os.path.join(out,".doctrees"),"linkcheck",status=io.StringIO(),warning=io.StringIO(),freshenv=True)
    app.build()
    return json.loads(open(os.path.join(out,"output.json")).read().strip().splitlines()[0])
port=fp(); srv=http.server.HTTPServer(("localhost",port),H)
threading.Thread(target=srv.serve_forever,kwargs={"poll_interval":0.01},daemon=True).start()
try: rec=build(port)
finally: srv.shutdown(); srv.server_close()
print("OBSERVED status=%r info=%r"%(rec["status"],rec["info"]))
ok = rec["status"]=="ignored"
print("CRITERION Req1.4 (503 -> ignored) ok=%r"%ok)
sys.exit(0 if ok else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
import http.server, threading, socket, tempfile, os, json, io, sys
BODY=b"<html><body><p>no matching id here</p></body></html>"
class H(http.server.BaseHTTPRequestHandler):
    def log_message(self,*a): pass
    def do_HEAD(self):
        self.send_response(200); self.send_header("Content-Length","0"); self.end_headers()
    def do_GET(self):
        self.send_response(200); self.send_header("Content-Type","text/html")
        self.send_header("Content-Length",str(len(BODY))); self.end_headers()
        self.wfile.write(BODY)
def fp():
    s=socket.socket(); s.bind(("localhost",0)); p=s.getsockname()[1]; s.close(); return p
def build(port):
    src=tempfile.mkdtemp()
    open(os.path.join(src,"conf.py"),"w").write("linkcheck_anchors=True\nexclude_patterns=['_build']\n")
    open(os.path.join(src,"index.rst"),"w").write("`local <http://localhost:%d/#missing_anchor>`_\n"%port)
    out=tempfile.mkdtemp()
    from sphinx.application import Sphinx
    app=Sphinx(src,src,out,os.path.join(out,".doctrees"),"linkcheck",status=io.StringIO(),warning=io.StringIO(),freshenv=True)
    app.build()
    return json.loads(open(os.path.join(out,"output.json")).read().strip().splitlines()[0])
port=fp(); srv=http.server.HTTPServer(("localhost",port),H)
threading.Thread(target=srv.serve_forever,kwargs={"poll_interval":0.01},daemon=True).start()
try: rec=build(port)
finally: srv.shutdown(); srv.server_close()
print("OBSERVED status=%r info=%r"%(rec["status"],rec["info"]))
ok = rec["status"]=="broken" and "anchor" in rec["info"].lower() and "not found" in rec["info"].lower()
print("CRITERION Req2.1 (200, anchor missing -> broken anchor-not-found) ok=%r"%ok)
sys.exit(0 if ok else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
import http.server, threading, socket, tempfile, os, json, io, sys
BODY=b"<html><body><p id='realanchor'>content</p></body></html>"
class H(http.server.BaseHTTPRequestHandler):
    def log_message(self,*a): pass
    def do_HEAD(self):
        self.send_response(200); self.send_header("Content-Length","0"); self.end_headers()
    def do_GET(self):
        self.send_response(200); self.send_header("Content-Type","text/html")
        self.send_header("Content-Length",str(len(BODY))); self.end_headers()
        self.wfile.write(BODY)
def fp():
    s=socket.socket(); s.bind(("localhost",0)); p=s.getsockname()[1]; s.close(); return p
def build(port):
    src=tempfile.mkdtemp()
    open(os.path.join(src,"conf.py"),"w").write("linkcheck_anchors=True\nexclude_patterns=['_build']\n")
    open(os.path.join(src,"index.rst"),"w").write("`local <http://localhost:%d/#realanchor>`_\n"%port)
    out=tempfile.mkdtemp()
    from sphinx.application import Sphinx
    app=Sphinx(src,src,out,os.path.join(out,".doctrees"),"linkcheck",status=io.StringIO(),warning=io.StringIO(),freshenv=True)
    app.build()
    return json.loads(open(os.path.join(out,"output.json")).read().strip().splitlines()[0])
port=fp(); srv=http.server.HTTPServer(("localhost",port),H)
threading.Thread(target=srv.serve_forever,kwargs={"poll_interval":0.01},daemon=True).start()
try: rec=build(port)
finally: srv.shutdown(); srv.server_close()
print("OBSERVED status=%r info=%r"%(rec["status"],rec["info"]))
ok = rec["status"]=="working"
print("CRITERION Req2.2 (200, anchor present -> working) ok=%r"%ok)
sys.exit(0 if ok else 1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
import http.server, threading, socket, tempfile, os, json, io, sys
BODY=b"<html><body><p>no anchor at all</p></body></html>"
class H(http.server.BaseHTTPRequestHandler):
    def log_message(self,*a): pass
    def do_HEAD(self):
        self.send_response(200); self.send_header("Content-Length","0"); self.end_headers()
    def do_GET(self):
        self.send_response(200); self.send_header("Content-Type","text/html")
        self.send_header("Content-Length",str(len(BODY))); self.end_headers()
        self.wfile.write(BODY)
def fp():
    s=socket.socket(); s.bind(("localhost",0)); p=s.getsockname()[1]; s.close(); return p
def build(port):
    src=tempfile.mkdtemp()
    open(os.path.join(src,"conf.py"),"w").write("linkcheck_anchors=True\nlinkcheck_anchors_ignore=['ignoreme']\nexclude_patterns=['_build']\n")
    open(os.path.join(src,"index.rst"),"w").write("`local <http://localhost:%d/#ignoreme>`_\n"%port)
    out=tempfile.mkdtemp()
    from sphinx.application import Sphinx
    app=Sphinx(src,src,out,os.path.join(out,".doctrees"),"linkcheck",status=io.StringIO(),warning=io.StringIO(),freshenv=True)
    app.build()
    return json.loads(open(os.path.join(out,"output.json")).read().strip().splitlines()[0])
port=fp(); srv=http.server.HTTPServer(("localhost",port),H)
threading.Thread(target=srv.serve_forever,kwargs={"poll_interval":0.01},daemon=True).start()
try: rec=build(port)
finally: srv.shutdown(); srv.server_close()
print("OBSERVED status=%r info=%r"%(rec["status"],rec["info"]))
# fragment check skipped -> not broken due to anchor; goes down HEAD/GET path -> working
ok = rec["status"]=="working"
print("CRITERION Req2.3 (ignored fragment -> skip anchor check -> working) ok=%r"%ok)
sys.exit(0 if ok else 1)
```

Attack 7 — `probe_7.py` → holds on the patched tree (good)

```python
import http.server, threading, socket, tempfile, os, json, io, sys
BODY=b"<html><body><p id='anchor'>anchor present but anchors disabled</p></body></html>"
class H(http.server.BaseHTTPRequestHandler):
    def log_message(self,*a): pass
    def do_HEAD(self): self.send_error(500,"Internal Server Error")
    def do_GET(self):
        self.send_response(500); self.send_header("Content-Type","text/html")
        self.send_header("Content-Length",str(len(BODY))); self.end_headers()
        try: self.wfile.write(BODY)
        except Exception: pass
def fp():
    s=socket.socket(); s.bind(("localhost",0)); p=s.getsockname()[1]; s.close(); return p
def build(port):
    src=tempfile.mkdtemp()
    open(os.path.join(src,"conf.py"),"w").write("linkcheck_anchors=False\nexclude_patterns=['_build']\n")
    open(os.path.join(src,"index.rst"),"w").write("`local <http://localhost:%d/#anchor>`_\n"%port)
    out=tempfile.mkdtemp()
    from sphinx.application import Sphinx
    app=Sphinx(src,src,out,os.path.join(out,".doctrees"),"linkcheck",status=io.StringIO(),warning=io.StringIO(),freshenv=True)
    app.build()
    return json.loads(open(os.path.join(out,"output.json")).read().strip().splitlines()[0])
port=fp(); srv=http.server.HTTPServer(("localhost",port),H)
threading.Thread(target=srv.serve_forever,kwargs={"poll_interval":0.01},daemon=True).start()
try: rec=build(port)
finally: srv.shutdown(); srv.server_close()
print("OBSERVED status=%r info=%r"%(rec["status"],rec["info"]))
ok = rec["status"]=="broken" and "500" in rec["info"] and ("anchor" not in rec["info"].lower() or "not found" not in rec["info"].lower())
print("CRITERION Req3.1 (anchors off, 500 -> broken HTTP error) ok=%r"%ok)
sys.exit(0 if ok else 1)
```

Attack 8 — `probe_8.py` → holds on the patched tree (good)

```python
import tempfile, os, json, io, sys
def build():
    src=tempfile.mkdtemp()
    open(os.path.join(src,"conf.py"),"w").write("linkcheck_anchors=True\nexclude_patterns=['_build']\n")
    open(os.path.join(src,"index.rst"),"w").write("`mail <mailto:someone@example.com>`_\n")
    out=tempfile.mkdtemp()
    from sphinx.application import Sphinx
    app=Sphinx(src,src,out,os.path.join(out,".doctrees"),"linkcheck",status=io.StringIO(),warning=io.StringIO(),freshenv=True)
    app.build()
    data=open(os.path.join(out,"output.json")).read().strip()
    return [json.loads(l) for l in data.splitlines()] if data else []
recs=build()
print("OBSERVED recs=%r"%recs)
# mailto should NOT be reported as broken; typically 'unchecked' -> not emitted, or working.
bad = any(r.get("uri","").startswith("mailto:") and r.get("status")=="broken" for r in recs)
ok = not bad
print("CRITERION Req3.2 (mailto not broken) ok=%r"%ok)
sys.exit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
# Positive control + Req1.1/1.2/1.5: error status governs anchor path, reported as HTTP error (broken),
# NOT anchor-not-found -- even though the anchor IS present in the error body.
import http.server, threading, socket, tempfile, os, json, io, sys

BODY = b"<html><body><p id='anchor'>here is the anchor</p></body></html>"

class Handler(http.server.BaseHTTPRequestHandler):
    status = 500
    def log_message(self, *a): pass
    def do_HEAD(self):
        self.send_response(self.status); self.send_header("Content-Length","0"); self.end_headers()
    def do_GET(self):
        self.send_response(self.status)
        self.send_header("Content-Type","text/html")
        self.send_header("Content-Length",str(len(BODY)))
        self.end_headers()
        self.wfile.write(BODY)

def free_port():
    s=socket.socket(); s.bind(("localhost",0)); p=s.getsockname()[1]; s.close(); return p

def build(port):
    src=tempfile.mkdtemp()
    open(os.path.join(src,"conf.py"),"w").write("linkcheck_anchors=True\nexclude_patterns=['_build']\n")
    open(os.path.join(src,"index.rst"),"w").write("`local <http://localhost:%d/#anchor>`_\n"%port)
    out=tempfile.mkdtemp()
    from sphinx.application import Sphinx
    app=Sphinx(src,src,out,os.path.join(out,".doctrees"),"linkcheck",status=io.StringIO(),warning=io.StringIO(),freshenv=True)
    app.build()
    return json.loads(open(os.path.join(out,"output.json")).read().strip().splitlines()[0])

port=free_port()
srv=http.server.HTTPServer(("localhost",port),Handler)
t=threading.Thread(target=srv.serve_forever,kwargs={"poll_interval":0.01},daemon=True); t.start()
try:
    rec=build(port)
finally:
    srv.shutdown(); srv.server_close()

status=rec["status"]; info=rec["info"]
print("OBSERVED status=%r info=%r" % (status, info))
anchor_msg = "anchor" in info.lower() and "not found" in info.lower()
ok = (status=="broken") and ("500" in info) and ("Server Error" in info) and (not anchor_msg)
print("CRITERION (Req1.1/1.2/1.5) ok=%r" % ok)
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance sphinx-8269: gold patch adds `response.raise_for_status()` after the anchor-path GET in check_uri, so an HTTP error status governs the outcome before the fragment is inspected and is routed through the existing except-handler that special-cases 401->working / 503->ignored / else->broken with the standard 'NNN Server Error ... for url:' text.

Probe suite (all run in the official image via nl_attack, building a real linkcheck project against a stdlib HTTP server):
- probe_1 (POSITIVE CONTROL; Req1.1/1.2/1.5): 500 error whose body CONTAINS the anchor -> must be 'broken' with '500 Server Error ...', NOT 'anchor not found'. HOLDS patched (broken/'500 Server Error: Internal Server Error for url:'); FAILS at base (status='working', empty info -- base never checks status and finds the anchor in the error body). Discriminates.
- probe_2 (Req1.3): 401 in anchor path -> 'working' (' - unauthorized'). HOLDS.
- probe_3 (Req1.4): 503 in anchor path -> 'ignored'. HOLDS.
- probe_4 (Req2.1): 200 + anchor absent -> 'broken', "Anchor '...' not found". HOLDS.
- probe_5 (Req2.2): 200 + anchor present -> 'working'. HOLDS.
- probe_6 (Req2.3): fragment matches linkcheck_anchors_ignore -> fragment check skipped, non-anchor validation -> 'working'. HOLDS.
- probe_7 (Req3.1 regression): linkcheck_anchors=False + 500 -> 'broken' via HEAD/GET path, standard HTTP text, unchanged. HOLDS.
- probe_8 (Req3.2 regression): mailto: URI -> not broken ('unchecked'). HOLDS.

DISCRIMINATION / candidate patch 'naive_generic_broken' (weak.diff): checks status_code>=400 but returns generic ('broken','HTTP %d') BEFORE/without the except-branch special-casing. Applies at base_commit cleanly. Under it probe_1 REJECTS (info 'HTTP 500' not standard text -> also would fail F2P test's exact-string assertion), probe_2 REJECTS (401 wrongly 'broken' instead of 'working'), probe_3 REJECTS (503 wrongly 'broken' instead of 'ignored'). Probes 4-8 still hold. So the suite discriminates wrong implementations and is NOT too weak. No requirements-conforming alternative found: any patch that satisfies probes 1-3 must funnel the error status through raise_for_status()->the existing handler, which is exactly the gold behavior that resolves the F2P test.

Conclusion: >=5 distinct probes all hold on the patched tree, positive control holds patched & fails at base (prepatch reproduced), and the plausible naive fix is rejected by 3 probes. SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 8 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 8 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py`, `probe_7.py`, `probe_8.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (8):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts, and on this backend both roles put it through the same derivation: every block below is a requirement probe run on the gold-patched tree, and the `machine verdict:` line each role publishes above reports BOTH that its probes hold there and how many candidate patches the probe suite rejected — so the two roles re-ran ONE probe suite and each recorded its own outcome for every probe in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `probe_1.py` → holds on the patched tree (good)

Attack 2 — `probe_2.py` → holds on the patched tree (good)

Attack 3 — `probe_3.py` → holds on the patched tree (good)

Attack 4 — `probe_4.py` → holds on the patched tree (good)

Attack 5 — `probe_5.py` → holds on the patched tree (good)

Attack 6 — `probe_6.py` → holds on the patched tree (good)

Attack 7 — `probe_7.py` → holds on the patched tree (good)

Attack 8 — `probe_8.py` → holds on the patched tree (good)

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
# Positive control + Req1.1/1.2/1.5: error status governs anchor path, reported as HTTP error (broken),
# NOT anchor-not-found -- even though the anchor IS present in the error body.
import http.server, threading, socket, tempfile, os, json, io, sys

BODY = b"<html><body><p id='anchor'>here is the anchor</p></body></html>"

class Handler(http.server.BaseHTTPRequestHandler):
    status = 500
    def log_message(self, *a): pass
    def do_HEAD(self):
        self.send_response(self.status); self.send_header("Content-Length","0"); self.end_headers()
    def do_GET(self):
        self.send_response(self.status)
        self.send_header("Content-Type","text/html")
        self.send_header("Content-Length",str(len(BODY)))
        self.end_headers()
        self.wfile.write(BODY)

def free_port():
    s=socket.socket(); s.bind(("localhost",0)); p=s.getsockname()[1]; s.close(); return p

def build(port):
    src=tempfile.mkdtemp()
    open(os.path.join(src,"conf.py"),"w").write("linkcheck_anchors=True\nexclude_patterns=['_build']\n")
    open(os.path.join(src,"index.rst"),"w").write("`local <http://localhost:%d/#anchor>`_\n"%port)
    out=tempfile.mkdtemp()
    from sphinx.application import Sphinx
    app=Sphinx(src,src,out,os.path.join(out,".doctrees"),"linkcheck",status=io.StringIO(),warning=io.StringIO(),freshenv=True)
    app.build()
    return json.loads(open(os.path.join(out,"output.json")).read().strip().splitlines()[0])

port=free_port()
srv=http.server.HTTPServer(("localhost",port),Handler)
t=threading.Thread(target=srv.serve_forever,kwargs={"poll_interval":0.01},daemon=True); t.start()
try:
    rec=build(port)
finally:
    srv.shutdown(); srv.server_close()

status=rec["status"]; info=rec["info"]
print("OBSERVED status=%r info=%r" % (status, info))
anchor_msg = "anchor" in info.lower() and "not found" in info.lower()
ok = (status=="broken") and ("500" in info) and ("Server Error" in info) and (not anchor_msg)
print("CRITERION (Req1.1/1.2/1.5) ok=%r" % ok)
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance sphinx-8269: gold patch adds `response.raise_for_status()` after the anchor-path GET in check_uri, so an HTTP error status governs the outcome before the fragment is inspected and is routed through the existing except-handler that special-cases 401->working / 503->ignored / else->broken with the standard 'NNN Server Error ... for url:' text.

Probe suite (all run in the official image via nl_attack, building a real linkcheck project against a stdlib HTTP server):
- probe_1 (POSITIVE CONTROL; Req1.1/1.2/1.5): 500 error whose body CONTAINS the anchor -> must be 'broken' with '500 Server Error ...', NOT 'anchor not found'. HOLDS patched (broken/'500 Server Error: Internal Server Error for url:'); FAILS at base (status='working', empty info -- base never checks status and finds the anchor in the error body). Discriminates.
- probe_2 (Req1.3): 401 in anchor path -> 'working' (' - unauthorized'). HOLDS.
- probe_3 (Req1.4): 503 in anchor path -> 'ignored'. HOLDS.
- probe_4 (Req2.1): 200 + anchor absent -> 'broken', "Anchor '...' not found". HOLDS.
- probe_5 (Req2.2): 200 + anchor present -> 'working'. HOLDS.
- probe_6 (Req2.3): fragment matches linkcheck_anchors_ignore -> fragment check skipped, non-anchor validation -> 'working'. HOLDS.
- probe_7 (Req3.1 regression): linkcheck_anchors=False + 500 -> 'broken' via HEAD/GET path, standard HTTP text, unchanged. HOLDS.
- probe_8 (Req3.2 regression): mailto: URI -> not broken ('unchecked'). HOLDS.

DISCRIMINATION / candidate patch 'naive_generic_broken' (weak.diff): checks status_code>=400 but returns generic ('broken','HTTP %d') BEFORE/without the except-branch special-casing. Applies at base_commit cleanly. Under it probe_1 REJECTS (info 'HTTP 500' not standard text -> also would fail F2P test's exact-string assertion), probe_2 REJECTS (401 wrongly 'broken' instead of 'working'), probe_3 REJECTS (503 wrongly 'broken' instead of 'ignored'). Probes 4-8 still hold. So the suite discriminates wrong implementations and is NOT too weak. No requirements-conforming alternative found: any patch that satisfies probes 1-3 must funnel the error status through raise_for_status()->the existing handler, which is exactly the gold behavior that resolves the F2P test.

Conclusion: >=5 distinct probes all hold on the patched tree, positive control holds patched & fails at base (prepatch reproduced), and the plausible naive fix is rejected by 3 probes. SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** The modeling boundary is correct: requirements pin the changed observable behavior (status consulted before fragment; error status routed through existing HTTPError special-casing) rather than a narrow slice. The status->outcome mappings (401->working, 503->ignored, other errors->broken with str(err)) are the pre-existing HTTPError handler that raise_for_status now feeds into; the requirements accurately describe reuse of that path. No unfaithful mandate, forbidden behavior, or invented behavior found.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** requirements.md localizes the change to linkcheck.py / check_uri / CheckExternalLinksBuilder (legitimate). All concrete details (404/500, 'NNN Error ... for url' message format, expected == linkcheck_anchors=False behavior) come from the PUBLIC problem_statement. The enumeration in Req 1.3/1.4 (unauthorized->working, service-unavailable->ignored) describes existing source-code status handling and covers MORE cases than the single-case (500) hidden test, so it mirrors behavior, not the test parametrization. No test name (test_raises_for_invalid_status), test path, testroot name (linkcheck-localserver), port 7777, fixture/handler classes, verbatim assertion string, or the gold identifier response.raise_for_status() appears. Behavioral requirement 'consult status before searching the fragment' is a valid restatement of intended behavior, not a transcription of the one-line gold edit.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
