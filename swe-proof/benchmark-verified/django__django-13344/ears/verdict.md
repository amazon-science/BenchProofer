# P2 adversarial audit — django__django-13344

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
"""Positive control -- Req1.1: async handler => instance recognized as async.
Covers all 5 affected middleware classes. Must HOLD patched, FAIL at base."""
import asyncio, sys

def setup():
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            DEBUG=True,
            CACHES={"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}},
            SESSION_ENGINE="django.contrib.sessions.backends.signed_cookies",
        )
    import django
    django.setup()

setup()
from django.contrib.sessions.middleware import SessionMiddleware
from django.middleware.cache import UpdateCacheMiddleware, FetchFromCacheMiddleware, CacheMiddleware
from django.middleware.security import SecurityMiddleware

async def aget(request):
    return None

classes = [SessionMiddleware, UpdateCacheMiddleware, FetchFromCacheMiddleware, CacheMiddleware, SecurityMiddleware]
ok = True
for cls in classes:
    inst = cls(aget)
    is_async = asyncio.iscoroutinefunction(inst)
    print(f"{cls.__name__}: iscoroutinefunction(instance)={is_async}")
    if not is_async:
        ok = False
sys.exit(0 if ok else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""Req1.2: sync handler => instance NOT recognized as async, for all 5 classes."""
import asyncio, sys

from django.conf import settings
if not settings.configured:
    settings.configure(
        DEBUG=True,
        CACHES={"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}},
        SESSION_ENGINE="django.contrib.sessions.backends.signed_cookies",
    )
import django
django.setup()

from django.contrib.sessions.middleware import SessionMiddleware
from django.middleware.cache import UpdateCacheMiddleware, FetchFromCacheMiddleware, CacheMiddleware
from django.middleware.security import SecurityMiddleware

def sget(request):
    return None

classes = [SessionMiddleware, UpdateCacheMiddleware, FetchFromCacheMiddleware, CacheMiddleware, SecurityMiddleware]
ok = True
for cls in classes:
    inst = cls(sget)
    is_async = asyncio.iscoroutinefunction(inst)
    print(f"{cls.__name__}: iscoroutinefunction(instance)={is_async}")
    if is_async:
        ok = False
sys.exit(0 if ok else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""Req2.1/2.2/2.3: deprecation warning emitted on missing/None handler, NOT on
a real handler. Req2.4: supplied handler stored on instance."""
import sys, warnings

from django.conf import settings
if not settings.configured:
    settings.configure(
        DEBUG=True,
        CACHES={"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}},
        SESSION_ENGINE="django.contrib.sessions.backends.signed_cookies",
    )
import django
django.setup()
from django.utils.deprecation import RemovedInDjango40Warning
from django.contrib.sessions.middleware import SessionMiddleware
from django.middleware.cache import UpdateCacheMiddleware, FetchFromCacheMiddleware, CacheMiddleware
from django.middleware.security import SecurityMiddleware

classes = [SessionMiddleware, UpdateCacheMiddleware, FetchFromCacheMiddleware, CacheMiddleware, SecurityMiddleware]
ok = True

def warned(fn):
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        fn()
        got = [x for x in w if issubclass(x.category, RemovedInDjango40Warning)
               and "None" in str(x.message) and "get_response" in str(x.message)]
        return len(got) > 0

def sget(request):
    return None

for cls in classes:
    # no arg
    no_arg = warned(lambda: cls())
    # explicit None
    none_arg = warned(lambda: cls(None))
    # real handler => NO warning
    real = warned(lambda: cls(sget))
    inst = cls(sget)
    stored = getattr(inst, "get_response", "MISSING") is sget
    print(f"{cls.__name__}: warn_noarg={no_arg} warn_none={none_arg} warn_real={real} stored={stored}")
    if not (no_arg and none_arg and (not real) and stored):
        ok = False
sys.exit(0 if ok else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""Req3.1/3.2/3.6: UpdateCacheMiddleware & FetchFromCacheMiddleware config
attributes correct from settings; cache backend matches resolved alias."""
import sys

from django.conf import settings
if not settings.configured:
    settings.configure(
        DEBUG=True,
        CACHES={
            "default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"},
            "other": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache", "LOCATION": "other"},
        },
        CACHE_MIDDLEWARE_SECONDS=123,
        CACHE_MIDDLEWARE_KEY_PREFIX="myprefix",
        CACHE_MIDDLEWARE_ALIAS="other",
    )
import django
django.setup()
from django.core.cache import caches
from django.middleware.cache import UpdateCacheMiddleware, FetchFromCacheMiddleware

def h(request):
    return None

ok = True
u = UpdateCacheMiddleware(h)
print(f"Update: timeout={u.cache_timeout} page_timeout={u.page_timeout} prefix={u.key_prefix} alias={u.cache_alias} cache_is_alias={u.cache is caches['other']}")
if not (u.cache_timeout == 123 and u.page_timeout is None and u.key_prefix == "myprefix"
        and u.cache_alias == "other" and u.cache is caches["other"]):
    ok = False

f = FetchFromCacheMiddleware(h)
print(f"Fetch: prefix={f.key_prefix} alias={f.cache_alias} cache_is_alias={f.cache is caches['other']}")
if not (f.key_prefix == "myprefix" and f.cache_alias == "other" and f.cache is caches["other"]):
    ok = False
sys.exit(0 if ok else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""Req3.3/3.4/3.5/3.6: CacheMiddleware config resolution.
- no overrides -> from settings
- overrides -> use provided (None prefix -> '', None alias -> default)
- explicit timeout used; else default
- cache backend matches effective alias."""
import sys

from django.conf import settings
if not settings.configured:
    settings.configure(
        DEBUG=True,
        CACHES={
            "default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"},
            "other": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache", "LOCATION": "other"},
        },
        CACHE_MIDDLEWARE_SECONDS=123,
        CACHE_MIDDLEWARE_KEY_PREFIX="myprefix",
        CACHE_MIDDLEWARE_ALIAS="other",
    )
import django
django.setup()
from django.core.cache import caches, DEFAULT_CACHE_ALIAS
from django.middleware.cache import CacheMiddleware

def h(request):
    return None

ok = True

# no overrides: resolves from same settings as Update/Fetch
c = CacheMiddleware(h)
print(f"no-ovr: prefix={c.key_prefix!r} alias={c.cache_alias!r} timeout={c.cache_timeout} cache_ok={c.cache is caches['other']}")
if not (c.key_prefix == "myprefix" and c.cache_alias == "other"
        and c.cache_timeout == 123 and c.cache is caches["other"]):
    ok = False

# explicit timeout used
c2 = CacheMiddleware(h, cache_timeout=99)
print(f"timeout-ovr: timeout={c2.cache_timeout}")
if c2.cache_timeout != 99:
    ok = False

# overrides: None prefix -> '', None alias -> default
c3 = CacheMiddleware(h, key_prefix=None, cache_alias=None)
print(f"none-ovr: prefix={c3.key_prefix!r} alias={c3.cache_alias!r} cache_ok={c3.cache is caches[DEFAULT_CACHE_ALIAS]}")
if not (c3.key_prefix == "" and c3.cache_alias == DEFAULT_CACHE_ALIAS
        and c3.cache is caches[DEFAULT_CACHE_ALIAS]):
    ok = False

# explicit alias override -> cache matches it
c4 = CacheMiddleware(h, cache_alias="default", key_prefix="p")
print(f"alias-ovr: alias={c4.cache_alias!r} prefix={c4.key_prefix!r} cache_ok={c4.cache is caches['default']}")
if not (c4.cache_alias == "default" and c4.key_prefix == "p" and c4.cache is caches["default"]):
    ok = False

sys.exit(0 if ok else 1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
"""Req4.2/4.3: SecurityMiddleware retains its settings reads after fix, and
its request-phase behavior is preserved (a plain HTTP GET on an exempt path
proceeds without SSL redirect)."""
import sys

from django.conf import settings
if not settings.configured:
    settings.configure(
        DEBUG=True,
        ALLOWED_HOSTS=["testserver", "*"],
        CACHES={"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}},
        SECURE_HSTS_SECONDS=3600,
        SECURE_HSTS_INCLUDE_SUBDOMAINS=True,
        SECURE_HSTS_PRELOAD=True,
        SECURE_CONTENT_TYPE_NOSNIFF=True,
        SECURE_REFERRER_POLICY="same-origin",
        SECURE_SSL_REDIRECT=True,
        SECURE_SSL_HOST=None,
        SECURE_REDIRECT_EXEMPT=[r"^exempt/"],
    )
import django
django.setup()
from django.middleware.security import SecurityMiddleware
from django.http import HttpRequest, HttpResponse

def h(request):
    return HttpResponse("ok")

ok = True
m = SecurityMiddleware(h)
print(f"sts_seconds={m.sts_seconds} include_sub={m.sts_include_subdomains} preload={m.sts_preload} redirect={m.redirect} referrer={m.referrer_policy!r} exempt_n={len(m.redirect_exempt)}")
if not (m.sts_seconds == 3600 and m.sts_include_subdomains and m.sts_preload
        and m.redirect and m.referrer_policy == "same-origin" and len(m.redirect_exempt) == 1):
    ok = False

# exempt path over http: no redirect (process_request returns None)
req = HttpRequest()
req.META["SERVER_NAME"] = "testserver"
req.META["SERVER_PORT"] = "80"
req.path = "/exempt/foo"
req.path_info = "/exempt/foo"
resp = m.process_request(req)
print(f"exempt process_request -> {resp!r}")
if resp is not None:
    ok = False

# non-exempt path over http: redirect to https
req2 = HttpRequest()
req2.META["SERVER_NAME"] = "testserver"
req2.META["SERVER_PORT"] = "80"
req2.path = "/secret"
req2.path_info = "/secret"
resp2 = m.process_request(req2)
code = getattr(resp2, "status_code", None)
print(f"nonexempt process_request -> status={code}")
if code not in (301, 302):
    ok = False

sys.exit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Positive control -- Req1.1: async handler => instance recognized as async.
Covers all 5 affected middleware classes. Must HOLD patched, FAIL at base."""
import asyncio, sys

def setup():
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            DEBUG=True,
            CACHES={"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}},
            SESSION_ENGINE="django.contrib.sessions.backends.signed_cookies",
        )
    import django
    django.setup()

setup()
from django.contrib.sessions.middleware import SessionMiddleware
from django.middleware.cache import UpdateCacheMiddleware, FetchFromCacheMiddleware, CacheMiddleware
from django.middleware.security import SecurityMiddleware

async def aget(request):
    return None

classes = [SessionMiddleware, UpdateCacheMiddleware, FetchFromCacheMiddleware, CacheMiddleware, SecurityMiddleware]
ok = True
for cls in classes:
    inst = cls(aget)
    is_async = asyncio.iscoroutinefunction(inst)
    print(f"{cls.__name__}: iscoroutinefunction(instance)={is_async}")
    if not is_async:
        ok = False
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

6 probes, all HOLD on the gold-patched tree; positive control (probe_1) discriminates (HOLDS patched, VIOLATED at base: cache+security middleware report iscoroutinefunction=False at base). Coverage: probe_1 Req1.1 async handler => async instance across all 5 classes (positive control); probe_2 Req1.2 sync handler => not async; probe_3 Req2.1/2.2/2.3/2.4 deprecation warning on missing/None handler, none on real handler, handler stored; probe_4 Req3.1/3.2/3.6 Update/Fetch cache config from settings + backend matches alias; probe_5 Req3.3/3.4/3.5/3.6 CacheMiddleware resolution incl. None-override -> ''/default and explicit timeout; probe_6 Req4.2/4.3 SecurityMiddleware settings reads + request-phase (exempt no-redirect / non-exempt 301) preserved. Candidate patch 'partial_fix_session_security_only' applies super().__init__ only to Session+Security, leaving cache middleware unfixed — REJECTED by probe_1 (Update/Fetch/CacheMiddleware iscoroutinefunction=False), demonstrating the suite discriminates a plausible weak reading (fixing only the classes the reporter first noticed). No too-weak candidate passed the suite. Verdict SOUND.

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
"""Positive control -- Req1.1: async handler => instance recognized as async.
Covers all 5 affected middleware classes. Must HOLD patched, FAIL at base."""
import asyncio, sys

def setup():
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            DEBUG=True,
            CACHES={"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}},
            SESSION_ENGINE="django.contrib.sessions.backends.signed_cookies",
        )
    import django
    django.setup()

setup()
from django.contrib.sessions.middleware import SessionMiddleware
from django.middleware.cache import UpdateCacheMiddleware, FetchFromCacheMiddleware, CacheMiddleware
from django.middleware.security import SecurityMiddleware

async def aget(request):
    return None

classes = [SessionMiddleware, UpdateCacheMiddleware, FetchFromCacheMiddleware, CacheMiddleware, SecurityMiddleware]
ok = True
for cls in classes:
    inst = cls(aget)
    is_async = asyncio.iscoroutinefunction(inst)
    print(f"{cls.__name__}: iscoroutinefunction(instance)={is_async}")
    if not is_async:
        ok = False
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

6 probes, all HOLD on the gold-patched tree; positive control (probe_1) discriminates (HOLDS patched, VIOLATED at base: cache+security middleware report iscoroutinefunction=False at base). Coverage: probe_1 Req1.1 async handler => async instance across all 5 classes (positive control); probe_2 Req1.2 sync handler => not async; probe_3 Req2.1/2.2/2.3/2.4 deprecation warning on missing/None handler, none on real handler, handler stored; probe_4 Req3.1/3.2/3.6 Update/Fetch cache config from settings + backend matches alias; probe_5 Req3.3/3.4/3.5/3.6 CacheMiddleware resolution incl. None-override -> ''/default and explicit timeout; probe_6 Req4.2/4.3 SecurityMiddleware settings reads + request-phase (exempt no-redirect / non-exempt 301) preserved. Candidate patch 'partial_fix_session_security_only' applies super().__init__ only to Session+Security, leaving cache middleware unfixed — REJECTED by probe_1 (Update/Fetch/CacheMiddleware iscoroutinefunction=False), demonstrating the suite discriminates a plausible weak reading (fixing only the classes the reporter first noticed). No too-weak candidate passed the suite. Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Probe ran both --patched (exit 0, ALL OK) and --base (exit 1, VIOLATED on Req 1.1). Verified CacheMiddleware override paths per the diff's restructured try/except (self.key_prefix/self.cache_alias/self.cache set only inside try; cache_timeout only overwritten when explicit). No requirement mandates behavior absent from the patch, forbids present behavior, nor pins a narrow slice — Req 1.3/1.4 correctly generalize to the changed behavior rather than one branch.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The requirements.md describes only behavior derivable from the PUBLIC problem_statement (coroutine handed to process_response instead of HttpResponse under ASGI) plus legitimate localization of the change. Checked against hidden material:

- No test file paths leaked (tests/deprecation/test_middleware_mixin.py, tests/cache/tests.py absent).
- No test function/class names (test_coroutine, test_constructor, test_update_cache_middleware_constructor, MiddlewareMixinTests) appear.
- No quoted test or gold code; fix-invented/internal identifiers (super().__init__, MiddlewareMixin._async_check, _get_response_none_deprecation, _is_coroutine) are described behaviorally as 'shared base initialization', not transmitted.
- Naming the 5 affected constructors (SessionMiddleware, UpdateCacheMiddleware, FetchFromCacheMiddleware, CacheMiddleware, SecurityMiddleware) is LEGITIMATE localization — these are the gold-patched files, and the document must say what changes.
- Requirement 1.3 generalizes to 'all built-in middleware from the base', which is BROADER than the test's specific 19-middleware list — not a mirror of the test parametrization.
- Requirement 3's cache-attribute enumeration is described generically via setting names (CACHE_MIDDLEWARE_SECONDS/KEY_PREFIX/ALIAS, caches[alias]) — behavior readable from the base-commit constructors — and does NOT reproduce the test's concrete literal values (30, 'middlewareprefix', 'other', self.other_cache/self.default_cache) or the new assertEqual(middleware.cache, ...) lines. It translates constructor behavior into requirements, which is the intended purpose.
- Deprecation message is paraphrased and is public API-facing behavior.

This is behavioral translation, not test/gold transmission.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
