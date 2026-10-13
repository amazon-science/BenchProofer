# P2 adversarial audit — matplotlib__matplotlib-24177

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

Counterexample / evidence:

```
none — no probe fails on the patched tree, and the requirements-permissive weak candidate is rejected by the suite
```

**Attacks re-run (7):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
import sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.path as mpath

verts = np.array([[-5.45, 0.0], [-5.45, 0.0], [-5.29, 0.0], [-5.29, 0.0], [-5.13, 0.0], [-5.13, 0.0], [-4.97, 0.0], [-4.97, 0.0], [-4.81, 0.0], [-4.81, 0.0], [-4.65, 0.0], [-4.65, 0.0], [-4.49, 0.0], [-4.49, 0.0], [-4.33, 0.0], [-4.33, 0.0], [-4.17, 0.0], [-4.17, 0.0], [-4.01, 0.0], [-4.01, 0.0], [-3.85, 0.0], [-3.85, 0.0], [-3.69, 0.0], [-3.69, 0.0], [-3.53, 0.0], [-3.53, 0.0], [-3.37, 0.0], [-3.37, 0.0], [-3.21, 0.0], [-3.21, 0.01], [-3.05, 0.01], [-3.05, 0.01], [-2.89, 0.01], [-2.89, 0.01], [-2.73, 0.01], [-2.73, 0.02], [-2.57, 0.02], [-2.57, 0.04], [-2.41, 0.04], [-2.41, 0.04], [-2.25, 0.04], [-2.25, 0.06], [-2.09, 0.06], [-2.09, 0.08], [-1.93, 0.08], [-1.93, 0.1], [-1.77, 0.1], [-1.77, 0.12], [-1.61, 0.12], [-1.61, 0.14], [-1.45, 0.14], [-1.45, 0.17], [-1.3, 0.17], [-1.3, 0.19], [-1.14, 0.19], [-1.14, 0.22], [-0.98, 0.22], [-0.98, 0.25], [-0.82, 0.25], [-0.82, 0.27], [-0.66, 0.27], [-0.66, 0.29], [-0.5, 0.29], [-0.5, 0.3], [-0.34, 0.3], [-0.34, 0.32], [-0.18, 0.32], [-0.18, 0.33], [-0.02, 0.33], [-0.02, 0.32], [0.13, 0.32], [0.13, 0.33], [0.29, 0.33], [0.29, 0.31], [0.45, 0.31], [0.45, 0.3], [0.61, 0.3], [0.61, 0.28], [0.77, 0.28], [0.77, 0.25], [0.93, 0.25], [0.93, 0.22], [1.09, 0.22], [1.09, 0.19], [1.25, 0.19], [1.25, 0.17], [1.41, 0.17], [1.41, 0.15], [1.57, 0.15], [1.57, 0.12], [1.73, 0.12], [1.73, 0.1], [1.89, 0.1], [1.89, 0.08], [2.05, 0.08], [2.05, 0.07], [2.21, 0.07], [2.21, 0.05], [2.37, 0.05], [2.37, 0.04], [2.53, 0.04], [2.53, 0.02], [2.69, 0.02], [2.69, 0.02], [2.85, 0.02], [2.85, 0.01], [3.01, 0.01], [3.01, 0.01], [3.17, 0.01], [3.17, 0.0], [3.33, 0.0], [3.33, 0.0], [3.49, 0.0], [3.49, 0.0], [3.65, 0.0], [3.65, 0.0], [3.81, 0.0], [3.81, 0.0], [3.97, 0.0], [3.97, 0.0], [4.13, 0.0], [4.13, 0.0], [4.29, 0.0], [4.29, 0.0], [4.45, 0.0], [4.45, 0.0], [4.61, 0.0], [4.61, 0.0], [4.77, 0.0], [4.77, 0.0], [4.93, 0.0], [4.93, 0.0]])
minx, maxx = np.min(verts[:,0]), np.max(verts[:,0])
miny, maxy = np.min(verts[:,1]), np.max(verts[:,1])

p = mpath.Path(verts)
fig, ax = plt.subplots()
ax.add_patch(mpatches.PathPatch(p))
ax.autoscale()
xlim = ax.get_xlim(); ylim = ax.get_ylim()
print("xlim", xlim, "ylim", ylim)
print("data extremes minx",minx,"maxx",maxx,"miny",miny,"maxy",maxy)
ok = (xlim[0] <= minx and xlim[1] >= maxx and ylim[0] <= miny and ylim[1] >= maxy)
print("ENCLOSES_ALL:", ok)
sys.exit(0 if ok else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
import sys
import numpy as np
import matplotlib.path as mpath
from matplotlib.path import Path

verts = np.array([[-5.45, 0.0], [-5.45, 0.0], [-5.29, 0.0], [-5.29, 0.0], [-5.13, 0.0], [-5.13, 0.0], [-4.97, 0.0], [-4.97, 0.0], [-4.81, 0.0], [-4.81, 0.0], [-4.65, 0.0], [-4.65, 0.0], [-4.49, 0.0], [-4.49, 0.0], [-4.33, 0.0], [-4.33, 0.0], [-4.17, 0.0], [-4.17, 0.0], [-4.01, 0.0], [-4.01, 0.0], [-3.85, 0.0], [-3.85, 0.0], [-3.69, 0.0], [-3.69, 0.0], [-3.53, 0.0], [-3.53, 0.0], [-3.37, 0.0], [-3.37, 0.0], [-3.21, 0.0], [-3.21, 0.01], [-3.05, 0.01], [-3.05, 0.01], [-2.89, 0.01], [-2.89, 0.01], [-2.73, 0.01], [-2.73, 0.02], [-2.57, 0.02], [-2.57, 0.04], [-2.41, 0.04], [-2.41, 0.04], [-2.25, 0.04], [-2.25, 0.06], [-2.09, 0.06], [-2.09, 0.08], [-1.93, 0.08], [-1.93, 0.1], [-1.77, 0.1], [-1.77, 0.12], [-1.61, 0.12], [-1.61, 0.14], [-1.45, 0.14], [-1.45, 0.17], [-1.3, 0.17], [-1.3, 0.19], [-1.14, 0.19], [-1.14, 0.22], [-0.98, 0.22], [-0.98, 0.25], [-0.82, 0.25], [-0.82, 0.27], [-0.66, 0.27], [-0.66, 0.29], [-0.5, 0.29], [-0.5, 0.3], [-0.34, 0.3], [-0.34, 0.32], [-0.18, 0.32], [-0.18, 0.33], [-0.02, 0.33], [-0.02, 0.32], [0.13, 0.32], [0.13, 0.33], [0.29, 0.33], [0.29, 0.31], [0.45, 0.31], [0.45, 0.3], [0.61, 0.3], [0.61, 0.28], [0.77, 0.28], [0.77, 0.25], [0.93, 0.25], [0.93, 0.22], [1.09, 0.22], [1.09, 0.19], [1.25, 0.19], [1.25, 0.17], [1.41, 0.17], [1.41, 0.15], [1.57, 0.15], [1.57, 0.12], [1.73, 0.12], [1.73, 0.1], [1.89, 0.1], [1.89, 0.08], [2.05, 0.08], [2.05, 0.07], [2.21, 0.07], [2.21, 0.05], [2.37, 0.05], [2.37, 0.04], [2.53, 0.04], [2.53, 0.02], [2.69, 0.02], [2.69, 0.02], [2.85, 0.02], [2.85, 0.01], [3.01, 0.01], [3.01, 0.01], [3.17, 0.01], [3.17, 0.0], [3.33, 0.0], [3.33, 0.0], [3.49, 0.0], [3.49, 0.0], [3.65, 0.0], [3.65, 0.0], [3.81, 0.0], [3.81, 0.0], [3.97, 0.0], [3.97, 0.0], [4.13, 0.0], [4.13, 0.0], [4.29, 0.0], [4.29, 0.0], [4.45, 0.0], [4.45, 0.0], [4.61, 0.0], [4.61, 0.0], [4.77, 0.0], [4.77, 0.0], [4.93, 0.0], [4.93, 0.0]])
p = Path(verts)  # all LINETO after first MOVETO
n_codes = len(p.vertices)
# count bezier segments with simplify disabled
segs_off = list(p.iter_bezier(simplify=False))
print("num vertices:", n_codes, "bezier segs simplify=False:", len(segs_off))
# with simplification active (default path.simplify True), a many-point path drops vertices
segs_default = list(p.iter_bezier())
print("bezier segs default:", len(segs_default))
# Requirement 1.4: with simplify disabled, EVERY segment is yielded => one bezier per vertex (MOVETO + LINETOs)
ok = (len(segs_off) == n_codes)
print("YIELDS_EVERY_SEGMENT:", ok)
sys.exit(0 if ok else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
import sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.path as mpath

verts = np.array([[-5.45, 0.0], [-5.45, 0.0], [-5.29, 0.0], [-5.29, 0.0], [-5.13, 0.0], [-5.13, 0.0], [-4.97, 0.0], [-4.97, 0.0], [-4.81, 0.0], [-4.81, 0.0], [-4.65, 0.0], [-4.65, 0.0], [-4.49, 0.0], [-4.49, 0.0], [-4.33, 0.0], [-4.33, 0.0], [-4.17, 0.0], [-4.17, 0.0], [-4.01, 0.0], [-4.01, 0.0], [-3.85, 0.0], [-3.85, 0.0], [-3.69, 0.0], [-3.69, 0.0], [-3.53, 0.0], [-3.53, 0.0], [-3.37, 0.0], [-3.37, 0.0], [-3.21, 0.0], [-3.21, 0.01], [-3.05, 0.01], [-3.05, 0.01], [-2.89, 0.01], [-2.89, 0.01], [-2.73, 0.01], [-2.73, 0.02], [-2.57, 0.02], [-2.57, 0.04], [-2.41, 0.04], [-2.41, 0.04], [-2.25, 0.04], [-2.25, 0.06], [-2.09, 0.06], [-2.09, 0.08], [-1.93, 0.08], [-1.93, 0.1], [-1.77, 0.1], [-1.77, 0.12], [-1.61, 0.12], [-1.61, 0.14], [-1.45, 0.14], [-1.45, 0.17], [-1.3, 0.17], [-1.3, 0.19], [-1.14, 0.19], [-1.14, 0.22], [-0.98, 0.22], [-0.98, 0.25], [-0.82, 0.25], [-0.82, 0.27], [-0.66, 0.27], [-0.66, 0.29], [-0.5, 0.29], [-0.5, 0.3], [-0.34, 0.3], [-0.34, 0.32], [-0.18, 0.32], [-0.18, 0.33], [-0.02, 0.33], [-0.02, 0.32], [0.13, 0.32], [0.13, 0.33], [0.29, 0.33], [0.29, 0.31], [0.45, 0.31], [0.45, 0.3], [0.61, 0.3], [0.61, 0.28], [0.77, 0.28], [0.77, 0.25], [0.93, 0.25], [0.93, 0.22], [1.09, 0.22], [1.09, 0.19], [1.25, 0.19], [1.25, 0.17], [1.41, 0.17], [1.41, 0.15], [1.57, 0.15], [1.57, 0.12], [1.73, 0.12], [1.73, 0.1], [1.89, 0.1], [1.89, 0.08], [2.05, 0.08], [2.05, 0.07], [2.21, 0.07], [2.21, 0.05], [2.37, 0.05], [2.37, 0.04], [2.53, 0.04], [2.53, 0.02], [2.69, 0.02], [2.69, 0.02], [2.85, 0.02], [2.85, 0.01], [3.01, 0.01], [3.01, 0.01], [3.17, 0.01], [3.17, 0.0], [3.33, 0.0], [3.33, 0.0], [3.49, 0.0], [3.49, 0.0], [3.65, 0.0], [3.65, 0.0], [3.81, 0.0], [3.81, 0.0], [3.97, 0.0], [3.97, 0.0], [4.13, 0.0], [4.13, 0.0], [4.29, 0.0], [4.29, 0.0], [4.45, 0.0], [4.45, 0.0], [4.61, 0.0], [4.61, 0.0], [4.77, 0.0], [4.77, 0.0], [4.93, 0.0], [4.93, 0.0]])
maxy = np.max(verts[:,1])
# find x location of the max-y point
p = mpath.Path(verts)
fig, ax = plt.subplots()
ax.add_patch(mpatches.PathPatch(p))
ax.autoscale()
ylim = ax.get_ylim()
print("ylim", ylim, "maxy", maxy)
# The tallest bin (maxy) must be enclosed; the pre-fix bug clipped it.
ok = ylim[1] >= maxy
print("MAXY_ENCLOSED:", ok)
sys.exit(0 if ok else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
import sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

fig, ax = plt.subplots()
ax.plot([1,2,3],[1,2,3])  # establish some data limits
xlim0 = ax.get_xlim(); ylim0 = ax.get_ylim()
# add a zero-size rectangle far away
ax.add_patch(mpatches.Rectangle((100.0, 100.0), 0, 0))
ax.autoscale()
xlim1 = ax.get_xlim(); ylim1 = ax.get_ylim()
print("before", xlim0, ylim0)
print("after ", xlim1, ylim1)
# zero-size rect must not stretch limits toward 100
ok = xlim1[1] < 50 and ylim1[1] < 50
print("ZERO_RECT_IGNORED:", ok)
sys.exit(0 if ok else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
import sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.path import Path

# a cubic bezier that bulges beyond its endpoints in y (interior extremum)
verts = [(0.0, 0.0), (0.0, 2.0), (1.0, 2.0), (1.0, 0.0)]
codes = [Path.MOVETO, Path.CURVE4, Path.CURVE4, Path.CURVE4]
p = Path(verts, codes)
fig, ax = plt.subplots()
ax.add_patch(mpatches.PathPatch(p))
ax.autoscale()
ylim = ax.get_ylim()
# analytic interior max of this symmetric cubic: y peaks at t=0.5 -> 1.5
# endpoints are y=0,0 so without interior extrema ylim top would be ~0
print("ylim", ylim)
ok = ylim[1] >= 1.4
print("INTERIOR_EXTREMUM_INCLUDED:", ok)
sys.exit(0 if ok else 1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
import sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.path import Path

fig, ax = plt.subplots()
ax.plot([1,2,3],[1,2,3])
xlim0 = ax.get_xlim(); ylim0 = ax.get_ylim()
empty = Path(np.empty((0,2)))
try:
    ax.add_patch(mpatches.PathPatch(empty))
    ax.autoscale()
except Exception as e:
    print("EXCEPTION", type(e).__name__, e)
    sys.exit(1)
xlim1 = ax.get_xlim(); ylim1 = ax.get_ylim()
print("before", xlim0, ylim0, "after", xlim1, ylim1)
ok = np.allclose(xlim0, xlim1) and np.allclose(ylim0, ylim1)
print("EMPTY_PATH_NOCHANGE:", ok)
sys.exit(0 if ok else 1)
```

Attack 7 — `probe_7.py` → holds on the patched tree (good)

```python
import sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

fig, ax = plt.subplots()
ax.add_patch(mpatches.Rectangle((0,0), 1, 1))
ax.add_patch(mpatches.Rectangle((5,5), 2, 2))
ax.autoscale()
xlim = ax.get_xlim(); ylim = ax.get_ylim()
print("xlim", xlim, "ylim", ylim)
ok = xlim[0] <= 0 and xlim[1] >= 7 and ylim[0] <= 0 and ylim[1] >= 7
print("UNION_ENCLOSED:", ok)
sys.exit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
import sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.path as mpath

verts = np.array([[-5.45, 0.0], [-5.45, 0.0], [-5.29, 0.0], [-5.29, 0.0], [-5.13, 0.0], [-5.13, 0.0], [-4.97, 0.0], [-4.97, 0.0], [-4.81, 0.0], [-4.81, 0.0], [-4.65, 0.0], [-4.65, 0.0], [-4.49, 0.0], [-4.49, 0.0], [-4.33, 0.0], [-4.33, 0.0], [-4.17, 0.0], [-4.17, 0.0], [-4.01, 0.0], [-4.01, 0.0], [-3.85, 0.0], [-3.85, 0.0], [-3.69, 0.0], [-3.69, 0.0], [-3.53, 0.0], [-3.53, 0.0], [-3.37, 0.0], [-3.37, 0.0], [-3.21, 0.0], [-3.21, 0.01], [-3.05, 0.01], [-3.05, 0.01], [-2.89, 0.01], [-2.89, 0.01], [-2.73, 0.01], [-2.73, 0.02], [-2.57, 0.02], [-2.57, 0.04], [-2.41, 0.04], [-2.41, 0.04], [-2.25, 0.04], [-2.25, 0.06], [-2.09, 0.06], [-2.09, 0.08], [-1.93, 0.08], [-1.93, 0.1], [-1.77, 0.1], [-1.77, 0.12], [-1.61, 0.12], [-1.61, 0.14], [-1.45, 0.14], [-1.45, 0.17], [-1.3, 0.17], [-1.3, 0.19], [-1.14, 0.19], [-1.14, 0.22], [-0.98, 0.22], [-0.98, 0.25], [-0.82, 0.25], [-0.82, 0.27], [-0.66, 0.27], [-0.66, 0.29], [-0.5, 0.29], [-0.5, 0.3], [-0.34, 0.3], [-0.34, 0.32], [-0.18, 0.32], [-0.18, 0.33], [-0.02, 0.33], [-0.02, 0.32], [0.13, 0.32], [0.13, 0.33], [0.29, 0.33], [0.29, 0.31], [0.45, 0.31], [0.45, 0.3], [0.61, 0.3], [0.61, 0.28], [0.77, 0.28], [0.77, 0.25], [0.93, 0.25], [0.93, 0.22], [1.09, 0.22], [1.09, 0.19], [1.25, 0.19], [1.25, 0.17], [1.41, 0.17], [1.41, 0.15], [1.57, 0.15], [1.57, 0.12], [1.73, 0.12], [1.73, 0.1], [1.89, 0.1], [1.89, 0.08], [2.05, 0.08], [2.05, 0.07], [2.21, 0.07], [2.21, 0.05], [2.37, 0.05], [2.37, 0.04], [2.53, 0.04], [2.53, 0.02], [2.69, 0.02], [2.69, 0.02], [2.85, 0.02], [2.85, 0.01], [3.01, 0.01], [3.01, 0.01], [3.17, 0.01], [3.17, 0.0], [3.33, 0.0], [3.33, 0.0], [3.49, 0.0], [3.49, 0.0], [3.65, 0.0], [3.65, 0.0], [3.81, 0.0], [3.81, 0.0], [3.97, 0.0], [3.97, 0.0], [4.13, 0.0], [4.13, 0.0], [4.29, 0.0], [4.29, 0.0], [4.45, 0.0], [4.45, 0.0], [4.61, 0.0], [4.61, 0.0], [4.77, 0.0], [4.77, 0.0], [4.93, 0.0], [4.93, 0.0]])
minx, maxx = np.min(verts[:,0]), np.max(verts[:,0])
miny, maxy = np.min(verts[:,1]), np.max(verts[:,1])

p = mpath.Path(verts)
fig, ax = plt.subplots()
ax.add_patch(mpatches.PathPatch(p))
ax.autoscale()
xlim = ax.get_xlim(); ylim = ax.get_ylim()
print("xlim", xlim, "ylim", ylim)
print("data extremes minx",minx,"maxx",maxx,"miny",miny,"maxy",maxy)
ok = (xlim[0] <= minx and xlim[1] >= maxx and ylim[0] <= miny and ylim[1] >= maxy)
print("ENCLOSES_ALL:", ok)
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance matplotlib__matplotlib-24177. Bug: Axes._update_patch_limits iterated p.iter_bezier() which forwards simplify=None -> path.should_simplify, so line-simplification dropped extreme vertices and autoscale clipped the artist. Gold fix: p.iter_bezier(simplify=False).

Probe suite (7 distinct, all HOLD on gold-patched tree):
- probe_1 (Req1.1/1.2, POSITIVE CONTROL): the #24097 132-vertex PathPatch reproducer; asserts autoscaled xlim/ylim enclose min/max of all defining points. HOLDS patched (ylim top 0.3465 >= maxy 0.33); FAILS at base (ylim top 0.2625 < 0.33) -> prepatch reproduced. Discriminates.
- probe_2 (Req1.4): Path(132 verts).iter_bezier(simplify=False) yields 132 bezier segments (== vertex count), vs 11 with default simplification. NOTE: this probe HOLDS at base too — iter_bezier already accepted **kwargs pre-fix, so it does not discriminate on its own; it documents the forwarding contract Req1.4 pins.
- probe_3 (Req1.3): tallest-bin y-extreme enclosed by autoscale. HOLDS patched, FAILS base — second discriminator.
- probe_4 (Req3.1): zero-width AND zero-height Rectangle far from data does NOT move limits (exclusion retained).
- probe_5 (Req2.1): cubic bezier with interior y-extremum (peak 1.5) framed to ylim top 1.575 — per-segment axis_aligned_extrema still collected.
- probe_6 (Req3.4): empty Path leaves data limits unchanged, no exception.
- probe_7 (Req4.2): two rectangles -> autoscaled limits enclose the union of extents.

Candidate wrong-fix (weak.diff): iter_bezier(simplify=True) — the lazy/naive reading that a weak spec might permit (keeps default-style simplification). Applies cleanly at base. Probe suite REJECTS it: probe_1 VIOLATED (ylim 0.2625 < 0.33), probe_3 VIOLATED. This demonstrates the suite discriminates a probe-non-conforming wrong implementation. No requirements-conforming alternative exists that leaves the bug: Req1.2/1.3 mandate enclosing the max-extent vertex, which by construction requires the unsimplified collection.

Conclusion: >=5 probes hold on patched, positive control discriminates (holds patched / fails base), and a plausible wrong fix is rejected. Requirements faithfully and not-too-weakly capture the gold behavior. SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 7 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 7 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py`, `probe_7.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

Counterexample / evidence:

```
none — no probe fails on the patched tree, and the requirements-permissive weak candidate is rejected by the suite
```

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
import sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.path as mpath

verts = np.array([[-5.45, 0.0], [-5.45, 0.0], [-5.29, 0.0], [-5.29, 0.0], [-5.13, 0.0], [-5.13, 0.0], [-4.97, 0.0], [-4.97, 0.0], [-4.81, 0.0], [-4.81, 0.0], [-4.65, 0.0], [-4.65, 0.0], [-4.49, 0.0], [-4.49, 0.0], [-4.33, 0.0], [-4.33, 0.0], [-4.17, 0.0], [-4.17, 0.0], [-4.01, 0.0], [-4.01, 0.0], [-3.85, 0.0], [-3.85, 0.0], [-3.69, 0.0], [-3.69, 0.0], [-3.53, 0.0], [-3.53, 0.0], [-3.37, 0.0], [-3.37, 0.0], [-3.21, 0.0], [-3.21, 0.01], [-3.05, 0.01], [-3.05, 0.01], [-2.89, 0.01], [-2.89, 0.01], [-2.73, 0.01], [-2.73, 0.02], [-2.57, 0.02], [-2.57, 0.04], [-2.41, 0.04], [-2.41, 0.04], [-2.25, 0.04], [-2.25, 0.06], [-2.09, 0.06], [-2.09, 0.08], [-1.93, 0.08], [-1.93, 0.1], [-1.77, 0.1], [-1.77, 0.12], [-1.61, 0.12], [-1.61, 0.14], [-1.45, 0.14], [-1.45, 0.17], [-1.3, 0.17], [-1.3, 0.19], [-1.14, 0.19], [-1.14, 0.22], [-0.98, 0.22], [-0.98, 0.25], [-0.82, 0.25], [-0.82, 0.27], [-0.66, 0.27], [-0.66, 0.29], [-0.5, 0.29], [-0.5, 0.3], [-0.34, 0.3], [-0.34, 0.32], [-0.18, 0.32], [-0.18, 0.33], [-0.02, 0.33], [-0.02, 0.32], [0.13, 0.32], [0.13, 0.33], [0.29, 0.33], [0.29, 0.31], [0.45, 0.31], [0.45, 0.3], [0.61, 0.3], [0.61, 0.28], [0.77, 0.28], [0.77, 0.25], [0.93, 0.25], [0.93, 0.22], [1.09, 0.22], [1.09, 0.19], [1.25, 0.19], [1.25, 0.17], [1.41, 0.17], [1.41, 0.15], [1.57, 0.15], [1.57, 0.12], [1.73, 0.12], [1.73, 0.1], [1.89, 0.1], [1.89, 0.08], [2.05, 0.08], [2.05, 0.07], [2.21, 0.07], [2.21, 0.05], [2.37, 0.05], [2.37, 0.04], [2.53, 0.04], [2.53, 0.02], [2.69, 0.02], [2.69, 0.02], [2.85, 0.02], [2.85, 0.01], [3.01, 0.01], [3.01, 0.01], [3.17, 0.01], [3.17, 0.0], [3.33, 0.0], [3.33, 0.0], [3.49, 0.0], [3.49, 0.0], [3.65, 0.0], [3.65, 0.0], [3.81, 0.0], [3.81, 0.0], [3.97, 0.0], [3.97, 0.0], [4.13, 0.0], [4.13, 0.0], [4.29, 0.0], [4.29, 0.0], [4.45, 0.0], [4.45, 0.0], [4.61, 0.0], [4.61, 0.0], [4.77, 0.0], [4.77, 0.0], [4.93, 0.0], [4.93, 0.0]])
minx, maxx = np.min(verts[:,0]), np.max(verts[:,0])
miny, maxy = np.min(verts[:,1]), np.max(verts[:,1])

p = mpath.Path(verts)
fig, ax = plt.subplots()
ax.add_patch(mpatches.PathPatch(p))
ax.autoscale()
xlim = ax.get_xlim(); ylim = ax.get_ylim()
print("xlim", xlim, "ylim", ylim)
print("data extremes minx",minx,"maxx",maxx,"miny",miny,"maxy",maxy)
ok = (xlim[0] <= minx and xlim[1] >= maxx and ylim[0] <= miny and ylim[1] >= maxy)
print("ENCLOSES_ALL:", ok)
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance matplotlib__matplotlib-24177. Bug: Axes._update_patch_limits iterated p.iter_bezier() which forwards simplify=None -> path.should_simplify, so line-simplification dropped extreme vertices and autoscale clipped the artist. Gold fix: p.iter_bezier(simplify=False).

Probe suite (7 distinct, all HOLD on gold-patched tree):
- probe_1 (Req1.1/1.2, POSITIVE CONTROL): the #24097 132-vertex PathPatch reproducer; asserts autoscaled xlim/ylim enclose min/max of all defining points. HOLDS patched (ylim top 0.3465 >= maxy 0.33); FAILS at base (ylim top 0.2625 < 0.33) -> prepatch reproduced. Discriminates.
- probe_2 (Req1.4): Path(132 verts).iter_bezier(simplify=False) yields 132 bezier segments (== vertex count), vs 11 with default simplification. NOTE: this probe HOLDS at base too — iter_bezier already accepted **kwargs pre-fix, so it does not discriminate on its own; it documents the forwarding contract Req1.4 pins.
- probe_3 (Req1.3): tallest-bin y-extreme enclosed by autoscale. HOLDS patched, FAILS base — second discriminator.
- probe_4 (Req3.1): zero-width AND zero-height Rectangle far from data does NOT move limits (exclusion retained).
- probe_5 (Req2.1): cubic bezier with interior y-extremum (peak 1.5) framed to ylim top 1.575 — per-segment axis_aligned_extrema still collected.
- probe_6 (Req3.4): empty Path leaves data limits unchanged, no exception.
- probe_7 (Req4.2): two rectangles -> autoscaled limits enclose the union of extents.

Candidate wrong-fix (weak.diff): iter_bezier(simplify=True) — the lazy/naive reading that a weak spec might permit (keeps default-style simplification). Applies cleanly at base. Probe suite REJECTS it: probe_1 VIOLATED (ylim 0.2625 < 0.33), probe_3 VIOLATED. This demonstrates the suite discriminates a probe-non-conforming wrong implementation. No requirements-conforming alternative exists that leaves the bug: Req1.2/1.3 mandate enclosing the max-extent vertex, which by construction requires the unsimplified collection.

Conclusion: >=5 probes hold on patched, positive control discriminates (holds patched / fails base), and a plausible wrong fix is rejected. Requirements faithfully and not-too-weakly capture the gold behavior. SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** One-line gold patch: `for curve, code in p.iter_bezier():` -> `p.iter_bezier(simplify=False)` in _AxesBase._update_patch_limits. Probes run via nl_attack on the instance image confirm patched-vs-base divergence on the F2P scenario (y clipping) and that iter_bezier(simplify=False) yields all segments. Requirements correctly identify both the mechanism (disable simplification during limit collection) and the observable effect (data limits enclose the full unsimplified path), and explicitly preserve the untouched surrounding rules. No requirement forbids present behavior, mandates absent behavior, or invents behavior.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The requirements localize the fix by naming legitimate modules/functions (_update_patch_limits, Path.iter_bezier, iter_segments, axis_aligned_extrema, update_datalim, lib/matplotlib/axes/_base.py) and translate behavior into acceptance criteria. Req 1.4 paraphrases the one-line gold edit (iter_bezier with simplification disabled forwarding to segment iteration), but uses only pre-existing matplotlib API/rcParams (simplify, should_simplify, path.simplify[_threshold]) — no fix-invented identifiers. Req 1.2 describes the class of inputs (many closely spaced, small-magnitude points) where the bug manifests behaviorally, not the verbatim vertex array. No test names (test_small_autoscale), test file paths (tests/test_axes.py), node ids, parametrization enumerations, or quoted test/gold code appear. The single FAIL_TO_PASS test is unparametrized, and nothing in the doc reconstructs its concrete vertices or assertions beyond describing the general autoscale-encloses-extent behavior. This is legitimate behavioral spec, not test transmission.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
