# P2 adversarial audit — django__django-11087

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
"""Positive control — Requirement 1.2/1.3/1.6.

When deleting an Origin that cascades to Referrer (which has a large TextField
'large_field' that is NOT referenced by any further cascade relation), the
SELECT that fetches Referrer rows must NOT load 'large_field' (only the
referenced identity columns id + unique_field). HOLDS on patched, FAILS at base.
"""
import django
from django.conf import settings

settings.configure(
    DEBUG=True,
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
    INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
    USE_TZ=False,
)
django.setup()

from django.db import models, connection


class Origin(models.Model):
    class Meta:
        app_label = 'auth'


class Referrer(models.Model):
    origin = models.ForeignKey(Origin, models.CASCADE)
    unique_field = models.IntegerField(unique=True)
    large_field = models.TextField()

    class Meta:
        app_label = 'auth'


class SecondReferrer(models.Model):
    referrer = models.ForeignKey(Referrer, models.CASCADE)
    other_referrer = models.ForeignKey(
        Referrer, models.CASCADE, to_field='unique_field', related_name='+'
    )

    class Meta:
        app_label = 'auth'


with connection.schema_editor() as se:
    se.create_model(Origin)
    se.create_model(Referrer)
    se.create_model(SecondReferrer)

origin = Origin.objects.create()
Referrer.objects.create(origin=origin, unique_field=1, large_field='x' * 50)

connection.queries_log.clear()
origin.delete()

# Find the SELECT that fetches Referrer rows for cascade.
select_sqls = [q['sql'] for q in connection.queries
               if q['sql'].strip().upper().startswith('SELECT')
               and 'referrer' in q['sql'].lower()
               and 'secondreferrer' not in q['sql'].lower()]
print("Referrer SELECTs:")
for s in select_sqls:
    print("  ", s)

quoted = connection.ops.quote_name('large_field')
loads_large = any(quoted in s for s in select_sqls)
print("large_field loaded in Referrer SELECT:", loads_large)

if not select_sqls:
    print("FAIL: no Referrer SELECT captured")
    raise SystemExit(1)
if loads_large:
    print("FAIL: large_field was loaded (columns not narrowed)")
    raise SystemExit(1)
print("PASS: large_field NOT loaded — columns narrowed to referenced fields")
raise SystemExit(0)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""Requirement 1.5 / 2.2 / 3.5 — signal listeners force full-column fetch.

WHEN a pre_delete OR post_delete listener is connected for the related model,
the cascade SELECT for that model SHALL load the full default column set
(including large_field), so the listener observes complete objects.
"""
import django
from django.conf import settings

settings.configure(
    DEBUG=True,
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
    INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
    USE_TZ=False,
)
django.setup()

from django.db import models, connection


class Origin(models.Model):
    class Meta:
        app_label = 'auth'


class Referrer(models.Model):
    origin = models.ForeignKey(Origin, models.CASCADE)
    unique_field = models.IntegerField(unique=True)
    large_field = models.TextField()

    class Meta:
        app_label = 'auth'


class SecondReferrer(models.Model):
    referrer = models.ForeignKey(Referrer, models.CASCADE)
    other_referrer = models.ForeignKey(
        Referrer, models.CASCADE, to_field='unique_field', related_name='+'
    )

    class Meta:
        app_label = 'auth'


with connection.schema_editor() as se:
    se.create_model(Origin)
    se.create_model(Referrer)
    se.create_model(SecondReferrer)

quoted = connection.ops.quote_name('large_field')


def receiver(instance, **kwargs):
    pass


ok = True
for signal_name in ('pre_delete', 'post_delete'):
    origin = Origin.objects.create()
    Referrer.objects.create(origin=origin, unique_field={'pre_delete': 10, 'post_delete': 20}[signal_name], large_field='y' * 40)
    signal = getattr(models.signals, signal_name)
    signal.connect(receiver, sender=Referrer)
    connection.queries_log.clear()
    origin.delete()
    selects = [q['sql'] for q in connection.queries
               if q['sql'].strip().upper().startswith('SELECT')
               and 'referrer' in q['sql'].lower()
               and 'secondreferrer' not in q['sql'].lower()]
    signal.disconnect(receiver, sender=Referrer)
    loads_large = any(quoted in s for s in selects)
    print(f"[{signal_name}] Referrer SELECTs:")
    for s in selects:
        print("   ", s)
    print(f"[{signal_name}] large_field loaded:", loads_large)
    if not loads_large:
        print(f"FAIL: {signal_name} connected but large_field NOT loaded")
        ok = False

if ok:
    print("PASS: signals force full-column fetch")
    raise SystemExit(0)
raise SystemExit(1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""Requirement 3.3 / 3.4 — correctness: the SAME objects are deleted.

Column narrowing must not change which objects are collected/deleted. After
deleting the Origin, all cascaded Referrer and SecondReferrer rows (and the
Origin) must be gone; unrelated rows must remain.
"""
import django
from django.conf import settings

settings.configure(
    DEBUG=True,
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
    INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
    USE_TZ=False,
)
django.setup()

from django.db import models, connection


class Origin(models.Model):
    class Meta:
        app_label = 'auth'


class Referrer(models.Model):
    origin = models.ForeignKey(Origin, models.CASCADE)
    unique_field = models.IntegerField(unique=True)
    large_field = models.TextField()

    class Meta:
        app_label = 'auth'


class SecondReferrer(models.Model):
    referrer = models.ForeignKey(Referrer, models.CASCADE)
    other_referrer = models.ForeignKey(
        Referrer, models.CASCADE, to_field='unique_field', related_name='+'
    )

    class Meta:
        app_label = 'auth'


with connection.schema_editor() as se:
    se.create_model(Origin)
    se.create_model(Referrer)
    se.create_model(SecondReferrer)

o1 = Origin.objects.create()
r1 = Referrer.objects.create(origin=o1, unique_field=1, large_field='a')
SecondReferrer.objects.create(referrer=r1, other_referrer=r1)

# unrelated rows that must survive
o2 = Origin.objects.create()
r2 = Referrer.objects.create(origin=o2, unique_field=2, large_field='b')

o1.delete()

origins = set(Origin.objects.values_list('pk', flat=True))
referrers = set(Referrer.objects.values_list('pk', flat=True))
seconds = SecondReferrer.objects.count()
print("origins remaining:", origins)
print("referrers remaining:", referrers)
print("secondreferrers remaining:", seconds)

ok = (origins == {o2.pk} and referrers == {r2.pk} and seconds == 0)
if ok:
    print("PASS: cascade deleted exactly the correct objects")
    raise SystemExit(0)
print("FAIL: wrong object set deleted")
raise SystemExit(1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""Requirement 2.1/2.2 and 4.1 — signal-listener detection + can_fast_delete.

- Collector._has_signal_listeners(model) must exist and report True iff the
  model has pre_delete OR post_delete listeners, False otherwise.
- Collector.can_fast_delete must return False when such listeners exist.
"""
import django
from django.conf import settings

settings.configure(
    DEBUG=True,
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
    INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
    USE_TZ=False,
)
django.setup()

from django.db import models, connection
from django.db.models.deletion import Collector


class Origin(models.Model):
    class Meta:
        app_label = 'auth'


class Referrer(models.Model):
    origin = models.ForeignKey(Origin, models.CASCADE)
    unique_field = models.IntegerField(unique=True)
    large_field = models.TextField()

    class Meta:
        app_label = 'auth'


with connection.schema_editor() as se:
    se.create_model(Origin)
    se.create_model(Referrer)

c = Collector(using='default')
if not hasattr(c, '_has_signal_listeners'):
    print("FAIL: Collector._has_signal_listeners missing")
    raise SystemExit(1)


def rec(instance, **kwargs):
    pass


ok = True
# No listeners -> negative
base = c._has_signal_listeners(Referrer)
print("no listeners _has_signal_listeners:", base)
if base:
    ok = False
    print("FAIL: reported positive with no listeners")

r = Referrer.objects.create(origin=Origin.objects.create(), unique_field=1, large_field='z')

for signal_name in ('pre_delete', 'post_delete'):
    sig = getattr(models.signals, signal_name)
    sig.connect(rec, sender=Referrer)
    got = c._has_signal_listeners(Referrer)
    can_fd = c.can_fast_delete(Referrer.objects.all())
    print(f"[{signal_name}] _has_signal_listeners:", got, "can_fast_delete:", can_fd)
    if not got:
        ok = False
        print(f"FAIL: {signal_name} not detected")
    if can_fd:
        ok = False
        print(f"FAIL: can_fast_delete True despite {signal_name} listener")
    sig.disconnect(rec, sender=Referrer)

# after disconnect -> negative again
after = c._has_signal_listeners(Referrer)
print("after disconnect:", after)
if after:
    ok = False
    print("FAIL: still positive after disconnect")

if ok:
    print("PASS")
    raise SystemExit(0)
raise SystemExit(1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""Requirement 2.3 — m2m_changed listeners SHALL NOT force a full-column fetch.

The signal check governing column narrowing considers only pre_delete and
post_delete. If only an m2m_changed listener is connected for the related
model, narrowing must STILL apply (large_field NOT loaded).
"""
import django
from django.conf import settings

settings.configure(
    DEBUG=True,
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
    INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
    USE_TZ=False,
)
django.setup()

from django.db import models, connection


class Origin(models.Model):
    class Meta:
        app_label = 'auth'


class Referrer(models.Model):
    origin = models.ForeignKey(Origin, models.CASCADE)
    unique_field = models.IntegerField(unique=True)
    large_field = models.TextField()

    class Meta:
        app_label = 'auth'


class SecondReferrer(models.Model):
    referrer = models.ForeignKey(Referrer, models.CASCADE)
    other_referrer = models.ForeignKey(
        Referrer, models.CASCADE, to_field='unique_field', related_name='+'
    )

    class Meta:
        app_label = 'auth'


with connection.schema_editor() as se:
    se.create_model(Origin)
    se.create_model(Referrer)
    se.create_model(SecondReferrer)


def rec(sender, **kwargs):
    pass


models.signals.m2m_changed.connect(rec, sender=Referrer)

origin = Origin.objects.create()
Referrer.objects.create(origin=origin, unique_field=1, large_field='q' * 30)

connection.queries_log.clear()
origin.delete()
models.signals.m2m_changed.disconnect(rec, sender=Referrer)

quoted = connection.ops.quote_name('large_field')
selects = [q['sql'] for q in connection.queries
           if q['sql'].strip().upper().startswith('SELECT')
           and 'referrer' in q['sql'].lower()
           and 'secondreferrer' not in q['sql'].lower()]
print("Referrer SELECTs with m2m_changed connected:")
for s in selects:
    print("   ", s)
loads_large = any(quoted in s for s in selects)
print("large_field loaded:", loads_large)

if not selects:
    print("FAIL: no Referrer SELECT captured")
    raise SystemExit(1)
if loads_large:
    print("FAIL: m2m_changed wrongly forced full-column fetch")
    raise SystemExit(1)
print("PASS: m2m_changed did NOT force full fetch — narrowing still applied")
raise SystemExit(0)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
"""Requirement 4.2/4.3 + 3.1/3.2 — fast-delete preserved; on_delete gating.

A simple FK relation with no signals and no further cascade targets should be
fast-deleted (added to fast_deletes, no per-object on_delete SELECT). And when
there are no related rows, the cascade fetch must be empty and not trigger a
spurious extra SELECT for on_delete.
"""
import django
from django.conf import settings

settings.configure(
    DEBUG=True,
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
    INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
    USE_TZ=False,
)
django.setup()

from django.db import models, connection
from django.db.models.deletion import Collector


class Origin(models.Model):
    class Meta:
        app_label = 'auth'


class Leaf(models.Model):
    # simple FK, no further cascade targets, no signals -> fast-deletable
    origin = models.ForeignKey(Origin, models.CASCADE)

    class Meta:
        app_label = 'auth'


with connection.schema_editor() as se:
    se.create_model(Origin)
    se.create_model(Leaf)

c = Collector(using='default')
can_fd = c.can_fast_delete(Leaf.objects.all())
print("can_fast_delete(Leaf all):", can_fd)
if not can_fd:
    print("FAIL: simple no-signal FK relation not fast-deletable")
    raise SystemExit(1)

# Deleting an Origin with a Leaf should still delete the Leaf (correctness),
# and an Origin with NO leaves should still be deletable.
o1 = Origin.objects.create()
Leaf.objects.create(origin=o1)
o1.delete()
if Leaf.objects.exists():
    print("FAIL: leaf not deleted on cascade")
    raise SystemExit(1)

o2 = Origin.objects.create()  # no leaves
o2.delete()
if Origin.objects.exists():
    print("FAIL: origin without leaves not deleted")
    raise SystemExit(1)

print("PASS: fast-delete preserved and empty-relation cascade fine")
raise SystemExit(0)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Positive control — Requirement 1.2/1.3/1.6.

When deleting an Origin that cascades to Referrer (which has a large TextField
'large_field' that is NOT referenced by any further cascade relation), the
SELECT that fetches Referrer rows must NOT load 'large_field' (only the
referenced identity columns id + unique_field). HOLDS on patched, FAILS at base.
"""
import django
from django.conf import settings

settings.configure(
    DEBUG=True,
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
    INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
    USE_TZ=False,
)
django.setup()

from django.db import models, connection


class Origin(models.Model):
    class Meta:
        app_label = 'auth'


class Referrer(models.Model):
    origin = models.ForeignKey(Origin, models.CASCADE)
    unique_field = models.IntegerField(unique=True)
    large_field = models.TextField()

    class Meta:
        app_label = 'auth'


class SecondReferrer(models.Model):
    referrer = models.ForeignKey(Referrer, models.CASCADE)
    other_referrer = models.ForeignKey(
        Referrer, models.CASCADE, to_field='unique_field', related_name='+'
    )

    class Meta:
        app_label = 'auth'


with connection.schema_editor() as se:
    se.create_model(Origin)
    se.create_model(Referrer)
    se.create_model(SecondReferrer)

origin = Origin.objects.create()
Referrer.objects.create(origin=origin, unique_field=1, large_field='x' * 50)

connection.queries_log.clear()
origin.delete()

# Find the SELECT that fetches Referrer rows for cascade.
select_sqls = [q['sql'] for q in connection.queries
               if q['sql'].strip().upper().startswith('SELECT')
               and 'referrer' in q['sql'].lower()
               and 'secondreferrer' not in q['sql'].lower()]
print("Referrer SELECTs:")
for s in select_sqls:
    print("  ", s)

quoted = connection.ops.quote_name('large_field')
loads_large = any(quoted in s for s in select_sqls)
print("large_field loaded in Referrer SELECT:", loads_large)

if not select_sqls:
    print("FAIL: no Referrer SELECT captured")
    raise SystemExit(1)
if loads_large:
    print("FAIL: large_field was loaded (columns not narrowed)")
    raise SystemExit(1)
print("PASS: large_field NOT loaded — columns narrowed to referenced fields")
raise SystemExit(0)
```

Prepatch bug re-encoded as an attack: `True`.

Instance django__django-11087: gold narrows the cascade-fetch queryset via .only(referenced identity columns) unless select_related is in effect or the related model has pre_delete/post_delete listeners.

Probes (all standalone, django configured with sqlite in-memory, app_label='auth' to satisfy the image's INSTALLED_APPS; each exercises one requirement and exits 0 iff it holds):
- probe_1 (Req 1.2/1.3/1.6, POSITIVE CONTROL): deleting an Origin cascading to Referrer(large TextField not referenced by further cascade) must NOT load large_field in the Referrer SELECT. HOLDS patched (SELECT loads only id,unique_field), FAILS at base (loads id,origin_id,unique_field,large_field). Discriminates.
- probe_2 (Req 1.5/2.2/3.5): with pre_delete OR post_delete listener connected for Referrer, large_field MUST be loaded (full fetch). HOLDS patched.
- probe_3 (Req 3.3/3.4): cascade deletes exactly the correct object set (Origin+its Referrer+SecondReferrer gone; unrelated survive). HOLDS patched.
- probe_4 (Req 2.1/2.2/4.1): Collector._has_signal_listeners exists; reports True iff pre/post_delete listeners present, False otherwise; can_fast_delete returns False when such listeners exist. HOLDS patched.
- probe_5 (Req 2.3): m2m_changed-only listener does NOT force full fetch — narrowing still applies. HOLDS patched.
- probe_6 (Req 4.2/4.3/3.1/3.2): simple no-signal FK relation is fast-deletable; empty-relation cascade fine; cascade still deletes leaves. HOLDS patched.

All 6 probes HOLD on the gold-patched tree. Positive control (probe_1) FAILS at base and HOLDS patched — discriminating power confirmed.

Candidate wrong patches (both apply at base_commit; each REJECTED by a distinct probe, proving the suite discriminates):
- weak_nosignal.diff: narrows columns but omits the _has_signal_listeners guard. Passes probe_1 and probe_5 but is REJECTED by probe_2 (pre/post_delete connected yet large_field not loaded) — a listener would observe an incomplete object; would break the FAIL_TO_PASS test's signal subtests.
- weak_m2m.diff: adds the guard but wrongly includes m2m_changed in the narrowing check. Passes probe_1/probe_2 but REJECTED by probe_5 (m2m_changed forces a full fetch, violating Req 2.3).

No requirements-conforming alternative found that would fail the hidden tests. Requirements faithfully and tightly encode the gold behavior. Verdict SOUND.

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
"""Positive control — Requirement 1.2/1.3/1.6.

When deleting an Origin that cascades to Referrer (which has a large TextField
'large_field' that is NOT referenced by any further cascade relation), the
SELECT that fetches Referrer rows must NOT load 'large_field' (only the
referenced identity columns id + unique_field). HOLDS on patched, FAILS at base.
"""
import django
from django.conf import settings

settings.configure(
    DEBUG=True,
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
    INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
    USE_TZ=False,
)
django.setup()

from django.db import models, connection


class Origin(models.Model):
    class Meta:
        app_label = 'auth'


class Referrer(models.Model):
    origin = models.ForeignKey(Origin, models.CASCADE)
    unique_field = models.IntegerField(unique=True)
    large_field = models.TextField()

    class Meta:
        app_label = 'auth'


class SecondReferrer(models.Model):
    referrer = models.ForeignKey(Referrer, models.CASCADE)
    other_referrer = models.ForeignKey(
        Referrer, models.CASCADE, to_field='unique_field', related_name='+'
    )

    class Meta:
        app_label = 'auth'


with connection.schema_editor() as se:
    se.create_model(Origin)
    se.create_model(Referrer)
    se.create_model(SecondReferrer)

origin = Origin.objects.create()
Referrer.objects.create(origin=origin, unique_field=1, large_field='x' * 50)

connection.queries_log.clear()
origin.delete()

# Find the SELECT that fetches Referrer rows for cascade.
select_sqls = [q['sql'] for q in connection.queries
               if q['sql'].strip().upper().startswith('SELECT')
               and 'referrer' in q['sql'].lower()
               and 'secondreferrer' not in q['sql'].lower()]
print("Referrer SELECTs:")
for s in select_sqls:
    print("  ", s)

quoted = connection.ops.quote_name('large_field')
loads_large = any(quoted in s for s in select_sqls)
print("large_field loaded in Referrer SELECT:", loads_large)

if not select_sqls:
    print("FAIL: no Referrer SELECT captured")
    raise SystemExit(1)
if loads_large:
    print("FAIL: large_field was loaded (columns not narrowed)")
    raise SystemExit(1)
print("PASS: large_field NOT loaded — columns narrowed to referenced fields")
raise SystemExit(0)
```

Prepatch bug re-encoded as an attack: `True`.

Instance django__django-11087: gold narrows the cascade-fetch queryset via .only(referenced identity columns) unless select_related is in effect or the related model has pre_delete/post_delete listeners.

Probes (all standalone, django configured with sqlite in-memory, app_label='auth' to satisfy the image's INSTALLED_APPS; each exercises one requirement and exits 0 iff it holds):
- probe_1 (Req 1.2/1.3/1.6, POSITIVE CONTROL): deleting an Origin cascading to Referrer(large TextField not referenced by further cascade) must NOT load large_field in the Referrer SELECT. HOLDS patched (SELECT loads only id,unique_field), FAILS at base (loads id,origin_id,unique_field,large_field). Discriminates.
- probe_2 (Req 1.5/2.2/3.5): with pre_delete OR post_delete listener connected for Referrer, large_field MUST be loaded (full fetch). HOLDS patched.
- probe_3 (Req 3.3/3.4): cascade deletes exactly the correct object set (Origin+its Referrer+SecondReferrer gone; unrelated survive). HOLDS patched.
- probe_4 (Req 2.1/2.2/4.1): Collector._has_signal_listeners exists; reports True iff pre/post_delete listeners present, False otherwise; can_fast_delete returns False when such listeners exist. HOLDS patched.
- probe_5 (Req 2.3): m2m_changed-only listener does NOT force full fetch — narrowing still applies. HOLDS patched.
- probe_6 (Req 4.2/4.3/3.1/3.2): simple no-signal FK relation is fast-deletable; empty-relation cascade fine; cascade still deletes leaves. HOLDS patched.

All 6 probes HOLD on the gold-patched tree. Positive control (probe_1) FAILS at base and HOLDS patched — discriminating power confirmed.

Candidate wrong patches (both apply at base_commit; each REJECTED by a distinct probe, proving the suite discriminates):
- weak_nosignal.diff: narrows columns but omits the _has_signal_listeners guard. Passes probe_1 and probe_5 but is REJECTED by probe_2 (pre/post_delete connected yet large_field not loaded) — a listener would observe an incomplete object; would break the FAIL_TO_PASS test's signal subtests.
- weak_m2m.diff: adds the guard but wrongly includes m2m_changed in the narrowing check. Passes probe_1/probe_2 but REJECTED by probe_5 (m2m_changed forces a full fetch, violating Req 2.3).

No requirements-conforming alternative found that would fail the hidden tests. Requirements faithfully and tightly encode the gold behavior. Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Gold patch: adds _has_signal_listeners helper (pre_delete OR post_delete, dropping m2m_changed from can_fast_delete's guard); in collect() when related objs aren't fast-deletable and no select_related/signal-listeners, narrows sub_objs via .only(referenced target attnames gathered from get_candidate_relations_to_delete). Probes on the instance image: probe.py (fast-delete leaf + post_delete full-fetch + m2m_changed=True + pre_delete=False) HOLDS patched; probe2.py (non-fast-deletable B narrowed to id only) HOLDS patched, VIOLATED at base (base loads payload). All acceptance criteria faithfully reflect the diff and observed behavior. Note R1.2 wording 'select_related is not in effect' correctly maps to sub_objs.query.select_related falsy.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The requirements describe the fix behaviorally without transmitting hidden-test/gold content. No test names/paths/ids (test_only_referenced_fields_selected, delete.tests) appear; no test model/column names (Origin, Referrer, SecondReferrer, unique_field, large_field, to_field='unique_field') appear; no assertion specifics (assertNumQueries(2), the 'id','unique_field' selection) appear. Fix-invented identifiers are paraphrased, not quoted: 'an internal check for deletion-time signal listeners' (not `_has_signal_listeners`), 'candidate cascade relations ... attribute names of foreign related fields ... duplicate column names removed' (behavioral paraphrase of `set(chain.from_iterable(rf.attname for rf in rel.field.foreign_related_fields ...))`, without naming get_candidate_relations_to_delete). The select_related guard and the pre_delete/post_delete-only (excluding m2m_changed) distinctions are behavioral translations of the gold edit, which is the legitimate purpose of the doc; m2m_changed is not covered by any hidden test so no reconstruction occurs. Borderline: Req 4.2 enumerates fast-delete categories (fk, m2m, reverse m2m, qs, large batch, inheritance, self-referential no-update) that map closely onto the PASS_TO_PASS FastDeleteTests method names, and Req 3.4 mirrors OnDeleteTests; however these are documented Django on_delete/fast-delete behavior categories derivable from deletion.py and public docs, framed as 'preserve existing behavior,' and expose no test ids, parametrization values, or invented identifiers. Localization to Collector.collect/can_fast_delete/related_objects in deletion.py is legitimate. Net: behavioral spec, not test transmission.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
