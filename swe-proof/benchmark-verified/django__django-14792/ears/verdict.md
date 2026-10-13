# P2 adversarial audit — django__django-14792

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 8 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 8 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py`, `probe_7.py`, `probe_8.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (8):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
import pytz
from django.utils.timezone import _get_timezone_name
tz = pytz.timezone("Etc/GMT-10")
r = _get_timezone_name(tz)
print("result:", repr(r), "tzname:", repr(tz.tzname(None)), "str:", repr(str(tz)))
assert r == "+10", "expected '+10' got %r" % (r,)
print("OK")
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
import datetime
from django.utils.timezone import _get_timezone_name
tz = datetime.timezone(datetime.timedelta(hours=5), "Weird/Name")
r = _get_timezone_name(tz)
print("result:", repr(r), "tzname:", repr(tz.tzname(None)))
assert r == "Weird/Name", r
print("OK")
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
import datetime
from django.utils.timezone import _get_timezone_name
class NoName(datetime.tzinfo):
    def utcoffset(self, dt): return datetime.timedelta(0)
    def tzname(self, dt): return None
    def __str__(self): return "FALLBACK_STR"
tz = NoName()
r = _get_timezone_name(tz)
print("result:", repr(r), "tzname:", repr(tz.tzname(None)), "str:", repr(str(tz)))
assert r == "FALLBACK_STR", r
print("OK")
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
import datetime
from django.utils.timezone import _get_timezone_name
class EmptyName(datetime.tzinfo):
    def utcoffset(self, dt): return datetime.timedelta(0)
    def tzname(self, dt): return ""
    def __str__(self): return "EMPTY_FALLBACK"
tz = EmptyName()
r = _get_timezone_name(tz)
print("result:", repr(r), "str:", repr(str(tz)))
assert r == "EMPTY_FALLBACK", r
print("OK")
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
import pytz
from django.utils.timezone import _get_timezone_name
tz = pytz.timezone("Europe/Paris")
r = _get_timezone_name(tz)
tn = tz.tzname(None)
print("result:", repr(r), "tzname:", repr(tn), "str:", repr(str(tz)))
assert tn, "tzname empty"
assert r == tn, (r, tn)
print("OK")
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
from django.conf import settings
if not settings.configured:
    settings.configure(USE_TZ=True, TIME_ZONE="UTC")
import pytz
from django.utils import timezone as tz
tz.activate(pytz.timezone("Etc/GMT-10"))
cur = tz.get_current_timezone_name()
print("current:", repr(cur))
assert cur == "+10", cur
tz.deactivate()
# default zone name delegates too
dn = tz.get_default_timezone_name()
print("default:", repr(dn))
print("OK")
```

Attack 7 — `probe_7.py` → holds on the patched tree (good)

```python
import datetime
from django.utils.timezone import is_aware, is_naive
naive = datetime.datetime(2020,1,1,12,0)
aware = datetime.datetime(2020,1,1,12,0, tzinfo=datetime.timezone.utc)
print("naive:", is_aware(naive), is_naive(naive))
print("aware:", is_aware(aware), is_naive(aware))
assert is_aware(naive) is False and is_naive(naive) is True
assert is_aware(aware) is True and is_naive(aware) is False
print("OK")
```

Attack 8 — `probe_8.py` → holds on the patched tree (good)

```python
import datetime
from django.utils.timezone import _get_timezone_name
tz = datetime.timezone(datetime.timedelta(hours=-7))
r = _get_timezone_name(tz)
print("result:", repr(r), "tzname:", repr(tz.tzname(None)))
assert r == tz.tzname(None), r
assert r == "UTC-07:00", r
print("OK")
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
import pytz
from django.utils.timezone import _get_timezone_name
tz = pytz.timezone("Etc/GMT-10")
r = _get_timezone_name(tz)
print("result:", repr(r), "tzname:", repr(tz.tzname(None)), "str:", repr(str(tz)))
assert r == "+10", "expected '+10' got %r" % (r,)
print("OK")
```

Prepatch bug re-encoded as an attack: `True`.

Env: py3.8, pytz 2024.2, NO zoneinfo (so zoneinfo-specific criteria are exercised via pytz + datetime.timezone equivalents). Gold patch: `_get_timezone_name` returns `timezone.tzname(None) or str(timezone)`.

Probes (all HOLD on patched tree):
- probe_1 (R2.2, POSITIVE CONTROL): pytz Etc/GMT-10 -> '+10'. FAILS at base ('Etc/GMT-10'), HOLDS patched -> discriminates.
- probe_2 (R1.1): datetime.timezone with explicit name -> returns tzname exactly ('Weird/Name').
- probe_3 (R1.2): custom tzinfo with tzname(None)==None -> falls back to str(timezone).
- probe_4 (R1.2/R1.3): tzname(None)=='' (empty) -> falls back to str(timezone).
- probe_5 (R2.4): pytz named zone Europe/Paris -> reported tzname(None), non-empty; matches str here.
- probe_6 (R3.1): get_current_timezone_name delegates -> '+10' for active fixed zone; FAILS at base too.
- probe_7 (R3.2): is_aware/is_naive correctness on naive vs aware datetimes.
- probe_8 (R2.3): datetime.timezone(-7h) default -> 'UTC-07:00' (its tzname).

Weak candidate (type_branching_weak): applies the tzname-or-str rule ONLY when isinstance(timezone, datetime.timezone), else str(timezone). This is the lazy fix a weak reading permits, but it VIOLATES R2.1 (impl-independence) and R2.2 (pytz/zoneinfo fixed-offset case). REJECTED by probe_1 and probe_6 (pytz Etc/GMT-10 still yields 'Etc/GMT-10'). Confirms the suite discriminates wrong implementations.

All 8 probes hold on patched; positive control discriminates base vs patched; >=1 wrong candidate exercised and rejected. Verdict SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 8 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 8 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py`, `probe_7.py`, `probe_8.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (8):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts, and on this backend both roles put it through the same derivation: every block below is a requirement probe run on the gold-patched tree, and the `machine verdict:` line each role publishes above reports BOTH that its probes hold there and how many candidate patches the probe suite rejected — so the two roles re-ran ONE probe suite and each recorded its own outcome for every probe in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `probe_1.py` → holds on the patched tree (good)

Attack 2 — `probe_2.py` → holds on the patched tree (good)

Attack 3 — `probe_3.py` → holds on the patched tree (good)

Attack 4 — `probe_4.py` → holds on the patched tree (good)

Attack 5 — `probe_5.py` → holds on the patched tree (good)

Attack 6 — `probe_6.py` → holds on the patched tree (good)

Attack 7 — `probe_7.py` → holds on the patched tree (good)

Attack 8 — `probe_8.py` → holds on the patched tree (good)

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
import pytz
from django.utils.timezone import _get_timezone_name
tz = pytz.timezone("Etc/GMT-10")
r = _get_timezone_name(tz)
print("result:", repr(r), "tzname:", repr(tz.tzname(None)), "str:", repr(str(tz)))
assert r == "+10", "expected '+10' got %r" % (r,)
print("OK")
```

Prepatch bug re-encoded as an attack: `True`.

Env: py3.8, pytz 2024.2, NO zoneinfo (so zoneinfo-specific criteria are exercised via pytz + datetime.timezone equivalents). Gold patch: `_get_timezone_name` returns `timezone.tzname(None) or str(timezone)`.

Probes (all HOLD on patched tree):
- probe_1 (R2.2, POSITIVE CONTROL): pytz Etc/GMT-10 -> '+10'. FAILS at base ('Etc/GMT-10'), HOLDS patched -> discriminates.
- probe_2 (R1.1): datetime.timezone with explicit name -> returns tzname exactly ('Weird/Name').
- probe_3 (R1.2): custom tzinfo with tzname(None)==None -> falls back to str(timezone).
- probe_4 (R1.2/R1.3): tzname(None)=='' (empty) -> falls back to str(timezone).
- probe_5 (R2.4): pytz named zone Europe/Paris -> reported tzname(None), non-empty; matches str here.
- probe_6 (R3.1): get_current_timezone_name delegates -> '+10' for active fixed zone; FAILS at base too.
- probe_7 (R3.2): is_aware/is_naive correctness on naive vs aware datetimes.
- probe_8 (R2.3): datetime.timezone(-7h) default -> 'UTC-07:00' (its tzname).

Weak candidate (type_branching_weak): applies the tzname-or-str rule ONLY when isinstance(timezone, datetime.timezone), else str(timezone). This is the lazy fix a weak reading permits, but it VIOLATES R2.1 (impl-independence) and R2.2 (pytz/zoneinfo fixed-offset case). REJECTED by probe_1 and probe_6 (pytz Etc/GMT-10 still yields 'Etc/GMT-10'). Confirms the suite discriminates wrong implementations.

All 8 probes hold on patched; positive control discriminates base vs patched; >=1 wrong candidate exercised and rejected. Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Probe (patched vs --base) verified: patched Etc/GMT-10→'+10', base→'Etc/GMT-10'; named zones unchanged in both. Req 1 models the changed observable behavior at the correct boundary (the `or` selection over the full string form), not a narrow branch. Req 2 correctly asserts implementation-independence (single expression, no type dispatch) and pins the publicly-reported '+10' case. Req 3 is standard regression protection over untouched helpers (matches the one-line diff scope). zoneinfo unavailable in image (py<3.9) but requirement's zoneinfo claim is equivalent to pytz path and consistent with the impl-agnostic single expression, so not a divergence. FAITHFUL.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** requirements.md describes the behavior of the one-line gold fix (_get_timezone_name = tzname(None) or str(timezone)). All concrete example values it uses ('Etc/GMT-10' -> '+10', pytz/zoneinfo equivalence, Trunc/Extract, AT TIME ZONE, the get_tzname chain) come straight from the public problem_statement. Naming _get_timezone_name and the surrounding helpers is legitimate localization. Requirements 2.3/2.4 describe the datetime.timezone-with-name and named-zone cases as general tzname(None) behavior; they do NOT reproduce the hidden test's distinguishing literals — 'UTC+10:00' and 'Europe/Madrid' never appear, and no test function names, file paths, parametrization ids, or fix-invented identifiers are present (the gold introduces no new identifiers). The three-implementation enumeration is the publicly stated goal, not a leak of the parametrized table.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
