# P2 adversarial audit — pytest-dev__pytest-7432

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
"""Positive control / Req1.1: mark-skip + --runxfail -rs -> skip location points
at the test's own file, NOT inside src/_pytest/skipping.py.
Holds on patched, must FAIL on base."""
import subprocess, sys, os, tempfile, textwrap, re

TEST = textwrap.dedent('''
    import pytest
    @pytest.mark.skip(reason="unconditional skip")
    def test_skipmark():
        pass
''')

def run(tmpd):
    p = os.path.join(tmpd, "test_probe1.py")
    with open(p, "w") as f:
        f.write(TEST)
    r = subprocess.run(
        [sys.executable, "-m", "pytest", "-rs", "--runxfail", p],
        cwd=tmpd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    return r.stdout

with tempfile.TemporaryDirectory() as tmpd:
    out = run(tmpd)
print(out)
# find the SKIPPED summary line
lines = [l for l in out.splitlines() if l.strip().startswith("SKIPPED")]
print("SKIPPED lines:", lines)
if not lines:
    print("FAIL: no SKIPPED summary line found")
    sys.exit(1)
line = lines[0]
if "skipping.py" in line:
    print("FAIL: skip location points inside framework (skipping.py):", line)
    sys.exit(1)
if "test_probe1.py" not in line:
    print("FAIL: skip location does not point at the test's own file:", line)
    sys.exit(1)
print("OK: skip location points at test's own file under --runxfail")
sys.exit(0)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""Req2.1/2.2/2.3 & Req5.2: the corrected skip location and reason are IDENTICAL
with and without --runxfail (location = test's own file+line; reason preserved)."""
import subprocess, sys, os, tempfile, textwrap

TEST = textwrap.dedent('''
    import pytest
    @pytest.mark.skip(reason="my custom skip reason")
    def test_skipmark():
        pass
''')

def run(tmpd, runxfail):
    p = os.path.join(tmpd, "test_probe2.py")
    with open(p, "w") as f:
        f.write(TEST)
    args = [sys.executable, "-m", "pytest", "-rs", p]
    if runxfail:
        args.insert(3, "--runxfail")
    r = subprocess.run(args, cwd=tmpd, stdout=subprocess.PIPE,
                       stderr=subprocess.STDOUT, text=True)
    for l in r.stdout.splitlines():
        if l.strip().startswith("SKIPPED"):
            return l.strip()
    return None

with tempfile.TemporaryDirectory() as tmpd:
    without = run(tmpd, False)
    with_rx = run(tmpd, True)
print("without --runxfail:", without)
print("with    --runxfail:", with_rx)
if without is None or with_rx is None:
    print("FAIL: missing SKIPPED line")
    sys.exit(1)
if without != with_rx:
    print("FAIL: skip summary line differs between runs")
    sys.exit(1)
if "test_probe2.py" not in without or "skipping.py" in without:
    print("FAIL: location not pointing at test file")
    sys.exit(1)
if "my custom skip reason" not in without:
    print("FAIL: reason text not preserved")
    sys.exit(1)
print("OK: identical corrected location+reason regardless of --runxfail")
sys.exit(0)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""Req3.1 (kept behavior): WHILE --runxfail is enabled, xfail-marked tests run
normally and report their real pass/fail outcome instead of xfailed/xpassed.
A failing xfail test SHALL be reported as a real FAILURE (not xfailed)."""
import subprocess, sys, os, tempfile, textwrap

TEST = textwrap.dedent('''
    import pytest
    @pytest.mark.xfail(reason="expected to fail")
    def test_xfail_fails():
        assert False
    @pytest.mark.xfail(reason="expected to fail")
    def test_xfail_passes():
        assert True
''')

with tempfile.TemporaryDirectory() as tmpd:
    p = os.path.join(tmpd, "test_probe3.py")
    with open(p, "w") as f:
        f.write(TEST)
    r = subprocess.run(
        [sys.executable, "-m", "pytest", "-rxX", "--runxfail", "-v", p],
        cwd=tmpd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    out = r.stdout
print(out)
# Under --runxfail: the failing one must be a real FAILED, the passing one real PASSED.
# There must be NO xfailed/xpassed counts.
low = out.lower()
if "xfailed" in low or "xpassed" in low:
    print("FAIL: xfail conversion still happening under --runxfail")
    sys.exit(1)
if "1 failed" not in low or "1 passed" not in low:
    print("FAIL: expected 1 failed + 1 passed under --runxfail; got:", out.splitlines()[-1])
    sys.exit(1)
print("OK: --runxfail runs xfail tests normally (real pass/fail)")
sys.exit(0)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""Req4.1 & Req4.2 (kept behavior, WITHOUT --runxfail): xfail dispatch preserved.
- failing xfail -> xfailed
- passing xfail -> xpassed
- strict xfail that passes -> FAILED with strict message"""
import subprocess, sys, os, tempfile, textwrap

TEST = textwrap.dedent('''
    import pytest
    @pytest.mark.xfail(reason="boom")
    def test_xfail_fail():
        assert False
    @pytest.mark.xfail(reason="surprise")
    def test_xfail_pass():
        assert True
    @pytest.mark.xfail(reason="must fail", strict=True)
    def test_xfail_strict_pass():
        assert True
''')

with tempfile.TemporaryDirectory() as tmpd:
    p = os.path.join(tmpd, "test_probe4.py")
    with open(p, "w") as f:
        f.write(TEST)
    r = subprocess.run(
        [sys.executable, "-m", "pytest", "-rxX", p],
        cwd=tmpd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    out = r.stdout
print(out)
low = out.lower()
ok = True
if "1 xfailed" not in low:
    print("FAIL: expected 1 xfailed"); ok = False
if "1 xpassed" not in low:
    print("FAIL: expected 1 xpassed"); ok = False
if "1 failed" not in low:
    print("FAIL: expected 1 failed (strict xpass)"); ok = False
# strict message check
if "[XPASS(strict)]".lower() not in low and "must fail" not in low:
    print("FAIL: strict-xpass explanation missing"); ok = False
if not ok:
    sys.exit(1)
print("OK: xfail/xpass/strict-xpass dispatch preserved")
sys.exit(0)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""Req1 (skipif) + Req4.6: a skipif-skipped test under --runxfail reports its own
source location (skipif is a skip mark). Location -> test file, reason preserved."""
import subprocess, sys, os, tempfile, textwrap

TEST = textwrap.dedent('''
    import pytest
    @pytest.mark.skipif(True, reason="cond skip reason")
    def test_skipif():
        pass
''')

with tempfile.TemporaryDirectory() as tmpd:
    p = os.path.join(tmpd, "test_probe5.py")
    with open(p, "w") as f:
        f.write(TEST)
    r = subprocess.run(
        [sys.executable, "-m", "pytest", "-rs", "--runxfail", p],
        cwd=tmpd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    out = r.stdout
print(out)
lines = [l.strip() for l in out.splitlines() if l.strip().startswith("SKIPPED")]
print("SKIPPED:", lines)
if not lines:
    print("FAIL: no SKIPPED line")
    sys.exit(1)
line = lines[0]
if "skipping.py" in line:
    print("FAIL: skipif location points inside framework")
    sys.exit(1)
if "test_probe5.py" not in line:
    print("FAIL: skipif location not at test file")
    sys.exit(1)
if "cond skip reason" not in line:
    print("FAIL: skipif reason not preserved")
    sys.exit(1)
print("OK: skipif under --runxfail reports own location + reason")
sys.exit(0)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
"""Req1.4 / Req4.6 (guard clause): a test skipped IMPERATIVELY (pytest.skip()
inside the test body, NOT by a skip mark) must NOT have its location rewritten to
the test's own def line. Because skipped_by_mark_key is False, the location
correction SHALL be left unchanged (it should reflect the pytest.skip() call site
inside the test body, i.e. the line where skip() was called, not the def line)."""
import subprocess, sys, os, tempfile, textwrap

# test def is on line 3, the pytest.skip() call is on line 5.
TEST = textwrap.dedent('''\
import pytest

def test_imperative_skip():
    x = 1
    pytest.skip("imperative reason")
''')

def run(runxfail):
    with tempfile.TemporaryDirectory() as tmpd:
        p = os.path.join(tmpd, "test_probe6.py")
        with open(p, "w") as f:
            f.write(TEST)
        args = [sys.executable, "-m", "pytest", "-rs", p]
        if runxfail:
            args.insert(3, "--runxfail")
        r = subprocess.run(args, cwd=tmpd, stdout=subprocess.PIPE,
                           stderr=subprocess.STDOUT, text=True)
        for l in r.stdout.splitlines():
            if l.strip().startswith("SKIPPED"):
                return l.strip(), r.stdout
        return None, r.stdout

line_no, out_no = run(False)
line_rx, out_rx = run(True)
print("without runxfail:", line_no)
print("with    runxfail:", line_rx)
if line_no is None or line_rx is None:
    print("FAIL: missing SKIPPED line"); print(out_no); sys.exit(1)
# imperative skip is not mark-skip: location must NOT be rewritten to def line (line 3).
# It should point at the skip() call site (line 5) in the test file.
if not line_no.endswith(":5: imperative reason") and ":5:" not in line_no:
    print("FAIL: imperative-skip location was rewritten (expected call-site line 5):", line_no)
    sys.exit(1)
# and it must be identical with/without runxfail (guard clause independent of runxfail)
if line_no != line_rx:
    print("FAIL: imperative-skip location changed under --runxfail:", line_no, "vs", line_rx)
    sys.exit(1)
print("OK: imperative (non-mark) skip location left unchanged (guard clause holds)")
sys.exit(0)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Positive control / Req1.1: mark-skip + --runxfail -rs -> skip location points
at the test's own file, NOT inside src/_pytest/skipping.py.
Holds on patched, must FAIL on base."""
import subprocess, sys, os, tempfile, textwrap, re

TEST = textwrap.dedent('''
    import pytest
    @pytest.mark.skip(reason="unconditional skip")
    def test_skipmark():
        pass
''')

def run(tmpd):
    p = os.path.join(tmpd, "test_probe1.py")
    with open(p, "w") as f:
        f.write(TEST)
    r = subprocess.run(
        [sys.executable, "-m", "pytest", "-rs", "--runxfail", p],
        cwd=tmpd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    return r.stdout

with tempfile.TemporaryDirectory() as tmpd:
    out = run(tmpd)
print(out)
# find the SKIPPED summary line
lines = [l for l in out.splitlines() if l.strip().startswith("SKIPPED")]
print("SKIPPED lines:", lines)
if not lines:
    print("FAIL: no SKIPPED summary line found")
    sys.exit(1)
line = lines[0]
if "skipping.py" in line:
    print("FAIL: skip location points inside framework (skipping.py):", line)
    sys.exit(1)
if "test_probe1.py" not in line:
    print("FAIL: skip location does not point at the test's own file:", line)
    sys.exit(1)
print("OK: skip location points at test's own file under --runxfail")
sys.exit(0)
```

Prepatch bug re-encoded as an attack: `True`.

Instance pytest-dev__pytest-7432: gold fix in src/_pytest/skipping.py:pytest_runtest_makereport decouples the skip-location correction from the xfail dispatch chain (changes the final `elif` to an independent `if`), so --runxfail no longer suppresses skip-location correction.

Probe suite (all standalone python, drive pytest via subprocess inside the instance image; each exits 0 iff its criterion holds):
- probe_1 (Req1.1, POSITIVE CONTROL): @pytest.mark.skip + --runxfail -rs => SKIPPED summary points at test's own file (test_probe1.py:3), NOT src/_pytest/skipping.py. PATCHED: HOLDS. BASE: VIOLATED (reports ../../testbed/src/_pytest/skipping.py:239). Discriminates.
- probe_2 (Req2.1/2.2/2.3, Req5.2): corrected skip location+reason IDENTICAL with vs without --runxfail; reason text preserved. PATCHED: HOLDS.
- probe_3 (Req3.1 kept): under --runxfail, xfail tests run normally -> real 1 failed + 1 passed, no xfailed/xpassed. PATCHED: HOLDS.
- probe_4 (Req4.1/4.2 kept, no --runxfail): failing xfail->xfailed, passing xfail->xpassed, strict xpass->FAILED with XPASS(strict). PATCHED: HOLDS.
- probe_5 (Req1 skipif + Req4.6 kept): skipif-skipped test under --runxfail reports own location + reason. PATCHED: HOLDS.
- probe_6 (Req1.4/guard clause): IMPERATIVE pytest.skip() (skipped_by_mark_key False) must NOT be rewritten to def line -> location stays at call site (line 5), identical with/without --runxfail. PATCHED: HOLDS.

All 6 hold on patched tree; positive control fails at base (prepatch reproduced).

Candidate wrong-fix patches (both apply at base_commit, both REJECTED by the suite -> discriminating power confirmed):
- weak_A (weak_A.diff): decouples the branch but REPLACES the `skipped_by_mark_key` guard with `True`, so it over-rewrites imperative skips. Probes 1-5 HOLD but probe_6 VIOLATED (imperative skip location wrongly rewritten). Rejected.
- weak_B (weak_B.diff): the lazy non-fix — leaves the correction chained as `elif` (only adds a comment). Probes 1, 2, 5 VIOLATED (skip location still corrupted under --runxfail). Rejected.

No probe-conforming alternative patch found: every wrong reading of the requirements is caught. Verdict SOUND.

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
"""Positive control / Req1.1: mark-skip + --runxfail -rs -> skip location points
at the test's own file, NOT inside src/_pytest/skipping.py.
Holds on patched, must FAIL on base."""
import subprocess, sys, os, tempfile, textwrap, re

TEST = textwrap.dedent('''
    import pytest
    @pytest.mark.skip(reason="unconditional skip")
    def test_skipmark():
        pass
''')

def run(tmpd):
    p = os.path.join(tmpd, "test_probe1.py")
    with open(p, "w") as f:
        f.write(TEST)
    r = subprocess.run(
        [sys.executable, "-m", "pytest", "-rs", "--runxfail", p],
        cwd=tmpd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    return r.stdout

with tempfile.TemporaryDirectory() as tmpd:
    out = run(tmpd)
print(out)
# find the SKIPPED summary line
lines = [l for l in out.splitlines() if l.strip().startswith("SKIPPED")]
print("SKIPPED lines:", lines)
if not lines:
    print("FAIL: no SKIPPED summary line found")
    sys.exit(1)
line = lines[0]
if "skipping.py" in line:
    print("FAIL: skip location points inside framework (skipping.py):", line)
    sys.exit(1)
if "test_probe1.py" not in line:
    print("FAIL: skip location does not point at the test's own file:", line)
    sys.exit(1)
print("OK: skip location points at test's own file under --runxfail")
sys.exit(0)
```

Prepatch bug re-encoded as an attack: `True`.

Instance pytest-dev__pytest-7432: gold fix in src/_pytest/skipping.py:pytest_runtest_makereport decouples the skip-location correction from the xfail dispatch chain (changes the final `elif` to an independent `if`), so --runxfail no longer suppresses skip-location correction.

Probe suite (all standalone python, drive pytest via subprocess inside the instance image; each exits 0 iff its criterion holds):
- probe_1 (Req1.1, POSITIVE CONTROL): @pytest.mark.skip + --runxfail -rs => SKIPPED summary points at test's own file (test_probe1.py:3), NOT src/_pytest/skipping.py. PATCHED: HOLDS. BASE: VIOLATED (reports ../../testbed/src/_pytest/skipping.py:239). Discriminates.
- probe_2 (Req2.1/2.2/2.3, Req5.2): corrected skip location+reason IDENTICAL with vs without --runxfail; reason text preserved. PATCHED: HOLDS.
- probe_3 (Req3.1 kept): under --runxfail, xfail tests run normally -> real 1 failed + 1 passed, no xfailed/xpassed. PATCHED: HOLDS.
- probe_4 (Req4.1/4.2 kept, no --runxfail): failing xfail->xfailed, passing xfail->xpassed, strict xpass->FAILED with XPASS(strict). PATCHED: HOLDS.
- probe_5 (Req1 skipif + Req4.6 kept): skipif-skipped test under --runxfail reports own location + reason. PATCHED: HOLDS.
- probe_6 (Req1.4/guard clause): IMPERATIVE pytest.skip() (skipped_by_mark_key False) must NOT be rewritten to def line -> location stays at call site (line 5), identical with/without --runxfail. PATCHED: HOLDS.

All 6 hold on patched tree; positive control fails at base (prepatch reproduced).

Candidate wrong-fix patches (both apply at base_commit, both REJECTED by the suite -> discriminating power confirmed):
- weak_A (weak_A.diff): decouples the branch but REPLACES the `skipped_by_mark_key` guard with `True`, so it over-rewrites imperative skips. Probes 1-5 HOLD but probe_6 VIOLATED (imperative skip location wrongly rewritten). Rejected.
- weak_B (weak_B.diff): the lazy non-fix — leaves the correction chained as `elif` (only adds a comment). Probes 1, 2, 5 VIOLATED (skip location still corrupted under --runxfail). Rejected.

No probe-conforming alternative patch found: every wrong reading of the requirements is caught. Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Verified via nl_attack probe on the instance image: hook source shows `_, _, reason = rep.longrepr; filename, line = item.reportinfo()[:2]; rep.longrepr = str(filename), line + 1, reason` guarded by the standalone `if`, and both runxfail/no-runxfail runs produce `test_it.py:2`. Boundary is correct: requirements pin the changed observable behavior (skip-location correction fires regardless of dispatch branch), not a narrow slice. Reqs 3/4/5 accurately mark the preserved (unchanged) surrounding behavior.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The requirements describe the bug, its location, and the fix entirely from content already public in problem_statement plus the module's own source structure. problem_statement already discloses: the module/hook (src/_pytest/skipping.py, pytest_runtest_makereport), the --runxfail/-rs flags, the failing SKIPPED-vs-internal-path symptom, and the exact reproducer (@pytest.mark.skip test, 'unconditional skip'). The doc's mention of the branch chain (unexpected-success, --runxfail, raised-xfail, xfail-mark) and the elif→independent-if decoupling is a behavioral description of the gold edit and the surrounding hook code — legitimate localization, not transmission of the test. The 'structured triple (file, line, reason)' phrasing paraphrases the code guard (type(rep.longrepr) is tuple / skipped_by_mark_key), not test text. No hidden-test artifacts leak: no test file path (test_sample.py), no test/class name (test_xfail_run_with_skip_mark / TestXFail), no parametrization ids (test_input1-expected1), no quoted test/gold code, no fix-invented identifiers. Requirement 4's outcome enumeration mirrors the hook's existing dispatch branches (source-derived), not the FAIL_TO_PASS/PASS_TO_PASS list. No gold-reconstruction beyond the public statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
