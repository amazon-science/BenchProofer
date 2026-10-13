# P2 adversarial audit — matplotlib__matplotlib-26208

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 6 requirement probes hold on the patched tree; 2/2 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 6 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 6 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 2 alternative candidate patches, claimed to satisfy every cited requirement, and ran the same suite against them. The suite rejected all 2: a probe encoding a cited requirement fails under each of those, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (6):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
# R1.1: twinx twin's xaxis.units SHALL be the SAME OBJECT as source's.
# Also serves as positive control (fails at base: twin gets None).
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

fig, ax1 = plt.subplots()
ax1.plot(["a", "b", "c"], [1, 2, 3])  # establishes a category UnitData on xaxis
src = ax1.xaxis.units
print("source xaxis.units:", repr(src))
ax2 = ax1.twinx()
twin = ax2.xaxis.units
print("twin xaxis.units:", repr(twin))
ok = twin is src
print("same object:", ok)
raise SystemExit(0 if ok else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
# R2.1: twiny twin's yaxis.units SHALL be the SAME OBJECT as source's.
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

fig, ax1 = plt.subplots()
ax1.plot([1, 2, 3], ["a", "b", "c"])  # category UnitData on yaxis
src = ax1.yaxis.units
print("source yaxis.units:", repr(src))
ax2 = ax1.twiny()
twin = ax2.yaxis.units
print("twin yaxis.units:", repr(twin))
ok = twin is src
print("same object:", ok)
raise SystemExit(0 if ok else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
# R1.2 & R1.3 (twinx) + R2.2 & R2.3 (twiny): non-None inherits non-None; None inherits None.
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ok = True

# twinx, source has non-None units -> twin non-None (R1.2)
fig, ax1 = plt.subplots()
ax1.plot(["a", "b"], [1, 2])
assert ax1.xaxis.units is not None
t = ax1.twinx()
r12 = t.xaxis.units is not None
print("R1.2 non-None inherited non-None:", r12)
ok = ok and r12

# twinx, source has None units -> twin None (R1.3)
fig2, ax2 = plt.subplots()
ax2.plot([0, 1], [1, 2])
assert ax2.xaxis.units is None, repr(ax2.xaxis.units)
t2 = ax2.twinx()
r13 = t2.xaxis.units is None
print("R1.3 None inherited None:", r13, repr(t2.xaxis.units))
ok = ok and r13

# twiny, source has non-None units -> twin non-None (R2.2)
fig3, ax3 = plt.subplots()
ax3.plot([1, 2], ["a", "b"])
assert ax3.yaxis.units is not None
t3 = ax3.twiny()
r22 = t3.yaxis.units is not None
print("R2.2 non-None inherited non-None:", r22)
ok = ok and r22

# twiny, source has None units -> twin None (R2.3)
fig4, ax4 = plt.subplots()
ax4.plot([0, 1], [1, 2])
assert ax4.yaxis.units is None
t4 = ax4.twiny()
r23 = t4.yaxis.units is None
print("R2.3 None inherited None:", r23, repr(t4.yaxis.units))
ok = ok and r23

raise SystemExit(0 if ok else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
# R1.4 / R2.4: plotting NEW categorical data on the twin must NOT corrupt the
# source's data limits. This is the core bug: without inherited units, the twin
# builds its own category mapping ("a","b","c" -> 0,1,2 only if seen), so a twin
# plotting *unseen* categories remaps and corrupts the shared coordinate's limits
# on the source Axes.
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ok = True

# twinx: source has categories a,b,c => x-lim [0,2]. Twin plots d,e.
# Correct (units inherited): source limits stay [0,2]. Bug (base): remap -> [2,4].
fig, ax1 = plt.subplots()
ax1.plot(["a", "b", "c"], [1, 2, 3])
before = ax1.dataLim.intervalx.copy()
ax2 = ax1.twinx()
ax2.plot(["d", "e"], [10, 20])
after = ax1.dataLim.intervalx
print("twinx source dataLim x before:", before, "after:", after)
r14 = np.all(np.isfinite(after)) and np.allclose(before, after)
print("R1.4 source x-limits preserved & finite:", r14)
ok = ok and r14

# twiny: shared y categorical
fig2, axa = plt.subplots()
axa.plot([1, 2, 3], ["a", "b", "c"])
before_y = axa.dataLim.intervaly.copy()
axb = axa.twiny()
axb.plot([10, 20], ["d", "e"])
after_y = axa.dataLim.intervaly
print("twiny source dataLim y before:", before_y, "after:", after_y)
r24 = np.all(np.isfinite(after_y)) and np.allclose(before_y, after_y)
print("R2.4 source y-limits preserved & finite:", r24)
ok = ok and r24

raise SystemExit(0 if ok else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
# R3: preserve existing twin construction behavior (regression "SHALL keep").
# R3.1/3.2 shared axis; R3.4 twin patch invisible & shared coord axis hidden;
# R3.5 creating twin does not alter source's own data limits.
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ok = True

# --- twinx ---
fig, ax1 = plt.subplots()
ax1.plot([0, 1, 2], [1, 2, 3])
src_lim_before = (ax1.dataLim.intervalx.copy(), ax1.dataLim.intervaly.copy())
ax2 = ax1.twinx()

# R3.1: shares x-axis
r31 = ax1 in ax2.get_shared_x_axes().get_siblings(ax2)
print("R3.1 twinx shares x-axis:", r31)
ok = ok and r31

# R3.4: twin patch invisible; twin's shared (x) axis hidden
r34a = (ax2.patch.get_visible() is False)
r34b = (ax2.xaxis.get_visible() is False)
print("R3.4 twinx patch invisible:", r34a, " shared x hidden:", r34b)
ok = ok and r34a and r34b

# R3.5: creating twin (before any twin plotting) did not alter source data limits
r35 = (np.allclose(src_lim_before[0], ax1.dataLim.intervalx)
       and np.allclose(src_lim_before[1], ax1.dataLim.intervaly))
print("R3.5 twinx source limits unchanged by construction:", r35)
ok = ok and r35

# --- twiny ---
fig2, axa = plt.subplots()
axa.plot([0, 1, 2], [1, 2, 3])
axb = axa.twiny()
r32 = axa in axb.get_shared_y_axes().get_siblings(axb)
print("R3.2 twiny shares y-axis:", r32)
ok = ok and r32
r34c = (axb.patch.get_visible() is False)
r34d = (axb.yaxis.get_visible() is False)
print("R3.4 twiny patch invisible:", r34c, " shared y hidden:", r34d)
ok = ok and r34c and r34d

raise SystemExit(0 if ok else 1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
# R3.3: twinx inherits x-axis autoscale setting from source; twiny inherits y-axis
# autoscale setting. Set source autoscale off then create twin -> twin inherits.
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ok = True

# twinx: x autoscale inherited
fig, ax1 = plt.subplots()
ax1.set_autoscalex_on(False)
ax2 = ax1.twinx()
r33x_off = (ax2.get_autoscalex_on() is False)
print("twinx inherits autoscalex False:", r33x_off, ax2.get_autoscalex_on())
ok = ok and r33x_off

fig1b, ax1b = plt.subplots()
ax1b.set_autoscalex_on(True)
ax2b = ax1b.twinx()
r33x_on = (ax2b.get_autoscalex_on() is True)
print("twinx inherits autoscalex True:", r33x_on, ax2b.get_autoscalex_on())
ok = ok and r33x_on

# twiny: y autoscale inherited
fig2, axa = plt.subplots()
axa.set_autoscaley_on(False)
axb = axa.twiny()
r33y_off = (axb.get_autoscaley_on() is False)
print("twiny inherits autoscaley False:", r33y_off, axb.get_autoscaley_on())
ok = ok and r33y_off

fig2b, axa2 = plt.subplots()
axa2.set_autoscaley_on(True)
axb2 = axa2.twiny()
r33y_on = (axb2.get_autoscaley_on() is True)
print("twiny inherits autoscaley True:", r33y_on, axb2.get_autoscaley_on())
ok = ok and r33y_on

raise SystemExit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
# R1.1: twinx twin's xaxis.units SHALL be the SAME OBJECT as source's.
# Also serves as positive control (fails at base: twin gets None).
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

fig, ax1 = plt.subplots()
ax1.plot(["a", "b", "c"], [1, 2, 3])  # establishes a category UnitData on xaxis
src = ax1.xaxis.units
print("source xaxis.units:", repr(src))
ax2 = ax1.twinx()
twin = ax2.xaxis.units
print("twin xaxis.units:", repr(twin))
ok = twin is src
print("same object:", ok)
raise SystemExit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

matplotlib-26208: twinx/twiny must inherit the shared coordinate axis's `units` (UnitData) from the source Axes. Gold fix: `ax2.xaxis.units = self.xaxis.units` (twinx) and `ax2.yaxis.units = self.yaxis.units` (twiny).

Probe suite (all HOLD on gold-patched tree):
- probe_1 (R1.1, POSITIVE CONTROL): twin xaxis.units IS the same object as source. HOLDS patched / VIOLATED at base (twin gets None, not-same-object). Discriminates.
- probe_2 (R2.1): twin yaxis.units IS the same object as source (twiny). HOLDS patched.
- probe_3 (R1.2/1.3/2.2/2.3): non-None source units => twin non-None; None source => twin None, for both axes. HOLDS patched.
- probe_4 (R1.4/2.4, 2nd control): plotting NEW categorical data on the twin does not corrupt source data limits. HOLDS patched ([0,2] preserved) / VIOLATED at base (remapped to [2,4]). This encodes the F2P bug behavior; also discriminates.
- probe_5 (R3.1/3.2/3.4/3.5 regressions): twin shares x/y axis; twin patch invisible; twin's shared coordinate axis hidden; construction does not alter source limits. HOLDS patched.
- probe_6 (R3.3): twin inherits source's x (twinx) / y (twiny) autoscale setting, both True and False cases. HOLDS patched.

Candidate wrong patches (both REJECTED by the suite => discriminating power confirmed):
- partial.diff: patches only twinx, leaves twiny broken. REJECTED by probe_2 (R2.1 same-object), probe_3 (twiny None/non-None), probe_4 (twiny limit corruption). This is the lazy half-fix a weak reading might permit; the suite catches it.
- copy.diff: uses copy.copy(self.xaxis.units) instead of the same object. Preserves data limits (probe_4 HOLDS) but violates the same-object requirement R1.1/R2.1 => REJECTED by probe_1 and probe_2.

No requirements-conforming alternative found: the only surviving implementation must set the twin's shared-axis units to the identical source object on BOTH axes, which is exactly the gold fix. All 6 probes hold on patched; positive control (probe_1) and probe_4 both fail at base and pass patched. Verdict SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 requirement probes hold on the patched tree; 2/2 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 6 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 6 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 2 alternative candidate patches, claimed to satisfy every cited requirement, and ran the same suite against them. The suite rejected all 2: a probe encoding a cited requirement fails under each of those, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

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
# R1.1: twinx twin's xaxis.units SHALL be the SAME OBJECT as source's.
# Also serves as positive control (fails at base: twin gets None).
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

fig, ax1 = plt.subplots()
ax1.plot(["a", "b", "c"], [1, 2, 3])  # establishes a category UnitData on xaxis
src = ax1.xaxis.units
print("source xaxis.units:", repr(src))
ax2 = ax1.twinx()
twin = ax2.xaxis.units
print("twin xaxis.units:", repr(twin))
ok = twin is src
print("same object:", ok)
raise SystemExit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

matplotlib-26208: twinx/twiny must inherit the shared coordinate axis's `units` (UnitData) from the source Axes. Gold fix: `ax2.xaxis.units = self.xaxis.units` (twinx) and `ax2.yaxis.units = self.yaxis.units` (twiny).

Probe suite (all HOLD on gold-patched tree):
- probe_1 (R1.1, POSITIVE CONTROL): twin xaxis.units IS the same object as source. HOLDS patched / VIOLATED at base (twin gets None, not-same-object). Discriminates.
- probe_2 (R2.1): twin yaxis.units IS the same object as source (twiny). HOLDS patched.
- probe_3 (R1.2/1.3/2.2/2.3): non-None source units => twin non-None; None source => twin None, for both axes. HOLDS patched.
- probe_4 (R1.4/2.4, 2nd control): plotting NEW categorical data on the twin does not corrupt source data limits. HOLDS patched ([0,2] preserved) / VIOLATED at base (remapped to [2,4]). This encodes the F2P bug behavior; also discriminates.
- probe_5 (R3.1/3.2/3.4/3.5 regressions): twin shares x/y axis; twin patch invisible; twin's shared coordinate axis hidden; construction does not alter source limits. HOLDS patched.
- probe_6 (R3.3): twin inherits source's x (twinx) / y (twiny) autoscale setting, both True and False cases. HOLDS patched.

Candidate wrong patches (both REJECTED by the suite => discriminating power confirmed):
- partial.diff: patches only twinx, leaves twiny broken. REJECTED by probe_2 (R2.1 same-object), probe_3 (twiny None/non-None), probe_4 (twiny limit corruption). This is the lazy half-fix a weak reading might permit; the suite catches it.
- copy.diff: uses copy.copy(self.xaxis.units) instead of the same object. Preserves data limits (probe_4 HOLDS) but violates the same-object requirement R1.1/R2.1 => REJECTED by probe_1 and probe_2.

No requirements-conforming alternative found: the only surviving implementation must set the twin's shared-axis units to the identical source object on BOTH axes, which is exactly the gold fix. All 6 probes hold on patched; positive control (probe_1) and probe_4 both fail at base and pass patched. Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Gold patch is exactly the two `ax2.<axis>.units = self.<axis>.units` assignments in twinx/twiny in lib/matplotlib/axes/_base.py. Probes: same-object identity True on patched / False on base; non-None propagation for categorical data; None propagation for numeric data; source dataLim stays finite. The requirements pin the changed observable (unit-setting object identity + None propagation) as the modeling boundary, not a narrower slice, and the data-limit-preservation clauses (1.4/2.4/3.5) are the motivating consequence of that same inheritance. Requirement 3 accurately describes preserved prior behavior and adds no invented obligation. Verdict FAITHFUL.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The requirements localize the change to real public API surfaces — Axes.twinx/twiny in lib/matplotlib/axes/_base.py and the pre-existing Axis.units attribute (ax.xaxis.units / ax.yaxis.units) — which is legitimate. The gold patch is two lines: `ax2.xaxis.units = self.xaxis.units` and `ax2.yaxis.units = self.yaxis.units`. ACs 1-3 in Reqs 1&2 (twin's units is the SAME OBJECT as source's; non-None→non-None; None→None) faithfully translate the assignment's behavior; they mirror the hidden test's three assertions (`is`, `is not None`) but describe what the fix DOES rather than transmitting the test. No test names/paths (test_twin_units, test_axes.py), no parametrization ids ([x]/[y]), no quoted test or gold code, and no fix-invented identifiers appear. The twinx/twiny split reflects two documented public functions, not a leaked test enumeration. `.units` is a public matplotlib attribute, not a solution-invented name. The problem_statement only exposes the ±inf dataLims symptom; the units mechanism is only in hints_text (off-limits), but the doc's use of units is a legitimate description of the fix behavior, not test reconstruction.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
