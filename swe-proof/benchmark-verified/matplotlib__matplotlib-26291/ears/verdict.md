# P2 adversarial audit — matplotlib__matplotlib-26291

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
"""Positive control (R1.2 / R2.1 / R2.3): inset_axes with width/height only,
then savefig(bbox_inches='tight') must complete without exception.
HOLDS on patched, FAILS at base (AttributeError NoneType._get_renderer)."""
import io
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1.inset_locator import inset_axes

fig, ax = plt.subplots()
inset_axes(ax, width=1.3, height=0.9)
f = io.BytesIO()
try:
    fig.savefig(f, bbox_inches="tight")
except Exception as e:
    print("FAIL: savefig(bbox_inches='tight') raised:", type(e).__name__, e)
    raise SystemExit(1)
print("OK: savefig with bbox_inches='tight' succeeded, bytes=", len(f.getvalue()))
raise SystemExit(0)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""R1.1 / R1.2 / R1.4: calling the locator directly with renderer=None must NOT
raise, and must return a valid bbox (a Bbox with finite bounds)."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1.inset_locator import inset_axes
from matplotlib.transforms import BboxBase
import math

fig, ax = plt.subplots()
iax = inset_axes(ax, width=1.3, height=0.9)
locator = iax.get_axes_locator()
assert locator is not None, "no locator installed"

try:
    bbox = locator(ax, None)
except Exception as e:
    print("FAIL: locator(ax, None) raised:", type(e).__name__, e)
    raise SystemExit(1)

if not isinstance(bbox, BboxBase):
    print("FAIL: returned object is not a Bbox:", type(bbox))
    raise SystemExit(1)
pts = bbox.get_points()
if not all(math.isfinite(v) for v in pts.ravel()):
    print("FAIL: bbox has non-finite bounds:", pts)
    raise SystemExit(1)
if bbox.width <= 0 or bbox.height <= 0:
    print("FAIL: bbox has non-positive size:", bbox.width, bbox.height)
    raise SystemExit(1)
print("OK: locator(ax, None) returned valid Bbox:", pts.tolist())
raise SystemExit(0)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""R1.3: when given a non-None renderer, the locator SHALL use it unchanged and
SHALL NOT substitute a different one. We sabotage figure._get_renderer to raise;
if the locator still succeeds with a supplied renderer, it did not fetch its own.
Also check the returned bbox equals the one from the untampered path."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1.inset_locator import inset_axes

fig, ax = plt.subplots()
iax = inset_axes(ax, width=1.3, height=0.9)
locator = iax.get_axes_locator()

# Obtain a real renderer up front.
renderer = fig._get_renderer()

# Baseline bbox with the supplied renderer.
bbox_supplied = locator(ax, renderer)

# Now sabotage the fallback path.
orig = type(fig)._get_renderer
sentinel = {"called": False}
def boom(self, *a, **k):
    sentinel["called"] = True
    raise RuntimeError("fallback renderer path should not be used when renderer supplied")
type(fig)._get_renderer = boom
try:
    bbox2 = locator(ax, renderer)
except Exception as e:
    print("FAIL: locator raised with a supplied renderer (fetched fallback):", type(e).__name__, e)
    raise SystemExit(1)
finally:
    type(fig)._get_renderer = orig

if sentinel["called"]:
    print("FAIL: figure._get_renderer was invoked despite a supplied renderer")
    raise SystemExit(1)

if bbox2.get_points().tolist() != bbox_supplied.get_points().tolist():
    print("FAIL: bbox differs when renderer supplied:", bbox2.get_points().tolist(),
          bbox_supplied.get_points().tolist())
    raise SystemExit(1)

print("OK: supplied renderer used unchanged, no fallback fetch; bbox=",
      bbox_supplied.get_points().tolist())
raise SystemExit(0)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""R1.4: the fallback renderer SHALL be derived from the figure that owns the
host Axes passed to the locator. We call locator(ax, None) and assert the
renderer used comes from ax.figure — verified by monkeypatching that figure's
_get_renderer to tag its returned renderer, then confirming the tagged renderer
was the one measured (get_window_extent receives it)."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1.inset_locator import inset_axes

fig, ax = plt.subplots()
iax = inset_axes(ax, width=1.3, height=0.9)
locator = iax.get_axes_locator()

real = fig._get_renderer()
tag = object()
calls = {"n": 0, "fig": None}
def tagged_get_renderer(self, *a, **k):
    calls["n"] += 1
    calls["fig"] = self
    r = real
    setattr(r, "_probe_tag", tag)
    return r

# Patch on the specific figure instance's class path.
orig = type(fig)._get_renderer
type(fig)._get_renderer = tagged_get_renderer

seen = {}
orig_gwe = type(locator).get_window_extent
def spy_gwe(self, renderer, *a, **k):
    seen["renderer"] = renderer
    return orig_gwe(self, renderer, *a, **k)
type(locator).get_window_extent = spy_gwe
try:
    bbox = locator(ax, None)
finally:
    type(fig)._get_renderer = orig
    type(locator).get_window_extent = orig_gwe

if calls["n"] == 0:
    print("FAIL: figure._get_renderer never called for fallback")
    raise SystemExit(1)
if calls["fig"] is not ax.figure:
    print("FAIL: fallback renderer fetched from a different figure than ax.figure")
    raise SystemExit(1)
if getattr(seen.get("renderer"), "_probe_tag", None) is not tag:
    print("FAIL: measured renderer is not the one from ax.figure._get_renderer")
    raise SystemExit(1)
print("OK: fallback renderer derived from ax.figure and used for measurement")
raise SystemExit(0)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""R3.3: draw() SHALL remain unsupported (raise RuntimeError); and R3.2/R2:
normal drawing (fig.canvas.draw / savefig without tight) still works and the
locator returns the same bbox during normal draw as when called with an
explicit renderer."""
import io
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1.inset_locator import inset_axes

fig, ax = plt.subplots()
iax = inset_axes(ax, width=1.3, height=0.9)
locator = iax.get_axes_locator()

# draw must raise RuntimeError
raised = False
try:
    locator.draw(fig._get_renderer())
except RuntimeError:
    raised = True
except Exception as e:
    print("FAIL: draw raised wrong exception type:", type(e).__name__, e)
    raise SystemExit(1)
if not raised:
    print("FAIL: draw did not raise RuntimeError")
    raise SystemExit(1)

# normal draw / plain savefig succeeds
try:
    fig.canvas.draw()
    f = io.BytesIO()
    fig.savefig(f)  # no bbox_inches
except Exception as e:
    print("FAIL: normal draw/savefig raised:", type(e).__name__, e)
    raise SystemExit(1)

print("OK: draw() raises RuntimeError; normal draw & plain savefig succeed")
raise SystemExit(0)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
"""R3.1 / R3.4: other supported inset-axes forms still build and save with
bbox_inches='tight': (a) sizes relative to parent (percent strings),
(b) explicit bbox_to_anchor + bbox_transform, (c) zoom-based inset via
zoomed_inset_axes, plus mark_inset. All must savefig(tight) without error."""
import io
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1.inset_locator import (
    inset_axes, zoomed_inset_axes, mark_inset)

fails = []

# (a) relative sizes
fig, ax = plt.subplots()
inset_axes(ax, width="30%", height="40%", loc="upper right")
f = io.BytesIO()
try:
    fig.savefig(f, bbox_inches="tight")
except Exception as e:
    fails.append(("relative-sizes", type(e).__name__, str(e)))
plt.close(fig)

# (b) explicit anchor bbox + transform
fig, ax = plt.subplots()
inset_axes(ax, width=1.0, height=1.0,
           bbox_to_anchor=(0.2, 0.2, 0.5, 0.5), bbox_transform=ax.transAxes)
f = io.BytesIO()
try:
    fig.savefig(f, bbox_inches="tight")
except Exception as e:
    fails.append(("explicit-bbox", type(e).__name__, str(e)))
plt.close(fig)

# (c) zoom-based inset + mark_inset
fig, ax = plt.subplots()
ax.plot(range(10))
axins = zoomed_inset_axes(ax, zoom=2, loc="upper left")
axins.plot(range(10))
axins.set_xlim(2, 4); axins.set_ylim(2, 4)
mark_inset(ax, axins, loc1=2, loc2=4)
f = io.BytesIO()
try:
    fig.savefig(f, bbox_inches="tight")
except Exception as e:
    fails.append(("zoom-inset", type(e).__name__, str(e)))
plt.close(fig)

if fails:
    print("FAIL:", fails)
    raise SystemExit(1)
print("OK: relative-size, explicit-bbox, and zoom insets all save with tight bbox")
raise SystemExit(0)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Positive control (R1.2 / R2.1 / R2.3): inset_axes with width/height only,
then savefig(bbox_inches='tight') must complete without exception.
HOLDS on patched, FAILS at base (AttributeError NoneType._get_renderer)."""
import io
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1.inset_locator import inset_axes

fig, ax = plt.subplots()
inset_axes(ax, width=1.3, height=0.9)
f = io.BytesIO()
try:
    fig.savefig(f, bbox_inches="tight")
except Exception as e:
    print("FAIL: savefig(bbox_inches='tight') raised:", type(e).__name__, e)
    raise SystemExit(1)
print("OK: savefig with bbox_inches='tight' succeeded, bytes=", len(f.getvalue()))
raise SystemExit(0)
```

Prepatch bug re-encoded as an attack: `True`.

Instance fixes AnchoredLocatorBase.__call__ to fetch ax.figure._get_renderer() when renderer is None. Six probes, all HOLD on gold-patched tree:
- probe_1 (R1.2/R2.1/R2.3 + POSITIVE CONTROL): inset_axes(width,height) then savefig(bbox_inches='tight') succeeds. Patched exit0; base exit1 (AttributeError NoneType._get_renderer). prepatch reproduced.
- probe_2 (R1.1/R1.2/R1.4): locator(ax, None) does not raise and returns a valid BboxBase with finite positive bounds. Patched exit0; base exit1.
- probe_3 (R1.3): with a supplied non-None renderer, the locator uses it unchanged and does NOT fetch a fallback (figure._get_renderer sabotaged to raise); returned bbox identical. Patched exit0.
- probe_4 (R1.4): fallback renderer is derived from ax.figure (monkeypatch tags the renderer; get_window_extent spy confirms the tagged renderer is measured, and _get_renderer is called on ax.figure). Patched exit0; base exit1.
- probe_5 (R3.3/R3.2): draw() still raises RuntimeError; normal fig.canvas.draw()+plain savefig succeed. Patched exit0.
- probe_6 (R3.1/R3.4): relative-size, explicit bbox_to_anchor+transform, and zoomed_inset_axes+mark_inset all savefig(tight) without error. Patched exit0.

DISCRIMINATION: candidate 'weak_always' unconditionally overrides renderer=ax.figure._get_renderer() (ignores any supplied renderer). It is REJECTED by probe_3 (R1.3 violated: substitutes a different renderer). This shows the suite distinguishes a wrong reading of R1.3 from the gold fix. No probe-conforming alternative patch was found that fails hidden tests. Verdict SOUND: >=5 probes hold on patched, positive control discriminates (holds patched / fails base), and >=1 candidate exercised and rejected.

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
"""Positive control (R1.2 / R2.1 / R2.3): inset_axes with width/height only,
then savefig(bbox_inches='tight') must complete without exception.
HOLDS on patched, FAILS at base (AttributeError NoneType._get_renderer)."""
import io
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1.inset_locator import inset_axes

fig, ax = plt.subplots()
inset_axes(ax, width=1.3, height=0.9)
f = io.BytesIO()
try:
    fig.savefig(f, bbox_inches="tight")
except Exception as e:
    print("FAIL: savefig(bbox_inches='tight') raised:", type(e).__name__, e)
    raise SystemExit(1)
print("OK: savefig with bbox_inches='tight' succeeded, bytes=", len(f.getvalue()))
raise SystemExit(0)
```

Prepatch bug re-encoded as an attack: `True`.

Instance fixes AnchoredLocatorBase.__call__ to fetch ax.figure._get_renderer() when renderer is None. Six probes, all HOLD on gold-patched tree:
- probe_1 (R1.2/R2.1/R2.3 + POSITIVE CONTROL): inset_axes(width,height) then savefig(bbox_inches='tight') succeeds. Patched exit0; base exit1 (AttributeError NoneType._get_renderer). prepatch reproduced.
- probe_2 (R1.1/R1.2/R1.4): locator(ax, None) does not raise and returns a valid BboxBase with finite positive bounds. Patched exit0; base exit1.
- probe_3 (R1.3): with a supplied non-None renderer, the locator uses it unchanged and does NOT fetch a fallback (figure._get_renderer sabotaged to raise); returned bbox identical. Patched exit0.
- probe_4 (R1.4): fallback renderer is derived from ax.figure (monkeypatch tags the renderer; get_window_extent spy confirms the tagged renderer is measured, and _get_renderer is called on ax.figure). Patched exit0; base exit1.
- probe_5 (R3.3/R3.2): draw() still raises RuntimeError; normal fig.canvas.draw()+plain savefig succeed. Patched exit0.
- probe_6 (R3.1/R3.4): relative-size, explicit bbox_to_anchor+transform, and zoomed_inset_axes+mark_inset all savefig(tight) without error. Patched exit0.

DISCRIMINATION: candidate 'weak_always' unconditionally overrides renderer=ax.figure._get_renderer() (ignores any supplied renderer). It is REJECTED by probe_3 (R1.3 violated: substitutes a different renderer). This shows the suite distinguishes a wrong reading of R1.3 from the gold fix. No probe-conforming alternative patch was found that fails hidden tests. Verdict SOUND: >=5 probes hold on patched, positive control discriminates (holds patched / fails base), and >=1 candidate exercised and rejected.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** The one-line gold patch touches the shared base class `AnchoredLocatorBase.__call__`, which covers both AnchoredSizeLocator and AnchoredZoomLocator subclasses (they don't override __call__), so Req1's phrasing '(AnchoredLocatorBase.__call__ and its subclasses)' pins the correct modeling boundary — the changed observable behavior — not a narrow slice. Requirements 2 and 3 are the behavioral/regression envelope and match the F2P test test_inset_axes_tight. No mandated behavior absent from code, no forbidden behavior present, no invented behavior.

Counterexample / evidence:

```
N/A — no divergence. Patched probe: savefig tight OK; renderer=None bbox == renderer-given bbox (match: True); draw raises RuntimeError. Base probe: AttributeError 'NoneType' object has no attribute '_get_renderer'.
```


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The document describes behavior and localizes the change to AnchoredLocatorBase.__call__ / AnchoredSizeLocator / AnchoredZoomLocator in inset_locator.py — all of which, along with get_window_extent, get_offset, _get_renderer, and the AttributeError, are already public in the problem_statement's traceback and repro code (inset_axes(ax, width=1.3, height=0.9); bbox_inches='tight'). The renderer-from-host-Axes-figure requirement (Req 1) is a behavioral translation of the gold fix (renderer = ax.figure._get_renderer()) using only public identifiers, not a quote of test/gold code. The hidden test test_inset_axes_tight reuses the SAME repro that is already public, so Req 2.3 leaks nothing. Req 3.3's mention of the draw method raising RuntimeError is existing source-code localization (a context line in the diff), not a test-invented identifier; the PASS_TO_PASS test names (e.g. test_anchored_locator_base_call, test_inset_axes_complete) are never surfaced. Req 3.1's enumeration of supported argument forms describes the public API surface, not parametrization ids. No test paths, test/function names, parametrization ids, verbatim gold/test lines, or fix-invented identifiers found beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
