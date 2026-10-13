# P2 adversarial audit — astropy__astropy-7671

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
import sys, types
from astropy.utils.introspection import minversion

# Req1 / Req2.3 (POSITIVE CONTROL): required version with dev qualifier and
# available version with extra numeric component must return a bool, not raise.
mod = types.ModuleType("fakemod")
mod.__version__ = "1.14.3"
try:
    r = minversion(mod, "1.14dev")
except TypeError as e:
    print("FAIL: raised TypeError:", e)
    sys.exit(1)
print("observed minversion(1.14.3, '1.14dev') =", repr(r))
# 1.14.3 >= 1.14 -> True
if r is True:
    sys.exit(0)
print("FAIL: expected True")
sys.exit(1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
import sys, types
from astropy.utils.introspection import minversion

# Req1.3 / Req2.1: normalization discards trailing qualifier. '1.2rc1' -> '1.2'.
# available 1.2 should be >= normalized 1.2 -> True (inclusive default).
mod = types.ModuleType("fakemod")
mod.__version__ = "1.2"
try:
    r = minversion(mod, "1.2rc1")
except Exception as e:
    print("FAIL: raised", type(e).__name__, e)
    sys.exit(1)
print("observed minversion(1.2, '1.2rc1') =", repr(r))
# if the rc1 suffix were NOT stripped, LooseVersion('1.2') >= LooseVersion('1.2rc1')
# would compare 1.2 vs 1.2rc1 -> False (rc1 > empty). Stripped -> True.
if r is True:
    sys.exit(0)
print("FAIL: expected True (suffix must be stripped)")
sys.exit(1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
import sys, types
from astropy.utils.introspection import minversion

# Req1.4: a required-version string NOT beginning with a release number is used
# unchanged. Use an all-alpha version on both sides to avoid int/str clashes.
mod = types.ModuleType("fakemod")
mod.__version__ = "dev"
try:
    r = minversion(mod, "dev")
except Exception as e:
    print("FAIL: raised", type(e).__name__, e)
    sys.exit(1)
print("observed minversion('dev', 'dev') =", repr(r))
# 'dev' unchanged; LooseVersion('dev') >= LooseVersion('dev') -> True.
if r is True:
    sys.exit(0)
print("FAIL: expected True (non-release string must be used unchanged)")
sys.exit(1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
import sys, types
from astropy.utils.introspection import minversion

# Req2.1/2.2: inclusive vs strict semantics on the NORMALIZED requirement.
mod = types.ModuleType("fakemod")
mod.__version__ = "1.14"
# required '1.14dev' -> normalized '1.14'; available exactly 1.14.
inc = minversion(mod, "1.14dev", inclusive=True)
strict = minversion(mod, "1.14dev", inclusive=False)
print("inclusive:", repr(inc), "strict:", repr(strict))
# equal -> inclusive True, strict False
if inc is True and strict is False:
    sys.exit(0)
print("FAIL: expected inclusive True and strict False")
sys.exit(1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
import sys, types
from astropy.utils.introspection import minversion

# Req3: module resolution / version discovery preserved.
results = []

# 3.2: string naming a non-importable module -> False
r = minversion("this_module_does_not_exist_xyz", "1.0")
results.append(("bad-import returns False", r is False))

# 3.3: neither module nor string -> ValueError
try:
    minversion(12345, "1.0")
    results.append(("non-module raises ValueError", False))
except ValueError:
    results.append(("non-module raises ValueError", True))
except Exception as e:
    print("wrong exc:", type(e).__name__)
    results.append(("non-module raises ValueError", False))

# 3.4: dotted version_path resolution
mod = types.ModuleType("fakemod")
sub = types.ModuleType("fakemod.sub")
sub.ver = "3.0"
mod.sub = sub
import sys as _s
_s.modules["fakemod"] = mod
_s.modules["fakemod.sub"] = sub
r2 = minversion(mod, "2.0", version_path="sub.ver")
results.append(("dotted version_path", r2 is True))

# 3.4 default version_path __version__ + plain attr
mod2 = types.ModuleType("fakemod2")
mod2.__version__ = "5.0"
r3 = minversion(mod2, "4.0")
results.append(("default __version__", r3 is True))

for name, ok in results:
    print(("OK " if ok else "BAD") + " " + name)
sys.exit(0 if all(ok for _, ok in results) else 1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
import sys, types
from astropy.utils.introspection import minversion

# Req1.1/1.2/1.5: longest leading release-number prefix (multi-component)
# preserved; pure release string unchanged.
mod = types.ModuleType("fakemod")
mod.__version__ = "1.14.2"

# '1.14.3.dev0' -> normalized '1.14.3' (longest release prefix, dot before dev
# NOT part of a release number since 'dev' isn't a digit run).
# available 1.14.2 >= 1.14.3 ? -> False. If suffix NOT stripped it would raise
# TypeError. So a bool False is the correct discriminating answer.
try:
    r = minversion(mod, "1.14.3.dev0")
except Exception as e:
    print("FAIL: raised", type(e).__name__, e)
    sys.exit(1)
print("minversion(1.14.2, '1.14.3.dev0') =", repr(r))
if r is not False:
    print("FAIL: expected False (1.14.2 < 1.14.3)")
    sys.exit(1)

# pure release string, Req1.5: normalized == original -> 1.14.2 >= 1.14.2 True
r2 = minversion(mod, "1.14.2")
print("minversion(1.14.2, '1.14.2') =", repr(r2))
if r2 is not True:
    print("FAIL: expected True for equal pure release")
    sys.exit(1)
sys.exit(0)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
import sys, types
from astropy.utils.introspection import minversion

# Req1 / Req2.3 (POSITIVE CONTROL): required version with dev qualifier and
# available version with extra numeric component must return a bool, not raise.
mod = types.ModuleType("fakemod")
mod.__version__ = "1.14.3"
try:
    r = minversion(mod, "1.14dev")
except TypeError as e:
    print("FAIL: raised TypeError:", e)
    sys.exit(1)
print("observed minversion(1.14.3, '1.14dev') =", repr(r))
# 1.14.3 >= 1.14 -> True
if r is True:
    sys.exit(0)
print("FAIL: expected True")
sys.exit(1)
```

Prepatch bug re-encoded as an attack: `True`.

6 probes covering all 3 requirements. Probe_1 (Req1/Req2.3, POSITIVE CONTROL): minversion(1.14.3,'1.14dev') raises TypeError at base, returns True patched. Probe_2 (Req1.3/Req2.1): '1.2rc1'->'1.2' so minversion(1.2,'1.2rc1')=True patched, False at base. Probe_3 (Req1.4): non-release string 'dev' used unchanged -> True. Probe_4 (Req2.1/2.2): inclusive True / strict False on equal normalized version. Probe_5 (Req3.2/3.3/3.4): bad import->False, non-module->ValueError, dotted version_path, default __version__ all preserved. Probe_6 (Req1.1/1.2/1.5): multi-component prefix '1.14.3.dev0'->'1.14.3' gives False (1.14.2<1.14.3) with no raise, pure release '1.14.2'==original. All 6 HOLD on patched tree. Weak candidate (naive fix stripping only literal 'dev'): REJECTED by probe_2 (does not strip 'rc1', minversion(1.2,'1.2rc1')=False) and probe_3 (crashes on 'dev'->'' -> empty LooseVersion). Suite discriminates wrong implementations. Verdict SOUND. (Note: bundle G-PANEL-3 flags the epoch-`!` clause in Req1.2 as leakage of the exact gold regex structure, but that is a separate leakage concern, not a spec-fidelity/too-weak defect for G-EQ.)

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
import sys, types
from astropy.utils.introspection import minversion

# Req1 / Req2.3 (POSITIVE CONTROL): required version with dev qualifier and
# available version with extra numeric component must return a bool, not raise.
mod = types.ModuleType("fakemod")
mod.__version__ = "1.14.3"
try:
    r = minversion(mod, "1.14dev")
except TypeError as e:
    print("FAIL: raised TypeError:", e)
    sys.exit(1)
print("observed minversion(1.14.3, '1.14dev') =", repr(r))
# 1.14.3 >= 1.14 -> True
if r is True:
    sys.exit(0)
print("FAIL: expected True")
sys.exit(1)
```

Prepatch bug re-encoded as an attack: `True`.

6 probes covering all 3 requirements. Probe_1 (Req1/Req2.3, POSITIVE CONTROL): minversion(1.14.3,'1.14dev') raises TypeError at base, returns True patched. Probe_2 (Req1.3/Req2.1): '1.2rc1'->'1.2' so minversion(1.2,'1.2rc1')=True patched, False at base. Probe_3 (Req1.4): non-release string 'dev' used unchanged -> True. Probe_4 (Req2.1/2.2): inclusive True / strict False on equal normalized version. Probe_5 (Req3.2/3.3/3.4): bad import->False, non-module->ValueError, dotted version_path, default __version__ all preserved. Probe_6 (Req1.1/1.2/1.5): multi-component prefix '1.14.3.dev0'->'1.14.3' gives False (1.14.2<1.14.3) with no raise, pure release '1.14.2'==original. All 6 HOLD on patched tree. Weak candidate (naive fix stripping only literal 'dev'): REJECTED by probe_2 (does not strip 'rc1', minversion(1.2,'1.2rc1')=False) and probe_3 (crashes on 'dev'->'' -> empty LooseVersion). Suite discriminates wrong implementations. Verdict SOUND. (Note: bundle G-PANEL-3 flags the epoch-`!` clause in Req1.2 as leakage of the exact gold regex structure, but that is a separate leakage concern, not a spec-fidelity/too-weak defect for G-EQ.)

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** The modeling boundary is correct: requirements pin the observable changed behavior (required-version operand normalized to its PEP440 leading release prefix, then LooseVersion comparison yields a boolean), not just a narrow helper/branch. Base-commit probe confirms the pre-patch TypeError regression; patched probe confirms boolean results. Regex-direct probes confirm all epoch/release-number edge cases (1.2). No requirement mandates behavior the code lacks, forbids behavior it has, or invents behavior.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** requirements.md describes behavior and localizes the change to minversion in astropy/utils/introspection.py (legitimate). Public examples (1.14dev, 1.14.3, TypeError, LooseVersion, PR #7647 scenario) all come from problem_statement. Req 1.2 gives a precise prose description of the normalization regex, but that regex is the public PEP440 pattern (the gold comment itself cites PEP440), and fully specifying the normalization algorithm is legitimate spec — no fix-invented identifiers. No hidden-test artifacts leaked: absent are the test path/name (test_introspection.py::test_minversion), the good_versions/bad_versions enumerations (0.12, 0.12.1, 0.12.0.dev, 0.12dev, '1'), the test module version 0.12.2, and any quoted test/gold code. The one string 1.2rc1 (line 15) coincides with a hidden bad_versions entry but is a generic pre-release illustration, not a parametrization enumeration, so it does not reconstruct the test.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
