# P2 adversarial audit — scikit-learn__scikit-learn-14141

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
# Positive control + Req1.1: _get_deps_info() returns a mapping containing 'joblib'.
import sys
from sklearn.utils._show_versions import _get_deps_info
info = _get_deps_info()
print("keys:", sorted(info.keys()))
if "joblib" not in info:
    print("FAIL: 'joblib' key missing")
    sys.exit(1)
print("OK: joblib present ->", info["joblib"])
sys.exit(0)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
# Req1.2: joblib entry value equals installed joblib module's reported version.
import sys
import joblib
from sklearn.utils._show_versions import _get_deps_info
info = _get_deps_info()
got = info.get("joblib")
expected = joblib.__version__
print("reported:", got, "actual joblib.__version__:", expected)
if got != expected:
    print("FAIL: reported joblib version does not match module version")
    sys.exit(1)
print("OK: matches")
sys.exit(0)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
# Req1.3: if joblib cannot be imported, _get_deps_info() sets joblib -> None
# (the same null/absent marker used for any unavailable dep), without raising.
import sys
import importlib.abc

# Import everything first so sklearn package init (which imports joblib) is done.
from sklearn.utils._show_versions import _get_deps_info

class BlockJoblib(importlib.abc.MetaPathFinder):
    def find_spec(self, name, path, target=None):
        if name == "joblib" or name.startswith("joblib."):
            raise ImportError("blocked by probe")
        return None

# Drop cached joblib so get_version's import_module re-attempts (and is blocked).
for k in list(sys.modules):
    if k == "joblib" or k.startswith("joblib."):
        del sys.modules[k]
sys.meta_path.insert(0, BlockJoblib())

try:
    info = _get_deps_info()
except Exception as e:
    print("FAIL: _get_deps_info raised", type(e).__name__, e)
    sys.exit(1)

val = info.get("joblib", "MISSING_KEY")
print("joblib value when unimportable:", repr(val))
if val is not None:
    print("FAIL: expected None null-marker, got", repr(val))
    sys.exit(1)
print("OK: joblib -> None, no error raised")
sys.exit(0)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
# Req1.4: show_versions() printed output includes joblib name and its version.
import sys, io, contextlib
import joblib
from sklearn.utils._show_versions import show_versions
buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    show_versions()
out = buf.getvalue()
print("---captured---")
print(out)
if "joblib" not in out:
    print("FAIL: 'joblib' not in show_versions output")
    sys.exit(1)
if joblib.__version__ not in out:
    print("FAIL: joblib version string not in output")
    sys.exit(1)
print("OK: joblib name and version rendered")
sys.exit(0)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
# Req2.1 + 2.2: all previously reported deps still present, and each resolves
# to its reported version (importable) or None. Regression guard.
import sys, importlib
from sklearn.utils._show_versions import _get_deps_info
info = _get_deps_info()
required = ["pip", "setuptools", "sklearn", "numpy", "scipy", "Cython",
            "pandas", "matplotlib"]
print("keys:", sorted(info.keys()))
missing = [d for d in required if d not in info]
if missing:
    print("FAIL: missing prior dependency entries:", missing)
    sys.exit(1)
# Verify resolution rule: importable -> version, else None.
for d in required:
    try:
        mod = importlib.import_module(d)
        expected = getattr(mod, "__version__", None)
    except ImportError:
        expected = None
    got = info[d]
    if expected is not None and got != expected:
        print(f"FAIL: {d} reported {got!r} != {expected!r}")
        sys.exit(1)
    print(f"OK {d}: {got!r}")
sys.exit(0)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
# Req2.3: _get_sys_info() still contains python, executable, machine.
import sys
from sklearn.utils._show_versions import _get_sys_info
info = _get_sys_info()
print("sys_info keys:", sorted(info.keys()))
for k in ("python", "executable", "machine"):
    if k not in info:
        print("FAIL: missing sys info key", k)
        sys.exit(1)
print("OK: python/executable/machine present")
sys.exit(0)
```

Attack 7 — `probe_7.py` → holds on the patched tree (good)

```python
# Req2.4: show_versions() output still includes system info, BLAS section, and
# python-dependency section (python, numpy names + BLAS heading).
import sys, io, contextlib
from sklearn.utils._show_versions import show_versions
buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    show_versions()
out = buf.getvalue()
print("---captured---")
print(out)
for token in ("python", "numpy", "BLAS"):
    if token not in out:
        print("FAIL: expected token not in output:", token)
        sys.exit(1)
print("OK: system/BLAS/python-deps sections rendered")
sys.exit(0)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
# Positive control + Req1.1: _get_deps_info() returns a mapping containing 'joblib'.
import sys
from sklearn.utils._show_versions import _get_deps_info
info = _get_deps_info()
print("keys:", sorted(info.keys()))
if "joblib" not in info:
    print("FAIL: 'joblib' key missing")
    sys.exit(1)
print("OK: joblib present ->", info["joblib"])
sys.exit(0)
```

Prepatch bug re-encoded as an attack: `True`.

Instance adds 'joblib' to the dependency list in _get_deps_info(). 7 probes cover every acceptance criterion.

Probes / criteria / results (patched | base):
- probe_1 (Req1.1: 'joblib' key present in _get_deps_info): HOLDS patched | VIOLATED base. Positive control.
- probe_2 (Req1.2: joblib entry == joblib.__version__ '1.1.1'): HOLDS patched | VIOLATED base.
- probe_3 (Req1.3: joblib unimportable -> None null-marker, no raise; blocks import via meta_path after full sklearn init): HOLDS patched (None) | (n/a base, key absent).
- probe_4 (Req1.4: show_versions() output includes 'joblib' name + version): HOLDS patched | VIOLATED base.
- probe_5 (Req2.1+2.2: all prior deps pip/setuptools/sklearn/numpy/scipy/Cython/pandas/matplotlib present and each resolves to module version or None): HOLDS patched.
- probe_6 (Req2.3: _get_sys_info has python/executable/machine): HOLDS patched.
- probe_7 (Req2.4: show_versions still prints system, BLAS heading, python-deps incl python & numpy): HOLDS patched.

Positive control probe_1 discriminates: exit 0 patched, exit 1 base (joblib key missing) — prepatch reproduced.

Candidate wrong-fix (weak.diff): hardcodes deps_info['joblib']='1.0' after the loop. It satisfies the hidden test (only asserts 'joblib' in deps_info) and passes probe_1 & probe_5, but is REJECTED by probe_2 (wrong version), probe_3 (returns '1.0' instead of None when unimportable), and probe_4 (version string absent from output). This demonstrates the suite discriminates a requirements-violating but hidden-test-passing implementation, and confirms requirements are not too weak. No requirements-conforming alternative that fails the hidden test was found — the requirements pin the exact reported version and the null-marker behavior, matching gold. Verdict SOUND.

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
# Positive control + Req1.1: _get_deps_info() returns a mapping containing 'joblib'.
import sys
from sklearn.utils._show_versions import _get_deps_info
info = _get_deps_info()
print("keys:", sorted(info.keys()))
if "joblib" not in info:
    print("FAIL: 'joblib' key missing")
    sys.exit(1)
print("OK: joblib present ->", info["joblib"])
sys.exit(0)
```

Prepatch bug re-encoded as an attack: `True`.

Instance adds 'joblib' to the dependency list in _get_deps_info(). 7 probes cover every acceptance criterion.

Probes / criteria / results (patched | base):
- probe_1 (Req1.1: 'joblib' key present in _get_deps_info): HOLDS patched | VIOLATED base. Positive control.
- probe_2 (Req1.2: joblib entry == joblib.__version__ '1.1.1'): HOLDS patched | VIOLATED base.
- probe_3 (Req1.3: joblib unimportable -> None null-marker, no raise; blocks import via meta_path after full sklearn init): HOLDS patched (None) | (n/a base, key absent).
- probe_4 (Req1.4: show_versions() output includes 'joblib' name + version): HOLDS patched | VIOLATED base.
- probe_5 (Req2.1+2.2: all prior deps pip/setuptools/sklearn/numpy/scipy/Cython/pandas/matplotlib present and each resolves to module version or None): HOLDS patched.
- probe_6 (Req2.3: _get_sys_info has python/executable/machine): HOLDS patched.
- probe_7 (Req2.4: show_versions still prints system, BLAS heading, python-deps incl python & numpy): HOLDS patched.

Positive control probe_1 discriminates: exit 0 patched, exit 1 base (joblib key missing) — prepatch reproduced.

Candidate wrong-fix (weak.diff): hardcodes deps_info['joblib']='1.0' after the loop. It satisfies the hidden test (only asserts 'joblib' in deps_info) and passes probe_1 & probe_5, but is REJECTED by probe_2 (wrong version), probe_3 (returns '1.0' instead of None when unimportable), and probe_4 (version string absent from output). This demonstrates the suite discriminates a requirements-violating but hidden-test-passing implementation, and confirms requirements are not too weak. No requirements-conforming alternative that fails the hidden test was found — the requirements pin the exact reported version and the null-marker behavior, matching gold. Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Requirements pin the actual changed observable (joblib appears in the deps mapping and show_versions output) rather than a narrow slice. R1.3's null-marker claim matches the unchanged get_version helper (returns None on ImportError). Verified via probe (gold and --base) in the instance image.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The document localizes the change to `_get_deps_info()`/`show_versions()` and requires a `joblib` entry — all public via the problem_statement ('Add joblib in show_versions'). The enumerated existing dependencies (pip, setuptools, sklearn, numpy, scipy, Cython, pandas, matplotlib) and the `_get_sys_info` keys (python, executable, machine) and BLAS section are read from the existing public source module, not the hidden tests. The gold patch invents no identifiers (it appends the public string 'joblib' to an existing list). Requirement prose describes behavior; it does not reproduce the test assertions, paths, or ids (test_get_deps_info / test_show_versions.py). Naming the touched module/functions is legitimate localization. No test-shaped enumeration mirroring parametrization exists (the tests are non-parametrized). No leakage.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
