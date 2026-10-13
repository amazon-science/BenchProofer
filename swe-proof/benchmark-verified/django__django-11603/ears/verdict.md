# P2 adversarial audit — django__django-11603

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
import sys
import django
from django.conf import settings
if not settings.configured:
    settings.configure(
        DEBUG=True,
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
        INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
        USE_TZ=False,
    )
django.setup()
from django.db import models, connection

class Widget(models.Model):
    val = models.IntegerField()
    class Meta:
        app_label = 'auth'

def fill(values):
    with connection.schema_editor() as se:
        se.create_model(Widget)
    for v in values:
        Widget.objects.create(val=v)

from django.db.models import Avg, Sum
ok = True
try:
    a = Avg('val', distinct=True)
    print("Avg(distinct=True) constructed; allow_distinct=", Avg.allow_distinct, "instance.distinct=", a.distinct)
    if not Avg.allow_distinct:
        print("FAIL: Avg.allow_distinct not enabled"); ok = False
except TypeError as e:
    print("FAIL: Avg(distinct=True) raised TypeError:", e); ok = False
try:
    s = Sum('val', distinct=True)
    print("Sum(distinct=True) constructed; allow_distinct=", Sum.allow_distinct, "instance.distinct=", s.distinct)
    if not Sum.allow_distinct:
        print("FAIL: Sum.allow_distinct not enabled"); ok = False
except TypeError as e:
    print("FAIL: Sum(distinct=True) raised TypeError:", e); ok = False
sys.exit(0 if ok else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
import sys
import django
from django.conf import settings
if not settings.configured:
    settings.configure(
        DEBUG=True,
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
        INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
        USE_TZ=False,
    )
django.setup()
from django.db import models, connection

class Widget(models.Model):
    val = models.IntegerField()
    class Meta:
        app_label = 'auth'

def fill(values):
    with connection.schema_editor() as se:
        se.create_model(Widget)
    for v in values:
        Widget.objects.create(val=v)

from django.db.models import Avg
fill([2, 2, 2, 8])
res = Widget.objects.aggregate(x=Avg('val', distinct=True))
print("distinct Avg result:", res)
ann = Widget.objects.annotate(x=Avg('val', distinct=True))
sql, params = ann.query.get_compiler('default').as_sql()
print("SQL:", sql)
ok = True
if abs(res['x'] - 5.0) > 1e-9:
    print("FAIL: distinct Avg expected 5.0, got", res['x']); ok = False
if 'DISTINCT' not in sql.upper():
    print("FAIL: DISTINCT keyword absent from Avg SQL"); ok = False
sys.exit(0 if ok else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
import sys
import django
from django.conf import settings
if not settings.configured:
    settings.configure(
        DEBUG=True,
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
        INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
        USE_TZ=False,
    )
django.setup()
from django.db import models, connection

class Widget(models.Model):
    val = models.IntegerField()
    class Meta:
        app_label = 'auth'

def fill(values):
    with connection.schema_editor() as se:
        se.create_model(Widget)
    for v in values:
        Widget.objects.create(val=v)

from django.db.models import Sum
fill([2, 2, 2, 8])
res = Widget.objects.aggregate(x=Sum('val', distinct=True))
print("distinct Sum result:", res)
ann = Widget.objects.annotate(x=Sum('val', distinct=True))
sql, params = ann.query.get_compiler('default').as_sql()
print("SQL:", sql)
ok = True
if res['x'] != 10:
    print("FAIL: distinct Sum expected 10, got", res['x']); ok = False
if 'DISTINCT' not in sql.upper():
    print("FAIL: DISTINCT keyword absent from Sum SQL"); ok = False
sys.exit(0 if ok else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
import sys
import django
from django.conf import settings
if not settings.configured:
    settings.configure(
        DEBUG=True,
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
        INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
        USE_TZ=False,
    )
django.setup()
from django.db import models, connection

class Widget(models.Model):
    val = models.IntegerField()
    class Meta:
        app_label = 'auth'

def fill(values):
    with connection.schema_editor() as se:
        se.create_model(Widget)
    for v in values:
        Widget.objects.create(val=v)

from django.db.models import Min, Max, StdDev, Variance
from django.db.models.aggregates import Aggregate
ok = True
for cls in (Min, Max, StdDev, Variance):
    try:
        cls('val', distinct=True)
        print("FAIL:", cls.__name__, "did NOT raise on distinct=True"); ok = False
    except TypeError as e:
        msg = str(e)
        print(cls.__name__, "raised TypeError:", msg)
        if cls.__name__ not in msg or 'distinct' not in msg.lower():
            print("FAIL: message does not name class/distinct:", msg); ok = False
if Aggregate.allow_distinct is not False:
    print("FAIL: base Aggregate.allow_distinct not False"); ok = False
else:
    print("base Aggregate.allow_distinct =", Aggregate.allow_distinct)
sys.exit(0 if ok else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
import sys
import django
from django.conf import settings
if not settings.configured:
    settings.configure(
        DEBUG=True,
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
        INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
        USE_TZ=False,
    )
django.setup()
from django.db import models, connection

class Widget(models.Model):
    val = models.IntegerField()
    class Meta:
        app_label = 'auth'

def fill(values):
    with connection.schema_editor() as se:
        se.create_model(Widget)
    for v in values:
        Widget.objects.create(val=v)

from django.db.models import Count
fill([2, 2, 2, 8])
if not Count.allow_distinct:
    print("FAIL: Count.allow_distinct disabled"); sys.exit(1)
res = Widget.objects.aggregate(x=Count('val', distinct=True))
print("distinct Count:", res)
ann = Widget.objects.annotate(x=Count('val', distinct=True))
sql, params = ann.query.get_compiler('default').as_sql()
print("SQL:", sql)
ok = True
if res['x'] != 2:
    print("FAIL: distinct Count expected 2, got", res['x']); ok = False
if 'DISTINCT' not in sql.upper():
    print("FAIL: DISTINCT absent from Count SQL"); ok = False
sys.exit(0 if ok else 1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
import sys
import django
from django.conf import settings
if not settings.configured:
    settings.configure(
        DEBUG=True,
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
        INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
        USE_TZ=False,
    )
django.setup()
from django.db import models, connection

class Widget(models.Model):
    val = models.IntegerField()
    class Meta:
        app_label = 'auth'

def fill(values):
    with connection.schema_editor() as se:
        se.create_model(Widget)
    for v in values:
        Widget.objects.create(val=v)

from django.db.models import Avg, Sum, Count
fill([2, 2, 2, 8])
ok = True
for cls in (Avg, Sum, Count):
    inst = cls('val')
    if inst.distinct is not False:
        print("FAIL:", cls.__name__, "distinct default not False"); ok = False
ann = Widget.objects.annotate(a=Avg('val'), s=Sum('val'), c=Count('val'))
sql, params = ann.query.get_compiler('default').as_sql()
print("non-distinct SQL:", sql)
if 'DISTINCT' in sql.upper():
    print("FAIL: DISTINCT present in non-distinct SQL"); ok = False
res = Widget.objects.aggregate(a=Avg('val'), s=Sum('val'), c=Count('val'))
print("non-distinct results:", res)
if abs(res['a'] - 3.5) > 1e-9 or res['s'] != 14 or res['c'] != 4:
    print("FAIL: non-distinct aggregate values wrong"); ok = False
empty = Widget.objects.aggregate()
print("empty aggregate:", empty)
if empty != {}:
    print("FAIL: empty aggregate not {}"); ok = False
sys.exit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
import sys
import django
from django.conf import settings
if not settings.configured:
    settings.configure(
        DEBUG=True,
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
        INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
        USE_TZ=False,
    )
django.setup()
from django.db import models, connection

class Widget(models.Model):
    val = models.IntegerField()
    class Meta:
        app_label = 'auth'

def fill(values):
    with connection.schema_editor() as se:
        se.create_model(Widget)
    for v in values:
        Widget.objects.create(val=v)

from django.db.models import Avg, Sum
ok = True
try:
    a = Avg('val', distinct=True)
    print("Avg(distinct=True) constructed; allow_distinct=", Avg.allow_distinct, "instance.distinct=", a.distinct)
    if not Avg.allow_distinct:
        print("FAIL: Avg.allow_distinct not enabled"); ok = False
except TypeError as e:
    print("FAIL: Avg(distinct=True) raised TypeError:", e); ok = False
try:
    s = Sum('val', distinct=True)
    print("Sum(distinct=True) constructed; allow_distinct=", Sum.allow_distinct, "instance.distinct=", s.distinct)
    if not Sum.allow_distinct:
        print("FAIL: Sum.allow_distinct not enabled"); ok = False
except TypeError as e:
    print("FAIL: Sum(distinct=True) raised TypeError:", e); ok = False
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Change under test: add allow_distinct=True to Avg and Sum in django/db/models/aggregates.py.

6 probes, all standalone python (django repo pkg only, in-memory sqlite, model on 'auth' app_label to avoid app-registry issues). All HOLD on the gold-patched tree; positive control (probe_1) FAILS at base (discriminating).

Probe->requirement mapping and observed results (patched / base):
- probe_1 (Req1.1/1.4, Req2.1/2.4 — Avg & Sum accept distinct=True and report allow_distinct): patched HOLDS; base VIOLATED (Avg & Sum raise 'does not allow distinct'). POSITIVE CONTROL.
- probe_2 (Req1.2/1.3 — Avg distinct SQL emits DISTINCT and computes distinct mean): patched HOLDS (result {'x':5.0} on {2,2,2,8}, SQL 'AVG(DISTINCT ...)'); base VIOLATED (TypeError).
- probe_3 (Req2.2/2.3 — Sum distinct SQL emits DISTINCT, distinct sum=10): patched HOLDS; base VIOLATED (TypeError).
- probe_4 (Req4.1/4.2/4.3 — Min/Max/StdDev/Variance still reject distinct with class-named message; base Aggregate.allow_distinct is False): patched HOLDS.
- probe_5 (Req3 regression — Count still permits distinct, COUNT(DISTINCT) SQL, distinct count=2): patched HOLDS; base HOLDS (unchanged, as expected).
- probe_6 (Req5 non-distinct unchanged + Req6 empty aggregate — defaults distinct=False, no DISTINCT in plain SQL, all-values avg=3.5/sum=14/count=4, aggregate()=={}): patched HOLDS.

Candidate wrong-fix patches, both REJECTED by the suite (demonstrates discrimination):
- weak_partial.diff (lazy/partial fix: only Avg gets allow_distinct, Sum forgotten): REJECTED — probe_1 fails (Sum raises TypeError) and probe_3 fails (Sum distinct query errors). This is exactly the too-narrow reading Req2 forbids.
- weak_broad.diff (over-broad fix: set allow_distinct=True on base Aggregate): REJECTED — probe_4 fails because Min/Max/StdDev/Variance and base Aggregate would then wrongly accept distinct=True, violating Req4.

No probe fails on the patched tree; no requirements-conforming alternative patch was found that fails the hidden tests. Requirements are faithful (not too strong) and the suite rejects both the too-narrow and too-broad readings (not too weak). Verdict SOUND.

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
import sys
import django
from django.conf import settings
if not settings.configured:
    settings.configure(
        DEBUG=True,
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
        INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
        USE_TZ=False,
    )
django.setup()
from django.db import models, connection

class Widget(models.Model):
    val = models.IntegerField()
    class Meta:
        app_label = 'auth'

def fill(values):
    with connection.schema_editor() as se:
        se.create_model(Widget)
    for v in values:
        Widget.objects.create(val=v)

from django.db.models import Avg, Sum
ok = True
try:
    a = Avg('val', distinct=True)
    print("Avg(distinct=True) constructed; allow_distinct=", Avg.allow_distinct, "instance.distinct=", a.distinct)
    if not Avg.allow_distinct:
        print("FAIL: Avg.allow_distinct not enabled"); ok = False
except TypeError as e:
    print("FAIL: Avg(distinct=True) raised TypeError:", e); ok = False
try:
    s = Sum('val', distinct=True)
    print("Sum(distinct=True) constructed; allow_distinct=", Sum.allow_distinct, "instance.distinct=", s.distinct)
    if not Sum.allow_distinct:
        print("FAIL: Sum.allow_distinct not enabled"); ok = False
except TypeError as e:
    print("FAIL: Sum(distinct=True) raised TypeError:", e); ok = False
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Change under test: add allow_distinct=True to Avg and Sum in django/db/models/aggregates.py.

6 probes, all standalone python (django repo pkg only, in-memory sqlite, model on 'auth' app_label to avoid app-registry issues). All HOLD on the gold-patched tree; positive control (probe_1) FAILS at base (discriminating).

Probe->requirement mapping and observed results (patched / base):
- probe_1 (Req1.1/1.4, Req2.1/2.4 — Avg & Sum accept distinct=True and report allow_distinct): patched HOLDS; base VIOLATED (Avg & Sum raise 'does not allow distinct'). POSITIVE CONTROL.
- probe_2 (Req1.2/1.3 — Avg distinct SQL emits DISTINCT and computes distinct mean): patched HOLDS (result {'x':5.0} on {2,2,2,8}, SQL 'AVG(DISTINCT ...)'); base VIOLATED (TypeError).
- probe_3 (Req2.2/2.3 — Sum distinct SQL emits DISTINCT, distinct sum=10): patched HOLDS; base VIOLATED (TypeError).
- probe_4 (Req4.1/4.2/4.3 — Min/Max/StdDev/Variance still reject distinct with class-named message; base Aggregate.allow_distinct is False): patched HOLDS.
- probe_5 (Req3 regression — Count still permits distinct, COUNT(DISTINCT) SQL, distinct count=2): patched HOLDS; base HOLDS (unchanged, as expected).
- probe_6 (Req5 non-distinct unchanged + Req6 empty aggregate — defaults distinct=False, no DISTINCT in plain SQL, all-values avg=3.5/sum=14/count=4, aggregate()=={}): patched HOLDS.

Candidate wrong-fix patches, both REJECTED by the suite (demonstrates discrimination):
- weak_partial.diff (lazy/partial fix: only Avg gets allow_distinct, Sum forgotten): REJECTED — probe_1 fails (Sum raises TypeError) and probe_3 fails (Sum distinct query errors). This is exactly the too-narrow reading Req2 forbids.
- weak_broad.diff (over-broad fix: set allow_distinct=True on base Aggregate): REJECTED — probe_4 fails because Min/Max/StdDev/Variance and base Aggregate would then wrongly accept distinct=True, violating Req4.

No probe fails on the patched tree; no requirements-conforming alternative patch was found that fails the hidden tests. Requirements are faithful (not too strong) and the suite rejects both the too-narrow and too-broad readings (not too weak). Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Gold patch adds `allow_distinct = True` to Avg and Sum only. Probes on the patched tree confirm: R1/R2 — Avg('x',distinct=True) and Sum('x',distinct=True) construct without TypeError, and as_sql emits AVG(DISTINCT ...) / SUM(DISTINCT ...); Avg.allow_distinct=True, Sum.allow_distinct=True. R3 — Count.allow_distinct=True, COUNT(DISTINCT ...) still works. R4 — Min/Max/StdDev/Variance and base Aggregate all raise TypeError 'X does not allow distinct'; Aggregate.allow_distinct=False (default). R5 — no DISTINCT emitted without the flag (AVG("...")); distinct defaults False. R6 — empty aggregate() returns {} (matches FAIL_TO_PASS test_empty_aggregate). Boundary is correct: requirements pin the observable allow_distinct policy change and SQL rendering, which is exactly what the patch changes, not a narrow branch/helper.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The document describes behavior without transmitting the hidden tests. The test's discriminating magic constants (Avg=4.125, Sum=16.5, Count=4) never appear; distinct aggregation is described generically ('arithmetic mean of the set of distinct values', 'total of the set of distinct values'). No test names/paths/ids (test_distinct_on_aggregate, test_empty_aggregate, AggregateTestCase), no quoted test/gold code. The 'allow_distinct' distinct-policy attribute is already named in the public problem_statement ('setting these classes as allowing DISTINCT'), so it is not fix-invented. The class enumeration (Avg/Sum/Count permit; Min/Max/StdDev/Variance/Aggregate reject) is derivable from the public class hierarchy and problem_statement, not the test parametrization. Requirement 6 (empty aggregate()->{}) maps to the FAIL_TO_PASS test_empty_aggregate which is absent from the problem_statement, but it is stated as a legitimate behavioral requirement, not as test code/ids — behavioral translation is exactly what the spec is for. No case enumeration mirrors the (Avg,Count,Sum)+expected-value tuples.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
