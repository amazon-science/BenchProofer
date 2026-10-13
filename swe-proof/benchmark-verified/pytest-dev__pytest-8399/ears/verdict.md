# P2 adversarial audit — pytest-dev__pytest-8399

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
"""POSITIVE CONTROL + Req 2.1/2.3/2.4: default `pytest --fixtures` against
xunit setup/teardown tests must NOT emit any 'no docstring available' notice
(the synthesized fixtures are hidden) and must exit 0.

Base (unpatched, 6.2.0-era names lack leading underscore) => the fixtures leak
into default output and each emits 'no docstring available' => probe FAILS.
Patched => hidden => probe HOLDS.
"""
import subprocess, sys, tempfile, os, textwrap

d = tempfile.mkdtemp()
test = os.path.join(d, "test_xunit.py")
with open(test, "w") as f:
    f.write(textwrap.dedent('''
        def setup_module(): pass
        def teardown_module(): pass
        def setup_function(func): pass
        def teardown_function(func): pass
        def test_world(): pass
        class Test(object):
            def setup_class(cls): pass
            def teardown_class(cls): pass
            def setup_method(self, meth): pass
            def teardown_method(self, meth): pass
            def test_method(self): pass
    '''))

r = subprocess.run([sys.executable, "-m", "pytest", "--fixtures", test],
                   cwd=d, capture_output=True, text=True)
out = r.stdout + r.stderr
print("returncode:", r.returncode)
print("has 'no docstring available':", "no docstring available" in out)
# show any leaked xunit fixture lines
for line in out.splitlines():
    if "xunit" in line or "no docstring" in line:
        print("LINE:", line.strip())

ok = (r.returncode == 0) and ("no docstring available" not in out)
print("HOLDS" if ok else "VIOLATED")
sys.exit(0 if ok else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""Req 1.1 & 1.3 & 1.4: the module/function/class/method synthesized xunit
fixtures each get a name whose first char is '_', built from the same template
+ owning object name (i.e. exactly '_' + previous name). Verify via
`--fixtures -v` output which lists fixture names.

Expected private names:
  _xunit_setup_module_fixture_<module>
  _xunit_setup_function_fixture_<module>
  _xunit_setup_class_fixture_<Class>
  _xunit_setup_method_fixture_<Class>
"""
import subprocess, sys, tempfile, os, textwrap

d = tempfile.mkdtemp()
test = os.path.join(d, "test_xunit.py")
with open(test, "w") as f:
    f.write(textwrap.dedent('''
        def setup_module(): pass
        def teardown_module(): pass
        def setup_function(func): pass
        def teardown_function(func): pass
        def test_world(): pass
        class Test(object):
            def setup_class(cls): pass
            def teardown_class(cls): pass
            def setup_method(self, meth): pass
            def teardown_method(self, meth): pass
            def test_method(self): pass
    '''))

r = subprocess.run([sys.executable, "-m", "pytest", "--fixtures", "-v", test],
                   cwd=d, capture_output=True, text=True)
out = r.stdout + r.stderr
print("returncode:", r.returncode)

needed_private = [
    "_xunit_setup_module_fixture_test_xunit",
    "_xunit_setup_function_fixture_test_xunit",
    "_xunit_setup_class_fixture_Test",
    "_xunit_setup_method_fixture_Test",
]
ok = r.returncode == 0
for name in needed_private:
    present = name in out
    # ensure the NON-underscore leaked variant is NOT present as a standalone fixture name
    leaked = ("\n" + name[1:] + " ") in ("\n"+out) or ("\n" + name[1:] + "\n") in ("\n"+out)
    print(f"{name}: present={present}")
    if not present:
        ok = False

print("HOLDS" if ok else "VIOLATED")
sys.exit(0 if ok else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""Req 3.1 & 3.2 & 3.3 & 3.5: under `-v`, the synthesized xunit fixtures ARE
shown and each docstring-less one emits exactly one 'no docstring available'
notice; run exits 0. Our test file yields 4 synthesized xunit fixtures =>
exactly 4 notices.
"""
import subprocess, sys, tempfile, os, textwrap

d = tempfile.mkdtemp()
test = os.path.join(d, "test_xunit.py")
with open(test, "w") as f:
    f.write(textwrap.dedent('''
        def setup_module(): pass
        def teardown_module(): pass
        def setup_function(func): pass
        def teardown_function(func): pass
        def test_world(): pass
        class Test(object):
            def setup_class(cls): pass
            def teardown_class(cls): pass
            def setup_method(self, meth): pass
            def teardown_method(self, meth): pass
            def test_method(self): pass
    '''))

r = subprocess.run([sys.executable, "-m", "pytest", "--fixtures", "-v", test],
                   cwd=d, capture_output=True, text=True)
out = r.stdout + r.stderr
n = out.count("no docstring available")
print("returncode:", r.returncode)
print("no-docstring notice count:", n)
shown = all(nm in out for nm in [
    "_xunit_setup_module_fixture_test_xunit",
    "_xunit_setup_function_fixture_test_xunit",
    "_xunit_setup_class_fixture_Test",
    "_xunit_setup_method_fixture_Test",
])
print("all 4 fixtures shown:", shown)
ok = (r.returncode == 0) and shown and (n == 4)
print("HOLDS" if ok else "VIOLATED")
sys.exit(0 if ok else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""Req 1.2 & 2.2 & 3.4: unittest.TestCase class-level setUpClass/tearDownClass.
Default `--fixtures` must NOT show the synthesized unittest fixture (no
'no docstring available'), exit 0. Under `-v` the fixture IS shown with its
'no docstring available' notice, and its name starts with '_':
  _unittest_setUpClass_fixture_MyTestCase
"""
import subprocess, sys, tempfile, os, textwrap

d = tempfile.mkdtemp()
test = os.path.join(d, "test_ut.py")
with open(test, "w") as f:
    f.write(textwrap.dedent('''
        import unittest
        class MyTestCase(unittest.TestCase):
            @classmethod
            def setUpClass(cls): pass
            def test_func1(self): pass
            @classmethod
            def tearDownClass(cls): pass
    '''))

# default
r1 = subprocess.run([sys.executable, "-m", "pytest", "--fixtures", test],
                    cwd=d, capture_output=True, text=True)
o1 = r1.stdout + r1.stderr
# verbose
r2 = subprocess.run([sys.executable, "-m", "pytest", "--fixtures", "-v", test],
                    cwd=d, capture_output=True, text=True)
o2 = r2.stdout + r2.stderr

print("default rc:", r1.returncode, "has no-docstring:", "no docstring available" in o1)
print("verbose rc:", r2.returncode, "verbose no-docstring count:", o2.count("no docstring available"))
name = "_unittest_setUpClass_fixture_MyTestCase"
print("private name present in verbose:", name in o2)

ok = (r1.returncode == 0 and "no docstring available" not in o1
      and r2.returncode == 0 and name in o2 and o2.count("no docstring available") >= 1)
print("HOLDS" if ok else "VIOLATED")
sys.exit(0 if ok else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""Req 4.1 & 4.2: renaming the fixtures private must NOT change setup/teardown
execution — the xunit hooks still run at the right lifecycle points and the
tests pass. We record hook invocation order in a file and assert it.
"""
import subprocess, sys, tempfile, os, textwrap

d = tempfile.mkdtemp()
logf = os.path.join(d, "order.log")
test = os.path.join(d, "test_life.py")
with open(test, "w") as f:
    f.write(textwrap.dedent(f'''
        LOG = {logf!r}
        def rec(s):
            with open(LOG, "a") as fh: fh.write(s + "\\n")
        def setup_module(m): rec("setup_module")
        def teardown_module(m): rec("teardown_module")
        def setup_function(fn): rec("setup_function")
        def teardown_function(fn): rec("teardown_function")
        def test_a(): rec("test_a")
        class TestK:
            def setup_class(cls): rec("setup_class")
            def teardown_class(cls): rec("teardown_class")
            def setup_method(self, m): rec("setup_method")
            def teardown_method(self, m): rec("teardown_method")
            def test_m(self): rec("test_m")
    '''))

r = subprocess.run([sys.executable, "-m", "pytest", "-q", test],
                   cwd=d, capture_output=True, text=True)
out = r.stdout + r.stderr
print("returncode:", r.returncode)
order = open(logf).read().splitlines() if os.path.exists(logf) else []
print("order:", order)

expected_prefix_module = order and order[0] == "setup_module"
# function-level hooks wrap test_a
seg = order
ok_func = ("setup_function" in seg and "test_a" in seg
           and seg.index("setup_function") < seg.index("test_a") < seg.index("teardown_function"))
# class hooks wrap the method test
ok_class = ("setup_class" in seg and "test_m" in seg
            and seg.index("setup_class") < seg.index("setup_method")
            < seg.index("test_m") < seg.index("teardown_method")
            < seg.index("teardown_class"))
ok_mod_end = order and order[-1] == "teardown_module"

ok = (r.returncode == 0 and "2 passed" in out and expected_prefix_module
      and ok_func and ok_class and ok_mod_end)
print("module-first:", expected_prefix_module, "func-wrap:", ok_func,
      "class-wrap:", ok_class, "module-last:", ok_mod_end)
print("HOLDS" if ok else "VIOLATED")
sys.exit(0 if ok else 1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
"""Req 4.3: skip conditions on unittest test cases are still honored when the
synthesized fixture runs — a skipped case is NOT set up. If the whole class is
skipped, setUpClass must not run.
"""
import subprocess, sys, tempfile, os, textwrap

d = tempfile.mkdtemp()
logf = os.path.join(d, "ran.log")
test = os.path.join(d, "test_skip.py")
with open(test, "w") as f:
    f.write(textwrap.dedent(f'''
        import unittest
        LOG = {logf!r}
        def rec(s):
            with open(LOG, "a") as fh: fh.write(s + "\\n")
        @unittest.skip("skip whole case")
        class MyTestCase(unittest.TestCase):
            @classmethod
            def setUpClass(cls): rec("setUpClass")
            def setUp(self): rec("setUp")
            def test_func1(self): rec("test")
    '''))

r = subprocess.run([sys.executable, "-m", "pytest", "-q", test],
                   cwd=d, capture_output=True, text=True)
out = r.stdout + r.stderr
print("returncode:", r.returncode)
ran = open(logf).read().splitlines() if os.path.exists(logf) else []
print("recorded:", ran)
print("skipped in output:", "skipped" in out or "1 skipped" in out)

ok = (r.returncode == 0 and "setUpClass" not in ran and "setUp" not in ran
      and "test" not in ran)
print("HOLDS" if ok else "VIOLATED")
sys.exit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""POSITIVE CONTROL + Req 2.1/2.3/2.4: default `pytest --fixtures` against
xunit setup/teardown tests must NOT emit any 'no docstring available' notice
(the synthesized fixtures are hidden) and must exit 0.

Base (unpatched, 6.2.0-era names lack leading underscore) => the fixtures leak
into default output and each emits 'no docstring available' => probe FAILS.
Patched => hidden => probe HOLDS.
"""
import subprocess, sys, tempfile, os, textwrap

d = tempfile.mkdtemp()
test = os.path.join(d, "test_xunit.py")
with open(test, "w") as f:
    f.write(textwrap.dedent('''
        def setup_module(): pass
        def teardown_module(): pass
        def setup_function(func): pass
        def teardown_function(func): pass
        def test_world(): pass
        class Test(object):
            def setup_class(cls): pass
            def teardown_class(cls): pass
            def setup_method(self, meth): pass
            def teardown_method(self, meth): pass
            def test_method(self): pass
    '''))

r = subprocess.run([sys.executable, "-m", "pytest", "--fixtures", test],
                   cwd=d, capture_output=True, text=True)
out = r.stdout + r.stderr
print("returncode:", r.returncode)
print("has 'no docstring available':", "no docstring available" in out)
# show any leaked xunit fixture lines
for line in out.splitlines():
    if "xunit" in line or "no docstring" in line:
        print("LINE:", line.strip())

ok = (r.returncode == 0) and ("no docstring available" not in out)
print("HOLDS" if ok else "VIOLATED")
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

pytest-8399: gold prefixes '_' to the 4 synthesized xunit fixture names (python.py) and the unittest _make_xunit_fixture name (unittest.py) so they are hidden at default `--fixtures` verbosity. Probes exercise pytest as a subprocess (stdlib only, no pytest-as-testrunner).

Probe results (patched HOLDS / base):
- probe_1 (POSITIVE CONTROL; Req 2.1/2.3/2.4): default `--fixtures` on xunit tests emits NO 'no docstring available' and exits 0. HOLDS patched, FAILED at base (4 notices + leaked xunit_* names) => discriminates.
- probe_2 (Req 1.1/1.3/1.4): verbose listing shows the 4 private names _xunit_setup_{module,function,class,method}_fixture_* (template+owner unchanged bar leading '_'). HOLDS.
- probe_3 (Req 3.1/3.3/3.5): verbose shows all 4 fixtures and emits exactly 4 no-docstring notices, exit 0. HOLDS patched, FAILED at base (fixtures not shown-by-private-name; also positive-control leg).
- probe_4 (Req 1.2/2.2/3.4): unittest.TestCase setUpClass — default hides fixture (no notice, exit 0), verbose shows _unittest_setUpClass_fixture_MyTestCase with its notice. HOLDS patched, FAILED at base => discriminates.
- probe_5 (Req 4.1/4.2): setup/teardown hooks still run in correct lifecycle order (module wraps run; function wraps test_a; class wraps method), 2 passed. HOLDS.
- probe_6 (Req 4.3): skipped unittest case is NOT set up (setUpClass/setUp/test never recorded). HOLDS.

Candidate wrong-fix (weak_partial.diff): fixes only python.py (4 xunit names) leaving unittest.py name un-prefixed — the lazy/partial reading of the requirements. Applies at base_commit. Suite REJECTS it: probe_4 VIOLATED (unittest fixture still leaks 'no docstring available' at default verbosity, private name absent), while probe_1 still passes. This demonstrates the suite discriminates a partial implementation that the hidden test (test_fixtures_setup_setUpClass_issue8394, which targets exactly the unittest path) would also fail. No too-weak (probe-conforming yet non-resolving) patch found.

Conclusion: 6 distinct probes all hold on the gold-patched tree; positive controls (probe_1/3/4) fail at base and hold patched (discriminating power confirmed); the partial-fix candidate is rejected by the suite. Requirements are faithful and adequately tight. SOUND.

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
"""POSITIVE CONTROL + Req 2.1/2.3/2.4: default `pytest --fixtures` against
xunit setup/teardown tests must NOT emit any 'no docstring available' notice
(the synthesized fixtures are hidden) and must exit 0.

Base (unpatched, 6.2.0-era names lack leading underscore) => the fixtures leak
into default output and each emits 'no docstring available' => probe FAILS.
Patched => hidden => probe HOLDS.
"""
import subprocess, sys, tempfile, os, textwrap

d = tempfile.mkdtemp()
test = os.path.join(d, "test_xunit.py")
with open(test, "w") as f:
    f.write(textwrap.dedent('''
        def setup_module(): pass
        def teardown_module(): pass
        def setup_function(func): pass
        def teardown_function(func): pass
        def test_world(): pass
        class Test(object):
            def setup_class(cls): pass
            def teardown_class(cls): pass
            def setup_method(self, meth): pass
            def teardown_method(self, meth): pass
            def test_method(self): pass
    '''))

r = subprocess.run([sys.executable, "-m", "pytest", "--fixtures", test],
                   cwd=d, capture_output=True, text=True)
out = r.stdout + r.stderr
print("returncode:", r.returncode)
print("has 'no docstring available':", "no docstring available" in out)
# show any leaked xunit fixture lines
for line in out.splitlines():
    if "xunit" in line or "no docstring" in line:
        print("LINE:", line.strip())

ok = (r.returncode == 0) and ("no docstring available" not in out)
print("HOLDS" if ok else "VIOLATED")
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

pytest-8399: gold prefixes '_' to the 4 synthesized xunit fixture names (python.py) and the unittest _make_xunit_fixture name (unittest.py) so they are hidden at default `--fixtures` verbosity. Probes exercise pytest as a subprocess (stdlib only, no pytest-as-testrunner).

Probe results (patched HOLDS / base):
- probe_1 (POSITIVE CONTROL; Req 2.1/2.3/2.4): default `--fixtures` on xunit tests emits NO 'no docstring available' and exits 0. HOLDS patched, FAILED at base (4 notices + leaked xunit_* names) => discriminates.
- probe_2 (Req 1.1/1.3/1.4): verbose listing shows the 4 private names _xunit_setup_{module,function,class,method}_fixture_* (template+owner unchanged bar leading '_'). HOLDS.
- probe_3 (Req 3.1/3.3/3.5): verbose shows all 4 fixtures and emits exactly 4 no-docstring notices, exit 0. HOLDS patched, FAILED at base (fixtures not shown-by-private-name; also positive-control leg).
- probe_4 (Req 1.2/2.2/3.4): unittest.TestCase setUpClass — default hides fixture (no notice, exit 0), verbose shows _unittest_setUpClass_fixture_MyTestCase with its notice. HOLDS patched, FAILED at base => discriminates.
- probe_5 (Req 4.1/4.2): setup/teardown hooks still run in correct lifecycle order (module wraps run; function wraps test_a; class wraps method), 2 passed. HOLDS.
- probe_6 (Req 4.3): skipped unittest case is NOT set up (setUpClass/setUp/test never recorded). HOLDS.

Candidate wrong-fix (weak_partial.diff): fixes only python.py (4 xunit names) leaving unittest.py name un-prefixed — the lazy/partial reading of the requirements. Applies at base_commit. Suite REJECTS it: probe_4 VIOLATED (unittest fixture still leaks 'no docstring available' at default verbosity, private name absent), while probe_1 still passes. This demonstrates the suite discriminates a partial implementation that the hidden test (test_fixtures_setup_setUpClass_issue8394, which targets exactly the unittest path) would also fail. No too-weak (probe-conforming yet non-resolving) patch found.

Conclusion: 6 distinct probes all hold on the gold-patched tree; positive controls (probe_1/3/4) fail at base and hold patched (discriminating power confirmed); the partial-fix candidate is rejected by the suite. Requirements are faithful and adequately tight. SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Req 1.1/1.2 (leading underscore on all module/function/class/method + unittest fixtures) = patch's literal change. Req 1.3/1.4 (name differs only by leading '_', still unique per owning object) — probe shows '_xunit_setup_module_fixture_test_xunit', '_unittest_setUpClass_fixture_MyTestCase' etc., identical to base except the '_' prefix; uniqueness via owning obj __name__/__qualname__ preserved. Req 2.1/2.2 hidden at default, 2.3 no 'no docstring' notice, 2.4 exit 0 — all confirmed. Req 3.1-3.5 (-v reveals, one notice per shown fixture, exit 0) — confirmed 5 notices for 5 fixtures. Req 4 (execution behavior preserved) — patch touches ONLY the name= kwarg; scope/autouse/fixture bodies (skip handling, cleanup on success/setup-fail/teardown-fail) are unchanged in the diff, so Req 4.1-4.4 hold trivially. F2P test test_fixtures_setup_setUpClass_issue8394 passes (G-RESOLVE=resolved). No over/under-claim or wrong boundary found.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The document translates the hidden tests' checks into behavioral requirements without transmitting the tests themselves. It names real source symbols (_inject_setup_module_fixture/_function/_class/_method, _make_xunit_fixture in unittest.py, _showfixtures_main, _show_fixtures_per_test, write_fixture) — legitimate localization of the change site. The gold edit's actual behavior (prefix generated fixture names with a leading underscore; hidden at default verbosity, shown under -v) is described in prose, not by quoting the new identifiers like `_xunit_setup_module_fixture_...`. The 'no docstring available' notice and the -v behavior are already public in the problem_statement. The xunit module/function/class/method coverage exceeds problem_statement (which only shows unittest setUpClass) but corresponds to the gold patch's four edited call sites, described behaviorally — not the test_nose.py xunit test. No leaked test file paths (testing/test_nose.py, testing/test_unittest.py), test function names (test_fixtures_setup_setUpClass_issue8394, test_fixtures_nose_setup_issue8394), parametrization ids, makepyfile bodies, or the fnmatch_lines([match,match,match,match]) count. Req 3.3 states the notice count behaviorally ('one per shown fixture') rather than hardcoding 4. No semantic gold/test reconstruction beyond behavioral description.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
