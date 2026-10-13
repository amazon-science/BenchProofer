# P2 adversarial audit — django__django-11138

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 5 requirement probes hold on the patched tree; 2/2 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 5 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 5 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 2 alternative candidate patches, claimed to satisfy every cited requirement, and ran the same suite against them. The suite rejected all 2: a probe encoding a cited requirement fails under each of those, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (5):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
"""Positive control + Req 2.4/2.5: SQLite __date lookup honors connection TIME_ZONE.

Replicates the hidden test test_query_convert_timezones end-to-end via the ORM
on an in-memory SQLite db. Exits 0 iff BOTH cases match.
"""
import sys
import datetime
import contextlib
import django
from django.conf import settings

settings.configure(
    USE_TZ=True,
    TIME_ZONE='Africa/Nairobi',  # current tz => EAT (+3h)
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
    INSTALLED_APPS=[],
)
django.setup()

from django.db import connection, models
from django.utils import timezone

EAT = timezone.get_fixed_timezone(180)   # Africa/Nairobi (+3h)
ICT = timezone.get_fixed_timezone(420)   # Asia/Bangkok (+7h)


class Event(models.Model):
    dt = models.DateTimeField()
    class Meta:
        app_label = 'probeapp'


@contextlib.contextmanager
def override_conn_tz(tz):
    orig = connection.settings_dict['TIME_ZONE']
    connection.settings_dict['TIME_ZONE'] = tz
    connection.timezone
    del connection.timezone
    connection.timezone_name
    del connection.timezone_name
    try:
        yield
    finally:
        connection.settings_dict['TIME_ZONE'] = orig
        connection.timezone
        del connection.timezone
        connection.timezone_name
        del connection.timezone_name


with connection.schema_editor() as se:
    se.create_model(Event)

ok = True

# Case A: connection tz == current tz (Nairobi) -> no conversion, found by its own date
with override_conn_tz('Africa/Nairobi'):
    ev_dt = datetime.datetime(2016, 1, 2, 23, 10, 11, 123, tzinfo=EAT)
    ev = Event.objects.create(dt=ev_dt)
    found = Event.objects.filter(dt__date=ev_dt.date()).first()
    print("case A (equal tz): found=%r expected pk=%r" % (found, ev.pk))
    if found != ev:
        ok = False

# Case B: connection tz (Bangkok +7) != current tz (Nairobi +3) -> shift -4h
with override_conn_tz('Asia/Bangkok'):
    ev_dt = datetime.datetime(2016, 1, 2, 3, 10, 11, tzinfo=ICT)
    ev = Event.objects.create(dt=ev_dt)
    found = Event.objects.filter(dt__date=datetime.date(2016, 1, 1)).first()
    print("case B (diff tz -4h): found=%r expected pk=%r" % (found, ev.pk))
    if found != ev:
        ok = False

print("RESULT:", "HOLDS" if ok else "VIOLATED")
sys.exit(0 if ok else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""Req 1.1 & 2.1 (MySQL): _convert_field_to_tz source = connection tz; skip when equal.

Directly exercise the MySQL DatabaseOperations._convert_field_to_tz string builder
without connecting to MySQL. Exits 0 iff:
 - USE_TZ + conn tz != target -> CONVERT_TZ(col, '<conn tz>', '<target>') and no 'UTC' hardcode
 - USE_TZ + conn tz == target -> column returned unchanged
"""
import sys
import django
from django.conf import settings

settings.configure(USE_TZ=True, DATABASES={}, INSTALLED_APPS=[])
django.setup()

from django.db.backends.mysql.operations import DatabaseOperations


class FakeConn:
    def __init__(self, tzname):
        self.timezone_name = tzname


ops = DatabaseOperations(connection=FakeConn('Europe/Paris'))
ok = True

# diff tz -> conversion from connection tz
out = ops._convert_field_to_tz('mycol', 'UTC')
print("diff-tz:", out)
if out != "CONVERT_TZ(mycol, 'Europe/Paris', 'UTC')":
    print("  UNEXPECTED sql"); ok = False
if "'UTC', 'UTC'" in out or ", 'UTC', 'Europe/Paris'" in out:
    pass  # not this
# make sure the SOURCE is the connection tz, not a hardcoded UTC source
if "CONVERT_TZ(mycol, 'UTC'," in out:
    print("  source is hardcoded UTC -> VIOLATION"); ok = False

# equal tz -> unchanged
ops2 = DatabaseOperations(connection=FakeConn('UTC'))
out2 = ops2._convert_field_to_tz('mycol', 'UTC')
print("equal-tz:", out2)
if out2 != 'mycol':
    print("  expected unchanged column"); ok = False

print("RESULT:", "HOLDS" if ok else "VIOLATED")
sys.exit(0 if ok else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""Req 1.2, 2.2, 3.1, 4.4 (Oracle): _convert_field_to_tz.

Exercise Oracle DatabaseOperations._convert_field_to_tz string builder.
Exits 0 iff:
 - USE_TZ + conn tz != target -> CAST((FROM_TZ(col, '<conn tz>') AT TIME ZONE '<target>') AS TIMESTAMP), no '0:00'
 - USE_TZ + conn tz == target -> unchanged column
 - invalid tzname -> ValueError
"""
import sys
import django
from django.conf import settings

settings.configure(USE_TZ=True, DATABASES={}, INSTALLED_APPS=[])
django.setup()

# oracle operations imports .base which needs cx_Oracle; stub it so we can
# exercise the pure string-builder behavior of _convert_field_to_tz.
import types
if 'cx_Oracle' not in sys.modules:
    class _FakeCx(types.ModuleType):
        class DatabaseError(Exception):
            pass
        __version__ = '8.0.0'
        def __getattr__(self, name):
            # any constant referenced at import time -> a unique sentinel object
            v = object()
            setattr(self, name, v)
            return v
    fake = _FakeCx('cx_Oracle')
    fake.makedsn = lambda *a, **k: ''
    sys.modules['cx_Oracle'] = fake
import django.db.backends.oracle.base  # resolve circular import base<->operations
from django.db.backends.oracle.operations import DatabaseOperations


class FakeConn:
    def __init__(self, tzname):
        self.timezone_name = tzname


ok = True
ops = DatabaseOperations(connection=FakeConn('Europe/Paris'))

out = ops._convert_field_to_tz('mycol', 'UTC')
print("diff-tz:", out)
expected = "CAST((FROM_TZ(mycol, 'Europe/Paris') AT TIME ZONE 'UTC') AS TIMESTAMP)"
if out != expected:
    print("  UNEXPECTED"); ok = False
if "'0:00'" in out:
    print("  hardcoded 0:00 source -> VIOLATION"); ok = False

ops2 = DatabaseOperations(connection=FakeConn('UTC'))
out2 = ops2._convert_field_to_tz('mycol', 'UTC')
print("equal-tz:", out2)
if out2 != 'mycol':
    print("  expected unchanged"); ok = False

# invalid tzname -> ValueError (Req 4.4)
try:
    ops.convert_val = None
    bad = ops._convert_field_to_tz('mycol', "bad'; DROP")
    print("  invalid tzname did NOT raise, got:", bad); ok = False
except ValueError as e:
    print("invalid tzname raised ValueError:", e)

print("RESULT:", "HOLDS" if ok else "VIOLATED")
sys.exit(0 if ok else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""Req 1.3, 2.3, 4.1, 4.2, 4.3 (SQLite callbacks + builders arity).

Exercise the SQLite python callbacks and SQL builders directly.
Exits 0 iff:
 - callbacks accept the connection-tz arg (arity): cast_date/cast_time take 3,
   extract takes 4, trunc takes 4  (Req 4.1)
 - conn tz != target -> value interpreted in conn tz then expressed in target (Req 1.3)
 - conn tz == target -> value left in connection tz, no further shift (Req 2.3)
 - null value -> None (Req 4.2); unparseable -> None (Req 4.3)
 - SQL builders emit 3/4-arg calls and pass both tz args (USE_TZ) (Req 1.3)
"""
import sys
import inspect
import datetime
import django
from django.conf import settings

settings.configure(USE_TZ=True, DATABASES={}, INSTALLED_APPS=[])
django.setup()

from django.db.backends.sqlite3 import base as sb
from django.db.backends.sqlite3.operations import DatabaseOperations

ok = True

# --- arity of callbacks (Req 4.1) ---
def nargs(fn):
    sig = inspect.signature(fn)
    return len(sig.parameters)

print("cast_date params:", nargs(sb._sqlite_datetime_cast_date))
print("cast_time params:", nargs(sb._sqlite_datetime_cast_time))
print("extract params  :", nargs(sb._sqlite_datetime_extract))
print("trunc params    :", nargs(sb._sqlite_datetime_trunc))
if nargs(sb._sqlite_datetime_cast_date) < 3: ok = False
if nargs(sb._sqlite_datetime_cast_time) < 3: ok = False
if nargs(sb._sqlite_datetime_extract) < 4: ok = False
if nargs(sb._sqlite_datetime_trunc) < 4: ok = False

# stored naive value (as stored in DB): 2016-01-02 03:10:11 recorded in Bangkok (+7)
stored = '2016-01-02 03:10:11'

# --- Req 1.3: conn tz Bangkok(+7), target Nairobi(+3) -> -4h -> 2016-01-01 23:10:11 ---
d = sb._sqlite_datetime_cast_date(stored, 'Africa/Nairobi', 'Asia/Bangkok')
print("cast_date diff-tz:", d)
if d != '2016-01-01':
    print("  expected 2016-01-01 (shifted -4h)"); ok = False

# --- Req 2.3: conn tz == target -> no shift, stays on its own date ---
d2 = sb._sqlite_datetime_cast_date(stored, 'Asia/Bangkok', 'Asia/Bangkok')
print("cast_date equal-tz:", d2)
if d2 != '2016-01-02':
    print("  expected 2016-01-02 (no shift)"); ok = False

# --- Req 4.2: null value -> None ---
if sb._sqlite_datetime_cast_date(None, 'Africa/Nairobi', 'Asia/Bangkok') is not None:
    print("  null did not return None"); ok = False
else:
    print("null -> None OK")

# --- Req 4.3: unparseable -> None ---
if sb._sqlite_datetime_cast_date('not-a-timestamp', 'Africa/Nairobi', 'Asia/Bangkok') is not None:
    print("  unparseable did not return None"); ok = False
else:
    print("unparseable -> None OK")

# --- SQL builders pass both tz args when USE_TZ ---
ops = DatabaseOperations(connection=type('C', (), {'timezone_name': 'Asia/Bangkok'})())
cd = ops.datetime_cast_date_sql('col', 'Africa/Nairobi')
print("cast_date_sql:", cd)
if "'Africa/Nairobi'" not in cd or "'Asia/Bangkok'" not in cd:
    print("  builder missing a tz arg"); ok = False
ex = ops.datetime_extract_sql('year', 'col', 'Africa/Nairobi')
print("extract_sql:", ex)
if "'Africa/Nairobi'" not in ex or "'Asia/Bangkok'" not in ex:
    print("  extract builder missing a tz arg"); ok = False

print("RESULT:", "HOLDS" if ok else "VIOLATED")
sys.exit(0 if ok else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""Req 3.1, 3.2 (USE_TZ disabled) + Req 4.5 regression (UTC conn tz == UTC source).

Exits 0 iff:
 - USE_TZ False: MySQL & Oracle _convert_field_to_tz return column unchanged (3.1)
 - USE_TZ False: SQLite builders pass NULL for both tz args (3.2)
 - Req 4.5: with conn tz == UTC and USE_TZ, SQLite cast_date matches the historical
   UTC-source result (value interpreted as UTC then shown in target).
"""
import sys
import django
from django.conf import settings

settings.configure(USE_TZ=False, DATABASES={}, INSTALLED_APPS=[])
django.setup()

ok = True

from django.db.backends.mysql.operations import DatabaseOperations as MyOps
from django.db.backends.sqlite3.operations import DatabaseOperations as SqOps

conn = type('C', (), {'timezone_name': 'UTC'})()

# Req 3.1 MySQL unchanged when USE_TZ off
m = MyOps(connection=conn)
mo = m._convert_field_to_tz('col', 'UTC')
print("mysql USE_TZ off:", mo)
if mo != 'col':
    print("  mysql should be unchanged"); ok = False

try:
    from django.db.backends.oracle.operations import DatabaseOperations as OrOps
    o = OrOps(connection=conn)
    oo = o._convert_field_to_tz('col', 'UTC')
    print("oracle USE_TZ off:", oo)
    if oo != 'col':
        print("  oracle should be unchanged"); ok = False
except Exception as e:
    print("oracle import skipped:", e)

# Req 3.2 SQLite builders pass NULL for both tz args
s = SqOps(connection=conn)
cd = s.datetime_cast_date_sql('col', 'Africa/Nairobi')
print("sqlite cast_date_sql USE_TZ off:", cd)
# should contain two NULL args, no quoted tz names
if "NULL, NULL" not in cd.replace("'col'", "col"):
    print("  expected NULL, NULL for both tz args"); ok = False
if "'Africa/Nairobi'" in cd:
    print("  leaked target tz while USE_TZ off"); ok = False
ex = s.datetime_extract_sql('year', 'col', 'Africa/Nairobi')
print("sqlite extract_sql USE_TZ off:", ex)
if "NULL, NULL" not in ex:
    print("  extract expected NULL, NULL"); ok = False

# Req 4.5: conn tz UTC == historical source. Turn USE_TZ back on for callback test.
settings.USE_TZ = True
from django.db.backends.sqlite3 import base as sb
# stored value in UTC 2016-01-02 01:30:00, target Nairobi(+3) => 2016-01-02 04:30 -> date 2016-01-02
d = sb._sqlite_datetime_cast_date('2016-01-02 01:30:00', 'Africa/Nairobi', 'UTC')
print("UTC-source cast_date:", d)
if d != '2016-01-02':
    print("  UTC-source regression"); ok = False
# stored UTC 2016-01-02 23:30:00 target Nairobi(+3) => 2016-01-03 02:30 -> date 2016-01-03
d2 = sb._sqlite_datetime_cast_date('2016-01-02 23:30:00', 'Africa/Nairobi', 'UTC')
print("UTC-source cast_date 2:", d2)
if d2 != '2016-01-03':
    print("  UTC-source regression 2"); ok = False

print("RESULT:", "HOLDS" if ok else "VIOLATED")
sys.exit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Positive control + Req 2.4/2.5: SQLite __date lookup honors connection TIME_ZONE.

Replicates the hidden test test_query_convert_timezones end-to-end via the ORM
on an in-memory SQLite db. Exits 0 iff BOTH cases match.
"""
import sys
import datetime
import contextlib
import django
from django.conf import settings

settings.configure(
    USE_TZ=True,
    TIME_ZONE='Africa/Nairobi',  # current tz => EAT (+3h)
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
    INSTALLED_APPS=[],
)
django.setup()

from django.db import connection, models
from django.utils import timezone

EAT = timezone.get_fixed_timezone(180)   # Africa/Nairobi (+3h)
ICT = timezone.get_fixed_timezone(420)   # Asia/Bangkok (+7h)


class Event(models.Model):
    dt = models.DateTimeField()
    class Meta:
        app_label = 'probeapp'


@contextlib.contextmanager
def override_conn_tz(tz):
    orig = connection.settings_dict['TIME_ZONE']
    connection.settings_dict['TIME_ZONE'] = tz
    connection.timezone
    del connection.timezone
    connection.timezone_name
    del connection.timezone_name
    try:
        yield
    finally:
        connection.settings_dict['TIME_ZONE'] = orig
        connection.timezone
        del connection.timezone
        connection.timezone_name
        del connection.timezone_name


with connection.schema_editor() as se:
    se.create_model(Event)

ok = True

# Case A: connection tz == current tz (Nairobi) -> no conversion, found by its own date
with override_conn_tz('Africa/Nairobi'):
    ev_dt = datetime.datetime(2016, 1, 2, 23, 10, 11, 123, tzinfo=EAT)
    ev = Event.objects.create(dt=ev_dt)
    found = Event.objects.filter(dt__date=ev_dt.date()).first()
    print("case A (equal tz): found=%r expected pk=%r" % (found, ev.pk))
    if found != ev:
        ok = False

# Case B: connection tz (Bangkok +7) != current tz (Nairobi +3) -> shift -4h
with override_conn_tz('Asia/Bangkok'):
    ev_dt = datetime.datetime(2016, 1, 2, 3, 10, 11, tzinfo=ICT)
    ev = Event.objects.create(dt=ev_dt)
    found = Event.objects.filter(dt__date=datetime.date(2016, 1, 1)).first()
    print("case B (diff tz -4h): found=%r expected pk=%r" % (found, ev.pk))
    if found != ev:
        ok = False

print("RESULT:", "HOLDS" if ok else "VIOLATED")
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Requirements faithfully capture django-11138 (honor connection TIME_ZONE as the datetime-conversion source; skip conversion when source==target). Five probes cover all four requirements; each is a standalone stdlib script.

Probes / criteria / observed:
- probe_1 (Req 2.4/2.5, POSITIVE CONTROL): end-to-end ORM SQLite __date lookup. Case A conn tz==current(Nairobi) found by own date; case B conn tz Bangkok(+7)!=current(+3) matches date shifted -4h. PATCHED=HOLDS, BASE=VIOLATED (both cases found=None at base) => discriminates.
- probe_2 (Req 1.1/2.1 MySQL): _convert_field_to_tz emits CONVERT_TZ(col,'<conn tz>','<target>') (source=conn tz, no hardcoded UTC) when differing; returns col unchanged when equal. PATCHED=HOLDS.
- probe_3 (Req 1.2/2.2/4.4 Oracle): CAST((FROM_TZ(col,'<conn tz>') AT TIME ZONE '<target>') AS TIMESTAMP), no '0:00' source; unchanged when equal; invalid tzname raises ValueError. (cx_Oracle stubbed to import the pure builder.) PATCHED=HOLDS.
- probe_4 (Req 1.3/2.3/4.1/4.2/4.3 SQLite): callback arities (cast 3, extract/trunc 4); conn-tz interpret-then-shift (-4h) vs no-shift when equal; None->None; unparseable->None; builders pass both tz args. PATCHED=HOLDS.
- probe_5 (Req 3.1/3.2 + 4.5): USE_TZ off => MySQL/Oracle unchanged, SQLite builders emit NULL,NULL; USE_TZ on with conn tz==UTC reproduces historical UTC-source results. PATCHED=HOLDS.

Candidate wrong-fix patches exercised:
- weak_partial.diff: SQLite-only fix (MySQL & Oracle left unpatched). REJECTED by probe_2 (still CONVERT_TZ(...,'UTC','UTC')) and probe_3 (still FROM_TZ(...,'0:00')). probe_1/4/5 hold (SQLite path fixed) -> not too-weak, discriminated on the backend boundary.
- weak_ignoreconn.diff: correct arity/plumbing but callback ignores conn_tzname (keeps UTC source). REJECTED by probe_1 (case B found=None) and probe_4 (wrong date). Confirms probes bind the actual conversion source, not just the SQL shape.

All 5 probes HOLD on the gold-patched tree; positive control fails at base and holds patched; >=2 requirements-plausible wrong fixes are rejected. No violation and no probe-conforming alternative found.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 5 requirement probes hold on the patched tree; 2/2 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 5 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 5 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 2 alternative candidate patches, claimed to satisfy every cited requirement, and ran the same suite against them. The suite rejected all 2: a probe encoding a cited requirement fails under each of those, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (5):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

_The 5 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts, and on this backend both roles put it through the same derivation: every block below is a requirement probe run on the gold-patched tree, and the `machine verdict:` line each role publishes above reports BOTH that its probes hold there and how many candidate patches the probe suite rejected — so the two roles re-ran ONE probe suite and each recorded its own outcome for every probe in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `probe_1.py` → holds on the patched tree (good)

Attack 2 — `probe_2.py` → holds on the patched tree (good)

Attack 3 — `probe_3.py` → holds on the patched tree (good)

Attack 4 — `probe_4.py` → holds on the patched tree (good)

Attack 5 — `probe_5.py` → holds on the patched tree (good)

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Positive control + Req 2.4/2.5: SQLite __date lookup honors connection TIME_ZONE.

Replicates the hidden test test_query_convert_timezones end-to-end via the ORM
on an in-memory SQLite db. Exits 0 iff BOTH cases match.
"""
import sys
import datetime
import contextlib
import django
from django.conf import settings

settings.configure(
    USE_TZ=True,
    TIME_ZONE='Africa/Nairobi',  # current tz => EAT (+3h)
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
    INSTALLED_APPS=[],
)
django.setup()

from django.db import connection, models
from django.utils import timezone

EAT = timezone.get_fixed_timezone(180)   # Africa/Nairobi (+3h)
ICT = timezone.get_fixed_timezone(420)   # Asia/Bangkok (+7h)


class Event(models.Model):
    dt = models.DateTimeField()
    class Meta:
        app_label = 'probeapp'


@contextlib.contextmanager
def override_conn_tz(tz):
    orig = connection.settings_dict['TIME_ZONE']
    connection.settings_dict['TIME_ZONE'] = tz
    connection.timezone
    del connection.timezone
    connection.timezone_name
    del connection.timezone_name
    try:
        yield
    finally:
        connection.settings_dict['TIME_ZONE'] = orig
        connection.timezone
        del connection.timezone
        connection.timezone_name
        del connection.timezone_name


with connection.schema_editor() as se:
    se.create_model(Event)

ok = True

# Case A: connection tz == current tz (Nairobi) -> no conversion, found by its own date
with override_conn_tz('Africa/Nairobi'):
    ev_dt = datetime.datetime(2016, 1, 2, 23, 10, 11, 123, tzinfo=EAT)
    ev = Event.objects.create(dt=ev_dt)
    found = Event.objects.filter(dt__date=ev_dt.date()).first()
    print("case A (equal tz): found=%r expected pk=%r" % (found, ev.pk))
    if found != ev:
        ok = False

# Case B: connection tz (Bangkok +7) != current tz (Nairobi +3) -> shift -4h
with override_conn_tz('Asia/Bangkok'):
    ev_dt = datetime.datetime(2016, 1, 2, 3, 10, 11, tzinfo=ICT)
    ev = Event.objects.create(dt=ev_dt)
    found = Event.objects.filter(dt__date=datetime.date(2016, 1, 1)).first()
    print("case B (diff tz -4h): found=%r expected pk=%r" % (found, ev.pk))
    if found != ev:
        ok = False

print("RESULT:", "HOLDS" if ok else "VIOLATED")
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Requirements faithfully capture django-11138 (honor connection TIME_ZONE as the datetime-conversion source; skip conversion when source==target). Five probes cover all four requirements; each is a standalone stdlib script.

Probes / criteria / observed:
- probe_1 (Req 2.4/2.5, POSITIVE CONTROL): end-to-end ORM SQLite __date lookup. Case A conn tz==current(Nairobi) found by own date; case B conn tz Bangkok(+7)!=current(+3) matches date shifted -4h. PATCHED=HOLDS, BASE=VIOLATED (both cases found=None at base) => discriminates.
- probe_2 (Req 1.1/2.1 MySQL): _convert_field_to_tz emits CONVERT_TZ(col,'<conn tz>','<target>') (source=conn tz, no hardcoded UTC) when differing; returns col unchanged when equal. PATCHED=HOLDS.
- probe_3 (Req 1.2/2.2/4.4 Oracle): CAST((FROM_TZ(col,'<conn tz>') AT TIME ZONE '<target>') AS TIMESTAMP), no '0:00' source; unchanged when equal; invalid tzname raises ValueError. (cx_Oracle stubbed to import the pure builder.) PATCHED=HOLDS.
- probe_4 (Req 1.3/2.3/4.1/4.2/4.3 SQLite): callback arities (cast 3, extract/trunc 4); conn-tz interpret-then-shift (-4h) vs no-shift when equal; None->None; unparseable->None; builders pass both tz args. PATCHED=HOLDS.
- probe_5 (Req 3.1/3.2 + 4.5): USE_TZ off => MySQL/Oracle unchanged, SQLite builders emit NULL,NULL; USE_TZ on with conn tz==UTC reproduces historical UTC-source results. PATCHED=HOLDS.

Candidate wrong-fix patches exercised:
- weak_partial.diff: SQLite-only fix (MySQL & Oracle left unpatched). REJECTED by probe_2 (still CONVERT_TZ(...,'UTC','UTC')) and probe_3 (still FROM_TZ(...,'0:00')). probe_1/4/5 hold (SQLite path fixed) -> not too-weak, discriminated on the backend boundary.
- weak_ignoreconn.diff: correct arity/plumbing but callback ignores conn_tzname (keeps UTC source). REJECTED by probe_1 (case B found=None) and probe_4 (wrong date). Confirms probes bind the actual conversion source, not just the SQL shape.

All 5 probes HOLD on the gold-patched tree; positive control fails at base and holds patched; >=2 requirements-plausible wrong fixes are rejected. No violation and no probe-conforming alternative found.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Oracle (Req2.2/3.1/4.4) could not be exercised live (cx_Oracle absent in image), but the gold patch.diff text unambiguously implements: FROM_TZ source = connection.timezone_name, returns bare field_name when conn tz == tzname, USE_TZ-off passthrough retained, and the pre-existing _tzname_re guard raising ValueError('Invalid time zone name') is preserved — all matching the Oracle requirements. Requirements correctly model the changed observable behavior (conversion source zone, skip-when-equal, disabled passthrough, callback arity/contract) rather than a narrow slice, consistent with F2P test timezones.tests.NewDatabaseTests.test_query_convert_timezones. Non-load-bearing wording nit: Req1.3 example says a value 4h ahead matches a date 4h earlier — direction depends on relative offsets, but it is illustrative and not a testable mandate that conflicts with the code.

Counterexample / evidence:

```
N/A — no divergence.
```


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The document localizes the change to the per-backend datetime helpers (MySQL/Oracle _convert_field_to_tz, SQLite operations SQL builders, base.py callbacks + get_new_connection). Naming these changed modules/functions is legitimate localization derivable from the gold edit's structure, not a test artifact. All named functions are the actual changed functions; naming them is explicitly allowed. The MySQL helper, the CONVERT_TZ('UTC',...) bug, the skip-when-equal fix, and the UTC-default are ALL already public in the problem_statement. The requirements translate behavior (convert from connection tz as source; skip when source==target; preserve USE_TZ=False no-op; SQLite callback arity accommodating the extra arg; ValueError on bad Oracle tzname) into obligations — this is the intended work, not leakage. No test names/paths (test_query_convert_timezones, override_database_connection_timezone), no test datetimes (2016-01-02, EAT/ICT), no expected date (2016-01-01), and no gold-invented identifiers (conn_tzname, _convert_tznames_to_sql) are quoted or near-quoted. Closest concern: Req 2 criterion 5's 'four hours ahead ... four hours earlier' example matches the hidden test's Bangkok/Nairobi 4h differential (and its '(-4h)' comment), whereas the problem_statement only uses a zero-difference Paris/Paris example. But a single illustrative magnitude, absent the timezones/datetimes/expected date, does not reconstruct the parametrization nor enumerate cases; it illustrates the tz-shift semantics behaviorally and stays on the describe-behavior side of the line. Insufficient to constitute a leak.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
