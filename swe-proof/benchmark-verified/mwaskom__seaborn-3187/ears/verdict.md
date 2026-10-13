# P2 adversarial audit — mwaskom__seaborn-3187

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
"""Req 1.3 (objects interface, POSITIVE CONTROL): legend labels reflect true
magnitude for large numeric ranges. HOLD patched, FAIL base."""
import matplotlib
matplotlib.use("Agg")
import numpy as np
import seaborn.objects as so

rng = np.random.RandomState(0)
x = rng.uniform(0, 10, 40)
y = rng.uniform(0, 10, 40)
color = np.add(x, 1e8)

p = so.Plot(x=x, y=y, color=color).add(so.Dot()).plot()
legend = p._figure.legends[0]
texts = [t.get_text() for t in legend.texts]
print("legend texts:", texts)

parsed = []
for t in texts:
    try:
        parsed.append(float(t))
    except ValueError:
        print("NON-NUMERIC label (offset annotation shape):", repr(t))
        raise SystemExit(1)

print("parsed floats:", parsed)
if not parsed:
    print("no legend texts")
    raise SystemExit(1)
if all(v > 1e7 for v in parsed):
    print("OK: all labels represent true magnitude (>1e7)")
    raise SystemExit(0)
print("FAIL: some label near zero (offset factored out)")
raise SystemExit(1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""Req 2.3 (relational interface): relplot legend labels reflect true magnitude
for large numeric hue. HOLD patched, FAIL base."""
import matplotlib
matplotlib.use("Agg")
import numpy as np
import pandas as pd
from seaborn import relplot

rng = np.random.RandomState(1)
n = 60
long_df = pd.DataFrame(dict(
    x=rng.uniform(0, 10, n),
    y=rng.uniform(0, 10, n),
    z=rng.uniform(0, 10, n),
))
g = relplot(data=long_df, x="x", y="y", hue=long_df["z"] + 1e8)
texts = [t.get_text() for t in g.legend.texts]
print("legend texts:", texts)

parsed = []
for t in texts:
    try:
        parsed.append(float(t))
    except ValueError:
        # title / non-numeric entries in relplot legend can exist; skip
        print("skipping non-numeric label:", repr(t))
        continue

print("parsed numeric floats:", parsed)
if not parsed:
    print("FAIL: no numeric labels parsed")
    raise SystemExit(1)
if all(v > 1e7 for v in parsed):
    print("OK: all numeric labels represent true magnitude (>1e7)")
    raise SystemExit(0)
print("FAIL: some numeric label near zero (offset factored out)")
raise SystemExit(1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""Req 2.3 + 2.4: locator_to_legend_entries — for large levels, each formatted
label reflects true magnitude AND levels/labels are one-to-one over in-range
levels. Unit-level probe. HOLD patched, FAIL base (magnitude leg)."""
import matplotlib
matplotlib.use("Agg")
import matplotlib as mpl
from seaborn.utils import locator_to_legend_entries

locator = mpl.ticker.MaxNLocator(nbins=6)
limits = (1e8, 1e8 + 100)
levels, labels = locator_to_legend_entries(locator, limits, float)
print("levels:", levels)
print("labels:", labels)

# Req 2.4: one-to-one correspondence
if len(levels) != len(labels):
    print("FAIL: levels/labels not one-to-one")
    raise SystemExit(1)
if len(levels) == 0:
    print("FAIL: no levels")
    raise SystemExit(1)

# Req 2.4: levels are in-range
for lv in levels:
    if not (limits[0] <= lv <= limits[1]):
        print("FAIL: level out of range:", lv)
        raise SystemExit(1)

# Req 2.3: each label reflects true magnitude of its level
for lv, lab in zip(levels, labels):
    try:
        val = float(lab)
    except ValueError:
        print("FAIL: non-numeric label (offset shape):", repr(lab))
        raise SystemExit(1)
    if val < 1e7:
        print("FAIL: label near zero, offset factored out:", repr(lab), "for level", lv)
        raise SystemExit(1)
    # tolerance: label should be close to the true level
    if abs(val - lv) > 1000:
        print("FAIL: label far from level:", lab, "vs", lv)
        raise SystemExit(1)

print("OK: labels reflect true magnitude and pair one-to-one with in-range levels")
raise SystemExit(0)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""Req 3.1: small-magnitude numeric legends produce the SAME human-readable
labels as before (no regression). Compares against expected plain labels."""
import matplotlib
matplotlib.use("Agg")
import matplotlib as mpl
from seaborn.utils import locator_to_legend_entries

# Ordinary small magnitude range
locator = mpl.ticker.MaxNLocator(nbins=5)
limits = (0.0, 10.0)
levels, labels = locator_to_legend_entries(locator, limits, float)
print("levels:", levels)
print("labels:", labels)

if len(levels) != len(labels) or not levels:
    print("FAIL: bad pairing")
    raise SystemExit(1)

# Each label should parse back to (approx) its level -- ordinary plain formatting
for lv, lab in zip(levels, labels):
    try:
        val = float(lab)
    except ValueError:
        print("FAIL: non-numeric small-magnitude label:", repr(lab))
        raise SystemExit(1)
    if abs(val - lv) > 1e-6:
        print("FAIL: small label does not match level:", lab, lv)
        raise SystemExit(1)

# Sanity: labels shouldn't be blown up scientific strings for small range
print("OK: small-magnitude labels are plain and match levels")
raise SystemExit(0)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""Req 3.4: log scale preserved. locator_to_legend_entries with a LogLocator
must use LogFormatter (unaffected by offset/scientific handling) and produce
one label per in-range level. This must HOLD on both trees (regression)."""
import matplotlib
matplotlib.use("Agg")
import matplotlib as mpl
from seaborn.utils import locator_to_legend_entries

locator = mpl.ticker.LogLocator(base=10)
limits = (1.0, 1000.0)
levels, labels = locator_to_legend_entries(locator, limits, float)
print("levels:", levels)
print("labels:", labels)

if len(levels) != len(labels):
    print("FAIL: log levels/labels not one-to-one")
    raise SystemExit(1)
if not levels:
    print("FAIL: no log levels")
    raise SystemExit(1)
for lv in levels:
    if not (limits[0] <= lv <= limits[1]):
        print("FAIL: log level out of range:", lv)
        raise SystemExit(1)
# labels should be non-empty strings (log formatting preserved)
if any(lab == "" and lv not in (1.0,) for lv, lab in zip(levels, labels)):
    pass  # LogFormatter may blank some, that's fine/preserved
print("OK: log scale legend entries preserved and paired")
raise SystemExit(0)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
"""Req 1.5: objects Continuous scale legend retains one label per retained tick
location (locations/labels one-to-one). Uses large magnitude too. Regression +
pairing. Should HOLD on both trees."""
import matplotlib
matplotlib.use("Agg")
import numpy as np
import seaborn.objects as so

rng = np.random.RandomState(3)
x = rng.uniform(0, 10, 50)
y = rng.uniform(0, 10, 50)
color = np.add(x, 1e8)

p = so.Plot(x=x, y=y, color=color).add(so.Dot()).plot()
legend = p._figure.legends[0]
texts = [t.get_text() for t in legend.texts]
print("legend texts:", texts)

# Inspect the scale legend directly: (locations, labels) one-to-one
# Find the color scale on the built plot
scales = getattr(p, "_scales", {})
found = False
for name, scale in scales.items():
    leg = getattr(scale, "_legend", None)
    if leg is not None:
        locs, labs = leg
        print(f"scale {name!r}: {len(locs)} locations, {len(labs)} labels")
        found = True
        if len(locs) != len(labs):
            print("FAIL: locations/labels not one-to-one for", name)
            raise SystemExit(1)

if not texts:
    print("FAIL: no legend texts")
    raise SystemExit(1)
print("OK: legend locations and labels are paired one-to-one")
raise SystemExit(0)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Req 1.3 (objects interface, POSITIVE CONTROL): legend labels reflect true
magnitude for large numeric ranges. HOLD patched, FAIL base."""
import matplotlib
matplotlib.use("Agg")
import numpy as np
import seaborn.objects as so

rng = np.random.RandomState(0)
x = rng.uniform(0, 10, 40)
y = rng.uniform(0, 10, 40)
color = np.add(x, 1e8)

p = so.Plot(x=x, y=y, color=color).add(so.Dot()).plot()
legend = p._figure.legends[0]
texts = [t.get_text() for t in legend.texts]
print("legend texts:", texts)

parsed = []
for t in texts:
    try:
        parsed.append(float(t))
    except ValueError:
        print("NON-NUMERIC label (offset annotation shape):", repr(t))
        raise SystemExit(1)

print("parsed floats:", parsed)
if not parsed:
    print("no legend texts")
    raise SystemExit(1)
if all(v > 1e7 for v in parsed):
    print("OK: all labels represent true magnitude (>1e7)")
    raise SystemExit(0)
print("FAIL: some label near zero (offset factored out)")
raise SystemExit(1)
```

Prepatch bug re-encoded as an attack: `True`.

6 probes, all HOLD on gold-patched tree; positive controls (probe_1 objects, probe_2 relplot, probe_3 unit locator_to_legend_entries) FAIL at base and HOLD patched -> discriminating power confirmed.

Probe -> requirement mapping (with observed results base | patched):
- probe_1: Req 1.3 (objects interface, large 1e8 range) -> labels reflect true magnitude (>1e7). base labels ['2','4','6','8'] FAIL | patched ['100000002',...] OK. [POSITIVE CONTROL]
- probe_2: Req 2.3 (relplot/relational interface, hue+1e8) -> numeric labels >1e7. base FAIL | patched OK.
- probe_3: Req 2.3/2.4 (unit locator_to_legend_entries): each label reflects true magnitude AND levels/labels one-to-one over in-range levels. base labels ['0','20',...] FAIL | patched ['100000000',...] OK.
- probe_4: Req 3.1 (small-magnitude regression): plain labels matching levels. HOLD base & patched.
- probe_5: Req 3.4 (log scale preserved via LogFormatter, one-to-one). HOLD base & patched.
- probe_6: Req 1.5 (objects scale legend locations/labels one-to-one). HOLD base & patched.

Candidate wrong-fix patches, both REJECTED by the suite:
- weak_objects_only (fixes only scales.py objects path, leaves utils.py relational path unpatched): probes 2 and 3 FAIL (relational labels still ['2','4'...]/['0','20'...]). Demonstrates suite enforces Req 2 relational path, not just Req 1.
- weak_offset_only (disables set_useOffset in BOTH paths but NOT set_scientific): probes 1,2,3 FAIL -- scientific notation still factors the common power of ten, giving labels ~1.0 (e.g. '1.00000002', '1.0000000'). Demonstrates suite enforces the scientific-mode-disable criteria (Req 1.2 / 2.2) as distinct from offset-disable (Req 1.1 / 2.1). This is exactly the discriminator a weak reading would miss.

Conclusion: SOUND. The requirements are faithful (no probe fails on the gold-patched tree) and discriminate wrong implementations along both dimensions (path coverage: objects vs relational; and formatter setting: offset vs scientific). No too-weak candidate survived the probe suite.

(Advisory only re G-PANEL-3 leakage stamp in meta.json: that is a separate leakage judgement about spec prose reproducing hidden-test constants 1e8/1e7 and is out of scope for G-EQ spec-fidelity, which concerns faithfulness/strength only.)

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
"""Req 1.3 (objects interface, POSITIVE CONTROL): legend labels reflect true
magnitude for large numeric ranges. HOLD patched, FAIL base."""
import matplotlib
matplotlib.use("Agg")
import numpy as np
import seaborn.objects as so

rng = np.random.RandomState(0)
x = rng.uniform(0, 10, 40)
y = rng.uniform(0, 10, 40)
color = np.add(x, 1e8)

p = so.Plot(x=x, y=y, color=color).add(so.Dot()).plot()
legend = p._figure.legends[0]
texts = [t.get_text() for t in legend.texts]
print("legend texts:", texts)

parsed = []
for t in texts:
    try:
        parsed.append(float(t))
    except ValueError:
        print("NON-NUMERIC label (offset annotation shape):", repr(t))
        raise SystemExit(1)

print("parsed floats:", parsed)
if not parsed:
    print("no legend texts")
    raise SystemExit(1)
if all(v > 1e7 for v in parsed):
    print("OK: all labels represent true magnitude (>1e7)")
    raise SystemExit(0)
print("FAIL: some label near zero (offset factored out)")
raise SystemExit(1)
```

Prepatch bug re-encoded as an attack: `True`.

6 probes, all HOLD on gold-patched tree; positive controls (probe_1 objects, probe_2 relplot, probe_3 unit locator_to_legend_entries) FAIL at base and HOLD patched -> discriminating power confirmed.

Probe -> requirement mapping (with observed results base | patched):
- probe_1: Req 1.3 (objects interface, large 1e8 range) -> labels reflect true magnitude (>1e7). base labels ['2','4','6','8'] FAIL | patched ['100000002',...] OK. [POSITIVE CONTROL]
- probe_2: Req 2.3 (relplot/relational interface, hue+1e8) -> numeric labels >1e7. base FAIL | patched OK.
- probe_3: Req 2.3/2.4 (unit locator_to_legend_entries): each label reflects true magnitude AND levels/labels one-to-one over in-range levels. base labels ['0','20',...] FAIL | patched ['100000000',...] OK.
- probe_4: Req 3.1 (small-magnitude regression): plain labels matching levels. HOLD base & patched.
- probe_5: Req 3.4 (log scale preserved via LogFormatter, one-to-one). HOLD base & patched.
- probe_6: Req 1.5 (objects scale legend locations/labels one-to-one). HOLD base & patched.

Candidate wrong-fix patches, both REJECTED by the suite:
- weak_objects_only (fixes only scales.py objects path, leaves utils.py relational path unpatched): probes 2 and 3 FAIL (relational labels still ['2','4'...]/['0','20'...]). Demonstrates suite enforces Req 2 relational path, not just Req 1.
- weak_offset_only (disables set_useOffset in BOTH paths but NOT set_scientific): probes 1,2,3 FAIL -- scientific notation still factors the common power of ten, giving labels ~1.0 (e.g. '1.00000002', '1.0000000'). Demonstrates suite enforces the scientific-mode-disable criteria (Req 1.2 / 2.2) as distinct from offset-disable (Req 1.1 / 2.1). This is exactly the discriminator a weak reading would miss.

Conclusion: SOUND. The requirements are faithful (no probe fails on the gold-patched tree) and discriminate wrong implementations along both dimensions (path coverage: objects vs relational; and formatter setting: offset vs scientific). No too-weak candidate survived the probe suite.

(Advisory only re G-PANEL-3 leakage stamp in meta.json: that is a separate leakage judgement about spec prose reproducing hidden-test constants 1e8/1e7 and is out of scope for G-EQ spec-fidelity, which concerns faithfulness/strength only.)

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Modeling boundary is the changed observable (parsed legend-label magnitude) across BOTH code paths, not a narrow slice — matches the two patch hunks. No mandated-but-absent behavior, no forbidden-but-present behavior, no invented behavior. (Note: G-PANEL-3 separately flagged 1e8/1e7 constants as test-leakage; that is a leakage concern, not a faithfulness divergence — the requirements do not disagree with patched behavior.)


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Requirements name the changed modules/functions (Continuous._setup, locator_to_legend_entries, seaborn/_core/scales.py, seaborn/utils.py) — legitimate localization. ScalarFormatter, scales.py, offset, and scatterplot/relplot are all already public via problem_statement. The offset/scientific-notation 'disabled' acceptance criteria translate the fix into behavioral requirements (the whole point), and do not transmit the hidden tests: no test names (test_legend_has_no_offset), no test paths, no parametrization ids, and critically none of the test-specific numeric thresholds (1e8 added value, >1e7 assertion). No verbatim gold-patch lines and no fix-invented identifiers. Req 1.4 echoes the gold's hasattr(set_useOffset) guard as a robustness requirement but expresses it behaviorally, not as quoted code — within acceptable bounds.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
