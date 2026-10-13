# P2 adversarial audit — django__django-10999

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
import sys
from datetime import timedelta
from django.utils.dateparse import parse_duration

# Req 1.2: signed h:m:s negates ALL three components
got = parse_duration('-1:15:30')
want = timedelta(hours=-1, minutes=-15, seconds=-30)
print("parse_duration('-1:15:30') =", got, "want", want)
sys.exit(0 if got == want else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
import sys
from datetime import timedelta
from django.utils.dateparse import parse_duration

# Req 1.3: signed m:s -> both minutes and seconds negative
got = parse_duration('-15:30')
want = timedelta(minutes=-15, seconds=-30)
print("parse_duration('-15:30') =", got, "want", want)
sys.exit(0 if got == want else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
import sys
from datetime import timedelta
from django.utils.dateparse import parse_duration

# Req 1.4: fractional seconds sub-second portion also negated
got = parse_duration('-30.1')
want = timedelta(seconds=-30, milliseconds=-100)
print("parse_duration('-30.1') =", got, "want", want)
# also -01:01 -> minus 61 seconds (whole negation)
got2 = parse_duration('-01:01')
want2 = timedelta(seconds=-61)
print("parse_duration('-01:01') =", got2, "want", want2)
sys.exit(0 if got == want and got2 == want2 else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
import sys
from django.utils.dateparse import parse_duration

# Req 2.1: a sign before an interior component => None
got = parse_duration('-01:-01')
print("parse_duration('-01:-01') =", got, "(want None)")
got2 = parse_duration('00:-01:-01')
print("parse_duration('00:-01:-01') =", got2, "(want None)")
sys.exit(0 if got is None and got2 is None else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
import sys
from datetime import timedelta
from django.utils.dateparse import parse_duration

# Req 3: days keep independent sign; bare signed seconds
ok = True
got = parse_duration('-4 15:30')
want = timedelta(days=-4, minutes=15, seconds=30)
print("'-4 15:30' =", got, "want", want); ok &= got == want
got = parse_duration('-172800')
want = timedelta(days=-2)
print("'-172800' =", got, "want", want); ok &= got == want
# -00:01:01 -> (-00):(+01):(+01) = +61 seconds per issue discussion
got = parse_duration('-00:01:01')
want = timedelta(minutes=-1, seconds=-1)
print("'-00:01:01' =", got, "want", want); ok &= got == want
sys.exit(0 if ok else 1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
import sys
from datetime import timedelta
from django.utils.dateparse import parse_duration

# Req 4 & 5: positive standard, fractions, days, ISO, postgres, roundtrip
ok = True
def chk(s, want):
    global ok
    got = parse_duration(s)
    eq = got == want
    print(repr(s), "=", repr(got), "want", repr(want), "OK" if eq else "MISMATCH")
    ok &= eq

chk('10:15:30', timedelta(hours=10, minutes=15, seconds=30))
chk('15:30', timedelta(minutes=15, seconds=30))
chk('30', timedelta(seconds=30))
chk('4 15:30', timedelta(days=4, minutes=15, seconds=30))
chk('4 10:15:30', timedelta(days=4, hours=10, minutes=15, seconds=30))
chk('15:30.1', timedelta(minutes=15, seconds=30, milliseconds=100))
# ISO 8601
chk('P4DT1H15M20S', timedelta(days=4, hours=1, minutes=15, seconds=20))
chk('P4Y', None)  # not accepted before -> None
# Postgres interval with independent day/time signs
chk('-2 days +03:04:05', timedelta(days=-2, hours=3, minutes=4, seconds=5))
chk('3 days 04:05:06', timedelta(days=3, hours=4, minutes=5, seconds=6))
# roundtrip str() of negative-day timedelta
td = timedelta(days=-1, hours=1, minutes=2, seconds=3)
chk(str(td), td)
# not well formed -> None
chk('not a duration', None)
sys.exit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
import sys
from datetime import timedelta
from django.utils.dateparse import parse_duration

# Req 1.2: signed h:m:s negates ALL three components
got = parse_duration('-1:15:30')
want = timedelta(hours=-1, minutes=-15, seconds=-30)
print("parse_duration('-1:15:30') =", got, "want", want)
sys.exit(0 if got == want else 1)
```

Prepatch bug re-encoded as an attack: `True`.

parse_duration() negative-duration fix (django/utils/dateparse.py standard_duration_re). Six standalone stdlib probes, all HOLD on gold-patched tree, all fail at base except regression probe.

Probes -> requirement:
- probe_1 (Req 1.2, POSITIVE CONTROL): '-1:15:30' -> timedelta(hours=-1,minutes=-1... all negative). HOLDS patched, FAILS base (base gives hours-only negative), FAILS weak.
- probe_2 (Req 1.3): '-15:30' -> minutes=-15,seconds=-30. HOLDS patched, FAILS base/weak.
- probe_3 (Req 1.4): '-30.1' fractional negated + '-01:01' -> -61s whole negation. HOLDS patched, FAILS base/weak.
- probe_4 (Req 2.1): '-01:-01' and '00:-01:-01' -> None (interior sign rejected). HOLDS patched, FAILS base/weak.
- probe_5 (Req 3): '-4 15:30' independent day sign, '-172800' bare signed seconds, '-00:01:01' -> (-00):(-01):(-01). HOLDS patched, FAILS base/weak.
- probe_6 (Req 4 & 5 regression): positive h:m:s / m:s / bare / day / fractional forms, ISO8601 accept + reject (P4Y->None), postgres interval with independent signs, negative-day str() roundtrip, malformed->None. HOLDS patched.

CANDIDATE PATCH (naive_lookahead_only): the exact fix proposed in the issue text — add '-?' to the hours lookahead only, r'(?=-?\d+:-?\d+)', leaving per-component -? signs. A weak reading of 'accept negative' permits this. Run under --patch: REJECTED by probes 1-5 (it applies the sign to only the hours component and still accepts interior signs like '-01:-01'), passes only probe_6. This demonstrates the suite discriminates the plausible wrong fix.

All needed runs completed. >=5 distinct probes hold on patched; positive control discriminates (fails at base); >=1 candidate exercised and REJECTED. No too-weak candidate survived the probe suite.

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
import sys
from datetime import timedelta
from django.utils.dateparse import parse_duration

# Req 1.2: signed h:m:s negates ALL three components
got = parse_duration('-1:15:30')
want = timedelta(hours=-1, minutes=-15, seconds=-30)
print("parse_duration('-1:15:30') =", got, "want", want)
sys.exit(0 if got == want else 1)
```

Prepatch bug re-encoded as an attack: `True`.

parse_duration() negative-duration fix (django/utils/dateparse.py standard_duration_re). Six standalone stdlib probes, all HOLD on gold-patched tree, all fail at base except regression probe.

Probes -> requirement:
- probe_1 (Req 1.2, POSITIVE CONTROL): '-1:15:30' -> timedelta(hours=-1,minutes=-1... all negative). HOLDS patched, FAILS base (base gives hours-only negative), FAILS weak.
- probe_2 (Req 1.3): '-15:30' -> minutes=-15,seconds=-30. HOLDS patched, FAILS base/weak.
- probe_3 (Req 1.4): '-30.1' fractional negated + '-01:01' -> -61s whole negation. HOLDS patched, FAILS base/weak.
- probe_4 (Req 2.1): '-01:-01' and '00:-01:-01' -> None (interior sign rejected). HOLDS patched, FAILS base/weak.
- probe_5 (Req 3): '-4 15:30' independent day sign, '-172800' bare signed seconds, '-00:01:01' -> (-00):(-01):(-01). HOLDS patched, FAILS base/weak.
- probe_6 (Req 4 & 5 regression): positive h:m:s / m:s / bare / day / fractional forms, ISO8601 accept + reject (P4Y->None), postgres interval with independent signs, negative-day str() roundtrip, malformed->None. HOLDS patched.

CANDIDATE PATCH (naive_lookahead_only): the exact fix proposed in the issue text — add '-?' to the hours lookahead only, r'(?=-?\d+:-?\d+)', leaving per-component -? signs. A weak reading of 'accept negative' permits this. Run under --patch: REJECTED by probes 1-5 (it applies the sign to only the hours component and still accepts interior signs like '-01:-01'), passes only probe_6. This demonstrates the suite discriminates the plausible wrong fix.

All needed runs completed. >=5 distinct probes hold on patched; positive control discriminates (fails at base); >=1 candidate exercised and REJECTED. No too-weak candidate survived the probe suite.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** The regex patch adds a single (?P<sign>-?) group applied to the whole time-of-day and removes per-component signs. Requirements pin exactly this changed observable behavior (parse_duration output), at the correct boundary — the full standard-layout sign semantics — rather than one branch/helper. Numeric examples are illustrative, matching probed values. G-EQ already recorded 6 probes hold + weak-candidate rejected + base/patched discrimination. No mandated-but-absent, forbidden-but-present, wrong-boundary, or invented behavior found.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** requirements.md describes the negative-duration parsing behavior of parse_duration() in django/utils/dateparse.py, naming the module legitimately for localization. The hidden test parametrization strings (-15:30, -1:15:30, -30.1, -00:01:01, -01:01, -01:-01) and their expected timedeltas are NOT quoted or near-quoted. The only concrete numeric examples used (10:15:30, 15:30, 30, 4 15:30, 15:30.1) are positive illustrations of the standard layout forms — generic behavior, not the F2P negative cases. The interior-sign->None rule (Req 2.1) is stated as a behavioral rule (sign before an interior component following a colon), not as the test literal -01:-01. The gold patch's invented regex group name `sign` is not surfaced; only the ordinary English word 'sign' appears. Sub-criteria enumerate layout forms (h:m:s / m:s / fractional / bare seconds) which is legitimate behavioral decomposition, not test-parametrization mirroring. Nothing derivable only from the hidden tests or gold edit beyond the public problem_statement.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
