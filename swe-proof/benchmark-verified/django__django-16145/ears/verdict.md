# P2 adversarial audit — django__django-16145

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
# shared render helper embedded via exec in each probe
import io, os
os.environ.setdefault("DJANGO_SETTINGS_MODULE","django.conf.global_settings")
from django.conf import settings
if not settings.configured:
    settings.configure(SETTINGS_MODULE="dummy.settings", USE_TZ=True)
import django.core.management.commands.runserver as rs
from django.core.management.commands.runserver import Command

class _Stop(Exception): pass

def render(addr, port="8000", raw_ipv6=False, use_ipv6=False, protocol="http", skip_checks=True):
    c = Command()
    out = io.StringIO()
    c.stdout = type(c.stdout)(out)
    c.addr = addr; c.port = port; c._raw_ipv6 = raw_ipv6
    c.use_ipv6 = use_ipv6; c.protocol = protocol
    c.check = lambda *a, **k: None
    c.check_migrations = lambda *a, **k: None
    cap = {}
    def fake_run(addr_arg, port_arg, *a, **k):
        cap['bind_addr']=addr_arg; cap['bind_port']=port_arg
        raise _Stop()
    rs.run = fake_run
    c.get_handler = lambda *a, **k: None
    try:
        c.inner_run(skip_checks=skip_checks, use_threading=False, use_reloader=False, shutdown_message="")
    except _Stop:
        pass
    return out.getvalue(), cap

banner, cap = render("0", port="8000")
print("BANNER:", repr(banner))
ok = "Starting development server at http://0.0.0.0:8000/" in banner
print("expected substring present:", ok)
raise SystemExit(0 if ok else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
# shared render helper embedded via exec in each probe
import io, os
os.environ.setdefault("DJANGO_SETTINGS_MODULE","django.conf.global_settings")
from django.conf import settings
if not settings.configured:
    settings.configure(SETTINGS_MODULE="dummy.settings", USE_TZ=True)
import django.core.management.commands.runserver as rs
from django.core.management.commands.runserver import Command

class _Stop(Exception): pass

def render(addr, port="8000", raw_ipv6=False, use_ipv6=False, protocol="http", skip_checks=True):
    c = Command()
    out = io.StringIO()
    c.stdout = type(c.stdout)(out)
    c.addr = addr; c.port = port; c._raw_ipv6 = raw_ipv6
    c.use_ipv6 = use_ipv6; c.protocol = protocol
    c.check = lambda *a, **k: None
    c.check_migrations = lambda *a, **k: None
    cap = {}
    def fake_run(addr_arg, port_arg, *a, **k):
        cap['bind_addr']=addr_arg; cap['bind_port']=port_arg
        raise _Stop()
    rs.run = fake_run
    c.get_handler = lambda *a, **k: None
    try:
        c.inner_run(skip_checks=skip_checks, use_threading=False, use_reloader=False, shutdown_message="")
    except _Stop:
        pass
    return out.getvalue(), cap

banner, cap = render("0", port="8000")
print("BIND:", cap)
ok = cap.get('bind_addr') == "0"
print("bind addr unchanged (== '0'):", ok)
raise SystemExit(0 if ok else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
# shared render helper embedded via exec in each probe
import io, os
os.environ.setdefault("DJANGO_SETTINGS_MODULE","django.conf.global_settings")
from django.conf import settings
if not settings.configured:
    settings.configure(SETTINGS_MODULE="dummy.settings", USE_TZ=True)
import django.core.management.commands.runserver as rs
from django.core.management.commands.runserver import Command

class _Stop(Exception): pass

def render(addr, port="8000", raw_ipv6=False, use_ipv6=False, protocol="http", skip_checks=True):
    c = Command()
    out = io.StringIO()
    c.stdout = type(c.stdout)(out)
    c.addr = addr; c.port = port; c._raw_ipv6 = raw_ipv6
    c.use_ipv6 = use_ipv6; c.protocol = protocol
    c.check = lambda *a, **k: None
    c.check_migrations = lambda *a, **k: None
    cap = {}
    def fake_run(addr_arg, port_arg, *a, **k):
        cap['bind_addr']=addr_arg; cap['bind_port']=port_arg
        raise _Stop()
    rs.run = fake_run
    c.get_handler = lambda *a, **k: None
    try:
        c.inner_run(skip_checks=skip_checks, use_threading=False, use_reloader=False, shutdown_message="")
    except _Stop:
        pass
    return out.getvalue(), cap

banner, cap = render("0", port="9999")
print("BANNER:", repr(banner))
ok = "http://0.0.0.0:9999/" in banner
print("port preserved with 0.0.0.0:", ok)
raise SystemExit(0 if ok else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
# shared render helper embedded via exec in each probe
import io, os
os.environ.setdefault("DJANGO_SETTINGS_MODULE","django.conf.global_settings")
from django.conf import settings
if not settings.configured:
    settings.configure(SETTINGS_MODULE="dummy.settings", USE_TZ=True)
import django.core.management.commands.runserver as rs
from django.core.management.commands.runserver import Command

class _Stop(Exception): pass

def render(addr, port="8000", raw_ipv6=False, use_ipv6=False, protocol="http", skip_checks=True):
    c = Command()
    out = io.StringIO()
    c.stdout = type(c.stdout)(out)
    c.addr = addr; c.port = port; c._raw_ipv6 = raw_ipv6
    c.use_ipv6 = use_ipv6; c.protocol = protocol
    c.check = lambda *a, **k: None
    c.check_migrations = lambda *a, **k: None
    cap = {}
    def fake_run(addr_arg, port_arg, *a, **k):
        cap['bind_addr']=addr_arg; cap['bind_port']=port_arg
        raise _Stop()
    rs.run = fake_run
    c.get_handler = lambda *a, **k: None
    try:
        c.inner_run(skip_checks=skip_checks, use_threading=False, use_reloader=False, shutdown_message="")
    except _Stop:
        pass
    return out.getvalue(), cap

# a normal raw ipv6 literal
b1, _ = render("::1", raw_ipv6=True, use_ipv6=True)
ok1 = "http://[::1]:8000/" in b1
print("ipv6 bracketed:", ok1, repr(b1.split(chr(10))[2] if len(b1.split(chr(10)))>2 else b1))
# precedence: addr '0' but marked raw ipv6 -> must be [0], NOT 0.0.0.0
b2, _ = render("0", raw_ipv6=True, use_ipv6=True)
ok2 = ("http://[0]:8000/" in b2) and ("0.0.0.0" not in b2)
print("ipv6 precedence over shorthand-0:", ok2, repr(b2))
raise SystemExit(0 if (ok1 and ok2) else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
# shared render helper embedded via exec in each probe
import io, os
os.environ.setdefault("DJANGO_SETTINGS_MODULE","django.conf.global_settings")
from django.conf import settings
if not settings.configured:
    settings.configure(SETTINGS_MODULE="dummy.settings", USE_TZ=True)
import django.core.management.commands.runserver as rs
from django.core.management.commands.runserver import Command

class _Stop(Exception): pass

def render(addr, port="8000", raw_ipv6=False, use_ipv6=False, protocol="http", skip_checks=True):
    c = Command()
    out = io.StringIO()
    c.stdout = type(c.stdout)(out)
    c.addr = addr; c.port = port; c._raw_ipv6 = raw_ipv6
    c.use_ipv6 = use_ipv6; c.protocol = protocol
    c.check = lambda *a, **k: None
    c.check_migrations = lambda *a, **k: None
    cap = {}
    def fake_run(addr_arg, port_arg, *a, **k):
        cap['bind_addr']=addr_arg; cap['bind_port']=port_arg
        raise _Stop()
    rs.run = fake_run
    c.get_handler = lambda *a, **k: None
    try:
        c.inner_run(skip_checks=skip_checks, use_threading=False, use_reloader=False, shutdown_message="")
    except _Stop:
        pass
    return out.getvalue(), cap

cases = {
  "127.0.0.1": "http://127.0.0.1:8000/",
  "1.2.3.4":   "http://1.2.3.4:8000/",
  "0.0.0.0":   "http://0.0.0.0:8000/",   # explicit dotted quad verbatim
  "example.com": "http://example.com:8000/",
  "localhost":   "http://localhost:8000/",
  "10":         "http://10:8000/",        # not exactly '0' -> verbatim
}
allok=True
for host, exp in cases.items():
    b,_=render(host)
    present = exp in b
    print(host, "->", present)
    if not present: allok=False
raise SystemExit(0 if allok else 1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
# shared render helper embedded via exec in each probe
import io, os
os.environ.setdefault("DJANGO_SETTINGS_MODULE","django.conf.global_settings")
from django.conf import settings
if not settings.configured:
    settings.configure(SETTINGS_MODULE="dummy.settings", USE_TZ=True)
import django.core.management.commands.runserver as rs
from django.core.management.commands.runserver import Command

class _Stop(Exception): pass

def render(addr, port="8000", raw_ipv6=False, use_ipv6=False, protocol="http", skip_checks=True):
    c = Command()
    out = io.StringIO()
    c.stdout = type(c.stdout)(out)
    c.addr = addr; c.port = port; c._raw_ipv6 = raw_ipv6
    c.use_ipv6 = use_ipv6; c.protocol = protocol
    c.check = lambda *a, **k: None
    c.check_migrations = lambda *a, **k: None
    cap = {}
    def fake_run(addr_arg, port_arg, *a, **k):
        cap['bind_addr']=addr_arg; cap['bind_port']=port_arg
        raise _Stop()
    rs.run = fake_run
    c.get_handler = lambda *a, **k: None
    try:
        c.inner_run(skip_checks=skip_checks, use_threading=False, use_reloader=False, shutdown_message="")
    except _Stop:
        pass
    return out.getvalue(), cap
import django

b,_ = render("0", port="8000", protocol="https", skip_checks=True)
print("BANNER:", repr(b))
checks = [
  ("https protocol", "https://0.0.0.0:8000/" in b),
  ("django version", django.get_version() in b),
  ("settings module", "'dummy.settings'" in b),
  ("no 'Performing system checks' when skip_checks", "Performing system checks" not in b),
]
allok=all(v for _,v in checks)
for n,v in checks: print(n, v)
raise SystemExit(0 if allok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
# shared render helper embedded via exec in each probe
import io, os
os.environ.setdefault("DJANGO_SETTINGS_MODULE","django.conf.global_settings")
from django.conf import settings
if not settings.configured:
    settings.configure(SETTINGS_MODULE="dummy.settings", USE_TZ=True)
import django.core.management.commands.runserver as rs
from django.core.management.commands.runserver import Command

class _Stop(Exception): pass

def render(addr, port="8000", raw_ipv6=False, use_ipv6=False, protocol="http", skip_checks=True):
    c = Command()
    out = io.StringIO()
    c.stdout = type(c.stdout)(out)
    c.addr = addr; c.port = port; c._raw_ipv6 = raw_ipv6
    c.use_ipv6 = use_ipv6; c.protocol = protocol
    c.check = lambda *a, **k: None
    c.check_migrations = lambda *a, **k: None
    cap = {}
    def fake_run(addr_arg, port_arg, *a, **k):
        cap['bind_addr']=addr_arg; cap['bind_port']=port_arg
        raise _Stop()
    rs.run = fake_run
    c.get_handler = lambda *a, **k: None
    try:
        c.inner_run(skip_checks=skip_checks, use_threading=False, use_reloader=False, shutdown_message="")
    except _Stop:
        pass
    return out.getvalue(), cap

banner, cap = render("0", port="8000")
print("BANNER:", repr(banner))
ok = "Starting development server at http://0.0.0.0:8000/" in banner
print("expected substring present:", ok)
raise SystemExit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

6 standalone probes exercise the banner-render path of Command.inner_run via an in-process render() harness (constructs Command, stubs check/check_migrations/run/get_handler, captures stdout banner and the bind (addr,port) passed to run()).

### RESULTS (patched / base):
- probe_1 (Req1.2, POSITIVE CONTROL): banner 'Starting development server at http://0.0.0.0:8000/'. HOLDS patched, FAILS base (base shows http://0:8000/). Discriminates.
- probe_2 (Req1.3 presentation-only): bind addr passed to run() stays '0'. HOLDS patched.
- probe_3 (Req1.2 port fidelity): host '0' with port 9999 -> http://0.0.0.0:9999/. HOLDS patched, FAILS base.
- probe_4 (Req2.1/2.2): raw IPv6 '::1' -> [::1]; and precedence: addr '0' WITH _raw_ipv6=True -> '[0]' not '0.0.0.0'. HOLDS patched (also HOLDS base, unchanged behavior).
- probe_5 (Req2.3/2.4/2.5): 127.0.0.1, 1.2.3.4, explicit 0.0.0.0, example.com, localhost, '10' all verbatim. HOLDS patched & base (regression leg).
- probe_6 (Req3.1/3.4): https protocol, django version, settings module all substituted; 'Performing system checks' absent under skip_checks. HOLDS patched.

### CANDIDATE WRONG-FIX PATCHES (both apply at base_commit, both REJECTED by suite -> suite discriminates wrong implementations):
- weak_precedence.diff: single-line ternary that checks self.addr=='0' BEFORE the _raw_ipv6 branch. probe_1 HOLDS but probe_4 REJECTS (addr '0' + raw ipv6 renders 0.0.0.0 instead of [0], violating Req2.2 precedence).
- weak_bind.diff: rewrites self.addr='0.0.0.0' before the banner (mutating the real bind address). probe_2 REJECTS (bind_addr becomes '0.0.0.0', violating Req1.3 presentation-only).

All 6 probes hold on patched; positive control fails at base and holds patched; >=1 candidate exercised and >=2 REJECTED. Requirements are faithful and not too weak. Verdict SOUND.

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
# shared render helper embedded via exec in each probe
import io, os
os.environ.setdefault("DJANGO_SETTINGS_MODULE","django.conf.global_settings")
from django.conf import settings
if not settings.configured:
    settings.configure(SETTINGS_MODULE="dummy.settings", USE_TZ=True)
import django.core.management.commands.runserver as rs
from django.core.management.commands.runserver import Command

class _Stop(Exception): pass

def render(addr, port="8000", raw_ipv6=False, use_ipv6=False, protocol="http", skip_checks=True):
    c = Command()
    out = io.StringIO()
    c.stdout = type(c.stdout)(out)
    c.addr = addr; c.port = port; c._raw_ipv6 = raw_ipv6
    c.use_ipv6 = use_ipv6; c.protocol = protocol
    c.check = lambda *a, **k: None
    c.check_migrations = lambda *a, **k: None
    cap = {}
    def fake_run(addr_arg, port_arg, *a, **k):
        cap['bind_addr']=addr_arg; cap['bind_port']=port_arg
        raise _Stop()
    rs.run = fake_run
    c.get_handler = lambda *a, **k: None
    try:
        c.inner_run(skip_checks=skip_checks, use_threading=False, use_reloader=False, shutdown_message="")
    except _Stop:
        pass
    return out.getvalue(), cap

banner, cap = render("0", port="8000")
print("BANNER:", repr(banner))
ok = "Starting development server at http://0.0.0.0:8000/" in banner
print("expected substring present:", ok)
raise SystemExit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

6 standalone probes exercise the banner-render path of Command.inner_run via an in-process render() harness (constructs Command, stubs check/check_migrations/run/get_handler, captures stdout banner and the bind (addr,port) passed to run()).

### RESULTS (patched / base):
- probe_1 (Req1.2, POSITIVE CONTROL): banner 'Starting development server at http://0.0.0.0:8000/'. HOLDS patched, FAILS base (base shows http://0:8000/). Discriminates.
- probe_2 (Req1.3 presentation-only): bind addr passed to run() stays '0'. HOLDS patched.
- probe_3 (Req1.2 port fidelity): host '0' with port 9999 -> http://0.0.0.0:9999/. HOLDS patched, FAILS base.
- probe_4 (Req2.1/2.2): raw IPv6 '::1' -> [::1]; and precedence: addr '0' WITH _raw_ipv6=True -> '[0]' not '0.0.0.0'. HOLDS patched (also HOLDS base, unchanged behavior).
- probe_5 (Req2.3/2.4/2.5): 127.0.0.1, 1.2.3.4, explicit 0.0.0.0, example.com, localhost, '10' all verbatim. HOLDS patched & base (regression leg).
- probe_6 (Req3.1/3.4): https protocol, django version, settings module all substituted; 'Performing system checks' absent under skip_checks. HOLDS patched.

### CANDIDATE WRONG-FIX PATCHES (both apply at base_commit, both REJECTED by suite -> suite discriminates wrong implementations):
- weak_precedence.diff: single-line ternary that checks self.addr=='0' BEFORE the _raw_ipv6 branch. probe_1 HOLDS but probe_4 REJECTS (addr '0' + raw ipv6 renders 0.0.0.0 instead of [0], violating Req2.2 precedence).
- weak_bind.diff: rewrites self.addr='0.0.0.0' before the banner (mutating the real bind address). probe_2 REJECTS (bind_addr becomes '0.0.0.0', violating Req1.3 presentation-only).

All 6 probes hold on patched; positive control fails at base and holds patched; >=1 candidate exercised and >=2 REJECTED. Requirements are faithful and not too weak. Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** The gold patch replaces the inline `"[%s]" % self.addr if self._raw_ipv6 else self.addr` with a 3-branch computation: if self._raw_ipv6 -> f"[{self.addr}]"; elif self.addr == "0" -> "0.0.0.0"; else -> self.addr. The requirements pin exactly this changed observable behavior (banner host component in inner_run), correctly capture the branch ORDERING (Req 2.2: IPv6-bracket takes precedence over shorthand-0, matching the elif), and correctly scope it as presentation-only (Req 1.3, confirmed by the patch touching only the display `addr` local, not the bind address). Modeling boundary is the full changed behavior, not a narrow slice. Probe: ALL PROBES PASS on gold-patched tree.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The core F2P behavior (runserver 0:8000 should print http://0.0.0.0:8000/) is stated verbatim in the PUBLIC problem_statement, so Requirement 1 leaks nothing hidden. Identifiers named (Command.inner_run, _raw_ipv6, addr) are existing source symbols and legitimate localization, not fix-invented. The doc uses generic <port>/'same port the user supplied' rather than the test's literal 8000, so no gold/test constant is transmitted. No test names, file paths, test-ids, or quoted test/gold code appear. Requirements 2/3 enumerate preservation cases (IPv6 bracketing, IPv4 literal, hostname, custom defaults, skip_checks, testserver) that loosely echo the PASS_TO_PASS set, but each is grounded in publicly readable source behavior and reads as a don't-regress behavioral spec rather than a reconstruction of hidden tests. Borderline only in that the preservation enumeration is somewhat suite-shaped, but nothing is derivable exclusively from the hidden material.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
