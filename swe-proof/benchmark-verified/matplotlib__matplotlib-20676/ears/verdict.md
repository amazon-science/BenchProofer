# P2 adversarial audit — matplotlib__matplotlib-20676

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 6 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 6 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 6 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_3.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (6):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
#!/usr/bin/env python
# Positive control. Requirement 1.1/1.3: constructing an interactive horizontal
# SpanSelector must leave the x view bounds unchanged (in particular NOT expand
# to include 0). Data view spans (10,20). HOLDS patched, FAILS at base.
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.widgets as widgets

# Rely on autoscaling (do NOT set explicit limits, else autoscale is disabled
# and adding an axvline at 0 wouldn't move the view). Data spans (10,20).
fig, ax = plt.subplots()
ax.plot([10, 20], [10, 20])
ax.figure.canvas.draw()
before = ax.get_xbound()
ss = widgets.SpanSelector(ax, lambda a, b: None, "horizontal", interactive=True)
after = ax.get_xbound()
print("xbound before:", before, "after:", after)
ok = (abs(after[0] - before[0]) < 1e-9 and abs(after[1] - before[1]) < 1e-9)
# specifically must not have pulled lower bound down to 0
if after[0] <= 1e-9:
    print("FAIL: lower x bound was pulled to ~0")
    ok = False
print("PASS" if ok else "FAIL")
raise SystemExit(0 if ok else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
#!/usr/bin/env python
# Requirement 1.2/1.3 (vertical): constructing an interactive vertical
# SpanSelector must leave the y view bounds unchanged (NOT expand to include 0).
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.widgets as widgets

# Rely on autoscaling (no explicit limits) so a stray handle at 0 would move view.
fig, ax = plt.subplots()
ax.plot([10, 20], [10, 20])
ax.figure.canvas.draw()
before = ax.get_ybound()
ss = widgets.SpanSelector(ax, lambda a, b: None, "vertical", interactive=True)
after = ax.get_ybound()
print("ybound before:", before, "after:", after)
ok = (abs(after[0] - before[0]) < 1e-9 and abs(after[1] - before[1]) < 1e-9)
if after[0] <= 1e-9:
    print("FAIL: lower y bound was pulled to ~0")
    ok = False
print("PASS" if ok else "FAIL")
raise SystemExit(0 if ok else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
#!/usr/bin/env python
# Requirement 2.1/2.2/2.3: on construction (no interaction yet), the edge handles'
# reported positions equal the operating axis' bounds. Horizontal -> xbound;
# vertical -> ybound.
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.widgets as widgets

ok = True
for direction in ("horizontal", "vertical"):
    fig, ax = plt.subplots()
    ax.plot([10, 20], [10, 20])
    ax.set_xlim(10, 20)
    ax.set_ylim(10, 20)
    ax.figure.canvas.draw()
    ss = widgets.SpanSelector(ax, lambda a, b: None, direction, interactive=True)
    bound = ax.get_xbound() if direction == "horizontal" else ax.get_ybound()
    pos = ss._edge_handles.positions
    print(direction, "handle positions:", pos, "expected bound:", bound)
    if not (len(pos) == 2 and abs(pos[0] - bound[0]) < 1e-9 and abs(pos[1] - bound[1]) < 1e-9):
        print("FAIL: handles not seeded from axis bounds for", direction)
        ok = False
    plt.close(fig)
print("PASS" if ok else "FAIL")
raise SystemExit(0 if ok else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
#!/usr/bin/env python
# Requirement 3.1/3.3: pressing at one coordinate and moving to another makes
# the edge handles report the span endpoints. Also 3.2: view bounds preserved
# throughout. Horizontal selector.
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.widgets as widgets
from matplotlib.testing.widgets import do_event

fig, ax = plt.subplots()
ax.plot([10, 20], [10, 20])
ax.set_xlim(10, 20)
ax.set_ylim(10, 20)
ax.figure.canvas.draw()
xb0, yb0 = ax.get_xbound(), ax.get_ybound()
ss = widgets.SpanSelector(ax, lambda a, b: None, "horizontal", interactive=True)

do_event(ss, "press", xdata=12, ydata=14)
do_event(ss, "onmove", xdata=17, ydata=14)
do_event(ss, "release", xdata=17, ydata=14)

pos = sorted(ss._edge_handles.positions)
print("handle positions after drag:", pos)
print("extents:", ss.extents)
ok = abs(pos[0] - 12) < 1e-6 and abs(pos[1] - 17) < 1e-6
xb1, yb1 = ax.get_xbound(), ax.get_ybound()
print("xbound", xb0, "->", xb1, " ybound", yb0, "->", yb1)
if xb1 != xb0 or yb1 != yb0:
    print("FAIL: view bounds changed during interaction")
    ok = False
print("PASS" if ok else "FAIL")
raise SystemExit(0 if ok else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
#!/usr/bin/env python
# Requirement 4.1: interactive edge handles exist as line artists (2 of them).
# Requirement 4.2: completing a selection > minspan invokes onselect with
# (min, max). Regression protection.
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.widgets as widgets
from matplotlib.lines import Line2D
from matplotlib.testing.widgets import do_event

fig, ax = plt.subplots()
ax.plot([10, 20], [10, 20])
ax.set_xlim(10, 20)
ax.set_ylim(10, 20)
ax.figure.canvas.draw()

calls = []
ss = widgets.SpanSelector(ax, lambda vmin, vmax: calls.append((vmin, vmax)),
                          "horizontal", interactive=True)

handles = ss._edge_handles.artists
print("num handle artists:", len(handles),
      "all Line2D:", all(isinstance(h, Line2D) for h in handles))
ok = len(handles) == 2 and all(isinstance(h, Line2D) for h in handles)

do_event(ss, "press", xdata=13, ydata=14)
do_event(ss, "onmove", xdata=18, ydata=14)
do_event(ss, "release", xdata=18, ydata=14)
print("onselect calls:", calls)
if not (len(calls) == 1 and abs(calls[0][0] - 13) < 1e-6 and abs(calls[0][1] - 18) < 1e-6):
    print("FAIL: onselect not called with (min,max)")
    ok = False
print("PASS" if ok else "FAIL")
raise SystemExit(0 if ok else 1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
#!/usr/bin/env python
# Requirement 4.4: changing direction after construction rebuilds handles for
# the new axis, and (Req 2) they seed from the new operating axis' bounds and
# still don't disturb the view. Start horizontal, switch to vertical.
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.widgets as widgets

fig, ax = plt.subplots()
ax.plot([10, 20], [10, 20])
ax.set_xlim(10, 20)
ax.set_ylim(5, 25)
ax.figure.canvas.draw()
xb0, yb0 = ax.get_xbound(), ax.get_ybound()
ss = widgets.SpanSelector(ax, lambda a, b: None, "horizontal", interactive=True)
ss.direction = "vertical"
print("direction now:", ss.direction)
pos = ss._edge_handles.positions
yb = ax.get_ybound()
print("handle positions:", pos, "expected ybound:", yb)
ok = ss.direction == "vertical" and len(ss._edge_handles.artists) == 2
if not (abs(pos[0] - yb[0]) < 1e-9 and abs(pos[1] - yb[1]) < 1e-9):
    print("FAIL: handles not reseeded to y bounds after direction change")
    ok = False
xb1, yb1 = ax.get_xbound(), ax.get_ybound()
print("bounds", xb0, xb1, yb0, yb1)
if xb1 != xb0 or yb1 != yb0:
    print("FAIL: view bounds changed by direction switch")
    ok = False
print("PASS" if ok else "FAIL")
raise SystemExit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_3.py`

```python
#!/usr/bin/env python
# Requirement 2.1/2.2/2.3: on construction (no interaction yet), the edge handles'
# reported positions equal the operating axis' bounds. Horizontal -> xbound;
# vertical -> ybound.
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.widgets as widgets

ok = True
for direction in ("horizontal", "vertical"):
    fig, ax = plt.subplots()
    ax.plot([10, 20], [10, 20])
    ax.set_xlim(10, 20)
    ax.set_ylim(10, 20)
    ax.figure.canvas.draw()
    ss = widgets.SpanSelector(ax, lambda a, b: None, direction, interactive=True)
    bound = ax.get_xbound() if direction == "horizontal" else ax.get_ybound()
    pos = ss._edge_handles.positions
    print(direction, "handle positions:", pos, "expected bound:", bound)
    if not (len(pos) == 2 and abs(pos[0] - bound[0]) < 1e-9 and abs(pos[1] - bound[1]) < 1e-9):
        print("FAIL: handles not seeded from axis bounds for", direction)
        ok = False
    plt.close(fig)
print("PASS" if ok else "FAIL")
raise SystemExit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

SpanSelector(interactive=True) must not disturb host axes view bounds; fix seeds edge handles from get_xbound/get_ybound instead of empty extents.

Probes (all HOLD on gold-patched tree):
- probe_1 (Req 1.1/1.3, horizontal): with autoscaling active (no explicit limits, data (10,20)->view (9.5,20.5)), constructing interactive selector leaves xbound unchanged and does NOT pull lower bound to ~0. PATCHED: (9.5,20.5)->(9.5,20.5) PASS. BASE: (9.5,20.5)->(-1.0,21.0) FAIL (bug reproduced).
- probe_2 (Req 1.2/1.3, vertical): same for ybound. PATCHED PASS; BASE (9.5,20.5)->(-1.0,21.0) FAIL.
- probe_3 (Req 2.1/2.2/2.3, POSITIVE CONTROL): freshly-constructed interactive selector's edge-handle positions equal the operating axis' bounds (x for horizontal, y for vertical). PATCHED: [10,20] for both PASS. BASE: [0,0] FAIL. Discriminates.
- probe_4 (Req 3.1/3.2/3.3, horizontal): press@12 move@17 => handle positions become [12,17]; view bounds unchanged through interaction. PATCHED PASS.
- probe_5 (Req 4.1/4.2): two Line2D handle artists exist; completing selection >minspan invokes onselect(vmin,vmax)=(13,18). PATCHED PASS.
- probe_6 (Req 4.4 + Req 2): switching direction horizontal->vertical rebuilds 2 handles reseeded to ybound (5,25), view bounds preserved. PATCHED PASS.

Note: probes 1/2 originally used set_xlim/set_ylim which disables autoscale and masked the bug (held at base); switched to autoscaling to faithfully encode Req 1 and confirm base violation.

Wrong-fix candidate (weak.diff): keeps seeding handles from empty self.extents (positions at 0) but save/restores axis bounds around handle creation so the view is not rescaled. This satisfies the view-bounds requirements (probes 1,2,4 PASS) and regression probe 5, but is REJECTED by probe_3 (handles at [0,0] not axis bounds) and probe_6 (reseed at [0,0] after direction change). Applies cleanly at base_commit. This demonstrates the suite discriminates a naive/partial fix that a weak reading of only Req 1 would permit; the handle-seeding requirements (Req 2) are load-bearing and enforced, matching the hidden F2P tests test_span_selector_bound[horizontal/vertical] which assert handle positions equal the bounds. Suite is sound and discriminating.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 6 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 6 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_3.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (6):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

_The 6 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts, and on this backend both roles put it through the same derivation: every block below is a requirement probe run on the gold-patched tree, and the `machine verdict:` line each role publishes above reports BOTH that its probes hold there and how many candidate patches the probe suite rejected — so the two roles re-ran ONE probe suite and each recorded its own outcome for every probe in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `probe_1.py` → holds on the patched tree (good)

Attack 2 — `probe_2.py` → holds on the patched tree (good)

Attack 3 — `probe_3.py` → holds on the patched tree (good)

Attack 4 — `probe_4.py` → holds on the patched tree (good)

Attack 5 — `probe_5.py` → holds on the patched tree (good)

Attack 6 — `probe_6.py` → holds on the patched tree (good)

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_3.py`

```python
#!/usr/bin/env python
# Requirement 2.1/2.2/2.3: on construction (no interaction yet), the edge handles'
# reported positions equal the operating axis' bounds. Horizontal -> xbound;
# vertical -> ybound.
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.widgets as widgets

ok = True
for direction in ("horizontal", "vertical"):
    fig, ax = plt.subplots()
    ax.plot([10, 20], [10, 20])
    ax.set_xlim(10, 20)
    ax.set_ylim(10, 20)
    ax.figure.canvas.draw()
    ss = widgets.SpanSelector(ax, lambda a, b: None, direction, interactive=True)
    bound = ax.get_xbound() if direction == "horizontal" else ax.get_ybound()
    pos = ss._edge_handles.positions
    print(direction, "handle positions:", pos, "expected bound:", bound)
    if not (len(pos) == 2 and abs(pos[0] - bound[0]) < 1e-9 and abs(pos[1] - bound[1]) < 1e-9):
        print("FAIL: handles not seeded from axis bounds for", direction)
        ok = False
    plt.close(fig)
print("PASS" if ok else "FAIL")
raise SystemExit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

SpanSelector(interactive=True) must not disturb host axes view bounds; fix seeds edge handles from get_xbound/get_ybound instead of empty extents.

Probes (all HOLD on gold-patched tree):
- probe_1 (Req 1.1/1.3, horizontal): with autoscaling active (no explicit limits, data (10,20)->view (9.5,20.5)), constructing interactive selector leaves xbound unchanged and does NOT pull lower bound to ~0. PATCHED: (9.5,20.5)->(9.5,20.5) PASS. BASE: (9.5,20.5)->(-1.0,21.0) FAIL (bug reproduced).
- probe_2 (Req 1.2/1.3, vertical): same for ybound. PATCHED PASS; BASE (9.5,20.5)->(-1.0,21.0) FAIL.
- probe_3 (Req 2.1/2.2/2.3, POSITIVE CONTROL): freshly-constructed interactive selector's edge-handle positions equal the operating axis' bounds (x for horizontal, y for vertical). PATCHED: [10,20] for both PASS. BASE: [0,0] FAIL. Discriminates.
- probe_4 (Req 3.1/3.2/3.3, horizontal): press@12 move@17 => handle positions become [12,17]; view bounds unchanged through interaction. PATCHED PASS.
- probe_5 (Req 4.1/4.2): two Line2D handle artists exist; completing selection >minspan invokes onselect(vmin,vmax)=(13,18). PATCHED PASS.
- probe_6 (Req 4.4 + Req 2): switching direction horizontal->vertical rebuilds 2 handles reseeded to ybound (5,25), view bounds preserved. PATCHED PASS.

Note: probes 1/2 originally used set_xlim/set_ylim which disables autoscale and masked the bug (held at base); switched to autoscaling to faithfully encode Req 1 and confirm base violation.

Wrong-fix candidate (weak.diff): keeps seeding handles from empty self.extents (positions at 0) but save/restores axis bounds around handle creation so the view is not rescaled. This satisfies the view-bounds requirements (probes 1,2,4 PASS) and regression probe 5, but is REJECTED by probe_3 (handles at [0,0] not axis bounds) and probe_6 (reseed at [0,0] after direction change). Applies cleanly at base_commit. This demonstrates the suite discriminates a naive/partial fix that a weak reading of only Req 1 would permit; the handle-seeding requirements (Req 2) are load-bearing and enforced, matching the hidden F2P tests test_span_selector_bound[horizontal/vertical] which assert handle positions equal the bounds. Suite is sound and discriminating.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Gold patch changes _setup_edge_handle to seed ToolLineHandles positions from get_xbound()/get_ybound() instead of self.extents. Requirements 1-3 pin exactly this changed observable behavior (view-bound preservation + bound-seeded handle positions) at the correct boundary — the observable behavior, not merely the helper. Req 4 covers unchanged behavior as regression protection. Probes on patched tree (exit 0) and base tree (exit 1, xbound changed) confirm the modeling boundary is correct and discriminating.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Requirements translate the public bug (interactive SpanSelector forcing view limits to include 0) into behavioral acceptance criteria. All named identifiers (SpanSelector, ToolLineHandles, get_xbound/get_ybound, axvline/axhline, interactive, span_stays) are legitimate public API / localization. The gold edit's essence (seed handle positions from axis bounds instead of empty extents) is the very fix implied by the public problem statement. No hidden-test artifacts leak: no test function name (test_span_selector_bound), no file path, no parametrization ids, and crucially none of the test's numeric probe values (press [10.5,11.5], move [11,13]) appear. The (10,20) data comes verbatim from the public problem_statement. The horizontal/vertical enumeration mirrors the widget's inherent direction API, not the test's parametrize list. Requirement 2.2 references handle 'positions' equalling the bounds list, but .positions is a pre-existing ToolLineHandles attribute and this is behavior description, not test code transmission.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
