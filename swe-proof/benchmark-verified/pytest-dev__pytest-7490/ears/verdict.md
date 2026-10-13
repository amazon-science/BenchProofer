# P2 adversarial audit — pytest-dev__pytest-7490

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
import os, sys, tempfile, textwrap, itertools
import pytest

_counter = itertools.count()

class _Collector:
    def __init__(self):
        self.reports = []
    def pytest_runtest_logreport(self, report):
        self.reports.append(report)

def run_pytest(test_src, extra_args=None):
    """Write test_src to an isolated tmp dir with a UNIQUE module name, run
    pytest.main in a fresh dir, return (tally, xfail_reasons)."""
    d = tempfile.mkdtemp(prefix="probe_run_")
    modname = "test_probe_%d.py" % next(_counter)
    tf = os.path.join(d, modname)
    with open(tf, "w") as f:
        f.write(textwrap.dedent(test_src))
    col = _Collector()
    args = [tf, "-p", "no:cacheprovider"]
    if extra_args:
        args += extra_args
    old = os.getcwd()
    os.chdir(d)
    try:
        pytest.main(args, plugins=[col])
    finally:
        os.chdir(old)
    tally = dict(passed=0, failed=0, xfailed=0, xpassed=0, skipped=0, error=0)
    reasons = []
    for r in col.reports:
        wasx = hasattr(r, "wasxfail")
        if r.when in ("setup", "teardown") and r.outcome == "failed":
            tally["error"] += 1
            continue
        if r.when == "call" or (r.when == "setup" and r.outcome == "skipped"):
            if r.outcome == "skipped" and wasx:
                tally["xfailed"] += 1
            elif r.outcome == "skipped":
                tally["skipped"] += 1
            elif r.outcome == "passed" and wasx:
                tally["xpassed"] += 1
            elif r.outcome == "passed":
                tally["passed"] += 1
            elif r.outcome == "failed":
                tally["failed"] += 1
        if wasx:
            reasons.append(str(getattr(r, "wasxfail", "")))
    return tally, reasons

# ==== probe body ====

tally, reasons = run_pytest("""
    import pytest
    def test_this(request):
        request.node.add_marker(pytest.mark.xfail(reason="dyn"))
        assert 0
""")
print("probe1 tally:", tally)
ok = tally["xfailed"] == 1 and tally["failed"] == 0
print("PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
import os, sys, tempfile, textwrap, itertools
import pytest

_counter = itertools.count()

class _Collector:
    def __init__(self):
        self.reports = []
    def pytest_runtest_logreport(self, report):
        self.reports.append(report)

def run_pytest(test_src, extra_args=None):
    """Write test_src to an isolated tmp dir with a UNIQUE module name, run
    pytest.main in a fresh dir, return (tally, xfail_reasons)."""
    d = tempfile.mkdtemp(prefix="probe_run_")
    modname = "test_probe_%d.py" % next(_counter)
    tf = os.path.join(d, modname)
    with open(tf, "w") as f:
        f.write(textwrap.dedent(test_src))
    col = _Collector()
    args = [tf, "-p", "no:cacheprovider"]
    if extra_args:
        args += extra_args
    old = os.getcwd()
    os.chdir(d)
    try:
        pytest.main(args, plugins=[col])
    finally:
        os.chdir(old)
    tally = dict(passed=0, failed=0, xfailed=0, xpassed=0, skipped=0, error=0)
    reasons = []
    for r in col.reports:
        wasx = hasattr(r, "wasxfail")
        if r.when in ("setup", "teardown") and r.outcome == "failed":
            tally["error"] += 1
            continue
        if r.when == "call" or (r.when == "setup" and r.outcome == "skipped"):
            if r.outcome == "skipped" and wasx:
                tally["xfailed"] += 1
            elif r.outcome == "skipped":
                tally["skipped"] += 1
            elif r.outcome == "passed" and wasx:
                tally["xpassed"] += 1
            elif r.outcome == "passed":
                tally["passed"] += 1
            elif r.outcome == "failed":
                tally["failed"] += 1
        if wasx:
            reasons.append(str(getattr(r, "wasxfail", "")))
    return tally, reasons

# ==== probe body ====

tally, reasons = run_pytest("""
    import pytest
    def test_this(request):
        request.node.add_marker(pytest.mark.xfail(reason="dyn", strict=True))
""")
print("probe2 tally:", tally)
ok = tally["failed"] == 1 and tally["passed"] == 0 and tally["xpassed"] == 0
print("PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
import os, sys, tempfile, textwrap, itertools
import pytest

_counter = itertools.count()

class _Collector:
    def __init__(self):
        self.reports = []
    def pytest_runtest_logreport(self, report):
        self.reports.append(report)

def run_pytest(test_src, extra_args=None):
    """Write test_src to an isolated tmp dir with a UNIQUE module name, run
    pytest.main in a fresh dir, return (tally, xfail_reasons)."""
    d = tempfile.mkdtemp(prefix="probe_run_")
    modname = "test_probe_%d.py" % next(_counter)
    tf = os.path.join(d, modname)
    with open(tf, "w") as f:
        f.write(textwrap.dedent(test_src))
    col = _Collector()
    args = [tf, "-p", "no:cacheprovider"]
    if extra_args:
        args += extra_args
    old = os.getcwd()
    os.chdir(d)
    try:
        pytest.main(args, plugins=[col])
    finally:
        os.chdir(old)
    tally = dict(passed=0, failed=0, xfailed=0, xpassed=0, skipped=0, error=0)
    reasons = []
    for r in col.reports:
        wasx = hasattr(r, "wasxfail")
        if r.when in ("setup", "teardown") and r.outcome == "failed":
            tally["error"] += 1
            continue
        if r.when == "call" or (r.when == "setup" and r.outcome == "skipped"):
            if r.outcome == "skipped" and wasx:
                tally["xfailed"] += 1
            elif r.outcome == "skipped":
                tally["skipped"] += 1
            elif r.outcome == "passed" and wasx:
                tally["xpassed"] += 1
            elif r.outcome == "passed":
                tally["passed"] += 1
            elif r.outcome == "failed":
                tally["failed"] += 1
        if wasx:
            reasons.append(str(getattr(r, "wasxfail", "")))
    return tally, reasons

# ==== probe body ====

t1,_ = run_pytest("""
    import pytest
    @pytest.mark.xfail(reason="r")
    def test_a():
        assert 0
""")
t2,_ = run_pytest("""
    import pytest
    @pytest.mark.xfail(reason="r")
    def test_b():
        assert 1
""")
t3,_ = run_pytest("""
    import pytest
    @pytest.mark.xfail(reason="r", strict=True)
    def test_c():
        assert 1
""")
print("t1",t1,"t2",t2,"t3",t3)
ok = (t1["xfailed"]==1 and t1["failed"]==0
      and t2["xpassed"]==1 and t2["failed"]==0
      and t3["failed"]==1 and t3["xpassed"]==0)
print("PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
import os, sys, tempfile, textwrap, itertools
import pytest

_counter = itertools.count()

class _Collector:
    def __init__(self):
        self.reports = []
    def pytest_runtest_logreport(self, report):
        self.reports.append(report)

def run_pytest(test_src, extra_args=None):
    """Write test_src to an isolated tmp dir with a UNIQUE module name, run
    pytest.main in a fresh dir, return (tally, xfail_reasons)."""
    d = tempfile.mkdtemp(prefix="probe_run_")
    modname = "test_probe_%d.py" % next(_counter)
    tf = os.path.join(d, modname)
    with open(tf, "w") as f:
        f.write(textwrap.dedent(test_src))
    col = _Collector()
    args = [tf, "-p", "no:cacheprovider"]
    if extra_args:
        args += extra_args
    old = os.getcwd()
    os.chdir(d)
    try:
        pytest.main(args, plugins=[col])
    finally:
        os.chdir(old)
    tally = dict(passed=0, failed=0, xfailed=0, xpassed=0, skipped=0, error=0)
    reasons = []
    for r in col.reports:
        wasx = hasattr(r, "wasxfail")
        if r.when in ("setup", "teardown") and r.outcome == "failed":
            tally["error"] += 1
            continue
        if r.when == "call" or (r.when == "setup" and r.outcome == "skipped"):
            if r.outcome == "skipped" and wasx:
                tally["xfailed"] += 1
            elif r.outcome == "skipped":
                tally["skipped"] += 1
            elif r.outcome == "passed" and wasx:
                tally["xpassed"] += 1
            elif r.outcome == "passed":
                tally["passed"] += 1
            elif r.outcome == "failed":
                tally["failed"] += 1
        if wasx:
            reasons.append(str(getattr(r, "wasxfail", "")))
    return tally, reasons

# ==== probe body ====

t1,_ = run_pytest("""
    import pytest
    @pytest.mark.xfail(reason="r")
    def test_a():
        assert 0
""", extra_args=["--runxfail"])
t2,reasons = run_pytest("""
    import pytest
    @pytest.mark.xfail(reason="r", run=False)
    def test_b():
        raise AssertionError("body should not run")
""")
print("runxfail t1",t1)
print("notrun t2",t2,"reasons",reasons)
ok = (t1["failed"]==1 and t1["xfailed"]==0
      and t2["xfailed"]==1 and t2["failed"]==0
      and any("NOTRUN" in r for r in reasons))
print("PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
import os, sys, tempfile, textwrap, itertools
import pytest

_counter = itertools.count()

class _Collector:
    def __init__(self):
        self.reports = []
    def pytest_runtest_logreport(self, report):
        self.reports.append(report)

def run_pytest(test_src, extra_args=None):
    """Write test_src to an isolated tmp dir with a UNIQUE module name, run
    pytest.main in a fresh dir, return (tally, xfail_reasons)."""
    d = tempfile.mkdtemp(prefix="probe_run_")
    modname = "test_probe_%d.py" % next(_counter)
    tf = os.path.join(d, modname)
    with open(tf, "w") as f:
        f.write(textwrap.dedent(test_src))
    col = _Collector()
    args = [tf, "-p", "no:cacheprovider"]
    if extra_args:
        args += extra_args
    old = os.getcwd()
    os.chdir(d)
    try:
        pytest.main(args, plugins=[col])
    finally:
        os.chdir(old)
    tally = dict(passed=0, failed=0, xfailed=0, xpassed=0, skipped=0, error=0)
    reasons = []
    for r in col.reports:
        wasx = hasattr(r, "wasxfail")
        if r.when in ("setup", "teardown") and r.outcome == "failed":
            tally["error"] += 1
            continue
        if r.when == "call" or (r.when == "setup" and r.outcome == "skipped"):
            if r.outcome == "skipped" and wasx:
                tally["xfailed"] += 1
            elif r.outcome == "skipped":
                tally["skipped"] += 1
            elif r.outcome == "passed" and wasx:
                tally["xpassed"] += 1
            elif r.outcome == "passed":
                tally["passed"] += 1
            elif r.outcome == "failed":
                tally["failed"] += 1
        if wasx:
            reasons.append(str(getattr(r, "wasxfail", "")))
    return tally, reasons

# ==== probe body ====

t1,_ = run_pytest("""
    import pytest
    @pytest.mark.skip(reason="r")
    def test_a():
        raise AssertionError("body ran")
""")
t2,_ = run_pytest("""
    import pytest
    @pytest.mark.skipif(True, reason="r")
    def test_b():
        raise AssertionError("body ran")
""")
print("skip",t1,"skipif",t2)
ok = t1["skipped"]==1 and t2["skipped"]==1
print("PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
import os, sys, tempfile, textwrap, itertools
import pytest

_counter = itertools.count()

class _Collector:
    def __init__(self):
        self.reports = []
    def pytest_runtest_logreport(self, report):
        self.reports.append(report)

def run_pytest(test_src, extra_args=None):
    """Write test_src to an isolated tmp dir with a UNIQUE module name, run
    pytest.main in a fresh dir, return (tally, xfail_reasons)."""
    d = tempfile.mkdtemp(prefix="probe_run_")
    modname = "test_probe_%d.py" % next(_counter)
    tf = os.path.join(d, modname)
    with open(tf, "w") as f:
        f.write(textwrap.dedent(test_src))
    col = _Collector()
    args = [tf, "-p", "no:cacheprovider"]
    if extra_args:
        args += extra_args
    old = os.getcwd()
    os.chdir(d)
    try:
        pytest.main(args, plugins=[col])
    finally:
        os.chdir(old)
    tally = dict(passed=0, failed=0, xfailed=0, xpassed=0, skipped=0, error=0)
    reasons = []
    for r in col.reports:
        wasx = hasattr(r, "wasxfail")
        if r.when in ("setup", "teardown") and r.outcome == "failed":
            tally["error"] += 1
            continue
        if r.when == "call" or (r.when == "setup" and r.outcome == "skipped"):
            if r.outcome == "skipped" and wasx:
                tally["xfailed"] += 1
            elif r.outcome == "skipped":
                tally["skipped"] += 1
            elif r.outcome == "passed" and wasx:
                tally["xpassed"] += 1
            elif r.outcome == "passed":
                tally["passed"] += 1
            elif r.outcome == "failed":
                tally["failed"] += 1
        if wasx:
            reasons.append(str(getattr(r, "wasxfail", "")))
    return tally, reasons

# ==== probe body ====

tally,_ = run_pytest("""
    import pytest
    @pytest.fixture
    def f(request):
        request.node.add_marker(pytest.mark.xfail(reason="setup dyn"))
    def test_this(f):
        assert 0
""")
print("probe6 tally:", tally)
ok = tally["xfailed"]==1 and tally["failed"]==0
print("PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)
```

Attack 7 — `probe_7.py` → holds on the patched tree (good)

```python
import os, sys, tempfile, textwrap, itertools
import pytest

_counter = itertools.count()

class _Collector:
    def __init__(self):
        self.reports = []
    def pytest_runtest_logreport(self, report):
        self.reports.append(report)

def run_pytest(test_src, extra_args=None):
    """Write test_src to an isolated tmp dir with a UNIQUE module name, run
    pytest.main in a fresh dir, return (tally, xfail_reasons)."""
    d = tempfile.mkdtemp(prefix="probe_run_")
    modname = "test_probe_%d.py" % next(_counter)
    tf = os.path.join(d, modname)
    with open(tf, "w") as f:
        f.write(textwrap.dedent(test_src))
    col = _Collector()
    args = [tf, "-p", "no:cacheprovider"]
    if extra_args:
        args += extra_args
    old = os.getcwd()
    os.chdir(d)
    try:
        pytest.main(args, plugins=[col])
    finally:
        os.chdir(old)
    tally = dict(passed=0, failed=0, xfailed=0, xpassed=0, skipped=0, error=0)
    reasons = []
    for r in col.reports:
        wasx = hasattr(r, "wasxfail")
        if r.when in ("setup", "teardown") and r.outcome == "failed":
            tally["error"] += 1
            continue
        if r.when == "call" or (r.when == "setup" and r.outcome == "skipped"):
            if r.outcome == "skipped" and wasx:
                tally["xfailed"] += 1
            elif r.outcome == "skipped":
                tally["skipped"] += 1
            elif r.outcome == "passed" and wasx:
                tally["xpassed"] += 1
            elif r.outcome == "passed":
                tally["passed"] += 1
            elif r.outcome == "failed":
                tally["failed"] += 1
        if wasx:
            reasons.append(str(getattr(r, "wasxfail", "")))
    return tally, reasons

# ==== probe body ====

t1,_ = run_pytest("""
    import pytest
    @pytest.mark.xfail(raises=ValueError)
    def test_a():
        raise ValueError("x")
""")
t2,_ = run_pytest("""
    import pytest
    @pytest.mark.xfail(raises=ValueError)
    def test_b():
        raise KeyError("x")
""")
print("match",t1,"nomatch",t2)
ok = t1["xfailed"]==1 and t1["failed"]==0 and t2["failed"]==1 and t2["xfailed"]==0
print("PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
import os, sys, tempfile, textwrap, itertools
import pytest

_counter = itertools.count()

class _Collector:
    def __init__(self):
        self.reports = []
    def pytest_runtest_logreport(self, report):
        self.reports.append(report)

def run_pytest(test_src, extra_args=None):
    """Write test_src to an isolated tmp dir with a UNIQUE module name, run
    pytest.main in a fresh dir, return (tally, xfail_reasons)."""
    d = tempfile.mkdtemp(prefix="probe_run_")
    modname = "test_probe_%d.py" % next(_counter)
    tf = os.path.join(d, modname)
    with open(tf, "w") as f:
        f.write(textwrap.dedent(test_src))
    col = _Collector()
    args = [tf, "-p", "no:cacheprovider"]
    if extra_args:
        args += extra_args
    old = os.getcwd()
    os.chdir(d)
    try:
        pytest.main(args, plugins=[col])
    finally:
        os.chdir(old)
    tally = dict(passed=0, failed=0, xfailed=0, xpassed=0, skipped=0, error=0)
    reasons = []
    for r in col.reports:
        wasx = hasattr(r, "wasxfail")
        if r.when in ("setup", "teardown") and r.outcome == "failed":
            tally["error"] += 1
            continue
        if r.when == "call" or (r.when == "setup" and r.outcome == "skipped"):
            if r.outcome == "skipped" and wasx:
                tally["xfailed"] += 1
            elif r.outcome == "skipped":
                tally["skipped"] += 1
            elif r.outcome == "passed" and wasx:
                tally["xpassed"] += 1
            elif r.outcome == "passed":
                tally["passed"] += 1
            elif r.outcome == "failed":
                tally["failed"] += 1
        if wasx:
            reasons.append(str(getattr(r, "wasxfail", "")))
    return tally, reasons

# ==== probe body ====

tally, reasons = run_pytest("""
    import pytest
    def test_this(request):
        request.node.add_marker(pytest.mark.xfail(reason="dyn"))
        assert 0
""")
print("probe1 tally:", tally)
ok = tally["xfailed"] == 1 and tally["failed"] == 0
print("PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance pytest-7490: restore honoring dynamically-added xfail markers in src/_pytest/skipping.py. 7 probes, each standalone (uses pytest.main + a logreport collector plugin, no pytest test-collection of the probe itself; runs each scenario in an isolated tmp dir with a unique module name). Results:

PATCHED tree — all 7 HOLD:
- probe_1 (Req1.1, POSITIVE CONTROL): dynamic non-strict xfail added in test body + fail -> xfailed=1, failed=0. HOLDS patched, VIOLATED at base (base reports failed=1). Discriminates; prepatch reproduced.
- probe_2 (Req2.1): dynamic strict xfail added in body + pass -> failed=1. HOLDS.
- probe_3 (Req3.1/3.2/3.3): static xfail+fail->xfailed; static non-strict+pass->xpassed; static strict+pass->failed. HOLDS.
- probe_4 (Req4.1/4.3): --runxfail makes failing xfail a real failure; run=False xfail (no runxfail) skips body -> xfailed with [NOTRUN] reason. HOLDS.
- probe_5 (Req5.1): skip and satisfied skipif -> skipped before body. HOLDS.
- probe_6 (Req6.1): xfail added during fixture setup + fail -> xfailed. HOLDS.
- probe_7 (Req3.4): xfail(raises=ValueError): matching exc -> xfailed, non-matching -> failed. HOLDS.

WRONG-FIX CANDIDATE (weak.diff = the gold refactor of setup/call hooks WITHOUT the post-yield re-derivation block that the fix adds after `yield` in pytest_runtest_call — i.e. the lazy reading that reorganizes runxfail checks but never re-reads markers introduced during the body): REJECTED by probe_1 and probe_2 (both VIOLATED — dynamic-body xfail still reported as hard failure / passing strict, exactly the F2P cases), while probes 3-7 still HOLD. This demonstrates the suite discriminates the core wrong implementation: any patch conforming to probes 1 & 2 must include the post-body re-derivation, which is precisely what resolves the hidden F2P tests test_dynamic_xfail_set_during_runtest_failed and _passed_strict.

Candidate exercised: 1; rejected: 1. Positive control discriminates. No requirements VIOLATION found on the patched tree; no probe-conforming TOO-WEAK patch found. Verdict SOUND.

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
import os, sys, tempfile, textwrap, itertools
import pytest

_counter = itertools.count()

class _Collector:
    def __init__(self):
        self.reports = []
    def pytest_runtest_logreport(self, report):
        self.reports.append(report)

def run_pytest(test_src, extra_args=None):
    """Write test_src to an isolated tmp dir with a UNIQUE module name, run
    pytest.main in a fresh dir, return (tally, xfail_reasons)."""
    d = tempfile.mkdtemp(prefix="probe_run_")
    modname = "test_probe_%d.py" % next(_counter)
    tf = os.path.join(d, modname)
    with open(tf, "w") as f:
        f.write(textwrap.dedent(test_src))
    col = _Collector()
    args = [tf, "-p", "no:cacheprovider"]
    if extra_args:
        args += extra_args
    old = os.getcwd()
    os.chdir(d)
    try:
        pytest.main(args, plugins=[col])
    finally:
        os.chdir(old)
    tally = dict(passed=0, failed=0, xfailed=0, xpassed=0, skipped=0, error=0)
    reasons = []
    for r in col.reports:
        wasx = hasattr(r, "wasxfail")
        if r.when in ("setup", "teardown") and r.outcome == "failed":
            tally["error"] += 1
            continue
        if r.when == "call" or (r.when == "setup" and r.outcome == "skipped"):
            if r.outcome == "skipped" and wasx:
                tally["xfailed"] += 1
            elif r.outcome == "skipped":
                tally["skipped"] += 1
            elif r.outcome == "passed" and wasx:
                tally["xpassed"] += 1
            elif r.outcome == "passed":
                tally["passed"] += 1
            elif r.outcome == "failed":
                tally["failed"] += 1
        if wasx:
            reasons.append(str(getattr(r, "wasxfail", "")))
    return tally, reasons

# ==== probe body ====

tally, reasons = run_pytest("""
    import pytest
    def test_this(request):
        request.node.add_marker(pytest.mark.xfail(reason="dyn"))
        assert 0
""")
print("probe1 tally:", tally)
ok = tally["xfailed"] == 1 and tally["failed"] == 0
print("PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance pytest-7490: restore honoring dynamically-added xfail markers in src/_pytest/skipping.py. 7 probes, each standalone (uses pytest.main + a logreport collector plugin, no pytest test-collection of the probe itself; runs each scenario in an isolated tmp dir with a unique module name). Results:

PATCHED tree — all 7 HOLD:
- probe_1 (Req1.1, POSITIVE CONTROL): dynamic non-strict xfail added in test body + fail -> xfailed=1, failed=0. HOLDS patched, VIOLATED at base (base reports failed=1). Discriminates; prepatch reproduced.
- probe_2 (Req2.1): dynamic strict xfail added in body + pass -> failed=1. HOLDS.
- probe_3 (Req3.1/3.2/3.3): static xfail+fail->xfailed; static non-strict+pass->xpassed; static strict+pass->failed. HOLDS.
- probe_4 (Req4.1/4.3): --runxfail makes failing xfail a real failure; run=False xfail (no runxfail) skips body -> xfailed with [NOTRUN] reason. HOLDS.
- probe_5 (Req5.1): skip and satisfied skipif -> skipped before body. HOLDS.
- probe_6 (Req6.1): xfail added during fixture setup + fail -> xfailed. HOLDS.
- probe_7 (Req3.4): xfail(raises=ValueError): matching exc -> xfailed, non-matching -> failed. HOLDS.

WRONG-FIX CANDIDATE (weak.diff = the gold refactor of setup/call hooks WITHOUT the post-yield re-derivation block that the fix adds after `yield` in pytest_runtest_call — i.e. the lazy reading that reorganizes runxfail checks but never re-reads markers introduced during the body): REJECTED by probe_1 and probe_2 (both VIOLATED — dynamic-body xfail still reported as hard failure / passing strict, exactly the F2P cases), while probes 3-7 still HOLD. This demonstrates the suite discriminates the core wrong implementation: any patch conforming to probes 1 & 2 must include the post-body re-derivation, which is precisely what resolves the hidden F2P tests test_dynamic_xfail_set_during_runtest_failed and _passed_strict.

Candidate exercised: 1; rejected: 1. Positive control discriminates. No requirements VIOLATION found on the patched tree; no probe-conforming TOO-WEAK patch found. Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Patch (src/_pytest/skipping.py): (a) setup now always stores xfailed_key = evaluate_xfail_marks(item) regardless of runxfail, gating only the [NOTRUN] xfail() on runxfail; (b) pytest_runtest_call, after `yield`, re-derives xfailed from the store ONLY if it is still None — i.e. a before-body annotation is authoritative, otherwise the after-body markers are consulted. This exactly matches the Introduction cascade (L26-31) and Req 1.3/1.4.

Behavioral confirmation on patched tree (probes):
- Req1: dynamic non-strict xfail added in body + assert 0 -> XFAIL (base tree: '1 failed' -> confirms regression the patch fixes).
- Req2: dynamic strict xfail added in body + passing test -> failed [XPASS(strict)] with reason 'dyn' preserved.
- Req3: static xfail fail->xfailed; static strict xpass->failed; skipif condition-false path handled (test_cond_false with condition=False failed, not xfailed).
- Req4: no flag -> 2 xfailed (incl run=False NOTRUN short-circuit); --runxfail -> 2 failed (real outcomes, body allowed to run).
- Req5: skip + satisfied skipif -> 2 skipped, evaluated independently of runxfail (skipped_by_mark_key = skipped is not None set unconditionally).
- Req6: fixture adds xfail during setup + assert 0 -> XFAIL; run=False dynamic honored when runxfail disabled.
F2P tests (test_dynamic_xfail_set_during_runtest_failed / _passed_strict) correspond directly to Req1/Req2. The modeling boundary (the effective-xfail cascade + report conversion) is the changed observable behavior, not a narrow slice.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** requirements.md describes behavior, not the hidden tests. The two FAIL_TO_PASS cases (test_dynamic_xfail_set_during_runtest_failed / _passed_strict) map to Req 1 and Req 2, but: (a) the failing-dynamic-xfail scenario (add_marker(xfail) + assert 0 -> xfailed) is already fully public in problem_statement, including the code snippet; (b) the strict-dynamic-xfail-on-passing-test -> failure case is a behavioral translation of standard xfail strict semantics, with no test name, path, class, assert_outcomes call, parametrization id, or quoted test/gold code reproduced. All named symbols (src/_pytest/skipping.py, pytest_runtest_setup/call/makereport, evaluate_skip_marks, evaluate_xfail_marks, runxfail) are pre-existing module identifiers used to localize the change — legitimate, not fix-invented; the gold patch introduces no new identifiers. The 'most-specific-known-first cascade' prose (lines 26-31) describes the store-then-reevaluate fix logic behaviorally rather than quoting it. Reqs 3-6 (static xfail, runxfail, skip/skipif, fixture-setup dynamic xfail) cover general pre-existing behavior broader than the two hidden tests, so they are not a test-parametrization mirror. No semantic reconstruction of the hidden test suite.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
