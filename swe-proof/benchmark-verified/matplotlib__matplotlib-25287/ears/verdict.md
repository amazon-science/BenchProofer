# P2 adversarial audit — matplotlib__matplotlib-25287

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 7 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 7 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py`, `probe_pc.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_pc.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (7):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# Req 1.1: x-axis, concrete xtick.labelcolor -> offset text uses labelcolor
with matplotlib.rc_context({"xtick.labelcolor": "red", "xtick.color": "blue"}):
    fig = plt.figure()
    ax = fig.add_subplot()
    c = ax.xaxis.get_offset_text().get_color()
print("x offsetText color =", c)
assert c == "red", f"expected 'red' (labelcolor), got {c!r}"
print("OK")
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# Req 1.2: x-axis, labelcolor='inherit' -> offset text uses xtick.color
with matplotlib.rc_context({"xtick.labelcolor": "inherit", "xtick.color": "green"}):
    fig = plt.figure()
    ax = fig.add_subplot()
    c = ax.xaxis.get_offset_text().get_color()
print("x offsetText color =", c)
assert c == "green", f"expected 'green' (xtick.color) under inherit, got {c!r}"
print("OK")
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# Req 2.1: y-axis, concrete ytick.labelcolor -> offset text uses labelcolor
with matplotlib.rc_context({"ytick.labelcolor": "red", "ytick.color": "blue"}):
    fig = plt.figure()
    ax = fig.add_subplot()
    c = ax.yaxis.get_offset_text().get_color()
print("y offsetText color =", c)
assert c == "red", f"expected 'red' (labelcolor), got {c!r}"
print("OK")
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# Req 2.2: y-axis, labelcolor='inherit' -> offset text uses ytick.color
with matplotlib.rc_context({"ytick.labelcolor": "inherit", "ytick.color": "green"}):
    fig = plt.figure()
    ax = fig.add_subplot()
    c = ax.yaxis.get_offset_text().get_color()
print("y offsetText color =", c)
assert c == "green", f"expected 'green' (ytick.color) under inherit, got {c!r}"
print("OK")
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# Req 3.1/3.2: offset text artist still created for both axes with expected
# position/alignment/fontsize preserved.
with matplotlib.rc_context({"xtick.labelsize": 17.0, "ytick.labelsize": 13.0}):
    fig = plt.figure()
    ax = fig.add_subplot()
    xo = ax.xaxis.get_offset_text()
    yo = ax.yaxis.get_offset_text()

assert xo is not None and yo is not None, "offset text missing"
# x offset anchored far end (right/top)
print("x va,ha =", xo.get_verticalalignment(), xo.get_horizontalalignment())
print("y va,ha =", yo.get_verticalalignment(), yo.get_horizontalalignment())
print("x fontsize =", xo.get_fontsize(), "y fontsize =", yo.get_fontsize())
assert xo.get_verticalalignment() == "top"
assert xo.get_horizontalalignment() == "right"
assert xo.get_verticalalignment() == "top"
assert abs(xo.get_fontsize() - 17.0) < 1e-6, xo.get_fontsize()
assert abs(yo.get_fontsize() - 13.0) < 1e-6, yo.get_fontsize()
print("OK")
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import to_rgba

# Req 3.3: default rcParams -> offset text color unchanged (== default tick color).
# Also Req 3.4: tick marks/labels unchanged is default-preserving.
with matplotlib.rc_context({}):
    fig = plt.figure()
    ax = fig.add_subplot()
    xc = ax.xaxis.get_offset_text().get_color()
    yc = ax.yaxis.get_offset_text().get_color()
    xtick = matplotlib.rcParams["xtick.color"]
    ytick = matplotlib.rcParams["ytick.color"]
    xlab = matplotlib.rcParams["xtick.labelcolor"]
    ylab = matplotlib.rcParams["ytick.labelcolor"]
print("defaults: xtick.color", xtick, "labelcolor", xlab)
print("x offset", xc, "y offset", yc)
# Default labelcolor is 'inherit' historically -> offset color == tick color (old behavior)
assert xlab == "inherit" and ylab == "inherit", (xlab, ylab)
assert to_rgba(xc) == to_rgba(xtick), (xc, xtick)
assert to_rgba(yc) == to_rgba(ytick), (yc, ytick)
print("OK")
```

Attack 7 — `probe_pc.py` → holds on the patched tree (good)

```python
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# POSITIVE CONTROL: concrete labelcolor differing from tick color.
# Patched -> offset text follows labelcolor ('red'); base bug -> tick color ('blue').
with matplotlib.rc_context({"xtick.labelcolor": "red", "xtick.color": "blue",
                            "ytick.labelcolor": "red", "ytick.color": "blue"}):
    fig = plt.figure()
    ax = fig.add_subplot()
    xc = ax.xaxis.get_offset_text().get_color()
    yc = ax.yaxis.get_offset_text().get_color()
print("x offset", xc, "y offset", yc)
assert xc == "red", f"x expected 'red', got {xc!r}"
assert yc == "red", f"y expected 'red', got {yc!r}"
print("OK")
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_pc.py`

```python
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# POSITIVE CONTROL: concrete labelcolor differing from tick color.
# Patched -> offset text follows labelcolor ('red'); base bug -> tick color ('blue').
with matplotlib.rc_context({"xtick.labelcolor": "red", "xtick.color": "blue",
                            "ytick.labelcolor": "red", "ytick.color": "blue"}):
    fig = plt.figure()
    ax = fig.add_subplot()
    xc = ax.xaxis.get_offset_text().get_color()
    yc = ax.yaxis.get_offset_text().get_color()
print("x offset", xc, "y offset", yc)
assert xc == "red", f"x expected 'red', got {xc!r}"
assert yc == "red", f"y expected 'red', got {yc!r}"
print("OK")
```

Prepatch bug re-encoded as an attack: `True`.

Requirement: offset (exponent) text color should follow tick LABEL color (honoring 'inherit'), not tick MARK color. Probes: probe_1 (Req1.1 x concrete labelcolor->label color red), probe_2 (Req1.2 x inherit->xtick.color green), probe_3 (Req2.1 y concrete labelcolor->red), probe_4 (Req2.2 y inherit->ytick.color green), probe_5 (Req3.1/3.2 offset artists still created; va/ha/fontsize preserved), probe_6 (Req3.3/3.4 defaults: labelcolor='inherit' so offset color==tick color, unchanged appearance). All 6 HOLD on gold-patched tree. Positive control probe_pc (x&y concrete labelcolor 'red' vs tick 'blue') HOLDS patched, FAILS at base (got 'blue') => discriminates, prepatch reproduced. Wrong-fix candidate weak.diff fixes only the x-axis _init and leaves y-axis using ytick.color: REJECTED by probe_3 (y offset='blue' not 'red') and by positive control => suite discriminates partial fixes. No too-weak finding. Verdict SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 7 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 7 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py`, `probe_pc.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_pc.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (7):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts, and on this backend both roles put it through the same derivation: every block below is a requirement probe run on the gold-patched tree, and the `machine verdict:` line each role publishes above reports BOTH that its probes hold there and how many candidate patches the probe suite rejected — so the two roles re-ran ONE probe suite and each recorded its own outcome for every probe in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `probe_1.py` → holds on the patched tree (good)

Attack 2 — `probe_2.py` → holds on the patched tree (good)

Attack 3 — `probe_3.py` → holds on the patched tree (good)

Attack 4 — `probe_4.py` → holds on the patched tree (good)

Attack 5 — `probe_5.py` → holds on the patched tree (good)

Attack 6 — `probe_6.py` → holds on the patched tree (good)

Attack 7 — `probe_pc.py` → holds on the patched tree (good)

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_pc.py`

```python
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# POSITIVE CONTROL: concrete labelcolor differing from tick color.
# Patched -> offset text follows labelcolor ('red'); base bug -> tick color ('blue').
with matplotlib.rc_context({"xtick.labelcolor": "red", "xtick.color": "blue",
                            "ytick.labelcolor": "red", "ytick.color": "blue"}):
    fig = plt.figure()
    ax = fig.add_subplot()
    xc = ax.xaxis.get_offset_text().get_color()
    yc = ax.yaxis.get_offset_text().get_color()
print("x offset", xc, "y offset", yc)
assert xc == "red", f"x expected 'red', got {xc!r}"
assert yc == "red", f"y expected 'red', got {yc!r}"
print("OK")
```

Prepatch bug re-encoded as an attack: `True`.

Requirement: offset (exponent) text color should follow tick LABEL color (honoring 'inherit'), not tick MARK color. Probes: probe_1 (Req1.1 x concrete labelcolor->label color red), probe_2 (Req1.2 x inherit->xtick.color green), probe_3 (Req2.1 y concrete labelcolor->red), probe_4 (Req2.2 y inherit->ytick.color green), probe_5 (Req3.1/3.2 offset artists still created; va/ha/fontsize preserved), probe_6 (Req3.3/3.4 defaults: labelcolor='inherit' so offset color==tick color, unchanged appearance). All 6 HOLD on gold-patched tree. Positive control probe_pc (x&y concrete labelcolor 'red' vs tick 'blue') HOLDS patched, FAILS at base (got 'blue') => discriminates, prepatch reproduced. Wrong-fix candidate weak.diff fixes only the x-axis _init and leaves y-axis using ytick.color: REJECTED by probe_3 (y offset='blue' not 'red') and by positive control => suite discriminates partial fixes. No too-weak finding. Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** The gold patch changes only the color= argument of self.offsetText.set() in XAxis._init and YAxis._init, selecting rcParams['*tick.labelcolor'] unless it is 'inherit' (then '*tick.color'). This is exactly the biconditional the two-branch acceptance criteria of Req1 and Req2 describe, for both x and y axes (correct modeling boundary — the changed behavior, not a narrow slice). Req3 (preserve position/transform/fontsize/default appearance, leave tick and tick-label colors unchanged) is consistent: the diff touches nothing but the color argument, and the default rcParams keep labelcolor='inherit' so default appearance is unchanged. No forbidden/invented/over-narrow behavior found.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The requirements describe only behavior fully derivable from the public problem_statement, which itself states the bug (offsetText colored from tick.color instead of tick.labelcolor), gives a reproduction, and even includes a suggested patch showing the exact 'labelcolor==inherit ? tick.color : labelcolor' logic per axis. The doc names XAxis._init/YAxis._init, offsetText, and the rcParams — legitimate localization of the change. No hidden-test content leaks: no test function names (test_xaxis_offsetText_color/test_yaxis_offsetText_color), no test file path, no gold-patch-invented identifier (the gold uses a local 'tick_color' var, not named in the doc), and no enumeration of the specific test colors (blue/yellow/green/red) or parametrization ids. The x/y split mirrors the real matplotlib API structure and the two problem-statement patch hunks, not the test cases.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
