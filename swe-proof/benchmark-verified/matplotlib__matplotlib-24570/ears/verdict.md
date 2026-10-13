# P2 adversarial audit — matplotlib__matplotlib-24570

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 6 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 6 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 6 | `probe_1_leftbottom.py`, `probe_2_righttop.py`, `probe_3_size_unchanged.py`, `probe_4_baseline_center.py`, `probe_5_hpacker.py`, `probe_6_vpacker.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_5_hpacker.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (6):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1_leftbottom.py` → holds on the patched tree (good)

```python
# R1.1: left/bottom -> descent 0, offset == box's own descent
import sys
import matplotlib.offsetbox as ob
hd = [(10.0, 2.0), (6.0, 1.0), (4.0, 0.5)]
total = 12.0
ok = True
for align in ["left", "bottom"]:
    h, d, offs = ob._get_aligned_offsets(hd, total, align)
    exp = [dd for _, dd in hd]
    print(align, "descent=", d, "offsets=", offs, "expected=", exp)
    if d != 0.:
        ok = False
    if list(offs) != exp:
        ok = False
sys.exit(0 if ok else 1)
```

Attack 2 — `probe_2_righttop.py` → holds on the patched tree (good)

```python
# R1.2: right/top -> descent 0, offset == total - length + descent
import sys
import matplotlib.offsetbox as ob
hd = [(10.0, 2.0), (6.0, 1.0), (4.0, 0.5)]
total = 12.0
ok = True
for align in ["right", "top"]:
    h, d, offs = ob._get_aligned_offsets(hd, total, align)
    exp = [total - hh + dd for hh, dd in hd]
    print(align, "descent=", d, "offsets=", offs, "expected=", exp)
    if d != 0.:
        ok = False
    if list(offs) != exp:
        ok = False
sys.exit(0 if ok else 1)
```

Attack 3 — `probe_3_size_unchanged.py` → holds on the patched tree (good)

```python
# R1.3: for left/top/right/bottom/center total is returned unchanged as resolved size
import sys
import matplotlib.offsetbox as ob
hd = [(10.0, 2.0), (6.0, 1.0), (4.0, 0.5)]
total = 12.0
ok = True
for align in ["left", "top", "right", "bottom", "center"]:
    h, d, offs = ob._get_aligned_offsets(hd, total, align)
    print(align, "resolved size=", h)
    if h != total:
        ok = False
sys.exit(0 if ok else 1)
```

Attack 4 — `probe_4_baseline_center.py` → holds on the patched tree (good)

```python
# R2.1 baseline, R2.2 center, R2.3 invalid raises
import sys
import matplotlib.offsetbox as ob
hd = [(10.0, 2.0), (6.0, 1.0), (4.0, 0.5)]
total = 12.0
ok = True
# baseline
h, d, offs = ob._get_aligned_offsets(hd, total, "baseline")
exp_h = max(hh - dd for hh, dd in hd) + max(dd for _, dd in hd)
exp_d = max(dd for _, dd in hd)
print("baseline size=", h, "exp=", exp_h, "descent=", d, "exp=", exp_d, "offs=", offs)
if h != exp_h or d != exp_d or list(offs) != [0.]*len(hd):
    ok = False
# center
h, d, offs = ob._get_aligned_offsets(hd, total, "center")
exp = [(total - hh) * .5 + dd for hh, dd in hd]
print("center descent=", d, "offs=", offs, "exp=", exp)
if d != 0. or list(offs) != exp:
    ok = False
# invalid raises
try:
    ob._get_aligned_offsets(hd, total, "bogus")
    print("invalid did NOT raise")
    ok = False
except Exception as e:
    print("invalid raised:", type(e).__name__, e)
sys.exit(0 if ok else 1)
```

Attack 5 — `probe_5_hpacker.py` → holds on the patched tree (good)

```python
# R3: HPacker vertical placement of children of differing heights.
import sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.offsetbox import DrawingArea, HPacker

fig = plt.figure()
renderer = fig.canvas.get_renderer()
ok = True

def child_extent(w, h):
    return DrawingArea(w, h, 0, 0).get_extent(renderer)  # (height, descent, width_related?)

def run(align):
    c1 = DrawingArea(10, 20.0, 0, 0)   # taller
    c2 = DrawingArea(10, 8.0, 0, 0)    # shorter
    p = HPacker(pad=0, sep=0, align=align, children=[c1, c2])
    ext = p.get_extent_offsets(renderer)
    w, h, xd, yd, offsets = ext
    e1 = c1.get_extent(renderer)  # (width, height, xdescent, ydescent)
    e2 = c2.get_extent(renderer)
    ys = [oy for ox, oy in offsets]
    return w, h, xd, yd, ys, e1, e2

# R3.4 extent
w, h, xd, yd, ys, e1, e2 = run("bottom")
sum_w = e1[0] + e2[0]
max_h = max(e1[1], e2[1])
print("extent w=", w, "sum_w=", sum_w, "h=", h, "max_h=", max_h, "xd=", xd, "yd=", yd)
if not (abs(w - sum_w) < 1e-6 and abs(h - max_h) < 1e-6 and xd == 0 and yd == 0):
    ok = False

hdiff = e1[1] - e2[1]  # taller - shorter

# baseline/left/bottom: shorter flush low -> diff 0
for align in ["baseline", "left", "bottom"]:
    _, _, _, _, ys, _, _ = run(align)
    diff = ys[1] - ys[0]
    print(align, "y offsets=", ys, "diff=", diff)
    if abs(diff) > 1e-9:
        ok = False

# top/right: shorter shifted by full height difference
for align in ["top", "right"]:
    _, _, _, _, ys, _, _ = run(align)
    diff = ys[1] - ys[0]
    print(align, "y offsets=", ys, "diff=", diff, "hdiff=", hdiff)
    if abs(diff - hdiff) > 1e-6:
        ok = False

# center: half diff
_, _, _, _, ys, _, _ = run("center")
diff = ys[1] - ys[0]
print("center y offsets=", ys, "diff=", diff, "half hdiff=", hdiff/2)
if abs(diff - hdiff/2) > 1e-6:
    ok = False

sys.exit(0 if ok else 1)
```

Attack 6 — `probe_6_vpacker.py` → holds on the patched tree (good)

```python
# R4: VPacker horizontal placement of children of differing widths.
import sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.offsetbox import DrawingArea, VPacker

fig = plt.figure()
renderer = fig.canvas.get_renderer()
ok = True

def run(align):
    c1 = DrawingArea(20.0, 10, 0, 0)   # wider
    c2 = DrawingArea(8.0, 10, 0, 0)    # narrower
    p = VPacker(pad=0, sep=0, align=align, children=[c1, c2])
    w, h, xd, yd, offsets = p.get_extent_offsets(renderer)
    e1 = c1.get_extent(renderer)  # (width, height, xdescent, ydescent)
    e2 = c2.get_extent(renderer)
    xs = [ox for ox, oy in offsets]
    return w, h, xd, yd, xs, e1, e2

# R4.4 extent: total width = max width, total height = sum heights, xd=0, yd = height of last child
w, h, xd, yd, xs, e1, e2 = run("bottom")
max_w = max(e1[0], e2[0])
sum_h = e1[1] + e2[1]
print("extent w=", w, "max_w=", max_w, "h=", h, "sum_h=", sum_h, "xd=", xd, "yd=", yd, "last_h=", e2[1])
if not (abs(w - max_w) < 1e-6 and abs(h - sum_h) < 1e-6 and xd == 0):
    ok = False

wdiff = e1[0] - e2[0]  # wider - narrower

# baseline/left/bottom: narrower flush left -> diff 0
for align in ["baseline", "left", "bottom"]:
    _, _, _, _, xs, _, _ = run(align)
    diff = xs[1] - xs[0]
    print(align, "x offsets=", xs, "diff=", diff)
    if abs(diff) > 1e-9:
        ok = False

# top/right: narrower shifted by full width difference
for align in ["top", "right"]:
    _, _, _, _, xs, _, _ = run(align)
    diff = xs[1] - xs[0]
    print(align, "x offsets=", xs, "diff=", diff, "wdiff=", wdiff)
    if abs(diff - wdiff) > 1e-6:
        ok = False

# center: half diff
_, _, _, _, xs, _, _ = run("center")
diff = xs[1] - xs[0]
print("center x offsets=", xs, "diff=", diff, "half wdiff=", wdiff/2)
if abs(diff - wdiff/2) > 1e-6:
    ok = False

sys.exit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_5_hpacker.py`

```python
# R3: HPacker vertical placement of children of differing heights.
import sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.offsetbox import DrawingArea, HPacker

fig = plt.figure()
renderer = fig.canvas.get_renderer()
ok = True

def child_extent(w, h):
    return DrawingArea(w, h, 0, 0).get_extent(renderer)  # (height, descent, width_related?)

def run(align):
    c1 = DrawingArea(10, 20.0, 0, 0)   # taller
    c2 = DrawingArea(10, 8.0, 0, 0)    # shorter
    p = HPacker(pad=0, sep=0, align=align, children=[c1, c2])
    ext = p.get_extent_offsets(renderer)
    w, h, xd, yd, offsets = ext
    e1 = c1.get_extent(renderer)  # (width, height, xdescent, ydescent)
    e2 = c2.get_extent(renderer)
    ys = [oy for ox, oy in offsets]
    return w, h, xd, yd, ys, e1, e2

# R3.4 extent
w, h, xd, yd, ys, e1, e2 = run("bottom")
sum_w = e1[0] + e2[0]
max_h = max(e1[1], e2[1])
print("extent w=", w, "sum_w=", sum_w, "h=", h, "max_h=", max_h, "xd=", xd, "yd=", yd)
if not (abs(w - sum_w) < 1e-6 and abs(h - max_h) < 1e-6 and xd == 0 and yd == 0):
    ok = False

hdiff = e1[1] - e2[1]  # taller - shorter

# baseline/left/bottom: shorter flush low -> diff 0
for align in ["baseline", "left", "bottom"]:
    _, _, _, _, ys, _, _ = run(align)
    diff = ys[1] - ys[0]
    print(align, "y offsets=", ys, "diff=", diff)
    if abs(diff) > 1e-9:
        ok = False

# top/right: shorter shifted by full height difference
for align in ["top", "right"]:
    _, _, _, _, ys, _, _ = run(align)
    diff = ys[1] - ys[0]
    print(align, "y offsets=", ys, "diff=", diff, "hdiff=", hdiff)
    if abs(diff - hdiff) > 1e-6:
        ok = False

# center: half diff
_, _, _, _, ys, _, _ = run("center")
diff = ys[1] - ys[0]
print("center y offsets=", ys, "diff=", diff, "half hdiff=", hdiff/2)
if abs(diff - hdiff/2) > 1e-6:
    ok = False

sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance matplotlib__matplotlib-24570: fix corrects swapped top/bottom anchors in _get_aligned_offsets (left/bottom share offset=descent rule; right/top share offset=total-length+descent rule).

Probes (all HOLD on gold-patched tree; results verified via nl_attack probe):
- probe_1_leftbottom (R1.1): left/bottom -> descent 0, offset==box descent. patched=HOLD, base=VIOLATED.
- probe_2_righttop (R1.2): right/top -> descent 0, offset==total-length+descent. patched=HOLD, base=VIOLATED.
- probe_3_size_unchanged (R1.3): left/top/right/bottom/center return total unchanged as resolved size. patched=HOLD.
- probe_4_baseline_center (R2.1/R2.2/R2.3): baseline size/descent/zero offsets; center offset=(total-length)/2+descent; invalid align raises. patched=HOLD.
- probe_5_hpacker (R3.1-3.4, POSITIVE CONTROL): HPacker with two children of differing heights; bottom/left/baseline flush low (diff 0), top/right shifted by full height diff, center by half; extent = sum widths / max height / xd=yd=0. patched=HOLD, base=VIOLATED (confirms prepatch top/bottom swap).
- probe_6_vpacker (R4.1-4.4): VPacker with two children of differing widths; analogous horizontal placement; extent = max width / sum heights / xd=0. patched=HOLD, base=VIOLATED.

Positive control probe_5 FAILS at base (top/bottom reversed) and HOLDS on patched -> discriminating power confirmed. prepatch_reproduced=true.

Candidate wrong-fix patches (>=1 exercised, >=1 REJECTED):
- partial_bottom_only (weak.diff): a partial reading that fixes only the left/bottom branch and drops 'bottom' from the second branch entirely, so align='bottom' falls through to an error. REJECTED by probe suite: probe_2 (right/top branch now malformed / 'bottom' not handled), probe_3 (bottom raises instead of returning total), probe_5 and probe_6 (HPacker/VPacker with align='bottom' raise). Demonstrates the suite discriminates a plausible partial fix.

Verdict SOUND: 6 distinct probes covering R1-R4 (behavioral SHALLs, boundary/invalid cases, and 'SHALL keep' baseline/center + extent regression criteria) all hold on the patched tree; positive control discriminates (fails at base, holds patched); the requirements-under-reading weak candidate is rejected by the suite, so the requirements are neither too strong (no mandated behavior missing on gold) nor demonstrably too weak (the exercised alternative is caught).

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 6 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 6 | `probe_1_leftbottom.py`, `probe_2_righttop.py`, `probe_3_size_unchanged.py`, `probe_4_baseline_center.py`, `probe_5_hpacker.py`, `probe_6_vpacker.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_5_hpacker.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (6):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

_The 6 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts, and on this backend both roles put it through the same derivation: every block below is a requirement probe run on the gold-patched tree, and the `machine verdict:` line each role publishes above reports BOTH that its probes hold there and how many candidate patches the probe suite rejected — so the two roles re-ran ONE probe suite and each recorded its own outcome for every probe in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `probe_1_leftbottom.py` → holds on the patched tree (good)

Attack 2 — `probe_2_righttop.py` → holds on the patched tree (good)

Attack 3 — `probe_3_size_unchanged.py` → holds on the patched tree (good)

Attack 4 — `probe_4_baseline_center.py` → holds on the patched tree (good)

Attack 5 — `probe_5_hpacker.py` → holds on the patched tree (good)

Attack 6 — `probe_6_vpacker.py` → holds on the patched tree (good)

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_5_hpacker.py`

```python
# R3: HPacker vertical placement of children of differing heights.
import sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.offsetbox import DrawingArea, HPacker

fig = plt.figure()
renderer = fig.canvas.get_renderer()
ok = True

def child_extent(w, h):
    return DrawingArea(w, h, 0, 0).get_extent(renderer)  # (height, descent, width_related?)

def run(align):
    c1 = DrawingArea(10, 20.0, 0, 0)   # taller
    c2 = DrawingArea(10, 8.0, 0, 0)    # shorter
    p = HPacker(pad=0, sep=0, align=align, children=[c1, c2])
    ext = p.get_extent_offsets(renderer)
    w, h, xd, yd, offsets = ext
    e1 = c1.get_extent(renderer)  # (width, height, xdescent, ydescent)
    e2 = c2.get_extent(renderer)
    ys = [oy for ox, oy in offsets]
    return w, h, xd, yd, ys, e1, e2

# R3.4 extent
w, h, xd, yd, ys, e1, e2 = run("bottom")
sum_w = e1[0] + e2[0]
max_h = max(e1[1], e2[1])
print("extent w=", w, "sum_w=", sum_w, "h=", h, "max_h=", max_h, "xd=", xd, "yd=", yd)
if not (abs(w - sum_w) < 1e-6 and abs(h - max_h) < 1e-6 and xd == 0 and yd == 0):
    ok = False

hdiff = e1[1] - e2[1]  # taller - shorter

# baseline/left/bottom: shorter flush low -> diff 0
for align in ["baseline", "left", "bottom"]:
    _, _, _, _, ys, _, _ = run(align)
    diff = ys[1] - ys[0]
    print(align, "y offsets=", ys, "diff=", diff)
    if abs(diff) > 1e-9:
        ok = False

# top/right: shorter shifted by full height difference
for align in ["top", "right"]:
    _, _, _, _, ys, _, _ = run(align)
    diff = ys[1] - ys[0]
    print(align, "y offsets=", ys, "diff=", diff, "hdiff=", hdiff)
    if abs(diff - hdiff) > 1e-6:
        ok = False

# center: half diff
_, _, _, _, ys, _, _ = run("center")
diff = ys[1] - ys[0]
print("center y offsets=", ys, "diff=", diff, "half hdiff=", hdiff/2)
if abs(diff - hdiff/2) > 1e-6:
    ok = False

sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance matplotlib__matplotlib-24570: fix corrects swapped top/bottom anchors in _get_aligned_offsets (left/bottom share offset=descent rule; right/top share offset=total-length+descent rule).

Probes (all HOLD on gold-patched tree; results verified via nl_attack probe):
- probe_1_leftbottom (R1.1): left/bottom -> descent 0, offset==box descent. patched=HOLD, base=VIOLATED.
- probe_2_righttop (R1.2): right/top -> descent 0, offset==total-length+descent. patched=HOLD, base=VIOLATED.
- probe_3_size_unchanged (R1.3): left/top/right/bottom/center return total unchanged as resolved size. patched=HOLD.
- probe_4_baseline_center (R2.1/R2.2/R2.3): baseline size/descent/zero offsets; center offset=(total-length)/2+descent; invalid align raises. patched=HOLD.
- probe_5_hpacker (R3.1-3.4, POSITIVE CONTROL): HPacker with two children of differing heights; bottom/left/baseline flush low (diff 0), top/right shifted by full height diff, center by half; extent = sum widths / max height / xd=yd=0. patched=HOLD, base=VIOLATED (confirms prepatch top/bottom swap).
- probe_6_vpacker (R4.1-4.4): VPacker with two children of differing widths; analogous horizontal placement; extent = max width / sum heights / xd=0. patched=HOLD, base=VIOLATED.

Positive control probe_5 FAILS at base (top/bottom reversed) and HOLDS on patched -> discriminating power confirmed. prepatch_reproduced=true.

Candidate wrong-fix patches (>=1 exercised, >=1 REJECTED):
- partial_bottom_only (weak.diff): a partial reading that fixes only the left/bottom branch and drops 'bottom' from the second branch entirely, so align='bottom' falls through to an error. REJECTED by probe suite: probe_2 (right/top branch now malformed / 'bottom' not handled), probe_3 (bottom raises instead of returning total), probe_5 and probe_6 (HPacker/VPacker with align='bottom' raise). Demonstrates the suite discriminates a plausible partial fix.

Verdict SOUND: 6 distinct probes covering R1-R4 (behavioral SHALLs, boundary/invalid cases, and 'SHALL keep' baseline/center + extent regression criteria) all hold on the patched tree; positive control discriminates (fails at base, holds patched); the requirements-under-reading weak candidate is rejected by the suite, so the requirements are neither too strong (no mandated behavior missing on gold) nor demonstrably too weak (the exercised alternative is caught).

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Ran probes via nl_attack on the patched tree (exit 0, all asserts pass). Requirements correctly pin the changed behavior at the right modeling boundary (the align-grouping in the shared helper) and propagate it to both HPacker/VPacker as observable child offsets and extents. Baseline/center left unchanged per issue intent. No mandated-but-absent, forbidden-but-present, or invented behavior detected.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The requirements describe pre-existing, public API surface only. (1) Named entities — `_get_aligned_offsets`, `HPacker`/`VPacker.get_extent_offsets`, and the six align keywords (baseline/left/top/right/bottom/center) — are all real matplotlib API and legitimate localization; the keywords and the classes appear in the PUBLIC reproduction snippet in problem_statement. (2) The offset formulas (`total - length + descent`, `(total-length)/2 + descent`, the baseline max formula) are the helper's PRE-EXISTING code, not fix-invented identifiers; the gold patch only swaps which keyword group maps to which branch (['left','bottom'] vs ['right','top']) — and that swap IS the subject of the public bug report. (3) The case grouping (left/bottom→0, top/right→diff, center→diff/2) is the corrected behavior derivable from the gold edit and is exactly the behavior the document is meant to specify — translation, not transmission. (4) No test names/paths (test_offsetbox.py, test_packers), no parametrization ids (FAIL_TO_PASS [bottom]/[top]), no numeric test fixtures (10/20/30/60, dpi=72), and no quoted test/gold source lines appear. Requirements 3/4 use an abstract 'two zero-pad/zero-sep children of differing size' scenario — the minimal natural way to describe alignment behavior — without reproducing the test's concrete assertions. The VPacker y-descent = height of last child and the extent tuples are behavioral facts recoverable from reading offsetbox.py, not test-only knowledge. Extra breadth (baseline/center preservation, error on unknown keyword) is standard behavioral completeness, not test mirroring.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
