# P2 adversarial audit — pytest-dev__pytest-10081

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 requirement probes hold on the patched tree; 2/2 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 7 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 7 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py`, `probe_7.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 2 alternative candidate patches, claimed to satisfy every cited requirement, and ran the same suite against them. The suite rejected all 2: a probe encoding a cited requirement fails under each of those, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (7):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
# Req1 (positive control): class-level @unittest.skip under --pdb -> no setUp/tearDown, reports skipped.
import subprocess, sys, tempfile, os, textwrap
d = tempfile.mkdtemp()
marker = os.path.join(d, "marker.txt")
test = textwrap.dedent(f'''
    import unittest, pytest
    LOG = {marker!r}
    def _rec(s):
        with open(LOG, "a") as f: f.write(s + "\\n")

    @unittest.skip("skipped for reasons")
    class MyTestCase(unittest.TestCase):
        def setUp(self): _rec("setUp:" + self.id())
        def tearDown(self): _rec("tearDown:" + self.id())
        def test_1(self): pass
''')
tf = os.path.join(d, "test_probe.py")
open(tf, "w").write(test)
env = dict(os.environ); env["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"
p = subprocess.run([sys.executable, "-m", "pytest", "-p", "no:cacheprovider",
                    "--pdb", tf, "-s"],
                   cwd=d, capture_output=True, text=True, timeout=300,
                   stdin=subprocess.DEVNULL)
out = p.stdout + p.stderr
tracked = ""
if os.path.exists(marker):
    tracked = open(marker).read()
print("=== stdout tail ===")
print(out[-1500:])
print("=== tracked setUp/tearDown ===")
print(repr(tracked))
ok_no_teardown = (tracked.strip() == "")
ok_skipped = ("1 skipped" in out)
ok_no_pdb = ("Pdb" not in out and "(Pdb)" not in out and "entering PDB" not in out)
print("no_setup_teardown:", ok_no_teardown, "reported_skipped:", ok_skipped, "no_pdb:", ok_no_pdb)
sys.exit(0 if (ok_no_teardown and ok_skipped and ok_no_pdb) else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
import subprocess, sys, tempfile, os, textwrap
d = tempfile.mkdtemp(); marker = os.path.join(d, "m.txt")
test = textwrap.dedent(f'''
    import unittest, pytest
    LOG = {marker!r}
    def _rec(s):
        with open(LOG, "a") as f: f.write(s + "\\n")
    @pytest.mark.skip("skipped for reasons")
    class MyTestCase(unittest.TestCase):
        def setUp(self): _rec("setUp:" + self.id())
        def tearDown(self): _rec("tearDown:" + self.id())
        def test_1(self): pass
''')
tf = os.path.join(d, "test_probe.py"); open(tf,"w").write(test)
p = subprocess.run([sys.executable,"-m","pytest","-p","no:cacheprovider","--pdb",tf,"-s"],
    cwd=d, capture_output=True, text=True, timeout=300, stdin=subprocess.DEVNULL)
out=p.stdout+p.stderr
tracked = open(marker).read() if os.path.exists(marker) else ""
print(out[-1200:]); print("tracked:",repr(tracked))
ok = (tracked.strip()=="") and ("1 skipped" in out)
print("PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
import subprocess, sys, tempfile, os, textwrap
d = tempfile.mkdtemp(); marker = os.path.join(d, "m.txt")
test = textwrap.dedent(f'''
    import unittest, pytest
    LOG = {marker!r}
    def _rec(s):
        with open(LOG, "a") as f: f.write(s + "\\n")
    class MyTestCase(unittest.TestCase):
        def setUp(self): _rec("setUp:" + self.id())
        def tearDown(self): _rec("tearDown:" + self.id())
        @unittest.skip("skipped for reasons")
        def test_1(self): pass
''')
tf = os.path.join(d, "test_probe.py"); open(tf,"w").write(test)
p = subprocess.run([sys.executable,"-m","pytest","-p","no:cacheprovider","--pdb",tf,"-s"],
    cwd=d, capture_output=True, text=True, timeout=300, stdin=subprocess.DEVNULL)
out=p.stdout+p.stderr
tracked = open(marker).read() if os.path.exists(marker) else ""
print(out[-1200:]); print("tracked:",repr(tracked))
ok = (tracked.strip()=="") and ("1 skipped" in out)
print("PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
import subprocess, sys, tempfile, os, textwrap
d = tempfile.mkdtemp(); marker = os.path.join(d, "m.txt")
test = textwrap.dedent(f'''
    import unittest, pytest
    LOG = {marker!r}
    def _rec(s):
        with open(LOG, "a") as f: f.write(s + "\\n")
    class MyTestCase(unittest.TestCase):
        def setUp(self): _rec("setUp:" + self.id())
        def tearDown(self): _rec("tearDown:" + self.id())
        @pytest.mark.skip("skipped for reasons")
        def test_1(self): pass
''')
tf = os.path.join(d, "test_probe.py"); open(tf,"w").write(test)
p = subprocess.run([sys.executable,"-m","pytest","-p","no:cacheprovider","--pdb",tf,"-s"],
    cwd=d, capture_output=True, text=True, timeout=300, stdin=subprocess.DEVNULL)
out=p.stdout+p.stderr
tracked = open(marker).read() if os.path.exists(marker) else ""
print(out[-1200:]); print("tracked:",repr(tracked))
ok = (tracked.strip()=="") and ("1 skipped" in out)
print("PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
import subprocess, sys, tempfile, os, textwrap
d = tempfile.mkdtemp(); marker = os.path.join(d, "m.txt")
test = textwrap.dedent(f'''
    import unittest, pytest
    LOG = {marker!r}
    def _rec(s):
        with open(LOG, "a") as f: f.write(s + "\\n")
    class MyTestCase(unittest.TestCase):
        def setUp(self): _rec("setUp:" + self.id())
        def tearDown(self): _rec("tearDown:" + self.id())
        def test_1(self): pass
''')
tf = os.path.join(d, "test_probe.py"); open(tf,"w").write(test)
p = subprocess.run([sys.executable,"-m","pytest","-p","no:cacheprovider","--pdb",tf,"-s"],
    cwd=d, capture_output=True, text=True, timeout=300, stdin=subprocess.DEVNULL)
out=p.stdout+p.stderr
tracked = open(marker).read() if os.path.exists(marker) else ""
print(out[-1000:]); print("tracked:",repr(tracked))
ok = ("setUp:" in tracked) and ("tearDown:" in tracked) and ("1 passed" in out)
print("PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
import subprocess, sys, tempfile, os, textwrap
def run(decorator, cls_line):
    d = tempfile.mkdtemp(); marker = os.path.join(d, "m.txt")
    test = textwrap.dedent(f'''
        import unittest, pytest
        LOG = {marker!r}
        def _rec(s):
            with open(LOG, "a") as f: f.write(s + "\\n")
        {decorator}
        class MyTestCase(unittest.TestCase):
            def setUp(self): _rec("setUp:" + self.id())
            def tearDown(self): _rec("tearDown:" + self.id())
            def test_1(self): pass
    ''')
    tf = os.path.join(d, "test_probe.py"); open(tf,"w").write(test)
    p = subprocess.run([sys.executable,"-m","pytest","-p","no:cacheprovider",tf,"-s"],
        cwd=d, capture_output=True, text=True, timeout=300, stdin=subprocess.DEVNULL)
    out=p.stdout+p.stderr
    tracked = open(marker).read() if os.path.exists(marker) else ""
    return out, tracked
# non-skipped: both run, passed
out1,t1 = run("", None)
ok1 = ("setUp:" in t1) and ("tearDown:" in t1) and ("1 passed" in out1)
# class-skipped normal run: none run, reported skipped
out2,t2 = run('@unittest.skip("r")', None)
ok2 = (t2.strip()=="") and ("1 skipped" in out2)
print("non_skipped tracked:",repr(t1),"->",ok1)
print("skipped tracked:",repr(t2),"->",ok2)
print("PASS" if (ok1 and ok2) else "FAIL")
sys.exit(0 if (ok1 and ok2) else 1)
```

Attack 7 — `probe_7.py` → holds on the patched tree (good)

```python
# Req3.1: for a NON-skipped FAILING test under --pdb, tearDown must be POSTPONED so that
# instance state is still available at the debugger prompt. We drive pdb via stdin: at the
# prompt we print an instance attribute that tearDown would delete, then continue.
# gold: attr still present (tearDown postponed). never-postpone: attr already gone.
import subprocess, sys, tempfile, os, textwrap
d = tempfile.mkdtemp()
test = textwrap.dedent('''
    import unittest
    class MyTestCase(unittest.TestCase):
        def setUp(self):
            self.state = "ALIVE"
        def tearDown(self):
            # if tearDown ran before the debugger, state is wiped
            self.state = "WIPED"
        def test_1(self):
            assert False, "boom"
''')
tf = os.path.join(d, "test_probe.py"); open(tf,"w").write(test)
# At the pdb prompt, inspect the testcase instance's state via the frame locals: `self.state`.
pdb_cmds = "p self.state\nc\n"
p = subprocess.run([sys.executable,"-m","pytest","-p","no:cacheprovider","--pdb",tf,"-s"],
    cwd=d, capture_output=True, text=True, timeout=300, input=pdb_cmds)
out = p.stdout + p.stderr
print("=== output tail ===")
print(out[-2000:])
saw_alive = "ALIVE" in out
saw_wiped_at_prompt = False
# crude: the 'p self.state' echo should show 'ALIVE' if postponed
ok = saw_alive
print("state ALIVE visible at pdb prompt (postponed):", saw_alive)
sys.exit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
# Req1 (positive control): class-level @unittest.skip under --pdb -> no setUp/tearDown, reports skipped.
import subprocess, sys, tempfile, os, textwrap
d = tempfile.mkdtemp()
marker = os.path.join(d, "marker.txt")
test = textwrap.dedent(f'''
    import unittest, pytest
    LOG = {marker!r}
    def _rec(s):
        with open(LOG, "a") as f: f.write(s + "\\n")

    @unittest.skip("skipped for reasons")
    class MyTestCase(unittest.TestCase):
        def setUp(self): _rec("setUp:" + self.id())
        def tearDown(self): _rec("tearDown:" + self.id())
        def test_1(self): pass
''')
tf = os.path.join(d, "test_probe.py")
open(tf, "w").write(test)
env = dict(os.environ); env["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"
p = subprocess.run([sys.executable, "-m", "pytest", "-p", "no:cacheprovider",
                    "--pdb", tf, "-s"],
                   cwd=d, capture_output=True, text=True, timeout=300,
                   stdin=subprocess.DEVNULL)
out = p.stdout + p.stderr
tracked = ""
if os.path.exists(marker):
    tracked = open(marker).read()
print("=== stdout tail ===")
print(out[-1500:])
print("=== tracked setUp/tearDown ===")
print(repr(tracked))
ok_no_teardown = (tracked.strip() == "")
ok_skipped = ("1 skipped" in out)
ok_no_pdb = ("Pdb" not in out and "(Pdb)" not in out and "entering PDB" not in out)
print("no_setup_teardown:", ok_no_teardown, "reported_skipped:", ok_skipped, "no_pdb:", ok_no_pdb)
sys.exit(0 if (ok_no_teardown and ok_skipped and ok_no_pdb) else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance pytest-dev__pytest-10081: gold makes --pdb teardown-postponement consider the enclosing TestCase class's skip marker (skipped = _is_skipped(self.obj) or _is_skipped(self.parent.obj)). All probes run the real pytest SUT as a subprocess on generated unittest files (stdlib only, no pytest-as-lib) and observe setUp/tearDown execution via a file marker.

Probe coverage (all HOLD on gold-patched tree):
- probe_1 (POSITIVE CONTROL, Req1.1/1.2/1.3/1.4): class-level @unittest.skip under --pdb -> no setUp/tearDown recorded, reported '1 skipped', no PDB prompt. HOLDS patched; FAILS at base (base records 'tearDown:...MyTestCase.test_1' — the exact defect). prepatch_reproduced=true.
- probe_2 (Req1.5): class-level @pytest.mark.skip under --pdb -> no setUp/tearDown, skipped. HOLDS patched; rejects weak1's positive-control equivalent path is exercised by probe_1.
- probe_3 (Req2.1): method-level @unittest.skip under --pdb -> no setUp/tearDown, skipped (regression).
- probe_4 (Req2.2): method-level @pytest.mark.skip under --pdb -> no setUp/tearDown, skipped (regression).
- probe_5 (Req3.1/3.2): non-skipped test under --pdb -> setUp AND tearDown both run, 1 passed (regression: teardown must ultimately execute).
- probe_6 (Req4.1/Req3.2): normal run (no --pdb): non-skipped runs both setUp+tearDown & passes; class @unittest.skip runs neither & reports skipped.
- probe_7 (Req3.1 POSTPONEMENT): non-skipped FAILING test under --pdb — drives the pdb prompt via stdin and inspects self.state. tearDown wipes state, so 'ALIVE' at the prompt proves tearDown was POSTPONED (deferred past the debugger), not run before it. HOLDS patched and base; needed to encode the 'postponed so instance state remains available' clause that probe_5 alone does not.

Candidate patches (both apply cleanly at base_commit; both REJECTED by the suite):
- weak1 (partial/naive fix): adds the parent assert + comment but keeps skipped = _is_skipped(self.obj) only (ignores class). REJECTED by probe_1 (VIOLATED: class-skip teardown still runs). This is exactly the lazy 'method-only' reading of the requirements — the suite catches it via the positive control.
- weak2 (over-broad fix): sets skipped=True unconditionally, so tearDown is never postponed. Passes probes 1-6 (all skip/report criteria satisfied and non-skipped tearDown still eventually runs) but is REJECTED by probe_7 (VIOLATED: state 'WIPED' at pdb prompt — teardown ran before the debugger, violating Req3.1's postponement mandate). Without probe_7 this over-broad fix would have been a spurious TOO-WEAK finding; adding the postponement probe closes the gap and confirms the requirement set discriminates it.

No requirements-conforming candidate survives the suite. >=5 distinct probes (7) all HOLD on the patched tree; the positive control discriminates (HOLDS patched, FAILS at base); >=1 candidate exercised and >=1 REJECTED (both rejected). SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 requirement probes hold on the patched tree; 2/2 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 7 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 7 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py`, `probe_7.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 2 alternative candidate patches, claimed to satisfy every cited requirement, and ran the same suite against them. The suite rejected all 2: a probe encoding a cited requirement fails under each of those, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

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
# Req1 (positive control): class-level @unittest.skip under --pdb -> no setUp/tearDown, reports skipped.
import subprocess, sys, tempfile, os, textwrap
d = tempfile.mkdtemp()
marker = os.path.join(d, "marker.txt")
test = textwrap.dedent(f'''
    import unittest, pytest
    LOG = {marker!r}
    def _rec(s):
        with open(LOG, "a") as f: f.write(s + "\\n")

    @unittest.skip("skipped for reasons")
    class MyTestCase(unittest.TestCase):
        def setUp(self): _rec("setUp:" + self.id())
        def tearDown(self): _rec("tearDown:" + self.id())
        def test_1(self): pass
''')
tf = os.path.join(d, "test_probe.py")
open(tf, "w").write(test)
env = dict(os.environ); env["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"
p = subprocess.run([sys.executable, "-m", "pytest", "-p", "no:cacheprovider",
                    "--pdb", tf, "-s"],
                   cwd=d, capture_output=True, text=True, timeout=300,
                   stdin=subprocess.DEVNULL)
out = p.stdout + p.stderr
tracked = ""
if os.path.exists(marker):
    tracked = open(marker).read()
print("=== stdout tail ===")
print(out[-1500:])
print("=== tracked setUp/tearDown ===")
print(repr(tracked))
ok_no_teardown = (tracked.strip() == "")
ok_skipped = ("1 skipped" in out)
ok_no_pdb = ("Pdb" not in out and "(Pdb)" not in out and "entering PDB" not in out)
print("no_setup_teardown:", ok_no_teardown, "reported_skipped:", ok_skipped, "no_pdb:", ok_no_pdb)
sys.exit(0 if (ok_no_teardown and ok_skipped and ok_no_pdb) else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance pytest-dev__pytest-10081: gold makes --pdb teardown-postponement consider the enclosing TestCase class's skip marker (skipped = _is_skipped(self.obj) or _is_skipped(self.parent.obj)). All probes run the real pytest SUT as a subprocess on generated unittest files (stdlib only, no pytest-as-lib) and observe setUp/tearDown execution via a file marker.

Probe coverage (all HOLD on gold-patched tree):
- probe_1 (POSITIVE CONTROL, Req1.1/1.2/1.3/1.4): class-level @unittest.skip under --pdb -> no setUp/tearDown recorded, reported '1 skipped', no PDB prompt. HOLDS patched; FAILS at base (base records 'tearDown:...MyTestCase.test_1' — the exact defect). prepatch_reproduced=true.
- probe_2 (Req1.5): class-level @pytest.mark.skip under --pdb -> no setUp/tearDown, skipped. HOLDS patched; rejects weak1's positive-control equivalent path is exercised by probe_1.
- probe_3 (Req2.1): method-level @unittest.skip under --pdb -> no setUp/tearDown, skipped (regression).
- probe_4 (Req2.2): method-level @pytest.mark.skip under --pdb -> no setUp/tearDown, skipped (regression).
- probe_5 (Req3.1/3.2): non-skipped test under --pdb -> setUp AND tearDown both run, 1 passed (regression: teardown must ultimately execute).
- probe_6 (Req4.1/Req3.2): normal run (no --pdb): non-skipped runs both setUp+tearDown & passes; class @unittest.skip runs neither & reports skipped.
- probe_7 (Req3.1 POSTPONEMENT): non-skipped FAILING test under --pdb — drives the pdb prompt via stdin and inspects self.state. tearDown wipes state, so 'ALIVE' at the prompt proves tearDown was POSTPONED (deferred past the debugger), not run before it. HOLDS patched and base; needed to encode the 'postponed so instance state remains available' clause that probe_5 alone does not.

Candidate patches (both apply cleanly at base_commit; both REJECTED by the suite):
- weak1 (partial/naive fix): adds the parent assert + comment but keeps skipped = _is_skipped(self.obj) only (ignores class). REJECTED by probe_1 (VIOLATED: class-skip teardown still runs). This is exactly the lazy 'method-only' reading of the requirements — the suite catches it via the positive control.
- weak2 (over-broad fix): sets skipped=True unconditionally, so tearDown is never postponed. Passes probes 1-6 (all skip/report criteria satisfied and non-skipped tearDown still eventually runs) but is REJECTED by probe_7 (VIOLATED: state 'WIPED' at pdb prompt — teardown ran before the debugger, violating Req3.1's postponement mandate). Without probe_7 this over-broad fix would have been a spurious TOO-WEAK finding; adding the postponement probe closes the gap and confirms the requirement set discriminates it.

No requirements-conforming candidate survives the suite. >=5 distinct probes (7) all HOLD on the patched tree; the positive control discriminates (HOLDS patched, FAILS at base); >=1 candidate exercised and >=1 REJECTED (both rejected). SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Patch verified in image at src/_pytest/unittest.py:342. _is_skipped checks __unittest_skip__ (line 390-392); pytest.mark.skip on a unittest class also sets __unittest_skip__, so Req1.5/2.2's 'regardless of unittest vs pytest marker' claim is accurate (probe confirms both). Requirements correctly avoid over-narrow boundaries: they pin the postponement branch AND the end-to-end observable outcomes (skip reporting, no pdb, teardown ultimately runs for non-skipped). No invented behavior; no forbidden behavior the code exhibits. G-DIFF-equivalent confirmed: base fails class-skip+pdb, gold passes all.

Counterexample / evidence:

```
No counterexample: probe.py results on gold-patched tree — @unittest.skip class + --pdb: skipped=True, trace='' (Req1.1/1.2/1.3); @pytest.mark.skip class + --pdb: skipped=True, trace='' (Req1.5); method-level @unittest.skip and @pytest.mark.skip + --pdb: skipped=True, trace='' (Req2.1/2.2); non-skipped + --pdb: passed, trace='setUp\ntearDown' i.e. tearDown ultimately runs (Req3.1); non-skipped without --pdb: trace='setUp\ntearDown' (Req3.2); skipped without --pdb: skipped=True, trace='' (Req4.1). Base tree violates only the class-skip+pdb case, confirming the modeled boundary is the changed behavior.
```


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The requirements describe behavior fully derivable from the public problem_statement (class-level unittest.skip + --pdb wrongly runs setUp/tearDown and triggers post-mortem; method-level was already fixed per #7215). Naming src/_pytest/unittest.py, the TestCaseFunction.runtest path, and the pre-existing _is_skipped helper / __unittest_skip__ attribute is legitimate localization of the change, not test/gold transmission. No hidden-test artifacts are leaked: no test file path (testing/test_unittest.py), no test function names (test_pdb_teardown_skipped_for_classes/_for_functions), no parametrization ids, no tracked/track_pdb_teardown_skipped monkeypatch mechanism, no '* 1 skipped in *' assertion, no issue #10060. The gold patch's invented local (`skipped`) and the `assert isinstance(self.parent, UnitTestCase)` line are not surfaced. Borderline: Req 1.5/2.2 note behavior holds for both the unittest skip decorator and pytest's own skip marker, which parallels the test parametrize [@unittest.skip, @pytest.mark.skip] — but this is a behavioral generalization, not an enumeration of test ids/code, and constitutes the legitimate translation of test intent into requirements rather than reconstruction of the tests.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
