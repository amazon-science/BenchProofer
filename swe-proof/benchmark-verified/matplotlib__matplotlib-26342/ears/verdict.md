# P2 adversarial audit — matplotlib__matplotlib-26342

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
"""Req1.1 + Req1.3 (positive control): base Collection.set_paths stores the
supplied list and does NOT raise NotImplementedError. get_paths returns it."""
import sys
from matplotlib.collections import Collection
from matplotlib.path import Path

c = Collection()
paths = [Path([[0, 0], [1, 1]]), Path([[2, 2], [3, 3]])]
try:
    c.set_paths(paths)
except NotImplementedError:
    print("FAIL: set_paths raised NotImplementedError")
    sys.exit(1)
got = c.get_paths()
print("get_paths returned same object:", got is paths)
if got is not paths:
    print("FAIL: get_paths did not return the exact supplied list")
    sys.exit(1)
print("PASS")
sys.exit(0)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""Req1.2: set_paths marks the collection stale (stale flag True)."""
import sys
from matplotlib.collections import Collection
from matplotlib.path import Path

c = Collection()
c.stale = False
c.set_paths([Path([[0, 0], [1, 1]])])
print("stale after set_paths:", c.stale)
if c.stale is not True:
    print("FAIL: stale not set True")
    sys.exit(1)
print("PASS")
sys.exit(0)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""Req1.4: set_paths leaves other state (offsets, transforms, colors) unchanged."""
import sys
import numpy as np
from matplotlib.collections import Collection
from matplotlib.path import Path

c = Collection(offsets=[[5, 6]])
fc = c.get_facecolor().copy()
offs = c.get_offsets().copy()
trans = c.get_transforms().copy()
c.set_paths([Path([[0, 0], [1, 1]])])
ok = (np.array_equal(c.get_facecolor(), fc)
      and np.array_equal(c.get_offsets(), offs)
      and np.array_equal(c.get_transforms(), trans))
print("facecolor unchanged:", np.array_equal(c.get_facecolor(), fc))
print("offsets unchanged:", np.array_equal(c.get_offsets(), offs))
print("transforms unchanged:", np.array_equal(c.get_transforms(), trans))
if not ok:
    print("FAIL: other state changed")
    sys.exit(1)
print("PASS")
sys.exit(0)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""Req2.1 + Req2.3: ContourSet (a Collection subclass) adopts supplied paths
wholesale via set_paths; get_paths returns exactly those, replacing prior."""
import sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

fig, ax = plt.subplots()
z = np.random.default_rng(0).random((10, 10))
cs1 = ax.contour(z)
fig2, ax2 = plt.subplots()
cs2 = ax2.contour(z + 5)

new_paths = cs2.get_paths()
old = cs1.get_paths()
cs1.set_paths(new_paths)
got = cs1.get_paths()
print("get_paths is supplied list:", got is new_paths)
print("replaced (not old):", got is not old)
if got is not new_paths:
    print("FAIL: contour set_paths did not adopt supplied list")
    sys.exit(1)
print("PASS")
sys.exit(0)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""Req3.1: PathCollection.set_paths still works: supplied paths become stored
paths, collection marked stale (regression preservation)."""
import sys
from matplotlib.collections import PathCollection
from matplotlib.path import Path

pc = PathCollection([Path([[0, 0], [1, 1]])])
pc.stale = False
newp = [Path([[9, 9], [8, 8]])]
pc.set_paths(newp)
print("get_paths is supplied:", pc.get_paths() is newp)
print("stale:", pc.stale)
if pc.get_paths() is not newp or pc.stale is not True:
    print("FAIL")
    sys.exit(1)
print("PASS")
sys.exit(0)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
"""Req2.2 + Req2.3: installing a replacement path list via set_paths is
equivalent to the in-place `get_paths()[:] = replacement` assignment. Two
identically-constructed contour artists get the same replacement paths, one
through set_paths and one through the legacy in-place idiom; their rendered
output must be byte-identical (visible geometry fully determined by installed
paths)."""
import sys
import io
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

rng = np.random.default_rng(1)
z = rng.random((20, 20))
# replacement geometry, taken from a contour of a shifted field
figSrc, axSrc = plt.subplots()
csSrc = axSrc.contour(z + 3)
replacement = list(csSrc.get_paths())


def render(build):
    fig, ax = plt.subplots()
    ax.set_axis_off()
    cs = ax.contour(z)
    build(cs)
    buf = io.BytesIO()
    fig.canvas.draw()
    fig.savefig(buf, format="png")
    plt.close(fig)
    return buf.getvalue()

img_setpaths = render(lambda cs: cs.set_paths(list(replacement)))
img_inplace = render(lambda cs: cs.get_paths().__setitem__(slice(None), list(replacement)))

same = img_setpaths == img_inplace
print("set_paths render == in-place-assignment render:", same)
if not same:
    print("FAIL: set_paths not equivalent to get_paths()[:] = replacement")
    sys.exit(1)
print("PASS")
sys.exit(0)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Req1.1 + Req1.3 (positive control): base Collection.set_paths stores the
supplied list and does NOT raise NotImplementedError. get_paths returns it."""
import sys
from matplotlib.collections import Collection
from matplotlib.path import Path

c = Collection()
paths = [Path([[0, 0], [1, 1]]), Path([[2, 2], [3, 3]])]
try:
    c.set_paths(paths)
except NotImplementedError:
    print("FAIL: set_paths raised NotImplementedError")
    sys.exit(1)
got = c.get_paths()
print("get_paths returned same object:", got is paths)
if got is not paths:
    print("FAIL: get_paths did not return the exact supplied list")
    sys.exit(1)
print("PASS")
sys.exit(0)
```

Prepatch bug re-encoded as an attack: `True`.

matplotlib-26342: gold patch makes base Collection.set_paths(paths) set self._paths=paths; self.stale=True (removing NotImplementedError stub) and removes PathCollection's now-redundant override.

Probes (all HOLD on gold-patched tree):
- probe_1 (Req1.1+1.3, POSITIVE CONTROL): base Collection.set_paths stores the exact supplied list, get_paths returns same object, no NotImplementedError. HOLDS patched, FAILS at base (raises NotImplementedError) -> discriminating.
- probe_2 (Req1.2): set_paths sets stale=True. HOLDS patched.
- probe_3 (Req1.4): set_paths leaves offsets/transforms/facecolor unchanged. HOLDS.
- probe_4 (Req2.1+2.3): ContourSet subclass adopts supplied path list wholesale via inherited set_paths; get_paths returns exactly it, replacing prior. HOLDS patched, FAILS at base.
- probe_5 (Req3.1): PathCollection.set_paths still stores supplied paths and marks stale after override removal (regression). HOLDS.
- probe_6 (Req2.2+2.3): rendering a contour after set_paths(replacement) is byte-identical to rendering after the legacy get_paths()[:]=replacement idiom. HOLDS.

Candidate wrong-fix: weak_nostale.diff sets self._paths=paths but omits self.stale=True (a partial fix a lax reading permits). REJECTED by probe_2 (stale=False observed). Demonstrates the suite discriminates: probe_2 uniquely catches the missing staleness flag; probes 1/3/4/5/6 still hold under it.

All needed runs completed. 6 probes hold patched; positive control discriminates (patched pass / base fail); >=1 candidate exercised and rejected. Verdict SOUND.

Note: initial probe_6 used cross-style byte equality (different levels/colors) which was over-specification and falsely 'violated'; re-encoded faithfully as set_paths-vs-in-place-assignment equivalence per Req2.3, which holds.

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
"""Req1.1 + Req1.3 (positive control): base Collection.set_paths stores the
supplied list and does NOT raise NotImplementedError. get_paths returns it."""
import sys
from matplotlib.collections import Collection
from matplotlib.path import Path

c = Collection()
paths = [Path([[0, 0], [1, 1]]), Path([[2, 2], [3, 3]])]
try:
    c.set_paths(paths)
except NotImplementedError:
    print("FAIL: set_paths raised NotImplementedError")
    sys.exit(1)
got = c.get_paths()
print("get_paths returned same object:", got is paths)
if got is not paths:
    print("FAIL: get_paths did not return the exact supplied list")
    sys.exit(1)
print("PASS")
sys.exit(0)
```

Prepatch bug re-encoded as an attack: `True`.

matplotlib-26342: gold patch makes base Collection.set_paths(paths) set self._paths=paths; self.stale=True (removing NotImplementedError stub) and removes PathCollection's now-redundant override.

Probes (all HOLD on gold-patched tree):
- probe_1 (Req1.1+1.3, POSITIVE CONTROL): base Collection.set_paths stores the exact supplied list, get_paths returns same object, no NotImplementedError. HOLDS patched, FAILS at base (raises NotImplementedError) -> discriminating.
- probe_2 (Req1.2): set_paths sets stale=True. HOLDS patched.
- probe_3 (Req1.4): set_paths leaves offsets/transforms/facecolor unchanged. HOLDS.
- probe_4 (Req2.1+2.3): ContourSet subclass adopts supplied path list wholesale via inherited set_paths; get_paths returns exactly it, replacing prior. HOLDS patched, FAILS at base.
- probe_5 (Req3.1): PathCollection.set_paths still stores supplied paths and marks stale after override removal (regression). HOLDS.
- probe_6 (Req2.2+2.3): rendering a contour after set_paths(replacement) is byte-identical to rendering after the legacy get_paths()[:]=replacement idiom. HOLDS.

Candidate wrong-fix: weak_nostale.diff sets self._paths=paths but omits self.stale=True (a partial fix a lax reading permits). REJECTED by probe_2 (stale=False observed). Demonstrates the suite discriminates: probe_2 uniquely catches the missing staleness flag; probes 1/3/4/5/6 still hold under it.

All needed runs completed. 6 probes hold patched; positive control discriminates (patched pass / base fail); >=1 candidate exercised and rejected. Verdict SOUND.

Note: initial probe_6 used cross-style byte equality (different levels/colors) which was over-specification and falsely 'violated'; re-encoded faithfully as set_paths-vs-in-place-assignment equivalence per Req2.3, which holds.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Requirements pin the changed observable behavior at the correct boundary (base method promoted stub->impl + subclass inheritance), not a narrow slice. R2.2 (render-equivalence when copying paths from another contour artist) matches the FAIL_TO_PASS image-comparison test. Verified base-vs-patched divergence via nl_attack probes: base ContourSet.set_paths raises NotImplementedError, patched works.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The document names only public/pre-existing identifiers: Collection, PathCollection, ContourSet, set_paths, get_paths, and the public `stale` artist attribute. All appear in or are directly derivable from the public problem_statement, which itself quotes both the `cs.get_paths()[:] = transformed_paths` idiom and the desired `cs.set_paths(transformed_paths)` API. No test names/paths (test_contour_set_paths, test_contour.py), no parametrization ids, no quoted test code, and no test-specific data (the [[0,1],[1,2]] / [[1,0],[2,1]] contour inputs, check_figures_equal harness) are transmitted. The gold edit invents no new identifiers — it just sets self._paths and self.stale in the base method — so there is nothing fix-invented to leak. Requirement 2.2 ('rendering the receiving artist equals rendering the source artist after set_paths') is a legitimate behavioral translation of the check_figures_equal test's intent, describing observable behavior rather than reconstructing the test. Requirement 3 lists preserved contour behaviors (construction, labeling, shape-validation) which mirror the PASS_TO_PASS surface conceptually but are generic no-regression prose, not an enumeration of specific parametrized case ids. No semantic leak beyond the public problem statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
