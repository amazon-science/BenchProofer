# P2 adversarial audit — matplotlib__matplotlib-21568

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 7 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 7 | `probe_1_colon.py`, `probe_2_space.py`, `probe_3_dash.py`, `probe_4_alpha.py`, `probe_5_wrap_empty.py`, `probe_6_formatter.py`, `probe_7_concise.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_2_space.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (7):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1_colon.py` → holds on the patched tree (good)

```python
import sys
from matplotlib.dates import _wrap_in_tex

# Req 1: every colon replaced with {:} inside math group; multiple colons.
cases = {
    "08:00": r"$\mathdefault{08{:}00}$",
    "08:00:00": r"$\mathdefault{08{:}00{:}00}$",
}
ok = True
for inp, exp in cases.items():
    got = _wrap_in_tex(inp)
    print(f"in={inp!r} got={got!r} exp={exp!r}")
    if got != exp:
        ok = False

# Req 1.3: no colon -> unchanged wrt colons (no {:} introduced)
g = _wrap_in_tex("1990")
print(f"nocolon got={g!r}")
if "{:}" in g or g != r"$\mathdefault{1990}$":
    ok = False

sys.exit(0 if ok else 1)
```

Attack 2 — `probe_2_space.py` → holds on the patched tree (good)

```python
import sys
from matplotlib.dates import _wrap_in_tex

# Req 2: every space inside math group -> thin space \;
cases = {
    "01 02": r"$\mathdefault{01\;02}$",
    "01 02 03": r"$\mathdefault{01\;02\;03}$",
}
ok = True
for inp, exp in cases.items():
    got = _wrap_in_tex(inp)
    print(f"in={inp!r} got={got!r} exp={exp!r}")
    if got != exp:
        ok = False
    if " " in got:
        print("  ERROR: raw space survived")
        ok = False
sys.exit(0 if ok else 1)
```

Attack 3 — `probe_3_dash.py` → holds on the patched tree (good)

```python
import sys
from matplotlib.dates import _wrap_in_tex

# Req 3 (kept): every dash -> {-}
inp = "1990-01-05"
exp = r"$\mathdefault{1990{-}01{-}05}$"
got = _wrap_in_tex(inp)
print(f"in={inp!r} got={got!r} exp={exp!r}")
sys.exit(0 if got == exp else 1)
```

Attack 4 — `probe_4_alpha.py` → holds on the patched tree (good)

```python
import sys
from matplotlib.dates import _wrap_in_tex

ok = True
# Req 4.1/4.3: letter run lifted to upright text; leading run -> no empty math group before it
g = _wrap_in_tex("Jan")
print(f"'Jan' -> {g!r}")
if g != "Jan":
    ok = False
if g.startswith(r"$\mathdefault{}$"):
    print("  ERROR: empty math group before leading letters")
    ok = False

# letters between numbers: e.g. "01Jan02"
g2 = _wrap_in_tex("01Jan02")
print(f"'01Jan02' -> {g2!r}")
# 01 wrapped, Jan verbatim upright, 02 wrapped
exp2 = r"$\mathdefault{01}$Jan$\mathdefault{02}$"
if g2 != exp2:
    ok = False

# Req 4.2: digits pass through unchanged
g3 = _wrap_in_tex("12345")
print(f"'12345' -> {g3!r}")
if g3 != r"$\mathdefault{12345}$":
    ok = False

sys.exit(0 if ok else 1)
```

Attack 5 — `probe_5_wrap_empty.py` → holds on the patched tree (good)

```python
import sys
from matplotlib.dates import _wrap_in_tex

ok = True
# Req 5.1: outer math wrapping for numeric content
g = _wrap_in_tex("2020")
print(f"'2020' -> {g!r}")
if not (g.startswith(r"$\mathdefault{") and g.endswith(r"}$")):
    ok = False

# Req 5.3: empty input -> empty string
g2 = _wrap_in_tex("")
print(f"'' -> {g2!r}")
if g2 != "":
    ok = False

# Req 5.2: no empty math group left anywhere
for inp in ["Jan", "Jan Feb", "", "Mon 08:00"]:
    r = _wrap_in_tex(inp)
    print(f"emptycheck {inp!r} -> {r!r}")
    if r"$\mathdefault{}$" in r:
        print("  ERROR: empty math group present")
        ok = False

# Req 5.4 determinism
if _wrap_in_tex("08:00 abc-1") != _wrap_in_tex("08:00 abc-1"):
    ok = False

sys.exit(0 if ok else 1)
```

Attack 6 — `probe_6_formatter.py` → holds on the patched tree (good)

```python
import sys
import matplotlib
matplotlib.use("Agg")
from matplotlib.dates import DateFormatter, _wrap_in_tex, date2num
import datetime

ok = True
# Req 6.1: DateFormatter with usetex active returns _wrap_in_tex of strftime output
x = date2num(datetime.datetime(1990, 1, 1, 8, 0, 0))

f_tex = DateFormatter("%H:%M", usetex=True)
got = f_tex(x)
exp = _wrap_in_tex("08:00")
print(f"usetex=True -> {got!r} exp={exp!r}")
if got != exp:
    ok = False
if got != r"$\mathdefault{08{:}00}$":
    ok = False

# WHILE tex inactive: plain formatted string unchanged
f_plain = DateFormatter("%H:%M", usetex=False)
gp = f_plain(x)
print(f"usetex=False -> {gp!r}")
if gp != "08:00":
    ok = False

sys.exit(0 if ok else 1)
```

Attack 7 — `probe_7_concise.py` → holds on the patched tree (good)

```python
import sys
import matplotlib
matplotlib.use("Agg")
import numpy as np
import datetime
from matplotlib.dates import ConciseDateFormatter, AutoDateLocator, _wrap_in_tex
import matplotlib.pyplot as plt

# Req 6.2: ConciseDateFormatter with usetex applies transform to every label.
# Build labels and check each is a _wrap_in_tex output (idempotent under re-check:
# every label must equal _wrap_in_tex of some plain string, i.e. contain math markup
# and never contain a raw un-braced colon or raw space inside a math group).
ok = True
locator = AutoDateLocator()
formatter = ConciseDateFormatter(locator, usetex=True)

t0 = datetime.datetime(1990, 1, 1, 0, 0, 0)
dates = [t0 + datetime.timedelta(hours=i) for i in range(0, 40, 3)]
from matplotlib.dates import date2num
x = date2num(dates)
locator.create_dummy_axis()
locator.axis.set_view_interval(x[0], x[-1])
vals = locator()
labels = formatter.format_ticks(vals)
print("labels:", labels)

for lab in labels:
    if lab == "":
        continue
    # A tex-transformed label must be math-wrapped
    if not ("$\\mathdefault{" in lab or "$" in lab):
        # purely alphabetic-only labels are lifted to upright text (allowed)
        # but a label containing digits must be math wrapped
        if any(c.isdigit() for c in lab):
            print("  ERROR: digit label not math-wrapped:", repr(lab))
            ok = False
    # colon must be braced, never bare inside a label with math
    if ":" in lab and "{:}" not in lab:
        print("  ERROR: bare colon in label:", repr(lab))
        ok = False

# Directly verify a known colon-bearing label transforms
sample = _wrap_in_tex("08:00")
print("sample:", sample)
if sample != r"$\mathdefault{08{:}00}$":
    ok = False

sys.exit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_2_space.py`

```python
import sys
from matplotlib.dates import _wrap_in_tex

# Req 2: every space inside math group -> thin space \;
cases = {
    "01 02": r"$\mathdefault{01\;02}$",
    "01 02 03": r"$\mathdefault{01\;02\;03}$",
}
ok = True
for inp, exp in cases.items():
    got = _wrap_in_tex(inp)
    print(f"in={inp!r} got={got!r} exp={exp!r}")
    if got != exp:
        ok = False
    if " " in got:
        print("  ERROR: raw space survived")
        ok = False
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Target: matplotlib.dates._wrap_in_tex TeX-mode spacing fix. 7 probes cover all 6 requirements.

Probe results (all on gold-PATCHED tree = HOLD/exit0):
- probe_1_colon (Req1): every colon -> {:}, multiple colons, no-colon unchanged. HOLDS patched, FAILS base (got '$\mathdefault{08:00}$').
- probe_2_space (Req2, POSITIVE CONTROL): every inner space -> \; . HOLDS patched, FAILS base (raw space survives). Discriminating.
- probe_3_dash (Req3 kept): dashes -> {-}. HOLDS patched AND base (kept behavior, correctly non-discriminating).
- probe_4_alpha (Req4): letter runs lifted to upright text, '01Jan02'->'$\mathdefault{01}$Jan$\mathdefault{02}$', leading 'Jan' with no empty leading group, digits pass through. HOLDS patched.
- probe_5_wrap_empty (Req5): outer $\mathdefault{...}$ wrap, empty input->'', no empty math group left, determinism. HOLDS patched.
- probe_6_formatter (Req6.1): DateFormatter usetex=True returns _wrap_in_tex(strftime), usetex=False returns plain '08:00'. HOLDS patched, FAILS base.
- probe_7_concise (Req6.2): ConciseDateFormatter usetex applies transform to every label (colons braced, digit labels math-wrapped). HOLDS patched.

Wrong-fix candidate (weak.diff): gold minus the space-handling lines (colon+dash rewrite only, a plausible partial reading that ignores Req2). Applies cleanly at base. Probe suite REJECTS it: probe_2_space VIOLATED (raw spaces survive); probes 1/3/6 HOLD. This matches the hidden F2P set which includes delta cases exercising space-separated day+time labels (test_date_formatter_usetex[delta2/3], test_concise_formatter_usetex[t_delta2/3]) that the colon-only fix would fail. Demonstrates suite discriminates a requirement-partial implementation.

>=5 probes all hold on patched; positive control (probe_2) holds patched and fails at base (prepatch reproduced); >=1 candidate exercised and rejected. Verdict SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 7 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 7 | `probe_1_colon.py`, `probe_2_space.py`, `probe_3_dash.py`, `probe_4_alpha.py`, `probe_5_wrap_empty.py`, `probe_6_formatter.py`, `probe_7_concise.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_2_space.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (7):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts, and on this backend both roles put it through the same derivation: every block below is a requirement probe run on the gold-patched tree, and the `machine verdict:` line each role publishes above reports BOTH that its probes hold there and how many candidate patches the probe suite rejected — so the two roles re-ran ONE probe suite and each recorded its own outcome for every probe in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `probe_1_colon.py` → holds on the patched tree (good)

Attack 2 — `probe_2_space.py` → holds on the patched tree (good)

Attack 3 — `probe_3_dash.py` → holds on the patched tree (good)

Attack 4 — `probe_4_alpha.py` → holds on the patched tree (good)

Attack 5 — `probe_5_wrap_empty.py` → holds on the patched tree (good)

Attack 6 — `probe_6_formatter.py` → holds on the patched tree (good)

Attack 7 — `probe_7_concise.py` → holds on the patched tree (good)

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_2_space.py`

```python
import sys
from matplotlib.dates import _wrap_in_tex

# Req 2: every space inside math group -> thin space \;
cases = {
    "01 02": r"$\mathdefault{01\;02}$",
    "01 02 03": r"$\mathdefault{01\;02\;03}$",
}
ok = True
for inp, exp in cases.items():
    got = _wrap_in_tex(inp)
    print(f"in={inp!r} got={got!r} exp={exp!r}")
    if got != exp:
        ok = False
    if " " in got:
        print("  ERROR: raw space survived")
        ok = False
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Target: matplotlib.dates._wrap_in_tex TeX-mode spacing fix. 7 probes cover all 6 requirements.

Probe results (all on gold-PATCHED tree = HOLD/exit0):
- probe_1_colon (Req1): every colon -> {:}, multiple colons, no-colon unchanged. HOLDS patched, FAILS base (got '$\mathdefault{08:00}$').
- probe_2_space (Req2, POSITIVE CONTROL): every inner space -> \; . HOLDS patched, FAILS base (raw space survives). Discriminating.
- probe_3_dash (Req3 kept): dashes -> {-}. HOLDS patched AND base (kept behavior, correctly non-discriminating).
- probe_4_alpha (Req4): letter runs lifted to upright text, '01Jan02'->'$\mathdefault{01}$Jan$\mathdefault{02}$', leading 'Jan' with no empty leading group, digits pass through. HOLDS patched.
- probe_5_wrap_empty (Req5): outer $\mathdefault{...}$ wrap, empty input->'', no empty math group left, determinism. HOLDS patched.
- probe_6_formatter (Req6.1): DateFormatter usetex=True returns _wrap_in_tex(strftime), usetex=False returns plain '08:00'. HOLDS patched, FAILS base.
- probe_7_concise (Req6.2): ConciseDateFormatter usetex applies transform to every label (colons braced, digit labels math-wrapped). HOLDS patched.

Wrong-fix candidate (weak.diff): gold minus the space-handling lines (colon+dash rewrite only, a plausible partial reading that ignores Req2). Applies cleanly at base. Probe suite REJECTS it: probe_2_space VIOLATED (raw spaces survive); probes 1/3/6 HOLD. This matches the hidden F2P set which includes delta cases exercising space-separated day+time labels (test_date_formatter_usetex[delta2/3], test_concise_formatter_usetex[t_delta2/3]) that the colon-only fix would fail. Demonstrates suite discriminates a requirement-partial implementation.

>=5 probes all hold on patched; positive control (probe_2) holds patched and fails at base (prepatch reproduced); >=1 candidate exercised and rejected. Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Base probe confirms delta: base '08:00'→'$\mathdefault{08:00}$' and 'Jan 01 08:00'→'Jan$\mathdefault{ 01 08:00}$' (raw colon, raw space); patched applies {:} and \;. Dashes, letter-run lifting, outer wrap, and empty-group removal are identical base vs patched, correctly framed as kept behavior (R3, R4, R5.2-3). Modeling boundary is the whole _wrap_in_tex transform plus its two call sites — the actual changed behavior, not one branch/helper.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The requirements are a behavioral specification of the math-wrapping transform in matplotlib.dates. Every precise token it names (colon->{:}, space->\; thin space, dash->{-}, outer $\mathdefault{...}$ wrap, empty-group removal, letter-run lifting) is the REQUIRED OUTPUT behavior — i.e. a legitimate translation of the gold fix into behavioral requirements, which is the intended purpose of the spec. Localization is clean: it names public API (DateFormatter, ConciseDateFormatter, module matplotlib.dates) and refers to the private helper only descriptively ('the math-wrapping transform'), never leaking the fix-invented private name _wrap_in_tex. No test file paths, test/function names, parametrization ids (delta0..3, t_delta*), expected-array literals, or quoted test/gold code appear. Example labels (08:00, 1990-01-05, Jan) are generic domain illustrations, not verbatim parametrized cases, and 08:00 is already implied by the public problem statement. The requirements describe rules generally rather than enumerating the four parametrized expected strings, so they do not reconstruct the hidden tests.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
