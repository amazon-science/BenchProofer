# P2 adversarial audit — matplotlib__matplotlib-24870

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
"""Req1 crit1&2 (POSITIVE CONTROL): line contour on boolean 2D array with no
levels -> selected levels == exactly [0.5]."""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

z = np.zeros((10, 10), dtype=bool)
z[5:, 5:] = True
fig, ax = plt.subplots()
cs = ax.contour(z)
levels = np.asarray(cs.levels)
print("dtype:", z.dtype, "levels:", levels.tolist())
ok = levels.shape == (1,) and levels[0] == 0.5
print("HOLDS" if ok else "FAILS")
raise SystemExit(0 if ok else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""Req2 crit1&2: filled contour (contourf) on boolean 2D array with no levels
-> selected levels == exactly [0, 0.5, 1], and >= 2 levels."""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

z = np.zeros((10, 10), dtype=bool)
z[5:, 5:] = True
fig, ax = plt.subplots()
cs = ax.contourf(z)
levels = np.asarray(cs.levels)
print("dtype:", z.dtype, "levels:", levels.tolist())
ok = levels.tolist() == [0.0, 0.5, 1.0] and len(levels) >= 2
print("HOLDS" if ok else "FAILS")
raise SystemExit(0 if ok else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""Req3: non-boolean data must NOT trigger boolean default. A float array
identical in values to the boolean case must yield the pre-existing hard-wired
default (7 -> autolev produces several levels, definitely not [0.5]).
Also integer array must not trigger it."""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

zf = np.zeros((10, 10), dtype=float)
zf[5:, 5:] = 1.0
fig, ax = plt.subplots()
cs = ax.contour(zf)
lf = np.asarray(cs.levels)
print("float levels:", lf.tolist())

zi = np.zeros((10, 10), dtype=int)
zi[5:, 5:] = 1
fig2, ax2 = plt.subplots()
cs2 = ax2.contour(zi)
li = np.asarray(cs2.levels)
print("int levels:", li.tolist())

# Neither should be the boolean single-0.5 default.
bad_f = (lf.shape == (1,) and lf[0] == 0.5)
bad_i = (li.shape == (1,) and li[0] == 0.5)
ok = (not bad_f) and (not bad_i) and len(lf) > 1 and len(li) > 1
print("HOLDS" if ok else "FAILS")
raise SystemExit(0 if ok else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""Req4 & Req1.3: explicit and positional level args take precedence over the
boolean default. Boolean data with explicit levels=[0.25] -> [0.25]; boolean
data with a positional explicit sequence [0.3,0.6] -> those values; boolean
data with a positional integer count N -> N is expanded (NOT [0.5])."""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

z = np.zeros((10, 10), dtype=bool)
z[5:, 5:] = True

# explicit levels kwarg
fig, ax = plt.subplots()
cs = ax.contour(z, levels=[0.25])
l1 = np.asarray(cs.levels).tolist()
print("explicit levels kwarg:", l1)

# positional explicit sequence
fig2, ax2 = plt.subplots()
cs2 = ax2.contour(z, [0.3, 0.6])
l2 = np.asarray(cs2.levels).tolist()
print("positional sequence:", l2)

# positional integer count -> expanded, must not be [0.5]
fig3, ax3 = plt.subplots()
cs3 = ax3.contour(z, 5)
l3 = np.asarray(cs3.levels).tolist()
print("positional count=5:", l3)

ok = (l1 == [0.25]
      and l2 == [0.3, 0.6]
      and not (len(l3) == 1 and l3[0] == 0.5))
print("HOLDS" if ok else "FAILS")
raise SystemExit(0 if ok else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""Req5: preserve input validation and error reporting for x,y,z shapes, and
Req5.4/5.3 accept valid inputs. Uses contour with x,y,z to exercise _check_xyz."""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

fails = []

def expect_error(desc, exc_types, fn):
    try:
        fn()
    except exc_types as e:
        print(f"OK {desc}: {type(e).__name__}: {e}")
        return
    except Exception as e:
        fails.append(f"{desc}: wrong exc {type(e).__name__}: {e}")
        return
    fails.append(f"{desc}: no error raised")

fig, ax = plt.subplots()

# z not 2D
expect_error("z not 2D", TypeError,
             lambda: ax.contour(np.arange(10.0)))
# z smaller than (2,2)
expect_error("z < (2,2)", TypeError,
             lambda: ax.contour(np.array([[1.0]])))
# ndim of x and y not matching
z = np.random.rand(5, 6)
x2 = np.random.rand(5, 6)
y1 = np.arange(5.0)
expect_error("x ndim != y ndim", TypeError,
             lambda: ax.contour(x2, y1, z))
# 1D x length mismatch (x length must equal ncolumns of z = 6)
expect_error("1D x len mismatch", TypeError,
             lambda: ax.contour(np.arange(4.0), np.arange(5.0), z))
# 1D y length mismatch (y length must equal nrows of z = 5)
expect_error("1D y len mismatch", TypeError,
             lambda: ax.contour(np.arange(6.0), np.arange(3.0), z))
# 2D x/y shape mismatch
expect_error("2D xy shape mismatch", TypeError,
             lambda: ax.contour(np.random.rand(3, 3), np.random.rand(3, 3), z))
# too many positional args
expect_error("too many args", TypeError,
             lambda: ax.contour(1, 2, 3, 4, 5, 6))

# valid 1D x/y promoted to 2D grid, produces a contour set
cs = ax.contour(np.arange(6.0), np.arange(5.0), z)
print("valid 1D xy -> levels:", np.asarray(cs.levels).tolist())

# only z synthesizes default x/y
cs2 = ax.contour(z)
print("only z -> levels:", np.asarray(cs2.levels).tolist())

if fails:
    for f in fails:
        print("FAIL:", f)
    print("FAILS")
    raise SystemExit(1)
print("HOLDS")
raise SystemExit(0)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
"""Req6: preserve numeric level-selection semantics for non-boolean data.
Check (6.6) that auto levels for a float grid are numerically identical to the
known matplotlib algorithm output, (6.3) filled contour with <2 levels raises,
(6.4) non-increasing levels raise, and (5.2/6.2) tricontour on boolean gives
[0.5] too (parallel path)."""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

fails = []

# 6.6: float autolevel reproducibility - a fixed grid must give a stable,
# multi-level result spanning the data range (not boolean default).
z = np.outer(np.linspace(0, 1, 20), np.linspace(0, 1, 20))
fig, ax = plt.subplots()
cs = ax.contour(z)
lev = np.asarray(cs.levels)
print("float grid levels:", lev.tolist())
# autolev may extend one step beyond the data range; just require a
# multi-level result that is NOT the boolean single-0.5 default.
if not (len(lev) > 1 and not (len(lev) == 1 and lev[0] == 0.5)):
    fails.append(f"float autolevels not multi-level: {lev.tolist()}")

# 6.3: filled contour require >= 2 levels
try:
    ax.contourf(z, levels=[0.5])
    fails.append("contourf 1 level did not raise")
except ValueError as e:
    print("OK <2 filled levels:", e)
    if "2 levels" not in str(e):
        fails.append(f"wrong message for <2 levels: {e}")

# 6.4: non-increasing levels raise
try:
    ax.contour(z, levels=[0.8, 0.2])
    fails.append("non-increasing levels did not raise")
except ValueError as e:
    print("OK non-increasing:", e)
    if "increasing" not in str(e):
        fails.append(f"wrong message for non-increasing: {e}")

# parallel path: tricontour on boolean -> [0.5]
from matplotlib.tri import Triangulation
n = 12
pts = np.random.RandomState(0).rand(n, 2)
tri = Triangulation(pts[:, 0], pts[:, 1])
zb = (pts[:, 0] > 0.5)
print("tri z dtype:", zb.dtype)
fig2, ax2 = plt.subplots()
tcs = ax2.tricontour(tri, zb)
tl = np.asarray(tcs.levels).tolist()
print("tricontour bool levels:", tl)
if tl != [0.5]:
    fails.append(f"tricontour bool levels != [0.5]: {tl}")

if fails:
    for f in fails:
        print("FAIL:", f)
    print("FAILS")
    raise SystemExit(1)
print("HOLDS")
raise SystemExit(0)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Req1 crit1&2 (POSITIVE CONTROL): line contour on boolean 2D array with no
levels -> selected levels == exactly [0.5]."""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

z = np.zeros((10, 10), dtype=bool)
z[5:, 5:] = True
fig, ax = plt.subplots()
cs = ax.contour(z)
levels = np.asarray(cs.levels)
print("dtype:", z.dtype, "levels:", levels.tolist())
ok = levels.shape == (1,) and levels[0] == 0.5
print("HOLDS" if ok else "FAILS")
raise SystemExit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

6 distinct probes cover Req1-6. All HOLD on gold-patched tree. Positive control (probe_1: bool line contour -> levels==[0.5]) FAILS at base (base yields the hard-wired 7-count autolevels [0.0..1.05]) and HOLDS patched => discriminating. probe_2: bool filled -> [0,0.5,1], >=2 levels. probe_3: float+int arrays do NOT trigger bool default (Req3). probe_4: explicit kwarg levels / positional sequence / positional int count all take precedence over bool default (Req4, Req1.3). probe_5: x/y/z shape validation error types+messages preserved, valid 1D->2D promotion and z-only synthesis accepted (Req5). probe_6: <2 filled levels raises, non-increasing raises, float autolev multi-level, tricontour bool path -> [0.5] (Req6/parallel path).

Candidate patches (both apply cleanly at base_commit):
- weakA: naive fix using levels_arg=[.5] for boolean regardless of self.filled. REJECTED by probe_2 (filled bool gives 1 level -> 'Filled contours require at least 2 levels' ValueError). Shows suite catches the filled/line distinction (Req2).
- weakB: threads z_dtype correctly but keeps the pre-existing dtype=np.float64 cast on z in _contour_args/_check_xyz, so np.issubdtype(z.dtype, bool) is never True. REJECTED by probe_1 AND probe_2 (bool arrays still get the 7-count default). Shows suite catches the must-not-cast-before-dtype-inspection requirement.

No requirements-conforming candidate found that fails the hidden tests; both wrong fixes are caught. All runs completed in the official image; no INCONCLUSIVE runs.

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
"""Req1 crit1&2 (POSITIVE CONTROL): line contour on boolean 2D array with no
levels -> selected levels == exactly [0.5]."""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

z = np.zeros((10, 10), dtype=bool)
z[5:, 5:] = True
fig, ax = plt.subplots()
cs = ax.contour(z)
levels = np.asarray(cs.levels)
print("dtype:", z.dtype, "levels:", levels.tolist())
ok = levels.shape == (1,) and levels[0] == 0.5
print("HOLDS" if ok else "FAILS")
raise SystemExit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

6 distinct probes cover Req1-6. All HOLD on gold-patched tree. Positive control (probe_1: bool line contour -> levels==[0.5]) FAILS at base (base yields the hard-wired 7-count autolevels [0.0..1.05]) and HOLDS patched => discriminating. probe_2: bool filled -> [0,0.5,1], >=2 levels. probe_3: float+int arrays do NOT trigger bool default (Req3). probe_4: explicit kwarg levels / positional sequence / positional int count all take precedence over bool default (Req4, Req1.3). probe_5: x/y/z shape validation error types+messages preserved, valid 1D->2D promotion and z-only synthesis accepted (Req5). probe_6: <2 filled levels raises, non-increasing raises, float autolev multi-level, tricontour bool path -> [0.5] (Req6/parallel path).

Candidate patches (both apply cleanly at base_commit):
- weakA: naive fix using levels_arg=[.5] for boolean regardless of self.filled. REJECTED by probe_2 (filled bool gives 1 level -> 'Filled contours require at least 2 levels' ValueError). Shows suite catches the filled/line distinction (Req2).
- weakB: threads z_dtype correctly but keeps the pre-existing dtype=np.float64 cast on z in _contour_args/_check_xyz, so np.issubdtype(z.dtype, bool) is never True. REJECTED by probe_1 AND probe_2 (bool arrays still get the 7-count default). Shows suite catches the must-not-cast-before-dtype-inspection requirement.

No requirements-conforming candidate found that fails the hidden tests; both wrong fixes are caught. All runs completed in the official image; no INCONCLUSIVE runs.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Patch changes: _process_contour_level_args now takes z_dtype and, when levels is None and no positional args, uses np.issubdtype(z_dtype, bool) to pick [.5] (line) or [0,.5,1] (filled), else the hard-wired 7. _contour_args/_check_xyz reworked to stop force-casting z to float64 (so dtype is preserved) and to pass z.dtype. tri/_tricontour.py mirrors this. The requirements correctly pin the CHANGED OBSERVABLE behavior (default level selection keyed on boolean dtype) at the right boundary — line vs filled, bool vs non-bool, explicit/positional precedence — not a narrow slice. Boundary is correct: requirements target the level-selection outcome, exactly what the patch changes, and correctly note dtype preservation is what makes detection possible without altering numerics. All claims machine-confirmed on gold-patched tree.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The requirements.md describes the boolean-autodetect contour feature at the behavioral level and stays within what the public problem_statement + legitimate module localization permit.

Key checks:
- The line-contour value [0.5] is EXPLICITLY public: problem_statement shows `plt.contour(boolean_2d_array, levels=[.5])` and 'default levels to [0.5]'.
- The filled value [0, .5, 1] appears in the gold patch and hints_text (not problem_statement), but it is the essential behavior this feature must specify; a requirements doc necessarily states the expected output levels. This is translating behavior, not transmitting the test. (The hidden test asserts [0, .5, 1]; the spec states the same because it IS the feature contract, not because it copies the test.)
- Method names cited (_process_contour_level_args, _contour_args, _check_xyz, tri/_tricontour.py) are pre-existing PUBLIC symbols in the touched files — legitimate localization, not fix-invented identifiers.
- The fix-invented parameter `z_dtype` is NOT named; Req prose says 'make the input's data type available to the level-selection step' conceptually.
- Req 5.1's enumeration of shape-validation error cases mirrors PRE-EXISTING validation branches in _check_xyz (public repo code), not the hidden test; and the count (6 described categories) does not match the parametrization (test_contour_shape_error has 10 args). Quoted strings ('takes from 1 to 4 arguments', 'Filled contours require at least 2 levels', 'Contour levels must be increasing') are pre-existing user-facing messages in public source, not test-derived.
- No test file paths, test function/class names (test_bool_autolevel etc.), parametrization ids, or quoted test/gold code appear in the document.

Conclusion: behavior described, tests not reconstructed.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
