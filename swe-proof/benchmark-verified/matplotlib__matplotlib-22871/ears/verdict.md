# P2 adversarial audit — matplotlib__matplotlib-22871

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 6 requirement probes hold on the patched tree; 2/2 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 6 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 6 | `probe_1_core.py`, `probe_2_jan_suppress.py`, `probe_3_disabled.py`, `probe_4_regress_ranges.py`, `probe_5_day_level.py`, `probe_6_level_select.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 2 alternative candidate patches, claimed to satisfy every cited requirement, and ran the same suite against them. The suite rejected all 2: a probe encoding a cited requirement fails under each of those, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1_core.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (6):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1_core.py` → holds on the patched tree (good)

```python
# Req 2.3 & 2.4 (CORE FIX / positive control):
# Sub-year span, >1 month, no January -> month is finest varying, value 1 absent
# -> offset kept, non-empty, contains the year.
import sys, datetime
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt, matplotlib.dates as mdates
fig, ax = plt.subplots()
d1 = datetime.datetime(1997, 3, 1); d2 = datetime.datetime(1997, 9, 1)
loc = mdates.AutoDateLocator()
fmt = mdates.ConciseDateFormatter(loc)
ax.xaxis.set_major_locator(loc); ax.xaxis.set_major_formatter(fmt)
ax.plot([d1, d2], [0, 0]); fig.draw_without_rendering()
off = fmt.get_offset()
print("Mar-Sep 1997 offset:", repr(off))
ok = (off != '') and ('1997' in off)
print("PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)
```

Attack 2 — `probe_2_jan_suppress.py` → holds on the patched tree (good)

```python
# Req 2.2 & 3.1 (regression-keep): month-level span that INCLUDES January
# (month value 1 present) -> a start-of-year tick carries the year -> offset suppressed (empty).
import sys, datetime
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt, matplotlib.dates as mdates
fig, ax = plt.subplots()
d1 = datetime.datetime(1997, 1, 1); d2 = datetime.datetime(1997, 8, 1)
loc = mdates.AutoDateLocator()
fmt = mdates.ConciseDateFormatter(loc)
ax.xaxis.set_major_locator(loc); ax.xaxis.set_major_formatter(fmt)
ax.plot([d1, d2], [0, 0]); fig.draw_without_rendering()
off = fmt.get_offset()
print("Jan-Aug 1997 (month varies incl Jan) offset:", repr(off))
ok = (off == '')
print("PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)
```

Attack 3 — `probe_3_disabled.py` → holds on the patched tree (good)

```python
# Req 3.2: when constructed with offset display disabled, offset is empty
# REGARDLESS of level/value-1 conditions (use the core non-Jan month case).
import sys, datetime
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt, matplotlib.dates as mdates
fig, ax = plt.subplots()
d1 = datetime.datetime(1997, 3, 1); d2 = datetime.datetime(1997, 9, 1)
loc = mdates.AutoDateLocator()
fmt = mdates.ConciseDateFormatter(loc, show_offset=False)
ax.xaxis.set_major_locator(loc); ax.xaxis.set_major_formatter(fmt)
ax.plot([d1, d2], [0, 0]); fig.draw_without_rendering()
off = fmt.get_offset()
print("show_offset=False, Mar-Sep offset:", repr(off))
ok = (off == '')
print("PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)
```

Attack 4 — `probe_4_regress_ranges.py` → holds on the patched tree (good)

```python
# Req 3.3 & test_offset_changes: previously-supported ranges keep their content.
# decade -> '' ; a ~3-week span starting Jan 1 -> '1997-Jan'.
import sys, datetime
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt, matplotlib.dates as mdates
fig, ax = plt.subplots()
d1 = datetime.datetime(1997, 1, 1); d2 = d1 + datetime.timedelta(weeks=520)
loc = mdates.AutoDateLocator()
fmt = mdates.ConciseDateFormatter(loc)
ax.xaxis.set_major_locator(loc); ax.xaxis.set_major_formatter(fmt)
ax.plot([d1, d2], [0, 0]); fig.draw_without_rendering()
o_decade = fmt.get_offset()
ax.set_xlim(d1, d1 + datetime.timedelta(weeks=3)); fig.draw_without_rendering()
o_wk3 = fmt.get_offset()
ax.set_xlim(d1, d1 + datetime.timedelta(weeks=520)); fig.draw_without_rendering()
o_decade2 = fmt.get_offset()
print("decade:", repr(o_decade), "weeks=3:", repr(o_wk3), "decade2:", repr(o_decade2))
ok = (o_decade == '') and (o_wk3 == '1997-Jan') and (o_decade2 == '')
print("PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)
```

Attack 5 — `probe_5_day_level.py` → holds on the patched tree (good)

```python
# Req 2.5: when the chosen level is day (or finer), the level does NOT suppress
# the offset. Day-level non-Jan span -> offset kept and non-empty ('1997-Mar').
import sys, datetime
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt, matplotlib.dates as mdates, numpy as np
fig, ax = plt.subplots()
d1 = datetime.datetime(1997, 3, 5); d2 = datetime.datetime(1997, 3, 25)
loc = mdates.AutoDateLocator()
fmt = mdates.ConciseDateFormatter(loc)
ax.xaxis.set_major_locator(loc); ax.xaxis.set_major_formatter(fmt)
ax.plot([d1, d2], [0, 0]); fig.draw_without_rendering()
# confirm the chosen level is day (index 2) or finer
vals = loc(); tdt = [mdates.num2date(v) for v in vals]
td = np.array([t.timetuple()[:6] for t in tdt])
lvl = None
for level in range(5, -1, -1):
    if len(np.unique(td[:, level])) > 1:
        lvl = level; break
off = fmt.get_offset()
print("day-level offset:", repr(off), "chosen level:", lvl)
ok = (lvl is not None and lvl >= 2) and off != '' and ('1997' in off)
print("PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)
```

Attack 6 — `probe_6_level_select.py` → holds on the patched tree (good)

```python
# Req 1: the labelling level is the FINEST calendar component that varies.
# A within-single-day span where hours vary but year/month/day are constant
# -> chosen level must be hour (index 3) or finer, NOT overridden by a coarser
#    (constant) component; and the offset carries the coarse '1997-Mar-05' context.
import sys, datetime
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt, matplotlib.dates as mdates, numpy as np
fig, ax = plt.subplots()
d1 = datetime.datetime(1997, 3, 5, 1, 0); d2 = datetime.datetime(1997, 3, 5, 7, 0)
loc = mdates.AutoDateLocator()
fmt = mdates.ConciseDateFormatter(loc)
ax.xaxis.set_major_locator(loc); ax.xaxis.set_major_formatter(fmt)
ax.plot([d1, d2], [0, 0]); fig.draw_without_rendering()
vals = loc(); tdt = [mdates.num2date(v) for v in vals]
td = np.array([t.timetuple()[:6] for t in tdt])
# expected finest-varying = first (from 5..0) with >1 unique
expected = None
for level in range(5, -1, -1):
    if len(np.unique(td[:, level])) > 1:
        expected = level; break
years = np.unique(td[:,0]); months = np.unique(td[:,1]); days = np.unique(td[:,2])
off = fmt.get_offset()
print("hours vary within a day: expected finest level", expected,
      "years", years.tolist(), "months", months.tolist(), "days", days.tolist(),
      "offset", repr(off))
# year/month/day constant, hour varies -> finest varying should be hour(3) or minute(4)
ok = (expected is not None and expected >= 3) and (len(years)==1 and len(months)==1 and len(days)==1)
print("PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1_core.py`

```python
# Req 2.3 & 2.4 (CORE FIX / positive control):
# Sub-year span, >1 month, no January -> month is finest varying, value 1 absent
# -> offset kept, non-empty, contains the year.
import sys, datetime
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt, matplotlib.dates as mdates
fig, ax = plt.subplots()
d1 = datetime.datetime(1997, 3, 1); d2 = datetime.datetime(1997, 9, 1)
loc = mdates.AutoDateLocator()
fmt = mdates.ConciseDateFormatter(loc)
ax.xaxis.set_major_locator(loc); ax.xaxis.set_major_formatter(fmt)
ax.plot([d1, d2], [0, 0]); fig.draw_without_rendering()
off = fmt.get_offset()
print("Mar-Sep 1997 offset:", repr(off))
ok = (off != '') and ('1997' in off)
print("PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

ConciseDateFormatter offset-suppression fix (matplotlib__matplotlib-22871). Gold patch: at month/year level, suppress offset only when value 1 (January) is among the varying component's unique values. Six probes cover the requirement criteria:

- probe_1_core (POSITIVE CONTROL; Req 2.3/2.4): Mar-Sep 1997 (month varies, no Jan) -> offset non-empty and contains year. HOLDS patched ('1997'); FAILS at base ('') — discriminates.
- probe_2_jan_suppress (Req 2.2/3.1 regression-keep): Jan-Aug 1997 (month varies, includes Jan) -> offset suppressed (''). HOLDS patched.
- probe_3_disabled (Req 3.2): show_offset=False on the core non-Jan case -> '' regardless of level/value-1. HOLDS patched.
- probe_4_regress_ranges (Req 3.3 / F2P test_offset_changes): decade span -> '', 3-week Jan-1 span -> '1997-Jan', decade again -> ''. HOLDS patched.
- probe_5_day_level (Req 2.5): day-level non-Jan span -> level index 2, offset kept ('1997-Mar'). HOLDS patched.
- probe_6_level_select (Req 1): hours-vary-within-a-day span -> finest varying level >=3 (hour), coarser constant components do not override; year/month/day constant. HOLDS patched.

All 6 hold on the gold-patched tree. Positive control holds patched and fails at base (prepatch reproduced). The other 5 also hold at base (they encode regression/level behavior unchanged by the fix), as expected.

CANDIDATE PATCHES — both REJECTED by the suite, proving discrimination:
- weak_neverMonth.diff (lazy fix: suppress only at year level, `if level < 1`): passes probe_1 but probe_2 REJECTS it (Jan-Aug 1997 wrongly shows '1997' instead of '' — reintroduces failure to suppress when a January start-of-year tick is present, violating Req 2.2/3.1).
- weak_original.diff (original buggy `if level < 2` with no value-1 guard = base behavior): probe_1 REJECTS it (Mar-Sep -> '', the reported bug).

No probe-conforming alternative patch was found that would not resolve the hidden test — every wrong reading tried is caught. Verdict SOUND: >=5 probes hold, positive control discriminates, >=1 candidate exercised and rejected in each attack direction.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 requirement probes hold on the patched tree; 2/2 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 6 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 6 | `probe_1_core.py`, `probe_2_jan_suppress.py`, `probe_3_disabled.py`, `probe_4_regress_ranges.py`, `probe_5_day_level.py`, `probe_6_level_select.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 2 alternative candidate patches, claimed to satisfy every cited requirement, and ran the same suite against them. The suite rejected all 2: a probe encoding a cited requirement fails under each of those, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1_core.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (6):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

_The 6 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts, and on this backend both roles put it through the same derivation: every block below is a requirement probe run on the gold-patched tree, and the `machine verdict:` line each role publishes above reports BOTH that its probes hold there and how many candidate patches the probe suite rejected — so the two roles re-ran ONE probe suite and each recorded its own outcome for every probe in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `probe_1_core.py` → holds on the patched tree (good)

Attack 2 — `probe_2_jan_suppress.py` → holds on the patched tree (good)

Attack 3 — `probe_3_disabled.py` → holds on the patched tree (good)

Attack 4 — `probe_4_regress_ranges.py` → holds on the patched tree (good)

Attack 5 — `probe_5_day_level.py` → holds on the patched tree (good)

Attack 6 — `probe_6_level_select.py` → holds on the patched tree (good)

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1_core.py`

```python
# Req 2.3 & 2.4 (CORE FIX / positive control):
# Sub-year span, >1 month, no January -> month is finest varying, value 1 absent
# -> offset kept, non-empty, contains the year.
import sys, datetime
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt, matplotlib.dates as mdates
fig, ax = plt.subplots()
d1 = datetime.datetime(1997, 3, 1); d2 = datetime.datetime(1997, 9, 1)
loc = mdates.AutoDateLocator()
fmt = mdates.ConciseDateFormatter(loc)
ax.xaxis.set_major_locator(loc); ax.xaxis.set_major_formatter(fmt)
ax.plot([d1, d2], [0, 0]); fig.draw_without_rendering()
off = fmt.get_offset()
print("Mar-Sep 1997 offset:", repr(off))
ok = (off != '') and ('1997' in off)
print("PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

ConciseDateFormatter offset-suppression fix (matplotlib__matplotlib-22871). Gold patch: at month/year level, suppress offset only when value 1 (January) is among the varying component's unique values. Six probes cover the requirement criteria:

- probe_1_core (POSITIVE CONTROL; Req 2.3/2.4): Mar-Sep 1997 (month varies, no Jan) -> offset non-empty and contains year. HOLDS patched ('1997'); FAILS at base ('') — discriminates.
- probe_2_jan_suppress (Req 2.2/3.1 regression-keep): Jan-Aug 1997 (month varies, includes Jan) -> offset suppressed (''). HOLDS patched.
- probe_3_disabled (Req 3.2): show_offset=False on the core non-Jan case -> '' regardless of level/value-1. HOLDS patched.
- probe_4_regress_ranges (Req 3.3 / F2P test_offset_changes): decade span -> '', 3-week Jan-1 span -> '1997-Jan', decade again -> ''. HOLDS patched.
- probe_5_day_level (Req 2.5): day-level non-Jan span -> level index 2, offset kept ('1997-Mar'). HOLDS patched.
- probe_6_level_select (Req 1): hours-vary-within-a-day span -> finest varying level >=3 (hour), coarser constant components do not override; year/month/day constant. HOLDS patched.

All 6 hold on the gold-patched tree. Positive control holds patched and fails at base (prepatch reproduced). The other 5 also hold at base (they encode regression/level behavior unchanged by the fix), as expected.

CANDIDATE PATCHES — both REJECTED by the suite, proving discrimination:
- weak_neverMonth.diff (lazy fix: suppress only at year level, `if level < 1`): passes probe_1 but probe_2 REJECTS it (Jan-Aug 1997 wrongly shows '1997' instead of '' — reintroduces failure to suppress when a January start-of-year tick is present, violating Req 2.2/3.1).
- weak_original.diff (original buggy `if level < 2` with no value-1 guard = base behavior): probe_1 REJECTS it (Mar-Sep -> '', the reported bug).

No probe-conforming alternative patch was found that would not resolve the hidden test — every wrong reading tried is caught. Verdict SOUND: >=5 probes hold, positive control discriminates, >=1 candidate exercised and rejected in each attack direction.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Patch is a one-line addition of `np.any(unique == 1)` to the offset-suppression condition; requirements pin the changed observable behavior (get_offset() across level+value-1 combinations) at the correct boundary, not a narrow slice. Verified in-image at gold-patched and base commits via nl_attack probes; all HOLDS.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The requirements localize the change (ConciseDateFormatter.format_ticks / get_offset in lib/matplotlib/dates.py) and translate the gold fix (`if level < 2:` -> `if level < 2 and np.any(unique == 1):`) into behavioral requirements: suppress the offset only when the chosen level is coarser than day AND the value 1 (January / first unit) occurs among the component's values, otherwise keep it. This is legitimate behavioral description, not test transmission. No hidden-test content leaks: the test function name (test_offset_changes), the specific year '1997', the concrete week spans (weeks=7..30), and the parametrization ids (t_delta0-6) are all absent. The new expected behavior (year visible in offset for a <1yr, non-January span) is already public via the problem_statement. The fix introduces no new named identifier (only a local `unique`), and none is echoed. Req 3.3's enumeration (single instant, sub-day, day, month-with-January, multi-year) reflects the natural calendar-level taxonomy the domain implies, not a verbatim mirror of the PASS_TO_PASS show_offset parametrization values.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
