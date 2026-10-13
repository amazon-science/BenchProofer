# P2 adversarial audit — django__django-16429

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
"""Positive control / Req1.1 & 1.3: aware datetime, ~31 days ago -> '1 month', no TypeError.
Holds on patched, must FAIL at base (base raises TypeError)."""
import datetime
import django
from django.conf import settings
if not settings.configured:
    settings.configure(USE_I18N=False, USE_TZ=True, INSTALLED_APPS=[])
django.setup()
from django.utils.timesince import timesince

now = datetime.datetime(2023, 2, 15, 12, 0, 0, tzinfo=datetime.timezone.utc)
d = now - datetime.timedelta(days=31)
try:
    r = timesince(d, now)
except TypeError as e:
    print("FAIL: raised TypeError:", e)
    raise SystemExit(1)
print("observed:", repr(r))
if r != "1\xa0month":
    print("FAIL: expected '1\\xa0month', got", repr(r))
    raise SystemExit(1)
print("OK")
raise SystemExit(0)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""Req1.2 & 3.1: pivot must carry d's tzinfo AND clamp day to last valid day of pivot month.
Directly exercise the intermediate pivot logic by picking a start day (31) that doesn't exist
in the pivot month, with an aware d. This must not raise and must give a sane month count."""
import datetime
import django
from django.conf import settings
if not settings.configured:
    settings.configure(USE_I18N=False, USE_TZ=True, INSTALLED_APPS=[])
django.setup()
from django.utils.timesince import timesince

# d on Jan 31 aware; now ~ a bit over one month later. Pivot month = Feb which has no 31st.
d = datetime.datetime(2023, 1, 31, 0, 0, 0, tzinfo=datetime.timezone.utc)
now = datetime.datetime(2023, 3, 1, 0, 0, 0, tzinfo=datetime.timezone.utc)
try:
    r = timesince(d, now)
except Exception as e:
    print("FAIL: raised", type(e).__name__, e)
    raise SystemExit(1)
print("observed:", repr(r))
# Jan31 -> Mar1 : should report at least 1 month, no overflow crash.
if "month" not in r:
    print("FAIL: expected a month count, got", repr(r))
    raise SystemExit(1)
print("OK")
raise SystemExit(0)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""Req2.1/2.3: multi-unit depth output identical for aware and naive; and Req1.4 timeuntil.
Interval = 1 year + 1 month + 1 week + 1 day + 1 hour. Check depth 1..4 for aware,
and that aware == naive results."""
import datetime
import django
from django.conf import settings
if not settings.configured:
    settings.configure(USE_I18N=False, USE_TZ=True, INSTALLED_APPS=[])
django.setup()
from django.utils.timesince import timesince, timeuntil

def build(tz):
    d = datetime.datetime(2000, 1, 1, 0, 0, 0, tzinfo=tz)
    # add 1 year, 1 month, 1 week, 1 day, 1 hour
    now = datetime.datetime(2001, 2, 9, 1, 0, 0, tzinfo=tz)
    return d, now

utc = datetime.timezone.utc
da, na = build(utc)
dn, nn = build(None)

ok = True
for depth in (1, 2, 3, 4):
    ra = timesince(da, na, depth=depth)
    rn = timesince(dn, nn, depth=depth)
    print(f"depth={depth} aware={ra!r} naive={rn!r}")
    if ra != rn:
        print("FAIL: aware != naive at depth", depth)
        ok = False

# depth expectations
exp = {1: "1\xa0year", 2: "1\xa0year, 1\xa0month"}
for depth, e in exp.items():
    ra = timesince(da, na, depth=depth)
    if ra != e:
        print(f"FAIL depth {depth}: expected {e!r} got {ra!r}")
        ok = False

# timeuntil aware (Req1.4): now in future relative to d
tu = timeuntil(na, da)  # na is 'd', da is 'now' => interval from da to na
print("timeuntil aware:", repr(tu))
try:
    _ = timeuntil(na, da)
except TypeError as e:
    print("FAIL: timeuntil raised", e)
    ok = False

if not ok:
    raise SystemExit(1)
print("OK")
raise SystemExit(0)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""Req2.2 non-adjacent units -> only largest; Req2.4 depth<=0 -> ValueError (aware & naive)."""
import datetime
import django
from django.conf import settings
if not settings.configured:
    settings.configure(USE_I18N=False, USE_TZ=True, INSTALLED_APPS=[])
django.setup()
from django.utils.timesince import timesince

utc = datetime.timezone.utc
ok = True

# non-adjacent: 1 year + 1 hour (skip months/weeks/days) -> only "1 year"
d = datetime.datetime(2000, 1, 1, 0, 0, 0, tzinfo=utc)
now = datetime.datetime(2001, 1, 1, 1, 0, 0, tzinfo=utc)
r = timesince(d, now, depth=2)
print("non-adjacent aware:", repr(r))
if r != "1\xa0year":
    print("FAIL: expected '1\\xa0year', got", repr(r))
    ok = False

# depth<=0 must raise ValueError for both aware & naive
for label, dd, nn in [("aware", d, now),
                      ("naive", datetime.datetime(2000,1,1), datetime.datetime(2001,1,1,1))]:
    try:
        timesince(dd, nn, depth=0)
        print(f"FAIL {label}: depth=0 did not raise")
        ok = False
    except ValueError as e:
        print(f"{label} depth=0 ValueError:", e)
        if "greater than 0" not in str(e):
            print(f"FAIL {label}: message wrong:", e)
            ok = False
    except Exception as e:
        print(f"FAIL {label}: wrong exception {type(e).__name__}: {e}")
        ok = False

if not ok:
    raise SystemExit(1)
print("OK")
raise SystemExit(0)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""Req4 regressions: past/equal -> '0 minutes'; sub-minute -> '0 minutes';
naive unchanged; custom time_strings used; long-interval year count (Req3.3)."""
import datetime
import django
from django.conf import settings
if not settings.configured:
    settings.configure(USE_I18N=False, USE_TZ=True, INSTALLED_APPS=[])
django.setup()
from django.utils.timesince import timesince

utc = datetime.timezone.utc
ok = True

# Req4.1 comparison earlier/equal -> "0 minutes"
d = datetime.datetime(2023,1,1,12,0,0, tzinfo=utc)
r = timesince(d, d)
print("equal:", repr(r))
if r != "0\xa0minutes":
    print("FAIL equal:", repr(r)); ok=False
r = timesince(d, d - datetime.timedelta(days=5))
print("future-d:", repr(r))
if r != "0\xa0minutes":
    print("FAIL past-target:", repr(r)); ok=False

# Req4.2 sub-minute
r = timesince(d, d + datetime.timedelta(seconds=30))
print("sub-minute:", repr(r))
if r != "0\xa0minutes":
    print("FAIL sub-minute:", repr(r)); ok=False

# Req4.4 naive unchanged: 90 minutes -> "1 hour, 30 minutes"
dn = datetime.datetime(2023,1,1,0,0,0)
r = timesince(dn, dn + datetime.timedelta(minutes=90))
print("naive 90min:", repr(r))
if r != "1\xa0hour, 30\xa0minutes":
    print("FAIL naive:", repr(r)); ok=False

# Req4.7 custom time_strings
ts = {"minute": "%(num)d min", "hour": "%(num)d hr", "day": "%(num)d d",
      "week": "%(num)d wk", "month": "%(num)d mo", "year": "%(num)d yr"}
r = timesince(dn, dn + datetime.timedelta(minutes=90), time_strings=ts)
print("custom ts:", repr(r))
if r != "1\xa0hr, 30\xa0min":
    print("FAIL custom ts:", repr(r)); ok=False

# Req3.3 long interval year count, aware, ~1000 years
d2 = datetime.datetime(1000,1,1,0,0,0, tzinfo=utc)
now2 = datetime.datetime(2000,1,1,0,0,0, tzinfo=utc)
r = timesince(d2, now2, depth=1)
print("1000yr aware:", repr(r))
if r != "1000\xa0years":
    print("FAIL 1000yr:", repr(r)); ok=False

if not ok:
    raise SystemExit(1)
print("OK")
raise SystemExit(0)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
"""Req4.6: tzinfo reporting no defined UTC offset -> treated as naive, no raise, correct.
Req4.5/4.3: different-timezone instants; date (not datetime) inputs work.
Uses a custom tzinfo whose utcoffset returns None."""
import datetime
import django
from django.conf import settings
if not settings.configured:
    settings.configure(USE_I18N=False, USE_TZ=True, INSTALLED_APPS=[])
django.setup()
from django.utils.timesince import timesince

utc = datetime.timezone.utc
ok = True

class NoOffset(datetime.tzinfo):
    def utcoffset(self, dt): return None
    def dst(self, dt): return None
    def tzname(self, dt): return None

# Req4.6: value with tzinfo but no offset -> naive treatment, long interval, no raise
d = datetime.datetime(2023,1,1,0,0,0, tzinfo=NoOffset())
now = datetime.datetime(2023,2,5,0,0,0, tzinfo=NoOffset())
try:
    r = timesince(d, now)
except Exception as e:
    print("FAIL Req4.6 raised", type(e).__name__, e); ok=False
    r = None
print("no-offset tz:", repr(r))
if r is not None and "month" not in r:
    print("FAIL Req4.6: expected month, got", repr(r)); ok=False

# Req4.3: date inputs (not datetime)
try:
    r = timesince(datetime.date(2023,1,1), datetime.date(2023,2,5))
    print("date inputs:", repr(r))
    if "month" not in r:
        print("FAIL date inputs:", repr(r)); ok=False
except Exception as e:
    print("FAIL date inputs raised", type(e).__name__, e); ok=False

# Req4.5: two different tz representing same/known instants -> based on actual instant
tz_plus2 = datetime.timezone(datetime.timedelta(hours=2))
d = datetime.datetime(2023,1,1,0,0,0, tzinfo=utc)           # instant A
now = datetime.datetime(2023,2,1,2,0,0, tzinfo=tz_plus2)    # = 2023-02-01 00:00 UTC
try:
    r = timesince(d, now)
    print("diff-tz:", repr(r))
    if "month" not in r:
        print("FAIL diff-tz:", repr(r)); ok=False
except Exception as e:
    print("FAIL diff-tz raised", type(e).__name__, e); ok=False

if not ok:
    raise SystemExit(1)
print("OK")
raise SystemExit(0)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Positive control / Req1.1 & 1.3: aware datetime, ~31 days ago -> '1 month', no TypeError.
Holds on patched, must FAIL at base (base raises TypeError)."""
import datetime
import django
from django.conf import settings
if not settings.configured:
    settings.configure(USE_I18N=False, USE_TZ=True, INSTALLED_APPS=[])
django.setup()
from django.utils.timesince import timesince

now = datetime.datetime(2023, 2, 15, 12, 0, 0, tzinfo=datetime.timezone.utc)
d = now - datetime.timedelta(days=31)
try:
    r = timesince(d, now)
except TypeError as e:
    print("FAIL: raised TypeError:", e)
    raise SystemExit(1)
print("observed:", repr(r))
if r != "1\xa0month":
    print("FAIL: expected '1\\xa0month', got", repr(r))
    raise SystemExit(1)
print("OK")
raise SystemExit(0)
```

Prepatch bug re-encoded as an attack: `True`.

Instance: pivot construction in timesince() omitted tzinfo, so aware+long intervals raised TypeError. Gold patch adds tzinfo=d.tzinfo.

Probes (all HOLD on gold-patched tree):
- probe_1 (Req1.1/1.3, POSITIVE CONTROL): aware d ~31 days ago -> '1\xa0month', no TypeError. HOLDS patched, FAILS at base (TypeError). Discriminates.
- probe_2 (Req1.2/3.1): aware Jan-31 start, day-clamp into Feb pivot; no raise/overflow. HOLDS patched, FAILS at base.
- probe_3 (Req2.1/2.3/1.4): 1y1mo1w1d1h interval; depth 1..4 aware==naive; depth-1='1 year', depth-2='1 year, 1 month'; timeuntil aware no-raise. HOLDS.
- probe_4 (Req2.2/2.4): non-adjacent (1y+1h)-> '1 year' only; depth<=0 -> ValueError 'greater than 0' for aware & naive. HOLDS.
- probe_5 (Req4.1/4.2/4.4/4.7/3.3): equal/past->'0 minutes'; sub-minute->'0 minutes'; naive 90min unchanged; custom time_strings honored; ~1000y aware -> '1000 years'. HOLDS.
- probe_6 (Req4.6/4.3/4.5): no-offset tzinfo treated naive; date() inputs; cross-tz instant. HOLDS.

Positive control: FAILS at base (TypeError 'can't subtract offset-naive and offset-aware'), HOLDS patched => prepatch reproduced.

Candidate wrong-fix 'hardcoded_utc_tzinfo' (weak.diff): sets tzinfo=timezone.utc instead of d.tzinfo. This is the lazy fix a weak reading permits (it stops the aware crash). Suite REJECTS it: probe_3 fails (naive long intervals now raise TypeError because pivot is forced aware) and probe_6 fails (naive-via-no-offset and date() inputs raise). Confirms Req2.3/4.3/4.4/4.6 discriminate wrong implementations. No requirements-conforming-yet-nonresolving candidate found; the tzinfo=d.tzinfo behavior is uniquely pinned by the probe suite.

Verdict SOUND: 6 distinct probes all hold on gold-patched tree, positive control discriminates (holds patched / fails base), and >=1 candidate patch is exercised and rejected.

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
"""Positive control / Req1.1 & 1.3: aware datetime, ~31 days ago -> '1 month', no TypeError.
Holds on patched, must FAIL at base (base raises TypeError)."""
import datetime
import django
from django.conf import settings
if not settings.configured:
    settings.configure(USE_I18N=False, USE_TZ=True, INSTALLED_APPS=[])
django.setup()
from django.utils.timesince import timesince

now = datetime.datetime(2023, 2, 15, 12, 0, 0, tzinfo=datetime.timezone.utc)
d = now - datetime.timedelta(days=31)
try:
    r = timesince(d, now)
except TypeError as e:
    print("FAIL: raised TypeError:", e)
    raise SystemExit(1)
print("observed:", repr(r))
if r != "1\xa0month":
    print("FAIL: expected '1\\xa0month', got", repr(r))
    raise SystemExit(1)
print("OK")
raise SystemExit(0)
```

Prepatch bug re-encoded as an attack: `True`.

Instance: pivot construction in timesince() omitted tzinfo, so aware+long intervals raised TypeError. Gold patch adds tzinfo=d.tzinfo.

Probes (all HOLD on gold-patched tree):
- probe_1 (Req1.1/1.3, POSITIVE CONTROL): aware d ~31 days ago -> '1\xa0month', no TypeError. HOLDS patched, FAILS at base (TypeError). Discriminates.
- probe_2 (Req1.2/3.1): aware Jan-31 start, day-clamp into Feb pivot; no raise/overflow. HOLDS patched, FAILS at base.
- probe_3 (Req2.1/2.3/1.4): 1y1mo1w1d1h interval; depth 1..4 aware==naive; depth-1='1 year', depth-2='1 year, 1 month'; timeuntil aware no-raise. HOLDS.
- probe_4 (Req2.2/2.4): non-adjacent (1y+1h)-> '1 year' only; depth<=0 -> ValueError 'greater than 0' for aware & naive. HOLDS.
- probe_5 (Req4.1/4.2/4.4/4.7/3.3): equal/past->'0 minutes'; sub-minute->'0 minutes'; naive 90min unchanged; custom time_strings honored; ~1000y aware -> '1000 years'. HOLDS.
- probe_6 (Req4.6/4.3/4.5): no-offset tzinfo treated naive; date() inputs; cross-tz instant. HOLDS.

Positive control: FAILS at base (TypeError 'can't subtract offset-naive and offset-aware'), HOLDS patched => prepatch reproduced.

Candidate wrong-fix 'hardcoded_utc_tzinfo' (weak.diff): sets tzinfo=timezone.utc instead of d.tzinfo. This is the lazy fix a weak reading permits (it stops the aware crash). Suite REJECTS it: probe_3 fails (naive long intervals now raise TypeError because pivot is forced aware) and probe_6 fails (naive-via-no-offset and date() inputs raise). Confirms Req2.3/4.3/4.4/4.6 discriminate wrong implementations. No requirements-conforming-yet-nonresolving candidate found; the tzinfo=d.tzinfo behavior is uniquely pinned by the probe suite.

Verdict SOUND: 6 distinct probes all hold on gold-patched tree, positive control discriminates (holds patched / fails base), and >=1 candidate patch is exercised and rejected.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** The modeling boundary is correct: requirements pin the changed observable behavior (aware long intervals no longer raising, with pivot carrying d's tzinfo) rather than a narrow slice. R1.2/R3.1 describe internal pivot mechanics (tzinfo propagation, day-clamp via min(MONTHS_DAYS[...], d.day)) that match the actual code lines 93-100. R4 correctly frames preserved behaviors as unchanged. Base-vs-patched probe confirms the divergence is exactly the TypeError fix. No mandated-but-absent, forbidden-but-present, or invented behavior detected.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The requirements translate test-checked behaviors into behavioral requirements without transmitting the hidden tests. The core fix (pivot must carry d.tzinfo), the module (django/utils/timesince.py), the TypeError, USE_TZ=True, the >1 month crash, the L93-L100 pivot construction, and the days=31 -> '1 month' example are ALL already in the public problem_statement (which even names the fix 'Adding 0, d.tzinfo arguments'). Requirements naming leap-year, thousand-years, and months-edge correctness (Req 3.2-3.4) do conceptually align with hidden test method names (test_leap_year_new_years_eve, test_thousand_years_ago, test_months_edge), but they are stated as generic calendar-correctness behaviors with no quoted test code, no test datetime literals, no test paths, no class/decorator names (TZAwareTimesinceTests / override_settings / requires_tz_support), and no test ids. The depth ValueError message 'depth must be greater than 0' matches the test assertion string but is a pre-existing part of the function's public contract, not fix-invented content. Naming modules/functions and describing behavior is legitimate localization; nothing reconstructs the hidden tests.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
