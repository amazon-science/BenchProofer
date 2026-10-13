# P2 adversarial audit — django__django-14170

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 7 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 7 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py`, `probe_7.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_4.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (7):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
"""R1.1 & R1.2: ISO-year bounds for a DATE column.

lower == date.fromisocalendar(value,1,1)
upper == date.fromisocalendar(value+1,1,1) - 1 day
Also positive control: base has no iso_year kwarg -> TypeError -> fails.
"""
import datetime
import django
from django.conf import settings

if not settings.configured:
    settings.configure(
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
        INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
        USE_TZ=False,
    )
django.setup()

from django.db import connection

value = 2020
bounds = connection.ops.year_lookup_bounds_for_date_field(value, iso_year=True)
print("bounds:", bounds)

exp_lower = connection.ops.adapt_datefield_value(datetime.date.fromisocalendar(value, 1, 1))
exp_upper = connection.ops.adapt_datefield_value(
    datetime.date.fromisocalendar(value + 1, 1, 1) - datetime.timedelta(days=1)
)
print("expected lower:", exp_lower, "expected upper:", exp_upper)

ok = (list(bounds) == [exp_lower, exp_upper])
# extra: iso week1 of 2020 begins 2019-12-30
print("raw fromisocalendar lower:", datetime.date.fromisocalendar(2020, 1, 1))
if not ok:
    print("MISMATCH")
    raise SystemExit(1)
print("OK")
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""R2.1 & R2.2: ISO-year bounds for a DATETIME column (USE_TZ=False).

lower == datetime.fromisocalendar(value,1,1)
upper == datetime.fromisocalendar(value+1,1,1) - 1 microsecond
"""
import datetime
import django
from django.conf import settings

if not settings.configured:
    settings.configure(
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
        INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
        USE_TZ=False,
    )
django.setup()

from django.db import connection

value = 2020
bounds = connection.ops.year_lookup_bounds_for_datetime_field(value, iso_year=True)
print("bounds:", bounds)

exp_lower = connection.ops.adapt_datetimefield_value(
    datetime.datetime.fromisocalendar(value, 1, 1)
)
exp_upper = connection.ops.adapt_datetimefield_value(
    datetime.datetime.fromisocalendar(value + 1, 1, 1) - datetime.timedelta(microseconds=1)
)
print("expected lower:", exp_lower, "expected upper:", exp_upper)

if list(bounds) != [exp_lower, exp_upper]:
    print("MISMATCH")
    raise SystemExit(1)
print("OK")
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""R2.3: WHILE USE_TZ active, ISO-year datetime bounds SHALL be tz-aware in
current timezone (like calendar-year bounds). Check tzinfo present and values
equal make_aware(naive) for both calendar and iso modes.
"""
import datetime
import django
from django.conf import settings

if not settings.configured:
    settings.configure(
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
        INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
        USE_TZ=True,
        TIME_ZONE="America/New_York",
    )
django.setup()

from django.db import connection
from django.utils import timezone

value = 2020
tz = timezone.get_current_timezone()

# iso bounds
iso = connection.ops.year_lookup_bounds_for_datetime_field(value, iso_year=True)
print("iso bounds:", iso)

naive_lower = datetime.datetime.fromisocalendar(value, 1, 1)
naive_upper = datetime.datetime.fromisocalendar(value + 1, 1, 1) - datetime.timedelta(microseconds=1)
exp_lower = connection.ops.adapt_datetimefield_value(timezone.make_aware(naive_lower, tz))
exp_upper = connection.ops.adapt_datetimefield_value(timezone.make_aware(naive_upper, tz))
print("expected:", [exp_lower, exp_upper])

if list(iso) != [exp_lower, exp_upper]:
    print("MISMATCH iso tz-aware")
    raise SystemExit(1)

# sanity: calendar path also tz-aware (regression baseline)
cal = connection.ops.year_lookup_bounds_for_datetime_field(value)
cnl = connection.ops.adapt_datetimefield_value(timezone.make_aware(datetime.datetime(value,1,1), tz))
cnu = connection.ops.adapt_datetimefield_value(timezone.make_aware(datetime.datetime(value,12,31,23,59,59,999999), tz))
if list(cal) != [cnl, cnu]:
    print("MISMATCH calendar tz-aware")
    raise SystemExit(1)
print("OK")
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""R3.1/R3.4: __iso_year filter selects exactly rows whose ISO year matches,
including late-Dec-prior-calendar-year and early-Jan boundary rows.

2019-12-30 is ISO year 2020 (Mon of ISO week1). 2019-12-29 is ISO year 2019.
2021-01-03 is ISO year 2020 (Sun of last ISO week). 2021-01-04 is ISO 2021.
"""
import datetime
import django
from django.conf import settings

if not settings.configured:
    settings.configure(
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
        INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
        USE_TZ=False,
    )
django.setup()

from django.db import connection, models

class Ev(models.Model):
    d = models.DateField()
    class Meta:
        app_label = "contenttypes"

with connection.schema_editor() as se:
    se.create_model(Ev)

dates = {
    "2019-12-29": datetime.date(2019,12,29),  # iso 2019
    "2019-12-30": datetime.date(2019,12,30),  # iso 2020
    "2020-06-15": datetime.date(2020,6,15),   # iso 2020
    "2021-01-03": datetime.date(2021,1,3),    # iso 2020
    "2021-01-04": datetime.date(2021,1,4),    # iso 2021
}
for _, dv in dates.items():
    Ev.objects.create(d=dv)

got = set(Ev.objects.filter(d__iso_year=2020).values_list("d", flat=True))
expected = {dv for dv in dates.values() if dv.isocalendar()[0] == 2020}
print("got:", sorted(got))
print("expected:", sorted(expected))

# confirm the query used BETWEEN (range optimization), not EXTRACT
sqlstr = str(Ev.objects.filter(d__iso_year=2020).query)
print("sql:", sqlstr)

if got != expected:
    print("MISMATCH rows")
    raise SystemExit(1)
if "BETWEEN" not in sqlstr.upper():
    print("NOT using BETWEEN optimization")
    raise SystemExit(1)
print("OK")
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""R3.5: ExtractIsoYear as explicit annotation used in filter vs int gives same
ISO-year range semantics as implicit __iso_year lookup.
"""
import datetime
import django
from django.conf import settings

if not settings.configured:
    settings.configure(
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
        INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
        USE_TZ=False,
    )
django.setup()

from django.db import connection, models
from django.db.models.functions import ExtractIsoYear

class Ev(models.Model):
    d = models.DateField()
    class Meta:
        app_label = "contenttypes"

with connection.schema_editor() as se:
    se.create_model(Ev)

dates = [datetime.date(2019,12,29), datetime.date(2019,12,30),
         datetime.date(2020,6,15), datetime.date(2021,1,3), datetime.date(2021,1,4)]
for dv in dates:
    Ev.objects.create(d=dv)

qs_ann = Ev.objects.annotate(iy=ExtractIsoYear("d")).filter(iy=2020)
qs_imp = Ev.objects.filter(d__iso_year=2020)
got_ann = set(qs_ann.values_list("d", flat=True))
got_imp = set(qs_imp.values_list("d", flat=True))
expected = {dv for dv in dates if dv.isocalendar()[0] == 2020}
print("annotation:", sorted(got_ann))
print("implicit:", sorted(got_imp))
print("expected:", sorted(expected))

if got_ann != expected or got_imp != expected:
    print("MISMATCH")
    raise SystemExit(1)
print("OK")
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
"""R4.1/R4.2/R4.3/R4.4: calendar-year regression.
- date bounds default: Jan1 .. Dec31 of value
- datetime bounds default: Jan1 00:00 .. Dec31 23:59:59.999999
- __year filter selects by calendar year (not ISO).
2019-12-30 is calendar 2019 but ISO 2020; must NOT appear in __year=2020.
"""
import datetime
import django
from django.conf import settings

if not settings.configured:
    settings.configure(
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
        INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
        USE_TZ=False,
    )
django.setup()

from django.db import connection, models

# date bounds default
db = connection.ops.year_lookup_bounds_for_date_field(2020)
exp = [connection.ops.adapt_datefield_value(datetime.date(2020,1,1)),
       connection.ops.adapt_datefield_value(datetime.date(2020,12,31))]
print("date default bounds:", db, "exp:", exp)
if list(db) != exp:
    print("date MISMATCH"); raise SystemExit(1)

# datetime bounds default
dtb = connection.ops.year_lookup_bounds_for_datetime_field(2020)
expdt = [connection.ops.adapt_datetimefield_value(datetime.datetime(2020,1,1)),
         connection.ops.adapt_datetimefield_value(datetime.datetime(2020,12,31,23,59,59,999999))]
print("datetime default bounds:", dtb, "exp:", expdt)
if list(dtb) != expdt:
    print("datetime MISMATCH"); raise SystemExit(1)

# __year filter selects by calendar year
class Ev(models.Model):
    d = models.DateField()
    class Meta:
        app_label = "contenttypes"
with connection.schema_editor() as se:
    se.create_model(Ev)
dates = [datetime.date(2019,12,30), datetime.date(2020,6,15), datetime.date(2021,1,3)]
for dv in dates:
    Ev.objects.create(d=dv)
got = set(Ev.objects.filter(d__year=2020).values_list("d", flat=True))
expected = {dv for dv in dates if dv.year == 2020}
print("__year=2020 got:", sorted(got), "exp:", sorted(expected))
if got != expected:
    print("__year MISMATCH"); raise SystemExit(1)
print("OK")
```

Attack 7 — `probe_7.py` → holds on the patched tree (good)

```python
"""R4.5: full range of year comparison lookups work for ISO year, each using the
right bound. Test gt/gte/lt/lte on __iso_year with boundary rows.

value=2020. ISO year boundaries: lower=2019-12-30, upper=2021-01-03.
gte 2020 -> d >= lower ; lte 2020 -> d <= upper ; gt/lt use adjacent bounds.
"""
import datetime
import django
from django.conf import settings

if not settings.configured:
    settings.configure(
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
        INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
        USE_TZ=False,
    )
django.setup()

from django.db import connection, models

class Ev(models.Model):
    d = models.DateField()
    class Meta:
        app_label = "contenttypes"
with connection.schema_editor() as se:
    se.create_model(Ev)

dates = [datetime.date(2019,12,29), datetime.date(2019,12,30),
         datetime.date(2020,6,15), datetime.date(2021,1,3), datetime.date(2021,1,4)]
for dv in dates:
    Ev.objects.create(d=dv)

def iy(dt): return dt.isocalendar()[0]

# gte 2020 => iso year >= 2020
got = set(Ev.objects.filter(d__iso_year__gte=2020).values_list("d", flat=True))
exp = {dv for dv in dates if iy(dv) >= 2020}
print("gte:", sorted(got), "exp:", sorted(exp))
if got != exp: print("gte MISMATCH"); raise SystemExit(1)

# lte 2020 => iso year <= 2020
got = set(Ev.objects.filter(d__iso_year__lte=2020).values_list("d", flat=True))
exp = {dv for dv in dates if iy(dv) <= 2020}
print("lte:", sorted(got), "exp:", sorted(exp))
if got != exp: print("lte MISMATCH"); raise SystemExit(1)

# gt 2020 => iso year > 2020
got = set(Ev.objects.filter(d__iso_year__gt=2020).values_list("d", flat=True))
exp = {dv for dv in dates if iy(dv) > 2020}
print("gt:", sorted(got), "exp:", sorted(exp))
if got != exp: print("gt MISMATCH"); raise SystemExit(1)

# lt 2020 => iso year < 2020
got = set(Ev.objects.filter(d__iso_year__lt=2020).values_list("d", flat=True))
exp = {dv for dv in dates if iy(dv) < 2020}
print("lt:", sorted(got), "exp:", sorted(exp))
if got != exp: print("lt MISMATCH"); raise SystemExit(1)

print("OK")
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_4.py`

```python
"""R3.1/R3.4: __iso_year filter selects exactly rows whose ISO year matches,
including late-Dec-prior-calendar-year and early-Jan boundary rows.

2019-12-30 is ISO year 2020 (Mon of ISO week1). 2019-12-29 is ISO year 2019.
2021-01-03 is ISO year 2020 (Sun of last ISO week). 2021-01-04 is ISO 2021.
"""
import datetime
import django
from django.conf import settings

if not settings.configured:
    settings.configure(
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
        INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
        USE_TZ=False,
    )
django.setup()

from django.db import connection, models

class Ev(models.Model):
    d = models.DateField()
    class Meta:
        app_label = "contenttypes"

with connection.schema_editor() as se:
    se.create_model(Ev)

dates = {
    "2019-12-29": datetime.date(2019,12,29),  # iso 2019
    "2019-12-30": datetime.date(2019,12,30),  # iso 2020
    "2020-06-15": datetime.date(2020,6,15),   # iso 2020
    "2021-01-03": datetime.date(2021,1,3),    # iso 2020
    "2021-01-04": datetime.date(2021,1,4),    # iso 2021
}
for _, dv in dates.items():
    Ev.objects.create(d=dv)

got = set(Ev.objects.filter(d__iso_year=2020).values_list("d", flat=True))
expected = {dv for dv in dates.values() if dv.isocalendar()[0] == 2020}
print("got:", sorted(got))
print("expected:", sorted(expected))

# confirm the query used BETWEEN (range optimization), not EXTRACT
sqlstr = str(Ev.objects.filter(d__iso_year=2020).query)
print("sql:", sqlstr)

if got != expected:
    print("MISMATCH rows")
    raise SystemExit(1)
if "BETWEEN" not in sqlstr.upper():
    print("NOT using BETWEEN optimization")
    raise SystemExit(1)
print("OK")
```

Prepatch bug re-encoded as an attack: `True`.

Instance django__django-14170: __iso_year lookup must use ISO week-numbering-year BETWEEN bounds instead of calendar-year bounds.

Probes (criterion -> patched / base):
- probe_1 (R1.1,R1.2 date ISO bounds = fromisocalendar(v,1,1) .. fromisocalendar(v+1,1,1)-1day): HOLD / FAIL(base: TypeError, no iso_year kwarg).
- probe_2 (R2.1,R2.2 datetime ISO bounds, upper = -1 microsecond): HOLD / FAIL.
- probe_3 (R2.3 USE_TZ -> ISO datetime bounds tz-aware like calendar, checked America/New_York): HOLD.
- probe_4 POSITIVE CONTROL (R3.1,R3.4 d__iso_year=2020 selects exactly ISO-2020 rows incl. 2019-12-30 & 2021-01-03, excl. 2019-12-29 & 2021-01-04; verifies BETWEEN optimization used): HOLD / FAIL(base returns only 2020-06-15 via calendar BETWEEN 2020-01-01..2020-12-31). Discriminates.
- probe_5 (R3.5 ExtractIsoYear annotation-then-filter == implicit __iso_year): HOLD / FAIL.
- probe_6 (R4.1-R4.4 calendar regression: date/datetime default bounds Jan1..Dec31; __year=2020 excludes ISO-only 2019-12-30): HOLD.
- probe_7 (R4.5 gt/gte/lt/lte over __iso_year use correct single bound): HOLD.

All 7 HOLD on gold-patched tree. Positive control probe_4 FAILS at base and HOLDS patched (prepatch reproduced).

Candidate wrong-fix 'ops_only_no_lookup_wiring' (weak.diff): applies ONLY the operations.py half of the gold (adds iso_year param to both bounds functions) but leaves lookups.py YearLookup unchanged, so ISO bounds are never requested. This is the lazy partial fix a weak reading permits. Under it: probes 1,2,3,6 HOLD (they call the ops functions directly) but probes 4,5,7 REJECT it (behavioral __iso_year filter still returns calendar-year rows). Suite discriminates the wrong implementation -> requirements are not too weak on the wiring criterion (R3.1).

Verdict SOUND: >=5 distinct probes all hold on patched tree, positive control discriminates base vs patched, and a probe-conforming-only partial patch is rejected by the behavioral probes.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 7 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 7 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py`, `probe_7.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_4.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (7):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts, and on this backend both roles put it through the same derivation: every block below is a requirement probe run on the gold-patched tree, and the `machine verdict:` line each role publishes above reports BOTH that its probes hold there and how many candidate patches the probe suite rejected — so the two roles re-ran ONE probe suite and each recorded its own outcome for every probe in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `probe_1.py` → holds on the patched tree (good)

Attack 2 — `probe_2.py` → holds on the patched tree (good)

Attack 3 — `probe_3.py` → holds on the patched tree (good)

Attack 4 — `probe_4.py` → holds on the patched tree (good)

Attack 5 — `probe_5.py` → holds on the patched tree (good)

Attack 6 — `probe_6.py` → holds on the patched tree (good)

Attack 7 — `probe_7.py` → holds on the patched tree (good)

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_4.py`

```python
"""R3.1/R3.4: __iso_year filter selects exactly rows whose ISO year matches,
including late-Dec-prior-calendar-year and early-Jan boundary rows.

2019-12-30 is ISO year 2020 (Mon of ISO week1). 2019-12-29 is ISO year 2019.
2021-01-03 is ISO year 2020 (Sun of last ISO week). 2021-01-04 is ISO 2021.
"""
import datetime
import django
from django.conf import settings

if not settings.configured:
    settings.configure(
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
        INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
        USE_TZ=False,
    )
django.setup()

from django.db import connection, models

class Ev(models.Model):
    d = models.DateField()
    class Meta:
        app_label = "contenttypes"

with connection.schema_editor() as se:
    se.create_model(Ev)

dates = {
    "2019-12-29": datetime.date(2019,12,29),  # iso 2019
    "2019-12-30": datetime.date(2019,12,30),  # iso 2020
    "2020-06-15": datetime.date(2020,6,15),   # iso 2020
    "2021-01-03": datetime.date(2021,1,3),    # iso 2020
    "2021-01-04": datetime.date(2021,1,4),    # iso 2021
}
for _, dv in dates.items():
    Ev.objects.create(d=dv)

got = set(Ev.objects.filter(d__iso_year=2020).values_list("d", flat=True))
expected = {dv for dv in dates.values() if dv.isocalendar()[0] == 2020}
print("got:", sorted(got))
print("expected:", sorted(expected))

# confirm the query used BETWEEN (range optimization), not EXTRACT
sqlstr = str(Ev.objects.filter(d__iso_year=2020).query)
print("sql:", sqlstr)

if got != expected:
    print("MISMATCH rows")
    raise SystemExit(1)
if "BETWEEN" not in sqlstr.upper():
    print("NOT using BETWEEN optimization")
    raise SystemExit(1)
print("OK")
```

Prepatch bug re-encoded as an attack: `True`.

Instance django__django-14170: __iso_year lookup must use ISO week-numbering-year BETWEEN bounds instead of calendar-year bounds.

Probes (criterion -> patched / base):
- probe_1 (R1.1,R1.2 date ISO bounds = fromisocalendar(v,1,1) .. fromisocalendar(v+1,1,1)-1day): HOLD / FAIL(base: TypeError, no iso_year kwarg).
- probe_2 (R2.1,R2.2 datetime ISO bounds, upper = -1 microsecond): HOLD / FAIL.
- probe_3 (R2.3 USE_TZ -> ISO datetime bounds tz-aware like calendar, checked America/New_York): HOLD.
- probe_4 POSITIVE CONTROL (R3.1,R3.4 d__iso_year=2020 selects exactly ISO-2020 rows incl. 2019-12-30 & 2021-01-03, excl. 2019-12-29 & 2021-01-04; verifies BETWEEN optimization used): HOLD / FAIL(base returns only 2020-06-15 via calendar BETWEEN 2020-01-01..2020-12-31). Discriminates.
- probe_5 (R3.5 ExtractIsoYear annotation-then-filter == implicit __iso_year): HOLD / FAIL.
- probe_6 (R4.1-R4.4 calendar regression: date/datetime default bounds Jan1..Dec31; __year=2020 excludes ISO-only 2019-12-30): HOLD.
- probe_7 (R4.5 gt/gte/lt/lte over __iso_year use correct single bound): HOLD.

All 7 HOLD on gold-patched tree. Positive control probe_4 FAILS at base and HOLDS patched (prepatch reproduced).

Candidate wrong-fix 'ops_only_no_lookup_wiring' (weak.diff): applies ONLY the operations.py half of the gold (adds iso_year param to both bounds functions) but leaves lookups.py YearLookup unchanged, so ISO bounds are never requested. This is the lazy partial fix a weak reading permits. Under it: probes 1,2,3,6 HOLD (they call the ops functions directly) but probes 4,5,7 REJECT it (behavioral __iso_year filter still returns calendar-year rows). Suite discriminates the wrong implementation -> requirements are not too weak on the wiring criterion (R3.1).

Verdict SOUND: >=5 distinct probes all hold on patched tree, positive control discriminates base vs patched, and a probe-conforming-only partial patch is rejected by the behavioral probes.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** The patch adds an iso_year kwarg (default False) to both year_lookup_bounds_for_date_field/datetime_field, computing bounds via datetime(.date).fromisocalendar for the ISO branch, and YearLookup selects it via isinstance(self.lhs, ExtractIsoYear). Requirements pin exactly the changed observable behavior (ISO bounds selection + calendar preservation) — the modeling boundary is correct, not a narrow single-branch/helper slice: R3 covers the lookup-level dispatch AND the implicit __iso_year vs explicit-annotation equivalence noted in the issue. Adaptation caveats (R1.3/R2.4/R2.3 tz) are also faithfully required. Probe verified on gold-patched instance image (HOLDS exit=0). No mandated-but-absent, forbidden-but-present, or invented behavior found.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The spec localizes the change to genuine public modules/functions (YearLookup, year_lookup_bounds_for_date/datetime_field, ExtractIsoYear, base/operations.py, lookups.py) — legitimate. References to datetime.date/datetime.fromisocalendar mirror gold-patch code but are standard-library functions that constitute the canonical *definition* of an ISO week-numbering-year boundary; using them to specify the lower/upper bound is behavioral description, not transmission of a fix-invented identifier. The comparison-lookup enumeration (exact/gt/gte/lt/lte, Req 4.5) lists the full YearLookup family rather than the test's 3-case subset (iso_year=, __gt, __lte), so it describes the feature generally, not the parametrization. No test names/paths (test_extract_iso_year_func_boundaries, DateFunctionTests/WithTimeZoneTests), no DTModel/week_52/week_53 object identifiers, no specific test year values (2014/2015) or gold-patch's iso_year kwarg leak beyond behavior. The 'late December/early January' phrasing is generic ISO-8601 semantics already implicit in the public problem_statement. No hidden-test/gold reconstruction beyond describing behavior.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
