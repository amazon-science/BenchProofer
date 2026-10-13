# P2 adversarial audit — matplotlib__matplotlib-25311

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
# Req 1.1 + 2.1 + positive control: draggable legend figure pickles, stream carries NO backend canvas ref
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pickle
fig, ax = plt.subplots()
ax.plot([1,2,3],[3,2,1], label="l")
leg = ax.legend(); leg.set_draggable(True)
data = pickle.dumps(fig)
canvas_cls = type(fig.canvas).__name__.encode()
print("pickled ok len", len(data), "canvas class token", canvas_cls, "present:", canvas_cls in data)
assert canvas_cls not in data, "backend canvas class embedded in stream"
assert b"FigureCanvasAgg" not in data
print("OK: legend figure pickled with no backend canvas ref")
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
# Req 1.2 + 2.1: draggable annotation figure pickles, no backend canvas ref
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pickle
fig, ax = plt.subplots()
ann = ax.annotate("t",(0.5,0.5))
ann.draggable(True)
data = pickle.dumps(fig)
tok = type(fig.canvas).__name__.encode()
print("pickled ok len", len(data), "token present:", tok in data)
assert tok not in data, "backend canvas embedded via draggable annotation"
print("OK: annotation figure pickled clean")
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
# Req 3.1/3.2/3.3 + 2.2: canvas is a recomputed accessor, not stored on instance; reflects current figure canvas
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
fig, ax = plt.subplots()
ax.plot([1],[1],label="a"); leg=ax.legend(); leg.set_draggable(True)
d = leg._draggable
print("'canvas' in instance __dict__:", 'canvas' in d.__dict__)
assert 'canvas' not in d.__dict__, "canvas stored on instance state"
# returns current canvas via ref_artist.figure
assert d.canvas is fig.canvas, "canvas does not resolve to figure canvas"
# dynamic recompute: swap in a sentinel canvas on the owning figure
class Sentinel: pass
sent = Sentinel()
d.ref_artist.figure.canvas = sent
assert d.canvas is sent, "canvas not recomputed on access after figure canvas change"
print("OK: canvas is a dynamic computed accessor reflecting current figure canvas")
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
# Req 1.4 + 5.2: deserialized figure carrying draggable artist is usable — canvas can redraw
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pickle
fig, ax = plt.subplots()
ax.plot([1,2],[2,1],label="a"); leg=ax.legend(); leg.set_draggable(True)
fig2 = pickle.loads(pickle.dumps(fig))
fig2.canvas.draw()  # must not raise
print("OK: restored figure drew via canvas; canvas type", type(fig2.canvas).__name__)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
# Req 4: interaction behavior preserved — pickable ref_artist, use_blit gating, pick/release callbacks registered, on_release finalize/disconnect exist
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.offsetbox import DraggableBase
fig, ax = plt.subplots()
ax.plot([1],[1],label="a"); leg=ax.legend()
# Req 4.5: ref_artist made pickable
leg.set_draggable(True, use_blit=True)
d = leg._draggable
print("ref_artist pickable:", d.ref_artist.pickable())
assert d.ref_artist.pickable()
# Req 4.1: use_blit only when both request and canvas.supports_blit
expected = True and d.canvas.supports_blit
print("_use_blit:", d._use_blit, "supports_blit:", d.canvas.supports_blit)
assert d._use_blit == expected
# Req 4.2: pick + button_release callbacks registered (cids present)
print("num cids:", len(d.cids))
assert len(d.cids) >= 2
# Req 4.4: on_release finalizes offset & disconnects motion callback
import inspect
src = inspect.getsource(DraggableBase.on_release)
print("on_release disconnects:", "disconnect" in src, "finalizes:", "finalize_offset" in src)
assert "disconnect" in src and "finalize_offset" in src
print("OK: interaction behavior preserved")
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
# Req 5.1/5.3: ordinary (non-draggable) figure round-trips, content preserved, no live backend canvas embedded
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pickle, numpy as np
fig, ax = plt.subplots()
ax.plot([0,1,2],[0,1,4], label="quad")
ax.errorbar([0,1],[1,2], yerr=[0.1,0.2])
ax.legend()  # NOT draggable
data = pickle.dumps(fig)
tok = type(fig.canvas).__name__.encode()
print("no backend canvas token:", tok not in data)
assert tok not in data
fig2 = pickle.loads(data)
fig2.canvas.draw()
# content preserved: first line ydata
yd = list(fig2.axes[0].lines[0].get_ydata())
print("restored ydata:", yd)
assert yd == [0.0,1.0,4.0]
print("OK: ordinary figure round-trips, content preserved, no canvas ref")
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
# Req 1.1 + 2.1 + positive control: draggable legend figure pickles, stream carries NO backend canvas ref
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pickle
fig, ax = plt.subplots()
ax.plot([1,2,3],[3,2,1], label="l")
leg = ax.legend(); leg.set_draggable(True)
data = pickle.dumps(fig)
canvas_cls = type(fig.canvas).__name__.encode()
print("pickled ok len", len(data), "canvas class token", canvas_cls, "present:", canvas_cls in data)
assert canvas_cls not in data, "backend canvas class embedded in stream"
assert b"FigureCanvasAgg" not in data
print("OK: legend figure pickled with no backend canvas ref")
```

Prepatch bug re-encoded as an attack: `True`.

Instance fix: DraggableBase stored self.canvas = ref_artist.figure.canvas (a live backend canvas) on the instance, poisoning the figure pickle stream; gold replaces it with a computed property canvas = property(lambda self: self.ref_artist.figure.canvas).

Probe suite (6, all HOLD on patched):
- probe_1 (Req 1.1/2.1, POSITIVE CONTROL): draggable-legend figure pickles and the backend canvas class token (FigureCanvasAgg) is absent from the stream. HOLDS patched, VIOLATED at base (base embeds FigureCanvasAgg bytes). Note: on Agg pickling does not raise even at base, so the discriminating signal is the presence of the backend-canvas class token in the byte stream, exactly what Req 2.1 mandates.
- probe_2 (Req 1.2/2.1): draggable-annotation figure pickles with no backend canvas token. HOLDS patched, VIOLATED at base.
- probe_3 (Req 3.1/3.2/3.3/2.2): 'canvas' is NOT in instance __dict__; d.canvas resolves to fig.canvas; after swapping the owning figure's canvas to a sentinel, d.canvas recomputes to the sentinel (dynamic accessor). HOLDS patched, VIOLATED at base.
- probe_4 (Req 1.4/5.2): round-tripped draggable-legend figure redraws via canvas.draw(). HOLDS both trees.
- probe_5 (Req 4.1/4.2/4.4/4.5): ref_artist pickable, _use_blit == (request and canvas.supports_blit), >=2 cids (pick+release), on_release source finalizes offset and disconnects. HOLDS both.
- probe_6 (Req 5.1/5.3): ordinary non-draggable figure (lines+errorbar+legend) round-trips, ydata preserved, no backend canvas token. HOLDS both.

Discrimination: probes 1/2/3 fail at base -> confirmed prepatch reproduction and positive control discriminates.

Weak candidate (getstate_strip, weak.diff): keeps self.canvas as stored instance state but adds __getstate__ that pops 'canvas' before pickling. This cleans the serialized stream (satisfies the naive reading of Req 1/2) and preserves interaction (Req 4) and round-trip (Req 5) -> passes probes 1,2,4,5,6. But it does NOT make canvas a recomputed accessor: 'canvas' remains in instance __dict__ and would go stale after deserialization onto a new canvas. probe_3 REJECTS it (VIOLATED). This demonstrates the suite discriminates a plausibly-wrong partial fix that Req 3's dynamic-accessor criteria forbid.

All needed runs completed cleanly. 6/6 probes hold patched; positive control discriminates; 1/1 weak candidate rejected.

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
# Req 1.1 + 2.1 + positive control: draggable legend figure pickles, stream carries NO backend canvas ref
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pickle
fig, ax = plt.subplots()
ax.plot([1,2,3],[3,2,1], label="l")
leg = ax.legend(); leg.set_draggable(True)
data = pickle.dumps(fig)
canvas_cls = type(fig.canvas).__name__.encode()
print("pickled ok len", len(data), "canvas class token", canvas_cls, "present:", canvas_cls in data)
assert canvas_cls not in data, "backend canvas class embedded in stream"
assert b"FigureCanvasAgg" not in data
print("OK: legend figure pickled with no backend canvas ref")
```

Prepatch bug re-encoded as an attack: `True`.

Instance fix: DraggableBase stored self.canvas = ref_artist.figure.canvas (a live backend canvas) on the instance, poisoning the figure pickle stream; gold replaces it with a computed property canvas = property(lambda self: self.ref_artist.figure.canvas).

Probe suite (6, all HOLD on patched):
- probe_1 (Req 1.1/2.1, POSITIVE CONTROL): draggable-legend figure pickles and the backend canvas class token (FigureCanvasAgg) is absent from the stream. HOLDS patched, VIOLATED at base (base embeds FigureCanvasAgg bytes). Note: on Agg pickling does not raise even at base, so the discriminating signal is the presence of the backend-canvas class token in the byte stream, exactly what Req 2.1 mandates.
- probe_2 (Req 1.2/2.1): draggable-annotation figure pickles with no backend canvas token. HOLDS patched, VIOLATED at base.
- probe_3 (Req 3.1/3.2/3.3/2.2): 'canvas' is NOT in instance __dict__; d.canvas resolves to fig.canvas; after swapping the owning figure's canvas to a sentinel, d.canvas recomputes to the sentinel (dynamic accessor). HOLDS patched, VIOLATED at base.
- probe_4 (Req 1.4/5.2): round-tripped draggable-legend figure redraws via canvas.draw(). HOLDS both trees.
- probe_5 (Req 4.1/4.2/4.4/4.5): ref_artist pickable, _use_blit == (request and canvas.supports_blit), >=2 cids (pick+release), on_release source finalizes offset and disconnects. HOLDS both.
- probe_6 (Req 5.1/5.3): ordinary non-draggable figure (lines+errorbar+legend) round-trips, ydata preserved, no backend canvas token. HOLDS both.

Discrimination: probes 1/2/3 fail at base -> confirmed prepatch reproduction and positive control discriminates.

Weak candidate (getstate_strip, weak.diff): keeps self.canvas as stored instance state but adds __getstate__ that pops 'canvas' before pickling. This cleans the serialized stream (satisfies the naive reading of Req 1/2) and preserves interaction (Req 4) and round-trip (Req 5) -> passes probes 1,2,4,5,6. But it does NOT make canvas a recomputed accessor: 'canvas' remains in instance __dict__ and would go stale after deserialization onto a new canvas. probe_3 REJECTS it (VIOLATED). This demonstrates the suite discriminates a plausibly-wrong partial fix that Req 3's dynamic-accessor criteria forbid.

All needed runs completed cleanly. 6/6 probes hold patched; positive control discriminates; 1/1 weak candidate rejected.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Probe run in-image on gold-patched tree: legend pickles, annotation pickles, canvas is a property reflecting the current figure canvas dynamically. Note the requirements deliberately frame Req 2 around 'no backend canvas reference introduced by the handler' (Req 2.3 even when the canvas is itself picklable) — this is the correct behavioral boundary and does not overreach; the Agg-backend base actually pickles (its canvas is serializable), so the requirements correctly do NOT claim serialization always failed on base, only that the handler must not embed a canvas reference. Faithfulness gate only; a separate G-PANEL-3 leakage concern (Req 5 / hidden-test enumeration) exists but is out of scope here.

Counterexample / evidence:

```
N/A — no divergence found. Positive control confirms the modeling boundary is meaningful: on the base commit the draggable handler stores a live canvas attribute (Req 3.3 property does not exist there).
```


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Requirements describe only public-API surface (offsetbox.py, DraggableBase/DraggableLegend/DraggableAnnotation, canvas, ref_artist) and behavior derivable from the public problem_statement (pickle raises TypeError on backend canvas; expected: pickle succeeds). No test names/paths/ids (test_complete, test_pickle.py, [png]) appear; the hidden assertion's specifics (pickletools.genops, the literal 'FigureCanvasAgg', Agg backend) are NOT reproduced — Req 2 states the no-canvas-in-stream property behaviorally and backend-agnostically. Req 4 enumerates pre-existing DraggableBase interaction behaviors (blit/pick/release/motion/pickable) from public source, not test parametrization. Closest concern is Req 3 AC3 (canvas as a recomputed accessor rather than stored attribute), which paraphrases the gold's property-vs-attribute choice; however it prescribes the natural design consequence of the publicly-diagnosed root cause (a stored live canvas reference poisons the pickle) and transmits no test artifact, verbatim gold line, or fix-invented identifier. Legitimate behavioral spec, not test/gold reconstruction.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
