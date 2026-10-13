# P2 adversarial audit — django__django-13670

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

Counterexample / evidence:

```
Weak candidate `return str(self.data.year)[-2:]` (last-two-chars, no zero-pad) satisfies Req1.1/1.3 and all Req2 regressions but FAILS Req1.2/1.4/1.5: year 9 -> '9' (expected '09'), years 1/5/9 give length-1 output. Probes 2 and 3 reject it. This is the lazy fix a weak reading of the requirements would permit, and the probe suite correctly discriminates it.
```

**Attacks re-run (6):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
import sys, datetime
from django.utils import dateformat
# Req1.3 / positive control: 3-digit year 123 -> 'y' == '23' (last two digits), not old '3'
d = datetime.date(123, 4, 5)
out = dateformat.format(d, 'y')
print("year=123 y=%r" % out)
sys.exit(0 if out == '23' else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
import sys, datetime
from django.utils import dateformat
# Req1.2 / 1.4: single-digit year 9 -> '09' (zero-padded), old slicing gives ''
d = datetime.date(9, 1, 1)
out = dateformat.format(d, 'y')
print("year=9 y=%r" % out)
sys.exit(0 if out == '09' else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
import sys, datetime
from django.utils import dateformat
# Req1.5: y output always length 2 across a wide range of years incl <1000
bad = []
for yr in [1, 5, 9, 10, 23, 99, 100, 105, 123, 999, 1000, 1979, 2000, 2005, 2021, 9999]:
    out = dateformat.format(datetime.date(yr, 6, 15), 'y')
    expect = '%02d' % (yr % 100)
    if len(out) != 2 or out != expect:
        bad.append((yr, out, expect))
print("mismatches=%r" % bad)
sys.exit(0 if not bad else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
import sys, datetime
from django.utils import dateformat
# Req2.1 regression: year >= 1000 unchanged, 1979 -> '79'
out = dateformat.format(datetime.date(1979, 7, 4), 'y')
print("year=1979 y=%r" % out)
sys.exit(0 if out == '79' else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
import sys, datetime
from django.utils import dateformat
# Req2.2/2.4: Y unchanged (full year); mixed date format substitutes independently,
# literal (escaped) preserved, other date specifiers (d,m) unaffected. Sub-1000 year.
d = datetime.date(123, 4, 5)
Y = dateformat.format(d, 'Y')
mixed = dateformat.format(d, 'd/m/y')       # day=05 month=04 year->23
esc = dateformat.format(d, r'\y=y')         # literal 'y' + '=' + real y -> 'y=23'
print("Y=%r mixed=%r esc=%r" % (Y, mixed, esc))
ok = (Y == '123') and (mixed == '05/04/23') and (esc == 'y=23')
sys.exit(0 if ok else 1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
import sys, datetime
from django.conf import settings
if not settings.configured:
    settings.configure(USE_TZ=False, USE_I18N=False)
import django
django.setup()
from django.utils import dateformat
# Req2.3 regression: other time specifiers unchanged on a normal datetime
dt = datetime.datetime(2021, 3, 9, 14, 5, 6)
out = dateformat.format(dt, 'Y-m-d H:i:s')
print("full=%r" % out)
sys.exit(0 if out == '2021-03-09 14:05:06' else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
import sys, datetime
from django.utils import dateformat
# Req1.3 / positive control: 3-digit year 123 -> 'y' == '23' (last two digits), not old '3'
d = datetime.date(123, 4, 5)
out = dateformat.format(d, 'y')
print("year=123 y=%r" % out)
sys.exit(0 if out == '23' else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Gold patch: `return '%02d' % (self.data.year % 100)`.

Probe->requirement mapping and results (PATCHED / BASE / WEAK):
- probe_1 (Req1.3, POSITIVE CONTROL): year 123 -> 'y'=='23'. PATCHED HOLDS('23'), BASE FAILS('3'), WEAK HOLDS. Discriminates base.
- probe_2 (Req1.2/1.4): year 9 -> '09'. PATCHED HOLDS, BASE FAILS(''), WEAK REJECTS('9').
- probe_3 (Req1.5): y length==2 and ==year%%100 across [1..9999] incl <1000. PATCHED HOLDS, BASE FAILS(many), WEAK REJECTS(years 1/5/9).
- probe_4 (Req2.1): year 1979 -> '79' unchanged. HOLDS on all trees.
- probe_5 (Req2.2/2.4): Y=='123' full year; mixed 'd/m/y'->'05/04/23'; escaped literal '\y=y'->'y=23'; independent substitution + literal preservation. HOLDS patched/weak.
- probe_6 (Req2.3): datetime 'Y-m-d H:i:s' -> '2021-03-09 14:05:06' other specifiers unchanged (settings.configure needed for TIME_ZONE). HOLDS patched/weak.

>=5 distinct probes all hold on patched tree; positive control discriminates (holds patched, fails base); >=1 candidate patch exercised and REJECTED by the suite. No requirements-conforming alternative found that would misresolve. Verdict SOUND (advisory).

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 6 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 6 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

Counterexample / evidence:

```
Weak candidate `return str(self.data.year)[-2:]` (last-two-chars, no zero-pad) satisfies Req1.1/1.3 and all Req2 regressions but FAILS Req1.2/1.4/1.5: year 9 -> '9' (expected '09'), years 1/5/9 give length-1 output. Probes 2 and 3 reject it. This is the lazy fix a weak reading of the requirements would permit, and the probe suite correctly discriminates it.
```

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
import sys, datetime
from django.utils import dateformat
# Req1.3 / positive control: 3-digit year 123 -> 'y' == '23' (last two digits), not old '3'
d = datetime.date(123, 4, 5)
out = dateformat.format(d, 'y')
print("year=123 y=%r" % out)
sys.exit(0 if out == '23' else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Gold patch: `return '%02d' % (self.data.year % 100)`.

Probe->requirement mapping and results (PATCHED / BASE / WEAK):
- probe_1 (Req1.3, POSITIVE CONTROL): year 123 -> 'y'=='23'. PATCHED HOLDS('23'), BASE FAILS('3'), WEAK HOLDS. Discriminates base.
- probe_2 (Req1.2/1.4): year 9 -> '09'. PATCHED HOLDS, BASE FAILS(''), WEAK REJECTS('9').
- probe_3 (Req1.5): y length==2 and ==year%%100 across [1..9999] incl <1000. PATCHED HOLDS, BASE FAILS(many), WEAK REJECTS(years 1/5/9).
- probe_4 (Req2.1): year 1979 -> '79' unchanged. HOLDS on all trees.
- probe_5 (Req2.2/2.4): Y=='123' full year; mixed 'd/m/y'->'05/04/23'; escaped literal '\y=y'->'y=23'; independent substitution + literal preservation. HOLDS patched/weak.
- probe_6 (Req2.3): datetime 'Y-m-d H:i:s' -> '2021-03-09 14:05:06' other specifiers unchanged (settings.configure needed for TIME_ZONE). HOLDS patched/weak.

>=5 distinct probes all hold on patched tree; positive control discriminates (holds patched, fails base); >=1 candidate patch exercised and REJECTED by the suite. No requirements-conforming alternative found that would misresolve. Verdict SOUND (advisory).

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Gold patch changes only DateFormat.y() from str(year)[2:] to '%02d' % (year % 100). Requirements pin the observable changed behavior (the 'y' specifier through the public dateformat.format entry point) at the correct modeling boundary: last-two-digits mod 100, always zero-padded to width 2, for all years including <1000, <100, <10; and Req2 correctly scopes preservation of Y and all other specifiers. Requirement 1.5 (always length 2) verified across probes. No unfaithful mandate, forbiddance, narrow-slice mispin, or invented behavior found.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The hidden test test_year_before_1000 parametrizes years [476->'76', 42->'42', 4->'04']. None of these specific case values appear in requirements.md. The illustrative values the document uses (year 9->'09', 123->'23', 1979->'79') are either taken from the public problem_statement (123) or are generic/non-test values, and they do not mirror the test's parametrization. The gold edit is `'%02d' % (self.data.year % 100)`; the requirements restate this as behavior ('last two digits'/'year modulo 100'/'zero-padded to width two'), which is legitimate behavioral translation, not quoted gold code or an invented identifier. Naming `django.utils.dateformat.format` and the `y` specifier is legitimate localization (public). No test names/paths/ids or fix-invented identifiers leaked.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
