# P2 adversarial audit — django__django-15569

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 6 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 6 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 6 | `probe_1_get_lookups.py`, `probe_2_get_lookup.py`, `probe_3_transform.py`, `probe_4_shadow_restore.py`, `probe_5_keyerror.py`, `probe_6_register_preserved.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1_get_lookups.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (6):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1_get_lookups.py` → holds on the patched tree (good)

```python
# Req 1.3 / 1.4 (POSITIVE CONTROL): after registering then unregistering a
# lookup, get_lookups() must NOT include the name, WITHOUT any manual cache
# clear. On base (no _clear_cached_lookups in _unregister_lookup) the memoized
# cache stays stale -> name still present -> FAIL. On patched -> HOLD.
import django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True, DATABASES={}, INSTALLED_APPS=[])
django.setup()
from django.db.models import CharField
from django.db.models.lookups import Lookup

NAME = "sbu_probe_lk_unique"

class MyLookup(Lookup):
    lookup_name = NAME

CharField.register_lookup(MyLookup)
# prime the memoized cache while the lookup is registered
primed = CharField.get_lookups()
print("registered present in primed cache:", NAME in primed)
assert NAME in primed, "sanity: registration not visible"

# unregister WITHOUT any manual _clear_cached_lookups call
CharField._unregister_lookup(MyLookup)
after = CharField.get_lookups()
present = NAME in after
print("present in get_lookups() after unregister (no manual clear):", present)
raise SystemExit(0 if not present else 1)
```

Attack 2 — `probe_2_get_lookup.py` → holds on the patched tree (good)

```python
# Req 1.5: after register then unregister, get_lookup(name) resolves as though
# never registered (returns inherited/fallback or None, not the removed lookup).
import django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True, DATABASES={}, INSTALLED_APPS=[])
django.setup()
from django.db.models import CharField
from django.db.models.lookups import Lookup

NAME = "sbu_probe_getlookup_unique"

class MyLookup(Lookup):
    lookup_name = NAME

f = CharField()
CharField.register_lookup(MyLookup)
got = f.get_lookup(NAME)
print("get_lookup while registered:", got)
assert got is MyLookup, "sanity: registration not resolvable"

CharField._unregister_lookup(MyLookup)
got2 = f.get_lookup(NAME)
print("get_lookup after unregister (no manual clear):", got2)
# must not be the removed lookup; for a fresh unique name fallback is None
raise SystemExit(0 if got2 is not MyLookup and got2 is None else 1)
```

Attack 3 — `probe_3_transform.py` → holds on the patched tree (good)

```python
# Req 2.1 / 2.3: after registering a transform then unregistering it,
# get_transform(name) must NOT return the removed transform, without manual clear.
import django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True, DATABASES={}, INSTALLED_APPS=[])
django.setup()
from django.db.models import CharField
from django.db.models.lookups import Transform

NAME = "sbu_probe_tf_unique"

class MyTransform(Transform):
    lookup_name = NAME

f = CharField()
CharField.register_lookup(MyTransform)
got = f.get_transform(NAME)
print("get_transform while registered:", got)
assert got is MyTransform, "sanity: transform not resolvable"

CharField._unregister_lookup(MyTransform)
got2 = f.get_transform(NAME)
print("get_transform after unregister (no manual clear):", got2)
raise SystemExit(0 if got2 is not MyTransform and got2 is None else 1)
```

Attack 4 — `probe_4_shadow_restore.py` → holds on the patched tree (good)

```python
# Req 2.2 / 2.3: a transform registered on JSONField shadows the JSONField
# key-transform fallback for its name. After unregister (NO manual cache clear),
# get_transform(name) must resolve back to the inherited/fallback transform
# (a KeyTransformFactory), not the removed transform. Mirrors the F2P test
# model_fields.test_jsonfield.TestMethods.test_get_transforms.
import django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True, DATABASES={}, INSTALLED_APPS=[])
django.setup()
from django.db import models
from django.db.models.lookups import Transform
from django.db.models.fields.json import KeyTransformFactory

NAME = "sbu_probe_my_transform"

class MyTransform(Transform):
    lookup_name = NAME

models.JSONField.register_lookup(MyTransform)
field = models.JSONField()
t = field.get_transform(NAME)
print("while registered:", t)
assert t is MyTransform, "sanity: transform not resolvable"

models.JSONField._unregister_lookup(MyTransform)   # no manual _clear_cached_lookups
t2 = field.get_transform(NAME)
print("after unregister (no manual clear):", t2)
ok = (t2 is not MyTransform) and isinstance(t2, KeyTransformFactory)
raise SystemExit(0 if ok else 1)
```

Attack 5 — `probe_5_keyerror.py` → holds on the patched tree (good)

```python
# Req 3.6: unregistering a name not present in cls.class_lookups raises KeyError
# (removal targets the class-local registry). Also Req 1.1/1.2: name resolution
# from lookup.lookup_name and explicit lookup_name both remove correctly.
import django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True, DATABASES={}, INSTALLED_APPS=[])
django.setup()
from django.db.models import CharField
from django.db.models.lookups import Lookup

class L(Lookup):
    lookup_name = "sbu_probe_keyerr_unique"

# 3.6: removing an absent name -> KeyError
raised = False
try:
    CharField._unregister_lookup(L)
except KeyError:
    raised = True
print("KeyError on absent removal:", raised)
assert raised, "expected KeyError for absent name"

# 1.1: lookup_name inferred from lookup.lookup_name
CharField.register_lookup(L)
assert "sbu_probe_keyerr_unique" in CharField.get_lookups()
CharField._unregister_lookup(L)  # no explicit name
assert "sbu_probe_keyerr_unique" not in CharField.get_lookups()
print("inferred-name removal ok")

# 1.2: explicit lookup_name removal
CharField.register_lookup(L, lookup_name="explicit_alias_probe")
assert "explicit_alias_probe" in CharField.get_lookups()
CharField._unregister_lookup(L, lookup_name="explicit_alias_probe")
assert "explicit_alias_probe" not in CharField.get_lookups()
print("explicit-name removal ok")
raise SystemExit(0)
```

Attack 6 — `probe_6_register_preserved.py` → holds on the patched tree (good)

```python
# Req 3.1/3.2/3.3: register_lookup unchanged — adds entry, invalidates cache,
# RETURNS the registered lookup; registered name present & resolvable;
# get_lookups() memoized & consistent, recomputes after invalidation.
# This is a "SHALL keep" regression: holds on BOTH base and patched.
import django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True, DATABASES={}, INSTALLED_APPS=[])
django.setup()
from django.db.models import CharField
from django.db.models.lookups import Lookup

NAME = "sbu_probe_reg_preserved"

class L(Lookup):
    lookup_name = NAME

f = CharField()
ret = CharField.register_lookup(L)
print("register_lookup returned:", ret)
assert ret is L, "register_lookup must return the registered lookup"

# 3.2 present & resolvable
lk = CharField.get_lookups()
assert NAME in lk, "registered name absent from get_lookups()"
assert f.get_lookup(NAME) is L, "registered lookup not resolvable"

# 3.3 memoized: repeated calls identical object with no intervening (un)register
a = CharField.get_lookups()
b = CharField.get_lookups()
print("memoized identical object:", a is b)
assert a is b, "get_lookups not memoized (should be lru_cached)"

# cleanup so probe is self-contained; must invalidate after
CharField._unregister_lookup(L)
raise SystemExit(0)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1_get_lookups.py`

```python
# Req 1.3 / 1.4 (POSITIVE CONTROL): after registering then unregistering a
# lookup, get_lookups() must NOT include the name, WITHOUT any manual cache
# clear. On base (no _clear_cached_lookups in _unregister_lookup) the memoized
# cache stays stale -> name still present -> FAIL. On patched -> HOLD.
import django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True, DATABASES={}, INSTALLED_APPS=[])
django.setup()
from django.db.models import CharField
from django.db.models.lookups import Lookup

NAME = "sbu_probe_lk_unique"

class MyLookup(Lookup):
    lookup_name = NAME

CharField.register_lookup(MyLookup)
# prime the memoized cache while the lookup is registered
primed = CharField.get_lookups()
print("registered present in primed cache:", NAME in primed)
assert NAME in primed, "sanity: registration not visible"

# unregister WITHOUT any manual _clear_cached_lookups call
CharField._unregister_lookup(MyLookup)
after = CharField.get_lookups()
present = NAME in after
print("present in get_lookups() after unregister (no manual clear):", present)
raise SystemExit(0 if not present else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Fix under audit: add cls._clear_cached_lookups() to RegisterLookupMixin._unregister_lookup so removing a lookup/transform invalidates the lru_cache'd get_lookups() (django/db/models/query_utils.py). Base names the classmethod _clear_cached_lookups (repo HEAD renamed it _clear_cached_class_lookups; the base_commit 884b4c2 uses _clear_cached_lookups, matching the gold patch).

Probe suite (all run in the official image; standalone python, repo pkg only):
- probe_1_get_lookups.py (Req 1.3/1.4, POSITIVE CONTROL): register on CharField, prime get_lookups() cache, unregister WITHOUT manual clear, assert name absent. patched HOLDS, base VIOLATED (stale cache retains name). Discriminates.
- probe_2_get_lookup.py (Req 1.5): get_lookup(name) after unregister returns None (not the removed lookup). patched HOLDS, base VIOLATED.
- probe_3_transform.py (Req 2.1/2.3): get_transform(name) after unregister != removed transform. patched HOLDS, base VIOLATED.
- probe_4_shadow_restore.py (Req 2.2): transform registered on JSONField shadows the KeyTransformFactory fallback; after unregister, get_transform resolves back to a KeyTransformFactory (mirrors F2P test_get_transforms). patched HOLDS, base VIOLATED.
- probe_5_keyerror.py (Req 3.6 + 1.1/1.2): KeyError on absent removal; inferred-name AND explicit-name removals both invalidate cache. patched HOLDS, base VIOLATED.
- probe_6_register_preserved.py (Req 3.1/3.2/3.3 SHALL-keep regression): register_lookup returns the lookup, name present & resolvable, get_lookups() memoized (identical object). HOLDS on BOTH base and patched (regression criterion, non-discriminating by design).

Discrimination proof (candidate patch): weak_A.diff = partial fix that calls cls._clear_cached_lookups() only inside the `if lookup_name is None` branch (inferred-name path). It satisfies probes 1-4 & 6 but probe_5 REJECTS it (VIOLATED): the explicit-lookup_name removal leaves the cache stale, so 'explicit_alias_probe' persists in get_lookups(). This demonstrates the suite distinguishes an incomplete requirements-conforming-looking fix from the gold one.

Verdict SOUND: 6 distinct probes all hold on the gold-patched tree; positive control (probe_1) holds patched and fails at base (prepatch reproduced); probes 1-5 fail at base; the wrong-fix candidate weak_A is rejected by the suite. No requirements VIOLATION found on the patched tree and no probe-conforming alternative patch discovered that the suite fully accepts.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 6 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 6 | `probe_1_get_lookups.py`, `probe_2_get_lookup.py`, `probe_3_transform.py`, `probe_4_shadow_restore.py`, `probe_5_keyerror.py`, `probe_6_register_preserved.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1_get_lookups.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (6):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

_The 6 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts, and on this backend both roles put it through the same derivation: every block below is a requirement probe run on the gold-patched tree, and the `machine verdict:` line each role publishes above reports BOTH that its probes hold there and how many candidate patches the probe suite rejected — so the two roles re-ran ONE probe suite and each recorded its own outcome for every probe in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `probe_1_get_lookups.py` → holds on the patched tree (good)

Attack 2 — `probe_2_get_lookup.py` → holds on the patched tree (good)

Attack 3 — `probe_3_transform.py` → holds on the patched tree (good)

Attack 4 — `probe_4_shadow_restore.py` → holds on the patched tree (good)

Attack 5 — `probe_5_keyerror.py` → holds on the patched tree (good)

Attack 6 — `probe_6_register_preserved.py` → holds on the patched tree (good)

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1_get_lookups.py`

```python
# Req 1.3 / 1.4 (POSITIVE CONTROL): after registering then unregistering a
# lookup, get_lookups() must NOT include the name, WITHOUT any manual cache
# clear. On base (no _clear_cached_lookups in _unregister_lookup) the memoized
# cache stays stale -> name still present -> FAIL. On patched -> HOLD.
import django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True, DATABASES={}, INSTALLED_APPS=[])
django.setup()
from django.db.models import CharField
from django.db.models.lookups import Lookup

NAME = "sbu_probe_lk_unique"

class MyLookup(Lookup):
    lookup_name = NAME

CharField.register_lookup(MyLookup)
# prime the memoized cache while the lookup is registered
primed = CharField.get_lookups()
print("registered present in primed cache:", NAME in primed)
assert NAME in primed, "sanity: registration not visible"

# unregister WITHOUT any manual _clear_cached_lookups call
CharField._unregister_lookup(MyLookup)
after = CharField.get_lookups()
present = NAME in after
print("present in get_lookups() after unregister (no manual clear):", present)
raise SystemExit(0 if not present else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Fix under audit: add cls._clear_cached_lookups() to RegisterLookupMixin._unregister_lookup so removing a lookup/transform invalidates the lru_cache'd get_lookups() (django/db/models/query_utils.py). Base names the classmethod _clear_cached_lookups (repo HEAD renamed it _clear_cached_class_lookups; the base_commit 884b4c2 uses _clear_cached_lookups, matching the gold patch).

Probe suite (all run in the official image; standalone python, repo pkg only):
- probe_1_get_lookups.py (Req 1.3/1.4, POSITIVE CONTROL): register on CharField, prime get_lookups() cache, unregister WITHOUT manual clear, assert name absent. patched HOLDS, base VIOLATED (stale cache retains name). Discriminates.
- probe_2_get_lookup.py (Req 1.5): get_lookup(name) after unregister returns None (not the removed lookup). patched HOLDS, base VIOLATED.
- probe_3_transform.py (Req 2.1/2.3): get_transform(name) after unregister != removed transform. patched HOLDS, base VIOLATED.
- probe_4_shadow_restore.py (Req 2.2): transform registered on JSONField shadows the KeyTransformFactory fallback; after unregister, get_transform resolves back to a KeyTransformFactory (mirrors F2P test_get_transforms). patched HOLDS, base VIOLATED.
- probe_5_keyerror.py (Req 3.6 + 1.1/1.2): KeyError on absent removal; inferred-name AND explicit-name removals both invalidate cache. patched HOLDS, base VIOLATED.
- probe_6_register_preserved.py (Req 3.1/3.2/3.3 SHALL-keep regression): register_lookup returns the lookup, name present & resolvable, get_lookups() memoized (identical object). HOLDS on BOTH base and patched (regression criterion, non-discriminating by design).

Discrimination proof (candidate patch): weak_A.diff = partial fix that calls cls._clear_cached_lookups() only inside the `if lookup_name is None` branch (inferred-name path). It satisfies probes 1-4 & 6 but probe_5 REJECTS it (VIOLATED): the explicit-lookup_name removal leaves the cache stale, so 'explicit_alias_probe' persists in get_lookups(). This demonstrates the suite distinguishes an incomplete requirements-conforming-looking fix from the gold one.

Verdict SOUND: 6 distinct probes all hold on the gold-patched tree; positive control (probe_1) holds patched and fails at base (prepatch reproduced); probes 1-5 fail at base; the wrong-fix candidate weak_A is rejected by the suite. No requirements VIOLATION found on the patched tree and no probe-conforming alternative patch discovered that the suite fully accepts.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Verified on the patched image: R1.4/R1.5 — after CharField.register_lookup(MyLookup) then _unregister_lookup, get_lookups() no longer contains 'mylkp' and get_lookup('mylkp') returns None with NO manual clear (on base these still returned the removed lookup — HOLDS(base) shows 'mylkp' in get_lookups() True, get_lookup -> MyLookup). R1.1/R1.2 — both the lookup_name=None (resolves lookup.lookup_name) and explicit-name deletion paths work. R2.1/R2.2 — JSONField transform registered then unregistered: get_transform('myt') no longer returns the removed Transform without manual clear. R3.6 — unregistering an absent name raises KeyError (del cls.class_lookups[name]). R3.1/R3.2/R3.3 — register_lookup still adds entry, invalidates cache, and get_lookup resolves the registered lookup. Source of RegisterLookupMixin on the patched image confirms the added `_clear_cached_lookups()` call. Requirement boundary is the changed behavior itself, correctly biconditional (base fails, patched passes). No divergence between requirements and patched code.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Requirements describe the fix behaviorally: making _unregister_lookup invalidate the memoized cache symmetric with register_lookup. All named symbols (RegisterLookupMixin, _unregister_lookup, register_lookup, _clear_cached_lookups, get_lookups/get_lookup/get_transform, class_lookups) are pre-existing source identifiers used for legitimate localization; register_lookup/_unregister_lookup/query_utils.py/cache-clearing are all in the public problem_statement, which also explicitly names the test_func_unique_constraint_lookups test that Req 3.5 alludes to. The hidden FAIL_TO_PASS tests (test_get_transforms in test_jsonfield, test_lookups_caching in custom_lookups) are translated into behavioral acceptance criteria (transform reverts to inherited/fallback after unregister; get_lookups no longer includes the removed name without manual clearing) WITHOUT leaking the test file paths, test function/class names, the fix-invented test identifiers (MyTransform, 'my_transform', 'exactly', Exactly, ForeignObject, KeyTransformFactory), or quoted test/gold code. The gold edit adds only a cls._clear_cached_lookups() call, and _clear_cached_lookups is an existing method, not fix-invented. No case-enumeration mirroring of test parametrization. This is proper behavioral specification, not test reconstruction.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
