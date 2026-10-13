# P2 adversarial audit — matplotlib__matplotlib-20859

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 5 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 5 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 5 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (5):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
"""Positive control / Req1.1+1.2+1.3: Legend with SubFigure parent.
Constructor completes, isaxes False, figure is the subfigure (identity).
HOLDS on patched, FAILS at base (TypeError)."""
import sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.legend import Legend

fig = plt.figure()
subfigs = fig.subfigures(1, 2)
subfig = subfigs[0]
axs = subfig.subplots()
axs.plot([1, 2, 3], [1, 2, 3], label="line")
handles, labels = axs.get_legend_handles_labels()

try:
    leg = Legend(subfig, handles, labels)
except Exception as e:
    print("FAIL: construction raised", type(e).__name__, e)
    sys.exit(1)

print("constructed OK; isaxes=", leg.isaxes, "figure is subfig:", leg.figure is subfig)
ok = (leg.isaxes is False) and (leg.figure is subfig)
sys.exit(0 if ok else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""Req1.4: subfig.legend() with a labelled artist creates, registers, and returns a Legend."""
import sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.legend import Legend

fig = plt.figure()
subfig = fig.subfigures(1, 2)[0]
ax = subfig.subplots()
ax.plot([1, 2, 3], [3, 2, 1], label="mine")

try:
    leg = subfig.legend()
except Exception as e:
    print("FAIL: subfig.legend() raised", type(e).__name__, e)
    sys.exit(1)

registered = getattr(subfig, "legends", None)
print("returned:", type(leg).__name__, "registered:", registered)
ok = isinstance(leg, Legend) and leg in (registered or [])
sys.exit(0 if ok else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""Req2: top-level Figure parent -> isaxes False, figure is the figure; fig.legend returns."""
import sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.legend import Legend

fig = plt.figure()
ax = fig.subplots()
ax.plot([0, 1], [0, 1], label="top")
handles, labels = ax.get_legend_handles_labels()

leg = Legend(fig, handles, labels)
print("ctor isaxes=", leg.isaxes, "figure is fig:", leg.figure is fig)
if leg.isaxes is not False or leg.figure is not fig:
    print("FAIL ctor semantics")
    sys.exit(1)

leg2 = fig.legend()
print("fig.legend returned:", type(leg2).__name__, "in figure.legends:", leg2 in fig.legends)
ok = isinstance(leg2, Legend) and leg2 in fig.legends
sys.exit(0 if ok else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""Req3: Axes parent -> isaxes True, figure is axes.figure (not the axes), ax.legend works."""
import sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.legend import Legend

fig, ax = plt.subplots()
ax.plot([0, 1], [1, 0], label="ax")
handles, labels = ax.get_legend_handles_labels()

leg = Legend(ax, handles, labels)
print("isaxes=", leg.isaxes, "figure is ax.figure:", leg.figure is ax.figure,
      "figure is not ax:", leg.figure is not ax)
if leg.isaxes is not True or leg.figure is not ax.figure or leg.figure is ax:
    print("FAIL axes ctor semantics")
    sys.exit(1)

leg2 = ax.legend()
print("ax.legend returned Legend:", isinstance(leg2, Legend))
sys.exit(0 if isinstance(leg2, Legend) else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""Req4: invalid parent -> TypeError mentioning axes and figure-like object."""
import sys
import matplotlib
matplotlib.use("Agg")
from matplotlib.legend import Legend

class Bogus:
    pass

handles = []
labels = []
try:
    Legend(Bogus(), handles, labels)
    print("FAIL: no error raised for invalid parent")
    sys.exit(1)
except TypeError as e:
    msg = str(e).lower()
    print("TypeError:", e)
    ok = ("axes" in msg) and ("figure" in msg)
    if not ok:
        print("FAIL: message must mention axes and figure-like")
    sys.exit(0 if ok else 1)
except Exception as e:
    print("FAIL: wrong exception type", type(e).__name__, e)
    sys.exit(1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Positive control / Req1.1+1.2+1.3: Legend with SubFigure parent.
Constructor completes, isaxes False, figure is the subfigure (identity).
HOLDS on patched, FAILS at base (TypeError)."""
import sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.legend import Legend

fig = plt.figure()
subfigs = fig.subfigures(1, 2)
subfig = subfigs[0]
axs = subfig.subplots()
axs.plot([1, 2, 3], [1, 2, 3], label="line")
handles, labels = axs.get_legend_handles_labels()

try:
    leg = Legend(subfig, handles, labels)
except Exception as e:
    print("FAIL: construction raised", type(e).__name__, e)
    sys.exit(1)

print("constructed OK; isaxes=", leg.isaxes, "figure is subfig:", leg.figure is subfig)
ok = (leg.isaxes is False) and (leg.figure is subfig)
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Requirements: change Legend ctor parent check from isinstance(parent, Figure) to FigureBase so SubFigure is accepted as a figure-level legend parent.

Probes (all HOLD on gold-patched tree):
- probe_1 (Req1.1/1.2/1.3, POSITIVE CONTROL): Legend(subfig,...) constructs OK, isaxes==False, leg.figure is subfig. PATCHED exit0; BASE exit1 (TypeError 'Legend needs either Axes or Figure as parent'). Discriminates.
- probe_2 (Req1.4): subfig.legend() returns a Legend and registers it on subfig.legends. PATCHED exit0; BASE exit1 (TypeError).
- probe_3 (Req2): Figure parent -> isaxes False, figure is fig; fig.legend() returns+registers. HOLDS patched.
- probe_4 (Req3): Axes parent -> isaxes True, figure is ax.figure (not the axes); ax.legend() returns Legend. HOLDS patched.
- probe_5 (Req4.1/4.2): invalid parent raises TypeError with message mentioning both 'axes' and 'figure'. HOLDS patched.

Wrong-fix candidate (weak.diff): accepts SubFigure but routes it through the AXES branch (isaxes=True, set_figure(parent.figure)). This satisfies a lazy reading (subfig.legend works, no TypeError) but violates Req1.2/1.3. My suite REJECTS it: probe_1 fails under the candidate (observed isaxes=True, figure is subfig: False), while probes 2-5 pass. This demonstrates the suite discriminates a plausibly-wrong implementation.

All 5 probes hold on patched tree; positive control discriminates base vs patched; candidate patch rejected by probe_1. Verdict SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 5 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 5 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 5 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (5):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

_The 5 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts, and on this backend both roles put it through the same derivation: every block below is a requirement probe run on the gold-patched tree, and the `machine verdict:` line each role publishes above reports BOTH that its probes hold there and how many candidate patches the probe suite rejected — so the two roles re-ran ONE probe suite and each recorded its own outcome for every probe in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `probe_1.py` → holds on the patched tree (good)

Attack 2 — `probe_2.py` → holds on the patched tree (good)

Attack 3 — `probe_3.py` → holds on the patched tree (good)

Attack 4 — `probe_4.py` → holds on the patched tree (good)

Attack 5 — `probe_5.py` → holds on the patched tree (good)

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Positive control / Req1.1+1.2+1.3: Legend with SubFigure parent.
Constructor completes, isaxes False, figure is the subfigure (identity).
HOLDS on patched, FAILS at base (TypeError)."""
import sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.legend import Legend

fig = plt.figure()
subfigs = fig.subfigures(1, 2)
subfig = subfigs[0]
axs = subfig.subplots()
axs.plot([1, 2, 3], [1, 2, 3], label="line")
handles, labels = axs.get_legend_handles_labels()

try:
    leg = Legend(subfig, handles, labels)
except Exception as e:
    print("FAIL: construction raised", type(e).__name__, e)
    sys.exit(1)

print("constructed OK; isaxes=", leg.isaxes, "figure is subfig:", leg.figure is subfig)
ok = (leg.isaxes is False) and (leg.figure is subfig)
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Requirements: change Legend ctor parent check from isinstance(parent, Figure) to FigureBase so SubFigure is accepted as a figure-level legend parent.

Probes (all HOLD on gold-patched tree):
- probe_1 (Req1.1/1.2/1.3, POSITIVE CONTROL): Legend(subfig,...) constructs OK, isaxes==False, leg.figure is subfig. PATCHED exit0; BASE exit1 (TypeError 'Legend needs either Axes or Figure as parent'). Discriminates.
- probe_2 (Req1.4): subfig.legend() returns a Legend and registers it on subfig.legends. PATCHED exit0; BASE exit1 (TypeError).
- probe_3 (Req2): Figure parent -> isaxes False, figure is fig; fig.legend() returns+registers. HOLDS patched.
- probe_4 (Req3): Axes parent -> isaxes True, figure is ax.figure (not the axes); ax.legend() returns Legend. HOLDS patched.
- probe_5 (Req4.1/4.2): invalid parent raises TypeError with message mentioning both 'axes' and 'figure'. HOLDS patched.

Wrong-fix candidate (weak.diff): accepts SubFigure but routes it through the AXES branch (isaxes=True, set_figure(parent.figure)). This satisfies a lazy reading (subfig.legend works, no TypeError) but violates Req1.2/1.3. My suite REJECTS it: probe_1 fails under the candidate (observed isaxes=True, figure is subfig: False), while probes 2-5 pass. This demonstrates the suite discriminates a plausibly-wrong implementation.

All 5 probes hold on patched tree; positive control discriminates base vs patched; candidate patch rejected by probe_1. Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** The change is a 3-line isinstance(parent, Figure) -> isinstance(parent, FigureBase) swap plus updated TypeError text ('Legend needs either Axes or FigureBase as parent'). Requirements pin the exact changed observable boundary: figure-like acceptance (both Figure and SubFigure derive from FigureBase), the isaxes flag, figure-identity via set_figure, and the reject-message wording. Req 4.2's 'figure-like object' phrasing is consistent with the literal 'FigureBase' message string. No narrow-slice or invented-behavior defect found.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The gold edit changes the parent isinstance check in legend.py from Figure to FigureBase and updates the TypeError message; the only new test (test_subfigure_legend) builds a subfigure, plots a labelled line, calls subfig.legend(), and asserts leg.figure is subfig. The requirements describe all of this at the behavioral level without transmitting hidden-test/gold content: (1) No test names, file paths (tests/test_legend.py), function names, or parametrization ids appear. (2) The FAIL_TO_PASS assertion `leg.figure is subfig` is rendered as behavior in Req 1.3 ('record that same sub-figure object as its associated figure ... identity equality') — this is the natural specification of the fix, not quoted test code. (3) The invented identifier is the switch to FigureBase; Req 4.2 deliberately paraphrases the new error message as 'either an axes or a figure-like object' rather than leaking the verbatim 'FigureBase' token. (4) SubFigure/FigureBase/Figure and the reproduction (subfigures().subplots(), labelled artist, subfig.legend()) are all already PUBLIC in the problem_statement (which shows the traceback through legend.py:441 and the exact reproduction snippet) and the suggestion to check against FigureBase. Naming legend.py/figure.py and the classes is legitimate localization. The single F2P test means there is no parametrization enumeration to mirror. All requirement content is derivable from the public problem_statement or is a legitimate behavioral translation.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
