# P2 adversarial audit — django__django-13089

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
"""
Positive control + Requirement 1.3 / 3.1:
Storing a value under a config that forces the cull pass and an EMPTY boundary
result must complete WITHOUT error and the just-stored key must be present.

Encoding: cull cache with _max_entries = -1 forces _cull to run the boundary
query; with -1 max entries the culling_sql LIMIT/OFFSET yields no row.
HOLDS iff set() succeeds and has_key() reports True.
"""
import sys


def main():
    import django
    from django.conf import settings
    settings.configure(
        DEBUG=True,
        DATABASES={
            'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'},
        },
        CACHES={
            'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'},
            'cull': {
                'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
                'LOCATION': 'test_cull_table',
                'OPTIONS': {'MAX_ENTRIES': 30, 'CULL_FREQUENCY': 3},
            },
        },
        USE_TZ=False,
        INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
    )
    django.setup()

    from django.core.cache import caches
    from django.core.management import call_command
    call_command('createcachetable')

    cull_cache = caches['cull']
    old_max = cull_cache._max_entries
    cull_cache._max_entries = -1  # force _cull to delete on first record
    try:
        cull_cache.set('force_cull_delete', 'value', 1000)
        present = cull_cache.has_key('force_cull_delete')
        print('set() completed; has_key ->', present)
        if present is not True:
            print('FAIL: key not present after store')
            return 1
        print('PASS')
        return 0
    except Exception as e:
        print('FAIL: exception during set/has_key:', type(e).__name__, e)
        return 1
    finally:
        cull_cache._max_entries = old_max


if __name__ == '__main__':
    sys.exit(main())
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""
Requirement 1.4 / 2.3 (regression): when the boundary query returns an actual
row, the backend deletes entries whose cache_key sorts below it, so normal
size-limiting culling keeps the table bounded.

Encoding: MAX_ENTRIES=30, CULL_FREQUENCY=3; insert 60 distinct keys (all with a
long timeout, none expired). _cull must run and boundary-delete, so the final
row count must be strictly below the number inserted.
HOLDS iff final_count < inserted.
"""
import sys


def main():
    import django
    from django.conf import settings
    settings.configure(
        DEBUG=True,
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
        CACHES={
            'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'},
            'cull': {
                'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
                'LOCATION': 'probe2_cull_table',
                'OPTIONS': {'MAX_ENTRIES': 30, 'CULL_FREQUENCY': 3},
            },
        },
        USE_TZ=False,
        INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
    )
    django.setup()
    from django.core.cache import caches
    from django.core.management import call_command
    from django.db import connections, router
    call_command('createcachetable')

    cull_cache = caches['cull']
    inserted = 60
    for i in range(inserted):
        cull_cache.set('key_%02d' % i, 'value_%d' % i, 1000)

    db = router.db_for_read(cull_cache.cache_model_class)
    with connections[db].cursor() as cursor:
        cursor.execute('SELECT COUNT(*) FROM probe2_cull_table')
        count = cursor.fetchone()[0]
    print('inserted=%d final_count=%d' % (inserted, count))
    if count < inserted:
        print('PASS: culling reduced the table (boundary deletion happened)')
        return 0
    print('FAIL: table not reduced; boundary deletion did not occur')
    return 1


if __name__ == '__main__':
    sys.exit(main())
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""
Requirement 2.1 (regression): the maintenance pass first deletes every entry
whose `expires` lies strictly before `now`.

Encoding: insert entries with a tiny timeout so they expire, sleep past them,
then set a fresh key which triggers _cull. Expired entries must be gone.
HOLDS iff the expired keys are absent afterwards while the fresh key is present.
"""
import sys
import time


def main():
    import django
    from django.conf import settings
    settings.configure(
        DEBUG=True,
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
        CACHES={
            'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'},
            'cull': {
                'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
                'LOCATION': 'probe3_cull_table',
                'OPTIONS': {'MAX_ENTRIES': 1000, 'CULL_FREQUENCY': 3},
            },
        },
        USE_TZ=False,
        INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
    )
    django.setup()
    from django.core.cache import caches
    from django.core.management import call_command
    call_command('createcachetable')

    cull_cache = caches['cull']
    for i in range(5):
        cull_cache.set('expiring_%d' % i, 'v', 1)  # 1 second timeout
    time.sleep(1.5)
    # This set triggers _cull -> expired deletion first.
    cull_cache.set('fresh', 'v', 1000)

    expired_present = [i for i in range(5) if cull_cache.has_key('expiring_%d' % i)]
    fresh_present = cull_cache.has_key('fresh')
    print('expired_still_present=%s fresh_present=%s' % (expired_present, fresh_present))
    if not expired_present and fresh_present is True:
        print('PASS: expired removed, fresh kept')
        return 0
    print('FAIL')
    return 1


if __name__ == '__main__':
    sys.exit(main())
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""
Requirement 2.2 (regression): when after expiry removal the number of entries
does NOT exceed MAX_ENTRIES, no further (boundary) deletion happens and entries
remain in place.

Encoding: MAX_ENTRIES high (1000), insert 10 non-expiring keys. After a further
set triggers _cull, all 11 keys must remain present (no boundary culling).
HOLDS iff all keys present.
"""
import sys


def main():
    import django
    from django.conf import settings
    settings.configure(
        DEBUG=True,
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
        CACHES={
            'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'},
            'cull': {
                'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
                'LOCATION': 'probe4_cull_table',
                'OPTIONS': {'MAX_ENTRIES': 1000, 'CULL_FREQUENCY': 3},
            },
        },
        USE_TZ=False,
        INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
    )
    django.setup()
    from django.core.cache import caches
    from django.core.management import call_command
    call_command('createcachetable')

    cull_cache = caches['cull']
    keys = ['k_%02d' % i for i in range(10)]
    for k in keys:
        cull_cache.set(k, 'v', 1000)
    cull_cache.set('trigger', 'v', 1000)

    missing = [k for k in keys if not cull_cache.has_key(k)]
    trigger_present = cull_cache.has_key('trigger')
    print('missing=%s trigger_present=%s' % (missing, trigger_present))
    if not missing and trigger_present is True:
        print('PASS: under-max, nothing culled')
        return 0
    print('FAIL: entries removed despite being under max')
    return 1


if __name__ == '__main__':
    sys.exit(main())
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""
Requirement 2.4 (regression): if CULL_FREQUENCY is zero, the backend clears the
ENTIRE table rather than doing boundary-based culling.

Encoding: MAX_ENTRIES small (10), CULL_FREQUENCY=0. Insert enough non-expiring
keys to exceed max, then a set triggers _cull -> clear(). Table must be nearly
empty (only the just-inserted keys survive the clear performed before the last
insert). We assert the count dropped far below the number inserted, and no error.
HOLDS iff the pass completes and count is drastically reduced (<= a few).
"""
import sys


def main():
    import django
    from django.conf import settings
    settings.configure(
        DEBUG=True,
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
        CACHES={
            'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'},
            'cull': {
                'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
                'LOCATION': 'probe5_cull_table',
                'OPTIONS': {'MAX_ENTRIES': 10, 'CULL_FREQUENCY': 0},
            },
        },
        USE_TZ=False,
        INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
    )
    django.setup()
    from django.core.cache import caches
    from django.core.management import call_command
    from django.db import connections, router
    call_command('createcachetable')

    cull_cache = caches['cull']
    try:
        for i in range(30):
            cull_cache.set('z_%02d' % i, 'v', 1000)
    except Exception as e:
        print('FAIL: exception during zero-cull set:', type(e).__name__, e)
        return 1

    db = router.db_for_read(cull_cache.cache_model_class)
    with connections[db].cursor() as cursor:
        cursor.execute('SELECT COUNT(*) FROM probe5_cull_table')
        count = cursor.fetchone()[0]
    print('inserted=30 final_count=%d (zero cull -> clear())' % count)
    # After clear() the table is emptied when over max; only a small tail remains.
    if count <= 11:
        print('PASS: zero-cull cleared the table')
        return 0
    print('FAIL: table not cleared under zero cull frequency')
    return 1


if __name__ == '__main__':
    sys.exit(main())
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
"""
Requirement 3.2: repeated cache writes that keep triggering the cull pass with
an empty boundary result must ALL complete successfully (no leak of the empty
boundary result into a failure).

Encoding: cull cache with _max_entries=-1 (forces empty-boundary cull each set).
Do many consecutive sets; every one must succeed and its key be present.
HOLDS iff all N sets succeed with keys present.
"""
import sys


def main():
    import django
    from django.conf import settings
    settings.configure(
        DEBUG=True,
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
        CACHES={
            'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'},
            'cull': {
                'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
                'LOCATION': 'probe6_cull_table',
                'OPTIONS': {'MAX_ENTRIES': 30, 'CULL_FREQUENCY': 3},
            },
        },
        USE_TZ=False,
        INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
    )
    django.setup()
    from django.core.cache import caches
    from django.core.management import call_command
    call_command('createcachetable')

    cull_cache = caches['cull']
    cull_cache._max_entries = -1
    N = 15
    for i in range(N):
        try:
            cull_cache.set('rep_%d' % i, 'v', 1000)
        except Exception as e:
            print('FAIL: set #%d raised %s: %s' % (i, type(e).__name__, e))
            return 1
        if cull_cache.has_key('rep_%d' % i) is not True:
            print('FAIL: key rep_%d absent after set' % i)
            return 1
    print('PASS: %d consecutive empty-boundary culling sets all succeeded' % N)
    return 0


if __name__ == '__main__':
    sys.exit(main())
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""
Positive control + Requirement 1.3 / 3.1:
Storing a value under a config that forces the cull pass and an EMPTY boundary
result must complete WITHOUT error and the just-stored key must be present.

Encoding: cull cache with _max_entries = -1 forces _cull to run the boundary
query; with -1 max entries the culling_sql LIMIT/OFFSET yields no row.
HOLDS iff set() succeeds and has_key() reports True.
"""
import sys


def main():
    import django
    from django.conf import settings
    settings.configure(
        DEBUG=True,
        DATABASES={
            'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'},
        },
        CACHES={
            'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'},
            'cull': {
                'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
                'LOCATION': 'test_cull_table',
                'OPTIONS': {'MAX_ENTRIES': 30, 'CULL_FREQUENCY': 3},
            },
        },
        USE_TZ=False,
        INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
    )
    django.setup()

    from django.core.cache import caches
    from django.core.management import call_command
    call_command('createcachetable')

    cull_cache = caches['cull']
    old_max = cull_cache._max_entries
    cull_cache._max_entries = -1  # force _cull to delete on first record
    try:
        cull_cache.set('force_cull_delete', 'value', 1000)
        present = cull_cache.has_key('force_cull_delete')
        print('set() completed; has_key ->', present)
        if present is not True:
            print('FAIL: key not present after store')
            return 1
        print('PASS')
        return 0
    except Exception as e:
        print('FAIL: exception during set/has_key:', type(e).__name__, e)
        return 1
    finally:
        cull_cache._max_entries = old_max


if __name__ == '__main__':
    sys.exit(main())
```

Prepatch bug re-encoded as an attack: `True`.

Instance django__django-13089: _cull must tolerate an empty boundary result (cache_key_culling_sql returns no row). Gold patch guards `last_cache_key = cursor.fetchone(); if last_cache_key:` before the boundary DELETE.

Probes (all standalone; configure DatabaseCache on sqlite :memory:, createcachetable):
- probe_1 (POSITIVE CONTROL, Req 1.3/3.1): cull cache with _max_entries=-1 forces cull with empty boundary; set() must succeed and has_key True. HOLDS patched (exit0), FAILS at base (TypeError: 'NoneType' object is not subscriptable) => discriminates.
- probe_2 (Req 1.4/2.3 regression): 60 non-expiring keys with MAX_ENTRIES=30/CULL_FREQ=3 must reduce table (boundary deletion still works). HOLDS patched (final_count=30). REJECTS the weak candidate (final_count=60).
- probe_3 (Req 2.1): expired entries removed first, fresh kept. HOLDS patched.
- probe_4 (Req 2.2): under-max => nothing culled, all keys kept. HOLDS patched.
- probe_5 (Req 2.4): CULL_FREQUENCY=0 => clear() whole table. HOLDS patched (final_count=8 after 30 inserts).
- probe_6 (Req 3.2): 15 consecutive empty-boundary culling sets all succeed. HOLDS patched.

Candidate patch weak.diff (drop_boundary_deletion): removes the boundary DELETE entirely (just calls cursor.fetchone()). It satisfies Req 1 (no crash) — probe_1 and probe_6 HOLD under it — but violates the regression criterion Req 1.4/2.3: probe_2 REJECTS it (table not reduced, final_count=60). This demonstrates the probe suite discriminates a requirements-plausible wrong fix; the candidate would also fail the size-limiting behavior the standard cull tests exercise.

All 6 probes hold on the gold-patched tree; positive control holds patched and fails at base. Verdict SOUND.

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
"""
Positive control + Requirement 1.3 / 3.1:
Storing a value under a config that forces the cull pass and an EMPTY boundary
result must complete WITHOUT error and the just-stored key must be present.

Encoding: cull cache with _max_entries = -1 forces _cull to run the boundary
query; with -1 max entries the culling_sql LIMIT/OFFSET yields no row.
HOLDS iff set() succeeds and has_key() reports True.
"""
import sys


def main():
    import django
    from django.conf import settings
    settings.configure(
        DEBUG=True,
        DATABASES={
            'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'},
        },
        CACHES={
            'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'},
            'cull': {
                'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
                'LOCATION': 'test_cull_table',
                'OPTIONS': {'MAX_ENTRIES': 30, 'CULL_FREQUENCY': 3},
            },
        },
        USE_TZ=False,
        INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
    )
    django.setup()

    from django.core.cache import caches
    from django.core.management import call_command
    call_command('createcachetable')

    cull_cache = caches['cull']
    old_max = cull_cache._max_entries
    cull_cache._max_entries = -1  # force _cull to delete on first record
    try:
        cull_cache.set('force_cull_delete', 'value', 1000)
        present = cull_cache.has_key('force_cull_delete')
        print('set() completed; has_key ->', present)
        if present is not True:
            print('FAIL: key not present after store')
            return 1
        print('PASS')
        return 0
    except Exception as e:
        print('FAIL: exception during set/has_key:', type(e).__name__, e)
        return 1
    finally:
        cull_cache._max_entries = old_max


if __name__ == '__main__':
    sys.exit(main())
```

Prepatch bug re-encoded as an attack: `True`.

Instance django__django-13089: _cull must tolerate an empty boundary result (cache_key_culling_sql returns no row). Gold patch guards `last_cache_key = cursor.fetchone(); if last_cache_key:` before the boundary DELETE.

Probes (all standalone; configure DatabaseCache on sqlite :memory:, createcachetable):
- probe_1 (POSITIVE CONTROL, Req 1.3/3.1): cull cache with _max_entries=-1 forces cull with empty boundary; set() must succeed and has_key True. HOLDS patched (exit0), FAILS at base (TypeError: 'NoneType' object is not subscriptable) => discriminates.
- probe_2 (Req 1.4/2.3 regression): 60 non-expiring keys with MAX_ENTRIES=30/CULL_FREQ=3 must reduce table (boundary deletion still works). HOLDS patched (final_count=30). REJECTS the weak candidate (final_count=60).
- probe_3 (Req 2.1): expired entries removed first, fresh kept. HOLDS patched.
- probe_4 (Req 2.2): under-max => nothing culled, all keys kept. HOLDS patched.
- probe_5 (Req 2.4): CULL_FREQUENCY=0 => clear() whole table. HOLDS patched (final_count=8 after 30 inserts).
- probe_6 (Req 3.2): 15 consecutive empty-boundary culling sets all succeed. HOLDS patched.

Candidate patch weak.diff (drop_boundary_deletion): removes the boundary DELETE entirely (just calls cursor.fetchone()). It satisfies Req 1 (no crash) — probe_1 and probe_6 HOLD under it — but violates the regression criterion Req 1.4/2.3: probe_2 REJECTS it (table not reduced, final_count=60). This demonstrates the probe suite discriminates a requirements-plausible wrong fix; the candidate would also fail the size-limiting behavior the standard cull tests exercise.

All 6 probes hold on the gold-patched tree; positive control holds patched and fails at base. Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Gold patch only wraps the boundary DELETE in `if last_cache_key:` after `fetchone()`. Requirements pin the changed observable behavior (skip boundary deletion on empty result, no TypeError, stored key intact) rather than a narrow slice, and correctly describe the unchanged culling scaffolding. Boundary probe with a monkeypatched empty cache_key_culling_sql: base VIOLATED (TypeError at db.py:272), patched HOLDS (key4 present, no error). No requirement mandates behavior the code lacks, forbids behavior it has, or invents unseen behavior.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** All requirement content is derivable from the public problem_statement, which already names _cull, connection.ops.cache_key_culling_sql(), the DELETE FROM ... WHERE cache_key < %s SQL, cursor.fetchone()[0], and the exact 'NoneType object is not subscriptable' TypeError. The doc translates the guard-on-empty-boundary behavior into EARS requirements. No hidden-test artifacts leak: no test names/paths (test_cull_delete_when_store_empty, DBCacheTests/DBCacheWithTimeZoneTests), no fix-invented identifier (last_cache_key), no _max_entries=-1 forcing trick, no parametrization ids. Req 1.3 (store completes + key present after) mirrors the F2P assertion but is the natural fix behavior already implied by the problem statement's 'leave the freshly stored entry intact'; it describes behavior, not the test. Req 2 restates pre-existing culling algorithm for localization, which is legitimate.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
