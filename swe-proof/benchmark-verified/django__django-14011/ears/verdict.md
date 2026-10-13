# P2 adversarial audit — django__django-14011

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 requirement probes hold on the patched tree; 2/2 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 7 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 7 | `probe_1_ctor.py`, `probe_2_retain.py`, `probe_3_adopt.py`, `probe_4_close.py`, `probe_5_close_order.py`, `probe_6_sqlite_skip.py`, `probe_7_poscontrol.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 2 alternative candidate patches, claimed to satisfy every cited requirement, and ran the same suite against them. The suite rejected all 2: a probe encoding a cited requirement fails under each of those, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_7_poscontrol.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (7):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1_ctor.py` → holds on the patched tree (good)

```python
"""R1.1 / R1.4: ThreadedWSGIServer.__init__ accepts an OPTIONAL keyword-only
`connections_override` (default None/absent) IN ADDITION to the existing
WSGIServer construction args (which flow through via *args/**kwargs, incl.
ipv6/allow_reuse_address). Exit 0 iff the signature admits the new kwarg as
keyword-only with a default AND still forwards the pre-existing args."""
import inspect
import django
from django.conf import settings
settings.configure(DEBUG=True,
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    ALLOWED_HOSTS=["*"], INSTALLED_APPS=[])
django.setup()
from django.core.servers.basehttp import ThreadedWSGIServer, WSGIServer

sig = inspect.signature(ThreadedWSGIServer.__init__)
params = sig.parameters
print("ThreadedWSGIServer.__init__", sig)

if "connections_override" not in params:
    print("FAIL: no connections_override parameter")
    raise SystemExit(1)
p = params["connections_override"]
if p.kind is not inspect.Parameter.KEYWORD_ONLY:
    print(f"FAIL: connections_override is not keyword-only ({p.kind})")
    raise SystemExit(1)
if p.default is inspect.Parameter.empty or p.default is not None:
    print(f"FAIL: connections_override default is not None ({p.default!r})")
    raise SystemExit(1)

# Existing WSGIServer args must still be reachable: __init__ must accept
# arbitrary *args and **kwargs so ipv6/allow_reuse_address/etc still pass.
kinds = {n: pp.kind for n, pp in params.items()}
has_var_pos = any(k is inspect.Parameter.VAR_POSITIONAL for k in kinds.values())
has_var_kw = any(k is inspect.Parameter.VAR_KEYWORD for k in kinds.values())
print("has *args", has_var_pos, "has **kwargs", has_var_kw)
# WSGIServer still exposes ipv6/allow_reuse_address so behaviour preserved
wsgi_params = inspect.signature(WSGIServer.__init__).parameters
print("WSGIServer params", list(wsgi_params))
if not (has_var_pos and has_var_kw):
    print("FAIL: does not forward existing positional/keyword args")
    raise SystemExit(1)
if "ipv6" not in wsgi_params or "allow_reuse_address" not in wsgi_params:
    print("FAIL: WSGIServer lost ipv6/allow_reuse_address args")
    raise SystemExit(1)
print("PASS: optional keyword-only connections_override + existing args preserved")
raise SystemExit(0)
```

Attack 2 — `probe_2_retain.py` → holds on the patched tree (good)

```python
"""R1.2 / R1.3 / R2.3: the server RETAINS a supplied connections collection on
the instance (available to per-request code), and when constructed WITHOUT one
the stored value is falsy (absent) so no request thread's connections are
overridden. Exit 0 iff both hold."""
import django
from django.conf import settings
settings.configure(DEBUG=True,
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    ALLOWED_HOSTS=["*"], INSTALLED_APPS=[])
django.setup()
from django.core.servers.basehttp import ThreadedWSGIServer, WSGIRequestHandler

ADDR = ("127.0.0.1", 0)

# (a) constructed WITHOUT a collection -> constructs fine; stored value falsy.
s0 = ThreadedWSGIServer(ADDR, WSGIRequestHandler, bind_and_activate=False)
attr = getattr(s0, "connections_override", "MISSING")
print("no-override attr =", repr(attr))
if attr == "MISSING":
    print("FAIL: server does not store the override attribute at all")
    raise SystemExit(1)
if attr:
    print("FAIL: default override is truthy; would override request connections")
    raise SystemExit(1)

# (b) constructed WITH a collection -> retained, same object, accessible.
sentinel = {"default": object()}
s1 = ThreadedWSGIServer(ADDR, WSGIRequestHandler,
                        connections_override=sentinel, bind_and_activate=False)
got = getattr(s1, "connections_override", None)
print("with-override attr is sentinel:", got is sentinel)
if got is not sentinel:
    print("FAIL: supplied collection not retained on the instance")
    raise SystemExit(1)
print("PASS: collection retained; absent-collection default is falsy")
raise SystemExit(0)
```

Attack 3 — `probe_3_adopt.py` → holds on the patched tree (good)

```python
"""R2.1 / R2.2 / R2.3: when servicing a request in its own thread, the server
installs each supplied connection into django.db.connections under its alias
(lookups by alias in that thread return the supplied object); aliases NOT
supplied are left untouched (a normal working connection); when no set was
supplied, the request thread does NOT get a foreign/overridden connection.

NOTE: django.db.connections is THREAD-LOCAL, so we observe from inside the
request thread. Exit 0 iff supplied alias adopts the sentinel, an unsupplied
alias remains a real DB wrapper (not the sentinel), and the no-override case
yields a real DB wrapper (never the sentinel)."""
import threading
import django
from django.conf import settings
settings.configure(DEBUG=True,
    DATABASES={
        "default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"},
        "other": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"},
    },
    ALLOWED_HOSTS=["*"], INSTALLED_APPS=[])
django.setup()
from django.core.servers.basehttp import ThreadedWSGIServer, WSGIRequestHandler
from django.db import connections
from django.db.backends.base.base import BaseDatabaseWrapper

ADDR = ("127.0.0.1", 0)

class Sentinel:
    """Stand-in connection object; not a real DB wrapper."""
    alias = "default"

obs = {}

import socketserver
orig = socketserver.ThreadingMixIn.process_request_thread
def observe(self, request, client_address):
    # inside the request thread's own thread-local connections registry
    obs["default"] = connections["default"]
    obs["other"] = connections["other"]
socketserver.ThreadingMixIn.process_request_thread = observe
try:
    sentinel = Sentinel()
    server = ThreadedWSGIServer(ADDR, WSGIRequestHandler,
                                connections_override={"default": sentinel},
                                bind_and_activate=False)
    t = threading.Thread(target=server.process_request_thread, args=(None, ADDR))
    t.start(); t.join(timeout=10)
    print("supplied 'default' is sentinel:", obs.get("default") is sentinel)
    print("unsupplied 'other' is real DB wrapper:",
          isinstance(obs.get("other"), BaseDatabaseWrapper))
    if obs.get("default") is not sentinel:
        print("FAIL: supplied 'default' connection not adopted in request thread")
        raise SystemExit(1)
    if obs.get("other") is sentinel or not isinstance(obs.get("other"), BaseDatabaseWrapper):
        print("FAIL: unsupplied 'other' alias was disturbed")
        raise SystemExit(1)

    # No-override case: thread must not receive a foreign/overridden object.
    obs.clear()
    server2 = ThreadedWSGIServer(ADDR, WSGIRequestHandler, bind_and_activate=False)
    t2 = threading.Thread(target=server2.process_request_thread, args=(None, ADDR))
    t2.start(); t2.join(timeout=10)
    print("no-override 'default' is real DB wrapper:",
          isinstance(obs.get("default"), BaseDatabaseWrapper))
    if obs.get("default") is sentinel or not isinstance(obs.get("default"), BaseDatabaseWrapper):
        print("FAIL: no-override case replaced connection with a foreign object")
        raise SystemExit(1)
finally:
    socketserver.ThreadingMixIn.process_request_thread = orig

print("PASS: adopts supplied aliases, leaves others untouched, no-override no-op")
raise SystemExit(0)
```

Attack 4 — `probe_4_close.py` → holds on the patched tree (good)

```python
"""R3.1 / R3.2 / R3.3 / R3.5: per-request cleanup (close_request) closes every
DB connection in the thread's registry via a SINGLE overridable step, tears
down a real open connection's underlying link, AND still invokes the base
server's normal close_request (socket teardown). Exit 0 iff all hold.

- overridable step: a dedicated method exists that close_request delegates to,
  so a subclass can substitute it and observe the call.
- actual close: an open on-disk sqlite connection reports .connection is None
  after the step.
- base cleanup still runs: overriding the base close_request records it ran.
"""
import os, tempfile
import django
from django.conf import settings
tmp = tempfile.mkdtemp()
settings.configure(DEBUG=True,
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3",
                            "NAME": os.path.join(tmp, "t.sqlite3")}},
    ALLOWED_HOSTS=["*"], INSTALLED_APPS=[])
django.setup()
from django.core.servers.basehttp import ThreadedWSGIServer, WSGIRequestHandler
from django.db import connections

ADDR = ("127.0.0.1", 0)
server = ThreadedWSGIServer(ADDR, WSGIRequestHandler, bind_and_activate=False)

class FakeRequest:
    """A stand-in for the socket request; base close_request calls .close()."""
    def __init__(self):
        self.closed = False
    def close(self):
        self.closed = True
REQ = FakeRequest()

# R3.2: a single overridable close step exists and close_request delegates to
# it. Find the delegate method by subclassing and recording.
calls = {"close_step": 0, "base_close": 0}

# The base server's close_request (via super()) must still run. Find the
# class in the MRO ABOVE ThreadedWSGIServer that actually defines
# close_request (socketserver.TCPServer) and spy on it.
import socketserver
base_owner = None
for klass in type(server).__mro__[1:]:
    if "close_request" in klass.__dict__:
        base_owner = klass
        break
print("base close_request owner:", base_owner.__name__)
base_cr = base_owner.close_request
def spy_base(self, request):
    calls["base_close"] += 1
    return base_cr(self, request)
base_owner.close_request = spy_base

# Detect the overridable step. The gold impl names it _close_connections, but
# to be implementation-agnostic we require SOME instance method (other than
# close_request itself) that close_request calls and whose override changes
# the closing action. We test overridability by monkeypatching each candidate.
try:
    # open a real connection in THIS thread's registry
    c = connections["default"]
    c.ensure_connection()
    assert c.connection is not None, "precondition: connection should be open"

    # Find candidate close step: subclass overriding close_request must call
    # something. We verify the documented contract: there is a hook method
    # such that overriding it is observed AND normal control flow (super
    # close_request) still runs.
    hook_name = None
    for name in dir(type(server)):
        if name == "close_request":
            continue
        attr = getattr(type(server), name, None)
        if callable(attr) and ("close" in name.lower() and "conn" in name.lower()):
            hook_name = name
            break
    print("discovered close-step hook:", hook_name)
    if hook_name is None:
        print("FAIL: no dedicated overridable connection-closing step found")
        raise SystemExit(1)

    orig_hook = getattr(type(server), hook_name)
    def spy_hook(self):
        calls["close_step"] += 1
        return orig_hook(self)
    setattr(type(server), hook_name, spy_hook)
    try:
        server.close_request(REQ)  # base close_request will call REQ.close()
    finally:
        setattr(type(server), hook_name, orig_hook)

    print("close-step invoked:", calls["close_step"])
    print("base close_request invoked:", calls["base_close"])
    print("connection after close:", c.connection)

    if calls["close_step"] != 1:
        print("FAIL: overridable close step not invoked exactly once")
        raise SystemExit(1)
    if calls["base_close"] < 1:
        print("FAIL: base server close_request (socket teardown) not invoked")
        raise SystemExit(1)
    if c.connection is not None:
        print("FAIL: open connection's underlying link not torn down")
        raise SystemExit(1)
finally:
    base_owner.close_request = base_cr

print("PASS: single overridable step closes connections + base cleanup still runs")
raise SystemExit(0)
```

Attack 5 — `probe_5_close_order.py` → holds on the patched tree (good)

```python
"""R3.1 / R3.5 (ordering) + R3.4: connections are closed BEFORE the base
server's normal per-request cleanup (socket teardown) completes; and if a
connection's close() is a no-op (in-memory sqlite), the step still runs without
error and still performs the normal cleanup.

We record the temporal order of (close-connections step) vs (base
close_request), and verify no exception with an in-memory DB. Exit 0 iff the
close step runs before base cleanup and the in-memory path is error-free."""
import django
from django.conf import settings
settings.configure(DEBUG=True,
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    ALLOWED_HOSTS=["*"], INSTALLED_APPS=[])
django.setup()
from django.core.servers.basehttp import ThreadedWSGIServer, WSGIRequestHandler
from django.db import connections

ADDR = ("127.0.0.1", 0)
server = ThreadedWSGIServer(ADDR, WSGIRequestHandler, bind_and_activate=False)

class FakeRequest:
    def close(self):
        pass
REQ = FakeRequest()

order = []

import socketserver
base_owner = None
for klass in type(server).__mro__[1:]:
    if "close_request" in klass.__dict__:
        base_owner = klass
        break
base_cr = base_owner.close_request
def spy_base(self, request):
    order.append("base_close")
    return base_cr(self, request)
base_owner.close_request = spy_base

# find hook
hook_name = None
for name in dir(type(server)):
    if name != "close_request" and callable(getattr(type(server), name, None)) \
       and "close" in name.lower() and "conn" in name.lower():
        hook_name = name
        break
if hook_name is None:
    print("FAIL: no connection-closing step")
    base_owner.close_request = base_cr
    raise SystemExit(1)
orig_hook = getattr(type(server), hook_name)
def spy_hook(self):
    order.append("close_conn")
    return orig_hook(self)
setattr(type(server), hook_name, spy_hook)

# in-memory connection: close() is a no-op; must not raise.
c = connections["default"]
c.ensure_connection()
try:
    server.close_request(REQ)  # must not raise even though close() is no-op
    print("order:", order)
    print("in-memory close_request completed without error")
finally:
    setattr(type(server), hook_name, orig_hook)
    base_owner.close_request = base_cr

if "close_conn" not in order or "base_close" not in order:
    print("FAIL: missing one of close_conn/base_close")
    raise SystemExit(1)
if order.index("close_conn") > order.index("base_close"):
    print("FAIL: connections closed AFTER base socket cleanup, not before")
    raise SystemExit(1)
print("PASS: connections closed before base cleanup; in-memory no-op safe")
raise SystemExit(0)
```

Attack 6 — `probe_6_sqlite_skip.py` → holds on the patched tree (good)

```python
"""R4.1 / R4.2: the sqlite3 backend's in-memory skip set declares the threaded
server's per-request connection-closing test under the SAME "close() is a no-op
for an in-memory database" explanation as the pre-existing connection-closing
skip entry, and every previously declared skip is RETAINED (additions only).

Exit 0 iff the new entry (LiveServerTestCloseConnectionTest.test_closes_connections)
is grouped under a key mentioning close()/no-op/in-memory ALONGSIDE the
pre-existing LiveServerThreadTest.test_closes_connections entry, and the
pre-existing entry is still present."""
import django
from django.conf import settings
settings.configure(DEBUG=True,
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    ALLOWED_HOSTS=["*"], INSTALLED_APPS=[])
django.setup()
from django.db import connection

skips = connection.features.django_test_skips
# flatten
all_vals = set()
group_for = {}
for key, vals in skips.items():
    for v in vals:
        all_vals.add(v)
        group_for[v] = key

PRE = "servers.test_liveserverthread.LiveServerThreadTest.test_closes_connections"
NEW = "servers.tests.LiveServerTestCloseConnectionTest.test_closes_connections"

print("has pre-existing entry:", PRE in all_vals)
print("has new entry:", NEW in all_vals)
if PRE not in all_vals:
    print("FAIL: pre-existing connection-closing skip removed")
    raise SystemExit(1)
if NEW not in all_vals:
    print("FAIL: new per-request connection-closing skip not declared")
    raise SystemExit(1)

kpre = group_for[PRE]
knew = group_for[NEW]
print("group for pre:", repr(kpre))
print("group for new:", repr(knew))
if kpre != knew:
    print("FAIL: new entry not grouped under the same explanation as pre-existing")
    raise SystemExit(1)
low = kpre.lower()
if not (("no-op" in low or "no op" in low) and "in-memory" in low):
    print("FAIL: grouping key is not the close()-is-a-no-op / in-memory explanation")
    raise SystemExit(1)
print("PASS: new skip grouped with pre-existing under no-op/in-memory explanation")
raise SystemExit(0)
```

Attack 7 — `probe_7_poscontrol.py` → holds on the patched tree (good)

```python
"""POSITIVE CONTROL — core fixed behavior (R3.1/R3.3): calling the threaded
server's close_request MUST close the DB connections held in the thread's
registry (an open on-disk sqlite connection reports .connection is None
afterwards). At base (unpatched) close_request is the inherited socketserver
method that does NOT touch DB connections, so the connection stays open and
this probe VIOLATES. On the patched tree it HOLDS. This is the discriminating
leg. No introspection of method names — pure observable behavior."""
import os, tempfile
import django
from django.conf import settings
tmp = tempfile.mkdtemp()
settings.configure(DEBUG=True,
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3",
                            "NAME": os.path.join(tmp, "t.sqlite3")}},
    ALLOWED_HOSTS=["*"], INSTALLED_APPS=[])
django.setup()
from django.core.servers.basehttp import ThreadedWSGIServer, WSGIRequestHandler
from django.db import connections

ADDR = ("127.0.0.1", 0)
server = ThreadedWSGIServer(ADDR, WSGIRequestHandler, bind_and_activate=False)

class FakeRequest:
    """Base close_request calls .close(); provide it so socket teardown is a
    clean no-op on BOTH trees (isolating the DB-connection effect)."""
    def close(self):
        pass
REQ = FakeRequest()

c = connections["default"]
c.ensure_connection()
print("before close_request, connection open:", c.connection is not None)
if c.connection is None:
    print("FAIL(precondition): could not open connection")
    raise SystemExit(1)

# base close_request just closes the (fake) socket; no effect on DB conns.
# Only the patched close_request closes DB conns.
server.close_request(REQ)

print("after close_request, connection object:", c.connection)
if c.connection is not None:
    print("VIOLATED: DB connection still open after close_request (base behavior)")
    raise SystemExit(1)
print("HOLDS: DB connection closed by close_request (patched behavior)")
raise SystemExit(0)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_7_poscontrol.py`

```python
"""POSITIVE CONTROL — core fixed behavior (R3.1/R3.3): calling the threaded
server's close_request MUST close the DB connections held in the thread's
registry (an open on-disk sqlite connection reports .connection is None
afterwards). At base (unpatched) close_request is the inherited socketserver
method that does NOT touch DB connections, so the connection stays open and
this probe VIOLATES. On the patched tree it HOLDS. This is the discriminating
leg. No introspection of method names — pure observable behavior."""
import os, tempfile
import django
from django.conf import settings
tmp = tempfile.mkdtemp()
settings.configure(DEBUG=True,
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3",
                            "NAME": os.path.join(tmp, "t.sqlite3")}},
    ALLOWED_HOSTS=["*"], INSTALLED_APPS=[])
django.setup()
from django.core.servers.basehttp import ThreadedWSGIServer, WSGIRequestHandler
from django.db import connections

ADDR = ("127.0.0.1", 0)
server = ThreadedWSGIServer(ADDR, WSGIRequestHandler, bind_and_activate=False)

class FakeRequest:
    """Base close_request calls .close(); provide it so socket teardown is a
    clean no-op on BOTH trees (isolating the DB-connection effect)."""
    def close(self):
        pass
REQ = FakeRequest()

c = connections["default"]
c.ensure_connection()
print("before close_request, connection open:", c.connection is not None)
if c.connection is None:
    print("FAIL(precondition): could not open connection")
    raise SystemExit(1)

# base close_request just closes the (fake) socket; no effect on DB conns.
# Only the patched close_request closes DB conns.
server.close_request(REQ)

print("after close_request, connection object:", c.connection)
if c.connection is not None:
    print("VIOLATED: DB connection still open after close_request (base behavior)")
    raise SystemExit(1)
print("HOLDS: DB connection closed by close_request (patched behavior)")
raise SystemExit(0)
```

Prepatch bug re-encoded as an attack: `True`.

6 requirement probes cover R1-R5: probe_1_ctor (R1.1/R1.4 optional keyword-only connections_override kwarg + preserved *args/**kwargs and WSGIServer ipv6/allow_reuse_address); probe_2_retain (R1.2/R1.3/R2.3 collection retained on instance, falsy default => no override); probe_3_adopt (R2.1/R2.2/R2.3, thread-local: supplied alias adopts the exact object inside the request thread, unsupplied alias stays a real DB wrapper, no-override thread untouched); probe_4_close (R3.1/R3.2/R3.3/R3.5: a dedicated overridable close-connections step is invoked exactly once, base server close_request still runs, and a real open on-disk sqlite connection is torn down to .connection is None); probe_5_close_order (R3.1/R3.4/R3.5: close step runs BEFORE base socket cleanup, in-memory sqlite close() no-op path error-free); probe_6_sqlite_skip (R4.1/R4.2: new servers.tests.LiveServerTestCloseConnectionTest.test_closes_connections grouped under the SAME 'close() is a no-op...in-memory database' key as the pre-existing LiveServerThreadTest entry, pre-existing retained).

ALL 6 HOLD on the gold-patched tree and VIOLATE at base_commit. Positive control probe_7 (close_request closes an open DB connection) HOLDS patched, VIOLATED at base (prepatch reproduced). Two wrong-fix candidates constructed and REJECTED by the suite: weak_A adopts connections but never closes them per request (fails probes 4,5,7); weak_B closes inline in process_request_thread's finally rather than via the overridable _close_connections step in close_request (fails probes 4,5,7 — matching that the hidden test mocks _close_connections and drives close via close_request). Both are requirements-nonconforming, so no TOO-WEAK finding.

Notes on probe engineering: django.db.connections is thread-local (probe_3 observes inside the request thread and checks object identity/DB-wrapper type, not cross-thread identity); base close_request is owned by socketserver.TCPServer (found dynamically via MRO) and calls request.close(), so probes pass a FakeRequest with a close() method to isolate the DB-connection effect on both trees.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 requirement probes hold on the patched tree; 2/2 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 7 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 7 | `probe_1_ctor.py`, `probe_2_retain.py`, `probe_3_adopt.py`, `probe_4_close.py`, `probe_5_close_order.py`, `probe_6_sqlite_skip.py`, `probe_7_poscontrol.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 2 alternative candidate patches, claimed to satisfy every cited requirement, and ran the same suite against them. The suite rejected all 2: a probe encoding a cited requirement fails under each of those, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_7_poscontrol.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (7):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts, and on this backend both roles put it through the same derivation: every block below is a requirement probe run on the gold-patched tree, and the `machine verdict:` line each role publishes above reports BOTH that its probes hold there and how many candidate patches the probe suite rejected — so the two roles re-ran ONE probe suite and each recorded its own outcome for every probe in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `probe_1_ctor.py` → holds on the patched tree (good)

Attack 2 — `probe_2_retain.py` → holds on the patched tree (good)

Attack 3 — `probe_3_adopt.py` → holds on the patched tree (good)

Attack 4 — `probe_4_close.py` → holds on the patched tree (good)

Attack 5 — `probe_5_close_order.py` → holds on the patched tree (good)

Attack 6 — `probe_6_sqlite_skip.py` → holds on the patched tree (good)

Attack 7 — `probe_7_poscontrol.py` → holds on the patched tree (good)

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_7_poscontrol.py`

```python
"""POSITIVE CONTROL — core fixed behavior (R3.1/R3.3): calling the threaded
server's close_request MUST close the DB connections held in the thread's
registry (an open on-disk sqlite connection reports .connection is None
afterwards). At base (unpatched) close_request is the inherited socketserver
method that does NOT touch DB connections, so the connection stays open and
this probe VIOLATES. On the patched tree it HOLDS. This is the discriminating
leg. No introspection of method names — pure observable behavior."""
import os, tempfile
import django
from django.conf import settings
tmp = tempfile.mkdtemp()
settings.configure(DEBUG=True,
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3",
                            "NAME": os.path.join(tmp, "t.sqlite3")}},
    ALLOWED_HOSTS=["*"], INSTALLED_APPS=[])
django.setup()
from django.core.servers.basehttp import ThreadedWSGIServer, WSGIRequestHandler
from django.db import connections

ADDR = ("127.0.0.1", 0)
server = ThreadedWSGIServer(ADDR, WSGIRequestHandler, bind_and_activate=False)

class FakeRequest:
    """Base close_request calls .close(); provide it so socket teardown is a
    clean no-op on BOTH trees (isolating the DB-connection effect)."""
    def close(self):
        pass
REQ = FakeRequest()

c = connections["default"]
c.ensure_connection()
print("before close_request, connection open:", c.connection is not None)
if c.connection is None:
    print("FAIL(precondition): could not open connection")
    raise SystemExit(1)

# base close_request just closes the (fake) socket; no effect on DB conns.
# Only the patched close_request closes DB conns.
server.close_request(REQ)

print("after close_request, connection object:", c.connection)
if c.connection is not None:
    print("VIOLATED: DB connection still open after close_request (base behavior)")
    raise SystemExit(1)
print("HOLDS: DB connection closed by close_request (patched behavior)")
raise SystemExit(0)
```

Prepatch bug re-encoded as an attack: `True`.

6 requirement probes cover R1-R5: probe_1_ctor (R1.1/R1.4 optional keyword-only connections_override kwarg + preserved *args/**kwargs and WSGIServer ipv6/allow_reuse_address); probe_2_retain (R1.2/R1.3/R2.3 collection retained on instance, falsy default => no override); probe_3_adopt (R2.1/R2.2/R2.3, thread-local: supplied alias adopts the exact object inside the request thread, unsupplied alias stays a real DB wrapper, no-override thread untouched); probe_4_close (R3.1/R3.2/R3.3/R3.5: a dedicated overridable close-connections step is invoked exactly once, base server close_request still runs, and a real open on-disk sqlite connection is torn down to .connection is None); probe_5_close_order (R3.1/R3.4/R3.5: close step runs BEFORE base socket cleanup, in-memory sqlite close() no-op path error-free); probe_6_sqlite_skip (R4.1/R4.2: new servers.tests.LiveServerTestCloseConnectionTest.test_closes_connections grouped under the SAME 'close() is a no-op...in-memory database' key as the pre-existing LiveServerThreadTest entry, pre-existing retained).

ALL 6 HOLD on the gold-patched tree and VIOLATE at base_commit. Positive control probe_7 (close_request closes an open DB connection) HOLDS patched, VIOLATED at base (prepatch reproduced). Two wrong-fix candidates constructed and REJECTED by the suite: weak_A adopts connections but never closes them per request (fails probes 4,5,7); weak_B closes inline in process_request_thread's finally rather than via the overridable _close_connections step in close_request (fails probes 4,5,7 — matching that the hidden test mocks _close_connections and drives close via close_request). Both are requirements-nonconforming, so no TOO-WEAK finding.

Notes on probe engineering: django.db.connections is thread-local (probe_3 observes inside the request thread and checks object identity/DB-wrapper type, not cross-thread identity); base close_request is owned by socketserver.TCPServer (found dynamically via MRO) and calls request.close(), so probes pass a FakeRequest with a close() method to isolate the DB-connection effect on both trees.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Probed in the instance image on the gold-patched tree (exit 0, all asserts held) and at base_commit (all four methods absent on ThreadedWSGIServer). Requirement modeling boundary correctly targets the three server-side behaviors (construct-with-connections, per-request adopt, per-request close) plus the sqlite3 skip-set addition — matching the full diff with no invented, mandated-but-absent, or forbidden-but-present behavior.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** requirements.md describes the gold change in behavioral/structural terms and legitimately localizes it to django/core/servers/basehttp.py (ThreadedWSGIServer) and django/db/backends/sqlite3/features.py — all module/class names (ThreadedWSGIServer, WSGIServer, LiveServerThread, LiveServerTestCase) are already public in the problem_statement. No hidden-test content is transmitted: no test file paths, no test function/class names (e.g. LiveServerTestCloseConnectionTest, test_closes_connections), no verbatim test id in the sqlite skip set, no parametrization ids, no quoted test/gold code, no fix-invented identifiers (connections_override, _close_connections, process_request_thread) named verbatim. Closest call is Req 3.2, which reflects the gold's _close_connections testability seam that the hidden test subclass overrides, but it is phrased as a generic 'overridable step for testability' without naming the method, the threading.Event mechanism, or the test — it describes gold structure, not the test. Req 4 describes the sqlite3 django_test_skips addition abstractly ('per-request connection-closing check') and only paraphrases the pre-existing 'close() is a no-op for an in-memory database' dict-key string; it does not quote the new test id. Translating tested behavior into EARS requirements is the document's purpose, not a leak.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
