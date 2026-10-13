# P2 adversarial audit — matplotlib__matplotlib-23412

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
# Positive control: Req1.1 + Req1.4 — Patch.draw applies the stored (scaled)
# dash OFFSET to the renderer's gc, rather than substituting 0.
# HOLDS patched, FAILS at base (base forces offset 0).
import sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.lines as mlines
from matplotlib.patches import Rectangle


def record_dashes(patch):
    fig = plt.figure()
    ax = fig.add_subplot()
    ax.add_patch(patch)
    renderer = fig.canvas.get_renderer()
    RCls = type(renderer)
    orig = RCls.draw_path
    recs = []

    def spy(self, gc, path, transform, rgbFace=None):
        recs.append(gc.get_dashes())
        return orig(self, gc, path, transform, rgbFace)

    RCls.draw_path = spy
    try:
        patch.draw(renderer)
    finally:
        RCls.draw_path = orig
    plt.close(fig)
    return recs


lw = 3
rect = Rectangle((0.1, 0.1), 0.8, 0.8, linewidth=lw, edgecolor='b',
                 linestyle=(6, [6, 6]))

# expected scaled offset
off, seq = mlines._get_dash_pattern((6, [6, 6]))
soff, sseq = mlines._scale_dashes(off, seq, lw)
print("expected scaled offset:", soff, "seq:", sseq)

recs = record_dashes(rect)
print("gc dashes observed at draw_path:", recs)
if not recs:
    print("FAIL: no draw_path calls")
    sys.exit(1)

# main edge draw is the (only) call here (no gapcolor)
observed_offset, observed_seq = recs[-1]
print("observed offset:", observed_offset, "seq:", observed_seq)

if observed_offset is None:
    print("FAIL: offset is None (no dashes applied)")
    sys.exit(1)
if abs(observed_offset - soff) > 1e-9:
    print("FAIL: applied offset %r != stored scaled offset %r" % (observed_offset, soff))
    sys.exit(1)
if soff == 0:
    print("FAIL: test misconfigured, scaled offset is 0")
    sys.exit(1)
print("PASS: stored non-zero scaled offset applied to renderer")
sys.exit(0)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
# Req1.2 — Patch.draw applies the stored on/off dash SEQUENCE (2nd element of
# the scaled pattern) to the renderer UNCHANGED.
import sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.lines as mlines
from matplotlib.patches import Rectangle


def record_dashes(patch):
    fig = plt.figure()
    ax = fig.add_subplot()
    ax.add_patch(patch)
    renderer = fig.canvas.get_renderer()
    RCls = type(renderer)
    orig = RCls.draw_path
    recs = []

    def spy(self, gc, path, transform, rgbFace=None):
        recs.append(gc.get_dashes())
        return orig(self, gc, path, transform, rgbFace)

    RCls.draw_path = spy
    try:
        patch.draw(renderer)
    finally:
        RCls.draw_path = orig
    plt.close(fig)
    return recs


lw = 2
rect = Rectangle((0.1, 0.1), 0.8, 0.8, linewidth=lw, edgecolor='g',
                 linestyle=(3, [4, 2, 1, 2]))
off, seq = mlines._get_dash_pattern((3, [4, 2, 1, 2]))
soff, sseq = mlines._scale_dashes(off, seq, lw)
print("expected scaled seq:", sseq)

recs = record_dashes(rect)
print("observed:", recs)
if not recs:
    print("FAIL: no draw calls")
    sys.exit(1)
obs_off, obs_seq = recs[-1]
if list(obs_seq) != list(sseq):
    print("FAIL: seq %r != expected %r" % (obs_seq, sseq))
    sys.exit(1)
print("PASS: on/off sequence applied unchanged (scaled)")
sys.exit(0)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
# Req1.3 — Two patches identical except dash OFFSET must NOT be forced to render
# identical dashes. The equivalence from the gold test: rect(6,[6,6]) vs the
# workaround rect(0,[0,6,6,0]) should draw the SAME dashes; while rect(0,[6,6])
# and rect(6,[6,6]) must DIFFER in phase.
import sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle


def record_dashes(patch):
    fig = plt.figure()
    ax = fig.add_subplot()
    ax.add_patch(patch)
    renderer = fig.canvas.get_renderer()
    RCls = type(renderer)
    orig = RCls.draw_path
    recs = []

    def spy(self, gc, path, transform, rgbFace=None):
        recs.append(gc.get_dashes())
        return orig(self, gc, path, transform, rgbFace)

    RCls.draw_path = spy
    try:
        patch.draw(renderer)
    finally:
        RCls.draw_path = orig
    plt.close(fig)
    return recs[-1]


def mk(ls):
    return Rectangle((0.1, 0.1), 0.8, 0.8, linewidth=3, edgecolor='b',
                     linestyle=ls)


d0 = record_dashes(mk((0, [6, 6])))
d6 = record_dashes(mk((6, [6, 6])))
print("offset0 gc dashes:", d0)
print("offset6 gc dashes:", d6)

# must differ in offset (phase)
if d0[0] == d6[0]:
    print("FAIL: offsets forced identical (%r == %r)" % (d0[0], d6[0]))
    sys.exit(1)
print("PASS: differing dash offset yields differing rendered phase")
sys.exit(0)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
# Req1.4 — Patch dash offset shifts phase in the SAME manner as Line2D.
# Capture the gc dashes a Line2D applies for the same (offset,onoffseq) and lw,
# and require the Patch to apply the same offset+seq.
import sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib.lines import Line2D


def capture(artist, is_patch):
    fig = plt.figure()
    ax = fig.add_subplot()
    if is_patch:
        ax.add_patch(artist)
    else:
        ax.add_line(artist)
    renderer = fig.canvas.get_renderer()
    RCls = type(renderer)
    orig = RCls.draw_path
    recs = []

    def spy(self, gc, path, transform, rgbFace=None):
        recs.append(gc.get_dashes())
        return orig(self, gc, path, transform, rgbFace)

    RCls.draw_path = spy
    try:
        artist.draw(renderer)
    finally:
        RCls.draw_path = orig
    plt.close(fig)
    return recs


ls = (5, [8, 4])
lw = 3
rect = Rectangle((0.1, 0.1), 0.8, 0.8, linewidth=lw, edgecolor='b', linestyle=ls)
line = Line2D([0.1, 0.9], [0.1, 0.9], linewidth=lw, color='b', linestyle=ls)

prec = capture(rect, True)
lrec = capture(line, False)
print("patch gc dashes:", prec)
print("line  gc dashes:", lrec)
if not prec or not lrec:
    print("FAIL: missing draw calls")
    sys.exit(1)
po, ps = prec[-1]
lo, lsq = lrec[-1]
if po is None or lo is None:
    print("FAIL: None offset")
    sys.exit(1)
if abs(po - lo) > 1e-9:
    print("FAIL: patch offset %r != line offset %r" % (po, lo))
    sys.exit(1)
if list(ps) != list(lsq):
    print("FAIL: seq mismatch patch %r vs line %r" % (ps, lsq))
    sys.exit(1)
print("PASS: patch applies same offset+seq as Line2D")
sys.exit(0)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
# Req1.5 — invisible patch draws nothing (draw returns early).
# Req2.1/2.2 — get_linestyle returns the set (offset, onoffseq) unchanged,
# preserving non-zero and zero offsets.
import sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

ok = True

# --- Req1.5: invisible patch draws nothing ---
rect = Rectangle((0.1, 0.1), 0.8, 0.8, linewidth=3, edgecolor='b',
                 linestyle=(6, [6, 6]))
rect.set_visible(False)
fig = plt.figure(); ax = fig.add_subplot(); ax.add_patch(rect)
renderer = fig.canvas.get_renderer()
RCls = type(renderer); orig = RCls.draw_path
calls = []
def spy(self, gc, path, transform, rgbFace=None):
    calls.append(1); return orig(self, gc, path, transform, rgbFace)
RCls.draw_path = spy
try:
    rect.draw(renderer)
finally:
    RCls.draw_path = orig
plt.close(fig)
print("invisible draw_path calls:", len(calls))
if calls:
    print("FAIL: invisible patch drew"); ok = False

# --- Req2.1/2.2: get_linestyle round-trips ---
for ls in [(6, [6, 6]), (0, [6, 6]), (0, [0, 6, 6, 0])]:
    r = Rectangle((0, 0), 1, 1, linestyle=ls)
    got = r.get_linestyle()
    print("set", ls, "-> get", got)
    if got != ls:
        print("FAIL: get_linestyle %r != set %r" % (got, ls)); ok = False

if ok:
    print("PASS")
    sys.exit(0)
sys.exit(1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
# Req3.1 — Patch.draw keeps the PDF/SVG workaround: a fully transparent
# facecolor is passed to draw_path as None (so hatches still draw), while a
# non-transparent facecolor is passed as its rgba tuple.
import sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle


def capture_rgbface(patch):
    fig = plt.figure(); ax = fig.add_subplot(); ax.add_patch(patch)
    renderer = fig.canvas.get_renderer()
    RCls = type(renderer); orig = RCls.draw_path
    faces = []
    def spy(self, gc, path, transform, rgbFace=None):
        faces.append(rgbFace); return orig(self, gc, path, transform, rgbFace)
    RCls.draw_path = spy
    try:
        patch.draw(renderer)
    finally:
        RCls.draw_path = orig
    plt.close(fig)
    return faces


# fully transparent facecolor -> None
r_transp = Rectangle((0.1, 0.1), 0.8, 0.8, facecolor=(0.2, 0.3, 0.4, 0.0),
                     edgecolor='b')
f1 = capture_rgbface(r_transp)
print("transparent face rgbFace:", f1)
if not f1 or f1[-1] is not None:
    print("FAIL: transparent facecolor not passed as None")
    sys.exit(1)

# opaque facecolor -> rgba tuple, not None
r_opaque = Rectangle((0.1, 0.1), 0.8, 0.8, facecolor=(0.2, 0.3, 0.4, 1.0),
                     edgecolor='b')
f2 = capture_rgbface(r_opaque)
print("opaque face rgbFace:", f2)
if not f2 or f2[-1] is None:
    print("FAIL: opaque facecolor became None")
    sys.exit(1)

print("PASS: PDF/SVG transparent-facecolor->None workaround preserved")
sys.exit(0)
```

Attack 7 — `probe_7.py` → holds on the patched tree (good)

```python
# Req3.3/3.2 — defaults preserved (linestyle 'solid', capstyle 'butt',
# joinstyle 'miter', antialiased True) and named/custom/accent linestyles
# still accepted; and Req2.3 — scaled dash pattern equals _scale_dashes of the
# unscaled pattern (offset scaled by linewidth, not zeroed).
import sys
import matplotlib
matplotlib.use("Agg")
import matplotlib as mpl
import matplotlib.lines as mlines
from matplotlib.patches import Rectangle

ok = True
r = Rectangle((0, 0), 1, 1)
print("default linestyle:", r.get_linestyle())
if r.get_linestyle() != 'solid':
    print("FAIL default linestyle"); ok = False
print("default capstyle:", r.get_capstyle())
if r.get_capstyle() != 'butt':
    print("FAIL default capstyle"); ok = False
print("default joinstyle:", r.get_joinstyle())
if r.get_joinstyle() != 'miter':
    print("FAIL default joinstyle"); ok = False
print("default antialiased:", r.get_antialiased())
if r.get_antialiased() != mpl.rcParams['patch.antialiased']:
    print("FAIL default antialiased"); ok = False

# named / accent aliases accepted
for ls in ['dashed', 'dashdot', '--', '-.', ':', 'solid', 'None']:
    try:
        Rectangle((0, 0), 1, 1, linestyle=ls)
    except Exception as e:
        print("FAIL accepting linestyle %r: %r" % (ls, e)); ok = False

# custom on/off accepted
Rectangle((0, 0), 1, 1, linestyle=(0, (5, 3)))

# Req2.3 scaled pattern integrity
lw = 4
r2 = Rectangle((0, 0), 1, 1, linewidth=lw, linestyle=(6, [6, 6]))
off, seq = mlines._get_dash_pattern((6, [6, 6]))
exp = mlines._scale_dashes(off, seq, lw)
print("stored _dash_pattern:", r2._dash_pattern, "expected:", exp)
if tuple(r2._dash_pattern[1]) != tuple(exp[1]) or r2._dash_pattern[0] != exp[0]:
    print("FAIL scaled dash pattern mismatch"); ok = False

if ok:
    print("PASS"); sys.exit(0)
sys.exit(1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
# Positive control: Req1.1 + Req1.4 — Patch.draw applies the stored (scaled)
# dash OFFSET to the renderer's gc, rather than substituting 0.
# HOLDS patched, FAILS at base (base forces offset 0).
import sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.lines as mlines
from matplotlib.patches import Rectangle


def record_dashes(patch):
    fig = plt.figure()
    ax = fig.add_subplot()
    ax.add_patch(patch)
    renderer = fig.canvas.get_renderer()
    RCls = type(renderer)
    orig = RCls.draw_path
    recs = []

    def spy(self, gc, path, transform, rgbFace=None):
        recs.append(gc.get_dashes())
        return orig(self, gc, path, transform, rgbFace)

    RCls.draw_path = spy
    try:
        patch.draw(renderer)
    finally:
        RCls.draw_path = orig
    plt.close(fig)
    return recs


lw = 3
rect = Rectangle((0.1, 0.1), 0.8, 0.8, linewidth=lw, edgecolor='b',
                 linestyle=(6, [6, 6]))

# expected scaled offset
off, seq = mlines._get_dash_pattern((6, [6, 6]))
soff, sseq = mlines._scale_dashes(off, seq, lw)
print("expected scaled offset:", soff, "seq:", sseq)

recs = record_dashes(rect)
print("gc dashes observed at draw_path:", recs)
if not recs:
    print("FAIL: no draw_path calls")
    sys.exit(1)

# main edge draw is the (only) call here (no gapcolor)
observed_offset, observed_seq = recs[-1]
print("observed offset:", observed_offset, "seq:", observed_seq)

if observed_offset is None:
    print("FAIL: offset is None (no dashes applied)")
    sys.exit(1)
if abs(observed_offset - soff) > 1e-9:
    print("FAIL: applied offset %r != stored scaled offset %r" % (observed_offset, soff))
    sys.exit(1)
if soff == 0:
    print("FAIL: test misconfigured, scaled offset is 0")
    sys.exit(1)
print("PASS: stored non-zero scaled offset applied to renderer")
sys.exit(0)
```

Prepatch bug re-encoded as an attack: `True`.

Instance matplotlib-23412: Patch.draw must honor the stored dash OFFSET instead of forcing 0. Gold patch replaces `_dash_pattern=(0, self._dash_pattern[1])` with the full stored `_dash_pattern`.

7 probes, all HOLD on the gold-patched tree, each capturing the actual (offset,seq) carried by the renderer gc at every draw_path call by monkeypatching RendererAgg.draw_path:
- probe_1 (Req1.1/1.4, POSITIVE CONTROL): Rectangle ls=(6,[6,6]), lw=3 -> gc offset must equal the SCALED offset 18 (=6*3). HOLDS patched (offset 18), FAILS at base (offset 0, the traditional-ignore behavior). Discriminates.
- probe_2 (Req1.2): on/off sequence applied unchanged (scaled) -> [8,4,2,4] for ls=(3,[4,2,1,2]),lw=2.
- probe_3 (Req1.3): offset0 vs offset6 rectangles produce DIFFERING gc offsets (0 vs 18), not forced identical.
- probe_4 (Req1.4): patch applies the SAME scaled offset+seq as a Line2D with the same linestyle/linewidth (both 15,[24,12]).
- probe_5 (Req1.5/2.1/2.2): invisible patch draws nothing; get_linestyle round-trips (6,[6,6]),(0,[6,6]),(0,[0,6,6,0]).
- probe_6 (Req3.1): fully-transparent facecolor passed to draw_path as None (hatch workaround), opaque passed as rgba.
- probe_7 (Req2.3/3.2/3.3): defaults solid/butt/miter/AA preserved; named+accent+custom linestyles accepted; stored _dash_pattern == _scale_dashes(unscaled, lw).

WRONG-FIX CANDIDATE (weak_unscaled.diff): applies the UNSCALED offset (self._unscaled_dash_pattern[0]) with the scaled seq — a natural but wrong reading. REJECTED by probe_1 (offset 6 != scaled 18) and probe_4 (patch offset 5 != Line2D offset 15). This confirms the suite discriminates the exact scaling requirement that Req1.1/1.4 mandate (the gold test uses the (6,[6,6]) vs (0,[0,6,6,0]) equivalence which only holds with the SCALED offset). Probes 2,3,5,6,7 still passed under it, correctly, since those criteria are unaffected.

All runs completed cleanly via the official runner on the patched, base, and candidate trees. No violation found; alternative patch does not conform to the probe suite.

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
# Positive control: Req1.1 + Req1.4 — Patch.draw applies the stored (scaled)
# dash OFFSET to the renderer's gc, rather than substituting 0.
# HOLDS patched, FAILS at base (base forces offset 0).
import sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.lines as mlines
from matplotlib.patches import Rectangle


def record_dashes(patch):
    fig = plt.figure()
    ax = fig.add_subplot()
    ax.add_patch(patch)
    renderer = fig.canvas.get_renderer()
    RCls = type(renderer)
    orig = RCls.draw_path
    recs = []

    def spy(self, gc, path, transform, rgbFace=None):
        recs.append(gc.get_dashes())
        return orig(self, gc, path, transform, rgbFace)

    RCls.draw_path = spy
    try:
        patch.draw(renderer)
    finally:
        RCls.draw_path = orig
    plt.close(fig)
    return recs


lw = 3
rect = Rectangle((0.1, 0.1), 0.8, 0.8, linewidth=lw, edgecolor='b',
                 linestyle=(6, [6, 6]))

# expected scaled offset
off, seq = mlines._get_dash_pattern((6, [6, 6]))
soff, sseq = mlines._scale_dashes(off, seq, lw)
print("expected scaled offset:", soff, "seq:", sseq)

recs = record_dashes(rect)
print("gc dashes observed at draw_path:", recs)
if not recs:
    print("FAIL: no draw_path calls")
    sys.exit(1)

# main edge draw is the (only) call here (no gapcolor)
observed_offset, observed_seq = recs[-1]
print("observed offset:", observed_offset, "seq:", observed_seq)

if observed_offset is None:
    print("FAIL: offset is None (no dashes applied)")
    sys.exit(1)
if abs(observed_offset - soff) > 1e-9:
    print("FAIL: applied offset %r != stored scaled offset %r" % (observed_offset, soff))
    sys.exit(1)
if soff == 0:
    print("FAIL: test misconfigured, scaled offset is 0")
    sys.exit(1)
print("PASS: stored non-zero scaled offset applied to renderer")
sys.exit(0)
```

Prepatch bug re-encoded as an attack: `True`.

Instance matplotlib-23412: Patch.draw must honor the stored dash OFFSET instead of forcing 0. Gold patch replaces `_dash_pattern=(0, self._dash_pattern[1])` with the full stored `_dash_pattern`.

7 probes, all HOLD on the gold-patched tree, each capturing the actual (offset,seq) carried by the renderer gc at every draw_path call by monkeypatching RendererAgg.draw_path:
- probe_1 (Req1.1/1.4, POSITIVE CONTROL): Rectangle ls=(6,[6,6]), lw=3 -> gc offset must equal the SCALED offset 18 (=6*3). HOLDS patched (offset 18), FAILS at base (offset 0, the traditional-ignore behavior). Discriminates.
- probe_2 (Req1.2): on/off sequence applied unchanged (scaled) -> [8,4,2,4] for ls=(3,[4,2,1,2]),lw=2.
- probe_3 (Req1.3): offset0 vs offset6 rectangles produce DIFFERING gc offsets (0 vs 18), not forced identical.
- probe_4 (Req1.4): patch applies the SAME scaled offset+seq as a Line2D with the same linestyle/linewidth (both 15,[24,12]).
- probe_5 (Req1.5/2.1/2.2): invisible patch draws nothing; get_linestyle round-trips (6,[6,6]),(0,[6,6]),(0,[0,6,6,0]).
- probe_6 (Req3.1): fully-transparent facecolor passed to draw_path as None (hatch workaround), opaque passed as rgba.
- probe_7 (Req2.3/3.2/3.3): defaults solid/butt/miter/AA preserved; named+accent+custom linestyles accepted; stored _dash_pattern == _scale_dashes(unscaled, lw).

WRONG-FIX CANDIDATE (weak_unscaled.diff): applies the UNSCALED offset (self._unscaled_dash_pattern[0]) with the scaled seq — a natural but wrong reading. REJECTED by probe_1 (offset 6 != scaled 18) and probe_4 (patch offset 5 != Line2D offset 15). This confirms the suite discriminates the exact scaling requirement that Req1.1/1.4 mandate (the gold test uses the (6,[6,6]) vs (0,[0,6,6,0]) equivalence which only holds with the SCALED offset). Probes 2,3,5,6,7 still passed under it, correctly, since those criteria are unaffected.

All runs completed cleanly via the official runner on the patched, base, and candidate trees. No violation found; alternative patch does not conform to the probe suite.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Probe (patched): r0 dashes [(0.0,[40.0,40.0])], r10 dashes [(40.0,[40.0,40.0])], get_linestyle preserved -> PASS. Base: r10 offset stays 0 -> AssertionError, confirming the discriminating behavior. Requirement 1.1's phrase 'first element of its scaled dash pattern' correctly identifies self._dash_pattern (the linewidth-scaled pattern, offset 40.0=10*scale), matching the code. Requirements pin the changed observable behavior (dash offset reaching the renderer), not a narrow slice.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The hidden FAIL_TO_PASS test (test_dash_offset_patch_draw) has a distinctive design: it proves linestyle (6,[6,6]) renders identically to (0,[0,6,6,0]) via check_figures_equal, with specific geometry/colors. NONE of that distinctive content (the equivalence trick, the shifted onoff-sequence construction, check_figures_equal, test name/path, the concrete dimensions) appears in requirements.md. R1.3/R1.4 (two offsets differ in dash phase; Line2D-analogous phase shift) derive directly from the PUBLIC problem_statement, which already shows offsets 0 vs 10 and the Line2D expected-outcome comparison. The gold edit (removing the forced-zero dashoffset in Patch.draw) is described behaviorally in R1.1/R3.1 by naming the module/function only — legitimate localization, no quoted gold lines or fix-invented identifiers. Requirement 3's regression enumeration (default capstyle/joinstyle/antialiasing, string repr, containment, hatching, alpha, accent aliases) loosely tracks the PASS_TO_PASS suite, but those are the repo's PRE-EXISTING PUBLIC tests, not the hidden gold test, and the list reads as generic 'preserve existing behavior' rather than reconstructing the new hidden test's parametrization. No semantic leak beyond the problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
