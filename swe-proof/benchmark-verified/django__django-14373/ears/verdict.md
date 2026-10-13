# P2 adversarial audit — django__django-14373

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
# Req1 c2/c3: Y for year 1 -> '0001', year 999 -> '0999'  (POSITIVE CONTROL)
import datetime
from django.utils.dateformat import format
d1 = datetime.date(1, 1, 1)
d999 = datetime.date(999, 6, 15)
r1 = format(d1, 'Y')
r999 = format(d999, 'Y')
print("year1 ->", repr(r1), "; year999 ->", repr(r999))
ok = (r1 == '0001') and (r999 == '0999')
raise SystemExit(0 if ok else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
# Req1 c4: year >=1000 renders full, no truncation/extra zeros
import datetime
from django.utils.dateformat import format
r = format(datetime.date(1999,1,1), 'Y')
r2 = format(datetime.date(9999,1,1), 'Y')
print("1999 ->", repr(r), "; 9999 ->", repr(r2))
ok = (r == '1999') and (r2 == '9999')
raise SystemExit(0 if ok else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
# Req1 c5/c6: Y renders only decimal digits, leading zeros survive joining in surrounding text
import datetime
from django.utils.dateformat import format
r = format(datetime.date(1,1,1), r'Y-\Y')  # literal Y after backslash
print("format 'Y-\\Y' ->", repr(r))
# Y=0001, literal Y => '0001-Y'
ok = (r == '0001-Y')
# also ensure no sign/separator: pure digits for standalone
r2 = format(datetime.date(5,1,1), 'Y')
print("year5 ->", repr(r2))
ok = ok and r2 == '0005' and r2.isdigit()
raise SystemExit(0 if ok else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
# Req2: y specifier unchanged - last two digits, width 2
import datetime
from django.utils.dateformat import format
cases = {5: '05', 1: '01', 999: '99', 2021: '21', 100: '00'}
allok = True
for yr, exp in cases.items():
    r = format(datetime.date(yr,1,1), 'y')
    print("y for", yr, "->", repr(r), "exp", exp)
    if r != exp or len(r) != 2:
        allok = False
raise SystemExit(0 if allok else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
# Req3: other specifiers unchanged; escapes literal; empty string; time spec on date raises
from django.conf import settings
if not settings.configured:
    settings.configure(USE_I18N=False, USE_L10N=False, USE_TZ=False)
import django; django.setup()
import datetime
from django.utils.dateformat import format
d = datetime.date(2021, 3, 9)  # Tuesday
day = format(d, 'd'); mon = format(d, 'm'); wd = format(d, 'D')
print("d,m,D ->", day, mon, wd)
esc = format(d, r'\Y\d')  # both escaped -> literal 'Yd'
print("escaped ->", repr(esc))
empty = format(d, '')
print("empty ->", repr(empty))
raised = False
try:
    format(d, 'H')  # time spec on date
except Exception as e:
    raised = True
    print("time-on-date raised:", type(e).__name__)
ok = (day=='09' and mon=='03' and wd=='Tue' and esc=='Yd' and empty=='' and raised)
raise SystemExit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
# Req1 c2/c3: Y for year 1 -> '0001', year 999 -> '0999'  (POSITIVE CONTROL)
import datetime
from django.utils.dateformat import format
d1 = datetime.date(1, 1, 1)
d999 = datetime.date(999, 6, 15)
r1 = format(d1, 'Y')
r999 = format(d999, 'Y')
print("year1 ->", repr(r1), "; year999 ->", repr(r999))
ok = (r1 == '0001') and (r999 == '0999')
raise SystemExit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Requirements mandate Y specifier always renders zero-padded 4-digit year (gold: `return '%04d' % self.data.year`).

Probes (all on PATCHED tree unless noted):
- probe_1 (Req1 c2/c3, POSITIVE CONTROL): year 1 -> '0001', year 999 -> '0999'. HOLDS patched (exit0); FAILS at base ('1'/'999'). Discriminates.
- probe_2 (Req1 c4): year 1999 -> '1999', 9999 -> '9999' (no truncation/extra zeros). HOLDS. (Initially probed year 12345 but datetime.date max year is 9999 -> ValueError; corrected to 9999.)
- probe_3 (Req1 c5/c6): standalone Y=='0005' pure digits, and 'Y-\Y' -> '0001-Y' proving leading zeros survive joining + escape handling. HOLDS.
- probe_4 (Req2): y specifier last-two-digits width-2 for {5,1,999,2021,100} -> {'05','01','99','21','00'}. HOLDS.
- probe_5 (Req3): d/m/D unchanged, '\Y\d'->'Yd' literal escape, empty format ''->'' , time spec 'H' on date raises TypeError. HOLDS (settings configured in-probe to avoid ImproperlyConfigured).

Candidate wrong-fix patches (both apply at base):
- weak_space (`'%4d'`, space-pad): REJECTED by probe_1 (year1->'   1') and probe_3 (year5->'   5'). Requirements c1/c5 demand '0'-padding and only decimal digits.
- weak_partial (only pad when year>=1000, else str): REJECTED by probe_1 (year1->'1') and probe_3. Partial fix leaving <1000 broken.

Both wrong candidates rejected => suite discriminates wrong implementations. All 5 probes hold on patched tree; positive control holds patched and fails at base. No TOO-WEAK or VIOLATION finding.

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
# Req1 c2/c3: Y for year 1 -> '0001', year 999 -> '0999'  (POSITIVE CONTROL)
import datetime
from django.utils.dateformat import format
d1 = datetime.date(1, 1, 1)
d999 = datetime.date(999, 6, 15)
r1 = format(d1, 'Y')
r999 = format(d999, 'Y')
print("year1 ->", repr(r1), "; year999 ->", repr(r999))
ok = (r1 == '0001') and (r999 == '0999')
raise SystemExit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Requirements mandate Y specifier always renders zero-padded 4-digit year (gold: `return '%04d' % self.data.year`).

Probes (all on PATCHED tree unless noted):
- probe_1 (Req1 c2/c3, POSITIVE CONTROL): year 1 -> '0001', year 999 -> '0999'. HOLDS patched (exit0); FAILS at base ('1'/'999'). Discriminates.
- probe_2 (Req1 c4): year 1999 -> '1999', 9999 -> '9999' (no truncation/extra zeros). HOLDS. (Initially probed year 12345 but datetime.date max year is 9999 -> ValueError; corrected to 9999.)
- probe_3 (Req1 c5/c6): standalone Y=='0005' pure digits, and 'Y-\Y' -> '0001-Y' proving leading zeros survive joining + escape handling. HOLDS.
- probe_4 (Req2): y specifier last-two-digits width-2 for {5,1,999,2021,100} -> {'05','01','99','21','00'}. HOLDS.
- probe_5 (Req3): d/m/D unchanged, '\Y\d'->'Yd' literal escape, empty format ''->'' , time spec 'H' on date raises TypeError. HOLDS (settings configured in-probe to avoid ImproperlyConfigured).

Candidate wrong-fix patches (both apply at base):
- weak_space (`'%4d'`, space-pad): REJECTED by probe_1 (year1->'   1') and probe_3 (year5->'   5'). Requirements c1/c5 demand '0'-padding and only decimal digits.
- weak_partial (only pad when year>=1000, else str): REJECTED by probe_1 (year1->'1') and probe_3. Partial fix leaving <1000 broken.

Both wrong candidates rejected => suite discriminates wrong implementations. All 5 probes hold on patched tree; positive control holds patched and fails at base. No TOO-WEAK or VIOLATION finding.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Base (unpatched) probe VIOLATED at year=1 ('1' vs '0001'), confirming the twin discriminator is exactly the padded-Y behavior the requirements model. Note '%04d' pads to minimum width 4 without truncating longer years, exactly as R1.4 states. Requirements correctly scope the change to Y only and leave y/others untouched.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The requirements describe the Y-specifier zero-padding behavior in prose and name only public/legitimate structures (django.utils.dateformat, DateFormat/TimeFormat, Formatter.format, str() coercion, the Y and y specifiers) — permissible localization. No test names, file paths, test ids, or quoted test/gold code appear. The gold patch ('%04d' % self.data.year) invents no identifiers to leak. The specific examples year 1 -> '0001' and year 999 -> '0999' (Req 1 criteria 2-3) coincide with the two assertions in the hidden test_Y_format_year_before_1000, but these are the natural documented boundary values (smallest year, largest year below 1000) derivable directly from the public problem_statement ('four-digit year... not the case for year < 1000'); the '1999' example is straight from the public docstring. The y-specifier requirement describes the documented modulo-100 contract and does NOT reproduce the hidden y-test's parametrized cases (476->76, 42->42, etc.). This is behavior-as-prose, not test reconstruction.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
