# P2 adversarial audit — astropy__astropy-13033

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
"""Positive control / Req 1.2 & 1.3 & 1.4:
Multi required-column mismatch: expected side = full bracketed list,
found side = truncated actual leading cols (here single 'time'),
plural 'columns'. Exact gold string.
Exit 0 iff message == "TimeSeries object is invalid - expected
['time', 'flux'] as the first columns but found 'time'".
"""
import sys
import numpy as np
from astropy.timeseries import TimeSeries
from astropy.time import Time

ts = TimeSeries(time=Time([1, 2, 3], format='mjd'))
ts['flux'] = [1.0, 2.0, 3.0]
ts._required_columns = ['time', 'flux']

try:
    ts.remove_column('flux')
    print("NO ERROR RAISED - unexpected")
    sys.exit(1)
except ValueError as e:
    msg = str(e)
    print("observed:", repr(msg))
    expected = ("TimeSeries object is invalid - expected ['time', 'flux'] "
                "as the first columns but found 'time'")
    if msg == expected:
        print("MATCH")
        sys.exit(0)
    print("MISMATCH, expected:", repr(expected))
    sys.exit(1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""Req 1.2/1.3/1.4: multi required, found side has 2+ cols -> bracketed list.
required=['time','a']; after remove('a') leading two cols = ['time','b'].
Exit 0 iff message ==
"TimeSeries object is invalid - expected ['time', 'a'] as the first columns but found ['time', 'b']".
"""
import sys
from astropy.timeseries import TimeSeries
from astropy.time import Time

ts = TimeSeries(time=Time([1, 2, 3], format='mjd'))
ts['a'] = [1.0, 2.0, 3.0]
ts['b'] = [4.0, 5.0, 6.0]
ts._required_columns = ['time', 'a']

try:
    ts.remove_column('a')
    print("NO ERROR RAISED - unexpected")
    sys.exit(1)
except ValueError as e:
    msg = str(e)
    print("observed:", repr(msg))
    expected = ("TimeSeries object is invalid - expected ['time', 'a'] "
                "as the first columns but found ['time', 'b']")
    if msg == expected:
        print("MATCH")
        sys.exit(0)
    print("MISMATCH, expected:", repr(expected))
    sys.exit(1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""Req 2.1/2.2/2.3/2.4: single required column preserved wording.
TimeSeries requires only 'time'; rename time->banana leaves first col 'banana'.
Exit 0 iff message ==
"TimeSeries object is invalid - expected 'time' as the first column but found 'banana'".
"""
import sys
from astropy.timeseries import TimeSeries
from astropy.time import Time

ts = TimeSeries(time=Time([1, 2, 3], format='mjd'))
ts['flux'] = [1.0, 2.0, 3.0]  # extra non-required trailing column
# default _required_columns for TimeSeries is ['time']
print("required:", ts._required_columns)

try:
    ts.rename_column('time', 'banana')
    print("NO ERROR RAISED - unexpected")
    sys.exit(1)
except ValueError as e:
    msg = str(e)
    print("observed:", repr(msg))
    expected = ("TimeSeries object is invalid - expected 'time' "
                "as the first column but found 'banana'")
    if msg == expected:
        print("MATCH")
        sys.exit(0)
    print("MISMATCH, expected:", repr(expected))
    sys.exit(1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""Req 3.3: no-columns branch keeps single-name wording with plural keyed on
required count. Build a TimeSeries requiring ['time','flux'] with zero columns,
call _check_required_columns directly.
Exit 0 iff ValueError message ==
"TimeSeries object is invalid - expected 'time' as the first columns but time series has no columns".
"""
import sys
from astropy.timeseries import TimeSeries

ts = TimeSeries()
ts._required_columns = ['time', 'flux']
ts._required_columns_relax = False
print("colnames:", ts.colnames)

try:
    ts._check_required_columns()
    print("NO ERROR RAISED - unexpected")
    sys.exit(1)
except ValueError as e:
    msg = str(e)
    print("observed:", repr(msg))
    expected = ("TimeSeries object is invalid - expected 'time' "
                "as the first columns but time series has no columns")
    if msg == expected:
        print("MATCH")
        sys.exit(0)
    print("MISMATCH, expected:", repr(expected))
    sys.exit(1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""Req 3.4/3.6 regression: valid construction and valid column ops do NOT raise.
Build a valid TimeSeries, add & remove a non-required column, verify no raise
and leading col preserved.
Exit 0 iff all operations succeed without ValueError.
"""
import sys
from astropy.timeseries import TimeSeries
from astropy.time import Time

try:
    ts = TimeSeries(time=Time([1, 2, 3], format='mjd'))
    ts['flux'] = [1.0, 2.0, 3.0]      # add_column -> ok, time still first
    ts['extra'] = [7, 8, 9]           # add_column -> ok
    ts.remove_column('extra')         # remove non-required -> ok
    ts.rename_column('flux', 'flux2') # rename non-required -> ok
    assert ts.colnames[0] == 'time', ts.colnames
    print("colnames:", ts.colnames)
    print("OK no raise")
    sys.exit(0)
except Exception as e:
    print("UNEXPECTED raise:", type(e).__name__, e)
    sys.exit(1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
"""Req 3.1/3.2: disabled flag and None required-set -> no raise even with
mismatched columns.
Exit 0 iff both cases return without raising.
"""
import sys
from astropy.timeseries import TimeSeries
from astropy.time import Time

ok = True

# Case A: required_columns None
ts = TimeSeries(time=Time([1, 2, 3], format='mjd'))
ts._required_columns = None
try:
    ts._check_required_columns()
    print("None-required: no raise OK")
except Exception as e:
    print("None-required RAISED:", e); ok = False

# Case B: disabled flag with an actual mismatch present
ts2 = TimeSeries(time=Time([1, 2, 3], format='mjd'))
ts2['flux'] = [1.0, 2.0, 3.0]
ts2._required_columns = ['time', 'flux']
ts2._required_columns_enabled = False
# manually break leading columns would be hard; instead force a mismatch by
# setting required to something not matching, checking disabled short-circuits
ts2._required_columns = ['flux', 'time']  # mismatch vs actual ['time','flux',...]
try:
    ts2._check_required_columns()
    print("disabled: no raise OK")
except Exception as e:
    print("disabled RAISED:", e); ok = False

sys.exit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Positive control / Req 1.2 & 1.3 & 1.4:
Multi required-column mismatch: expected side = full bracketed list,
found side = truncated actual leading cols (here single 'time'),
plural 'columns'. Exact gold string.
Exit 0 iff message == "TimeSeries object is invalid - expected
['time', 'flux'] as the first columns but found 'time'".
"""
import sys
import numpy as np
from astropy.timeseries import TimeSeries
from astropy.time import Time

ts = TimeSeries(time=Time([1, 2, 3], format='mjd'))
ts['flux'] = [1.0, 2.0, 3.0]
ts._required_columns = ['time', 'flux']

try:
    ts.remove_column('flux')
    print("NO ERROR RAISED - unexpected")
    sys.exit(1)
except ValueError as e:
    msg = str(e)
    print("observed:", repr(msg))
    expected = ("TimeSeries object is invalid - expected ['time', 'flux'] "
                "as the first columns but found 'time'")
    if msg == expected:
        print("MATCH")
        sys.exit(0)
    print("MISMATCH, expected:", repr(expected))
    sys.exit(1)
```

Prepatch bug re-encoded as an attack: `True`.

6 probes cover: Req1.2/1.3/1.4 multi-required mismatch with truncated single found side (probe_1, exact gold string 'expected [\'time\', \'flux\'] as the first columns but found \'time\''); Req1.3 multi found side as bracketed list (probe_2, 'found [\'time\', \'b\']'); Req2.1-2.4 single-required wording preserved (probe_3); Req3.3 no-columns branch single-name wording + plural keyed on required count (probe_4); Req3.4/3.6 valid ops don't raise (probe_5); Req3.1/3.2 disabled flag & None short-circuit (probe_6).

All 6 HOLD on patched tree. Positive control probe_1 FAILS at base ('expected \'time\' ... but found \'time\'', bracket-less, offending col invisible) and HOLDS patched -> discriminates. probe_2 also fails at base.

Weak candidate: renders found side from full self.colnames instead of the len(required_columns) truncated slice. REJECTED by probe_3 (yields 'found [\'banana\', \'flux\']' instead of required 'found \'banana\''). This proves the suite discriminates a plausibly-wrong fix. Probes 1,2 alone do NOT catch it (their found slice equals full colnames), so probe_3's trailing-column setup is the discriminating leg.

NOTE on the meta.json G-PANEL-2 UNFAITHFUL claim: it asserts Req1.3 demands found=='['time']' for the remove-flux case. This is INCORRECT — requirements.md lines 67-71 explicitly mandate the single-remaining-column case renders as bare 'time' (no brackets), matching gold exactly, because the rendering convention keys bracket-vs-quote on THAT side's own length. Probe_1 confirms gold produces 'found \'time\'' and the spec's worked example matches it verbatim. The spec is faithful to gold on this point.

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
"""Positive control / Req 1.2 & 1.3 & 1.4:
Multi required-column mismatch: expected side = full bracketed list,
found side = truncated actual leading cols (here single 'time'),
plural 'columns'. Exact gold string.
Exit 0 iff message == "TimeSeries object is invalid - expected
['time', 'flux'] as the first columns but found 'time'".
"""
import sys
import numpy as np
from astropy.timeseries import TimeSeries
from astropy.time import Time

ts = TimeSeries(time=Time([1, 2, 3], format='mjd'))
ts['flux'] = [1.0, 2.0, 3.0]
ts._required_columns = ['time', 'flux']

try:
    ts.remove_column('flux')
    print("NO ERROR RAISED - unexpected")
    sys.exit(1)
except ValueError as e:
    msg = str(e)
    print("observed:", repr(msg))
    expected = ("TimeSeries object is invalid - expected ['time', 'flux'] "
                "as the first columns but found 'time'")
    if msg == expected:
        print("MATCH")
        sys.exit(0)
    print("MISMATCH, expected:", repr(expected))
    sys.exit(1)
```

Prepatch bug re-encoded as an attack: `True`.

6 probes cover: Req1.2/1.3/1.4 multi-required mismatch with truncated single found side (probe_1, exact gold string 'expected [\'time\', \'flux\'] as the first columns but found \'time\''); Req1.3 multi found side as bracketed list (probe_2, 'found [\'time\', \'b\']'); Req2.1-2.4 single-required wording preserved (probe_3); Req3.3 no-columns branch single-name wording + plural keyed on required count (probe_4); Req3.4/3.6 valid ops don't raise (probe_5); Req3.1/3.2 disabled flag & None short-circuit (probe_6).

All 6 HOLD on patched tree. Positive control probe_1 FAILS at base ('expected \'time\' ... but found \'time\'', bracket-less, offending col invisible) and HOLDS patched -> discriminates. probe_2 also fails at base.

Weak candidate: renders found side from full self.colnames instead of the len(required_columns) truncated slice. REJECTED by probe_3 (yields 'found [\'banana\', \'flux\']' instead of required 'found \'banana\''). This proves the suite discriminates a plausibly-wrong fix. Probes 1,2 alone do NOT catch it (their found slice equals full colnames), so probe_3's trailing-column setup is the discriminating leg.

NOTE on the meta.json G-PANEL-2 UNFAITHFUL claim: it asserts Req1.3 demands found=='['time']' for the remove-flux case. This is INCORRECT — requirements.md lines 67-71 explicitly mandate the single-remaining-column case renders as bare 'time' (no brackets), matching gold exactly, because the rendering convention keys bracket-vs-quote on THAT side's own length. Probe_1 confirms gold produces 'found \'time\'' and the spec's worked example matches it verbatim. The spec is faithful to gold on this point.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Probes on gold-patched image: (A) TimeSeries(time,flux), _required_columns=['time','flux'], remove_column('flux') -> ValueError "expected ['time', 'flux'] as the first columns but found 'time'" — matches Req 1.2 (expected full bracketed list), Req 1.3 (found side is truncated slice ['time'] which has len 1, so rendered as single-quoted 'time', NOT bracketed — exactly the example in the requirement), Req 1.4 (plural 'columns' keyed on 2 required). (B) _required_columns=['time','a'], remove 'a' leaving 'b' -> "expected ['time', 'a'] as the first columns but found ['time', 'b']" — matches Req 1.3 (2-element found slice rendered bracketed). (C) single required 'time', rename to 'banana' -> "expected 'time' as the first column but found 'banana'" — matches Req 2.1/2.2/2.3/2.4 (singular quotes both sides, singular noun 'column'). (D) no-columns branch, 2 required -> "expected 'time' as the first columns but time series has no columns" — matches Req 3.3 (first-required single-name wording, plural keyed on 2 required). The rendering convention (scalar/len-1/len>=2) and the plural-keyed-on-required-count vs found-side-keyed-on-its-own-length distinction are described accurately and match the patch's as_scalar_or_list_str helper. No divergence found.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The document's worked example ('time','flux'; remove flux → found 'time') tracks the PUBLIC problem_statement reproduction, not the hidden test, which uses required ['time','a'], remove_column('a'), and asserts found ['time','b'] — none of those test-specific identifiers or the two-element bracketed found-side appear in requirements.md. The fix-invented helper name (as_scalar_or_list_str) is not disclosed. No test file paths, test function/class names (test_required_columns), or parametrization ids leak. Named modules/methods (core.py, BaseTimeSeries._check_required_columns, _required_columns, add_column/remove_column/etc.) are legitimate localization / public API. The rendering convention is a behavioral translation of the gold, not quoted gold code.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
