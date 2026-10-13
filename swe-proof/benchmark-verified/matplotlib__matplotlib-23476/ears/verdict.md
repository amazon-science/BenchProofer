# P2 adversarial audit — matplotlib__matplotlib-23476

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
#!/usr/bin/env python
# Req1.3 / Req1.1 (positive control): a figure whose working dpi was scaled by a
# device-pixel-ratio change must, after pickle round-trip, restore to the BASELINE dpi.
import sys, os, pickle
os.environ.setdefault("MPLBACKEND", "Agg")
import matplotlib
from matplotlib.figure import Figure

fig = Figure(dpi=42)
fig.canvas._set_device_pixel_ratio(7)
print("live dpi after ratio:", fig.dpi)
assert fig.dpi == 42 * 7, "precondition: live dpi should be scaled to 294"
fig2 = pickle.loads(pickle.dumps(fig))
print("restored dpi:", fig2.dpi)
if fig2.dpi != 42:
    print("FAIL: restored dpi is", fig2.dpi, "expected baseline 42")
    sys.exit(1)
print("PASS: restored dpi equals baseline 42")
sys.exit(0)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
#!/usr/bin/env python
# Req1.4: repeated pickle/unpickle cycles must keep dpi constant and NOT grow.
import sys, os, pickle
os.environ.setdefault("MPLBACKEND", "Agg")
from matplotlib.figure import Figure

fig = Figure(dpi=42)
fig.canvas._set_device_pixel_ratio(7)
dpis = []
cur = fig
for i in range(5):
    cur = pickle.loads(pickle.dumps(cur))
    dpis.append(cur.dpi)
print("dpi across cycles:", dpis)
if any(d != 42 for d in dpis):
    print("FAIL: dpi not constant at baseline 42:", dpis)
    sys.exit(1)
print("PASS: dpi constant at 42 across all cycles")
sys.exit(0)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
#!/usr/bin/env python
# Req1.2 / Req2.2: a figure with NO _original_dpi recorded (never had canvas ratio
# change) must serialize its current working dpi unchanged; round-trip preserves it.
# Also Req1.1: __getstate__ output records _dpi correctly.
import sys, os, pickle
os.environ.setdefault("MPLBACKEND", "Agg")
from matplotlib.figure import Figure

# Build a figure and ensure _original_dpi is absent from what getstate records.
fig = Figure(dpi=77)
# don't attach any device pixel ratio scaling
state = fig.__getstate__()
print("state _dpi:", state.get("_dpi"), "has _original_dpi:", "_original_dpi" in state)
if state.get("_dpi") != 77:
    print("FAIL: getstate _dpi should be current 77, got", state.get("_dpi"))
    sys.exit(1)
fig2 = pickle.loads(pickle.dumps(fig))
print("restored dpi:", fig2.dpi)
if fig2.dpi != 77:
    print("FAIL: restored dpi should be 77, got", fig2.dpi)
    sys.exit(1)
print("PASS: unscaled figure preserves dpi 77")
sys.exit(0)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
#!/usr/bin/env python
# Req2.1: __getstate__ SHALL exclude canvas and cached renderer and include version.
import sys, os
os.environ.setdefault("MPLBACKEND", "Agg")
import matplotlib as mpl
from matplotlib.figure import Figure

fig = Figure(dpi=50)
state = fig.__getstate__()
ok = True
if state.get("_cachedRenderer") is not None:
    print("FAIL: _cachedRenderer not None:", state.get("_cachedRenderer")); ok = False
if "canvas" in state:
    print("FAIL: canvas present in state"); ok = False
if state.get("__mpl_version__") != mpl.__version__:
    print("FAIL: version not recorded correctly:", state.get("__mpl_version__")); ok = False
print("has canvas key:", "canvas" in state, "cachedRenderer:", state.get("_cachedRenderer"),
      "version:", state.get("__mpl_version__"))
if not ok:
    sys.exit(1)
print("PASS: canvas excluded, cachedRenderer None, version recorded")
sys.exit(0)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
#!/usr/bin/env python
# Req2.4: live (non-pickled) device-pixel-ratio change SHALL still set working dpi to
# ratio * baseline. Req2.3: direct dpi set updates dpi/transform/size consistently.
import sys, os
os.environ.setdefault("MPLBACKEND", "Agg")
from matplotlib.figure import Figure

fig = Figure(dpi=100)
# baseline recorded when canvas attached is 100
fig.canvas._set_device_pixel_ratio(2)
print("live scaled dpi:", fig.dpi)
if fig.dpi != 200:
    print("FAIL: live scaled dpi should be 200, got", fig.dpi); sys.exit(1)

# Req2.3: direct dpi set consistency
fig2 = Figure(dpi=100)
w0, h0 = fig2.bbox.size
fig2.dpi = 150
scale = fig2.dpi_scale_trans.to_values()[0]  # sx
w1, h1 = fig2.bbox.size
print("reported dpi:", fig2.dpi, "transform sx:", scale, "size0:", (w0,h0), "size1:", (w1,h1))
if fig2.dpi != 150:
    print("FAIL: dpi not 150"); sys.exit(1)
if abs(scale - 150) > 1e-9:
    print("FAIL: dpi_scale_trans not updated to 150, got", scale); sys.exit(1)
if not (w1 > w0 and h1 > h0):
    print("FAIL: pixel size did not grow with dpi"); sys.exit(1)
print("PASS: live ratio scaling and direct dpi set are consistent")
sys.exit(0)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
#!/usr/bin/env python
# Req2.6: Figure stays deep-copyable with no loss of state; Req2.5 restore path works.
import sys, os, copy, pickle
os.environ.setdefault("MPLBACKEND", "Agg")
from matplotlib.figure import Figure

fig = Figure(dpi=90)
ax = fig.add_subplot()
ax.plot([0, 1], [0, 1])
fig.canvas._set_device_pixel_ratio(3)  # scale live to 270

fig2 = copy.deepcopy(fig)
print("deepcopy dpi:", fig2.dpi, "n_axes:", len(fig2.axes))
# deepcopy also routes through __getstate__/__setstate__, so baseline should restore
if fig2.dpi != 90:
    print("FAIL: deepcopy dpi should restore to baseline 90, got", fig2.dpi); sys.exit(1)
if len(fig2.axes) != 1:
    print("FAIL: axes lost in deepcopy"); sys.exit(1)

# pickle preserves axes too
fig3 = pickle.loads(pickle.dumps(fig))
if len(fig3.axes) != 1:
    print("FAIL: axes lost in pickle"); sys.exit(1)
print("PASS: deep-copyable & picklable with state preserved, dpi restored to baseline")
sys.exit(0)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
#!/usr/bin/env python
# Req1.3 / Req1.1 (positive control): a figure whose working dpi was scaled by a
# device-pixel-ratio change must, after pickle round-trip, restore to the BASELINE dpi.
import sys, os, pickle
os.environ.setdefault("MPLBACKEND", "Agg")
import matplotlib
from matplotlib.figure import Figure

fig = Figure(dpi=42)
fig.canvas._set_device_pixel_ratio(7)
print("live dpi after ratio:", fig.dpi)
assert fig.dpi == 42 * 7, "precondition: live dpi should be scaled to 294"
fig2 = pickle.loads(pickle.dumps(fig))
print("restored dpi:", fig2.dpi)
if fig2.dpi != 42:
    print("FAIL: restored dpi is", fig2.dpi, "expected baseline 42")
    sys.exit(1)
print("PASS: restored dpi equals baseline 42")
sys.exit(0)
```

Prepatch bug re-encoded as an attack: `True`.

Bundle: matplotlib-23476. Gold patch: in Figure.__getstate__, state['_dpi'] = state.get('_original_dpi', state['_dpi']) — serialize baseline dpi so pickle round-trips are resolution-stable.

6 probes, all HOLD on the gold-patched tree:
- probe_1 (Req1.3/1.1, POSITIVE CONTROL): scale dpi via _set_device_pixel_ratio(7) on dpi=42 (live=294), pickle round-trip restores 42. PATCHED: restored 42 (PASS). BASE: restored 294 (FAIL) => discriminates. Candidate(halve): 147 (FAIL).
- probe_2 (Req1.4): 5 successive pickle cycles keep dpi constant, no growth. PATCHED [42,42,42,42,42] PASS; BASE [294,...] FAIL; candidate decays [147,73.5,...] FAIL.
- probe_3 (Req1.2/1.5/2.2): figure with dpi=77, __getstate__ records _dpi=77 unchanged and round-trip preserves 77. Encodes Req1.5 'no arithmetic on the two resolutions'. PATCHED PASS (77); BASE PASS (77, regression leg); candidate FAIL (38.5) — directly catches arithmetic-based fixes.
- probe_4 (Req2.1): __getstate__ excludes canvas, sets _cachedRenderer=None, records __mpl_version__. Holds on both trees (regression).
- probe_5 (Req2.3/2.4): live _set_device_pixel_ratio(2) gives ratio*baseline=200; direct fig.dpi=150 updates dpi, dpi_scale_trans sx=150, and bbox size grows. Holds on both trees (regression).
- probe_6 (Req2.5/2.6): deepcopy preserves axes and restores baseline dpi (90 not 270); pickle preserves axes. PATCHED PASS; BASE FAIL (270); candidate FAIL (135).

Candidate patch 'halve_dpi_naive' (weak.diff): a lazy fix the issue prose ('resolution doubles each round trip') tempts — state['_dpi']/=2 in __getstate__. Applies cleanly at base_commit. REJECTED by probes 1,2,3,6 (and it corrupts every unscaled figure). Demonstrates the suite discriminates wrong implementations that do arithmetic rather than selecting the baseline.

Positive control failed at base (294 vs 42) and holds patched => discriminating power confirmed. All 6 probes hold on patched; no violation found; the requirements-conforming wrong fix is rejected. Verdict SOUND.

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
#!/usr/bin/env python
# Req1.3 / Req1.1 (positive control): a figure whose working dpi was scaled by a
# device-pixel-ratio change must, after pickle round-trip, restore to the BASELINE dpi.
import sys, os, pickle
os.environ.setdefault("MPLBACKEND", "Agg")
import matplotlib
from matplotlib.figure import Figure

fig = Figure(dpi=42)
fig.canvas._set_device_pixel_ratio(7)
print("live dpi after ratio:", fig.dpi)
assert fig.dpi == 42 * 7, "precondition: live dpi should be scaled to 294"
fig2 = pickle.loads(pickle.dumps(fig))
print("restored dpi:", fig2.dpi)
if fig2.dpi != 42:
    print("FAIL: restored dpi is", fig2.dpi, "expected baseline 42")
    sys.exit(1)
print("PASS: restored dpi equals baseline 42")
sys.exit(0)
```

Prepatch bug re-encoded as an attack: `True`.

Bundle: matplotlib-23476. Gold patch: in Figure.__getstate__, state['_dpi'] = state.get('_original_dpi', state['_dpi']) — serialize baseline dpi so pickle round-trips are resolution-stable.

6 probes, all HOLD on the gold-patched tree:
- probe_1 (Req1.3/1.1, POSITIVE CONTROL): scale dpi via _set_device_pixel_ratio(7) on dpi=42 (live=294), pickle round-trip restores 42. PATCHED: restored 42 (PASS). BASE: restored 294 (FAIL) => discriminates. Candidate(halve): 147 (FAIL).
- probe_2 (Req1.4): 5 successive pickle cycles keep dpi constant, no growth. PATCHED [42,42,42,42,42] PASS; BASE [294,...] FAIL; candidate decays [147,73.5,...] FAIL.
- probe_3 (Req1.2/1.5/2.2): figure with dpi=77, __getstate__ records _dpi=77 unchanged and round-trip preserves 77. Encodes Req1.5 'no arithmetic on the two resolutions'. PATCHED PASS (77); BASE PASS (77, regression leg); candidate FAIL (38.5) — directly catches arithmetic-based fixes.
- probe_4 (Req2.1): __getstate__ excludes canvas, sets _cachedRenderer=None, records __mpl_version__. Holds on both trees (regression).
- probe_5 (Req2.3/2.4): live _set_device_pixel_ratio(2) gives ratio*baseline=200; direct fig.dpi=150 updates dpi, dpi_scale_trans sx=150, and bbox size grows. Holds on both trees (regression).
- probe_6 (Req2.5/2.6): deepcopy preserves axes and restores baseline dpi (90 not 270); pickle preserves axes. PATCHED PASS; BASE FAIL (270); candidate FAIL (135).

Candidate patch 'halve_dpi_naive' (weak.diff): a lazy fix the issue prose ('resolution doubles each round trip') tempts — state['_dpi']/=2 in __getstate__. Applies cleanly at base_commit. REJECTED by probes 1,2,3,6 (and it corrupts every unscaled figure). Demonstrates the suite discriminates wrong implementations that do arithmetic rather than selecting the baseline.

Positive control failed at base (294 vs 42) and holds patched => discriminating power confirmed. All 6 probes hold on patched; no violation found; the requirements-conforming wrong fix is rejected. Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Probe on gold-patched tree: ALL OK (exit 0). Base tree VIOLATED: dpi=294 after one round-trip (scaling doubles), confirming requirements track the actual fix. Requirement 5's 'no arithmetic' clause matches the patch (pure dict.get selection). Req 2.3 (dpi property/_set_dpi transform+pixel-size consistency) untouched by patch and is a preserved-behavior clause, consistent. Boundary is correct: requirements model the observable pickle round-trip dpi invariance, not just the helper.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The requirements translate the gold fix (state['_dpi'] = state.get('_original_dpi', state['_dpi'])) into behavioral EARS criteria: serialize baseline (_original_dpi) when present else current _dpi, no arithmetic, round-trip stability. All named identifiers (Figure._dpi, _original_dpi, __getstate__, __setstate__, FigureCanvasBase._set_device_pixel_ratio, Figure._set_dpi, __mpl_version__ version-mismatch warning) are pre-existing source symbols used for legitimate localization, not fix-invented. The only symbol also present in the test_patch is _set_device_pixel_ratio, which is a public source method — naming the scaling mechanism is legitimate. No hidden-test content leaks: no test function name (test_unpickle_with_device_pixel_ratio), no file path (tests/test_figure.py), no parametrization ids, and none of the concrete test values (dpi=42, ratio 7, 42*7) appear. The doubling/OverflowError/M1 high-DPI context is all in the public problem_statement. Req 1.5's 'no arithmetic on the two resolutions' describes the select-one semantics behaviorally rather than quoting the gold dict.get line. Requirement 2's regression-preservation clauses describe pre-existing __getstate__/__setstate__ behavior derivable from source, not from tests.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
