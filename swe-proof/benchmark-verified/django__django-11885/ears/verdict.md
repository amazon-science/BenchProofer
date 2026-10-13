# P2 adversarial audit — django__django-11885

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
"""Probe 1 (POSITIVE CONTROL) — Req1 AC3 + AC2/AC4.
Deleting a Referrer cascades to SecondReferrer through TWO CASCADE FKs
(referrer_id and other_referrer via to_field=unique_field). The combined
fast-delete must issue exactly 2 queries: one combined bulk DELETE for
SecondReferrer + one DELETE for the Referrer itself. Also verifies the
combined DELETE removes rows related through EITHER column (union).
Exits 0 iff exactly 2 queries AND both SecondReferrer rows deleted.
"""
import sys
sys.path.insert(0, '/testbed'); sys.path.insert(0, '/testbed/tests')
import django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True,
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
        INSTALLED_APPS=['django.contrib.contenttypes','django.contrib.auth','delete'],
        USE_TZ=False)
django.setup()
from django.db import connection
from django.apps import apps
with connection.schema_editor() as se:
    for m in apps.get_app_config('delete').get_models():
        try: se.create_model(m)
        except Exception: pass

from delete.models import Origin, Referrer, SecondReferrer

origin = Origin.objects.create()
referer = Referrer.objects.create(origin=origin, unique_field=42)
# Two SecondReferrer rows: one linked via referrer_id, one via other_referrer.
sr1 = SecondReferrer.objects.create(referrer=referer, other_referrer=referer)

from django.test.utils import CaptureQueriesContext
with CaptureQueriesContext(connection) as ctx:
    referer.delete()
_TX = ('BEGIN', 'COMMIT', 'SAVEPOINT', 'RELEASE', 'ROLLBACK')
sqls = [q['sql'] for q in ctx.captured_queries
        if not q['sql'].strip().upper().startswith(_TX)]
n = len(sqls)
remaining = SecondReferrer.objects.count()
combined = any(' OR ' in q for q in sqls)
print("KINDS:", [q.split()[0] for q in sqls])
print("RESULT num_queries=%d remaining=%d combined_OR=%s" % (n, remaining, combined))
ok = (n == 2) and (remaining == 0)
sys.exit(0 if ok else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""Probe 2 — Req2 AC1 & AC3: Collector.related_objects(related_model,
related_fields, objs) returns a queryset matching rows related through ANY
supplied field (OR of <field>__in), and with a single field equals the
single-field lookup. Encodes the new calling convention behaviorally.
Exit 0 iff both hold."""
import sys
sys.path.insert(0, "/testbed"); sys.path.insert(0, "/testbed/tests")
import django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True,
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
        INSTALLED_APPS=["django.contrib.contenttypes","django.contrib.auth","delete"],
        USE_TZ=False)
django.setup()
from django.db import connection
from django.apps import apps
with connection.schema_editor() as se:
    for m in apps.get_app_config("delete").get_models():
        try: se.create_model(m)
        except Exception: pass

from delete.models import Origin, Referrer, SecondReferrer
from django.db.models.deletion import Collector

origin = Origin.objects.create()
r = Referrer.objects.create(origin=origin, unique_field=42)
# a: only referrer_id points to r ; b: only other_referrer points to r
other = Referrer.objects.create(origin=origin, unique_field=99)
a = SecondReferrer.objects.create(referrer=r, other_referrer=other)   # via referrer only
b = SecondReferrer.objects.create(referrer=other, other_referrer=r)   # via other_referrer only

f_ref = SecondReferrer._meta.get_field("referrer")
f_oth = SecondReferrer._meta.get_field("other_referrer")

c = Collector(using=connection.alias)
qs_both = c.related_objects(SecondReferrer, [f_ref, f_oth], [r])
got_both = set(qs_both.values_list("pk", flat=True))
qs_one = c.related_objects(SecondReferrer, [f_ref], [r])
got_one = set(qs_one.values_list("pk", flat=True))

print("OR union pks:", sorted(got_both), "expected:", sorted([a.pk, b.pk]))
print("single-field pks:", sorted(got_one), "expected:", [a.pk])
ok = (got_both == {a.pk, b.pk}) and (got_one == {a.pk})
sys.exit(0 if ok else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""Probe 3 — Req3 AC1-3: get_del_batches(objs, fields) accepts a LIST of
fields, sizes batches from bulk_batch_size(all field names), returns a single
batch when objs fit, and splits into ordered covering batches when they don't.
Exit 0 iff all three hold."""
import sys
sys.path.insert(0, "/testbed"); sys.path.insert(0, "/testbed/tests")
import django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True,
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
        INSTALLED_APPS=["django.contrib.contenttypes","django.contrib.auth","delete"],
        USE_TZ=False)
django.setup()
from django.db import connection
from django.apps import apps
with connection.schema_editor() as se:
    for m in apps.get_app_config("delete").get_models():
        try: se.create_model(m)
        except Exception: pass

from delete.models import SecondReferrer
from django.db.models.deletion import Collector
from django.db import connections

c = Collector(using=connection.alias)
f_ref = SecondReferrer._meta.get_field("referrer")
f_oth = SecondReferrer._meta.get_field("other_referrer")

objs = list(range(10))
# single batch when small
b1 = c.get_del_batches(objs, [f_ref, f_oth])
single_ok = (len(b1) == 1) and (list(b1[0]) == objs)

# force splitting: monkeypatch bulk_batch_size to return 3 for this connection
ops = connections[connection.alias].ops
orig = ops.bulk_batch_size
captured = {}
def fake(fields, o):
    captured["fields"] = list(fields)
    return 3
ops.bulk_batch_size = fake
try:
    b2 = c.get_del_batches(objs, [f_ref, f_oth])
finally:
    ops.bulk_batch_size = orig

flat = [x for batch in b2 for x in batch]
split_ok = (all(len(b) <= 3 for b in b2) and flat == objs and len(b2) == 4)
# batch size computed from ALL supplied field names
names_ok = set(captured.get("fields", [])) == {"referrer", "other_referrer"}

print("single_batch_ok:", single_ok)
print("split covering/order ok:", split_ok, "batches:", [list(b) for b in b2])
print("field_names passed to bulk_batch_size:", captured.get("fields"))
ok = single_ok and split_ok and names_ok
sys.exit(0 if ok else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""Probe 4 — Req1 AC5 & Req4 AC1: a related model reached through ONE
qualifying fast-delete relation still gets exactly one fast-delete; and the
delete() return value (total + per-model breakdown) is exactly correct for a
combined cascade. Uses Referrer->SecondReferrer(2 FKs) scenario and checks the
returned counts.
Exit 0 iff counts correct AND single-relation cascade removes its rows."""
import sys
sys.path.insert(0, "/testbed"); sys.path.insert(0, "/testbed/tests")
import django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True,
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
        INSTALLED_APPS=["django.contrib.contenttypes","django.contrib.auth","delete"],
        USE_TZ=False)
django.setup()
from django.db import connection
from django.apps import apps
with connection.schema_editor() as se:
    for m in apps.get_app_config("delete").get_models():
        try: se.create_model(m)
        except Exception: pass

from delete.models import Origin, Referrer, SecondReferrer

origin = Origin.objects.create()
r = Referrer.objects.create(origin=origin, unique_field=42)
SecondReferrer.objects.create(referrer=r, other_referrer=r)
SecondReferrer.objects.create(referrer=r, other_referrer=r)

total, per_model = r.delete()
print("total:", total, "per_model:", per_model)
# 1 Referrer + 2 SecondReferrer = 3
ok_counts = (total == 3
             and per_model.get("delete.Referrer") == 1
             and per_model.get("delete.SecondReferrer") == 2)

# single-relation fast delete: Origin -> Referrer (one FK 'origin')
o2 = Origin.objects.create()
Referrer.objects.create(origin=o2, unique_field=7)
Referrer.objects.create(origin=o2, unique_field=8)
t2, pm2 = o2.delete()
print("origin delete total:", t2, "per_model:", pm2)
ok_single = (pm2.get("delete.Referrer") == 2 and Referrer.objects.filter(origin_id=o2.pk).count() == 0)

sys.exit(0 if (ok_counts and ok_single) else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""Probe 5 — Req4 AC3 (SET_NULL preserved) + AC2 (DO_NOTHING = no cascade
action). SET_NULL checked via a real delete (MRNull.r = FK(R, SET_NULL)).
DO_NOTHING checked via the Collector directly (RelToBase.base = FK(Base,
DO_NOTHING)): after Collector.collect([base]), the RelToBase model must NOT
appear anywhere in the collector's scheduled work (data, fast_deletes,
field_updates) — i.e. no cascade action taken for that relation.
Exit 0 iff both hold."""
import sys
sys.path.insert(0, "/testbed"); sys.path.insert(0, "/testbed/tests")
import django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True,
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
        INSTALLED_APPS=["django.contrib.contenttypes","django.contrib.auth","delete"],
        USE_TZ=False)
django.setup()
from django.db import connection
from django.apps import apps
with connection.schema_editor() as se:
    for m in apps.get_app_config("delete").get_models():
        try: se.create_model(m)
        except Exception: pass

from delete.models import R, M, MRNull, Base, RelToBase
from django.db.models.deletion import Collector

# SET_NULL via real delete
m = M.objects.create()
r = R.objects.create()
mr = MRNull.objects.create(m=m, r=r)
r.delete()
mr.refresh_from_db()
set_null_ok = (mr.r_id is None)
print("SET_NULL: MRNull.r_id after R.delete() =", mr.r_id, "->", set_null_ok)

# DO_NOTHING via collector inspection
b = Base.objects.create()
rel = RelToBase.objects.create(base=b)
c = Collector(using=connection.alias)
c.collect([b])
scheduled_models = set(c.data.keys())
for qs in c.fast_deletes:
    scheduled_models.add(qs.model)
scheduled_models |= set(c.field_updates.keys())
print("scheduled models after collecting Base:", sorted(mm.__name__ for mm in scheduled_models))
do_nothing_ok = RelToBase not in scheduled_models
print("DO_NOTHING: RelToBase absent from cascade =", do_nothing_ok)

sys.exit(0 if (set_null_ok and do_nothing_ok) else 1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
"""Probe 6 — Req4 AC7 + AC4 (regression, non-combined paths preserved):
(a) AC7: a queryset qualifying for fast deletion as a whole is fast-deleted in a
    single bulk operation: SecondReferrer.objects.all().delete() => 1 DELETE.
(b) AC4: a related model that does NOT qualify for fast deletion still has its
    objects collected and dispatched to its on_delete handler. MRNull.r is
    SET_NULL (non fast-delete cascade path); deleting R must still null it and
    the R row deletion count reflects only R.
Exit 0 iff both hold."""
import sys
sys.path.insert(0, "/testbed"); sys.path.insert(0, "/testbed/tests")
import django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True,
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
        INSTALLED_APPS=["django.contrib.contenttypes","django.contrib.auth","delete"],
        USE_TZ=False)
django.setup()
from django.db import connection
from django.apps import apps
with connection.schema_editor() as se:
    for m in apps.get_app_config("delete").get_models():
        try: se.create_model(m)
        except Exception: pass

from delete.models import R, M, MRNull, Origin, Referrer, SecondReferrer
from django.test.utils import CaptureQueriesContext
_TX = ("BEGIN","COMMIT","SAVEPOINT","RELEASE","ROLLBACK")
def real(ctx):
    return [q["sql"] for q in ctx.captured_queries
            if not q["sql"].strip().upper().startswith(_TX)]

# (a) whole-queryset fast delete = single op
o = Origin.objects.create()
r2 = Referrer.objects.create(origin=o, unique_field=2)
SecondReferrer.objects.create(referrer=r2, other_referrer=r2)
SecondReferrer.objects.create(referrer=r2, other_referrer=r2)
with CaptureQueriesContext(connection) as ctx:
    n = SecondReferrer.objects.all().delete()
q = real(ctx)
print("whole-qs delete kinds:", [x.split()[0] for x in q], "n=", len(q), "ret=", n)
ok_a = (len(q) == 1 and q[0].strip().upper().startswith("DELETE")
        and SecondReferrer.objects.count() == 0)

# (b) non-fast-delete handler path (SET_NULL) still dispatched
m = M.objects.create()
r = R.objects.create()
mr = MRNull.objects.create(m=m, r=r)
total, per = r.delete()
mr.refresh_from_db()
print("R.delete total=", total, "per=", per, "MRNull.r_id=", mr.r_id)
ok_b = (mr.r_id is None and per.get("delete.R") == 1)

sys.exit(0 if (ok_a and ok_b) else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Probe 1 (POSITIVE CONTROL) — Req1 AC3 + AC2/AC4.
Deleting a Referrer cascades to SecondReferrer through TWO CASCADE FKs
(referrer_id and other_referrer via to_field=unique_field). The combined
fast-delete must issue exactly 2 queries: one combined bulk DELETE for
SecondReferrer + one DELETE for the Referrer itself. Also verifies the
combined DELETE removes rows related through EITHER column (union).
Exits 0 iff exactly 2 queries AND both SecondReferrer rows deleted.
"""
import sys
sys.path.insert(0, '/testbed'); sys.path.insert(0, '/testbed/tests')
import django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True,
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
        INSTALLED_APPS=['django.contrib.contenttypes','django.contrib.auth','delete'],
        USE_TZ=False)
django.setup()
from django.db import connection
from django.apps import apps
with connection.schema_editor() as se:
    for m in apps.get_app_config('delete').get_models():
        try: se.create_model(m)
        except Exception: pass

from delete.models import Origin, Referrer, SecondReferrer

origin = Origin.objects.create()
referer = Referrer.objects.create(origin=origin, unique_field=42)
# Two SecondReferrer rows: one linked via referrer_id, one via other_referrer.
sr1 = SecondReferrer.objects.create(referrer=referer, other_referrer=referer)

from django.test.utils import CaptureQueriesContext
with CaptureQueriesContext(connection) as ctx:
    referer.delete()
_TX = ('BEGIN', 'COMMIT', 'SAVEPOINT', 'RELEASE', 'ROLLBACK')
sqls = [q['sql'] for q in ctx.captured_queries
        if not q['sql'].strip().upper().startswith(_TX)]
n = len(sqls)
remaining = SecondReferrer.objects.count()
combined = any(' OR ' in q for q in sqls)
print("KINDS:", [q.split()[0] for q in sqls])
print("RESULT num_queries=%d remaining=%d combined_OR=%s" % (n, remaining, combined))
ok = (n == 2) and (remaining == 0)
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance django__django-11885: combine cascading fast-delete queries that target the same related model into a single DELETE ... WHERE colA IN(...) OR colB IN(...). Scenario models (tests/delete/models.py): deleting a Referrer cascades to SecondReferrer via TWO CASCADE FKs (referrer_id and other_referrer via to_field=unique_field).

### SIX PROBES (all HOLD on gold-patched tree; runner re-runs):
- probe_1.py (POSITIVE CONTROL; Req1 AC2/AC3/AC4): deleting a Referrer that cascades to SecondReferrer through 2 columns issues exactly 2 non-transaction queries (one combined bulk DELETE with an OR of both column lookups + one Referrer delete), and both SecondReferrer rows are removed (union). PATCHED: HOLDS (num_queries=2, combined_OR=True). BASE: VIOLATED (num_queries=3, combined_OR=False). Discriminates.
- probe_2.py (Req2 AC1/AC3): Collector.related_objects(related_model, related_fields, objs) returns rows matching ANY supplied field (OR of <field>__in); single-field case equals that field's __in lookup. PATCHED HOLDS; BASE VIOLATED (TypeError: old 3-arg signature).
- probe_3.py (Req3 AC1/AC2/AC3): get_del_batches(objs, fields) takes a LIST of fields, sizes batches from bulk_batch_size(all field names), returns single batch when small, splits into ordered covering batches when large. PATCHED HOLDS; BASE VIOLATED (AttributeError: list has no .name).
- probe_4.py (Req1 AC5 + Req4 AC1): single-relation cascade still one op; delete() total+per-model counts exactly correct for the combined cascade (3 total; SecondReferrer=2, Referrer=1). Regression criterion: HOLDS on both trees.
- probe_5.py (Req4 AC2/AC3): SET_NULL (MRNull.r) nulls the FK on delete; DO_NOTHING (RelToBase.base) takes NO cascade action (RelToBase absent from collector schedule after collecting Base). Regression: HOLDS on both.
- probe_6.py (Req4 AC7 + AC4): whole-queryset SecondReferrer.objects.all().delete() is a single bulk op (1 query); non-fast-delete SET_NULL handler path still dispatched (R.delete nulls MRNull.r, per-model R=1). Regression: HOLDS on both.

CANDIDATE WRONG-FIX (weak.diff, applies at base_commit, generated via git from a real checkout): adopts the FULL new API surface — new related_objects(related_model, related_fields, objs) OR-predicate, get_del_batches(objs, fields) multi-field sizing, admin utils.py select_related over all fields — but does NOT combine per-column fast-deletes in Collector.collect (schedules one fast_delete per column, as before). This is the lazy reading of the requirements that satisfies Req2/Req3/Req4 verbatim yet fails the core Req1 goal. Result: probes 2,3,4,5,6 HOLD, probe_1 VIOLATED (num_queries=3, combined_OR=False). The suite REJECTS this candidate → discriminating power on wrong implementations confirmed; it would also fail the hidden test test_fast_delete_combined_relationships (assertNumQueries(2)).

All six probes standalone python (stdlib + django only, in-memory sqlite, delete test app), no pytest. Infra: django 3.1, /testbed, py3.6 testbed env. Verdict SOUND: >=5 probes hold on patched, positive control discriminates (fails at base), >=1 requirements-conforming candidate exercised and REJECTED.

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
"""Probe 1 (POSITIVE CONTROL) — Req1 AC3 + AC2/AC4.
Deleting a Referrer cascades to SecondReferrer through TWO CASCADE FKs
(referrer_id and other_referrer via to_field=unique_field). The combined
fast-delete must issue exactly 2 queries: one combined bulk DELETE for
SecondReferrer + one DELETE for the Referrer itself. Also verifies the
combined DELETE removes rows related through EITHER column (union).
Exits 0 iff exactly 2 queries AND both SecondReferrer rows deleted.
"""
import sys
sys.path.insert(0, '/testbed'); sys.path.insert(0, '/testbed/tests')
import django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True,
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
        INSTALLED_APPS=['django.contrib.contenttypes','django.contrib.auth','delete'],
        USE_TZ=False)
django.setup()
from django.db import connection
from django.apps import apps
with connection.schema_editor() as se:
    for m in apps.get_app_config('delete').get_models():
        try: se.create_model(m)
        except Exception: pass

from delete.models import Origin, Referrer, SecondReferrer

origin = Origin.objects.create()
referer = Referrer.objects.create(origin=origin, unique_field=42)
# Two SecondReferrer rows: one linked via referrer_id, one via other_referrer.
sr1 = SecondReferrer.objects.create(referrer=referer, other_referrer=referer)

from django.test.utils import CaptureQueriesContext
with CaptureQueriesContext(connection) as ctx:
    referer.delete()
_TX = ('BEGIN', 'COMMIT', 'SAVEPOINT', 'RELEASE', 'ROLLBACK')
sqls = [q['sql'] for q in ctx.captured_queries
        if not q['sql'].strip().upper().startswith(_TX)]
n = len(sqls)
remaining = SecondReferrer.objects.count()
combined = any(' OR ' in q for q in sqls)
print("KINDS:", [q.split()[0] for q in sqls])
print("RESULT num_queries=%d remaining=%d combined_OR=%s" % (n, remaining, combined))
ok = (n == 2) and (remaining == 0)
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance django__django-11885: combine cascading fast-delete queries that target the same related model into a single DELETE ... WHERE colA IN(...) OR colB IN(...). Scenario models (tests/delete/models.py): deleting a Referrer cascades to SecondReferrer via TWO CASCADE FKs (referrer_id and other_referrer via to_field=unique_field).

### SIX PROBES (all HOLD on gold-patched tree; runner re-runs):
- probe_1.py (POSITIVE CONTROL; Req1 AC2/AC3/AC4): deleting a Referrer that cascades to SecondReferrer through 2 columns issues exactly 2 non-transaction queries (one combined bulk DELETE with an OR of both column lookups + one Referrer delete), and both SecondReferrer rows are removed (union). PATCHED: HOLDS (num_queries=2, combined_OR=True). BASE: VIOLATED (num_queries=3, combined_OR=False). Discriminates.
- probe_2.py (Req2 AC1/AC3): Collector.related_objects(related_model, related_fields, objs) returns rows matching ANY supplied field (OR of <field>__in); single-field case equals that field's __in lookup. PATCHED HOLDS; BASE VIOLATED (TypeError: old 3-arg signature).
- probe_3.py (Req3 AC1/AC2/AC3): get_del_batches(objs, fields) takes a LIST of fields, sizes batches from bulk_batch_size(all field names), returns single batch when small, splits into ordered covering batches when large. PATCHED HOLDS; BASE VIOLATED (AttributeError: list has no .name).
- probe_4.py (Req1 AC5 + Req4 AC1): single-relation cascade still one op; delete() total+per-model counts exactly correct for the combined cascade (3 total; SecondReferrer=2, Referrer=1). Regression criterion: HOLDS on both trees.
- probe_5.py (Req4 AC2/AC3): SET_NULL (MRNull.r) nulls the FK on delete; DO_NOTHING (RelToBase.base) takes NO cascade action (RelToBase absent from collector schedule after collecting Base). Regression: HOLDS on both.
- probe_6.py (Req4 AC7 + AC4): whole-queryset SecondReferrer.objects.all().delete() is a single bulk op (1 query); non-fast-delete SET_NULL handler path still dispatched (R.delete nulls MRNull.r, per-model R=1). Regression: HOLDS on both.

CANDIDATE WRONG-FIX (weak.diff, applies at base_commit, generated via git from a real checkout): adopts the FULL new API surface — new related_objects(related_model, related_fields, objs) OR-predicate, get_del_batches(objs, fields) multi-field sizing, admin utils.py select_related over all fields — but does NOT combine per-column fast-deletes in Collector.collect (schedules one fast_delete per column, as before). This is the lazy reading of the requirements that satisfies Req2/Req3/Req4 verbatim yet fails the core Req1 goal. Result: probes 2,3,4,5,6 HOLD, probe_1 VIOLATED (num_queries=3, combined_OR=False). The suite REJECTS this candidate → discriminating power on wrong implementations confirmed; it would also fail the hidden test test_fast_delete_combined_relationships (assertNumQueries(2)).

All six probes standalone python (stdlib + django only, in-memory sqlite, delete test app), no pytest. Infra: django 3.1, /testbed, py3.6 testbed env. Verdict SOUND: >=5 probes hold on patched, positive control discriminates (fails at base), >=1 requirements-conforming candidate exercised and REJECTED.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Verified each requirement against patch.diff and live probe: Req 2 signature related_objects(related_model, related_fields, objs) with reduce(operator.or_, Q(field__in=objs)) over _base_manager.using(self.using) — matches lines added in deletion.py. Req 3 get_del_batches(objs, fields) computes bulk_batch_size([f.name for f in fields]) — matches. Req 1 grouping via model_fast_deletes=defaultdict(list) keyed by related_model then one combined related_objects/append loop — matches. Admin override Req 2.4 select_related(*[rf.name for rf in related_fields]) — matches utils.py hunk. Req 4 preservation (DO_NOTHING skip, non-fast-delete .only() deferral branch, on_delete dispatch) all retained in patched collect. One minor looseness: Req 1.1 'at most one fast-delete operation per distinct target related model' ignores that get_del_batches may still emit multiple batches per model when object count exceeds bulk_batch_size (each appended separately), but that within-model batching is explicitly the subject of Req 3 and does not misstate the changed observable boundary (one combined OR query per model per batch). This is a faithful description of the change, not a wrong boundary or invented behavior.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** requirements.md localizes the change to real, pre-existing symbols (Collector.collect, related_objects, get_del_batches, django/contrib/admin/utils.py) and describes OR-combining behavior. The illustrative example (entry/created_by_id/updated_by_id, person_friends, 'WHERE ... OR ...') is taken verbatim from the PUBLIC problem_statement, not the hidden tests. None of the hidden-test identifiers leak: Origin/Referrer/SecondReferrer, referrer_id, unique_field, assertNumQueries(2), or test_fast_delete_combined_relationships are absent. No quoted test/gold code and no fix-invented internal identifiers (e.g. model_fast_deletes) are surfaced. Req 1.3's 'exactly two columns -> two queries' echoes the test's assertNumQueries(2) but is a direct behavioral consequence of the public two-column (created_by/updated_by) example rather than a leaked parametrization or model name -- legitimate behavior translation.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
