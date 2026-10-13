# P2 adversarial audit — django__django-13810

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 requirement probes hold on the patched tree; 1/2 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 7 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 7 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py`, `probe_7.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 2 alternative candidate patches, claimed to satisfy every cited requirement, and ran the same suite against them. The suite rejected 1 of the 2: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. The other 1 was not rejected by the suite. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

Counterexample / evidence:

```
Base bug: the mode-coerced handler was committed to `handler` before the middleware was instantiated, so a MiddlewareNotUsed skip left `handler` (and its mode) poisoned for the next middleware. Concretely, MIDDLEWARE=[OuterAsyncMW(async-only), InnerSyncSkip(sync-only, raises MiddlewareNotUsed)] under is_async=True: at base OuterAsyncMW is instantiated with a sync-coerced handler and the async chain raises `RuntimeError: You cannot use AsyncToSync in the same thread as an async event loop` / returns a non-awaitable; under the fix it receives an async handler and the chain resolves to 200 OK.
```

**Attacks re-run (7):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
# Positive control: Req 1.1/1.3/2.1 — a skipped (inner) middleware must not
# poison the handler handed to the surviving outer middleware. In async mode
# the outer middleware must receive an ASYNC (coroutine) handler.
import asyncio, django
from django.conf import settings
settings.configure(DEBUG=True, ALLOWED_HOSTS=['*'],
    MIDDLEWARE=['__main__.OuterAsyncMW', '__main__.InnerSyncSkip'],
    LOGGING_CONFIG=None, DATABASES={}, INSTALLED_APPS=[])
django.setup()
from django.core.exceptions import MiddlewareNotUsed

RECORD = {}

class OuterAsyncMW:
    sync_capable = False
    async_capable = True
    def __init__(self, get_response):
        self.get_response = get_response
        RECORD['outer_gets_async'] = asyncio.iscoroutinefunction(get_response)
    async def __call__(self, request):
        return await self.get_response(request)

class InnerSyncSkip:
    sync_capable = True
    async_capable = False
    def __init__(self, get_response):
        raise MiddlewareNotUsed('skip me')
    def __call__(self, request):
        return self.get_response(request)

from django.core.handlers.base import BaseHandler
h = BaseHandler()
h.load_middleware(is_async=True)
print('outer_gets_async =', RECORD.get('outer_gets_async'))
# Under the fix the outer surviving middleware must receive an async handler.
assert RECORD.get('outer_gets_async') is True, 'outer middleware received a poisoned (sync-coerced) handler'
print('OK: outer middleware received an async handler')
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
# Req 1.2/2.1/2.3: skip in the MIDDLE of two async middleware; the async chain
# must still resolve to 200 OK. Under the base bug the mid skip poisons the
# handler handed to the surviving outer async middleware.
import asyncio, django
from django.conf import settings
settings.configure(DEBUG=False, ALLOWED_HOSTS=['*'], ROOT_URLCONF='__main__',
    MIDDLEWARE=['__main__.OuterA','__main__.MidSkip','__main__.InnerA'],
    LOGGING_CONFIG=None, DATABASES={}, INSTALLED_APPS=[])
django.setup()
from django.core.exceptions import MiddlewareNotUsed
from django.http import HttpResponse
from django.urls import path
def view(r): return HttpResponse(b'OK')
urlpatterns=[path('x', view)]
class _Async:
    sync_capable=False; async_capable=True
    def __init__(self,g): self.g=g
    async def __call__(self,r): return await self.g(r)
class OuterA(_Async): pass
class InnerA(_Async): pass
class MidSkip:
    sync_capable=True; async_capable=False
    def __init__(self,g): raise MiddlewareNotUsed()
    def __call__(self,r): return self.g(r)
from django.core.handlers.base import BaseHandler
from django.test import RequestFactory
h=BaseHandler(); h.load_middleware(is_async=True)
req=RequestFactory().get('/x')
res=h._middleware_chain(req)
awaitable = asyncio.iscoroutine(res) or hasattr(res,'__await__')
print('awaitable:', awaitable)
assert awaitable, 'async chain did not return an awaitable (poisoned to sync)'
resp=asyncio.new_event_loop().run_until_complete(res)
print('status',resp.status_code,'body',resp.content)
assert resp.status_code==200 and resp.content==b'OK'
print('OK: async chain with mid skip resolved to 200 OK')
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
# Req 2.2: async chain assembled with a skipped inner middleware yields an
# awaitable response resolving to 200 and the expected body.
import asyncio, django
from django.conf import settings
settings.configure(DEBUG=False, ALLOWED_HOSTS=['*'], ROOT_URLCONF='__main__',
    MIDDLEWARE=['__main__.OuterAsyncMW','__main__.InnerSyncSkip'],
    LOGGING_CONFIG=None, DATABASES={}, INSTALLED_APPS=[])
django.setup()
from django.core.exceptions import MiddlewareNotUsed
from django.http import HttpResponse
from django.urls import path
def view(r): return HttpResponse(b'OK')
urlpatterns=[path('x', view)]
class OuterAsyncMW:
    sync_capable=False; async_capable=True
    def __init__(self,g): self.g=g
    async def __call__(self,r): return await self.g(r)
class InnerSyncSkip:
    sync_capable=True; async_capable=False
    def __init__(self,g): raise MiddlewareNotUsed()
    def __call__(self,r): return self.g(r)
from django.core.handlers.base import BaseHandler
from django.test import RequestFactory
h=BaseHandler(); h.load_middleware(is_async=True)
req=RequestFactory().get('/x')
res=h._middleware_chain(req)
awaitable = asyncio.iscoroutine(res) or hasattr(res,'__await__')
print('awaitable:', awaitable)
assert awaitable, 'chain not awaitable'
resp=asyncio.new_event_loop().run_until_complete(res)
print('status',resp.status_code,'body',resp.content)
assert resp.status_code==200 and resp.content==b'OK'
print('OK: async chain yielded awaitable 200 OK')
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
# Req 4.1/4.3: with DEBUG on and an async chain, adapting the skipped sync
# middleware to async emits an 'Asynchronous ... adapted.' record, followed by
# the 'MiddlewareNotUsed: ...' record naming the dotted path. Order preserved.
import logging, django
from django.conf import settings
settings.configure(DEBUG=True, ALLOWED_HOSTS=['*'],
    MIDDLEWARE=['__main__.OuterA','__main__.SkipMW'],
    LOGGING_CONFIG=None, DATABASES={}, INSTALLED_APPS=[])
django.setup()
from django.core.exceptions import MiddlewareNotUsed
class OuterA:
    sync_capable=False; async_capable=True
    def __init__(self,g): self.g=g
    async def __call__(self,r): return await self.g(r)
class SkipMW:
    sync_capable=True; async_capable=False
    def __init__(self,g): raise MiddlewareNotUsed()
    def __call__(self,r): return self.g(r)
recs=[]
class H(logging.Handler):
    def emit(self,r): recs.append(r.getMessage())
lg=logging.getLogger('django.request'); lg.setLevel(logging.DEBUG); lg.addHandler(H())
from django.core.handlers.base import BaseHandler
BaseHandler().load_middleware(is_async=True)
print('records:', recs)
assert any('adapted.' in m and 'SkipMW' in m for m in recs), 'missing adaptation record for skipped mw'
skip_msgs=[m for m in recs if m.startswith('MiddlewareNotUsed')]
assert skip_msgs and "'__main__.SkipMW'" in skip_msgs[0], 'missing/incorrect MiddlewareNotUsed record'
adapt_i=next(i for i,m in enumerate(recs) if 'adapted.' in m and 'SkipMW' in m)
skip_i=next(i for i,m in enumerate(recs) if m.startswith('MiddlewareNotUsed'))
assert adapt_i < skip_i, 'adaptation record should precede MiddlewareNotUsed record'
print('OK: adaptation then MiddlewareNotUsed, correct order & dotted path')
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
# Req 4.2: with DEBUG disabled, a MiddlewareNotUsed skip emits NO debug record.
import logging, django
from django.conf import settings
settings.configure(DEBUG=False, ALLOWED_HOSTS=['*'],
    MIDDLEWARE=['__main__.OuterA','__main__.SkipMW'],
    LOGGING_CONFIG=None, DATABASES={}, INSTALLED_APPS=[])
django.setup()
from django.core.exceptions import MiddlewareNotUsed
class OuterA:
    sync_capable=False; async_capable=True
    def __init__(self,g): self.g=g
    async def __call__(self,r): return await self.g(r)
class SkipMW:
    sync_capable=True; async_capable=False
    def __init__(self,g): raise MiddlewareNotUsed()
    def __call__(self,r): return self.g(r)
recs=[]
class Hd(logging.Handler):
    def emit(self,r): recs.append(r.getMessage())
lg=logging.getLogger('django.request'); lg.setLevel(logging.DEBUG); lg.addHandler(Hd())
from django.core.handlers.base import BaseHandler
BaseHandler().load_middleware(is_async=True)
print('records:', recs)
assert not any(m.startswith('MiddlewareNotUsed') for m in recs), 'must not log MiddlewareNotUsed when DEBUG off'
print('OK: no MiddlewareNotUsed record with DEBUG off')
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
# Req 3.1/3.2: a middleware that installs successfully IS instantiated with the
# adapted handler and the running handler carries the successful installation
# forward. Verified by a successful two-async-mw chain (no skip) resolving 200.
import asyncio, django
from django.conf import settings
settings.configure(DEBUG=False, ALLOWED_HOSTS=['*'], ROOT_URLCONF='__main__',
    MIDDLEWARE=['__main__.A1','__main__.A2'],
    LOGGING_CONFIG=None, DATABASES={}, INSTALLED_APPS=[])
django.setup()
from django.http import HttpResponse
from django.urls import path
def view(r): return HttpResponse(b'OK')
urlpatterns=[path('x', view)]
class _Async:
    sync_capable=False; async_capable=True
    def __init__(self,g): self.g=g
    async def __call__(self,r): return await self.g(r)
class A1(_Async): pass
class A2(_Async): pass
from django.core.handlers.base import BaseHandler
from django.test import RequestFactory
h=BaseHandler(); h.load_middleware(is_async=True)
res=h._middleware_chain(RequestFactory().get('/x'))
assert asyncio.iscoroutine(res) or hasattr(res,'__await__'), 'normal async chain not awaitable'
resp=asyncio.new_event_loop().run_until_complete(res)
print('status',resp.status_code,'body',resp.content)
assert resp.status_code==200 and resp.content==b'OK'
print('OK: normal (no-skip) async chain composes and resolves 200')
```

Attack 7 — `probe_7.py` → holds on the patched tree (good)

```python
# Req 3.3: factory returning None -> ImproperlyConfigured; a middleware that is
# neither sync nor async capable -> RuntimeError. (Regression preservation.)
import django
from django.conf import settings
settings.configure(DEBUG=False, ALLOWED_HOSTS=['*'],
    MIDDLEWARE=['__main__.NoneMW'],
    LOGGING_CONFIG=None, DATABASES={}, INSTALLED_APPS=[])
django.setup()
from django.core.exceptions import ImproperlyConfigured
class NoneMW:
    sync_capable=True; async_capable=True
    def __new__(cls,g): return None
    def __call__(self,r): return self.g(r)
from django.core.handlers.base import BaseHandler
ok=False
try:
    BaseHandler().load_middleware(is_async=False)
except ImproperlyConfigured as e:
    ok=True; print('got ImproperlyConfigured:', e)
assert ok, 'factory returning None must raise ImproperlyConfigured'

# neither capable
settings.MIDDLEWARE=['__main__.Neither']
class Neither:
    sync_capable=False; async_capable=False
    def __init__(self,g): self.g=g
    def __call__(self,r): return self.g(r)
import __main__ as M; M.Neither=Neither
ok2=False
try:
    BaseHandler().load_middleware(is_async=False)
except RuntimeError as e:
    ok2=True; print('got RuntimeError:', e)
assert ok2, 'neither-capable middleware must raise RuntimeError'
print('OK: ImproperlyConfigured and RuntimeError preserved')
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
# Positive control: Req 1.1/1.3/2.1 — a skipped (inner) middleware must not
# poison the handler handed to the surviving outer middleware. In async mode
# the outer middleware must receive an ASYNC (coroutine) handler.
import asyncio, django
from django.conf import settings
settings.configure(DEBUG=True, ALLOWED_HOSTS=['*'],
    MIDDLEWARE=['__main__.OuterAsyncMW', '__main__.InnerSyncSkip'],
    LOGGING_CONFIG=None, DATABASES={}, INSTALLED_APPS=[])
django.setup()
from django.core.exceptions import MiddlewareNotUsed

RECORD = {}

class OuterAsyncMW:
    sync_capable = False
    async_capable = True
    def __init__(self, get_response):
        self.get_response = get_response
        RECORD['outer_gets_async'] = asyncio.iscoroutinefunction(get_response)
    async def __call__(self, request):
        return await self.get_response(request)

class InnerSyncSkip:
    sync_capable = True
    async_capable = False
    def __init__(self, get_response):
        raise MiddlewareNotUsed('skip me')
    def __call__(self, request):
        return self.get_response(request)

from django.core.handlers.base import BaseHandler
h = BaseHandler()
h.load_middleware(is_async=True)
print('outer_gets_async =', RECORD.get('outer_gets_async'))
# Under the fix the outer surviving middleware must receive an async handler.
assert RECORD.get('outer_gets_async') is True, 'outer middleware received a poisoned (sync-coerced) handler'
print('OK: outer middleware received an async handler')
```

Prepatch bug re-encoded as an attack: `True`.

Requirements coverage — probe_1 (positive control, Req 1.1/1.3/2.1): outer async survivor receives an async handler; HOLDS patched, FAILS at base. probe_2 (Req 1.2/2.1/2.3): skip in the MIDDLE of two async mw, async chain still resolves 200; HOLDS patched, VIOLATED base. probe_3 (Req 2.2): async chain w/ skipped inner mw yields awaitable 200/body; HOLDS patched, VIOLATED base. probe_4 (Req 4.1/4.3): DEBUG on emits 'Asynchronous ... adapted.' then "MiddlewareNotUsed: '...'" in that order with dotted path; HOLDS. probe_5 (Req 4.2): DEBUG off emits NO MiddlewareNotUsed record; HOLDS. probe_6 (Req 3.1/3.2): normal no-skip async chain composes to 200; HOLDS. probe_7 (Req 3.3): factory returning None -> ImproperlyConfigured, neither-capable mw -> RuntimeError; HOLDS.

All 7 probes HOLD on the gold-patched tree; positive control (probe_1) FAILS at base (prepatch reproduced) — discriminating power confirmed.

Candidate patches: (1) weak_noop — cosmetic-only diff that leaves the pre-commit poisoning bug intact; REJECTED by probes 1/2/3 (VIOLATED), proving the suite discriminates wrong implementations. (2) weak_noelse_refactor — the gold change minus the `else: handler = adapted_handler` line; PASSES every probe. This is NOT a too-weak finding: on the success path `handler` is unconditionally reassigned by `handler = convert_exception_to_response(mw_instance)` immediately after, and on the skip path `continue` bypasses any commit, so weak_noelse is behaviorally equivalent to gold (the `else` in gold is redundant/defensive). It correctly resolves the FAIL_TO_PASS test. Runner may re-check it against the official harness; expected to resolve.

Early false-start note: an initial `handler_is_async = middleware_is_async` naive-except patch also happened to FIX the bug (re-adaptation from the pre-skip mode), so it was not a valid wrong candidate; replaced with weak_noop which genuinely leaves the bug.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 requirement probes hold on the patched tree; 1/2 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 7 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 7 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py`, `probe_7.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 2 alternative candidate patches, claimed to satisfy every cited requirement, and ran the same suite against them. The suite rejected 1 of the 2: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. The other 1 was not rejected by the suite. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

Counterexample / evidence:

```
Base bug: the mode-coerced handler was committed to `handler` before the middleware was instantiated, so a MiddlewareNotUsed skip left `handler` (and its mode) poisoned for the next middleware. Concretely, MIDDLEWARE=[OuterAsyncMW(async-only), InnerSyncSkip(sync-only, raises MiddlewareNotUsed)] under is_async=True: at base OuterAsyncMW is instantiated with a sync-coerced handler and the async chain raises `RuntimeError: You cannot use AsyncToSync in the same thread as an async event loop` / returns a non-awaitable; under the fix it receives an async handler and the chain resolves to 200 OK.
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
# Positive control: Req 1.1/1.3/2.1 — a skipped (inner) middleware must not
# poison the handler handed to the surviving outer middleware. In async mode
# the outer middleware must receive an ASYNC (coroutine) handler.
import asyncio, django
from django.conf import settings
settings.configure(DEBUG=True, ALLOWED_HOSTS=['*'],
    MIDDLEWARE=['__main__.OuterAsyncMW', '__main__.InnerSyncSkip'],
    LOGGING_CONFIG=None, DATABASES={}, INSTALLED_APPS=[])
django.setup()
from django.core.exceptions import MiddlewareNotUsed

RECORD = {}

class OuterAsyncMW:
    sync_capable = False
    async_capable = True
    def __init__(self, get_response):
        self.get_response = get_response
        RECORD['outer_gets_async'] = asyncio.iscoroutinefunction(get_response)
    async def __call__(self, request):
        return await self.get_response(request)

class InnerSyncSkip:
    sync_capable = True
    async_capable = False
    def __init__(self, get_response):
        raise MiddlewareNotUsed('skip me')
    def __call__(self, request):
        return self.get_response(request)

from django.core.handlers.base import BaseHandler
h = BaseHandler()
h.load_middleware(is_async=True)
print('outer_gets_async =', RECORD.get('outer_gets_async'))
# Under the fix the outer surviving middleware must receive an async handler.
assert RECORD.get('outer_gets_async') is True, 'outer middleware received a poisoned (sync-coerced) handler'
print('OK: outer middleware received an async handler')
```

Prepatch bug re-encoded as an attack: `True`.

Requirements coverage — probe_1 (positive control, Req 1.1/1.3/2.1): outer async survivor receives an async handler; HOLDS patched, FAILS at base. probe_2 (Req 1.2/2.1/2.3): skip in the MIDDLE of two async mw, async chain still resolves 200; HOLDS patched, VIOLATED base. probe_3 (Req 2.2): async chain w/ skipped inner mw yields awaitable 200/body; HOLDS patched, VIOLATED base. probe_4 (Req 4.1/4.3): DEBUG on emits 'Asynchronous ... adapted.' then "MiddlewareNotUsed: '...'" in that order with dotted path; HOLDS. probe_5 (Req 4.2): DEBUG off emits NO MiddlewareNotUsed record; HOLDS. probe_6 (Req 3.1/3.2): normal no-skip async chain composes to 200; HOLDS. probe_7 (Req 3.3): factory returning None -> ImproperlyConfigured, neither-capable mw -> RuntimeError; HOLDS.

All 7 probes HOLD on the gold-patched tree; positive control (probe_1) FAILS at base (prepatch reproduced) — discriminating power confirmed.

Candidate patches: (1) weak_noop — cosmetic-only diff that leaves the pre-commit poisoning bug intact; REJECTED by probes 1/2/3 (VIOLATED), proving the suite discriminates wrong implementations. (2) weak_noelse_refactor — the gold change minus the `else: handler = adapted_handler` line; PASSES every probe. This is NOT a too-weak finding: on the success path `handler` is unconditionally reassigned by `handler = convert_exception_to_response(mw_instance)` immediately after, and on the skip path `continue` bypasses any commit, so weak_noelse is behaviorally equivalent to gold (the `else` in gold is redundant/defensive). It correctly resolves the FAIL_TO_PASS test. Runner may re-check it against the official harness; expected to resolve.

Early false-start note: an initial `handler_is_async = middleware_is_async` naive-except patch also happened to FIX the bug (re-adaptation from the pre-skip mode), so it was not a valid wrong candidate; replaced with weak_noop which genuinely leaves the bug.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Ran the probe on the instance image both directions. PATCHED (gold): ASGI GET returns status 200, body b'OK', with django.request DEBUG records ['Asynchronous middleware __main__.NotUsedMiddleware adapted.', "MiddlewareNotUsed: '__main__.NotUsedMiddleware'"] — i.e. the adaptation record precedes the MiddlewareNotUsed record. BASE (unpatched): raises TypeError: object HttpResponse can't be used in 'await' expression — exactly the issue's symptom. Requirement-by-requirement: R1 ↔ the else:handler=adapted_handler change (skipped mw does not alter running handler/mode) — matches. R2 ↔ async chain still resolves to 200/expected body after a skipped non-async mw — probe confirms. R3 ↔ successful install still instantiated with adapted handler and propagates it; ImproperlyConfigured (factory None) and RuntimeError (neither sync nor async) paths untouched by patch — faithful. R4 ↔ MiddlewareNotUsed debug logging under DEBUG (and suppression when off), adaptation logging, and their relative ordering preserved — probe's record order confirms 4.3, and the F2P test test_async_and_sync_middleware_chain_async_call asserts exactly this ordering. The requirements pin the changed observable behavior biconditionally (skip must have no lasting effect while installed-mw adaptation still composes), not a narrow single-branch slice.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** requirements.md describes the fix behaviorally and correctly localized to BaseHandler.load_middleware / adapt_method_mode / the MiddlewareNotUsed skip path — all of which is public via the problem_statement (which quotes the exact file, the handler-overwrite defect, and the 'HttpResponse can't be awaited' symptom). No hidden-test content leaks: the test function name (test_async_and_sync_middleware_chain_async_call), class (MiddlewareNotUsedTests), file path (tests/middleware_exceptions/tests.py), and the specific middleware classes used (SyncAndAsyncMiddleware, MyMiddleware) do NOT appear. The gold-invented identifier `adapted_handler` does NOT appear. The verbatim log strings from the test ('Asynchronous middleware ... adapted.', "MiddlewareNotUsed: '...'") are NOT reproduced — Req 4.1/4.3 describe logging generically (django.request logger, dotted path). Req 2.2's 'status code 200 and the expected response body' is generic; the body literal b'OK' is not quoted. Req 4.3's adaptation-then-MiddlewareNotUsed ordering matches the test's records[0]/records[1] assertion but is derivable from the code's causal flow (adapt -> instantiate -> skip) rather than transmitting the test. Naming the modules/functions is legitimate localization. This is behavioral translation, not test reconstruction.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
