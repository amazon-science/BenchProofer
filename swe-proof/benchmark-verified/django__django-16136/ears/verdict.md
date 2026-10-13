# P2 adversarial audit — django__django-16136

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
"""Req1.1 + 1.2 (POSITIVE CONTROL): async view -> http_method_not_allowed
returns an awaitable (coroutine) that resolves to HttpResponseNotAllowed.
This is the core fix: at base it returns a bare response (not awaitable)."""
import sys, asyncio, inspect
import django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True, ALLOWED_HOSTS=["*"])
    django.setup()
from django.views.generic.base import View
from django.http import HttpResponseNotAllowed


class AsyncView(View):
    async def get(self, request, *args, **kwargs):
        pass


class Req:
    method = "DELETE"
    path = "/x"


v = AsyncView()
v.request = Req()
ret = v.http_method_not_allowed(Req())
print("returned type:", type(ret), "iscoroutine:", inspect.iscoroutine(ret))
if not inspect.iscoroutine(ret):
    print("FAIL: async view did not return a coroutine")
    sys.exit(1)
resolved = asyncio.new_event_loop().run_until_complete(ret)
print("resolved type:", type(resolved))
if not isinstance(resolved, HttpResponseNotAllowed):
    print("FAIL: awaited result is not HttpResponseNotAllowed")
    sys.exit(1)
print("PASS")
sys.exit(0)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""Req1.3: sync view -> http_method_not_allowed returns HttpResponseNotAllowed
directly, NOT a coroutine. (Holds at base too — regression criterion.)"""
import sys, inspect
import django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True, ALLOWED_HOSTS=["*"])
    django.setup()
from django.views.generic.base import View
from django.http import HttpResponseNotAllowed


class SyncView(View):
    def get(self, request, *args, **kwargs):
        pass


class Req:
    method = "DELETE"
    path = "/x"


v = SyncView()
v.request = Req()
ret = v.http_method_not_allowed(Req())
print("returned type:", type(ret), "iscoroutine:", inspect.iscoroutine(ret))
if inspect.iscoroutine(ret):
    print("FAIL: sync view returned a coroutine")
    sys.exit(1)
if not isinstance(ret, HttpResponseNotAllowed):
    print("FAIL: not HttpResponseNotAllowed")
    sys.exit(1)
print("PASS")
sys.exit(0)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""Req2.1/2.2/2.3: response identity preserved. Both sync and async modes
produce HttpResponseNotAllowed with status 405 and identical permitted-methods
payload = view._allowed_methods() (upper-cased implemented methods)."""
import sys, asyncio
import django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True, ALLOWED_HOSTS=["*"])
    django.setup()
from django.views.generic.base import View
from django.http import HttpResponseNotAllowed


class SyncView(View):
    def get(self, request, *a, **k):
        pass

    def post(self, request, *a, **k):
        pass


class AsyncView(View):
    async def get(self, request, *a, **k):
        pass

    async def post(self, request, *a, **k):
        pass


class Req:
    method = "DELETE"
    path = "/x"


sv = SyncView(); sv.request = Req()
av = AsyncView(); av.request = Req()

sresp = sv.http_method_not_allowed(Req())
aresp = asyncio.new_event_loop().run_until_complete(av.http_method_not_allowed(Req()))

print("sync status:", sresp.status_code, "async status:", aresp.status_code)
if sresp.status_code != 405 or aresp.status_code != 405:
    print("FAIL: not 405")
    sys.exit(1)
if not (isinstance(sresp, HttpResponseNotAllowed) and isinstance(aresp, HttpResponseNotAllowed)):
    print("FAIL: wrong type")
    sys.exit(1)

# permitted methods payload -- HttpResponseNotAllowed sets Allow header
s_allow = sresp.headers.get("Allow")
a_allow = aresp.headers.get("Allow")
expected = ", ".join(sv._allowed_methods())
print("sync Allow:", s_allow, "| async Allow:", a_allow, "| expected:", expected)
if s_allow != a_allow:
    print("FAIL: allow payload differs between modes")
    sys.exit(1)
# _allowed_methods must be the upper-cased implemented method names
if set(sv._allowed_methods()) != {"GET", "POST", "HEAD"} and set(sv._allowed_methods()) != {"GET", "POST"}:
    # head auto-added only in setup(); here just check upper-case + includes GET,POST
    pass
if "GET" not in sv._allowed_methods() or "POST" not in sv._allowed_methods():
    print("FAIL: _allowed_methods missing implemented methods")
    sys.exit(1)
if any(m != m.upper() for m in sv._allowed_methods()):
    print("FAIL: methods not upper-cased")
    sys.exit(1)
print("PASS")
sys.exit(0)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""Req2.4: http_method_not_allowed SHALL still emit the "Method Not Allowed"
warning log record with status_code 405, unchanged (in async mode too)."""
import sys, asyncio, logging
import django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True, ALLOWED_HOSTS=["*"])
    django.setup()
from django.views.generic.base import View


class AsyncView(View):
    async def get(self, request, *a, **k):
        pass


class Req:
    method = "DELETE"
    path = "/somepath"


records = []


class Handler(logging.Handler):
    def emit(self, record):
        records.append(record)


logger = logging.getLogger("django.request")
h = Handler()
logger.addHandler(h)
logger.setLevel(logging.WARNING)

v = AsyncView(); v.request = Req()
ret = v.http_method_not_allowed(Req())
asyncio.new_event_loop().run_until_complete(ret)

logger.removeHandler(h)

matched = [r for r in records if "Method Not Allowed" in r.getMessage()
           and getattr(r, "status_code", None) == 405]
print("records captured:", len(records))
for r in records:
    print("  msg:", r.getMessage(), "status_code:", getattr(r, "status_code", None))
if not matched:
    print("FAIL: no Method Not Allowed warning with status_code 405")
    sys.exit(1)
print("PASS")
sys.exit(0)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""Req3: OPTIONS regression. async -> coroutine yielding HttpResponse;
sync -> HttpResponse directly (not coroutine); Allow header + Content-Length 0."""
import sys, asyncio, inspect
import django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True, ALLOWED_HOSTS=["*"])
    django.setup()
from django.views.generic.base import View
from django.http import HttpResponse


class SyncView(View):
    def get(self, request, *a, **k):
        pass


class AsyncView(View):
    async def get(self, request, *a, **k):
        pass


class Req:
    method = "OPTIONS"
    path = "/x"


sv = SyncView(); sv.request = Req()
av = AsyncView(); av.request = Req()

sret = sv.options(Req())
print("sync options iscoroutine:", inspect.iscoroutine(sret))
if inspect.iscoroutine(sret):
    print("FAIL: sync options returned coroutine")
    sys.exit(1)
if not isinstance(sret, HttpResponse):
    print("FAIL: sync options not HttpResponse")
    sys.exit(1)

aret = av.options(Req())
print("async options iscoroutine:", inspect.iscoroutine(aret))
if not inspect.iscoroutine(aret):
    print("FAIL: async options not coroutine")
    sys.exit(1)
aresp = asyncio.new_event_loop().run_until_complete(aret)
if not isinstance(aresp, HttpResponse):
    print("FAIL: awaited options not HttpResponse")
    sys.exit(1)

for resp, name in [(sret, "sync"), (aresp, "async")]:
    allow = resp.headers.get("Allow")
    clen = resp.headers.get("Content-Length")
    print(name, "Allow:", allow, "Content-Length:", clen)
    if allow is None:
        print("FAIL: missing Allow header", name)
        sys.exit(1)
    if clen != "0":
        print("FAIL: Content-Length not 0", name)
        sys.exit(1)
print("PASS")
sys.exit(0)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
"""Req4: view_is_async detection regression.
- base View and handler-less subclass -> False
- all sync -> False ; all async -> True
- mixed sync/async -> ImproperlyConfigured
- as_view() callable coroutine-marked iff async."""
import sys, asyncio
import django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True, ALLOWED_HOSTS=["*"])
    django.setup()
from django.views.generic.base import View
from django.core.exceptions import ImproperlyConfigured


class Empty(View):
    pass


class SyncV(View):
    def get(self, r, *a, **k):
        pass


class AsyncV(View):
    async def get(self, r, *a, **k):
        pass


class MixedV(View):
    def get(self, r, *a, **k):
        pass

    async def post(self, r, *a, **k):
        pass


ok = True
print("View.view_is_async:", View.view_is_async)
if View.view_is_async is not False:
    print("FAIL base View not False"); ok = False
if Empty.view_is_async is not False:
    print("FAIL Empty not False"); ok = False
if SyncV.view_is_async is not False:
    print("FAIL SyncV not False"); ok = False
if AsyncV.view_is_async is not True:
    print("FAIL AsyncV not True"); ok = False

try:
    MixedV.view_is_async
    print("FAIL: mixed did not raise"); ok = False
except ImproperlyConfigured as e:
    print("mixed raised ImproperlyConfigured:", str(e))
    if "sync" not in str(e).lower() or "async" not in str(e).lower():
        print("FAIL: message lacks sync/async wording"); ok = False

sync_cb = SyncV.as_view()
async_cb = AsyncV.as_view()
print("sync as_view coroutine-marked:", asyncio.iscoroutinefunction(sync_cb))
print("async as_view coroutine-marked:", asyncio.iscoroutinefunction(async_cb))
if asyncio.iscoroutinefunction(sync_cb):
    print("FAIL: sync as_view marked coroutine"); ok = False
if not asyncio.iscoroutinefunction(async_cb):
    print("FAIL: async as_view not marked coroutine"); ok = False

if not ok:
    sys.exit(1)
print("PASS")
sys.exit(0)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Req1.1 + 1.2 (POSITIVE CONTROL): async view -> http_method_not_allowed
returns an awaitable (coroutine) that resolves to HttpResponseNotAllowed.
This is the core fix: at base it returns a bare response (not awaitable)."""
import sys, asyncio, inspect
import django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True, ALLOWED_HOSTS=["*"])
    django.setup()
from django.views.generic.base import View
from django.http import HttpResponseNotAllowed


class AsyncView(View):
    async def get(self, request, *args, **kwargs):
        pass


class Req:
    method = "DELETE"
    path = "/x"


v = AsyncView()
v.request = Req()
ret = v.http_method_not_allowed(Req())
print("returned type:", type(ret), "iscoroutine:", inspect.iscoroutine(ret))
if not inspect.iscoroutine(ret):
    print("FAIL: async view did not return a coroutine")
    sys.exit(1)
resolved = asyncio.new_event_loop().run_until_complete(ret)
print("resolved type:", type(resolved))
if not isinstance(resolved, HttpResponseNotAllowed):
    print("FAIL: awaited result is not HttpResponseNotAllowed")
    sys.exit(1)
print("PASS")
sys.exit(0)
```

Prepatch bug re-encoded as an attack: `True`.

6 probes covering all 4 requirements, all HOLD on gold-patched tree.

Probes:
- probe_1 (Req1.1/1.2, POSITIVE CONTROL): async view http_method_not_allowed returns a coroutine that resolves to HttpResponseNotAllowed. HOLDS patched, FAILS at base (base returns bare HttpResponseNotAllowed, iscoroutine=False) -> discriminating power confirmed.
- probe_2 (Req1.3): sync view returns HttpResponseNotAllowed directly, NOT a coroutine.
- probe_3 (Req2.1/2.2/2.3): both modes -> 405 HttpResponseNotAllowed with identical Allow payload = upper-cased _allowed_methods().
- probe_4 (Req2.4): async mode still emits 'Method Not Allowed' warning log record with status_code 405.
- probe_5 (Req3): OPTIONS regression - async coroutine->HttpResponse, sync direct HttpResponse, Allow header + Content-Length 0 in both.
- probe_6 (Req4): view_is_async detection - base/empty/sync False, async True, mixed raises ImproperlyConfigured (msg mentions all sync/all async), as_view() coroutine-marked iff async.

Wrong-fix candidate 'always_coroutine' (weak.diff): naive fix that always wraps response in a coroutine regardless of view_is_async (a lazy reading of 'make it awaitable'). REJECTED by the suite: probe_2 fails (sync view returns coroutine) and probe_3 fails (sync response is a coroutine with no status_code). This demonstrates the suite discriminates the requirement's mode-dependent selection rule (Req1.3/1.4). Candidate applies cleanly at base.

All runs completed in the official image. Verdict SOUND: >=6 probes hold on patched, positive control fails at base, and a plausibly-wrong candidate is rejected.

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
"""Req1.1 + 1.2 (POSITIVE CONTROL): async view -> http_method_not_allowed
returns an awaitable (coroutine) that resolves to HttpResponseNotAllowed.
This is the core fix: at base it returns a bare response (not awaitable)."""
import sys, asyncio, inspect
import django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True, ALLOWED_HOSTS=["*"])
    django.setup()
from django.views.generic.base import View
from django.http import HttpResponseNotAllowed


class AsyncView(View):
    async def get(self, request, *args, **kwargs):
        pass


class Req:
    method = "DELETE"
    path = "/x"


v = AsyncView()
v.request = Req()
ret = v.http_method_not_allowed(Req())
print("returned type:", type(ret), "iscoroutine:", inspect.iscoroutine(ret))
if not inspect.iscoroutine(ret):
    print("FAIL: async view did not return a coroutine")
    sys.exit(1)
resolved = asyncio.new_event_loop().run_until_complete(ret)
print("resolved type:", type(resolved))
if not isinstance(resolved, HttpResponseNotAllowed):
    print("FAIL: awaited result is not HttpResponseNotAllowed")
    sys.exit(1)
print("PASS")
sys.exit(0)
```

Prepatch bug re-encoded as an attack: `True`.

6 probes covering all 4 requirements, all HOLD on gold-patched tree.

Probes:
- probe_1 (Req1.1/1.2, POSITIVE CONTROL): async view http_method_not_allowed returns a coroutine that resolves to HttpResponseNotAllowed. HOLDS patched, FAILS at base (base returns bare HttpResponseNotAllowed, iscoroutine=False) -> discriminating power confirmed.
- probe_2 (Req1.3): sync view returns HttpResponseNotAllowed directly, NOT a coroutine.
- probe_3 (Req2.1/2.2/2.3): both modes -> 405 HttpResponseNotAllowed with identical Allow payload = upper-cased _allowed_methods().
- probe_4 (Req2.4): async mode still emits 'Method Not Allowed' warning log record with status_code 405.
- probe_5 (Req3): OPTIONS regression - async coroutine->HttpResponse, sync direct HttpResponse, Allow header + Content-Length 0 in both.
- probe_6 (Req4): view_is_async detection - base/empty/sync False, async True, mixed raises ImproperlyConfigured (msg mentions all sync/all async), as_view() coroutine-marked iff async.

Wrong-fix candidate 'always_coroutine' (weak.diff): naive fix that always wraps response in a coroutine regardless of view_is_async (a lazy reading of 'make it awaitable'). REJECTED by the suite: probe_2 fails (sync view returns coroutine) and probe_3 fails (sync response is a coroutine with no status_code). This demonstrates the suite discriminates the requirement's mode-dependent selection rule (Req1.3/1.4). Candidate applies cleanly at base.

All runs completed in the official image. Verdict SOUND: >=6 probes hold on patched, positive control fails at base, and a plausibly-wrong candidate is rejected.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Probe on gold tree: SyncV.http_method_not_allowed -> HttpResponseNotAllowed (not coroutine, 405); AsyncV -> coroutine resolving to HttpResponseNotAllowed with Allow='POST, OPTIONS'; Base().view_is_async False; Mixed().view_is_async raises ImproperlyConfigured; SyncV.options -> HttpResponse Content-Length 0, AsyncV.options -> coroutine yielding HttpResponse; as_view() coroutine-marked for async only. Req 2.3's 'identical sync vs async' is soundly interpreted as same-view mode invariance (payload comes from mode-independent _allowed_methods()); the GET vs POST Allow difference in the probe is due to different view classes, not a divergence.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The requirements describe behavior in terms of real, public Django API names (View.http_method_not_allowed, options, view_is_async, _allowed_methods, as_view, HttpResponseNotAllowed, ImproperlyConfigured) — all legitimate localization of the change, not test artifacts. No test file paths (tests/async/tests.py), test/class names (ViewTests, test_http_method_not_allowed_responds_correctly, test_mixed_views_raise_error), parametrization ids, or quoted test code appear. The gold patch's fix-invented inner coroutine name `func` is not mentioned. Req 4's enumeration of view_is_async classification (all-sync→false / all-async→true / mixed→ImproperlyConfigured) mirrors pre-existing public Django behavior — that property is untouched by the gold edit — so it is behavioral regression framing, not reconstruction of the hidden tests. Req 1's 'return an awaitable (coroutine) vs bare response' is a direct translation of the fix's observable contract (analogous to options), which is the intended purpose, not leakage. The async-crash symptom and the options-sibling pattern are already in the public problem_statement/hints. Nothing derivable only from test_patch/patch beyond legitimate behavioral translation.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
