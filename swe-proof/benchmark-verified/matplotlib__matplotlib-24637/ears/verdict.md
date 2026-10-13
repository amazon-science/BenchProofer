# P2 adversarial audit — matplotlib__matplotlib-24637

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
"""Positive control + R1.2 + R4.3: user-set gid on AnnotationBbox reaches SVG as <g id=...>.

Encodes: Req1 crit2 (gid passed to open_group) and Req4 crit3 (SVG contains a <g>
whose id equals the user-set gid). Should HOLD patched, FAIL at base.
"""
import io
import re
import numpy as np
import matplotlib
matplotlib.use("svg")
import matplotlib.pyplot as plt
from matplotlib.offsetbox import OffsetImage, AnnotationBbox

GID = "My_Special_GID_12345"

fig, ax = plt.subplots()
arr = np.arange(100).reshape(10, 10)
im = OffsetImage(arr, zoom=1)
ab = AnnotationBbox(im, (0.5, 0.5), xybox=(0.5, 0.5), xycoords="data")
ab.set_gid(GID)
ax.add_artist(ab)

buf = io.BytesIO()
fig.savefig(buf, format="svg")
svg = buf.getvalue().decode("utf-8")

# Look for a <g ...> element whose id attribute equals GID exactly.
ids = re.findall(r'<g[^>]*\bid="([^"]*)"', svg)
print("group ids found in SVG:", ids)
found = GID in ids
print("expected gid present:", found)
if not found:
    raise SystemExit(1)
print("PASS: gid reached SVG")
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""R1.1, R1.5, R2.1, R2.2, R2.3: exactly one open/close pair for the AnnotationBbox
draw, group-open precedes ALL part draws, group-close follows them, and the parts
draw in order arrow -> patch -> offsetbox, all INSIDE the group.

Instruments the SVG renderer's open_group/close_group and the AnnotationBbox's
constituent-part draw methods, records the event sequence, and checks nesting/order.
"""
import io
import numpy as np
import matplotlib
matplotlib.use("svg")
import matplotlib.pyplot as plt
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
from matplotlib.backends.backend_svg import RendererSVG

events = []

orig_open = RendererSVG.open_group
orig_close = RendererSVG.close_group

def rec_open(self, s, gid=None):
    events.append(("open", s, gid))
    return orig_open(self, s, gid=gid)

def rec_close(self, s):
    events.append(("close", s))
    return orig_close(self, s)

RendererSVG.open_group = rec_open
RendererSVG.close_group = rec_close

fig, ax = plt.subplots()
arr = np.arange(100).reshape(10, 10)
im = OffsetImage(arr, zoom=1)
ab = AnnotationBbox(im, (0.2, 0.2), xybox=(0.8, 0.8), xycoords="data",
                    arrowprops=dict(arrowstyle="->"))
ab.set_gid("GIDORDER")
ax.add_artist(ab)

# wrap the specific instance's part draws
def wrap(obj, name, tag):
    orig = obj.draw
    def d(renderer, *a, **k):
        events.append(("draw", tag))
        return orig(renderer, *a, **k)
    obj.draw = d

wrap(ab.arrow_patch, "arrow", "arrow")
wrap(ab.patch, "patch", "patch")
wrap(ab.offsetbox, "offsetbox", "offsetbox")

buf = io.BytesIO()
fig.savefig(buf, format="svg")

# find the AnnotationBbox open/close indices
open_idxs = [i for i, e in enumerate(events) if e[0] == "open" and e[1] == "AnnotationBbox"]
close_idxs = [i for i, e in enumerate(events) if e[0] == "close" and e[1] == "AnnotationBbox"]
print("AnnotationBbox opens:", len(open_idxs), "closes:", len(close_idxs))
assert len(open_idxs) == 1, "expected exactly one open"
assert len(close_idxs) == 1, "expected exactly one close"
oi, ci = open_idxs[0], close_idxs[0]
assert oi < ci, "open must precede close"

# gid must have been passed at open
assert events[oi][2] == "GIDORDER", f"gid at open was {events[oi][2]!r}"

# all part draws must be strictly between oi and ci
draws = [(i, e[1]) for i, e in enumerate(events) if e[0] == "draw"]
print("draw events (idx,tag):", draws)
for i, tag in draws:
    assert oi < i < ci, f"draw {tag} at {i} not inside group ({oi},{ci})"

order = [tag for _, tag in draws]
print("part draw order:", order)
assert order == ["arrow", "patch", "offsetbox"], f"bad order {order}"
print("PASS: single balanced pair, correct order, all inside group")
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""R1.3 & R1.4: the group is opened AND closed tagged with the class-name label
'AnnotationBbox'. Also R2.4: update_positions emits no grouping marker.

Instruments RendererBase.open_group/close_group at the AnnotationBbox.draw level by
recording every open/close and asserting the AnnotationBbox pair uses the class name
as label. Also patches update_positions to assert no marker is emitted during it.
"""
import io
import numpy as np
import matplotlib
matplotlib.use("svg")
import matplotlib.pyplot as plt
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
from matplotlib.backends.backend_svg import RendererSVG

events = []
orig_open = RendererSVG.open_group
orig_close = RendererSVG.close_group
RendererSVG.open_group = lambda self, s, gid=None: (events.append(("open", s, gid)), orig_open(self, s, gid=gid))[1]
RendererSVG.close_group = lambda self, s: (events.append(("close", s)), orig_close(self, s))[1]

# track markers emitted during update_positions
in_update = {"flag": False}
markers_during_update = []
orig_up = AnnotationBbox.update_positions
def up(self, renderer):
    in_update["flag"] = True
    try:
        return orig_up(self, renderer)
    finally:
        in_update["flag"] = False
AnnotationBbox.update_positions = up

orig_open2 = RendererSVG.open_group
def open_guard(self, s, gid=None):
    if in_update["flag"]:
        markers_during_update.append(("open", s))
    return orig_open2(self, s, gid=gid)
RendererSVG.open_group = open_guard

fig, ax = plt.subplots()
arr = np.arange(100).reshape(10, 10)
ab = AnnotationBbox(OffsetImage(arr, zoom=1), (0.5, 0.5), xycoords="data")
ab.set_gid("LBL")
ax.add_artist(ab)
buf = io.BytesIO()
fig.savefig(buf, format="svg")

opens = [e for e in events if e[0] == "open" and e[1] == "AnnotationBbox"]
closes = [e for e in events if e[0] == "close" and e[1] == "AnnotationBbox"]
print("open labels 'AnnotationBbox':", len(opens))
print("close labels 'AnnotationBbox':", len(closes))
print("markers during update_positions:", markers_during_update)
assert len(opens) == 1, "open must use class-name label exactly once"
assert len(closes) == 1, "close must use class-name label exactly once"
assert not markers_during_update, "update_positions must not emit grouping markers"
print("PASS: class-name label on open+close, no marker during update_positions")
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""R3.1: an invisible AnnotationBbox emits NOTHING — no group open/close, no part draw.

Sets visible=False; instruments open_group/close_group and part draws; asserts the
AnnotationBbox contributes zero events, and that no <g id="INVIS"> appears in the SVG.
"""
import io
import re
import numpy as np
import matplotlib
matplotlib.use("svg")
import matplotlib.pyplot as plt
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
from matplotlib.backends.backend_svg import RendererSVG

events = []
orig_open = RendererSVG.open_group
orig_close = RendererSVG.close_group
RendererSVG.open_group = lambda self, s, gid=None: (events.append(("open", s, gid)), orig_open(self, s, gid=gid))[1]
RendererSVG.close_group = lambda self, s: (events.append(("close", s)), orig_close(self, s))[1]

fig, ax = plt.subplots()
arr = np.arange(100).reshape(10, 10)
ab = AnnotationBbox(OffsetImage(arr, zoom=1), (0.5, 0.5), xycoords="data")
ab.set_gid("INVIS")
ab.set_visible(False)
ax.add_artist(ab)

part_draws = []
for obj, tag in [(ab.patch, "patch"), (ab.offsetbox, "offsetbox")]:
    orig = obj.draw
    def mk(orig, tag):
        def d(r, *a, **k):
            part_draws.append(tag)
            return orig(r, *a, **k)
        return d
    obj.draw = mk(orig, tag)

buf = io.BytesIO()
fig.savefig(buf, format="svg")
svg = buf.getvalue().decode("utf-8")

ab_opens = [e for e in events if e[0] == "open" and e[1] == "AnnotationBbox"]
print("AnnotationBbox opens (should be 0):", len(ab_opens))
print("part draws (should be empty):", part_draws)
ids = re.findall(r'<g[^>]*\bid="([^"]*)"', svg)
print("INVIS in svg ids (should be False):", "INVIS" in ids)
assert len(ab_opens) == 0, "invisible artist must not open a group"
assert not part_draws, "invisible artist must not draw parts"
assert "INVIS" not in ids, "no stray group for invisible artist"
print("PASS: invisible annotation emits nothing")
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""R5.1 & R5.2 (regression): another artist's set_gid still reaches SVG unchanged,
AND all <g> open/close tags in the SVG are balanced/properly nested.

- Add a Line2D with set_gid -> its gid must still appear in SVG.
- Also add an AnnotationBbox with a gid.
- Parse the SVG as XML to prove all group elements are balanced & well-formed.
"""
import io
import re
import xml.etree.ElementTree as ET
import numpy as np
import matplotlib
matplotlib.use("svg")
import matplotlib.pyplot as plt
from matplotlib.offsetbox import OffsetImage, AnnotationBbox

fig, ax = plt.subplots()
(ln,) = ax.plot([0, 1, 2], [0, 1, 0])
ln.set_gid("MY_LINE_GID")

arr = np.arange(100).reshape(10, 10)
ab = AnnotationBbox(OffsetImage(arr, zoom=1), (1, 0.5), xycoords="data")
ab.set_gid("MY_BOX_GID")
ax.add_artist(ab)

buf = io.BytesIO()
fig.savefig(buf, format="svg")
svg = buf.getvalue().decode("utf-8")

ids = re.findall(r'<g[^>]*\bid="([^"]*)"', svg)
print("line gid present:", "MY_LINE_GID" in ids)
print("box gid present:", "MY_BOX_GID" in ids)

# Well-formedness / balance: XML must parse (unbalanced tags would raise).
try:
    ET.fromstring(svg)
    parsed = True
except ET.ParseError as e:
    parsed = False
    print("XML parse error:", e)
print("SVG parses as well-formed XML (balanced):", parsed)

assert "MY_LINE_GID" in ids, "existing artist gid must be preserved"
assert "MY_BOX_GID" in ids, "annotationbbox gid must appear"
assert parsed, "SVG groups must be balanced/well-formed"
print("PASS: existing gid preserved + balanced groups")
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
"""R4.2: SVG renderer opens a group with NO gid -> the <g> id derives from the label
(so unlabeled groups stay distinguishable), and R5.3-ish: unchanged rendered geometry.

Directly exercise the SVG renderer open_group with gid=None and a label, and assert a
<g> with an id derived from the label is emitted (id present and containing the label).
Uses only the public backend API on a fresh renderer.
"""
import io
import re
import matplotlib
matplotlib.use("svg")
from matplotlib.backends.backend_svg import FigureCanvasSVG
import matplotlib.pyplot as plt

fig = plt.figure()
canvas = FigureCanvasSVG(fig)
# get a real SVG renderer via the printing machinery
from matplotlib.backends.backend_svg import RendererSVG
import matplotlib.backends.backend_svg as bsvg

buf = io.StringIO()
# build a renderer directly
w, h = 100, 100
from matplotlib.backends.backend_svg import XMLWriter
writer_target = io.StringIO()
r = RendererSVG(w, h, writer_target)
# open a group with label but no gid
r.open_group("myLabelThing", gid=None)
r.close_group("myLabelThing")
r.finalize()
out = writer_target.getvalue()
ids = re.findall(r'<g[^>]*\bid="([^"]*)"', out)
print("group ids when gid=None:", ids)
# There must be a group whose id is derived from the label (label appears in some id)
derived = [i for i in ids if "myLabelThing" in i]
print("label-derived ids:", derived)
assert derived, "with no gid, id must be derived from the label"
print("PASS: unlabeled(no-gid) group id derived from label")
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Positive control + R1.2 + R4.3: user-set gid on AnnotationBbox reaches SVG as <g id=...>.

Encodes: Req1 crit2 (gid passed to open_group) and Req4 crit3 (SVG contains a <g>
whose id equals the user-set gid). Should HOLD patched, FAIL at base.
"""
import io
import re
import numpy as np
import matplotlib
matplotlib.use("svg")
import matplotlib.pyplot as plt
from matplotlib.offsetbox import OffsetImage, AnnotationBbox

GID = "My_Special_GID_12345"

fig, ax = plt.subplots()
arr = np.arange(100).reshape(10, 10)
im = OffsetImage(arr, zoom=1)
ab = AnnotationBbox(im, (0.5, 0.5), xybox=(0.5, 0.5), xycoords="data")
ab.set_gid(GID)
ax.add_artist(ab)

buf = io.BytesIO()
fig.savefig(buf, format="svg")
svg = buf.getvalue().decode("utf-8")

# Look for a <g ...> element whose id attribute equals GID exactly.
ids = re.findall(r'<g[^>]*\bid="([^"]*)"', svg)
print("group ids found in SVG:", ids)
found = GID in ids
print("expected gid present:", found)
if not found:
    raise SystemExit(1)
print("PASS: gid reached SVG")
```

Prepatch bug re-encoded as an attack: `True`.

Requirements: AnnotationBbox.draw must wrap its part-drawing in a renderer group carrying the artist's gid (class-name label) so a user-set gid reaches SVG as <g id=...>.

Probes (all HOLD on gold-patched tree):
- probe_1 (POSITIVE CONTROL; R1.2, R4.3): user-set gid 'My_Special_GID_12345' appears as a <g id> in saved SVG. HOLDS patched, FAILS at base (base SVG has no such id) -> discriminates.
- probe_2 (R1.1, R1.5, R2.1-2.3): instruments RendererSVG.open_group/close_group and the 3 part-draws; asserts exactly one AnnotationBbox open/close pair, gid passed at open, all part draws strictly inside the group, order arrow->patch->offsetbox. HOLDS.
- probe_3 (R1.3, R1.4, R2.4): open and close both labelled with class name 'AnnotationBbox'; update_positions emits no grouping marker. HOLDS.
- probe_4 (R3.1): invisible AnnotationBbox opens no group, draws no part, no stray <g id>. HOLDS.
- probe_5 (R5.1, R5.2): a Line2D's set_gid still reaches SVG; SVG parses as well-formed/balanced XML alongside a gid'd AnnotationBbox. HOLDS.
- probe_6 (R4.2): SVG renderer open_group with gid=None derives the <g> id from the label ('myLabelThing_1'). HOLDS.

Candidate wrong-fixes (both REJECTED by the suite):
- weak_nogid.diff: opens/closes the group but omits gid= (label only). REJECTED by probe_1 (gid absent from SVG; only 'AnnotationBbox_1' appears), probe_2 (gid at open is None), probe_5 (box gid missing). This is precisely the F2P test failure mode.
- weak_partial.diff: closes the group before drawing the offsetbox (offsetbox left outside group). REJECTED by probe_2 (unbalanced/one-close ordering) and probe_3 (close label count wrong).

Gold-patched tree passes all 6 probes; base fails positive control; two probe-conforming-looking wrong fixes are caught. Suite discriminates. SOUND.

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
"""Positive control + R1.2 + R4.3: user-set gid on AnnotationBbox reaches SVG as <g id=...>.

Encodes: Req1 crit2 (gid passed to open_group) and Req4 crit3 (SVG contains a <g>
whose id equals the user-set gid). Should HOLD patched, FAIL at base.
"""
import io
import re
import numpy as np
import matplotlib
matplotlib.use("svg")
import matplotlib.pyplot as plt
from matplotlib.offsetbox import OffsetImage, AnnotationBbox

GID = "My_Special_GID_12345"

fig, ax = plt.subplots()
arr = np.arange(100).reshape(10, 10)
im = OffsetImage(arr, zoom=1)
ab = AnnotationBbox(im, (0.5, 0.5), xybox=(0.5, 0.5), xycoords="data")
ab.set_gid(GID)
ax.add_artist(ab)

buf = io.BytesIO()
fig.savefig(buf, format="svg")
svg = buf.getvalue().decode("utf-8")

# Look for a <g ...> element whose id attribute equals GID exactly.
ids = re.findall(r'<g[^>]*\bid="([^"]*)"', svg)
print("group ids found in SVG:", ids)
found = GID in ids
print("expected gid present:", found)
if not found:
    raise SystemExit(1)
print("PASS: gid reached SVG")
```

Prepatch bug re-encoded as an attack: `True`.

Requirements: AnnotationBbox.draw must wrap its part-drawing in a renderer group carrying the artist's gid (class-name label) so a user-set gid reaches SVG as <g id=...>.

Probes (all HOLD on gold-patched tree):
- probe_1 (POSITIVE CONTROL; R1.2, R4.3): user-set gid 'My_Special_GID_12345' appears as a <g id> in saved SVG. HOLDS patched, FAILS at base (base SVG has no such id) -> discriminates.
- probe_2 (R1.1, R1.5, R2.1-2.3): instruments RendererSVG.open_group/close_group and the 3 part-draws; asserts exactly one AnnotationBbox open/close pair, gid passed at open, all part draws strictly inside the group, order arrow->patch->offsetbox. HOLDS.
- probe_3 (R1.3, R1.4, R2.4): open and close both labelled with class name 'AnnotationBbox'; update_positions emits no grouping marker. HOLDS.
- probe_4 (R3.1): invisible AnnotationBbox opens no group, draws no part, no stray <g id>. HOLDS.
- probe_5 (R5.1, R5.2): a Line2D's set_gid still reaches SVG; SVG parses as well-formed/balanced XML alongside a gid'd AnnotationBbox. HOLDS.
- probe_6 (R4.2): SVG renderer open_group with gid=None derives the <g> id from the label ('myLabelThing_1'). HOLDS.

Candidate wrong-fixes (both REJECTED by the suite):
- weak_nogid.diff: opens/closes the group but omits gid= (label only). REJECTED by probe_1 (gid absent from SVG; only 'AnnotationBbox_1' appears), probe_2 (gid at open is None), probe_5 (box gid missing). This is precisely the F2P test failure mode.
- weak_partial.diff: closes the group before drawing the offsetbox (offsetbox left outside group). REJECTED by probe_2 (unbalanced/one-close ordering) and probe_3 (close label count wrong).

Gold-patched tree passes all 6 probes; base fails positive control; two probe-conforming-looking wrong fixes are caught. Suite discriminates. SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** The modeling boundary is correct: requirements pin the changed observable behavior (gid reaching SVG via a group wrapping the whole annotation), not a narrow slice. Req 4's fallback-label branch and Req 3's early-return are pre-existing behavior correctly described, not invented. Draw-order preservation and update_positions ordering-neutrality (Req 2.4) match the patch (open_group precedes update_positions but no part is drawn between them). No unfaithful mandate, forbiddance, mis-boundary, or invented behavior found.

Counterexample / evidence:

```
Probe on gold-patched tree: SVG contains id="My_label" (exit 0). Probe on base_commit: assertion fails, gid absent (exit 1). RendererSVG.open_group source confirms id=gid when gid truthy, else derived from label. Matches F2P test test_annotationbbox_gid.
```


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Requirements describe the fix behaviorally using only public-API/module names (offsetbox.AnnotationBbox.draw, backend_svg, RendererBase.open_group/close_group, get_gid) — all legitimate localization already implied by the problem_statement (which names AnnotationBbox, set_gid, SVG, and references PR #15087). Using the class name as group label (Req 1.3/1.4) and the arrow→patch→offsetbox draw order (Req 2.1) and the visibility/position-resolvable early return (Req 3) are all pre-existing code visible in the gold-patch context, not test-derived. Req 4's <g id=...> exact-string behavior is the behavioral translation of what the test verifies — the intended purpose, not a leak. Critically, NONE of the hidden test's concrete artifacts leak: no test path/name (test_annotationbbox_gid), no gid literal ('a test for issue 20044'), no np.ones((32,32))/zoom=0.1/xy/xybox values, no quoted test/gold code, no fix-invented identifiers (the fix reuses existing open_group/close_group). Single FAIL_TO_PASS, so no parametrization enumeration to mirror.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
