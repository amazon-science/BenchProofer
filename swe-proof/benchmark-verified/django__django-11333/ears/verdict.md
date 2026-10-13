# P2 adversarial audit — django__django-11333

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

**Attacks re-run (7):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
"""Req 1.2 / positive control: get_resolver(None) and get_resolver(ROOT_URLCONF)
return the SAME-identity URLResolver object."""
from django.conf import settings
settings.configure(ROOT_URLCONF='sbu_probe_urlconf_A', DEBUG=True)
import django
django.setup()
from django.urls.resolvers import get_resolver

r_none = get_resolver(None)
r_explicit = get_resolver('sbu_probe_urlconf_A')
print("r_none:", id(r_none), "r_explicit:", id(r_explicit))
print("same identity:", r_none is r_explicit)
import sys
sys.exit(0 if r_none is r_explicit else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""Req 1.4: construction/population happen at most once for one effective
config. We patch URLResolver.__init__ to count constructions and confirm that
a None call followed by an explicit-default call builds exactly one resolver."""
from django.conf import settings
settings.configure(ROOT_URLCONF='sbu_probe_urlconf_B', DEBUG=True)
import django
django.setup()
from django.urls import resolvers as R

count = {'n': 0}
orig_init = R.URLResolver.__init__
def counting_init(self, *a, **kw):
    count['n'] += 1
    return orig_init(self, *a, **kw)
R.URLResolver.__init__ = counting_init

a = R.get_resolver(None)
b = R.get_resolver('sbu_probe_urlconf_B')
c = R.get_resolver(None)
print("URLResolver constructions:", count['n'])
import sys
sys.exit(0 if count['n'] == 1 else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""Req 2.1 / 2.2: two genuinely different urlconf values yield DISTINCT
resolvers."""
from django.conf import settings
settings.configure(ROOT_URLCONF='sbu_probe_urlconf_C', DEBUG=True)
import django
django.setup()
from django.urls.resolvers import get_resolver

r1 = get_resolver('sbu_probe_urlconf_C')
r2 = get_resolver('sbu_probe_urlconf_OTHER')
print("r1:", id(r1), "r2:", id(r2), "distinct:", r1 is not r2)
import sys
sys.exit(0 if r1 is not r2 else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""Req 3.1 / 3.2: the returned resolver is a URLResolver rooted at '^/' and
built for the requested urlconf."""
from django.conf import settings
settings.configure(ROOT_URLCONF='sbu_probe_urlconf_D', DEBUG=True)
import django
django.setup()
from django.urls.resolvers import get_resolver, URLResolver

r = get_resolver(None)
print("type:", type(r).__name__)
print("urlconf_name:", r.urlconf_name)
print("pattern regex:", r.pattern.regex.pattern)
ok = (isinstance(r, URLResolver)
      and r.urlconf_name == 'sbu_probe_urlconf_D'
      and r.pattern.regex.pattern == '^/')
import sys
sys.exit(0 if ok else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""Req 4.1 / 4.3: clear_url_caches() discards cached resolvers so a subsequent
get_resolver rebuilds a fresh object (different identity)."""
from django.conf import settings
settings.configure(ROOT_URLCONF='sbu_probe_urlconf_E', DEBUG=True)
import django
django.setup()
from django.urls.resolvers import get_resolver
from django.urls.base import clear_url_caches

r1 = get_resolver(None)
clear_url_caches()
r2 = get_resolver(None)
print("before:", id(r1), "after clear:", id(r2), "rebuilt:", r1 is not r2)
# and after clearing, None and explicit still collapse
r3 = get_resolver('sbu_probe_urlconf_E')
print("collapse after clear:", r2 is r3)
import sys
sys.exit(0 if (r1 is not r2 and r2 is r3) else 1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
"""Req 4.2: clear_url_caches also clears the get_callable cache and calls
cache_clear on get_ns_resolver, exactly as before. We populate get_callable
(real), and instrument get_ns_resolver.cache_clear to confirm it is invoked."""
from django.conf import settings
settings.configure(ROOT_URLCONF='sbu_probe_urlconf_F', DEBUG=True)
import django
django.setup()
from django.urls.base import clear_url_caches
from django.urls.utils import get_callable
from django.urls import resolvers as R

get_callable('django.views.defaults.page_not_found')
before_gc = get_callable.cache_info().currsize

ns_cleared = {'n': 0}
orig = R.get_ns_resolver.cache_clear
def wrapped():
    ns_cleared['n'] += 1
    return orig()
R.get_ns_resolver.cache_clear = wrapped

clear_url_caches()
after_gc = get_callable.cache_info().currsize
print("get_callable currsize:", before_gc, "->", after_gc)
print("get_ns_resolver.cache_clear called:", ns_cleared['n'])
ok = (before_gc > 0 and after_gc == 0 and ns_cleared['n'] == 1)
import sys
sys.exit(0 if ok else 1)
```

Attack 7 — `probe_7.py` → holds on the patched tree (good)

```python
"""Req 5.1: get_resolver callable with no arg, None, or a value; returns
URLResolver in every case."""
from django.conf import settings
settings.configure(ROOT_URLCONF='sbu_probe_urlconf_G', DEBUG=True)
import django
django.setup()
from django.urls.resolvers import get_resolver, URLResolver

a = get_resolver()
b = get_resolver(None)
c = get_resolver('sbu_probe_urlconf_G')
d = get_resolver('sbu_probe_urlconf_H')
print([type(x).__name__ for x in (a, b, c, d)])
ok = all(isinstance(x, URLResolver) for x in (a, b, c, d))
# no-arg, None, explicit-default all identical
ok = ok and (a is b is c) and (d is not a)
print("noarg/None/default collapse:", a is b is c, "distinct other:", d is not a)
import sys
sys.exit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Req 1.2 / positive control: get_resolver(None) and get_resolver(ROOT_URLCONF)
return the SAME-identity URLResolver object."""
from django.conf import settings
settings.configure(ROOT_URLCONF='sbu_probe_urlconf_A', DEBUG=True)
import django
django.setup()
from django.urls.resolvers import get_resolver

r_none = get_resolver(None)
r_explicit = get_resolver('sbu_probe_urlconf_A')
print("r_none:", id(r_none), "r_explicit:", id(r_explicit))
print("same identity:", r_none is r_explicit)
import sys
sys.exit(0 if r_none is r_explicit else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Requirements: get_resolver should normalize urlconf=None to settings.ROOT_URLCONF BEFORE the memoized lookup, so None and the explicit default collapse to one cached URLResolver, while distinctness, construction shape, and clear_url_caches behavior are preserved. Gold patch splits normalization (get_resolver) from the lru_cache (_get_cached_resolver) and repoints clear_url_caches at _get_cached_resolver.cache_clear.

Probes (all HOLD on gold-patched tree):
- probe_1 (Req 1.2, POSITIVE CONTROL): get_resolver(None) is get_resolver(ROOT_URLCONF). HOLDS patched, VIOLATED at base (base: r_none != r_explicit) -> discriminates.
- probe_2 (Req 1.4): instruments URLResolver.__init__ count; None+explicit+None builds exactly 1. HOLDS patched (1), VIOLATED at base (2).
- probe_3 (Req 2.1/2.2): two different urlconf strings -> distinct resolvers. HOLDS.
- probe_4 (Req 3.1/3.2): returned object is URLResolver, urlconf_name == effective config, pattern regex == '^/'. HOLDS.
- probe_5 (Req 4.1/4.3): clear_url_caches() rebuilds a fresh resolver (different identity) and collapse still holds afterward. HOLDS patched.
- probe_6 (Req 4.2): clear_url_caches empties get_callable cache and invokes get_ns_resolver.cache_clear. HOLDS.
- probe_7 (Req 5.1): get_resolver callable no-arg/None/value, always URLResolver; no-arg/None/default collapse, other stays distinct. HOLDS.

Candidate wrong-fix weak_A: replaces the lru_cache on get_resolver with a manual module-level dict cache (collapses None/default correctly, keeps distinctness) but does NOT wire the new cache into clear_url_caches (base.py still calls get_resolver.cache_clear which no longer exists). Probes 1,2,3,4,7 pass under weak_A, but probes 5 and 6 REJECT it (AttributeError: 'function' object has no attribute 'cache_clear') -> the suite discriminates a plausible partial fix that breaks Req 4. This is the required >=1 exercised, >=1 rejected candidate.

Conclusion: >=5 distinct probes all hold on patched tree; positive control fails at base and holds patched (prepatch_reproduced=true); a requirements-relevant wrong candidate is rejected by the suite. No violation or too-weak finding. Verdict SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 7 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 7 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py`, `probe_7.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

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
"""Req 1.2 / positive control: get_resolver(None) and get_resolver(ROOT_URLCONF)
return the SAME-identity URLResolver object."""
from django.conf import settings
settings.configure(ROOT_URLCONF='sbu_probe_urlconf_A', DEBUG=True)
import django
django.setup()
from django.urls.resolvers import get_resolver

r_none = get_resolver(None)
r_explicit = get_resolver('sbu_probe_urlconf_A')
print("r_none:", id(r_none), "r_explicit:", id(r_explicit))
print("same identity:", r_none is r_explicit)
import sys
sys.exit(0 if r_none is r_explicit else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Requirements: get_resolver should normalize urlconf=None to settings.ROOT_URLCONF BEFORE the memoized lookup, so None and the explicit default collapse to one cached URLResolver, while distinctness, construction shape, and clear_url_caches behavior are preserved. Gold patch splits normalization (get_resolver) from the lru_cache (_get_cached_resolver) and repoints clear_url_caches at _get_cached_resolver.cache_clear.

Probes (all HOLD on gold-patched tree):
- probe_1 (Req 1.2, POSITIVE CONTROL): get_resolver(None) is get_resolver(ROOT_URLCONF). HOLDS patched, VIOLATED at base (base: r_none != r_explicit) -> discriminates.
- probe_2 (Req 1.4): instruments URLResolver.__init__ count; None+explicit+None builds exactly 1. HOLDS patched (1), VIOLATED at base (2).
- probe_3 (Req 2.1/2.2): two different urlconf strings -> distinct resolvers. HOLDS.
- probe_4 (Req 3.1/3.2): returned object is URLResolver, urlconf_name == effective config, pattern regex == '^/'. HOLDS.
- probe_5 (Req 4.1/4.3): clear_url_caches() rebuilds a fresh resolver (different identity) and collapse still holds afterward. HOLDS patched.
- probe_6 (Req 4.2): clear_url_caches empties get_callable cache and invokes get_ns_resolver.cache_clear. HOLDS.
- probe_7 (Req 5.1): get_resolver callable no-arg/None/value, always URLResolver; no-arg/None/default collapse, other stays distinct. HOLDS.

Candidate wrong-fix weak_A: replaces the lru_cache on get_resolver with a manual module-level dict cache (collapses None/default correctly, keeps distinctness) but does NOT wire the new cache into clear_url_caches (base.py still calls get_resolver.cache_clear which no longer exists). Probes 1,2,3,4,7 pass under weak_A, but probes 5 and 6 REJECT it (AttributeError: 'function' object has no attribute 'cache_clear') -> the suite discriminates a plausible partial fix that breaks Req 4. This is the required >=1 exercised, >=1 rejected candidate.

Conclusion: >=5 distinct probes all hold on patched tree; positive control fails at base and holds patched (prepatch_reproduced=true); a requirements-relevant wrong candidate is rejected by the suite. No violation or too-weak finding. Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Patch moves the lru_cache from get_resolver onto a new _get_cached_resolver helper and resolves urlconf=None -> settings.ROOT_URLCONF BEFORE the memoized lookup; clear_url_caches now calls _get_cached_resolver.cache_clear(). Probe results on patched tree: R1.2 None==explicit same identity True; R2 distinct configs distinct True; R3 URLResolver rooted at '^/' True; R4 clear_url_caches rebuilds True; R5 signature preserved. Base-commit probe reproduces the bug (distinct objects). R4.3 explicitly guards the correct cache-clearing boundary the patch touches (the actual lru_cache now lives on the helper), avoiding a wrong-boundary spec. No requirement mandates behavior the code lacks, forbids behavior it has, or invents behavior.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** requirements.md describes the get_resolver cache-keying fix in behavioral terms and localizes to legitimate public symbols (get_resolver, URLResolver, _populate, settings.ROOT_URLCONF, reverse/resolve, set_urlconf, functools.lru_cache) — all present in the public problem_statement. The gold-invented helper `_get_cached_resolver` is NOT leaked. Hidden-test artifacts (test path tests/urlpatterns/test_resolvers.py, class ResolverCacheTests, method test_resolver_cache_default__root_urlconf, and the concrete urlconf module ids 'urlpatterns.path_urls'/'urlpatterns.path_dynamic_urls') do not appear. The assertIs/assertIsNot checks are rendered as abstract same-identity vs distinct-identity behavioral requirements (Req1.2, Req2.1), which is behavior description, not test reconstruction. `RegexPattern(r'^/')` / `^/` (Req3.1) and clear_url_caches clearing get_callable/get_ns_resolver (Req4) are pre-existing public code preserved by the patch, not fix-invented or test-derived. No case enumeration mirrors the test parametrization (the test is a single non-parametrized case).


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
