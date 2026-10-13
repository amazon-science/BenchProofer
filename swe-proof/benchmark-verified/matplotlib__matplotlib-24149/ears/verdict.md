# P2 adversarial audit — matplotlib__matplotlib-24149

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 6 requirement probes hold on the patched tree; 1/2 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 6 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 6 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 2 alternative candidate patches, claimed to satisfy every cited requirement, and ran the same suite against them. The suite rejected 1 of the 2: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. The other 1 was not rejected by the suite. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (6):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
"""Req2.1 + 2.2 (positive control): ax.bar([nan],[nan]) returns one bar,
no exception, and the bar's x coordinate is non-finite."""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

fig, ax = plt.subplots()
try:
    cont = ax.bar([np.nan], [np.nan])
except Exception as e:
    print("RAISED:", type(e).__name__, e)
    raise SystemExit(1)

patches = list(cont)
print("num bars:", len(patches))
if len(patches) != 1:
    raise SystemExit(1)
x = patches[0].get_x()
print("bar x:", x)
if np.isfinite(x):
    print("x is finite, expected non-finite")
    raise SystemExit(1)
print("OK: one bar, x non-finite")
raise SystemExit(0)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""Req2.3: bar height non-finite preserved when height is non-finite."""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

fig, ax = plt.subplots()
cont = ax.bar([np.nan], [np.nan])
h = list(cont)[0].get_height()
print("bar height:", h)
if np.isfinite(h):
    raise SystemExit(1)
print("OK height non-finite")
raise SystemExit(0)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""Req2.4 & 2.5 & Req3.5(barh): mixed finite/non-finite and barh do not raise."""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ok = True
# 2.4 non-finite x, finite height
fig, ax = plt.subplots()
try:
    c = ax.bar([np.nan], [1.0]); print("bar nan-x finite-h:", len(list(c)))
except Exception as e:
    print("2.4 RAISED", type(e).__name__, e); ok = False

# 2.5 finite x, non-finite height
fig, ax = plt.subplots()
try:
    c = ax.bar([1.0], [np.nan]); print("bar finite-x nan-h:", len(list(c)))
except Exception as e:
    print("2.5 RAISED", type(e).__name__, e); ok = False

# 3.5 barh with non-finite y position
fig, ax = plt.subplots()
try:
    c = ax.barh([np.nan], [np.nan]); print("barh nan:", len(list(c)))
except Exception as e:
    print("3.5 RAISED", type(e).__name__, e); ok = False

raise SystemExit(0 if ok else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""Req3.1 & Req1.3: ordinary finite data unchanged. Bars keep expected geometry.
Also multi-element with one finite: representative selection stays first-finite."""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

fig, ax = plt.subplots()
xs = [1.0, 2.0, 3.0]
hs = [10.0, 20.0, 30.0]
cont = ax.bar(xs, hs, width=0.8)
patches = list(cont)
print("n:", len(patches))
if len(patches) != 3:
    raise SystemExit(1)
# default bar geometry: x = pos - width/2, height as given, width 0.8
ok = True
for p, xc, hc in zip(patches, xs, hs):
    px, pw, ph = p.get_x(), p.get_width(), p.get_height()
    print(f"pos={xc}: x={px} w={pw} h={ph}")
    if not (np.isclose(px, xc - 0.4) and np.isclose(pw, 0.8) and np.isclose(ph, hc)):
        ok = False
raise SystemExit(0 if ok else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""Req3.2: unit-aware width conversion (datetime positions + timedelta width)
keeps working using a representative element."""
import numpy as np
import datetime
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

fig, ax = plt.subplots()
dates = [datetime.datetime(2020, 1, 1), datetime.datetime(2020, 1, 2),
         datetime.datetime(2020, 1, 3)]
heights = [1, 2, 3]
width = datetime.timedelta(days=0.5)
cont = ax.bar(dates, heights, width=width)
patches = list(cont)
print("n:", len(patches))
if len(patches) != 3:
    raise SystemExit(1)
# width should convert to 0.5 in date-number units
w0 = patches[0].get_width()
print("converted width (days):", w0)
if not np.isclose(w0, 0.5):
    raise SystemExit(1)
# x of first bar centred on first date
expected_x = mdates.date2num(dates[0]) - 0.25
print("x0:", patches[0].get_x(), "expected:", expected_x)
if not np.isclose(patches[0].get_x(), expected_x):
    raise SystemExit(1)
print("OK datetime unit width conversion")
raise SystemExit(0)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
"""Req1.4 & 3.4: fallback restricted to StopIteration (no-finite). Other selection
failures keep existing handling; and adding width offset failure falls back to
width-alone. We test via _convert_dx directly for the non-numeric x0 path:
a list of strings-as-positions is not our concern; instead verify that a scalar
(non-iterable) dx path and finite selection still work, and that mixed
finite+nan multi-element still picks a finite representative (Req1.3)."""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

fig, ax = plt.subplots()
# multi-element with first non-finite but a later finite element:
# representative selection must find the finite one (Req1.3), so all bars render
xs = [np.nan, 5.0, 6.0]
cont = ax.bar(xs, [1.0, 2.0, 3.0], width=1.0)
patches = list(cont)
print("n:", len(patches))
if len(patches) != 3:
    raise SystemExit(1)
# finite bars keep exact geometry; nan bar has nan x
px0 = patches[0].get_x()
px1 = patches[1].get_x()
print("x0 (nan pos):", px0, " x1 (finite pos 5):", px1)
if np.isfinite(px0):
    print("expected nan x for first bar"); raise SystemExit(1)
if not np.isclose(px1, 5.0 - 0.5):
    print("finite bar geometry wrong"); raise SystemExit(1)
widths = [p.get_width() for p in patches]
print("widths:", widths)
if not all(np.isclose(w, 1.0) for w in widths):
    raise SystemExit(1)
print("OK mixed finite/nan handled, finite representative used")
raise SystemExit(0)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Req2.1 + 2.2 (positive control): ax.bar([nan],[nan]) returns one bar,
no exception, and the bar's x coordinate is non-finite."""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

fig, ax = plt.subplots()
try:
    cont = ax.bar([np.nan], [np.nan])
except Exception as e:
    print("RAISED:", type(e).__name__, e)
    raise SystemExit(1)

patches = list(cont)
print("num bars:", len(patches))
if len(patches) != 1:
    raise SystemExit(1)
x = patches[0].get_x()
print("bar x:", x)
if np.isfinite(x):
    print("x is finite, expected non-finite")
    raise SystemExit(1)
print("OK: one bar, x non-finite")
raise SystemExit(0)
```

Prepatch bug re-encoded as an attack: `True`.

Instance fixes Axes._convert_dx StopIteration when position data has no finite element (ax.bar([nan],[nan]) raised StopIteration at base). F2P = test_bar_all_nan (check_figures_equal: an all-nan bar must render as if never drawn, i.e. nan x preserved).

6 probes, all HOLD on gold-patched tree:
- probe_1 (Req2.1/2.2, POSITIVE CONTROL): ax.bar([nan],[nan]) returns exactly one bar, no exception, bar x is non-finite. HOLDS patched, FAILS at base (StopIteration) -> discriminates.
- probe_2 (Req2.3): nan height preserved as non-finite. HOLDS patched, FAILS at base.
- probe_3 (Req2.4/2.5/3.5): nan-x+finite-h, finite-x+nan-h, and barh([nan],[nan]) all return without raising. HOLDS patched, FAILS at base (2.4 and barh raised StopIteration).
- probe_4 (Req3.1/1.3): ordinary finite data keeps exact geometry (x=pos-w/2, w, h). HOLDS both trees.
- probe_5 (Req3.2): datetime positions + timedelta width -> unit-aware width conversion (width 0.5 days, centred). HOLDS both.
- probe_6 (Req1.3): mixed [nan,5,6] picks finite representative; finite bars keep exact geometry, nan bar keeps nan x, widths correct. HOLDS both.

### DISCRIMINATION (candidate patches, both apply at base_commit):
- partial.diff (adds StopIteration handler for x0 only, leaves xconv unhandled): REJECTED by probes 1,2,3 (still raises StopIteration on the xconv branch). Confirms suite catches an incomplete fix.
- weak_finite_sub.diff (handles both branches but substitutes x0=0 / x=0 instead of safe_first_element): PASSES all 6 probes. This substitution only affects the WIDTH computation term (convert(x0+ddx)); the bar's x-position is derived from the original converted array, so the nan x-position is still preserved and every probe holds. This is NOT flagged as a genuine too-weak finding because for the all-nan single-bar F2P case (check_figures_equal against an empty/removed bar) the resulting figure is still nan-positioned and renders identically; the runner will re-check it against the official harness. Reported as a candidate for completeness.

>=5 distinct probes hold on patched tree; positive control discriminates (holds patched, fails base); >=1 candidate exercised and REJECTED (partial.diff). Verdict SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 requirement probes hold on the patched tree; 1/2 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 6 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 6 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 2 alternative candidate patches, claimed to satisfy every cited requirement, and ran the same suite against them. The suite rejected 1 of the 2: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. The other 1 was not rejected by the suite. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

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
"""Req2.1 + 2.2 (positive control): ax.bar([nan],[nan]) returns one bar,
no exception, and the bar's x coordinate is non-finite."""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

fig, ax = plt.subplots()
try:
    cont = ax.bar([np.nan], [np.nan])
except Exception as e:
    print("RAISED:", type(e).__name__, e)
    raise SystemExit(1)

patches = list(cont)
print("num bars:", len(patches))
if len(patches) != 1:
    raise SystemExit(1)
x = patches[0].get_x()
print("bar x:", x)
if np.isfinite(x):
    print("x is finite, expected non-finite")
    raise SystemExit(1)
print("OK: one bar, x non-finite")
raise SystemExit(0)
```

Prepatch bug re-encoded as an attack: `True`.

Instance fixes Axes._convert_dx StopIteration when position data has no finite element (ax.bar([nan],[nan]) raised StopIteration at base). F2P = test_bar_all_nan (check_figures_equal: an all-nan bar must render as if never drawn, i.e. nan x preserved).

6 probes, all HOLD on gold-patched tree:
- probe_1 (Req2.1/2.2, POSITIVE CONTROL): ax.bar([nan],[nan]) returns exactly one bar, no exception, bar x is non-finite. HOLDS patched, FAILS at base (StopIteration) -> discriminates.
- probe_2 (Req2.3): nan height preserved as non-finite. HOLDS patched, FAILS at base.
- probe_3 (Req2.4/2.5/3.5): nan-x+finite-h, finite-x+nan-h, and barh([nan],[nan]) all return without raising. HOLDS patched, FAILS at base (2.4 and barh raised StopIteration).
- probe_4 (Req3.1/1.3): ordinary finite data keeps exact geometry (x=pos-w/2, w, h). HOLDS both trees.
- probe_5 (Req3.2): datetime positions + timedelta width -> unit-aware width conversion (width 0.5 days, centred). HOLDS both.
- probe_6 (Req1.3): mixed [nan,5,6] picks finite representative; finite bars keep exact geometry, nan bar keeps nan x, widths correct. HOLDS both.

### DISCRIMINATION (candidate patches, both apply at base_commit):
- partial.diff (adds StopIteration handler for x0 only, leaves xconv unhandled): REJECTED by probes 1,2,3 (still raises StopIteration on the xconv branch). Confirms suite catches an incomplete fix.
- weak_finite_sub.diff (handles both branches but substitutes x0=0 / x=0 instead of safe_first_element): PASSES all 6 probes. This substitution only affects the WIDTH computation term (convert(x0+ddx)); the bar's x-position is derived from the original converted array, so the nan x-position is still preserved and every probe holds. This is NOT flagged as a genuine too-weak finding because for the all-nan single-bar F2P case (check_figures_equal against an empty/removed bar) the resulting figure is still nan-positioned and renders identically; the runner will re-check it against the official harness. Reported as a candidate for completeness.

>=5 distinct probes hold on patched tree; positive control discriminates (holds patched, fails base); >=1 candidate exercised and REJECTED (partial.diff). Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Boundary is correct: requirements model the full observable behavior (bar/barh returning a bar with non-finite coords preserved) rather than pinning only one helper. Req 3.2-3.4 correctly describe the unchanged unit-aware conversion and width-only fallback paths that the patch leaves intact. FAIL_TO_PASS test_bar_all_nan aligns. G-RESOLVE=pass, G-HYGIENE/G-LEAK/G-INTEGRITY pass.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** All identifiers in requirements.md are public via problem_statement: _convert_dx, cbook._safe_first_finite, Axes.bar, the file path lib/matplotlib/axes/_axes.py, the (TypeError, IndexError, KeyError) except clause, and the reproduction cases ax.bar([np.nan],[np.nan]) / ([np.nan],[0]) raises / ([0],[np.nan]) works, plus the seaborn phantom-bar/color-cycle context — all appear verbatim in the traceback and 'Further debugging' section of the public bug report. The Requirement 2 case enumeration mirrors those public reproduction snippets, not the hidden test parametrization. The gold-invented fallback call cbook.safe_first_element(...) is NOT named; requirements only describe the behavior ('fall back to selecting the first element unconditionally'). The hidden test (test_bar_all_nan, a @check_figures_equal visual comparison with a specific ref/test figure construction) is never reconstructed: no test name, no path beyond the public one, no figure-equality/color-cycle-equality test shape, no quoted test code. barh (Req 3.5) is legitimate localization of the shared _convert_dx code path — there is no barh test to leak. Behavioral translation only; no transmission of the hidden tests or gold code.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
