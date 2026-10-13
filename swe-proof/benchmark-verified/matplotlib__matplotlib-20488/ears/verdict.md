# P2 adversarial audit — matplotlib__matplotlib-20488

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
"""Positive control / Req 1.4 & 1.1:
Drawing an image with LogNorm whose resampled data mixes non-positive entries
(-1) with huge-magnitude entries (1e20) SHALL complete without raising
ValueError("Invalid vmin or vmax"). This is exactly the FAIL_TO_PASS scenario.
Exit 0 iff the draw completes without that ValueError.
"""
import sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import colors

data = np.full((5, 5), -1, dtype=np.float64)
data[0:2, :] = 1E20

fig, ax = plt.subplots()
ax.imshow(data, norm=colors.LogNorm(vmin=1, vmax=data.max()),
          interpolation='nearest', cmap='viridis')
try:
    fig.canvas.draw()
except ValueError as e:
    print("FAIL: draw raised ValueError:", e)
    sys.exit(1)
print("OK: huge-range LogNorm draw completed without ValueError")
sys.exit(0)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""Req 1.1 & 1.2: When LogNorm's re-derived lower bound is <= 0, the drawing
routine SHALL replace it with EXACTLY the machine-epsilon floor of the working
dtype (float64 here) before applying the norm, independent of the original
non-positive value. We spy on the vmin the norm actually receives at draw time.
Exit 0 iff the received vmin == np.finfo(float64).eps (and is strictly > 0).
"""
import sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import colors

seen = {}
class SpyLog(colors.LogNorm):
    def __call__(self, value, clip=None):
        seen['vmin'] = float(self.vmin)
        return super().__call__(value, clip)

data = np.full((5, 5), -1, dtype=np.float64)
data[0:2, :] = 1E20
fig, ax = plt.subplots()
ax.imshow(data, norm=SpyLog(vmin=1, vmax=data.max()),
          interpolation='nearest', cmap='viridis')
fig.canvas.draw()

eps = float(np.finfo(np.float64).eps)
vmin = seen.get('vmin')
print("received vmin =", repr(vmin), " eps =", repr(eps))
if vmin is None:
    print("FAIL: norm never called")
    sys.exit(1)
if vmin <= 0:
    print("FAIL: non-positive vmin forwarded to LogNorm")
    sys.exit(1)
if vmin != eps:
    print("FAIL: replacement is not exactly the machine-epsilon floor")
    sys.exit(1)
print("OK: lower bound replaced with exactly eps")
sys.exit(0)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""Req 2.2 & 2.3 & 3.2: A NON-logarithmic (linear) normalisation SHALL leave the
re-derived lower bound unchanged regardless of sign. With data mixing -1 and
1e20 and a linear Normalize(vmin=1,...), the norm must receive a negative vmin
(the raw re-derived value, NOT eps). Values below vmin map through under-range.
Exit 0 iff the linear norm received a vmin < 0 (unchanged), i.e. NOT floored.
"""
import sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import colors

seen = {}
class SpyNorm(colors.Normalize):
    def __call__(self, value, clip=None):
        seen['vmin'] = float(self.vmin)
        return super().__call__(value, clip)

data = np.full((5, 5), -1.0, dtype=np.float64)
data[0:2, :] = 1E20
fig, ax = plt.subplots()
ax.imshow(data, norm=SpyNorm(vmin=1, vmax=data.max()),
          interpolation='nearest', cmap='viridis')
fig.canvas.draw()

vmin = seen.get('vmin')
eps = float(np.finfo(np.float64).eps)
print("linear norm received vmin =", repr(vmin))
if vmin is None:
    print("FAIL: norm never called")
    sys.exit(1)
if vmin == eps or vmin > 0:
    print("FAIL: linear norm's lower bound was floored/altered — sanitisation leaked to linear")
    sys.exit(1)
print("OK: linear normalisation lower bound left unchanged (negative preserved)")
sys.exit(0)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""Req 2.1 & 3.1: LogNorm with an already-valid (strictly positive) re-derived
lower bound SHALL be left UNCHANGED (not overwritten with eps). With all-positive
data, the norm must receive a vmin close to the true lower bound (~1.0), NOT eps.
Exit 0 iff the received vmin is strictly positive and clearly != eps (i.e. > 0.5).
"""
import sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import colors

seen = {}
class SpyLog(colors.LogNorm):
    def __call__(self, value, clip=None):
        seen['vmin'] = float(self.vmin)
        return super().__call__(value, clip)

data = np.full((5, 5), 5.0, dtype=np.float64)
data[0:2, :] = 1E5
fig, ax = plt.subplots()
ax.imshow(data, norm=SpyLog(vmin=1, vmax=data.max()),
          interpolation='nearest', cmap='viridis')
fig.canvas.draw()

vmin = seen.get('vmin')
eps = float(np.finfo(np.float64).eps)
print("received vmin =", repr(vmin), " eps =", repr(eps))
if vmin is None:
    print("FAIL: norm never called")
    sys.exit(1)
if vmin <= 0:
    print("FAIL: positive bound wrongly made non-positive")
    sys.exit(1)
if abs(vmin - eps) < 1e-12 or vmin < 0.5:
    print("FAIL: valid positive lower bound was overwritten (looks floored to eps)")
    sys.exit(1)
print("OK: valid positive LogNorm lower bound preserved unchanged")
sys.exit(0)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""Req 1.3: LogNorm with re-derived lower bound EXACTLY zero SHALL be treated as
non-positive and replaced with the positive floor. Use data of {0, 1e20}.
Also Req 1.5: the UPPER value must be left unchanged. We spy both vmin and vmax.
Exit 0 iff draw completes, received vmin == eps (strictly positive floor),
and received vmax equals the original data max (upper unchanged).
"""
import sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import colors

seen = {}
class SpyLog(colors.LogNorm):
    def __call__(self, value, clip=None):
        seen['vmin'] = float(self.vmin)
        seen['vmax'] = float(self.vmax)
        return super().__call__(value, clip)

data = np.full((5, 5), 0.0, dtype=np.float64)
data[0:2, :] = 1E20
vmax0 = float(data.max())
fig, ax = plt.subplots()
ax.imshow(data, norm=SpyLog(vmin=1, vmax=vmax0),
          interpolation='nearest', cmap='viridis')
try:
    fig.canvas.draw()
except ValueError as e:
    print("FAIL: zero lower bound caused ValueError:", e)
    sys.exit(1)

eps = float(np.finfo(np.float64).eps)
vmin, vmax = seen.get('vmin'), seen.get('vmax')
print("received vmin =", repr(vmin), " vmax =", repr(vmax), " eps =", repr(eps),
      " orig vmax =", repr(vmax0))
if vmin is None:
    print("FAIL: norm never called")
    sys.exit(1)
if vmin != eps:
    print("FAIL: zero not replaced with exact eps floor")
    sys.exit(1)
if vmax != vmax0:
    print("FAIL: upper value was altered during sanitisation")
    sys.exit(1)
print("OK: zero treated as non-positive -> eps; upper bound unchanged")
sys.exit(0)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
"""Req 3.4 (regression): An EMPTY image drawn with either linear or logarithmic
normalisation SHALL continue to behave as before (no crash from the sanitisation
logic). Exit 0 iff both empty draws complete without raising.
"""
import sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import colors

ok = True
for label, norm in [("Normalize", colors.Normalize()), ("LogNorm", colors.LogNorm())]:
    fig, ax = plt.subplots()
    ax.imshow(np.zeros((0, 0)), norm=norm)
    try:
        fig.canvas.draw()
        print(label, "empty draw: OK")
    except Exception as e:
        print(label, "empty draw FAIL:", type(e).__name__, e)
        ok = False
    plt.close(fig)

sys.exit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Positive control / Req 1.4 & 1.1:
Drawing an image with LogNorm whose resampled data mixes non-positive entries
(-1) with huge-magnitude entries (1e20) SHALL complete without raising
ValueError("Invalid vmin or vmax"). This is exactly the FAIL_TO_PASS scenario.
Exit 0 iff the draw completes without that ValueError.
"""
import sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import colors

data = np.full((5, 5), -1, dtype=np.float64)
data[0:2, :] = 1E20

fig, ax = plt.subplots()
ax.imshow(data, norm=colors.LogNorm(vmin=1, vmax=data.max()),
          interpolation='nearest', cmap='viridis')
try:
    fig.canvas.draw()
except ValueError as e:
    print("FAIL: draw raised ValueError:", e)
    sys.exit(1)
print("OK: huge-range LogNorm draw completed without ValueError")
sys.exit(0)
```

Prepatch bug re-encoded as an attack: `True`.

matplotlib-20488: gold fix changes the LogNorm lower-bound guard in image._make_image from `if s_vmin < 0: s_vmin = max(s_vmin, eps)` to `if isinstance(norm, LogNorm) and s_vmin <= 0: s_vmin = eps`. Probes spy on the vmin/vmax the norm actually receives during fig.canvas.draw().

Probe results (all HOLD on patched tree):
- probe_1 (POSITIVE CONTROL; Req1.4/1.1): huge-range LogNorm data {-1, 1e20} draws without ValueError. PATCHED exit0; BASE exit1 -> discriminates.
- probe_2 (Req1.1/1.2): non-positive lower bound replaced with EXACTLY finfo(float64).eps, independent of original. Received vmin==eps on patched; BASE exit1.
- probe_3 (Req2.2/2.3/3.2): linear Normalize with {-1,1e20} data leaves lower bound unchanged (received vmin=-1.0, not floored). HOLDS patched & weak.
- probe_4 (Req2.1/3.1): all-positive LogNorm data keeps its true positive lower bound (~1.0), NOT overwritten with eps. HOLDS.
- probe_5 (Req1.3/1.5): ZERO lower bound treated as non-positive -> eps, and upper vmax left unchanged (1e20). PATCHED exit0; BASE exit1 -> discriminates the boundary.
- probe_6 (Req3.4): empty image draw with both Normalize and LogNorm completes without crash. HOLDS.

Wrong-fix candidate `weak.diff` = naive partial fix keeping the original strict `s_vmin < 0` guard (only assigns eps). REJECTED by probes 1, 2, 5 (the s_vmin==0 boundary still forwards 0 to LogNorm -> ValueError), matching the exact gap the requirements (Req1.3) and hidden test test_huge_range_log[png--1] target. probes 3,4,6 pass under it (expected, they aren't the discriminator). This demonstrates the suite discriminates the lazy reading that a weaker spec would permit.

All 6 probes hold on patched tree; positive control fails at base and holds patched. Requirements are faithful to the gold behavior and the suite rejects the plausible weak fix -> SOUND.

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
"""Positive control / Req 1.4 & 1.1:
Drawing an image with LogNorm whose resampled data mixes non-positive entries
(-1) with huge-magnitude entries (1e20) SHALL complete without raising
ValueError("Invalid vmin or vmax"). This is exactly the FAIL_TO_PASS scenario.
Exit 0 iff the draw completes without that ValueError.
"""
import sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import colors

data = np.full((5, 5), -1, dtype=np.float64)
data[0:2, :] = 1E20

fig, ax = plt.subplots()
ax.imshow(data, norm=colors.LogNorm(vmin=1, vmax=data.max()),
          interpolation='nearest', cmap='viridis')
try:
    fig.canvas.draw()
except ValueError as e:
    print("FAIL: draw raised ValueError:", e)
    sys.exit(1)
print("OK: huge-range LogNorm draw completed without ValueError")
sys.exit(0)
```

Prepatch bug re-encoded as an attack: `True`.

matplotlib-20488: gold fix changes the LogNorm lower-bound guard in image._make_image from `if s_vmin < 0: s_vmin = max(s_vmin, eps)` to `if isinstance(norm, LogNorm) and s_vmin <= 0: s_vmin = eps`. Probes spy on the vmin/vmax the norm actually receives during fig.canvas.draw().

Probe results (all HOLD on patched tree):
- probe_1 (POSITIVE CONTROL; Req1.4/1.1): huge-range LogNorm data {-1, 1e20} draws without ValueError. PATCHED exit0; BASE exit1 -> discriminates.
- probe_2 (Req1.1/1.2): non-positive lower bound replaced with EXACTLY finfo(float64).eps, independent of original. Received vmin==eps on patched; BASE exit1.
- probe_3 (Req2.2/2.3/3.2): linear Normalize with {-1,1e20} data leaves lower bound unchanged (received vmin=-1.0, not floored). HOLDS patched & weak.
- probe_4 (Req2.1/3.1): all-positive LogNorm data keeps its true positive lower bound (~1.0), NOT overwritten with eps. HOLDS.
- probe_5 (Req1.3/1.5): ZERO lower bound treated as non-positive -> eps, and upper vmax left unchanged (1e20). PATCHED exit0; BASE exit1 -> discriminates the boundary.
- probe_6 (Req3.4): empty image draw with both Normalize and LogNorm completes without crash. HOLDS.

Wrong-fix candidate `weak.diff` = naive partial fix keeping the original strict `s_vmin < 0` guard (only assigns eps). REJECTED by probes 1, 2, 5 (the s_vmin==0 boundary still forwards 0 to LogNorm -> ValueError), matching the exact gap the requirements (Req1.3) and hidden test test_huge_range_log[png--1] target. probes 3,4,6 pass under it (expected, they aren't the discriminator). This demonstrates the suite discriminates the lazy reading that a weaker spec would permit.

All 6 probes hold on patched tree; positive control fails at base and holds patched. Requirements are faithful to the gold behavior and the suite rejects the plausible weak fix -> SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Patch replaces `if isinstance(norm,LogNorm): if s_vmin<0: s_vmin=max(s_vmin,eps)` with `if isinstance(norm,LogNorm) and s_vmin<=0: s_vmin=np.finfo(scaled_dtype).eps`. Requirements pin exactly the changed observable behavior in _make_image: (Req1.1/1.3) LogNorm AND s_vmin<=0 -> replace with dtype-eps floor, covering the =0 case which is the true behavioral delta (old max(.,eps) for negative also yields eps, so 0 is where old code forwarded a fatal value); (Req1.2) replacement is unconditional eps, not depending on original — confirmed the removal of max(); (Req1.5/2.1/2.2/2.3) only s_vmin, only LogNorm, only when <=0, positives and non-LogNorm untouched; (Req3) no other lines changed, resampling/masking preserved. Modeling boundary is the changed behavior, not a narrow branch; eps correctly described as machine epsilon of working scaled_dtype (probe confirmed float64 eps used). No invented behavior.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The requirements doc localizes the change to _make_image in lib/matplotlib/image.py and LogNorm in colors.py, and describes the ValueError("Invalid vmin or vmax") — all of which are already public in the problem_statement's traceback. The fix mechanism (replace a non-positive lower bound with the dtype machine-epsilon floor np.finfo(<dtype>).eps; boundary at <= 0) is a legitimate behavioral translation of the gold edit, not a transmission of test material: no fix-invented identifiers are quoted (scaled_dtype/s_vmin/vrange never appear), no verbatim gold lines. No hidden-test artifacts leak: no test function/file names (test_huge_range_log, test_image.py), no parametrization ids ([png--1], test_empty_imshow[LogNorm]), no quoted test code, no check_figures_equal/with_extremes/set_under references. Req 1.4's 'non-positive entries with very large magnitude' matches public facts (LogNorm non-positive is the bug; fill_value=1e+20 appears in the traceback) rather than the hidden parametrization values. Reqs 3.2 (under-range colour) and 3.4 (empty image, linear+log) are generic regression concerns, not test-shaped enumerations mirroring the parametrization. NO-LEAKAGE.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
