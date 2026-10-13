# P2 adversarial audit — matplotlib__matplotlib-14623

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 requirement probes hold on the patched tree; 2/2 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 8 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 8 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py`, `probe_7.py`, `probe_8.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 2 alternative candidate patches, claimed to satisfy every cited requirement, and ran the same suite against them. The suite rejected all 2: a probe encoding a cited requirement fails under each of those, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (8):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
# Req 1.2 (POSITIVE CONTROL): log y-axis, decreasing order stays descending.
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

fig, ax = plt.subplots()
ax.set_yscale("log")
ax.set_ylim(10, 1)
lim = ax.get_ylim()
print("log set_ylim(10,1) -> get_ylim() =", lim)
ok = lim == (10, 1)
print("HOLDS" if ok else "FAILS")
import sys; sys.exit(0 if ok else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
# Req 1.1 & 1.3: linear axis, decreasing stays descending, increasing stays ascending.
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

fig, ax = plt.subplots()
ax.set_xlim(5, -3)   # decreasing
ax.set_ylim(-3, 5)   # increasing
xl = ax.get_xlim(); yl = ax.get_ylim()
print("set_xlim(5,-3) -> ", xl)
print("set_ylim(-3,5) -> ", yl)
ok = xl == (5, -3) and yl == (-3, 5)
print("HOLDS" if ok else "FAILS")
import sys; sys.exit(0 if ok else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
# Req 1.4: committed pair magnitudes are exactly those from nonsingular+limit_range_for_scale,
# only the order is adjusted. Use a log axis with decreasing order; the magnitudes should equal
# the sorted (increasing) result, just reversed. We compare set of magnitudes.
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

fig, ax = plt.subplots()
ax.set_yscale("log")
ax.set_ylim(1000, 5)
lim = ax.get_ylim()
print("log set_ylim(1000,5) -> get_ylim() =", lim)
# descending order preserved, magnitudes unchanged (non-degenerate, positive)
ok = lim == (1000, 5)
print("HOLDS" if ok else "FAILS")
import sys; sys.exit(0 if ok else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
# Req 1.5: 3-D setters preserve descending direction on any scale.
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D  # noqa

fig = plt.figure()
ax = fig.add_subplot(111, projection="3d")
ax.set_xlim3d(4, -2)
ax.set_ylim3d(9, 3)
ax.set_zlim3d(100, 1)
xl = ax.get_xlim3d(); yl = ax.get_ylim3d(); zl = ax.get_zlim3d()
print("xlim3d(4,-2)->", xl, " ylim3d(9,3)->", yl, " zlim3d(100,1)->", zl)
ok = xl == (4, -2) and yl == (9, 3) and zl == (100, 1)
print("HOLDS" if ok else "FAILS")
import sys; sys.exit(0 if ok else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
# Req 2.1/2.2: base Locator.nonsingular returns endpoints in increasing order,
# for a descending pair reordered ascending; non-degenerate magnitudes preserved.
import matplotlib.ticker as mticker

r1 = mticker.Locator().nonsingular(10, 1)
r2 = mticker.Locator().nonsingular(1, 10)
r3 = mticker.Locator().nonsingular(-2.0, 7.0)
print("nonsingular(10,1)=", r1)
print("nonsingular(1,10)=", r2)
print("nonsingular(-2,7)=", r3)
ok = (tuple(r1) == (1, 10)) and (tuple(r2) == (1, 10)) and (tuple(r3) == (-2.0, 7.0))
print("HOLDS" if ok else "FAILS")
import sys; sys.exit(0 if ok else 1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
# Req 2.3/2.4 & Req 3.1: nonsingular expands a degenerate range into distinct increasing
# endpoints; and set_ylim on equal endpoints warns and commits a non-empty expanded interval.
import warnings
import matplotlib
matplotlib.use("Agg")
import matplotlib.ticker as mticker
import matplotlib.pyplot as plt

# degenerate range through the base locator -> distinct, increasing
d = mticker.Locator().nonsingular(5.0, 5.0)
print("nonsingular(5,5)=", d)
distinct_incr = d[0] < d[1]

# set_ylim identical endpoints: warn + non-empty
fig, ax = plt.subplots()
with warnings.catch_warnings(record=True) as w:
    warnings.simplefilter("always")
    ax.set_ylim(3, 3)
    lim = ax.get_ylim()
    msgs = [str(x.message) for x in w]
warned = any("singular transformations" in m and "expanding" in m for m in msgs)
nonempty = lim[0] != lim[1]
print("set_ylim(3,3)->", lim, " warned=", warned)
ok = distinct_incr and warned and nonempty
print("HOLDS" if ok else "FAILS")
import sys; sys.exit(0 if ok else 1)
```

Attack 7 — `probe_7.py` → holds on the patched tree (good)

```python
# Req 3.2 & 3.3: non-positive limit on log axis warned & ignored (keeps prior);
# None reuses current limit for that endpoint.
import warnings
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

fig, ax = plt.subplots()
ax.set_yscale("log")
ax.set_ylim(1, 100)  # establish
before = ax.get_ylim()
with warnings.catch_warnings(record=True) as w:
    warnings.simplefilter("always")
    ax.set_ylim(-5, 100)  # invalid lower on log
    lim = ax.get_ylim()
    msgs = [str(x.message) for x in w]
print("before=", before, " after set_ylim(-5,100)=", lim)
warned = any("nonpositive" in m.lower() or "non-positive" in m.lower() or "log" in m.lower() for m in msgs)
kept_low = lim[0] == before[0]  # invalid bottom ignored, keep prior bottom

# None reuse
fig2, ax2 = plt.subplots()
ax2.set_ylim(2, 8)
ax2.set_ylim(None, 20)  # bottom reused
lim2 = ax2.get_ylim()
print("set_ylim(None,20) after (2,8) ->", lim2, " warned_nonpos=", warned)
reuse = lim2[0] == 2 and lim2[1] == 20
ok = warned and kept_low and reuse
print("HOLDS" if ok else "FAILS")
import sys; sys.exit(0 if ok else 1)
```

Attack 8 — `probe_8.py` → holds on the patched tree (good)

```python
# Req 3.4: shared axes propagation + returns committed pair.
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

fig, (ax1, ax2) = plt.subplots(1, 2, sharey=True)
ret = ax1.set_ylim(7, -1, emit=True)
print("returned=", ret, " sibling get_ylim=", ax2.get_ylim())
ok = ret == (7, -1) and ax2.get_ylim() == (7, -1)
print("HOLDS" if ok else "FAILS")
import sys; sys.exit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
# Req 1.2 (POSITIVE CONTROL): log y-axis, decreasing order stays descending.
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

fig, ax = plt.subplots()
ax.set_yscale("log")
ax.set_ylim(10, 1)
lim = ax.get_ylim()
print("log set_ylim(10,1) -> get_ylim() =", lim)
ok = lim == (10, 1)
print("HOLDS" if ok else "FAILS")
import sys; sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

8 probes, all HOLD on the gold-patched tree; three (probe_1, probe_3, probe_5) also serve as positive controls and FAIL at base, so the suite has discriminating power.

Coverage vs requirements:
- probe_1 (Req 1.2, POSITIVE CONTROL): log y-axis set_ylim(10,1) -> get_ylim()==(10,1). HOLDS patched, FAILS base ((1,10)).
- probe_2 (Req 1.1/1.3): linear set_xlim(5,-3)->(5,-3) [descending kept], set_ylim(-3,5)->(-3,5) [ascending kept]. HOLDS patched; also HOLDS base (linear was never broken).
- probe_3 (Req 1.4, extra positive control): log set_ylim(1000,5)->(1000,5), magnitudes preserved, only order restored. HOLDS patched, FAILS base ((5,1000)).
- probe_4 (Req 1.5): 3-D set_xlim3d/ylim3d/zlim3d descending preserved. HOLDS patched; HOLDS base (base 3D setters didn't reorder — they never called the sorting path meaningfully here).
- probe_5 (Req 2.1/2.2, positive control): base Locator().nonsingular reorders descending pair ascending, preserves non-degenerate magnitudes. HOLDS patched ((1,10)/(1,10)/(-2,7)), FAILS base ((10,1) — increasing=False preserved order).
- probe_6 (Req 2.3/2.4 & 3.1): degenerate nonsingular(5,5)->distinct increasing; set_ylim(3,3) warns 'singular transformations...expanding' and commits non-empty. HOLDS both trees.
- probe_7 (Req 3.2/3.3): non-positive limit on log warned & ignored (prior kept); None reuses current endpoint. HOLDS both trees.
- probe_8 (Req 3.4): shared-axis propagation + returns committed (bottom,top) pair, descending preserved. HOLDS patched, FAILS base direction ((-1,7)).

### CANDIDATE PATCHES (both REJECTED by the suite — floor satisfied):
- weak_ticker_only.diff: only the ticker.py hunk (drop increasing=False from Locator.nonsingular) WITHOUT the set_xlim/ylim swapped-restore logic. REJECTED by probe_1 (log (1,10)), probe_2 (linear now (-3,5)!), probe_3, probe_4, probe_8. This is the naive/partial fix a weak reading permits; it also REGRESSES linear inversion, so the suite catches it decisively.
- weak_no3d.diff: gold 2-D + ticker hunks but OMITS the mpl_toolkits/mplot3d/axes3d.py hunks. REJECTED by probe_4 (3D setters come out ascending). Confirms Req 1.5 (3-D) is discriminating.

NOTE on the prior recorded G-EQ/G-PANEL-1 VIOLATION (probe_4 in a previous audit): almost certainly a probe bug, not a real spec violation. I reproduced the identical failure mode: calling matplotlib.ticker.LogLocator().nonsingular(10,1) directly (no attached axis) raises AttributeError "'NoneType' object has no attribute 'get_minpos'" — LogLocator overrides nonsingular and needs self.axis. The base Locator.nonsingular (the one Req 2 actually names) behaves exactly as the spec mandates on both trees. Every requirement-mandated behavior, exercised through the public API on a real axis, HOLDS on the gold-patched tree. G-PANEL-2's 'unfaithful' note is also mistaken: Req 2 explicitly concerns the base Locator.nonsingular (used by log/default locators via inheritance), which the patch does change from increasing=False to default sorting — precisely what the spec describes.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 requirement probes hold on the patched tree; 2/2 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 8 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 8 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py`, `probe_7.py`, `probe_8.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 2 alternative candidate patches, claimed to satisfy every cited requirement, and ran the same suite against them. The suite rejected all 2: a probe encoding a cited requirement fails under each of those, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (8):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts, and on this backend both roles put it through the same derivation: every block below is a requirement probe run on the gold-patched tree, and the `machine verdict:` line each role publishes above reports BOTH that its probes hold there and how many candidate patches the probe suite rejected — so the two roles re-ran ONE probe suite and each recorded its own outcome for every probe in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `probe_1.py` → holds on the patched tree (good)

Attack 2 — `probe_2.py` → holds on the patched tree (good)

Attack 3 — `probe_3.py` → holds on the patched tree (good)

Attack 4 — `probe_4.py` → holds on the patched tree (good)

Attack 5 — `probe_5.py` → holds on the patched tree (good)

Attack 6 — `probe_6.py` → holds on the patched tree (good)

Attack 7 — `probe_7.py` → holds on the patched tree (good)

Attack 8 — `probe_8.py` → holds on the patched tree (good)

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
# Req 1.2 (POSITIVE CONTROL): log y-axis, decreasing order stays descending.
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

fig, ax = plt.subplots()
ax.set_yscale("log")
ax.set_ylim(10, 1)
lim = ax.get_ylim()
print("log set_ylim(10,1) -> get_ylim() =", lim)
ok = lim == (10, 1)
print("HOLDS" if ok else "FAILS")
import sys; sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

8 probes, all HOLD on the gold-patched tree; three (probe_1, probe_3, probe_5) also serve as positive controls and FAIL at base, so the suite has discriminating power.

Coverage vs requirements:
- probe_1 (Req 1.2, POSITIVE CONTROL): log y-axis set_ylim(10,1) -> get_ylim()==(10,1). HOLDS patched, FAILS base ((1,10)).
- probe_2 (Req 1.1/1.3): linear set_xlim(5,-3)->(5,-3) [descending kept], set_ylim(-3,5)->(-3,5) [ascending kept]. HOLDS patched; also HOLDS base (linear was never broken).
- probe_3 (Req 1.4, extra positive control): log set_ylim(1000,5)->(1000,5), magnitudes preserved, only order restored. HOLDS patched, FAILS base ((5,1000)).
- probe_4 (Req 1.5): 3-D set_xlim3d/ylim3d/zlim3d descending preserved. HOLDS patched; HOLDS base (base 3D setters didn't reorder — they never called the sorting path meaningfully here).
- probe_5 (Req 2.1/2.2, positive control): base Locator().nonsingular reorders descending pair ascending, preserves non-degenerate magnitudes. HOLDS patched ((1,10)/(1,10)/(-2,7)), FAILS base ((10,1) — increasing=False preserved order).
- probe_6 (Req 2.3/2.4 & 3.1): degenerate nonsingular(5,5)->distinct increasing; set_ylim(3,3) warns 'singular transformations...expanding' and commits non-empty. HOLDS both trees.
- probe_7 (Req 3.2/3.3): non-positive limit on log warned & ignored (prior kept); None reuses current endpoint. HOLDS both trees.
- probe_8 (Req 3.4): shared-axis propagation + returns committed (bottom,top) pair, descending preserved. HOLDS patched, FAILS base direction ((-1,7)).

### CANDIDATE PATCHES (both REJECTED by the suite — floor satisfied):
- weak_ticker_only.diff: only the ticker.py hunk (drop increasing=False from Locator.nonsingular) WITHOUT the set_xlim/ylim swapped-restore logic. REJECTED by probe_1 (log (1,10)), probe_2 (linear now (-3,5)!), probe_3, probe_4, probe_8. This is the naive/partial fix a weak reading permits; it also REGRESSES linear inversion, so the suite catches it decisively.
- weak_no3d.diff: gold 2-D + ticker hunks but OMITS the mpl_toolkits/mplot3d/axes3d.py hunks. REJECTED by probe_4 (3D setters come out ascending). Confirms Req 1.5 (3-D) is discriminating.

NOTE on the prior recorded G-EQ/G-PANEL-1 VIOLATION (probe_4 in a previous audit): almost certainly a probe bug, not a real spec violation. I reproduced the identical failure mode: calling matplotlib.ticker.LogLocator().nonsingular(10,1) directly (no attached axis) raises AttributeError "'NoneType' object has no attribute 'get_minpos'" — LogLocator overrides nonsingular and needs self.axis. The base Locator.nonsingular (the one Req 2 actually names) behaves exactly as the spec mandates on both trees. Every requirement-mandated behavior, exercised through the public API on a real axis, HOLDS on the gold-patched tree. G-PANEL-2's 'unfaithful' note is also mistaken: Req 2 explicitly concerns the base Locator.nonsingular (used by log/default locators via inheritance), which the patch does change from increasing=False to default sorting — precisely what the spec describes.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Patch adds a `swapped = a > b` flag in set_xlim/set_ylim (_base.py) and set_xlim3d/set_ylim3d/set_zlim3d (axes3d.py), restores caller order after nonsingular+limit_range_for_scale, and changes Locator.nonsingular in ticker.py to drop increasing=False so it returns endpoints ascending. Requirements 1 (caller-visible direction preservation on all scales incl 3d), 2 (nonsingular returns ascending; limit-setter restores order), and 3 (preserved behaviors: degenerate expand warning, log non-positive ignore, None reuse, shared-axis emit/return) exactly describe this. Modeling boundary is correct: pins the changed observable behavior (direction survives normalization) plus the enabling helper change, not a narrow single branch. Probes: log inversion, linear desc+asc, nonsingular ascending, nonsingular(inf,nan) fallback, zlim3d desc — all pass on patch; base fails at log inversion.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Hidden test material: FAIL_TO_PASS = the single test test_inverted_limits, whose added lines set yscale('log'), set_ylim(10,1), and assert get_ylim()==(10,1). That scenario (inverting a log axis via its limits, set_ylim(top,bottom)) is fully public in the problem_statement reproduction. The requirements contain NO test file paths, test/function/class names, parametrization ids, or quoted test/gold code. Every identifier used (set_xlim/set_ylim, set_xlim3d/ylim3d/zlim3d, _AxesBase, Axes3D, get_major_locator().nonsingular, limit_range_for_scale, LogLocator, Locator.nonsingular) is pre-existing public matplotlib API — legitimate localization, not fix-invented. The gold patch's invented identifier `swapped` never appears; the doc paraphrases the mechanism ('remember whether decreasing order was requested and restore it after normalizing'). 

Borderline points considered and cleared: (1) Requirement 2 describes nonsingular returning endpoints in increasing order, which mirrors the ticker.py gold edit (removing increasing=False). This is describing the gold implementation strategy, an over-specification/faithfulness concern, not transmission of hidden TESTS — there is no test that inspects nonsingular ordering. (2) Requirement 1.5 covers set_xlim3d/ylim3d/zlim3d, which are modified by the gold patch but NOT covered by any hidden test (no 3D test exists); it describes a behavioral generalization rather than reconstructing a test case. (3) Req 1.2's log-scale descending example restates the public bug reproduction, not a parametrized test id. No enumeration mirrors test parametrization (the sole test is not parametrized). Conclusion: the document translates behavior into requirements and describes the fix approach, but does not leak the hidden evaluation.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
