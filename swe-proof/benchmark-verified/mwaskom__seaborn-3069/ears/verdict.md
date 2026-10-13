# P2 adversarial audit — mwaskom__seaborn-3069

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
import sys
# shim for pandas/seaborn version incompat (mode.use_inf_as_null)
try:
    import pandas as pd
    try:
        pd.set_option("mode.use_inf_as_null", False)
    except Exception:
        try:
            pd._config.config.register_option("mode.use_inf_as_null", False)
        except Exception:
            pass
except Exception:
    pass

import matplotlib
matplotlib.use("Agg")
import seaborn.objects as so

p = so.Plot(x=["a", "b", "c"], y=[1, 2, 3])
ax = p.plot()._figure.axes[0]
xlim = ax.get_xlim()
print("nominal x, 3 cats -> xlim =", xlim)
ok = xlim == (-0.5, 2.5)
print("PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
import sys
try:
    import pandas as pd
    try:
        pd.set_option("mode.use_inf_as_null", False)
    except Exception:
        try:
            pd._config.config.register_option("mode.use_inf_as_null", False)
        except Exception:
            pass
except Exception:
    pass

import matplotlib
matplotlib.use("Agg")
import seaborn.objects as so

# Req 1.3 / 1.4: nominal y axis with 3 categories -> ylim reversed (2.5, -0.5)
p = so.Plot(x=[1, 2, 3], y=["a", "b", "c"])
ax = p.plot()._figure.axes[0]
ylim = ax.get_ylim()
print("nominal y, 3 cats -> ylim =", ylim)
ok = ylim == (2.5, -0.5)
print("PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
import sys
try:
    import pandas as pd
    try:
        pd.set_option("mode.use_inf_as_null", False)
    except Exception:
        try:
            pd._config.config.register_option("mode.use_inf_as_null", False)
        except Exception:
            pass
except Exception:
    pass

import matplotlib
matplotlib.use("Agg")
import seaborn as sns
import seaborn.objects as so

# Req 2: grid hidden on nominal axis even when style would show one.
sns.set_theme(style="whitegrid")  # a grid-showing style
p = so.Plot(x=["a", "b", "c"], y=[1, 2, 3])
ax = p.plot()._figure.axes[0]
xgrid_vis = [g.get_visible() for g in ax.xaxis.get_gridlines()]
print("x gridlines visibility:", xgrid_vis)
ok = not any(xgrid_vis)
print("PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
import sys
try:
    import pandas as pd
    try:
        pd.set_option("mode.use_inf_as_null", False)
    except Exception:
        try:
            pd._config.config.register_option("mode.use_inf_as_null", False)
        except Exception:
            pass
except Exception:
    pass

import matplotlib
matplotlib.use("Agg")
import seaborn.objects as so

# Req 3.2 / 3.3: user-pinned limits on nominal axis are honored verbatim
# (NOT replaced by categorical extent, NOT reversed for y).
lim = (-1, 2.1)
px = so.Plot(x=["a", "b", "c"], y=[1, 2, 3]).limit(x=lim)
axx = px.plot()._figure.axes[0]
xlim = axx.get_xlim()
print("nominal x with user limit -> xlim =", xlim)

py = so.Plot(x=[1, 2, 3], y=["a", "b", "c"]).limit(y=lim)
axy = py.plot()._figure.axes[0]
ylim = axy.get_ylim()
print("nominal y with user limit -> ylim =", ylim)

ok = (xlim == lim) and (ylim == lim)
print("PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
import sys
try:
    import pandas as pd
    try:
        pd.set_option("mode.use_inf_as_null", False)
    except Exception:
        try:
            pd._config.config.register_option("mode.use_inf_as_null", False)
        except Exception:
            pass
except Exception:
    pass

import matplotlib
matplotlib.use("Agg")
import seaborn as sns
import seaborn.objects as so

# Req 4.1: numeric (non-nominal) axes are NOT pinned to categorical extent
# and their grid is NOT hidden when the style shows one.
sns.set_theme(style="whitegrid")
p = so.Plot(x=[1, 2, 3], y=[10, 20, 30])
ax = p.plot()._figure.axes[0]
xlim = ax.get_xlim()
# categorical extent for 3 ticks would be (-0.5, 2.5); numeric must differ
xgrid_vis = [g.get_visible() for g in ax.xaxis.get_gridlines()]
print("numeric x -> xlim =", xlim, "grid visible any =", any(xgrid_vis))
not_categorical = xlim != (-0.5, 2.5)
grid_shown = any(xgrid_vis)
ok = not_categorical and grid_shown
print("PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
import sys
try:
    import pandas as pd
    try:
        pd.set_option("mode.use_inf_as_null", False)
    except Exception:
        try:
            pd._config.config.register_option("mode.use_inf_as_null", False)
        except Exception:
            pass
except Exception:
    pass

import matplotlib
matplotlib.use("Agg")
from matplotlib.figure import Figure
import seaborn.objects as so

# Req 4.4: keep producing a valid figure for numeric / log-scaled axes without error.
# log-scaled numeric axis must not be pinned to categorical extent.
p = so.Plot(x=[1, 10, 100], y=[1, 2, 3]).scale(x="log")
fig = p.plot()._figure
ax = fig.axes[0]
xlim = ax.get_xlim()
print("log x -> scale =", ax.get_xscale(), "xlim =", xlim)
# valid figure produced without error; log axis not pinned to categorical extent
ok = isinstance(fig, Figure) and ax.get_xscale() != "linear" and xlim != (-0.5, 2.5)
print("PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
import sys
# shim for pandas/seaborn version incompat (mode.use_inf_as_null)
try:
    import pandas as pd
    try:
        pd.set_option("mode.use_inf_as_null", False)
    except Exception:
        try:
            pd._config.config.register_option("mode.use_inf_as_null", False)
        except Exception:
            pass
except Exception:
    pass

import matplotlib
matplotlib.use("Agg")
import seaborn.objects as so

p = so.Plot(x=["a", "b", "c"], y=[1, 2, 3])
ax = p.plot()._figure.axes[0]
xlim = ax.get_xlim()
print("nominal x, 3 cats -> xlim =", xlim)
ok = xlim == (-0.5, 2.5)
print("PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Probes cover the four requirements of the EARS bundle for mwaskom__seaborn-3069 (nominal-scale axis treatment in Plotter._finalize_figure). All 6 probes use a pandas mode.use_inf_as_null shim for an unrelated version incompat and run in the instance image via nl_attack.

Probe->criterion->results (PATCHED / BASE):
- probe_1 (Req 1.2/1.4): nominal x, 3 cats -> xlim exactly (-0.5, 2.5). PATCHED HOLDS; BASE VIOLATED (base gives ~(-0.055,0.055)). POSITIVE CONTROL.
- probe_2 (Req 1.3/1.4): nominal y, 3 cats -> ylim reversed (2.5, -0.5). PATCHED HOLDS; BASE VIOLATED.
- probe_3 (Req 2): with whitegrid style, nominal x gridlines all invisible. PATCHED HOLDS; BASE VIOLATED (grid visible).
- probe_4 (Req 3.2/3.3): user-pinned limit (-1,2.1) honored verbatim on nominal x AND y (y NOT reversed). PATCHED HOLDS.
- probe_5 (Req 4.1): numeric x axis NOT pinned to categorical extent and grid shown under whitegrid. PATCHED HOLDS.
- probe_6 (Req 4.4): log-scaled numeric axis produces a valid Figure, scale != linear, not pinned to categorical extent. PATCHED HOLDS.

Discrimination: positive control probe_1 fails at base and holds patched (prepatch reproduced). Wrong-fix candidate weak_no_yreverse.diff (pins extent + hides grid but OMITS the y-axis reversal of Req 1.3) is REJECTED by probe_2 (ylim comes out (-0.5,2.5) instead of (2.5,-0.5)); all other probes still hold. This demonstrates the suite discriminates a requirements-violating implementation, so no TOO-WEAK finding. Verdict SOUND: 6 probes hold patched, positive control discriminates base vs patched, and >=1 wrong candidate is rejected.

Note (informational, not affecting G-EQ soundness): the bundle's own G-PANEL-3 flagged a LEAKAGE concern that Req 3.2/3.3 embed the arbitrary hidden-test fixture pair (-1, 2.1) verbatim; probe_4 deliberately reuses that same pair since it is the value the spec pins.

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
import sys
# shim for pandas/seaborn version incompat (mode.use_inf_as_null)
try:
    import pandas as pd
    try:
        pd.set_option("mode.use_inf_as_null", False)
    except Exception:
        try:
            pd._config.config.register_option("mode.use_inf_as_null", False)
        except Exception:
            pass
except Exception:
    pass

import matplotlib
matplotlib.use("Agg")
import seaborn.objects as so

p = so.Plot(x=["a", "b", "c"], y=[1, 2, 3])
ax = p.plot()._figure.axes[0]
xlim = ax.get_xlim()
print("nominal x, 3 cats -> xlim =", xlim)
ok = xlim == (-0.5, 2.5)
print("PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Probes cover the four requirements of the EARS bundle for mwaskom__seaborn-3069 (nominal-scale axis treatment in Plotter._finalize_figure). All 6 probes use a pandas mode.use_inf_as_null shim for an unrelated version incompat and run in the instance image via nl_attack.

Probe->criterion->results (PATCHED / BASE):
- probe_1 (Req 1.2/1.4): nominal x, 3 cats -> xlim exactly (-0.5, 2.5). PATCHED HOLDS; BASE VIOLATED (base gives ~(-0.055,0.055)). POSITIVE CONTROL.
- probe_2 (Req 1.3/1.4): nominal y, 3 cats -> ylim reversed (2.5, -0.5). PATCHED HOLDS; BASE VIOLATED.
- probe_3 (Req 2): with whitegrid style, nominal x gridlines all invisible. PATCHED HOLDS; BASE VIOLATED (grid visible).
- probe_4 (Req 3.2/3.3): user-pinned limit (-1,2.1) honored verbatim on nominal x AND y (y NOT reversed). PATCHED HOLDS.
- probe_5 (Req 4.1): numeric x axis NOT pinned to categorical extent and grid shown under whitegrid. PATCHED HOLDS.
- probe_6 (Req 4.4): log-scaled numeric axis produces a valid Figure, scale != linear, not pinned to categorical extent. PATCHED HOLDS.

Discrimination: positive control probe_1 fails at base and holds patched (prepatch reproduced). Wrong-fix candidate weak_no_yreverse.diff (pins extent + hides grid but OMITS the y-axis reversal of Req 1.3) is REJECTED by probe_2 (ylim comes out (-0.5,2.5) instead of (2.5,-0.5)); all other probes still hold. This demonstrates the suite discriminates a requirements-violating implementation, so no TOO-WEAK finding. Verdict SOUND: 6 probes hold patched, positive control discriminates base vs patched, and >=1 wrong candidate is rejected.

Note (informational, not affecting G-EQ soundness): the bundle's own G-PANEL-3 flagged a LEAKAGE concern that Req 3.2/3.3 embed the arbitrary hidden-test fixture pair (-1, 2.1) verbatim; probe_4 deliberately reuses that same pair since it is the value the spec pins.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Patch adds nominal special-casing in Plotter._finalize_figure: axis_obj.grid(False, which='both'); when axis_key not in p._limits, nticks=len(get_major_ticks()), lo,hi=-.5,nticks-.5, swapped for y, then set_?lim(lo,hi,auto=None). The requirements pin exactly this changed observable behavior at the correct modeling boundary — the full changed behavior (limits, y-reversal, grid suppression, user-limit precedence, non-nominal untouched), not a narrow slice or single helper. Req 1.5's 'suppress auto re-margining' faithfully maps to auto=None. Probe run in instance image with a pandas mode.use_inf_as_null register shim to bypass an unrelated pandas/seaborn version incompatibility; all six observable requirement claims confirmed HOLDS on patched (exit 0). Note: the specific pair (-1, 2.1) in Req 3.2/3.3 is a leakage concern (correctly flagged by G-PANEL-3), NOT a faithfulness defect — that exact pair is behaviorally consistent with the patched code.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** All three behaviors (±0.5 extent, hidden grid, inverted y) are already in the PUBLIC problem_statement. Requirement 1.4's worked example 'three categories -> (-0.5, 2.5)' and '(2.5, -0.5)' is arithmetic directly derivable from the public '+/- 0.5 from first and last tick' description (category positions 0,1,2), not from the hidden test. No test names/paths/ids (test_nominal_x_axis_tweaks, test_nominal_y_axis_tweaks), no quoted test/gold code (get_major_ticks, get_gridlines, auto=None), no test value (-1, 2.1), and no fix-invented identifiers appear. Naming _finalize_figure, Nominal, ax.xaxis/ax.yaxis is legitimate change localization. Requirement 3 describes user-limit-override behavior generally without the specific parametrized values. Behavioral translation only.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
