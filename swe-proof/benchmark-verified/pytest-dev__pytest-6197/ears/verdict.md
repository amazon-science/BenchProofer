# P2 adversarial audit — pytest-dev__pytest-6197

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 8 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 8 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py`, `probe_7.py`, `probe_8.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (8):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
"""REQ 1.2 (positive control): a tree containing a sub-package whose __init__.py
raises at import time, with no test selected inside it, SHALL complete with an
all-tests-passed exit status and NOT report a collection error.

Base: enumerating the package eagerly imports foopkg/__init__.py ('assert False')
-> collection error -> nonzero exit -> VIOLATED.
Patched: lazy -> exit OK -> HOLDS.
"""
import os, subprocess, sys, tempfile

d = tempfile.mkdtemp()
with open(os.path.join(d, "test_top.py"), "w") as f:
    f.write("def test():\n    pass\n")
pkg = os.path.join(d, "foopkg")
os.makedirs(pkg)
with open(os.path.join(pkg, "__init__.py"), "w") as f:
    f.write("assert False\n")

r = subprocess.run([sys.executable, "-m", "pytest", "-p", "no:cacheprovider", d],
                   cwd=d, capture_output=True, text=True)
print("EXIT", r.returncode)
print(r.stdout[-1500:])
print(r.stderr[-500:])
# ExitCode.OK == 0 (all collected tests passed, no collection errors)
sys.exit(0 if r.returncode == 0 else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""REQ 3.1 & 3.2: a src/ package not on sys.path is NOT put on the import path
by collection; a test importing such a module fails with ImportError, and the
run still completes all-tests-passed.

Base: eager mount inserts src/ dir semantics such that 'import nope' succeeds
(or otherwise the run doesn't behave as REQ3); Patched: import raises ImportError
and the pytest.raises test passes -> exit OK.
"""
import os, subprocess, sys, tempfile

d = tempfile.mkdtemp()
os.makedirs(os.path.join(d, "src", "nope"))
open(os.path.join(d, "src", "nope", "__init__.py"), "w").close()
with open(os.path.join(d, "test_it.py"), "w") as f:
    f.write(
        "import pytest\n"
        "def test():\n"
        "    with pytest.raises(ImportError):\n"
        "        import nope\n"
    )
r = subprocess.run([sys.executable, "-m", "pytest", "-p", "no:cacheprovider", d],
                   cwd=d, capture_output=True, text=True)
print("EXIT", r.returncode)
print(r.stdout[-1500:])
print(r.stderr[-500:])
sys.exit(0 if r.returncode == 0 else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""REQ 4.2 (SHALL keep): legitimate collection of tests inside a package is
preserved when the package dir is passed as an initial arg (with a test-bearing
__init__.py and another test module). Both the __init__ test and the module test
must be collected and pass.
"""
import os, subprocess, sys, tempfile

d = tempfile.mkdtemp()
pkg = os.path.join(d, "pkg")
os.makedirs(pkg)
with open(os.path.join(pkg, "__init__.py"), "w") as f:
    f.write("def test_init():\n    assert True\n")
with open(os.path.join(pkg, "test_mod.py"), "w") as f:
    f.write("def test_mod():\n    assert True\n")

# python_files must include __init__.py-matching pattern? default python_files is
# test_*.py *_test.py which does NOT match __init__.py; REQ4.1 conditions the
# init-module yield on it matching python_files. Here we just check the module
# tests collect and pass when passing the package dir.
r = subprocess.run([sys.executable, "-m", "pytest", "-p", "no:cacheprovider",
                    "-v", pkg], cwd=d, capture_output=True, text=True)
print("EXIT", r.returncode)
out = r.stdout
print(out[-1800:])
print(r.stderr[-400:])
ok = r.returncode == 0 and "test_mod" in out and "1 passed" in out
sys.exit(0 if ok else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""REQ 4.1 (SHALL keep): when a package's own __init__.py matches the configured
python_files pattern, the collection yields a Module for that __init__.py before
the package's other contents, and the __init__ test is collected & runs.

Configure python_files to include __init__.py so the init module is test-bearing.
"""
import os, subprocess, sys, tempfile

d = tempfile.mkdtemp()
with open(os.path.join(d, "tox.ini"), "w") as f:
    f.write("[pytest]\npython_files = *.py\n")
pkg = os.path.join(d, "pkg")
os.makedirs(pkg)
with open(os.path.join(pkg, "__init__.py"), "w") as f:
    f.write("def test_in_init():\n    assert True\n")
with open(os.path.join(pkg, "test_mod.py"), "w") as f:
    f.write("def test_mod():\n    assert True\n")

r = subprocess.run([sys.executable, "-m", "pytest", "-p", "no:cacheprovider",
                    "-v", d], cwd=d, capture_output=True, text=True)
print("EXIT", r.returncode)
out = r.stdout
print(out[-2000:])
print(r.stderr[-400:])
ok = (r.returncode == 0 and "test_in_init" in out and "test_mod" in out)
if ok:
    # ordering: __init__ module collected before test_mod
    ok = out.index("test_in_init") < out.index("test_mod")
sys.exit(0 if ok else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""REQ 2.1, 2.2 & 2.3: node construction does NOT resolve obj; obj resolves &
caches on first read (same object on repeat, no re-import); assigning obj makes
reads return the assigned value. Exercise PyobjMixin.obj on a Module node.
"""
import os, subprocess, sys, tempfile

d = tempfile.mkdtemp()
mod = os.path.join(d, "test_probe_mod.py")
with open(mod, "w") as f:
    f.write("VALUE = 12345\n"
            "def test_x():\n    assert True\n")

script = os.path.join(d, "run.py")
with open(script, "w") as f:
    f.write(
        "import sys, py\n"
        "from _pytest.config import _prepareconfig\n"
        "from _pytest.main import Session\n"
        "import _pytest.python as pymod\n"
        f"config = _prepareconfig([{d!r}])\n"
        "session = Session(config)\n"
        f"m = pymod.Module(py.path.local({mod!r}), parent=session)\n"
        "pre = getattr(m, '_obj', None)\n"
        "print('constructed_obj_unresolved', pre is None)\n"
        "o1 = m.obj\n"
        "o2 = m.obj\n"
        "print('same_cached', o1 is o2)\n"
        "print('has_value', getattr(o1, 'VALUE', None))\n"
        "sentinel = object()\n"
        "m.obj = sentinel\n"
        "print('assigned_returns', m.obj is sentinel)\n"
        "ok = (pre is None) and (o1 is o2) \\\n"
        "     and getattr(o1,'VALUE',None)==12345 and (m.obj is sentinel)\n"
        "sys.exit(0 if ok else 1)\n"
    )
r = subprocess.run([sys.executable, script], cwd=d, capture_output=True, text=True)
print("EXIT", r.returncode)
print(r.stdout[-1500:])
print(r.stderr[-1200:])
sys.exit(r.returncode)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
"""REQ 5.2: a package-level pytestmark skip declared in __init__.py is NO LONGER
reliably propagated to sibling tests once __init__.py is not eagerly imported.
At least one sibling test that eager-import would have skipped SHALL instead be
collected and executed (able to pass/fail on its own) rather than skipped.

Base: __init__.py is imported during enumeration -> pytestmark skip applies to
all siblings -> both skipped (2 skipped, exit 0).
Patched: __init__.py not imported during enumeration -> at least one sibling runs
(not skipped). Encode as: NOT all sibling tests are skipped.
"""
import os, re, subprocess, sys, tempfile

d = tempfile.mkdtemp()
pkg = os.path.join(d, "pkg")
os.makedirs(pkg)
with open(os.path.join(pkg, "__init__.py"), "w") as f:
    f.write("import pytest\npytestmark = pytest.mark.skip\n")
with open(os.path.join(pkg, "test_a.py"), "w") as f:
    f.write("def test_skip1():\n    assert 0\n"
            "def test_skip2():\n    assert 0\n")

r = subprocess.run([sys.executable, "-m", "pytest", "-p", "no:cacheprovider",
                    "-rs", d], cwd=d, capture_output=True, text=True)
out = r.stdout
print("EXIT", r.returncode)
print(out[-1800:])
print(r.stderr[-400:])
# count skipped from summary line
m = re.search(r"(\d+) skipped", out)
skipped = int(m.group(1)) if m else 0
ran = ("failed" in out) or ("passed" in out)
print("skipped_count", skipped, "some_ran", ran)
# REQ5.2: at least one sibling NOT skipped by package marker -> skipped < 2
ok = skipped < 2 and ran
sys.exit(0 if ok else 1)
```

Attack 7 — `probe_7.py` → holds on the patched tree (good)

```python
"""REQ 5.1 & 5.3 (SHALL keep): markers on test functions within imported modules
evaluate as before (skip/xfail), and pytest.importorskip behaves unchanged.
"""
import os, re, subprocess, sys, tempfile

d = tempfile.mkdtemp()
with open(os.path.join(d, "test_marks.py"), "w") as f:
    f.write(
        "import pytest\n"
        "@pytest.mark.skip(reason='r')\n"
        "def test_s():\n    assert 0\n"
        "@pytest.mark.xfail\n"
        "def test_xf():\n    assert 0\n"
        "def test_importorskip():\n"
        "    with pytest.raises(pytest.skip.Exception):\n"
        "        pytest.importorskip('this_module_does_not_exist_zzz')\n"
    )
r = subprocess.run([sys.executable, "-m", "pytest", "-p", "no:cacheprovider",
                    "-rsx", d], cwd=d, capture_output=True, text=True)
out = r.stdout
print("EXIT", r.returncode)
print(out[-1800:])
print(r.stderr[-400:])
sk = re.search(r"(\d+) skipped", out)
xf = re.search(r"(\d+) xfailed", out)
pa = re.search(r"(\d+) passed", out)
ok = (r.returncode == 0 and sk and int(sk.group(1)) == 1
      and xf and int(xf.group(1)) == 1 and pa and int(pa.group(1)) == 1)
sys.exit(0 if ok else 1)
```

Attack 8 — `probe_8.py` → holds on the patched tree (good)

```python
"""REQ 2.4: when a node's underlying object is resolved for the first time and it
participates in marker collection, marks unpacked from the object are added to
own_markers exactly once (no duplication across repeated obj access).

Exercise: build a Module with a module-level pytestmark, read .obj several times,
and assert the mark appears exactly once in own_markers.
"""
import os, subprocess, sys, tempfile

d = tempfile.mkdtemp()
mod = os.path.join(d, "test_dupmark.py")
with open(mod, "w") as f:
    f.write("import pytest\n"
            "pytestmark = pytest.mark.skip(reason='pkgmark')\n"
            "def test_x():\n    assert True\n")
script = os.path.join(d, "run.py")
with open(script, "w") as f:
    f.write(
        "import sys, py\n"
        "from _pytest.config import _prepareconfig\n"
        "from _pytest.main import Session\n"
        "import _pytest.python as pymod\n"
        f"config = _prepareconfig([{d!r}])\n"
        "session = Session(config)\n"
        f"m = pymod.Module(py.path.local({mod!r}), parent=session)\n"
        "for _ in range(4):\n"
        "    _ = m.obj\n"
        "names = [mk.name for mk in m.own_markers]\n"
        "print('own_markers', names)\n"
        "cnt = names.count('skip')\n"
        "print('skip_count', cnt)\n"
        "sys.exit(0 if cnt == 1 else 1)\n"
    )
r = subprocess.run([sys.executable, script], cwd=d, capture_output=True, text=True)
print("EXIT", r.returncode)
print(r.stdout[-1500:])
print(r.stderr[-1200:])
sys.exit(r.returncode)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""REQ 1.2 (positive control): a tree containing a sub-package whose __init__.py
raises at import time, with no test selected inside it, SHALL complete with an
all-tests-passed exit status and NOT report a collection error.

Base: enumerating the package eagerly imports foopkg/__init__.py ('assert False')
-> collection error -> nonzero exit -> VIOLATED.
Patched: lazy -> exit OK -> HOLDS.
"""
import os, subprocess, sys, tempfile

d = tempfile.mkdtemp()
with open(os.path.join(d, "test_top.py"), "w") as f:
    f.write("def test():\n    pass\n")
pkg = os.path.join(d, "foopkg")
os.makedirs(pkg)
with open(os.path.join(pkg, "__init__.py"), "w") as f:
    f.write("assert False\n")

r = subprocess.run([sys.executable, "-m", "pytest", "-p", "no:cacheprovider", d],
                   cwd=d, capture_output=True, text=True)
print("EXIT", r.returncode)
print(r.stdout[-1500:])
print(r.stderr[-500:])
# ExitCode.OK == 0 (all collected tests passed, no collection errors)
sys.exit(0 if r.returncode == 0 else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance pytest-dev__pytest-6197: fix makes underlying-object access lazy so enumerating a package's directory no longer imports its own __init__.py. Base Package.collect starts with `self._mount_obj_if_needed()` (eager import); gold removes that, drops the Module.__init__ _ALLOW_MARKERS special-case, and refactors PyobjMixin.obj into a lazy cached property.

8 probes, all HOLD on the gold-patched tree:
- probe_1 (REQ 1.2, POSITIVE CONTROL): sub-package foopkg/__init__.py = 'assert False', no test selected inside it -> run exits 0, no collection error. VIOLATED at base (exit 1, collection errors), HOLDS patched -> discriminates.
- probe_2 (REQ 3.1/3.2): src/nope/__init__.py off sys.path; a test does `with pytest.raises(ImportError): import nope`; run exits 0. VIOLATED at base.
- probe_3 (REQ 4.2 SHALL-keep): passing a package dir still collects & passes its test module.
- probe_4 (REQ 4.1 SHALL-keep): with python_files=*.py the test-bearing __init__.py is collected and ordered before the package's other modules.
- probe_5 (REQ 2.1/2.2/2.3): Module construction leaves _obj unresolved; obj resolves+caches on first read (same object on repeat); assigning obj makes subsequent reads return the assigned value.
- probe_6 (REQ 5.2): package-level pytestmark=skip in __init__.py is NOT reliably propagated to siblings once __init__.py is no longer eagerly imported -> skipped<2 and at least one sibling runs. VIOLATED at base (2 skipped, full propagation).
- probe_7 (REQ 5.1/5.3 SHALL-keep): function-level skip/xfail evaluate as before and importorskip raises Skipped for a missing module (1 passed,1 skipped,1 xfailed).
- probe_8 (REQ 2.4): repeated obj access adds the module's unpacked marks to own_markers exactly once (skip_count==1, no duplication).

Discriminating power confirmed: positive control probe_1 FAILS at base, HOLDS patched (prepatch_reproduced=true); probes 2 and 6 also fail at base and hold patched.

Weak-candidate check (REQUIRED floor met): weak.diff wraps the eager `_mount_obj_if_needed()` in try/except pass — a naive reading that only silences the import-error symptom without deferring the import. The probe suite REJECTS it: probe_2 VIOLATED (src/ package still imported/importable -> ImportError not raised) and probe_6 VIOLATED (package marker still fully propagates, 2 skipped). So the suite discriminates a plausibly-wrong partial fix from the real lazy-import fix. No probe-conforming alternative patch was found that would fail the hidden tests.

Verdict SOUND: >=5 distinct probes (8) all hold on patched, positive control discriminates base vs patched, and >=1 wrong-fix candidate is rejected by the suite.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 8 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 8 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py`, `probe_7.py`, `probe_8.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (8):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts, and on this backend both roles put it through the same derivation: every block below is a requirement probe run on the gold-patched tree, and the `machine verdict:` line each role publishes above reports BOTH that its probes hold there and how many candidate patches the probe suite rejected — so the two roles re-ran ONE probe suite and each recorded its own outcome for every probe in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `probe_1.py` → holds on the patched tree (good)

Attack 2 — `probe_2.py` → holds on the patched tree (good)

Attack 3 — `probe_3.py` → holds on the patched tree (good)

Attack 4 — `probe_4.py` → holds on the patched tree (good)

Attack 5 — `probe_5.py` → holds on the patched tree (good)

Attack 6 — `probe_6.py` → holds on the patched tree (good)

Attack 7 — `probe_7.py` → holds on the patched tree (good)

Attack 8 — `probe_8.py` → holds on the patched tree (good)

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""REQ 1.2 (positive control): a tree containing a sub-package whose __init__.py
raises at import time, with no test selected inside it, SHALL complete with an
all-tests-passed exit status and NOT report a collection error.

Base: enumerating the package eagerly imports foopkg/__init__.py ('assert False')
-> collection error -> nonzero exit -> VIOLATED.
Patched: lazy -> exit OK -> HOLDS.
"""
import os, subprocess, sys, tempfile

d = tempfile.mkdtemp()
with open(os.path.join(d, "test_top.py"), "w") as f:
    f.write("def test():\n    pass\n")
pkg = os.path.join(d, "foopkg")
os.makedirs(pkg)
with open(os.path.join(pkg, "__init__.py"), "w") as f:
    f.write("assert False\n")

r = subprocess.run([sys.executable, "-m", "pytest", "-p", "no:cacheprovider", d],
                   cwd=d, capture_output=True, text=True)
print("EXIT", r.returncode)
print(r.stdout[-1500:])
print(r.stderr[-500:])
# ExitCode.OK == 0 (all collected tests passed, no collection errors)
sys.exit(0 if r.returncode == 0 else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance pytest-dev__pytest-6197: fix makes underlying-object access lazy so enumerating a package's directory no longer imports its own __init__.py. Base Package.collect starts with `self._mount_obj_if_needed()` (eager import); gold removes that, drops the Module.__init__ _ALLOW_MARKERS special-case, and refactors PyobjMixin.obj into a lazy cached property.

8 probes, all HOLD on the gold-patched tree:
- probe_1 (REQ 1.2, POSITIVE CONTROL): sub-package foopkg/__init__.py = 'assert False', no test selected inside it -> run exits 0, no collection error. VIOLATED at base (exit 1, collection errors), HOLDS patched -> discriminates.
- probe_2 (REQ 3.1/3.2): src/nope/__init__.py off sys.path; a test does `with pytest.raises(ImportError): import nope`; run exits 0. VIOLATED at base.
- probe_3 (REQ 4.2 SHALL-keep): passing a package dir still collects & passes its test module.
- probe_4 (REQ 4.1 SHALL-keep): with python_files=*.py the test-bearing __init__.py is collected and ordered before the package's other modules.
- probe_5 (REQ 2.1/2.2/2.3): Module construction leaves _obj unresolved; obj resolves+caches on first read (same object on repeat); assigning obj makes subsequent reads return the assigned value.
- probe_6 (REQ 5.2): package-level pytestmark=skip in __init__.py is NOT reliably propagated to siblings once __init__.py is no longer eagerly imported -> skipped<2 and at least one sibling runs. VIOLATED at base (2 skipped, full propagation).
- probe_7 (REQ 5.1/5.3 SHALL-keep): function-level skip/xfail evaluate as before and importorskip raises Skipped for a missing module (1 passed,1 skipped,1 xfailed).
- probe_8 (REQ 2.4): repeated obj access adds the module's unpacked marks to own_markers exactly once (skip_count==1, no duplication).

Discriminating power confirmed: positive control probe_1 FAILS at base, HOLDS patched (prepatch_reproduced=true); probes 2 and 6 also fail at base and hold patched.

Weak-candidate check (REQUIRED floor met): weak.diff wraps the eager `_mount_obj_if_needed()` in try/except pass — a naive reading that only silences the import-error symptom without deferring the import. The probe suite REJECTS it: probe_2 VIOLATED (src/ package still imported/importable -> ImportError not raised) and probe_6 VIOLATED (package marker still fully propagates, 2 skipped). So the suite discriminates a plausibly-wrong partial fix from the real lazy-import fix. No probe-conforming alternative patch was found that would fail the hidden tests.

Verdict SOUND: >=5 distinct probes (8) all hold on patched, positive control discriminates base vs patched, and >=1 wrong-fix candidate is rejected by the suite.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** The prior G-PANEL-2 UNFAITHFUL verdict rests on a MISREADING of REQ 5.2. It claimed 5.2 predicts 'both siblings run and fail', then observed 'test_skip1 FAILED, test_skip2 SKIPPED' (order-dependent partial propagation) and called that a mismatch. But 5.2 never says both run. Its literal text: the package-level marker 'SHALL NOT be reliably propagated to ALL of the sibling tests ... AT LEAST ONE such sibling test ... SHALL instead be collected and executed — able to pass or fail on its own', plus the explicit hedge '(whether any given later-collected sibling still observes the marker is no longer guaranteed)'. That is EXACTLY the observed partial propagation, and it discriminates from base.

Probe evidence (via nl_attack, gold-patched vs --base):
- REQ 5.2: pkg/__init__.py sets pytestmark=skip; siblings test_skip1/test_skip2 both `assert 0`. PATCHED: exit=1, `1 failed, 1 skipped` (test_skip1 FAILED — executed on its own, marker NOT applied). BASE: exit=1 mapped from `2 skipped` (both skipped, full propagation). REQ 5.2 HOLDS; base VIOLATES. The 'at least one sibling collected and executed' condition is met.
- REQ 1 (probe2): tree with foobar/__init__.py = `assert False`, no test selected inside; top-level test passes -> patched exit=0, '1 passed', no collection error. HOLDS.
- REQ 4.1 (probe2): package with python_files including __init__.py -> `pkg/__init__.py::test_in_init` collected BEFORE `pkg/test_z.py::test_z` (init idx 313 < z idx 380). HOLDS.
- REQ 3 (probe3): off-path src/mypkg not inserted on sys.path; a test importing mypkg.mod hits ImportError and the run still ends '1 passed', exit=0. HOLDS.

Requirements 2 (lazy mount, cache-once, setter, marker-once) and 4.2-4.4 mirror the gold patch verbatim: obj property caches _obj on first _getobj(), setter writes _obj, Module.__init__ removal + Package.collect no longer calling _mount_obj_if_needed. All consistent with the diff. G-PANEL-2 should be FAITHFUL; the recorded fail is a reading error, not a modeling defect.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** requirements.md describes behavior and localizes the change to legitimately-named pre-existing source symbols (src/_pytest/python.py, PyobjMixin.obj, Module collector, Package.collect). No test file paths, no test function/class names (test_does_not_eagerly_collect_packages, test_does_not_put_src_on_path, test_skip_package), no parametrization ids, no quoted test/gold code, and no fix-invented identifiers (_ALLOW_MARKERS, _mount_obj_if_needed are only described generically as 'lazy-mount helper' / 'participates in marker collection'). The 'assert False' failing-init example (Req 1.2) is already in the public problem_statement. Req 3 (src-layout / ImportError) and Req 5.2 (package-level marker no longer reliably skips siblings) correspond to hidden tests but are stated as generalized behavior (src/<pkg>/__init__.py, 'at least one such sibling'), which is legitimate test->behavior translation rather than transmitting the tests. No case enumeration mirrors the test parametrization.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
