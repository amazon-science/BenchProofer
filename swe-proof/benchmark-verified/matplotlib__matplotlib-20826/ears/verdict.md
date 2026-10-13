# P2 adversarial audit — matplotlib__matplotlib-20826

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

Counterexample / evidence:

```
weak1 (delete both _reset_*_tick_kw() calls from clear() without recomputing gridOn) is REJECTED by probe_3: after clearing with axes.grid=False the tables retained gridOn=True (stale) instead of recomputing to False -> violates Req 2.1/2.3. This shows the suite discriminates the lazy over-fix.
```

**Attacks re-run (5):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
"""Req 1.1/1.2 + positive control: clear() must RETAIN per-side tick-kw entries.

Set a per-side visibility entry (label1On=False) into the major tick-kw table,
then call Axis.clear(); the entry must survive with its value.
At base, clear() wipes the whole table -> entry lost.
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

fig, ax = plt.subplots()
# Set per-side tick-label visibility flags (not the grid flag).
ax.tick_params(axis="x", which="major", labelbottom=False, labeltop=False)
before = dict(ax.xaxis._major_tick_kw)
print("major_tick_kw before clear:", before)
assert before.get("label1On") is False, "setup failed: label1On not False"

ax.xaxis.clear()
after = dict(ax.xaxis._major_tick_kw)
print("major_tick_kw after clear:", after)

ok = after.get("label1On") is False and after.get("label2On") is False
print("label1On retained False:", after.get("label1On"))
print("label2On retained False:", after.get("label2On"))
if not ok:
    print("VIOLATION: per-side tick-kw entries not retained across clear()")
    raise SystemExit(1)
print("PASS: entries retained")
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""Req 1.4 (end-to-end): shared-axis interior ticks/labels stay hidden after clear.

subplots(2,2, sharex, sharey): interior axes have some sides hidden. After
ax.clear()+replot, the tick-label visibility of a cleared interior axes must
match the same interior axes in a never-cleared reference figure.
At base, clear() re-exposes hidden labels.
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

def label_visibility(fig, cleared):
    axs = fig.subplots(2, 2, sharex=True, sharey=True)
    x = np.arange(0.0, 6.0, 0.01)
    y = np.sin(x)
    out = []
    for ax in axs.flat:
        if cleared:
            ax.clear()
        ax.plot(x, y)
    fig.canvas.draw()
    for ax in axs.flat:
        row = []
        for t in ax.xaxis.get_major_ticks() + ax.yaxis.get_major_ticks():
            row.append((t.label1.get_visible(), t.label2.get_visible(),
                        t.tick1line.get_visible(), t.tick2line.get_visible()))
        out.append(tuple(row))
    return out

fref = plt.figure()
ftest = plt.figure()
ref = label_visibility(fref, cleared=False)
test = label_visibility(ftest, cleared=True)

for i, (r, t) in enumerate(zip(ref, test)):
    print(f"axes {i}: ref={r}")
    print(f"axes {i}: test={t}")

ok = ref == test
if not ok:
    print("VIOLATION: cleared shared axes visibility differs from never-cleared")
    raise SystemExit(1)
print("PASS: cleared shared-axis visibility matches reference")
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""Req 2.1/2.2/2.3: clear() recomputes gridOn from current rcParams,
independent of prior gridOn value.

Force gridOn=True in the tables, set rcParams axes.grid=False, clear ->
gridOn must become False for both major and minor (recomputed, not preserved).
Then set axes.grid=True / which='major' -> major True, minor False.
This must hold on BOTH base and patched (grid flag is always recomputed).
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib as mpl

fig, ax = plt.subplots()

# Case A: grid off
mpl.rcParams['axes.grid'] = False
mpl.rcParams['axes.grid.which'] = 'both'
ax.xaxis._major_tick_kw['gridOn'] = True
ax.xaxis._minor_tick_kw['gridOn'] = True
ax.xaxis.clear()
maj = ax.xaxis._major_tick_kw.get('gridOn')
mnr = ax.xaxis._minor_tick_kw.get('gridOn')
print("grid off -> major gridOn:", maj, "minor gridOn:", mnr)
assert maj is False and mnr is False, "gridOn not recomputed to False"

# Case B: grid on, which='major'
mpl.rcParams['axes.grid'] = True
mpl.rcParams['axes.grid.which'] = 'major'
ax.xaxis._major_tick_kw['gridOn'] = False
ax.xaxis._minor_tick_kw['gridOn'] = True
ax.xaxis.clear()
maj = ax.xaxis._major_tick_kw.get('gridOn')
mnr = ax.xaxis._minor_tick_kw.get('gridOn')
print("grid on/major -> major gridOn:", maj, "minor gridOn:", mnr)
assert maj is True and mnr is False, "gridOn(major-only) wrong"

# Case C: grid on, which='minor'
mpl.rcParams['axes.grid.which'] = 'minor'
ax.xaxis.clear()
maj = ax.xaxis._major_tick_kw.get('gridOn')
mnr = ax.xaxis._minor_tick_kw.get('gridOn')
print("grid on/minor -> major gridOn:", maj, "minor gridOn:", mnr)
assert maj is False and mnr is True, "gridOn(minor-only) wrong"

print("PASS: gridOn recomputed from rcParams in all cases")
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""Req 3.1: set_tick_params(reset=True) must still FULL-reset the table to only
the recomputed grid flag before applying new updates.

Put a stray per-side entry, call set_tick_params(reset=True, labelsize=...) ->
the stray entry must be gone (full reset semantics preserved), while the new
kwargs are applied. Must hold on both base and patched.
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib as mpl

mpl.rcParams['axes.grid'] = False
fig, ax = plt.subplots()

# stray per-side entry that reset should wipe
ax.xaxis._major_tick_kw['label1On'] = False
ax.xaxis._major_tick_kw['STRAY'] = 12345
print("before reset:", dict(ax.xaxis._major_tick_kw))

ax.xaxis.set_tick_params(which='major', reset=True, labelsize=7)
after = dict(ax.xaxis._major_tick_kw)
print("after reset+labelsize:", after)

assert 'STRAY' not in after, "reset=True did not full-reset the table"
assert after.get('label1On') is not False or 'label1On' not in after, \
    "stray label1On survived a reset"
assert after.get('labelsize') == 7, "supplied kwarg not applied after reset"
assert 'gridOn' in after, "gridOn missing after reset"
print("PASS: reset=True full-reset semantics preserved")
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""Req 3.2/3.5: after Axes.clear(), shared axes remain joined (matching view
limits & scale) and twin/inversion behavior preserved.
Regression 'SHALL keep'. Must hold on base and patched.
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

fig, axs = plt.subplots(2, 2, sharex='all', sharey='all')
for ax in axs.flat:
    ax.plot([0, 2], 'o-')

# clear one and replot
axs[0, 0].clear()
axs[0, 0].plot([0, 2], 'o-')

# changing limits on one must affect all (still joined)
axs[0, 0].set_xlim(-1, 5)
for ax in axs.flat:
    print("xlim", ax.get_xlim())
    assert ax.get_xlim() == axs[0, 0].get_xlim(), "shared xlim broke after clear"
    assert ax.get_ylim() == axs[0, 0].get_ylim(), "shared ylim broke after clear"

# twin + inversion regression
fig2, ax2 = plt.subplots()
axt = ax2.twinx()
ax2.set_ylim(10, 0)  # inverted
ax2.clear()
ax2.set_ylim(10, 0)
lo, hi = ax2.get_ylim()
print("inverted after clear:", (lo, hi))
assert lo > hi, "inversion not preserved after clear"
assert axt in ax2._twinned_axes.get_siblings(ax2), "twin relation lost"

print("PASS: shared/twin/inversion regressions preserved")
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Req 1.1/1.2 + positive control: clear() must RETAIN per-side tick-kw entries.

Set a per-side visibility entry (label1On=False) into the major tick-kw table,
then call Axis.clear(); the entry must survive with its value.
At base, clear() wipes the whole table -> entry lost.
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

fig, ax = plt.subplots()
# Set per-side tick-label visibility flags (not the grid flag).
ax.tick_params(axis="x", which="major", labelbottom=False, labeltop=False)
before = dict(ax.xaxis._major_tick_kw)
print("major_tick_kw before clear:", before)
assert before.get("label1On") is False, "setup failed: label1On not False"

ax.xaxis.clear()
after = dict(ax.xaxis._major_tick_kw)
print("major_tick_kw after clear:", after)

ok = after.get("label1On") is False and after.get("label2On") is False
print("label1On retained False:", after.get("label1On"))
print("label2On retained False:", after.get("label2On"))
if not ok:
    print("VIOLATION: per-side tick-kw entries not retained across clear()")
    raise SystemExit(1)
print("PASS: entries retained")
```

Prepatch bug re-encoded as an attack: `True`.

Fix (patch.diff): clear() replaces _reset_major/minor_tick_kw() with an in-place recompute of only gridOn, preserving all other _major/_minor_tick_kw entries; reset_ticks() then rebuilds Tick objects from the preserved+recomputed table.

Probe coverage & results (patched / base):
- probe_1 (Req1.1/1.2, POSITIVE CONTROL): per-side label1On/label2On=False survives Axis.clear(). HOLDS patched / FAILS base (base wipes table to {gridOn}).
- probe_2 (Req1.4, end-to-end): tick/label visibility of cleared+replotted interior shared axes matches never-cleared reference figure. HOLDS patched / FAILS base (interior labels re-exposed).
- probe_3 (Req2.1/2.2/2.3): gridOn recomputed from axes.grid + axes.grid.which (off, major-only, minor-only cases), independent of prior value. HOLDS on both trees (grid flag always recomputed) — used as the discriminator against weak1, which it REJECTS.
- probe_4 (Req3.1): set_tick_params(reset=True) still full-resets table to only recomputed gridOn before applying kwargs (STRAY entry wiped, labelsize applied). HOLDS both.
- probe_5 (Req3.2/3.5, regression SHALL-keep): after Axes.clear(), shared group stays joined (shared xlim/ylim propagate), twin relationship + inverted-limits preserved. HOLDS both.

All 5 probes HOLD on the gold-patched tree; positive controls probe_1 and probe_2 FAIL at base (prepatch reproduced). Candidate weak1 exercised and REJECTED by probe_3 -> suite discriminates a probe-nonconforming wrong fix. No probe-conforming alternative that would fail the hidden test was found; requirements faithfully bound the gold behavior.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 5 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 5 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 5 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

Counterexample / evidence:

```
weak1 (delete both _reset_*_tick_kw() calls from clear() without recomputing gridOn) is REJECTED by probe_3: after clearing with axes.grid=False the tables retained gridOn=True (stale) instead of recomputing to False -> violates Req 2.1/2.3. This shows the suite discriminates the lazy over-fix.
```

**Attacks re-run (5):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

_The 5 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts, and on this backend both roles put it through the same derivation: every block below is a requirement probe run on the gold-patched tree, and the `machine verdict:` line each role publishes above reports BOTH that its probes hold there and how many candidate patches the probe suite rejected — so the two roles re-ran ONE probe suite and each recorded its own outcome for every probe in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `probe_1.py` → holds on the patched tree (good)

Attack 2 — `probe_2.py` → holds on the patched tree (good)

Attack 3 — `probe_3.py` → holds on the patched tree (good)

Attack 4 — `probe_4.py` → holds on the patched tree (good)

Attack 5 — `probe_5.py` → holds on the patched tree (good)

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Req 1.1/1.2 + positive control: clear() must RETAIN per-side tick-kw entries.

Set a per-side visibility entry (label1On=False) into the major tick-kw table,
then call Axis.clear(); the entry must survive with its value.
At base, clear() wipes the whole table -> entry lost.
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

fig, ax = plt.subplots()
# Set per-side tick-label visibility flags (not the grid flag).
ax.tick_params(axis="x", which="major", labelbottom=False, labeltop=False)
before = dict(ax.xaxis._major_tick_kw)
print("major_tick_kw before clear:", before)
assert before.get("label1On") is False, "setup failed: label1On not False"

ax.xaxis.clear()
after = dict(ax.xaxis._major_tick_kw)
print("major_tick_kw after clear:", after)

ok = after.get("label1On") is False and after.get("label2On") is False
print("label1On retained False:", after.get("label1On"))
print("label2On retained False:", after.get("label2On"))
if not ok:
    print("VIOLATION: per-side tick-kw entries not retained across clear()")
    raise SystemExit(1)
print("PASS: entries retained")
```

Prepatch bug re-encoded as an attack: `True`.

Fix (patch.diff): clear() replaces _reset_major/minor_tick_kw() with an in-place recompute of only gridOn, preserving all other _major/_minor_tick_kw entries; reset_ticks() then rebuilds Tick objects from the preserved+recomputed table.

Probe coverage & results (patched / base):
- probe_1 (Req1.1/1.2, POSITIVE CONTROL): per-side label1On/label2On=False survives Axis.clear(). HOLDS patched / FAILS base (base wipes table to {gridOn}).
- probe_2 (Req1.4, end-to-end): tick/label visibility of cleared+replotted interior shared axes matches never-cleared reference figure. HOLDS patched / FAILS base (interior labels re-exposed).
- probe_3 (Req2.1/2.2/2.3): gridOn recomputed from axes.grid + axes.grid.which (off, major-only, minor-only cases), independent of prior value. HOLDS on both trees (grid flag always recomputed) — used as the discriminator against weak1, which it REJECTS.
- probe_4 (Req3.1): set_tick_params(reset=True) still full-resets table to only recomputed gridOn before applying kwargs (STRAY entry wiped, labelsize applied). HOLDS both.
- probe_5 (Req3.2/3.5, regression SHALL-keep): after Axes.clear(), shared group stays joined (shared xlim/ylim propagate), twin relationship + inverted-limits preserved. HOLDS both.

All 5 probes HOLD on the gold-patched tree; positive controls probe_1 and probe_2 FAIL at base (prepatch reproduced). Candidate weak1 exercised and REJECTED by probe_3 -> suite discriminates a probe-nonconforming wrong fix. No probe-conforming alternative that would fail the hidden test was found; requirements faithfully bound the gold behavior.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Gold patch: Axis.clear() no longer calls _reset_major/minor_tick_kw(); instead it directly sets _major_tick_kw['gridOn'] and _minor_tick_kw['gridOn'] from rcParams (axes.grid AND axes.grid.which in ('both','major'/'minor')), keeping all other entries, then calls reset_ticks(). The reset helpers still exist and clear the table (used only by set_tick_params(reset=True)). Requirements pin the CHANGED observable behavior (shared-axis tick/label visibility surviving clear) at the correct boundary (Axis.clear), not a narrow branch or helper. Req1 (preserve entries), Req2 (recompute grid flag biconditionally), Req3.1 (reset=True semantics), Req3.2-3.6 (preserved shared/twin/grid/tick_params behavior) all consistent with patch and unrefuted by probe. R2.4/R3.4 reset_ticks inheritance consistent. No mandated-but-absent, forbidden-but-present, or invented behavior.

Counterexample / evidence:

```
No divergence found. Behavioral probe on a sharex/sharey subplot: PATCHED clear() preserves xaxis._major_tick_kw['label1On']=False (interior x tick-labels stay hidden) -> Req1/Req1.4 hold; BASE drops it to None (the regression). With axes.grid=True/which='minor', patched clear() yields MAJOR gridOn=False, MINOR gridOn=True -> exact biconditional of Req2.1/2.2. set_tick_params(reset=True) re-inits table to only ['gridOn'] -> Req3.1 holds.
```


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The requirements localize the change to real, pre-existing matplotlib internals (Axis.clear, _reset_major/minor_tick_kw, _major/_minor_tick_kw, gridOn, reset_ticks, rcParams axes.grid / axes.grid.which) — legitimate localization, not fix-invented identifiers. Requirement 2 transliterates the gold patch's grid-flag logic (in ('both','major') / ('both','minor')) but as a behavioral requirement, which is the intended purpose of the spec; matplotlib grid config semantics are public. The hidden FAIL_TO_PASS test (test_shared_axes_clear) mirrors the reproduction snippet already present verbatim in the PUBLIC problem_statement (subplots 2x2 sharex/sharey, arange(0,2*pi,0.01), sin, clear+plot loop). No test file path, test function/class names, parametrization ids, or quoted test/gold code appear. The combined/major/minor enumeration reflects real behavior, not the hidden-test parametrization. No semantic reconstruction of the hidden tests.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
