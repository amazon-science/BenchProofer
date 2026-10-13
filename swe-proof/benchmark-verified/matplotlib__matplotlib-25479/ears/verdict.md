# P2 adversarial audit — matplotlib__matplotlib-25479

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 10 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 10 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 10 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py`, `probe_7.py`, `probe_8.py`, `probe_9.py`, `probe_10.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (10):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
import sys
import matplotlib as mpl
import matplotlib.pyplot as plt

# Req 1.1 + positive control: two colormaps differing only in name compare EQUAL
cmap = plt.get_cmap("viridis")
renamed = cmap.copy()
renamed.name = "some_other_name"
cmap._init()
renamed._init()
print("names:", cmap.name, renamed.name)
print("colorbar_extend:", cmap.colorbar_extend, renamed.colorbar_extend)
eq = (cmap == renamed)
print("equal:", eq)
sys.exit(0 if eq else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
import sys
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap

# Req 1.2: equal names but different lookup tables => NOT equal
a = ListedColormap(["red", "green", "blue"], name="same")
b = ListedColormap(["red", "green", "black"], name="same")
a._init(); b._init()
eq = (a == b)
print("names equal:", a.name == b.name, "eq:", eq)
sys.exit(0 if not eq else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
import sys
from matplotlib.colors import ListedColormap

# Req 1.3: different-size lookup tables => NOT equal
a = ListedColormap(["red", "green", "blue"], name="x")
b = ListedColormap(["red", "green", "blue", "yellow"], name="x")
a._init(); b._init()
print("N:", a.N, b.N)
eq = (a == b)
print("eq:", eq)
sys.exit(0 if not eq else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
import sys
import matplotlib.pyplot as plt

# Req 1.4: differ in colorbar_extend => NOT equal even with same name
a = plt.get_cmap("viridis").copy()
b = plt.get_cmap("viridis").copy()
a.colorbar_extend = True
b.colorbar_extend = False
a.name = b.name = "same"
a._init(); b._init()
eq = (a == b)
print("colorbar_extend:", a.colorbar_extend, b.colorbar_extend, "eq:", eq)
sys.exit(0 if not eq else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
import sys
import matplotlib.pyplot as plt

# Req 1.5: comparing against a non-Colormap => NOT equal
cmap = plt.get_cmap("viridis")
res1 = (cmap == "viridis")
res2 = (cmap == 42)
res3 = (cmap == None)
print("cmp str/int/None:", res1, res2, res3)
sys.exit(0 if (res1 is False and res2 is False and res3 is False) else 1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
import sys
import matplotlib.pyplot as plt
import matplotlib as mpl

# Req 2.1/2.2/2.3: register a relabelled cmap under a new name; lookup reports name and compares equal
src = plt.get_cmap("viridis").with_extremes(over="0.75")
print("src.name before:", src.name)
regname = "my_registered_cmap_25479"
try:
    mpl.colormaps.unregister(regname)
except Exception:
    pass
mpl.colormaps.register(src, name=regname)
got = mpl.colormaps[regname]
print("looked-up name:", got.name)
ok_name = (got.name == regname)          # 2.1/2.2
ok_eq = (got == src)                     # 2.3
print("name==regname:", ok_name, "got==src:", ok_eq)
sys.exit(0 if (ok_name and ok_eq) else 1)
```

Attack 7 — `probe_7.py` → holds on the patched tree (good)

```python
import sys
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl

# Req 2.4: registration preserves color-producing content (LUT + extremes), changing only name
src = plt.get_cmap("viridis").with_extremes(over="red", under="blue", bad="green")
regname = "preserve_content_25479"
try:
    mpl.colormaps.unregister(regname)
except Exception:
    pass
mpl.colormaps.register(src, name=regname)
got = mpl.colormaps[regname]
src._init(); got._init()
lut_ok = np.array_equal(src._lut, got._lut)
over_ok = np.array_equal(src.get_over(), got.get_over())
under_ok = np.array_equal(src.get_under(), got.get_under())
bad_ok = np.array_equal(src.get_bad(), got.get_bad())
print("lut_ok:", lut_ok, "over:", over_ok, "under:", under_ok, "bad:", bad_ok)
print("name:", got.name)
sys.exit(0 if (lut_ok and over_ok and under_ok and bad_ok and got.name == regname) else 1)
```

Attack 8 — `probe_8.py` → holds on the patched tree (good)

```python
import sys
import matplotlib.pyplot as plt
import matplotlib as mpl

# Req 3.1: registry stores independent copy; mutating original doesn't affect registered
src = plt.get_cmap("viridis").copy()
src.name = "indep_orig"
regname = "indep_reg_25479"
try:
    mpl.colormaps.unregister(regname)
except Exception:
    pass
mpl.colormaps.register(src, name=regname)
# mutate original after registration
src.colorbar_extend = True
src._rgba_over = (1, 0, 0, 1)
got = mpl.colormaps[regname]
print("orig colorbar_extend:", src.colorbar_extend, "got:", got.colorbar_extend)
# registered copy should be unaffected by post-registration mutation
sys.exit(0 if got.colorbar_extend is False else 1)
```

Attack 9 — `probe_9.py` → holds on the patched tree (good)

```python
import sys
import matplotlib.pyplot as plt
import matplotlib as mpl

# Req 3.2 & 3.3: re-register without force => ValueError and no replacement; overwrite builtin => ValueError
a = plt.get_cmap("viridis").copy()
regname = "dup_reg_25479"
try:
    mpl.colormaps.unregister(regname)
except Exception:
    pass
mpl.colormaps.register(a, name=regname)

ok_dup = False
try:
    mpl.colormaps.register(a, name=regname)  # no force
except ValueError:
    ok_dup = True
print("dup raised ValueError:", ok_dup)

ok_builtin = False
try:
    mpl.colormaps.register(a, name="viridis")  # builtin, no force
except ValueError:
    ok_builtin = True
print("builtin overwrite raised ValueError:", ok_builtin)

# Req 3.5: unknown lookup raises
ok_missing = False
try:
    mpl.colormaps["definitely_not_a_cmap_25479"]
except Exception:
    ok_missing = True
print("missing lookup raised:", ok_missing)

sys.exit(0 if (ok_dup and ok_builtin and ok_missing) else 1)
```

Attack 10 — `probe_10.py` → holds on the patched tree (good)

```python
import sys
import matplotlib.pyplot as plt
import matplotlib as mpl

# Req 3.4: no name supplied => uses cmap's own name; Req 2.5: name already equals regname => unchanged content
src = plt.get_cmap("viridis").copy()
src.name = "self_named_25479"
try:
    mpl.colormaps.unregister("self_named_25479")
except Exception:
    pass
mpl.colormaps.register(src)  # no name
got = mpl.colormaps["self_named_25479"]
print("looked up by own name, got.name:", got.name)
ok = (got.name == "self_named_25479") and (got == src)
sys.exit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
import sys
import matplotlib as mpl
import matplotlib.pyplot as plt

# Req 1.1 + positive control: two colormaps differing only in name compare EQUAL
cmap = plt.get_cmap("viridis")
renamed = cmap.copy()
renamed.name = "some_other_name"
cmap._init()
renamed._init()
print("names:", cmap.name, renamed.name)
print("colorbar_extend:", cmap.colorbar_extend, renamed.colorbar_extend)
eq = (cmap == renamed)
print("equal:", eq)
sys.exit(0 if eq else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance matplotlib-25479: gold patch (1) drops the name check from Colormap.__eq__ so equality depends only on LUT + colorbar_extend, and (2) makes ColormapRegistry.register stamp the stored copy's .name to the registration name.

10 probes, one per acceptance criterion, all HOLD on the gold-patched tree (exit 0):
- probe_1  Req1.1  two cmaps differing only in name compare EQUAL. POSITIVE CONTROL: HOLDS patched, FAILS at base (base equal=False). 
- probe_2  Req1.2  equal names, differing LUT => not equal. HOLDS.
- probe_3  Req1.3  different-size LUTs => not equal. HOLDS.
- probe_4  Req1.4  differing colorbar_extend => not equal despite same name. HOLDS.
- probe_5  Req1.5  compare vs non-Colormap (str/int/None) => False. HOLDS.
- probe_6  Req2.1/2.2/2.3  register relabelled viridis under new name; lookup reports regname AND compares equal to source. SECONDARY POSITIVE CONTROL: HOLDS patched, FAILS at base (base name mismatch).
- probe_7  Req2.4  registration preserves LUT + over/under/bad extremes, only name changes. HOLDS.
- probe_8  Req3.1  registry stores independent copy; post-registration mutation of original does not affect stored copy. HOLDS.
- probe_9  Req3.2/3.3/3.5  duplicate register w/o force => ValueError; overwrite builtin => ValueError; missing lookup raises. HOLDS.
- probe_10 Req3.4/2.5  no name supplied uses cmap's own name; equal to source. HOLDS.

Base runs: probe_1 VIOLATED (equal=False), probe_6 VIOLATED (name mismatch) — positive controls discriminate. probe_2/5/10 hold at base as expected (they encode unchanged/regression behavior).

Candidate wrong patch: cm_only_partial_fix (weak.diff) applies ONLY the cm.py name-stamping half and leaves Colormap.__eq__ with the name check — the lazy fix a weak reading of Req2 alone permits. The suite REJECTS it: probe_1 fails (equality still name-sensitive) and probe_6 fails (got==src is False because __eq__ still compares names). Probes 2/5/9 correctly still hold. This demonstrates the probe suite discriminates a plausible partial implementation, so the requirements are not too weak.

All needed runs completed cleanly. Verdict SOUND: >=5 distinct probes all hold on patched, two positive controls discriminate patched-vs-base, and a requirements-plausible partial patch is rejected.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 10 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 10 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 10 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py`, `probe_7.py`, `probe_8.py`, `probe_9.py`, `probe_10.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (10):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

_The 10 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts, and on this backend both roles put it through the same derivation: every block below is a requirement probe run on the gold-patched tree, and the `machine verdict:` line each role publishes above reports BOTH that its probes hold there and how many candidate patches the probe suite rejected — so the two roles re-ran ONE probe suite and each recorded its own outcome for every probe in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `probe_1.py` → holds on the patched tree (good)

Attack 2 — `probe_2.py` → holds on the patched tree (good)

Attack 3 — `probe_3.py` → holds on the patched tree (good)

Attack 4 — `probe_4.py` → holds on the patched tree (good)

Attack 5 — `probe_5.py` → holds on the patched tree (good)

Attack 6 — `probe_6.py` → holds on the patched tree (good)

Attack 7 — `probe_7.py` → holds on the patched tree (good)

Attack 8 — `probe_8.py` → holds on the patched tree (good)

Attack 9 — `probe_9.py` → holds on the patched tree (good)

Attack 10 — `probe_10.py` → holds on the patched tree (good)

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
import sys
import matplotlib as mpl
import matplotlib.pyplot as plt

# Req 1.1 + positive control: two colormaps differing only in name compare EQUAL
cmap = plt.get_cmap("viridis")
renamed = cmap.copy()
renamed.name = "some_other_name"
cmap._init()
renamed._init()
print("names:", cmap.name, renamed.name)
print("colorbar_extend:", cmap.colorbar_extend, renamed.colorbar_extend)
eq = (cmap == renamed)
print("equal:", eq)
sys.exit(0 if eq else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance matplotlib-25479: gold patch (1) drops the name check from Colormap.__eq__ so equality depends only on LUT + colorbar_extend, and (2) makes ColormapRegistry.register stamp the stored copy's .name to the registration name.

10 probes, one per acceptance criterion, all HOLD on the gold-patched tree (exit 0):
- probe_1  Req1.1  two cmaps differing only in name compare EQUAL. POSITIVE CONTROL: HOLDS patched, FAILS at base (base equal=False). 
- probe_2  Req1.2  equal names, differing LUT => not equal. HOLDS.
- probe_3  Req1.3  different-size LUTs => not equal. HOLDS.
- probe_4  Req1.4  differing colorbar_extend => not equal despite same name. HOLDS.
- probe_5  Req1.5  compare vs non-Colormap (str/int/None) => False. HOLDS.
- probe_6  Req2.1/2.2/2.3  register relabelled viridis under new name; lookup reports regname AND compares equal to source. SECONDARY POSITIVE CONTROL: HOLDS patched, FAILS at base (base name mismatch).
- probe_7  Req2.4  registration preserves LUT + over/under/bad extremes, only name changes. HOLDS.
- probe_8  Req3.1  registry stores independent copy; post-registration mutation of original does not affect stored copy. HOLDS.
- probe_9  Req3.2/3.3/3.5  duplicate register w/o force => ValueError; overwrite builtin => ValueError; missing lookup raises. HOLDS.
- probe_10 Req3.4/2.5  no name supplied uses cmap's own name; equal to source. HOLDS.

Base runs: probe_1 VIOLATED (equal=False), probe_6 VIOLATED (name mismatch) — positive controls discriminate. probe_2/5/10 hold at base as expected (they encode unchanged/regression behavior).

Candidate wrong patch: cm_only_partial_fix (weak.diff) applies ONLY the cm.py name-stamping half and leaves Colormap.__eq__ with the name check — the lazy fix a weak reading of Req2 alone permits. The suite REJECTS it: probe_1 fails (equality still name-sensitive) and probe_6 fails (got==src is False because __eq__ still compares names). Probes 2/5/9 correctly still hold. This demonstrates the probe suite discriminates a plausible partial implementation, so the requirements are not too weak.

All needed runs completed cleanly. Verdict SOUND: >=5 distinct probes all hold on patched, two positive controls discriminate patched-vs-base, and a requirements-plausible partial patch is rejected.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Gold patch has two hunks: colors.py Colormap.__eq__ drops the `self.name != other.name` term (equality now = isinstance + colorbar_extend + element-wise lut compare, ignoring name); cm.py register stamps self._cmaps[name].name = name when it differs. Requirement 1 pins the __eq__ change, Requirement 2 pins the register change — the modeling boundary matches the changed observable behavior on both halves, not a narrow slice or an invented behavior. R2.5 (name already equals registration name -> unchanged) is consistent with the `if != name` guard. Verified via nl_attack probe: patched exit 0 (ALL OK), base exit 1 on R1.1.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The requirements describe behavior derivable from the public problem_statement (name-mismatch bug across register/set_cmap/get_cmap) plus legitimate localization of the change to colors.py:Colormap.__eq__ and cm.py:ColormapRegistry.register. Req 1's enumerated equality cases (isinstance, colorbar_extend, element-wise LUT compare, size mismatch, ignore name) describe the __eq__ implementation the gold produces — a behavioral translation, not the hidden test. None of the test's invented identifiers ('test-cmap', 'wrong-cmap'), the specific parametrization/assertions, over='r', test file paths, function names, or verbatim gold lines appear. The viridis/with_extremes(...) intro example is a generic illustrative scenario (matching the public issue/maintainer discussion), carries no test-specific tokens, and does not reconstruct the hidden tests.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
