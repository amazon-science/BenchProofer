# P2 adversarial audit — pytest-dev__pytest-7236

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

Counterexample / evidence:

```
weakA applies the _is_skipped helper to collect() and the fixture (Req 4/5) but leaves the runtest postponement unconditional (`if self.config.getoption('usepdb')` without `and not _is_skipped(self.obj)`) — the exact original regression. Under --pdb a @unittest.skip test then has its stashed tearDown called during the item teardown step: probe_1 (Req 1.3) fails teardown_ran=True; probe_3 (Req 1.1) fails with '1 skipped, 1 error' because the booby-trapped tearDown fires. Suite rejects it.
```

**Attacks re-run (7):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
# Req 1.3 (POSITIVE CONTROL): a @unittest.skip TestCase run with --pdb must NOT
# have its tearDown invoked (neither immediately nor by a later explicit call).
# Patched: tearDown marker absent. Base: tearDown runs -> marker present -> FAIL.
import os, sys, subprocess, tempfile, textwrap

d = tempfile.mkdtemp(prefix="probe1_")
marker = os.path.join(d, "teardown_ran")
test = os.path.join(d, "test_x.py")
open(test, "w").write(textwrap.dedent(f"""
    import unittest
    class T(unittest.TestCase):
        @unittest.skip("skipping")
        def test_a(self):
            pass
        def tearDown(self):
            open({marker!r}, "w").write("x")
"""))
r = subprocess.run([sys.executable, "-m", "pytest", "--pdb", "-p", "no:cacheprovider",
                    test, "-q"], cwd=d, stdin=subprocess.DEVNULL,
                   capture_output=True, text=True, timeout=300)
print("rc", r.returncode)
print(r.stdout[-2000:])
print(r.stderr[-500:])
ran = os.path.exists(marker)
print("teardown_ran:", ran)
sys.exit(1 if ran else 0)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
# Req 1.2: a @unittest.skip TestCase run with --pdb must NOT invoke setUp.
import os, sys, subprocess, tempfile, textwrap

d = tempfile.mkdtemp(prefix="probe2_")
marker = os.path.join(d, "setup_ran")
test = os.path.join(d, "test_x.py")
open(test, "w").write(textwrap.dedent(f"""
    import unittest
    class T(unittest.TestCase):
        def setUp(self):
            open({marker!r}, "w").write("x")
        @unittest.skip("skipping")
        def test_a(self):
            pass
"""))
r = subprocess.run([sys.executable, "-m", "pytest", "--pdb", "-p", "no:cacheprovider",
                    test, "-q"], cwd=d, stdin=subprocess.DEVNULL,
                   capture_output=True, text=True, timeout=300)
print("rc", r.returncode)
print(r.stdout[-2000:])
ran = os.path.exists(marker)
print("setup_ran:", ran)
sys.exit(1 if ran else 0)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
# Req 1.1: a @unittest.skip TestCase run with --pdb must be REPORTED as skipped,
# NOT as error or failure. setUp/tearDown are booby-trapped so that if they run,
# the test errors. Patched: rc==0, "1 skipped", no error/failed.
import os, sys, subprocess, tempfile, textwrap, re

d = tempfile.mkdtemp(prefix="probe3_")
test = os.path.join(d, "test_x.py")
open(test, "w").write(textwrap.dedent("""
    import unittest
    class T(unittest.TestCase):
        def setUp(self):
            raise RuntimeError("setup boom")
        @unittest.skip("skipping")
        def test_a(self):
            pass
        def tearDown(self):
            raise RuntimeError("teardown boom")
"""))
r = subprocess.run([sys.executable, "-m", "pytest", "--pdb", "-p", "no:cacheprovider",
                    test], cwd=d, stdin=subprocess.DEVNULL,
                   capture_output=True, text=True, timeout=300)
out = r.stdout
print("rc", r.returncode)
print(out[-2500:])
# The final summary line, e.g. "1 skipped in 0.01s" or "1 error in ..."
last = [l for l in out.splitlines() if re.search(r"(passed|failed|error|skipped)\b", l)]
summary = last[-1] if last else ""
print("summary:", summary)
ok = (r.returncode == 0 and "skipped" in summary
      and "error" not in summary and "failed" not in summary)
sys.exit(0 if ok else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
# Req 2 (both criteria): skip behavior depends only on __unittest_skip__ marker,
# not on which API set it. Use @pytest.mark.skip (a DIFFERENT mechanism than
# @unittest.skip) on a unittest.TestCase run under --pdb. It must be skipped and
# setUp/tearDown left uncalled. This is the [@pytest.mark.skip] parametrization.
import os, sys, subprocess, tempfile, textwrap, re

d = tempfile.mkdtemp(prefix="probe4_")
smark = os.path.join(d, "setup_ran")
tmark = os.path.join(d, "teardown_ran")
test = os.path.join(d, "test_x.py")
open(test, "w").write(textwrap.dedent(f"""
    import pytest, unittest
    class T(unittest.TestCase):
        def setUp(self):
            open({smark!r}, "w").write("x")
        @pytest.mark.skip("skipping")
        def test_a(self):
            pass
        def tearDown(self):
            open({tmark!r}, "w").write("x")
"""))
r = subprocess.run([sys.executable, "-m", "pytest", "--pdb", "-p", "no:cacheprovider",
                    test], cwd=d, stdin=subprocess.DEVNULL,
                   capture_output=True, text=True, timeout=300)
out = r.stdout
print("rc", r.returncode)
print(out[-2000:])
setup_ran = os.path.exists(smark)
teardown_ran = os.path.exists(tmark)
last = [l for l in out.splitlines() if re.search(r"(passed|failed|error|skipped)\b", l)]
summary = last[-1] if last else ""
print("setup_ran:", setup_ran, "teardown_ran:", teardown_ran, "summary:", summary)
ok = (not setup_ran and not teardown_ran and "skipped" in summary
      and "error" not in summary and "failed" not in summary)
sys.exit(0 if ok else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
# Req 3.1 / 4.5: a NON-skipped unittest test under --pdb must still have its real
# tearDown invoked (postponed to the item teardown step, but ultimately called).
# The test fails so pdb is entered; we feed 'c' to continue. tearDown marker must
# appear. (Guards against a naive fix that suppresses tearDown for ALL cases.)
import os, sys, subprocess, tempfile, textwrap

d = tempfile.mkdtemp(prefix="probe5_")
tmark = os.path.join(d, "teardown_ran")
test = os.path.join(d, "test_x.py")
open(test, "w").write(textwrap.dedent(f"""
    import unittest
    class T(unittest.TestCase):
        def test_a(self):
            assert False, "boom"
        def tearDown(self):
            open({tmark!r}, "w").write("x")
"""))
r = subprocess.run([sys.executable, "-m", "pytest", "--pdb", "-p", "no:cacheprovider",
                    test], cwd=d, input="c\n",
                   capture_output=True, text=True, timeout=300)
print("rc", r.returncode)
print(r.stdout[-2000:])
teardown_ran = os.path.exists(tmark)
print("teardown_ran:", teardown_ran)
sys.exit(0 if teardown_ran else 1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
# Req 4.1: a @unittest.skip on the CLASS -> framework SHALL skip injecting its
# setup/teardown fixtures AND still report the class's tests as skipped. We run
# WITHOUT --pdb (the fixture-injection/reporting behavior 4.1 pins). setUp must
# not run (fixture not injected) and the test must be reported skipped.
import os, sys, subprocess, tempfile, textwrap, re

d = tempfile.mkdtemp(prefix="probe6_")
smark = os.path.join(d, "setup_ran")
tmark = os.path.join(d, "teardown_ran")
test = os.path.join(d, "test_x.py")
open(test, "w").write(textwrap.dedent(f"""
    import unittest
    @unittest.skip("class skip")
    class T(unittest.TestCase):
        def setUp(self):
            open({smark!r}, "w").write("x")
        def test_a(self):
            pass
        def tearDown(self):
            open({tmark!r}, "w").write("x")
"""))
r = subprocess.run([sys.executable, "-m", "pytest", "-p", "no:cacheprovider", test],
                   cwd=d, stdin=subprocess.DEVNULL,
                   capture_output=True, text=True, timeout=300)
out = r.stdout
print("rc", r.returncode)
print(out[-2000:])
setup_ran = os.path.exists(smark)
teardown_ran = os.path.exists(tmark)
last = [l for l in out.splitlines() if re.search(r"(passed|failed|error|skipped)\b", l)]
summary = last[-1] if last else ""
print("setup_ran:", setup_ran, "teardown_ran:", teardown_ran, "summary:", summary)
ok = (not setup_ran and not teardown_ran and "skipped" in summary
      and "error" not in summary and "failed" not in summary)
sys.exit(0 if ok else 1)
```

Attack 7 — `probe_7.py` → holds on the patched tree (good)

```python
# Req 4.2 / 4.3: a NON-skipped ordinary TestCase (and a runTest-only class) run
# WITHOUT --pdb must run setUp and tearDown normally, and be collected/run. This
# is the baseline regression guard.
import os, sys, subprocess, tempfile, textwrap, re

d = tempfile.mkdtemp(prefix="probe7_")
smark = os.path.join(d, "setup_ran")
tmark = os.path.join(d, "teardown_ran")
test = os.path.join(d, "test_x.py")
open(test, "w").write(textwrap.dedent(f"""
    import unittest
    class T(unittest.TestCase):
        def setUp(self):
            open({smark!r}, "w").write("x")
        def test_a(self):
            self.assertTrue(True)
        def tearDown(self):
            open({tmark!r}, "w").write("x")
    class R(unittest.TestCase):
        def runTest(self):
            self.assertTrue(True)
"""))
r = subprocess.run([sys.executable, "-m", "pytest", "-p", "no:cacheprovider", test],
                   cwd=d, stdin=subprocess.DEVNULL,
                   capture_output=True, text=True, timeout=300)
out = r.stdout
print("rc", r.returncode)
print(out[-2000:])
setup_ran = os.path.exists(smark)
teardown_ran = os.path.exists(tmark)
passed2 = bool(re.search(r"2 passed", out))
print("setup_ran:", setup_ran, "teardown_ran:", teardown_ran, "2 passed:", passed2)
ok = setup_ran and teardown_ran and passed2 and r.returncode == 0
sys.exit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
# Req 1.3 (POSITIVE CONTROL): a @unittest.skip TestCase run with --pdb must NOT
# have its tearDown invoked (neither immediately nor by a later explicit call).
# Patched: tearDown marker absent. Base: tearDown runs -> marker present -> FAIL.
import os, sys, subprocess, tempfile, textwrap

d = tempfile.mkdtemp(prefix="probe1_")
marker = os.path.join(d, "teardown_ran")
test = os.path.join(d, "test_x.py")
open(test, "w").write(textwrap.dedent(f"""
    import unittest
    class T(unittest.TestCase):
        @unittest.skip("skipping")
        def test_a(self):
            pass
        def tearDown(self):
            open({marker!r}, "w").write("x")
"""))
r = subprocess.run([sys.executable, "-m", "pytest", "--pdb", "-p", "no:cacheprovider",
                    test, "-q"], cwd=d, stdin=subprocess.DEVNULL,
                   capture_output=True, text=True, timeout=300)
print("rc", r.returncode)
print(r.stdout[-2000:])
print(r.stderr[-500:])
ran = os.path.exists(marker)
print("teardown_ran:", ran)
sys.exit(1 if ran else 0)
```

Prepatch bug re-encoded as an attack: `True`.

Environment: instance Docker image, py3.9.20, repo pytest 5.4.1 run via `python -m pytest` (no pytest installed as a fixture dep; probes are stdlib subprocess drivers). Patched-tree results: probe_1 teardown_ran=False (HOLD, Req1.3); probe_2 setup_ran=False (HOLD, Req1.2); probe_3 '1 skipped' rc0 no error (HOLD, Req1.1); probe_4 @pytest.mark.skip mechanism -> skipped, setUp/tearDown uncalled (HOLD, Req2.1/2.2 — the [@pytest.mark.skip] P2P parametrization); probe_5 non-skipped failing test under --pdb, real tearDown still invoked (HOLD, Req3.1/4.5); probe_6 class-level @unittest.skip w/o --pdb: fixtures not injected, reported skipped (HOLD, Req4.1); probe_7 non-skipped ordinary + runTest-only class w/o --pdb run setUp/tearDown, '2 passed' (HOLD, Req4.2/4.3).

Positive control probe_1 FAILS at base (teardown_ran=True under --pdb) and HOLDS patched => discriminates base vs patched (G-DIFF analog). Note during dev: an earlier probe_6 that ran the class-skip case *under --pdb* and expected teardown NOT to run failed on the patched tree — that was an OVER-STRONG probe, not a spec violation: with a class-level marker `_is_skipped(self.obj)` (bound method) is False, so gold correctly still arranges postponement and fires the explicit tearDown; Req 4.1 only pins fixture-injection/reporting, which probe_6 now tests without --pdb. Candidate floor met: 1 exercised, 1 rejected (weakA). No too-weak candidate found; the runtest-line guard is load-bearing and every probe-conforming fix must include it.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 7 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 7 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py`, `probe_7.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

Counterexample / evidence:

```
weakA applies the _is_skipped helper to collect() and the fixture (Req 4/5) but leaves the runtest postponement unconditional (`if self.config.getoption('usepdb')` without `and not _is_skipped(self.obj)`) — the exact original regression. Under --pdb a @unittest.skip test then has its stashed tearDown called during the item teardown step: probe_1 (Req 1.3) fails teardown_ran=True; probe_3 (Req 1.1) fails with '1 skipped, 1 error' because the booby-trapped tearDown fires. Suite rejects it.
```

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
# Req 1.3 (POSITIVE CONTROL): a @unittest.skip TestCase run with --pdb must NOT
# have its tearDown invoked (neither immediately nor by a later explicit call).
# Patched: tearDown marker absent. Base: tearDown runs -> marker present -> FAIL.
import os, sys, subprocess, tempfile, textwrap

d = tempfile.mkdtemp(prefix="probe1_")
marker = os.path.join(d, "teardown_ran")
test = os.path.join(d, "test_x.py")
open(test, "w").write(textwrap.dedent(f"""
    import unittest
    class T(unittest.TestCase):
        @unittest.skip("skipping")
        def test_a(self):
            pass
        def tearDown(self):
            open({marker!r}, "w").write("x")
"""))
r = subprocess.run([sys.executable, "-m", "pytest", "--pdb", "-p", "no:cacheprovider",
                    test, "-q"], cwd=d, stdin=subprocess.DEVNULL,
                   capture_output=True, text=True, timeout=300)
print("rc", r.returncode)
print(r.stdout[-2000:])
print(r.stderr[-500:])
ran = os.path.exists(marker)
print("teardown_ran:", ran)
sys.exit(1 if ran else 0)
```

Prepatch bug re-encoded as an attack: `True`.

Environment: instance Docker image, py3.9.20, repo pytest 5.4.1 run via `python -m pytest` (no pytest installed as a fixture dep; probes are stdlib subprocess drivers). Patched-tree results: probe_1 teardown_ran=False (HOLD, Req1.3); probe_2 setup_ran=False (HOLD, Req1.2); probe_3 '1 skipped' rc0 no error (HOLD, Req1.1); probe_4 @pytest.mark.skip mechanism -> skipped, setUp/tearDown uncalled (HOLD, Req2.1/2.2 — the [@pytest.mark.skip] P2P parametrization); probe_5 non-skipped failing test under --pdb, real tearDown still invoked (HOLD, Req3.1/4.5); probe_6 class-level @unittest.skip w/o --pdb: fixtures not injected, reported skipped (HOLD, Req4.1); probe_7 non-skipped ordinary + runTest-only class w/o --pdb run setUp/tearDown, '2 passed' (HOLD, Req4.2/4.3).

Positive control probe_1 FAILS at base (teardown_ran=True under --pdb) and HOLDS patched => discriminates base vs patched (G-DIFF analog). Note during dev: an earlier probe_6 that ran the class-skip case *under --pdb* and expected teardown NOT to run failed on the patched tree — that was an OVER-STRONG probe, not a spec violation: with a class-level marker `_is_skipped(self.obj)` (bound method) is False, so gold correctly still arranges postponement and fires the explicit tearDown; Req 4.1 only pins fixture-injection/reporting, which probe_6 now tests without --pdb. Candidate floor met: 1 exercised, 1 rejected (weakA). No too-weak candidate found; the runtest-line guard is load-bearing and every probe-conforming fix must include it.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Boundary is correct: requirements pin the teardown-postponement DECISION (usepdb AND not skipped) plus the collect/fixture skip checks — i.e. the full changed observable behavior, not a narrow slice. Requirement 5/2.2 correctly grounds the decision in the `__unittest_skip__` marker, which is exactly what `_is_skipped` reads. G-EQ already recorded 6 probes hold + weak-candidate rejected. Probed live in the instance image (patched exit=0, base shows error).


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The requirements describe only public/legitimate content. The bug (skipped unittest teardown/setUp running under --pdb) and the @unittest.skip decorator are all in the public problem_statement. Naming the mechanism (__unittest_skip__ marker, usepdb/--pdb, the stash-and-replace teardown postponement, UnitTestCase/TestCaseFunction in src/_pytest/unittest.py) is legitimate localization — these are the module/functions being changed. No hidden-test content is transmitted: the test name (test_pdb_teardown_skipped), test file path (testing/test_unittest.py), parametrization ids ([@unittest.skip]/[@pytest.mark.skip]), and the monkeypatch/tracked test scaffolding are absent. The fix-invented helper identifier _is_skipped is NOT mentioned; behavior is described functionally. Requirement 2's generalization ('irrespective of which decorator or marker API set that marker') is a behavioral property tied to the __unittest_skip__ marker presence, not an enumeration of the two parametrized cases (@pytest.mark.skip is never named). This is translating what the tests check into behavioral requirements, which is the intended purpose.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
