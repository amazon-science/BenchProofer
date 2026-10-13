# P2 adversarial audit — pytest-dev__pytest-5840

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
# R3.1/R3.2 + core F2P: after loading a conftest, the cache key equals the
# file's resolved (absolute, symlink-resolved) pathlib.Path with case preserved,
# i.e. Path(str(conftestpath)).resolve() is present in _conftestpath2mod.
import tempfile, os, py
from pathlib import Path
from _pytest.config import PytestPluginManager

d = tempfile.mkdtemp()
sub = os.path.join(d, "sub"); os.mkdir(sub)
conf = os.path.join(sub, "conftest.py")
open(conf, "w").write("")
pm = PytestPluginManager()
confp = py.path.local(conf)
mod = pm._importconftest(confp)
key = Path(str(confp)).resolve()
keys = list(pm._conftestpath2mod)
print("stored key types:", [type(k).__name__ for k in keys])
print("lookup key:", key, type(key).__name__)
assert key in pm._conftestpath2mod, ("resolved Path key NOT in cache", keys)
assert len(pm._conftestpath2mod) == 1, ("expected exactly 1 entry", len(pm._conftestpath2mod))
print("OK: resolved Path key present; exactly one cache entry")
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
# R2.2: same physical conftest reached via a symlinked/aliased path returns the
# already-loaded module from cache (imported only once, no second entry).
import tempfile, os, py
from _pytest.config import PytestPluginManager

d = tempfile.mkdtemp()
real = os.path.join(d, "realdir"); os.mkdir(real)
conf = os.path.join(real, "conftest.py"); open(conf, "w").write("")
link = os.path.join(d, "linkdir"); os.symlink(real, link)
aliased = os.path.join(link, "conftest.py")
assert os.path.realpath(aliased) == os.path.realpath(conf)

pm = PytestPluginManager()
mod1 = pm._importconftest(py.path.local(conf))
n_after_first = len(pm._conftestpath2mod)
mod2 = pm._importconftest(py.path.local(aliased))
print("n after first:", n_after_first, "n after aliased:", len(pm._conftestpath2mod))
print("same module returned:", mod1 is mod2)
assert mod1 is mod2, "aliased path did not return cached module"
assert len(pm._conftestpath2mod) == n_after_first == 1, "symlink alias created a duplicate cache entry"
print("OK: symlink alias de-duplicated to a single cached module")
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
# R3.3/R3.4: a directory with no conftest.py adds NO cache entry; and when
# exactly one applicable conftest is discovered, the cache holds exactly one.
import tempfile, os, py
from pathlib import Path
from _pytest.config import PytestPluginManager

d = tempfile.mkdtemp()
plain = os.path.join(d, "plainsub"); os.mkdir(plain)   # no conftest here
withc = os.path.join(d, "withc"); os.mkdir(withc)
conf = os.path.join(withc, "conftest.py"); open(conf, "w").write("")

pm = PytestPluginManager()
# discover conftests for the plain (no-conftest) directory
pm._getconftestmodules(py.path.local(plain))
would_be = Path(str(py.path.local(os.path.join(plain, "conftest.py")))).resolve()
print("cache after plain-dir discovery:", len(pm._conftestpath2mod))
assert would_be not in pm._conftestpath2mod, "phantom entry for non-existent conftest"
assert len(pm._conftestpath2mod) == 0, ("expected empty cache", list(pm._conftestpath2mod))

# now the directory that DOES have exactly one conftest
pm._importconftest(py.path.local(conf))
print("cache after one real conftest:", len(pm._conftestpath2mod))
assert len(pm._conftestpath2mod) == 1, "expected exactly one entry"
print("OK: no phantom entries; exactly one for a single discovered conftest")
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
# R1.4/R1.5/R4 end-to-end: a conftest under an UPPERCASE-named package dir loads
# without a lower-cased-path import error; collection finishes with
# "no tests collected" (ExitCode.NO_TESTS_COLLECTED == 5).
import tempfile, os, sys, subprocess
d = tempfile.mkdtemp()
os.makedirs(os.path.join(d, "Foo"))
open(os.path.join(d, "__init__.py"), "w").write("")
open(os.path.join(d, "Foo", "__init__.py"), "w").write("")
open(os.path.join(d, "Foo", "conftest.py"), "w").write("")
# run pytest as the system-under-test via subprocess (probe itself uses no pytest API)
proc = subprocess.run([sys.executable, "-m", "pytest", "-p", "no:cacheprovider"],
                      cwd=d, capture_output=True, text=True)
out = proc.stdout + proc.stderr
print("returncode:", proc.returncode)
print(out[-800:])
assert "ImportError" not in out and "ModuleNotFoundError" not in out, "spurious import error on uppercase tree"
assert proc.returncode == 5, ("expected NO_TESTS_COLLECTED (5), got %d" % proc.returncode)
print("OK: uppercase-named conftest loaded; no tests collected, no import error")
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
# R1.1/R1.2/R3.1 case-preservation: with an UPPERCASE component in the path, the
# stored cache key must retain that uppercase (no lower-casing) and equal the
# resolved case-preserving path. Also _getconftestmodules must find it.
import tempfile, os, py
from pathlib import Path
from _pytest.config import PytestPluginManager

d = tempfile.mkdtemp()
up = os.path.join(d, "MixedCaseDir"); os.mkdir(up)
conf = os.path.join(up, "conftest.py"); open(conf, "w").write("")

pm = PytestPluginManager()
mod = pm._importconftest(py.path.local(conf))
keys = [str(k) for k in pm._conftestpath2mod]
print("keys:", keys)
assert any("MixedCaseDir" in k for k in keys), ("uppercase folded away", keys)
assert not any("mixedcasedir" in k for k in keys), ("path was lower-cased", keys)
key = Path(str(py.path.local(conf))).resolve()
assert key in pm._conftestpath2mod, "resolved case-preserving key not found"
# discovery over the directory should locate the same single module
vals = pm._getconftestmodules(py.path.local(up))
assert len(vals) == 1 and vals[0] is mod, ("discovery mismatch", vals)
assert vals[0].__file__.startswith(str(py.path.local(conf).dirpath())), vals[0].__file__
print("OK: uppercase preserved in key; discovery returns the one module")
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
# R4.1/R4.2/R4.3: confcutdir boundary respected — parents at/above the cut are
# skipped; only conftests at/below it are imported; the returned module's file
# is the conftest at the expected resolved location; loaded exactly once.
import tempfile, os, py
from _pytest.config import PytestPluginManager

d = tempfile.mkdtemp()
# outer conftest ABOVE the cut, inner conftest AT the cut dir
outer_conf = os.path.join(d, "conftest.py"); open(outer_conf, "w").write("")
cut = os.path.join(d, "cutdir"); os.mkdir(cut)
inner_conf = os.path.join(cut, "conftest.py"); open(inner_conf, "w").write("")
target = os.path.join(cut, "sub"); os.mkdir(target)

pm = PytestPluginManager()
class NS:  # minimal namespace for _set_initial_conftests
    confcutdir = cut
    pyargs = False
    file_or_dir = [target]
    noconftest = False
    importmode = "prepend"
    rootdir = d
pm._set_initial_conftests(NS)

vals = pm._getconftestmodules(py.path.local(target))
files = [m.__file__ for m in vals]
print("confcutdir:", pm._confcutdir)
print("loaded files:", files)
# The outer conftest is ABOVE the cut -> must NOT be loaded; inner (at cut) IS.
assert any(os.path.realpath(inner_conf) == os.path.realpath(f) or
           f.startswith(str(py.path.local(inner_conf).dirpath())) for f in files), \
    ("inner conftest not loaded", files)
assert not any(f.startswith(str(py.path.local(d))) and "cutdir" not in f for f in files), \
    ("outer conftest above cut leaked in", files)
# exactly once
assert len(files) == len(set(files)), ("duplicate load", files)
print("OK: confcutdir respected; inner loaded, outer skipped, no duplicates")
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
# R3.1/R3.2 + core F2P: after loading a conftest, the cache key equals the
# file's resolved (absolute, symlink-resolved) pathlib.Path with case preserved,
# i.e. Path(str(conftestpath)).resolve() is present in _conftestpath2mod.
import tempfile, os, py
from pathlib import Path
from _pytest.config import PytestPluginManager

d = tempfile.mkdtemp()
sub = os.path.join(d, "sub"); os.mkdir(sub)
conf = os.path.join(sub, "conftest.py")
open(conf, "w").write("")
pm = PytestPluginManager()
confp = py.path.local(conf)
mod = pm._importconftest(confp)
key = Path(str(confp)).resolve()
keys = list(pm._conftestpath2mod)
print("stored key types:", [type(k).__name__ for k in keys])
print("lookup key:", key, type(key).__name__)
assert key in pm._conftestpath2mod, ("resolved Path key NOT in cache", keys)
assert len(pm._conftestpath2mod) == 1, ("expected exactly 1 entry", len(pm._conftestpath2mod))
print("OK: resolved Path key present; exactly one cache entry")
```

Prepatch bug re-encoded as an attack: `True`.

Instance pytest-dev__pytest-5840: conftest path canonicalization must preserve letter case and key the cache by the resolved pathlib.Path. On Linux (the audit image is case-sensitive, os.path.normcase is identity) the TRUE discriminator between the buggy and fixed code is the cache-key TYPE and identity, not visible casing: base stores a py.path.local built from unique_path(normcase(realpath)); gold stores Path(str(conftestpath)).resolve() (a PosixPath). This mirrors the hidden F2P (test_setinitial_conftest_subdirs asserting `Path(str(subconftest)).resolve() in _conftestpath2mod`).

Six probes, all HOLD on the gold-patched tree:
 - probe_1 (R3.1/R3.2/R3.4, core F2P): after _importconftest, Path(str(conftestpath)).resolve() is present in _conftestpath2mod and there is exactly one entry. HOLDS patched, VIOLATED at base (base key is a local(...), resolved Path absent). POSITIVE CONTROL — discriminates.
 - probe_2 (R2.2): symlink-aliased path returns the already-cached module, single entry. HOLDS base+patched (regression preserved).
 - probe_3 (R3.3/R3.4): no phantom cache entry for a conftest-less dir; exactly one for a single discovered conftest. HOLDS base+patched.
 - probe_4 (R1.4/R1.5/R4 end-to-end): uppercase-named package tree (Foo/) collects with NO_TESTS_COLLECTED(5), no ImportError/ModuleNotFoundError. HOLDS base+patched (Linux is case-sensitive so the bug is not reproducible end-to-end there; kept as a regression/no-crash probe).
 - probe_5 (R1.1/R1.2/R3.1 case-preservation): with a MixedCaseDir component, the stored key retains 'MixedCaseDir' (never lower-cased) and equals the resolved case-preserving Path; discovery returns the one module. HOLDS patched, VIOLATED at base (resolved Path key absent) — second discriminator.
 - probe_6 (R4.1/R4.2/R4.3 confcutdir): inner conftest at the cut is loaded, outer conftest above the cut is skipped, loaded exactly once, file at expected resolved location. HOLDS base+patched.

Candidate wrong patch exercised: weak.diff removes normcase from unique_path but keeps `type(path)(str(path.realpath()))` — the LAZY reading of 'SHALL NOT fold to lower case'. It satisfies the surface casing/symlink requirements (probe_2/3/4/6 HOLD) but keeps the cache key a py.path.local rather than the resolved pathlib.Path mandated by R3.1/R3.2 and the F2P test. probe_1 and probe_5 REJECT it (resolved-Path key absent) — the suite discriminates this plausibly-wrong implementation, and it would not resolve the hidden F2P. No requirements-conforming alternative that fails the tests was found; the suite pins the resolved-Path cache-key identity, which is exactly what the fix and hidden tests require.

Protocol: >=5 distinct probes (6), all HOLD patched; positive control (probe_1) HOLDS patched and FAILS at base (prepatch_reproduced=true, corroborated by probe_5); >=1 candidate patch exercised and REJECTED. Verdict SOUND.

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
# R3.1/R3.2 + core F2P: after loading a conftest, the cache key equals the
# file's resolved (absolute, symlink-resolved) pathlib.Path with case preserved,
# i.e. Path(str(conftestpath)).resolve() is present in _conftestpath2mod.
import tempfile, os, py
from pathlib import Path
from _pytest.config import PytestPluginManager

d = tempfile.mkdtemp()
sub = os.path.join(d, "sub"); os.mkdir(sub)
conf = os.path.join(sub, "conftest.py")
open(conf, "w").write("")
pm = PytestPluginManager()
confp = py.path.local(conf)
mod = pm._importconftest(confp)
key = Path(str(confp)).resolve()
keys = list(pm._conftestpath2mod)
print("stored key types:", [type(k).__name__ for k in keys])
print("lookup key:", key, type(key).__name__)
assert key in pm._conftestpath2mod, ("resolved Path key NOT in cache", keys)
assert len(pm._conftestpath2mod) == 1, ("expected exactly 1 entry", len(pm._conftestpath2mod))
print("OK: resolved Path key present; exactly one cache entry")
```

Prepatch bug re-encoded as an attack: `True`.

Instance pytest-dev__pytest-5840: conftest path canonicalization must preserve letter case and key the cache by the resolved pathlib.Path. On Linux (the audit image is case-sensitive, os.path.normcase is identity) the TRUE discriminator between the buggy and fixed code is the cache-key TYPE and identity, not visible casing: base stores a py.path.local built from unique_path(normcase(realpath)); gold stores Path(str(conftestpath)).resolve() (a PosixPath). This mirrors the hidden F2P (test_setinitial_conftest_subdirs asserting `Path(str(subconftest)).resolve() in _conftestpath2mod`).

Six probes, all HOLD on the gold-patched tree:
 - probe_1 (R3.1/R3.2/R3.4, core F2P): after _importconftest, Path(str(conftestpath)).resolve() is present in _conftestpath2mod and there is exactly one entry. HOLDS patched, VIOLATED at base (base key is a local(...), resolved Path absent). POSITIVE CONTROL — discriminates.
 - probe_2 (R2.2): symlink-aliased path returns the already-cached module, single entry. HOLDS base+patched (regression preserved).
 - probe_3 (R3.3/R3.4): no phantom cache entry for a conftest-less dir; exactly one for a single discovered conftest. HOLDS base+patched.
 - probe_4 (R1.4/R1.5/R4 end-to-end): uppercase-named package tree (Foo/) collects with NO_TESTS_COLLECTED(5), no ImportError/ModuleNotFoundError. HOLDS base+patched (Linux is case-sensitive so the bug is not reproducible end-to-end there; kept as a regression/no-crash probe).
 - probe_5 (R1.1/R1.2/R3.1 case-preservation): with a MixedCaseDir component, the stored key retains 'MixedCaseDir' (never lower-cased) and equals the resolved case-preserving Path; discovery returns the one module. HOLDS patched, VIOLATED at base (resolved Path key absent) — second discriminator.
 - probe_6 (R4.1/R4.2/R4.3 confcutdir): inner conftest at the cut is loaded, outer conftest above the cut is skipped, loaded exactly once, file at expected resolved location. HOLDS base+patched.

Candidate wrong patch exercised: weak.diff removes normcase from unique_path but keeps `type(path)(str(path.realpath()))` — the LAZY reading of 'SHALL NOT fold to lower case'. It satisfies the surface casing/symlink requirements (probe_2/3/4/6 HOLD) but keeps the cache key a py.path.local rather than the resolved pathlib.Path mandated by R3.1/R3.2 and the F2P test. probe_1 and probe_5 REJECT it (resolved-Path key absent) — the suite discriminates this plausibly-wrong implementation, and it would not resolve the hidden F2P. No requirements-conforming alternative that fails the tests was found; the suite pins the resolved-Path cache-key identity, which is exactly what the fix and hidden tests require.

Protocol: >=5 distinct probes (6), all HOLD patched; positive control (probe_1) HOLDS patched and FAILS at base (prepatch_reproduced=true, corroborated by probe_5); >=1 candidate patch exercised and REJECTED. Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Gold patch removes unique_path (which applied normcase=lowercase on top of realpath) and substitutes case-preserving resolution at all three call sites. The requirements pin the changed observable behavior (case preservation across the three canonicalization sites) rather than a narrow branch, and correctly retain symlink dedup and confcutdir semantics. Minor non-issue: the F2P test module still top-level imports the now-removed unique_path symbol, but that concerns the test harness, not the requirements' fidelity to the code change.

Counterexample / evidence:

```
n/a — probe_beh.py on gold-patched tree: NKEYS 1, KEYTYPE PosixPath, KEY_HAS_UPPER True, KEY_IS_ABS True, DEDUP_SAME True, NKEYS_AFTER 1, KEY_EQ_RESOLVE True.
```


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Requirements describe behavior and localize the change to the genuinely-changed functions (_importconftest, _getconftestmodules, _set_initial_conftests, pathlib helper) — legitimate localization. The core symptom (Windows case-insensitive FS lower-casing paths -> ModuleNotFoundError while loading conftest) is fully public in problem_statement. Borderline items considered: (a) Req 1.5 'no tests collected rather than import error' echoes the NO_TESTS_COLLECTED assertion in test_conftest_uppercase/test_conftest_badcase, but is the natural behavioral consequence of a successful collection over a test-less tree, not a transmitted test id/name; (b) Req 3.3/3.4 'no entry'/'exactly one entry' echoes the len(_conftestpath2mod)==0/1 assertions in test_setinitial_conftest_subdirs, but describes generic cache semantics and does NOT enumerate the parametrization ids (test/tests/whatever/.dotdir). No test file paths, function/class names, parametrization ids, verbatim gold lines, issue numbers (#5792/#5819), or fix-invented identifiers (unique_path, key) appear. Translation of test checks into behavioral requirements is the intended purpose, not leakage.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
