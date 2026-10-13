# P2 adversarial audit — matplotlib__matplotlib-25960

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
"""Positive control — Req 1 (criteria 2-6). Core fixed behavior:
subfigures(2,3, hspace=0.5, wspace=1/6) on a plain figure yields panel bboxes
with the requested spacing. Exact device-pixel rectangles per the test math.
HOLDS on patched, FAILS at base (edge-to-edge)."""
import sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

fig = plt.figure()  # default 6.4x4.8in @100dpi => 640x480 px
sub = fig.subfigures(2, 3, hspace=0.5, wspace=1/6.)
w, h = 640, 480

expect = {
    (0, 0): ([0., h*0.6], [w*0.3, h]),
    (0, 1): ([w*0.35, h*0.6], [w*0.65, h]),
    (0, 2): ([w*0.7, h*0.6], [w, h]),
    (1, 0): ([0, 0], [w*0.3, h*0.4]),
    (1, 1): ([w*0.35, 0], [w*0.65, h*0.4]),
    (1, 2): ([w*0.7, 0], [w, h*0.4]),
}
ok = True
for (j, i), (mn, mx) in expect.items():
    gmn = np.asarray(sub[j, i].bbox.min)
    gmx = np.asarray(sub[j, i].bbox.max)
    good = np.allclose(gmn, mn, atol=1e-6) and np.allclose(gmx, mx, atol=1e-6)
    print(f"panel[{j},{i}] min={gmn} exp={mn} max={gmx} exp={mx} ok={good}")
    ok = ok and good

print("HOLDS" if ok else "VIOLATED")
sys.exit(0 if ok else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""Req 1 criterion 2 & 4 (horizontal): with wspace=w only, each column has
figure-fraction width c_w = 1/(ncols + w*(ncols-1)), left edge of column i at
i*(c_w + w*c_w), gap between columns = w*c_w. Check via bbox fractions.
General check across several w values and column counts."""
import sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ok = True
for ncols, w in [(3, 1/6.), (4, 0.5), (2, 0.3)]:
    fig = plt.figure()
    W = fig.bbox.width
    sub = fig.subfigures(1, ncols, wspace=w)
    c_w = 1.0 / (ncols + w*(ncols-1))
    for i in range(ncols):
        left_exp = i*(c_w + w*c_w)
        right_exp = left_exp + c_w
        x0 = sub[i].bbox.min[0] / W
        x1 = sub[i].bbox.max[0] / W
        good = abs(x0-left_exp) < 1e-9 and abs(x1-right_exp) < 1e-9
        print(f"ncols={ncols} w={w} col{i}: x0={x0:.6f} exp={left_exp:.6f} "
              f"x1={x1:.6f} exp={right_exp:.6f} ok={good}")
        ok = ok and good
    # gap check
    for i in range(ncols-1):
        gap = sub[i+1].bbox.min[0]/W - sub[i].bbox.max[0]/W
        good = abs(gap - w*c_w) < 1e-9
        print(f"ncols={ncols} w={w} gap{i}={gap:.6f} exp={w*c_w:.6f} ok={good}")
        ok = ok and good
    plt.close(fig)

print("HOLDS" if ok else "VIOLATED")
sys.exit(0 if ok else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""Req 1 criteria 3 & 5 (vertical) + criterion 7 (fill unit square):
with hspace=h only, row j has height c_h = 1/(nrows + h*(nrows-1)), top edge
at 1 - j*(c_h + h*c_h). Also top row top=1, bottom row bottom=0."""
import sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ok = True
for nrows, h in [(2, 0.5), (3, 0.2), (4, 1.0)]:
    fig = plt.figure()
    H = fig.bbox.height
    sub = fig.subfigures(nrows, 1, hspace=h)
    c_h = 1.0 / (nrows + h*(nrows-1))
    for j in range(nrows):
        top_exp = 1 - j*(c_h + h*c_h)
        bot_exp = top_exp - c_h
        ytop = sub[j].bbox.max[1] / H
        ybot = sub[j].bbox.min[1] / H
        good = abs(ytop-top_exp) < 1e-9 and abs(ybot-bot_exp) < 1e-9
        print(f"nrows={nrows} h={h} row{j}: top={ytop:.6f} exp={top_exp:.6f} "
              f"bot={ybot:.6f} exp={bot_exp:.6f} ok={good}")
        ok = ok and good
    # criterion 7: extremes fill unit square
    top0 = sub[0].bbox.max[1]/H
    botN = sub[nrows-1].bbox.min[1]/H
    good = abs(top0-1.0) < 1e-9 and abs(botN-0.0) < 1e-9
    print(f"nrows={nrows} h={h} top0={top0:.6f} botN={botN:.6f} ok={good}")
    ok = ok and good
    plt.close(fig)

print("HOLDS" if ok else "VIOLATED")
sys.exit(0 if ok else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""Req 2 criteria 1 & 2 (regression): with NO wspace/hspace supplied (None) and
no layout engine, panels tile edge-to-edge. Column i spans [i/ncols,(i+1)/ncols],
row j spans [1-(j+1)/nrows, 1-j/nrows]. Must HOLD on both base and patched."""
import sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ok = True
nrows, ncols = 2, 3
fig = plt.figure()
W, H = fig.bbox.width, fig.bbox.height
sub = fig.subfigures(nrows, ncols)
for j in range(nrows):
    for i in range(ncols):
        x0 = sub[j, i].bbox.min[0]/W
        x1 = sub[j, i].bbox.max[0]/W
        y0 = sub[j, i].bbox.min[1]/H
        y1 = sub[j, i].bbox.max[1]/H
        xe0, xe1 = i/ncols, (i+1)/ncols
        ye0, ye1 = 1-(j+1)/nrows, 1-j/nrows
        good = (abs(x0-xe0) < 1e-9 and abs(x1-xe1) < 1e-9 and
                abs(y0-ye0) < 1e-9 and abs(y1-ye1) < 1e-9)
        print(f"[{j},{i}] x=[{x0:.4f},{x1:.4f}] exp=[{xe0:.4f},{xe1:.4f}] "
              f"y=[{y0:.4f},{y1:.4f}] exp=[{ye0:.4f},{ye1:.4f}] ok={good}")
        ok = ok and good

print("HOLDS" if ok else "VIOLATED")
sys.exit(0 if ok else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""Req 1 criterion 8: distinct spacing values => panels differ; larger wspace
shrinks panels and widens gaps. Compare wspace=0 vs 0.5 for a 1x3 grid."""
import sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

fig0 = plt.figure(); W0 = fig0.bbox.width
s0 = fig0.subfigures(1, 3, wspace=0.0)
fig1 = plt.figure(); W1 = fig1.bbox.width
s1 = fig1.subfigures(1, 3, wspace=0.5)

# panel width of col0
pw0 = (s0[0].bbox.max[0]-s0[0].bbox.min[0])/W0
pw1 = (s1[0].bbox.max[0]-s1[0].bbox.min[0])/W1
gap0 = s0[1].bbox.min[0]/W0 - s0[0].bbox.max[0]/W0
gap1 = s1[1].bbox.min[0]/W1 - s1[0].bbox.max[0]/W1

print(f"wspace=0.0: panelwidth={pw0:.6f} gap={gap0:.6f}")
print(f"wspace=0.5: panelwidth={pw1:.6f} gap={gap1:.6f}")

shrinks = pw1 < pw0 - 1e-9
widens = gap1 > gap0 + 1e-9
# wspace=0 should be gapless third (1/3) width
gapless0 = abs(pw0 - 1/3.) < 1e-9 and abs(gap0) < 1e-9
print(f"shrinks={shrinks} widens={widens} gapless0={gapless0}")
ok = shrinks and widens and gapless0
print("HOLDS" if ok else "VIOLATED")
sys.exit(0 if ok else 1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
"""Req 3 criteria 3 & 1 & 2: width_ratios honored + spacing gaps applied on top;
row-major indexing preserved; squeeze default. Use 1x3 with width_ratios=[1,2,1]
and wspace=0.5. Column fraction widths should be proportional to ratios after
reserving gaps: total = sum(ratios) + w*avg_width*(ncols-1) in ratio units.
Verify: widths proportional to [1,2,1], all gaps equal, fills unit square."""
import sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

fig = plt.figure(); W = fig.bbox.width
ratios = [1, 2, 1]
w = 0.5
sub = fig.subfigures(1, 3, wspace=w, width_ratios=ratios)
# squeeze default: 1x3 -> 1-D length-3
assert sub.shape == (3,), f"shape {sub.shape}"

widths = [(sub[i].bbox.max[0]-sub[i].bbox.min[0])/W for i in range(3)]
gaps = [sub[i+1].bbox.min[0]/W - sub[i].bbox.max[0]/W for i in range(2)]
print("widths", widths)
print("gaps", gaps)

# proportional to ratios
ok = abs(widths[0]-widths[2]) < 1e-9 and abs(widths[1]-2*widths[0]) < 1e-9
# gaps equal
ok = ok and abs(gaps[0]-gaps[1]) < 1e-9 and gaps[0] > 1e-9
# fills unit square
fill = abs(sub[0].bbox.min[0]/W) < 1e-9 and abs(sub[2].bbox.max[0]/W - 1.0) < 1e-9
ok = ok and fill
# gap size: average width * w. avg width = mean(widths)
avgw = sum(widths)/3
ok = ok and abs(gaps[0] - w*avgw) < 1e-9
print(f"prop&gaps&fill ok={ok} avgw={avgw:.6f} w*avgw={w*avgw:.6f}")
print("HOLDS" if ok else "VIOLATED")
sys.exit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Positive control — Req 1 (criteria 2-6). Core fixed behavior:
subfigures(2,3, hspace=0.5, wspace=1/6) on a plain figure yields panel bboxes
with the requested spacing. Exact device-pixel rectangles per the test math.
HOLDS on patched, FAILS at base (edge-to-edge)."""
import sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

fig = plt.figure()  # default 6.4x4.8in @100dpi => 640x480 px
sub = fig.subfigures(2, 3, hspace=0.5, wspace=1/6.)
w, h = 640, 480

expect = {
    (0, 0): ([0., h*0.6], [w*0.3, h]),
    (0, 1): ([w*0.35, h*0.6], [w*0.65, h]),
    (0, 2): ([w*0.7, h*0.6], [w, h]),
    (1, 0): ([0, 0], [w*0.3, h*0.4]),
    (1, 1): ([w*0.35, 0], [w*0.65, h*0.4]),
    (1, 2): ([w*0.7, 0], [w, h*0.4]),
}
ok = True
for (j, i), (mn, mx) in expect.items():
    gmn = np.asarray(sub[j, i].bbox.min)
    gmx = np.asarray(sub[j, i].bbox.max)
    good = np.allclose(gmn, mn, atol=1e-6) and np.allclose(gmx, mx, atol=1e-6)
    print(f"panel[{j},{i}] min={gmn} exp={mn} max={gmx} exp={mx} ok={good}")
    ok = ok and good

print("HOLDS" if ok else "VIOLATED")
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

matplotlib-25960: make Figure.subfigures honour wspace/hspace when no layout engine is active. 6 probes cover: probe_1 (positive control, Req1 c2-6 exact device-pixel bboxes for subfigures(2,3,hspace=.5,wspace=1/6) matching the hidden test) HOLDS patched / FAILS at base (edge-to-edge). probe_2 Req1 c2&4 horizontal: c_w=1/(ncols+w(ncols-1)), left edge i*(c_w+w*c_w), gap w*c_w across 3 configs. probe_3 Req1 c3&5&7 vertical: c_h formula, top edge 1-j*(c_h+h*c_h), extremes fill unit square. probe_4 Req2 c1&2 regression: None spacing => edge-to-edge tiling i/ncols, 1-(j+1)/nrows (holds base+patched). probe_5 Req1 c8 monotonicity: larger wspace shrinks panels & widens gaps, wspace=0 gapless third-width. probe_6 Req3 c1-3 width_ratios honoured + equal gaps + row-major squeeze default.

All 6 HOLD on patched tree; positive control FAILS at base (confirmed). CANDIDATE weak.diff = the lazy partial fix: adds GridSpec left=0/right=1/bottom=0/top=1 bounds (matching the doc change) but OMITS the _redo_transform_rel_fig loop; suite REJECTS it (probes 1,2,3,5,6 VIOLATED — panels still edge-to-edge; probe_4 correctly still holds since it tests the None-spacing regression path). Suite discriminates wrong implementations. No TOO-WEAK candidate found. (A second candidate weak2.diff had a corrupt hunk and was not usable; not needed — floor met.)

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
"""Positive control — Req 1 (criteria 2-6). Core fixed behavior:
subfigures(2,3, hspace=0.5, wspace=1/6) on a plain figure yields panel bboxes
with the requested spacing. Exact device-pixel rectangles per the test math.
HOLDS on patched, FAILS at base (edge-to-edge)."""
import sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

fig = plt.figure()  # default 6.4x4.8in @100dpi => 640x480 px
sub = fig.subfigures(2, 3, hspace=0.5, wspace=1/6.)
w, h = 640, 480

expect = {
    (0, 0): ([0., h*0.6], [w*0.3, h]),
    (0, 1): ([w*0.35, h*0.6], [w*0.65, h]),
    (0, 2): ([w*0.7, h*0.6], [w, h]),
    (1, 0): ([0, 0], [w*0.3, h*0.4]),
    (1, 1): ([w*0.35, 0], [w*0.65, h*0.4]),
    (1, 2): ([w*0.7, 0], [w, h*0.4]),
}
ok = True
for (j, i), (mn, mx) in expect.items():
    gmn = np.asarray(sub[j, i].bbox.min)
    gmx = np.asarray(sub[j, i].bbox.max)
    good = np.allclose(gmn, mn, atol=1e-6) and np.allclose(gmx, mx, atol=1e-6)
    print(f"panel[{j},{i}] min={gmn} exp={mn} max={gmx} exp={mx} ok={good}")
    ok = ok and good

print("HOLDS" if ok else "VIOLATED")
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

matplotlib-25960: make Figure.subfigures honour wspace/hspace when no layout engine is active. 6 probes cover: probe_1 (positive control, Req1 c2-6 exact device-pixel bboxes for subfigures(2,3,hspace=.5,wspace=1/6) matching the hidden test) HOLDS patched / FAILS at base (edge-to-edge). probe_2 Req1 c2&4 horizontal: c_w=1/(ncols+w(ncols-1)), left edge i*(c_w+w*c_w), gap w*c_w across 3 configs. probe_3 Req1 c3&5&7 vertical: c_h formula, top edge 1-j*(c_h+h*c_h), extremes fill unit square. probe_4 Req2 c1&2 regression: None spacing => edge-to-edge tiling i/ncols, 1-(j+1)/nrows (holds base+patched). probe_5 Req1 c8 monotonicity: larger wspace shrinks panels & widens gaps, wspace=0 gapless third-width. probe_6 Req3 c1-3 width_ratios honoured + equal gaps + row-major squeeze default.

All 6 HOLD on patched tree; positive control FAILS at base (confirmed). CANDIDATE weak.diff = the lazy partial fix: adds GridSpec left=0/right=1/bottom=0/top=1 bounds (matching the doc change) but OMITS the _redo_transform_rel_fig loop; suite REJECTS it (probes 1,2,3,5,6 VIOLATED — panels still edge-to-edge; probe_4 correctly still holds since it tests the None-spacing regression path). Suite discriminates wrong implementations. No TOO-WEAK candidate found. (A second candidate weak2.diff had a corrupt hunk and was not usable; not needed — floor met.)

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Patch adds left=0,right=1,bottom=0,top=1 to the GridSpec and, when get_layout_engine() is None and (wspace is not None or hspace is not None), calls gs.get_grid_positions(self) and _redo_transform_rel_fig per panel. This precisely matches Req 1.1 (guard: no layout engine AND at least one spacing not None), Req 2.1/2.3 (None+None -> zero spacing edge-to-edge), and Req 3.5 (spacing applied only when no layout engine active). Reqs 3.1-3.4 describe pre-existing grid/squeeze/ratios/SubFigure behavior untouched by the patch and correctly stated as preserved invariants. The modeling boundary is the changed observable behavior (per-panel bbox rectangles as a function of wspace/hspace), not a helper or single branch. No divergence found.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** requirements.md describes the wspace/hspace layout behavior generically. It transmits none of the hidden test's parametrization: no 2x3 grid, no hspace=0.5/wspace=1/6, no 640/480 dims, none of the specific bbox fractions (0.3/0.35/0.6/0.65/0.7/0.4), no test name/path. The formulas c=1/(k+s(k-1)) and gap s*c are the standard public GridSpec grid math, derivable from the documented meaning of wspace/hspace, not lifted from the tests. Identifiers named (figure.py, FigureBase.subfigures, GridSpec.get_grid_positions) are pre-existing public symbols used for legitimate localization; the problem_statement already points at figure.py. Fix-invented/private symbols in the gold (_redo_transform_rel_fig, Bbox.from_extents, the left=0/right=1 GridSpec args) are NOT present. The no-layout-engine + spacing-not-None guard mirrors the documented docstring semantics rather than quoting the gold. This is behavioral translation, not test/gold transmission.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
