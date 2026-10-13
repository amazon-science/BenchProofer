# P2 adversarial audit — matplotlib__matplotlib-26466

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
# Positive control: Req 1.2/1.3 -- annotation anchor captured by value.
# Mutating the numpy array passed as xy after annotate() must NOT change ann.xy.
# HOLDS on patched tree, FAILS at base (where xy aliases the array).
import matplotlib
matplotlib.use("Agg")
import numpy as np
import matplotlib.pyplot as plt

fig, ax = plt.subplots()
xy = np.array([1.0, 2.0])
ann = ax.annotate("t", xy=xy, xytext=(5, 5), textcoords="offset points")
xy[1] = 999.0  # in-place mutation of the caller's array
stored = tuple(ann.xy)
print("stored ann.xy after mutation:", stored)
ok = (stored[0] == 1.0 and stored[1] == 2.0)
print("PASS" if ok else "FAIL")
raise SystemExit(0 if ok else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
# Req 1.2: stored anchor coordinate SHALL NOT alias the container.
# Even before any mutation, ann.xy must not BE the same numpy array object.
import matplotlib
matplotlib.use("Agg")
import numpy as np
import matplotlib.pyplot as plt

fig, ax = plt.subplots()
xy = np.array([3.0, 4.0])
ann = ax.annotate("t", xy=xy, xytext=(0, 0), textcoords="offset points")
aliased = ann.xy is xy
print("ann.xy is the passed array?", aliased, "type:", type(ann.xy))
# Must not alias. Confirm decoupling by mutation too.
xy[0] = -7.0
still = tuple(ann.xy)
print("after mutate xy[0]=-7:", still)
ok = (not aliased) and still[0] == 3.0 and still[1] == 4.0
print("PASS" if ok else "FAIL")
raise SystemExit(0 if ok else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
# Req 2.2/2.3: OffsetFrom reference coordinate captured by value; mutating the
# array after construction must not change the offset transform from __call__.
import matplotlib
matplotlib.use("Agg")
import numpy as np
from matplotlib.text import OffsetFrom
from matplotlib.transforms import IdentityTransform

class FakeRenderer:
    def points_to_pixels(self, v):
        return 2.0 * v

ref = np.array([10.0, 20.0])
of = OffsetFrom(IdentityTransform(), ref, unit="pixels")
# Snapshot transform translation before mutation
tr_before = of(FakeRenderer())
mtx_before = tr_before.get_matrix().copy()
ref[0] = 555.0
ref[1] = 666.0
tr_after = of(FakeRenderer())
mtx_after = tr_after.get_matrix()
print("matrix before:\n", mtx_before)
print("matrix after mutation:\n", mtx_after)
# translation entries at [0,2] and [1,2]
import numpy as _np
ok = _np.allclose(mtx_before, mtx_after) and mtx_after[0, 2] == 10.0 and mtx_after[1, 2] == 20.0
print("PASS" if ok else "FAIL")
raise SystemExit(0 if ok else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
# Req 3.2: OffsetFrom.__call__ SHALL scale by 1 for "pixels" and by
# renderer.points_to_pixels(1) otherwise, then translate by the ref point.
import matplotlib
matplotlib.use("Agg")
import numpy as np
from matplotlib.text import OffsetFrom
from matplotlib.transforms import IdentityTransform

class FakeRenderer:
    def points_to_pixels(self, v):
        return 1.5 * v

ref = (10.0, 20.0)
# points unit -> scale should be 1.5
of_pts = OffsetFrom(IdentityTransform(), ref, unit="points")
m_pts = of_pts(FakeRenderer()).get_matrix()
# pixels unit -> scale should be 1
of_px = OffsetFrom(IdentityTransform(), ref, unit="pixels")
m_px = of_px(FakeRenderer()).get_matrix()
print("points matrix:\n", m_pts)
print("pixels matrix:\n", m_px)
ok = (
    np.isclose(m_pts[0, 0], 1.5) and np.isclose(m_pts[1, 1], 1.5)
    and np.isclose(m_pts[0, 2], 10.0) and np.isclose(m_pts[1, 2], 20.0)
    and np.isclose(m_px[0, 0], 1.0) and np.isclose(m_px[1, 1], 1.0)
    and np.isclose(m_px[0, 2], 10.0) and np.isclose(m_px[1, 2], 20.0)
)
print("PASS" if ok else "FAIL")
raise SystemExit(0 if ok else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
# Req 1.4 / Req 3.1: stored anchor exposes two ordered components equal to the
# supplied coordinate; a tuple input works exactly as before (no regression).
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

fig, ax = plt.subplots()
ann = ax.annotate("t", xy=(7.5, -3.25), xytext=(0, 0), textcoords="offset points")
stored = tuple(ann.xy)
print("stored ann.xy for tuple input:", stored, "len:", len(ann.xy))
ok = len(ann.xy) == 2 and stored[0] == 7.5 and stored[1] == -3.25
# also drawing must work without error (positioning uses xy)
fig.canvas.draw()
print("draw succeeded")
print("PASS" if ok else "FAIL")
raise SystemExit(0 if ok else 1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
# Req 3.3: invalid xycoords spec SHALL still be rejected with same error type.
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

fig, ax = plt.subplots()
ann = ax.annotate("t", xy=(0, 0), xycoords="nonsense-coords",
                  xytext=(0, 0), textcoords="offset points")
raised = False
etype = None
try:
    fig.canvas.draw()
except Exception as e:
    raised = True
    etype = type(e).__name__
    print("raised:", etype, str(e)[:120])
print("raised?", raised)
ok = raised  # invalid coord system must still error
print("PASS" if ok else "FAIL")
raise SystemExit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
# Positive control: Req 1.2/1.3 -- annotation anchor captured by value.
# Mutating the numpy array passed as xy after annotate() must NOT change ann.xy.
# HOLDS on patched tree, FAILS at base (where xy aliases the array).
import matplotlib
matplotlib.use("Agg")
import numpy as np
import matplotlib.pyplot as plt

fig, ax = plt.subplots()
xy = np.array([1.0, 2.0])
ann = ax.annotate("t", xy=xy, xytext=(5, 5), textcoords="offset points")
xy[1] = 999.0  # in-place mutation of the caller's array
stored = tuple(ann.xy)
print("stored ann.xy after mutation:", stored)
ok = (stored[0] == 1.0 and stored[1] == 2.0)
print("PASS" if ok else "FAIL")
raise SystemExit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Requirements: capture annotation anchor (xy) and OffsetFrom ref_coord by value at construction so later in-place mutation of the caller's array does not move the annotation/offset. Gold patch unpacks `x, y = xy` / `x, y = ref_coord` and stores a fresh tuple.

Probes (all standalone, stdlib + matplotlib; each exits 0 iff criterion holds):
- probe_1 (Req 1.2/1.3, POSITIVE CONTROL): mutate numpy xy after annotate(); ann.xy must stay (1.0,2.0). PATCHED HOLDS; BASE FAILS (gets (1.0,999.0)).
- probe_2 (Req 1.2): ann.xy must not alias the passed array (`is` check) and stays decoupled. PATCHED HOLDS (tuple, not ndarray); BASE FAILS (aliases ndarray, becomes (-7.0,4.0)).
- probe_3 (Req 2.2/2.3, POSITIVE CONTROL): mutate numpy ref_coord after OffsetFrom(); __call__ transform translation must stay (10,20). PATCHED HOLDS; BASE FAILS (translation becomes 555,666).
- probe_4 (Req 3.2 regression): OffsetFrom.__call__ scales by 1 for 'pixels', by points_to_pixels(1) otherwise, then translates by ref. HOLDS on both trees (unchanged behavior).
- probe_5 (Req 1.4/3.1 regression): tuple input stored as 2 ordered components (7.5,-3.25); draw() succeeds. HOLDS both trees.
- probe_6 (Req 3.3 regression): invalid xycoords ('nonsense-coords') still raises ValueError at draw. HOLDS both trees.

Discrimination: positive controls (1,2,3) FAIL at base and HOLD patched. Regression probes (4,5,6) hold on both (they encode unchanged behavior, not the fix).

Candidate wrong patch (partial_fix_annotation_only / weak.diff): fixes only _AnnotationBase (snapshots xy) but leaves OffsetFrom storing ref_coord by reference. Applies cleanly at base. Result under this candidate: probe_1,2 HOLD (annotation fixed) but probe_3 is REJECTED (VIOLATED) — Req 2 unmet. This demonstrates the suite discriminates a plausibly-wrong partial fix; it is NOT reported as too-weak since a probe rejects it.

Verdict SOUND: >=5 distinct probes covering Req 1 (anchor by-value, no-alias, ordered components), Req 2 (OffsetFrom by-value + transform from snapshot), Req 3 (scale/translate semantics, tuple regression, invalid-coord rejection). All hold on patched tree; positive controls discriminate base vs patched; a requirements-partial candidate is rejected.

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
# Positive control: Req 1.2/1.3 -- annotation anchor captured by value.
# Mutating the numpy array passed as xy after annotate() must NOT change ann.xy.
# HOLDS on patched tree, FAILS at base (where xy aliases the array).
import matplotlib
matplotlib.use("Agg")
import numpy as np
import matplotlib.pyplot as plt

fig, ax = plt.subplots()
xy = np.array([1.0, 2.0])
ann = ax.annotate("t", xy=xy, xytext=(5, 5), textcoords="offset points")
xy[1] = 999.0  # in-place mutation of the caller's array
stored = tuple(ann.xy)
print("stored ann.xy after mutation:", stored)
ok = (stored[0] == 1.0 and stored[1] == 2.0)
print("PASS" if ok else "FAIL")
raise SystemExit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Requirements: capture annotation anchor (xy) and OffsetFrom ref_coord by value at construction so later in-place mutation of the caller's array does not move the annotation/offset. Gold patch unpacks `x, y = xy` / `x, y = ref_coord` and stores a fresh tuple.

Probes (all standalone, stdlib + matplotlib; each exits 0 iff criterion holds):
- probe_1 (Req 1.2/1.3, POSITIVE CONTROL): mutate numpy xy after annotate(); ann.xy must stay (1.0,2.0). PATCHED HOLDS; BASE FAILS (gets (1.0,999.0)).
- probe_2 (Req 1.2): ann.xy must not alias the passed array (`is` check) and stays decoupled. PATCHED HOLDS (tuple, not ndarray); BASE FAILS (aliases ndarray, becomes (-7.0,4.0)).
- probe_3 (Req 2.2/2.3, POSITIVE CONTROL): mutate numpy ref_coord after OffsetFrom(); __call__ transform translation must stay (10,20). PATCHED HOLDS; BASE FAILS (translation becomes 555,666).
- probe_4 (Req 3.2 regression): OffsetFrom.__call__ scales by 1 for 'pixels', by points_to_pixels(1) otherwise, then translates by ref. HOLDS on both trees (unchanged behavior).
- probe_5 (Req 1.4/3.1 regression): tuple input stored as 2 ordered components (7.5,-3.25); draw() succeeds. HOLDS both trees.
- probe_6 (Req 3.3 regression): invalid xycoords ('nonsense-coords') still raises ValueError at draw. HOLDS both trees.

Discrimination: positive controls (1,2,3) FAIL at base and HOLD patched. Regression probes (4,5,6) hold on both (they encode unchanged behavior, not the fix).

Candidate wrong patch (partial_fix_annotation_only / weak.diff): fixes only _AnnotationBase (snapshots xy) but leaves OffsetFrom storing ref_coord by reference. Applies cleanly at base. Result under this candidate: probe_1,2 HOLD (annotation fixed) but probe_3 is REJECTED (VIOLATED) — Req 2 unmet. This demonstrates the suite discriminates a plausibly-wrong partial fix; it is NOT reported as too-weak since a probe rejects it.

Verdict SOUND: >=5 distinct probes covering Req 1 (anchor by-value, no-alias, ordered components), Req 2 (OffsetFrom by-value + transform from snapshot), Req 3 (scale/translate semantics, tuple regression, invalid-coord rejection). All hold on patched tree; positive controls discriminate base vs patched; a requirements-partial candidate is rejected.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Patch: both _AnnotationBase.__init__ and OffsetFrom.__init__ now do `x,y = coord; store (x,y)` (by-value tuple snapshot); _get_scale inlined into __call__ with identical semantics. Requirements pin the changed observable behavior on BOTH constructors (not a narrow slice) and correctly preserve the refactored offset-transform behavior. Probe on gold-patched tree: HOLDS; on base: VIOLATED (aliasing). No mandated-but-absent, forbidden-but-present, wrong-boundary, or invented behavior.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** requirements.md describes behavior only. It names OffsetFrom, _AnnotationBase, Axes.annotate and lib/matplotlib/text.py — legitimate localization of the change (all are public API/scope of the gold edit); naming modules/functions is permitted. The by-value snapshot requirements translate what the test verifies into behavioral prose rather than transmitting the test. No hidden-test artifacts leak: no test name (test_annotate_and_offsetfrom_copy_input), no path, no parametrization id, no check_figures_equal reference, no test values (np.array([.5,.5]), of_xy[:]=1/an_xy[:]=2). The only concrete mutation example (xy_0[1]=3) comes verbatim from the PUBLIC problem_statement. Req 3.2 describes OffsetFrom.__call__'s scale/translate as PRESERVED existing behavior; it does not name the removed private helper _get_scale nor quote gold lines, and no fix-invented identifiers appear (the gold introduces only local x,y vars). No test-shaped enumeration. Coverage of OffsetFrom beyond the problem_statement is reasonable engineering inference about the aliasing bug's scope, not test reconstruction.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
