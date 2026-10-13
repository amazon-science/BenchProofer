# P2 adversarial audit — django__django-13363

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 6 requirement probes hold on the patched tree; 1/2 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 6 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 6 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 2 alternative candidate patches, claimed to satisfy every cited requirement, and ran the same suite against them. The suite rejected 1 of the 2: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. The other 1 was not rejected by the suite. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (6):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
"""Req1.1-3 / Req2.1-3 positive control: TruncDate & TruncTime honor explicit tzinfo.
Under USE_TZ, an explicit tzinfo produces the calendar date / wall-clock time of the
stored instant AS OBSERVED IN THAT ZONE, and two different zones yield different results.
Exit 0 iff behavior holds."""
import django
from django.conf import settings
settings.configure(
    DEBUG=True,
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
    INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth', 'testapp'],
    USE_TZ=True, TIME_ZONE='UTC',
)
import sys, types
app = types.ModuleType('testapp'); app.__path__=['/tmp']
sys.modules['testapp']=app
django.setup()
from django.db import models, connection
class DTModel(models.Model):
    start_datetime = models.DateTimeField(null=True)
    class Meta: app_label='testapp'
with connection.schema_editor() as se:
    se.create_model(DTModel)
import pytz, datetime
from django.db.models.functions import TruncDate, TruncTime, TruncYear
melb = pytz.timezone('Australia/Melbourne')
pacific = pytz.timezone('US/Pacific')
# instant chosen so calendar date differs across zones
start = pytz.utc.localize(datetime.datetime(2016, 1, 1, 1, 30, 50, 321))
DTModel.objects.create(start_datetime=start)
row = DTModel.objects.annotate(
    md=TruncDate('start_datetime', tzinfo=melb),
    pd=TruncDate('start_datetime', tzinfo=pacific),
    mt=TruncTime('start_datetime', tzinfo=melb),
    pt=TruncTime('start_datetime', tzinfo=pacific),
).get()
melb_dt = start.astimezone(melb); pac_dt = start.astimezone(pacific)
print("melb date", row.md, "expect", melb_dt.date())
print("pac  date", row.pd, "expect", pac_dt.date())
print("melb time", row.mt, "expect", melb_dt.time())
print("pac  time", row.pt, "expect", pac_dt.time())
ok = (row.md==melb_dt.date() and row.pd==pac_dt.date()
      and row.mt==melb_dt.time() and row.pt==pac_dt.time())
diff = (row.md != row.pd) and (row.mt != row.pt)
print("dates differ / times differ:", row.md!=row.pd, row.mt!=row.pt)
sys.exit(0 if (ok and diff) else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""Req1.4 & 2.4: with USE_TZ and NO explicit tzinfo, TruncDate/TruncTime use the
ambient (current) timezone -> preserves prior default behavior. Set TIME_ZONE to a
non-UTC zone and check the result matches ambient conversion. Exit 0 iff holds."""
import django, sys, types, datetime, pytz
from django.conf import settings
settings.configure(DEBUG=True,
    DATABASES={'default':{'ENGINE':'django.db.backends.sqlite3','NAME':':memory:'}},
    INSTALLED_APPS=['django.contrib.contenttypes','django.contrib.auth','testapp'],
    USE_TZ=True, TIME_ZONE='US/Pacific')
app=types.ModuleType('testapp'); app.__path__=['/tmp']; sys.modules['testapp']=app
django.setup()
from django.db import models, connection
class DTModel(models.Model):
    start_datetime=models.DateTimeField(null=True)
    class Meta: app_label='testapp'
with connection.schema_editor() as se: se.create_model(DTModel)
from django.db.models.functions import TruncDate, TruncTime
from django.utils import timezone as djtz
start=pytz.utc.localize(datetime.datetime(2016,1,1,1,30,50,321))
DTModel.objects.create(start_datetime=start)
row=DTModel.objects.annotate(d=TruncDate('start_datetime'), t=TruncTime('start_datetime')).get()
amb=pytz.timezone('US/Pacific'); adt=start.astimezone(amb)
print("ambient date",row.d,"expect",adt.date())
print("ambient time",row.t,"expect",adt.time())
sys.exit(0 if (row.d==adt.date() and row.t==adt.time()) else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""Req1.5 & 2.5: USE_TZ disabled -> null zone passed regardless of tzinfo; TruncDate/
TruncTime still produce the naive stored date/time. Also checks tzname resolves to None.
Exit 0 iff holds."""
import django, sys, types, datetime, pytz
from django.conf import settings
settings.configure(DEBUG=True,
    DATABASES={'default':{'ENGINE':'django.db.backends.sqlite3','NAME':':memory:'}},
    INSTALLED_APPS=['django.contrib.contenttypes','django.contrib.auth','testapp'],
    USE_TZ=False, TIME_ZONE='UTC')
app=types.ModuleType('testapp'); app.__path__=['/tmp']; sys.modules['testapp']=app
django.setup()
from django.db import models, connection
class DTModel(models.Model):
    start_datetime=models.DateTimeField(null=True)
    class Meta: app_label='testapp'
with connection.schema_editor() as se: se.create_model(DTModel)
from django.db.models.functions import TruncDate, TruncTime
melb=pytz.timezone('Australia/Melbourne')
start=datetime.datetime(2016,1,1,1,30,50,321)  # naive
DTModel.objects.create(start_datetime=start)
# even with an explicit tzinfo, USE_TZ off => null zone => naive value unchanged
td=TruncDate('start_datetime', tzinfo=melb); tt=TruncTime('start_datetime', tzinfo=melb)
print("td.get_tzname()", td.get_tzname(), "tt.get_tzname()", tt.get_tzname())
row=DTModel.objects.annotate(d=td, t=tt).get()
print("date",row.d,"expect",start.date(),"time",row.t,"expect",start.time())
ok = (td.get_tzname() is None and tt.get_tzname() is None
      and row.d==start.date() and row.t==start.time())
sys.exit(0 if ok else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""Req4.2: null input -> TruncDate/TruncTime yield null. Exit 0 iff holds."""
import django, sys, types, datetime, pytz
from django.conf import settings
settings.configure(DEBUG=True,
    DATABASES={'default':{'ENGINE':'django.db.backends.sqlite3','NAME':':memory:'}},
    INSTALLED_APPS=['django.contrib.contenttypes','django.contrib.auth','testapp'],
    USE_TZ=True, TIME_ZONE='UTC')
app=types.ModuleType('testapp'); app.__path__=['/tmp']; sys.modules['testapp']=app
django.setup()
from django.db import models, connection
class DTModel(models.Model):
    start_datetime=models.DateTimeField(null=True)
    class Meta: app_label='testapp'
with connection.schema_editor() as se: se.create_model(DTModel)
from django.db.models.functions import TruncDate, TruncTime
melb=pytz.timezone('Australia/Melbourne')
DTModel.objects.create(start_datetime=None)
row=DTModel.objects.annotate(d=TruncDate('start_datetime', tzinfo=melb),
                             t=TruncTime('start_datetime', tzinfo=melb)).get()
print("date",row.d,"time",row.t)
sys.exit(0 if (row.d is None and row.t is None) else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""Req3.2: an explicit tzinfo applied to a datetime-output truncation (TruncYear) and to
TruncDate/TruncTime over the same instant apply the SAME supplied zone. Check TruncDate's
result equals TruncYear(tz).date-consistent zone, i.e. date matches the same-zone instant.
Exit 0 iff both TruncYear.year and TruncDate reflect the pacific zone (2015 / 2015-12-31)."""
import django, sys, types, datetime, pytz
from django.conf import settings
settings.configure(DEBUG=True,
    DATABASES={'default':{'ENGINE':'django.db.backends.sqlite3','NAME':':memory:'}},
    INSTALLED_APPS=['django.contrib.contenttypes','django.contrib.auth','testapp'],
    USE_TZ=True, TIME_ZONE='UTC')
app=types.ModuleType('testapp'); app.__path__=['/tmp']; sys.modules['testapp']=app
django.setup()
from django.db import models, connection
class DTModel(models.Model):
    start_datetime=models.DateTimeField(null=True)
    class Meta: app_label='testapp'
with connection.schema_editor() as se: se.create_model(DTModel)
from django.db.models.functions import TruncDate, TruncTime, TruncYear
pacific=pytz.timezone('US/Pacific')
start=pytz.utc.localize(datetime.datetime(2016,1,1,1,30,50,321))
DTModel.objects.create(start_datetime=start)
row=DTModel.objects.annotate(y=TruncYear('start_datetime', tzinfo=pacific),
                             d=TruncDate('start_datetime', tzinfo=pacific),
                             t=TruncTime('start_datetime', tzinfo=pacific)).get()
pdt=start.astimezone(pacific)
print("year",row.y.year,"expect 2015 ; date",row.d,"expect",pdt.date(),"time",row.t,"expect",pdt.time())
ok = (row.y.year==2015 and row.d==pdt.date() and row.t==pdt.time())
sys.exit(0 if ok else 1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
"""Req4.6: invalid input/output field combos still rejected. TruncTime over a DateField
(no time component) must raise ValueError at query time, as before. Exit 0 iff it raises."""
import django, sys, types, datetime
from django.conf import settings
settings.configure(DEBUG=True,
    DATABASES={'default':{'ENGINE':'django.db.backends.sqlite3','NAME':':memory:'}},
    INSTALLED_APPS=['django.contrib.contenttypes','django.contrib.auth','testapp'],
    USE_TZ=True, TIME_ZONE='UTC')
app=types.ModuleType('testapp'); app.__path__=['/tmp']; sys.modules['testapp']=app
django.setup()
from django.db import models, connection
class DModel(models.Model):
    start_date=models.DateField(null=True)
    class Meta: app_label='testapp'
with connection.schema_editor() as se: se.create_model(DModel)
from django.db.models.functions import TruncTime
DModel.objects.create(start_date=datetime.date(2016,1,1))
try:
    list(DModel.objects.annotate(t=TruncTime('start_date')))
    print("NO ERROR raised - regression")
    sys.exit(1)
except ValueError as e:
    print("raised ValueError:", e)
    sys.exit(0)
except Exception as e:
    print("raised other:", type(e).__name__, e)
    sys.exit(1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Req1.1-3 / Req2.1-3 positive control: TruncDate & TruncTime honor explicit tzinfo.
Under USE_TZ, an explicit tzinfo produces the calendar date / wall-clock time of the
stored instant AS OBSERVED IN THAT ZONE, and two different zones yield different results.
Exit 0 iff behavior holds."""
import django
from django.conf import settings
settings.configure(
    DEBUG=True,
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
    INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth', 'testapp'],
    USE_TZ=True, TIME_ZONE='UTC',
)
import sys, types
app = types.ModuleType('testapp'); app.__path__=['/tmp']
sys.modules['testapp']=app
django.setup()
from django.db import models, connection
class DTModel(models.Model):
    start_datetime = models.DateTimeField(null=True)
    class Meta: app_label='testapp'
with connection.schema_editor() as se:
    se.create_model(DTModel)
import pytz, datetime
from django.db.models.functions import TruncDate, TruncTime, TruncYear
melb = pytz.timezone('Australia/Melbourne')
pacific = pytz.timezone('US/Pacific')
# instant chosen so calendar date differs across zones
start = pytz.utc.localize(datetime.datetime(2016, 1, 1, 1, 30, 50, 321))
DTModel.objects.create(start_datetime=start)
row = DTModel.objects.annotate(
    md=TruncDate('start_datetime', tzinfo=melb),
    pd=TruncDate('start_datetime', tzinfo=pacific),
    mt=TruncTime('start_datetime', tzinfo=melb),
    pt=TruncTime('start_datetime', tzinfo=pacific),
).get()
melb_dt = start.astimezone(melb); pac_dt = start.astimezone(pacific)
print("melb date", row.md, "expect", melb_dt.date())
print("pac  date", row.pd, "expect", pac_dt.date())
print("melb time", row.mt, "expect", melb_dt.time())
print("pac  time", row.pt, "expect", pac_dt.time())
ok = (row.md==melb_dt.date() and row.pd==pac_dt.date()
      and row.mt==melb_dt.time() and row.pt==pac_dt.time())
diff = (row.md != row.pd) and (row.mt != row.pt)
print("dates differ / times differ:", row.md!=row.pd, row.mt!=row.pt)
sys.exit(0 if (ok and diff) else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Bundle mandates that TruncDate/TruncTime resolve their conversion zone via TimezoneMixin.get_tzname() so an explicit tzinfo is honored under USE_TZ, while preserving ambient-default, USE_TZ-off (null zone), null-input, cross-family consistency (TruncYear), and invalid-combo-rejection behavior.

Probes (all self-contained; settings.configure + in-memory sqlite + synthetic 'testapp' with __path__=['/tmp']; run in the official image):
- probe_1 (Req1.1-3/Req2.1-3, POSITIVE CONTROL): explicit tzinfo (Melbourne vs US/Pacific) over instant 2016-01-01 01:30:50 UTC. Patched: melb_date=2016-01-01, pac_date=2015-12-31, melb_time=12:30:50, pac_time=17:30:50, all matching astimezone; dates & times differ across zones. HOLDS patched, VIOLATED at base (base ignores tzinfo -> both zones give ambient 2016-01-01 / 01:30:50). Discriminates.
- probe_2 (Req1.4/2.4): USE_TZ on, no tzinfo, TIME_ZONE=US/Pacific -> ambient conversion (2015-12-31). HOLDS.
- probe_3 (Req1.5/2.5): USE_TZ off -> get_tzname() is None for both even with tzinfo=melb; naive stored value unchanged. HOLDS.
- probe_4 (Req4.2): null input -> both yield None. HOLDS.
- probe_5 (Req3.2): explicit US/Pacific applied to TruncYear AND TruncDate/TruncTime over same instant -> year 2015, date 2015-12-31, time 17:30:50 (same zone everywhere). HOLDS.
- probe_6 (Req4.6): TruncTime over a DateField raises ValueError 'Cannot truncate DateField to TimeField'. HOLDS.

Candidate patches:
- weak_partial: applies get_tzname() to TruncDate only, leaves TruncTime as the buggy get_current_timezone_name(). REJECTED by probe_1 (pac_time wrong) and probe_5 (time=01:30:50 not 17:30:50). Demonstrates the suite discriminates a partial/wrong fix.
- weak_nousetz: inlines the get_tzname policy explicitly (tzinfo precedence, USE_TZ gating) in both as_sql methods. Passes ALL probes -- this is a functionally-equivalent CORRECT fix, not a too-weak alternative (it will resolve the hidden tests), so it is NOT reported as a weakness.

Verdict SOUND: 6 distinct probes cover all four requirements' behavioral SHALLs, boundary cases, and 'SHALL keep' regressions; positive control HOLDS patched / FAILS at base; >=1 requirements-inadequate candidate (weak_partial) is REJECTED by the suite.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 requirement probes hold on the patched tree; 1/2 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 6 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 6 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 2 alternative candidate patches, claimed to satisfy every cited requirement, and ran the same suite against them. The suite rejected 1 of the 2: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. The other 1 was not rejected by the suite. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

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
"""Req1.1-3 / Req2.1-3 positive control: TruncDate & TruncTime honor explicit tzinfo.
Under USE_TZ, an explicit tzinfo produces the calendar date / wall-clock time of the
stored instant AS OBSERVED IN THAT ZONE, and two different zones yield different results.
Exit 0 iff behavior holds."""
import django
from django.conf import settings
settings.configure(
    DEBUG=True,
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
    INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth', 'testapp'],
    USE_TZ=True, TIME_ZONE='UTC',
)
import sys, types
app = types.ModuleType('testapp'); app.__path__=['/tmp']
sys.modules['testapp']=app
django.setup()
from django.db import models, connection
class DTModel(models.Model):
    start_datetime = models.DateTimeField(null=True)
    class Meta: app_label='testapp'
with connection.schema_editor() as se:
    se.create_model(DTModel)
import pytz, datetime
from django.db.models.functions import TruncDate, TruncTime, TruncYear
melb = pytz.timezone('Australia/Melbourne')
pacific = pytz.timezone('US/Pacific')
# instant chosen so calendar date differs across zones
start = pytz.utc.localize(datetime.datetime(2016, 1, 1, 1, 30, 50, 321))
DTModel.objects.create(start_datetime=start)
row = DTModel.objects.annotate(
    md=TruncDate('start_datetime', tzinfo=melb),
    pd=TruncDate('start_datetime', tzinfo=pacific),
    mt=TruncTime('start_datetime', tzinfo=melb),
    pt=TruncTime('start_datetime', tzinfo=pacific),
).get()
melb_dt = start.astimezone(melb); pac_dt = start.astimezone(pacific)
print("melb date", row.md, "expect", melb_dt.date())
print("pac  date", row.pd, "expect", pac_dt.date())
print("melb time", row.mt, "expect", melb_dt.time())
print("pac  time", row.pt, "expect", pac_dt.time())
ok = (row.md==melb_dt.date() and row.pd==pac_dt.date()
      and row.mt==melb_dt.time() and row.pt==pac_dt.time())
diff = (row.md != row.pd) and (row.mt != row.pt)
print("dates differ / times differ:", row.md!=row.pd, row.mt!=row.pt)
sys.exit(0 if (ok and diff) else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Bundle mandates that TruncDate/TruncTime resolve their conversion zone via TimezoneMixin.get_tzname() so an explicit tzinfo is honored under USE_TZ, while preserving ambient-default, USE_TZ-off (null zone), null-input, cross-family consistency (TruncYear), and invalid-combo-rejection behavior.

Probes (all self-contained; settings.configure + in-memory sqlite + synthetic 'testapp' with __path__=['/tmp']; run in the official image):
- probe_1 (Req1.1-3/Req2.1-3, POSITIVE CONTROL): explicit tzinfo (Melbourne vs US/Pacific) over instant 2016-01-01 01:30:50 UTC. Patched: melb_date=2016-01-01, pac_date=2015-12-31, melb_time=12:30:50, pac_time=17:30:50, all matching astimezone; dates & times differ across zones. HOLDS patched, VIOLATED at base (base ignores tzinfo -> both zones give ambient 2016-01-01 / 01:30:50). Discriminates.
- probe_2 (Req1.4/2.4): USE_TZ on, no tzinfo, TIME_ZONE=US/Pacific -> ambient conversion (2015-12-31). HOLDS.
- probe_3 (Req1.5/2.5): USE_TZ off -> get_tzname() is None for both even with tzinfo=melb; naive stored value unchanged. HOLDS.
- probe_4 (Req4.2): null input -> both yield None. HOLDS.
- probe_5 (Req3.2): explicit US/Pacific applied to TruncYear AND TruncDate/TruncTime over same instant -> year 2015, date 2015-12-31, time 17:30:50 (same zone everywhere). HOLDS.
- probe_6 (Req4.6): TruncTime over a DateField raises ValueError 'Cannot truncate DateField to TimeField'. HOLDS.

Candidate patches:
- weak_partial: applies get_tzname() to TruncDate only, leaves TruncTime as the buggy get_current_timezone_name(). REJECTED by probe_1 (pac_time wrong) and probe_5 (time=01:30:50 not 17:30:50). Demonstrates the suite discriminates a partial/wrong fix.
- weak_nousetz: inlines the get_tzname policy explicitly (tzinfo precedence, USE_TZ gating) in both as_sql methods. Passes ALL probes -- this is a functionally-equivalent CORRECT fix, not a too-weak alternative (it will resolve the hidden tests), so it is NOT reported as a weakness.

Verdict SOUND: 6 distinct probes cover all four requirements' behavioral SHALLs, boundary cases, and 'SHALL keep' regressions; positive control HOLDS patched / FAILS at base; >=1 requirements-inadequate candidate (weak_partial) is REJECTED by the suite.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Modeling boundary is correct: requirements pin the observable zone-selection change for BOTH TruncDate and TruncTime (not a narrow single-branch slice), including the null/ambient/explicit cases and the invariance of the inner expression compilation. No mandated behavior the code lacks, no forbidden behavior it has, no invented behavior. Probes: probe.py (patched) exit 0 = ALL OK; probe_base.py --base VIOLATED as expected (base not using get_tzname).


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The requirements describe the fix behaviorally without transmitting hidden-test or gold content beyond the public problem_statement. All named symbols are either explicitly public in the problem_statement (TruncDate, TruncTime, TruncBase, TimezoneMixin, get_current_timezone_name, tzinfo, django/db/models/functions/datetime.py, the aggregate-by-date use case, and the 'expected method' get_tzname linked at datetime.py#L17) or pre-existing codebase identifiers used for legitimate localization (get_tzname, datetime_cast_date_sql, datetime_cast_time_sql — none are fix-invented; the gold patch invents no identifiers, it only swaps a conditional for self.get_tzname()). No test names/paths/class names (test_extract_trunc.py, DateFunctionWithTimeZoneTests, test_trunc_timezone_applied_before_truncation), no parametrization ids, no quoted test/gold lines, and no melbourne/pacific two-zone case structure appear. Req 3.2's 'e.g. TruncYear' is a public documented function, and the two-different-timezones-differ criteria (1.3/2.3) are behavioral statements, not a mirror of the specific test's astimezone(tz).date()/.time() assertions. Req 4.1's enumeration of trunc/extract units is the standard public API family (regression preservation), not a reconstruction of the PASS_TO_PASS list. This is behavioral translation of what the tests check — the intended purpose — not transmission of the tests themselves.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
