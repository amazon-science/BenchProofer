# P2 adversarial audit — matplotlib__matplotlib-13989

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
"""Req 1.3 (also 1.1): string bins 'auto' + range + density=True -> edges span [lo,hi].
This is the POSITIVE CONTROL: holds on patched, fails at base."""
import sys
import matplotlib
matplotlib.use("Agg")
import numpy as np
import matplotlib.pyplot as plt

rng = np.random.RandomState(0)
data = rng.normal(0.5, 5.0, size=2000)  # spread well outside [0,1]
lo, hi = 0.0, 1.0
fig, ax = plt.subplots()
n, bins, patches = ax.hist(data, "auto", range=(lo, hi), density=True)
print("first edge:", bins[0], "last edge:", bins[-1])
ok = np.isclose(bins[0], lo) and np.isclose(bins[-1], hi)
print("OK" if ok else "FAIL")
sys.exit(0 if ok else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""Req 1.1: single dataset, integer bins, range + density=True -> first/last edges = lo/hi."""
import sys
import matplotlib
matplotlib.use("Agg")
import numpy as np
import matplotlib.pyplot as plt

data = np.array([-10., -5., 0.2, 0.5, 0.7, 5., 20.])
lo, hi = 0.0, 1.0
fig, ax = plt.subplots()
n, bins, patches = ax.hist(data, bins=10, range=(lo, hi), density=True)
print("first edge:", bins[0], "last edge:", bins[-1], "nbins:", len(bins) - 1)
ok = np.isclose(bins[0], lo) and np.isclose(bins[-1], hi) and (len(bins) - 1 == 10)
print("OK" if ok else "FAIL")
sys.exit(0 if ok else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""Req 1.2: deprecated normed=True (density unset) + range -> edges span [lo,hi]."""
import sys
import warnings
import matplotlib
matplotlib.use("Agg")
import numpy as np
import matplotlib.pyplot as plt

data = np.array([-10., -5., 0.2, 0.5, 0.7, 5., 20.])
lo, hi = 0.0, 1.0
fig, ax = plt.subplots()
with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    n, bins, patches = ax.hist(data, bins=8, range=(lo, hi), normed=True)
print("first edge:", bins[0], "last edge:", bins[-1])
ok = np.isclose(bins[0], lo) and np.isclose(bins[-1], hi)
print("OK" if ok else "FAIL")
sys.exit(0 if ok else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""Req 2.1: density=True unstacked -> normalized so sum(value*binwidth)==1."""
import sys
import matplotlib
matplotlib.use("Agg")
import numpy as np
import matplotlib.pyplot as plt

rng = np.random.RandomState(1)
data = rng.normal(0.5, 5.0, size=3000)
lo, hi = 0.0, 1.0
fig, ax = plt.subplots()
n, bins, patches = ax.hist(data, bins=12, range=(lo, hi), density=True)
widths = np.diff(bins)
integral = np.sum(n * widths)
print("integral:", integral)
ok = np.isclose(integral, 1.0)
print("OK" if ok else "FAIL")
sys.exit(0 if ok else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""Req 3.2: stacked=True + density -> per-dataset density NOT forwarded; combined
area over stacked histograms == 1 (top curve integrates to 1)."""
import sys
import matplotlib
matplotlib.use("Agg")
import numpy as np
import matplotlib.pyplot as plt

rng = np.random.RandomState(2)
d1 = rng.normal(0.3, 0.2, size=1000)
d2 = rng.normal(0.7, 0.2, size=1000)
lo, hi = 0.0, 1.0
fig, ax = plt.subplots()
n, bins, patches = ax.hist([d1, d2], bins=10, range=(lo, hi),
                           density=True, stacked=True)
widths = np.diff(bins)
top = n[-1]  # topmost stacked cumulative curve
integral = np.sum(top * widths)
print("stacked top integral:", integral)
print("first/last edge:", bins[0], bins[-1])
ok = np.isclose(integral, 1.0) and np.isclose(bins[0], lo) and np.isclose(bins[-1], hi)
print("OK" if ok else "FAIL")
sys.exit(0 if ok else 1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
"""Req 3.1: non-density + explicit range still spans [lo,hi] (regression).
Req 3.3: multiple datasets share common edges constrained by range."""
import sys
import matplotlib
matplotlib.use("Agg")
import numpy as np
import matplotlib.pyplot as plt

rng = np.random.RandomState(3)
d1 = rng.normal(0.3, 3.0, size=800)
d2 = rng.normal(0.7, 3.0, size=800)
lo, hi = 0.0, 1.0
fig, ax = plt.subplots()
n, bins, patches = ax.hist([d1, d2], bins=9, range=(lo, hi), density=False)
print("first/last edge:", bins[0], bins[-1], "nbins:", len(bins) - 1)
ok = np.isclose(bins[0], lo) and np.isclose(bins[-1], hi) and (len(bins) - 1 == 9)
print("OK" if ok else "FAIL")
sys.exit(0 if ok else 1)
```

Attack 7 — `probe_7.py` → holds on the patched tree (good)

```python
"""Req 3.5: range not given, non-density -> edges derived from finite data extremes."""
import sys
import matplotlib
matplotlib.use("Agg")
import numpy as np
import matplotlib.pyplot as plt

data = np.array([2.0, 3.0, 4.0, 5.0, 8.0])
fig, ax = plt.subplots()
n, bins, patches = ax.hist(data, bins=6)
print("first/last edge:", bins[0], bins[-1])
ok = np.isclose(bins[0], data.min()) and np.isclose(bins[-1], data.max())
print("OK" if ok else "FAIL")
sys.exit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Req 1.3 (also 1.1): string bins 'auto' + range + density=True -> edges span [lo,hi].
This is the POSITIVE CONTROL: holds on patched, fails at base."""
import sys
import matplotlib
matplotlib.use("Agg")
import numpy as np
import matplotlib.pyplot as plt

rng = np.random.RandomState(0)
data = rng.normal(0.5, 5.0, size=2000)  # spread well outside [0,1]
lo, hi = 0.0, 1.0
fig, ax = plt.subplots()
n, bins, patches = ax.hist(data, "auto", range=(lo, hi), density=True)
print("first edge:", bins[0], "last edge:", bins[-1])
ok = np.isclose(bins[0], lo) and np.isclose(bins[-1], hi)
print("OK" if ok else "FAIL")
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Bug: `hist_kwargs = dict(density=density)` replaces the whole kwargs dict, discarding the previously-recorded `hist_kwargs['range'] = bin_range`. Gold fix: `hist_kwargs['density'] = density` (additive).

Probes (all HOLD on gold-patched tree):
- probe_1 (Req 1.3/1.1, POSITIVE CONTROL): 'auto' string bins + range=(0,1) + density=True -> edges [0.0,1.0]. Patched: OK. Base: VIOLATED (edges -14.7..16.4).
- probe_2 (Req 1.1): int bins + range + density=True -> edges 0.0/1.0, 10 bins. Patched OK; base VIOLATED (-10..20).
- probe_3 (Req 1.2): deprecated normed=True + range -> edges 0.0/1.0. Patched OK; base VIOLATED (-10..20).
- probe_4 (Req 2.1): density=True unstacked -> integral sum(n*width)==1. Patched OK (1.0).
- probe_5 (Req 3.2): stacked=True + density -> per-dataset density NOT forwarded, combined top curve integrates to 1 and edges span range. Patched OK.
- probe_6 (Req 3.1/3.3): multi-dataset non-density + range -> shared edges 0.0/1.0, 9 bins. Patched OK.
- probe_7 (Req 3.5): no range, non-density -> edges from data extremes (2.0/8.0). Patched OK.

Discriminating power: positive controls probe_1/2/3 FAIL at base and HOLD patched.

Candidate wrong-fix 'partial_drop_density' (weak.diff): replaces the buggy reassignment with `pass` — this is the lazy reading of Req 1.4 ('do not overwrite range') that satisfies range-preservation but forgets Req 2.3 (density must still be forwarded). Under it: probe_1 HOLDS (range preserved) and probe_5 HOLDS, but probe_4 is REJECTED (integral=19.0, not normalized). So the suite discriminates the too-weak partial fix; NOT a TOO-WEAK finding. Verdict SOUND: 7 probes hold patched, positive control discriminates, and a probe-conforming-only partial patch is rejected by the density-normalization probe.

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
"""Req 1.3 (also 1.1): string bins 'auto' + range + density=True -> edges span [lo,hi].
This is the POSITIVE CONTROL: holds on patched, fails at base."""
import sys
import matplotlib
matplotlib.use("Agg")
import numpy as np
import matplotlib.pyplot as plt

rng = np.random.RandomState(0)
data = rng.normal(0.5, 5.0, size=2000)  # spread well outside [0,1]
lo, hi = 0.0, 1.0
fig, ax = plt.subplots()
n, bins, patches = ax.hist(data, "auto", range=(lo, hi), density=True)
print("first edge:", bins[0], "last edge:", bins[-1])
ok = np.isclose(bins[0], lo) and np.isclose(bins[-1], hi)
print("OK" if ok else "FAIL")
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Bug: `hist_kwargs = dict(density=density)` replaces the whole kwargs dict, discarding the previously-recorded `hist_kwargs['range'] = bin_range`. Gold fix: `hist_kwargs['density'] = density` (additive).

Probes (all HOLD on gold-patched tree):
- probe_1 (Req 1.3/1.1, POSITIVE CONTROL): 'auto' string bins + range=(0,1) + density=True -> edges [0.0,1.0]. Patched: OK. Base: VIOLATED (edges -14.7..16.4).
- probe_2 (Req 1.1): int bins + range + density=True -> edges 0.0/1.0, 10 bins. Patched OK; base VIOLATED (-10..20).
- probe_3 (Req 1.2): deprecated normed=True + range -> edges 0.0/1.0. Patched OK; base VIOLATED (-10..20).
- probe_4 (Req 2.1): density=True unstacked -> integral sum(n*width)==1. Patched OK (1.0).
- probe_5 (Req 3.2): stacked=True + density -> per-dataset density NOT forwarded, combined top curve integrates to 1 and edges span range. Patched OK.
- probe_6 (Req 3.1/3.3): multi-dataset non-density + range -> shared edges 0.0/1.0, 9 bins. Patched OK.
- probe_7 (Req 3.5): no range, non-density -> edges from data extremes (2.0/8.0). Patched OK.

Discriminating power: positive controls probe_1/2/3 FAIL at base and HOLD patched.

Candidate wrong-fix 'partial_drop_density' (weak.diff): replaces the buggy reassignment with `pass` — this is the lazy reading of Req 1.4 ('do not overwrite range') that satisfies range-preservation but forgets Req 2.3 (density must still be forwarded). Under it: probe_1 HOLDS (range preserved) and probe_5 HOLDS, but probe_4 is REJECTED (integral=19.0, not normalized). So the suite discriminates the too-weak partial fix; NOT a TOO-WEAK finding. Verdict SOUND: 7 probes hold patched, positive control discriminates, and a probe-conforming-only partial patch is rejected by the density-normalization probe.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Modeling boundary is correct: Req 1.4 pins the additive-record semantics (the literal patch), Req 1.1-1.3 pin the observable range-governs-edges consequence, Req 2 preserves density normalization, Req 3.2 correctly reflects the `if density and not stacked` guard (stacked not forwarded per-dataset), Req 3.3-3.5 assert unchanged non-density/multi-dataset paths. No mandated-but-absent, forbidden-but-present, or invented behavior found. Requirements consistent with issue and fix.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The only FAIL_TO_PASS test (test_hist_range_and_density) asserts bins[0]==0 and bins[-1]==1 for plt.hist(np.random.rand(10), 'auto', range=(0,1), density=True) — but that exact reproduction snippet and expected outcome ('first value is 0 and the last one is 1') are already in the PUBLIC problem_statement, so the requirements' matching example (lines 14-15, 42-44) leaks nothing beyond public content. The gold edit (hist_kwargs['density']=density replacing hist_kwargs=dict(density=density)) is described behaviorally as 'additive vs replaces the whole mapping' (lines 17-19, 45-47) without quoting code or using the literal variable name hist_kwargs. No test names/paths/ids, no fix-invented identifiers. Module/function naming (Axes.hist, _axes.py) is legitimate localization. Enumerated cases (density/normed/stacked/multi-dataset) describe general hist behavior derivable from the public API and source, not the single hidden test's parametrization.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
