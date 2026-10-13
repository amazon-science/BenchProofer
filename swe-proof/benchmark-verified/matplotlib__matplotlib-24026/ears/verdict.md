# P2 adversarial audit — matplotlib__matplotlib-24026

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
"""Requirement 1 (positive control): supplying `colors` must NOT alter the
Axes property cycle. After stackplot(colors=...), the next artist drawn on the
same Axes must still get the ORIGINAL first cycle color (not the palette).
On base (set_prop_cycle mutation) this fails; on patched it holds."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import to_rgba

# The default first cycle color.
cycle = plt.rcParams['axes.prop_cycle'].by_key()['color']
expected_first = to_rgba(cycle[0])

fig, ax = plt.subplots()
x = np.arange(4)
ys = [np.array([1.0, 2, 3, 4]), np.array([1.0, 1, 1, 1]), np.array([2.0, 2, 2, 2])]
palette = ['red', 'green', 'blue']
ax.stackplot(x, *ys, colors=palette)

# Next line drawn should follow the ORIGINAL cycle, i.e. first cycle color,
# NOT 'red' (the palette's first entry).
line, = ax.plot(x, x)
got = to_rgba(line.get_color())
print("expected next cycle color:", expected_first)
print("got line color:", got)
palette_first = to_rgba(palette[0])
print("palette first:", palette_first)

if got == expected_first and got != palette_first:
    print("PASS: axes cycle unchanged by stackplot colors")
    raise SystemExit(0)
print("FAIL: axes cycle was mutated by stackplot colors")
raise SystemExit(1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""Requirement 1.2: a caller recording the next cycle color before stackplot
(via colors=) must get that SAME color for the following artist. Uses
ax._get_lines.get_next_color-independent check by comparing two axes:
one without stackplot, one with stackplot(colors=). Both should give the
same first plot color."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import to_rgba

x = np.arange(4)
ys = [np.array([1.0, 2, 3, 4]), np.array([1.0, 1, 1, 1])]

# Control axes: no stackplot.
fig, (ax_a, ax_b) = plt.subplots(1, 2)
line_a, = ax_a.plot(x, x)
color_a = to_rgba(line_a.get_color())

# Axes with stackplot(colors=) first, then plot.
ax_b.stackplot(x, *ys, colors=['C3', 'C4'])
line_b, = ax_b.plot(x, x)
color_b = to_rgba(line_b.get_color())

print("plot color without stackplot:", color_a)
print("plot color after stackplot(colors=):", color_b)
if color_a == color_b:
    print("PASS: following artist gets the untouched next cycle color")
    raise SystemExit(0)
print("FAIL: stackplot(colors=) shifted the cycle seen by the next artist")
raise SystemExit(1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""Requirement 2: C<N> reference tokens must be accepted (no ValueError) and
each must resolve to the same color the token denotes elsewhere. On base,
set_prop_cycle(color=['C0',...]) raises ValueError."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import to_rgba

x = np.arange(4)
ys = [np.array([1.0, 2, 3, 4]), np.array([1.0, 1, 1, 1]), np.array([2.0, 2, 2, 2])]
cycle = plt.rcParams['axes.prop_cycle'].by_key()['color']

fig, ax = plt.subplots()
try:
    polys = ax.stackplot(x, *ys, colors=['C0', 'C1', 'C2'])
except ValueError as e:
    print("FAIL: ValueError raised on C<N> tokens:", e)
    raise SystemExit(1)

# Verify each region facecolor matches to_rgba('C0'/'C1'/'C2') == cycle color.
for i, tok in enumerate(['C0', 'C1', 'C2']):
    fc = polys[i].get_facecolor()[0]
    expected = to_rgba(tok)
    expected2 = to_rgba(cycle[i])
    print(f"region {i}: token {tok} facecolor={tuple(fc)} expected={expected} cycle={expected2}")
    if not (np.allclose(fc, expected) and np.allclose(expected, expected2)):
        print(f"FAIL: region {i} facecolor does not match {tok}")
        raise SystemExit(1)
print("PASS: C<N> tokens accepted and resolved correctly")
raise SystemExit(0)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""Requirement 3: regions colored by cycling palette in order with wrap-around.
region i gets colors[i mod len(colors)]. Use more regions than palette entries."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import to_rgba

x = np.arange(5)
# 5 regions, palette of 2 -> wrap-around.
ys = [np.array([1.0, 1, 1, 1, 1]) for _ in range(5)]
palette = ['red', 'blue']

fig, ax = plt.subplots()
polys = ax.stackplot(x, *ys, colors=palette)
print("num regions:", len(polys))
if len(polys) != 5:
    print("FAIL: expected 5 regions, got", len(polys))
    raise SystemExit(1)
ok = True
for i in range(5):
    fc = polys[i].get_facecolor()[0]
    expected = to_rgba(palette[i % len(palette)])
    print(f"region {i}: facecolor={tuple(fc)} expected={expected}")
    if not np.allclose(fc, expected):
        ok = False
if ok:
    print("PASS: palette cycled with wrap-around, one region per series")
    raise SystemExit(0)
print("FAIL: wrap-around coloring incorrect")
raise SystemExit(1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""Requirement 4: when colors is None, regions colored from Axes property cycle,
advancing exactly one color per region (n colors for n regions)."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import to_rgba

x = np.arange(4)
ys = [np.array([1.0, 1, 1, 1]) for _ in range(3)]
cycle = plt.rcParams['axes.prop_cycle'].by_key()['color']

fig, ax = plt.subplots()
polys = ax.stackplot(x, *ys)  # no colors
if len(polys) != 3:
    print("FAIL: expected 3 regions"); raise SystemExit(1)
for i in range(3):
    fc = polys[i].get_facecolor()[0]
    expected = to_rgba(cycle[i])
    print(f"region {i}: facecolor={tuple(fc)} expected cycle[{i}]={expected}")
    if not np.allclose(fc, expected):
        print("FAIL: region not colored from property cycle in order")
        raise SystemExit(1)

# Next artist should get cycle[3] -> cycle advanced by exactly 3.
line, = ax.plot(x, x)
got = to_rgba(line.get_color())
expected_next = to_rgba(cycle[3])
print("next line color:", got, "expected cycle[3]:", expected_next)
if got != expected_next:
    print("FAIL: cycle not advanced by exactly one per region")
    raise SystemExit(1)
print("PASS: default cycle used and advanced by exactly n")
raise SystemExit(0)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
"""Requirement 5 (regression): return value = one artist per series in order;
labels applied in order then stop; baselines 'zero'/'sym'/'wiggle'/
'weighted_wiggle' supported and other rejected; 'zero' pins sticky edge at 0."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

x = np.arange(6)
ys = [np.array([1.0, 2, 3, 4, 5, 6]),
      np.array([2.0, 2, 2, 2, 2, 2]),
      np.array([1.0, 1, 1, 1, 1, 1])]

# Return value: one per series, in order, with labels applied then stopping.
fig, ax = plt.subplots()
polys = ax.stackplot(x, *ys, labels=['a', 'b'])  # fewer labels than regions
print("num artists:", len(polys))
if len(polys) != 3:
    print("FAIL: expected 3 artists"); raise SystemExit(1)
labels = [p.get_label() for p in polys]
print("labels:", labels)
if labels[0] != 'a' or labels[1] != 'b':
    print("FAIL: labels not applied in order"); raise SystemExit(1)
# third label should NOT be 'a'/'b' (no label applied -> default auto label)
if labels[2] in ('a', 'b'):
    print("FAIL: label applied beyond sequence"); raise SystemExit(1)

# sticky edge at zero for baseline='zero'
se = polys[0].sticky_edges.y
print("first region sticky_edges.y:", list(se))
if list(se) != [0]:
    print("FAIL: first region lower edge not pinned at 0"); raise SystemExit(1)

# All valid baselines succeed.
for bl in ['zero', 'sym', 'wiggle', 'weighted_wiggle']:
    fig2, ax2 = plt.subplots()
    try:
        ax2.stackplot(x, *ys, baseline=bl)
    except Exception as e:
        print(f"FAIL: baseline {bl} raised {e!r}"); raise SystemExit(1)
    print(f"baseline {bl} ok")

# Invalid baseline rejected.
fig3, ax3 = plt.subplots()
try:
    ax3.stackplot(x, *ys, baseline='bogus')
    print("FAIL: invalid baseline not rejected"); raise SystemExit(1)
except ValueError:
    print("invalid baseline rejected ok")

print("PASS: regression behaviors preserved")
raise SystemExit(0)
```

Attack 7 — `probe_7.py` → holds on the patched tree (good)

```python
"""Requirement 5.4: data-mapping resolution. Pass x and y series as keys into a
`data` mapping."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import to_rgba

data = {
    'xx': np.arange(4),
    'y1': np.array([1.0, 2, 3, 4]),
    'y2': np.array([1.0, 1, 1, 1]),
}
fig, ax = plt.subplots()
polys = ax.stackplot('xx', 'y1', 'y2', data=data, colors=['red', 'blue'])
print("num artists:", len(polys))
if len(polys) != 2:
    print("FAIL: expected 2 regions from data keys"); raise SystemExit(1)
fc0 = polys[0].get_facecolor()[0]
if not np.allclose(fc0, to_rgba('red')):
    print("FAIL: first region color wrong from data path"); raise SystemExit(1)
print("PASS: data-mapping key resolution preserved")
raise SystemExit(0)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Requirement 1 (positive control): supplying `colors` must NOT alter the
Axes property cycle. After stackplot(colors=...), the next artist drawn on the
same Axes must still get the ORIGINAL first cycle color (not the palette).
On base (set_prop_cycle mutation) this fails; on patched it holds."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import to_rgba

# The default first cycle color.
cycle = plt.rcParams['axes.prop_cycle'].by_key()['color']
expected_first = to_rgba(cycle[0])

fig, ax = plt.subplots()
x = np.arange(4)
ys = [np.array([1.0, 2, 3, 4]), np.array([1.0, 1, 1, 1]), np.array([2.0, 2, 2, 2])]
palette = ['red', 'green', 'blue']
ax.stackplot(x, *ys, colors=palette)

# Next line drawn should follow the ORIGINAL cycle, i.e. first cycle color,
# NOT 'red' (the palette's first entry).
line, = ax.plot(x, x)
got = to_rgba(line.get_color())
print("expected next cycle color:", expected_first)
print("got line color:", got)
palette_first = to_rgba(palette[0])
print("palette first:", palette_first)

if got == expected_first and got != palette_first:
    print("PASS: axes cycle unchanged by stackplot colors")
    raise SystemExit(0)
print("FAIL: axes cycle was mutated by stackplot colors")
raise SystemExit(1)
```

Prepatch bug re-encoded as an attack: `True`.

7 probes, all HOLD on gold-patched tree; all pass a clean apply. Coverage by requirement: probe_1 (R1.1/1.2, positive control) — after stackplot(colors=), next plot artist gets the ORIGINAL first cycle color, not the palette's first entry; HOLDS patched, FAILS at base (got 'red' from mutated prop_cycle). probe_2 (R1.2) — plot color after stackplot(colors=['C3','C4']) equals plot color on a fresh axes; also fails at base with ValueError on C-token. probe_3 (R2.1/2.2/2.3, secondary positive control) — colors=['C0','C1','C2'] completes without ValueError and each region facecolor == to_rgba(Cn) == cycle[n]; FAILS at base with 'Cannot put cycle reference in prop_cycler'. probe_4 (R3.1/3.2) — 5 regions, palette of 2, region i facecolor == palette[i%2] with wrap-around and exactly 5 artists. probe_5 (R4.1/4.2/4.3) — colors=None colors regions from prop cycle in order and advances by exactly n (next line == cycle[3]). probe_6 (R5.1/5.2/5.3/5.5) — one artist per series in order, labels applied then stop, sticky_edges.y==[0] for baseline zero, all four valid baselines accepted, invalid rejected with ValueError. probe_7 (R5.4) — data-mapping key resolution ('xx','y1','y2', data=...) yields correct regions/colors.

DISCRIMINATION: candidate 'weak_iter_no_wraparound' fixes the cycle mutation and C-token acceptance correctly (probes 1,2,3,5,6,7 all pass) but uses iter(colors) instead of itertools.cycle(colors) — a requirements-weak reading that omits R3 wrap-around. probe_4 REJECTS it (StopIteration when regions exceed palette length). This proves the suite discriminates a plausible partial fix on the wrap-around criterion. Positive control discriminates base vs patched. Verdict SOUND: >=5 probes hold on patched, positive control fails at base, and a wrong-fix candidate is rejected.

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
"""Requirement 1 (positive control): supplying `colors` must NOT alter the
Axes property cycle. After stackplot(colors=...), the next artist drawn on the
same Axes must still get the ORIGINAL first cycle color (not the palette).
On base (set_prop_cycle mutation) this fails; on patched it holds."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import to_rgba

# The default first cycle color.
cycle = plt.rcParams['axes.prop_cycle'].by_key()['color']
expected_first = to_rgba(cycle[0])

fig, ax = plt.subplots()
x = np.arange(4)
ys = [np.array([1.0, 2, 3, 4]), np.array([1.0, 1, 1, 1]), np.array([2.0, 2, 2, 2])]
palette = ['red', 'green', 'blue']
ax.stackplot(x, *ys, colors=palette)

# Next line drawn should follow the ORIGINAL cycle, i.e. first cycle color,
# NOT 'red' (the palette's first entry).
line, = ax.plot(x, x)
got = to_rgba(line.get_color())
print("expected next cycle color:", expected_first)
print("got line color:", got)
palette_first = to_rgba(palette[0])
print("palette first:", palette_first)

if got == expected_first and got != palette_first:
    print("PASS: axes cycle unchanged by stackplot colors")
    raise SystemExit(0)
print("FAIL: axes cycle was mutated by stackplot colors")
raise SystemExit(1)
```

Prepatch bug re-encoded as an attack: `True`.

7 probes, all HOLD on gold-patched tree; all pass a clean apply. Coverage by requirement: probe_1 (R1.1/1.2, positive control) — after stackplot(colors=), next plot artist gets the ORIGINAL first cycle color, not the palette's first entry; HOLDS patched, FAILS at base (got 'red' from mutated prop_cycle). probe_2 (R1.2) — plot color after stackplot(colors=['C3','C4']) equals plot color on a fresh axes; also fails at base with ValueError on C-token. probe_3 (R2.1/2.2/2.3, secondary positive control) — colors=['C0','C1','C2'] completes without ValueError and each region facecolor == to_rgba(Cn) == cycle[n]; FAILS at base with 'Cannot put cycle reference in prop_cycler'. probe_4 (R3.1/3.2) — 5 regions, palette of 2, region i facecolor == palette[i%2] with wrap-around and exactly 5 artists. probe_5 (R4.1/4.2/4.3) — colors=None colors regions from prop cycle in order and advances by exactly n (next line == cycle[3]). probe_6 (R5.1/5.2/5.3/5.5) — one artist per series in order, labels applied then stop, sticky_edges.y==[0] for baseline zero, all four valid baselines accepted, invalid rejected with ValueError. probe_7 (R5.4) — data-mapping key resolution ('xx','y1','y2', data=...) yields correct regions/colors.

DISCRIMINATION: candidate 'weak_iter_no_wraparound' fixes the cycle mutation and C-token acceptance correctly (probes 1,2,3,5,6,7 all pass) but uses iter(colors) instead of itertools.cycle(colors) — a requirements-weak reading that omits R3 wrap-around. probe_4 REJECTS it (StopIteration when regions exceed palette length). This proves the suite discriminates a plausible partial fix on the wrap-around criterion. Positive control discriminates base vs patched. Verdict SOUND: >=5 probes hold on patched, positive control fails at base, and a wrong-fix candidate is rejected.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Probed on the instance image. Gold patch: `if colors is not None: colors = itertools.cycle(colors) else: colors = (axes._get_lines.get_next_color() for _ in y)`, then each fill_between uses facecolor=next(colors) instead of the old set_prop_cycle(color=colors)+get_next_color(). Verified: Req1 — next cycle color identical before/after stackplot with explicit colors (next_before==next_after). Req2 — colors=['C2','C3','C4'] completes and region 0 facecolor == to_rgba('C2') (base raises ValueError 'Cannot put cycle reference (C2)'). Req3 — colors=['C2'] wraps to all 3 regions; pal>=regions gives region i == colors[i]; len(r)==3 one per series. Req4 — colors=None still yields 3 regions from the prop cycle. Req5 items (return list, labels, baselines, data-key resolution, sticky edge at 0, **kwargs forwarding) are untouched by the diff and thus preserved. The modeling boundary tracks the changed observable behavior (region facecolors + non-mutation of the Axes cycle), not a narrow branch/helper.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** requirements.md translates the hidden test/gold into behavioral requirements without transmitting the tests themselves. All potentially sensitive content is either public via problem_statement (CN tokens like C0/C1/C2, set_prop_cycle, ValueError, stackplot API, colors argument) or legitimate change-localization (naming lib/matplotlib/stackplot.py::stackplot and the collaborating internal API Axes._get_lines.get_next_color(), an existing identifier, not fix-invented). The wrap-around/`i mod len(colors)` cycling (Req 3) is a behavioral description of the itertools.cycle fix, not quoted gold code. No test function/class names (test_stackplot, TestScatter), no test file path (tests/test_axes.py), no parametrization ids ([png]/[pdf]), no verbatim gold lines, and no test-shaped enumerations mirroring the parametrized cases. Preservation clauses in Req 5 cover pre-existing public behavior (baseline options, sticky edges, data-mapping), not the hidden test.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
