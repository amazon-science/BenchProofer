# P2 adversarial audit — matplotlib__matplotlib-26113

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
# Positive control. Req 1.1 & Req 4: with C supplied and integer mincnt=1,
# a cell whose point count is >= mincnt (here exactly 1) SHALL be included.
# Well-separated points => each lands in its own hex cell (count==1 each).
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

x = np.array([0., 10., 20., 30.])
y = np.array([0., 10., 20., 30.])
C = np.array([1., 2., 3., 4.])

fig, ax = plt.subplots()
pc = ax.hexbin(x, y, C=C, gridsize=20, mincnt=1)
n_with_C = len(pc.get_array())

fig2, ax2 = plt.subplots()
pc2 = ax2.hexbin(x, y, gridsize=20, mincnt=1)
n_no_C = len(pc2.get_array())

print(f"displayed cells with C={n_with_C}, without C={n_no_C}")
# Each of the 4 points is isolated => 4 single-point cells; all must show on both paths.
ok = (n_with_C == n_no_C) and (n_with_C == 4)
print("HOLDS" if ok else "FAILS")
raise SystemExit(0 if ok else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
# Req 1.2: cells with point count strictly less than mincnt SHALL be discarded.
# Use mincnt=2. A cell with exactly 1 point must be dropped; a cell with >=2 kept.
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

# cluster of 3 points near (0,0) -> one cell count 3; single isolated point at (50,50) -> count 1
x = np.array([0., 0.01, -0.01, 50.])
y = np.array([0., 0.01, -0.01, 50.])
C = np.array([1., 1., 1., 9.])
fig, ax = plt.subplots()
pc = ax.hexbin(x, y, C=C, gridsize=30, mincnt=2)
vals = np.asarray(pc.get_array())
print("kept cells with C, mincnt=2:", len(vals), "values:", sorted(vals.tolist()))
# The isolated single-point cell (count 1 < 2) must be dropped; only the cluster remains.
ok = (len(vals) == 1)
print("HOLDS" if ok else "FAILS")
raise SystemExit(0 if ok else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
# Req 1.3 & 1.5: cell with point count exactly == mincnt is included AND its value
# is exactly reduce_C_function applied to that cell's C values.
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
# Two coincident points -> guaranteed same cell -> count 2. mincnt=2 (exactly equal).
x = np.array([1., 1.])
y = np.array([1., 1.])
C = np.array([3., 7.])
for func, expected in [(np.mean,5.0),(np.sum,10.0),(np.max,7.0)]:
    fig, ax = plt.subplots()
    pc = ax.hexbin(x, y, C=C, gridsize=10, mincnt=2, extent=(0,2,0,2), reduce_C_function=func)
    vals = np.asarray(pc.get_array())
    plt.close(fig)
    print(f"func={func.__name__} kept={len(vals)} vals={vals.tolist()} expected~{expected}")
    if len(vals) != 1 or not np.isclose(vals[0], expected):
        print("FAILS"); raise SystemExit(1)
print("HOLDS"); raise SystemExit(0)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
# Req 4 (broader): for a range of point counts, the SET of displayed cells is identical
# with and without C, for integer mincnt>=1.
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

rng = np.random.RandomState(12345)
x = rng.rand(500)*10
y = rng.rand(500)*10
C = rng.rand(500)
for mincnt in [1,2,3,5]:
    fig,ax = plt.subplots()
    pc = ax.hexbin(x,y,C=C,gridsize=15,mincnt=mincnt,extent=(0,10,0,10))
    off_C = pc.get_offsets()
    plt.close(fig)
    fig,ax = plt.subplots()
    pc2 = ax.hexbin(x,y,gridsize=15,mincnt=mincnt,extent=(0,10,0,10))
    off_noC = pc2.get_offsets()
    plt.close(fig)
    sC = set(map(tuple, np.round(np.asarray(off_C),6).tolist()))
    sN = set(map(tuple, np.round(np.asarray(off_noC),6).tolist()))
    print(f"mincnt={mincnt}: |C|={len(sC)} |noC|={len(sN)} equal={sC==sN}")
    if sC != sN:
        print("FAILS"); raise SystemExit(1)
print("HOLDS"); raise SystemExit(0)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
# Req 2.1: no-C path with integer mincnt displays exactly cells with count>=mincnt (unchanged).
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
# cluster of 3, cluster of 2, single of 1
x = np.array([0.,0.005,-0.005, 20.,20.005, 50.])
y = np.array([0.,0.005,-0.005, 20.,20.005, 50.])
fig,ax=plt.subplots()
pc = ax.hexbin(x,y,gridsize=40,mincnt=2)
vals = np.asarray(pc.get_array())
print("no-C mincnt=2 kept:", len(vals), "counts:", sorted(vals.tolist()))
# should keep the count-3 and count-2 cells only => 2 cells, values {2,3}
ok = (len(vals)==2) and set(int(v) for v in vals)=={2,3}
print("HOLDS" if ok else "FAILS")
raise SystemExit(0 if ok else 1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
# Req 2.2: mincnt=None default. no-C path: every cell in grid shown incl count 0.
# C-path with None: reduce applied to every (possibly empty) cell; empty dropped only if reduce->NaN.
# With default reduce (np.mean), empty cell -> mean([]) = nan -> dropped. So C-path with None keeps
# only non-empty cells, same as ">=0" over non-empty. Also verify no-C shows empty cells (count 0).
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
x = np.array([0.,10.])
y = np.array([0.,10.])
# no-C, mincnt None => all grid cells displayed including zero-count ones
fig,ax=plt.subplots()
pc = ax.hexbin(x,y,gridsize=5,mincnt=None,extent=(0,10,0,10))
vals = np.asarray(pc.get_array())
nzero = int((vals==0).sum())
print("no-C None: total cells", len(vals), "zero-count cells", nzero)
plt.close(fig)
if nzero < 1:
    print("FAILS: expected empty cells displayed on no-C None path"); raise SystemExit(1)
# C-path None with default mean: empty cells reduce to nan -> dropped; kept == non-empty cells
fig,ax=plt.subplots()
pc2 = ax.hexbin(x,y,C=np.array([1.,2.]),gridsize=5,mincnt=None,extent=(0,10,0,10))
vals2 = np.asarray(pc2.get_array())
print("C None (mean): kept cells", len(vals2))
plt.close(fig)
ok = (len(vals2)==2)
print("HOLDS" if ok else "FAILS")
raise SystemExit(0 if ok else 1)
```

Attack 7 — `probe_7.py` → holds on the patched tree (good)

```python
# Req 2.2 (C-path, mincnt=None): reduce_C_function is applied to EVERY cell's
# (possibly empty) collection; an empty cell is omitted only when the reduction
# yields NaN. So with a reduce that maps empty->non-NaN (here len -> 0), empty
# cells within the grid MUST now appear on the C-supplied path.
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
x = np.array([0., 10.])
y = np.array([0., 10.])
C = np.array([1., 2.])
# no-C: number of grid cells displayed (all of them at None)
fig,ax=plt.subplots()
pc_noC = ax.hexbin(x,y,gridsize=5,mincnt=None,extent=(0,10,0,10))
n_noC = len(np.asarray(pc_noC.get_array())); plt.close(fig)
# C-path with reduce=len (empty->0, non-nan): should keep ALL cells too
fig,ax=plt.subplots()
pc_C = ax.hexbin(x,y,C=C,gridsize=5,mincnt=None,extent=(0,10,0,10),
                 reduce_C_function=len)
n_C = len(np.asarray(pc_C.get_array())); plt.close(fig)
print(f"None + reduce=len: no-C cells={n_noC}, C-path cells={n_C}")
# Empty cells must NOT be dropped on C-path since len([])=0 is non-nan.
ok = (n_C == n_noC) and (n_C > 2)
print("HOLDS" if ok else "FAILS")
raise SystemExit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
# Positive control. Req 1.1 & Req 4: with C supplied and integer mincnt=1,
# a cell whose point count is >= mincnt (here exactly 1) SHALL be included.
# Well-separated points => each lands in its own hex cell (count==1 each).
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

x = np.array([0., 10., 20., 30.])
y = np.array([0., 10., 20., 30.])
C = np.array([1., 2., 3., 4.])

fig, ax = plt.subplots()
pc = ax.hexbin(x, y, C=C, gridsize=20, mincnt=1)
n_with_C = len(pc.get_array())

fig2, ax2 = plt.subplots()
pc2 = ax2.hexbin(x, y, gridsize=20, mincnt=1)
n_no_C = len(pc2.get_array())

print(f"displayed cells with C={n_with_C}, without C={n_no_C}")
# Each of the 4 points is isolated => 4 single-point cells; all must show on both paths.
ok = (n_with_C == n_no_C) and (n_with_C == 4)
print("HOLDS" if ok else "FAILS")
raise SystemExit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Fix: C-path threshold `len(acc) > mincnt` -> `len(acc) >= mincnt` in Axes.hexbin (lib/matplotlib/axes/_axes.py). 7 probes cover the criteria: probe_1 (Req1.1/Req4 positive control: C-path includes count==mincnt=1 cells; identical displayed-cell count with/without C — HOLDS patched 4==4, FAILS base 0 vs 4). probe_2 (Req1.2: count<mincnt cells discarded, mincnt=2 drops the single-point cell). probe_3 (Req1.3/1.5: count==mincnt cell included with value == reduce_C_function over the cell's C values; checked mean/sum/max). probe_4 (Req4: displayed-cell SET identical with/without C across mincnt in {1,2,3,5} on 500-point random data). probe_5 (Req2.1: no-C path unchanged, mincnt=2 keeps only count>=2 cells). probe_6 (Req2.2: no-C None shows zero-count cells; C-path None with mean drops empty cells since mean([])=NaN). probe_7 (Req2.2 discriminating: C-path None with reduce=len keeps empty cells (len([])=0 non-NaN) -> all grid cells shown; HOLDS patched 28==28, FAILS base 2).

All 7 HOLD on patched tree. Positive control (probe_1) discriminates base(FAIL)/patched(HOLD). Weak candidate `weak.diff` (`len(acc) > mincnt - 1 and len(acc) > 0`) is equivalent to gold for integer mincnt>=1 but re-imposes the `>0` empty-cell drop on the None path, violating Req2.2 — REJECTED by probe_7 (C-path cells=2 vs expected 28) while passing probes 1-6. Suite discriminates a plausibly-wrong partial fix. Verdict SOUND: >=5 probes hold, positive control discriminates, >=1 candidate exercised and rejected.

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
# Positive control. Req 1.1 & Req 4: with C supplied and integer mincnt=1,
# a cell whose point count is >= mincnt (here exactly 1) SHALL be included.
# Well-separated points => each lands in its own hex cell (count==1 each).
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

x = np.array([0., 10., 20., 30.])
y = np.array([0., 10., 20., 30.])
C = np.array([1., 2., 3., 4.])

fig, ax = plt.subplots()
pc = ax.hexbin(x, y, C=C, gridsize=20, mincnt=1)
n_with_C = len(pc.get_array())

fig2, ax2 = plt.subplots()
pc2 = ax2.hexbin(x, y, gridsize=20, mincnt=1)
n_no_C = len(pc2.get_array())

print(f"displayed cells with C={n_with_C}, without C={n_no_C}")
# Each of the 4 points is isolated => 4 single-point cells; all must show on both paths.
ok = (n_with_C == n_no_C) and (n_with_C == 4)
print("HOLDS" if ok else "FAILS")
raise SystemExit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Fix: C-path threshold `len(acc) > mincnt` -> `len(acc) >= mincnt` in Axes.hexbin (lib/matplotlib/axes/_axes.py). 7 probes cover the criteria: probe_1 (Req1.1/Req4 positive control: C-path includes count==mincnt=1 cells; identical displayed-cell count with/without C — HOLDS patched 4==4, FAILS base 0 vs 4). probe_2 (Req1.2: count<mincnt cells discarded, mincnt=2 drops the single-point cell). probe_3 (Req1.3/1.5: count==mincnt cell included with value == reduce_C_function over the cell's C values; checked mean/sum/max). probe_4 (Req4: displayed-cell SET identical with/without C across mincnt in {1,2,3,5} on 500-point random data). probe_5 (Req2.1: no-C path unchanged, mincnt=2 keeps only count>=2 cells). probe_6 (Req2.2: no-C None shows zero-count cells; C-path None with mean drops empty cells since mean([])=NaN). probe_7 (Req2.2 discriminating: C-path None with reduce=len keeps empty cells (len([])=0 non-NaN) -> all grid cells shown; HOLDS patched 28==28, FAILS base 2).

All 7 HOLD on patched tree. Positive control (probe_1) discriminates base(FAIL)/patched(HOLD). Weak candidate `weak.diff` (`len(acc) > mincnt - 1 and len(acc) > 0`) is equivalent to gold for integer mincnt>=1 but re-imposes the `>0` empty-cell drop on the None path, violating Req2.2 — REJECTED by probe_7 (C-path cells=2 vs expected 28) while passing probes 1-6. Suite discriminates a plausibly-wrong partial fix. Verdict SOUND: >=5 probes hold, positive control discriminates, >=1 candidate exercised and rejected.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Patch: single line `len(acc) > mincnt` -> `len(acc) >= mincnt` in the C-supplied accum comprehension; cell kept iff not NaN via good_idxs=~np.isnan(accum). Req 1.1/1.2 correctly model the biconditional include/discard at the count boundary; Req 1.3 the equality case; Req 1.4 the cross-path identity for mincnt>=1 (verified 3==3). Req 1.5/2.3/2.4 (reduction value, positions/ordering, PolyCollection return) unaffected and consistent. Req 2.1 (no-C >= unchanged) verified 3 on both base and patched. Req 2.2 is the only subtle claim and it is precisely faithful: it correctly states the None->0 threshold now applies reduce_C_function to empty collections and omits a cell only when the reduction is NaN, and that empty cells newly appear when reduce maps empty->non-NaN (np.sum([])=0.0). Modeling boundary = the changed observable (displayed-cell set), pinned biconditionally, not a narrow branch/helper. Probes ran green on both --base and gold-patched trees.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The gold edit is a single-line threshold change `len(acc) > mincnt` -> `len(acc) >= mincnt` (with the pre-existing `if mincnt is None: mincnt = 0`). The requirements.md describes exactly this behavior, but every load-bearing fact is ALREADY PUBLIC in the problem_statement: (a) the >=-vs-> fix is stated verbatim in the issue's Resolution section ("i.e. `len(vals) >= mincnt`, rather than the current `len(vals) > mincnt`"); (b) the C-vs-no-C consistency goal and the mincnt=1 expected outcome are the issue's Expected outcome; (c) the mincnt=None->0 default and empty-cell behavior are general documented hexbin semantics visible in the surrounding code. No hidden-test content is transmitted: no test name (test_hexbin_mincnt_behavior_upon_C_parameter), file path, or parametrization id appears; none of the specific test fixture values (datapoints [(0,0),(0,0),(6,0),(0,6)], gridsize=(7,7), extent=[-10,10,-10,10], reduce_C_function=lambda v: sum(v), check_figures_equal) appear. Requirement 1.4 ('set of displayed cells identical whether or not C is supplied') restates the public expected outcome, not the test. Naming Axes.hexbin, lib/matplotlib/axes/_axes.py, reduce_C_function, mincnt, C, and PolyCollection is legitimate localization / public API vocabulary. The acceptance criteria are behavioral translations, not a mirror of the single (non-parametrized) test's cases.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
