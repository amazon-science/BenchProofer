# P2 adversarial audit — matplotlib__matplotlib-23314

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
# Req 1.2/1.3 (positive control): hidden Axes3D renders pixel-identical to empty figure
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

def buf(fig):
    fig.canvas.draw()
    return np.asarray(fig.canvas.buffer_rgba()).copy()

# figure with hidden 3d axes + content
fig1 = plt.figure(figsize=(4,3), dpi=80)
ax = fig1.add_subplot(111, projection='3d')
ax.scatter([0,1,2],[0,1,2],[0,1,2])
ax.plot([0,1],[0,1],[0,1])
ax.set_visible(False)
b1 = buf(fig1)

# empty figure, same geometry, no axes content
fig2 = plt.figure(figsize=(4,3), dpi=80)
b2 = buf(fig2)

same = np.array_equal(b1, b2)
ndiff = int((b1 != b2).sum())
print("hidden-3d vs empty identical:", same, "diff-bytes:", ndiff)
raise SystemExit(0 if same else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
# Req 1.1/1.4: hidden Axes3D.draw returns early -> its OWN draw body side effects not run.
# Detect invocation ONLY when Axes3D.draw is on the call stack (draw invoking them).
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import traceback

fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')
ax.scatter([0,1],[0,1],[0,1])
ax.set_visible(False)

flags = {"apply_aspect_from_draw": False, "unstale_from_draw": False}

def in_axes3d_draw():
    for fr in traceback.extract_stack():
        if fr.name == "draw" and "axes3d.py" in fr.filename:
            return True
    return False

orig_aa = ax.apply_aspect
orig_us = ax._unstale_viewLim
def spy_aa(*a, **k):
    if in_axes3d_draw():
        flags["apply_aspect_from_draw"] = True
    return orig_aa(*a, **k)
def spy_us(*a, **k):
    if in_axes3d_draw():
        flags["unstale_from_draw"] = True
    return orig_us(*a, **k)
ax.apply_aspect = spy_aa
ax._unstale_viewLim = spy_us

fig.canvas.draw()
print("apply_aspect invoked from Axes3D.draw:", flags["apply_aspect_from_draw"],
      "| _unstale_viewLim invoked from Axes3D.draw:", flags["unstale_from_draw"])
ok = (not flags["apply_aspect_from_draw"]) and (not flags["unstale_from_draw"])
raise SystemExit(0 if ok else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
# Req 2.1/2.3: VISIBLE Axes3D still renders content (differs from empty) and toggling matters
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

def buf(fig):
    fig.canvas.draw()
    return np.asarray(fig.canvas.buffer_rgba()).copy()

fig1 = plt.figure(figsize=(4,3), dpi=80)
ax = fig1.add_subplot(111, projection='3d')
ax.scatter([0,1,2],[0,1,2],[0,1,2])
b_vis = buf(fig1)

fig2 = plt.figure(figsize=(4,3), dpi=80)
b_empty = buf(fig2)

differs = not np.array_equal(b_vis, b_empty)
print("visible-3d differs from empty:", differs)
raise SystemExit(0 if differs else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
# Req 2.2: per-artist visibility honored within a visible Axes3D.
# Same fig content and data limits; only difference is the line's own visibility flag.
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

def buf(fig):
    fig.canvas.draw()
    return np.asarray(fig.canvas.buffer_rgba()).copy()

def make(hide):
    fig = plt.figure(figsize=(4,3), dpi=80)
    ax = fig.add_subplot(111, projection='3d')
    l, = ax.plot([0,1,2],[0,1,2],[0,2,1], lw=5, color='red')
    # fix limits so autoscale differences don't confound the comparison
    ax.set_xlim(0,2); ax.set_ylim(0,2); ax.set_zlim(0,2)
    if hide:
        l.set_visible(False)
    return buf(fig)

b_visible = make(False)
b_hidden = make(True)
differs = not np.array_equal(b_visible, b_hidden)
print("visible-line vs hidden-line differ (per-artist visibility honored):", differs)
raise SystemExit(0 if differs else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
# Req 3.1: 2D hidden axes renders nothing (identical to empty) - regression preserved
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

def buf(fig):
    fig.canvas.draw()
    return np.asarray(fig.canvas.buffer_rgba()).copy()

fig1 = plt.figure(figsize=(4,3), dpi=80)
ax = fig1.add_subplot(111)
ax.plot([0,1,2],[2,1,0])
ax.set_visible(False)
b1 = buf(fig1)

fig2 = plt.figure(figsize=(4,3), dpi=80)
b2 = buf(fig2)

same = np.array_equal(b1, b2)
print("hidden-2d vs empty identical:", same)
raise SystemExit(0 if same else 1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
# Req 3.3: hidden axes not returned by pointer hit-testing (inaxes) - preserved for both 2D and 3D
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

fig = plt.figure(figsize=(4,3), dpi=80)
ax = fig.add_subplot(111, projection='3d')
fig.canvas.draw()
# center pixel
x = fig.bbox.width/2
y = fig.bbox.height/2
before = ax.contains_point if False else None
# use MouseEvent-like inaxes via canvas
from matplotlib.backend_bases import MouseEvent
ev = MouseEvent("motion_notify_event", fig.canvas, x, y)
in_when_visible = ev.inaxes
ax.set_visible(False)
ev2 = MouseEvent("motion_notify_event", fig.canvas, x, y)
in_when_hidden = ev2.inaxes
print("inaxes when visible:", in_when_visible, "| when hidden:", in_when_hidden)
ok = (in_when_visible is ax) and (in_when_hidden is None)
raise SystemExit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
# Req 1.2/1.3 (positive control): hidden Axes3D renders pixel-identical to empty figure
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

def buf(fig):
    fig.canvas.draw()
    return np.asarray(fig.canvas.buffer_rgba()).copy()

# figure with hidden 3d axes + content
fig1 = plt.figure(figsize=(4,3), dpi=80)
ax = fig1.add_subplot(111, projection='3d')
ax.scatter([0,1,2],[0,1,2],[0,1,2])
ax.plot([0,1],[0,1],[0,1])
ax.set_visible(False)
b1 = buf(fig1)

# empty figure, same geometry, no axes content
fig2 = plt.figure(figsize=(4,3), dpi=80)
b2 = buf(fig2)

same = np.array_equal(b1, b2)
ndiff = int((b1 != b2).sum())
print("hidden-3d vs empty identical:", same, "diff-bytes:", ndiff)
raise SystemExit(0 if same else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance fix: Axes3D.draw must honor set_visible(False), matching 2D Axes. Gold patch adds `if not self.get_visible(): return` at the very top of Axes3D.draw (before self._unstale_viewLim()).

Probe suite (all 6 HOLD on gold-patched tree):
- probe_1 (Req 1.2/1.3, POSITIVE CONTROL): hidden Axes3D with scatter+line renders pixel-identical to an empty figure of the same geometry. HOLDS patched (0 diff-bytes); VIOLATED at base (63912 diff-bytes) => prepatch reproduced, discriminating power confirmed.
- probe_2 (Req 1.1/1.4): when Axes3D is hidden, neither apply_aspect nor _unstale_viewLim is invoked FROM WITHIN Axes3D.draw (detected via call-stack frame filter on axes3d.py:draw). HOLDS patched; VIOLATED at base (both invoked from draw). This is the leg that catches an early-return placed too late.
- probe_3 (Req 2.1/2.3): a VISIBLE Axes3D with a scatter still renders content (differs from empty figure). HOLDS on both base and patched (no regression).
- probe_4 (Req 2.2): within a visible Axes3D, per-artist visibility is honored — toggling a line's own set_visible changes the render (limits pinned to isolate the artist). HOLDS both.
- probe_5 (Req 3.1): 2D hidden axes renders identically to empty figure — 2D contract preserved. HOLDS both.
- probe_6 (Req 3.3): a hidden axes is not returned by pointer hit-testing (MouseEvent.inaxes is None when hidden, is the axes when visible). HOLDS both.

Note on early-probe iterations: initial probe_2 spied all apply_aspect/_unstale_viewLim calls without a stack filter and falsely flagged apply_aspect (invoked by figure layout machinery, not by draw); initial probe_4 compared hidden-line vs no-line-added, confounded by autoscale data-limit differences. Both were corrected to test the actual criteria; corrected versions HOLD patched.

Candidate wrong-fix (weak_partial): places `if not self.get_visible(): return` AFTER self._unstale_viewLim() and self.patch.draw(renderer). This is the plausible lazy misreading. Probe suite REJECTS it: probe_2 VIOLATED (candidate-patched) because _unstale_viewLim still runs from draw — violating Req 1.4's mandate that the early return avoid the view-limit-refresh side effect. (probe_1/3/5 happen to still HOLD because Agg over-paints the background pane opaquely, so pixel identity survives — but Req 1.4's behavioral pin catches the defect.) Suite discriminates wrong implementations.

Verdict SOUND: >=5 distinct probes covering all three requirements' criteria (including 'SHALL keep' regressions 3.1/3.3) all hold on the patched tree; positive control (probe_1) discriminates base vs patched; and the requirements-conforming-but-partial candidate is rejected by the suite (probe_2).

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
# Req 1.2/1.3 (positive control): hidden Axes3D renders pixel-identical to empty figure
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

def buf(fig):
    fig.canvas.draw()
    return np.asarray(fig.canvas.buffer_rgba()).copy()

# figure with hidden 3d axes + content
fig1 = plt.figure(figsize=(4,3), dpi=80)
ax = fig1.add_subplot(111, projection='3d')
ax.scatter([0,1,2],[0,1,2],[0,1,2])
ax.plot([0,1],[0,1],[0,1])
ax.set_visible(False)
b1 = buf(fig1)

# empty figure, same geometry, no axes content
fig2 = plt.figure(figsize=(4,3), dpi=80)
b2 = buf(fig2)

same = np.array_equal(b1, b2)
ndiff = int((b1 != b2).sum())
print("hidden-3d vs empty identical:", same, "diff-bytes:", ndiff)
raise SystemExit(0 if same else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance fix: Axes3D.draw must honor set_visible(False), matching 2D Axes. Gold patch adds `if not self.get_visible(): return` at the very top of Axes3D.draw (before self._unstale_viewLim()).

Probe suite (all 6 HOLD on gold-patched tree):
- probe_1 (Req 1.2/1.3, POSITIVE CONTROL): hidden Axes3D with scatter+line renders pixel-identical to an empty figure of the same geometry. HOLDS patched (0 diff-bytes); VIOLATED at base (63912 diff-bytes) => prepatch reproduced, discriminating power confirmed.
- probe_2 (Req 1.1/1.4): when Axes3D is hidden, neither apply_aspect nor _unstale_viewLim is invoked FROM WITHIN Axes3D.draw (detected via call-stack frame filter on axes3d.py:draw). HOLDS patched; VIOLATED at base (both invoked from draw). This is the leg that catches an early-return placed too late.
- probe_3 (Req 2.1/2.3): a VISIBLE Axes3D with a scatter still renders content (differs from empty figure). HOLDS on both base and patched (no regression).
- probe_4 (Req 2.2): within a visible Axes3D, per-artist visibility is honored — toggling a line's own set_visible changes the render (limits pinned to isolate the artist). HOLDS both.
- probe_5 (Req 3.1): 2D hidden axes renders identically to empty figure — 2D contract preserved. HOLDS both.
- probe_6 (Req 3.3): a hidden axes is not returned by pointer hit-testing (MouseEvent.inaxes is None when hidden, is the axes when visible). HOLDS both.

Note on early-probe iterations: initial probe_2 spied all apply_aspect/_unstale_viewLim calls without a stack filter and falsely flagged apply_aspect (invoked by figure layout machinery, not by draw); initial probe_4 compared hidden-line vs no-line-added, confounded by autoscale data-limit differences. Both were corrected to test the actual criteria; corrected versions HOLD patched.

Candidate wrong-fix (weak_partial): places `if not self.get_visible(): return` AFTER self._unstale_viewLim() and self.patch.draw(renderer). This is the plausible lazy misreading. Probe suite REJECTS it: probe_2 VIOLATED (candidate-patched) because _unstale_viewLim still runs from draw — violating Req 1.4's mandate that the early return avoid the view-limit-refresh side effect. (probe_1/3/5 happen to still HOLD because Agg over-paints the background pane opaquely, so pixel identity survives — but Req 1.4's behavioral pin catches the defect.) Suite discriminates wrong implementations.

Verdict SOUND: >=5 distinct probes covering all three requirements' criteria (including 'SHALL keep' regressions 3.1/3.3) all hold on the patched tree; positive control (probe_1) discriminates base vs patched; and the requirements-conforming-but-partial candidate is rejected by the suite (probe_2).

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Probe (gold-patched): 'HOLDS exit=0; REQ1.3 OK / REQ2 OK / ALL OK'. Probe (--base): 'VIOLATED exit=1; AssertionError: hidden 3d not identical to empty'. Requirements pin the changed observable behavior (hidden Axes3D produces empty-equivalent render) rather than merely the branch/helper, matching the correct modeling boundary.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The requirements describe behavior derivable from the public problem_statement (set_visible(False) on a 3D projection subplot should hide it) and localize the change to Axes3D.draw / _AxesBase.draw — legitimate. References to subsequent draw side effects (aspect recompute, projection matrix, view-limit/_unstale_viewLim refresh) come from the public draw method source, not the hidden tests; the gold patch merely inserts `if not self.get_visible(): return` before _unstale_viewLim. No hidden-test artifacts leak: no test function/class names (test_invisible_axes / test_invisible_axes_events / TestScatter), no test file paths (lib/mpl_toolkits/tests/test_mplot3d.py, lib/matplotlib/tests/test_axes.py), no parametrization ids ([png]), no check_figures_equal decorator/fixtures, no quoted test or gold code, no fix-invented identifiers. Req 1.3's 'pixel-identical to an empty figure' is a faithful behavioral translation (of the check_figures_equal comparison) rather than a transmission of the test itself. Req 3.3's hit-testing/inaxes preservation corresponds to the renamed pre-existing 2D events test but is stated as a behavioral contract, not test content.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
