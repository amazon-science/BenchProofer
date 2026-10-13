# P2 adversarial audit — django__django-17029

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
# Req 1.1/1.2: clear_cache discards get_swappable_settings_name cache -> currsize 0
import sys
import django
from django.conf import settings
settings.configure(INSTALLED_APPS=["django.contrib.contenttypes","django.contrib.auth"], DATABASES={})
django.setup()
from django.apps import apps

apps.get_swappable_settings_name("auth.user")
apps.get_swappable_settings_name("contenttypes.contenttype")
before = apps.get_swappable_settings_name.cache_info().currsize
print("swap currsize before clear_cache:", before)
assert before > 0, "precondition: cache should hold entries"

apps.clear_cache()
after = apps.get_swappable_settings_name.cache_info().currsize
print("swap currsize after clear_cache:", after)
sys.exit(0 if after == 0 else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
# Req 1.3: after clear_cache, get_swappable_settings_name recomputes from current
# registry contents rather than returning a value memoized before clear_cache.
# We verify recomputation by observing a cache miss (not a hit) after clear_cache.
import sys
import django
from django.conf import settings
settings.configure(INSTALLED_APPS=["django.contrib.contenttypes","django.contrib.auth"], DATABASES={})
django.setup()
from django.apps import apps

apps.get_swappable_settings_name("auth.user")  # populate
apps.clear_cache()
info_before = apps.get_swappable_settings_name.cache_info()
val = apps.get_swappable_settings_name("auth.user")
info_after = apps.get_swappable_settings_name.cache_info()
print("value:", val)
print("misses before/after call:", info_before.misses, info_after.misses)
print("hits before/after call:", info_before.hits, info_after.hits)
# recompute => a miss registered, not a hit served from stale memo
recomputed = (info_after.misses == info_before.misses + 1) and (info_after.hits == info_before.hits)
print("recomputed (fresh miss, no stale hit):", recomputed)
sys.exit(0 if (recomputed and val == "AUTH_USER_MODEL") else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
# Req 2.1/2.2: clear_cache continues to discard get_models cache -> currsize 0
import sys
import django
from django.conf import settings
settings.configure(INSTALLED_APPS=["django.contrib.contenttypes","django.contrib.auth"], DATABASES={})
django.setup()
from django.apps import apps

apps.get_models()
apps.get_models(include_auto_created=True)
before = apps.get_models.cache_info().currsize
print("get_models currsize before clear_cache:", before)
assert before > 0

apps.clear_cache()
after = apps.get_models.cache_info().currsize
print("get_models currsize after clear_cache:", after)
sys.exit(0 if after == 0 else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
# Req 3.1/3.2/3.3: clear_cache leaves ready flag unchanged, expires per-model _meta
# caches without refilling get_models, and leaves both caches empty afterwards.
import sys
import django
from django.conf import settings
settings.configure(INSTALLED_APPS=["django.contrib.contenttypes","django.contrib.auth"], DATABASES={})
django.setup()
from django.apps import apps

# populate a per-model _meta cache (fields cache)
User = apps.get_model("auth", "User")
_ = User._meta.fields  # triggers _meta caching
# ensure a cached property populated on _meta
meta = User._meta
# populate _get_fields_cache via get_fields
_ = meta._get_fields(forward=True, reverse=True)
had_fields_cache = bool(getattr(meta, "_get_fields_cache", {}))
print("had _get_fields_cache before:", had_fields_cache)

apps.get_models()
apps.get_swappable_settings_name("auth.user")

ready_before = apps.ready
apps.clear_cache()
ready_after = apps.ready
print("ready before/after:", ready_before, ready_after)

meta_cache_after = getattr(meta, "_get_fields_cache", {})
print("_get_fields_cache after clear:", meta_cache_after)

gm = apps.get_models.cache_info().currsize
gs = apps.get_swappable_settings_name.cache_info().currsize
print("get_models currsize after:", gm, "swap currsize after:", gs)

ok = (ready_before == ready_after) and (ready_after is True) \
     and (len(meta_cache_after) == 0) and (gm == 0) and (gs == 0)
sys.exit(0 if ok else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
# Req 4.1/4.2: cached query methods keep existing semantics.
import sys
import django
from django.conf import settings
settings.configure(INSTALLED_APPS=["django.contrib.contenttypes","django.contrib.auth"], DATABASES={})
django.setup()
from django.apps import apps

models_default = apps.get_models()
models_auto = apps.get_models(include_auto_created=True)
print("n models default:", len(models_default), "n with auto:", len(models_auto))
# flags honored: auto-created superset of default
default_set = set(models_default)
auto_set = set(models_auto)
flag_ok = default_set.issubset(auto_set) and len(auto_set) >= len(default_set)

swap_user = apps.get_swappable_settings_name("auth.user")
swap_nonswap = apps.get_swappable_settings_name("contenttypes.contenttype")
print("swap auth.user:", swap_user, "| contenttype:", swap_nonswap)
sem_ok = (swap_user == "AUTH_USER_MODEL") and (swap_nonswap is None)

# also correct after a clear_cache (recompute yields same answers)
apps.clear_cache()
print("post-clear swap auth.user:", apps.get_swappable_settings_name("auth.user"))
post_ok = apps.get_swappable_settings_name("auth.user") == "AUTH_USER_MODEL" \
          and len(apps.get_models()) == len(models_default)

ok = flag_ok and sem_ok and post_ok
print("flag_ok:", flag_ok, "sem_ok:", sem_ok, "post_ok:", post_ok)
sys.exit(0 if ok else 1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
# Req 4.3: set/unset_available_apps and set/unset_installed_apps end with BOTH
# cached query methods cleared. Focus on set_available_apps/unset_available_apps
# which don't require re-populating INSTALLED_APPS machinery.
import sys
import django
from django.conf import settings
settings.configure(INSTALLED_APPS=["django.contrib.contenttypes","django.contrib.auth"], DATABASES={})
django.setup()
from django.apps import apps

results = {}

# set_available_apps
apps.get_models(); apps.get_swappable_settings_name("auth.user")
apps.set_available_apps(["django.contrib.contenttypes","django.contrib.auth"])
results["set_available_gm"] = apps.get_models.cache_info().currsize
results["set_available_gs"] = apps.get_swappable_settings_name.cache_info().currsize

# unset_available_apps
apps.get_models(); apps.get_swappable_settings_name("auth.user")
apps.unset_available_apps()
results["unset_available_gm"] = apps.get_models.cache_info().currsize
results["unset_available_gs"] = apps.get_swappable_settings_name.cache_info().currsize

print(results)
ok = all(v == 0 for v in results.values())
sys.exit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
# Req 1.1/1.2: clear_cache discards get_swappable_settings_name cache -> currsize 0
import sys
import django
from django.conf import settings
settings.configure(INSTALLED_APPS=["django.contrib.contenttypes","django.contrib.auth"], DATABASES={})
django.setup()
from django.apps import apps

apps.get_swappable_settings_name("auth.user")
apps.get_swappable_settings_name("contenttypes.contenttype")
before = apps.get_swappable_settings_name.cache_info().currsize
print("swap currsize before clear_cache:", before)
assert before > 0, "precondition: cache should hold entries"

apps.clear_cache()
after = apps.get_swappable_settings_name.cache_info().currsize
print("swap currsize after clear_cache:", after)
sys.exit(0 if after == 0 else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Requirements: clear_cache() must clear the get_swappable_settings_name memoized cache (Req1), keep clearing get_models (Req2), preserve ready + expire per-model _meta without refilling get_models, leaving both caches empty (Req3), and keep query semantics + clear both on set/unset_available/installed_apps (Req4). Gold patch adds `self.get_swappable_settings_name.cache_clear()`.

Probe results (path : requirement : base -> patched -> weak-candidate):
- probe_1 (Req1.1/1.2 swap currsize==0 after clear_cache): FAIL(base) -> HOLD(patched) -> FAIL(weak). POSITIVE CONTROL, discriminates.
- probe_2 (Req1.3 recompute = fresh miss not stale hit): FAIL(base) -> HOLD -> FAIL(weak).
- probe_3 (Req2.1/2.2 get_models currsize==0): HOLD(base) -> HOLD -> HOLD. Regression-keep criterion (already true at base).
- probe_4 (Req3.1/3.2/3.3 ready unchanged, _meta expired, both caches empty): FAIL(base, swap currsize=1) -> HOLD -> FAIL(weak).
- probe_5 (Req4.1/4.2 get_models flags honored, swap None for non-swappable, semantics after clear): HOLD(base) -> HOLD -> HOLD. Semantics-preservation.
- probe_6 (Req4.3 set/unset_available_apps clear BOTH caches): FAIL(base, swap gs=1) -> HOLD -> FAIL(weak).

Positive control (probe_1) FAILS at base and HOLDS on patched => discriminating power confirmed.

Candidate wrong-fix (weak.diff): touches the swappable cache but only calls cache_info() instead of cache_clear() — the lazy 'looks like it handles the cache' fix a weak reading permits. Probe suite REJECTS it (probes 1,2,4,6 VIOLATED), so the suite discriminates wrong implementations. No probe-conforming alternative patch was found. All 6 probes hold on the gold-patched tree. VERDICT: SOUND.

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
# Req 1.1/1.2: clear_cache discards get_swappable_settings_name cache -> currsize 0
import sys
import django
from django.conf import settings
settings.configure(INSTALLED_APPS=["django.contrib.contenttypes","django.contrib.auth"], DATABASES={})
django.setup()
from django.apps import apps

apps.get_swappable_settings_name("auth.user")
apps.get_swappable_settings_name("contenttypes.contenttype")
before = apps.get_swappable_settings_name.cache_info().currsize
print("swap currsize before clear_cache:", before)
assert before > 0, "precondition: cache should hold entries"

apps.clear_cache()
after = apps.get_swappable_settings_name.cache_info().currsize
print("swap currsize after clear_cache:", after)
sys.exit(0 if after == 0 else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Requirements: clear_cache() must clear the get_swappable_settings_name memoized cache (Req1), keep clearing get_models (Req2), preserve ready + expire per-model _meta without refilling get_models, leaving both caches empty (Req3), and keep query semantics + clear both on set/unset_available/installed_apps (Req4). Gold patch adds `self.get_swappable_settings_name.cache_clear()`.

Probe results (path : requirement : base -> patched -> weak-candidate):
- probe_1 (Req1.1/1.2 swap currsize==0 after clear_cache): FAIL(base) -> HOLD(patched) -> FAIL(weak). POSITIVE CONTROL, discriminates.
- probe_2 (Req1.3 recompute = fresh miss not stale hit): FAIL(base) -> HOLD -> FAIL(weak).
- probe_3 (Req2.1/2.2 get_models currsize==0): HOLD(base) -> HOLD -> HOLD. Regression-keep criterion (already true at base).
- probe_4 (Req3.1/3.2/3.3 ready unchanged, _meta expired, both caches empty): FAIL(base, swap currsize=1) -> HOLD -> FAIL(weak).
- probe_5 (Req4.1/4.2 get_models flags honored, swap None for non-swappable, semantics after clear): HOLD(base) -> HOLD -> HOLD. Semantics-preservation.
- probe_6 (Req4.3 set/unset_available_apps clear BOTH caches): FAIL(base, swap gs=1) -> HOLD -> FAIL(weak).

Positive control (probe_1) FAILS at base and HOLDS on patched => discriminating power confirmed.

Candidate wrong-fix (weak.diff): touches the swappable cache but only calls cache_info() instead of cache_clear() — the lazy 'looks like it handles the cache' fix a weak reading permits. Probe suite REJECTS it (probes 1,2,4,6 VIOLATED), so the suite discriminates wrong implementations. No probe-conforming alternative patch was found. All 6 probes hold on the gold-patched tree. VERDICT: SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Requirements pin the full changed behavior (both caches cleared after clear_cache, plus preservation of ready/_meta refresh), not a narrow slice. Req 1.2/2.2 use the precise observable (cache_info().currsize==0). Req 3.2 (expire per-model _meta without refilling get_models) and Req 4 (unchanged query semantics) correctly describe code the patch leaves intact. Modeling boundary matches the gold patch; no invented, over-mandated, or forbidden behavior detected.

Counterexample / evidence:

```
None found. Patched tree probe exits 0 (HOLDS); base_commit probe exits 1 with AssertionError 'swappable not cleared', matching the fix's single-line effect.
```


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** All load-bearing content is public via problem_statement: it names Apps.clear_cache(), get_swappable_settings_name, the functools LRU cache wrapper, and even the exact fix line self.get_swappable_settings_name.cache_clear(). The requirements translate this into behavioral EARS criteria. The cache_info().currsize == 0 assertions (Req 1.2 / 2.2) mirror the hidden test's two assertions, but currsize is the standard functools inspection API and is the natural way to observe 'cache cleared' — a behavioral description, not test transcription. No test function/class names (test_clear_cache, apps.tests.AppsTests), file paths (tests/apps/tests.py), parametrization ids, gold-invented identifiers, or test-shaped case enumerations are present. Naming get_models / get_swappable_settings_name is legitimate localization of the change.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
