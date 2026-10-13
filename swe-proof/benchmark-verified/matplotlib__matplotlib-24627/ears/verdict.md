# P2 adversarial audit — matplotlib__matplotlib-24627

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 8 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 8 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py`, `probe_7.py`, `probe_8.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (8):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# Positive control: clear() deparents a plotted line (.axes and .figure -> None)
fig, ax = plt.subplots()
line, = ax.plot([1, 2, 3])
assert line.axes is ax
assert line.figure is fig
ax.clear()
print("after clear: line.axes=%r line.figure=%r" % (line.axes, line.figure))
ok = (line.axes is None) and (line.figure is None)
print("HOLDS" if ok else "FAILS")
raise SystemExit(0 if ok else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# Req1 crit1&2 via cla(): cla() also deparents a plotted line
fig, ax = plt.subplots()
line, = ax.plot([1, 2, 3])
ax.cla()
print("after cla: line.axes=%r line.figure=%r" % (line.axes, line.figure))
ok = (line.axes is None) and (line.figure is None)
print("HOLDS" if ok else "FAILS")
raise SystemExit(0 if ok else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

# Req1 crit3: deparenting applies uniformly to every artist type, not a subset
fig, ax = plt.subplots()
line, = ax.plot([1, 2, 3])
txt = ax.text(0.5, 0.5, "hello")
patch = ax.add_patch(mpatches.Rectangle((0, 0), 1, 1))
sc = ax.scatter([0, 1], [0, 1])  # a collection

artists = {"line": line, "text": txt, "patch": patch, "collection": sc}
ax.clear()
bad = []
for name, a in artists.items():
    print("%s: axes=%r figure=%r" % (name, a.axes, a.figure))
    if a.axes is not None or a.figure is not None:
        bad.append(name)
ok = not bad
print("still parented: %r" % bad)
print("HOLDS" if ok else "FAILS")
raise SystemExit(0 if ok else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# Req2 crit1: cleared Axes retains none of its previous child artists
fig, ax = plt.subplots()
line, = ax.plot([1, 2, 3])
prev = list(ax._children)
assert line in prev
ax.clear()
remaining = [c for c in ax._children if c in prev]
print("previous children still retained: %r" % remaining)
print("ax.lines=%r" % list(ax.lines))
ok = (len(remaining) == 0) and (line not in ax._children) and (len(ax.lines) == 0)
print("HOLDS" if ok else "FAILS")
raise SystemExit(0 if ok else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# Req2 crit2: clearing's detachment matches Artist.remove() individual removal
# Build two identical setups; remove one line individually, clear the other axes.
fig1, ax1 = plt.subplots()
l1, = ax1.plot([1, 2, 3])
l1.remove()
removed_state = (l1.axes, l1.figure)

fig2, ax2 = plt.subplots()
l2, = ax2.plot([1, 2, 3])
ax2.clear()
cleared_state = (l2.axes, l2.figure)

print("removed_state=%r cleared_state=%r" % (removed_state, cleared_state))
ok = removed_state == (None, None) and cleared_state == (None, None)
print("HOLDS" if ok else "FAILS")
raise SystemExit(0 if ok else 1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# Req1 crit4 (regression, holds on both trees): while a child is not cleared/removed,
# its .axes refers to the Axes and .figure to the Figure.
fig, ax = plt.subplots()
line, = ax.plot([1, 2, 3])
print("line.axes is ax: %r ; line.figure is fig: %r" % (line.axes is ax, line.figure is fig))
ok = (line.axes is ax) and (line.figure is fig)
print("HOLDS" if ok else "FAILS")
raise SystemExit(0 if ok else 1)
```

Attack 7 — `probe_7.py` → holds on the patched tree (good)

```python
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# Req3 crit3: clearing still resets the Axes' own state (scale/limits/grid).
fig, ax = plt.subplots()
ax.plot([1, 2, 3])
ax.set_xscale("log")
ax.set_xlim(3, 17)
assert ax.get_xscale() == "log"
ax.clear()
xs = ax.get_xscale()
lim = ax.get_xlim()
print("after clear: xscale=%r xlim=%r" % (xs, lim))
# default axes come back linear with autoscaled default limits (0,1)
ok = (xs == "linear") and (tuple(lim) == (0.0, 1.0))
print("HOLDS" if ok else "FAILS")
raise SystemExit(0 if ok else 1)
```

Attack 8 — `probe_8.py` → holds on the patched tree (good)

```python
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# Req3 crit1: cla() and clear() produce equivalent deparenting behavior.
fig1, ax1 = plt.subplots()
a1, = ax1.plot([1, 2, 3])
ax1.cla()
s1 = (a1.axes, a1.figure, len(ax1._children))

fig2, ax2 = plt.subplots()
a2, = ax2.plot([1, 2, 3])
ax2.clear()
s2 = (a2.axes, a2.figure, len(ax2._children))

print("cla state=%r clear state=%r" % (s1, s2))
ok = s1 == s2 == (None, None, 0)
print("HOLDS" if ok else "FAILS")
raise SystemExit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# Positive control: clear() deparents a plotted line (.axes and .figure -> None)
fig, ax = plt.subplots()
line, = ax.plot([1, 2, 3])
assert line.axes is ax
assert line.figure is fig
ax.clear()
print("after clear: line.axes=%r line.figure=%r" % (line.axes, line.figure))
ok = (line.axes is None) and (line.figure is None)
print("HOLDS" if ok else "FAILS")
raise SystemExit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Requirements: clearing an Axes (cla/clear) must deparent every former child by unsetting BOTH .axes and .figure (matching Artist.remove()), while preserving all other clear behavior.

Probes (criterion -> result base -> patched):
- probe_1 (R1.1/1.2 via clear(), POSITIVE CONTROL): line.axes/.figure -> None. BASE FAILS (axes/figure still set), PATCHED HOLDS. Discriminates.
- probe_2 (R1.1/1.2 via cla()): BASE FAILS, PATCHED HOLDS.
- probe_3 (R1.3 uniformity: line/text/patch/collection all deparented): BASE FAILS (all 4 still parented), PATCHED HOLDS.
- probe_4 (R2.1 Axes retains no former children / ax.lines empty): HOLDS on BOTH (list was already replaced pre-patch) — regression-style; does not discriminate alone but confirms retention behavior.
- probe_5 (R2.2 clear detachment == Artist.remove() state): BASE FAILS (cleared line still (axes,figure)), PATCHED HOLDS.
- probe_6 (R1.4 uncleared child still parented): HOLDS BOTH (regression).
- probe_7 (R3.3 scale/limits/grid reset persists): HOLDS BOTH (regression).
- probe_8 (R3.1 cla()==clear() equivalence, both deparent + empty): BASE FAILS, PATCHED HOLDS.

All 8 HOLD on gold-patched tree. Positive control (probe_1) FAILS at base, HOLDS patched => prepatch reproduced, discriminating power confirmed.

CANDIDATE WRONG PATCH (weak.diff): the lazy fix that unsets only chld.axes (not chld.figure). REJECTED by probes 1,2,3,5,8 (.figure still points at Figure) — this is exactly the R1.2 obligation. Demonstrates the suite discriminates a plausible partial fix that a weak reading (deparent = detach from Axes only) would permit. No requirements-conforming-yet-nonresolving (too-weak) patch found; suite pins both .axes and .figure per R2.2's equivalence-to-remove().

Env: swebench-lean conda python 3.12; probes are stdlib+matplotlib(Agg) only.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 8 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 8 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py`, `probe_7.py`, `probe_8.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

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
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# Positive control: clear() deparents a plotted line (.axes and .figure -> None)
fig, ax = plt.subplots()
line, = ax.plot([1, 2, 3])
assert line.axes is ax
assert line.figure is fig
ax.clear()
print("after clear: line.axes=%r line.figure=%r" % (line.axes, line.figure))
ok = (line.axes is None) and (line.figure is None)
print("HOLDS" if ok else "FAILS")
raise SystemExit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Requirements: clearing an Axes (cla/clear) must deparent every former child by unsetting BOTH .axes and .figure (matching Artist.remove()), while preserving all other clear behavior.

Probes (criterion -> result base -> patched):
- probe_1 (R1.1/1.2 via clear(), POSITIVE CONTROL): line.axes/.figure -> None. BASE FAILS (axes/figure still set), PATCHED HOLDS. Discriminates.
- probe_2 (R1.1/1.2 via cla()): BASE FAILS, PATCHED HOLDS.
- probe_3 (R1.3 uniformity: line/text/patch/collection all deparented): BASE FAILS (all 4 still parented), PATCHED HOLDS.
- probe_4 (R2.1 Axes retains no former children / ax.lines empty): HOLDS on BOTH (list was already replaced pre-patch) — regression-style; does not discriminate alone but confirms retention behavior.
- probe_5 (R2.2 clear detachment == Artist.remove() state): BASE FAILS (cleared line still (axes,figure)), PATCHED HOLDS.
- probe_6 (R1.4 uncleared child still parented): HOLDS BOTH (regression).
- probe_7 (R3.3 scale/limits/grid reset persists): HOLDS BOTH (regression).
- probe_8 (R3.1 cla()==clear() equivalence, both deparent + empty): BASE FAILS, PATCHED HOLDS.

All 8 HOLD on gold-patched tree. Positive control (probe_1) FAILS at base, HOLDS patched => prepatch reproduced, discriminating power confirmed.

CANDIDATE WRONG PATCH (weak.diff): the lazy fix that unsets only chld.axes (not chld.figure). REJECTED by probes 1,2,3,5,8 (.figure still points at Figure) — this is exactly the R1.2 obligation. Demonstrates the suite discriminates a plausible partial fix that a weak reading (deparent = detach from Axes only) would permit. No requirements-conforming-yet-nonresolving (too-weak) patch found; suite pins both .axes and .figure per R2.2's equivalence-to-remove().

Env: swebench-lean conda python 3.12; probes are stdlib+matplotlib(Agg) only.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Requirements are faithful to the actual change and pinned at the correct modeling boundary (deparent all former children), not a narrow slice. Note: this gate judges faithfulness only; the bundle's own G-PANEL-3 recorded a LEAKAGE fail (imshow/two-type example derivable only from the hidden test), which is a separate leakage concern and does not affect faithfulness.

Counterexample / evidence:

```
No divergence found. The patch changes exactly one observable: former children are deparented on clear. The requirements pin that biconditional boundary (all child artist types, both cla and clear, consistent with individual remove), matching probe results on both patched (holds) and base (violated) trees.
```


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The requirements describe behavior already public in the problem_statement: cla()/clear() should unset deparented artists' .axes and .figure, mirroring Artist.remove(), with the exact In[11]/In[12] example. Localizing the change to the internal __clear method in lib/matplotlib/axes/_base.py is legitimate localization (naming modules/functions is allowed), and matches the changed file — no test file path, no test name (test_cla_clears_children_axes_and_fig), no parametrization ids, no gold identifiers (old_children/chld) appear. Req 1.3 ('regardless of artist's type, not limited to a subset') is a behavioral generalization, not an enumeration mirroring the hidden test's specific line+image cases (the doc never enumerates plot-lines vs imshow-image). Reqs 2 and 3 (equivalence of cla/clear, subclass override dispatch, twinned axes, reset of scales/limits/grid) restate general preserved behavior corresponding to PASS_TO_PASS coverage but describe behavior rather than transmitting the tests themselves. Nothing is derivable only from the hidden test_patch or gold edit.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
