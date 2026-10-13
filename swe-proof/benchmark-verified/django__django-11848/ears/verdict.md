# P2 adversarial audit — django__django-11848

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 5 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 5 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 5 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (5):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
"""Positive control + R1 core (R1.1-R1.6).
Encodes the sliding current-year-relative expansion. Uses yy=70 which the
base fixed-70 rule expands to 1970 but the correct rule (current year 2026)
must expand to 2070 -> discriminates base vs patched.
Exits 0 iff parse_http_date expands each two-digit year per the sliding rule.
"""
import calendar, datetime
from django.utils.http import parse_http_date

def expand(yy, cur):
    cur2 = cur % 100
    century = cur - cur2
    if yy - cur2 > 50:
        return yy + century - 100
    return yy + century

def rfc850(yy, mon, day, h, mi, s, wd="Sunday"):
    return "%s, %02d-%s-%02d %02d:%02d:%02d GMT" % (wd, day, mon, yy, h, mi, s)

cur = datetime.datetime.utcnow().year
ok = True
# check a spread of two-digit years incl the discriminating one (70) and
# ones on either side of the sliding boundary
for yy in range(0, 100):
    exp_year = expand(yy, cur)
    got = parse_http_date(rfc850(yy, "Nov", 6, 8, 49, 37))
    want = calendar.timegm((exp_year, 11, 6, 8, 49, 37))
    got_year = datetime.datetime.utcfromtimestamp(got).year
    if got != want:
        ok = False
        print("FAIL yy=%02d cur=%d expected_year=%d got_year=%d" % (yy, cur, exp_year, got_year))
        if yy in (70,):
            print("  (this is the base-vs-patched discriminator)")
print("current_year=%d, checked yy=0..99" % cur)
print("HOLDS" if ok else "VIOLATED")
raise SystemExit(0 if ok else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""R2.1 + R2.2: four-digit years used verbatim (no century adjustment) and
RFC 1123 returns correct epoch seconds (UTC). RFC 1123 carries a 4-digit year.
"""
import calendar
from django.utils.http import parse_http_date

ok = True
cases = [
    ("Sun, 06 Nov 1994 08:49:37 GMT", (1994,11,6,8,49,37)),
    ("Mon, 01 Jan 2035 00:00:00 GMT", (2035,1,1,0,0,0)),
    ("Tue, 31 Dec 1899 23:59:59 GMT", (1899,12,31,23,59,59)),
]
for s, t in cases:
    got = parse_http_date(s)
    want = calendar.timegm(t)
    print("%-40s got=%d want=%d" % (s, got, want))
    if got != want:
        ok = False
        print("  FAIL")
print("HOLDS" if ok else "VIOLATED")
raise SystemExit(0 if ok else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""R2.3: asctime format returns correct epoch seconds (UTC). asctime has a
4-digit year and no timezone (assumed GMT).
"""
import calendar
from django.utils.http import parse_http_date

ok = True
cases = [
    ("Sun Nov  6 08:49:37 1994", (1994,11,6,8,49,37)),
    ("Wed Jan  1 00:00:00 2020", (2020,1,1,0,0,0)),
]
for s, t in cases:
    got = parse_http_date(s)
    want = calendar.timegm(t)
    print("%-30r got=%d want=%d" % (s, got, want))
    if got != want:
        ok = False
        print("  FAIL")
print("HOLDS" if ok else "VIOLATED")
raise SystemExit(0 if ok else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""R2.5 + R2.6: invalid input / impossible date raises ValueError; and
R2.7: parse_http_date_safe returns None instead of raising.
"""
from django.utils.http import parse_http_date, parse_http_date_safe

ok = True
bad = [
    "not a date at all",
    "",
    "Sun, 06 Foo 1994 08:49:37 GMT",   # bad month name
    "Sun, 32 Nov 1994 08:49:37 GMT",   # impossible day
    "Sun, 06 Nov 1994 25:49:37 GMT",   # impossible hour
]
for s in bad:
    try:
        r = parse_http_date(s)
        ok = False
        print("FAIL no ValueError for %r -> %r" % (s, r))
    except ValueError:
        print("ok ValueError for %r" % s)
    # safe wrapper must return None (never raise)
    try:
        r = parse_http_date_safe(s)
        if r is not None:
            ok = False
            print("FAIL safe returned %r for %r" % (r, s))
        else:
            print("ok safe->None for %r" % s)
    except Exception as e:
        ok = False
        print("FAIL safe raised %r for %r" % (e, s))
print("HOLDS" if ok else "VIOLATED")
raise SystemExit(0 if ok else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""R1.3/R1.4/R1.5/R1.6 boundary + R2.4 (RFC850 correct epoch).
Focuses on the sliding boundary: the exact yy where placing it in the current
century is <=50 vs >50 years ahead. Also asserts the R1.5 cap: expanded year
is never more than 50 years after current year, and never earlier than
(current_year - 49).
"""
import calendar, datetime
from django.utils.http import parse_http_date

def rfc850(yy):
    return "Sunday, 06-Nov-%02d 08:49:37 GMT" % yy

cur = datetime.datetime.utcnow().year
cur2 = cur % 100
century = cur - cur2
ok = True
for yy in range(0, 100):
    got = parse_http_date(rfc850(yy))
    y = datetime.datetime.utcfromtimestamp(got).year
    # R1.1: last two digits preserved
    if y % 100 != yy:
        ok = False; print("FAIL last-two-digits yy=%02d got_year=%d" % (yy, y))
    # R1.5 cap: not more than 50 years after current
    if y > cur + 50:
        ok = False; print("FAIL >cur+50 yy=%02d got_year=%d" % (yy, y))
    # most-recent-past floor: at least cur-49
    if y < cur - 49:
        ok = False; print("FAIL <cur-49 yy=%02d got_year=%d" % (yy, y))
    # R1.6 biconditional: in current century iff (yy - cur2) <= 50
    in_current_century = (y == yy + century)
    should = (yy - cur2 <= 50)
    if in_current_century != should:
        ok = False
        print("FAIL biconditional yy=%02d got_year=%d in_cur_century=%s should=%s"
              % (yy, y, in_current_century, should))
# spot RFC850 epoch correctness for a specific expanded year
got = parse_http_date("Sunday, 06-Nov-94 08:49:37 GMT")
exp = 94 + century if (94 - cur2 <= 50) else 94 + century - 100
print("94 -> %d, epoch match=%s" % (exp, got == calendar.timegm((exp,11,6,8,49,37))))
if got != calendar.timegm((exp,11,6,8,49,37)):
    ok = False
print("current_year=%d boundary yy where (yy-cur2)==50 => yy=%d" % (cur, cur2+50))
print("HOLDS" if ok else "VIOLATED")
raise SystemExit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Positive control + R1 core (R1.1-R1.6).
Encodes the sliding current-year-relative expansion. Uses yy=70 which the
base fixed-70 rule expands to 1970 but the correct rule (current year 2026)
must expand to 2070 -> discriminates base vs patched.
Exits 0 iff parse_http_date expands each two-digit year per the sliding rule.
"""
import calendar, datetime
from django.utils.http import parse_http_date

def expand(yy, cur):
    cur2 = cur % 100
    century = cur - cur2
    if yy - cur2 > 50:
        return yy + century - 100
    return yy + century

def rfc850(yy, mon, day, h, mi, s, wd="Sunday"):
    return "%s, %02d-%s-%02d %02d:%02d:%02d GMT" % (wd, day, mon, yy, h, mi, s)

cur = datetime.datetime.utcnow().year
ok = True
# check a spread of two-digit years incl the discriminating one (70) and
# ones on either side of the sliding boundary
for yy in range(0, 100):
    exp_year = expand(yy, cur)
    got = parse_http_date(rfc850(yy, "Nov", 6, 8, 49, 37))
    want = calendar.timegm((exp_year, 11, 6, 8, 49, 37))
    got_year = datetime.datetime.utcfromtimestamp(got).year
    if got != want:
        ok = False
        print("FAIL yy=%02d cur=%d expected_year=%d got_year=%d" % (yy, cur, exp_year, got_year))
        if yy in (70,):
            print("  (this is the base-vs-patched discriminator)")
print("current_year=%d, checked yy=0..99" % cur)
print("HOLDS" if ok else "VIOLATED")
raise SystemExit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

5 distinct probes covering the requirements, all HOLD on gold-patched tree (current_year=2026 in image).

Probe->requirement mapping:
- probe_1 (R1.1-R1.6, positive control): sliding current-year-relative expansion across all yy=0..99, compared to a reference implementation of the >50-rule. PATCHED: HOLDS. BASE: FAILS (base fixed-70 rule maps yy=71..76 to 1971..1976 instead of 2071..2076) -> discriminates.
- probe_2 (R2.1 verbatim 4-digit year, R2.2 RFC1123 epoch): HOLDS patched (incl. pre-1970 negative epoch and future 2035).
- probe_3 (R2.3 asctime epoch): HOLDS patched.
- probe_4 (R2.5 invalid raises ValueError, R2.6 impossible calendar date raises, R2.7 parse_http_date_safe->None): HOLDS patched.
- probe_5 (R1.3/1.4/1.5/1.6 boundary + R1.1 last-two-digits + R2.4 RFC850 epoch): asserts last-two-digits preserved, year<=cur+50 cap, year>=cur-49 floor, and the exact R1.6 biconditional (in current century iff yy-cur2<=50). PATCHED: HOLDS. BASE: FAILS.

Discriminating power confirmed against a plausibly-wrong alternative:
- weak_offbyone.diff: identical to gold except the century-boundary test uses '>= 50' instead of '> 50'. Applies cleanly at base. REJECTED by probe_1 and probe_5 (yy=76: gold/requirements put it in current century 2076 since 76-26=50 is not >50; the off-by-one wrongly pushes it to 1976). This shows the suite catches an off-by-one at the sliding boundary mandated by R1.6.

All needed runs completed. >=5 probes hold, positive control discriminates (base fails, patched holds), and a requirements-violating candidate patch is rejected by the suite.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 5 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 5 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 5 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

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
"""Positive control + R1 core (R1.1-R1.6).
Encodes the sliding current-year-relative expansion. Uses yy=70 which the
base fixed-70 rule expands to 1970 but the correct rule (current year 2026)
must expand to 2070 -> discriminates base vs patched.
Exits 0 iff parse_http_date expands each two-digit year per the sliding rule.
"""
import calendar, datetime
from django.utils.http import parse_http_date

def expand(yy, cur):
    cur2 = cur % 100
    century = cur - cur2
    if yy - cur2 > 50:
        return yy + century - 100
    return yy + century

def rfc850(yy, mon, day, h, mi, s, wd="Sunday"):
    return "%s, %02d-%s-%02d %02d:%02d:%02d GMT" % (wd, day, mon, yy, h, mi, s)

cur = datetime.datetime.utcnow().year
ok = True
# check a spread of two-digit years incl the discriminating one (70) and
# ones on either side of the sliding boundary
for yy in range(0, 100):
    exp_year = expand(yy, cur)
    got = parse_http_date(rfc850(yy, "Nov", 6, 8, 49, 37))
    want = calendar.timegm((exp_year, 11, 6, 8, 49, 37))
    got_year = datetime.datetime.utcfromtimestamp(got).year
    if got != want:
        ok = False
        print("FAIL yy=%02d cur=%d expected_year=%d got_year=%d" % (yy, cur, exp_year, got_year))
        if yy in (70,):
            print("  (this is the base-vs-patched discriminator)")
print("current_year=%d, checked yy=0..99" % cur)
print("HOLDS" if ok else "VIOLATED")
raise SystemExit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

5 distinct probes covering the requirements, all HOLD on gold-patched tree (current_year=2026 in image).

Probe->requirement mapping:
- probe_1 (R1.1-R1.6, positive control): sliding current-year-relative expansion across all yy=0..99, compared to a reference implementation of the >50-rule. PATCHED: HOLDS. BASE: FAILS (base fixed-70 rule maps yy=71..76 to 1971..1976 instead of 2071..2076) -> discriminates.
- probe_2 (R2.1 verbatim 4-digit year, R2.2 RFC1123 epoch): HOLDS patched (incl. pre-1970 negative epoch and future 2035).
- probe_3 (R2.3 asctime epoch): HOLDS patched.
- probe_4 (R2.5 invalid raises ValueError, R2.6 impossible calendar date raises, R2.7 parse_http_date_safe->None): HOLDS patched.
- probe_5 (R1.3/1.4/1.5/1.6 boundary + R1.1 last-two-digits + R2.4 RFC850 epoch): asserts last-two-digits preserved, year<=cur+50 cap, year>=cur-49 floor, and the exact R1.6 biconditional (in current century iff yy-cur2<=50). PATCHED: HOLDS. BASE: FAILS.

Discriminating power confirmed against a plausibly-wrong alternative:
- weak_offbyone.diff: identical to gold except the century-boundary test uses '>= 50' instead of '> 50'. Applies cleanly at base. REJECTED by probe_1 and probe_5 (yy=76: gold/requirements put it in current century 2076 since 76-26=50 is not >50; the off-by-one wrongly pushes it to 1976). This shows the suite catches an off-by-one at the sliding boundary mandated by R1.6.

All needed runs completed. >=5 probes hold, positive control discriminates (base fails, patched holds), and a requirements-violating candidate patch is rejected by the suite.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** The patch replaces the fixed <70 → 2000s / else 1900s rule with current_year = datetime.datetime.utcnow().year; current_century = current_year - (current_year%100); if year-(current_year%100) > 50: year += current_century-100 else year += current_century. Requirement 1.6 correctly restates this branch condition (`two - last2 <= 50` for current century). Requirement 2 (RFC1123/asctime/4-digit/ValueError/safe wrapper) covers the preserved surrounding behavior the patch does not touch. Probe HOLDS exit=0 on the patched tree.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The requirements restate the sliding, current-year-relative 50-year rule, which is public in the problem_statement (verbatim RFC 7231 quote) and the 0-69/70-99 hard-coded rule it replaces (also in problem_statement). Module/function names (parse_http_date, parse_http_date_safe, django/utils/http.py) are legitimate localization. Req 1.6's boundary condition ('two-digit value minus last two digits of current year no greater than 50') mirrors the gold's `year - (current_year % 100) > 50`, but this is the RFC-mandated algorithm itself — legitimate behavioral description, not test transmission. UTC reference-year (Req 1.2) reflects gold's datetime.utcnow(); this is a modeling boundary, also implied by problem_statement's 'current year'. Critically, the document does NOT enumerate the hidden test's specific parametrized cases (utcnow pins 2019/2020/2048; years 69,70,94,70,71,00,99), test names (test_parsing_rfc850, test_parsing_year_less_than_70), file path (tests/utils_tests/test_http.py), or the mock.patch scaffolding. No test-shaped enumeration mirroring the parametrization. No fix-invented identifiers leaked.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
