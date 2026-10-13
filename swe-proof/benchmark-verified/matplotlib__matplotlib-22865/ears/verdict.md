# P2 adversarial audit — matplotlib__matplotlib-22865

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 7 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 7 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py`, `probe_7.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (7):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib as mpl
from matplotlib.colors import BoundaryNorm

def make(extend, drawedges=True):
    cmap = plt.get_cmap("viridis")
    bounds = [0, 1, 2, 3, 4, 5, 6]
    norm = BoundaryNorm(bounds, cmap.N, extend=extend)
    fig, ax = plt.subplots()
    cb = fig.colorbar(mpl.cm.ScalarMappable(norm=norm, cmap=cmap),
                      cax=ax, drawedges=drawedges, extend=extend)
    return fig, cb

def ys(cb):
    return sorted(round(float(s[0][1]), 4) for s in cb.dividers.get_segments())

import sys
fig, cb = make("both")
y = ys(cb)
print("extend=both drawedges=True ys=", y)
# Req1.4: both extremities (0.0 and 6.0) AND all interior 1..5 present
expected = [0.0,1.0,2.0,3.0,4.0,5.0,6.0]
ok = (y == expected)
print("expected", expected, "ok", ok)
sys.exit(0 if ok else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib as mpl
from matplotlib.colors import BoundaryNorm

def make(extend, drawedges=True):
    cmap = plt.get_cmap("viridis")
    bounds = [0, 1, 2, 3, 4, 5, 6]
    norm = BoundaryNorm(bounds, cmap.N, extend=extend)
    fig, ax = plt.subplots()
    cb = fig.colorbar(mpl.cm.ScalarMappable(norm=norm, cmap=cmap),
                      cax=ax, drawedges=drawedges, extend=extend)
    return fig, cb

def ys(cb):
    return sorted(round(float(s[0][1]), 4) for s in cb.dividers.get_segments())

import sys
fig, cb = make("min")
y = ys(cb)
print("extend=min ys=", y)
# lower extremity 0.0 included, upper 6.0 excluded, interior present
ok = (0.0 in y) and (6.0 not in y) and all(v in y for v in [1,2,3,4,5])
print("ok", ok)
sys.exit(0 if ok else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib as mpl
from matplotlib.colors import BoundaryNorm

def make(extend, drawedges=True):
    cmap = plt.get_cmap("viridis")
    bounds = [0, 1, 2, 3, 4, 5, 6]
    norm = BoundaryNorm(bounds, cmap.N, extend=extend)
    fig, ax = plt.subplots()
    cb = fig.colorbar(mpl.cm.ScalarMappable(norm=norm, cmap=cmap),
                      cax=ax, drawedges=drawedges, extend=extend)
    return fig, cb

def ys(cb):
    return sorted(round(float(s[0][1]), 4) for s in cb.dividers.get_segments())

import sys
fig, cb = make("max")
y = ys(cb)
print("extend=max ys=", y)
ok = (6.0 in y) and (0.0 not in y) and all(v in y for v in [1,2,3,4,5])
print("ok", ok)
sys.exit(0 if ok else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib as mpl
from matplotlib.colors import BoundaryNorm

def make(extend, drawedges=True):
    cmap = plt.get_cmap("viridis")
    bounds = [0, 1, 2, 3, 4, 5, 6]
    norm = BoundaryNorm(bounds, cmap.N, extend=extend)
    fig, ax = plt.subplots()
    cb = fig.colorbar(mpl.cm.ScalarMappable(norm=norm, cmap=cmap),
                      cax=ax, drawedges=drawedges, extend=extend)
    return fig, cb

def ys(cb):
    return sorted(round(float(s[0][1]), 4) for s in cb.dividers.get_segments())

import sys
fig, cb = make("neither")
y = ys(cb)
print("extend=neither ys=", y)
# only interior 1..5; 0.0 and 6.0 excluded
ok = (0.0 not in y) and (6.0 not in y) and y == [1.0,2.0,3.0,4.0,5.0]
print("ok", ok)
sys.exit(0 if ok else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib as mpl
from matplotlib.colors import BoundaryNorm

def make(extend, drawedges=True):
    cmap = plt.get_cmap("viridis")
    bounds = [0, 1, 2, 3, 4, 5, 6]
    norm = BoundaryNorm(bounds, cmap.N, extend=extend)
    fig, ax = plt.subplots()
    cb = fig.colorbar(mpl.cm.ScalarMappable(norm=norm, cmap=cmap),
                      cax=ax, drawedges=drawedges, extend=extend)
    return fig, cb

def ys(cb):
    return sorted(round(float(s[0][1]), 4) for s in cb.dividers.get_segments())

import sys
allok = True
for extend in ["neither","both","min","max"]:
    fig, cb = make(extend, drawedges=False)
    n = len(cb.dividers.get_segments())
    print("drawedges=False extend=%s nseg=%d" % (extend, n))
    if n != 0:
        allok = False
sys.exit(0 if allok else 1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib as mpl
from matplotlib.colors import BoundaryNorm

def make(extend, drawedges=True):
    cmap = plt.get_cmap("viridis")
    bounds = [0, 1, 2, 3, 4, 5, 6]
    norm = BoundaryNorm(bounds, cmap.N, extend=extend)
    fig, ax = plt.subplots()
    cb = fig.colorbar(mpl.cm.ScalarMappable(norm=norm, cmap=cmap),
                      cax=ax, drawedges=drawedges, extend=extend)
    return fig, cb

def ys(cb):
    return sorted(round(float(s[0][1]), 4) for s in cb.dividers.get_segments())

import sys
import numpy as np
# For extend both, number of segments should equal number of boundary rows kept.
# boundaries mesh has len(bounds) rows for interior; check ordering matches mesh Y.
fig, cb = make("both")
segs = cb.dividers.get_segments()
# segments should be in increasing y order matching the color band boundaries
yvals = [float(s[0][1]) for s in segs]
print("segment first-point ys (order):", yvals)
ordered = all(yvals[i] <= yvals[i+1] for i in range(len(yvals)-1))
# each segment is a 2-point line collection
shapes_ok = all(np.asarray(s).shape[0] == 2 for s in segs)
print("ordered", ordered, "shapes_ok", shapes_ok, "count", len(segs))
ok = ordered and shapes_ok and len(segs) == 7
sys.exit(0 if ok else 1)
```

Attack 7 — `probe_7.py` → holds on the patched tree (good)

```python
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib as mpl
from matplotlib.colors import BoundaryNorm

def make(extend, drawedges=True):
    cmap = plt.get_cmap("viridis")
    bounds = [0, 1, 2, 3, 4, 5, 6]
    norm = BoundaryNorm(bounds, cmap.N, extend=extend)
    fig, ax = plt.subplots()
    cb = fig.colorbar(mpl.cm.ScalarMappable(norm=norm, cmap=cmap),
                      cax=ax, drawedges=drawedges, extend=extend)
    return fig, cb

def ys(cb):
    return sorted(round(float(s[0][1]), 4) for s in cb.dividers.get_segments())

import sys
import numpy as np
fig, cb = make("both")
lc = cb.dividers
# colors and linewidths present & nonzero
colors = lc.get_edgecolors()
lws = lc.get_linewidths()
print("edgecolors shape", np.asarray(colors).shape, "linewidths", lws)
# solids drawn (color bands unaffected)
has_solids = cb.solids is not None
print("has_solids", has_solids)
ok = len(np.asarray(colors)) >= 1 and len(np.asarray(lws)) >= 1 and has_solids
sys.exit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib as mpl
from matplotlib.colors import BoundaryNorm

def make(extend, drawedges=True):
    cmap = plt.get_cmap("viridis")
    bounds = [0, 1, 2, 3, 4, 5, 6]
    norm = BoundaryNorm(bounds, cmap.N, extend=extend)
    fig, ax = plt.subplots()
    cb = fig.colorbar(mpl.cm.ScalarMappable(norm=norm, cmap=cmap),
                      cax=ax, drawedges=drawedges, extend=extend)
    return fig, cb

def ys(cb):
    return sorted(round(float(s[0][1]), 4) for s in cb.dividers.get_segments())

import sys
fig, cb = make("both")
y = ys(cb)
print("extend=both drawedges=True ys=", y)
# Req1.4: both extremities (0.0 and 6.0) AND all interior 1..5 present
expected = [0.0,1.0,2.0,3.0,4.0,5.0,6.0]
ok = (y == expected)
print("expected", expected, "ok", ok)
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance fixes Colorbar._add_solids to keep terminal separator segments at OPEN (extended) ends while omitting them at closed ends, driven by _extend_lower()/_extend_upper().

7 probes, all HOLD on gold-patched tree:
- probe_1 (Req1.4, POSITIVE CONTROL): extend='both' -> separators at ys [0..6] incl both extremities. HOLDS patched, FAILS base (base gives [1..5]). Discriminates.
- probe_2 (Req1.5): extend='min' -> lower extremity 0.0 kept, upper 6.0 omitted, interior present. HOLDS patched, FAILS base.
- probe_3 (Req1.6): extend='max' -> upper 6.0 kept, lower 0.0 omitted. HOLDS patched, FAILS base.
- probe_4 (Req2.3): extend='neither' -> exactly interior [1..5], both ends excluded (prior behavior). HOLDS patched AND base (regression criterion).
- probe_5 (Req4.1): drawedges=False -> 0 segments for all extend values. HOLDS patched AND base.
- probe_6 (Req1.1): segments ordered from mesh, 2-point shapes, count==kept boundaries (7 for both). HOLDS patched, FAILS base.
- probe_7 (Req5.4/5.2): divider edgecolor & linewidth present (1x4 rgba, lw 0.4) and solids drawn. HOLDS patched AND base.

CANDIDATE (weak.diff): naive fix that ALWAYS keeps every boundary segment including both ends (np.dstack([X,Y]) with no start/end slicing). Applies at base. Under it probes 2,3,4 are REJECTED (extend='min'/'max' wrongly include the closed extremity; extend='neither' wrongly includes both ends -> doubled outer edge, violating Req2). This is the exact fix a weak reading ("draw all edges") permits and it breaks the closed-end omission requirement, so it would not match the hidden tests' expectation. Suite discriminates the wrong implementation.

All needed runs completed (patched + base + candidate). Positive control discriminates. Verdict SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 7 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 7 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py`, `probe_7.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (7):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts, and on this backend both roles put it through the same derivation: every block below is a requirement probe run on the gold-patched tree, and the `machine verdict:` line each role publishes above reports BOTH that its probes hold there and how many candidate patches the probe suite rejected — so the two roles re-ran ONE probe suite and each recorded its own outcome for every probe in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `probe_1.py` → holds on the patched tree (good)

Attack 2 — `probe_2.py` → holds on the patched tree (good)

Attack 3 — `probe_3.py` → holds on the patched tree (good)

Attack 4 — `probe_4.py` → holds on the patched tree (good)

Attack 5 — `probe_5.py` → holds on the patched tree (good)

Attack 6 — `probe_6.py` → holds on the patched tree (good)

Attack 7 — `probe_7.py` → holds on the patched tree (good)

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib as mpl
from matplotlib.colors import BoundaryNorm

def make(extend, drawedges=True):
    cmap = plt.get_cmap("viridis")
    bounds = [0, 1, 2, 3, 4, 5, 6]
    norm = BoundaryNorm(bounds, cmap.N, extend=extend)
    fig, ax = plt.subplots()
    cb = fig.colorbar(mpl.cm.ScalarMappable(norm=norm, cmap=cmap),
                      cax=ax, drawedges=drawedges, extend=extend)
    return fig, cb

def ys(cb):
    return sorted(round(float(s[0][1]), 4) for s in cb.dividers.get_segments())

import sys
fig, cb = make("both")
y = ys(cb)
print("extend=both drawedges=True ys=", y)
# Req1.4: both extremities (0.0 and 6.0) AND all interior 1..5 present
expected = [0.0,1.0,2.0,3.0,4.0,5.0,6.0]
ok = (y == expected)
print("expected", expected, "ok", ok)
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance fixes Colorbar._add_solids to keep terminal separator segments at OPEN (extended) ends while omitting them at closed ends, driven by _extend_lower()/_extend_upper().

7 probes, all HOLD on gold-patched tree:
- probe_1 (Req1.4, POSITIVE CONTROL): extend='both' -> separators at ys [0..6] incl both extremities. HOLDS patched, FAILS base (base gives [1..5]). Discriminates.
- probe_2 (Req1.5): extend='min' -> lower extremity 0.0 kept, upper 6.0 omitted, interior present. HOLDS patched, FAILS base.
- probe_3 (Req1.6): extend='max' -> upper 6.0 kept, lower 0.0 omitted. HOLDS patched, FAILS base.
- probe_4 (Req2.3): extend='neither' -> exactly interior [1..5], both ends excluded (prior behavior). HOLDS patched AND base (regression criterion).
- probe_5 (Req4.1): drawedges=False -> 0 segments for all extend values. HOLDS patched AND base.
- probe_6 (Req1.1): segments ordered from mesh, 2-point shapes, count==kept boundaries (7 for both). HOLDS patched, FAILS base.
- probe_7 (Req5.4/5.2): divider edgecolor & linewidth present (1x4 rgba, lw 0.4) and solids drawn. HOLDS patched AND base.

CANDIDATE (weak.diff): naive fix that ALWAYS keeps every boundary segment including both ends (np.dstack([X,Y]) with no start/end slicing). Applies at base. Under it probes 2,3,4 are REJECTED (extend='min'/'max' wrongly include the closed extremity; extend='neither' wrongly includes both ends -> doubled outer edge, violating Req2). This is the exact fix a weak reading ("draw all edges") permits and it breaks the closed-end omission requirement, so it would not match the hidden tests' expectation. Suite discriminates the wrong implementation.

All needed runs completed (patched + base + candidate). Positive control discriminates. Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Gold patch replaces the fixed `[1:-1]` slice of np.dstack([X,Y]) with start_idx=0 if _extend_lower() else 1, end_idx=len(X) if _extend_upper() else -1, and empties dividers when not drawedges. Probe on gold-patched tree (5-boundary BoundaryNorm colorbar): drawedges=True segment counts = neither:3, min:4, max:4, both:5; drawedges=False both:0; inverted-axis both:5, inverted min:4 (lo=False,up=True). All match Req1(1-6), Req2(1-3), Req3(1-2), Req4(1). Req5 preservation claims are true (patch touches only the dividers.set_segments selection line; extension shapes, ticks, rasterization, styling unchanged). Modeling boundary is correct — requirements target the full changed behavior (terminal-segment inclusion at open ends) rather than a single branch or helper.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The document names only pre-existing code entities — Colorbar._add_solids, the dividers line collection, _extend_lower()/_extend_upper(), drawedges, n_rasterize (rasterization) — all of which exist in the codebase before the fix and are legitimate localization, not fix-invented identifiers. The gold patch's invented locals (start_idx, end_idx) and the [start_idx:end_idx] slicing do NOT appear; requirements instead describe behavior ('keep terminal boundary at open ends, omit at closed ends'). The enumeration of extend='both'/'min'/'max'/'neither' (Req 1.4-1.6, 2.3) mirrors the four test parametrization cases, but these four values are the complete public set of the extend API parameter (extend='both' is already named in problem_statement), and the requirements state only behavioral outcomes (which extremity separator is included/excluded) — NOT the hidden test's concrete segment-coordinate arrays (e.g. np.array([[0.,0.],[0.,1.]])), coloroffset values, test function name test_colorbar_extend_drawedges, file path, or res ids. No quoted test/gold code, no test-shaped reconstruction beyond an exhaustive-by-API description of behavior. This is legitimate translation of test-checked behavior into requirements.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
